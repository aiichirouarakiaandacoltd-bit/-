"""速報ショートの見張り役: 宮内庁の新着を前回と比べて一覧にする(荒木承認 2026-11-27)。

見るページ(1回の実行で一覧4〜6ページ+詳細ページ最大 --max-detail 件。1件ごとに --interval 秒あける):
  - 新着情報             https://www.kunaicho.go.jp/news/index.html
  - 天皇ご一家のご日程   /watch/activity/schedule01/<YYYYMM>/index.html(当月。月初10日までは前月も)
  - 秋篠宮家のご日程     /watch/activity/schedule03/<YYYYMM>/index.html(同上)
  - 天皇ご一家のご活動   /watch/activity/imperial-family-activity-01/index.html(「ご活動」の報告ページ一覧)
新しい行事ページ・写真ページだけ詳細を開き、写真の枚数と提供者表記(「写真：警察庁」等)の有無を数える。
おことばのページは一覧に載せるだけ(本文は事実確認係が G1 で読む)。

照合: research/batches/*.yaml の「承認済」で条件付きの企画(rank や note に「条件」)について、
条件を満たしたかを判定する。機械で判定できるよう、企画に次の項目を書いておく(無ければ note から推定):
  watch: {date: '2026-11-20', keywords: [ペルー, チリ], min_photos: 5, schedule: schedule01}

出力: data/watch_report.md(人が読む報告)・data/watch_state.json(前回の状態)
終了コード: 0=新着なし / 2=新着あり / 3=条件を満たした企画あり(新着ありを含む) / 1=一覧ページを1つも取得できない

使い方:
  bin/kabu run watch                       前回との差分
  bin/kabu run watch --since 2026-11-19    指定日以降に載ったものを(前回に関係なく)新着として一覧にする
  python -m pipeline.watch_kunaicho --no-save   状態を書き換えずに試す
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import html
import re
import sys
import time
import urllib.parse

import requests

from .common import ROOT, load_json, now_jst, save_json

BASE = "https://www.kunaicho.go.jp"
UA = {"User-Agent": "Mozilla/5.0 (RoyalShortsPipeline watch; low-frequency)"}
DATA = ROOT / "data"
STATE = DATA / "watch_state.json"
REPORT = DATA / "watch_report.md"
SCHEDULES = {"schedule01": "天皇ご一家", "schedule03": "秋篠宮家"}
ACTIVITY_TOP = "/watch/activity/imperial-family-activity-01/index.html"
PHOTO_PAGE = re.compile(r"/watch/activity/(?:schedule0\d|imperial-family-activity-0\d/info|activity0\d)/")


def _txt(x: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def reiwa_date(s: str) -> str | None:
    m = re.search(r"令和(\d+|元)年(\d+)月(\d+)日", s)
    if not m:
        return None
    y = 2018 + (1 if m.group(1) == "元" else int(m.group(1)))
    return f"{y:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


class Fetcher:
    """控えめなアクセス: 1件ごとに interval 秒あけ、1回の実行の取得数に上限を設ける。"""

    def __init__(self, interval: float, limit: int):
        self.interval, self.limit, self.count, self.errors = interval, limit, 0, []
        self._last = 0.0

    def get(self, path: str) -> str | None:
        if self.count >= self.limit:
            return None
        wait = self.interval - (time.time() - self._last)
        if self._last and wait > 0:
            time.sleep(wait)
        url = urllib.parse.urljoin(BASE, path)
        self.count += 1
        try:
            r = requests.get(url, headers=UA, timeout=30)
            self._last = time.time()
            if r.status_code != 200:
                self.errors.append(f"{url} → HTTP {r.status_code}")
                return None
            r.encoding = "utf-8"
            return r.text
        except Exception as e:  # 取得失敗でも全体は止めない
            self._last = time.time()
            self.errors.append(f"{url} → {e}")
            return None


def _main(s: str) -> str:
    m = re.search(r"<main.*?</main>", s, re.S)
    return m.group(0) if m else s


def _kind(url: str) -> str:
    if "/okotoba/" in url:
        return "おことば"
    if PHOTO_PAGE.search(url):
        return "行事ページ"
    return "その他"


# ---------- 一覧ページの読み取り ----------

def parse_news(s: str) -> list[dict]:
    out = []
    for m in re.finditer(r'c-info-link-time">([^<]+)</div>\s*<div class="c-info-link-tag[^"]*">([^<]+)</div>\s*'
                         r'<a class="c-info-link" href="([^"]+)">(.*?)</a>', s, re.S):
        url = urllib.parse.urljoin(BASE, html.unescape(m.group(3)))
        out.append({"key": f"news|{url}", "src": "新着情報", "date": reiwa_date(m.group(1)),
                    "family": _txt(m.group(2)), "title": _txt(m.group(4)), "url": url, "kind": _kind(url)})
    return out


def parse_schedule(s: str, sched: str) -> list[dict]:
    """月別ご日程の表: <tbody data-date=…> ごとに、日付の小見出し行と(対象, 内容, 写真ページへのリンク)の行。"""
    out = []
    for attr, body in re.findall(r"<tbody([^>]*)>(.*?)</tbody>", _main(s), re.S):
        cur = reiwa_date(html.unescape(attr))  # 小見出し行が無い表もある。複数日の表は小見出しで上書き
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
            if "c-table__subtitle" in tr:
                cur = reiwa_date(_txt(tr)) or cur
                continue
            th = re.search(r"<th[^>]*>(.*?)</th>", tr, re.S)
            td = re.search(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if not (th and td and cur):
                continue
            who, what = _txt(th.group(1)), _txt(td.group(1))
            a = re.search(r'href="([^"]+)"', td.group(1))
            url = urllib.parse.urljoin(BASE, a.group(1)) if a else ""
            out.append({"key": f"sch|{sched}|{cur}|{who}|{what}", "src": f"ご日程({SCHEDULES[sched]})", "date": cur,
                        "family": SCHEDULES[sched], "who": who, "title": what, "url": url,
                        "kind": "行事ページ" if url else "ご日程(写真ページなし)", "sched": sched})
    return out


def parse_activity(s: str) -> list[dict]:
    """天皇ご一家のトップの「ご活動」一覧: 報告ページ(info/)と写真付きのご日程ページ。"""
    out, seen = [], set()
    for m in re.finditer(r'<a[^>]+href="(/watch/activity/(?:imperial-family-activity-01/info|schedule01)/[^"#]+\.html)"[^>]*>(.*?)</a>',
                         _main(s), re.S):
        url = BASE + m.group(1)
        if url in seen:
            continue
        seen.add(url)
        t = _txt(m.group(2))
        d = reiwa_date(t)
        ud = re.search(r"/(20\d{2})(\d{2})(\d{2})-\d+\.html$", url)
        if not d and ud:
            d = "-".join(ud.groups())
        title = re.sub(r"\s*令和[\d元]+年\d+月\d+日（.）\s*$", "", t).strip()
        out.append({"key": f"act|{url}", "src": "ご活動(天皇ご一家)", "date": d, "family": "天皇ご一家",
                    "title": title, "url": url, "kind": "行事ページ"})
    return out


# ---------- 詳細ページ: 写真の枚数と提供者表記 ----------

def count_photos(s: str, page_url: str = "") -> dict:
    main = _main(s)
    imgs = list(re.finditer(r'<img[^>]+src="([^"]+\.(?:jpe?g|png))"[^>]*>', main, re.I))
    imgs = [m for m in imgs if re.search(r"/(?:wp-content/uploads|data|activity|about)/", m.group(1)) and "/common/" not in m.group(1)]
    photos, srcs = [], set()
    for i, m in enumerate(imgs):
        src = urllib.parse.urljoin(BASE, m.group(1))
        if src in srcs:
            continue
        srcs.add(src)
        nxt = imgs[i + 1].start() if i + 1 < len(imgs) else len(main)
        win = m.group(0) + main[m.end():min(nxt, m.end() + 1200)]
        prov = re.search(r"写真[：:]\s*([^）)」<\s]+)", win)
        photos.append({"src": src, "provider": prov.group(1) if prov else ""})
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", main, re.S)
    # ご活動の報告ページ(info/26aichi2-1.html)は写真が「〜日目」の子ページ(-2, -3 …)にもある
    subs = []
    m = re.search(r"/info/([A-Za-z0-9\-]+?)-?(\d+)\.html", page_url or "")
    if m:
        stem = m.group(1)
        subs = sorted({urllib.parse.urljoin(BASE, x) for x in re.findall(rf'href="([^"#]*/info/{re.escape(stem)}-?\d+\.html)', main)}
                      - {page_url})
    return {"subpages": subs, "photos": len(photos), "no_credit": sum(1 for p in photos if not p["provider"]),
            "providers": sorted({p["provider"] for p in photos if p["provider"]}),
            "h1": _txt(h1.group(1)) if h1 else "", "srcs": [p["src"] for p in photos]}


# ---------- 条件待ちの企画 ----------

def conditional_items() -> list[dict]:
    import yaml
    out = []
    for f in sorted(glob.glob(str(ROOT / "research" / "batches" / "*.yaml"))):
        try:
            b = yaml.safe_load(open(f, encoding="utf-8"))
        except Exception as e:
            out.append({"batch": f.rsplit("/", 1)[-1], "id": "-", "error": f"読めない({str(e).splitlines()[0]})"})
            continue
        for it in (b or {}).get("items") or []:
            if it.get("status") != "承認済":
                continue
            text = " ".join(str(it.get(k) or "") for k in ("rank", "note", "publish_plan", "condition"))
            if "条件" not in text and not it.get("watch"):
                continue
            w = dict(it.get("watch") or {})
            if not w:  # note から推定: 「11/20 … 5枚以上」
                cond = text[text.find("条件"):] if "条件" in text else text
                md = re.search(r"(\d{1,2})/(\d{1,2})", cond)
                mn = re.search(r"(\d+)枚以上", cond)
                year = str(it.get("approved_at") or b.get("created") or now_jst().year)[:4]
                if md:
                    w["date"] = f"{year}-{int(md.group(1)):02d}-{int(md.group(2)):02d}"
                if mn:
                    w["min_photos"] = int(mn.group(1))
                w["guessed"] = True
            out.append({"batch": b.get("batch") or f.rsplit("/", 1)[-1][:-5], "id": it.get("id"),
                        "title": it.get("title", ""), "note": it.get("note", ""), "watch": w})
    return out


def _months(today: dt.date, extra: list[str]) -> list[str]:
    ms = [today.strftime("%Y%m")]
    if today.day <= 10:
        ms.insert(0, (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y%m"))
    for d in extra:  # 条件の日付の月も見る(2か月以内に限る)
        try:
            x = dt.date.fromisoformat(d)
        except Exception:
            continue
        if (today - x).days <= 62 and x.strftime("%Y%m") not in ms:
            ms.insert(0, x.strftime("%Y%m"))
    return ms


def run(a) -> int:
    now = now_jst()
    today = now.date()
    state = {} if a.reset else (load_json(STATE) or {})
    seen: dict = state.get("seen", {})
    pages: dict = state.get("pages", {})
    first_run = not seen
    conds = conditional_items()
    f = Fetcher(a.interval, a.max_index + a.max_detail)

    # 1) 一覧ページ
    items, fetched = [], []
    s = f.get("/news/index.html")
    if s:
        news = parse_news(s)
        items += news[:a.news_limit]
        fetched.append(f"新着情報 {len(news)}件(新しい {a.news_limit}件を比較)")
    for ym in _months(today, [c["watch"].get("date", "") for c in conds if "watch" in c]):
        for sched in SCHEDULES:
            s = f.get(f"/watch/activity/{sched}/{ym}/index.html")
            if s:
                rows = parse_schedule(s, sched)
                items += rows
                last = max((r["date"] for r in rows), default="なし")
                fetched.append(f"ご日程 {SCHEDULES[sched]} {ym}: {len(rows)}行・最終掲載日 {last}")
    s = f.get(ACTIVITY_TOP)
    if s:
        act = parse_activity(s)
        items += act
        fetched.append(f"天皇ご一家のご活動 {len(act)}件")
    if not fetched:
        print("宮内庁のページを1つも取得できませんでした:\n  " + "\n  ".join(f.errors))
        return 1

    # 2) 差分(新着) : 初めての項目、またはご日程の行に写真ページのリンクが付いた項目
    new = []
    for it in items:
        old = seen.get(it["key"])
        if a.since:
            is_new = bool(it["date"] and it["date"] >= a.since)
        elif first_run:
            is_new = bool(it["date"] and (today - dt.date.fromisoformat(it["date"])).days <= 14)
        else:
            is_new = old is None or (it["url"] and not old.get("url"))
        if is_new:
            if old and it["url"] and not old.get("url"):
                it["kind"] += "(写真ページ追加)"
            new.append(it)
    # 同じページが新着情報・ご日程・ご活動の複数に出たら1行にまとめる(行事ページの URL で)
    merged, by_url = [], {}
    for it in new:
        u = it["url"].split("#")[0]
        if u and u in by_url and it["kind"] != "おことば":
            by_url[u]["also"].append(it["src"])
            continue
        it["also"] = []
        merged.append(it)
        if u:
            by_url[u] = it

    # 3) 詳細: 新しい行事ページ+条件に関わるページの写真を数える(既に数えたページは数え直さない。条件のページは毎回)
    def cond_hits(c):
        w = c["watch"]
        return [it for it in items if it["url"] and it["date"] == w.get("date")
                and (not w.get("keywords") or any(k in it["title"] for k in w["keywords"]))
                and (not w.get("schedule") or it.get("sched") in (None, w["schedule"]))]

    want = []
    for c in conds:
        if "watch" in c:
            want += [it["url"].split("#")[0] for it in cond_hits(c)]
    want += [it["url"].split("#")[0] for it in merged if it["url"] and it["kind"].startswith("行事ページ")
             and it["url"].split("#")[0] not in pages]
    want = list(dict.fromkeys(want))
    skipped = []
    for u in want:
        if f.count >= f.limit:
            skipped.append(u)
            continue
        s = f.get(u)
        if not s:
            continue
        info = count_photos(s, u)
        for sub in info.pop("subpages")[:a.max_sub]:  # 報告ページの子ページの写真も合算する
            if f.count >= f.limit:
                info["note"] = "子ページの一部は上限のため未計数"
                break
            ss = f.get(sub)
            if ss:
                si = count_photos(ss, sub)
                new_srcs = [x for x in si["srcs"] if x not in info["srcs"]]
                info["srcs"] += new_srcs
                info["photos"] += len(new_srcs)
                info["no_credit"] += min(si["no_credit"], len(new_srcs))
                info["providers"] = sorted(set(info["providers"]) | set(si["providers"]))
                info.setdefault("pages_counted", [u]).append(sub)
        info["checked_at"] = now.isoformat(timespec="seconds")
        pages[u] = info

    # 4) 条件の判定
    cond_res = []
    for c in conds:
        if "error" in c:
            continue
        w = c["watch"]
        if not w.get("date") or not w.get("min_photos"):
            cond_res.append({**c, "met": None, "why": "条件を機械で読めない(企画に watch: {date, keywords, min_photos} を書く)"})
            continue
        hits = list({it["url"].split("#")[0]: it for it in cond_hits(c)}.values())
        total = sum(pages.get(it["url"].split("#")[0], {}).get("photos", 0) for it in hits)
        usable = sum(pages.get(it["url"].split("#")[0], {}).get("no_credit", 0) for it in hits)
        rows_any = [it for it in items if it["date"] == w["date"] and (not w.get("keywords") or any(k in it["title"] for k in w["keywords"]))]
        met = total >= w["min_photos"]
        if hits:
            why = f"{w['date']} の該当ページ {len(hits)}件・写真 {total}枚(提供者表記なし {usable}枚)/必要 {w['min_photos']}枚"
        elif rows_any:
            why = f"{w['date']} のご日程に行は載ったが写真ページなし(写真 0枚/必要 {w['min_photos']}枚)"
        else:
            why = f"{w['date']} の該当行事はまだ宮内庁に未掲載(写真 0枚/必要 {w['min_photos']}枚)"
        cond_res.append({**c, "met": met, "why": why, "hits": hits, "total": total, "usable": usable})

    # 5) 報告
    write_report(now, a, merged, pages, fetched, f, cond_res, skipped, first_run)
    if not a.no_save:
        for it in items:
            seen.setdefault(it["key"], {"first_seen": now.isoformat(timespec="seconds")})
            seen[it["key"]].update({"url": it["url"] or seen[it["key"]].get("url", ""), "date": it["date"]})
        save_json(STATE, {"updated_at": now.isoformat(timespec="seconds"), "seen": seen, "pages": pages,
                          "last_new": [m["key"] for m in merged]})
    met_any = any(c.get("met") for c in cond_res)
    print(f"新着 {len(merged)}件 / 条件を満たした企画 {sum(1 for c in cond_res if c.get('met'))}件 → {REPORT.relative_to(ROOT)}")
    return 3 if met_any else (2 if merged else 0)


def _ph(info: dict | None) -> tuple[str, str, str]:
    if not info:
        return "未確認", "", ""
    prov = "・".join(info["providers"]) if info["providers"] else "なし"
    return str(info["photos"]), str(info["no_credit"]), prov


def write_report(now, a, merged, pages, fetched, f, cond_res, skipped, first_run):
    L = [f"# 宮内庁 見張り報告({now.strftime('%Y-%m-%d %H:%M')} JST)", ""]
    if a.since:
        L.append(f"- 比べ方: {a.since} 以降の日付のものを新着として一覧(前回の状態に関係なく)")
    elif first_run:
        L.append("- 比べ方: 初回(前回の状態なし)。直近14日以内の日付のものを一覧")
    else:
        L.append("- 比べ方: 前回の data/watch_state.json との差分")
    L.append(f"- 取得: {f.count}ページ(間隔 {a.interval:.0f}秒)。" + " / ".join(fetched))
    if f.errors:
        L.append("- 取得できなかったページ: " + " / ".join(f.errors))
    if skipped:
        L.append(f"- 上限のため詳細を開かなかったページ {len(skipped)}件(次回に開く): " + " ".join(skipped))
    L += ["", "日付は、新着情報=宮内庁の掲載日、ご日程・ご活動=行事の日。写真の数は詳細ページの実測。"
          "「表記なし」=「写真：〇〇」の提供者表記が付いていない写真(第3章の素材の候補)。", ""]

    L += [f"## 1. 新着 {len(merged)}件", ""]
    groups = [("行事ページ(写真)", lambda k: k.startswith("行事ページ")), ("おことば", lambda k: k == "おことば"),
              ("ご日程(写真ページなし)", lambda k: k.startswith("ご日程")), ("その他", lambda k: k == "その他")]
    for name, pred in groups:
        rows = sorted([m for m in merged if pred(m["kind"])], key=lambda m: (m["date"] or "", m["title"]), reverse=True)
        if not rows:
            continue
        L += [f"### {name} {len(rows)}件", ""]
        if name.startswith("行事ページ"):
            L += ["| 日付 | 宮家 | 題名 | 写真 | 表記なし | 提供者表記 | 載った所 | URL |", "|---|---|---|---|---|---|---|---|"]
            for m in rows:
                n, nc, pv = _ph(pages.get(m["url"].split("#")[0]))
                src = "・".join([m["src"], *m["also"]])
                L.append(f"| {m['date']} | {m['family']} | {m['title']}{'(' + m['who'] + ')' if m.get('who') else ''} | {n} | {nc} | {pv} | {src} | {m['url']} |")
        elif name == "おことば":
            L += ["| 掲載日 | 宮家 | 題名 | URL |", "|---|---|---|---|"]
            L += [f"| {m['date']} | {m['family']} | {m['title']} | {m['url']} |" for m in rows]
        else:
            L += ["| 日付 | 宮家 | 対象 | 内容 |", "|---|---|---|---|"]
            L += [f"| {m['date']} | {m['family']} | {m.get('who', '')} | {m['title']} |" for m in rows]
        L.append("")
    if not merged:
        L += ["(新着なし)", ""]

    L += ["## 2. 条件待ちの企画(承認済・条件付き)", ""]
    if not cond_res:
        L += ["(該当なし)", ""]
    else:
        L += ["| 企画 | 条件 | 判定 | 根拠 |", "|---|---|---|---|"]
        for c in cond_res:
            w = c.get("watch", {})
            cond = (f"{w.get('date', '?')} {'・'.join(w.get('keywords', [])) or '(行事名の指定なし)'} の写真 {w.get('min_photos', '?')}枚以上"
                    + ("(note から推定)" if w.get("guessed") else "")) if w else "-"
            mark = {True: "**満たした → 着手**", False: "まだ", None: "判定できない"}[c.get("met")]
            L.append(f"| {c['batch']}:{c['id']} | {cond} | {mark} | {c['why']} |")
        L.append("")
        for c in cond_res:
            for it in c.get("hits", []):
                n, nc, pv = _ph(pages.get(it["url"].split("#")[0]))
                L.append(f"- {c['batch']}:{c['id']} の該当ページ: {it['date']} {it['title']} — 写真 {n}枚・表記なし {nc}枚・提供者 {pv} — {it['url']}")
            if c.get("met"):
                L.append(f"- 次の一手: G0 は承認済み。`bin/kabu new --from-batch {c['batch']}:{c['id']}` で案件を作り、"
                         "templates/sokuhou_short.md の工程で G1 から進める")
        L.append("")

    bad = [c for c in conditional_items() if "error" in c]
    if bad:
        L += ["- 読めなかった企画ファイル(YAML の書き方の誤り。条件の照合から外した): " + " / ".join(f"{c['batch']} {c['error']}" for c in bad), ""]
    L += ["## 3. 速報にするか(G0 の判断材料)", "",
          "- 写真が5枚以上・提供者表記なし・主役の方の寄りがある行事ページ、またはおことばの全文が載ったものが速報の候補。",
          "- 候補にする時は templates/sokuhou_short.md の「G0 で荒木さんに出すもの」を作り、承認を1回だけもらう(第2章)。",
          "- 報道だけで宮内庁に載っていない出来事は、速報の題材にしない(事実は宮内庁原文だけ)。", ""]
    DATA.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="宮内庁の新着を前回と比べる(速報ショートの見張り)")
    ap.add_argument("--since", help="この日付(YYYY-MM-DD)以降のものを新着として一覧にする")
    ap.add_argument("--reset", action="store_true", help="前回の状態を使わない")
    ap.add_argument("--no-save", action="store_true", help="状態(data/watch_state.json)を書き換えない")
    ap.add_argument("--interval", type=float, default=3.0, help="アクセスの間隔(秒)")
    ap.add_argument("--max-index", type=int, default=8, help="一覧ページの上限")
    ap.add_argument("--max-detail", type=int, default=10, help="詳細ページ(写真を数える)の上限")
    ap.add_argument("--max-sub", type=int, default=3, help="報告ページ1件あたりに開く子ページの上限")
    ap.add_argument("--news-limit", type=int, default=40, help="新着情報の先頭から比べる件数")
    a = ap.parse_args(argv)
    sys.exit(run(a))


if __name__ == "__main__":
    main()
