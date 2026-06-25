"""Script writing module for long-format and Shorts narration scripts.

Generates complete narration scripts that outsourcers can use directly.
Channel: 日本が誇る皇室物語
Promise: 公式事実で、静かな感動を。
Target audience: 55+ women, especially 65+, smartphone viewers.
"""

import os
from pathlib import Path

import config as cfg


def _fact_label(status):
    """Return cautious language marker for partial facts."""
    if status == cfg.FactStatus.PARTIAL:
        return "（※一部未確認情報を含みます）"
    return ""


def _filter_confirmed_facts(research_data):
    """Extract only CONFIRMED and PARTIAL facts from research data.

    Returns a dict with 'confirmed' and 'partial' lists.
    UNCONFIRMED and REJECTED facts are excluded entirely.
    """
    confirmed = []
    partial = []
    facts = research_data.get("facts", [])
    for fact in facts:
        status = fact.get("status", cfg.FactStatus.UNCONFIRMED)
        if status == cfg.FactStatus.CONFIRMED:
            confirmed.append(fact)
        elif status == cfg.FactStatus.PARTIAL:
            partial.append(fact)
    return {"confirmed": confirmed, "partial": partial}


def _build_long_script_text(topic, research_data):
    """Build the full narration text for a long-format script.

    Target: 8-12 minutes (aim ~10 min read-aloud).
    Structure: opening hook (15-30s), 5-7 chapters, quiet ending.
    """
    filtered = _filter_confirmed_facts(research_data)
    channel = cfg.CHANNEL_NAME
    # Collect partial fact notes for cautious treatment
    partial_notes = [f.get("note", "") for f in filtered["partial"]]

    lines = []

    # --- Opening Hook (15-30 seconds) ---
    lines.append("【オープニング】")
    lines.append("")
    lines.append(f"{channel}。")
    lines.append("")
    lines.append(
        "「愛子」という御名に、どのような願いが込められているか、"
        "ご存じでしょうか。"
    )
    lines.append(
        "そこには、二千年以上前の中国古典『孟子』に記された、"
        "ある深い言葉がありました。"
    )
    lines.append(
        "今回は、敬宮愛子内親王殿下の御名と御称号に秘められた由来を、"
        "公式の記録をもとにお伝えいたします。"
    )
    lines.append("")

    # --- Chapter 1: 導入 ---
    lines.append("【第一章　なぜ御名と御称号が大切なのか】")
    lines.append("")
    lines.append(
        "皇室において、お子様の御名と御称号は、"
        "単なる呼び名ではありません。"
    )
    lines.append(
        "そこには、ご両親の深い願いと、"
        "日本の長い歴史に裏打ちされた伝統が込められています。"
    )
    lines.append(
        "御名は天皇陛下が命名され、"
        "御称号もまた、古典に基づいて選ばれるのが慣例です。"
    )
    lines.append(
        "敬宮愛子内親王殿下の場合も、"
        "その御名と御称号には、明確な典拠がございます。"
    )
    lines.append("")

    # --- Chapter 2: 御名「愛子」の由来 ---
    lines.append("【第二章　御名「愛子」の由来】")
    lines.append("")
    lines.append(
        "「愛子」という御名は、中国の古典『孟子』に由来しています。"
    )
    lines.append(
        "『孟子』離婁章句下に、次のような一節がございます。"
    )
    lines.append("")
    lines.append(
        "「仁者は人を愛し、礼ある者は人を敬う。"
        "人を愛する者は、人恒に之を愛し、"
        "人を敬う者は、人恒に之を敬う。」"
    )
    lines.append("")
    lines.append(
        "この言葉は、「思いやりの心を持つ人は他者を愛し、"
        "礼を大切にする人は他者を敬う。"
        "人を愛する者は、人々からも常に愛され、"
        "人を敬う者は、人々からも常に敬われる」という意味です。"
    )
    lines.append(
        "「愛子」の「愛」は、まさにこの「人を愛する」という"
        "仁の精神から取られたものです。"
    )
    lines.append("")

    # --- Chapter 3: 『孟子』離婁章句下の原文と意味 ---
    lines.append("【第三章　『孟子』離婁章句下の教え】")
    lines.append("")
    lines.append(
        "『孟子』は、紀元前四世紀頃の中国の思想家、孟子の言行を"
        "まとめた書物です。"
    )
    lines.append(
        "儒教の重要な経典「四書」の一つとして、"
        "日本でも古くから広く読まれてきました。"
    )
    lines.append(
        "離婁章句下は、仁と礼の本質について論じた章であり、"
        "人と人との関わりにおいて、"
        "愛と敬いがいかに大切であるかを説いています。"
    )
    lines.append(
        "この章句では、他者への愛情と敬意は、"
        "一方通行ではなく、必ず自分にも返ってくるものだと"
        "教えています。"
    )
    lines.append(
        "皇室がこの古典から御名と御称号を選ばれたことは、"
        "日本と中国の古典文化の深い結びつきを感じさせます。"
    )
    lines.append("")

    # --- Chapter 4: 御称号「敬宮」の由来 ---
    lines.append("【第四章　御称号「敬宮」の由来】")
    lines.append("")
    lines.append(
        "御称号「敬宮」もまた、同じ『孟子』離婁章句下の一節に"
        "由来しています。"
    )
    lines.append(
        "先ほどの「人を愛する者は、人恒に之を愛し、"
        "人を敬う者は、人恒に之を敬う」という言葉の中の、"
        "「敬」の一字が用いられました。"
    )
    lines.append(
        "「敬宮」とは、「人を敬い、人からも敬われる存在」"
        "という深い願いが込められた御称号です。"
    )
    lines.append(
        "御名の「愛」と御称号の「敬」が、"
        "同じ一節から選ばれているという事実は、"
        "この命名がいかに深い思慮のもとに行われたかを物語っています。"
    )
    lines.append("")

    # --- Chapter 5: 皇族の命名の伝統 ---
    lines.append("【第五章　皇族の命名の伝統】")
    lines.append("")
    lines.append(
        "皇族のお子様の御名は、天皇陛下がお決めになります。"
    )
    lines.append(
        "御称号は、皇族のお子様に贈られる特別な呼び名であり、"
        "古くから中国や日本の古典に典拠を求める伝統がございます。"
    )
    lines.append(
        "たとえば、上皇陛下の御称号「継宮」は、"
        "皇統を継承されるという意味が込められていました。"
    )
    lines.append(
        "秋篠宮悠仁親王殿下の「悠仁」という御名もまた、"
        "「ゆったりとした、おおらかな心」を願って命名されたと"
        "報じられています。"
    )
    if partial_notes:
        lines.append(
            "なお、命名の詳細な経緯については、"
            "公式に公表されていない部分もございます。"
        )
    lines.append("")

    # --- Chapter 6: 2001年12月1日の誕生と発表 ---
    lines.append("【第六章　二〇〇一年十二月一日　ご誕生の日】")
    lines.append("")
    lines.append(
        "平成十三年、西暦二〇〇一年十二月一日。"
    )
    lines.append(
        "皇太子殿下（現在の天皇陛下）と"
        "皇太子妃雅子殿下（現在の皇后陛下）の"
        "第一子が、宮内庁病院にてご誕生になりました。"
    )
    lines.append(
        "内親王殿下のご誕生は、宮内庁を通じて速やかに発表され、"
        "日本中が喜びに包まれました。"
    )
    lines.append(
        "御名「愛子」、御称号「敬宮」は、"
        "ご誕生後に正式に発表されました。"
    )
    lines.append(
        "その由来が『孟子』であることも併せて公表され、"
        "多くの国民がその深い意味に感銘を受けたのです。"
    )
    lines.append("")

    # --- Ending: 結び（静かな余韻） ---
    lines.append("【結び】")
    lines.append("")
    lines.append(
        "「人を愛する者は、人からも愛される。"
        "人を敬う者は、人からも敬われる。」"
    )
    lines.append(
        "二千年以上前に記されたこの言葉が、"
        "令和の時代を生きる一人の内親王殿下の御名と御称号に"
        "息づいています。"
    )
    lines.append(
        "敬宮愛子内親王殿下の御名に込められた願いは、"
        "時代を超えて、私たちの心に静かに響いてまいります。"
    )
    lines.append("")
    lines.append(f"{channel}。")
    lines.append("最後までお聴きいただき、ありがとうございました。")
    lines.append(
        "このチャンネルでは、公式の事実に基づいて、"
        "皇室にまつわる物語をお届けしております。"
    )
    lines.append("チャンネル登録をしていただけますと、大変励みになります。")
    lines.append("それでは、また次回の動画でお会いしましょう。")

    return "\n".join(lines)


