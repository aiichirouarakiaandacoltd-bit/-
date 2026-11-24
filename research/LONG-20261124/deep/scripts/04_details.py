"""動画ごとの詳細(/next): 正確な再生数・公開日・コメント数・高評価・章・説明文・関連動画。出力: raw/details/<id>.json
対象: 各競合チャンネルの人気上位6+直近4、好意型の高再生、報道の皇室関連(検索結果より)"""
import yt, json, csv, os, sys, re
EXCL = ["一月万冊","むすび大学","古是三春","衝撃のJAPAN"]
FRIENDLY = ["日本一新","令和の光","令和の輝き","世界が見た雅子さま","皇室と共に歩む","皇室日記","皇室Labo","皇室JAPAN","皇室ヒストリー","皇室のさくらん","皇室の華","日本の雑学","人生の心つづり","皇室秘話室","菊の紋章","皇室のひだまり","皇室のお話","皇室のキセキ","皇室物語","kata62kima","宮内庁","皇室の夢","皇室〜記録館〜","雅子さまと愛子さま"]
rows = list(csv.DictReader(open("../videos_all.csv")))
ids = []
def add(i):
    if i not in ids: ids.append(i)
for r in rows:
    if any(e in r["channel"] for e in EXCL): continue
    v = int(float(r["views"] or 0)); rk = int(r["rank"])
    fr = any(f in r["channel"] for f in FRIENDLY)
    if r["kind"] == "競合":
        if (r["list"] == "popular" and rk <= (12 if fr else 6)) or (r["list"] == "new" and rk <= (6 if fr else 4)): add(r["id"])
        elif r["type"] in ("事実・好意型", "反応・感情型") and v >= 500000: add(r["id"])
    elif "宮内庁" in r["channel"] and (rk <= 12): add(r["id"])
# 報道: 検索結果のうち皇室関連で再生上位
S = json.load(open("../raw/search_results.json"))
news = {}
for v in S["videos"]:
    if any(n in (v["channel"] or "") for n in ["日テレNEWS","TBS NEWS DIG","ANNnewsCH","テレ東BIZ","FNN","THE PAGE","産経"]) and v["views"]:
        news[v["id"]] = v
for v in sorted(news.values(), key=lambda v: -v["views"])[:60]: add(v["id"])
extra = sys.argv[1:]
for e in extra: add(e)
print("targets", len(ids), flush=True)
os.makedirs("../raw/details", exist_ok=True)
for n, vid in enumerate(ids):
    fp = f"../raw/details/{vid}.json"
    if os.path.exists(fp): continue
    try:
        d = yt.api("next", {"videoId": vid})
        o = {"id": vid}
        for p in yt.walk(d, "videoPrimaryInfoRenderer"):
            o["title"] = yt.txt(p.get("title")); o["views"] = yt.num(yt.txt(p.get("viewCount", {}).get("videoViewCountRenderer", {}).get("viewCount")))
            o["date_text"] = yt.txt(p.get("dateText")); break
        for b in yt.walk(d, "likeButtonViewModel"):
            for t in yt.walk(b, "accessibilityText"):
                if "高評価" in t: o["likes_text"] = t; o["likes"] = yt.num(re.sub(r"^.*?(?=[\d.])", "", t)); break
            break
        for e in yt.walk(d, "engagementPanelSectionListRenderer"):
            if e.get("panelIdentifier") == "engagement-panel-comments-section":
                for c in yt.walk(e, "contextualInfo"): o["comments"] = yt.num(yt.txt(c))
        for ow in yt.walk(d, "videoOwnerRenderer"):
            o["channel"] = yt.txt(ow.get("title")); o["subs_text"] = yt.txt(ow.get("subscriberCountText"))
            for be in yt.walk(ow, "browseId"): o["channel_id"] = be; break
            break
        for a in yt.walk(d, "attributedDescription"): o["description"] = a.get("content", ""); break
        ch = []; seen = set()
        for m in yt.walk(d, "macroMarkersListItemRenderer"):
            t = yt.txt(m.get("timeDescription"))
            if t in seen: continue
            seen.add(t); th = ""
            for u in yt.walk(m.get("thumbnail", {}), "url"): th = u
            ch.append({"t": t, "title": yt.txt(m.get("title")), "thumb": th})
        o["chapters"] = ch
        rel = []
        for s in yt.walk(d, "secondaryResults"): rel = yt.extract_videos(s)
        o["related"] = [{"id": v["id"], "channel": v["channel"], "channel_id": v["channel_id"], "title": v["title"], "length": v["length"]} for v in rel]
        o["has_transcript_panel"] = bool(next(yt.walk(d, "getTranscriptEndpoint"), None))
        json.dump(o, open(fp, "w"), ensure_ascii=False, indent=0)
        if n % 25 == 0: print(n, vid, o.get("views"), o.get("comments"), len(ch), flush=True)
    except Exception as e:
        print("ERR", vid, e, flush=True)
print("done", flush=True)
