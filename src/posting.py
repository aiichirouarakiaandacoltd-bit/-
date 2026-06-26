"""Title, description, fixed comment, credits generator."""
from pathlib import Path

import config as cfg


def generate_posting_package(topic, research_data, bgm_config, output_dir):
    """Generate 05_posting_package.md with title candidates, description, fixed comment, credits."""
    output_dir = Path(output_dir)
    lines = []

    lines.append("# 投稿用文面パッケージ")
    lines.append("")
    lines.append(f"企画テーマ: {topic}")
    lines.append(f"チャンネル: {cfg.CHANNEL_NAME}")
    lines.append("")

    lines.append("## タイトル候補（10案）")
    lines.append("")
    titles = _generate_title_candidates(topic, research_data)
    for i, t in enumerate(titles, 1):
        lines.append(f"### 案{i}: {t['title']}")
        lines.append(f"- 種別: {t['category']}")
        lines.append(f"- 狙い: {t['intent']}")
        lines.append(f"- リスク: {t['risk']}")
        lines.append(f"- 採用順位: {t['priority']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 概要欄（description）")
    lines.append("")
    lines.extend(_generate_description_lines(topic, research_data, bgm_config))
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 固定コメント（fixed_comment）")
    lines.append("")
    lines.extend(_generate_fixed_comment_lines(topic))
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## クレジット（credits）")
    lines.append("")
    lines.extend(_generate_credits_lines(research_data, bgm_config))

    content = "\n".join(lines)
    (output_dir / "05_posting_package.md").write_text(content, encoding="utf-8")
    return {"titles": titles, "file": "05_posting_package.md"}


def _generate_title_candidates(topic, research_data):
    key_facts = []
    for f in research_data.get("facts", []):
        if f.get("usable_in_script"):
            key_facts.append(f.get("claim", ""))

    base = topic.replace("――", " ").replace("「", "").replace("」", "")
    short_topic = topic.split("――")[0] if "――" in topic else topic

    titles = [
        {"title": topic, "category": "本命", "intent": "企画テーマそのまま", "risk": "低", "priority": 1},
        {"title": f"知っていますか？{short_topic}", "category": "本命", "intent": "問いかけで関心を引く", "risk": "低", "priority": 2},
        {"title": f"{short_topic}｜公式資料から読み解く", "category": "本命", "intent": "信頼性を訴求", "risk": "低", "priority": 3},
        {"title": f"{short_topic}の意外な背景", "category": "安全", "intent": "軽い驚きで興味喚起", "risk": "低", "priority": 4},
        {"title": f"【解説】{short_topic}", "category": "安全", "intent": "情報整理として訴求", "risk": "低", "priority": 5},
        {"title": f"{short_topic}を丁寧に解説します", "category": "安全", "intent": "安心感を与える", "risk": "低", "priority": 6},
        {"title": f"多くの人が知らない{short_topic}の話", "category": "CTR重視", "intent": "知識欲を刺激", "risk": "中（煽りに見えないよう注意）", "priority": 7},
        {"title": f"日本人として知っておきたい{short_topic}", "category": "CTR重視", "intent": "当事者意識を刺激", "risk": "中", "priority": 8},
        {"title": f"{short_topic} 歴史 由来 解説", "category": "検索性重視", "intent": "検索キーワード網羅", "risk": "低", "priority": 9},
        {"title": f"{short_topic}とは？わかりやすく解説", "category": "検索性重視", "intent": "検索意図に直接対応", "risk": "低", "priority": 10},
    ]
    return titles


def _generate_description_lines(topic, research_data, bgm_config):
    lines = []
    lines.append(f"「{cfg.CHANNEL_NAME}」をご視聴いただきありがとうございます。")
    lines.append("")
    lines.append(f"今回は「{topic}」について、公式資料をもとに丁寧に解説します。")
    lines.append("")
    lines.append("【主な参考資料】")
    for s in research_data.get("sources", []):
        name = s.get("source_name", "")
        url = s.get("source_url")
        if url:
            lines.append(f"・{name}: {url}")
        else:
            lines.append(f"・{name}")
    lines.append("")
    lines.append("【音声】")
    lines.append(f"VOICEVOX: {cfg.VOICEVOX_SETTINGS['speaker_name']}")
    lines.append("")

    bgm_url = bgm_config.get("download_or_reference_url")
    if bgm_url:
        lines.append("【BGM】")
        lines.append(bgm_config.get("credit_text", cfg.BGM_SETTINGS["credit_text"]))
        lines.append("")

    lines.append("※ 本動画の内容は公式資料に基づいていますが、解釈を含む部分があります。")
    lines.append("※ 皇族のAI生成画像は一切使用しておりません。")
    lines.append("")
    lines.append(f"#皇室 #日本 #伝統 #令和 #天皇陛下")
    return lines


def _generate_fixed_comment_lines(topic):
    lines = []
    lines.append(f"ご視聴ありがとうございます。")
    lines.append(f"")
    lines.append(f"今回のテーマについて、皆さまはどのようにお感じになりましたか？")
    lines.append(f"ぜひコメント欄でお聞かせください。")
    lines.append(f"")
    lines.append(f"チャンネル登録・高評価もよろしくお願いいたします。")
    lines.append(f"")
    lines.append(f"※ コメント欄では、温かいやりとりをお願いいたします。")
    lines.append(f"  特定の人物への攻撃や根拠のない憶測はご遠慮ください。")
    return lines


def _generate_credits_lines(research_data, bgm_config):
    lines = []
    lines.append(f"チャンネル: {cfg.CHANNEL_NAME}")
    lines.append(f"音声: VOICEVOX {cfg.VOICEVOX_SETTINGS['speaker_name']}")
    lines.append("")

    bgm_url = bgm_config.get("download_or_reference_url")
    if bgm_url:
        credit = bgm_config.get("credit_text", cfg.BGM_SETTINGS["credit_text"])
        if credit.startswith("BGM:") or credit.startswith("BGM："):
            credit = credit.split(":", 1)[1].strip() if ":" in credit else credit.split("：", 1)[1].strip()
        lines.append(f"BGM: {credit}")
    else:
        lines.append("BGM: 要確認（BGM正式URLが未設定）")
    lines.append("")
    lines.append("素材: 各素材の出典は動画制作指示書を参照")
    lines.append("")
    lines.append("※ 本動画に皇族のAI生成画像は一切使用しておりません。")
    return lines
