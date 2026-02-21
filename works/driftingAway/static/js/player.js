/**
 * Drifting Away — Player Screen Logic
 * Handles all interactions for a single player's display.
 * Includes a mic-setup overlay that persists the device choice in localStorage.
 *
 * URL: /player/1  or  /player/2
 */

(function () {
  const PLAYER_ID = parseInt(document.body.dataset.playerId, 10);
  const STORAGE_KEY = `drifting_mic_p${PLAYER_ID}`;
  const socket = new DriftSocket(`player${PLAYER_ID}`);
  const audio = new AudioCapture(socket);

  // ── DOM refs ──────────────────────────────────────────────────────
  const $timer = document.getElementById("timer");
  const $cards = document.getElementById("prompt-cards");
  const $messages = document.getElementById("messages");
  const $pttDot = document.getElementById("ptt-dot");
  const $pttLabel = document.getElementById("ptt-label");
  const $revealBody = document.getElementById("reveal-body");

  // Mic setup overlay
  const $micSetup = document.getElementById("mic-setup");
  const $micList = document.getElementById("mic-list");
  const $micTestBtn = document.getElementById("mic-test-btn");
  const $micConfirmBtn = document.getElementById("mic-confirm-btn");

  let isStartingPlayer = false;
  let pttActive = false;
  let micReady = false;
  let _testStream = null;
  let _testCtx = null;
  let _testAnimFrame = null;

  // Minimum display time for messages (ms)
  const MIN_DISPLAY_MS = 6000;
  let _lastMessageShown = 0;
  let _pendingMessage = null;
  let _pendingTimer = null;

  // ══════════════════════════════════════════════════════════════════
  // MIC SETUP
  // ══════════════════════════════════════════════════════════════════

  async function initMicSetup() {
    const savedId = localStorage.getItem(STORAGE_KEY);

    if (savedId) {
      // Verify saved device still exists
      const devices = await AudioCapture.getAudioDevices();
      const found = devices.find((d) => d.deviceId === savedId);
      if (found) {
        console.log(`[Mic] Using saved device: ${found.label}`);
        audio.setDevice(savedId);
        await audio.init();
        micReady = true;
        $micSetup.hidden = true;
        return;
      }
      // Saved device gone — show picker again
      localStorage.removeItem(STORAGE_KEY);
    }

    // Show the mic setup overlay
    $micSetup.hidden = false;
    await renderMicList();
  }

  async function renderMicList() {
    const devices = await AudioCapture.getAudioDevices();

    if (devices.length === 0) {
      $micList.innerHTML =
        '<p class="mic-loading">No microphones found. Please connect a USB mic and refresh.</p>';
      return;
    }

    $micList.innerHTML = "";
    let selectedId = null;

    devices.forEach((dev, i) => {
      const id = dev.deviceId;
      const label = dev.label || `Microphone ${i + 1}`;

      const option = document.createElement("label");
      option.className = "mic-option";
      option.dataset.deviceId = id;
      option.innerHTML = `
        <input type="radio" name="mic" value="${id}">
        <span class="mic-label">${label}</span>
        <div class="mic-level"><div class="mic-level-bar" data-device="${id}"></div></div>
      `;

      const radio = option.querySelector("input");
      radio.addEventListener("change", () => {
        selectedId = id;
        document
          .querySelectorAll(".mic-option")
          .forEach((o) => o.classList.remove("selected"));
        option.classList.add("selected");
        $micTestBtn.disabled = false;
        $micConfirmBtn.disabled = false;
      });

      $micList.appendChild(option);
    });

    // Auto-select first device
    const firstRadio = $micList.querySelector("input[type=radio]");
    if (firstRadio) {
      firstRadio.checked = true;
      firstRadio.dispatchEvent(new Event("change"));
    }

    // ── Test button: show live mic level ─────────────────────────
    $micTestBtn.addEventListener("click", async () => {
      // Toggle test off if already running
      if (_testStream) {
        stopMicTest();
        return;
      }
      if (!selectedId) return;

      try {
        _testStream = await navigator.mediaDevices.getUserMedia({
          audio: { deviceId: { exact: selectedId } },
        });
        _testCtx = new AudioContext();
        const src = _testCtx.createMediaStreamSource(_testStream);
        const analyser = _testCtx.createAnalyser();
        analyser.fftSize = 256;
        src.connect(analyser);

        const buf = new Uint8Array(analyser.frequencyBinCount);
        const bar = document.querySelector(
          `.mic-level-bar[data-device="${selectedId}"]`,
        );

        function draw() {
          analyser.getByteFrequencyData(buf);
          const avg = buf.reduce((a, b) => a + b, 0) / buf.length;
          const pct = Math.min(100, (avg / 128) * 100);
          if (bar) bar.style.width = pct + "%";
          _testAnimFrame = requestAnimationFrame(draw);
        }
        draw();
        $micTestBtn.textContent = "⏹ Stop test";
      } catch (e) {
        console.error("[Mic] Test failed:", e);
      }
    });

    // ── Confirm button: save choice and init audio ──────────────
    $micConfirmBtn.addEventListener("click", async () => {
      stopMicTest();
      if (!selectedId) return;

      localStorage.setItem(STORAGE_KEY, selectedId);
      audio.setDevice(selectedId);
      await audio.init();
      micReady = true;
      $micSetup.hidden = true;
    });
  }

  function stopMicTest() {
    if (_testAnimFrame) cancelAnimationFrame(_testAnimFrame);
    if (_testStream) _testStream.getTracks().forEach((t) => t.stop());
    if (_testCtx) _testCtx.close();
    _testStream = null;
    _testCtx = null;
    // Reset all level bars
    document
      .querySelectorAll(".mic-level-bar")
      .forEach((b) => (b.style.width = "0%"));
    if ($micTestBtn) $micTestBtn.textContent = "🔊 Test";
  }

  // Start mic setup immediately
  initMicSetup();

  // ══════════════════════════════════════════════════════════════════
  // GAME LOGIC
  // ══════════════════════════════════════════════════════════════════

  // ── Phase handling ────────────────────────────────────────────────
  socket.on("snapshot", (msg) => applyState(msg));
  socket.on("phase", (msg) => applyState(msg));

  function applyState(msg) {
    const phase = msg.phase;
    showPhase(phase);

    if (phase === "idle") {
      $timer.classList.remove("visible");
    }

    if (phase === "waiting") {
      $timer.classList.remove("visible");
      const readyList = msg.playersReady || [];
      const $waitText = document.getElementById("waiting-text");
      if ($waitText) {
        if (readyList.includes(PLAYER_ID)) {
          // This player is ready, waiting for the other
          $waitText.innerHTML =
            'Waiting for the other player<span class="waiting-dots"></span>';
        } else {
          // The other player is already waiting for us
          $waitText.innerHTML =
            'The other player is ready! Press any button to begin<span class="waiting-dots"></span>';
        }
      }
    }

    if (phase === "prompt_select") {
      isStartingPlayer = msg.startingPlayer === PLAYER_ID;
      const idx = msg.highlightIndex !== undefined ? msg.highlightIndex : 0;
      renderPromptCards(msg.choices || msg.promptChoices || [], idx);
    }

    if (phase === "conversation") {
      $timer.classList.add("visible");
      // Only the player who chose the topic sees it
      if (isStartingPlayer && msg.prompt) {
        addTopicMessage(msg.prompt.topic);
      }
    }

    if (phase === "reveal") {
      $timer.classList.remove("visible");
      renderReveal(msg);
    }

    if (phase === "reset") {
      $timer.classList.remove("visible", "warning", "danger");
      clearMessages();
    }

    if (phase === "idle") {
      $timer.textContent = "3:00";
      $timer.classList.remove("visible", "warning", "danger");
      clearMessages();
      isStartingPlayer = false;
      pttActive = false;
    }
  }

  // ── Timer ─────────────────────────────────────────────────────────
  socket.on("timer", (msg) => {
    const r = msg.remaining;
    $timer.textContent = formatTime(r);
    $timer.classList.toggle("warning", r <= 30 && r > 10);
    $timer.classList.toggle("danger", r <= 10);
  });

  // ── Incoming messages ─────────────────────────────────────────────
  socket.on("message", (msg) => {
    addMessage(msg.text, msg.isOwn);
  });

  // ── Prompt card rendering ─────────────────────────────────────────
  function renderPromptCards(choices, highlightIdx) {
    $cards.innerHTML = "";
    if (!isStartingPlayer) {
      const el = document.createElement("div");
      el.className = "idle-screen";
      el.innerHTML =
        '<h1>Drifting Away</h1><p>The other player is choosing a topic<span class="waiting-dots"></span></p>';
      $cards.appendChild(el);
      return;
    }
    // Show a single topic with a hint line underneath
    if (choices.length > 0) {
      const topic = choices[highlightIdx] || choices[0];
      const card = document.createElement("div");
      card.className = "prompt-card highlighted";
      card.textContent = topic.topic;
      card.addEventListener("click", () => {
        socket.send({ action: "select_prompt" });
      });
      $cards.appendChild(card);
      fitText(card, $cards);
    }

    // Hint goes outside the cards container (appended to .prompt-select parent)
    const existingHint = document.querySelector(".prompt-key-hint");
    if (existingHint) existingHint.remove();
    const hint = document.createElement("div");
    hint.className = "prompt-key-hint";
    hint.innerHTML =
      "\u2190 Previous prompt &nbsp;&nbsp;&nbsp; \u25cf Select prompt &nbsp;&nbsp;&nbsp; Generate new prompt \u2192";
    $cards.parentElement.appendChild(hint);
  }

  // ── Auto-fit text size ───────────────────────────────────────────
  function fitText(el, container) {
    // Start at a large size and shrink until it fits
    const maxPx = 72;
    const minPx = 18;
    let size = maxPx;
    el.style.fontSize = size + "px";
    while (
      size > minPx &&
      (el.scrollHeight > container.clientHeight ||
        el.scrollWidth > container.clientWidth)
    ) {
      size -= 2;
      el.style.fontSize = size + "px";
    }
  }

  // ── Message rendering ─────────────────────────────────────────────
  // All message display goes through the queue so the 8-second minimum
  // is always respected — no message can be replaced sooner.

  function _enqueue(renderFn) {
    const now = Date.now();
    const elapsed = now - _lastMessageShown;

    if (_lastMessageShown > 0 && elapsed < MIN_DISPLAY_MS) {
      if (_pendingTimer) clearTimeout(_pendingTimer);
      _pendingMessage = renderFn;
      _pendingTimer = setTimeout(() => {
        _pendingTimer = null;
        _pendingMessage = null;
        renderFn();
        _lastMessageShown = Date.now();
      }, MIN_DISPLAY_MS - elapsed);
      return;
    }

    renderFn();
    _lastMessageShown = Date.now();
  }

  function addMessage(text, isOwn) {
    _enqueue(() => {
      $messages.innerHTML = "";
      const div = document.createElement("div");
      div.className = `message ${isOwn ? "message--own" : "message--other"}`;
      div.textContent = text;
      $messages.appendChild(div);
      fitText(div, $messages);
    });
  }

  function addSystemMessage(text) {
    _enqueue(() => {
      $messages.innerHTML = "";
      const div = document.createElement("div");
      div.className = "message message--system";
      div.textContent = text;
      $messages.appendChild(div);
      fitText(div, $messages);
    });
  }

  function addTopicMessage(topic) {
    _enqueue(() => {
      $messages.innerHTML = "";
      const wrapper = document.createElement("div");
      wrapper.className = "message message--topic";
      const label = document.createElement("div");
      label.className = "topic-label";
      label.textContent = "Original Topic";
      const text = document.createElement("div");
      text.className = "topic-text";
      text.textContent = topic;
      wrapper.appendChild(label);
      wrapper.appendChild(text);
      $messages.appendChild(wrapper);
      fitText(text, $messages);
    });
  }

  function clearMessages() {
    if (_pendingTimer) clearTimeout(_pendingTimer);
    _pendingTimer = null;
    _pendingMessage = null;
    _lastMessageShown = 0;
    $messages.innerHTML = "";
  }

  // ── Reveal rendering ──────────────────────────────────────────────
  function renderReveal(msg) {
    $revealBody.innerHTML = `<p class="subtitle">Take off your earmuffs and talk to each other!</p>`;
  }

  // ── Remote key events (universal keyboard relay) ──────────────────
  // All key presses go: any window → server → correct player via remote_key.
  // This ensures keys work even when this window is not focused.
  socket.on("remote_key", (msg) => {
    const k = msg.keyAction;

    if (msg.eventType === "keydown") {
      const phase = document.querySelector("[data-phase]:not([hidden])")
        ?.dataset.phase;

      // Any key in idle or waiting = mark this player as ready
      if (phase === "idle" || phase === "waiting") {
        socket.send({ action: "player_ready" });
        return;
      }

      if (phase === "prompt_select" && isStartingPlayer) {
        if (k === "prev") socket.send({ action: "prev_prompt" });
        if (k === "select") socket.send({ action: "select_prompt" });
        if (k === "next") socket.send({ action: "reroll_prompt" });
      }

      if (
        phase === "conversation" &&
        k === "select" &&
        !pttActive &&
        micReady
      ) {
        pttActive = true;
        $pttDot.classList.add("active");
        audio.startCapture();
      }
    }

    if (msg.eventType === "keyup") {
      if (k === "select" && pttActive) {
        pttActive = false;
        $pttDot.classList.remove("active");
        audio.stopCapture();
      }
    }
  });
})();
