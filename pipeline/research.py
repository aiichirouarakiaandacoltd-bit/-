"""ステージ1: ニュース候補の自動収集とスコアリング。

情報源:
  - 宮内庁「新着情報」(一次情報: 日付・宮家・行事名・URL)
  - Google ニュース RSS(報道: 見出し・媒体名・公開日)
LLMは使わない(決定的な処理)。事実確認と台本化は script_writer ステージで行う。

出力: research/<job>/candidates.json
"""
from __future__ import annotations

import datetime as dt
import html
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime

import requests

from .common import JST, ROOT, Job, get_logger, load_json, now_jst, save_json, settings

UA = {"User-Agent": "Mozilla/5.0 (RoyalShortsPipeline research)"}
ERA_REIWA = 2018  # 令和N年 = 2018 + N


def _reiwa_date(s: str) -> str | None:
    m = re.search(r"令和(\d+|元)年(\d+)月(\d+)日", s)
    if not m:
        return None
    y = 1 if m.group(1) == "元" else int(m.group(1))
    return f"{ERA_REIWA + y:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def fetch_kunaicho_news(log) -> list[dict]:
    src = load_json(ROOT / "config" / "sources.json")["kunaicho"]
    url = src["base"] + "/news/"
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        r.encoding = "utf-8"
    except Exception as e:  # 取得失敗でも全体は止めない
        log.warning(f"宮内庁新着情報の取得失敗: {e}")
        return []
    items = []
    for m in re.finditer(
        r'c-info-link-time">([^<]+)</div>\s*<div class="c-info-link-tag[^"]*">([^<]+)</div>\s*<a class="c-info-link" href="([^"]+)">([^<]+)</a>',
        r.text,
    ):
        date = _reiwa_date(m.group(1))
        items.append({
            "source_type": "primary",
            "source": "宮内庁",
            "family": html.unescape(m.group(2)).strip(),
            "title": html.unescape(m.group(4)).strip(),
            "url": urllib.parse.urljoin(src["base"], m.group(3)),
            "published": date,
            "event_date": date,  # 宮内庁の新着は原則として行事日の掲載
        })
    log.info(f"宮内庁 新着情報: {len(items)}件")
    return items


def fetch_google_news(query: str, days: int, log) -> list[dict]:
    q = urllib.parse.quote(f"{query} when:{days}d")
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    root = None
    for attempt in range(3):
        try:
            time.sleep(1.5 + attempt * 4)
            r = requests.get(url, headers=UA, timeout=20)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            break
        except Exception as e:
            log.warning(f"Google News RSS 失敗({query}) 試行{attempt + 1}: {e}")
    if root is None:
        return []
    out = []
    for it in root.iter("item"):
        title = it.findtext("title") or ""
        source = it.findtext("source") or ""
        # 見出し末尾の " - 媒体名" を除去
        clean = re.sub(r"\s+-\s+[^-]+$", "", title).strip()
        pub = it.findtext("pubDate")
        try:
            pub_iso = parsedate_to_datetime(pub).astimezone(JST).date().isoformat()
        except Exception:
            pub_iso = None
        out.append({
            "source_type": "report",
            "source": source,
            "title": clean,
            "raw_title": title,
            "url": it.findtext("link"),
            "published": pub_iso,
            "event_date": None,  # 報道の公開日と出来事の発生日は区別する(script段階で確認)
            "query": query,
        })
    return out


def _tier(source: str, title: str, cfg: dict) -> str:
    text = f"{source} {title}"
    if source == "宮内庁":
        return "primary"
    for k in cfg["tiers"]["weekly"]:
        if k in text:
            return "weekly"
    for k in cfg["tiers"]["trusted"]:
        if k in source or k in title[-20:]:
            return "trusted"
    if "Yahoo" in source:
        return "unknown_aggregator"
    return "unknown"


def _persons(title: str, cfg: dict) -> list[str]:
    return [p for p, kws in cfg["persons"].items() if any(k in title for k in kws)]


def _norm(t: str) -> str:
    t = re.sub(r"[（(《【〈「『].*?[）)》】〉」』]", "", t)
    return re.sub(r"[\s、。・!！?？…\-|｜]", "", t)


_GENERIC = set("天皇ご一家秋篠宮家両陛下皇后陛下")


def _tokens(t: str) -> set[str]:
    """一次情報と報道見出しの照合用: 漢字・カナ・かなの2文字組(一般語は除外)。"""
    t = re.sub(r"[^\u3040-\u30ff\u4e00-\u9fffー]", " ", t)
    grams = {t[i:i + 2] for i in range(len(t) - 1) if " " not in t[i:i + 2]}
    return {g for g in grams if not (g[0] in _GENERIC and g[1] in _GENERIC) and not re.fullmatch(r"[\u3040-\u309f]{2}", g)}


