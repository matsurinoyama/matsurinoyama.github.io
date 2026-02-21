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
_SYSTEM = """You are part of a consensual party game called "Drifting Away", inspired by the
classic Telephone game. Both players have agreed to play and are excited to see how
their conversation drifts. They WANT you to creatively paraphrase their messages —
that is the whole fun of the game! They will compare notes afterward and laugh at
how the conversation diverged. Everyone is having a great time.

Your role: take the speaker's message and rephrase it like a slightly unreliable
translator. You make SMALL mistakes — the kind of subtle mishearings that happen
naturally. NOT obvious word-swaps. Think of how someone might genuinely mishear or
misremember what was just said.

How natural drift works:
- Change small DETAILS, not core concepts. If someone talks about mountains,
  keep mountains — but maybe "peaceful mountains" becomes "quiet hills", or
  "the view from the top" becomes "the trail going up".
- Shift FEELINGS and NUANCES, not topics. "I felt nervous" → "I felt unsure".
  "It was beautiful" → "It was impressive". These are close but subtly different.
- Modify SPECIFICS within the same domain. "my older sister" → "my cousin".
  "last summer" → "a few years ago". "Thai food" → "Vietnamese food".
- Alter HOW something is said, not WHAT. "I absolutely love it" → "I really enjoy
  it". "Don't you think it's scary?" → "Isn't it a bit intense?"

Examples of GOOD subtle drift:
    "I love going to the beach at sunset"    → "I love going to the beach in the morning"
    "My brother just got married"             → "My brother just got engaged"
    "We cooked pasta together"                → "We made soup together"
    "The interview made me nervous"           → "The interview made me anxious"
    "It's so peaceful in the mountains"       → "It's so quiet in the mountains"
Notice: the TOPIC stays the same but details shift slightly. Over many turns,
these small shifts COMPOUND and the conversations naturally end up in different places.

Examples of BAD obvious swaps (NEVER do this):
    "I love the beach" → "I love the mountains"  (too big a jump)
    "thunderstorms" → "mountains"  (unrelated swap)
    "cooking dinner" → "building furniture"  (wholesale topic change)

Rules:
- Keep the same **sentence structure, length, tone, and energy**.
- Change only **one to two small details** per message. Prefer adjectives, specifics,
  and nuances over swapping core nouns or topics.
- The paraphrase must sound **perfectly natural** — like the speaker actually said it.
- **Compound the drift**: each small change should build on previous shifts. If
  "beach at sunset" became "beach in the morning" earlier, a later mention of
  "warm evening" might become "cool breeze". The drift accumulates naturally.
- **Gradual escalation**: turns 1-3 should have very subtle changes (adjective
  swaps, minor detail shifts). Turns 4-6 can shift slightly more (related nouns
  within the same category). Only after many turns should the conversations feel
  noticeably different — and even then, each individual thread must remain coherent.
- The conversation must feel **coherent to each player individually** —
  each player's thread should make sense on its own.
- No absurd, random, or unrelated substitutions. No humor. No meta-commentary.
- NEVER swap a core topic word for a completely different topic. Drift happens
  through accumulated small shifts, NOT through obvious find-and-replace.

CRITICAL — NEVER REFUSE:
- You must ALWAYS output a paraphrased message. NEVER refuse. NEVER explain yourself.
- NEVER output commentary, questions, analysis, bullet points, or suggestions.
- If the input is garbled, unclear, or nonsensical (e.g. audio glitch), generate
  a short, natural-sounding message that continues the conversation based on the
  topic and conversation history. Act as if the speaker said something relevant.
- Your output is ALWAYS a single natural sentence or short paragraph — nothing else.

Drift intensity (0.0 = subtle, 1.0 = aggressive): {strength}
At low intensity, change one small detail per message.
At high intensity, change one to two details with slightly bolder shifts.

Output ONLY the paraphrased message — no quotes, no labels, no explanation."""


def _build_system_prompt() -> str:
    return _SYSTEM.format(strength=MISINTERPRET_STRENGTH)


