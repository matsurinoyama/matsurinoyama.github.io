"""
Drifting Away — Transcription Engine
Uses mlx-whisper for fast on-device speech-to-text on Apple Silicon.
Falls back to openai/whisper if mlx-whisper is unavailable.
"""

from __future__ import annotations

import io
import logging
import tempfile
import wave
from pathlib import Path

import numpy as np

from config import WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_BEAM_SIZE, SAMPLE_RATE

log = logging.getLogger("drifting.transcription")

# ── Lazy-load the model once ──────────────────────────────────────────
_model_loaded: bool = False
_backend: str = "none"


def _ensure_model():
    """Load the Whisper model on first call. mlx-whisper keeps its own
    global cache, so we just need to trigger a transcribe once or let
    it download on first use."""
    global _model_loaded, _backend
    if _model_loaded:
        return

    try:
        import mlx_whisper  # noqa: F401
        _backend = "mlx"
        log.info("Using mlx-whisper with model %s", WHISPER_MODEL)
    except ImportError:
        try:
            import whisper  # noqa: F401
            _backend = "openai"
            log.info("mlx-whisper not found; falling back to openai/whisper")
        except ImportError:
            log.error("No whisper backend available! Install mlx-whisper or openai-whisper.")
            _backend = "none"

    _model_loaded = True


# ── Public API ─────────────────────────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes, language: str | None = None) -> str:
    """
    Accepts raw PCM-16 mono audio at SAMPLE_RATE and returns text.
    The audio comes from the browser via MediaRecorder → WAV.
    If *language* is given it overrides the config default (e.g. "ja" or "en").
    """
    _ensure_model()

    if _backend == "none":
        return "[transcription unavailable]"

    lang = language or WHISPER_LANGUAGE

    # Write a temporary WAV so the whisper libs can ingest it
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    try:
        _write_wav(tmp.name, audio_bytes)
        text = _run_transcription(tmp.name, lang)
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    return text.strip()


def _write_wav(path: str, pcm_bytes: bytes):
    """Wrap raw PCM-16 in a WAV container."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)


def _run_transcription(wav_path: str, language: str = "ja") -> str:
    if _backend == "mlx":
        return _transcribe_mlx(wav_path, language)
    elif _backend == "openai":
        return _transcribe_openai_whisper(wav_path, language)
    return ""


def _transcribe_mlx(wav_path: str, language: str = "ja") -> str:
    import mlx_whisper

    result = mlx_whisper.transcribe(
        wav_path,
        path_or_hf_repo=WHISPER_MODEL,
        language=language,
        fp16=True,
        verbose=False,
    )
    return result.get("text", "")


def _transcribe_openai_whisper(wav_path: str, language: str = "ja") -> str:
    import whisper

    model = whisper.load_model("small")
    result = model.transcribe(
        wav_path,
        language=language,
        beam_size=WHISPER_BEAM_SIZE,
        fp16=False,
    )
    return result.get("text", "")


# ── Utility ────────────────────────────────────────────────────────────

def pcm_rms_db(pcm_bytes: bytes) -> float:
    """Return RMS in dB for a chunk of PCM-16 audio."""
    samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
    if len(samples) == 0:
        return -100.0
    rms = np.sqrt(np.mean(samples ** 2))
    if rms < 1:
        return -100.0
    return 20 * np.log10(rms / 32768.0)
