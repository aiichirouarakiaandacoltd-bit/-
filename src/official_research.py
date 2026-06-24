"""
公式情報リサーチ メインランナー
実行: python -m src.official_research [--date YYYY-MM-DD] [--dry-run]

フロー:
  1. 宮内庁HP (ニュース・行事・トピックス) を取得
  2. 宮内庁YouTube RSS を取得
  3. 政府機関情報を取得 (Phase 5 - 現在はスタブ)
  4. 取得済みURLを記録
  5. 人物・行事タイプを識別
  6. 100点スコアリング + 重複チェック
  7. Markdownレポートを outputs/daily_official_research/ に保存
  8. TODOしきい値超えアイテムをプロジェクトDBに追加 (--dry-run では行わない)
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def run(today: str = None, dry_run: bool = False):
    if not today:
        today = datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("皇室物語 デイリーリサーチシステム")
    print(f"日付: {today}")
    if dry_run:
        print("[DRY-RUN] プロジェクトDB への書き込みはスキップします")
    print("=" * 60)

    # ── ステップ1: 情報取得 ─────────────────────────────────────────
    print("\n[1/6] 公式情報を取得中...")

    from src.fetch_kunaicho import fetch_all as fetch_kunaicho
    from src.fetch_youtube import fetch_all as fetch_youtube
    from src.fetch_instagram import fetch_all as fetch_instagram
    from src.fetch_government import fetch_all as fetch_government
    from src.fetch_instagram import generate_manual_check_section

    kunaicho_items = fetch_kunaicho()
    youtube_items = fetch_youtube()
    instagram_items = fetch_instagram()
    government_items = fetch_government()

    raw_items = kunaicho_items + youtube_items + instagram_items + government_items
    print(f"  合計 {len(raw_items)} 件取得")

    # ── ステップ2: URL記録 ─────────────────────────────────────────
    print("\n[2/6] URL記録...")
    from src.duplicate_checker import mark_urls_seen_bulk, is_url_seen
    mark_urls_seen_bulk(raw_items)

    # ── ステップ3: 人物・行事識別 ──────────────────────────────────
    print("\n[3/6] 人物・行事タイプを識別中...")
    from src.person_database import identify_persons, identify_event_type

    enriched = []
    for item in raw_items:
        text = item.get("title", "") + " " + item.get("url", "")
        item["person_ids"] = identify_persons(text)
        item["event_type"] = identify_event_type(text)
        enriched.append(item)

    # ── ステップ4: スコアリング ─────────────────────────────────────
    print("\n[4/6] スコアリング中...")
    from src.idea_ranker import rank_items
    ranked = rank_items(enriched)
    print(f"  Aランク: {sum(1 for i in ranked if i.get('rank')=='A')}件")
    print(f"  Bランク: {sum(1 for i in ranked if i.get('rank')=='B')}件")
    print(f"  Cランク: {sum(1 for i in ranked if i.get('rank')=='C')}件")

    # ── ステップ5: TODO生成 ─────────────────────────────────────────
    print("\n[5/6] TODOリスト生成中...")
    from src.todo_generator import generate_todo_items
    todos = generate_todo_items(ranked)
    print(f"  TODO: {len(todos)}件 自動生成")

    # プロジェクトDBへの書き込み
    if not dry_run and todos:
        from src.project_manager import add_project
        import yaml
        with open("config/ranking_rules.yaml", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
        threshold = rules["output"].get("auto_create_todo_threshold", 70)

        added = 0
        for todo in todos:
            if todo.get("score", 0) >= threshold:
                add_project(
                    title=todo["title"],
                    source_url=todo["url"],
                    person_ids=todo.get("person_ids", []),
                    event_type=todo.get("event_type", "unknown"),
                    score=todo["score"],
                    formats=todo.get("safe_formats", ["長尺"]),
                )
                added += 1
        print(f"  プロジェクトDB: {added}件 追加")
    elif dry_run:
        print("  [DRY-RUN] プロジェクトDB書き込みをスキップ")

    # ── ステップ6: レポート生成 ─────────────────────────────────────
    print("\n[6/6] レポートを生成中...")
    instagram_section = generate_manual_check_section()

    from src.research_report_generator import generate_report
    report_path = generate_report(
        ranked_items=ranked,
        todos=todos,
        instagram_section=instagram_section,
        today=today,
    )

    print("\n" + "=" * 60)
    print(f"完了！レポート: {report_path}")
    print("")
    print("次のアクション（荒木さんへ）:")
    print("  1. レポートを開いて上位アイテムを確認")
    print("  2. Aランクを中心に台本作成を検討")
    print("  3. Instagram（@kunaicho_jp）を手動確認")
    print("  4. 採用するアイテムのTODOチェックボックスにチェック")
    print("  ※ 自動投稿は行いません。投稿は必ず手動で行ってください。")
    print("=" * 60)

    return report_path


def _cli():
    parser = argparse.ArgumentParser(description="皇室物語 デイリーリサーチシステム")
    parser.add_argument("--date", default=None, help="処理日付 YYYY-MM-DD（デフォルト: 今日）")
    parser.add_argument("--dry-run", action="store_true", help="プロジェクトDB書き込みをスキップ")
    args = parser.parse_args()
    run(today=args.date, dry_run=args.dry_run)


if __name__ == "__main__":
    _cli()
