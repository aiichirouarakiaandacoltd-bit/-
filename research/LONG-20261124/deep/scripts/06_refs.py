"""参考動画: 高解像度サムネ + 自動生成の場面画像(hq1〜3) + 章の開始画像 を取得し、一覧画像を作る"""
import yt, json, os, sys
from PIL import Image, ImageDraw, ImageFont
yt.DELAY = 0.3
R = json.load(open("refs.json")); D = "../raw/details"; T = "../raw/ref_imgs"; os.makedirs(T, exist_ok=True)
F = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"; f1 = ImageFont.truetype(F, 16); f2 = ImageFont.truetype(F, 22)
def dl(url, fp):
    if os.path.exists(fp): return True
    try:
        yt._wait(); r = yt.S.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 1500: open(fp, "wb").write(r.content); return True
    except Exception: pass
    return False
def img(fp, size):
    try: return Image.open(fp).convert("RGB").resize(size)
    except Exception: return Image.new("RGB", size, (60, 60, 60))
def man(v): return "?" if v is None else (f"{v/10000:.1f}万" if v >= 10000 else str(v))
def get(vid):
    d = json.load(open(f"{D}/{vid}.json")) if os.path.exists(f"{D}/{vid}.json") else {"id": vid, "title": "?"}
    if not dl(f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", f"{T}/{vid}_t.jpg"): dl(f"https://i.ytimg.com/vi/{vid}/hq720.jpg", f"{T}/{vid}_t.jpg") or dl(f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg", f"{T}/{vid}_t.jpg")
    for n in (1, 2, 3): dl(f"https://i.ytimg.com/vi/{vid}/hq{n}.jpg", f"{T}/{vid}_f{n}.jpg")
    for i, c in enumerate(d.get("chapters", [])[:4]):
        if c.get("thumb"): dl(c["thumb"], f"{T}/{vid}_c{i}.jpg")
    return d
def thumb_sheet(name, ids, title):
    cols = 3; W = cols * 432 + 8; rows = (len(ids) + cols - 1) // cols
    im = Image.new("RGB", (W, 40 + rows * 296), (245, 245, 245)); dr = ImageDraw.Draw(im); dr.text((8, 6), title, font=f2, fill=0)
    for i, vid in enumerate(ids):
        d = get(vid); x = 8 + (i % cols) * 432; y = 40 + (i // cols) * 296
        im.paste(img(f"{T}/{vid}_t.jpg", (424, 238)), (x, y))
        dr.text((x, y + 240), f'#{i+1} {(d.get("channel") or "")[:12]} / {man(d.get("views"))}回 / {d.get("date_text","")}', font=f1, fill=(160, 0, 0))
        dr.text((x, y + 262), (d.get("title") or "")[:26], font=f1, fill=0)
    im.save(f"../sheets/{name}.jpg", quality=88)
def frame_sheet(name, ids, title):
    W = 8 + 4 * 328; im = Image.new("RGB", (W, 40 + len(ids) * 210), (245, 245, 245)); dr = ImageDraw.Draw(im); dr.text((8, 6), title, font=f2, fill=0)
    for i, vid in enumerate(ids):
        d = get(vid); y = 40 + i * 210
        im.paste(img(f"{T}/{vid}_t.jpg", (320, 180)), (8, y))
        c0 = f"{T}/{vid}_c1.jpg" if os.path.exists(f"{T}/{vid}_c1.jpg") else None
        for n in (1, 2, 3):
            fp = f"{T}/{vid}_f{n}.jpg"
            fr = img(fp, (320, 240)).crop((0, 30, 320, 210))
            im.paste(fr, (8 + n * 328, y))
        dr.text((8, y + 182), f'#{i+1} {(d.get("channel") or "")[:10]} {man(d.get("views"))} | {(d.get("title") or "")[:52]} | 左=表紙, 右3枚=本編の自動抽出画像(約25/50/75%)', font=f1, fill=0)
    im.save(f"../sheets/{name}.jpg", quality=85)
if __name__ == "__main__":
    fr = R["friendly"]
    thumb_sheet("ref_thumbs_01-18", fr[:18], "参考動画(好意型) 表紙 #1-18"); thumb_sheet("ref_thumbs_19-36", fr[18:], "参考動画(好意型) 表紙 #19-36")
    for k in range(0, len(fr), 9): frame_sheet(f"ref_frames_{k+1:02d}-{min(k+9,len(fr)):02d}", fr[k:k+9], f"参考動画(好意型) 表紙+本編画像 #{k+1}-")
    thumb_sheet("ref_thumbs_news_oxford", R["news"] + R["oxford_small"], "報道(オックスフォード) #1-6 と 小規模チャンネルの同題材 #7-18")
    frame_sheet("ref_frames_oxford_small", R["oxford_small"][:9], "小規模チャンネルの同題材(オックスフォード) 表紙+本編画像")
    thumb_sheet("ref_thumbs_ng", R["ng"], "NG型で伸びた例(要素の記録のみ・当方は不採用)")
    print("ok")
