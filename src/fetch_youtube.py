"""
宮内庁公式YouTubeチャンネル 動画情報取得モジュール
RSSフィードから最新動画リストを取得する
"""

import re
import time
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree as ET

import requests
import yaml

CONFIG_PATH = "config/official_sources.yaml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KoushitsuResearchBot/1.0)"
}
REQUEST_TIMEOUT = 15


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_youtube_rss(max_items: int = 20) -> list[dict]:
    """宮内庁公式YouTubeのRSSフィードから動画一覧を取得する"""
    cfg = _load_config()
    yt_cfg = cfg.get("kunaicho_youtube", {})

    if not yt_cfg.get("enabled", False):
        print("  [スキップ] YouTube取得は無効（enabled: false）")
        return []

    rss_url = yt_cfg.get("rss_url")
    channel_url = yt_cfg.get("channel_url", "")

    print(f"  [取得] YouTube RSS: {rss_url}")

    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [警告] YouTube RSS取得失敗: {e}")
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"  [エラー] RSS解析失敗: {e}")
        return []

    items = []
    for entry in root.findall("atom:entry", ns)[:max_items]:
        title_elem = entry.find("atom:title", ns)
        link_elem = entry.find("atom:link", ns)
        published_elem = entry.find("atom:published", ns)
        video_id_elem = entry.find("yt:videoId", ns)

        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
        url = link_elem.get("href", "") if link_elem is not None else ""
        published = published_elem.text.strip() if published_elem is not None and published_elem.text else ""
        video_id = video_id_elem.text.strip() if video_id_elem is not None and video_id_elem.text else ""

        date_str = None
        if published:
            m = re.match(r"(\d{4}-\d{2}-\d{2})", published)
            if m:
                date_str = m.group(1)

        if not title or not url:
            continue

        items.append({
            "source": "kunaicho_youtube",
            "title": title,
            "url": url,
            "video_id": video_id,
            "date": date_str,
            "fetched_at": datetime.now().isoformat(),
            "official": True,
            "format_hint": "動画",
        })

    print(f"  → {len(items)}件 取得")
    return items


def fetch_all() -> list[dict]:
    """YouTube情報を取得する（将来的に複数チャンネル対応可能）"""
    return fetch_youtube_rss()


if __name__ == "__main__":
    results = fetch_all()
    print(f"\n合計 {len(results)} 件取得完了")
    for r in results[:5]:
        print(f"  [{r['date']}] {r['title'][:50]}")
        print(f"    URL: {r['url']}")
