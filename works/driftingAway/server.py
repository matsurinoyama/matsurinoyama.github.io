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

    if action == "start_game":
        if game.phase == Phase.IDLE:
            await game.enter_prompt_select()

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
            # 1. Transcribe
            original_text = await transcribe_audio(audio_bytes)
            if not original_text.strip():
                return

            # Skip fragments too short to be meaningful (< 3 words)
            words = original_text.strip().split()
            if len(words) < 3:
                log.debug("P%d: ignoring short fragment (%d words): %s",
                          player_num, len(words), original_text.strip())
                return

            log.info("P%d said: %s", player_num, original_text)

            # 2. Misinterpret
            history = [t.to_dict() for t in game.turns]
            topic = game.selected_prompt.get("topic", "") if game.selected_prompt else None
            misheard_text = await misinterpret(
                original_text,
                conversation_history=history,
                prompt_topic=topic,
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
