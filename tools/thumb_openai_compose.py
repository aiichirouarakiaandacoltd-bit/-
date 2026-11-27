"""表紙(サムネイル)の組み立て: AI(gpt-image)で作った背景・額縁・金の札 + 宮内庁の写真の切り抜き + 文字。

- AI で作るのは背景・額縁・金の飾り・光だけ(tools/thumb_openai_gen.py)。
- 皇族方のお姿は宮内庁の写真を切り抜いたもの(加工は拡大縮小と切り抜きのみ)。
- 出力先 projects/<P>/thumb_openai/ は .gitignore で除外(写真入りの画像は保管庫に入れない)。

使い方:
  python tools/thumb_openai_compose.py --work <作業フォルダ> --out <出力フォルダ>
  作業フォルダには ai/bg_A.png bg_B.png bg_S.png plaque.png と cut/A060.png A061.png A062.png A063.jpg(元写真) A066.png を置く。
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
NAVY = (22, 36, 58)
QUOTE = "「あと20年で100年もの月日が」"  # 宮内庁 令和7年 皇后陛下お誕生日に際してのご感想 原文どおり
SRC_Q = "「」内は 令和7年 皇后陛下お誕生日に際してのご感想より(宮内庁)"


def font(path, size):
    return ImageFont.truetype(path, size, index=0)


def fit_cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def text_size(txt, f, stroke=0):
    b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), txt, font=f, stroke_width=stroke)
    return b[2] - b[0], b[3] - b[1], b


def gold_fill(w, h):
    """上から 明るい金 → 濃い金 → 明るい金 の縦グラデーション。"""
    stops = [(0.0, (255, 246, 205)), (0.38, (236, 199, 104)), (0.62, (182, 128, 42)), (0.82, (232, 192, 98)), (1.0, (255, 236, 170))]
    ys = np.linspace(0, 1, h)
    col = np.zeros((h, 3))
    for c in range(3):
        col[:, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
    return Image.fromarray(np.repeat(col[:, None, :], w, axis=1).astype(np.uint8), "RGB")


def draw_text(canvas, xy, txt, f, fill="gold", stroke=0, stroke_fill=(20, 14, 6), shadow=True, anchor="mm", glow=None):
    """文字を描く。fill="gold" で金のグラデーション。anchor は中心(mm)か左上(la)。"""
    tw, th, b = text_size(txt, f, stroke)
    pad = stroke + 30
    W, H = tw + pad * 2, th + pad * 2
    ox, oy = pad - b[0], pad - b[1]
    m_fill = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m_fill).text((ox, oy), txt, font=f, fill=255)
    m_all = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m_all).text((ox, oy), txt, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", (W, H), glow + (0,))
        g.putalpha(m_all.filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, int(v * 1.2))))
        layer = Image.alpha_composite(layer, g)
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sa = m_all.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.75))
        sh.paste((0, 0, 0, 255), (4, 6), sa)
        layer = Image.alpha_composite(layer, sh)
    if stroke:
        st = Image.new("RGBA", (W, H), stroke_fill + (0,))
        st.putalpha(m_all)
        layer = Image.alpha_composite(layer, st)
    if fill == "gold":
        fl = gold_fill(W, H).convert("RGBA")
    else:
        fl = Image.new("RGBA", (W, H), fill + (255,))
    fl.putalpha(m_fill)
    layer = Image.alpha_composite(layer, fl)
    x, y = xy
    if anchor == "mm":
        x, y = x - W // 2, y - H // 2
    else:
        x, y = x - pad, y - pad
    canvas.alpha_composite(layer, (int(x), int(y)))
    return (x + pad, y + pad, x + pad + tw, y + pad + th)


def person(canvas, cut, scale, x, y, rim=(255, 214, 140)):
    """切り抜きを置く。後ろに金の柔らかい光(加工はお姿ではなく背景側のみ)。"""
    a = np.array(cut)[:, :, 3]
    ys, xs = np.where(a > 128)
    cut = cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    cut = cut.resize((round(cut.width * scale), round(cut.height * scale)), Image.LANCZOS)
    P = 90
    ga = Image.new("L", (cut.width + P * 2, cut.height + P * 2), 0)
    ga.paste(cut.getchannel("A"), (P, P))
    glow = Image.new("RGBA", ga.size, rim + (0,))
    glow.putalpha(ga.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.55)))
    canvas.alpha_composite(glow, (x - P, y - P))
    canvas.alpha_composite(cut, (x, y))
    return (x, y, x + cut.width, y + cut.height)


def vgrad(canvas, y0, y1, color, a0, a1):
    w = canvas.width
    h = y1 - y0
    al = np.linspace(a0, a1, h)[:, None].repeat(w, axis=1).astype(np.uint8)
    g = Image.new("RGBA", (w, h), color + (0,))
    g.putalpha(Image.fromarray(al, "L"))
    canvas.alpha_composite(g, (0, y0))


def credit(canvas, lines, xy, size=15, anchor="rb"):
    f = font(SANS_B, size)
    d = ImageDraw.Draw(canvas)
    x, y = xy
    for i, ln in enumerate(reversed(lines)):
        d.text((x, y - i * (size + 5)), ln, font=f, fill=(235, 235, 235), anchor=anchor, stroke_width=2, stroke_fill=(10, 14, 24))


def plaque_img(work, width):
    p = Image.open(os.path.join(work, "ai/plaque.png")).convert("RGBA")
    a = np.array(p)[:, :, 3]
    ys, xs = np.where(a > 200)
    p = p.crop((xs.min() - 30, ys.min() - 30, xs.max() + 31, ys.max() + 31))
    s = width / p.width
    return p.resize((width, round(p.height * s)), Image.LANCZOS)


def gold_frame_mask(work, size):
    """AI の額縁(bg_A)から、縁の金の線だけを取り出す。"""
    bg = fit_cover(Image.open(os.path.join(work, "ai/bg_A.png")).convert("RGB"), *size)
    arr = np.array(bg).astype(int)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    gold = ((r - b) > 45) & (r > 110)
    edge = np.zeros(gold.shape, bool)
    m = int(min(size) * 0.13)
    edge[:m, :] = edge[-m:, :] = True
    edge[:, :m] = edge[:, -m:] = True
    al = (gold & edge).astype(np.uint8) * 255
    frame = bg.convert("RGBA")
    frame.putalpha(Image.fromarray(al, "L").filter(ImageFilter.GaussianBlur(0.6)))
    return frame


# ---------------- 長尺 A: 濃紺と金の額縁・左右に人物・中央に金の札 ----------------
def long_A(work, out):
    W, H = 1280, 720
    c = fit_cover(Image.open(os.path.join(work, "ai/bg_A.png")).convert("RGB"), W, H).convert("RGBA")
    masako = Image.open(os.path.join(work, "cut/A061.png"))
    emp = Image.open(os.path.join(work, "cut/A066.png"))
    pm = person(c, masako, 0.93, 34, 70)
    pe = person(c, emp, 0.665, 892, 74)
    draw_text(c, (640, 92), "雅子さま 63歳のお誕生日へ", font(SERIF, 36), fill=(255, 255, 255), stroke=0)
    pl = plaque_img(work, 600)
    c.alpha_composite(pl, (640 - pl.width // 2, 128))
    draw_text(c, (640, 128 + pl.height // 2 + 1), QUOTE, font(SERIF, 33), fill=(255, 255, 255), shadow=False)
    draw_text(c, (640, 128 + pl.height + 110), "戦後80年", font(SERIF, 158), fill="gold", stroke=6,
              stroke_fill=(40, 26, 6), glow=(255, 200, 90))
    draw_text(c, (640, 128 + pl.height + 228), "その先に願われたこととは…", font(SERIF, 40), fill=(255, 255, 255), stroke=4,
              stroke_fill=NAVY)
    credit(c, ["写真:宮内庁 令和7年 皇后陛下・天皇陛下お誕生日に際してのご近影(切り抜き)", SRC_Q], (W - 46, H - 30), 13)
    c.convert("RGB").save(out)
    return {"masako": pm, "emperor": pe}


# ---------------- 長尺 B: 光の中のお二人・左に特大の金文字 ----------------
def long_B(work, out):
    W, H = 1280, 720
    c = fit_cover(Image.open(os.path.join(work, "ai/bg_B.png")).convert("RGB"), W, H).convert("RGBA")
    couple = Image.open(os.path.join(work, "cut/A062.png"))
    pc = person(c, couple, 1.12, 612, 58)
    x0 = 64
    draw_text(c, (x0, 70), "令和7年 お誕生日のご感想", font(SERIF, 30), fill=(240, 226, 190), anchor="la", shadow=True)
    d = ImageDraw.Draw(c)
    d.line((x0, 124, x0 + 360, 124), fill=(216, 188, 114), width=2)
    draw_text(c, (x0, 148), "雅子さま", font(SERIF, 92), fill=(255, 255, 255), anchor="la", stroke=4, stroke_fill=NAVY)
    draw_text(c, (x0 - 6, 262), "63歳", font(SERIF, 228), fill="gold", anchor="la", stroke=7, stroke_fill=(40, 26, 6),
              glow=(255, 200, 90))
    draw_text(c, (x0, 532), "戦後80年に", font(SERIF, 62), fill=(255, 255, 255), anchor="la", stroke=4, stroke_fill=NAVY)
    draw_text(c, (x0, 612), "心に刻まれた願い…", font(SERIF, 62), fill=(255, 236, 170), anchor="la", stroke=4,
              stroke_fill=NAVY)
    credit(c, ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(切り抜き)"], (W - 24, H - 16), 13)
    c.convert("RGB").save(out)
    return {"couple": pc}


# ---------------- 長尺 C: 競合の型(上に黄色の「」・写真2枚・下に水色とピンクの2行) ----------------
def long_C(work, out, photos_dir):
    W, H = 1280, 720
    c = Image.new("RGBA", (W, H), NAVY + (255,))
    left = Image.open(os.path.join(photos_dir, "A060.jpg")).convert("RGB")
    s = 1.30
    left = left.resize((round(left.width * s), round(left.height * s)), Image.LANCZOS)
    cx = int(342 * s)
    left = left.crop((cx - 320, 150, cx + 320, 150 + H))
    right = Image.open(os.path.join(photos_dir, "A063.jpg")).convert("RGB")
    s = 1.45
    right = right.resize((round(right.width * s), round(right.height * s)), Image.LANCZOS)
    cx = int(505 * s)
    right = right.crop((cx - 320, 140, cx + 320, 140 + H))
    c.paste(left, (0, 0))
    c.paste(right, (640, 0))
    vgrad(c, 0, 200, (10, 18, 34), 215, 0)
    vgrad(c, 430, 720, (10, 18, 34), 0, 235)
    # 真ん中の金の仕切り(光)
    line = Image.new("RGBA", (40, H), (0, 0, 0, 0))
    ImageDraw.Draw(line).rectangle((18, 0, 21, H), fill=(240, 205, 120, 255))
    glow = line.filter(ImageFilter.GaussianBlur(8))
    c.alpha_composite(glow, (620, 0))
    c.alpha_composite(line, (620, 0))
    c.alpha_composite(gold_frame_mask(work, (W, H)))
    draw_text(c, (640, 78), QUOTE, font(SANS, 70), fill=(255, 225, 60), stroke=9, stroke_fill=(15, 15, 20))
    draw_text(c, (640, 520), "雅子さま 戦後80年のご感想", font(SANS, 72), fill=(120, 226, 255), stroke=9,
              stroke_fill=(15, 15, 20))
    t2 = "その先に願われたこととは…"
    f2 = font(SANS, 62)
    tw, th, _ = text_size(t2, f2)
    band = Image.new("RGBA", (tw + 70, th + 34), (0, 0, 0, 0))
    ImageDraw.Draw(band).rounded_rectangle((0, 0, band.width - 1, band.height - 1), radius=22, fill=(236, 72, 145, 255))
    bx, by = 640 - band.width // 2, 572
    c.alpha_composite(band, (bx, by))
    draw_text(c, (640, by + band.height // 2), t2, f2, fill=(255, 255, 255), stroke=0)
    credit(c, ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影", SRC_Q], (W - 44, H - 30), 12)
    c.convert("RGB").save(out)


# ---------------- ショート: 縦の額縁・雅子さまお一人 ----------------
def short(work, out):
    W, H = 1080, 1920
    c = fit_cover(Image.open(os.path.join(work, "ai/bg_S.png")).convert("RGB"), W, H).convert("RGBA")
    masako = Image.open(os.path.join(work, "cut/A061.png"))
    pm = person(c, masako, 2.55, 66, 735)
    vgrad(c, 1450, 1920, (10, 18, 34), 0, 200)
    draw_text(c, (540, 205), "雅子さま 63歳のお誕生日へ", font(SERIF, 66), fill=(255, 255, 255), stroke=4, stroke_fill=NAVY)
    pl = plaque_img(work, 960)
    c.alpha_composite(pl, (540 - pl.width // 2, 270))
    draw_text(c, (540, 270 + pl.height // 2 + 2), QUOTE, font(SERIF, 54), fill=(255, 255, 255), shadow=False)
    draw_text(c, (540, 270 + pl.height + 130), "戦後80年", font(SERIF, 196), fill="gold", stroke=7,
              stroke_fill=(40, 26, 6), glow=(255, 200, 90))
    draw_text(c, (540, 1700), "その先に願われたこととは…", font(SERIF, 70), fill=(255, 255, 255), stroke=6, stroke_fill=NAVY)
    credit(c, ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(切り抜き)", SRC_Q], (W - 60, H - 60), 20)
    c.convert("RGB").save(out)
    return {"masako": pm}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--photos", default="assets/KB-20261124-01")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print("A", long_A(a.work, os.path.join(a.out, "long_A_frame.png")))
    print("B", long_B(a.work, os.path.join(a.out, "long_B_glow.png")))
    long_C(a.work, os.path.join(a.out, "long_C_rival.png"), a.photos)
    print("S", short(a.work, os.path.join(a.out, "short_cover.png")))
