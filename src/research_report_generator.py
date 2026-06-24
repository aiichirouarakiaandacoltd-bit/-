"""公式リサーチレポート生成モジュール"""

from datetime import datetime
from pathlib import Path


OUTPUTS_DIR = Path(__file__).parent.parent / "outputs" / "daily_official_research"


def generate_report(
    entries: list[dict],
    ranked: list[dict],
    duplicates_map: dict,
    todos: str,
    manual_checks: list[dict] = None,
) -> str:
    """毎日の公式リサーチレポートを生成する"""
    today = datetime.now().strftime("%Y年%m月%d日")
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# 公式情報リサーチレポート（{today}）",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]

    # 新着情報
    lines.append("## 1. 新着情報")
    lines.append("")
    if entries:
        lines.append(f"**新着情報あり** （{len(entries)}件）")
        lines.append("")
        for i, entry in enumerate(entries, 1):
            lines.append(f"### [{i}] {entry.get('source', '不明')}")
            lines.append(f"- 日付: {entry.get('date_text', '不明')}")
            lines.append(f"- 内容: {entry.get('content', '')}")
            if entry.get("urls"):
                lines.append(f"- 公式URL:")
                for url in entry["urls"]:
                    lines.append(f"  - {url}")
            lines.append(f"- 公式素材: {'あり' if entry.get('has_official_material') else 'なし/未確認'}")
            if entry.get("note"):
                lines.append(f"- 注記: {entry['note']}")
            lines.append("")
    else:
        lines.append("**新着情報なし**")
        lines.append("")

    # 人物別分類
    lines.append("## 2. 人物別分類")
    lines.append("")
    person_map = {}
    for entry in entries:
        from person_database import classify_persons
        persons = classify_persons(entry.get("content", ""))
        if not persons:
            persons = ["分類不明"]
        for person in persons:
            person_map.setdefault(person, []).append(entry)

    if person_map:
        for person, person_entries in person_map.items():
            lines.append(f"### {person}")
            for e in person_entries:
                lines.append(f"- {e.get('content', '')[:80]}")
            lines.append("")
    else:
        lines.append("該当なし")
        lines.append("")

    # 手動確認項目（Instagram, YouTube等）
    if manual_checks:
        lines.append("## 3. 手動確認項目")
        lines.append("")
        for check in manual_checks:
            lines.append(f"### {check.get('source', '')}")
            lines.append(f"- 確認URL: {check.get('check_url', '')}")
            lines.append(f"- ステータス: {check.get('status', '')}")
            lines.append(f"- {check.get('note', '')}")
            lines.append("")

    # AI企画ランキング
    section_num = 4 if manual_checks else 3
    lines.append(f"## {section_num}. AI企画ランキング")
    lines.append("")
    if ranked:
        for r in ranked:
            rank = r.get("rank", "?")
            score = r.get("total_score", 0)
            content = r.get("content", "")
            persons = r.get("persons", [])

            lines.append(f"### 第{rank}位: 企画価値 {score}点")
            lines.append(f"- 内容: {content}")
            if persons:
                lines.append(f"- 人物: {'・'.join(persons)}")

            lines.append("- 理由:")
            for reason in r.get("reasons", []):
                lines.append(f"  - {reason}")

            lines.append(f"- 推奨: {r.get('recommendation', '')}")

            if r.get("warnings"):
                lines.append("- ⚠ 警告:")
                for w in r["warnings"]:
                    lines.append(f"  - {w}")

            # スコア詳細
            scores = r.get("scores", {})
            if scores:
                lines.append("- スコア詳細:")
                for k, v in scores.items():
                    lines.append(f"  - {k}: {v}点")

            lines.append("")
    else:
        lines.append("企画候補なし")
        lines.append("")

    # 重複判定
    section_num += 1
    lines.append(f"## {section_num}. 重複判定")
    lines.append("")
    if duplicates_map:
        for content_key, dups in duplicates_map.items():
            lines.append(f"### 「{content_key[:50]}」")
            for dup in dups:
                pct = dup.get("overlap_percentage", 0)
                proj = dup.get("existing_project", {})
                lines.append(f"- 重複判定: {pct}%重複")
                lines.append(f"- 過去動画: {proj.get('title', '')}")
                lines.append(f"- ステータス: {proj.get('status', '')}")

                if pct >= 70:
                    lines.append("- 判断: 重複度が高いため、別の切り口での差別化が必要")
                elif pct >= 40:
                    lines.append("- 判断: 切り口を変えれば別企画として制作可能")
                else:
                    lines.append("- 判断: 新規企画として制作可能")
            lines.append("")
    else:
        lines.append("重複なし、または過去企画データなし")
        lines.append("")

    # 本日の最優先企画
    section_num += 1
    lines.append(f"## {section_num}. 本日の最優先企画")
    lines.append("")
    if ranked:
        top = ranked[0]
        lines.append(f"**{top.get('content', '')}**")
        lines.append(f"- 企画価値: {top.get('total_score', 0)}点")
        lines.append(f"- 推奨: {top.get('recommendation', '')}")
        if top.get("persons"):
            lines.append(f"- 人物: {'・'.join(top['persons'])}")
    else:
        lines.append("本日の最優先企画はありません。")
    lines.append("")

    # TODO
    section_num += 1
    lines.append(f"## {section_num}. {todos}")
    lines.append("")

    # 参考URL一覧
    section_num += 1
    lines.append(f"## {section_num}. 参考URL一覧")
    lines.append("")
    all_urls = set()
    for entry in entries:
        for url in entry.get("urls", []):
            all_urls.add(url)
    if all_urls:
        for url in sorted(all_urls):
            lines.append(f"- {url}")
    else:
        lines.append("なし")
    lines.append("")

    # フッター
    lines.append("---")
    lines.append("")
    lines.append("※ このレポートは公式情報のみに基づいて自動生成されています。")
    lines.append("※ 最終判断、台本確定、投稿判断は荒木が行います。")
    lines.append("※ 個人ブログ、Wikipedia、週刊誌、まとめサイト、出典不明SNSは一次情報として扱っていません。")

    return "\n".join(lines)


def save_report(content: str) -> Path:
    """レポートをファイルに保存する"""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = OUTPUTS_DIR / f"{date_str}_official_research.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] レポートを保存しました: {filepath}")
    return filepath
