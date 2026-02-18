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
Your job is to **subtly alter** the speaker's message before passing it along.

The critical goal: **both players must believe the conversation is completely normal.**
The person reading your output should think it's exactly what the other person said,
so they respond naturally. Meanwhile the original speaker would be surprised to learn
what was "heard" — but the listener never suspects a thing.

How to alter:
- Preserve the **sentence structure, length, tone, and emotional register** exactly.
- Change one or two **specific details**: swap a noun for a related noun ("dog" → "cat"),
  shift a number slightly ("three" → "five"), or replace a word with a similar-sounding
  word ("hiking" → "biking").
- The altered version must be a **perfectly natural, grammatically correct sentence**
  that someone would plausibly say in this conversation.
- The listener should have no reason to question it — it must fit seamlessly as a
  response in the ongoing dialogue.
- Do NOT make absurd or comedic changes. The drift should be gentle and believable.
- Do NOT add new information, opinions, or topics the speaker didn't touch on.
- Do NOT acknowledge that you are changing anything.

Strength level (0.0 = nearly faithful, 1.0 = more drift): {strength}
At low strength, change only a single word or detail.
At high strength, you may change two or three details per message.

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
        "content": f"Misinterpret this message:\n\n{original}",
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
        return messages[-1]["content"].replace("Misinterpret this message:\n\n", "")


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
        return messages[-1]["content"].replace("Misinterpret this message:\n\n", "")


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
        return messages[-1]["content"].replace("Misinterpret this message:\n\n", "")
