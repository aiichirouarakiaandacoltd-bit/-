"""企画生成・分析モジュール"""
import json
import os

THEME_DATABASE = [
    {
        "theme": "なぜ昭和のテレビには布をかけていたのか",
        "category": "暮らし",
        "era": "昭和30〜50年代",
        "scores": {"懐かしさ": 18, "意外性": 14, "なぜの強さ": 14, "経験接点": 16, "タイトル力": 9, "素材調達": 9, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ昔の家には電話が玄関近くにあったのか",
        "category": "暮らし",
        "era": "昭和30〜60年代",
        "scores": {"懐かしさ": 17, "意外性": 13, "なぜの強さ": 13, "経験接点": 16, "タイトル力": 8, "素材調達": 9, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ給食で脱脂粉乳が出たのか",
        "category": "学校",
        "era": "昭和20〜40年代",
        "scores": {"懐かしさ": 16, "意外性": 14, "なぜの強さ": 15, "経験接点": 14, "タイトル力": 9, "素材調達": 8, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ電車でタバコが吸えたのか",
        "category": "交通",
        "era": "昭和〜平成初期",
        "scores": {"懐かしさ": 15, "意外性": 15, "なぜの強さ": 14, "経験接点": 15, "タイトル力": 10, "素材調達": 8, "常緑性": 9, "権利安全": 4},
    },
    {
        "theme": "なぜデパートの屋上に遊園地があったのか",
        "category": "買い物・商売",
        "era": "昭和30〜平成初期",
        "scores": {"懐かしさ": 19, "意外性": 13, "なぜの強さ": 13, "経験接点": 16, "タイトル力": 10, "素材調達": 8, "常緑性": 9, "権利安全": 4},
    },
    {
        "theme": "なぜ公衆電話に行列ができたのか",
        "category": "通信・メディア",
        "era": "昭和40〜平成初期",
        "scores": {"懐かしさ": 17, "意外性": 12, "なぜの強さ": 13, "経験接点": 16, "タイトル力": 8, "素材調達": 9, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ会社の運動会があったのか",
        "category": "仕事",
        "era": "昭和30〜60年代",
        "scores": {"懐かしさ": 16, "意外性": 13, "なぜの強さ": 14, "経験接点": 14, "タイトル力": 8, "素材調達": 8, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ駅に伝言板があったのか",
        "category": "交通",
        "era": "昭和〜平成初期",
        "scores": {"懐かしさ": 18, "意外性": 13, "なぜの強さ": 13, "経験接点": 15, "タイトル力": 9, "素材調達": 8, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ缶切りが必要だったのか",
        "category": "食文化",
        "era": "昭和〜平成初期",
        "scores": {"懐かしさ": 16, "意外性": 14, "なぜの強さ": 14, "経験接点": 16, "タイトル力": 9, "素材調達": 9, "常緑性": 9, "権利安全": 5},
    },
    {
        "theme": "なぜ土曜日も学校があったのか",
        "category": "学校",
        "era": "昭和〜平成初期",
        "scores": {"懐かしさ": 17, "意外性": 12, "なぜの強さ": 14, "経験接点": 17, "タイトル力": 9, "素材調達": 8, "常緑性": 9, "権利安全": 5},
    },
]


def score_theme(theme_data):
    return sum(theme_data["scores"].values())


def generate_idea_analysis(theme, output_dir):
    matched = None
    for t in THEME_DATABASE:
        if t["theme"] == theme:
            matched = t
            break

    if not matched:
        matched = {
            "theme": theme,
            "category": "暮らし",
            "era": "昭和〜平成",
            "scores": {"懐かしさ": 16, "意外性": 13, "なぜの強さ": 14, "経験接点": 15, "タイトル力": 9, "素材調達": 8, "常緑性": 9, "権利安全": 4},
        }

    total = score_theme(matched)
    analysis = {
        "theme": matched["theme"],
        "category": matched["category"],
        "era": matched["era"],
        "scores": matched["scores"],
        "total_score": total,
        "adopted": total >= 70,
        "format": {
            "attribute": "昭和・平成の日本人",
            "genre": matched["category"],
            "value": "当時の合理性と時代背景",
            "type": "なぜ解説",
        },
        "target_viewer": "45歳以上、昭和・平成を経験した世代",
        "center_pin": f"「{matched['theme'].replace('なぜ', '').replace('のか', '')}」の背景にある時代の合理性",
    }

    path = os.path.join(output_dir, "idea_analysis.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    return analysis


def auto_suggest_themes(count=10):
    ranked = sorted(THEME_DATABASE, key=score_theme, reverse=True)
    return ranked[:count]
