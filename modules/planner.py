"""
Topic evaluation and planning module for showa-heisei-video-automation.
Evaluates topics against criteria and generates title/thumbnail ideas.
"""

import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BANNED_TITLE_WORDS = [
    "衝撃",
    "激震",
    "日本中が涙",
    "メディアが隠した",
    "誰も知らない真実",
    "昭和は最高だった",
    "今の若者は知らない",
    "現代人には理解できない",
    "世界が驚いた",
]

# Topic knowledge base for scoring and title generation
TOPIC_KNOWLEDGE = {
    "テレビ": {
        "nostalgic_items": ["ブラウン管テレビ", "テレビの布カバー", "チャンネルのダイヤル"],
        "era_keywords": ["昭和30年代", "昭和40年代", "三種の神器"],
        "why_angles": ["高価だったから", "家具だったから", "真空管の熱", "ほこりよけ"],
    },
    "電話": {
        "nostalgic_items": ["黒電話", "ダイヤル式電話", "電話台"],
        "era_keywords": ["昭和40年代", "昭和50年代"],
        "why_angles": ["交換手がいた", "呼び出し電話", "家族共有"],
    },
    "布": {
        "nostalgic_items": ["テレビカバー", "ミシンカバー", "電話カバー", "レースの敷物"],
        "era_keywords": ["昭和の家庭", "応接間"],
        "why_angles": ["ほこりよけ", "装飾", "大切なものを守る文化"],
    },
}


def _extract_topic_keywords(topic):
    """Extract key terms from a topic string for matching."""
    keywords = []
    for key in TOPIC_KNOWLEDGE:
        if key in topic:
            keywords.append(key)
    return keywords


def evaluate_topic(topic, config):
    """
    Evaluate a topic against the configured criteria.

    Args:
        topic: Topic string (e.g., "なぜ昔のテレビには布をかけていたのか")
        config: Full settings config dict

    Returns:
        dict with:
            total_score: int
            max_score: int
            per_criterion: list of dicts
            passed: bool
            threshold: int
    """
    criteria = config.get("planning", {}).get("evaluation_criteria", [])
    threshold = config.get("planning", {}).get("min_score", 70)
    keywords = _extract_topic_keywords(topic)

    per_criterion = []
    total_score = 0
    max_score = 0

    for criterion in criteria:
        name = criterion["name"]
        weight = criterion["weight"]
        max_score += weight

        score = _score_criterion(name, weight, topic, keywords)
        total_score += score
        per_criterion.append({
            "name": name,
            "weight": weight,
            "score": score,
            "ratio": f"{score}/{weight}",
        })

    passed = total_score >= threshold

    return {
        "total_score": total_score,
        "max_score": max_score,
        "per_criterion": per_criterion,
        "passed": passed,
        "threshold": threshold,
    }


def _score_criterion(name, weight, topic, keywords):
    """Score a single criterion for a topic. Returns 0..weight."""
    has_naze = "なぜ" in topic or "どうして" in topic
    has_concrete = len(keywords) > 0
    has_showa_heisei = any(
        w in topic for w in ["昭和", "平成", "昔", "かつて", "当時"]
    )

    scoring = {
        "視聴者適合性": lambda: weight if (has_showa_heisei and has_concrete) else weight * 0.5,
        "懐かしさ": lambda: weight if has_concrete else weight * 0.3,
        "なぜの深さ": lambda: weight if has_naze else weight * 0.2,
        "公式資料の有無": lambda: weight * 0.7,  # Default moderate availability
        "素材調達可能性": lambda: weight * 0.8 if has_concrete else weight * 0.5,
        "権利安全性": lambda: weight * 0.8,  # Default moderate safety
        "長尺化情報量": lambda: weight * 0.7 if has_concrete else weight * 0.4,
        "Shorts分解可能性": lambda: weight * 0.8 if has_naze else weight * 0.5,
        "タイトル・サムネイル": lambda: weight * 0.9 if (has_naze and has_concrete) else weight * 0.5,
        "常緑性": lambda: weight * 0.8 if has_showa_heisei else weight * 0.5,
        "競合差別化": lambda: weight * 0.6,  # Default moderate
        "制作原価": lambda: weight * 0.8,  # Generally low cost
        "再現性": lambda: weight * 0.7,  # Default moderate
    }

    scorer = scoring.get(name)
    if scorer:
        return max(0, min(weight, int(round(scorer()))))
    return int(weight * 0.5)


