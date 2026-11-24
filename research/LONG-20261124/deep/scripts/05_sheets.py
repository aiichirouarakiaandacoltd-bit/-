"""チャンネル別サムネ一覧(人気上位12+直近8)を作る。画像は downloaded/ に置き(未信頼データ)、sheets/ に一覧を書き出す"""
import yt, json, glob, os, sys, re
from PIL import Image, ImageDraw, ImageFont
yt.DELAY = 0.25
FONT = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"
f1 = ImageFont.truetype(FONT, 15); f2 = ImageFont.truetype(FONT, 22)
TH = "../raw/thumbs_mq"; os.makedirs(TH, exist_ok=True); os.makedirs("../sheets", exist_ok=True)
def mq(vid):
    fp = f"{TH}/{vid}.jpg"
    if not os.path.exists(fp):
        try:
            yt._wait(); r = yt.S.get(f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg", timeout=30)
            if r.status_code == 200: open(fp, "wb").write(r.content)
            else: return None
        except Exception: return None
    try: return Image.open(fp).convert("RGB").resize((320, 180))
    except Exception: return None
def man(v):
    if v is None: return "?"
    return f"{v/10000:.1f}万" if v >= 10000 else str(v)
def sheet(title, items, out, cols=4):
    rows = (len(items) + cols - 1) // cols
    W = cols * 328 + 8; H = 44 + rows * 232
    im = Image.new("RGB", (W, H), (245, 245, 245)); d = ImageDraw.Draw(im)
    d.text((8, 8), title, font=f2, fill=(0, 0, 0))
    for i, v in enumerate(items):
        x = 8 + (i % cols) * 328; y = 44 + (i // cols) * 232
        t = mq(v["id"])
        if t: im.paste(t, (x, y))
        d.text((x, y + 182), f'{v.get("tag","")} {man(v["views"])}回 / {v.get("length_text") or v.get("length","")} / {v.get("published","")}', font=f1, fill=(160, 0, 0))
        d.text((x, y + 202), (v.get("label") or v["title"])[:21], font=f1, fill=(0, 0, 0))
    im.save(out, quality=88)
if __name__ == "__main__":
    SKIP = ["一月万冊","むすび大学","古是三春","衝撃のJAPAN","日テレNEWS","TBS NEWS","ANNnewsCH","テレ東BIZ","FNNプライムオンライン"]
    for fp in sorted(glob.glob("../raw/channels/*.json")):
        j = json.load(open(fp)); name = j["meta"].get("channel") or ""
        if (any(s in name for s in SKIP) and "皇室のニュース" not in name) or not j["new"]: continue
        out = "../sheets/ch_" + re.sub(r"[^\w]+", "_", name)[:30] + ".jpg"
        if os.path.exists(out): continue
        items = [dict(v, tag=f"人気{i+1}") for i, v in enumerate(j["popular"][:12])] + [dict(v, tag=f"新{i+1}") for i, v in enumerate(j["new"][:8])]
        sheet(f'{name} / 登録 {j["meta"].get("subs")} / 開設 {j["about"].get("joined","?")} / 上段3行=人気順, 下段2行=新しい順', items, out)
        print(name, len(items), flush=True)
