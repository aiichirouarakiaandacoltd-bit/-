"""
TODO自動生成モジュール
ランキング上位アイテムから荒木さん向けのTODOリストを生成する
"""

from datetime import datetime

import yaml

RANKING_RULES_PATH = "config/ranking_rules.yaml"


def _load_rules() -> dict:
    with open(RANKING_RULES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _format_breakdown(breakdown: dict) -> str:
    parts = [
        f"人物:{breakdown.get('person', 0)}点",
        f"行事:{breakdown.get('event_type', 0)}点",
        f"鮮度:{breakdown.get('freshness', 0)}点",
        f"Shorts:{breakdown.get('shorts', 0)}点",
    ]
    penalty = breakdown.get("penalty", 0)
    if penalty:
        parts.append(f"重複ペナルティ:-{penalty}点")
    return " / ".join(parts)


def _format_formats(safe_formats: list[str]) -> str:
    if not safe_formats:
        return "長尺"
    return " + ".join(safe_formats)


def generate_todo_items(ranked_items: list[dict]) -> list[dict]:
    """
    ランキング済みアイテムからTODOアイテムを生成する。
    しきい値以上のアイテムのみ対象。
    """
    rules = _load_rules()
    threshold = rules["output"].get("auto_create_todo_threshold", 70)

    todos = []
    for item in ranked_items:
        if item.get("score", 0) < threshold:
            continue

        person_ids = item.get("person_ids", ["OTHER"])
        from src.person_database import get_person_info, get_safe_formats
        person_names = []
        for pid in person_ids:
            info = get_person_info(pid)
            if info:
                person_names.append(info.get("name", pid))

        event_type = item.get("event_type", "unknown")
        safe_formats = get_safe_formats(person_ids, event_type)

        dup_check = item.get("duplicate_check", {})
        warnings = []
        if dup_check.get("url_seen"):
            warnings.append("⚠️ このURLは既に取得済み")
        if dup_check.get("title_duplicates"):
            warnings.append("⚠️ 類似タイトルが過去に存在")
        if dup_check.get("person_event_conflicts_7d"):
            warnings.append("⚠️ 同一人物×行事が7日以内に投稿済み")
        elif dup_check.get("person_event_conflicts_30d"):
            warnings.append("⚠️ 同一人物×行事が30日以内に投稿済み")

        todos.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "date": item.get("date", ""),
            "source": item.get("source", ""),
            "score": item.get("score", 0),
            "rank": item.get("rank", "D"),
            "rank_label": item.get("rank_label", ""),
            "person_names": person_names,
            "event_type": event_type,
            "safe_formats": safe_formats,
            "breakdown": item.get("breakdown", {}),
            "warnings": warnings,
        })

    return todos


def format_todo_markdown(todos: list[dict], today: str = None) -> str:
    """TODOリストをMarkdown形式に整形する"""
    if not today:
        today = datetime.now().strftime("%Y-%m-%d")

    if not todos:
        return "\n### TODO自動生成\n\n（本日はしきい値を超えるアイテムがありませんでした）\n"

    lines = [f"\n### ✅ TODO自動生成（{today}）\n"]
    lines.append(f"> しきい値70点以上の案件を自動抽出しています。最終判断は荒木さんが行ってください。\n")

    for i, todo in enumerate(todos, 1):
        persons_str = "・".join(todo["person_names"]) if todo["person_names"] else "不明"
        formats_str = _format_formats(todo["safe_formats"])
        breakdown_str = _format_breakdown(todo["breakdown"])

        lines.append(f"#### {i}. [{todo['rank_label']} {todo['score']}点] {todo['title']}")
        lines.append(f"- **人物**: {persons_str}")
        lines.append(f"- **行事タイプ**: {todo['event_type']}")
        lines.append(f"- **推奨フォーマット**: {formats_str}")
        lines.append(f"- **スコア内訳**: {breakdown_str}")
        lines.append(f"- **情報源**: {todo['source']} ({todo['date']})")
        lines.append(f"- **URL**: {todo['url']}")

        for warning in todo["warnings"]:
            lines.append(f"- {warning}")

        lines.append("")
        lines.append("**荒木さんの確認欄:**")
        lines.append("- [ ] 内容確認済み")
        lines.append("- [ ] 台本作成指示")
        lines.append("- [ ] 不採用（理由: ）")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