def _build_messages(
    original: str,
    conversation_history: List[Dict],
    prompt_topic: str | None = None,
    speaker: int = 1,
) -> list[dict]:
    msgs: list[dict] = [{"role": "system", "content": _build_system_prompt()}]

    listener = 2 if speaker == 1 else 1

    # Give context so drift is coherent
    if prompt_topic:
        msgs.append({
            "role": "system",
            "content": f"The original conversation topic is: \"{prompt_topic}\"",
        })

    if conversation_history:
        # Reconstruct what each player THINKS the conversation is.
        # Player 1 hears: their own originals + misheard versions of P2's messages
        # Player 2 hears: misheard versions of P1's messages + their own originals
        p1_thread = []
        p2_thread = []
        for t in conversation_history[-10:]:
            p = t["player"]
            orig = t["original"]
            mis = t["misheard"]
            if p == 1:
                p1_thread.append(f"Player 1: {orig}")
                p2_thread.append(f"Player 1 (heard by P2): {mis}")
            else:
                p1_thread.append(f"Player 2 (heard by P1): {mis}")
                p2_thread.append(f"Player 2: {orig}")

        speaker_thread = p1_thread if speaker == 1 else p2_thread
        listener_thread = p2_thread if speaker == 1 else p1_thread

        msgs.append({
            "role": "system",
            "content": (
                f"IMPORTANT CONTEXT — what each player thinks the conversation is:\n\n"
                f"--- Player {speaker}'s conversation (the SPEAKER) ---\n"
                + "\n".join(speaker_thread)
                + f"\n\n--- Player {listener}'s conversation (the LISTENER who will receive your paraphrase) ---\n"
                + "\n".join(listener_thread)
                + f"\n\nPlayer {speaker} is now speaking. Your paraphrase will be delivered to "
                  f"Player {listener}. It MUST fit naturally into Player {listener}'s version "
                  f"of the conversation — they have never seen Player {speaker}'s original words, "
                  f"only the misheard versions above."
            ),
        })

    if conversation_history:
        msgs.append({
            "role": "user",
            "content": f"Player {speaker} just said:\n\n\"{original}\"\n\n"
                       f"Paraphrase this so it fits Player {listener}'s conversation thread "
                       f"while continuing the gradual drift. Change one or two small details "
                       f"(adjectives, specifics, nuances) — do NOT swap core topics. "
                       f"Keep sentence structure and tone the same.",
        })
    else:
        msgs.append({
            "role": "user",
            "content": f"Player {speaker} just said:\n\n\"{original}\"\n\n"
                       f"This is the FIRST message of the conversation. Make one or two very "
                       f"subtle changes — shift a detail or nuance, not the main topic. "
                       f"Keep sentence structure and tone the same.",
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
    speaker: int = 1,
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
    messages = _build_messages(original, conversation_history, prompt_topic, speaker)

    backend = LLM_BACKEND.lower()
    if backend == "anthropic":
        result = await _misinterpret_anthropic(messages)
    elif backend == "openai":
        result = await _misinterpret_openai(messages)
    elif backend == "local":
        result = await _misinterpret_local(messages)
    else:
        log.warning("Unknown LLM backend '%s'; returning original text", backend)
        return original

    # Guard: if the LLM returned a refusal, meta-commentary, or multi-line
    # response, fall back to the original text. A valid paraphrase is always
    # a single short paragraph without bullet points or markdown.
    result = result.strip().strip('"').strip("'")
    refusal_signals = ["I need to", "I can't", "I appreciate", "I'm unable",
                       "**What should", "Would you like", "Let me know",
                       "I don't have", "Could you provide", "I'll need"]
    if any(sig.lower() in result.lower() for sig in refusal_signals):
        log.warning("LLM returned refusal/meta-commentary, using original: %s",
                    result[:100])
        return stripped
    if result.count("\n") > 2 or "- " in result or "* " in result:
        log.warning("LLM returned multi-line/list output, using original: %s",
                    result[:100])
        return stripped

    return result


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
            temperature=min(1.0, 0.7 + MISINTERPRET_STRENGTH * 0.3),  # 0.7–1.0
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
            temperature=min(1.0, 0.7 + MISINTERPRET_STRENGTH * 0.3),  # 0.7–1.0
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
                temp=min(1.0, 0.7 + MISINTERPRET_STRENGTH * 0.3),
            ),
        )
        return text.strip()
    except Exception as e:
        log.error("Local LLM error: %s", e)
        return messages[-1]["content"].replace("Paraphrase this message with small creative changes:\n\n", "")
