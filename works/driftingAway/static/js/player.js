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
  const $pttDot = document.getElementById("ptt-indicator");
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

    if (phase === "prompt_select") {
      isStartingPlayer = msg.startingPlayer === PLAYER_ID;
      const idx = msg.highlightIndex !== undefined ? msg.highlightIndex : 0;
      renderPromptCards(msg.choices || msg.promptChoices || [], idx);
    }

    if (phase === "conversation") {
      $timer.classList.add("visible");
      // Audio is already initialized from mic setup
      if (msg.prompt) {
        addSystemMessage(`Topic: "${msg.prompt.topic}"`);
      }
    }

    if (phase === "reveal") {
      $timer.classList.remove("visible");
      renderReveal(msg);
    }

    if (phase === "reset" || phase === "idle") {
      clearMessages();
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
      el.className = "message--system";
      el.style.padding = "2rem";
      el.style.fontSize = "1.2rem";
      el.textContent = "The other player is choosing a topic…";
      $cards.appendChild(el);
      return;
    }
    // Show a single topic with instructions
    if (choices.length > 0) {
      const topic = choices[highlightIdx] || choices[0];
      const card = document.createElement("div");
      card.className = "prompt-card highlighted";
      card.textContent = topic.topic;
      card.addEventListener("click", () => {
        socket.send({ action: "select_prompt" });
      });
      $cards.appendChild(card);

      const hint = document.createElement("div");
      hint.className = "message--system";
      hint.style.marginTop = "1.5rem";
      hint.style.fontSize = "0.9rem";
      hint.innerHTML =
        "Press <strong>[2]</strong> to start &nbsp;·&nbsp; <strong>[3]</strong> for a different topic";
      $cards.appendChild(hint);
    }
  }

  // ── Message rendering ─────────────────────────────────────────────
  function addMessage(text, isOwn) {
    const div = document.createElement("div");
    div.className = `message ${isOwn ? "message--own" : "message--other"}`;
    div.textContent = text;
    $messages.appendChild(div);
    $messages.scrollTop = $messages.scrollHeight;
  }

  function addSystemMessage(text) {
    const div = document.createElement("div");
    div.className = "message message--system";
    div.textContent = text;
    $messages.appendChild(div);
  }

  function clearMessages() {
    $messages.innerHTML = "";
  }

  // ── Reveal rendering ──────────────────────────────────────────────
  function renderReveal(msg) {
    let html = "";
    if (msg.prompt) {
      html += `<div class="original-prompt">
        <div class="label">Original Topic</div>
        <div>${msg.prompt.topic}</div>
      </div>`;
    }
    html += `<p class="subtitle">Take off your earmuffs and compare notes!</p>`;
    $revealBody.innerHTML = html;
  }

  // ── Keyboard input ────────────────────────────────────────────────
  document.addEventListener("keydown", (e) => {
    const k = mapKey(e.code);
    if (!k) return;
    e.preventDefault();

    const phase = document.querySelector("[data-phase]:not([hidden])")?.dataset
      .phase;

    // Any numpad key starts the game from idle
    if (phase === "idle") {
      socket.send({ action: "start_game" });
      return;
    }

    if (phase === "prompt_select" && isStartingPlayer) {
      if (k === "select") socket.send({ action: "select_prompt" });
      if (k === "next") socket.send({ action: "reroll_prompt" });
    }

    if (phase === "conversation" && k === "select" && !pttActive && micReady) {
      pttActive = true;
      $pttDot.classList.add("active");
      $pttLabel.textContent = "Recording…";
      audio.startCapture();
    }
  });

  document.addEventListener("keyup", (e) => {
    const k = mapKey(e.code);
    if (k === "select" && pttActive) {
      pttActive = false;
      $pttDot.classList.remove("active");
      $pttLabel.textContent = "Hold [2] to talk";
      audio.stopCapture();
    }
  });
})();
