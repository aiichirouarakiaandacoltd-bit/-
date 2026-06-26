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
    usable = [f for f in confirmed if f.get("usable_in_script")]
    channel = cfg.CHANNEL_NAME
    facts_by_id = {f["fact_id"]: f for f in usable}
    section_config = research_data.get("section_config", [])
    topic_context = research_data.get("topic_context", "")
    ending_context = research_data.get("ending_context", "")

    lines = []

    lines.append("【オープニング】")
    lines.append("")
    lines.append(f"「{channel}」をご視聴いただきありがとうございます。")
    lines.append("")

    if usable and section_config:
        lines.append(f"今回は「{topic}」について、")
        lines.append("公式の記録や資料をもとに、お伝えしてまいります。")
        lines.append("")
        if topic_context:
            lines.append(topic_context)
            lines.append("")
        lines.append("ぜひ最後までお付き合いください。")
        lines.append("")

        seen_excerpts = set()
        for ch_idx, section in enumerate(section_config):
            title = section.get("title", "")
            fact_ids = section.get("fact_ids", [])
            lines.append(f"【第{_num_kanji(ch_idx + 1)}章　{title}】")
            lines.append("")

            for fact_id in fact_ids:
                fact = facts_by_id.get(fact_id)
                if not fact:
                    continue
                narration_lead = fact.get("narration_lead", "")
                narration_source_intro = fact.get("narration_source_intro", "")
                narration_after = fact.get("narration_after", "")
                excerpt = fact.get("verified_excerpt", "")

                if narration_lead:
                    lines.append(narration_lead)
                    lines.append("")

                if excerpt and excerpt not in seen_excerpts:
                    seen_excerpts.add(excerpt)
                    if narration_source_intro:
                        lines.append(narration_source_intro)
                        lines.append("")
                    lines.append(f"「{excerpt}」")
                    lines.append("")
                elif excerpt and excerpt in seen_excerpts:
                    source_name = fact.get("source_name", "")
                    if source_name:
                        lines.append(
                            f"先ほどご紹介した{source_name}の記録にも記されている通りです。"
                        )
                        lines.append("")

                if narration_after:
                    lines.append(narration_after)
                    lines.append("")

        lines.append("【まとめ】")
        lines.append("")
        if ending_context:
            lines.append(ending_context)
            lines.append("")
    elif usable:
        lines.append(f"今回は「{topic}」について、")
        lines.append("公式の記録や資料をもとに、お伝えしてまいります。")
        lines.append("")
        lines.append("ぜひ最後までお付き合いください。")
        lines.append("")

        seen_excerpts = set()
        for i, fact in enumerate(usable):
            narration_lead = fact.get("narration_lead", fact.get("claim", "") + "。")
            narration_source_intro = fact.get("narration_source_intro", "")
            narration_after = fact.get("narration_after", "")
            excerpt = fact.get("verified_excerpt", "")

            lines.append(narration_lead)
            lines.append("")

            if excerpt and excerpt not in seen_excerpts:
                seen_excerpts.add(excerpt)
                if narration_source_intro:
                    lines.append(narration_source_intro)
                    lines.append("")
                lines.append(f"「{excerpt}」")
                lines.append("")

            if narration_after:
                lines.append(narration_after)
                lines.append("")

        lines.append("【まとめ】")
        lines.append("")
        if ending_context:
            lines.append(ending_context)
            lines.append("")
    else:
        lines.append(f"今回は「{topic}」についてお話しいたします。")
        lines.append("")
        lines.append("※ 本テーマについては出典の確認が必要です。")
        lines.append("※ 以下は台本の構成案であり、事実確認後に内容を確定してください。")
        lines.append("")

    lines.append("【エンディング】")
    lines.append("")
    lines.append(f"以上、「{topic}」についてお伝えいたしました。")
    lines.append("")
    if usable:
        lines.append("公式の記録をもとに、その由来をたどってまいりました。")
        lines.append("この動画が、皆さまの知識の一助となれば幸いです。")
        lines.append("")
    lines.append("最後までご視聴いただき、ありがとうございます。")
    lines.append("チャンネル登録、高評価をいただけますと、大変励みになります。")
    lines.append("また次の動画でお会いしましょう。")
    lines.append("")

    return "\n".join(lines)


def count_narration_chars(script_text):
    count = 0
    for line in script_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("【") and stripped.endswith("】"):
            continue
        if stripped.startswith("※"):
            continue
        if stripped.startswith("（※"):
            continue
        if all(c == "=" for c in stripped):
            continue
        if stripped.startswith("#"):
            continue
        count += len(stripped)
    return count


def estimate_reading_minutes(char_count, speed=None):
    if speed is None:
        speed = cfg.VOICEVOX_SETTINGS.get("speed", 1.0)
    base_chars_per_min = 350
    effective_rate = base_chars_per_min * speed
    return char_count / effective_rate if effective_rate > 0 else 0


def _num_kanji(n):
    kanji = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七"}
    return kanji.get(n, str(n))


def _build_shorts_01_text(topic, research_data):
    pre_written = research_data.get("shorts_01_text", "")
    if pre_written:
        return pre_written

    filtered = _filter_confirmed_facts(research_data)
    usable = [f for f in filtered["confirmed"] if f.get("usable_in_script")]
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append(f"「{channel}」をご視聴いただきありがとうございます。")
    lines.append("")

    if usable:
        lines.append(f"今回は「{topic}」についてお伝えします。")
        lines.append("")
        lines.append(f"{usable[0].get('claim', '')}。")
        lines.append("")
        if len(usable) > 1:
            lines.append(f"そして、{usable[1].get('claim', '')}。")
            lines.append("")
    else:
        lines.append(f"「{topic}」について、ご存じですか。")
        lines.append("")

    lines.append("詳しくは関連動画からご覧ください。")
    lines.append("")

    return "\n".join(lines)


def _build_shorts_02_text(topic, research_data):
    pre_written = research_data.get("shorts_02_text", "")
    if pre_written:
        return pre_written

    filtered = _filter_confirmed_facts(research_data)
    usable = [f for f in filtered["confirmed"] if f.get("usable_in_script")]

    lines = []
    lines.append(f"「{cfg.CHANNEL_NAME}」をご視聴いただきありがとうございます。")
    lines.append("")

    if usable:
        lines.append(f"{usable[-1].get('claim', '')}。")
        lines.append("")
    else:
        lines.append("このテーマについて、詳しくは長尺動画をご覧ください。")

    lines.append("")
    lines.append("詳しくは関連動画からご覧ください。")
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
        + "=" * 60
        + "\n\n"
    )

    text_01 = _build_shorts_01_text(topic, research_data)
    path_01 = output_dir / "shorts_01_script.txt"
    path_01.write_text(header + text_01, encoding="utf-8")

    text_02 = _build_shorts_02_text(topic, research_data)
    path_02 = output_dir / "shorts_02_script.txt"
    path_02.write_text(header + text_02, encoding="utf-8")

    return path_01, path_02
