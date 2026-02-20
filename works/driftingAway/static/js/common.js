/**
 * Drifting Away — Common utilities
 * Shared WebSocket connection, state management, key config.
 */

// Per-player key bindings
// Player 1: I / O / P   |   Player 2: J / K / L
const PLAYER_KEYS = {
  1: { prev: ["KeyI"], select: ["KeyO"], next: ["KeyP"] },
  2: { prev: ["KeyJ"], select: ["KeyK"], next: ["KeyL"] },
};

// Human-readable labels for UI hints (physical keycap symbols)
const PLAYER_KEY_LABELS = {
  1: { prev: "←", select: "⚪", next: "→" },
  2: { prev: "←", select: "⚪", next: "→" },
};

class DriftSocket {
  static _keyRelaySocket = null;

  constructor(role) {
    this.role = role;
    this.ws = null;
    this.handlers = {};
    this.reconnectDelay = 1000;
    this._connect();
    this._registerKeyRelay();
  }

  /**
   * Auto-register universal keyboard relay on the first DriftSocket
   * created on this page. Any recognised player key press is sent to
   * the server which forwards it to the correct player window.
   */
  _registerKeyRelay() {
    if (DriftSocket._keyRelaySocket) return;
    DriftSocket._keyRelaySocket = this;

    document.addEventListener("keydown", (e) => {
      const mapped = mapKeyUniversal(e.code);
      if (!mapped) return;
      e.preventDefault();
      DriftSocket._keyRelaySocket.send({
        action: "relay_key",
        targetPlayer: mapped.player,
        keyAction: mapped.action,
        eventType: "keydown",
      });
    });

    document.addEventListener("keyup", (e) => {
      const mapped = mapKeyUniversal(e.code);
      if (!mapped) return;
      e.preventDefault();
      DriftSocket._keyRelaySocket.send({
        action: "relay_key",
        targetPlayer: mapped.player,
        keyAction: mapped.action,
        eventType: "keyup",
      });
    });
  }

  _connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/ws/${this.role}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`[WS] Connected as ${this.role}`);
      this.reconnectDelay = 1000;
      this._emit("connected");
    };

    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        this._emit(msg.type || "message", msg);
      } catch (err) {
        console.error("[WS] Parse error", err);
      }
    };

    this.ws.onclose = () => {
      console.warn(
        `[WS] Disconnected. Reconnecting in ${this.reconnectDelay}ms…`,
      );
      setTimeout(() => this._connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 10000);
    };

    this.ws.onerror = (err) => console.error("[WS] Error", err);
  }

  on(type, handler) {
    if (!this.handlers[type]) this.handlers[type] = [];
    this.handlers[type].push(handler);
    return this;
  }

  _emit(type, data) {
    (this.handlers[type] || []).forEach((fn) => fn(data));
  }

  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }
}

// ── Timer formatting ──────────────────────────────────────────────────
function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ── Phase visibility helper ───────────────────────────────────────────
function showPhase(phaseId) {
  document.querySelectorAll("[data-phase]").forEach((el) => {
    el.hidden = el.dataset.phase !== phaseId;
  });
}

// ── Key mapping helper ────────────────────────────────────────────────
function mapKey(code, playerId) {
  const keys = playerId ? PLAYER_KEYS[playerId] : null;
  if (!keys) return null;
  if (keys.prev.includes(code)) return "prev";
  if (keys.select.includes(code)) return "select";
  if (keys.next.includes(code)) return "next";
  return null;
}

// ── Universal key mapping (any key → {player, action}) ───────────────
function mapKeyUniversal(code) {
  for (const pid of [1, 2]) {
    const keys = PLAYER_KEYS[pid];
    if (keys.prev.includes(code)) return { player: pid, action: "prev" };
    if (keys.select.includes(code)) return { player: pid, action: "select" };
    if (keys.next.includes(code)) return { player: pid, action: "next" };
  }
  return null;
}
