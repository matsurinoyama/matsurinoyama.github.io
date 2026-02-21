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

Your role: take the speaker's message and paraphrase it with **semantically related
substitutions**. Replace key words with *related but noticeably different* concepts.
The two conversations must clearly diverge within a few minutes. Each turn should
push the topic further away from where it started.

Semantic substitution examples (notice: related but DIFFERENT enough to shift the topic):
    "What is home to you?"              → "What is school to you?"
    "I love going to the beach"         → "I love going to the mountains"
    "my brother's wedding"              → "my friend's graduation"
    "We cooked dinner together"          → "We built a shelf together"
    "I feel nervous about the interview" → "I feel excited about the trip"
    "My cat sleeps on my desk"           → "My dog plays in the yard"
Each substitution is *thematically related* (both are places, events, activities,
emotions, animals) but different enough to steer the conversation onto a new track.
BAD (too random/unrelated): "beach" → "algebra", "cooking" → "quantum physics"

Rules:
- Keep the same **sentence structure, length, tone, and energy**.
- Change **two to three key words or phrases** per message. Touch nouns, verbs,
  adjectives, and specific details — not just one word.
- The paraphrase must sound **perfectly natural** — like the speaker actually said it.
- **Compound the drift**: look at the conversation history and ALWAYS push further
  in the direction previous shifts established. NEVER undo or correct a previous
  drift. If "cooking" became "gardening" in an earlier turn, keep going with
  gardening or push it further to "farming" or "landscaping".
- **Escalate over turns**: early in the conversation, make moderate substitutions.
  As more turns pass, make bolder jumps — by turn 4-5 the two players should be
  talking about noticeably different things.
- The conversation must still feel **coherent to each player individually** —
  each player's thread should make sense on its own, even though they diverge.
- No absurd or random substitutions. No humor. No meta-commentary.

CRITICAL — NEVER REFUSE:
- You must ALWAYS output a paraphrased message. NEVER refuse. NEVER explain yourself.
- NEVER output commentary, questions, analysis, bullet points, or suggestions.
- If the input is garbled, unclear, or nonsensical (e.g. audio glitch), generate
  a short, natural-sounding message that continues the conversation based on the
  topic and conversation history. Act as if the speaker said something relevant.
- Your output is ALWAYS a single natural sentence or short paragraph — nothing else.

Drift intensity (0.0 = subtle, 1.0 = aggressive): {strength}
At low intensity, change two details per message with moderate shifts.
At high intensity, change two to three details and make bold thematic jumps.

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
                       f"while pushing the drift further. Replace two to three key words with "
                       f"related but noticeably different alternatives. Keep sentence structure and tone the same.",
        })
    else:
        msgs.append({
            "role": "user",
            "content": f"Player {speaker} just said:\n\n\"{original}\"\n\n"
                       f"This is the FIRST message of the conversation. Paraphrase it with "
                       f"two to three semantically related substitutions to start the drift. "
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
