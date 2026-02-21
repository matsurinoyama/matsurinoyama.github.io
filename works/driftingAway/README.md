# 離れていく — Drifting Away

**An interactive installation where two players have a conversation through AI — but every message is _subtly_ misheard.**

🌐 **Now fully bilingual:** Japanese (default) with instant switching to English via **'A' key** or control panel buttons.

Like a game of telephone, the conversation slowly drifts apart until the players take off their earmuffs and discover they were talking about completely different things.

---

## How It Works

```
┌──────────┐     mic      ┌──────────┐     mic      ┌──────────┐
│ Player 1 │ ──────────▶  │  Server  │  ◀────────── │ Player 2 │
│  Screen  │ ◀── text ──  │  (M2)    │  ── text ──▶ │  Screen  │
└──────────┘              └────┬─────┘              └──────────┘
                               │
                               ▼
                         ┌──────────┐
                         │Spectator │
                         │  Screen  │
                         └──────────┘
```

### Experience Flow

1. **Idle** — Screens display a waiting state (in Japanese by default).
2. **Prompt Select** — The starting player picks a conversation topic using a 3-key USB numpad (`[1] Prev`, `[2] Select`, `[3] Next`). Topics are in the current language.
3. **Conversation (3 min)** — Players hold `[2]` to talk (push-to-talk). Speech is transcribed by **Whisper** on Apple Silicon in the active language, then an LLM intentionally _misinterprets_ it before showing it to the other player.
4. **Reveal** — Timer ends. Players remove earmuffs and compare what they thought they were discussing.
5. **Reset** — The system clears and waits for the next pair.

### Language Switching

- **Press 'A'** on any screen to toggle between 日本語 (Japanese) ↔ English
- **Control panel buttons** (🌐 言語) switch language for all connected screens simultaneously
- Language affects: UI text, conversation prompts, speech recognition, and AI misinterpretation instructions

Spectator monitors show both the original and misheard versions in real time.

---

## Hardware Setup

| Item                     | Purpose                                |
| ------------------------ | -------------------------------------- |
| Mac Mini M2 Pro          | Runs the server, transcription, and AI |
| 2 × Monitors (players)   | Player screens with conversation UI    |
| 1 × Monitor (spectator)  | Bystander view of both sides           |
| 2 × USB microphones      | One per player                         |
| 2 × Sound-proof earmuffs | So players can't hear each other       |
| 2 × 3-key USB numpads    | Navigation and push-to-talk            |

---

## Software Setup

### Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3)
- **Python 3.11+**
- An **Anthropic API key** (for the misinterpreter) — or uncomment `openai` or `mlx-lm` in requirements.txt for alternatives
- **Modern browser** (Chrome/Edge/Safari) with WebSocket and Web Audio API support

### Install

```bash
cd works/driftingAway

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure

Edit the `.env` file in the project root (auto-loaded on startup, git-ignored):

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: switch to OpenAI or local LLM
# DRIFTING_LLM_BACKEND=openai
# OPENAI_API_KEY=sk-...
```

The application starts in **Japanese by default**. Change in `config.py`:

```python
DEFAULT_LANGUAGE = "ja"  # "ja" or "en"
```

### Run

```bash
python server.py
```

Then open these URLs in separate browser windows (one per monitor):

| URL                               | Screen    |
| --------------------------------- | --------- |
| `http://localhost:8888/player/1`  | Player 1  |
| `http://localhost:8888/player/2`  | Player 2  |
| `http://localhost:8888/spectator` | Spectator |

> **Tip:** Use Chrome/Edge in kiosk mode for a clean full-screen look:
>
> ```bash
> open -a "Google Chrome" --args --kiosk "http://localhost:8888/player/1"
> ```

---

## Key Mapping

### USB Numpad (Navigation & PTT)

The 3-key numpad maps to:

| Key | Code    | Prompt Phase    | Conversation Phase      |
| --- | ------- | --------------- | ----------------------- |
| `1` | Numpad1 | Previous prompt | —                       |
| `2` | Numpad2 | Select prompt   | **Push-to-talk (hold)** |
| `3` | Numpad3 | Next prompt     | —                       |

### Global Keyboard

| Key | Function        |
| --- | --------------- |
| `A` | Toggle language |

(Toggles between Japanese ↔ English across all connected screens)

Regular number keys (`1`, `2`, `3`) also work as fallbacks.

---

## Architecture

```
server.py           FastAPI + WebSocket orchestrator
game_engine.py      State machine (idle → prompt → convo → reveal → reset)
transcription.py    mlx-whisper (Apple Silicon) speech-to-text
misinterpreter.py   LLM-powered "telephone game" text mangling
config.py           All tunable parameters

static/
  css/styles.css    Dark-themed installation UI
  js/i18n.js        Internationalization (Japanese + English strings)
  js/common.js      WebSocket client + key mapping + language relay
  js/audio.js       Browser mic capture → PCM-16 → base64
  js/player.js      Player screen controller (uses i18n)
  js/spectator.js   Spectator screen controller (uses i18n)
  prompts.json      100 English conversation topics
  prompts_ja.json   100 Japanese conversation topics

templates/
  player.html       Player screen (served per player ID)
  spectator.html    Bystander monitor
  control.html      Facilitator dashboard
```

---

## Tuning

In `config.py`:

| Parameter                | Default             | Description                                             |
| ------------------------ | ------------------- | ------------------------------------------------------- |
| `DEFAULT_LANGUAGE`       | `"ja"`              | Default UI language ("ja" or "en")                      |
| `ROUND_DURATION_SECONDS` | 180                 | Conversation length (seconds)                           |
| `MISINTERPRET_STRENGTH`  | 0.7                 | 0 = faithful, 1 = wild misinterpretation                |
| `WHISPER_LANGUAGE`       | `"ja"`              | Default speech-to-text language (overridden by UI lang) |
| `WHISPER_MODEL`          | `whisper-small-mlx` | Speed vs accuracy tradeoff                              |
| `AUDIO_CHUNK_MS`         | 10000               | How often audio is sent to server (ms)                  |
| `MIN_DISPLAY_MS`         | 6000                | Minimum message display time on player screens (ms)     |

---

## Internationalization (i18n)

The entire installation is bilingual:

- **UI strings** in `static/js/i18n.js` — all player/spectator/control panel text
- **Conversation topics** in `prompts.json` (English) and `prompts_ja.json` (Japanese)
- **Speech recognition** — Whisper automatically uses the active language
- **Misinterpretation** — Claude receives language-specific instructions (with Japanese drift examples)
- **Real-time switching** — 'A' key broadcasts language change to all clients via WebSocket

Add new languages by extending `i18n.js` and creating a new `prompts_xx.json` file.

---

## License

Part of the matsurinoyama portfolio.
