"""新しい表紙の型(荒木承認 2026-11-27)のサンプル: P4 雅子さまのお誕生日。
黒背景・中央に写真・上下は黒帯/1行目 赤い帯に白文字の「」付きの一言(宮内庁の原文)/2行目 黄・3行目 白の太字+黒縁取り。
写真: 宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(御所にて) KB-20261124-01 A060。切り抜き・拡大縮小のみ。"""
from PIL import Image, ImageDraw, ImageFont
import os
D = os.path.dirname(__file__)
PHOTO = os.path.join(D, "../../../assets/KB-20261124-01/A060.jpg")
BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
RED, YEL, WHITE = (190, 20, 30), (255, 214, 0), (255, 255, 255)
L1 = "「あと20年で100年もの月日が」"
SRC = "令和7年 皇后陛下お誕生日のご感想より"
L2 = "12月9日 63歳のお誕生日"
L3 = "昨年のご感想をたどる"
CAP = "令和7年 皇后陛下お誕生日に際してのご近影(御所にて)/宮内庁"

def font(p, s): return ImageFont.truetype(p, s, index=0)

def fit(draw, text, path, size, maxw):
    while size > 20:
        f = font(path, size)
        if draw.textlength(text, font=f) <= maxw: return f
        size -= 2
    return font(path, size)

def outlined(draw, xy, text, f, fill, stroke):
    draw.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0), anchor="mm")

def make(W, H, out, photo_box, band_y, band_h, l1_size, l2_y, l3_y, l23_size):
    im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    # 写真: 両陛下の上半身を中心に切り抜き、写真枠いっぱいに
    src = Image.open(PHOTO).convert("RGB"); sw, sh = src.size
    x0, y0, x1, y1 = photo_box; bw, bh = x1 - x0, y1 - y0
    cx, cy = 0.52 * sw, 0.42 * sh  # お二人の上半身の中心
    scale = max(bw / sw, bh / (sh * 0.62))
    cw, ch = bw / scale, bh / scale
    l = max(0, min(sw - cw, cx - cw / 2)); t = max(0, min(sh - ch, cy - ch / 2))
    crop = src.crop((int(l), int(t), int(l + cw), int(t + ch))).resize((bw, bh), Image.LANCZOS)
    im.paste(crop, (x0, y0))
    # 写真の下の撮影情報(小さく右寄せ)
    fc = font(BOLD, max(14, W // 64)); d.text((x1 - 6, y1 - 6), CAP, font=fc, fill=WHITE, anchor="rd", stroke_width=2, stroke_fill=(0, 0, 0))
    # 1行目: 赤い帯に白文字
    d.rectangle((0, band_y, W, band_y + band_h), fill=RED)
    f1 = fit(d, L1, BLACK, l1_size, W * 0.92)
    d.text((W / 2, band_y + band_h / 2), L1, font=f1, fill=WHITE, anchor="mm")
    # 出典は赤帯の外(すぐ下の黒地)に小さく右寄せ
    fs = font(BOLD, max(14, W // 72)); d.text((W - 12, band_y + band_h + 3), SRC, font=fs, fill=WHITE, anchor="rt")
    # 2行目(黄)・3行目(白): 太字+黒縁取り
    f2 = fit(d, L2, BLACK, l23_size, W * 0.94); f3 = fit(d, L3, BLACK, int(l23_size * 0.92), W * 0.94)
    stroke = max(6, l23_size // 9)
    outlined(d, (W / 2, l2_y), L2, f2, YEL, stroke)
    outlined(d, (W / 2, l3_y), L3, f3, WHITE, stroke)
    im.save(out, quality=95)

# 長尺 1280×720: 上の黒帯に赤帯の1行目、中央に写真、下の黒帯に2〜3行目(写真と少し重ねて大きく)
make(1280, 720, os.path.join(D, "sample_long_1280x720.png"), (290, 136, 990, 522), 10, 92, 64, 587, 668, 84)
# ショート 1080×1920: 同じ型を縦に
make(1080, 1920, os.path.join(D, "sample_short_1080x1920.png"), (60, 350, 1020, 1350), 150, 150, 80, 1500, 1660, 110)
print("ok")
