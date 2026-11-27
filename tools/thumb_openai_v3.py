"""表紙 第3版: AI(gpt-image-2)の背景と文字デザイン + 宮内庁の写真の切り抜き。
文字は AI が濃紺の無地の上に作ったものを、色の差で抜き出して重ねる(字は人の目で1字ずつ確認する)。
お姿は切り抜いた元の写真の画素をそのまま使う(AIは人物を描かない)。出力は .gitignore で除外。"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from thumb_openai_compose import fit_cover, person, vgrad, credit

def key(path, pad=6):
    im = np.array(Image.open(path).convert("RGB")).astype(float)
    bg = np.median(np.concatenate([im[:8].reshape(-1, 3), im[-8:].reshape(-1, 3), im[:, :8].reshape(-1, 3), im[:, -8:].reshape(-1, 3)]), axis=0)
    d = np.sqrt(((im - bg) ** 2).sum(-1))
    a = np.clip((d - 10) / 45, 0, 1)
    fg = np.where(a[..., None] > 0.02, (im - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 0.02), 0)
    out = np.dstack([np.clip(fg, 0, 255), a * 255]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    ys, xs = np.where(a > 0.25)
    return img.crop((max(xs.min() - pad, 0), max(ys.min() - pad, 0), xs.max() + pad, ys.max() + pad))

def place(c, lay, box, align="center"):
    x0, y0, x1, y1 = box
    s = min((x1 - x0) / lay.width, (y1 - y0) / lay.height)
    lay = lay.resize((round(lay.width * s), round(lay.height * s)), Image.LANCZOS)
    x = x0 + ((x1 - x0) - lay.width) // 2 if align == "center" else x0
    y = y0 + ((y1 - y0) - lay.height) // 2
    c.alpha_composite(lay, (x, y))
    return (x, y, x + lay.width, y + lay.height)

def main(work, v3, photos, out):
    os.makedirs(out, exist_ok=True)
    cut = lambda n: Image.open(os.path.join(work, f"cut/{n}.png"))
    boxes = {}
    # A
    c = fit_cover(Image.open(f"{v3}/bgA.png").convert("RGB"), 1280, 720).convert("RGBA")
    boxes["A_m"] = person(c, cut("A061"), 0.93, 22, 72)
    boxes["A_e"] = person(c, cut("A066"), 0.665, 906, 76)
    boxes["A_t"] = place(c, key(f"{v3}/xA.png"), (372, 96, 906, 640))
    credit(c, ["写真:宮内庁 令和7年 皇后陛下・天皇陛下お誕生日に際してのご近影(切り抜き)", "「」内は 令和7年 皇后陛下お誕生日に際してのご感想より(宮内庁)"], (1240, 690), 12)
    c.convert("RGB").save(f"{out}/long_A_frame.png")
    # B
    c = fit_cover(Image.open(f"{v3}/bgB.png").convert("RGB"), 1280, 720).convert("RGBA")
    boxes["B_c"] = person(c, cut("A062"), 1.12, 612, 58)
    boxes["B_t"] = place(c, key(f"{v3}/xB.png"), (56, 40, 600, 670), align="left")
    credit(c, ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(切り抜き)"], (1262, 708), 12)
    c.convert("RGB").save(f"{out}/long_B_glow.png")
    # C
    W, H = 1280, 720
    base = Image.new("RGB", (W, H))
    l = Image.open(f"{photos}/A060.jpg").convert("RGB"); s = 1.30
    l = l.resize((round(l.width * s), round(l.height * s)), Image.LANCZOS); cx = int(342 * s)
    base.paste(l.crop((cx - 320, 95, cx + 320, 95 + H)), (0, 0))
    r = Image.open(f"{photos}/A063.jpg").convert("RGB"); s = 1.45
    r = r.resize((round(r.width * s), round(r.height * s)), Image.LANCZOS); cx = int(505 * s)
    base.paste(r.crop((cx - 320, 85, cx + 320, 85 + H)), (640, 0))
    c = base.convert("RGBA")
    vgrad(c, 0, 150, (14, 22, 40), 240, 200); vgrad(c, 150, 215, (14, 22, 40), 200, 0)
    vgrad(c, 400, 480, (14, 22, 40), 0, 190); vgrad(c, 480, 720, (14, 22, 40), 190, 235)
    ln = Image.new("RGBA", (40, H), (0, 0, 0, 0)); ImageDraw.Draw(ln).rectangle((18, 0, 21, H), fill=(240, 205, 120, 255))
    c.alpha_composite(ln.filter(ImageFilter.GaussianBlur(7)), (620, 0)); c.alpha_composite(ln, (620, 0))
    boxes["C_top"] = place(c, key(f"{v3}/xCtop.png"), (24, 10, 1256, 140))
    boxes["C_bot"] = place(c, key(f"{v3}/xCbot.png"), (20, 452, 1260, 706))
    credit(c, ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影 /「」内は同年のご感想より"], (1268, 714), 11)
    c.convert("RGB").save(f"{out}/long_C_rival.png")
    # Short
    c = fit_cover(Image.open(f"{v3}/bgS.png").convert("RGB"), 1080, 1920).convert("RGBA")
    boxes["S_t"] = place(c, key(f"{v3}/xS.png"), (60, 90, 1020, 640))
    boxes["S_m"] = person(c, cut("A061"), 2.5, 84, 700)
    vgrad(c, 1480, 1920, (12, 20, 38), 0, 210)
    boxes["S_b"] = place(c, key(f"{v3}/xS2.png"), (70, 1640, 1010, 1780))
    credit(c, ["写真:宮内庁 令和7年 皇后陛下お誕生日に際してのご近影(切り抜き)", "「」内は 令和7年 皇后陛下お誕生日に際してのご感想より(宮内庁)"], (1020, 1880), 20)
    c.convert("RGB").save(f"{out}/short_cover.png")
    return boxes

if __name__ == "__main__":
    print(main(*sys.argv[1:5]))
