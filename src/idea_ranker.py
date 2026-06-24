"""AI企画ランキングモジュール (Phase 3)

公式情報から企画候補を100点満点で評価する。
"""

from datetime import datetime, timedelta
from pathlib import Path

import yaml

from person_database import classify_persons

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_ranking_rules() -> dict:
    with open(CONFIG_DIR / "ranking_rules.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_person_keywords() -> dict:
    with open(CONFIG_DIR / "person_keywords.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_forbidden_expressions(text: str) -> list[str]:
    """禁止表現チェック"""
    config = load_person_keywords()
    forbidden = config.get("forbidden_expressions", [])
    found = [expr for expr in forbidden if expr in text]
    return found


def score_timeliness(entry: dict) -> int:
    """速報性スコア (最大12点)"""
    date_text = entry.get("date_text", "")
    try:
        if len(date_text) == 10:
            entry_date = datetime.strptime(date_text, "%Y-%m-%d")
        else:
            entry_date = datetime.now()
    except ValueError:
        entry_date = datetime.now()

    delta = (datetime.now() - entry_date).days

    if delta <= 1:
        return 12
    elif delta <= 2:
        return 9
    elif delta <= 7:
        return 6
    else:
        return 3


def score_person_popularity(persons: list[str]) -> int:
    """人物人気スコア (最大10点)"""
    rules = load_ranking_rules()
    person_scores = rules["scoring"]["categories"]["人物人気"]["person_scores"]

    if not persons:
        return 3

    return max(person_scores.get(p, 4) for p in persons)


def score_material(entry: dict) -> int:
    """公式素材の使いやすさスコア (最大8点)"""
    urls = entry.get("urls", [])
    has_material = entry.get("has_official_material", False)

    if has_material and urls:
        return 8
    elif urls:
        return 5
    else:
        return 2


def score_shorts_suitability(entry: dict) -> int:
    """Shorts適性スコア (最大8点)"""
    content = entry.get("content", "")
    score = 4

    if len(content) < 200:
        score += 2
    if any(kw in content for kw in ["訪問", "お出まし", "ご挨拶", "握手", "笑顔"]):
        score += 2

    return min(score, 8)


def score_long_suitability(entry: dict) -> int:
    """長尺適性スコア (最大8点)"""
    content = entry.get("content", "")
    score = 4

    if len(content) > 100:
        score += 2
    if any(kw in content for kw in ["式典", "儀式", "外国", "国賓", "晩餐", "歴史"]):
        score += 2

    return min(score, 8)


def score_tiktok_suitability(entry: dict) -> int:
    """TikTok適性スコア (最大6点)"""
    content = entry.get("content", "")
    score = 3

    if any(kw in content for kw in ["愛子", "佳子", "悠仁"]):
        score += 2
    if entry.get("has_official_material"):
        score += 1

    return min(score, 6)


def score_target_audience(entry: dict, persons: list[str]) -> int:
    """65歳以上女性視聴者との相性スコア (最大12点)"""
    content = entry.get("content", "")
    score = 6

    warm_keywords = ["交流", "訪問", "お声", "笑顔", "お言葉", "見舞", "慰問"]
    if any(kw in content for kw in warm_keywords):
        score += 3

    popular_persons = ["愛子さま", "皇后陛下", "天皇皇后両陛下", "上皇后陛下"]
    if any(p in popular_persons for p in persons):
        score += 3

    return min(score, 12)


def score_safety(entry: dict) -> int:
    """安全性スコア (最大10点)"""
    content = entry.get("content", "")
    source = entry.get("source", "")

    score = 7

    if "宮内庁" in source or "公式" in source:
        score += 3

    forbidden = check_forbidden_expressions(content)
    score -= len(forbidden) * 2

    return max(score, 0)


def score_rights_risk(entry: dict) -> int:
    """権利リスクの低さスコア (最大10点)"""
    urls = entry.get("urls", [])
    source = entry.get("source", "")

    score = 6

    if "宮内庁" in source:
        score += 2
    if urls and all("kunaicho.go.jp" in u for u in urls):
        score += 2

    return min(score, 10)


def score_emotional_appeal(entry: dict) -> int:
    """感情訴求スコア (最大8点)"""
    content = entry.get("content", "")
    score = 4

    emotional_keywords = ["交流", "笑顔", "お声がけ", "温か", "心", "感謝", "祈り"]
    matches = sum(1 for kw in emotional_keywords if kw in content)
    score += min(matches * 2, 4)

    return min(score, 8)


def score_search_demand(entry: dict, persons: list[str]) -> int:
    """検索需要スコア (最大4点)"""
    score = 2

    high_demand = ["愛子さま", "佳子さま", "天皇皇后両陛下"]
    if any(p in high_demand for p in persons):
        score += 2

    return min(score, 4)


def score_production_ease(entry: dict) -> int:
    """制作しやすさスコア (最大4点)"""
    score = 2

    if entry.get("has_official_material"):
        score += 1
    if entry.get("urls"):
        score += 1

    return min(score, 4)


def rank_entry(entry: dict) -> dict:
    """エントリを100点満点で評価する"""
    content = entry.get("content", "")
    persons = classify_persons(content)

    scores = {
        "速報性": score_timeliness(entry),
        "人物人気": score_person_popularity(persons),
        "公式素材の使いやすさ": score_material(entry),
        "Shorts適性": score_shorts_suitability(entry),
        "長尺適性": score_long_suitability(entry),
        "TikTok適性": score_tiktok_suitability(entry),
        "65歳以上女性視聴者との相性": score_target_audience(entry, persons),
        "安全性": score_safety(entry),
        "権利リスクの低さ": score_rights_risk(entry),
        "感情訴求": score_emotional_appeal(entry),
        "検索需要": score_search_demand(entry, persons),
        "制作しやすさ": score_production_ease(entry),
    }

    total = sum(scores.values())

    reasons = []
    if persons:
        reasons.append(f"{'・'.join(persons)}関連で人物関心が高い")
    if scores["速報性"] >= 9:
        reasons.append("直近の公式情報と結びついている")
    if scores["公式素材の使いやすさ"] >= 6:
        reasons.append("公式素材が使用可能")
    if scores["Shorts適性"] >= 6:
        reasons.append("Shorts冒頭3秒で引きが作りやすい")
    if scores["長尺適性"] >= 6:
        reasons.append("長尺では背景解説に広げられる")
    if scores["権利リスクの低さ"] >= 8:
        reasons.append("権利リスクが低い")
    if scores["安全性"] >= 8:
        reasons.append("安全性が高い")

    shorts_score = scores["Shorts適性"]
    long_score = scores["長尺適性"]
    if shorts_score >= 6 and long_score >= 6:
        recommendation = "Shorts先行 → 長尺化 → TikTok転用"
    elif long_score >= 6:
        recommendation = "長尺のみ制作"
    elif shorts_score >= 6:
        recommendation = "Shortsのみ制作 → TikTok転用"
    else:
        recommendation = "企画内容を精査して判断"

    forbidden = check_forbidden_expressions(content)

    return {
        "content": content[:100],
        "persons": persons,
        "total_score": total,
        "scores": scores,
        "reasons": reasons,
        "recommendation": recommendation,
        "forbidden_expressions_found": forbidden,
        "warnings": [f"禁止表現「{e}」が含まれています" for e in forbidden],
    }


def rank_entries(entries: list[dict]) -> list[dict]:
    """複数エントリをランキングする"""
    ranked = [rank_entry(e) for e in entries]
    ranked.sort(key=lambda x: x["total_score"], reverse=True)

    for i, r in enumerate(ranked, 1):
        r["rank"] = i

    return ranked


if __name__ == "__main__":
    test = {
        "content": "天皇皇后両陛下が国賓として訪日されたオランダ国王夫妻と御所で面会された",
        "date_text": datetime.now().strftime("%Y-%m-%d"),
        "urls": ["https://www.kunaicho.go.jp/example"],
        "source": "宮内庁公式HP",
        "has_official_material": True,
    }
    result = rank_entry(test)
    print(f"企画価値: {result['total_score']}点")
    print("理由:")
    for r in result["reasons"]:
        print(f"  - {r}")
    print(f"推奨: {result['recommendation']}")
