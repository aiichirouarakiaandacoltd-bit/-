"""YouTube 公開ページ/innertube から競合調査用のメタデータを取得する小さなライブラリ。
動画本体は取得しない(メタデータ・字幕・サムネのみ)。アクセス間隔を空ける。"""
import json, re, time, os, random, requests
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
CTX = {"client": {"clientName": "WEB", "clientVersion": "2.20261123.00.00", "hl": "ja", "gl": "JP"}}
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ja,en;q=0.5"})
S.cookies.set("CONSENT", "YES+1", domain=".youtube.com")
DELAY = float(os.environ.get("YT_DELAY", "1.2"))
_last = [0.0]
def _wait():
    d = DELAY + random.random() * 0.6 - (time.time() - _last[0])
    if d > 0: time.sleep(d)
    _last[0] = time.time()
def api(endpoint, body, tries=3):
    b = {"context": CTX}; b.update(body)
    for i in range(tries):
        _wait()
        try:
            r = S.post(f"https://www.youtube.com/youtubei/v1/{endpoint}?key={KEY}&prettyPrint=false", json=b, timeout=40)
            if r.status_code == 200: return r.json()
            err = f"HTTP {r.status_code}"
        except Exception as e:
            err = repr(e)
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{endpoint} failed: {err}")
def get(url, tries=3):
    for i in range(tries):
        _wait()
        try:
            r = S.get(url, timeout=40)
            if r.status_code == 200: return r
            err = f"HTTP {r.status_code}"
        except Exception as e:
            err = repr(e)
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url} failed: {err}")
def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key: yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o: yield from walk(v, key)
def txt(o):
    if not o: return ""
    if isinstance(o, str): return o
    if "simpleText" in o: return o["simpleText"]
    if "content" in o and isinstance(o["content"], str): return o["content"]
    return "".join(r.get("text", "") for r in o.get("runs", []))
def num(s):
    """'1,234回視聴' '1.2万 回視聴' '登録者数 3.4万人' -> int"""
    if not s: return None
    s = s.replace(",", "")
    m = re.search(r"([\d.]+)\s*(億|万)?", s)
    if not m: return None
    v = float(m.group(1)); u = m.group(2)
    if u == "万": v *= 1e4
    if u == "億": v *= 1e8
    return int(v)
def dur(s):
    if not s: return None
    p = [int(x) for x in re.findall(r"\d+", s)]
    if not p: return None
    v = 0
    for x in p: v = v * 60 + x
    return v
def parse_video_renderer(v):
    """videoRenderer / gridVideoRenderer"""
    ch = txt(v.get("ownerText") or v.get("longBylineText") or v.get("shortBylineText"))
    chid = None
    for be in walk(v.get("ownerText") or v.get("longBylineText") or {}, "browseId"):
        chid = be; break
    return {"id": v.get("videoId"), "title": txt(v.get("title")), "channel": ch, "channel_id": chid,
            "views": num(txt(v.get("viewCountText"))), "views_text": txt(v.get("viewCountText")),
            "length": dur(txt(v.get("lengthText"))), "length_text": txt(v.get("lengthText")),
            "published": txt(v.get("publishedTimeText"))}
def parse_lockup(l):
    """lockupViewModel (new channel grid / related)"""
    if l.get("contentType") not in (None, "LOCKUP_CONTENT_TYPE_VIDEO"): return None
    vid = l.get("contentId")
    md = l.get("metadata", {}).get("lockupMetadataViewModel", {})
    title = txt(md.get("title"))
    parts = []
    for row in walk(md, "metadataParts"):
        for p in row: parts.append(txt(p.get("text")))
    length = None
    for b in walk(l.get("contentImage", {}), "thumbnailBadgeViewModel"):
        t = b.get("text", "")
        if re.match(r"^\d+(:\d+)+$", t): length = t
    views = next((p for p in parts if "視聴" in p or "views" in p), "")
    pub = next((p for p in parts if "前" in p or "ago" in p), "")
    ch = next((p for p in parts if p and p not in (views, pub)), "")
    chid = None
    for be in walk(md, "browseId"):
        if str(be).startswith("UC"): chid = be; break
    return {"id": vid, "title": title, "channel": ch, "channel_id": chid, "views": num(views), "views_text": views,
            "length": dur(length), "length_text": length or "", "published": pub}
