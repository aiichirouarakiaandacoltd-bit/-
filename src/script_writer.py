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
    partial = filtered["partial"]
    channel = cfg.CHANNEL_NAME

    lines = []

    lines.append("【オープニング】")
    lines.append("")
    lines.append(f"「{channel}」をご視聴いただきありがとうございます。")
    lines.append("")

    if usable:
        lines.append(f"今回は「{topic}」について、")
        lines.append("公式の記録や資料をもとに、丁寧にお伝えしてまいります。")
        lines.append("")
        lines.append(f"皆さまは、「{topic}」についてご存じでしょうか。")
        lines.append("その背景には、深い意味が込められています。")
        lines.append("この動画でお伝えする内容は、すべて公式の資料に基づいています。")
        lines.append("公式の記録をひもときながら、順を追って、一つひとつ見ていきましょう。")
        lines.append("ぜひ最後までお付き合いください。")
    else:
        lines.append(f"今回は「{topic}」についてお話しいたします。")
        lines.append("")
        lines.append("※ 本テーマについては出典の確認が必要です。")
        lines.append("※ 以下は台本の構成案であり、事実確認後に内容を確定してください。")
    lines.append("")

    if usable:
        seen_excerpts = set()
        context_idx = 0
        chapter_num = 1
        chapter_size = 3

        for chunk_start in range(0, len(usable), chapter_size):
            chunk = usable[chunk_start:chunk_start + chapter_size]
            lines.append(f"【第{_num_kanji(chapter_num)}章】")
            lines.append("")

            if chapter_num == 1:
                lines.append("まずは、基本的な事実から確認してまいりましょう。")
                lines.append("公式の記録に記された内容を、一つひとつたどっていきます。")
            elif chapter_num == 2:
                lines.append("ここからは、さらに詳しい背景を見てまいりましょう。")
                lines.append("公式の資料から、その由来をたどっていきます。")
            else:
                lines.append("最後に、もう一つ大切なことをお伝えいたします。")
                lines.append("ここまでの内容を踏まえて、もう一歩深く見てまいりましょう。")
            lines.append("")

            for i, fact in enumerate(chunk):
                claim = fact.get("claim", "")
                excerpt = fact.get("verified_excerpt", "")
                source_name = fact.get("source_name", "")

                if i == 0 and chapter_num == 1:
                    lines.append(f"まず、{claim}。")
                elif i == 0:
                    lines.append(f"{claim}。")
                elif i == 1:
                    lines.append(f"そして、{claim}。")
                else:
                    lines.append(f"さらに、{claim}。")
                lines.append("")

                if excerpt and excerpt not in seen_excerpts:
                    seen_excerpts.add(excerpt)
                    if source_name:
                        lines.append(f"{source_name}には、次のように記されています。")
                    else:
                        lines.append("公式の記録には、次のように記されています。")
                    lines.append("")
                    lines.append(f"「{excerpt}」")
                    lines.append("")
                    lines.append(_excerpt_context(fact, context_idx))
                    lines.append("")
                    context_idx += 1
                elif excerpt and excerpt in seen_excerpts:
                    if source_name:
                        lines.append(
                            f"これは、先ほどご紹介した{source_name}の記録でも"
                            "確認されている通りです。"
                        )
                    else:
                        lines.append(
                            "これは、先ほどご紹介した記録でも確認されている通りです。"
                        )
                    lines.append("同じ公式の記録のなかに、この事実も明記されています。")
                    lines.append("")

            if chunk_start + chapter_size < len(usable):
                lines.append("続いて、さらに詳しく見てまいりましょう。")
                lines.append("次の公式資料にも、大切な事実が記されています。")
                lines.append("")

            chapter_num += 1

        if len(usable) >= 3:
            lines.append("このテーマには、公式の記録をもとに確認できる、多くの事実があります。")
            lines.append("それぞれの記録が、一つの大きな物語を伝えてくれています。")
            lines.append("")
            lines.append("【まとめ】")
            lines.append("")
            lines.append(f"ここまで、「{topic}」について、")
            lines.append(f"{len(usable)}つの公式資料から確認してまいりました。")
            lines.append("すべて公式の記録に基づく事実のみをお伝えいたしました。")
            lines.append("一つひとつの事実が、このテーマの深い背景を伝えてくれています。")
            lines.append("")

        if partial:
            usable_partial = [f for f in partial if f.get("usable_in_script")]
            if usable_partial:
                lines.append(f"【第{_num_kanji(chapter_num)}章　補足】")
                lines.append("")
                lines.append("最後に、補足としてお伝えしたいことがございます。")
                lines.append("")
                for fact in usable_partial:
                    claim = fact.get("claim", "")
                    note = fact.get("notes", "")
                    lines.append(f"{claim}。")
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
    if usable:
        lines.append("公式の記録をもとに、その深い由来をたどってまいりましたが、")
        lines.append("いかがでしたでしょうか。")
        lines.append("公式の記録に基づく事実のみをお伝えいたしましたので、")
        lines.append("安心してお聞きいただけたのではないかと思います。")
        lines.append("この動画が、皆さまの知識の一助となれば幸いです。")
        lines.append("")
    lines.append("最後までご視聴いただき、ありがとうございます。")
    lines.append("チャンネル登録、高評価をいただけますと、大変励みになります。")
    lines.append("また次の動画でお会いしましょう。")
    lines.append("")

    return "\n".join(lines)


