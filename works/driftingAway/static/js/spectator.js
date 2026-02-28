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
  let _revealTimer = null;
  let _revealIdleTimer = null;
  let _currentTopic = null;

  // ── Phase handling ────────────────────────────────────────────────
  socket.on("snapshot", applyState);
  socket.on("phase", applyState);

  // ── Language change ─────────────────────────────────────────────
  socket.on("language_change", (msg) => {
    i18n.setLang(msg.language);
    document.documentElement.lang = msg.language;
    document.title = i18n.t("title.spectator") + " — Spectator";
    refreshStaticText();
  });
  socket.on("snapshot", (msg) => {
    if (msg.language) {
      i18n.setLang(msg.language);
      document.documentElement.lang = msg.language;
      document.title = i18n.t("title.spectator") + " — Spectator";
      refreshStaticText();
    }
  });

  /** Update all static text elements with current i18n strings */
  function refreshStaticText() {
    // Idle screen
    const h1 = document.querySelector(".spectator-idle h1");
    if (h1) h1.textContent = i18n.t("spectator.title");
    const sub = document.querySelector(".spectator-idle-sub");
    if (sub) sub.textContent = i18n.t("spectator.subtitle");
    const desc = document.querySelector(".spectator-idle-desc");
    if (desc) desc.textContent = i18n.t("spectator.description");
    // Player headers
    const p1H = document.querySelector(".spectator-panel--p1 h3");
    if (p1H) p1H.textContent = i18n.t("spectator.player1");
    const p2H = document.querySelector(".spectator-panel--p2 h3");
    if (p2H) p2H.textContent = i18n.t("spectator.player2");
    // Topic labels
    const splashLabel = document.querySelector(".topic-splash-label");
    if (splashLabel)
      splashLabel.textContent = i18n.t("spectator.originalTopic");
    const barLabel = document.querySelector(".spectator-topic-bar-label");
    if (barLabel) barLabel.textContent = i18n.t("spectator.originalTopic");
  }

  function applyState(msg) {
    const phase = msg.phase;

    // During the reveal sequence (splash + history display), ignore any phase
    // transitions that would dismiss it prematurely.  Allow "conversation" through
    // so a brand-new round can cancel the sequence cleanly.
    if (_revealTimer !== null || _revealIdleTimer !== null) {
      if (phase === "conversation") {
        // New round starting — cancel reveal and fall through normally
        if (_revealTimer) { clearTimeout(_revealTimer); _revealTimer = null; }
        if (_revealIdleTimer) { clearTimeout(_revealIdleTimer); _revealIdleTimer = null; }
        hideRevealSplash();
      } else if (phase !== "reveal") {
        return; // Swallow idle / reset / waiting / prompt_select
      }
    }

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
        i18n.t("spectator.waitingForPlayers") +
        '<span class="waiting-dots"></span>';
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
        i18n.t("spectator.nextRound") + '<span class="waiting-dots"></span>';
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
          i18n.t("spectator.waitingForPlayers") +
          '<span class="waiting-dots"></span>';
      } else if (ready.includes(1) && !ready.includes(2)) {
        $idleStatus.innerHTML =
          i18n.t("spectator.p1Ready") + '<span class="waiting-dots"></span>';
      } else if (ready.includes(2) && !ready.includes(1)) {
        $idleStatus.innerHTML =
          i18n.t("spectator.p2Ready") + '<span class="waiting-dots"></span>';
      } else {
        $idleStatus.innerHTML =
          i18n.t("spectator.bothReady") + '<span class="waiting-dots"></span>';
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
        i18n.t("spectator.deciding", { n: starter }) +
        '<span class="waiting-dots"></span>';
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

      // Grab topic from msg if not already stored (handles page-refresh mid-reveal)
      if (!_currentTopic && msg.prompt) _currentTopic = msg.prompt.topic;
      if (!_currentTopic && msg.topic) _currentTopic = msg.topic;

      // Guard against multiple stacked timers (reconnect / duplicate snapshots)
      if (_revealTimer) { clearTimeout(_revealTimer); _revealTimer = null; }
      if (_revealIdleTimer) { clearTimeout(_revealIdleTimer); _revealIdleTimer = null; }

      showRevealSplash();

      const revealTurns = msg.turns ? [...msg.turns] : null;
      _revealTimer = setTimeout(() => {
        _revealTimer = null;
        hideRevealSplash();
        $spectatorMain.hidden = false;
        if (_currentTopic) showTopicBar(_currentTopic);
        // Render full history (from stored turns)
        if (revealTurns && revealTurns.length > 0) {
          clearPanels();
          revealTurns.forEach((t) => addTurn(t));
        }
        // After 1 minute, return to idle
        _revealIdleTimer = setTimeout(() => {
          _revealIdleTimer = null;
          $spectatorMain.hidden = true;
          hideTopicBar();
          $idle.hidden = false;
          clearPanels();
          _currentTopic = null;
          $idleStatus.innerHTML =
            i18n.t("spectator.waitingForPlayers") +
            '<span class="waiting-dots"></span>';
        }, 60000);
      }, 15000);
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

  // ── Reveal splash ─────────────────────────────────────────────────
  function showRevealSplash() {
    document.getElementById("reveal-splash").hidden = false;
    $spectatorMain.hidden = true;
  }

  function hideRevealSplash() {
    document.getElementById("reveal-splash").hidden = true;
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