def extract_videos(data):
    out = []
    for v in walk(data, "videoRenderer"): out.append(parse_video_renderer(v))
    for v in walk(data, "gridVideoRenderer"): out.append(parse_video_renderer(v))
    for v in walk(data, "lockupViewModel"):
        p = parse_lockup(v)
        if p: out.append(p)
    seen = set(); res = []
    for v in out:
        if v["id"] and v["id"] not in seen:
            seen.add(v["id"]); res.append(v)
    return res
def cont_tokens(data):
    toks = []
    for c in walk(data, "continuationItemRenderer"):
        for t in walk(c, "token"): toks.append(t)
    return toks
def search(q, sp=None, pages=2):
    body = {"query": q}
    if sp: body["params"] = sp
    d = api("search", body); vids = extract_videos(d); chans = []
    for c in walk(d, "channelRenderer"):
        chans.append({"channel_id": c.get("channelId"), "channel": txt(c.get("title")), "subs_text": txt(c.get("videoCountText")) or txt(c.get("subscriberCountText"))})
    for _ in range(pages - 1):
        t = cont_tokens(d)
        if not t: break
        d = api("search", {"continuation": t[0]}); vids += extract_videos(d)
    return vids, chans
VIDEOS_TAB = "EgZ2aWRlb3PyBgQKAjoA"
def channel_videos(cid, sort="new", max_n=60):
    """sort: new / popular。長尺(動画タブ)のみ。"""
    d = api("browse", {"browseId": cid, "params": VIDEOS_TAB})
    meta = channel_meta(d)
    if sort == "popular":
        tok = None
        for chip in walk(d, "chipCloudChipRenderer"):
            if txt(chip.get("text")) in ("人気の動画", "Popular"):
                for t in walk(chip, "token"): tok = t; break
        if not tok:
            for chip in walk(d, "chipViewModel"):
                if chip.get("text") in ("人気の動画", "Popular"):
                    for t in walk(chip, "token"): tok = t; break
        if not tok:
            for it in walk(d, "listItemViewModel"):
                if txt(it.get("title")) in ("人気の動画", "Popular"):
                    for t in walk(it, "token"): tok = t; break
        if not tok: return meta, []
        d = api("browse", {"continuation": tok})
    vids = extract_videos(d)
    while len(vids) < max_n:
        t = cont_tokens(d)
        if not t: break
        d = api("browse", {"continuation": t[-1]})
        new = extract_videos(d)
        if not new: break
        ids = {v["id"] for v in vids}
        vids += [v for v in new if v["id"] not in ids]
    return meta, vids[:max_n]
def channel_meta(d):
    m = {}
    for x in walk(d, "channelMetadataRenderer"):
        m.update({"channel": x.get("title"), "channel_id": x.get("externalId"), "desc": x.get("description", "")[:600], "url": x.get("vanityChannelUrl")}); break
    texts = []
    for row in walk(d.get("header", {}), "metadataParts"):
        for p in row: texts.append(txt(p.get("text")))
    m["header_parts"] = texts
    for t in texts:
        if "登録者" in t: m["subs"] = num(t)
        if "本の動画" in t: m["video_count"] = num(t)
    return m
def channel_about(cid):
    d = api("browse", {"browseId": cid, "params": "EgVhYm91dPIGBAoCEgA%3D"})
    out = {}
    for a in walk(d, "aboutChannelViewModel"):
        out = {"joined": txt(a.get("joinedDateText")), "total_views": num(a.get("viewCountText", "")), "subs_text": a.get("subscriberCountText"),
               "video_count_text": a.get("videoCountText"), "country": a.get("country"), "about": (a.get("description") or "")[:800]}
        break
    return out
