import json, glob, statistics, collections, os, sys
sys.path.insert(0, "/home/user/-/research/LONG-20261124/deep/scripts"); import yt
rows=[]; chans=[]
for f in glob.glob("raw/*.json"):
    d=json.load(open(f)); new=[v for v in d["new"] if v["views"]]
    if len(new)<10: continue
    med=statistics.median(v["views"] for v in new)
    if med<3000: continue
    chans.append((d["name"],len(new),med,max([v["views"] for v in d["new"]+d["popular"]] or [0])))
    seen=set()
    for v in d["new"]+d["popular"]:
        if v["id"] in seen or not v["views"]: continue
        seen.add(v["id"]); rows.append({"channel":d["name"],"id":v["id"],"title":v["title"],"v":v["views"],"x":v["views"]/med,"med":med})
NG=["紀子","秋篠宮","佳子","悠仁","眞子","小室","美智子","ブチギレ","暴露","激怒","制裁","断罪","失態","炎上","差","一方"]
for r in rows: r["type"]="NG" if any(w in r["title"] for w in NG) else "好意"
per=collections.Counter(); top=[]
for r in sorted(rows,key=lambda r:-r["x"]):
    if r["v"]<200000 or per[r["channel"]]>=3: continue
    per[r["channel"]]+=1; top.append(r)
good=[r for r in top if r["type"]=="好意"][:18]; ng=[r for r in top if r["type"]=="NG"][:6]
chs={r["channel"] for r in good}; low=[]; per2=collections.Counter()
for r in sorted(rows,key=lambda r:r["x"]):
    if r["channel"] in chs and r["x"]<0.3 and per2[r["channel"]]<1: per2[r["channel"]]+=1; low.append(r)
os.makedirs("short_thumbs",exist_ok=True)
for r in good+ng+low:
    p=f"short_thumbs/{r['id']}.jpg"
    if os.path.exists(p): continue
    for q in ("oardefault","oar2","frame0","hq720","hqdefault"):
        try:
            rr=yt.S.get(f"https://i.ytimg.com/vi/{r['id']}/{q}.jpg",timeout=30)
            if rr.status_code==200 and len(rr.content)>3000: open(p,"wb").write(rr.content); break
        except Exception: pass
json.dump({"channels":sorted(chans,key=lambda c:-c[2]),"good":good,"ng":ng,"low":low},open("short_pick.json","w"),ensure_ascii=False,indent=1)
from sheet import sheet
sheet(good[:12],"sheets/short_good_01-12.jpg","short_thumbs",vertical=True)
sheet(good[12:18]+ng,"sheets/short_good_13-18_ng.jpg","short_thumbs",vertical=True)
sheet(low[:12],"sheets/short_low.jpg","short_thumbs",vertical=True)
print(len(chans),"channels",len(good),len(ng),len(low))
for c in sorted(chans,key=lambda c:-c[2])[:25]: print(c)
