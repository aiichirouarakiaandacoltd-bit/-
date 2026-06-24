"""人物別データベース管理モジュール (Phase 2/4)"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent / "config"
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
PERSON_DB_PATH = DATA_DIR / "person_database.json"
PERSON_KEYWORDS_PATH = CONFIG_DIR / "person_keywords.yaml"


def load_person_keywords() -> dict:
    with open(PERSON_KEYWORDS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_person_db() -> dict:
    if PERSON_DB_PATH.exists():
        with open(PERSON_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "last_updated": None,
        "persons": {},
    }


def save_person_db(db: dict):
    db["last_updated"] = datetime.now().isoformat()
    PERSON_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSON_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def classify_persons(text: str) -> list[str]:
    """テキストから関連人物を特定する"""
    config = load_person_keywords()
    persons = config.get("persons", {})
    matched = []

    for person_name, info in persons.items():
        keywords = info.get("keywords", []) + info.get("aliases", [])
        for kw in keywords:
            if kw in text:
                if person_name not in matched:
                    matched.append(person_name)
                break

    return matched


def add_entry(person: str, entry: dict):
    """人物データベースにエントリを追加する"""
    db = load_person_db()

    if person not in db["persons"]:
        db["persons"][person] = {"category": "その他", "entries": []}

    entry_with_meta = {
        "date": entry.get("date_text", datetime.now().strftime("%Y-%m-%d")),
        "event_name": entry.get("content", "")[:100],
        "place": entry.get("place", ""),
        "official_url": entry.get("urls", [None])[0] if entry.get("urls") else None,
        "all_urls": entry.get("urls", []),
        "has_official_material": entry.get("has_official_material", False),
        "related_keywords": [],
        "suitable_for_long": None,
        "suitable_for_shorts": None,
        "suitable_for_tiktok": None,
        "planning_status": "未分類",
        "memo": "",
        "added_at": datetime.now().isoformat(),
    }

    db["persons"][person]["entries"].append(entry_with_meta)
    save_person_db(db)


def add_entries_from_research(entries: list[dict]):
    """リサーチ結果から人物データベースに一括追加する"""
    for entry in entries:
        content = entry.get("content", "")
        persons = classify_persons(content)

        if not persons:
            persons = ["その他皇族"]

        for person in persons:
            add_entry(person, entry)


def query_person(person: str, days: int = 90) -> list[dict]:
    """人物別に期間指定でエントリを取得する"""
    db = load_person_db()

    if person not in db["persons"]:
        print(f"[警告] 人物「{person}」はデータベースに存在しません。")
        return []

    entries = db["persons"][person].get("entries", [])
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered = [e for e in entries if e.get("date", "") >= cutoff]
    filtered.sort(key=lambda x: x.get("date", ""), reverse=True)

    return filtered


def list_persons() -> list[str]:
    """登録済み人物一覧を返す"""
    db = load_person_db()
    return list(db["persons"].keys())


if __name__ == "__main__":
    print("登録済み人物:")
    for p in list_persons():
        db = load_person_db()
        count = len(db["persons"][p].get("entries", []))
        print(f"  - {p}: {count}件")
