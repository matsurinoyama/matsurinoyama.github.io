#!/usr/bin/env python3
"""
Drifting Away — Automated Play Tester

Simulates a full conversation between two AI players, showing how the
misinterpreter causes their understanding to diverge over multiple turns.

Usage:
    python test_conversation.py                  # defaults: Japanese, 8 turns
    python test_conversation.py --lang en        # English mode
    python test_conversation.py --turns 12       # more rounds
    python test_conversation.py --topic "子供の頃の思い出"  # custom topic
    python test_conversation.py --runs 3         # run 3 conversations back-to-back
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

# Make sure we can import project modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    PROMPTS_FILE,
    PROMPTS_FILE_JA,
    MISINTERPRET_STRENGTH,
)
from misinterpreter import misinterpret


# ── ANSI Terminal Colors ────────────────────────────────────────────────
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_GREEN = "\033[32m"
_CYAN  = "\033[36m"
_YELL  = "\033[33m"
_RST   = "\033[0m"


# ── Simulated Player (LLM pretends to be a person) ────────────────────

_PLAYER_SYSTEM_JA = """あなたはカジュアルな会話をしている日本人です。
相手の発言に自然に返事をしてください。1〜3文で短く、日常的な口調で。
自分の経験や意見を混ぜて、会話を続けてください。
普通の人のように自然に話してください。敬語は不要です。

重要なルール：
- 絶対にロールプレイから外れないこと。あなたは会話をしている普通の人です。
- 会話の形式・構造・システムについてコメントしないこと。
- 「相手の発言を確認」「同じ内容」「表示されてない」などのメタ発言は禁止。
- たとえ相手の発言が前と似ていても、自然に会話を続けること。
- 常に新しい内容で返事をすること — 自分の体験や意見を加える。"""

_PLAYER_SYSTEM_EN = """You are a person having a casual conversation.
Respond naturally to what the other person said. Keep it to 1-3 sentences,
casual and conversational. Mix in your own experiences and opinions.
Talk like a normal person would.

