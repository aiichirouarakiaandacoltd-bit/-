"""
デイリーリサーチレポート生成モジュール
公式情報・スコアリング・TODO を Markdown ファイルに出力する
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

RANKING_RULES_PATH = "config/ranking_rules.yaml"
OUTPUT_DIR = "outputs/daily_official_research"


def _load_rules() -> dict:
    with open(RANKING_RULES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _format_score_bar(score: int) -> str:
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled)


def _rank_badge(rank: str) -> str:
    badges = {"A": "🏆", "B": "🥈", "C": "📋", "D": "⬇️"}
    return badges.get(rank, "")


def generate_report(
    ranked_items: list[dict],
    todos: list[dict],
    instagram_section: str = "",
    today: str = None,
    output_path: Optional[str] = None,
) -> str:
    """
    デイリーリサーチレポートを生成してMarkdownファイルに保存する。
    返り値: 出力ファイルパス
    """
    if not today:
        today = datetime.now().strftime("%Y-%m-%d")

    rules = _load_rules()
    top_n = rules["output"].get("daily_report_top_n", 10)
    min_score = rules["output"].get("minimum_score_to_show", 30)

    if not output_path:
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{today}_research.md")

    lines = []

    # ── ヘッダー ─────────────────────────────────────────────────────────────
    lines.append(f"# 皇室物語 デイリーリサーチレポート")
    lines.append(f"**日付**: {today}  ")
    lines.append(f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    lines.append(f"**チャンネル**: 日本が誇る皇室物語  ")
    lines.append("")
    lines.append("> ⚠️ このレポートは公式情報のみを参照しています。最終判断・台本確定・投稿は必ず荒木さんが行ってください。")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── サマリー ─────────────────────────────────────────────────────────────
    total_items = len(ranked_items)
    rank_a = sum(1 for i in ranked_items if i.get("rank") == "A")
    rank_b = sum(1 for i in ranked_items if i.get("rank") == "B")
    rank_c = sum(1 for i in ranked_items if i.get("rank") == "C")

    lines.append("## 📊 本日のサマリー")
    lines.append("")
    lines.append(f"| 項目 | 件数 |")
    lines.append(f"|------|------|")
    lines.append(f"| 取得情報総数 | {total_items}件 |")
    lines.append(f"| 🏆 Aランク（優先制作） | {rank_a}件 |")
    lines.append(f"| 🥈 Bランク（制作候補） | {rank_b}件 |")
    lines.append(f"| 📋 Cランク（保存） | {rank_c}件 |")
    lines.append(f"| ✅ TODO自動生成 | {len(todos)}件 |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── ランキング ───────────────────────────────────────────────────────────
    lines.append(f"## 🏅 アイデアランキング（上位{top_n}件）")
    lines.append("")
    lines.append("> スコアは AI が算出した参考値です。荒木さんの判断を優先してください。")
    lines.append("")

    displayed = [i for i in ranked_items if i.get("score", 0) >= min_score][:top_n]

    if not displayed:
        lines.append("（本日はスコアがしきい値を超えるアイテムがありませんでした）")
    else:
        for rank_idx, item in enumerate(displayed, 1):
            score = item.get("score", 0)
            rank = item.get("rank", "D")
            rank_label = item.get("rank_label", "")
            title = item.get("title", "")
            date_str = item.get("date", "未確認")
            source = item.get("source", "")
            url = item.get("url", "")
            bd = item.get("breakdown", {})

            from src.person_database import get_person_info
            person_ids = item.get("person_ids", ["OTHER"])
            person_names = []
            for pid in person_ids:
                info = get_person_info(pid)
                if info:
                    person_names.append(info.get("name", pid))
            persons_str = "・".join(person_names) if person_names else "その他"

            lines.append(f"### {rank_idx}. {_rank_badge(rank)} {title}")
            lines.append(f"**スコア**: {score}点 `{_format_score_bar(score)}`  ")
            lines.append(f"**ランク**: {rank_label}  ")
            lines.append(f"**人物**: {persons_str}  ")
            lines.append(f"**行事**: {item.get('event_type', 'unknown')}  ")
            lines.append(f"**情報日**: {date_str} / **ソース**: {source}  ")
            lines.append(f"**URL**: {url}  ")

            breakdown_parts = [
                f"人物{bd.get('person', 0)}",
                f"行事{bd.get('event_type', 0)}",
                f"鮮度{bd.get('freshness', 0)}",
                f"Shorts{bd.get('shorts', 0)}",
            ]
            if bd.get("penalty"):
                breakdown_parts.append(f"ペナルティ-{bd['penalty']}")
            lines.append(f"**内訳**: {' / '.join(breakdown_parts)}")

            # 重複警告
            dup = item.get("duplicate_check", {})
            if dup.get("url_seen"):
                lines.append(f"⚠️ **このURLは既に取得済みです**")
            if dup.get("title_duplicates"):
                for td in dup["title_duplicates"]:
                    lines.append(f"⚠️ 類似タイトル: {td['project_id']} ({td['title'][:30]}…) 類似度{td['similarity']:.0%}")
            if dup.get("person_event_conflicts_7d"):
                lines.append(f"⚠️ 同一人物×行事が7日以内に投稿済み")
            elif dup.get("person_event_conflicts_30d"):
                lines.append(f"⚠️ 同一人物×行事が30日以内に投稿済み")

            lines.append("")

    lines.append("---")
    lines.append("")

    # ── TODO ─────────────────────────────────────────────────────────────────
    from src.todo_generator import format_todo_markdown
    lines.append(format_todo_markdown(todos, today))
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Instagram手動確認 ──────────────────────────────────────────────────
    if instagram_section:
        lines.append("## 📸 Instagram手動確認")
        lines.append(instagram_section)
        lines.append("---")
        lines.append("")

    # ── フッター ─────────────────────────────────────────────────────────────
    lines.append("## ℹ️ 注意事項")
    lines.append("")
    lines.append("- このレポートは **宮内庁公式HP・公式YouTube** の情報のみを参照しています")
    lines.append("- Wikipedia・ブログ・週刊誌・SNSまとめサイトは使用していません")
    lines.append("- 「未確認」と明記されている情報は公式確認がとれていません")
    lines.append("- 皇族の内心・発言の推測は含まれていません")
    lines.append("- **自動投稿は行いません。投稿は必ず荒木さんが手動で行ってください。**")
    lines.append("")

    content = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [レポート生成] → {output_path}")
    return output_path
