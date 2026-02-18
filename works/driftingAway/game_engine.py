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

from config import PROMPTS_FILE, PROMPT_CHOICES_COUNT, ROUND_DURATION_SECONDS


# ── Phases ─────────────────────────────────────────────────────────────
class Phase(str, Enum):
    IDLE = "idle"                  # waiting for two players
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
def load_prompts() -> list[dict]:
    with open(PROMPTS_FILE, "r") as f:
        data = json.load(f)
    return data["prompts"]


def pick_prompt_choices(pool: list[dict], n: int = 1) -> list[dict]:
    return random.sample(pool, min(n, len(pool)))


# ── Game State ─────────────────────────────────────────────────────────
class GameState:
    """Single source of truth for one round of the installation."""

    def __init__(self):
        self.phase: Phase = Phase.IDLE
        self.prompt_pool: list[dict] = load_prompts()
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

    # ── callbacks ──────────────────────────────────────────────────────
    def on_phase_change(self, cb: Callable[[Phase, dict], Coroutine]):
        self._on_phase_change = cb

    def on_timer_tick(self, cb: Callable[[float], Coroutine]):
        self._on_timer_tick = cb

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

    async def enter_prompt_select(self):
        self.phase = Phase.PROMPT_SELECT
        prompt = self._pick_random_prompt()
        self.prompt_choices = [prompt]
        self.selected_prompt_index = 0
        await self._emit_phase({
            "choices": self.prompt_choices,
            "highlightIndex": 0,
            "startingPlayer": self.starting_player,
        })

    async def reroll_prompt(self):
        """Replace the current topic with a new random one."""
        if self.phase != Phase.PROMPT_SELECT:
            return
        prompt = self._pick_random_prompt()
        self.prompt_choices = [prompt]
        self.selected_prompt_index = 0
        await self._emit_phase({
            "choices": self.prompt_choices,
            "highlightIndex": 0,
            "startingPlayer": self.starting_player,
        })

    async def navigate_prompt(self, direction: int):
        """Legacy — now acts as reroll."""
        await self.reroll_prompt()

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

    async def reset(self):
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self.starting_player = random.choice([1, 2])
        self.phase = Phase.RESET
        await self._emit_phase({})
        # brief pause before going back to idle
        await asyncio.sleep(2)
        self.turns.clear()
        self.selected_prompt = None
        self.prompt_choices.clear()
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
        }
