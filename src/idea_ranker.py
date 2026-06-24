"""
アイデアランキングモジュール（100点満点）
ranking_rules.yaml のルールに基づいてスコアを計算する
"""

from datetime import datetime, date
from typing import Optional

import yaml

RANKING_RULES_PATH = "config/ranking_rules.yaml"


def _load_rules() -> dict:
    with open(RANKING_RULES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _score_person(person_ids: list[str], rules: dict) -> int:
    """人物スコアを計算する（最大30点）"""
    from src.person_database import get_person_info

    if not person_ids:
        return 0

    rule = rules["scoring"]["person_score"]
    max_score = rule["max"]
    w_pop = rule["weight_popularity"]
    w_aff = rule["weight_audience_affinity"]

    # 複数人物の場合は最高スコアを採用
    best = 0
    for pid in person_ids:
        info = get_person_info(pid)
        if not info:
            continue
        pop = info.get("popularity_score", 5)
        aff = info.get("audience_affinity_65f", 5)
        score = (pop * w_pop + aff * w_aff) / 10 * max_score
        best = max(best, score)

    return round(best)


def _score_event_type(event_type: str, rules: dict) -> int:
    """行事タイプスコアを計算する（最大20点）"""
    scores = rules["scoring"]["event_type_score"]["scores"]
    return scores.get(event_type, scores.get("unknown", 8))


def _score_freshness(item_date: Optional[str], rules: dict) -> int:
    """鮮度スコアを計算する（最大20点）"""
    if not item_date:
        return 5

    rule = rules["scoring"]["freshness_score"]
    try:
        d = date.fromisoformat(item_date)
        days_ago = (date.today() - d).days
    except ValueError:
        return 5

    thresholds = sorted(rule["days_to_score"].items())
    for threshold_days, score in thresholds:
        if days_ago <= int(threshold_days):
            return score

    return 1


def _score_shorts_suitability(person_ids: list[str], event_type: str, rules: dict) -> int:
    """Shorts適合スコアを計算する（最大10点）"""
    from src.person_database import get_safe_formats

    safe_formats = get_safe_formats(person_ids, event_type)
    format_scores = rules["scoring"]["shorts_suitability_score"]["formats"]
    max_score = rules["scoring"]["shorts_suitability_score"]["max"]

    best = 0
    for fmt in safe_formats:
        best = max(best, format_scores.get(fmt, 0))
    return min(best, max_score)


def calculate_score(item: dict, duplicate_result: Optional[dict] = None) -> dict:
    """
    1件の情報アイテムに対してスコアを計算する。

    item に必要なキー:
      - title: str
      - url: str
      - date: str (YYYY-MM-DD)
      - person_ids: list[str]  (identify_persons() の結果)
      - event_type: str        (identify_event_type() の結果)

    返り値: {
      "score": int,
      "rank": str ("A"/"B"/"C"/"D"),
      "rank_label": str,
      "breakdown": {...各スコア内訳...},
    }
    """
    rules = _load_rules()

    person_ids = item.get("person_ids", ["OTHER"])
    event_type = item.get("event_type", "unknown")
    item_date = item.get("date")

    person_score = _score_person(person_ids, rules)
    event_score = _score_event_type(event_type, rules)
    freshness_score = _score_freshness(item_date, rules)
    shorts_score = _score_shorts_suitability(person_ids, event_type, rules)

    penalty = 0
    if duplicate_result:
        penalty = duplicate_result.get("penalty", 0)

    total = max(0, person_score + event_score + freshness_score + shorts_score - penalty)
    total = min(100, total)

    thresholds = rules["scoring"]["thresholds"]
    if total >= thresholds["A"]:
        rank = "A"
    elif total >= thresholds["B"]:
        rank = "B"
    elif total >= thresholds["C"]:
        rank = "C"
    else:
        rank = "D"

    rank_labels = rules.get("rank_labels", {})

    return {
        "score": total,
        "rank": rank,
        "rank_label": rank_labels.get(rank, rank),
        "breakdown": {
            "person": person_score,
            "event_type": event_score,
            "freshness": freshness_score,
            "shorts": shorts_score,
            "penalty": penalty,
        },
    }


def rank_items(items: list[dict]) -> list[dict]:
    """
    情報アイテムのリストをスコアリングして降順ソートして返す。
    各アイテムに person_ids, event_type が必要（事前に identify_persons 等を実行すること）。
    """
    from src.duplicate_checker import run_full_duplicate_check

    scored = []
    for item in items:
        dup = run_full_duplicate_check(item)
        score_result = calculate_score(item, dup)
        scored.append({**item, **score_result, "duplicate_check": dup})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
