"""表紙サンプル v2: それいけ皇室・みんなの皇室の雰囲気(黒地・極太の黄と白・縁取り二重・顔の大きな寄り・結末を伏せる下段)。
怒り/汗マーク・?!・矢印・赤丸・作られた台詞・対立の構図は使わない。赤は1行目の帯だけ。
写真: 宮内庁 令和7年 皇后陛下お誕生日に際してのご近影 A060(両陛下)・A061(皇后陛下)。切り抜き・拡大縮小のみ。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
RED, YEL, WHITE, GOLD = (200, 16, 30), (255, 221, 0), (255, 255, 255), (216, 188, 114)
L1 = "「あと20年で100年もの月日が」"; SRC = "令和7年 皇后陛下お誕生日のご感想より"
L2 = "12月9日 63歳のお誕生日"; L3 = "昨年のご感想の続きは…"
CAP = "令和7年 皇后陛下お誕生日に際してのご近影/宮内庁"
F = lambda p, s: ImageFont.truetype(p, s, index=0)

def fit(d, t, p, s, w):
    while s > 20 and d.textlength(t, font=F(p, s)) > w: s -= 2
    return F(p, s)

def double_outline(d, xy, t, f, fill, inner=(0, 0, 0), outer=WHITE, w=8, anchor="mm"):
    d.text(xy, t, font=f, fill=outer, stroke_width=w + 5, stroke_fill=outer, anchor=anchor)  # 外側の白
    d.text(xy, t, font=f, fill=fill, stroke_width=w, stroke_fill=inner, anchor=anchor)       # 内側の黒+本体

def face(src, cx, cy, frac, w, h):
    im = Image.open(os.path.join(A, src)).convert("RGB"); sw, sh = im.size
    ch = sh * frac; cw = ch * w / h
    l = max(0, min(sw - cw, cx * sw - cw / 2)); t = max(0, min(sh - ch, cy * sh - ch / 2))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((w, h), Image.LANCZOS)

def framed(base, img, x, y):
    d = ImageDraw.Draw(base); w, h = img.size
    sh = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((15, 15, w + 15, h + 15), fill=(0, 0, 0, 200))
    base.paste(sh.filter(ImageFilter.GaussianBlur(10)), (x - 8, y - 4), sh.filter(ImageFilter.GaussianBlur(10)))
    base.paste(img, (x, y)); d.rectangle((x - 4, y - 4, x + w + 3, y + h + 3), outline=GOLD, width=4)

def bg(W, H):
    # 黒地に、写真をぼかした暗い背景を薄く敷く(華やかさ)
    im = Image.open(os.path.join(A, "A060.jpg")).convert("RGB").resize((W, int(W * 1.5))).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(28))
    return Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, 0.28)

def long_v2(out):
    W, H = 1280, 720; im = bg(W, H); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 104), fill=RED)
    double_outline(d, (W / 2, 50), L1, fit(d, L1, BLACK, 70, W * 0.94), WHITE, outer=RED, w=5)
    fs = F(BOLD, 17); d.text((W - 10, 108), SRC, font=fs, fill=WHITE, anchor="rt")
    framed(im, face("A060.jpg", 0.385, 0.40, 0.30, 330, 380), 140, 140)   # 天皇陛下 胸から上
    framed(im, face("A061.jpg", 0.54, 0.24, 0.40, 330, 380), 810, 140)   # 皇后陛下 胸から上
    # 中央: お二人をつなぐ金の細線と小さな文字(対立ではなく「つながる」)
    d.line((490, 330, 790, 330), fill=GOLD, width=3); d.text((640, 312), "ともに歩まれて", font=F(BOLD, 26), fill=GOLD, anchor="mb")
    d.text((W - 10, 528), CAP, font=F(BOLD, 15), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0))
    double_outline(d, (W / 2, 578), L2, fit(d, L2, BLACK, 64, W * 0.92), WHITE, w=7)
    double_outline(d, (W / 2, 658), L3, fit(d, L3, BLACK, 92, W * 0.94), YEL, w=8)
    im.save(out, quality=95)

def short_v2(out):
    W, H = 1080, 1920; im = bg(W, H); d = ImageDraw.Draw(im)
    d.rectangle((0, 140, W, 300), fill=RED)
    double_outline(d, (W / 2, 220), L1, fit(d, L1, BLACK, 86, W * 0.94), WHITE, outer=RED, w=5)
    d.text((W - 12, 306), SRC, font=F(BOLD, 24), fill=WHITE, anchor="rt")
    framed(im, face("A061.jpg", 0.54, 0.30, 0.55, 860, 980), 110, 360)
    d.text((W - 110, 1336), CAP, font=F(BOLD, 22), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0))
    double_outline(d, (W / 2, 1450), L2, fit(d, L2, BLACK, 88, W * 0.92), WHITE, w=8)
    double_outline(d, (W / 2, 1600), L3, fit(d, L3, BLACK, 120, W * 0.96), YEL, w=10)
    im.save(out, quality=95)

long_v2(os.path.join(D, "sample_v2_long_1280x720.png")); short_v2(os.path.join(D, "sample_v2_short_1080x1920.png")); print("ok")
