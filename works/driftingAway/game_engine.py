"""
Drifting Away — Game Engine
Manages game state, phases, timers, and prompt selection.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from enum import Enum
from typing import Any, Callable, Coroutine

from config import PROMPTS_FILE, PROMPTS_FILE_JA, PROMPT_CHOICES_COUNT, ROUND_DURATION_SECONDS, DEFAULT_LANGUAGE


# ── Phases ─────────────────────────────────────────────────────────────
class Phase(str, Enum):
    IDLE = "idle"                  # start screen — press any button
    WAITING = "waiting"            # one player ready, waiting for the other
    PROMPT_SELECT = "prompt_select"  # starting player picks a topic
    CONVERSATION = "conversation"  # 3-min misheard conversation
    REVEAL = "reveal"              # earmuffs off — compare notes
    RESET = "reset"                # cleanup before next round


# ── Conversation Turn ──────────────────────────────────────────────────
class Turn:
    __slots__ = ("player", "original", "misheard", "timestamp")

    def __init__(self, player: int, original: str, misheard: str):
        self.player = player
        self.original = original
        self.misheard = misheard
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "player": self.player,
            "original": self.original,
            "misheard": self.misheard,
            "ts": self.timestamp,
        }


# ── Prompt Pool ────────────────────────────────────────────────────────
def load_prompts(language: str = "ja") -> list[dict]:
    path = PROMPTS_FILE_JA if language == "ja" else PROMPTS_FILE
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["prompts"]


def pick_prompt_choices(pool: list[dict], n: int = 1) -> list[dict]:
    return random.sample(pool, min(n, len(pool)))


# ── Game State ─────────────────────────────────────────────────────────
class GameState:
    """Single source of truth for one round of the installation."""

    def __init__(self):
        self.phase: Phase = Phase.IDLE
        self.language: str = DEFAULT_LANGUAGE
        self.prompt_pool: list[dict] = load_prompts(self.language)
        self.prompt_choices: list[dict] = []
        self.selected_prompt: dict | None = None
        self.selected_prompt_index: int = 0
        self.starting_player: int = random.choice([1, 2])
        self.turns: list[Turn] = []
        self.round_start: float = 0
        self.round_remaining: float = ROUND_DURATION_SECONDS
        self._timer_task: asyncio.Task | None = None
        self._on_phase_change: Callable[[Phase, dict], Coroutine] | None = None
        self._on_timer_tick: Callable[[float], Coroutine] | None = None
        self._used_prompt_ids: set = set()  # track used prompts to avoid repeats
        self._prompt_history: list[dict] = []  # browsed prompts in order
        self._prompt_cursor: int = -1          # current position in history
        self.players_ready: set[int] = set()   # which players have pressed ready

    # ── callbacks ──────────────────────────────────────────────────────
    def on_phase_change(self, cb: Callable[[Phase, dict], Coroutine]):
        self._on_phase_change = cb

    def on_timer_tick(self, cb: Callable[[float], Coroutine]):
        self._on_timer_tick = cb

    def set_language(self, lang: str):
        """Switch prompt language. Reloads the prompt pool."""
        self.language = lang
        self.prompt_pool = load_prompts(lang)
        self._used_prompt_ids.clear()

    async def _emit_phase(self, extra: dict | None = None):
        if self._on_phase_change:
            await self._on_phase_change(self.phase, extra or {})

    # ── phase transitions ─────────────────────────────────────────────
    def _pick_random_prompt(self) -> dict:
        """Pick one random prompt, avoiding recently used ones."""
        available = [p for p in self.prompt_pool if p.get("id") not in self._used_prompt_ids]
        if not available:
            # All prompts used — reset the pool
            self._used_prompt_ids.clear()
            available = self.prompt_pool
        choice = random.choice(available)
        self._used_prompt_ids.add(choice.get("id"))
        return choice

    async def player_ready(self, player_num: int):
        """Mark a player as ready. Transition to waiting or prompt_select."""
        if self.phase not in (Phase.IDLE, Phase.WAITING):
            return
        self.players_ready.add(player_num)

        if len(self.players_ready) >= 2:
            # Both ready — go to prompt select
            await self.enter_prompt_select()
        else:
            # First player ready — enter waiting phase
            self.phase = Phase.WAITING
            await self._emit_phase({
                "playersReady": list(self.players_ready),
            })

    async def enter_prompt_select(self):
        self.phase = Phase.PROMPT_SELECT
        self._prompt_history.clear()
        self._prompt_cursor = -1
        prompt = self._pick_random_prompt()
        self._prompt_history.append(prompt)
        self._prompt_cursor = 0
        self.prompt_choices = [prompt]
        self.selected_prompt_index = 0
        await self._emit_phase({
            "choices": self.prompt_choices,
            "highlightIndex": 0,
            "startingPlayer": self.starting_player,
        })

    async def reroll_prompt(self):
        """Pick a new random topic and append to history (next key)."""
        if self.phase != Phase.PROMPT_SELECT:
            return
        # If we're not at the end of history, just advance the cursor
        if self._prompt_cursor < len(self._prompt_history) - 1:
            self._prompt_cursor += 1
        else:
            # Pick a genuinely new prompt and append
            prompt = self._pick_random_prompt()
            self._prompt_history.append(prompt)
            self._prompt_cursor = len(self._prompt_history) - 1
        current = self._prompt_history[self._prompt_cursor]
        self.prompt_choices = [current]
        self.selected_prompt_index = 0
        await self._emit_phase({
            "choices": self.prompt_choices,
            "highlightIndex": 0,
            "startingPlayer": self.starting_player,
        })

    async def prev_prompt(self):
        """Go back to the previously shown topic (prev key)."""
        if self.phase != Phase.PROMPT_SELECT:
            return
        if self._prompt_cursor > 0:
            self._prompt_cursor -= 1
        current = self._prompt_history[self._prompt_cursor]
        self.prompt_choices = [current]
        self.selected_prompt_index = 0
        await self._emit_phase({
            "choices": self.prompt_choices,
            "highlightIndex": 0,
            "startingPlayer": self.starting_player,
        })

    async def navigate_prompt(self, direction: int):
        """Legacy — forward goes next, backward goes prev."""
        if direction >= 0:
            await self.reroll_prompt()
        else:
            await self.prev_prompt()

    async def confirm_prompt(self):
        if self.phase != Phase.PROMPT_SELECT:
            return
        self.selected_prompt = self.prompt_choices[self.selected_prompt_index]
        await self.enter_conversation()

    async def set_prompt_index(self, index: int):
        """Set the prompt index directly (from click) and confirm."""
        if self.phase != Phase.PROMPT_SELECT:
            return
        if 0 <= index < len(self.prompt_choices):
            self.selected_prompt_index = index
            self.selected_prompt = self.prompt_choices[index]
            await self.enter_conversation()

    async def enter_conversation(self):
        self.phase = Phase.CONVERSATION
        self.turns.clear()
        self.round_start = time.time()
        self.round_remaining = ROUND_DURATION_SECONDS
        await self._emit_phase({
            "prompt": self.selected_prompt,
            "duration": ROUND_DURATION_SECONDS,
            "startingPlayer": self.starting_player,
        })
        self._timer_task = asyncio.create_task(self._run_timer())

    async def _run_timer(self):
        try:
            while self.round_remaining > 0 and self.phase == Phase.CONVERSATION:
                await asyncio.sleep(1)
                elapsed = time.time() - self.round_start
                self.round_remaining = max(0, ROUND_DURATION_SECONDS - elapsed)
                if self._on_timer_tick:
                    await self._on_timer_tick(self.round_remaining)
            if self.phase == Phase.CONVERSATION:
                # Clear self-reference so enter_reveal() won't cancel us
                # (we're already finishing naturally)
                self._timer_task = None
                await self.enter_reveal()
        except asyncio.CancelledError:
            pass

    def add_turn(self, player: int, original: str, misheard: str) -> Turn:
        t = Turn(player=player, original=original, misheard=misheard)
        self.turns.append(t)
        return t

    async def enter_reveal(self):
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self.phase = Phase.REVEAL
        await self._emit_phase({
            "prompt": self.selected_prompt,
            "turns": [t.to_dict() for t in self.turns],
        })
        # Auto-reset after 5 seconds
        self._timer_task = asyncio.create_task(self._auto_reset())

    async def _auto_reset(self):
        try:
            await asyncio.sleep(5)
            if self.phase == Phase.REVEAL:
                self._timer_task = None  # clear ref so reset() won't cancel us
                await self.reset()
        except asyncio.CancelledError:
            pass

    async def reset(self):
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self.starting_player = random.choice([1, 2])
        self.phase = Phase.RESET
        await self._emit_phase({})
        # pause so players see "Thanks for playing" before going back to idle
        await asyncio.sleep(5)
        self.turns.clear()
        self.selected_prompt = None
        self.prompt_choices.clear()
        self._prompt_history.clear()
        self._prompt_cursor = -1
        self.players_ready.clear()
        self.round_remaining = ROUND_DURATION_SECONDS
        self.phase = Phase.IDLE
        await self._emit_phase({})

    # ── serialisation ─────────────────────────────────────────────────
    def snapshot(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "prompt": self.selected_prompt,
            "promptChoices": self.prompt_choices,
            "highlightIndex": self.selected_prompt_index,
            "startingPlayer": self.starting_player,
            "remaining": round(self.round_remaining, 1),
            "turns": [t.to_dict() for t in self.turns],
            "playersReady": list(self.players_ready),
        }
