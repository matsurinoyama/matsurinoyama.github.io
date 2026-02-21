"""
Drifting Away — Installation Configuration
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from the project root so API keys persist across restarts
load_dotenv(Path(__file__).resolve().parent / ".env")

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
PROMPTS_FILE = STATIC_DIR / "prompts.json"

# ── Server ─────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8888

# ── Game ───────────────────────────────────────────────────────────────
ROUND_DURATION_SECONDS = 180          # 3 minutes
PROMPT_CHOICES_COUNT = 3              # how many prompts to show at once
MAX_TRANSCRIPT_HISTORY = 50           # keep last N exchanges in context

# ── Audio ──────────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000                  # 16 kHz mono – Whisper native rate
AUDIO_CHUNK_MS = 10000                # send audio every 10 s to server

# ── Transcription (mlx-whisper on Apple Silicon) ───────────────────────
WHISPER_MODEL = "mlx-community/whisper-small-mlx"   # good speed/quality tradeoff
WHISPER_LANGUAGE = "en"
WHISPER_BEAM_SIZE = 3

# ── Misinterpreter (LLM) ──────────────────────────────────────────────
# Option A — Anthropic API  (set ANTHROPIC_API_KEY env var)  ← default
# Option B — OpenAI API     (set OPENAI_API_KEY env var)
# Option C — Local MLX model via mlx-lm
LLM_BACKEND = os.environ.get("DRIFTING_LLM_BACKEND", "anthropic")  # "anthropic" | "openai" | "local"

# Anthropic settings (default)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_MAX_TOKENS = 256

# OpenAI settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 256

# Local MLX-LM settings (fallback)
LOCAL_LLM_MODEL = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"

# How aggressively the AI should misinterpret (0.0 = faithful, 1.0 = wild)
MISINTERPRET_STRENGTH = 0.83

# ── Key Mapping (USB numpad → actions) ─────────────────────────────────
# The 3 keys on the numpad will emit these keycodes in the browser.
# Default: numpad 1/2/3  (codes: Numpad1, Numpad2, Numpad3)
KEY_PREV   = "Numpad1"      # navigate prompt left  / scroll up
KEY_SELECT = "Numpad2"      # select prompt / push-to-talk (hold)
KEY_NEXT   = "Numpad3"      # navigate prompt right / scroll down
