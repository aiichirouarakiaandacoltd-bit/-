# 表紙の組み立て: AI背景(bg/) + 宮内庁写真の切り抜き(cut/、画素は無加工) + 文字(明朝・ゴシックの極太)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SANS = "/home/user/-/templates/fonts/NotoSansJP-Black.ttf"
SANSB = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"
SRC = "/home/user/-/assets/KB-20261124-01/"
NAVY = (10, 18, 40); WHITE = (255, 255, 255)
QUOTE = "あと20年で100年もの月日が"   # 宮内庁 原文(raw/empress2025.txt 12行目)と一字一句同じ
def F(p, s): return ImageFont.truetype(p, s, index=0)

def bg(name, W, H):
    im = Image.open(f"bg/{name}.png").convert("RGB")
    s = max(W / im.width, H / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H)).convert("RGBA")

def grad_fill(size, stops):
    W, H = size; t = np.linspace(0, 1, H)[:, None]
    out = np.zeros((H, W, 3))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (t >= p0) & (t <= p1); k = np.clip((t - p0) / max(p1 - p0, 1e-6), 0, 1)
        for ch in range(3): out[..., ch] = np.where(m, c0[ch] + (c1[ch] - c0[ch]) * k, out[..., ch])
    return Image.fromarray(out.astype(np.uint8))
GOLD = [(0, (255, 246, 205)), (0.38, (240, 205, 120)), (0.55, (196, 150, 60)), (0.75, (233, 196, 108)), (1, (255, 236, 170))]

def text(im, xy, s, font, fill=WHITE, anchor="mm", stroke=6, stroke_fill=NAVY, gold=False, shadow=True, glow=None):
    W, H = im.size
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text(xy, s, font=font, fill=255, anchor=anchor)
    ms = Image.new("L", (W, H), 0); ImageDraw.Draw(ms).text(xy, s, font=font, fill=255, anchor=anchor, stroke_width=stroke)
    if glow:
        g = ms.filter(ImageFilter.GaussianBlur(18)); lay = Image.new("RGBA", (W, H), glow + (0,)); lay.putalpha(g.point(lambda v: int(v * 0.55)))
        im.alpha_composite(lay)
    if shadow:
        sh = ms.filter(ImageFilter.GaussianBlur(6)); sh = Image.fromarray(np.roll(np.asarray(sh), (5, 4), (0, 1)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.putalpha(sh.point(lambda v: int(v * 0.75))); im.alpha_composite(lay)
    if stroke:
        lay = Image.new("RGBA", (W, H), stroke_fill + (255,)); lay.putalpha(ms); im.alpha_composite(lay)
    bb = m.getbbox()
    if gold and bb:
        f = grad_fill((W, bb[3] - bb[1]), GOLD); full = Image.new("RGB", (W, H)); full.paste(f, (0, bb[1]))
        lay = full.convert("RGBA"); lay.putalpha(m); im.alpha_composite(lay)
        hl = m.filter(ImageFilter.GaussianBlur(1)); hl = Image.fromarray(np.clip(np.asarray(m, int) - np.roll(np.asarray(hl, int), (2, 0), (0, 1)), 0, 255).astype(np.uint8))
        lay = Image.new("RGBA", (W, H), (255, 255, 240, 0)); lay.putalpha(hl.point(lambda v: int(v * 0.6))); im.alpha_composite(lay)
    else:
        lay = Image.new("RGBA", (W, H), fill + (255,)); lay.putalpha(m); im.alpha_composite(lay)
    return bb

def fit(s, path, size, maxw):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    while d.textlength(s, font=F(path, size)) > maxw: size -= 2
    return F(path, size)

def person(name, h_target, crop_frac=1.0):
    c = Image.open(f"cut/{name}_cut.png"); bb = c.split()[-1].point(lambda v: 255 if v > 40 else 0).getbbox(); c = c.crop(bb)
    c = c.crop((0, 0, c.width, int(c.height * crop_frac)))
    s = h_target / c.height; return c.resize((round(c.width * s), round(h_target)), Image.LANCZOS)

def place(im, p, x_center, top, glow=(255, 214, 120), rim=True):
    W, H = im.size; x = int(x_center - p.width / 2)
    a = p.split()[-1]
    if glow:  # 人物の後ろの柔らかい光(AIではなく画面上の効果。お顔・お姿は変えない)
        g = Image.new("L", (W, H), 0); g.paste(a, (x, top)); g = g.filter(ImageFilter.GaussianBlur(40))
        lay = Image.new("RGBA", (W, H), glow + (0,)); lay.putalpha(g.point(lambda v: int(v * 0.55))); im.alpha_composite(lay)
    if rim:
        g = Image.new("L", (W, H), 0); g.paste(a, (x, top)); g = g.filter(ImageFilter.GaussianBlur(3))
        lay = Image.new("RGBA", (W, H), (255, 236, 180, 0)); lay.putalpha(g.point(lambda v: int(min(v, 255 - v) * 0.9))); im.alpha_composite(lay)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.paste(p, (x, top)); im.alpha_composite(lay)
    return (x, top, x + p.width, top + p.height)

def vgrad(im, y0, y1, color=NAVY, a0=0, a1=230):
    W, H = im.size; a = np.zeros((H, W), np.uint8)
    t = np.clip((np.arange(H) - y0) / max(y1 - y0, 1), 0, 1); a[:] = (a0 + (a1 - a0) * t)[:, None] * ((np.arange(H) >= min(y0, y1))[:, None])
    if y1 < y0: t = np.clip((y0 - np.arange(H)) / (y0 - y1), 0, 1); a[:] = (a0 + (a1 - a0) * t)[:, None] * ((np.arange(H) <= y0)[:, None])
    lay = Image.new("RGBA", (W, H), color + (0,)); lay.putalpha(Image.fromarray(a)); im.alpha_composite(lay)

def plaque(im, box, r=14):
    x0, y0, x1, y1 = box; W, H = im.size
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x0 + 6, y0 + 10, x1 + 6, y1 + 10), r, fill=200)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.putalpha(sh.filter(ImageFilter.GaussianBlur(12))); im.alpha_composite(lay)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    g = grad_fill((W, y1 - y0), [(0, (255, 240, 190)), (0.45, (232, 196, 110)), (0.6, (205, 162, 72)), (1, (242, 214, 140))])
    full = Image.new("RGB", (W, H)); full.paste(g, (0, y0)); full = full.convert("RGBA"); full.putalpha(m); im.alpha_composite(full)
    d = ImageDraw.Draw(im); d.rounded_rectangle((x0 + 8, y0 + 8, x1 - 8, y1 - 8), r - 6, outline=(120, 86, 30), width=2)
    d.rounded_rectangle((x0, y0, x1, y1), r, outline=(255, 248, 215), width=2)

