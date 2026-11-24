"""対象チャンネルごとに 概要(開設日・総再生) + 長尺 人気順30 + 新しい順30 を取得。出力: raw/channels/<id>.json"""
import yt, json, csv, os, sys, datetime
S = json.load(open("../raw/search_results.json"))
ids = {}
known_pick = {}
for k, lst in S["channel_search"].items():
    if lst: ids[lst[0]["channel_id"]] = ("known", lst[0]["channel"])
extra_known = {"皇室物語":"UCwhzwAIL6cvirjaGFU0ywQw"}
rows = list(csv.DictReader(open("../raw/channels_found.csv")))
SKIP = ["THE PAGE","ニコニコ","boardnews","産経","ABEMA","竹田","LATINHA","khunkdkgun","スポーツの感動","今日ヤバい話","日本ドラマ","TAROT","国会ブーメラン","水面ニュース","刺さらない","MrFuji","Kakarot","saitou","109ちゃんねる","維新","大学金剛","Uinkd","チャンネルくらら","モコモコ","狐の夜語り","厳選","今日の日本","世界が語る日本","皇室の瞬間","皇室禁書","皇室の余韻","皇室のきずな","すばらしき皇室"]
for r in rows:
    if int(r["hits"]) >= 7 or (int(r["hits"]) >= 4 and int(r["max_views"]) >= 300000):
        if any(s in r["channel"] for s in SKIP): continue
        ids.setdefault(r["channel_id"], ("found", r["channel"]))
print(len(ids))
os.makedirs("../raw/channels", exist_ok=True)
for cid, (src, name) in ids.items():
    fp = f"../raw/channels/{cid}.json"
    if os.path.exists(fp): continue
    try:
        meta, pop = yt.channel_videos(cid, "popular", 30)
        _, new = yt.channel_videos(cid, "new", 30)
        about = {}
        d = yt.api("browse", {"browseId": cid})
        for t in [e.get("token") for e in yt.walk(d, "continuationCommand")][:4]:
            try: x = yt.api("browse", {"continuation": t}, tries=1)
            except Exception: continue
            a = next(yt.walk(x, "aboutChannelViewModel"), None)
            if a:
                about = {"joined": yt.txt(a.get("joinedDateText")), "total_views": yt.num(a.get("viewCountText") or ""), "video_count": yt.num(a.get("videoCountText") or ""), "country": a.get("country")}
                break
        json.dump({"fetched": datetime.datetime.now(datetime.UTC).isoformat(), "source": src, "meta": meta, "about": about, "popular": pop, "new": new}, open(fp, "w"), ensure_ascii=False, indent=0)
        print(name, meta.get("subs"), about.get("joined"), len(pop), len(new), flush=True)
    except Exception as e:
        print("ERR", name, cid, e, flush=True)
