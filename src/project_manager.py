"""企画管理システムモジュール (Phase 4)

コマンドライン:
  python src/project_manager.py add --title "タイトル" --person "愛子さま" --format shorts --source-url "URL"
  python src/project_manager.py list [--status ステータス]
  python src/project_manager.py update --id KOSHI-0001 --status 外注依頼済み
  python src/project_manager.py show --id KOSHI-0001
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
PROJECT_DB_PATH = DATA_DIR / "project_database.json"

VALID_STATUSES = [
    "企画候補",
    "採用",
    "台本作成中",
    "編集指示書作成中",
    "外注依頼済み",
    "編集中",
    "修正中",
    "投稿待ち",
    "投稿済み",
    "成績分析済み",
    "不採用",
]

VALID_FORMATS = ["長尺", "Shorts", "TikTok"]


def load_db() -> dict:
    if PROJECT_DB_PATH.exists():
        with open(PROJECT_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "1.0", "last_updated": None, "next_id": 1, "projects": []}


def save_db(db: dict):
    db["last_updated"] = datetime.now().isoformat()
    PROJECT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROJECT_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def generate_id(db: dict) -> str:
    """企画IDを生成する"""
    next_id = db.get("next_id", 1)
    project_id = f"KOSHI-{next_id:04d}"
    db["next_id"] = next_id + 1
    return project_id


def add_project(title: str, person: str, format_type: str,
                source_url: str = "", memo: str = "") -> dict:
    """企画を追加する"""
    if format_type not in VALID_FORMATS:
        print(f"[エラー] 無効なフォーマット: {format_type}")
        print(f"有効な値: {', '.join(VALID_FORMATS)}")
        sys.exit(1)

    db = load_db()
    project_id = generate_id(db)

    project = {
        "id": project_id,
        "title": title,
        "persons": [person] if person else [],
        "source_url": source_url,
        "related_urls": [],
        "format": format_type,
        "status": "企画候補",
        "assignee": "",
        "planned_post_date": None,
        "post_url": None,
        "metrics": {
            "views": None,
            "ctr": None,
            "avg_watch_time": None,
            "retention": None,
            "subscribers_gained": None,
            "estimated_revenue": None,
        },
        "memo": memo,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    db["projects"].append(project)
    save_db(db)

    print(f"[OK] 企画を追加しました: {project_id}")
    print(f"  タイトル: {title}")
    print(f"  人物: {person}")
    print(f"  フォーマット: {format_type}")
    print(f"  ステータス: 企画候補")

    return project


def list_projects(status: str = None) -> list[dict]:
    """企画一覧を表示する"""
    db = load_db()
    projects = db.get("projects", [])

    if status:
        if status not in VALID_STATUSES:
            print(f"[エラー] 無効なステータス: {status}")
            print(f"有効な値: {', '.join(VALID_STATUSES)}")
            sys.exit(1)
        projects = [p for p in projects if p["status"] == status]

    if not projects:
        filter_msg = f"（ステータス: {status}）" if status else ""
        print(f"企画が見つかりません{filter_msg}")
        return []

    print(f"\n{'='*70}")
    print(f"企画一覧 {'（' + status + '）' if status else ''} - {len(projects)}件")
    print(f"{'='*70}")

    for p in projects:
        persons_str = "・".join(p.get("persons", [])) or "未設定"
        print(f"\n  [{p['id']}] {p['title']}")
        print(f"    人物: {persons_str} | フォーマット: {p['format']} | ステータス: {p['status']}")
        if p.get("assignee"):
            print(f"    担当: {p['assignee']}")
        if p.get("memo"):
            print(f"    メモ: {p['memo'][:50]}")

    print(f"\n{'='*70}")
    return projects


def update_project(project_id: str, **kwargs) -> dict:
    """企画を更新する"""
    db = load_db()
    project = None

    for p in db["projects"]:
        if p["id"] == project_id:
            project = p
            break

    if not project:
        print(f"[エラー] 企画が見つかりません: {project_id}")
        sys.exit(1)

    if "status" in kwargs:
        new_status = kwargs["status"]
        if new_status not in VALID_STATUSES:
            print(f"[エラー] 無効なステータス: {new_status}")
            print(f"有効な値: {', '.join(VALID_STATUSES)}")
            sys.exit(1)
        old_status = project["status"]
        project["status"] = new_status
        print(f"  ステータス: {old_status} → {new_status}")

    if "assignee" in kwargs:
        project["assignee"] = kwargs["assignee"]
        print(f"  担当: {kwargs['assignee']}")

    if "memo" in kwargs:
        project["memo"] = kwargs["memo"]

    if "post_url" in kwargs:
        project["post_url"] = kwargs["post_url"]

    if "planned_post_date" in kwargs:
        project["planned_post_date"] = kwargs["planned_post_date"]

    project["updated_at"] = datetime.now().isoformat()
    save_db(db)

    print(f"[OK] 企画を更新しました: {project_id}")
    return project


def show_project(project_id: str) -> dict:
    """企画詳細を表示する"""
    db = load_db()

    for p in db["projects"]:
        if p["id"] == project_id:
            print(f"\n{'='*50}")
            print(f"企画詳細: {p['id']}")
            print(f"{'='*50}")
            print(f"  タイトル: {p['title']}")
            print(f"  人物: {'・'.join(p.get('persons', [])) or '未設定'}")
            print(f"  フォーマット: {p['format']}")
            print(f"  ステータス: {p['status']}")
            print(f"  担当: {p.get('assignee', '未設定')}")
            print(f"  元公式URL: {p.get('source_url', '')}")
            print(f"  関連URL: {', '.join(p.get('related_urls', [])) or 'なし'}")
            print(f"  投稿URL: {p.get('post_url', '未設定')}")
            print(f"  予定投稿日: {p.get('planned_post_date', '未設定')}")

            metrics = p.get("metrics", {})
            if any(v is not None for v in metrics.values()):
                print(f"  成績:")
                for k, v in metrics.items():
                    if v is not None:
                        print(f"    {k}: {v}")

            print(f"  メモ: {p.get('memo', '')}")
            print(f"  作成日: {p.get('created_at', '')}")
            print(f"  更新日: {p.get('updated_at', '')}")
            print(f"{'='*50}")
            return p

    print(f"[エラー] 企画が見つかりません: {project_id}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="企画管理システム")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add", help="企画を追加")
    add_parser.add_argument("--title", required=True, help="企画タイトル")
    add_parser.add_argument("--person", default="", help="対象人物")
    add_parser.add_argument("--format", dest="format_type", default="Shorts",
                            choices=VALID_FORMATS, help="フォーマット")
    add_parser.add_argument("--source-url", default="", help="元公式URL")
    add_parser.add_argument("--memo", default="", help="メモ")

    # list
    list_parser = subparsers.add_parser("list", help="企画一覧")
    list_parser.add_argument("--status", default=None, help="ステータスでフィルタ")

    # update
    update_parser = subparsers.add_parser("update", help="企画を更新")
    update_parser.add_argument("--id", required=True, help="企画ID")
    update_parser.add_argument("--status", default=None, help="新しいステータス")
    update_parser.add_argument("--assignee", default=None, help="担当者")
    update_parser.add_argument("--memo", default=None, help="メモ")
    update_parser.add_argument("--post-url", default=None, help="投稿URL")
    update_parser.add_argument("--planned-post-date", default=None, help="予定投稿日")

    # show
    show_parser = subparsers.add_parser("show", help="企画詳細")
    show_parser.add_argument("--id", required=True, help="企画ID")

    args = parser.parse_args()

    if args.command == "add":
        add_project(args.title, args.person, args.format_type,
                    args.source_url, args.memo)
    elif args.command == "list":
        list_projects(args.status)
    elif args.command == "update":
        kwargs = {}
        if args.status:
            kwargs["status"] = args.status
        if args.assignee:
            kwargs["assignee"] = args.assignee
        if args.memo:
            kwargs["memo"] = args.memo
        if args.post_url:
            kwargs["post_url"] = args.post_url
        if args.planned_post_date:
            kwargs["planned_post_date"] = args.planned_post_date
        update_project(args.id, **kwargs)
    elif args.command == "show":
        show_project(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