def credit(im, xy, lines, size=15, anchor="rd", fill=(235, 235, 235)):
    d = ImageDraw.Draw(im); f = F(SANSB, size)
    d.multiline_text(xy, "\n".join(lines), font=f, fill=fill, anchor=anchor, align="right" if anchor[0] == "r" else "left", stroke_width=2, stroke_fill=(0, 0, 0), spacing=3)

def logo(im, xy, size=22, anchor="mm"):
    text(im, xy, "日本が誇る皇室物語", F(SERIF, size), anchor=anchor, stroke=3, gold=True, shadow=False)

CR_Q = "「」:宮内庁 令和7年 皇后陛下お誕生日に際してのご感想より"

# ---------- A1 濃紺と金の額縁・左右に両陛下 ----------
def long_A1():
    W, H = 1280, 720; im = bg("A1_frame_navy", W, H)
    e = person("A066", 900, 0.62); m = person("A061", 860, 0.66)
    place(im, e, 190, 118); place(im, m, 1090, 112)
    vgrad(im, 560, 720, a1=170)
    cx = 640
    logo(im, (cx, 62), 22)
    text(im, (cx, 120), "12月9日 63歳のお誕生日", F(SERIF, 38), stroke=5)
    plaque(im, (cx - 250, 162, cx + 250, 338))
    q = F(SERIF, 50)
    text(im, (cx, 218), "「あと20年で", q, fill=NAVY, stroke=0, shadow=False)
    text(im, (cx, 288), "100年もの月日が」", q, fill=NAVY, stroke=0, shadow=False)
    text(im, (cx, 358), "皇后陛下 令和7年のご感想より", F(SANSB, 17), fill=(240, 220, 160), stroke=2, shadow=False)
    text(im, (cx, 470), "戦後80年", F(SERIF, 132), stroke=8, gold=True, glow=(255, 200, 90))
    text(im, (cx, 592), "雅子さまが綴られた想いとは…", fit("雅子さまが綴られた想いとは…", SERIF, 46, 560), stroke=6)
    credit(im, (cx, 690), ["写真:宮内庁 令和7年 天皇陛下・皇后陛下お誕生日に際してのご近影(御所)", CR_Q], 13, anchor="md")
    return im

