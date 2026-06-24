"""
人物データベース CRUD モジュール
person_database.json と person_keywords.yaml を組み合わせて管理する
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

KEYWORDS_PATH = "config/person_keywords.yaml"
DB_PATH = "data/processed/person_database.json"


def _load_keywords() -> dict:
    with open(KEYWORDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_db() -> dict:
    path = Path(DB_PATH)
    if not path.exists():
        return {"_meta": {"version": "1.0", "last_updated": None}, "persons": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_db(db: dict):
    db["_meta"]["last_updated"] = datetime.now().isoformat()
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def identify_persons(text: str) -> list[str]:
    """テキストから言及されている人物IDのリストを返す（複数マッチ対応）"""
    keywords_cfg = _load_keywords()
    persons_cfg = keywords_cfg.get("persons", {})

    matched = []
    for person_id, cfg in persons_cfg.items():
        for kw in cfg.get("keywords_ja", []):
            if kw in text:
                matched.append(person_id)
                break

    # 両陛下が一致している場合、個別（TENNO/KOGO）は除外（より具体的な結果を優先）
    if "RYOUHEIKA" in matched:
        matched = [p for p in matched if p not in ("TENNO", "KOGO")]
    if "JOKO_COUPLE" in matched:
        matched = [p for p in matched if p not in ("JOKO", "JOKOGO")]

    return matched or ["OTHER"]


def get_person_info(person_id: str) -> Optional[dict]:
    """person_keywords.yaml から人物情報を取得する"""
    cfg = _load_keywords()
    return cfg.get("persons", {}).get(person_id)


def identify_event_type(text: str) -> str:
    """テキストから行事タイプを識別する"""
    cfg = _load_keywords()
    event_types = cfg.get("event_types", {})

    for event_id, event_cfg in event_types.items():
        for kw in event_cfg.get("keywords", []):
            if kw in text:
                return event_id

    return "unknown"


def get_safe_formats(person_ids: list[str], event_type: str) -> list[str]:
    """人物リストと行事タイプから適切な動画フォーマットを返す"""
    cfg = _load_keywords()
    persons_cfg = cfg.get("persons", {})
    event_types = cfg.get("event_types", {})

    # 全人物のsafe_formatsの積集合
    all_formats = None
    for pid in person_ids:
        pcfg = persons_cfg.get(pid, {})
        fmts = set(pcfg.get("safe_formats", ["長尺"]))
        all_formats = fmts if all_formats is None else all_formats & fmts

    if all_formats is None:
        all_formats = {"長尺"}

    # 行事タイプでフィルタリング
    event_cfg = event_types.get(event_type, {})
    if not event_cfg.get("shorts_suitable", True):
        all_formats.discard("Shorts")
        all_formats.discard("TikTok")
    if not event_cfg.get("long_suitable", True):
        all_formats.discard("長尺")

    return sorted(all_formats)


def record_video_posted(person_ids: list[str], event_type: str, video_title: str, posted_date: str):
    """動画投稿後に人物データベースを更新する"""
    db = _load_db()
    persons = db.setdefault("persons", {})

    for pid in person_ids:
        if pid not in persons:
            persons[pid] = {"name": pid, "total_videos": 0, "last_video_date": None, "event_history": []}

        persons[pid]["total_videos"] = persons[pid].get("total_videos", 0) + 1
        persons[pid]["last_video_date"] = posted_date
        persons[pid].setdefault("event_history", []).append({
            "event_type": event_type,
            "title": video_title,
            "date": posted_date,
        })
        # 最新100件のみ保持
        persons[pid]["event_history"] = persons[pid]["event_history"][-100:]

    _save_db(db)
    print(f"  [DB更新] {person_ids}: 投稿記録を追加 ({posted_date})")


def get_recent_event_dates(person_id: str, event_type: str, days: int = 30) -> list[str]:
    """指定人物×行事タイプの最近N日間の投稿日を返す（重複チェック用）"""
    from datetime import date, timedelta
    db = _load_db()
    person = db.get("persons", {}).get(person_id, {})
    history = person.get("event_history", [])

    cutoff = (datetime.now().date() - timedelta(days=days)).isoformat()
    return [
        h["date"] for h in history
        if h.get("event_type") == event_type and h.get("date", "") >= cutoff
    ]


def print_person_stats():
    """人物別投稿統計を表示する"""
    db = _load_db()
    cfg = _load_keywords()
    persons_cfg = cfg.get("persons", {})

    print("\n=== 人物別投稿統計 ===")
    for pid, pcfg in persons_cfg.items():
        person_db = db.get("persons", {}).get(pid, {})
        total = person_db.get("total_videos", 0)
        last = person_db.get("last_video_date", "未投稿")
        print(f"  {pcfg['name']:12s}: {total:3d}本 (最終: {last})")