def generate_title_candidates(topic):
    """
    Generate title candidates for a topic.
    Returns: dict with main_title and alternatives (4 more).

    Rules:
    - Must include "なぜ"
    - Concrete nostalgic item
    - Question about the era
    - Surprising rationality
    - No banned words
    """
    keywords = _extract_topic_keywords(topic)

    # Build titles based on topic analysis
    if "布" in topic and "テレビ" in topic:
        main_title = "なぜ昔のテレビには布をかけていたのか？〜月給数ヶ月分の家電を守る知恵〜"
        alternatives = [
            "なぜ昭和の家庭はテレビに布をかけたのか？真空管時代の合理的な理由",
            "なぜテレビに布カバーをかけていたのか？「家具としてのテレビ」の時代",
            "なぜブラウン管テレビには必ず布がかかっていたのか？ほこりと熱の意外な関係",
            "なぜ昔の家電には布をかける習慣があったのか？テレビ・ミシン・電話の共通点",
        ]
    elif "テレビ" in keywords:
        main_title = f"なぜ昭和のテレビはあんなに大切にされたのか？〜{topic}〜"
        alternatives = [
            f"なぜ昔のテレビは家族の中心だったのか？{topic}の答え",
            f"なぜ昭和の家庭ではテレビが特別だったのか？知られざる理由",
            "なぜテレビは「家具」だったのか？昭和の家電事情を探る",
            f"なぜ当時の人々はテレビをあれほど大切にしたのか？",
        ]
    else:
        # Generic but rule-compliant titles
        topic_core = topic.replace("なぜ", "").replace("？", "").replace(
            "のか", "").strip()
        main_title = f"なぜ{topic_core}のか？〜昭和・平成の意外な合理性〜"
        alternatives = [
            f"なぜ{topic_core}のか？当時の暮らしから見える理由",
            f"なぜ昭和の日本では{topic_core}のか？時代背景を探る",
            f"なぜ{topic_core}のか？知られていなかった合理的な理由",
            f"なぜかつての日本人は{topic_core}のか？その答えは意外にシンプルだった",
        ]

    # Validate no banned words
    all_titles = [main_title] + alternatives
    for i, title in enumerate(all_titles):
        for banned in BANNED_TITLE_WORDS:
            if banned in title:
                logger.warning(
                    f"タイトル候補にNGワードが含まれています: 「{banned}」 in 「{title}」"
                )
                # Replace with safer version
                all_titles[i] = title.replace(banned, "")

    return {
        "main_title": all_titles[0],
        "alternatives": all_titles[1:],
    }


