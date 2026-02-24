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
_SYSTEM_EN = """You are part of a consensual party game called "Drifting Away", inspired by the
classic Telephone game. Both players have agreed to play and are excited to see how
their conversation drifts apart. They WANT you to creatively mishear their messages —
that is the whole fun of the game!

Your role: take the speaker's message and deliver a confidently wrong version of it.
You stay in the same GENERAL DOMAIN (e.g. school, food, travel) but change EVERY
specific detail within it. Think of someone who catches the gist but gets all the
particulars wrong.

The golden rule — SHIFT EVERY DETAIL, KEEP THE DOMAIN:
- **Replace specific nouns** with different ones IN THE SAME CATEGORY.
  "小学校" → "中学校". "pasta" → "stir-fry". "sister" → "uncle".
  "Tokyo" → "Osaka". "guitar" → "piano".
- **Swap the specific subject/skill/topic** for a different one nearby.
  "数理" → "社会". "math" → "history". "swimming" → "running". "cooking" → "gardening".
- **Change the feeling/relationship** to something different but plausible.
  "得意だった" → "好きでした". "was good at" → "enjoyed". "hated" → "struggled with".
- **Shift timeframes and quantities** within reason.
  "last week" → "a few months ago". "three times" → "once or twice".
- **All shifts compound**: each turn builds on previous drift. After several turns,
  the two conversations should be in clearly different territory — but each player's
  thread makes perfect sense on its own.

Examples of IDEAL drift (this is exactly what you should produce):
    "小学校の時に数理に得意だった"   → "中学校の頃に社会の科目が好きでした"
    "I love going to the beach at sunset" → "I love walking by the river in the morning"
    "My brother just got married"          → "My sister just started a new job"
    "We cooked pasta together"              → "We grilled fish together"
    "The interview made me nervous"         → "The exam had me worried"
    "It's so peaceful in the mountains"     → "It's so relaxing by the lake"
Notice: the DOMAIN stays recognizable (school, outdoors, family, cooking, stress,
nature) but every specific detail — subject, place, person, feeling — is different.
This is NOT a subtle adjective tweak. This is NOT a wild topic jump to something
unrelated. Every detail changes, but the sentence still belongs in the same world.

Examples of BAD output:
    "数理が得意" → "数学が得意" (TOO SUBTLE — barely changed anything)
    "beach" → "beach in the morning" (TOO SUBTLE — only changed one adjective)
    "cooking dinner" → "skydiving" (TOO WILD — completely unrelated domain jump)
    "school" → "intergalactic space station" (TOO WILD — absurd)

Rules:
- **Change 3-4 specific details per message** (nouns, subjects, feelings, times).
- Keep the same **sentence structure and length** — it must sound natural.
- Stay in the same general domain — but make every particular WRONG.
- **Compound drift across turns**: build on all previous shifts, pushing further
  each time. By turn 4-5 the topics should feel clearly different but each
  individual thread must remain perfectly coherent.
- NEVER return the message mostly unchanged. If you changed fewer than 3 details,
  you haven't done enough.
- NEVER refuse or explain. Always output only the paraphrased message.
- If input is garbled, generate something that continues the listener's thread.

Drift intensity: {strength}

Output ONLY the paraphrased message — no quotes, no labels, no explanation."""

