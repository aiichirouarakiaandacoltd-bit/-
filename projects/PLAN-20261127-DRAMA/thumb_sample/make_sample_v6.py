"""表紙 v6: 荒木さん提示の参考(左に顔の大きな寄り/右に濃紺の文字面・金の帯・極太の白と金の文字)に合わせた型。
文字はお顔・頭に掛けない(体には掛かってよい)。菊の御紋は使わない(皇室の紋章=公式と誤解されるため)。赤は使わず強調線はラズベリー。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"; SANS = "/home/user/-/templates/fonts/NotoSansJP-Black.ttf"; SANSB = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"
F = lambda p, s: ImageFont.truetype(p, s, index=0) if p.endswith(".ttc") else ImageFont.truetype(p, s)
NAVY1, NAVY2 = (14, 24, 48), (28, 44, 82); GOLD1, GOLD2 = (255, 238, 160), (214, 160, 40); WHITE = (255, 255, 255); BERRY = (217, 43, 94)

def crop(name, cx, cy, frac, w, h):
    im = Image.open(os.path.join(A, name)).convert("RGB"); sw, sh = im.size
    ch = sh * frac; cw = ch * w / h
    if cw > sw: cw = sw; ch = cw * h / w
    l = max(0, min(sw - cw, cx * sw - cw / 2)); t = max(0, min(sh - ch, cy * sh - ch / 2))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((w, h), Image.LANCZOS)

def vgrad(size, c1, c2):
    w, h = size; g = Image.new("RGB", size); d = ImageDraw.Draw(g)
    for y in range(h):
        r = y / max(1, h - 1); d.line((0, y, w, y), fill=tuple(int(c1[k] + (c2[k] - c1[k]) * r) for k in range(3)))
    return g

def text(im, xy, s, f, fill=WHITE, gold=False, anchor="lm", sw=3):
    W, H = im.size
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 5), s, font=f, fill=(0, 0, 0, 220), anchor=anchor, stroke_width=sw + 3, stroke_fill=(0, 0, 0, 220))
    b = sh.filter(ImageFilter.GaussianBlur(8)); im.paste(b, (0, 0), b)
    d = ImageDraw.Draw(im); d.text(xy, s, font=f, fill=(10, 14, 28), anchor=anchor, stroke_width=sw, stroke_fill=(10, 14, 28))
    if gold:
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor); bb = m.getbbox()
        g = Image.new("RGB", (W, H)); g.paste(vgrad((W, bb[3] - bb[1]), GOLD1, GOLD2), (0, bb[1])); im.paste(g, (0, 0), m)
    else:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
    return d.textbbox(xy, s, font=f, anchor=anchor)

def gold_plate(im, box, s, f):
    x0, y0, x1, y1 = box; g = vgrad((x1 - x0, y1 - y0), (250, 226, 140), (196, 150, 50))
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).polygon([(14, 0), (g.size[0], 0), (g.size[0] - 14, g.size[1]), (0, g.size[1])], fill=255)
    im.paste(g, (x0, y0), m); ImageDraw.Draw(im).text(((x0 + x1) / 2, (y0 + y1) / 2), s, font=f, fill=NAVY1, anchor="mm")

def long(out):
    W, H = 1280, 720; im = vgrad((W, H), NAVY2, NAVY1)
    # 左: 雅子さまの顔の大きな寄り(右端を濃紺へなじませる)
    face = crop("A061.jpg", 0.52, 0.27, 0.42, 520, 720); fm = Image.new("L", (520, 720), 255); fd = ImageDraw.Draw(fm)
    for x in range(380, 520): fd.line((x, 0, x, 720), fill=int(255 * (520 - x) / 140))
    im.paste(face, (0, 0), fm)
    d = ImageDraw.Draw(im)
    gold_plate(im, (470, 28, 1240, 108), "日本が誇る皇室物語", F(SANS, 46))
    text(im, (480, 190), "12月9日 63歳を迎えられる", F(SANS, 58))
    b = text(im, (480, 300), "雅子さまのご感想", F(SERIF, 86), gold=True)
    d.rounded_rectangle((480, b[3] + 8, b[2], b[3] + 18), 5, fill=BERRY)  # 強調の下線(ラズベリー)
    d.line((440, 400, 1260, 400), fill=GOLD2, width=3)
    text(im, (470, 495), "「あと20年で", F(SERIF, 92))
    text(im, (470, 620), "100年もの月日が」", F(SERIF, 92), gold=True)
    d.line((0, 712, W, 712), fill=GOLD2, width=6)
    d.text((W - 10, H - 14), "写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影/「」は令和7年のご感想より", font=F(SANSB, 13), fill=(230, 230, 230), anchor="rb")
    im.save(out, quality=95)

long(os.path.join(D, "sample_v6_long.png")); print("ok")
