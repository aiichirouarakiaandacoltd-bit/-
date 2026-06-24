"""宮内庁公式Instagram確認モジュール (Phase 2)

Instagram APIへの自動アクセスは制限があるため、
手動確認URL欄として実装。
"""

from datetime import datetime


INSTAGRAM_URL = "https://www.instagram.com/kunaicho_jp/"


def generate_check_entry() -> dict:
    """Instagram手動確認エントリを生成する"""
    return {
        "source": "宮内庁公式Instagram",
        "check_url": INSTAGRAM_URL,
        "status": "手動確認必要",
        "date": datetime.now().isoformat(),
        "note": "Instagram公式アカウントの新規投稿を手動で確認してください。",
        "items_to_check": [
            "新規投稿の有無",
            "投稿内容（行事・人物）",
            "公式写真の使用可否",
            "投稿日時",
        ],
        "manual_entry_fields": {
            "has_new_post": None,
            "post_url": None,
            "description": None,
            "persons": [],
            "usable_material": None,
        },
    }


if __name__ == "__main__":
    entry = generate_check_entry()
    print(f"Instagram確認URL: {entry['check_url']}")
    print(f"ステータス: {entry['status']}")
