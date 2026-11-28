"""皇室系チャンネルのショート(新しい順60本+人気順30本)を公開ページから取得。CTRは非公開なので『その動画の再生数 ÷ そのチャンネルの直近ショートの中央値』(伸び倍率)で代用する。"""
import sys, json, csv, os, re, statistics, datetime
sys.path.insert(0, "/home/user/-/research/LONG-20261124/deep/scripts")
import yt
TAB = "EgZzaG9ydHPyBgUKA5oBAA=="
def parse(d):
    out = []
    for s in yt.walk(d, "shortsLockupViewModel"):
        vid = None
        for r in yt.walk(s, "reelWatchEndpoint"): vid = r.get("videoId"); break
        om = s.get("overlayMetadata", {})
        title = (om.get("primaryText") or {}).get("content", "")
        vt = (om.get("secondaryText") or {}).get("content", "")
        if not vid: continue
        if not vt:
            m = re.search(r",\s*([\d,\.万億]+)\s*回視聴", s.get("accessibilityText", "")); vt = m.group(1) + "回" if m else ""
        out.append({"id": vid, "title": title or s.get("accessibilityText", "").split(",")[0], "views": yt.num(vt), "views_text": vt})
    seen = set(); res = []
    for v in out:
        if v["id"] not in seen: seen.add(v["id"]); res.append(v)
    return res
def shorts(cid, sort, n):
    d = yt.api("browse", {"browseId": cid, "params": TAB}); meta = yt.channel_meta(d)
    if sort == "popular":
        tok = None
        for key in ("chipCloudChipRenderer", "chipViewModel"):
            for chip in yt.walk(d, key):
                t = chip.get("text"); t = yt.txt(t) if isinstance(t, dict) else t
                if t in ("人気の動画", "人気", "Popular"):
                    for x in yt.walk(chip, "token"): tok = x; break
                if tok: break
            if tok: break
        if not tok: return meta, []
        d = yt.api("browse", {"continuation": tok})
    v = parse(d)
    while len(v) < n:
        t = yt.cont_tokens(d)
        if not t: break
        d = yt.api("browse", {"continuation": t[-1]}); new = parse(d)
        if not new: break
        ids = {x["id"] for x in v}; v += [x for x in new if x["id"] not in ids]
    return meta, v[:n]
# 対象: 長尺調査の競合チャンネル + ショート中心の競合(名前で検索)
chans = {r["channel_id"]: r["channel"] for r in csv.DictReader(open("/home/user/-/research/LONG-20261124/deep/channels_summary.csv")) if r["kind"] == "競合"}
for name in ["皇室ヴェール", "皇室秘話室", "人生の心つづり", "皇室パンフレット", "雅子さまと愛子さま 皇室ファミリーの絆", "皇室の夢 海外の反応", "みんなの皇室", "それいけ皇室", "皇室秘話", "愛子さま ショート 皇室"]:
    try:
        _, cs = yt.search(name, sp="EgIQAg%3D%3D", pages=1)
        for c in cs[:2]: chans.setdefault(c["channel_id"], c["channel"])
    except Exception as e: print("search ERR", name, e)
for q in ["雅子さま #shorts", "愛子さま #shorts", "天皇陛下 #shorts", "皇室 #shorts"]:
    try:
        vids, _ = yt.search(q, pages=2)
        for v in vids:
            if v.get("channel_id") and v.get("views", 0) and v["views"] >= 300000: chans.setdefault(v["channel_id"], v["channel"])
    except Exception as e: print("search ERR", q, e)
print("channels", len(chans), flush=True)
os.makedirs("raw", exist_ok=True)
for cid, name in list(chans.items())[::-1]:
    fp = f"raw/{cid}.json"
    if os.path.exists(fp): continue
    try:
        meta, new = shorts(cid, "new", 60); pop = shorts(cid, "popular", 30)[1] if new else []
        json.dump({"name": name, "meta": meta, "new": new, "popular": pop, "fetched": datetime.datetime.now(datetime.UTC).isoformat()}, open(fp, "w"), ensure_ascii=False)
        print(name, len(new), len(pop), flush=True)
    except Exception as e: print("ERR", name, e, flush=True)
