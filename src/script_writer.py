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


def _num_kanji(n):
    kanji = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七"}
    return kanji.get(n, str(n))


def _chars_per_minute():
    speed = cfg.VOICEVOX_SETTINGS.get("speed", 1.0)
    return 350 * speed


def _estimate_seconds(text):
    c = count_narration_chars(text)
    cpm = _chars_per_minute()
    return (c / cpm * 60) if cpm > 0 else 0


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

    # --- Opening ---
    lines.append("【オープニング】")
    lines.append("")
    lines.append(f"「{channel}」をご視聴いただきありがとうございます。")
    lines.append("")
    lines.append("公式事実で、静かな感動を。")
    lines.append("これがこのチャンネルの約束です。")
    lines.append("")

    if usable and section_config:
        lines.append(f"今回は「{topic}」について、")
        lines.append("公式の記録や資料をもとに、お伝えしてまいります。")
        lines.append("")
        if topic_context:
            lines.append(topic_context)
            lines.append("")

        lines.append("本動画では、宮内庁をはじめとする公式機関が公開した記録のみを根拠としています。")
        lines.append("推測や憶測ではなく、記録に残された事実そのものを、丁寧にたどってまいります。")
        lines.append("")

        # Content preview
        if len(section_config) > 1:
            lines.append(f"本動画では、以下の{_num_kanji(len(section_config))}つの章に分けてお伝えしてまいります。")
            lines.append("")
            for idx, section in enumerate(section_config):
                lines.append(f"　{_num_kanji(idx + 1)}、{section.get('title', '')}。")
            lines.append("")
            lines.append("それでは、順にたどってまいりましょう。")
            lines.append("")

        # --- Chapter body ---
        seen_excerpts = set()
        for ch_idx, section in enumerate(section_config):
            title = section.get("title", "")
            fact_ids = section.get("fact_ids", [])

            if ch_idx > 0:
                lines.append(f"続いて、{title}について見てまいりましょう。")
                lines.append("")

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

                # Source context for facts with short narration
                narr_len = len((narration_lead or "") + (narration_after or ""))
                if narr_len < 120:
                    pub = fact.get("official_publisher", "")
                    stype = fact.get("source_type", "")
                    if pub and stype:
                        lines.append(f"この{stype}は、{pub}によって公式に公開されています。")
                        lines.append("")

        # --- Summary / Recap ---
        lines.append("【まとめ】")
        lines.append("")

        # Build the body text so far and check duration
        body_text = "\n".join(lines)
        body_chars = count_narration_chars(body_text)
        body_min = estimate_reading_minutes(body_chars)
        target_min = cfg.NARRATION_TARGET_MIN_MINUTES

        # Add recap section if body is under target duration
        if body_min < target_min and len(section_config) > 1:
            lines.append(f"ここまで、{_num_kanji(len(section_config))}つの章に分けて、")
            lines.append(f"「{topic}」についてお伝えしてまいりました。")
            lines.append("")
            for idx, section in enumerate(section_config):
                s_title = section.get("title", "")
                s_fids = section.get("fact_ids", [])
                first_fact = facts_by_id.get(s_fids[0]) if s_fids else None
                if first_fact:
                    ex = first_fact.get("verified_excerpt", "")
                    claim = first_fact.get("claim", "")
                    src_name = first_fact.get("source_name", "")
                    lines.append(f"{_num_kanji(idx + 1)}つ目の「{s_title}」では、")
                    lines.append(f"{claim}ことを確認いたしました。")
                    if ex and src_name and ex not in claim and ex not in src_name:
                        lines.append(f"{src_name}には「{ex}」と記されています。")
                    lines.append("")
            lines.append("これらの事実は、すべて公式の記録に基づいてお伝えいたしました。")
            lines.append("公式の記録を丁寧にたどることで、確かな事実に基づいた理解を深めていただければ幸いです。")
            lines.append("記録に残された事実をお届けすることが、このチャンネルの約束です。")
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

    # --- Ending ---
    lines.append("【エンディング】")
    lines.append("")
    lines.append(f"以上、「{topic}」についてお伝えいたしました。")
    lines.append("")
    if usable:
        lines.append("出典となる公式の記録をもとに、その歩みをたどってまいりました。")
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


