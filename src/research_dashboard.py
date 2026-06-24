"""
リサーチダッシュボード CLI
python -m src.research_dashboard --person 愛子さま --days 90
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path


def _find_person_id(name: str) -> list[str]:
    """名前または別名からperson_idを検索する"""
    import yaml
    with open("config/person_keywords.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    persons = cfg.get("persons", {})
    matched = []
    for pid, pcfg in persons.items():
        all_names = [pcfg.get("name", "")] + pcfg.get("aliases", [])
        if any(name in n or n in name for n in all_names):
            matched.append(pid)
    return matched


def show_person_summary(person_name: str, days: int = 90):
    """人物別の投稿履歴サマリーを表示する"""
    from src.person_database import get_person_info, get_recent_event_dates
    from src.project_manager import list_projects

    person_ids = _find_person_id(person_name)
    if not person_ids:
        print(f"  [エラー] '{person_name}' に一致する人物が見つかりません")
        return

    print(f"\n=== 人物サマリー: {person_name} (過去{days}日) ===")
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    for pid in person_ids:
        info = get_person_info(pid)
        if not info:
            continue
        print(f"\n【{info['name']}】(ID: {pid})")
        print(f"  人気スコア: {info.get('popularity_score', '-')}/10")
        print(f"  65歳以上女性親和度: {info.get('audience_affinity_65f', '-')}/10")
        print(f"  推奨フォーマット: {', '.join(info.get('safe_formats', []))}")

        # 投稿済みプロジェクト
        projects = list_projects()
        matching = [p for p in projects if pid in p.get("person_ids", []) and p.get("status") == "投稿済み"]
        recent = [p for p in matching if p.get("posted_at", "")[:10] >= cutoff]
        print(f"  投稿済み(全期間): {len(matching)}本 / 過去{days}日: {len(recent)}本")

        if recent:
            print(f"  直近の投稿:")
            for p in sorted(recent, key=lambda x: x.get("posted_at", ""), reverse=True)[:5]:
                posted = p.get("posted_at", "")[:10]
                print(f"    [{posted}] {p['id']}: {p['title'][:40]}")


def show_recent_reports(n: int = 7):
    """最近のレポートファイル一覧を表示する"""
    report_dir = Path("outputs/daily_official_research")
    if not report_dir.exists():
        print("  レポートフォルダが存在しません。")
        return

    reports = sorted(report_dir.glob("*_research.md"), reverse=True)[:n]
    if not reports:
        print("  レポートファイルがありません。")
        return

    print(f"\n=== 最近のレポート（{n}件） ===")
    for r in reports:
        size = r.stat().st_size
        print(f"  {r.name}  ({size // 1024}KB)")


def show_project_stats():
    """プロジェクト統計を表示する"""
    from src.project_manager import list_projects, VALID_STATUSES

    print("\n=== プロジェクト統計 ===")
    all_projects = list_projects(limit=9999)

    status_counts = {}
    for status in VALID_STATUSES:
        count = sum(1 for p in all_projects if p["status"] == status)
        if count > 0:
            status_counts[status] = count

    for status, count in status_counts.items():
        bar = "█" * count
        print(f"  {status:10s}: {count:3d}本  {bar}")

    print(f"\n  合計: {len(all_projects)}本")


def _cli():
    parser = argparse.ArgumentParser(description="皇室物語 リサーチダッシュボード")
    parser.add_argument("--person", help="人物名（例: 愛子さま）")
    parser.add_argument("--days", type=int, default=90, help="遡る日数（デフォルト: 90）")
    parser.add_argument("--reports", type=int, default=0, metavar="N", help="最近N件のレポートを表示")
    parser.add_argument("--stats", action="store_true", help="プロジェクト統計を表示")

    args = parser.parse_args()

    if args.person:
        show_person_summary(args.person, args.days)
    elif args.reports > 0:
        show_recent_reports(args.reports)
    elif args.stats:
        show_project_stats()
    else:
        parser.print_help()
        print("\n使用例:")
        print("  python -m src.research_dashboard --person 愛子さま --days 90")
        print("  python -m src.research_dashboard --reports 7")
        print("  python -m src.research_dashboard --stats")


if __name__ == "__main__":
    _cli()
