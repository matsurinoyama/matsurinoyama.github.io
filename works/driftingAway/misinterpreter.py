"""
Drifting Away — Misinterpreter
Takes a real transcription and produces an intentionally *slightly*
wrong version — as if a well-meaning but confused telephone-game
participant heard something different.
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict

from config import (
    LLM_BACKEND,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    ANTHROPIC_MAX_TOKENS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    LOCAL_LLM_MODEL,
    MISINTERPRET_STRENGTH,
)

log = logging.getLogger("drifting.misinterpreter")

# ── System prompt for the LLM ─────────────────────────────────────────
_SYSTEM = """You are a hidden layer inside an art installation called "Drifting Away".

Two people are having a live conversation, but neither can hear the other directly.
Each person reads what you produce instead of what was actually said.
Your job is to **alter** the speaker's message before passing it along so that the
two sides of the conversation gradually **drift into completely different topics**.

The critical goal: **each altered message must sound perfectly natural** so the
listener believes it is exactly what the other person said. But over the course of
many turns the conversation should split — each player ends up thinking they are
talking about something entirely different from the other.

How to alter:
- Preserve the **sentence structure, length, tone, and emotional register**.
- **Replace key nouns, subjects, and themes** with plausible alternatives that nudge
  the conversation in a new direction. For example: "I love going to the mountains"
  → "I love going to the ocean"; "my brother's wedding" → "my sister's graduation".
- Swap specific details aggressively: names, places, activities, objects, numbers.
  "We hiked for three hours" → "We sailed for five hours".
- Each alteration should **build on previous drift** — look at the conversation
  history and keep steering each side further apart. Don't correct course.
- The altered version must be a **perfectly natural, grammatically correct sentence**
  that fits the listener's version of the conversation (not the speaker's).
- Do NOT make obviously absurd or comedic changes — the drift should feel organic.
- Do NOT acknowledge that you are changing anything.

Strength level (0.0 = nearly faithful, 1.0 = aggressive drift): {strength}
At low strength, change one or two details per message.
At high strength, change multiple key words and actively steer toward a different topic.

Output ONLY the altered message — no quotes, no labels, no explanation."""


def _build_system_prompt() -> str:
    return _SYSTEM.format(strength=MISINTERPRET_STRENGTH)


def _build_messages(
    original: str,
    conversation_history: List[Dict],
    prompt_topic: str | None = None,
) -> list[dict]:
    msgs: list[dict] = [{"role": "system", "content": _build_system_prompt()}]

    # Give context so drift is coherent
    if prompt_topic:
        msgs.append({
            "role": "system",
            "content": f"The original conversation topic is: \"{prompt_topic}\"",
        })

    if conversation_history:
        history_text = "\n".join(
            f"[Player {t['player']}] (original) {t['original']}  →  (misheard) {t['misheard']}"
            for t in conversation_history[-8:]  # last 8 turns for context
        )
        msgs.append({
            "role": "system",
            "content": f"Conversation so far:\n{history_text}",
        })

    msgs.append({
        "role": "user",
        "content": f"Paraphrase this message with small creative changes:\n\n{original}",
    })
    return msgs


# ── Public API ─────────────────────────────────────────────────────────

# Minimum word count to bother sending to the LLM.
# Anything shorter is passed through unchanged.
_MIN_WORDS = 3


async def misinterpret(
    original: str,
    conversation_history: list[dict] | None = None,
    prompt_topic: str | None = None,
) -> str:
    """Return a subtly misheard version of *original*."""
    if not original or not original.strip():
        return ""

    stripped = original.strip()

    # Too short to meaningfully misinterpret — pass through unchanged
    if len(stripped.split()) < _MIN_WORDS:
        log.debug("Text too short to misinterpret (%d words), passing through: %s",
                  len(stripped.split()), stripped)
        return stripped

    conversation_history = conversation_history or []
    messages = _build_messages(original, conversation_history, prompt_topic)

    backend = LLM_BACKEND.lower()
    if backend == "anthropic":
        return await _misinterpret_anthropic(messages)
    elif backend == "openai":
        return await _misinterpret_openai(messages)
    elif backend == "local":
        return await _misinterpret_local(messages)
    else:
        log.warning("Unknown LLM backend '%s'; returning original text", backend)
        return original


# ── Anthropic backend (default) ────────────────────────────────────────

async def _misinterpret_anthropic(messages: list[dict]) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    # Anthropic separates system from messages; extract system content
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]

    try:
        resp = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            system="\n\n".join(system_parts),
            messages=user_messages,
            temperature=0.7 + MISINTERPRET_STRENGTH * 0.5,  # 0.7–1.2
        )
        return resp.content[0].text.strip()
    except Exception as e:
        log.error("Anthropic error: %s", e)
        return messages[-1]["content"].replace("Paraphrase this message with small creative changes:\n\n", "")


# ── OpenAI backend ─────────────────────────────────────────────────────

async def _misinterpret_openai(messages: list[dict]) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.7 + MISINTERPRET_STRENGTH * 0.5,  # 0.7–1.2
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.error("OpenAI error: %s", e)
        return messages[-1]["content"].replace("Paraphrase this message with small creative changes:\n\n", "")


# ── Local MLX-LM backend ──────────────────────────────────────────────

async def _misinterpret_local(messages: list[dict]) -> str:
    import asyncio

    try:
        from mlx_lm import load, generate

        model, tokenizer = load(LOCAL_LLM_MODEL)

        # Format as ChatML
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )

        # Run in thread so we don't block the event loop
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(
            None,
            lambda: generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=OPENAI_MAX_TOKENS,
                temp=0.7 + MISINTERPRET_STRENGTH * 0.5,
            ),
        )
        return text.strip()
    except Exception as e:
        log.error("Local LLM error: %s", e)
        return messages[-1]["content"].replace("Paraphrase this message with small creative changes:\n\n", "")
