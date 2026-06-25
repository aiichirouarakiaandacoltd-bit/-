import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAN_TYPES = {
    "super_play": "スーパープレー解説",
    "technique": "技術解説",
    "tactics": "戦術解説",
    "comparison": "比較",
    "record": "記録・データ",
    "trend": "話題・トレンド",
}

PROHIBITED_EXPRESSIONS = [
    "世界中が震えた",
    "全米が絶賛",
    "誰も止められない",
    "史上最高確定",
    "神を超えた",
    "NBAが震えた",
    "NBAが恐れた",
    "世界が恐れた",
    "相手を完全破壊",
    "選手生命終了",
    "本人が絶望した",
    "心が折れた",
]


def generate_script(player, topic, plan_type="technique"):
    from lib.player import normalize_player_name, get_player_info, get_nickname

    canonical = normalize_player_name(player)
    info = get_player_info(canonical)
    nickname = get_nickname(canonical) if info else player

    if plan_type == "technique" and "ノールックパス" in topic:
        return _script_kawamura_no_look(canonical, nickname, info)
    return _script_generic(canonical, nickname, topic, plan_type, info)


def _script_kawamura_no_look(canonical, nickname, info):
    script = {
        "player": canonical,
        "topic": "河村勇輝のノールックパスが守備を崩す理由",
        "plan_type": "technique",
        "plan_type_label": "技術解説",
        "sections": [
            {
                "time": "0-2秒",
                "label": "フック",
                "text": "このパス、本当に見ないで出しているのでしょうか。河村勇輝のノールックパスを解説します。",
            },
            {
                "time": "2-10秒",
                "label": "状況説明",
                "text": "河村勇輝はB.LEAGUEを代表するポイントガードです。身長172センチと小柄ながら、視野の広さとパスセンスで守備を崩します。",
            },
            {
                "time": "10-25秒",
                "label": "技術解説1",
                "text": "ノールックパスの本質は、パスそのものではありません。その前の動きにあります。河村はドライブで守備の注意を引きつけます。ディフェンスが河村に寄った瞬間、味方がフリーになります。",
            },
            {
                "time": "25-40秒",
                "label": "技術解説2",
                "text": "重要なのは視線です。河村はゴール方向を見たまま、横にパスを出します。守備は河村がシュートすると予測しているため、パスへの反応が遅れます。つまり、ノールックパスは見ていないのではなく、見ていないふりをして守備を騙す技術です。",
            },
            {
                "time": "40-52秒",
                "label": "結論",
                "text": "身長のハンデを技術で補う。それが河村勇輝のプレースタイルです。ノールックパスが成功する理由は、その前の駆け引きにあります。",
            },
            {
                "time": "52-57秒",
                "label": "CTA",
                "text": "ザ・ダンクでは、他のプレーも技術視点で解説しています。",
            },
        ],
    }
    return script


def _script_generic(canonical, nickname, topic, plan_type, info):
    team = info.get("team", "") if info else ""
    league = info.get("league", "") if info else ""

    intro = f"{nickname}の{topic}について解説します。" if nickname != canonical else f"{canonical}の{topic}について解説します。"

    script = {
        "player": canonical,
        "topic": topic,
        "plan_type": plan_type,
        "plan_type_label": PLAN_TYPES.get(plan_type, plan_type),
        "sections": [
            {"time": "0-2秒", "label": "フック", "text": intro},
            {"time": "2-10秒", "label": "状況説明", "text": f"{canonical}は{league}の{team}に所属しています。"},
            {"time": "10-40秒", "label": "解説", "text": f"{topic}の技術的なポイントを見ていきましょう。"},
            {"time": "40-52秒", "label": "結論", "text": f"これが{nickname}の強さです。"},
            {"time": "52-57秒", "label": "CTA", "text": "ザ・ダンクでは、他のプレーも解説しています。"},
        ],
    }
    return script


def script_to_narration(script):
    lines = []
    for section in script["sections"]:
        lines.append(section["text"])
    return "\n".join(lines)


def script_to_full_text(script):
    lines = []
    lines.append(f"テーマ: {script['topic']}")
    lines.append(f"選手: {script['player']}")
    lines.append(f"企画タイプ: {script['plan_type_label']}")
    lines.append("")
    for section in script["sections"]:
        lines.append(f"[{section['time']}] {section['label']}")
        lines.append(section["text"])
        lines.append("")
    return "\n".join(lines)


def validate_script(script):
    narration = script_to_narration(script)
    issues = []
    for expr in PROHIBITED_EXPRESSIONS:
        if expr in narration:
            issues.append(f"禁止表現を検出: {expr}")
    return {"ok": len(issues) == 0, "issues": issues}