# ---------- A2 金屏風の雲・両陛下お並び(右)・文字は左 ----------
def long_A2():
    W, H = 1280, 720; im = bg("A2_goldscreen", W, H)
    vgrad(im, 0, 0)  # no-op
    p = person("A062", 640, 1.0); place(im, p, 960, H - 640 + 10)
    # 左の文字の下に濃紺の薄い面(金の細線つき)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((40, 110, 640, 380), 18, fill=(8, 16, 40, 200)); im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((52, 122, 628, 368), 12, outline=(222, 186, 104), width=2)
    logo(im, (60, 60), 24, anchor="lm")
    text(im, (340, 148), "12月9日 63歳のお誕生日", F(SERIF, 30), stroke=4, gold=True, shadow=False)
    d.line((120, 176, 560, 176), fill=(222, 186, 104), width=1)
    q = F(SERIF, 64)
    text(im, (340, 238), "「あと20年で", q, stroke=5)
    text(im, (340, 318), "100年もの月日が」", q, stroke=5)
    text(im, (340, 400), "皇后陛下 令和7年のご感想より", F(SANSB, 17), fill=(240, 220, 160), stroke=3, shadow=False)
    text(im, (340, 515), "戦後80年", F(SERIF, 150), stroke=9, gold=True, glow=(255, 200, 90))
    text(im, (340, 640), "雅子さまの願いとは…", F(SERIF, 58), stroke=7)
    credit(im, (1268, 712), ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(御所)", CR_Q], 13)
    return im

# ---------- B 競合の型: 上に黄色の「」、写真2枚、下に水色とピンク ----------
def panel(im, src, crop, box):
    x0, y0, x1, y1 = box; ph = Image.open(SRC + src).convert("RGB").crop(crop).resize((x1 - x0, y1 - y0), Image.LANCZOS)
    W, H = im.size; sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rectangle((x0 + 4, y0 + 8, x1 + 4, y1 + 8), fill=220)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.putalpha(sh.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(lay)
    im.paste(ph, (x0, y0)); ImageDraw.Draw(im).rectangle(box, outline=(255, 255, 255), width=4)
    ImageDraw.Draw(im).rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), outline=(222, 186, 104), width=2)

def long_B():
    W, H = 1280, 720; im = bg("B_light", W, H)
    YEL = (255, 225, 60); BLUE = (96, 214, 255); PINK = (255, 120, 180)
    text(im, (640, 66), "「" + QUOTE + "」", fit("「" + QUOTE + "」", SANS, 84, 1220), fill=YEL, stroke=8, stroke_fill=(0, 0, 0))
    text(im, (1250, 122), "皇后陛下 令和7年のご感想より", F(SANSB, 16), anchor="rm", stroke=3, stroke_fill=(0, 0, 0), shadow=False)
    # 左: 雅子さま(A061 お顔〜胸元) 右: 両陛下(A060)  ※A060はお二人の上半身を中心に
    panel(im, "A061.jpg", (0, 40, 666, 459), (36, 140, 628, 513))
    panel(im, "A060.jpg", (110, 230, 610, 570), (652, 140, 1244, 513))
    credit(im, (620, 507), ["宮内庁 令和7年 皇后陛下お誕生日のご近影"], 13)
    credit(im, (1236, 507), ["宮内庁 令和7年 皇后陛下お誕生日のご近影(御所)"], 13)
    text(im, (640, 580), "雅子さま 63歳のお誕生日", fit("雅子さま 63歳のお誕生日", SANS, 74, 1200), fill=BLUE, stroke=9, stroke_fill=(0, 0, 0))
    text(im, (640, 670), "戦後80年に綴られた想いとは…", fit("戦後80年に綴られた想いとは…", SANS, 78, 1220), fill=PINK, stroke=9, stroke_fill=(0, 0, 0))
    return im

# ---------- ショートのカバー 1080x1920 ----------
def short():
    W, H = 1080, 1920; im = bg("S_frame_portrait", W, H)
    p = person("A061", 1500, 0.78); place(im, p, 540, 600)
    vgrad(im, 1320, 1700, a1=235); vgrad(im, 520, 380, a1=0)
    logo(im, (540, 150), 34)
    text(im, (540, 245), "12月9日 63歳のお誕生日", F(SERIF, 52), stroke=6, gold=True, shadow=False)
    plaque(im, (110, 300, 970, 560), 22)
    q = F(SERIF, 92)
    text(im, (540, 380), "「あと20年で", q, fill=NAVY, stroke=0, shadow=False)
    text(im, (540, 485), "100年もの月日が」", q, fill=NAVY, stroke=0, shadow=False)
    text(im, (540, 590), "皇后陛下 令和7年のご感想より", F(SANSB, 26), fill=(240, 220, 160), stroke=3, shadow=False)
    text(im, (540, 1450), "戦後80年", F(SERIF, 210), stroke=11, gold=True, glow=(255, 200, 90))
    text(im, (540, 1640), "雅子さまの願いとは…", F(SERIF, 92), stroke=9)
    credit(im, (1040, 1880), ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(御所)", CR_Q], 22)
    return im

if __name__ == "__main__":
    for name, fn in [("long_A1_frame", long_A1), ("long_A2_goldscreen", long_A2), ("long_B_rival", long_B), ("short_cover", short)]:
        fn().convert("RGB").save(f"{name}.png"); print(name)
