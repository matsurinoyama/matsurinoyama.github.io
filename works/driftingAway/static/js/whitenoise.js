/**
 * Drifting Away — White Noise Generator
 *
 * Generates white noise via the Web Audio API (no external file needed).
 * Provides start/stop with a gentle fade so it's not jarring.
 *
 * Usage:
 *   const wn = new WhiteNoise();   // created once
 *   wn.start();                     // fade in  (conversation begins)
 *   wn.stop();                      // fade out (reveal / reset)
 */

// eslint-disable-next-line no-unused-vars
class WhiteNoise {
  /**
   * @param {object}  opts
   * @param {number}  opts.volume   – 0-1, default 0.15 (subtle)
   * @param {number}  opts.fadeMs   – fade in/out duration in ms (default 1500)
   */
  constructor({ volume = 0.15, fadeMs = 1500 } = {}) {
    this._volume = volume;
    this._fadeSec = fadeMs / 1000;
    this._ctx = null;
    this._gain = null;
    this._source = null;
    this._running = false;
  }

  /** Lazily create or resume the AudioContext (must follow a user gesture). */
  _ensureContext() {
    if (!this._ctx) {
      this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (this._ctx.state === "suspended") {
      this._ctx.resume();
    }
  }

  /** Build a looping AudioBuffer filled with white noise. */
  _createNoiseBuffer() {
    const sr = this._ctx.sampleRate;
    const len = sr * 2; // 2-second loop
    const buf = this._ctx.createBuffer(1, len, sr);
    const data = buf.getChannelData(0);
    for (let i = 0; i < len; i++) {
      data[i] = Math.random() * 2 - 1; // uniform white noise
    }
    return buf;
  }

  /** Start white noise with a gentle fade-in. */
  start() {
    if (this._running) return;
    this._ensureContext();

    const buf = this._createNoiseBuffer();
    this._source = this._ctx.createBufferSource();
    this._source.buffer = buf;
    this._source.loop = true;

    this._gain = this._ctx.createGain();
    this._gain.gain.setValueAtTime(0, this._ctx.currentTime);
    this._gain.gain.linearRampToValueAtTime(
      this._volume,
      this._ctx.currentTime + this._fadeSec,
    );

    this._source.connect(this._gain);
    this._gain.connect(this._ctx.destination);
    this._source.start();
    this._running = true;
  }

  /** Stop white noise with a gentle fade-out, then disconnect. */
  stop() {
    if (!this._running || !this._gain) return;

    const now = this._ctx.currentTime;
    this._gain.gain.cancelScheduledValues(now);
    this._gain.gain.setValueAtTime(this._gain.gain.value, now);
    this._gain.gain.linearRampToValueAtTime(0, now + this._fadeSec);

    // Clean up after fade completes
    const src = this._source;
    setTimeout(
      () => {
        try {
          src.stop();
          src.disconnect();
        } catch (_) {
          /* already stopped */
        }
      },
      this._fadeSec * 1000 + 100,
    );

    this._source = null;
    this._gain = null;
    this._running = false;
  }
}
