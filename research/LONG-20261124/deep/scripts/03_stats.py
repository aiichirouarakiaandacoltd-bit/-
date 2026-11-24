"""チャンネル別の統計と全動画一覧(CSV)を作る。出力: channels_summary.csv, videos_all.csv"""
import json, glob, re, csv, statistics as st, os
NEWS = ["日テレNEWS","TBS NEWS DIG","ANNnewsCH","テレ東BIZ","FNNプライムオンライン","宮内庁","産経","THE PAGE"]
NG_FAM = r"紀子|秋篠宮|キコ|眞子|小室|悠仁|佳子|美智子|上皇后|A宮|ミテコ"
NG_NEG = r"発狂|激怒|制裁|暴露|嫌われ|ｗ|w$|逃亡|追放|違和感|失態|赤っ恥|蒼白|ブチギレ|ブチ切れ|激昂|末路|哀れ|崩壊|嘘|ウソ|偽|疑惑|批判|炎上|無視|拒否|拒絶|恥|ざまあ|悲鳴|悲惨|屈辱|公開処刑|格の違い|比較|比べ|一方|対照的|差|真逆|凍りつ|青ざめ|撃沈|完敗|断罪|追い詰め|没落|大恥|非常識|裏切|いじめ|イジメ|虐|闇|正体|本性|バレ|隠蔽|怒り|怒っ|叱|一喝|論破|ピシャリ|黙らせ|呆れ|失笑|嘲笑|震え|パニック|絶望|悲劇|暴走|横暴|傲慢|ポンコツ|仮病|不敬|冷遇|塩対応|門前払い|出禁|激震|修羅場|衝撃の理由|ヤバ|やば"
SENS = r"驚愕|絶句|騒然|海外の反応|世界が|世界中|大絶賛|衝撃|涙|号泣|感動|震撼|仰天|鳥肌|異例|神対応|とんでもない|まさか|前代未聞"
def days(s):
    m = re.search(r"(\d+)\s*(秒|分|時間|日|週間|か月|ヶ月|年)", s or "")
    if not m: return None
    n = int(m.group(1)); u = m.group(2)
    return {"秒":0,"分":0,"時間":n/24,"日":n,"週間":n*7,"か月":n*30.4,"ヶ月":n*30.4,"年":n*365}[u]
def cls(t):
    fam = re.search(NG_FAM, t); neg = re.search(NG_NEG, t)
    if neg and fam: return "NG対立"
    if neg: return "NG煽り"
    if re.search(SENS, t): return "反応・感情型"
    return "事実・好意型"
rows = []; allv = []
for fp in sorted(glob.glob("../raw/channels/*.json")):
    j = json.load(open(fp)); m = j["meta"]; a = j.get("about", {})
    name = m.get("channel") or ""
    kind = "報道・公式" if any(n in name for n in NEWS) else "競合"
    new = j["new"]; pop = j["popular"]
    nv = [v["views"] for v in new if v["views"] is not None]; pv = [v["views"] for v in pop if v["views"] is not None]
    med_new = st.median(nv) if nv else None; med_pop = st.median(pv) if pv else None
    nd = [days(v["published"]) for v in new]; nd = [d for d in nd if d is not None]
    span = max(nd) if nd else None
    per_week = round(len(nd) / max(span, 1) * 7, 1) if span else None
    nl = [v["length"] for v in new if v["length"]]; pl = [v["length"] for v in pop if v["length"]]
    top = max(pv) if pv else None
    kinds_new = [cls(v["title"]) for v in new]; kinds_pop = [cls(v["title"]) for v in pop]
    def share(k, L): return round(sum(1 for x in L if x.startswith(k)) / len(L), 2) if L else None
    rows.append({"channel": name, "kind": kind, "channel_id": m.get("channel_id"), "url": m.get("url"), "subs": m.get("subs"), "joined": (a.get("joined") or "").replace(" に登録",""),
                 "total_views": a.get("total_views"), "video_count": a.get("video_count") or m.get("video_count"),
                 "n_new": len(new), "n_pop": len(pop), "median_views_recent30": med_new, "median_views_top30": med_pop, "top_views": top,
                 "top_over_recent_median": round(top / med_new, 1) if top and med_new else None,
                 "recent30_span_days": round(span) if span else None, "videos_per_week": per_week,
                 "median_len_recent_min": round(st.median(nl) / 60, 1) if nl else None, "median_len_top_min": round(st.median(pl) / 60, 1) if pl else None,
                 "ng_share_recent": share("NG", kinds_new), "ng_share_top": share("NG", kinds_pop)})
    seen = set()
    for lst, tag in ((pop, "popular"), (new, "new")):
        for i, v in enumerate(lst):
            r = {"channel": name, "kind": kind, "channel_id": m.get("channel_id"), "list": tag, "rank": i + 1, "id": v["id"], "title": v["title"], "views": v["views"],
                 "length_sec": v["length"], "length": v["length_text"], "published": v["published"], "age_days": days(v["published"]),
                 "ratio_to_recent_median": round(v["views"] / med_new, 2) if v["views"] and med_new else None, "type": cls(v["title"]), "url": "https://www.youtube.com/watch?v=" + v["id"]}
            allv.append(r)
def wr(fp, rows):
    w = csv.DictWriter(open(fp, "w", newline=""), fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
rows.sort(key=lambda r: -(r["median_views_recent30"] or 0))
wr("../channels_summary.csv", rows); wr("../videos_all.csv", allv)
print(len(rows), len(allv))
for r in rows:
    print(f'{r["channel"][:22]:22s}|{r["kind"][:2]}|登{r["subs"]}|{r["joined"]}|中央(直近){r["median_views_recent30"]}|最大{r["top_views"]}|x{r["top_over_recent_median"]}|週{r["videos_per_week"]}本|尺{r["median_len_recent_min"]}/{r["median_len_top_min"]}分|NG {r["ng_share_recent"]}/{r["ng_share_top"]}')