def _build_shorts_generic(topic, research_data, variant):
    """Generic Shorts builder that produces 45-59.5s scripts from fact data.

    variant: 1 uses first facts, 2 uses later facts.
    """
    filtered = _filter_confirmed_facts(research_data)
    usable = [f for f in filtered["confirmed"] if f.get("usable_in_script")]
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append(f"「{channel}」をご視聴いただきありがとうございます。")
    lines.append("")

    if not usable:
        lines.append(f"「{topic}」について、ご存じですか。")
        lines.append("")
        lines.append("詳しくは関連動画からご覧ください。")
        lines.append("")
        return "\n".join(lines)

    if variant == 1:
        facts_to_use = usable[:3]
    else:
        facts_to_use = usable[max(0, len(usable) - 3):]
        if facts_to_use == usable[:3] and len(usable) > 1:
            facts_to_use = usable[1:4]

    primary = facts_to_use[0]
    excerpt = primary.get("verified_excerpt", "")
    claim = primary.get("claim", "")
    source_name = primary.get("source_name", "")

    if variant == 1:
        lines.append(f"今回は「{topic}」についてお伝えします。")
        lines.append("")
        lines.append(f"{claim}。")
        lines.append("")
        if excerpt:
            intro = primary.get("narration_source_intro", "")
            if intro:
                lines.append(intro)
            else:
                lines.append(f"{source_name}には、次のように記されています。")
            lines.append("")
            lines.append(f"「{excerpt}」")
            lines.append("")
    else:
        if excerpt:
            lines.append(f"「{excerpt}」")
            lines.append("")
            if source_name:
                lines.append(f"これは、{source_name}に記されたおことばです。")
                lines.append("")
        else:
            lines.append(f"{claim}。")
            lines.append("")

    if len(facts_to_use) > 1:
        second = facts_to_use[1]
        second_claim = second.get("claim", "")
        second_excerpt = second.get("verified_excerpt", "")
        if variant == 2 and second_excerpt and second_excerpt != excerpt:
            lines.append(f"{second_claim}。")
            lines.append("")
            lines.append(f"「{second_excerpt}」")
            lines.append("")
        else:
            lines.append(f"{second_claim}。")
            lines.append("")

    if len(facts_to_use) > 2:
        third = facts_to_use[2]
        third_claim = third.get("claim", "")
        lines.append(f"{third_claim}。")
        lines.append("")

    lines.append("すべて公式の記録に基づいた事実を、丁寧にお伝えしています。")
    lines.append("")
    lines.append("詳しくは関連動画からご覧ください。")
    lines.append("")

    return "\n".join(lines)


def _build_shorts_01_text(topic, research_data):
    pre_written = research_data.get("shorts_01_text", "")
    if pre_written:
        est = _estimate_seconds(pre_written)
        if est >= cfg.VIDEO_SPECS["shorts"]["duration_min_seconds"]:
            return pre_written

    return _build_shorts_generic(topic, research_data, variant=1)


def _build_shorts_02_text(topic, research_data):
    pre_written = research_data.get("shorts_02_text", "")
    if pre_written:
        est = _estimate_seconds(pre_written)
        if est >= cfg.VIDEO_SPECS["shorts"]["duration_min_seconds"]:
            return pre_written

    return _build_shorts_generic(topic, research_data, variant=2)


def _build_shorts_03_text(topic, research_data):
    pre_written = research_data.get("shorts_03_text", "")
    if pre_written:
        return pre_written
    return ""


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

    text_03 = _build_shorts_03_text(topic, research_data)
    if text_03:
        path_03 = output_dir / "shorts_03_script.txt"
        path_03.write_text(header + text_03, encoding="utf-8")
        return path_01, path_02, path_03

    return path_01, path_02
