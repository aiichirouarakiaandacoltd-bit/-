"""宮内庁公式HP新着情報取得モジュール (Phase 1)"""

import json
import re
import urllib.request
import urllib.error
import ssl
from datetime import datetime, date
from html.parser import HTMLParser
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
FETCHED_URLS_PATH = DATA_DIR / "fetched_urls.json"

KUNAICHO_BASE = "https://www.kunaicho.go.jp"
GONITTEI_URL = f"{KUNAICHO_BASE}/page/gonittei/top/1"
NEWS_URL = f"{KUNAICHO_BASE}/kunaicho/koho/taiseki/taiseki-top.html"


class KunaichoScheduleParser(HTMLParser):
    """宮内庁ご日程ページのHTMLパーサー"""

    def __init__(self):
        super().__init__()
        self.entries = []
        self._current = {}
        self._in_date = False
        self._in_content = False
        self._in_link = False
        self._capture = ""
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._tag_stack.append(tag)

        if tag == "h3" and "gonittei-date" in attrs_dict.get("class", ""):
            self._in_date = True
            self._capture = ""
        elif tag == "td":
            self._in_content = True
            self._capture = ""
        elif tag == "a" and self._in_content:
            href = attrs_dict.get("href", "")
            if href:
                self._in_link = True
                if not href.startswith("http"):
                    href = KUNAICHO_BASE + href
                self._current.setdefault("urls", []).append(href)

    def handle_endtag(self, tag):
        if self._tag_stack:
            self._tag_stack.pop()

        if tag == "h3" and self._in_date:
            self._in_date = False
            self._current["date_text"] = self._capture.strip()
        elif tag == "td" and self._in_content:
            self._in_content = False
            text = self._capture.strip()
            if text:
                self._current["content"] = text
                if self._current.get("date_text"):
                    self.entries.append(dict(self._current))
                self._current = {"date_text": self._current.get("date_text", "")}
        elif tag == "a":
            self._in_link = False

    def handle_data(self, data):
        if self._in_date or self._in_content:
            self._capture += data


class KunaichoNewsParser(HTMLParser):
    """宮内庁お知らせページのHTMLパーサー"""

    def __init__(self):
        super().__init__()
        self.entries = []
        self._in_item = False
        self._in_link = False
        self._current = {}
        self._capture = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "li":
            self._in_item = True
            self._current = {}
            self._capture = ""
        elif tag == "a" and self._in_item:
            href = attrs_dict.get("href", "")
            if href:
                if not href.startswith("http"):
                    href = KUNAICHO_BASE + href
                self._current["url"] = href
            self._in_link = True

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self._in_link = False
        elif tag == "li" and self._in_item:
            self._in_item = False
            text = self._capture.strip()
            if text:
                self._current["text"] = text
                date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
                if not date_match:
                    date_match = re.search(r"令和\d+年(\d{1,2})月(\d{1,2})日", text)
                if date_match:
                    self._current["has_date"] = True
                if self._current.get("url") or text:
                    self.entries.append(dict(self._current))

    def handle_data(self, data):
        if self._in_item:
            self._capture += data


def load_fetched_urls() -> dict:
    """取得済みURLデータベースを読み込む"""
    if FETCHED_URLS_PATH.exists():
        with open(FETCHED_URLS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "1.0", "last_updated": None, "urls": []}


def save_fetched_urls(data: dict):
    """取得済みURLデータベースを保存する"""
    data["last_updated"] = datetime.now().isoformat()
    FETCHED_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FETCHED_URLS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_url_fetched(url: str, fetched_data: dict) -> bool:
    """URLが取得済みか判定する"""
    return any(entry["url"] == url for entry in fetched_data.get("urls", []))


def register_url(url: str, source: str, fetched_data: dict):
    """URLを取得済みとして登録する"""
    if not is_url_fetched(url, fetched_data):
        fetched_data["urls"].append({
            "url": url,
            "source": source,
            "fetched_at": datetime.now().isoformat(),
        })


def fetch_page(url: str) -> str:
    """URLからHTMLを取得する"""
    ctx = ssl.create_default_context()
    ca_bundle = Path("/root/.ccr/ca-bundle.crt")
    if ca_bundle.exists():
        ctx.load_verify_locations(str(ca_bundle))

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; KoshitsuResearchBot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja,en;q=0.5",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(f"公式URL取得エラー: {url} - {e}") from e
    except Exception as e:
        raise RuntimeError(f"公式URL取得エラー: {url} - {e}") from e


def fetch_kunaicho_schedule() -> list[dict]:
    """宮内庁ご日程ページから新着情報を取得する"""
    try:
        html = fetch_page(GONITTEI_URL)
    except RuntimeError as e:
        print(f"[警告] {e}")
        return []

    parser = KunaichoScheduleParser()
    parser.feed(html)

    fetched = load_fetched_urls()
    results = []

    for entry in parser.entries:
        urls = entry.get("urls", [])
        content = entry.get("content", "")
        date_text = entry.get("date_text", "")

        is_new = True
        for url in urls:
            if is_url_fetched(url, fetched):
                is_new = False
                break

        if is_new and content:
            result = {
                "source": "宮内庁公式HP（ご日程）",
                "date_text": date_text,
                "content": content,
                "urls": urls,
                "fetched_at": datetime.now().isoformat(),
                "has_official_material": bool(urls),
            }
            results.append(result)

            for url in urls:
                register_url(url, "宮内庁公式HP", fetched)

    if not parser.entries:
        page_url = GONITTEI_URL
        if not is_url_fetched(page_url, fetched):
            register_url(page_url, "宮内庁公式HP", fetched)
            results.append({
                "source": "宮内庁公式HP（ご日程）",
                "date_text": date.today().isoformat(),
                "content": "ご日程ページを確認しました。個別エントリの解析は手動確認をお勧めします。",
                "urls": [page_url],
                "fetched_at": datetime.now().isoformat(),
                "has_official_material": False,
                "note": "HTMLの構造が想定と異なる可能性があります。手動確認してください。",
            })

    save_fetched_urls(fetched)
    return results


def fetch_kunaicho_news() -> list[dict]:
    """宮内庁お知らせページから新着情報を取得する"""
    try:
        html = fetch_page(NEWS_URL)
    except RuntimeError as e:
        print(f"[警告] {e}")
        return []

    parser = KunaichoNewsParser()
    parser.feed(html)

    fetched = load_fetched_urls()
    results = []

    for entry in parser.entries:
        url = entry.get("url", "")
        text = entry.get("text", "")

        if url and not is_url_fetched(url, fetched):
            result = {
                "source": "宮内庁公式HP（お知らせ）",
                "date_text": date.today().isoformat(),
                "content": text,
                "urls": [url] if url else [],
                "fetched_at": datetime.now().isoformat(),
                "has_official_material": False,
            }
            results.append(result)
            if url:
                register_url(url, "宮内庁公式HP", fetched)

    save_fetched_urls(fetched)
    return results


def fetch_all() -> list[dict]:
    """宮内庁の全情報を取得する"""
    results = []

    print("[INFO] 宮内庁ご日程ページを取得中...")
    schedule = fetch_kunaicho_schedule()
    results.extend(schedule)
    print(f"[INFO] ご日程: {len(schedule)}件取得")

    print("[INFO] 宮内庁お知らせページを取得中...")
    news = fetch_kunaicho_news()
    results.extend(news)
    print(f"[INFO] お知らせ: {len(news)}件取得")

    return results


if __name__ == "__main__":
    entries = fetch_all()
    print(f"\n取得結果: {len(entries)}件")
    for e in entries:
        print(f"  - [{e['source']}] {e['content'][:60]}...")
