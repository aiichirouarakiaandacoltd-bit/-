"""表紙 v5(採用案Aを洗練): 書体を「明朝の極太(Noto Serif CJK JP Black)+ゴシック(Noto Sans JP Black)」の組み合わせに、
太い黒縁取りをやめて細い縁+やわらかい影に、帯は赤とピンクの間(ラズベリー #D92B5E→#E8457A のグラデーション)に。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"; SANS = "/home/user/-/templates/fonts/NotoSansJP-Black.ttf"; SANSB = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"
F = lambda p, s: ImageFont.truetype(p, s, index=0) if p.endswith(".ttc") else ImageFont.truetype(p, s)
GOLD1, GOLD2, WHITE = (255, 236, 150), (238, 184, 40), (255, 255, 255)
BAND1, BAND2 = (217, 43, 94), (232, 69, 122)
Q = "「あと20年で100年もの月日が」"; CAP = "写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影/「」は令和7年のご感想より"

def fit(t, p, s, w):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while s > 20 and d.textlength(t, font=F(p, s)) > w: s -= 2
    return F(p, s)

def crop(name, cx, cy, frac, w, h):
    im = Image.open(os.path.join(A, name)).convert("RGB"); sw, sh = im.size
    ch = sh * frac; cw = ch * w / h
    if cw > sw: cw = sw; ch = cw * h / w
    l = max(0, min(sw - cw, cx * sw - cw / 2)); t = max(0, min(sh - ch, cy * sh - ch / 2))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((w, h), Image.LANCZOS)

def shade(im, y0, y1, a, up=False):
    W, H = im.size; m = Image.new("L", (1, y1 - y0))
    for i in range(y1 - y0):
        r = i / (y1 - y0); m.putpixel((0, i), int(a * ((1 - r) if up else r) ** 1.3))
    im.paste(Image.composite(Image.new("RGB", (W, y1 - y0)), im.crop((0, y0, W, y1)), m.resize((W, y1 - y0))), (0, y0))

def styled(im, xy, text, f, fill=WHITE, gradient=None, outline=3, shadow=10):
    W, H = im.size
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 5), text, font=f, fill=(0, 0, 0, 200), anchor="mm", stroke_width=outline + 2, stroke_fill=(0, 0, 0, 200))
    im.paste(sh.filter(ImageFilter.GaussianBlur(shadow)), (0, 0), sh.filter(ImageFilter.GaussianBlur(shadow)))
    d = ImageDraw.Draw(im); d.text(xy, text, font=f, fill=(20, 20, 20), anchor="mm", stroke_width=outline, stroke_fill=(20, 20, 20))
    if gradient:
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text(xy, text, font=f, fill=255, anchor="mm")
        bb = mask.getbbox(); g = Image.new("RGB", (W, H))
        gd = ImageDraw.Draw(g)
        for y in range(bb[1], bb[3]):
            r = (y - bb[1]) / max(1, bb[3] - bb[1]); c = tuple(int(gradient[0][k] + (gradient[1][k] - gradient[0][k]) * r) for k in range(3)); gd.line((0, y, W, y), fill=c)
        im.paste(g, (0, 0), mask)
    else:
        d.text(xy, text, font=f, fill=fill, anchor="mm")

def band(im, box, text, f):
    x0, y0, x1, y1 = box; W, H = im.size
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 8, x1 + 4, y1 + 8), 18, fill=(0, 0, 0, 150))
    im.paste(sh.filter(ImageFilter.GaussianBlur(10)), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    g = Image.new("RGB", (x1 - x0, y1 - y0)); gd = ImageDraw.Draw(g)
    for x in range(x1 - x0):
        r = x / (x1 - x0); gd.line((x, 0, x, y1 - y0), fill=tuple(int(BAND1[k] + (BAND2[k] - BAND1[k]) * r) for k in range(3)))
    m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, g.size[0] - 1, g.size[1] - 1), 18, fill=255)
    im.paste(g, (x0, y0), m)
    ImageDraw.Draw(im).text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=f, fill=WHITE, anchor="mm")

def long(out):
    W, H = 1280, 720; im = Image.new("RGB", (W, H))
    im.paste(crop("A061.jpg", 0.54, 0.30, 0.55, 560, 720), (0, 0)); im.paste(crop("A064.jpg", 0.55, 0.43, 0.62, 720, 720), (560, 0))
    shade(im, 0, 210, 190, up=True); shade(im, 400, 720, 235)
    styled(im, (W / 2, 78), Q, fit(Q, SERIF, 84, W * 0.95), gradient=(GOLD1, GOLD2))
    styled(im, (W / 2, 548), "12月9日 63歳を迎えられる雅子さま", fit("12月9日 63歳を迎えられる雅子さま", SANS, 56, W * 0.86))
    band(im, (90, 600, W - 90, 690), "昨年のご感想に綴られた想いとは…", fit("昨年のご感想に綴られた想いとは…", SANS, 62, W * 0.78))
    ImageDraw.Draw(im).text((W - 8, H - 6), CAP, font=F(SANSB, 13), fill=(235, 235, 235), anchor="rb")
    im.save(out, quality=95)

def short(out):
    W, H = 1080, 1920; im = crop("A061.jpg", 0.52, 0.36, 0.80, W, H); shade(im, 0, 470, 200, up=True); shade(im, 1080, 1920, 240)
    for i, line in enumerate(["「あと20年で", "100年もの月日が」"]): styled(im, (W / 2, 150 + i * 145), line, fit(line, SERIF, 130, W * 0.93), gradient=(GOLD1, GOLD2))
    styled(im, (W / 2, 1340), "12月9日 63歳を迎えられる", fit("12月9日 63歳を迎えられる", SANS, 70, W * 0.88))
    styled(im, (W / 2, 1450), "雅子さま", F(SERIF, 120), gradient=(GOLD1, GOLD2))
    band(im, (70, 1540, W - 70, 1670), "ご感想に綴られた想いとは…", fit("ご感想に綴られた想いとは…", SANS, 72, W * 0.8))
    ImageDraw.Draw(im).text((W - 12, 1712), CAP, font=F(SANSB, 18), fill=(235, 235, 235), anchor="rt")
    im.save(out, quality=95)

long(os.path.join(D, "sample_v5_long.png")); short(os.path.join(D, "sample_v5_short.png"))
a = Image.open(os.path.join(D, "sample_v5_long.png")); b = Image.open(os.path.join(D, "sample_v5_short.png")).resize((405, 720))
s = Image.new("RGB", (1685, 720)); s.paste(a, (0, 0)); s.paste(b, (1280, 0)); s.save(os.path.join(D, "sample_v5_overview.jpg"), quality=90); print("ok")