def generate_thumbnail_ideas(topic):
    """
    Generate thumbnail text and layout ideas.
    Returns: dict with text_ideas (3) and layout_ideas (2).
    """
    if "布" in topic and "テレビ" in topic:
        text_ideas = [
            "月給3ヶ月分のテレビ\nなぜ布をかけた？",
            "実は合理的だった\n昭和のテレビカバー",
            "ほこり？熱？装飾？\n布カバーの本当の理由",
        ]
        layout_ideas = [
            {
                "description": "左半分にレースカバーのかかった昭和のブラウン管テレビ、"
                               "右半分に現代の薄型テレビ。中央に大きく「なぜ？」の文字",
                "text_position": "右上",
                "color_scheme": "セピア調の背景に白文字、黄色アクセント",
            },
            {
                "description": "昭和の応接間を再現した背景。テレビに布カバーがかかっている。"
                               "手前に驚いた表情のイラストアイコン",
                "text_position": "下部中央",
                "color_scheme": "温かみのある茶系背景に白縁取り文字",
            },
        ]
    else:
        topic_short = topic[:15] if len(topic) > 15 else topic
        text_ideas = [
            f"昭和の常識\n{topic_short}",
            f"実は合理的だった\n{topic_short}",
            f"なぜ？\n{topic_short}",
        ]
        layout_ideas = [
            {
                "description": "昭和の風景写真を背景に、テーマに関連するアイテムを"
                               "中央に配置。大きな「なぜ？」の文字",
                "text_position": "右上",
                "color_scheme": "セピア調背景に白文字、黄色アクセント",
            },
            {
                "description": "ビフォーアフター形式。左に昭和、右に現代の対比。"
                               "中央に矢印と疑問符",
                "text_position": "下部中央",
                "color_scheme": "暖色系背景に白縁取り文字",
            },
        ]

    return {
        "text_ideas": text_ideas,
        "layout_ideas": layout_ideas,
    }


def write_planning_outputs(output_dir, titles, thumbnails, evaluation):
    """Write title_candidates.txt and thumbnail_plan.md to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    # title_candidates.txt
    title_path = os.path.join(output_dir, "title_candidates.txt")
    with open(title_path, "w", encoding="utf-8") as f:
        f.write("# タイトル候補\n\n")
        f.write(f"## メインタイトル\n{titles['main_title']}\n\n")
        f.write("## 代替タイトル\n")
        for i, alt in enumerate(titles["alternatives"], 1):
            f.write(f"{i}. {alt}\n")
        f.write(f"\n## 評価スコア: {evaluation['total_score']}/{evaluation['max_score']}\n")
        f.write(f"合格基準: {evaluation['threshold']}点\n")
        f.write(f"結果: {'合格' if evaluation['passed'] else '不合格'}\n")

    # thumbnail_plan.md
    thumb_path = os.path.join(output_dir, "thumbnail_plan.md")
    with open(thumb_path, "w", encoding="utf-8") as f:
        f.write("# サムネイル企画\n\n")
        f.write("## テキスト案\n\n")
        for i, text in enumerate(thumbnails["text_ideas"], 1):
            f.write(f"### 案{i}\n```\n{text}\n```\n\n")
        f.write("## レイアウト案\n\n")
        for i, layout in enumerate(thumbnails["layout_ideas"], 1):
            f.write(f"### レイアウト{i}\n")
            f.write(f"- **構図**: {layout['description']}\n")
            f.write(f"- **テキスト位置**: {layout['text_position']}\n")
            f.write(f"- **配色**: {layout['color_scheme']}\n\n")

    logger.info(f"企画ファイル出力: {title_path}, {thumb_path}")
    return title_path, thumb_path


def run_planner(topic, config, output_dir):
    """
    Main entry point for the planner module.

    Args:
        topic: Topic string
        config: settings.yaml config dict
        output_dir: Output directory path

    Returns:
        dict with evaluation, titles, thumbnails, and output paths
    """
    logger.info(f"トピック評価開始: {topic}")

    evaluation = evaluate_topic(topic, config)
    logger.info(
        f"評価スコア: {evaluation['total_score']}/{evaluation['max_score']} "
        f"({'合格' if evaluation['passed'] else '不合格'})"
    )

    for crit in evaluation["per_criterion"]:
        logger.info(f"  {crit['name']}: {crit['ratio']}")

    titles = generate_title_candidates(topic)
    logger.info(f"メインタイトル: {titles['main_title']}")

    thumbnails = generate_thumbnail_ideas(topic)

    title_path, thumb_path = write_planning_outputs(
        output_dir, titles, thumbnails, evaluation
    )

    return {
        "evaluation": evaluation,
        "titles": titles,
        "thumbnails": thumbnails,
        "title_candidates_path": title_path,
        "thumbnail_plan_path": thumb_path,
    }
