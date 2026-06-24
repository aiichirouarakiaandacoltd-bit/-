"""過去動画との重複判定モジュール (Phase 4)"""

import json
from datetime import datetime
from pathlib import Path

from person_database import classify_persons

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
PROJECT_DB_PATH = DATA_DIR / "project_database.json"


def load_project_db() -> dict:
    if PROJECT_DB_PATH.exists():
        with open(PROJECT_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "1.0", "last_updated": None, "next_id": 1, "projects": []}


def extract_keywords(text: str) -> set[str]:
    """テキストからキーワードを抽出する"""
    keywords = set()

    important_words = [
        "訪問", "式典", "儀式", "晩餐", "外国", "国賓", "公務",
        "お出まし", "ご挨拶", "交流", "面会", "謁見", "園遊会",
        "参拝", "追悼", "慰問", "視察", "懇談", "表彰", "祝賀",
        "オランダ", "イギリス", "アメリカ", "フランス", "ドイツ",
        "トルコ", "中国", "韓国", "インド", "ブラジル",
    ]

    for word in important_words:
        if word in text:
            keywords.add(word)

    return keywords


def calculate_overlap(new_entry: dict, existing_project: dict) -> dict:
    """新規企画と既存プロジェクトの重複度を計算する"""
    new_content = new_entry.get("content", "")
    new_persons = set(classify_persons(new_content))
    new_keywords = extract_keywords(new_content)
    new_urls = set(new_entry.get("urls", []))

    existing_title = existing_project.get("title", "")
    existing_persons = set(existing_project.get("persons", []))
    existing_keywords = extract_keywords(existing_title)
    existing_urls = set()
    if existing_project.get("source_url"):
        existing_urls.add(existing_project["source_url"])
    for url in existing_project.get("related_urls", []):
        existing_urls.add(url)

    overlap_scores = {}

    # 人物重複
    if new_persons and existing_persons:
        person_overlap = len(new_persons & existing_persons) / max(len(new_persons | existing_persons), 1)
        overlap_scores["人物"] = person_overlap * 100
    else:
        overlap_scores["人物"] = 0

    # キーワード重複
    if new_keywords and existing_keywords:
        kw_overlap = len(new_keywords & existing_keywords) / max(len(new_keywords | existing_keywords), 1)
        overlap_scores["キーワード"] = kw_overlap * 100
    else:
        overlap_scores["キーワード"] = 0

    # URL重複
    if new_urls and existing_urls:
        url_overlap = len(new_urls & existing_urls) / max(len(new_urls | existing_urls), 1)
        overlap_scores["公式URL"] = url_overlap * 100
    else:
        overlap_scores["公式URL"] = 0

    # タイトル類似（簡易）
    title_sim = 0
    if new_content and existing_title:
        new_chars = set(new_content[:50])
        existing_chars = set(existing_title)
        if new_chars and existing_chars:
            title_sim = len(new_chars & existing_chars) / max(len(new_chars | existing_chars), 1) * 100
    overlap_scores["タイトル類似"] = title_sim

    # 総合重複度
    weights = {"人物": 0.3, "キーワード": 0.3, "公式URL": 0.25, "タイトル類似": 0.15}
    total = sum(overlap_scores[k] * weights[k] for k in weights)

    return {
        "overlap_percentage": round(total, 1),
        "detail_scores": {k: round(v, 1) for k, v in overlap_scores.items()},
        "existing_project": {
            "id": existing_project.get("id", ""),
            "title": existing_title,
            "status": existing_project.get("status", ""),
        },
    }


def check_duplicates(new_entry: dict) -> list[dict]:
    """新規企画の重複チェックを行う"""
    db = load_project_db()
    projects = db.get("projects", [])

    results = []
    for project in projects:
        overlap = calculate_overlap(new_entry, project)
        if overlap["overlap_percentage"] > 20:
            results.append(overlap)

    results.sort(key=lambda x: x["overlap_percentage"], reverse=True)
    return results


def format_duplicate_report(new_entry: dict, duplicates: list[dict]) -> str:
    """重複判定レポートを生成する"""
    if not duplicates:
        return "重複判定：重複なし\n新規企画として制作可能です。"

    lines = []
    for dup in duplicates:
        pct = dup["overlap_percentage"]
        proj = dup["existing_project"]

        lines.append(f"重複判定：{pct}%重複")
        lines.append(f"過去動画：{proj['title']}")
        lines.append(f"ステータス：{proj['status']}")

        if pct >= 70:
            lines.append("判断：重複度が高いため、別の切り口での差別化が必要です。")
        elif pct >= 40:
            lines.append("判断：部分的に重複していますが、切り口を変えれば別企画として制作可能です。")
        else:
            lines.append("判断：軽微な重複のみ。新規企画として制作可能です。")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    test = {
        "content": "天皇皇后両陛下がオランダ国王夫妻と交流された",
        "urls": ["https://www.kunaicho.go.jp/test"],
    }
    dups = check_duplicates(test)
    print(format_duplicate_report(test, dups))
