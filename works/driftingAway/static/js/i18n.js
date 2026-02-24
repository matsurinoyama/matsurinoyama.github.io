/**
 * Drifting Away — Internationalisation (i18n)
 * Default language: Japanese (ja). English (en) available via 'A' key.
 *
 * Usage:
 *   i18n.t("idle.title")          → current-language string
 *   i18n.setLang("en")            → switch to English
 *   i18n.lang                     → current language code
 */

const i18n = (() => {
  const strings = {
    ja: {
      // ── Titles ──────────────────────────────────────────────────
      title: "離れていく",
      "title.player": "離れていく",
      "title.spectator": "離れていく",
      "title.control": "離れていく — コントロールパネル",

      // ── Player: Idle ────────────────────────────────────────────
      "idle.title": "離れていく",
      "idle.putOnEarmuffs": "イヤーマフをつけてください",
      "idle.pressButton": "準備ができたらボタンを押してください",

      // ── Player: Waiting ─────────────────────────────────────────
      "waiting.title": "準備中",
      "waiting.forOther": "もう一人のプレイヤーを待っています",
      "waiting.otherReady":
        "相手の準備ができました！ボタンを押して始めましょう",

      // ── Player: Prompt Select ───────────────────────────────────
      "prompt.otherChoosing": "相手が話題を選んでいます",
      "prompt.hint":
        "← 前の話題\u00a0\u00a0\u00a0● 話題決定\u00a0\u00a0\u00a0新しい話題 →",

      // ── Player: Conversation ────────────────────────────────────
      "ptt.label": "長押しで話す",
      "ptt.holdDot": "●",
      "topic.label": "元の話題",

      // ── Player: Reveal ──────────────────────────────────────────
      "reveal.title": "終了！",
      "reveal.subtitle": "イヤーマフを外して、お互いに話してみましょう！",

      // ── Player: Reset ───────────────────────────────────────────
      "reset.title": "お疲れさまでした！",
      "reset.preparing": "次のラウンドを準備中",

      // ── Player: Mic Setup ───────────────────────────────────────
      "mic.title": "🎙 マイクの設定",
      "mic.selectFor": "プレイヤー{id}のマイクを選択してください",
      "mic.requesting": "マイクへのアクセスを要求中…",
      "mic.noMics":
        "マイクが見つかりません。USBマイクを接続して更新してください。",
      "mic.test": "🔊 テスト",
      "mic.stopTest": "⏹ テスト停止",
      "mic.confirm": "✓ 確認",
      "mic.hint":
        "この設定はこのブラウザに保存されます。変更するには/player/{id}を再度開いてください。",

      // ── Spectator ───────────────────────────────────────────────
      "spectator.title": "離れていく",
      "spectator.subtitle":
        "ミスコミュニケーションについての体験型インスタレーション",
      "spectator.description":
        "二人が会話をしている。だが、お互いの声は直接聞こえない。AIがメッセージを少しだけ変えてから相手に届ける。会話が少しずつずれていく様子をご覧ください。",
      "spectator.waitingForPlayers": "プレイヤーの参加を待っています",
      "spectator.nextRound": "次のラウンドがまもなく始まります",
      "spectator.p1Ready": "プレイヤー1が準備完了、プレイヤー2を待っています",
      "spectator.p2Ready": "プレイヤー2が準備完了、プレイヤー1を待っています",
      "spectator.bothReady": "両プレイヤー準備完了",
      "spectator.deciding": "プレイヤー{n}が話題を選んでいます",
      "spectator.player1": "プレイヤー1",
      "spectator.player2": "プレイヤー2",
      "spectator.originalTopic": "元の話題",

      // ── Control Panel ───────────────────────────────────────────
      "control.title": "🎛 コントロールパネル",
      "control.start": "▶ ゲーム開始",
      "control.reveal": "⏭ 強制リビール（タイマースキップ）",
      "control.reset": "↺ ラウンドリセット",
      "control.status": "フェーズ: idle ｜ クライアント: 0",
      "control.screenUrls": "スクリーンURL：",
      "control.debugTitle": "🐛 デバッグ・トランスクリプト",
      "control.waitingForSpeech": "発話を待っています…",
      "control.clearLog": "ログをクリア",
      "control.language": "🌐 言語",
      "control.langJa": "日本語",
      "control.langEn": "English",
    },

    en: {
      // ── Titles ──────────────────────────────────────────────────
      title: "Drifting Away",
      "title.player": "Drifting Away",
      "title.spectator": "Drifting Away",
      "title.control": "Drifting Away — Control Panel",

      // ── Player: Idle ────────────────────────────────────────────
      "idle.title": "Drifting Away",
      "idle.putOnEarmuffs": "Put on your earmuffs",
      "idle.pressButton": "Press any button when you are ready",

      // ── Player: Waiting ─────────────────────────────────────────
      "waiting.title": "Ready!",
      "waiting.forOther": "Waiting for the other player",
      "waiting.otherReady":
        "The other player is ready! Press any button to begin",

      // ── Player: Prompt Select ───────────────────────────────────
      "prompt.otherChoosing": "The other player is choosing a topic",
      "prompt.hint":
        "\u2190 Previous prompt\u00a0\u00a0\u00a0\u25cf Select prompt\u00a0\u00a0\u00a0Generate new prompt \u2192",

      // ── Player: Conversation ────────────────────────────────────
      "ptt.label": "Hold to talk",
      "ptt.holdDot": "●",
      "topic.label": "Original Topic",

      // ── Player: Reveal ──────────────────────────────────────────
      "reveal.title": "Time's Up!",
      "reveal.subtitle": "Take off your earmuffs and talk to each other!",

      // ── Player: Reset ───────────────────────────────────────────
      "reset.title": "Thanks for playing!",
      "reset.preparing": "Preparing for the next round",

      // ── Player: Mic Setup ───────────────────────────────────────
      "mic.title": "🎙 Microphone Setup",
      "mic.selectFor": "Select the microphone for Player {id}",
      "mic.requesting": "Requesting mic access…",
      "mic.noMics":
        "No microphones found. Please connect a USB mic and refresh.",
      "mic.test": "🔊 Test",
      "mic.stopTest": "⏹ Stop test",
      "mic.confirm": "✓ Confirm",
      "mic.hint":
        "This choice is saved for this browser. Reopen /player/{id} to change it.",

      // ── Spectator ───────────────────────────────────────────────
      "spectator.title": "Drifting Away",
      "spectator.subtitle":
        "An interactive installation about miscommunication",
      "spectator.description":
        "Two people are having a conversation — but neither hears the other directly. An AI subtly alters every message before it reaches the other side. Watch as the conversation slowly drifts apart.",
      "spectator.waitingForPlayers": "Waiting for players to start",
      "spectator.nextRound": "Next round starting soon",
      "spectator.p1Ready": "Player 1 is ready, waiting for Player 2",
      "spectator.p2Ready": "Player 2 is ready, waiting for Player 1",
      "spectator.bothReady": "Both players ready",
      "spectator.deciding": "Player {n} is deciding the topic",
      "spectator.player1": "Player 1",
      "spectator.player2": "Player 2",
      "spectator.originalTopic": "Original Topic",

      // ── Control Panel ───────────────────────────────────────────
      "control.title": "🎛 Control Panel",
      "control.start": "▶ Start Game",
      "control.reveal": "⏭ Force Reveal (skip timer)",
      "control.reset": "↺ Reset Round",
      "control.status": "Phase: idle  |  Clients: 0",
      "control.screenUrls": "Screen URLs:",
      "control.debugTitle": "🐛 Debug Transcripts",
      "control.waitingForSpeech": "Waiting for speech…",
      "control.clearLog": "Clear log",
      "control.language": "🌐 Language",
      "control.langJa": "日本語",
      "control.langEn": "English",
    },
  };

  let _lang = "ja"; // default language
  const _listeners = [];

  function t(key, params) {
    const s =
      (strings[_lang] && strings[_lang][key]) ||
      (strings["en"] && strings["en"][key]) ||
      key;
    if (!params) return s;
    return s.replace(/\{(\w+)\}/g, (_, k) =>
      params[k] !== undefined ? params[k] : `{${k}}`,
    );
  }

  function setLang(code) {
    if (code === _lang) return;
    if (!strings[code]) return;
    _lang = code;
    _listeners.forEach((fn) => fn(_lang));
  }

  function onLangChange(fn) {
    _listeners.push(fn);
  }

  return {
    t,
    setLang,
    onLangChange,
    get lang() {
      return _lang;
    },
    get strings() {
      return strings;
    },
  };
})();