def _build_shorts_01_text(topic, research_data):
    """Build Shorts 1 script: preview/teaser before long video (45-59s).

    Hook in first 1-2 seconds. Does NOT reveal everything.
    """
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append("【Shorts 01：予告・ティーザー】")
    lines.append("")
    # Hook (first 1-2 seconds)
    lines.append("「愛子」という御名の由来、ご存じですか。")
    lines.append("")
    lines.append(
        "敬宮愛子内親王殿下の御名には、"
        "二千年以上前の中国古典が関わっています。"
    )
    lines.append(
        "その古典とは、儒教の重要な経典『孟子』。"
    )
    lines.append(
        "そこに記された、人と人との深い絆を説く一節が、"
        "御名の「愛」の一字に込められました。"
    )
    lines.append(
        "さらに、御称号「敬宮」にも、"
        "同じ一節から選ばれた深い意味があるのです。"
    )
    lines.append("")
    lines.append(
        "詳しくは、本編動画でお伝えいたします。"
    )
    lines.append(f"{channel}。")

    return "\n".join(lines)


def _build_shorts_02_text(topic, research_data):
    """Build Shorts 2 script: supplement after long video (45-59s).

    Adds something NOT in the long video. Hook in first 1-2 seconds.
    """
    channel = cfg.CHANNEL_NAME

    lines = []
    lines.append("【Shorts 02：補足・深掘り】")
    lines.append("")
    # Hook (first 1-2 seconds)
    lines.append("『孟子』の教えは、御名だけではありません。")
    lines.append("")
    lines.append(
        "本編では、敬宮愛子内親王殿下の御名と御称号の由来を"
        "お伝えいたしました。"
    )
    lines.append(
        "実は、『孟子』は日本の皇室や武家社会において、"
        "古くから帝王学の教科書として読まれてきた書物です。"
    )
    lines.append(
        "江戸時代には、藩校の必読書とされ、"
        "多くの指導者がこの書から人の上に立つ者の心得を学びました。"
    )
    lines.append(
        "「仁者は人を愛し、礼ある者は人を敬う。」"
    )
    lines.append(
        "この言葉は、御名の由来であると同時に、"
        "日本の指導者たちが大切にしてきた精神そのものでもあるのです。"
    )
    lines.append("")
    lines.append(f"{channel}。")
    lines.append("フォローして、次回もお楽しみに。")

    return "\n".join(lines)


