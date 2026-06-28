"""企画候補の人気度・参入価値を採点するモジュール"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_scoring_weights():
    path = os.path.join(BASE_DIR, "config", "scoring_weights.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_weights()


def _default_weights():
    return {
        "trend_score": 0.15,
        "velocity_score": 0.20,
        "small_channel_breakout_score": 0.10,
        "shorts_fit_score": 0.15,
        "explanation_value_score": 0.15,
        "repeatability_score": 0.10,
        "source_availability_score": 0.05,
        "rights_risk_score": 0.10,
    }


def score_candidate(video, now=None):
    """候補動画を多角的に採点する"""
    if now is None:
        now = datetime.utcnow()

    scores = {}

    view_count = video.get("view_count", 0)
    like_count = video.get("like_count", 0)
    comment_count = video.get("comment_count", 0)
    published_at = video.get("published_at", "")
    channel_subs = video.get("channel_subscriber_count")

    days_since = _days_since_published(published_at, now)
    if days_since <= 0:
        days_since = 1

    views_per_day = view_count / days_since

    scores["trend_score"] = min(1.0, views_per_day / 100000)

    if days_since <= 7:
        velocity_mult = 3.0
    elif days_since <= 30:
        velocity_mult = 2.0
    elif days_since <= 90:
        velocity_mult = 1.0
    else:
        velocity_mult = 0.5
    scores["velocity_score"] = min(1.0, (views_per_day / 50000) * velocity_mult)

    if channel_subs and channel_subs > 0:
        sub_ratio = view_count / channel_subs
        scores["small_channel_breakout_score"] = min(1.0, sub_ratio / 10)
    else:
        engagement = (like_count + comment_count * 5) / max(view_count, 1)
        scores["small_channel_breakout_score"] = min(1.0, engagement * 10)

    title = video.get("title", "")
    desc = video.get("description", "")
    play_keywords = ["パス", "ダンク", "ブロック", "シュート", "ドライブ", "ステップ",
                     "スリー", "アシスト", "クラッチ", "pass", "dunk", "block", "three",
                     "clutch", "assist", "crossover", "step back"]
    play_match = sum(1 for kw in play_keywords if kw.lower() in (title + desc).lower())
    scores["shorts_fit_score"] = min(1.0, play_match / 3)

    explanation_keywords = ["なぜ", "理由", "解説", "分析", "技術", "コツ",
                            "why", "how", "breakdown", "analysis", "technique"]
    explanation_potential = sum(1 for kw in explanation_keywords if kw.lower() in (title + desc).lower())
    scores["explanation_value_score"] = min(1.0, 0.3 + explanation_potential * 0.2)

    scores["repeatability_score"] = 0.5
    from lib.player import normalize_player_name
    for player_name in _get_priority_players():
        if player_name in title or player_name in desc:
            scores["repeatability_score"] = 0.8
            break

    scores["source_availability_score"] = 0.5

    risk_keywords = ["copyright", "著作権", "削除", "removed", "blocked"]
    risk_count = sum(1 for kw in risk_keywords if kw.lower() in (title + desc).lower())
    scores["rights_risk_score"] = max(0.0, 1.0 - risk_count * 0.3)

    weights = _load_scoring_weights()
    overall = sum(scores.get(k, 0) * weights.get(k, 0) for k in weights)
    scores["overall_score"] = round(overall, 4)

    return scores


def rank_candidates(candidates, now=None):
    """候補リストを採点してランキングする"""
    scored = []
    for video in candidates:
        scores = score_candidate(video, now)
        scored.append({
            **video,
            "scores": scores,
            "overall_score": scores["overall_score"],
        })
    scored.sort(key=lambda x: x["overall_score"], reverse=True)
    return scored


def _days_since_published(published_at, now):
    if not published_at:
        return 30
    try:
        pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        delta = now - pub.replace(tzinfo=None)
        return max(1, delta.days)
    except Exception:
        return 30


def _get_priority_players():
    return [
        "河村勇輝", "八村塁", "レブロン", "カリー", "ウェンバンヤマ",
        "富樫勇樹", "富永啓生", "渡邊雄太", "比江島慎",
        "ドンチッチ", "ヨキッチ", "ギルジャス", "デュラント",
        "エドワーズ", "フラッグ",
    ]
