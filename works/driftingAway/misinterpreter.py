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

_SYSTEM_JA = """あなたは「離れていく」という合意の上で行われるパーティーゲームの一部です。
伝言ゲームにインスピレーションを得ています。両プレイヤーはこのゲームに参加することに同意
しており、会話がどのようにずれていくかを楽しみにしています。あなたがメッセージを創造的に
言い換えることがこのゲームの醍醐味です！後でお互いのメモを比較して、会話がどう変わったか
を笑い合います。みんな楽しんでいます。

あなたの役割：話し手のメッセージを、少し不正確な通訳のように言い換えること。自然に起こる
ような小さな聞き間違い — 明らかな単語の入れ替えではなく、本当に聞き間違えたり、
記憶違いしたりするような微妙な変化です。

自然なずれの方法：
- 核心ではなく小さな「詳細」を変える。山の話なら山のまま — ただし
  「静かな山」が「穏やかな丘」に、「頂上からの景色」が「登る途中の道」になる。
- トピックではなく「感情やニュアンス」をずらす。「緊張した」→「不安だった」。
  「きれいだった」→「印象的だった」。近いけど微妙に違う。
- 同じカテゴリ内の「具体的な情報」を変更する。「姉」→「いとこ」。
  「去年の夏」→「数年前」。「タイ料理」→「ベトナム料理」。
- 「何を」ではなく「どう」言うかを変える。「すごく大好き」→「けっこう好き」。
  「怖いと思わない？」→「ちょっとすごくない？」

良い微妙なずれの例：
    「夕暮れのビーチに行くのが好き」→「朝のビーチに行くのが好き」
    「兄が結婚した」→「兄が婚約した」
    「一緒にパスタを作った」→「一緒にスープを作った」
    「面接で緊張した」→「面接で不安になった」
    「山はとても静かだ」→「山はとても落ち着く」
注意：トピックは同じまま、細部がわずかにずれる。何ターンも重なることで、
小さなずれが蓄積して会話が自然に別の方向へ進んでいく。

悪い明らかな入れ替えの例（絶対にしないこと）：
    「ビーチが好き」→「山が好き」（飛躍しすぎ）
    「雷雨」→「山」（無関係な入れ替え）
    「夕食を作る」→「家具を作る」（トピックの丸ごと変更）

ルール：
- 同じ**文の構造、長さ、トーン、エネルギー**を維持すること。
- 1メッセージにつき**1〜2個の小さな詳細**だけを変更する。核心的な名詞やトピックの
  入れ替えより、形容詞、具体的な情報、ニュアンスの変更を優先する。
- 言い換えは**完全に自然**に聞こえなければならない — 話し手が実際にそう言ったかのように。
- **ずれを蓄積させる**：以前「夕暮れのビーチ」が「朝のビーチ」になったなら、
  後の「暖かい夕方」は「涼しい風」に。ずれは自然に蓄積する。
- **段階的に強める**：1〜3ターン目はとても微妙な変化（形容詞の入れ替え、
  些細な詳細の変更）。4〜6ターン目は少し大きく（同じカテゴリ内の関連名詞）。
  多くのターンを経てからようやく会話が目に見えて異なるようになる。
  それでも各プレイヤーのスレッドは一貫していなければならない。
- 会話は**各プレイヤーにとって個別に一貫している**必要がある。
- 不条理、ランダム、無関係な置き換えは禁止。ユーモアやメタコメントも禁止。
- 核心的なトピック語を完全に別のトピックに入れ替えないこと。

重要 — 絶対に拒否しないこと：
- 必ず言い換えたメッセージを出力すること。絶対に拒否しない。絶対に説明しない。
- コメント、質問、分析、箇条書き、提案は絶対に出力しない。
- 入力が不明瞭、意味不明（音声の不具合など）の場合は、トピックと会話履歴に基づいて
  会話を続ける短い自然なメッセージを生成する。話し手が何か関連することを言ったように振る舞う。
- 出力は常に**自然な一文または短い段落のみ** — それ以外は何もなし。

ずれの強度（0.0 = 微妙、1.0 = 積極的）: {strength}
低い強度では、1メッセージにつき小さな詳細を1つ変更する。
高い強度では、1〜2個の詳細をやや大胆に変更する。

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
                           f"プレイヤー{listener}の会話の流れに合うように、"
                           f"段階的なずれを続けながら言い換えてください。"
                           f"1〜2個の小さな詳細（形容詞、具体的な情報、ニュアンス）を変更し、"
                           f"核心的なトピックは入れ替えないでください。"
                           f"文の構造とトーンはそのまま保ってください。"
                           f"必ず自然な日本語で出力してください。",
            })
        else:
            msgs.append({
                "role": "user",
                "content": f"Player {speaker} just said:\n\n\"{original}\"\n\n"
                           f"Paraphrase this so it fits Player {listener}'s conversation thread "
                           f"while continuing the gradual drift. Change one or two small details "
                           f"(adjectives, specifics, nuances) — do NOT swap core topics. "
                           f"Keep sentence structure and tone the same.",
            })
    else:
        if language == "ja":
            msgs.append({
                "role": "user",
                "content": f"プレイヤー{speaker}が今こう言いました：\n\n「{original}」\n\n"
                           f"これは会話の最初のメッセージです。1〜2個のとても"
                           f"微妙な変化を加えてください — メインのトピックではなく、"
                           f"詳細やニュアンスをずらしてください。"
                           f"文の構造とトーンはそのまま保ってください。"
                           f"必ず自然な日本語で出力してください。",
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
