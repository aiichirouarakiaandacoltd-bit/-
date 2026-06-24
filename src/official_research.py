"""YouTube運営秘書システム - 毎日の公式情報リサーチ

メインの実行スクリプト。
毎朝実行して、公式情報の取得→人物分類→企画ランキング→重複チェック→TODO生成→レポート出力を行う。

使い方:
  python src/official_research.py

注意:
  - 自動投稿は行わない
  - 最終判断、台本確定、投稿判断は荒木が行う
  - 個人ブログ、Wikipedia、週刊誌、まとめサイト、出典不明SNSは一次情報として扱わない
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch_kunaicho import fetch_all as fetch_kunaicho
from fetch_instagram import generate_check_entry as instagram_check
from fetch_youtube import generate_check_entry as youtube_check
from fetch_government import generate_check_entries as government_checks
from person_database import add_entries_from_research
from idea_ranker import rank_entries
from duplicate_checker import check_duplicates
from todo_generator import generate_todos
from research_report_generator import generate_report, save_report


def run_daily_research():
    """毎日の公式情報リサーチを実行する"""
    print("=" * 60)
    print(f"YouTube運営秘書システム - 公式情報リサーチ")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Phase 1: 宮内庁HP新着取得
    print("[Phase 1] 公式情報を取得中...")
    print("-" * 40)

    entries = []

    try:
        kunaicho_entries = fetch_kunaicho()
        entries.extend(kunaicho_entries)
        print(f"  宮内庁HP: {len(kunaicho_entries)}件取得")
    except Exception as e:
        print(f"  [エラー] 宮内庁HP取得失敗: {e}")
        print(f"  → 手動で https://www.kunaicho.go.jp を確認してください")

    # Phase 2: Instagram, YouTube（手動確認欄）
    manual_checks = []

    ig_check = instagram_check()
    manual_checks.append(ig_check)
    print(f"  Instagram: {ig_check['status']}")

    yt_check = youtube_check()
    manual_checks.append(yt_check)
    print(f"  YouTube: {yt_check['status']}")

    # Phase 5: 政府関連（未実装表示）
    gov_checks = government_checks()
    for gc in gov_checks:
        print(f"  {gc['source']}: {gc['status']}")

    print()

    # 人物分類 & データベース登録
    print("[Phase 2] 人物分類 & データベース登録中...")
    print("-" * 40)

    if entries:
        add_entries_from_research(entries)
        print(f"  {len(entries)}件を人物データベースに登録しました")
    else:
        print("  新着情報なし - 登録スキップ")

    print()

    # AI企画ランキング
    print("[Phase 3] AI企画ランキング生成中...")
    print("-" * 40)

    ranked = []
    if entries:
        ranked = rank_entries(entries)
        for r in ranked:
            print(f"  第{r['rank']}位: {r['total_score']}点 - {r['content'][:40]}...")
            if r.get("warnings"):
                for w in r["warnings"]:
                    print(f"    ⚠ {w}")
    else:
        print("  企画候補なし")

    print()

    # 重複チェック
    print("[Phase 4] 重複チェック中...")
    print("-" * 40)

    duplicates_map = {}
    for entry in entries:
        content = entry.get("content", "")[:50]
        dups = check_duplicates(entry)
        if dups:
            duplicates_map[content] = dups
            for dup in dups:
                print(f"  「{content}」→ {dup['overlap_percentage']}%重複")

    if not duplicates_map:
        print("  重複なし")

    print()

    # TODO生成
    print("[Phase 3] TODO生成中...")
    print("-" * 40)

    todos = generate_todos(ranked, duplicates_map)
    print(todos)
    print()

    # レポート生成・保存
    print("[出力] レポート生成中...")
    print("-" * 40)

    report = generate_report(
        entries=entries,
        ranked=ranked,
        duplicates_map=duplicates_map,
        todos=todos,
        manual_checks=manual_checks,
    )

    filepath = save_report(report)
    print()

    # サマリー
    print("=" * 60)
    print("完了サマリー")
    print("=" * 60)
    print(f"  新着情報: {len(entries)}件")
    print(f"  企画候補: {len(ranked)}件")
    if ranked:
        print(f"  最優先企画: {ranked[0]['content'][:40]}... ({ranked[0]['total_score']}点)")
    print(f"  重複検出: {len(duplicates_map)}件")
    print(f"  レポート: {filepath}")
    print()
    print("※ 最終判断、台本確定、投稿判断は荒木が行います。")
    print("※ 自動投稿は行いません。")
    print("=" * 60)

    return {
        "entries": entries,
        "ranked": ranked,
        "duplicates": duplicates_map,
        "report_path": str(filepath),
    }


if __name__ == "__main__":
    run_daily_research()
