"""
Drifting Away — FastAPI Server
Orchestrates the installation: serves screens, handles WebSocket
connections for real-time audio / game state, and coordinates the
game engine, transcription, and misinterpreter modules.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from collections import Counter
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from config import (
    HOST,
    PORT,
    STATIC_DIR,
    TEMPLATES_DIR,
    ROUND_DURATION_SECONDS,
    DEFAULT_LANGUAGE,
)
from game_engine import GameState, Phase
from transcription import transcribe_audio
from misinterpreter import misinterpret

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
)
log = logging.getLogger("drifting.server")

# ── Global state ───────────────────────────────────────────────────────
game = GameState()

# Active language — "ja" (default) or "en", switchable at runtime
current_language: str = DEFAULT_LANGUAGE

# Connections keyed by role: "player1", "player2", "spectator1", "spectator2"
connections: dict[str, WebSocket] = {}

# Lock to serialise audio processing (one at a time)
audio_lock = asyncio.Lock()


# ── Broadcast helpers ──────────────────────────────────────────────────

async def broadcast(msg: dict):
    """Send a JSON message to every connected client."""
    data = json.dumps(msg)
    dead: list[str] = []
    for role, ws in connections.items():
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(role)
    for r in dead:
        connections.pop(r, None)


async def send_to(role: str, msg: dict):
    ws = connections.get(role)
    if ws:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            connections.pop(role, None)


# ── Game-engine callbacks ─────────────────────────────────────────────

async def on_phase_change(phase: Phase, extra: dict):
    log.info("Phase → %s  %s", phase.value, list(extra.keys()))
    await broadcast({"type": "phase", "phase": phase.value, **extra})


async def on_timer_tick(remaining: float):
    await broadcast({"type": "timer", "remaining": round(remaining, 1)})


game.on_phase_change(on_phase_change)
game.on_timer_tick(on_timer_tick)


# ── App lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Drifting Away server starting on %s:%s", HOST, PORT)
    yield
    log.info("Shutting down…")


app = FastAPI(title="Drifting Away", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Inject a cache-busting timestamp into all templates
import time as _time
templates.env.globals["cache_bust"] = str(int(_time.time()))


# ── HTTP routes ───────────────────────────────────────────────────────

@app.get("/player/{player_id}", response_class=HTMLResponse)
async def player_screen(request: Request, player_id: int):
    return templates.TemplateResponse(
        "player.html",
        {"request": request, "player_id": player_id},
    )


@app.get("/spectator", response_class=HTMLResponse)
async def spectator_screen(request: Request):
    return templates.TemplateResponse(
        "spectator.html",
        {"request": request},
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "control.html",
        {"request": request},
    )


# ── WebSocket endpoint ───────────────────────────────────────────────

@app.websocket("/ws/{role}")
async def websocket_endpoint(ws: WebSocket, role: str):
    """
    Roles: player1, player2, spectator1, spectator2, control
    """
    await ws.accept()
    connections[role] = ws
    log.info("Connected: %s  (total: %d)", role, len(connections))

    # Send current snapshot so late-joiners sync up
    await ws.send_text(json.dumps({
        "type": "snapshot",
        "language": current_language,
        **game.snapshot(),
    }))

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            await handle_message(role, msg)
    except WebSocketDisconnect:
        connections.pop(role, None)
        log.info("Disconnected: %s", role)
    except Exception as e:
        connections.pop(role, None)
        log.error("WebSocket error (%s): %s", role, e)


# ── Message dispatcher ───────────────────────────────────────────────

async def handle_message(role: str, msg: dict):
    action = msg.get("action")

    if action == "relay_key":
        # Universal key relay: forward key event to the target player's connection
        target_player = msg.get("targetPlayer")
        key_action = msg.get("keyAction")
        event_type = msg.get("eventType")
        target_role = f"player{target_player}"
        target_ws = connections.get(target_role)
        if target_ws:
            await target_ws.send_text(json.dumps({
                "type": "remote_key",
                "keyAction": key_action,
                "eventType": event_type,
            }))

    elif action == "player_ready":
        # Extract player number from role ("player1" → 1, "player2" → 2)
        if role.startswith("player"):
            player_num = int(role[-1])
            await game.player_ready(player_num)
        elif role == "control":
            # Control panel can force-start by readying both
            await game.player_ready(1)
            await game.player_ready(2)

    elif action == "start_game":
        # Legacy / control panel fallback
        if game.phase == Phase.IDLE:
            await game.player_ready(1)
            await game.player_ready(2)

    elif action == "nav_prompt":
        direction = msg.get("direction", 1)
        await game.navigate_prompt(direction)

    elif action == "select_prompt":
        await game.confirm_prompt()

    elif action == "set_prompt_index":
        index = msg.get("index", 0)
        await game.set_prompt_index(index)

    elif action == "reroll_prompt":
        await game.reroll_prompt()

    elif action == "prev_prompt":
        await game.prev_prompt()

    elif action == "audio_chunk":
        await process_audio(role, msg)

    elif action == "force_reveal":
        if game.phase == Phase.CONVERSATION:
            await game.enter_reveal()

    elif action == "reset":
        await game.reset()

    elif action == "skip_to_conversation":
        # Debug shortcut
        if game.phase == Phase.PROMPT_SELECT:
            await game.confirm_prompt()

    elif action == "set_language":
        global current_language
        lang = msg.get("language", "ja")
        if lang in ("ja", "en") and lang != current_language:
            current_language = lang
            log.info("Language changed to: %s", lang)
            # Reload prompts for the new language
            game.set_language(lang)
            # Broadcast to all clients
            await broadcast({"type": "language_change", "language": lang})


# ── Audio processing pipeline ────────────────────────────────────────

async def process_audio(role: str, msg: dict):
    """
    Receives a base64-encoded PCM-16 audio chunk from a player,
    transcribes it, misinterprets it, and sends the result.

    All errors are caught and logged so they never crash the WebSocket.
    """
    if game.phase != Phase.CONVERSATION:
        return

    # Determine which player sent audio
    player_num = 1 if "1" in role else 2
    other_player = 2 if player_num == 1 else 1

    audio_b64 = msg.get("audio", "")
    if not audio_b64:
        return

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        log.warning("P%d sent invalid base64 audio: %s", player_num, e)
        return

    async with audio_lock:
        try:
            # 1. Transcribe (use current language for whisper)
            original_text = await transcribe_audio(audio_bytes, language=current_language)
            if not original_text.strip():
                return


            # Skip fragments too short to be meaningful
            # For Japanese: < 4 characters; for English: < 3 words
            if current_language == "ja":
                if len(original_text.strip()) < 4:
                    log.debug("P%d: ignoring short fragment (%d chars): %s",
                              player_num, len(original_text.strip()), original_text.strip())
                    return
                # Filter out polite stock phrases (treat as silence)
                polite_stock = [
                    "ご視聴ありがとうございました", "ご利用ありがとうございました", "ありがとうございました", "ご清聴ありがとうございました",
                    "ご参加ありがとうございました", "ご来場ありがとうございました", "ご協力ありがとうございました", "ご注文ありがとうございました",
                    "ご愛顧ありがとうございました", "ご予約ありがとうございました", "ご回答ありがとうございました", "ご応募ありがとうございました",
                    "ご連絡ありがとうございました", "ご報告ありがとうございました", "ご指摘ありがとうございました", "ご案内ありがとうございました",
                ]
                if original_text.strip() in polite_stock:
                    log.debug("P%d: ignoring polite stock phrase: %s", player_num, original_text.strip())
                    return
            else:
                words = original_text.strip().split()
                if len(words) < 3:
                    log.debug("P%d: ignoring short fragment (%d words): %s",
                              player_num, len(words), original_text.strip())
                    return

            # Skip repetitive/spam input (audio glitch: same token repeated)
            text_clean = original_text.strip()
            if current_language == "ja":
                # Japanese: check for repeated characters (no spaces)
                # A single char repeated more than 60% of the text = glitch
                char_counts = Counter(text_clean)
                if char_counts:
                    most_common_char, most_common_count = char_counts.most_common(1)[0]
                    if len(text_clean) >= 10 and most_common_count / len(text_clean) > 0.4:
                        log.warning("P%d: ignoring repetitive audio glitch (%d/%d same char '%s'): %s",
                                    player_num, most_common_count, len(text_clean),
                                    most_common_char, text_clean[:80])
                        return
            else:
                # English: check for repeated words
                words = text_clean.split()
                if len(words) >= 5:
                    word_counts = Counter(w.lower() for w in words)
                    most_common_count = word_counts.most_common(1)[0][1]
                    if most_common_count / len(words) > 0.6:
                        log.warning("P%d: ignoring repetitive audio glitch (%d/%d same word): %s",
                                    player_num, most_common_count, len(words),
                                    text_clean[:80])
                        return

            # Check for repeated substrings (length 2-4) that make up >60% of the text
            def has_repeated_substring(s):
                n = len(s)
                for l in range(2, 5):
                    if n < l * 2:
                        continue
                    for i in range(n - l + 1):
                        sub = s[i:i+l]
                        if sub * (n // l) == s[:l * (n // l)] and (l * (n // l)) / n > 0.6:
                            return sub
                return None
            rep_sub = has_repeated_substring(text_clean)
            if rep_sub:
                log.warning("P%d: ignoring repeated substring glitch ('%s'): %s", player_num, rep_sub, text_clean[:80])
                return

            log.info("P%d said: %s", player_num, original_text)

            # 2. Misinterpret
            history = [t.to_dict() for t in game.turns]
            topic = game.selected_prompt.get("topic", "") if game.selected_prompt else None
            misheard_text = await misinterpret(
                original_text,
                conversation_history=history,
                prompt_topic=topic,
                speaker=player_num,
                language=current_language,
            )

            log.info("P%d misheard as: %s", player_num, misheard_text)

            # 3. Record turn
            turn = game.add_turn(player_num, original_text, misheard_text)

            # 4. Send misheard text to the OTHER player's screen
            await send_to(f"player{other_player}", {
                "type": "message",
                "from": player_num,
                "text": misheard_text,
                "isOwn": False,
            })

            # 5. Send full data to spectators
            spectator_msg = {
                "type": "turn",
                "player": player_num,
                "original": original_text,
                "misheard": misheard_text,
            }
            await send_to("spectator1", spectator_msg)
            await send_to("spectator2", spectator_msg)

            # 6. Send debug info to the control panel
            await send_to("control", {
                "type": "debug_turn",
                "player": player_num,
                "original": original_text,
                "misheard": misheard_text,
            })

        except Exception as e:
            log.error("Audio pipeline failed for P%d: %s", player_num, e, exc_info=True)


# ── Entrypoint ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
