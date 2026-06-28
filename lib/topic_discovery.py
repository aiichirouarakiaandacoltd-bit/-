"""自動企画発掘・選手選定・テーマ決定モジュール"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRIORITY_5_PLAYERS = [
    {"name": "河村勇輝", "plays": ["ノールックパス", "ドライブ", "アシスト", "速攻"],
     "keywords_en": ["Yuki Kawamura", "no look pass", "assist"]},
    {"name": "八村塁", "plays": ["ダンク", "ポストプレー", "ミドルシュート"],
     "keywords_en": ["Rui Hachimura", "dunk", "post"]},
    {"name": "レブロン・ジェームズ", "plays": ["チェイスダウンブロック", "ノールックパス", "ダンク"],
     "keywords_en": ["LeBron James", "chase down block", "dunk"]},
    {"name": "ステフィン・カリー", "plays": ["ディープスリー", "速攻リリース", "ハンドリング"],
     "keywords_en": ["Steph Curry", "deep three", "quick release"]},
    {"name": "ビクター・ウェンバンヤマ", "plays": ["ブロック", "スリーポイント", "リバウンド"],
     "keywords_en": ["Victor Wembanyama", "block", "three"]},
    {"name": "富樫勇樹", "plays": ["ドライブ", "フローター", "ゲームメイク"],
     "keywords_en": ["Yuki Togashi", "drive", "floater"]},
    {"name": "富永啓生", "plays": ["スリーポイント", "キャッチアンドシュート", "速攻"],
     "keywords_en": ["Keisei Tominaga", "three pointer", "catch and shoot"]},
    {"name": "渡邊雄太", "plays": ["ディフェンス", "スティール", "3&D"],
     "keywords_en": ["Yuta Watanabe", "defense", "steal"]},
    {"name": "比江島慎", "plays": ["ユーロステップ", "ドライブ", "ミドルレンジ"],
     "keywords_en": ["Makoto Hiejima", "euro step", "drive"]},
]

PRIORITY_4_PLAYERS = [
    {"name": "ルカ・ドンチッチ", "plays": ["ステップバック", "トリプルダブル", "クラッチ"],
     "keywords_en": ["Luka Doncic", "step back", "clutch"]},
    {"name": "ニコラ・ヨキッチ", "plays": ["ノールックパス", "トリプルダブル", "ポスト"],
     "keywords_en": ["Nikola Jokic", "no look pass", "triple double"]},
    {"name": "シェイ・ギルジャス＝アレクサンダー", "plays": ["ミドルレンジ", "ドライブ", "フリースロー"],
     "keywords_en": ["Shai Gilgeous-Alexander", "midrange", "drive"]},
    {"name": "ケビン・デュラント", "plays": ["ミドルシュート", "アイソレーション", "ブロック不可"],
     "keywords_en": ["Kevin Durant", "midrange", "iso"]},
    {"name": "アンソニー・エドワーズ", "plays": ["ダンク", "アスレティシズム", "クラッチ"],
     "keywords_en": ["Anthony Edwards", "dunk", "athletic"]},
    {"name": "クーパー・フラッグ", "plays": ["オールラウンド", "ディフェンス", "トランジション"],
     "keywords_en": ["Cooper Flagg", "defense", "transition"]},
]

TOPIC_TEMPLATES = [
    "{player}の{play}が守備を崩す理由",
    "{player}の{play}を止められない本当の理由",
    "{player}はなぜ{play}で得点できるのか",
    "{player}の{play}が他の選手と違う理由",
    "なぜ{player}の{play}は成功率が高いのか",
    "{player}が{play}で相手を抜ける仕組み",
    "{player}の{play}が注目される理由",
]

TITLE_TEMPLATES = [
    "{player}の{play}が守備を崩す本当の理由",
    "{player}の{play}を止められない理由",
    "なぜ{player}の{play}は止められないのか",
    "{player}の{play}で守備のタイミングが外れる理由",
    "{player}はなぜ{play}で自由に得点できるのか",
]


def load_topic_history():
    path = os.path.join(BASE_DIR, "state", "topic_history.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"history": []}


def save_topic_history(history_data):
    path = os.path.join(BASE_DIR, "state", "topic_history.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)


def select_player(scored_candidates=None, history=None):
    """スコアと履歴に基づいて選手を自動選定"""
    if history is None:
        history = load_topic_history()

    recent_players = []
    for entry in history.get("history", [])[-10:]:
        recent_players.append(entry.get("selected_player", ""))

    player_scores = {}
    all_players = PRIORITY_5_PLAYERS + PRIORITY_4_PLAYERS

    for i, p in enumerate(all_players):
        name = p["name"]
        base_score = 1.0 if i < len(PRIORITY_5_PLAYERS) else 0.7

        recency_penalty = 0
        for j, rp in enumerate(reversed(recent_players)):
            if rp == name:
                recency_penalty = max(recency_penalty, 0.5 / (j + 1))

        candidate_boost = 0
        if scored_candidates:
            for c in scored_candidates[:20]:
                title = c.get("title", "")
                for keyword in [name] + p.get("keywords_en", []):
                    if keyword.lower() in title.lower():
                        candidate_boost = max(candidate_boost,
                                              c.get("overall_score", 0) * 0.5)
                        break

        player_scores[name] = base_score - recency_penalty + candidate_boost

    sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)

    selected = sorted_players[0][0]
    rejected = [(name, score) for name, score in sorted_players[1:6]]

    return {
        "selected_player": selected,
        "selection_score": sorted_players[0][1],
        "rejected_candidates": [
            {"player": name, "score": score, "reason": "スコアが低い"} for name, score in rejected
        ],
    }


def select_topic(player_name, scored_candidates=None, history=None):
    """選手に基づいてテーマを自動選定"""
    if history is None:
        history = load_topic_history()

    player_info = None
    for p in PRIORITY_5_PLAYERS + PRIORITY_4_PLAYERS:
        if p["name"] == player_name:
            player_info = p
            break

    if not player_info:
        player_info = {"name": player_name, "plays": ["プレー"], "keywords_en": []}

    recent_topics = [e.get("selected_topic", "") for e in history.get("history", [])[-20:]]

    best_play = None
    best_score = -1

    for play in player_info["plays"]:
        topic = f"{player_name}の{play}"
        similarity = sum(1 for rt in recent_topics if play in rt)
        candidate_relevance = 0
        if scored_candidates:
            for c in scored_candidates[:20]:
                title_lower = (c.get("title", "") + c.get("description", "")).lower()
                if play.lower() in title_lower or any(
                    kw.lower() in title_lower for kw in player_info.get("keywords_en", [])
                ):
                    candidate_relevance += c.get("overall_score", 0)

        score = candidate_relevance - similarity * 0.3
        if score > best_score:
            best_score = score
            best_play = play

    if best_play is None:
        best_play = player_info["plays"][0]

    import random
    template = TOPIC_TEMPLATES[hash(player_name + best_play) % len(TOPIC_TEMPLATES)]
    topic = template.format(player=player_name, play=best_play)

    return {
        "selected_play": best_play,
        "selected_topic": topic,
        "selection_reason": f"候補動画との関連性とテーマ重複回避に基づく選定",
    }


def generate_title_candidates(player_name, play, topic):
    """タイトル候補を5案生成し採点"""
    candidates = []
    for template in TITLE_TEMPLATES:
        title = template.format(player=player_name, play=play)
        scores = _score_title(title, player_name, play)
        candidates.append({"title": title, "scores": scores})

    candidates.sort(key=lambda x: x["scores"]["total"], reverse=True)
    return candidates


def select_best_title(candidates, history=None):
    """タイトル候補から最適な1案を選定"""
    if history is None:
        history = load_topic_history()

    past_titles = [e.get("selected_title", "") for e in history.get("history", [])[-50:]]

    for candidate in candidates:
        title = candidate["title"]
        is_duplicate = any(_title_similarity(title, pt) > 0.7 for pt in past_titles)
        if not is_duplicate:
            return {
                "selected_title": title,
                "scores": candidate["scores"],
                "rejected_count": candidates.index(candidate),
            }

    return {
        "selected_title": candidates[0]["title"],
        "scores": candidates[0]["scores"],
        "rejected_count": 0,
    }


def _score_title(title, player_name, play):
    clarity = 0.8 if player_name in title else 0.4
    specificity = 0.8 if play in title else 0.4
    curiosity = 0.7 if any(w in title for w in ["なぜ", "理由", "本当の", "仕組み"]) else 0.4
    shorts_fit = min(1.0, max(0.0, 1.0 - abs(len(title) - 25) / 30))
    truthfulness = 0.9
    originality = 0.7

    banned = ["衝撃", "ヤバすぎる", "神", "世界が震えた", "史上最高"]
    for b in banned:
        if b in title:
            truthfulness -= 0.3
            originality -= 0.3

    total = (clarity + specificity + curiosity + shorts_fit + truthfulness + originality) / 6
    return {
        "clarity": round(clarity, 2),
        "specificity": round(specificity, 2),
        "curiosity": round(curiosity, 2),
        "shorts_fit": round(shorts_fit, 2),
        "truthfulness": round(truthfulness, 2),
        "originality": round(originality, 2),
        "total": round(total, 2),
    }


def _title_similarity(a, b):
    if not a or not b:
        return 0.0
    set_a = set(a)
    set_b = set(b)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def run_auto_topic_selection(scored_candidates=None, history=None):
    """完全自動で選手・テーマ・タイトルを選定"""
    if history is None:
        history = load_topic_history()

    player_result = select_player(scored_candidates, history)
    player_name = player_result["selected_player"]

    topic_result = select_topic(player_name, scored_candidates, history)
    play = topic_result["selected_play"]
    topic = topic_result["selected_topic"]

    title_candidates = generate_title_candidates(player_name, play, topic)
    title_result = select_best_title(title_candidates, history)

    reference_urls = []
    if scored_candidates:
        for c in scored_candidates[:5]:
            reference_urls.append(c.get("url", ""))

    return {
        "selected_player": player_name,
        "selected_play": play,
        "selected_topic": topic,
        "selected_title": title_result["selected_title"],
        "selection_reason": topic_result["selection_reason"],
        "title_scores": title_result["scores"],
        "title_candidates": [c["title"] for c in title_candidates],
        "reference_video_urls": reference_urls,
        "rejected_candidates": player_result["rejected_candidates"],
        "player_selection_score": player_result["selection_score"],
    }