Critical rules:
- NEVER break character. You are a normal person in a conversation.
- NEVER comment on the conversation format, structure, or system.
- NEVER say things like "wait", "let me check", "that seems like the same message".
- Even if their message seems similar to before, just continue the conversation naturally.
- Always add new content — your own experiences, opinions, or questions."""


async def simulate_player_response(
    what_they_heard: str,
    their_history: list[str],
    topic: str,
    language: str = "ja",
) -> str:
    """Generate a simulated player response based on what they 'heard'."""
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system = _PLAYER_SYSTEM_JA if language == "ja" else _PLAYER_SYSTEM_EN

    # Build conversation context
    context_lines = []
    for i, line in enumerate(their_history[-6:]):
        speaker = "あなた" if i % 2 == 0 else "相手" if language == "ja" else "You" if i % 2 == 0 else "Them"
        context_lines.append(f"{speaker}: {line}")

    if language == "ja":
        user_msg = f"会話のトピック: {topic}\n\n"
        if context_lines:
            user_msg += "これまでの会話:\n" + "\n".join(context_lines) + "\n\n"
        user_msg += f"相手が今こう言いました: 「{what_they_heard}」\n\n自然に返事してください。"
    else:
        user_msg = f"Topic: {topic}\n\n"
        if context_lines:
            user_msg += "Conversation so far:\n" + "\n".join(context_lines) + "\n\n"
        user_msg += f"They just said: \"{what_they_heard}\"\n\nRespond naturally."

    try:
        resp = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
            temperature=0.9,
        )
        return resp.content[0].text.strip().strip('"')
    except Exception as e:
        print(f"  [ERROR generating player response: {e}]")
        return "そうだね、確かにそう思う。" if language == "ja" else "Yeah, I think so too."


# ── Conversation Simulator ─────────────────────────────────────────────

async def run_conversation(
    topic: str,
    language: str = "ja",
    num_turns: int = 8,
    run_number: int = 1,
) -> None:
    """Simulate a full conversation and print both threads side-by-side."""

    print(f"\n{'='*80}")
    print(f"  RUN #{run_number}")
    print(f"  Topic: {topic}")
    print(f"  Language: {'日本語' if language == 'ja' else 'English'}")
    print(f"  Turns: {num_turns}  |  Drift Strength: {MISINTERPRET_STRENGTH}")
    print(f"{'='*80}\n")

    # What each player THINKS the conversation is
    p1_thread: list[str] = []  # P1's perceived conversation
    p2_thread: list[str] = []  # P2's perceived conversation

    # Full history for the misinterpreter (matches server.py format)
    conversation_history: list[dict] = []

    # Player 1 starts by saying something about the topic
    if language == "ja":
        opener_prompt = f"「{topic}」について、会話を始めてください。1〜2文で自然に。"
    else:
        opener_prompt = f"Start a conversation about \"{topic}\". 1-2 sentences, casual."

    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    resp = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=150,
        system=_PLAYER_SYSTEM_JA if language == "ja" else _PLAYER_SYSTEM_EN,
        messages=[{"role": "user", "content": opener_prompt}],
        temperature=0.9,
    )
    p1_original = resp.content[0].text.strip().strip('"')

    for turn in range(num_turns):
        if turn % 2 == 0:
            # Player 1 speaks
            speaker, listener = 1, 2
            if turn == 0:
                original = p1_original
            else:
                # P1 responds to what they heard (the misheard version of P2)
                original = await simulate_player_response(
                    p1_thread[-1], p1_thread, topic, language
                )

            # Misinterpret for P2
            misheard = await misinterpret(
                original, conversation_history, topic, speaker, language
            )

            # P1's thread: sees their own original
            p1_thread.append(original)
            # P2's thread: sees the misheard version
            p2_thread.append(misheard)

        else:
            # Player 2 speaks
            speaker, listener = 2, 1

            # P2 responds to what they heard (the misheard version of P1)
            original = await simulate_player_response(
                p2_thread[-1], p2_thread, topic, language
            )

            # Misinterpret for P1
            misheard = await misinterpret(
                original, conversation_history, topic, speaker, language
            )

            # P2's thread: sees their own original
            p2_thread.append(original)
            # P1's thread: sees the misheard version
            p1_thread.append(misheard)

        # Record in history
        conversation_history.append({
            "player": speaker,
            "original": original,
            "misheard": misheard,
        })

        # Print this turn
        p_label = f"P{speaker}"
        print(f"  {_DIM}Turn {turn+1}{_RST} ({_BOLD}{p_label} speaks{_RST}):")
        print(f"    {_GREEN}Actually said:{_RST}  {original}")
        print(f"    {_YELL}Other heard:{_RST}   {misheard}")
        print()

    # ── Summary ────────────────────────────────────────────────────────

    self_lbl  = "自分" if language == "ja" else "You "
    other_lbl = "相手" if language == "ja" else "Them"

    def _print_thread(player_num: int, thread: list[str], header: str):
        print(f"\n  📖 {_BOLD}{header}{_RST}")
        print(f"  {'─'*40}")
        for i, msg in enumerate(thread):
            is_self = (i % 2 == 0) if player_num == 1 else (i % 2 == 1)
            # Blank line between exchanges (every pair of messages)
            if i > 0 and i % 2 == 0:
                print()
            if is_self:
                print(f"    {_GREEN}{self_lbl} ▶{_RST}  {msg}")
            else:
                print(f"    {_CYAN}{other_lbl} ◀{_RST}  {msg}")
        print()

    print(f"\n{'─'*80}")

    p1_hdr = "プレイヤー1が見た会話" if language == "ja" else "Player 1's perceived conversation"
    p2_hdr = "プレイヤー2が見た会話" if language == "ja" else "Player 2's perceived conversation"

    _print_thread(1, p1_thread, p1_hdr)
    _print_thread(2, p2_thread, p2_hdr)

    print(f"{'='*80}\n")


# ── Entry Point ────────────────────────────────────────────────────────

def load_random_topic(language: str) -> str:
    path = PROMPTS_FILE_JA if language == "ja" else PROMPTS_FILE
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Handle both {"prompts": [...]} and plain [...] formats
    prompts = data.get("prompts", data) if isinstance(data, dict) else data
    prompt = random.choice(prompts)
    if isinstance(prompt, dict):
        return prompt.get("topic", prompt.get("text", str(prompt)))
    return str(prompt)


async def main():
    parser = argparse.ArgumentParser(description="Drifting Away — Automated Play Tester")
    parser.add_argument("--lang", default="ja", choices=["ja", "en"],
                        help="Language (default: ja)")
    parser.add_argument("--turns", type=int, default=8,
                        help="Number of conversation turns (default: 8)")
    parser.add_argument("--topic", type=str, default=None,
                        help="Conversation topic (default: random from prompts)")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of conversations to simulate (default: 1)")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to .env file.")
        sys.exit(1)

    print("\n🎭 Drifting Away — Automated Play Tester")
    print(f"   Model: {ANTHROPIC_MODEL}")
    print(f"   Drift Strength: {MISINTERPRET_STRENGTH}")

    for run in range(1, args.runs + 1):
        topic = args.topic or load_random_topic(args.lang)
        await run_conversation(topic, args.lang, args.turns, run)


if __name__ == "__main__":
    asyncio.run(main())
