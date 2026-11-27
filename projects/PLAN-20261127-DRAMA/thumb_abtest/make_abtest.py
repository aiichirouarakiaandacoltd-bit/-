"""ABテスト用サンプル: 長尺3枚(A 額縁・格調型/B 顔の寄り+文字面/C 競合の3段型)+ショートのカバー1枚。
題材: 雅子さま 63歳のお誕生日(12/9)・令和7年のご感想(戦後80年)。「」と「後世に伝える」は宮内庁の原文(empress2025)。
決まり: 文字はお顔・頭に掛けない/菊の御紋・怒り汗マーク・矢印・赤丸・作り台詞・対立の構図なし/赤は使わない(帯はラズベリー)/写真は宮内庁の令和7年ご近影を切り抜き・拡大縮小のみ。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"; SANS = "/home/user/-/templates/fonts/NotoSansJP-Black.ttf"; SANSB = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"
def F(p, s): return ImageFont.truetype(p, s, index=0) if p.endswith(".ttc") else ImageFont.truetype(p, s)
NAVY1, NAVY2 = (10, 20, 44), (30, 48, 92); G1, G2, G3 = (255, 242, 180), (222, 172, 52), (150, 105, 25)
WHITE, YEL, SKY, PINK, BERRY1, BERRY2 = (255, 255, 255), (255, 236, 40), (160, 222, 255), (255, 150, 190), (217, 43, 94), (232, 69, 122)
CAP = "写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影/「」は令和7年のご感想より"
Q = "「あと20年で100年もの月日が」"

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

def fade_paste(base, img, xy, left=0, right=0, bottom=0):
    w, h = img.size; m = Image.new("L", (w, h), 255); d = ImageDraw.Draw(m)
    for i in range(left): d.line((i, 0, i, h), fill=int(255 * i / left))
    for i in range(right): d.line((w - 1 - i, 0, w - 1 - i, h), fill=int(255 * i / right))
    if bottom:
        mb = Image.new("L", (w, h), 255); db = ImageDraw.Draw(mb)
        for i in range(bottom): db.line((0, h - 1 - i, w, h - 1 - i), fill=int(255 * i / bottom))
        from PIL import ImageChops; m = ImageChops.multiply(m, mb)
    base.paste(img, xy, m)

def fit(t, p, s, w):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while s > 18 and d.textlength(t, font=F(p, s)) > w: s -= 2
    return F(p, s)

def text(im, xy, s, f, fill=WHITE, gold=False, anchor="mm", sw=3, shadow=True, stroke=(10, 14, 28)):
    W, H = im.size
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 5), s, font=f, fill=(0, 0, 0, 210), anchor=anchor, stroke_width=sw + 3, stroke_fill=(0, 0, 0, 210))
        b = sh.filter(ImageFilter.GaussianBlur(8)); im.paste(b, (0, 0), b)
    d = ImageDraw.Draw(im); d.text(xy, s, font=f, fill=stroke, anchor=anchor, stroke_width=sw, stroke_fill=stroke)
    if gold:
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor); bb = m.getbbox()
        g = Image.new("RGB", (W, H)); hh = bb[3] - bb[1]
        g.paste(vgrad((W, hh // 2 + 1), G1, G2), (0, bb[1])); g.paste(vgrad((W, hh - hh // 2), G2, G3), (0, bb[1] + hh // 2)); im.paste(g, (0, 0), m)
    else:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)

def plate(im, box, s, f, dark=True):
    x0, y0, x1, y1 = box; g = vgrad((x1 - x0, y1 - y0), (252, 232, 150), (190, 140, 40))
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.size[0] - 1, g.size[1] - 1), 10, fill=255)
    im.paste(g, (x0, y0), m); d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), 8, outline=(120, 80, 20), width=2)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), s, font=f, fill=NAVY1, anchor="mm")

def frame(im):
    W, H = im.size; d = ImageDraw.Draw(im)
    d.rectangle((8, 8, W - 9, H - 9), outline=G2, width=4); d.rectangle((18, 18, W - 19, H - 19), outline=G3, width=1)
    for (x, y, sx, sy) in ((18, 18, 1, 1), (W - 19, 18, -1, 1), (18, H - 19, 1, -1), (W - 19, H - 19, -1, -1)):  # 角の金の飾り(紋章ではない幾何の飾り)
        d.line((x, y + sy * 70, x + sx * 70, y), fill=G1, width=3); d.line((x, y + sy * 46, x + sx * 46, y), fill=G2, width=2)
        d.ellipse((x + sx * 26 - 6, y + sy * 26 - 6, x + sx * 26 + 6, y + sy * 26 + 6), fill=G2)

def cap(im, xy, anchor="rb", size=13): ImageDraw.Draw(im).text(xy, CAP, font=F(SANSB, size), fill=(230, 230, 230), anchor=anchor, stroke_width=2, stroke_fill=(0, 0, 0))

# A 額縁・格調型
def long_A(out):
    W, H = 1280, 720; im = vgrad((W, H), NAVY2, NAVY1)
    fade_paste(im, crop("A061.jpg", 0.52, 0.30, 0.55, 380, 690), (14, 18), right=120)
    fade_paste(im, crop("A060.jpg", 0.40, 0.36, 0.46, 400, 690), (W - 414, 18), left=140)
    frame(im); d = ImageDraw.Draw(im)
    plate(im, (430, 34, 850, 92), "日本が誇る皇室物語", F(SANS, 34))
    d.line((300, 63, 420, 63), fill=G2, width=2); d.line((860, 63, 980, 63), fill=G2, width=2)
    plate(im, (360, 120, 920, 290), "", F(SANS, 10))
    text(im, (640, 172), "戦後80年の年に", F(SERIF, 54), fill=NAVY1, shadow=False, sw=0, stroke=NAVY1)
    text(im, (640, 240), "綴られた想いとは？", F(SERIF, 54), fill=NAVY1, shadow=False, sw=0, stroke=NAVY1)
    text(im, (640, 400), "雅子さま63歳のお誕生日", fit("雅子さま63歳のお誕生日", SERIF, 76, 760), WHITE)
    text(im, (640, 545), "後世に伝えていく", fit("後世に伝えていく", SERIF, 130, 780), gold=True, sw=4)
    text(im, (640, 650), "令和7年のご感想より", F(SANS, 34), fill=G1, sw=3)
    cap(im, (W - 28, H - 26)); im.save(out, quality=95)

# B 顔の寄り+文字面
def long_B(out):
    W, H = 1280, 720; im = vgrad((W, H), NAVY2, NAVY1)
    fade_paste(im, crop("A061.jpg", 0.52, 0.27, 0.42, 520, 720), (0, 0), right=140)
    d = ImageDraw.Draw(im)
    plate(im, (500, 30, 1240, 100), "日本が誇る皇室物語", F(SANS, 42))
    text(im, (880, 185), "12月9日 63歳を迎えられる", fit("12月9日 63歳を迎えられる", SANS, 56, 720))
    text(im, (880, 285), "雅子さまのご感想", fit("雅子さまのご感想", SERIF, 92, 720), gold=True)
    d.rounded_rectangle((560, 340, 1200, 350), 5, fill=BERRY1)
    text(im, (880, 450), "「あと20年で", F(SERIF, 88))
    text(im, (880, 570), "100年もの月日が」", fit("100年もの月日が」", SERIF, 88, 740), gold=True)
    text(im, (880, 660), "戦後80年に綴られた想いとは…", fit("戦後80年に綴られた想いとは…", SANS, 40, 720), fill=SKY)
    d.line((0, 712, W, 712), fill=G2, width=6); cap(im, (W - 10, H - 14)); im.save(out, quality=95)

# C 競合の3段型(黄の「」/写真2枚/水色とピンク)
def long_C(out):
    W, H = 1280, 720; im = vgrad((W, H), (20, 36, 70), (45, 66, 110))
    im.paste(crop("A061.jpg", 0.52, 0.29, 0.50, 600, 350), (0, 112)); im.paste(crop("A064.jpg", 0.55, 0.43, 0.52, 620, 350), (660, 112))
    text(im, (W / 2, 60), Q, fit(Q, SANS, 82, W * 0.95), fill=YEL, sw=8, stroke=(15, 15, 20))
    text(im, (W / 2, 535), "雅子さまが昨年のご感想に", fit("雅子さまが昨年のご感想に", SANS, 84, W * 0.95), fill=SKY, sw=8, stroke=(15, 15, 20))
    text(im, (W / 2, 640), "綴られた戦後80年の想いとは？", fit("綴られた戦後80年の想いとは？", SANS, 84, W * 0.95), fill=PINK, sw=8, stroke=(15, 15, 20))
    cap(im, (W - 8, 466), anchor="rt"); im.save(out, quality=95)

# ショートのカバー: 写真全面+額縁の金+明朝の金文字+ラズベリーの帯
def short_cover(out):
    W, H = 1080, 1920; im = crop("A061.jpg", 0.52, 0.36, 0.80, W, H)
    shade = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = int(200 * max(0, (430 - y) / 430) ** 1.2) if y < 430 else int(235 * max(0, (y - 1080) / 840) ** 1.1) if y > 1080 else 0
        sd.line((0, y, W, y), fill=a)
    im.paste(Image.new("RGB", (W, H), NAVY1), (0, 0), shade); frame(im)
    plate(im, (290, 60, 790, 130), "日本が誇る皇室物語", F(SANS, 40))
    text(im, (W / 2, 235), "「あと20年で", F(SERIF, 120), gold=True); text(im, (W / 2, 375), "100年もの月日が」", fit("100年もの月日が」", SERIF, 120, W * 0.9), gold=True)
    text(im, (W / 2, 1330), "12月9日 63歳を迎えられる", fit("12月9日 63歳を迎えられる", SANS, 72, W * 0.86))
    text(im, (W / 2, 1450), "雅子さま", F(SERIF, 124), gold=True)
    x0, y0, x1, y1 = 80, 1540, W - 80, 1670; g = Image.new("RGB", (x1 - x0, y1 - y0)); gd = ImageDraw.Draw(g)
    for x in range(x1 - x0): gd.line((x, 0, x, y1 - y0), fill=tuple(int(BERRY1[k] + (BERRY2[k] - BERRY1[k]) * x / (x1 - x0)) for k in range(3)))
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.size[0] - 1, g.size[1] - 1), 18, fill=255); im.paste(g, (x0, y0), m)
    ImageDraw.Draw(im).text((W / 2, (y0 + y1) / 2), "戦後80年に綴られた想いとは…", font=fit("戦後80年に綴られた想いとは…", SANS, 66, W * 0.76), fill=WHITE, anchor="mm")
    cap(im, (W - 30, 1715), anchor="rt", size=18); im.save(out, quality=95)

for fn in (long_A, long_B, long_C, short_cover): fn(os.path.join(D, f"{fn.__name__}.png"))
L = [Image.open(os.path.join(D, f"long_{k}.png")).resize((640, 360)) for k in "ABC"]; S = Image.open(os.path.join(D, "short_cover.png")).resize((405, 720))
ov = Image.new("RGB", (1300 + 420, 740), (255, 255, 255))
ov.paste(L[0], (0, 0)); ov.paste(L[1], (650, 0)); ov.paste(L[2], (0, 375)); ov.paste(S, (1300, 0))
ImageDraw.Draw(ov).text((960, 550), "A 額縁・格調型 / B 顔+文字面 / C 競合の3段型\n右: ショートのカバー", font=F(SANSB, 22), fill=(30, 30, 30), anchor="mm", align="center")
ov.save(os.path.join(D, "overview.jpg"), quality=90); print("ok")