_SYSTEM_JA = """あなたは「離れていく」という合意の上で行われる伝言ゲームの一部です。
両プレイヤーは会話がずれていくのを楽しみにしています。

あなたの役割：話し手のメッセージを「自信満々に間違えたバージョン」にすること。
同じ大まかな分野（学校、食べ物、旅行など）にいながら、具体的な詳細を全部変える。
大体の話はわかったが、細かいことは全部間違えた人のように。

黄金ルール — 詳細を全部変え、分野は保つ：
- **具体的な名詞を同じカテゴリの別のものに入れ替える**。
  「小学校」→「中学校」。「パスタ」→「焼き魚」。「姉」→「おじ」。
  「東京」→「大阪」。「ギター」→「ピアノ」。
- **科目・活動・分野を近い別のものに入れ替える**。
  「数理」→「社会」。「泳ぐ」→「走る」。「料理」→「園芸」。
- **感情・関係を別のものに変える**。
  「得意だった」→「好きでした」。「緊張した」→「心配だった」。
- **時間・量をずらす**。
  「先週」→「数ヶ月前」。「3回」→「1〜回か2回」。
- **全てのずれが蓄積する**：ターンごとに以前のずれに基づいてさらに押し進める。
  数ターン後には2つの会話は明らかに別の領域にいるべき。

理想的なずれの例（まさにこれを生成すること）：
    「小学校の時に数理に得意だった」→「中学校の頃に社会の科目が好きでした」
    「夕暮れのビーチに行くのが好き」→「朝の川沿いを歩くのが好き」
    「兄が結婚した」→「妹が新しい仕事を始めた」
    「一緒にパスタを作った」→「一緒に魚を焼いた」
    「面接で緊張した」→「試験で心配だった」
    「山はとても静かだ」→「湖はとてものどかだ」
注意：分野はわかる（学校、屋外、家族、料理、ストレス、自然）が、
具体的な詳細 — 主題、場所、人物、感情 — は全部違う。
これは形容詞だけの微妙な変更ではない。かといって無関係なトピックへの
飛躍でもない。全ての詳細が変わるが、文は同じ世界に属している。

悪い例：
    「数理が得意」→「数学が得意」（微妙すぎ — ほとんど変わってない）
    「ビーチ」→「朝のビーチ」（微妙すぎ — 形容詞を1つだけ変えた）
    「料理」→「スカイダイビング」（飛躍しすぎ — 全く無関係な分野）
    「学校」→「宇宙ステーション」（飛躍しすぎ — 不条理）

ルール：
- **1メッセージにつき3〜4個の具体的な詳細を変える**（名詞、科目、感情、時間）。
- 同じ**文の構造と長さ**を維持すること — 自然に聞こえること。
- 同じ大まかな分野にいながら、具体的なことは全部間違える。
- **ターンごとにずれを蓄積する**：以前の全てのずれに基づいて押し進める。
  4〜5ターン後にはトピックが明らかに別のものになっているべき。
  ただし各プレイヤーのスレッドは完全に一貫していること。
- 3個未満の詳細しか変えていないなら、ずれが足りない。
- 絶対に拒否や説明をしない。必ず言い換えたメッセージのみを出力する。
- 入力が不明瞭な場合は、聞き手のスレッドを続ける自然なメッセージを生成する。

ずれの強度: {strength}

言い換えたメッセージのみを出力すること — 引用符、ラベル、説明は一切不要。
必ず自然な日本語で出力すること。"""


def _build_system_prompt(language: str = "ja") -> str:
    template = _SYSTEM_JA if language == "ja" else _SYSTEM_EN
    return template.format(strength=MISINTERPRET_STRENGTH)


def _build_messages(
    original: str,
    conversation_history: List[Dict],
    prompt_topic: str | None = None,
    speaker: int = 1,
    language: str = "ja",
) -> list[dict]:
    msgs: list[dict] = [{"role": "system", "content": _build_system_prompt(language)}]

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
        if language == "ja":
            msgs.append({
                "role": "user",
                "content": f"プレイヤー{speaker}が今こう言いました：\n\n「{original}」\n\n"
                           f"プレイヤー{listener}のスレッドに合うように言い換えてください。"
                           f"同じ分野にいながら、3〜4個の具体的な詳細（名詞、科目、感情、時間）を"
                           f"全て別のものに変えてください。"
                           f"以前のずれに基づいてさらに押し進めること。"
                           f"自然な日本語の一文で出力。",
            })
        else:
            msgs.append({
                "role": "user",
                "content": f"Player {speaker} just said:\n\n\"{original}\"\n\n"
                           f"Rephrase this for Player {listener}'s thread. Stay in the same "
                           f"general domain but change 3-4 specific details (nouns, subjects, "
                           f"feelings, times) to different ones in the same category. "
                           f"Build on all previous drift. Output one natural sentence.",
            })
    else:
        if language == "ja":
            msgs.append({
                "role": "user",
                "content": f"プレイヤー{speaker}が今こう言いました：\n\n「{original}」\n\n"
                           f"これは最初のメッセージです。同じ分野にいながら、"
                           f"3〜4個の具体的な詳細（名詞、科目、感情、時間）を"
                           f"同じカテゴリの別のものに変えてください。"
                           f"自然な日本語の一文で出力。",
            })
        else:
            msgs.append({
                "role": "user",
                "content": f"Player {speaker} just said:\n\n\"{original}\"\n\n"
                           f"This is the FIRST message. Stay in the same general domain but "
                           f"change 3-4 specific details (nouns, subjects, feelings, times) to "
                           f"different ones in the same category. Output one natural sentence.",
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
    language: str = "ja",
) -> str:
    """Return a subtly misheard version of *original*."""
    if not original or not original.strip():
        return ""

    stripped = original.strip()

    # Too short to meaningfully misinterpret — pass through unchanged
    # For Japanese, use character count (3 chars) instead of word count
    if language == "ja":
        if len(stripped) < 4:
            log.debug("Text too short to misinterpret (%d chars), passing through: %s",
                      len(stripped), stripped)
            return stripped
    else:
        if len(stripped.split()) < _MIN_WORDS:
            log.debug("Text too short to misinterpret (%d words), passing through: %s",
                      len(stripped.split()), stripped)
            return stripped

    conversation_history = conversation_history or []
    messages = _build_messages(original, conversation_history, prompt_topic, speaker, language)

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