def cluster(items: list[dict]) -> list[list[dict]]:
    clusters: list[list[dict]] = []
    # 報道を先にクラスタ化し、宮内庁一次情報は語彙の一致+日付の近さで紐付ける
    prim = [i for i in items if i["source_type"] == "primary"]
    items = [i for i in items if i["source_type"] != "primary"]
    for it in items:
        n = _norm(it["title"])
        tk = _tokens(it["title"])
        for c in clusters:
            if (SequenceMatcher(None, n, _norm(c[0]["title"])).ratio() > 0.45
                    or len(tk & _tokens(c[0]["title"])) >= 6):
                c.append(it)
                break
        else:
            clusters.append([it])
    for p in prim:
        pt = _tokens(p["title"])
        best = None
        for c in clusters:
            if any(i["source_type"] == "primary" for i in c):
                continue
            ct = set().union(*(_tokens(i["title"]) for i in c))
            near = any(i.get("published") and p["published"] and
                       abs((dt.date.fromisoformat(i["published"]) - dt.date.fromisoformat(p["published"])).days) <= 4 for i in c)
            ov = len(pt & ct)
            if near and ov >= 3 and (best is None or ov > best[0]):
                best = (ov, c)
        if best:
            best[1].insert(0, p)
        else:
            clusters.append([p])
    return clusters


def score_cluster(c: list[dict], cfg: dict, topic: str | None) -> dict:
    tiers = [i["tier"] for i in c]
    trusted = len({i["source"] for i in c if i["tier"] in ("trusted", "primary")})
    titles = " ".join(i["title"] for i in c)
    has_quote = bool(re.search(r"「[^」]{2,30}」", titles))
    dates = [i["published"] for i in c if i.get("published")]
    newest = max(dates) if dates else None
    age = (now_jst().date() - dt.date.fromisoformat(newest)).days if newest else 30
    neg = sum(1 for k in cfg["exclude_title_keywords"] if k in titles)
    s = 0.0
    s += 3.0 * ("primary" in tiers)
    s += 1.5 * min(trusted, 4)
    s += 1.5 * has_quote  # 印象的な発言
    s += 1.0 * bool(re.search(r"体験|ご覧|ご訪問|交流|笑顔|初めて|お見舞い|おことば|記者会見", titles))
    s -= 0.15 * age
    s -= 2.5 * neg  # 憶測・批判系は優先度を下げる
    s -= 2.0 * (trusted == 0)  # 信頼できる報道・一次情報が無い題材は避ける
    if topic:
        tk = [w for w in re.split(r"[\sの、]+", topic) if len(w) >= 2 and w not in ("最新ニュース", "ニュース", "最新")]
        hit = sum(1 for w in tk if w in titles)
        s += 2.0 * hit
    rep = sorted(c, key=lambda i: {"primary": 0, "trusted": 1, "unknown": 2, "unknown_aggregator": 3, "weekly": 4}[i["tier"]])[0]
    return {
        "headline": rep["title"],
        "score": round(s, 2),
        "persons": sorted({p for i in c for p in i["persons"]}),
        "newest_published": newest,
        "trusted_source_count": trusted,
        "has_primary": "primary" in tiers,
        "has_quote_in_headlines": has_quote,
        "negative_keyword_hits": neg,
        "items": c,
    }


def run_research(job: Job, topic: str | None = None, days: int | None = None) -> dict:
    log = get_logger(job)
    cfg = load_json(ROOT / "config" / "sources.json")
    st = settings()["research"]
    days = days or st["lookback_days"]
    since = (now_jst().date() - dt.timedelta(days=days)).isoformat()

    items = [i for i in fetch_kunaicho_news(log) if (i["published"] or "") >= since]
    queries = list(cfg["rss_queries"])
    if topic:
        queries = [topic] + queries[:3]
    seen = set()
    for q in queries:
        for i in fetch_google_news(q, days, log):
            if i["title"] in seen:
                continue
            seen.add(i["title"])
            items.append(i)
    for i in items:
        i["tier"] = _tier(i["source"], i.get("raw_title", i["title"]), cfg)
        i["persons"] = _persons(i["title"], cfg)
    items = [i for i in items if i["persons"] or i["source"] == "宮内庁"]
    clusters = [score_cluster(c, cfg, topic) for c in cluster(items)]
    clusters.sort(key=lambda c: c["score"], reverse=True)
    clusters = clusters[: st["max_candidates"]]
    out = {
        "job_id": job.id,
        "topic": topic,
        "collected_at": now_jst().isoformat(timespec="seconds"),
        "lookback_days": days,
        "notes": [
            "published=報道の公開日(または宮内庁掲載日)。event_date=出来事の発生日。報道の event_date は script 段階で確認する。",
            "tier: primary=宮内庁(一次情報) / trusted=大手報道 / weekly=週刊誌系(事実の根拠にしない) / unknown=要確認",
        ],
        "candidates": clusters,
    }
    save_json(job.candidates, out)
    log.info(f"候補 {len(clusters)}件 → {job.candidates}")
    for c in clusters[:8]:
        log.info(f"  [{c['score']:>5}] {c['headline'][:60]} ({c['trusted_source_count']}社, primary={c['has_primary']})")
    job.mark("research", True, candidates=len(clusters))
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--topic")
    ap.add_argument("--days", type=int)
    a = ap.parse_args()
    run_research(Job(a.job), a.topic, a.days)
