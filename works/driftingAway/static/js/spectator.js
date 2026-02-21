/**
 * Drifting Away — Spectator Screen Logic
 * Shows both players' original and misheard messages side by side.
 * Displays the topic in large text for 5 seconds at conversation start.
 */

(function () {
  const socket = new DriftSocket("spectator1");

  // ── DOM refs ──────────────────────────────────────────────────────
  const $timer = document.getElementById("timer");
  const $topicSplash = document.getElementById("topic-splash");
  const $topicSplashText = document.getElementById("topic-splash-text");
  const $spectatorMain = document.getElementById("spectator-main");
  const $p1Panel = document.getElementById("panel-p1");
  const $p2Panel = document.getElementById("panel-p2");
  const $topicBar = document.getElementById("spectator-topic-bar");
  const $topicBarText = document.getElementById("spectator-topic-bar-text");
  const $idle = document.getElementById("spectator-idle");
  const $idleStatus = document.getElementById("spectator-idle-status");

  let _splashTimer = null;
  let _currentTopic = null;

  // ── Phase handling ────────────────────────────────────────────────
  socket.on("snapshot", applyState);
  socket.on("phase", applyState);

  function applyState(msg) {
    const phase = msg.phase;

    if (phase === "idle") {
      $timer.classList.remove("warning", "danger");
      $timer.textContent = "3:00";
      hideSplash();
      hideTopicBar();
      $spectatorMain.hidden = true;
      $idle.hidden = false;
      clearPanels();
      _currentTopic = null;
      $idleStatus.innerHTML =
        'Waiting for players to start<span class="waiting-dots"></span>';
    }

    if (phase === "reset") {
      $timer.classList.remove("warning", "danger");
      $timer.textContent = "3:00";
      hideSplash();
      hideTopicBar();
      $spectatorMain.hidden = true;
      $idle.hidden = false;
      clearPanels();
      _currentTopic = null;
      $idleStatus.innerHTML =
        'Next round starting soon<span class="waiting-dots"></span>';
    }

    if (phase === "waiting") {
      $timer.classList.remove("warning", "danger");
      $timer.textContent = "3:00";
      hideSplash();
      hideTopicBar();
      $spectatorMain.hidden = true;
      $idle.hidden = false;
      clearPanels();
      _currentTopic = null;
      const ready = msg.playersReady || [];
      if (ready.length === 0) {
        $idleStatus.innerHTML =
          'Waiting for players to start<span class="waiting-dots"></span>';
      } else if (ready.includes(1) && !ready.includes(2)) {
        $idleStatus.innerHTML =
          'Player 1 is ready, waiting for Player 2<span class="waiting-dots"></span>';
      } else if (ready.includes(2) && !ready.includes(1)) {
        $idleStatus.innerHTML =
          'Player 2 is ready, waiting for Player 1<span class="waiting-dots"></span>';
      } else {
        $idleStatus.innerHTML =
          'Both players ready<span class="waiting-dots"></span>';
      }
    }

    if (phase === "prompt_select") {
      hideSplash();
      hideTopicBar();
      $spectatorMain.hidden = true;
      $idle.hidden = false;
      clearPanels();
      const starter = msg.startingPlayer || 0;
      $idleStatus.innerHTML =
        "Player " +
        starter +
        ' is deciding the topic<span class="waiting-dots"></span>';
    }

    if (phase === "conversation") {
      $idle.hidden = true;
      clearPanels();
      // Show topic in big text, then reveal chat panels + topic bar after 5s
      if (msg.prompt) {
        _currentTopic = msg.prompt.topic;
        showSplash(_currentTopic);
      } else {
        // No topic data (e.g. late joiner) — just show panels
        hideSplash();
        $spectatorMain.hidden = false;
        if (_currentTopic) showTopicBar(_currentTopic);
      }
    }

    if (phase === "reveal") {
      $idle.hidden = true;
      hideSplash();
      $spectatorMain.hidden = false;
      if (_currentTopic) showTopicBar(_currentTopic);
      // Render full history
      if (msg.turns) {
        clearPanels();
        msg.turns.forEach((t) => addTurn(t));
      }
    }
  }

  // ── Topic splash ─────────────────────────────────────────────────
  function showSplash(topic) {
    if (_splashTimer) clearTimeout(_splashTimer);
    $topicSplashText.textContent = topic;
    $topicSplash.hidden = false;
    $spectatorMain.hidden = true;
    _splashTimer = setTimeout(() => {
      hideSplash();
      $spectatorMain.hidden = false;
      showTopicBar(topic);
    }, 5000);
  }

  function hideSplash() {
    if (_splashTimer) {
      clearTimeout(_splashTimer);
      _splashTimer = null;
    }
    $topicSplash.hidden = true;
  }

  // ── Topic bar (persistent bottom strip) ───────────────────────────
  function showTopicBar(topic) {
    $topicBarText.textContent = topic;
    $topicBar.hidden = false;
  }

  function hideTopicBar() {
    $topicBar.hidden = true;
    $topicBarText.textContent = "";
  }

  // ── Timer ─────────────────────────────────────────────────────────
  socket.on("timer", (msg) => {
    const r = msg.remaining;
    $timer.textContent = formatTime(r);
    $timer.classList.toggle("warning", r <= 30 && r > 10);
    $timer.classList.toggle("danger", r <= 10);
  });

  // ── New turn (with minimum display time queue) ────────────────────
  const SPECTATOR_MIN_DISPLAY_MS = 6000;
  const _turnQueue = []; // queued turn objects
  let _turnBusy = false; // true while waiting for min display
  let _lastTurnShown = 0; // timestamp of last rendered turn

  socket.on("turn", (msg) => _enqueueTurn(msg));

  function _enqueueTurn(t) {
    _turnQueue.push(t);
    _flushTurnQueue();
  }

  function _flushTurnQueue() {
    if (_turnBusy || _turnQueue.length === 0) return;

    const now = Date.now();
    const elapsed = now - _lastTurnShown;

    if (_lastTurnShown > 0 && elapsed < SPECTATOR_MIN_DISPLAY_MS) {
      _turnBusy = true;
      setTimeout(() => {
        _turnBusy = false;
        _flushTurnQueue();
      }, SPECTATOR_MIN_DISPLAY_MS - elapsed);
      return;
    }

    const t = _turnQueue.shift();
    _lastTurnShown = Date.now();
    _renderTurn(t);

    // If more queued, schedule next
    if (_turnQueue.length > 0) {
      _turnBusy = true;
      setTimeout(() => {
        _turnBusy = false;
        _flushTurnQueue();
      }, SPECTATOR_MIN_DISPLAY_MS);
    }
  }

  function addTurn(t) {
    // Direct render (used for bulk replay on reconnect)
    _renderTurn(t);
  }

  function _renderTurn(t) {
    const panel = t.player === 1 ? $p1Panel : $p2Panel;
    const div = document.createElement("div");
    div.className = "spectator-turn";
    div.innerHTML = `
      <div class="original">${escHtml(t.original)}</div>
      <div class="misheard">${escHtml(t.misheard)}</div>
    `;
    panel.appendChild(div);
    // Scroll the parent .spectator-panel (which has overflow-y: auto)
    const scrollable = panel.closest(".spectator-panel");
    if (scrollable) scrollable.scrollTop = scrollable.scrollHeight;
  }

  function clearPanels() {
    $p1Panel.innerHTML = "";
    $p2Panel.innerHTML = "";
  }

  function escHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
})();
