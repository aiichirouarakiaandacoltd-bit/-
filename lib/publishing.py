"""投稿パッケージ生成モジュール"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HASHTAG_POOL = [
    "#バスケ", "#NBA", "#Bリーグ", "#basketball", "#shorts",
    "#ダンク", "#ブロック", "#アシスト", "#スリーポイント",
    "#バスケットボール", "#NBAハイライト",
]

PLAYER_HASHTAGS = {
    "河村勇輝": ["#河村勇輝", "#YukiKawamura"],
    "八村塁": ["#八村塁", "#RuiHachimura"],
    "レブロン・ジェームズ": ["#レブロン", "#LeBronJames"],
    "ステフィン・カリー": ["#ステフカリー", "#StephCurry"],
    "ビクター・ウェンバンヤマ": ["#ウェンバンヤマ", "#Wembanyama"],
    "富樫勇樹": ["#富樫勇樹", "#YukiTogashi"],
    "富永啓生": ["#富永啓生", "#KeiseiTominaga"],
    "渡邊雄太": ["#渡邊雄太", "#YutaWatanabe"],
    "比江島慎": ["#比江島慎", "#MakotoHiejima"],
    "ルカ・ドンチッチ": ["#ドンチッチ", "#LukaDoncic"],
    "ニコラ・ヨキッチ": ["#ヨキッチ", "#Jokic"],
    "ケビン・デュラント": ["#デュラント", "#KDurant"],
    "アンソニー・エドワーズ": ["#エドワーズ", "#AnthonyEdwards"],
    "クーパー・フラッグ": ["#フラッグ", "#CooperFlagg"],
    "シェイ・ギルジャス＝アレクサンダー": ["#SGA", "#ShaiGA"],
}


def generate_description(player, topic, title, play):
    """YouTube Shorts用の説明文を生成"""
    lines = [
        title,
        "",
        f"{player}の{play}を技術的に解説します。",
        "",
        "チャンネル登録お願いします！",
        "ザ・ダンク - バスケ技術解説Shorts",
        "",
        _generate_hashtag_line(player, play),
    ]
    return "\n".join(lines)


def generate_hashtags(player, play, max_tags=15):
    """ハッシュタグリストを生成"""
    tags = []

    player_tags = PLAYER_HASHTAGS.get(player, [f"#{player.replace('・', '')}"])
    tags.extend(player_tags)

    play_clean = play.replace("・", "")
    tags.append(f"#{play_clean}")

    tags.extend(HASHTAG_POOL)

    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique[:max_tags]


def generate_pinned_comment(player, play, topic):
    """固定コメント文を生成"""
    lines = [
        f"【技術解説】{player}の{play}",
        "",
        f"この動画では{player}の{play}がなぜ効果的なのか、技術的な観点から解説しています。",
        "",
        "質問やリクエストがあればコメントで教えてください！",
        "次回の解説で取り上げるかもしれません。",
        "",
        "チャンネル登録・高評価よろしくお願いします！",
    ]
    return "\n".join(lines)


def generate_publishing_package(player, play, topic, title, output_dir):
    """投稿パッケージ一式を生成"""
    os.makedirs(output_dir, exist_ok=True)

    description = generate_description(player, topic, title, play)
    with open(os.path.join(output_dir, "title.txt"), "w", encoding="utf-8") as f:
        f.write(title)

    with open(os.path.join(output_dir, "description.txt"), "w", encoding="utf-8") as f:
        f.write(description)

    hashtags = generate_hashtags(player, play)
    hashtag_line = " ".join(hashtags)
    with open(os.path.join(output_dir, "hashtags.txt"), "w", encoding="utf-8") as f:
        f.write(hashtag_line)

    pinned = generate_pinned_comment(player, play, topic)
    with open(os.path.join(output_dir, "pinned_comment.txt"), "w", encoding="utf-8") as f:
        f.write(pinned)

    package = {
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "pinned_comment": pinned,
        "player": player,
        "play": play,
        "topic": topic,
        "generated_at": datetime.now().isoformat(),
        "files": {
            "title": "title.txt",
            "description": "description.txt",
            "hashtags": "hashtags.txt",
            "pinned_comment": "pinned_comment.txt",
        },
    }

    with open(os.path.join(output_dir, "publishing_package.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)

    return package


def _generate_hashtag_line(player, play):
    tags = generate_hashtags(player, play, max_tags=10)
    return " ".join(tags)