def generate_long_script(topic, research_data, output_dir):
    """Write long_script.txt -- a complete narration script for outsourcing.

    Args:
        topic: Topic string for the video.
        research_data: Dict containing 'facts' list with 'status' and 'note' keys.
        output_dir: Path (str or Path) to the output directory.

    Returns:
        Path to the written file.
    """
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
    """Write shorts_01_script.txt and shorts_02_script.txt.

    Shorts 1: preview/teaser before long video (45-59s).
    Shorts 2: supplement after long video (45-59s).

    Args:
        topic: Topic string for the video.
        research_data: Dict containing 'facts' list.
        output_dir: Path (str or Path) to the output directory.

    Returns:
        Tuple of (path_shorts_01, path_shorts_02).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = cfg.VIDEO_SPECS["shorts"]
    header_lines = [
        f"テーマ: {topic}",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"対象視聴者: {cfg.TARGET_AUDIENCE}",
        f"目標尺: {specs['duration_min_seconds']}～{specs['duration_max_seconds']}秒",
        f"アスペクト比: 9:16（{specs['width']}x{specs['height']}）",
        f"ナレーション: VOICEVOX {cfg.VOICEVOX_SETTINGS['speaker_name']}"
        f" speed {cfg.VOICEVOX_SETTINGS['speed']}",
        "",
        "=" * 60,
        "",
    ]
    header = "\n".join(header_lines)

    # Shorts 01
    path_01 = output_dir / "shorts_01_script.txt"
    text_01 = _build_shorts_01_text(topic, research_data)
    path_01.write_text(header + text_01, encoding="utf-8")

    # Shorts 02
    path_02 = output_dir / "shorts_02_script.txt"
    text_02 = _build_shorts_02_text(topic, research_data)
    path_02.write_text(header + text_02, encoding="utf-8")

    return (path_01, path_02)
