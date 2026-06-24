"""
プロジェクト管理モジュール（KOSHI-XXXX ID体系）
台本制作・投稿のプロジェクトライフサイクルを管理する
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECTS_DB_PATH = "data/processed/project_database.json"

VALID_STATUSES = [
    "企画中",        # アイデア段階
    "台本作成中",    # 荒木さんが台本を書いている
    "台本確認待ち",  # 荒木さんの最終確認待ち
    "収録中",        # ナレーション・動画生成中
    "編集中",        # 最終編集
    "投稿待ち",      # YouTube投稿の準備完了
    "投稿済み",      # 投稿完了
    "没",            # 不採用
]


def _load_db() -> dict:
    path = Path(PROJECTS_DB_PATH)
    if not path.exists():
        return {"_meta": {"version": "1.0", "last_updated": None, "next_id": 1}, "projects": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_db(db: dict):
    db["_meta"]["last_updated"] = datetime.now().isoformat()
    Path(PROJECTS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(PROJECTS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _next_project_id(db: dict) -> str:
    next_id = db["_meta"].get("next_id", 1)
    db["_meta"]["next_id"] = next_id + 1
    return f"KOSHI-{next_id:04d}"


def add_project(
    title: str,
    source_url: str = "",
    person_ids: list = None,
    event_type: str = "unknown",
    score: int = 0,
    formats: list = None,
    notes: str = "",
) -> str:
    """新規プロジェクトを追加し、KOSHI-XXXXを返す"""
    db = _load_db()
    project_id = _next_project_id(db)

    db["projects"][project_id] = {
        "id": project_id,
        "title": title,
        "status": "企画中",
        "score": score,
        "source_url": source_url,
        "person_ids": person_ids or [],
        "event_type": event_type,
        "formats": formats or ["長尺"],
        "notes": notes,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "posted_at": None,
        "youtube_url": None,
        "history": [
            {"status": "企画中", "timestamp": datetime.now().isoformat(), "note": "自動生成"}
        ],
    }

    _save_db(db)
    print(f"  [プロジェクト作成] {project_id}: {title}")
    return project_id


def update_status(project_id: str, new_status: str, note: str = "") -> bool:
    """プロジェクトのステータスを更新する"""
    if new_status not in VALID_STATUSES:
        print(f"  [エラー] 無効なステータス: {new_status}")
        print(f"  有効なステータス: {', '.join(VALID_STATUSES)}")
        return False

    db = _load_db()
    if project_id not in db["projects"]:
        print(f"  [エラー] プロジェクトが見つかりません: {project_id}")
        return False

    proj = db["projects"][project_id]
    old_status = proj["status"]
    proj["status"] = new_status
    proj["updated_at"] = datetime.now().isoformat()

    if new_status == "投稿済み":
        proj["posted_at"] = datetime.now().isoformat()

    proj.setdefault("history", []).append({
        "from": old_status,
        "to": new_status,
        "timestamp": datetime.now().isoformat(),
        "note": note,
    })

    _save_db(db)
    print(f"  [ステータス更新] {project_id}: {old_status} → {new_status}")
    return True


def update_youtube_url(project_id: str, youtube_url: str):
    """投稿済みのYouTube URLを記録する"""
    db = _load_db()
    if project_id not in db["projects"]:
        print(f"  [エラー] プロジェクトが見つかりません: {project_id}")
        return
    db["projects"][project_id]["youtube_url"] = youtube_url
    db["projects"][project_id]["updated_at"] = datetime.now().isoformat()
    _save_db(db)
    print(f"  [URL更新] {project_id}: {youtube_url}")


def list_projects(status_filter: str = None, limit: int = 20) -> list[dict]:
    """プロジェクト一覧を返す（ステータスフィルタ対応）"""
    db = _load_db()
    projects = list(db["projects"].values())

    if status_filter:
        projects = [p for p in projects if p["status"] == status_filter]

    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return projects[:limit]


def get_project(project_id: str) -> dict:
    """プロジェクトの詳細を返す"""
    db = _load_db()
    proj = db["projects"].get(project_id)
    if not proj:
        print(f"  [エラー] プロジェクトが見つかりません: {project_id}")
    return proj


def print_project_list(status_filter: str = None):
    """プロジェクト一覧をターミナルに表示する"""
    projects = list_projects(status_filter)
    if not projects:
        print("  プロジェクトはありません。")
        return

    filter_label = f"（ステータス: {status_filter}）" if status_filter else ""
    print(f"\n=== プロジェクト一覧{filter_label} ===")
    print(f"{'ID':12s} {'ステータス':10s} {'スコア':6s} {'タイトル'}")
    print("-" * 70)
    for p in projects:
        print(f"{p['id']:12s} {p['status']:10s} {p.get('score', 0):4d}点  {p['title'][:35]}")


def print_project_detail(project_id: str):
    """プロジェクト詳細をターミナルに表示する"""
    proj = get_project(project_id)
    if not proj:
        return

    print(f"\n=== {proj['id']} ===")
    print(f"タイトル   : {proj['title']}")
    print(f"ステータス : {proj['status']}")
    print(f"スコア     : {proj.get('score', 0)}点")
    print(f"人物       : {', '.join(proj.get('person_ids', []))}")
    print(f"行事       : {proj.get('event_type', 'unknown')}")
    print(f"フォーマット: {', '.join(proj.get('formats', []))}")
    print(f"作成日     : {proj.get('created_at', '')[:10]}")
    print(f"更新日     : {proj.get('updated_at', '')[:10]}")
    if proj.get("posted_at"):
        print(f"投稿日     : {proj['posted_at'][:10]}")
    if proj.get("youtube_url"):
        print(f"YouTube URL: {proj['youtube_url']}")
    if proj.get("source_url"):
        print(f"情報源 URL : {proj['source_url']}")
    if proj.get("notes"):
        print(f"メモ       : {proj['notes']}")
    if proj.get("history"):
        print("\n--- ステータス履歴 ---")
        for h in proj["history"]:
            t = h.get("timestamp", "")[:16]
            if "from" in h:
                print(f"  {t}  {h['from']} → {h['to']}  {h.get('note', '')}")
            else:
                print(f"  {t}  {h.get('status', '')}  {h.get('note', '')}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="KOSHI プロジェクト管理CLI")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="プロジェクトを追加")
    p_add.add_argument("title", help="タイトル")
    p_add.add_argument("--url", default="", help="情報源URL")
    p_add.add_argument("--notes", default="", help="メモ")

    p_list = sub.add_parser("list", help="一覧表示")
    p_list.add_argument("--status", default=None, help="ステータスでフィルタ")

    p_detail = sub.add_parser("show", help="詳細表示")
    p_detail.add_argument("id", help="KOSHI-XXXX")

    p_status = sub.add_parser("status", help="ステータス更新")
    p_status.add_argument("id", help="KOSHI-XXXX")
    p_status.add_argument("new_status", help=f"新ステータス: {', '.join(VALID_STATUSES)}")
    p_status.add_argument("--note", default="", help="メモ")

    p_url = sub.add_parser("set-url", help="YouTube URL記録")
    p_url.add_argument("id", help="KOSHI-XXXX")
    p_url.add_argument("youtube_url", help="YouTube URL")

    args = parser.parse_args()

    if args.command == "add":
        pid = add_project(args.title, source_url=args.url, notes=args.notes)
        print(f"作成: {pid}")
    elif args.command == "list":
        print_project_list(args.status)
    elif args.command == "show":
        print_project_detail(args.id)
    elif args.command == "status":
        update_status(args.id, args.new_status, args.note)
    elif args.command == "set-url":
        update_youtube_url(args.id, args.youtube_url)
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
