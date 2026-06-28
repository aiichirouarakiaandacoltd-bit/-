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

    lines.append("## タイトル候補（5案）")
    lines.append("")
    titles = _generate_title_candidates(topic, research_data)
    for i, t in enumerate(titles, 1):
        lines.append(f"### 案{i}: {t['title']}")
        lines.append(f"- 方向性: {t.get('direction', t['category'])}")
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

    short_topic = topic.split("――")[0] if "――" in topic else topic
    subtitle = topic.split("――")[1] if "――" in topic else ""

    first_excerpt = ""
    if key_facts:
        first_claim = key_facts[0]
        if len(first_claim) > 30:
            first_excerpt = first_claim[:28] + "…"
        else:
            first_excerpt = first_claim

    titles = [
        {
            "title": topic,
            "category": "正攻法",
            "intent": "企画テーマそのまま。検索にも強い正統派タイトル",
            "risk": "低",
            "priority": 1,
            "direction": "正攻法（テーマ直球）",
        },
        {
            "title": f"知っていますか？{short_topic}",
            "category": "問いかけ型",
            "intent": "視聴者に問いかけ、知的好奇心で再生を促す",
            "risk": "低",
            "priority": 2,
            "direction": "問いかけ型（知的好奇心）",
        },
        {
            "title": f"{short_topic}｜公式資料から読み解く",
            "category": "信頼性訴求型",
            "intent": "公式資料ベースであることを明示し、信頼性で差別化",
            "risk": "低",
            "priority": 3,
            "direction": "信頼性訴求型（出典明示）",
        },
        {
            "title": f"【丁寧に解説】{short_topic}",
            "category": "安心感型",
            "intent": "シニア視聴者に「分かりやすそう」と思わせる",
            "risk": "低",
            "priority": 4,
            "direction": "安心感型（シニア向け）",
        },
        {
            "title": f"{short_topic}――記録が語る真実" if not subtitle else f"{short_topic}――{subtitle}",
            "category": "ストーリー型",
            "intent": "物語性・ドキュメンタリー感を演出し興味を引く",
            "risk": "低",
            "priority": 5,
            "direction": "ストーリー型（物語性）",
        },
    ]
    return titles


def _generate_description_lines(topic, research_data, bgm_config):
    lines = []
    lines.append(f"「{cfg.CHANNEL_NAME}」をご視聴いただきありがとうございます。")
    lines.append("")
    lines.append(f"今回は「{topic}」について、公式資料をもとに丁寧に解説します。")
    lines.append("")
    lines.append("【主な参考資料】")
    seen_urls = set()
    seen_names = set()
    for f in research_data.get("facts", []):
        url = f.get("source_url")
        name = f.get("source_name", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            seen_names.add(name)
            lines.append(f"・{name}: {url}")
        elif name and name not in seen_names:
            seen_names.add(name)
            lines.append(f"・{name}")
    lines.append("")
    lines.append("【音声】")
    lines.append(f"VOICEVOX: {cfg.VOICEVOX_SETTINGS['speaker_name']}")
    lines.append("")

    credit_text = bgm_config.get("credit_text", cfg.BGM_SETTINGS["credit_text"])
    lines.append("【BGM】")
    lines.append(credit_text)
    lines.append("")

    lines.append("※ 本動画の内容は公式資料に基づいていますが、解釈を含む部分があります。")
    lines.append("※ 皇族のAI生成画像は一切使用しておりません。")
    lines.append("")
    hashtags = research_data.get("hashtags", "#皇室 #日本 #伝統 #令和 #天皇陛下")
    lines.append(hashtags)
    return lines


def _generate_fixed_comment_lines(topic):
    lines = []
    lines.append(f"ご視聴ありがとうございます。")
    lines.append(f"")
    lines.append(f"「{topic}」について、最も印象に残ったことは何ですか。")
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

    credit_text = bgm_config.get("credit_text", cfg.BGM_SETTINGS["credit_text"])
    lines.append(credit_text)
    lines.append("")
    lines.append("素材: 各素材の出典は動画制作指示書を参照")
    lines.append("")
    lines.append("※ 本動画に皇族のAI生成画像は一切使用しておりません。")
    return lines