def _excerpt_context(fact, index):
    source_type = fact.get("source_type", "")
    if "古典" in source_type:
        return ("この古典の一節が、重要な典拠となっています。\n"
                "長い歴史のなかで受け継がれてきた言葉です。")
    if "ご日程" in source_type:
        return ("この公式のご日程記録に、明確に記されています。\n"
                "公の場で正式に行われた事実が、記録として残されています。")
    if "記者会見" in source_type:
        variants = [
            ("この記者会見の記録から、その経緯を確認することができます。\n"
             "公式の場で語られたお言葉は、大切な記録として残されています。"),
            ("このように、記者会見の場で公式に述べられています。\n"
             "その意味を、一つひとつ丁寧に確認してまいりましょう。"),
            ("この公式の記録が、重要な証左となっています。\n"
             "こうした記者会見の記録は、正確な理解の基礎となります。"),
        ]
        return variants[index % len(variants)]
    variants = [
        ("このように、公式の記録に明確に記されています。\n"
         "こうした公式の事実を一つひとつ確認していくことが大切です。"),
        ("この記録から、その事実を確認することができます。\n"
         "公式の記録をもとに、丁寧にたどっていきましょう。"),
        ("この公式の記録が、重要な背景を示しています。\n"
         "正式な記録に基づいて、事実を確認してまいります。"),
    ]
    return variants[index % len(variants)]


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
        lines.append("その詳しい背景は、長尺動画で丁寧に解説しています。")
    else:
        lines.append(f"「{topic}」について、ご存じですか。")
        lines.append("")
        lines.append("詳しくは長尺動画で解説しています。")

    lines.append(f"ぜひ{channel}で検索してください。")
    lines.append("")

    return "\n".join(lines)


def _build_shorts_02_text(topic, research_data):
    filtered = _filter_confirmed_facts(research_data)
    usable = [f for f in filtered["confirmed"] if f.get("usable_in_script")]
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append(f"「{channel}」をご視聴いただきありがとうございます。")
    lines.append("")
    lines.append(f"「{topic}」の補足です。")
    lines.append("")

    if len(usable) > 2:
        lines.append(f"{usable[-1].get('claim', '')}。")
        lines.append("")
        lines.append("長尺動画ではさらに詳しくお伝えしています。")
    elif usable:
        lines.append(f"{usable[-1].get('claim', '')}。")
        lines.append("")
        lines.append("長尺動画では、より丁寧にお伝えしています。")
    else:
        lines.append("このテーマについて、詳しくは長尺動画をご覧ください。")

    lines.append("")
    lines.append(f"ぜひ{channel}でご覧ください。")
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
