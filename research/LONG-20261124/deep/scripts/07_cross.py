"""横断分析: 尺・題名の要素・人物・題材ごとに、チャンネル内中央値に対する倍率(直近30本)の中央値を出す。出力: cross_analysis.json"""
import csv, re, statistics as st, json, glob, os
rows = [r for r in csv.DictReader(open("../videos_all.csv")) if r["kind"] == "競合" and r["views"] and not any(e in r["channel"] for e in ["一月万冊","むすび大学","古是三春","衝撃のJAPAN","kata62kima"])]
new = [r for r in rows if r["list"] == "new" and r["ratio_to_recent_median"] and float(r["age_days"] or 0) >= 2]
pop = {r["id"]: r for r in rows if r["list"] == "popular"}
def med(xs): return round(st.median(xs), 2) if xs else None
out = {}
def table(name, fn, base):
    g = {}
    for r in base:
        for k in fn(r): g.setdefault(k, []).append(r)
    t = {k: {"n": len(v), "median_ratio": med([float(r["ratio_to_recent_median"]) for r in v]), "median_views": med([float(r["views"]) for r in v]), "share_over_3x": round(sum(1 for r in v if float(r["ratio_to_recent_median"]) >= 3) / len(v), 2)} for k, v in g.items() if len(v) >= 8}
    out[name] = dict(sorted(t.items(), key=lambda kv: -(kv[1]["median_ratio"] or 0)))
    print("\n##", name)
    for k, v in out[name].items(): print(f'  {k:16s} n={v["n"]:4d} 倍率中央値={v["median_ratio"]} 再生中央値={int(v["median_views"])} 3倍超の割合={v["share_over_3x"]}')
def lb(r):
    s = int(r["length_sec"] or 0)
    return ["~4分" if s < 240 else "4-8分" if s < 480 else "8-12分" if s < 720 else "12-20分" if s < 1200 else "20-30分" if s < 1800 else "30-60分" if s < 3600 else "60分~"]
F = {"肉声/実音声/生声": r"肉声|実音声|生声|音声", "次の瞬間/直後/◯秒後": r"次の瞬間|直後|秒後", "理由/ワケ/なぜ": r"理由|ワケ|なぜ|真相|とは", "かぎかっこ引用": r"「[^」]{4,}」", "海外の反応/世界が": r"海外の反応|世界が|世界中", "疑問符？": r"[？?]", "【】見出し": r"^【", "語学/英語/◯語": r"語学|英語|フランス語|スペイン語|ポルトガル語|通訳", "涙/感動/号泣": r"涙|感動|号泣", "異例/前代未聞/驚愕": r"異例|前代未聞|驚愕|衝撃|騒然|絶句", "報じない/日本では": r"報じ|報道され", "数字入り": r"\d+(年|歳|秒|分|人|か国|カ国|回|日)", "総集編/まとめ/全": r"総集編|まとめ|すべて|全記録|選$|\d選", "説明調(〜され/〜られた…長文で疑問なし)": None}
def feats(r):
    t = r["title"]; o = [k for k, p in F.items() if p and re.search(p, t)]
    if not re.search(r"[？?！!…]|次の瞬間|理由|とは|【", t): o.append("説明調(記号・疑問なし)")
    return o
P = {"雅子さま": r"雅子", "愛子さま": r"愛子|敬宮", "天皇陛下": r"陛下(?!.*両)|天皇(?!皇后)", "両陛下": r"両陛下|天皇皇后", "ご一家": r"ご一家|御一家", "秋篠宮家関連": r"紀子|秋篠宮|佳子|悠仁|眞子|小室", "上皇ご夫妻関連": r"美智子|上皇", "外国要人": r"国王|王妃|大統領|皇太子|首相|夫人|キャサリン|チャールズ|トランプ|マクロン"}
T = {"シンガポール": r"シンガポール", "英国": r"英国|イギリス|チャールズ|バッキンガム|オックスフォード|ウィリアム|キャサリン", "オランダ/ベルギー": r"オランダ|ベルギー", "園遊会": r"園遊会", "晩餐会": r"晩餐会|晩さん会", "那須/ご静養": r"那須|静養|下田|御用邸", "地方ご訪問": r"青森|高知|大阪|鳥取|熊本|長崎|福島|国スポ|国民文化祭|海づくり", "装い/ティアラ": r"ドレス|コーデ|装い|ティアラ|着物|振袖|ファッション", "幼少期/家族史": r"幼少|歳の愛子|結婚|ご成婚|誕生|銀婚|\d+年前|パパ", "会見/おことば": r"会見|おことば|お言葉|スピーチ|ご感想", "生涯/人生": r"生涯|人生|半生"}
table("尺(直近30本)", lb, new)
table("題名の要素(直近30本)", feats, new)
table("人物(直近30本)", lambda r: [k for k, p in P.items() if re.search(p, r["title"])], new)
table("題材(直近30本)", lambda r: [k for k, p in T.items() if re.search(p, r["title"])], new)
table("区分(直近30本)", lambda r: [r["type"]], new)
# 絶対値: 人気上位(各ch上位30)での区分別
print("\n## 10万回以上の本数(全取得・重複除く)")
seen = {}
for r in rows: seen[r["id"]] = r
big = [r for r in seen.values() if float(r["views"]) >= 100000]
import collections
c = collections.Counter(r["type"] for r in big); print(dict(c), len(big))
c2 = collections.Counter(lb(r)[0] for r in big); print(dict(c2))
big1m = [r for r in seen.values() if float(r["views"]) >= 1000000]
print("100万以上", len(big1m), dict(collections.Counter(r["type"] for r in big1m)), dict(collections.Counter(lb(r)[0] for r in big1m)))
out["big_counts"] = {"100k_type": dict(c), "100k_len": dict(c2), "1m_type": dict(collections.Counter(r["type"] for r in big1m)), "1m_len": dict(collections.Counter(lb(r)[0] for r in big1m))}
# コメント率
D = {}
for fp in glob.glob("../raw/details/*.json"):
    d = json.load(open(fp)); D[d["id"]] = d
cr = {}
for r in seen.values():
    d = D.get(r["id"])
    if d and d.get("comments") and d.get("views") and d["views"] >= 20000: cr.setdefault(r["type"], []).append(d["comments"] / d["views"] * 1000)
print("\n## コメント数/1000再生 (中央値)", {k: (round(st.median(v), 2), len(v)) for k, v in cr.items()})
out["comments_per_1000"] = {k: {"median": round(st.median(v), 2), "n": len(v)} for k, v in cr.items()}
json.dump(out, open("../cross_analysis.json", "w"), ensure_ascii=False, indent=1)
