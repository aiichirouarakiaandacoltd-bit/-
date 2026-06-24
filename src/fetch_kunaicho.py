"""
宮内庁HP情報取得モジュール
kunaicho.go.jp のニュース・行事一覧を取得し、構造化データとして返す
"""

import re
import time
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup

CONFIG_PATH = "config/official_sources.yaml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KoushitsuResearchBot/1.0; +https://github.com/aiichirouarakiaandacoltd-bit/-)"
}
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.5  # 礼儀としてリクエスト間に待機


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        print(f"  [警告] 取得失敗: {url} — {e}")
        return None


def _parse_date_ja(text: str) -> Optional[str]:
    """令和7年6月24日 → 2025-06-24 形式に変換。西暦表記にも対応。"""
    reiwa_m = re.search(r"令和(\d+)年(\d+)月(\d+)日", text)
    if reiwa_m:
        y = 2018 + int(reiwa_m.group(1))
        return f"{y}-{int(reiwa_m.group(2)):02d}-{int(reiwa_m.group(3)):02d}"
    heisei_m = re.search(r"平成(\d+)年(\d+)月(\d+)日", text)
    if heisei_m:
        y = 1988 + int(heisei_m.group(1))
        return f"{y}-{int(heisei_m.group(2)):02d}-{int(heisei_m.group(3)):02d}"
    western_m = re.search(r"(\d{4})年(\d+)月(\d+)日", text)
    if western_m:
        return f"{western_m.group(1)}-{int(western_m.group(2)):02d}-{int(western_m.group(3)):02d}"
    return None


def _extract_date_from_url(url: str) -> Optional[str]:
    """URLパスに含まれる日付パターンを抽出 (例: /2025/06/24/)"""
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def fetch_news_list(max_items: int = 30) -> list[dict]:
    """宮内庁ニュース一覧を取得する"""
    cfg = _load_config()
    base_url = cfg["kunaicho"]["base_url"]
    news_url = cfg["kunaicho"]["endpoints"]["news"]

    print(f"  [取得] 宮内庁ニュース: {news_url}")
    soup = _get(news_url)
    if not soup:
        return []

    items = []
    # 宮内庁サイト構造に対応した複数のセレクタを試行
    for selector in ["ul.news-list li", "ul.list-news li", "div.news-list li", "article", "li"]:
        candidates = soup.select(selector)
        if candidates:
            break
    else:
        candidates = soup.find_all("li")

    for elem in candidates[:max_items]:
        a_tag = elem.find("a")
        if not a_tag or not a_tag.get("href"):
            continue
        href = a_tag["href"]
        full_url = urljoin(base_url, href)

        # 公式ドメイン外はスキップ
        if "kunaicho.go.jp" not in full_url:
            continue

        title = a_tag.get_text(strip=True)
        if not title:
            continue

        date_str = _parse_date_ja(elem.get_text()) or _extract_date_from_url(full_url)

        items.append({
            "source": "kunaicho_news",
            "title": title,
            "url": full_url,
            "date": date_str,
            "fetched_at": datetime.now().isoformat(),
            "official": True,
        })

    print(f"  → {len(items)}件 取得")
    return items


def fetch_activity_list(max_items: int = 30) -> list[dict]:
    """宮内庁行事一覧を取得する"""
    cfg = _load_config()
    base_url = cfg["kunaicho"]["base_url"]
    activity_url = cfg["kunaicho"]["endpoints"]["activity"]

    print(f"  [取得] 宮内庁行事: {activity_url}")
    time.sleep(REQUEST_DELAY)
    soup = _get(activity_url)
    if not soup:
        return []

    items = []
    for a_tag in soup.find_all("a", href=True)[:max_items * 2]:
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        if "kunaicho.go.jp" not in full_url:
            continue

        title = a_tag.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        parent_text = a_tag.parent.get_text() if a_tag.parent else ""
        date_str = _parse_date_ja(parent_text) or _extract_date_from_url(full_url)

        items.append({
            "source": "kunaicho_activity",
            "title": title,
            "url": full_url,
            "date": date_str,
            "fetched_at": datetime.now().isoformat(),
            "official": True,
        })
        if len(items) >= max_items:
            break

    print(f"  → {len(items)}件 取得")
    return items


def fetch_topics_list(max_items: int = 20) -> list[dict]:
    """宮内庁トピックス一覧を取得する"""
    cfg = _load_config()
    base_url = cfg["kunaicho"]["base_url"]
    topics_url = cfg["kunaicho"]["endpoints"]["topics"]

    print(f"  [取得] 宮内庁トピックス: {topics_url}")
    time.sleep(REQUEST_DELAY)
    soup = _get(topics_url)
    if not soup:
        return []

    items = []
    for a_tag in soup.find_all("a", href=True)[:max_items * 2]:
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        if "kunaicho.go.jp" not in full_url:
            continue

        title = a_tag.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        parent_text = a_tag.parent.get_text() if a_tag.parent else ""
        date_str = _parse_date_ja(parent_text) or _extract_date_from_url(full_url)

        items.append({
            "source": "kunaicho_topics",
            "title": title,
            "url": full_url,
            "date": date_str,
            "fetched_at": datetime.now().isoformat(),
            "official": True,
        })
        if len(items) >= max_items:
            break

    print(f"  → {len(items)}件 取得")
    return items


def fetch_all() -> list[dict]:
    """宮内庁HP全エンドポイントから情報を取得する（重複除去済み）"""
    all_items = []
    seen_urls = set()

    for fetch_fn in [fetch_news_list, fetch_activity_list, fetch_topics_list]:
        try:
            items = fetch_fn()
            for item in items:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    all_items.append(item)
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            print(f"  [エラー] {fetch_fn.__name__}: {e}")

    return all_items


if __name__ == "__main__":
    results = fetch_all()
    print(f"\n合計 {len(results)} 件取得完了")
    for r in results[:5]:
        print(f"  [{r['date']}] {r['title'][:40]} — {r['url']}")
