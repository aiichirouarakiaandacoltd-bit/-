"""
重複チェックモジュール
過去取得URL・プロジェクトタイトル・人物×行事タイプの重複を検出する
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

URLS_DB_PATH = "data/processed/fetched_urls.json"
PROJECTS_DB_PATH = "data/processed/project_database.json"


def _load_urls_db() -> dict:
    path = Path(URLS_DB_PATH)
    if not path.exists():
        return {"_meta": {}, "urls": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_urls_db(db: dict):
    db["_meta"]["last_updated"] = datetime.now().isoformat()
    Path(URLS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(URLS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _load_projects_db() -> dict:
    path = Path(PROJECTS_DB_PATH)
    if not path.exists():
        return {"_meta": {}, "projects": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _title_similarity(a: str, b: str) -> float:
    """タイトル類似度を返す（0.0〜1.0）。単純なbigram一致率で計算。"""
    def bigrams(s: str) -> set:
        s = re.sub(r"\s+", "", s)
        return {s[i:i+2] for i in range(len(s) - 1)}

    bg_a, bg_b = bigrams(a), bigrams(b)
    if not bg_a or not bg_b:
        return 0.0
    intersection = len(bg_a & bg_b)
    return intersection / max(len(bg_a), len(bg_b))


def is_url_seen(url: str) -> bool:
    """URLが過去に取得済みかどうかを確認する"""
    db = _load_urls_db()
    return url in db.get("urls", {})


def mark_url_seen(url: str, title: str = "", date: str = ""):
    """URLを取得済みとして記録する"""
    db = _load_urls_db()
    db.setdefault("urls", {})[url] = {
        "title": title,
        "date": date,
        "first_seen": datetime.now().isoformat(),
    }
    _save_urls_db(db)


def mark_urls_seen_bulk(items: list[dict]):
    """複数URLをまとめて取得済みとして記録する"""
    db = _load_urls_db()
    urls_db = db.setdefault("urls", {})
    now = datetime.now().isoformat()
    for item in items:
        url = item.get("url", "")
        if url and url not in urls_db:
            urls_db[url] = {
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "first_seen": now,
            }
    _save_urls_db(db)


def check_title_duplicate(title: str, threshold: float = 0.85) -> list[dict]:
    """プロジェクトDBに類似タイトルが存在するか確認する"""
    db = _load_projects_db()
    duplicates = []

    for proj_id, proj in db.get("projects", {}).items():
        existing_title = proj.get("title", "")
        sim = _title_similarity(title, existing_title)
        if sim >= threshold:
            duplicates.append({
                "project_id": proj_id,
                "title": existing_title,
                "similarity": round(sim, 2),
                "status": proj.get("status", "unknown"),
            })

    return duplicates


def check_person_event_recent(person_ids: list[str], event_type: str, days: int = 30) -> list[dict]:
    """同一人物×行事タイプが指定日数内に投稿済みかチェックする"""
    from src.person_database import get_recent_event_dates
    conflicts = []
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    for pid in person_ids:
        recent_dates = get_recent_event_dates(pid, event_type, days=days)
        if recent_dates:
            conflicts.append({
                "person_id": pid,
                "event_type": event_type,
                "recent_dates": recent_dates,
                "days_checked": days,
            })

    return conflicts


def run_full_duplicate_check(item: dict) -> dict:
    """
    1件の情報アイテムに対して全重複チェックを実行する。
    返り値: {"url_seen": bool, "title_duplicates": [...], "person_event_conflicts": [...], "penalty": int}
    """
    url = item.get("url", "")
    title = item.get("title", "")
    person_ids = item.get("person_ids", [])
    event_type = item.get("event_type", "unknown")

    result = {
        "url_seen": is_url_seen(url),
        "title_duplicates": check_title_duplicate(title),
        "person_event_conflicts_7d": check_person_event_recent(person_ids, event_type, days=7),
        "person_event_conflicts_30d": check_person_event_recent(person_ids, event_type, days=30),
        "penalty": 0,
    }

    # ペナルティ計算
    if result["url_seen"]:
        result["penalty"] += 20
    if result["title_duplicates"]:
        result["penalty"] += 15
    if result["person_event_conflicts_7d"]:
        result["penalty"] += 20
    elif result["person_event_conflicts_30d"]:
        result["penalty"] += 10

    return result
