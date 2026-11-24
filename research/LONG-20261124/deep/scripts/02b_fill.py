"""02 で欠けた 人気順 / 開設日 を補う"""
import yt, json, glob
for fp in sorted(glob.glob("../raw/channels/*.json")):
    j = json.load(open(fp)); cid = j["meta"].get("channel_id"); ch = False
    if not cid: continue
    if not j["popular"] and j["new"]:
        try:
            _, pop = yt.channel_videos(cid, "popular", 30); j["popular"] = pop; ch = True
        except Exception as e: print("ERR", e)
    if not j["about"].get("joined"):
        d = yt.api("browse", {"browseId": cid})
        for t in [e.get("token") for e in yt.walk(d, "continuationCommand")][:10]:
            try: x = yt.api("browse", {"continuation": t}, tries=1)
            except Exception: continue
            a = next(yt.walk(x, "aboutChannelViewModel"), None)
            if a:
                j["about"] = {"joined": yt.txt(a.get("joinedDateText")), "total_views": yt.num(a.get("viewCountText") or ""), "video_count": yt.num(a.get("videoCountText") or ""), "country": a.get("country")}; ch = True
                break
    if ch:
        json.dump(j, open(fp, "w"), ensure_ascii=False, indent=0); print(j["meta"].get("channel"), len(j["popular"]), j["about"].get("joined"), flush=True)
