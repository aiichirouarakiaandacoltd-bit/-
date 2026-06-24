"""
政府機関情報取得モジュール（Phase 5 スタブ）
首相官邸・外務省など宮内庁以外の公式ソースからの情報取得
現在はスタブ実装。Phase 5 で有効化予定。
"""

import yaml

CONFIG_PATH = "config/official_sources.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_kantei() -> list[dict]:
    """首相官邸ニュース取得（Phase 5 未実装）"""
    cfg = _load_config()
    if not cfg.get("kantei", {}).get("enabled", False):
        return []
    # Phase 5: BeautifulSoupで kantei.go.jp/jp/tyoukanpress/ をスクレイピング
    print("  [スキップ] 首相官邸取得は Phase 5 で有効化予定")
    return []


def fetch_mofa() -> list[dict]:
    """外務省ニュース取得（Phase 5 未実装）"""
    cfg = _load_config()
    if not cfg.get("mofa", {}).get("enabled", False):
        return []
    # Phase 5: BeautifulSoupで mofa.go.jp/mofaj/press/ をスクレイピング
    print("  [スキップ] 外務省取得は Phase 5 で有効化予定")
    return []


def fetch_all() -> list[dict]:
    """全政府機関情報を取得する（有効化済みのもののみ）"""
    items = []
    items.extend(fetch_kantei())
    items.extend(fetch_mofa())
    return items


if __name__ == "__main__":
    results = fetch_all()
    print(f"政府機関情報: {len(results)} 件")
