"""政府関連公式サイト取得モジュール (Phase 5)

首相官邸、外務省、地方自治体、訪問先施設の公式サイトから
皇室関連情報を取得する。Phase 5で本実装予定。
"""

from datetime import datetime


def generate_check_entries() -> list[dict]:
    """政府関連サイトの手動確認エントリを生成する"""
    sources = [
        {
            "name": "首相官邸公式サイト",
            "url": "https://www.kantei.go.jp",
            "check_path": "/jp/headline/",
        },
        {
            "name": "外務省公式サイト",
            "url": "https://www.mofa.go.jp",
            "check_path": "/mofaj/press/release/",
        },
    ]

    entries = []
    for source in sources:
        entries.append({
            "source": source["name"],
            "check_url": source["url"] + source["check_path"],
            "status": "Phase 5で自動化予定",
            "date": datetime.now().isoformat(),
            "note": f"{source['name']}の皇室関連情報を手動で確認してください。",
            "enabled": False,
        })

    return entries


if __name__ == "__main__":
    entries = generate_check_entries()
    for e in entries:
        print(f"[{e['source']}] {e['check_url']} - {e['status']}")
