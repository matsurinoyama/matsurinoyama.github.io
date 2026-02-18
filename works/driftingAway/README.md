# Drifting Away

**An interactive installation where two players have a conversation through AI — but every message is _subtly_ misheard.**

Like a game of telephone, the conversation slowly drifts apart until the players take off their earmuffs and discover they were talking about completely different things.

---

## How It Works

```
┌──────────┐     mic      ┌──────────┐     mic      ┌──────────┐
│ Player 1 │ ──────────▶  │  Server  │  ◀────────── │ Player 2 │
│  Screen  │ ◀── text ──  │  (M2)    │  ── text ──▶ │  Screen  │
└──────────┘              └────┬─────┘              └──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │Spectator │    │Spectator │    │ Control  │
        │ Left     │    │ Right    │    │ Panel    │
        └──────────┘    └──────────┘    └──────────┘
```

### Experience Flow

1. **Idle** — Screens display a waiting state.
2. **Prompt Select** — The starting player picks a conversation topic using a 3-key USB numpad (`[1] Prev`, `[2] Select`, `[3] Next`).
3. **Conversation (3 min)** — Players hold `[2]` to talk (push-to-talk). Speech is transcribed by **Whisper** on Apple Silicon, then an LLM intentionally _misinterprets_ it before showing it to the other player.
4. **Reveal** — Timer ends. Players remove earmuffs and compare what they thought they were discussing.
5. **Reset** — The system clears and waits for the next pair.

Spectator monitors show both the original and misheard versions in real time.

---

## Hardware Setup

| Item                      | Purpose                                |
| ------------------------- | -------------------------------------- |
| Mac Mini M2 Pro           | Runs the server, transcription, and AI |
| 2 × Monitors (players)    | Player screens with conversation UI    |
| 2 × Monitors (spectators) | Bystander view of both sides           |
| 1 × Monitor (optional)    | Control panel for the facilitator      |
| 2 × USB microphones       | One per player                         |
| 2 × Sound-proof earmuffs  | So players can't hear each other       |
| 2 × 3-key USB numpads     | Navigation and push-to-talk            |

---

## Software Setup

### Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3)
- **Python 3.11+**
- An **Anthropic API key** (for the misinterpreter) — or uncomment `openai` or `mlx-lm` in requirements.txt for alternatives

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

### Run

```bash
python server.py
```

Then open these URLs in separate browser windows (one per monitor):

| URL                               | Screen                                  |
| --------------------------------- | --------------------------------------- |
| `http://localhost:8888/`          | Control Panel (facilitator)             |
| `http://localhost:8888/player/1`  | Player 1                                |
| `http://localhost:8888/player/2`  | Player 2                                |
| `http://localhost:8888/spectator` | Spectator (open twice for two monitors) |

> **Tip:** Use Chrome/Edge in kiosk mode for a clean full-screen look:
>
> ```bash
> open -a "Google Chrome" --args --kiosk "http://localhost:8888/player/1"
> ```

---

## Key Mapping (USB Numpad)

The 3-key numpad maps to:

| Key | Code    | Prompt Phase    | Conversation Phase      |
| --- | ------- | --------------- | ----------------------- |
| `1` | Numpad1 | Previous prompt | —                       |
| `2` | Numpad2 | Select prompt   | **Push-to-talk (hold)** |
| `3` | Numpad3 | Next prompt     | —                       |

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
  js/common.js      WebSocket client + key mapping
  js/audio.js       Browser mic capture → PCM-16 → base64
  js/player.js      Player screen controller
  js/spectator.js   Spectator screen controller
  prompts.json      30 conversation topic prompts

templates/
  player.html       Player screen (served per player ID)
  spectator.html    Bystander monitor
  control.html      Facilitator dashboard
```

---

## Tuning

In `config.py`:

| Parameter                | Default             | Description                              |
| ------------------------ | ------------------- | ---------------------------------------- |
| `ROUND_DURATION_SECONDS` | 180                 | Conversation length                      |
| `MISINTERPRET_STRENGTH`  | 0.45                | 0 = faithful, 1 = wild misinterpretation |
| `WHISPER_MODEL`          | `whisper-small-mlx` | Speed vs accuracy tradeoff               |
| `AUDIO_CHUNK_MS`         | 3000                | How often audio is sent to server        |
| `SILENCE_THRESHOLD_DB`   | -40                 | Skip transcription below this level      |

---

## License

Part of the matsurinoyama portfolio.
