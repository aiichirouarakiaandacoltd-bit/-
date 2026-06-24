"""
宮内庁公式Instagram 手動確認テンプレート生成モジュール
Instagram API なしでは自動取得不可のため、手動確認用のチェックリストを生成する
"""

from datetime import datetime

import yaml

CONFIG_PATH = "config/official_sources.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_manual_check_section() -> str:
    """デイリーレポートに挿入するInstagram手動確認セクションを生成する"""
    cfg = _load_config()
    ig_cfg = cfg.get("kunaicho_instagram", {})

    account = ig_cfg.get("account", "@kunaicho_jp")
    profile_url = ig_cfg.get("profile_url", "https://www.instagram.com/kunaicho_jp/")
    today = datetime.now().strftime("%Y年%m月%d日")

    section = f"""
## 📸 Instagram手動確認（{today}）

**確認先**: {account}
**URL**: {profile_url}

### 確認チェックリスト
- [ ] 本日の投稿: ___件
- [ ] 投稿内容（タイトル/説明）:
  1.
  2.
  3.
- [ ] 写真枚数の確認
- [ ] キャプション内の日付・行事名の確認
- [ ] ハッシュタグに新規キーワードがあれば下記に記録:

### 本日の新規投稿メモ
（荒木さんが確認後に記入してください）

---
"""
    return section


def fetch_all() -> list[dict]:
    """Instagram情報を返す（手動確認のため空リストを返す）"""
    cfg = _load_config()
    ig_cfg = cfg.get("kunaicho_instagram", {})

    if not ig_cfg.get("manual_check", False):
        return []

    # 手動確認セクションをログに出力
    print("  [手動確認] 宮内庁Instagram（@kunaicho_jp）を直接確認してください:")
    print(f"    {ig_cfg.get('profile_url', 'https://www.instagram.com/kunaicho_jp/')}")
    return []


if __name__ == "__main__":
    print(generate_manual_check_section())
