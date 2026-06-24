"""人物別リサーチダッシュボードモジュール

使い方:
  python src/research_dashboard.py --person 愛子さま --days 90
  python src/research_dashboard.py --list
  python src/research_dashboard.py --all --days 30
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from person_database import query_person, list_persons, load_person_db


def show_person_report(person: str, days: int):
    """人物別レポートを表示する"""
    entries = query_person(person, days)

    print(f"\n{'='*60}")
    print(f"人物別レポート: {person}（過去{days}日間）")
    print(f"{'='*60}")

    if not entries:
        print(f"\n  {person}の情報は過去{days}日間にありません。")
        print(f"{'='*60}")
        return

    print(f"\n  件数: {len(entries)}件\n")

    for i, entry in enumerate(entries, 1):
        print(f"  [{i}] {entry.get('date', '不明')}")
        print(f"      行事: {entry.get('event_name', '')[:60]}")
        if entry.get("place"):
            print(f"      場所: {entry['place']}")
        if entry.get("official_url"):
            print(f"      URL: {entry['official_url']}")
        print(f"      素材: {'あり' if entry.get('has_official_material') else 'なし'}")
        print(f"      企画化: {entry.get('planning_status', '未分類')}")
        if entry.get("memo"):
            print(f"      メモ: {entry['memo'][:50]}")
        print()

    print(f"{'='*60}")


def show_all_persons(days: int):
    """全人物のサマリーを表示する"""
    persons = list_persons()
    db = load_person_db()

    print(f"\n{'='*60}")
    print(f"全人物サマリー（過去{days}日間）")
    print(f"{'='*60}\n")

    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    for person in persons:
        entries = db["persons"].get(person, {}).get("entries", [])
        recent = [e for e in entries if e.get("date", "") >= cutoff]
        total = len(entries)
        print(f"  {person}: {len(recent)}件（過去{days}日）/ {total}件（全期間）")

    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="人物別リサーチダッシュボード")
    parser.add_argument("--person", help="対象人物名")
    parser.add_argument("--days", type=int, default=90, help="遡る日数（デフォルト: 90）")
    parser.add_argument("--list", action="store_true", help="登録済み人物一覧")
    parser.add_argument("--all", action="store_true", help="全人物サマリー")

    args = parser.parse_args()

    if args.list:
        persons = list_persons()
        print("\n登録済み人物:")
        for p in persons:
            print(f"  - {p}")
    elif args.all:
        show_all_persons(args.days)
    elif args.person:
        show_person_report(args.person, args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
