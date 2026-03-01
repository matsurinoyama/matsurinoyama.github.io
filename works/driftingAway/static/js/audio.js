/**
 * Drifting Away — Audio Capture
 * Captures microphone audio via Web Audio API, converts to PCM-16,
 * and sends base64-encoded chunks to the server while PTT is held.
 * Supports selecting a specific audio input device per player.
 */

class AudioCapture {
  constructor(socket, chunkMs = 3000) {
    this.socket = socket;
    this.chunkMs = chunkMs;
    this.stream = null;
    this.context = null;
    this.processor = null;
    this.isCapturing = false;
    this._buffer = [];
    this._sendInterval = null;
    this._initialized = false;
    this._deviceId = null; // specific mic device ID
  }

  /**
   * Enumerate available audio input devices.
   * Must be called after at least one getUserMedia grant so labels are visible.
   */
  static async getAudioDevices() {
    // Request temporary permission so device labels become available
    try {
      const tempStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      tempStream.getTracks().forEach((t) => t.stop());
    } catch (e) {
      console.warn("[Audio] Mic permission denied during enumeration:", e);
      return [];
    }

    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter((d) => d.kind === "audioinput");
  }

  /**
   * Set the device ID to use. Call before init().
   * If null/undefined, uses the system default.
   */
  setDevice(deviceId) {
    this._deviceId = deviceId;
    // If already initialized, re-init with the new device
    if (this._initialized) {
      this._initialized = false;
      if (this.processor) this.processor.disconnect();
      if (this.context) this.context.close();
      if (this.stream) this.stream.getTracks().forEach((t) => t.stop());
      this.processor = null;
      this.context = null;
      this.stream = null;
    }
  }

  async init() {
    if (this._initialized) return;

    const audioConstraints = {
      channelCount: 1,
      sampleRate: 16000,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    };

    // Use specific device if set
    if (this._deviceId) {
      audioConstraints.deviceId = { exact: this._deviceId };
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: audioConstraints,
      });

      // Log which device we actually got
      const track = this.stream.getAudioTracks()[0];
      console.log("[Audio] Using device:", track.label || "Unknown");

      this.context = new AudioContext({ sampleRate: 16000 });
      const source = this.context.createMediaStreamSource(this.stream);

      // Use ScriptProcessorNode (widely supported) or AudioWorklet
      // ScriptProcessorNode is deprecated but universally available
      this.processor = this.context.createScriptProcessor(4096, 1, 1);
      this.processor.onaudioprocess = (e) => {
        if (!this.isCapturing) return;
        const float32 = e.inputBuffer.getChannelData(0);
        // Convert Float32 → Int16 PCM
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
          const s = Math.max(-1, Math.min(1, float32[i]));
          int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        this._buffer.push(int16);
      };

      source.connect(this.processor);
      this.processor.connect(this.context.destination);

      this._initialized = true;
      console.log("[Audio] Initialized — 16 kHz mono PCM");
    } catch (err) {
      console.error("[Audio] Mic access denied or unavailable:", err);
    }
  }

  startCapture() {
    if (!this._initialized || this.isCapturing) return;
    this.isCapturing = true;
    this._buffer = [];

    // Send a chunk every 10 seconds while PTT is held
    if (this._sendInterval) clearInterval(this._sendInterval);
    this._sendInterval = setInterval(() => this._flush(), 10000);
  }

  stopCapture() {
    this.isCapturing = false;
    if (this._sendInterval) {
      clearInterval(this._sendInterval);
      this._sendInterval = null;
    }
    // Flush any remaining audio
    this._flush();
  }

  _flush() {
    if (this._buffer.length === 0) return;

    // Concatenate all buffered chunks
    const totalLen = this._buffer.reduce((acc, a) => acc + a.length, 0);
    const merged = new Int16Array(totalLen);
    let offset = 0;
    for (const chunk of this._buffer) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }
    this._buffer = [];

    // Convert to base64 — chunked to avoid call-stack overflow
    const bytes = new Uint8Array(merged.buffer);
    const b64 = this._arrayBufferToBase64(bytes);

    this.socket.send({
      action: "audio_chunk",
      audio: b64,
    });
  }

  /** Safe base64 encoding that works with large buffers. */
  _arrayBufferToBase64(bytes) {
    const CHUNK = 0x8000; // 32 KB per chunk — safe for String.fromCharCode
    const parts = [];
    for (let i = 0; i < bytes.length; i += CHUNK) {
      parts.push(String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK)));
    }
    return btoa(parts.join(""));
  }

  destroy() {
    this.stopCapture();
    if (this.processor) this.processor.disconnect();
    if (this.context) this.context.close();
    if (this.stream) this.stream.getTracks().forEach((t) => t.stop());
  }
}
