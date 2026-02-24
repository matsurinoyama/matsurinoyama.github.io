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
  let $pttDot = document.getElementById("ptt-dot");
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
        '<p class="mic-loading">' + i18n.t("mic.noMics") + "</p>";
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
        $micTestBtn.textContent = i18n.t("mic.stopTest");
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
    if ($micTestBtn) $micTestBtn.textContent = i18n.t("mic.test");
  }

  // Start mic setup immediately
  initMicSetup();

  // ══════════════════════════════════════════════════════════════════
  // GAME LOGIC
  // ══════════════════════════════════════════════════════════════════

  // ── Phase handling ────────────────────────────────────────────────
  socket.on("snapshot", (msg) => applyState(msg));
  socket.on("phase", (msg) => applyState(msg));

  // ── Language change ─────────────────────────────────────────────
  socket.on("language_change", (msg) => {
    i18n.setLang(msg.language);
    document.documentElement.lang = msg.language;
    document.title = i18n.t("title.player") + " — " + PLAYER_ID;
    refreshStaticText();
  });
  socket.on("snapshot", (msg) => {
    if (msg.language) {
      i18n.setLang(msg.language);
      document.documentElement.lang = msg.language;
      document.title = i18n.t("title.player") + " — " + PLAYER_ID;
      refreshStaticText();
    }
  });

  /** Update all static text elements with current i18n strings */
  function refreshStaticText() {
    // Idle screen
    const idleScreen = document.querySelector(
      '[data-phase="idle"] .idle-screen',
    );
    if (idleScreen) {
      idleScreen.querySelector("h1").textContent = i18n.t("idle.title");
      idleScreen.querySelectorAll("p")[0].textContent =
        i18n.t("idle.putOnEarmuffs");
      const instrP = idleScreen.querySelector(".idle-instruction");
      if (instrP) instrP.textContent = i18n.t("idle.pressButton");
    }
    // Reset screen
    const resetScreen = document.querySelector(
      '[data-phase="reset"] .idle-screen',
    );
    if (resetScreen) {
      resetScreen.querySelector("h1").textContent = i18n.t("reset.title");
      const p = resetScreen.querySelector("p");
      if (p)
        p.innerHTML =
          i18n.t("reset.preparing") + '<span class="waiting-dots"></span>';
    }
    // Reveal
    const revealH2 = document.querySelector('[data-phase="reveal"] h2');
    if (revealH2) revealH2.textContent = i18n.t("reveal.title");
    // PTT label
    if ($pttLabel) {
      $pttLabel.innerHTML =
        i18n.t("ptt.label") + ' <span class="ptt-dot" id="ptt-dot"></span>';
      // Re-bind dot ref — the old $pttDot is now detached from the DOM
      $pttDot = document.getElementById("ptt-dot");
      if ($pttDot && pttActive) $pttDot.classList.add("active");
    }
    // Mic setup
    const micTitle = document.querySelector(".mic-setup-card h2");
    if (micTitle) micTitle.textContent = i18n.t("mic.title");
    const micSub = document.querySelector(".mic-setup-sub");
    if (micSub) micSub.textContent = i18n.t("mic.selectFor", { id: PLAYER_ID });
    const micHint = document.querySelector(".mic-setup-hint");
    if (micHint) micHint.textContent = i18n.t("mic.hint", { id: PLAYER_ID });
    if ($micTestBtn && !_testStream)
      $micTestBtn.textContent = i18n.t("mic.test");
    if ($micConfirmBtn) $micConfirmBtn.textContent = i18n.t("mic.confirm");
  }

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
            i18n.t("waiting.forOther") + '<span class="waiting-dots"></span>';
        } else {
          // The other player is already waiting for us
          $waitText.innerHTML =
            i18n.t("waiting.otherReady") + '<span class="waiting-dots"></span>';
        }
      }
      // Update waiting title
      const waitH1 = document.querySelector('[data-phase="waiting"] h1');
      if (waitH1) waitH1.textContent = i18n.t("waiting.title");
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
        "<h1>" +
        i18n.t("idle.title") +
        "</h1><p>" +
        i18n.t("prompt.otherChoosing") +
        '<span class="waiting-dots"></span></p>';
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
    hint.innerHTML = i18n.t("prompt.hint");
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
      label.textContent = i18n.t("topic.label");
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
    $revealBody.innerHTML = `<p class="subtitle">${i18n.t(
      "reveal.subtitle",
    )}</p>`;
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
