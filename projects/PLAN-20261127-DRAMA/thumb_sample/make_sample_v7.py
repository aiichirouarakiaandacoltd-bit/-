"""表紙 v7: みんなの皇室・それいけ皇室の「型」(上=黄の極太「」1行/中=写真2枚を左右/下=水色とピンクの極太2行・黒縁)に合わせる。
中身は事実だけ: 「」は宮内庁の原文、作られた台詞・「衝撃の仕打ち」等の対立語・赤い矢印・怒り/汗マークは使わない。文字はお顔に掛けない。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
D = os.path.dirname(__file__); A = os.path.join(D, "../../../assets/KB-20261124-01")
SANS = "/home/user/-/templates/fonts/NotoSansJP-Black.ttf"; SANSB = "/home/user/-/templates/fonts/NotoSansJP-Bold.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
YEL, SKY, PINK, WHITE = (255, 236, 40), (160, 222, 255), (255, 150, 190), (255, 255, 255)

def crop(name, cx, cy, frac, w, h):
    im = Image.open(os.path.join(A, name)).convert("RGB"); sw, sh = im.size
    ch = sh * frac; cw = ch * w / h
    if cw > sw: cw = sw; ch = cw * h / w
    l = max(0, min(sw - cw, cx * sw - cw / 2)); t = max(0, min(sh - ch, cy * sh - ch / 2))
    return im.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((w, h), Image.LANCZOS)

def fit(t, s, w):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while s > 20 and d.textlength(t, font=F(SANS, s)) > w: s -= 2
    return F(SANS, s)

def T(im, xy, s, f, fill, sw=8):
    W, H = im.size; sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 5), s, font=f, fill=(0, 0, 0, 200), anchor="mm", stroke_width=sw + 2, stroke_fill=(0, 0, 0, 200))
    b = sh.filter(ImageFilter.GaussianBlur(6)); im.paste(b, (0, 0), b)
    ImageDraw.Draw(im).text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=sw, stroke_fill=(15, 15, 20))

def long(out):
    W, H = 1280, 720
    bg = Image.new("RGB", (W, H)); d = ImageDraw.Draw(bg)
    for y in range(H): d.line((0, y, W, y), fill=(int(20 + 25 * y / H), int(36 + 30 * y / H), int(70 + 40 * y / H)))
    bg.paste(crop("A061.jpg", 0.52, 0.29, 0.50, 600, 350), (0, 112))       # 左 雅子さま(顔の寄り)
    bg.paste(crop("A064.jpg", 0.55, 0.43, 0.52, 620, 350), (660, 112))      # 右 両陛下
    T(bg, (W / 2, 62), "「あと20年で100年もの月日が」", fit("「あと20年で100年もの月日が」", 82, W * 0.95), YEL, 8)
    T(bg, (W / 2, 535), "雅子さまが昨年のご感想に", fit("雅子さまが昨年のご感想に", 84, W * 0.95), SKY, 8)
    T(bg, (W / 2, 640), "綴られた戦後80年の想いとは？", fit("綴られた戦後80年の想いとは？", 84, W * 0.95), PINK, 8)
    ImageDraw.Draw(bg).text((W - 8, 466), "写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影/「」は令和7年のご感想より", font=F(SANSB, 13), fill=(230, 230, 230), anchor="rt")
    bg.save(out, quality=95)

long(os.path.join(D, "sample_v7_long.png")); print("ok")
