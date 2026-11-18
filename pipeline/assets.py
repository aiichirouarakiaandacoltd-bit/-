"""ステージ3: 映像素材の検索・利用可否判定・取得。

方針(指示書7章):
  - 自動で取り込むのは「利用条件が機械的に確認できる」素材のみ:
      * Wikimedia Commons の自由ライセンス(CC0/PD/CC BY/CC BY-SA)画像
        (ja.wikipedia API の記事画像 → Commons メタデータ、および Commons 検索)
      * assets/library/ に人が置いた利用許可済み素材(同名 .json に権利情報)
  - 宮内庁サイトの皇族方の写真・映像は規約上「要相談」→ 候補URLとして記録のみ(取り込まない)
  - 報道写真は候補にも入れない(出典表記や「代表撮影」は利用許可ではない)
  - 素材が見つからないシーンは、オリジナルの図解テロップカードで代替(render で生成)
出力: assets/jobs/<job>/manifest.json と画像ファイル
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.parse
from pathlib import Path

import requests

from .common import ROOT, Job, get_logger, load_json, now_jst, save_json, settings

JAWIKI = "https://ja.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"

# 人物 → ja.wikipedia 記事名(画像の取得元)
PERSON_ARTICLES = {
    "天皇陛下": "徳仁", "天皇": "徳仁", "陛下": "徳仁",
    "皇后雅子さま": "皇后雅子", "雅子さま": "皇后雅子", "皇后さま": "皇后雅子",
    "天皇皇后両陛下": "徳仁", "両陛下": "徳仁",
    "愛子さま": "愛子内親王", "敬宮愛子さま": "愛子内親王",
    "佳子さま": "佳子内親王",
    "秋篠宮さま": "秋篠宮文仁親王", "秋篠宮ご夫妻": "秋篠宮文仁親王",
    "紀子さま": "文仁親王妃紀子",
    "悠仁さま": "悠仁親王",
    "上皇さま": "明仁", "上皇后美智子さま": "上皇后美智子",
}
EXCLUDE_FILE = re.compile(r"(\.svg|\.gif|\.tif|seal|crest|emblem|flag|logo|signature|map|coat_of_arms|紋|旗|地図|Imperial_Seal|Commons-logo|Wiki)", re.I)


class Http:
    def __init__(self, log):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = settings()["assets"]["commons_user_agent"]
        self.log = log
        self.commons_blocked = False

    def get_json(self, url, params, tries=3):
        params = {**params, "format": "json", "formatversion": 2}
        for k in range(tries):
            try:
                r = self.s.get(url, params=params, timeout=25)
                if r.status_code == 429:
                    if "commons" in url:
                        self.commons_blocked = True
                        self.log.warning("Commons API がレート制限(429)中 → ja.wikipedia 経由のみで検索")
                        return None
                    time.sleep(3 * (k + 1))
                    continue
                r.raise_for_status()
                time.sleep(0.4)
                return r.json()
            except Exception as e:
                self.log.warning(f"API失敗 {url} {e}")
                time.sleep(2 * (k + 1))
        return None


def _strip(s: str | None) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def license_ok(meta: dict) -> tuple[bool, str]:
    cfg = settings()["assets"]
    lic = _strip(meta.get("LicenseShortName", {}).get("value", ""))
    usage = _strip(meta.get("UsageTerms", {}).get("value", ""))
    full = f"{lic} {usage}"
    if any(re.search(rf"\b{re.escape(b)}\b", full) for b in cfg["blocked_license_keywords"]):
        return False, f"不可: {lic}(非営利/改変禁止/フェアユース等)"
    if any(a.lower() in full.lower() for a in cfg["allowed_licenses"]):
        return True, lic
    return False, f"不可(未確認ライセンス): {lic or '不明'}"


def _imageinfo(http: Http, api: str, titles: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(titles), 20):
        d = http.get_json(api, {"action": "query", "titles": "|".join(titles[i:i + 20]), "prop": "imageinfo",
                                "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600,
                                "iiextmetadatafilter": "LicenseShortName|UsageTerms|Artist|Credit|DateTimeOriginal|ImageDescription|AttributionRequired|LicenseUrl"})
        if not d:
            continue
        for p in d.get("query", {}).get("pages", []):
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]
            out.append({"title": p["title"], **ii})
    return out


def jawiki_article_images(http: Http, article: str) -> list[dict]:
    d = http.get_json(JAWIKI, {"action": "query", "titles": article, "prop": "images", "imlimit": 50, "redirects": 1})
    if not d:
        return []
    titles = [im["title"] for p in d["query"]["pages"] for im in p.get("images", []) if not EXCLUDE_FILE.search(im["title"])]
    return _imageinfo(http, JAWIKI, titles)


def jawiki_search_article(http: Http, q: str) -> str | None:
    d = http.get_json(JAWIKI, {"action": "query", "list": "search", "srsearch": q, "srlimit": 1})
    hits = (d or {}).get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def commons_search(http: Http, q: str, n=12) -> list[dict]:
    if http.commons_blocked:
        return []
    d = http.get_json(COMMONS, {"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q,
                                "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600})
    if not d:
        return []
    return [{"title": p["title"], **p["imageinfo"][0]} for p in d.get("query", {}).get("pages", []) if "imageinfo" in p]


def library_assets() -> list[dict]:
    out = []
    for f in sorted((ROOT / "assets" / "library").glob("*")):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"):
            continue
        meta = load_json(f.with_suffix(".json"), None)
        if not meta or not meta.get("usage_ok"):
            continue  # 権利情報が無い素材は使わない
        out.append({"path": str(f), **meta})
    return out


def _score(c: dict, subject: str, queries: list[str]) -> float:
    s = 0.0
    w, h = c.get("width", 0), c.get("height", 0)
    s += min(w * h / 2_000_000, 2.0)
    s += 1.0 if h >= w * 0.9 else 0.0  # 縦長・正方形は9:16に切り出しやすい
    t = c["title"].lower()
    for q in queries:
        for tok in re.findall(r"[a-z]{4,}", q.lower()):
            if tok in t:
                s += 0.3
    yr = re.search(r"(20[0-2]\d)", c.get("date", "") + c["title"])
    if yr:
        s += min((int(yr.group(1)) - 2005) * 0.08, 1.5)
    return s


def collect(job: Job, script: dict) -> dict:
    log = get_logger(job)
    cfg = settings()["assets"]
    http = Http(log)
    lib = library_assets()
    manifest = {"job_id": job.id, "collected_at": now_jst().isoformat(timespec="seconds"),
                "policy": "自由ライセンスのみ自動取得。宮内庁の皇族写真・報道写真は取り込まない。", "scenes": [], "files": {},
                "rejected": [], "candidates_need_permission": []}
    used: dict[str, int] = {}
    cache: dict[str, list[dict]] = {}

    # 宮内庁一次情報ページの画像は「要許可」候補として記録のみ
    for f in script.get("facts", []):
        if "kunaicho.go.jp" in (f.get("url") or ""):
            manifest["candidates_need_permission"].append({
                "url": f["url"], "rights_holder": "宮内庁",
                "terms": "皇室の方々が写っている画像・映像は宮内庁長官官房総務課広報室に要相談 (https://www.kunaicho.go.jp/copyright/)",
                "decision": "取り込まない(許可取得後に assets/library へ権利情報付きで配置すれば自動利用)"})

    for sc in script["scenes"]:
        v = sc.get("visual", {})
        subject = v.get("subject", "")
        queries = v.get("commons_queries", [])
        pool: list[dict] = []
        # 1) ライブラリ(利用許可済み)
        for a in lib:
            tags = " ".join(a.get("tags", [])) + " " + a.get("title", "")
            if subject and subject in tags or any(q in tags for q in queries):
                pool.append({"kind": "library", "title": a.get("title", Path(a["path"]).name), "local": a["path"],
                             "license": a.get("license"), "source": a.get("source"), "rights_holder": a.get("rights_holder"),
                             "width": 2000, "height": 2000, "score_bonus": 5})
        # 2) ja.wikipedia 記事画像(人物は対応表、それ以外は記事検索)
        articles = []
        if subject in PERSON_ARTICLES:
            articles.append(PERSON_ARTICLES[subject])
        for k, art in PERSON_ARTICLES.items():
            if k in subject and art not in articles:
                articles.append(art)
        if v.get("kind") in ("place", "object", "event") or not articles:
            for q in [subject] + [q for q in queries if re.search(r"[぀-鿿]", q)]:
                if q:
                    a = jawiki_search_article(http, q)
                    if a and a not in articles:
                        articles.append(a)
                        break
        for art in articles[:2]:
            key = "wiki:" + art
            if key not in cache:
                cache[key] = jawiki_article_images(http, art)
            pool += [{**c, "kind": "commons", "via": f"ja.wikipedia:{art}"} for c in cache[key]]
        # 3) Commons 検索(レート制限時はスキップ)
        for q in queries[:3]:
            key = "commons:" + q
            if key not in cache:
                cache[key] = commons_search(http, q)
            pool += [{**c, "kind": "commons", "via": f"commons-search:{q}"} for c in cache[key]]

        chosen = []
        seen = set()
        for c in pool:
            if c["title"] in seen:
                continue
            seen.add(c["title"])
            if c["kind"] == "library":
                c["license_ok"], c["license"] = True, c.get("license") or "利用許可済み(ライブラリ)"
                chosen.append(c)
                continue
            if EXCLUDE_FILE.search(c["title"]) or c.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
                continue
            ok, lic = license_ok(c.get("extmetadata", {}))
            meta = c.get("extmetadata", {})
            c["license"] = lic
            c["artist"] = _strip(meta.get("Artist", {}).get("value"))[:200]
            c["credit"] = _strip(meta.get("Credit", {}).get("value"))[:200]
            c["date"] = _strip(meta.get("DateTimeOriginal", {}).get("value"))[:40]
            c["description"] = _strip(meta.get("ImageDescription", {}).get("value"))[:300]
            c["license_url"] = _strip(meta.get("LicenseUrl", {}).get("value"))
            if not ok:
                manifest["rejected"].append({"scene": sc["id"], "title": c["title"], "reason": lic})
                continue
            if max(c.get("width", 0), c.get("height", 0)) < cfg["min_long_side"]:
                manifest["rejected"].append({"scene": sc["id"], "title": c["title"], "reason": "解像度不足"})
                continue
            chosen.append(c)
        chosen.sort(key=lambda c: _score(c, subject, queries) + c.get("score_bonus", 0) - 1.2 * used.get(c["title"], 0), reverse=True)
        chosen = chosen[: cfg["max_per_scene_candidates"]]
        entry = {"scene": sc["id"], "subject": subject, "kind": v.get("kind"), "queries": queries, "picks": []}
        for c in chosen[:3]:
            f = _download(http, c, job, log) if c["kind"] != "library" else c["local"]
            if not f:
                continue
            used[c["title"]] = used.get(c["title"], 0) + 1
            rec = {
                "file": str(Path(f).relative_to(ROOT)) if Path(f).is_relative_to(ROOT) else f,
                "source_title": c["title"],
                "source_url": c.get("descriptionurl") or c.get("source"),
                "original_url": c.get("url"),
                "found_via": c.get("via", "library"),
                "rights_holder": c.get("artist") or c.get("rights_holder") or "",
                "credit": c.get("credit", ""),
                "license": c["license"],
                "license_url": c.get("license_url", ""),
                "shot_date": c.get("date", ""),
                "description": c.get("description", ""),
                "retrieved_at": now_jst().isoformat(timespec="seconds"),
                "usage_decision": "利用可(自由ライセンス・クレジット表記が必要)" if c["kind"] != "library" else "利用可(ライブラリ登録済み)",
                "scene": sc["id"],
            }
            manifest["files"][rec["file"]] = rec
            entry["picks"].append(rec["file"])
        if not entry["picks"]:
            entry["fallback"] = "図解テロップカード(オリジナル)"
            log.info(f"  {sc['id']} {subject}: 利用可能な素材なし → 図解カードで代替")
        else:
            log.info(f"  {sc['id']} {subject}: {len(entry['picks'])}点 ({', '.join(Path(p).name[:30] for p in entry['picks'])})")
        manifest["scenes"].append(entry)
    manifest["credits"] = sorted({f"{r['source_title'].replace('File:', '').replace('ファイル:', '')} / {r['rights_holder'] or '作者不明'} / {r['license']}"
                                  for r in manifest["files"].values()})
    save_json(job.asset_manifest, manifest)
    n_img = len(manifest["files"])
    n_fb = sum(1 for s in manifest["scenes"] if not s["picks"])
    log.info(f"素材: {n_img}ファイル取得 / 代替カード {n_fb}シーン / 却下 {len(manifest['rejected'])}件 → {job.asset_manifest}")
    job.mark("assets", True, files=n_img, fallback_scenes=n_fb)
    return manifest


def _download(http: Http, c: dict, job: Job, log) -> str | None:
    # thumb.wikimedia.org は環境で未許可のため原寸(upload.wikimedia.org)を取得してローカルで縮小
    url = c.get("url") or c.get("thumburl")
    if not url:
        return None
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
    name = hashlib.md5(c["title"].encode()).hexdigest()[:10] + ".jpg"
    path = job.assets / name
    if path.exists():
        return str(path)
    for k in range(3):
        try:
            r = http.s.get(url, timeout=60)
            if r.status_code == 429:
                time.sleep(4 * (k + 1))
                continue
            r.raise_for_status()
            from io import BytesIO
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(BytesIO(r.content))).convert("RGB")
            if max(im.size) > 2400:
                im.thumbnail((2400, 2400), Image.LANCZOS)
            path = path.with_suffix(".jpg")
            im.save(path, quality=93)
            time.sleep(0.5)
            return str(path)
        except Exception as e:
            log.warning(f"ダウンロード失敗 {url}: {e}")
            time.sleep(2)
    return None


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    j = Job(a.job)
    collect(j, load_json(j.script))