def player(vid):
    """動画ページHTMLから ytInitialPlayerResponse / ytInitialData"""
    r = get(f"https://www.youtube.com/watch?v={vid}&hl=ja&gl=JP")
    h = r.text
    def grab(name):
        m = re.search(name + r"\s*=\s*(\{.+?\});\s*(?:var |</script>)", h, re.S)
        if not m: return {}
        try: return json.loads(m.group(1))
        except Exception: return {}
    return grab("ytInitialPlayerResponse"), grab("ytInitialData")
def video_detail(vid):
    pr, d = player(vid)
    vd = pr.get("videoDetails", {}); mf = pr.get("microformat", {}).get("playerMicroformatRenderer", {})
    out = {"id": vid, "title": vd.get("title"), "channel": vd.get("author"), "channel_id": vd.get("channelId"),
           "length": int(vd.get("lengthSeconds", 0) or 0), "views": int(vd.get("viewCount", 0) or 0),
           "publish_date": mf.get("publishDate"), "upload_date": mf.get("uploadDate"), "category": mf.get("category"),
           "description": vd.get("shortDescription", ""), "keywords": vd.get("keywords", []),
           "is_live": vd.get("isLiveContent"), "family_safe": mf.get("isFamilySafe")}
    # likes / comments
    for b in walk(d, "likeButtonViewModel"):
        for t in walk(b, "accessibilityText"):
            if "高評価" in t or "like" in t.lower():
                out["likes"] = num(t); break
        break
    for e in walk(d, "engagementPanelSectionListRenderer"):
        if e.get("panelIdentifier") in ("engagement-panel-comments-section", "comment-item-section"):
            for c in walk(e, "contextualInfo"): out["comments"] = num(txt(c)); out["comments_text"] = txt(c)
    if "comments" not in out:
        for c in walk(d, "commentCount"): out["comments"] = num(txt(c)); break
    # chapters
    ch = []
    for m in walk(d, "macroMarkersListItemRenderer"):
        ch.append({"t": txt(m.get("timeDescription")), "title": txt(m.get("title"))})
    seen = set(); out["chapters"] = [c for c in ch if not (c["t"] in seen or seen.add(c["t"]))]
    # owner subs
    for o in walk(d, "videoOwnerRenderer"):
        out["subs_text"] = txt(o.get("subscriberCountText")); out["subs"] = num(out["subs_text"]); break
    # related channels
    rel = []
    for sec in walk(d, "secondaryResults"):
        rel = extract_videos(sec)
    out["related"] = [{"id": v["id"], "channel": v["channel"], "title": v["title"], "views": v["views"], "length": v["length"]} for v in rel]
    # captions
    tracks = pr.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    out["caption_tracks"] = [{"lang": t.get("languageCode"), "kind": t.get("kind", ""), "url": t.get("baseUrl")} for t in tracks]
    # transcript params
    for p in walk(d, "getTranscriptEndpoint"):
        out["transcript_params"] = p.get("params"); break
    return out
def transcript(detail):
    """[(start_sec, text)]。get_transcript → captionTracks(json3) の順に試す"""
    p = detail.get("transcript_params")
    if p:
        try:
            d = api("get_transcript", {"params": p}, tries=1)
            segs = []
            for s in walk(d, "transcriptSegmentRenderer"):
                segs.append((int(s.get("startMs", 0)) / 1000, txt(s.get("snippet"))))
            if segs: return segs
        except Exception: pass
    for t in detail.get("caption_tracks", []):
        if t["lang"].startswith("ja"):
            try:
                r = get(t["url"] + "&fmt=json3", tries=1)
                j = r.json(); segs = []
                for e in j.get("events", []):
                    s = "".join(x.get("utf8", "") for x in e.get("segs", []) or []).strip()
                    if s: segs.append((e.get("tStartMs", 0) / 1000, s))
                if segs: return segs
            except Exception: pass
    return []
def thumb(vid, path):
    for q in ("maxresdefault", "hqdefault"):
        try:
            _wait()
            r = S.get(f"https://i.ytimg.com/vi/{vid}/{q}.jpg", timeout=30)
            if r.status_code == 200 and len(r.content) > 3000:
                open(path, "wb").write(r.content); return q
        except Exception: pass
    return None
