"""Script writing module for long-format and Shorts narration scripts.

Generates complete narration scripts that outsourcers can use directly.
Channel: 日本が誇る皇室物語
Promise: 公式事実で、静かな感動を。
Target audience: 55+ women, especially 65+, smartphone viewers.
"""
from pathlib import Path

import config as cfg


def _filter_confirmed_facts(research_data):
    facts = research_data.get("facts", [])
    return {
        "confirmed": [f for f in facts if f.get("status") == cfg.FactStatus.CONFIRMED],
        "partial": [f for f in facts if f.get("status") == cfg.FactStatus.PARTIAL],
    }


def _build_long_script_text(topic, research_data):
    filtered = _filter_confirmed_facts(research_data)
    confirmed = filtered["confirmed"]
    partial = filtered["partial"]
    channel = cfg.CHANNEL_NAME

    lines = []

    lines.append("【オープニング】")
    lines.append("")
    lines.append(f"{channel}。")
    lines.append("")

    if confirmed:
        lines.append(f"今回は「{topic}」について、公式の記録や資料をもとにお伝えいたします。")
    else:
        lines.append(f"今回は「{topic}」についてお話しいたします。")
        lines.append("")
        lines.append("※ 本テーマについては出典の確認が必要です。")
        lines.append("※ 以下は台本の構成案であり、事実確認後に内容を確定してください。")
    lines.append("")

    if confirmed:
        chapter_num = 1
        lines.append(f"【第{_num_kanji(chapter_num)}章　{topic}とは】")
        lines.append("")
        for fact in confirmed[:3]:
            claim = fact.get("claim", "")
            lines.append(f"{claim}")
            lines.append("")
        chapter_num += 1

        if len(confirmed) > 3:
            lines.append(f"【第{_num_kanji(chapter_num)}章　詳しく見ていきましょう】")
            lines.append("")
            for fact in confirmed[3:6]:
                claim = fact.get("claim", "")
                lines.append(f"{claim}")
                lines.append("")
            chapter_num += 1

        if len(confirmed) > 6:
            lines.append(f"【第{_num_kanji(chapter_num)}章　さらに深く】")
            lines.append("")
            for fact in confirmed[6:]:
                claim = fact.get("claim", "")
                lines.append(f"{claim}")
                lines.append("")
            chapter_num += 1

        if partial:
            lines.append(f"【第{_num_kanji(chapter_num)}章　補足情報】")
            lines.append("")
            for fact in partial:
                claim = fact.get("claim", "")
                note = fact.get("notes", "")
                lines.append(f"{claim}")
                if note:
                    lines.append(f"（※ {note}）")
                lines.append("")
            chapter_num += 1
    else:
        lines.append(f"【第一章　{topic}の概要】")
        lines.append("")
        lines.append(f"「{topic}」というテーマについて、")
        lines.append("まずは基本的な事実からお伝えいたします。")
        lines.append("")
        lines.append("（※ 出典確認後に具体的な内容を記載してください）")
        lines.append("")
        lines.append("【第二章　背景と歴史】")
        lines.append("")
        lines.append("このテーマの背景には、どのような歴史があるのでしょうか。")
        lines.append("")
        lines.append("（※ 出典確認後に具体的な内容を記載してください）")
        lines.append("")
        lines.append("【第三章　現在への影響】")
        lines.append("")
        lines.append("この出来事は、現在の私たちにどのような意味を持つのでしょうか。")
        lines.append("")
        lines.append("（※ 出典確認後に具体的な内容を記載してください）")
        lines.append("")

    lines.append("【エンディング】")
    lines.append("")
    lines.append(f"以上、「{topic}」についてお伝えいたしました。")
    lines.append("")
    lines.append("最後までご視聴いただき、ありがとうございます。")
    lines.append("チャンネル登録、高評価をいただけますと、大変励みになります。")
    lines.append("また次の動画でお会いしましょう。")
    lines.append("")

    return "\n".join(lines)


def _num_kanji(n):
    kanji = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七"}
    return kanji.get(n, str(n))


def _build_shorts_01_text(topic, research_data):
    filtered = _filter_confirmed_facts(research_data)
    confirmed = filtered["confirmed"]
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append(f"「{topic}」")
    lines.append("")

    if confirmed:
        lines.append(f"{confirmed[0].get('claim', '')}")
        lines.append("")
        if len(confirmed) > 1:
            lines.append("実は、この背景には深い理由があるのです。")
        lines.append("")
    else:
        lines.append("このテーマ、ご存じですか？")
        lines.append("")
        lines.append("意外な事実が隠されています。")
        lines.append("")

    lines.append("詳しくは長尺動画で解説しています。")
    lines.append(f"{channel}で検索してください。")
    lines.append("")

    return "\n".join(lines)


def _build_shorts_02_text(topic, research_data):
    filtered = _filter_confirmed_facts(research_data)
    confirmed = filtered["confirmed"]
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append(f"「{topic}」の補足情報です。")
    lines.append("")

    if len(confirmed) > 2:
        lines.append(f"{confirmed[-1].get('claim', '')}")
        lines.append("")
        lines.append("長尺動画では語りきれなかった視点をお伝えしました。")
    else:
        lines.append("このテーマについて、もう少し深くお伝えします。")
        lines.append("")
        lines.append("（※ 出典確認後に内容を記載してください）")

    lines.append("")
    lines.append(f"他の動画も{channel}でご覧ください。")
    lines.append("")

    return "\n".join(lines)


def generate_long_script(topic, research_data, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "long_script.txt"

    script_text = _build_long_script_text(topic, research_data)

    header_lines = [
        f"テーマ: {topic}",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"対象視聴者: {cfg.TARGET_AUDIENCE}",
        f"目標尺: {cfg.VIDEO_SPECS['long']['duration_min_seconds'] // 60}"
        f"～{cfg.VIDEO_SPECS['long']['duration_max_seconds'] // 60}分"
        "（読み上げ約10分を目安）",
        f"ナレーション: VOICEVOX {cfg.VOICEVOX_SETTINGS['speaker_name']}"
        f" speed {cfg.VOICEVOX_SETTINGS['speed']}",
        "",
        "=" * 60,
        "",
    ]

    content = "\n".join(header_lines) + script_text
    file_path.write_text(content, encoding="utf-8")
    return file_path


def generate_shorts_scripts(topic, research_data, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    header = (
        f"テーマ: {topic}\n"
        f"チャンネル: {cfg.CHANNEL_NAME}\n"
        f"対象視聴者: {cfg.TARGET_AUDIENCE}\n"
        f"目標尺: {cfg.VIDEO_SPECS['shorts']['duration_min_seconds']}"
        f"～{cfg.VIDEO_SPECS['shorts']['duration_max_seconds']}秒\n"
        f"ナレーション: VOICEVOX {cfg.VOICEVOX_SETTINGS['speaker_name']}"
        f" speed {cfg.VOICEVOX_SETTINGS['speed']}\n"
        "\n"
        "=" * 60
        + "\n\n"
    )

    text_01 = _build_shorts_01_text(topic, research_data)
    path_01 = output_dir / "shorts_01_script.txt"
    path_01.write_text(header + text_01, encoding="utf-8")

    text_02 = _build_shorts_02_text(topic, research_data)
    path_02 = output_dir / "shorts_02_script.txt"
    path_02.write_text(header + text_02, encoding="utf-8")

    return path_01, path_02
