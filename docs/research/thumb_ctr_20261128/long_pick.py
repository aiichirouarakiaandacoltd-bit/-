import csv, json, sys, collections
sys.path.insert(0, "/home/user/-/research/LONG-20261124/deep/scripts"); import yt
R=[r for r in csv.DictReader(open('/home/user/-/research/LONG-20261124/deep/videos_all.csv')) if r['kind']=='競合']
S={r['channel']:r for r in csv.DictReader(open('/home/user/-/research/LONG-20261124/deep/channels_summary.csv'))}
for r in R: r['v']=int(float(r['views'] or 0)); r['x']=float(r['ratio_to_recent_median'] or 0); r['med']=float(S.get(r['channel'],{}).get('median_views_recent30') or 0)
R=[r for r in R if r['med']>=5000]
seen=set(); per=collections.Counter(); top=[]
for r in sorted(R,key=lambda r:-r['x']):
    if r['id'] in seen or r['v']<300000 or per[r['channel']]>=3: continue
    seen.add(r['id']); per[r['channel']]+=1; top.append(r)
good=[r for r in top if not r['type'].startswith('NG')][:24]; ng=[r for r in top if r['type'].startswith('NG')][:8]
# 伸びなかった例(同じ上位チャンネルの直近で中央値の0.3倍未満)
chs={r['channel'] for r in good}; low=[]; per2=collections.Counter()
for r in sorted(R,key=lambda r:r['x']):
    if r['channel'] in chs and r['list']=='new' and 0<r['x']<0.35 and per2[r['channel']]<1 and r['id'] not in seen:
        per2[r['channel']]+=1; low.append(r); seen.add(r['id'])
low=low[:12]
out={'good':good,'ng':ng,'low':low}
for k,L in out.items():
    for r in L:
        p=f"long_thumbs/{r['id']}.jpg"
        import os
        if not os.path.exists(p): yt.thumb(r['id'],p)
json.dump({k:[{f:r[f] for f in ['channel','id','title','v','x','med','type']} for r in L] for k,L in out.items()},open('long_pick.json','w'),ensure_ascii=False,indent=1)
print({k:len(v) for k,v in out.items()})
