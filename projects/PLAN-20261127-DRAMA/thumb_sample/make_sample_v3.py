"""表紙サンプル v3: 競合(それいけ皇室・みんなの皇室)の実物を見て作り直し。
黒は上下の細い帯だけ。中段は写真2〜3枚を横幅いっぱいに並べる。上=黄の極太「」、下1行目=水色の極太、下2行目=赤い帯に白の極太(結末を伏せる)。
怒り/汗マーク・?!・矢印・赤丸・吹き出しの台詞・対立の構図は使わない。「」は宮内庁の原文。写真は宮内庁 令和7年 皇后陛下お誕生日のご近影(切り抜き・拡大縮小のみ)。"""
from PIL import Image, ImageDraw, ImageFont
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
YEL, CYAN, WHITE, RED = (255, 230, 0), (80, 220, 255), (255, 255, 255), (205, 15, 25)
F = lambda p, s: ImageFont.truetype(p, s, index=0)
L1 = "「あと20年で100年もの月日が」"
L2 = "12月9日 63歳を迎えられる雅子さま"
L3 = "昨年のご感想に綴られた想いとは…"
SRC = "令和7年 皇后陛下お誕生日のご感想より/写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影"

def fit(d, t, p, s, w):
    while s > 20 and d.textlength(t, font=F(p, s)) > w: s -= 2
    return F(p, s)

def crop(name, cx, cy, frac, w, h):
    im = Image.open(os.path.join(A, name)).convert("RGB"); sw, sh = im.size
    ch = sh * frac; cw = ch * w / h
    if cw > sw: cw = sw; ch = cw * h / w
    l = max(0, min(sw - cw, cx * sw - cw / 2)); t = max(0, min(sh - ch, cy * sh - ch / 2))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((w, h), Image.LANCZOS)

def make_long(out):
    W, H = 1280, 720; im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    top, bot = 96, 500  # 写真の帯
    panels = [("A061.jpg", 0.54, 0.24, 0.42, 400), ("A064.jpg", 0.55, 0.45, 0.50, 480), ("A060.jpg", 0.39, 0.30, 0.30, 400)]
    x = 0
    for n, cx, cy, fr, w in panels:
        im.paste(crop(n, cx, cy, fr, w, bot - top), (x, top)); x += w
    for xx in (400, 880): d.rectangle((xx - 2, top, xx + 2, bot), fill=(0, 0, 0))  # 写真の境目
    d.text((W / 2, 50), L1, font=fit(d, L1, BLACK, 78, W * 0.97), fill=YEL, stroke_width=7, stroke_fill=(0, 0, 0), anchor="mm")
    d.text((W - 6, bot - 4), SRC, font=F(BOLD, 13), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((W / 2, 555), L2, font=fit(d, L2, BLACK, 66, W * 0.96), fill=CYAN, stroke_width=7, stroke_fill=(0, 0, 0), anchor="mm")
    d.rectangle((0, 604, W, 712), fill=RED)
    d.text((W / 2, 657), L3, font=fit(d, L3, BLACK, 82, W * 0.97), fill=WHITE, stroke_width=6, stroke_fill=(0, 0, 0), anchor="mm")
    im.save(out, quality=95)

def make_short(out):
    W, H = 1080, 1920; im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((W / 2, 230), L1, font=fit(d, L1, BLACK, 92, W * 0.96), fill=YEL, stroke_width=8, stroke_fill=(0, 0, 0), anchor="mm")
    im.paste(crop("A061.jpg", 0.54, 0.36, 0.70, 1080, 620), (0, 300))
    im.paste(crop("A064.jpg", 0.55, 0.42, 0.40, 1080, 560), (0, 924))
    d.rectangle((0, 920, W, 924), fill=(0, 0, 0))
    d.text((W - 8, 1480), SRC.split("/")[1], font=F(BOLD, 20), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((W / 2, 1550), L2, font=fit(d, L2, BLACK, 80, W * 0.96), fill=CYAN, stroke_width=8, stroke_fill=(0, 0, 0), anchor="mm")
    d.rectangle((0, 1610, W, 1740), fill=RED)
    d.text((W / 2, 1675), L3, font=fit(d, L3, BLACK, 84, W * 0.97), fill=WHITE, stroke_width=7, stroke_fill=(0, 0, 0), anchor="mm")
    d.text((W - 10, 300), SRC.split("/")[0], font=F(BOLD, 20), fill=WHITE, anchor="rb")
    im.save(out, quality=95)

make_long(os.path.join(D, "sample_v3_long_1280x720.png")); make_short(os.path.join(D, "sample_v3_short_1080x1920.png")); print("ok")
