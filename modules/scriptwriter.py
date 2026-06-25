"""
Script writing module for showa-heisei-video-automation.
Generates long-form and shorts scripts from research results.
"""

import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Characters per second for Japanese narration at 0.92x speed
CHARS_PER_SECOND = 5.0

HEDGING_PHRASES = [
    "一部の家庭では",
    "地域によっては",
    "当時を知る人の証言では",
    "一般的に言われているところでは",
    "多くの家庭では",
    "都市部を中心に",
    "記録によれば",
    "広く知られているように",
]


def estimate_duration_seconds(text):
    """Estimate narration duration from Japanese character count."""
    # Remove stage directions in brackets
    narration_only = re.sub(r"[（\(][^）\)]*[）\)]", "", text)
    narration_only = re.sub(r"\[.*?\]", "", narration_only)
    # Remove blank lines, headers, etc.
    lines = [
        line.strip() for line in narration_only.split("\n")
        if line.strip() and not line.strip().startswith("#")
        and not line.strip().startswith("---")
    ]
    char_count = sum(len(line) for line in lines)
    return char_count / CHARS_PER_SECOND


def extract_narration(script_text):
    """
    Extract narration-only text from a script (remove stage directions,
    headers, and formatting marks).
    """
    lines = script_text.split("\n")
    narration_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines, headers, stage directions, separators
        if not stripped:
            narration_lines.append("")
            continue
        if stripped.startswith("#") or stripped.startswith("---"):
            continue
        if stripped.startswith("（") and stripped.endswith("）"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        # Remove inline stage directions
        cleaned = re.sub(r"[（\(][^）\)]*[）\)]", "", stripped)
        cleaned = re.sub(r"\[.*?\]", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            narration_lines.append(cleaned)
    # Remove consecutive blank lines
    result = []
    prev_blank = False
    for line in narration_lines:
        if line == "":
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    return "\n".join(result).strip()


def _get_fact_text(fact, use_hedging=False):
    """Get the claim text from a fact, optionally with hedging."""
    claim = fact.get("claim", "")
    if use_hedging and fact.get("status") == "PARTIAL":
        # Add appropriate hedging
        if "地域" in claim:
            return f"地域によっては、{claim}"
        elif "家庭" in claim:
            return f"多くの家庭では、{claim}"
        elif "一般" in claim or "普及" in claim:
            return f"広く知られているように、{claim}"
        else:
            return f"当時を知る人の証言では、{claim}"
    return claim


def _select_hedging_phrase(fact):
    """Select appropriate hedging phrase based on fact content."""
    claim = fact.get("claim", "")
    if "地域" in claim or "都市" in claim:
        return "地域によっては"
    if "家庭" in claim:
        return "一部の家庭では"
    if "証言" in claim or "言われ" in claim:
        return "当時を知る人の証言では"
    if "統計" in claim or "普及率" in claim:
        return "記録によれば"
    return "一般的に言われているところでは"


# =============================================================================
# Script Templates for テレビの布カバー topic
# =============================================================================

def _generate_tv_cloth_long_script(facts, topic):
    """Generate long-form script about TV cloth covers."""
    # Organize facts by theme
    price_facts = [f for f in facts if "価格" in f["claim"] or "月収" in f["claim"]
                   or "月給" in f["claim"]]
    dust_facts = [f for f in facts if "ほこり" in f["claim"] or "真空管" in f["claim"]
                  or "静電気" in f["claim"]]
    furniture_facts = [f for f in facts if "応接間" in f["claim"] or "家具" in f["claim"]
                       or "木製" in f["claim"]]
    culture_facts = [f for f in facts if "ミシン" in f["claim"] or "電話" in f["claim"]
                     or "布カバー" in f["claim"] and "文化" in f["claim"]]
    tech_facts = [f for f in facts if "真空管" in f["claim"] and "ブラウン管" in f["claim"]
                  or "液晶" in f["claim"]]
    spread_facts = [f for f in facts if "普及率" in f["claim"] or "NHK" in f["claim"]
                    or "放送" in f["claim"]]
    decline_facts = [f for f in facts if "薄れた" in f["claim"] or "安価" in f["claim"]
                     or "複数台" in f["claim"]]

    script = f"""# {topic}
# 長尺動画台本（8-12分想定）

---

## オープニング（0:00〜0:20）

（BGM: 懐かしい雰囲気のメロディ、静かに）

おばあちゃんの家に遊びに行くと、茶の間にはいつも大きなブラウン管テレビがあった。
そしてそのテレビには、必ずレースの布がかけられていた。

今の若い世代にとっては不思議な光景かもしれません。
なぜ、昔の人はテレビに布をかけていたのか？

実はそこには、当時の暮らしならではの、とても合理的な理由がありました。

今日はその「なぜ」を一緒にひもといていきましょう。

---

## 第1章: テレビは「特別な存在」だった

（BGM: 少しテンポアップ）

まず知っておきたいのは、当時のテレビがどれほど高価なものだったか、ということです。

"""
    # Use price facts
    if price_facts:
        fact = price_facts[0]
        hedge = _select_hedging_phrase(fact) if fact["status"] == "PARTIAL" else ""
        if hedge:
            script += f"{hedge}、昭和30年代の白黒テレビは、当時の一般家庭の月収の3ヶ月分から6ヶ月分もする高級品でした。\n\n"
        else:
            script += "昭和30年代の白黒テレビは、当時の一般家庭の月収の3ヶ月分から6ヶ月分もする高級品でした。\n\n"

    script += """今でいえば、新車を一台買うのに近い感覚です。
家族みんなで相談し、ようやく購入を決めた「一大イベント」だったのです。

"""
    # Use spread facts
    if spread_facts:
        for fact in spread_facts[:1]:
            hedge = _select_hedging_phrase(fact) if fact["status"] == "PARTIAL" else ""
            if hedge:
                script += f"{hedge}、NHKの本放送が始まったのは1953年、昭和28年のこと。\n"
            else:
                script += "NHKの本放送が始まったのは1953年、昭和28年のこと。\n"

    script += """テレビの普及率は1960年頃にはおよそ50％に達し、
1964年の東京オリンピックの前後には約90％にまで広がったとされています。

つまり、テレビは「庶民がようやく手に入れた憧れの品」だったのです。

そんな高価なものを、大切にしたいと思うのは自然なことですよね。

---

## 第2章: ほこりよけという実用的な理由

（BGM: 落ち着いた雰囲気に）

布をかけた理由のひとつに、「ほこりよけ」がありました。
しかもこれは、単なる気持ちの問題ではありません。

"""
    if dust_facts:
        fact = dust_facts[0]
        hedge = _select_hedging_phrase(fact) if fact["status"] == "PARTIAL" else ""
        if hedge:
            script += f"{hedge}、当時のテレビは真空管を使っていたため、非常に発熱が大きかったのです。\n\n"
        else:
            script += "当時のテレビは真空管を使っていたため、非常に発熱が大きかったのです。\n\n"

    script += """真空管が熱を持つと、画面に静電気が発生します。
この静電気が、空気中のほこりを画面に引き寄せてしまう。

視聴していないときに布をかけておけば、画面にほこりが積もるのを防げたのです。

当時の家庭は今ほど気密性が高くなく、窓を開けて過ごすことも多かった。
道路も舗装されていない場所が多く、砂ぼこりが家の中に入り込みやすい環境でした。

布カバーは、決して「おばあちゃんの趣味」ではなく、
テレビを長持ちさせるための、理にかなった知恵だったのです。

---

## 第3章: 家具としてのテレビ

（BGM: 温かみのある雰囲気）

もうひとつ、当時のテレビには今と大きく違う点がありました。
それは、テレビが「家具」だったということです。

"""
    if furniture_facts:
        fact = furniture_facts[0]
        hedge = _select_hedging_phrase(fact) if fact["status"] == "PARTIAL" else ""
        if hedge:
            script += f"{hedge}、初期のテレビは木製の立派なキャビネットに収められていました。\n\n"
        else:
            script += "初期のテレビは木製の立派なキャビネットに収められていました。\n\n"

    script += """まるで高級な箪笥やサイドボードのような佇まい。
応接間や茶の間の、最も目立つ場所に鎮座していたのです。

家具には布をかけるもの。
桐の箪笥には風呂敷を、ピアノにはピアノカバーを。
テレビにも、同じ感覚で布がかけられました。

それは「大切なものを守る」という、日本人の暮らしの中にある自然な行為だったのです。

---

## 第4章: 布をかける文化

（BGM: 穏やかなメロディ）

実は、テレビだけに布をかけていたわけではありません。

"""
    if culture_facts:
        fact = culture_facts[0]
        hedge = _select_hedging_phrase(fact) if fact["status"] == "PARTIAL" else ""
        if hedge:
            script += f"{hedge}、ミシンにも、電話機にも、同じように布やカバーがかけられていました。\n\n"
        else:
            script += "ミシンにも、電話機にも、同じように布やカバーがかけられていました。\n\n"

    script += """炊飯器にだって、使わないときはカバーがかかっていた家庭もありました。

この「高価なものには布をかける」という習慣は、
モノが貴重だった時代の、ごく自然な暮らしの知恵でした。

手編みのレースカバーをかけたり、
お気に入りの布を選んだり。
それは実用性だけでなく、インテリアの楽しみでもあったのです。

---

## 第5章: テレビ技術の変遷と布カバーの終わり

（BGM: やや感傷的な雰囲気に）

では、いつ頃から布をかけなくなったのでしょうか。

"""
    if tech_facts:
        fact = tech_facts[0]
        script += "テレビの技術は、真空管方式からブラウン管、そして液晶やプラズマへと進化していきました。\n\n"

    script += """ブラウン管の時代になると、真空管ほどの発熱はなくなりましたが、
それでも画面の静電気は残っていたため、布カバーの習慣はしばらく続きました。

"""
    if decline_facts:
        fact = decline_facts[0]
        hedge = _select_hedging_phrase(fact) if fact["status"] == "PARTIAL" else ""
        if hedge:
            script += f"{hedge}、転機となったのは1980年代以降。\n\n"
        else:
            script += "転機となったのは1980年代以降。\n\n"

    script += """テレビの価格が大きく下がり、一家に2台、3台と持つのが当たり前になっていきました。

「特別な一台」から「日用品の一つ」へ。
テレビの位置づけが変わるにつれて、布をかける理由も薄れていったのです。

そして平成に入り、薄型の液晶テレビが登場すると、
もはや布をかけるという発想自体が消えていきました。

---

## 最終章: 布の向こうに見えるもの

（BGM: 静かで温かい曲調に）

テレビに布をかけていた理由。
それは、ほこりよけであり、家具を守る習慣であり、
大切なものを大切にする暮らしの表れでした。

今、私たちのスマートフォンにはカバーをつけています。
画面には保護フィルムを貼っています。

形は変わっても、「大切なものを守りたい」という気持ちは、
あの頃と何も変わっていないのかもしれません。

あの布カバーの向こうには、
家族で囲んだ食卓の記憶と、
モノを大切にした時代の温もりが、今も静かに残っています。

（BGM: フェードアウト）

---
# 台本情報
"""

    duration = estimate_duration_seconds(script)
    script += f"# 推定時間: {duration:.0f}秒（約{duration/60:.1f}分）\n"
    script += f"# 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    return script


def _generate_tv_cloth_short1(facts, topic):
    """Generate Shorts 1: pre-release teaser."""
    script = f"""# Shorts 1: 予告ティーザー
# {topic}

---

おばあちゃんの家のテレビに、なぜ布がかかっていたか、知っていますか？

（間を置く）

「ほこりよけでしょ？」

たしかに、それもあります。
でも、本当の理由はもっと深いところにありました。

当時のテレビは、今の感覚でいうと新車と同じくらいの値段。
月給の何ヶ月分もする「家宝」だったのです。

その答えの続きは、本編で。

---
# Shorts情報
"""
    duration = estimate_duration_seconds(script)
    script += f"# 推定時間: {duration:.0f}秒\n"
    script += f"# タイプ: 予告ティーザー（部分的な回答のみ）\n"
    script += f"# 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    return script


def _generate_tv_cloth_short2(facts, topic):
    """Generate Shorts 2: supplementary, modern comparison angle."""
    script = f"""# Shorts 2: 補足動画（現代との比較）
# {topic}

---

昭和の人はテレビに布をかけた。
令和の人はスマホにカバーをつける。

やっていること、実は同じなんです。

昔のテレビは月給の何ヶ月分もした。
今のスマートフォンも、十万円を超えるものが珍しくない。

高価で大切なものを守りたい。
その気持ちは、時代が変わっても変わらない。

ただ一つ違うのは、昭和のテレビカバーには、
おばあちゃんの手編みのレースが使われていたこと。

あの温もりだけは、スマホケースにはないものかもしれません。

---
# Shorts情報
"""
    duration = estimate_duration_seconds(script)
    script += f"# 推定時間: {duration:.0f}秒\n"
    script += f"# タイプ: 補足動画（現代比較の切り口）\n"
    script += f"# 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    return script


# =============================================================================
# Generic Script Generation
# =============================================================================

def _generate_generic_long_script(facts, topic):
    """Generate a generic long-form script for any topic."""
    usable = [f for f in facts if f.get("usable_in_script")]
    confirmed = [f for f in usable if f["status"] == "CONFIRMED"]
    partial = [f for f in usable if f["status"] == "PARTIAL"]

    script = f"""# {topic}
# 長尺動画台本（8-12分想定）

---

## オープニング（0:00〜0:20）

（BGM: 懐かしい雰囲気のメロディ、静かに）

昭和から平成にかけて、当たり前だった暮らしの風景。
今振り返ると、「なぜあんなことをしていたのだろう？」と思うことがあります。

今日のテーマは、「{topic}」。

そこには、当時の人々の知恵と、時代の事情が隠されていました。

---

## 第1章: 時代背景

"""
    for i, fact in enumerate(confirmed[:2]):
        script += f"{fact['claim']}\n\n"

    script += """---

## 第2章: その理由

"""
    for i, fact in enumerate(partial[:3]):
        hedge = _select_hedging_phrase(fact)
        script += f"{hedge}、{fact['claim']}\n\n"

    script += """---

## 第3章: 暮らしの中の位置づけ

この習慣は、単なる個人の好みではなく、
当時の生活環境から生まれた合理的な選択でした。

"""
    for fact in partial[3:5]:
        hedge = _select_hedging_phrase(fact)
        script += f"{hedge}、{fact['claim']}\n\n"

    script += """---

## 第4章: 時代の変化

やがて技術の進歩と生活様式の変化により、
この習慣は少しずつ姿を消していきました。

"""
    for fact in (confirmed[2:] + partial[5:])[:2]:
        script += f"{fact['claim']}\n\n"

    script += f"""---

## 最終章: 今に残るもの

（BGM: 静かで温かい曲調に）

時代は変わり、暮らしの形も変わりました。
しかし、その根底にあった気持ちは、
形を変えて今の私たちの中にも残っているのかもしれません。

（BGM: フェードアウト）

---
# 台本情報
"""
    duration = estimate_duration_seconds(script)
    script += f"# 推定時間: {duration:.0f}秒（約{duration/60:.1f}分）\n"
    script += f"# 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    return script


def _generate_generic_short1(facts, topic):
    """Generate generic Shorts 1."""
    topic_short = topic[:30]
    script = f"""# Shorts 1: 予告ティーザー
# {topic}

---

{topic_short}？

この疑問、考えたことありますか。

実はそこには、当時ならではの合理的な理由がありました。

その答えは…本編で詳しくお話しします。

---
# Shorts情報
"""
    duration = estimate_duration_seconds(script)
    script += f"# 推定時間: {duration:.0f}秒\n"
    script += f"# タイプ: 予告ティーザー\n"
    script += f"# 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    return script


def _generate_generic_short2(facts, topic):
    """Generate generic Shorts 2."""
    script = f"""# Shorts 2: 補足動画
# {topic}

---

昭和と令和。
時代は大きく変わりました。

でも、人の気持ちの根っこの部分は、
実はそんなに変わっていないのかもしれません。

形は違っても、考え方は同じ。
そんな発見が、昭和の暮らしにはたくさん隠れています。

---
# Shorts情報
"""
    duration = estimate_duration_seconds(script)
    script += f"# 推定時間: {duration:.0f}秒\n"
    script += f"# タイプ: 補足動画\n"
    script += f"# 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    return script


# =============================================================================
# Main Entry Points
# =============================================================================

def generate_scripts(topic, facts, mode="production"):
    """
    Generate all scripts (long + 2 shorts) for a topic.

    Args:
        topic: Topic string
        facts: List of usable fact dicts (already filtered)
        mode: "production" or "test"

    Returns:
        dict with script_long, script_short_01, script_short_02 texts
        and their narration-only versions
    """
    logger.info(f"台本生成開始: {topic} (使用可能事実: {len(facts)}件)")

    # Filter to only CONFIRMED and PARTIAL
    usable = [
        f for f in facts
        if f.get("status") in ("CONFIRMED", "PARTIAL")
        and f.get("usable_in_script", False)
    ]

    # Choose template based on topic
    is_tv_cloth = "テレビ" in topic and "布" in topic

    if is_tv_cloth:
        script_long = _generate_tv_cloth_long_script(usable, topic)
        script_short_01 = _generate_tv_cloth_short1(usable, topic)
        script_short_02 = _generate_tv_cloth_short2(usable, topic)
    else:
        script_long = _generate_generic_long_script(usable, topic)
        script_short_01 = _generate_generic_short1(usable, topic)
        script_short_02 = _generate_generic_short2(usable, topic)

    # Generate narration-only versions
    narration_long = extract_narration(script_long)
    narration_short_01 = extract_narration(script_short_01)
    narration_short_02 = extract_narration(script_short_02)

    # Estimate durations
    dur_long = estimate_duration_seconds(script_long)
    dur_short_01 = estimate_duration_seconds(script_short_01)
    dur_short_02 = estimate_duration_seconds(script_short_02)

    logger.info(f"長尺台本: 推定{dur_long:.0f}秒 ({dur_long/60:.1f}分)")
    logger.info(f"Shorts 1: 推定{dur_short_01:.0f}秒")
    logger.info(f"Shorts 2: 推定{dur_short_02:.0f}秒")

    return {
        "script_long": script_long,
        "script_short_01": script_short_01,
        "script_short_02": script_short_02,
        "narration_long": narration_long,
        "narration_short_01": narration_short_01,
        "narration_short_02": narration_short_02,
        "durations": {
            "long_seconds": dur_long,
            "long_minutes": dur_long / 60,
            "short_01_seconds": dur_short_01,
            "short_02_seconds": dur_short_02,
        },
    }


def write_script_outputs(output_dir, scripts):
    """Write all script files to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    files = {
        "script_long.txt": scripts["script_long"],
        "script_short_01.txt": scripts["script_short_01"],
        "script_short_02.txt": scripts["script_short_02"],
        "narration_long.txt": scripts["narration_long"],
        "narration_short_01.txt": scripts["narration_short_01"],
        "narration_short_02.txt": scripts["narration_short_02"],
    }

    paths = {}
    for filename, content in files.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        paths[filename] = filepath
        logger.info(f"台本出力: {filepath}")

    return paths


def run_scriptwriter(topic, research_data, mode, output_dir):
    """
    Main entry point for the scriptwriter module.

    Args:
        topic: Topic string
        research_data: Dict from researcher module (contains usable_facts)
        mode: "production" or "test"
        output_dir: Output directory path

    Returns:
        dict with scripts, durations, and output paths
    """
    usable_facts = research_data.get("usable_facts", [])

    scripts = generate_scripts(topic, usable_facts, mode)
    file_paths = write_script_outputs(output_dir, scripts)

    return {
        "scripts": scripts,
        "durations": scripts["durations"],
        "file_paths": file_paths,
    }
