/**
 * Drifting Away — Spectator Screen Logic
 * Shows both players' original and misheard messages side by side,
 * plus the original prompt. Designed for bystander monitors.
 */

(function () {
  const socket = new DriftSocket("spectator1");

  // ── DOM refs ──────────────────────────────────────────────────────
  const $timer = document.getElementById("timer");
  const $promptBar = document.getElementById("spectator-prompt");
  const $p1Panel = document.getElementById("panel-p1");
  const $p2Panel = document.getElementById("panel-p2");
  const $phase = document.getElementById("spectator-phase");

  // ── Phase handling ────────────────────────────────────────────────
  socket.on("snapshot", applyState);
  socket.on("phase", applyState);

  function applyState(msg) {
    const phase = msg.phase;
    $phase.textContent = phaseLabel(phase);

    if (phase === "idle" || phase === "reset") {
      $timer.classList.remove("visible");
      $promptBar.hidden = true;
      clearPanels();
    }

    if (phase === "prompt_select") {
      $promptBar.hidden = true;
      clearPanels();
      const infoP1 = document.createElement("div");
      infoP1.className = "spectator-turn";
      infoP1.innerHTML = `<div class="misheard">Selecting topic…</div>`;
      $p1Panel.appendChild(infoP1);
    }

    if (phase === "conversation") {
      $timer.classList.add("visible");
      if (msg.prompt) {
        $promptBar.hidden = false;
        $promptBar.querySelector(".prompt-text").textContent = msg.prompt.topic;
      }
    }

    if (phase === "reveal") {
      $timer.classList.remove("visible");
      if (msg.prompt) {
        $promptBar.hidden = false;
        $promptBar.querySelector(".prompt-text").textContent = msg.prompt.topic;
      }
      // Render full history
      if (msg.turns) {
        clearPanels();
        msg.turns.forEach((t) => addTurn(t));
      }
    }
  }

  // ── Timer ─────────────────────────────────────────────────────────
  socket.on("timer", (msg) => {
    const r = msg.remaining;
    $timer.textContent = formatTime(r);
    $timer.classList.toggle("warning", r <= 30 && r > 10);
    $timer.classList.toggle("danger", r <= 10);
  });

  // ── New turn ──────────────────────────────────────────────────────
  socket.on("turn", (msg) => addTurn(msg));

  function addTurn(t) {
    const panel = t.player === 1 ? $p1Panel : $p2Panel;
    const div = document.createElement("div");
    div.className = "spectator-turn";
    div.innerHTML = `
      <div class="original">${escHtml(t.original)}</div>
      <div class="misheard">${escHtml(t.misheard)}</div>
    `;
    panel.appendChild(div);
    panel.scrollTop = panel.scrollHeight;
  }

  function clearPanels() {
    $p1Panel.innerHTML = "";
    $p2Panel.innerHTML = "";
  }

  function phaseLabel(p) {
    const labels = {
      idle: "WAITING FOR PLAYERS",
      prompt_select: "CHOOSING TOPIC",
      conversation: "CONVERSATION IN PROGRESS",
      reveal: "🎉 REVEAL",
      reset: "RESETTING…",
    };
    return labels[p] || p.toUpperCase();
  }

  function escHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
})();
