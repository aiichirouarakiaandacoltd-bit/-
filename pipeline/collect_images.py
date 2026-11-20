"""制作ルール 第3章: 人物画像の収集と ledger.csv(画像台帳)。

収集先(優先順): 宮内庁の写真ページ → 官公庁・主催者 → 主要報道(ネットワーク許可がある場合)→ Wikimedia Commons。
キャプション(掲載元の説明文)で「誰が・いつ・どこで」写っているかを確認できた画像だけを台帳に載せる。
確認できない画像は ledger に載せず rejected.csv に理由を残す(第0章4)。

使い方:
  python -m pipeline.collect_images --project P001 --pages URL1 URL2 ... [--commons "Empress Masako" ...]
  --pages: 宮内庁などの写真ページ(キャプション付き)
出力: assets/<制作番号>/A001.jpg ... と projects/<制作番号>/ledger.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
import time
import urllib.parse
from pathlib import Path

import requests
from PIL import Image

from .common import ROOT

UA = {"User-Agent": "Mozilla/5.0 (internal study material; contact: none)"}
LEDGER_COLS = ["番号", "ファイル名", "取得元URL", "掲載サイト名", "取得日", "写っている人物", "撮影日・場所・行事",
               "確認したキャプション", "使用する場面", "素材種別", "長辺px"]

# キャプション中の表記 → 画面に出す人物名(宮内庁の表記に合わせた短い呼び方)
PERSONS = [
    ("天皇皇后両陛下", ["天皇陛下", "皇后陛下"]), ("両陛下", ["天皇陛下", "皇后陛下"]),
    ("天皇陛下", ["天皇陛下"]), ("皇后陛下", ["皇后陛下"]), ("皇后雅子", ["皇后陛下"]), ("Empress Masako", ["皇后陛下"]),
    ("Emperor Naruhito", ["天皇陛下"]), ("愛子内親王", ["愛子内親王殿下"]), ("Princess Aiko", ["愛子内親王殿下"]),
    ("上皇陛下", ["上皇陛下"]), ("上皇后陛下", ["上皇后陛下"]),
    ("秋篠宮皇嗣同妃両殿下", ["秋篠宮皇嗣殿下", "秋篠宮皇嗣妃殿下"]), ("皇嗣同妃両殿下", ["秋篠宮皇嗣殿下", "秋篠宮皇嗣妃殿下"]),
    ("秋篠宮皇嗣殿下", ["秋篠宮皇嗣殿下"]), ("皇嗣殿下", ["秋篠宮皇嗣殿下"]), ("皇嗣妃殿下", ["秋篠宮皇嗣妃殿下"]),
    ("佳子内親王", ["佳子内親王殿下"]), ("Princess Kako", ["佳子内親王殿下"]), ("悠仁親王", ["悠仁親王殿下"]),
    ("高円宮妃", ["高円宮妃殿下"]), ("Princess Takamado", ["高円宮妃殿下"]), ("Princess Hisako", ["高円宮妃殿下"]),
    ("承子女王", ["承子女王殿下"]), ("彬子女王", ["彬子女王殿下"]), ("瑶子女王", ["瑶子女王殿下"]),
    ("寬仁親王妃", ["寬仁親王妃殿下"]), ("常陸宮妃", ["常陸宮妃殿下"]), ("常陸宮", ["常陸宮殿下"]),
]


def persons_in(caption: str) -> list[str]:
    found, rest = [], caption
    for key, names in PERSONS:
        if key in rest:
            for n in names:
                if n not in found:
                    found.append(n)
            rest = rest.replace(key, "")
    return found


def reiwa_date(text: str) -> str:
    m = re.search(r"令和(\d+|元)年(\d+)月(\d+)日", text)
    if not m:
        return ""
    y = 2018 + (1 if m.group(1) == "元" else int(m.group(1)))
    return f"{y}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def scrape_kunaicho(url: str) -> list[dict]:
    r = requests.get(url, headers=UA, timeout=30)
    r.encoding = "utf-8"
    s = r.text
    title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1)))).strip() \
        if re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S) else ""
    date = reiwa_date(s)
    out = []
    # 写真は <section> ごとに1枚。説明文(<p>)は同じ section 内にある場合だけ採用する(無ければ空 = 特定不可)
    for sec in re.findall(r"<section[^>]*>(.*?)</section>", s, re.S):
        m = re.search(r'<img[^>]+src="([^"]*/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png))"', sec)
        if not m:
            continue
        p = re.search(r"<p[^>]*>(.*?)</p>", sec, re.S)
        cap = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p.group(1)))).strip() if p else ""
        out.append({"src": urllib.parse.urljoin(url, m.group(1)), "site": "宮内庁", "page": url,
                    "caption": cap[:160], "event": f"{date} {title}".strip()})
    return out


def commons(query: str, n=8) -> list[dict]:
    api = "https://commons.wikimedia.org/w/api.php"
    p = {"action": "query", "format": "json", "formatversion": 2, "generator": "search", "gsrnamespace": 6,
         "gsrsearch": query, "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600}
    try:
        d = requests.get(api, params=p, headers=UA, timeout=30).json()
    except Exception:
        return []
    out = []
    for pg in d.get("query", {}).get("pages", []):
        ii = (pg.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        desc = re.sub(r"<[^>]+>", "", html.unescape(md.get("ImageDescription", {}).get("value", "")))[:200]
        date = re.sub(r"<[^>]+>", "", md.get("DateTimeOriginal", {}).get("value", ""))[:20]
        if ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        out.append({"src": ii.get("thumburl") or ii.get("url"), "site": "Wikimedia Commons", "page": ii.get("descriptionurl"),
                    "caption": (pg["title"].replace("File:", "") + " / " + desc).strip(" /"), "event": date})
    return out


def collect(project: str, pages: list[str], queries: list[str], scene_hint: str = "") -> Path:
    adir = ROOT / "assets" / project
    adir.mkdir(parents=True, exist_ok=True)
    pdir = ROOT / "projects" / project
    pdir.mkdir(parents=True, exist_ok=True)
    ledger = pdir / "ledger.csv"
    rows = list(csv.DictReader(open(ledger, encoding="utf-8"))) if ledger.exists() else []
    seen = {r["取得元URL"] for r in rows}
    rejected = []
    cands = []
    for u in pages:
        if "kunaicho.go.jp" in u:
            cands += scrape_kunaicho(u)
        time.sleep(1.0)  # 短時間に大量アクセスしない
    for q in queries:
        cands += commons(q)
        time.sleep(1.5)
    for c in cands:
        if c["src"] in seen:
            continue
        who = persons_in(c["caption"])
        if not who:
            rejected.append({**c, "reason": "キャプションで人物を特定できない"})
            continue
        if not c["event"]:
            rejected.append({**c, "reason": "撮影日・行事を確認できない"})
            continue
        try:
            r = requests.get(c["src"], headers=UA, timeout=60)
            r.raise_for_status()
            im = Image.open(__import__("io").BytesIO(r.content)).convert("RGB")
        except Exception as e:
            rejected.append({**c, "reason": f"取得失敗 {e}"})
            continue
        no = f"A{len(rows) + 1:03d}"
        fn = f"{no}.jpg"
        im.save(adir / fn, quality=93)
        rows.append({"番号": no, "ファイル名": f"assets/{project}/{fn}", "取得元URL": c["src"], "掲載サイト名": c["site"],
                     "取得日": dt.date.today().isoformat(), "写っている人物": "・".join(who),
                     "撮影日・場所・行事": c["event"], "確認したキャプション": c["caption"], "使用する場面": scene_hint, "素材種別": "写真",
                     "長辺px": max(im.size)})
        seen.add(c["src"])
        time.sleep(0.8)
    with open(ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LEDGER_COLS})
    with open(pdir / "rejected.csv", "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for r in rejected:
            w.writerow([r["src"], r["site"], r["caption"][:100], r["reason"]])
    print(f"台帳 {len(rows)}件(今回+{len(rows) - len(seen) + len(seen)}) / 不採用 {len(rejected)}件 → {ledger}")
    return ledger


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--pages", nargs="*", default=[])
    ap.add_argument("--commons", nargs="*", default=[])
    ap.add_argument("--scene", default="")
    a = ap.parse_args()
    collect(a.project, a.pages, a.commons, a.scene)
