"""宮内庁公式YouTube確認モジュール (Phase 2)

YouTube Data APIキーがない場合は手動確認欄として動作。
"""

from datetime import datetime


YOUTUBE_URL = "https://www.youtube.com/@kunaicho"


def generate_check_entry() -> dict:
    """YouTube手動確認エントリを生成する"""
    return {
        "source": "宮内庁公式YouTube",
        "check_url": YOUTUBE_URL,
        "status": "手動確認必要",
        "date": datetime.now().isoformat(),
        "note": "YouTube公式チャンネルの新規動画を手動で確認してください。",
        "items_to_check": [
            "新規動画の有無",
            "動画タイトル",
            "動画内容（行事・人物）",
            "公開日時",
        ],
        "manual_entry_fields": {
            "has_new_video": None,
            "video_url": None,
            "title": None,
            "description": None,
            "persons": [],
        },
    }


if __name__ == "__main__":
    entry = generate_check_entry()
    print(f"YouTube確認URL: {entry['check_url']}")
    print(f"ステータス: {entry['status']}")
