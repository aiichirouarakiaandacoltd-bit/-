"""検索(題材×長尺フィルタ)で競合チャンネルを洗い出す。出力: raw/search_results.json, raw/channels_found.csv"""
import yt, json, csv, collections, datetime
Q = ["愛子さま","雅子さま","天皇陛下","皇室","上皇后 美智子さま","天皇皇后両陛下 外国訪問","園遊会","おことば 天皇陛下","皇后雅子さま 晩餐会","愛子さま シンガポール",
     "雅子さま オックスフォード","皇室 海外の反応","敬宮愛子さま","天皇ご一家","雅子さま 語学","愛子さま ラオス","国賓 宮中晩餐会","雅子さま 感動","愛子さま 感動","皇室 ドキュメンタリー",
     "雅子さま 英国訪問","天皇陛下 留学","皇室 ティアラ","雅子さま 外務省","皇室 名場面","歌会始","佳子さま","悠仁さま","皇室 歴史 解説","愛子さま 成年"]
F = {"long20": "EgIYAg%3D%3D", "mid4_20": "EgIYAw%3D%3D", "long20_month": "EgQIBBgC", "long20_views": "CAMSAhgC"}
known = ["皇室栄華","みんなの皇室","それいけ皇室","皇室のお話","皇室のひだまり","雅の記憶","五葉つつじ物語","敬愛JAPAN","皇室秘録","日本を愛で包む","皇室の夢【海外の反応】","皇室秘話室","皇室ヴェール","人生の心つづり",
         "雅子さまと愛子さま【皇室ファミリーの絆】","皇室パンフレット","菊の紋章 陽と陰","菊影深録","皇室の輝き","皇室伝説","至高の輝き","JAPANの美と魅力","日本の神秘","日テレNEWS","TBS NEWS DIG","ANNnewsCH","テレ東BIZ","FNNプライムオンライン","宮内庁"]
res = []; chans = {}
for q in Q:
    for fn, sp in F.items():
        if fn in ("long20_month","long20_views") and Q.index(q) >= 12: continue
        try: v, c = yt.search(q, sp, pages=2)
        except Exception as e: print("ERR", q, fn, e); continue
        for x in v: x.update(query=q, filter=fn)
        res += v; print(q, fn, len(v), flush=True)
for k in known:
    try: v, c = yt.search(k, "EgIQAg%3D%3D", pages=1)
    except Exception as e: print("ERR", k, e); continue
    for x in c[:3]: x["query"] = k
    chans[k] = c[:3]; print(k, [(x["channel"], x["subs_text"]) for x in c[:3]], flush=True)
json.dump({"fetched": datetime.datetime.utcnow().isoformat()+"Z", "videos": res, "channel_search": chans}, open("../raw/search_results.json","w"), ensure_ascii=False, indent=0)
agg = collections.defaultdict(lambda: {"n":0,"views":0,"max":0,"name":"","qs":set(),"ids":set()})
for v in res:
    if not v["channel_id"] or v["id"] in agg[v["channel_id"]]["ids"]: continue
    a = agg[v["channel_id"]]; a["ids"].add(v["id"]); a["n"]+=1; a["views"]+=v["views"] or 0; a["max"]=max(a["max"], v["views"] or 0); a["name"]=v["channel"]; a["qs"].add(v["query"])
w = csv.writer(open("../raw/channels_found.csv","w")); w.writerow(["channel_id","channel","hits","sum_views","max_views","n_queries"])
for cid,a in sorted(agg.items(), key=lambda kv:-kv[1]["n"]): w.writerow([cid,a["name"],a["n"],a["views"],a["max"],len(a["qs"])])
print(len(res), len(agg))
