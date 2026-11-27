"""表紙サンプル v4: 黒の帯をやめた3案(A 写真全面+文字直乗せ / B 白基調 / C 濃紺と金)。長尺とショート。
文字は宮内庁の原文の「」・状況・結末を伏せる1行。怒り/汗マーク・矢印・赤丸・作り台詞なし。写真は宮内庁 令和7年 皇后陛下お誕生日のご近影(切り抜き・拡大縮小のみ)。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
YEL, WHITE, RED, NAVY, GOLD, INK = (255, 230, 0), (255, 255, 255), (205, 15, 25), (22, 36, 58), (216, 188, 114), (25, 25, 25)
F = lambda p, s: ImageFont.truetype(p, s, index=0)
Q = "「あと20年で100年もの月日が」"; S1 = "12月9日 63歳を迎えられる雅子さま"; S2 = "昨年のご感想に綴られた想いとは…"
CAP = "写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影/「」は令和7年のご感想より"

def fit(d, t, p, s, w):
    while s > 20 and d.textlength(t, font=F(p, s)) > w: s -= 2
    return F(p, s)

def crop(name, cx, cy, frac, w, h):
    im = Image.open(os.path.join(A, name)).convert("RGB"); sw, sh = im.size
    ch = sh * frac; cw = ch * w / h
    if cw > sw: cw = sw; ch = cw * h / w
    l = max(0, min(sw - cw, cx * sw - cw / 2)); t = max(0, min(sh - ch, cy * sh - ch / 2))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((w, h), Image.LANCZOS)

def grad(im, y0, y1, alpha_max=200, up=False):
    W, H = im.size; g = Image.new("L", (1, y1 - y0))
    for i in range(y1 - y0): g.putpixel((0, i), int(alpha_max * ((i / (y1 - y0)) if not up else 1 - i / (y1 - y0))))
    g = g.resize((W, y1 - y0)); black = Image.new("RGB", (W, y1 - y0), (0, 0, 0))
    region = im.crop((0, y0, W, y1)); im.paste(Image.composite(black, region, g), (0, y0))

def t(d, xy, s, f, fill, sw=7, sf=(0, 0, 0), anchor="mm"): d.text(xy, s, font=f, fill=fill, stroke_width=sw, stroke_fill=sf, anchor=anchor)

# ---- 長尺 1280×720 ----
def long_A(out):  # 写真全面(2枚つなぎ)+文字直乗せ
    W, H = 1280, 720; im = Image.new("RGB", (W, H))
    im.paste(crop("A061.jpg", 0.54, 0.30, 0.55, 560, 720), (0, 0)); im.paste(crop("A064.jpg", 0.55, 0.43, 0.62, 720, 720), (560, 0))
    grad(im, 0, 200, 170, up=True); grad(im, 430, 720, 230); d = ImageDraw.Draw(im)
    t(d, (W / 2, 70), Q, fit(d, Q, BLACK, 80, W * 0.96), YEL, 8)
    t(d, (W / 2, 560), S1, fit(d, S1, BLACK, 60, W * 0.92), WHITE, 7)
    d.rounded_rectangle((40, 610, W - 40, 700), 14, fill=RED); t(d, (W / 2, 655), S2, fit(d, S2, BLACK, 74, W * 0.9), WHITE, 5)
    d.text((W - 8, 604), CAP, font=F(BOLD, 13), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0)); im.save(out, quality=95)

def long_B(out):  # 白基調・写真を大きく右に、左に文字(上品)
    W, H = 1280, 720; im = Image.new("RGB", (W, H), (250, 248, 243)); d = ImageDraw.Draw(im)
    im.paste(crop("A064.jpg", 0.55, 0.43, 0.60, 700, 720), (580, 0))
    d.rectangle((0, 0, 14, H), fill=GOLD)
    for i, line in enumerate(["「あと20年で", "100年もの", "月日が」"]): t(d, (300, 120 + i * 105), line, F(BLACK, 92), INK, 0)
    d.line((60, 430, 540, 430), fill=GOLD, width=4)
    t(d, (300, 490), "63歳を迎えられる雅子さま", fit(d, "63歳を迎えられる雅子さま", BLACK, 44, 500), NAVY, 0)
    d.rectangle((40, 545, 560, 640), fill=RED); t(d, (300, 592), "ご感想の想いとは…", F(BLACK, 58), WHITE, 0)
    d.text((W - 8, H - 6), CAP, font=F(BOLD, 13), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0)); im.save(out, quality=95)

def long_C(out):  # 濃紺と金(チャンネルの色)・写真2枚+金の文字
    W, H = 1280, 720; im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    im.paste(crop("A061.jpg", 0.54, 0.30, 0.50, 420, 470), (60, 120)); im.paste(crop("A064.jpg", 0.55, 0.43, 0.55, 700, 470), (520, 120))
    for x0, x1 in ((60, 480), (520, 1220)): d.rectangle((x0 - 3, 117, x1 + 3, 593), outline=GOLD, width=3)
    t(d, (W / 2, 62), Q, fit(d, Q, BLACK, 74, W * 0.94), GOLD, 4, NAVY)
    t(d, (W / 2, 640), S2, fit(d, S2, BLACK, 70, W * 0.94), WHITE, 0)
    d.text((W - 60, 590), CAP, font=F(BOLD, 13), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0)); im.save(out, quality=95)

# ---- ショート 1080×1920(縦の写真を全面に) ----
def short_A(out):
    W, H = 1080, 1920; im = crop("A061.jpg", 0.52, 0.36, 0.80, W, H); grad(im, 0, 430, 200, up=True); grad(im, 1100, 1920, 235); d = ImageDraw.Draw(im)
    for i, line in enumerate(["「あと20年で", "100年もの月日が」"]): t(d, (W / 2, 150 + i * 140), line, fit(d, line, BLACK, 128, W * 0.95), YEL, 10)
    t(d, (W / 2, 1330), "12月9日 63歳を迎えられる", fit(d, "12月9日 63歳を迎えられる", BLACK, 76, W * 0.92), WHITE, 8)
    t(d, (W / 2, 1440), "雅子さま", F(BLACK, 110), WHITE, 10)
    d.rounded_rectangle((40, 1530, W - 40, 1660), 18, fill=RED); t(d, (W / 2, 1595), "ご感想に綴られた想いとは…", fit(d, "ご感想に綴られた想いとは…", BLACK, 76, W * 0.86), WHITE, 5)
    d.text((W - 12, 1708), CAP, font=F(BOLD, 18), fill=WHITE, anchor="rt", stroke_width=2, stroke_fill=(0, 0, 0)); im.save(out, quality=95)

def short_B(out):
    W, H = 1080, 1920; im = Image.new("RGB", (W, H), (250, 248, 243)); d = ImageDraw.Draw(im)
    im.paste(crop("A061.jpg", 0.52, 0.36, 0.78, W, 1150), (0, 0))
    d.rectangle((0, 1150, W, 1160), fill=GOLD)
    t(d, (W / 2, 1270), "「あと20年で100年もの月日が」", fit(d, "「あと20年で100年もの月日が」", BLACK, 100, W * 0.96), INK, 0)
    t(d, (W / 2, 1395), "63歳を迎えられる雅子さま", fit(d, "63歳を迎えられる雅子さま", BLACK, 84, W * 0.92), NAVY, 0)
    d.rectangle((40, 1470, W - 40, 1610), fill=RED); t(d, (W / 2, 1540), "ご感想に綴られた想いとは…", fit(d, "ご感想に綴られた想いとは…", BLACK, 86, W * 0.88), WHITE, 0)
    d.text((W - 12, 1140), CAP, font=F(BOLD, 18), fill=WHITE, anchor="rb", stroke_width=2, stroke_fill=(0, 0, 0)); im.save(out, quality=95)

def short_C(out):
    W, H = 1080, 1920; im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    im.paste(crop("A061.jpg", 0.54, 0.38, 0.80, 960, 1100), (60, 330)); d.rectangle((57, 327, 1023, 1433), outline=GOLD, width=4)
    for i, line in enumerate(["「あと20年で", "100年もの月日が」"]): t(d, (W / 2, 120 + i * 105), line, fit(d, line, BLACK, 100, W * 0.92), GOLD, 4, NAVY)
    t(d, (W / 2, 1520), "63歳を迎えられる雅子さま", fit(d, "63歳を迎えられる雅子さま", BLACK, 72, W * 0.9), WHITE, 0)
    t(d, (W / 2, 1630), "ご感想に綴られた想いとは…", fit(d, "ご感想に綴られた想いとは…", BLACK, 76, W * 0.92), YEL, 0)
    d.text((1020, 1440), CAP, font=F(BOLD, 18), fill=WHITE, anchor="rt"); im.save(out, quality=95)

for fn in (long_A, long_B, long_C, short_A, short_B, short_C): fn(os.path.join(D, f"sample_v4_{fn.__name__}.png"))
# 並べた確認画像
L = [Image.open(os.path.join(D, f"sample_v4_long_{k}.png")).resize((640, 360)) for k in "ABC"]
Sx = [Image.open(os.path.join(D, f"sample_v4_short_{k}.png")).resize((300, 533)) for k in "ABC"]
sheet = Image.new("RGB", (1940, 360 + 533 + 30), (255, 255, 255))
for i, im in enumerate(L): sheet.paste(im, (i * 650, 0))
for i, im in enumerate(Sx): sheet.paste(im, (i * 650 + 170, 390))
sheet.save(os.path.join(D, "sample_v4_overview.jpg"), quality=90); print("ok")
