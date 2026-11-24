"""長尺(横型)の表紙 1280×720 の型(荒木指示 2026-11-24 改訂): 写真を画面いっぱい・極太文字・矢印なし・濃紺なし。
上段=実際のお言葉の引用(白・極太)/中段=写真を端から端まで並べる/下段=2行(白・黄)。赤は使わない。"""
import sys, cv2
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from pipeline.rules_render import faces
FK = "/usr/local/share/fonts/noto-sans-jp/NotoSansJP-Black.ttf"
WHITE, YELLOW, BLACK = (255, 255, 255), (255, 214, 0), (0, 0, 0)
W, H = 1280, 720
TOP, BOT = 104, 548          # 写真の帯(上の文字帯の下〜下の文字帯の上)


def F(n): return ImageFont.truetype(FK, n)


def ctext(d, y, txt, size, fill, stroke, maxw=1250):
    while d.textlength(txt, font=F(size)) > maxw and size > 30:
        size -= 2
    w = d.textlength(txt, font=F(size))
    d.text(((W - w) / 2, y), txt, font=F(size), fill=fill, stroke_width=stroke, stroke_fill=BLACK)


def face_cover(path, w, h, zoom=4.0, focus=None):
    img = cv2.imread(path); ih, iw = img.shape[:2]; fs = [] if focus else faces(img)
    if focus:
        cx, cy, ch = focus[0] * iw, focus[1] * ih, ih
    elif fs:
        x, y, fw, fh = max(fs, key=lambda f: f[2] * f[3]); cx, cy = x + fw / 2, y + fh / 2
        ch = min(ih, fh * zoom)
    else:
        cx, cy, ch = iw / 2, ih * 0.4, ih
    cw = ch * w / h
    if cw > iw: cw = iw; ch = cw * h / w
    if ch > ih: ch = ih; cw = ch * w / h
    l = min(max(cx - cw / 2, 0), iw - cw); t = min(max(cy - 0.40 * ch, 0), ih - ch)
    c = img[int(t):int(t + ch), int(l):int(l + cw)]
    return Image.fromarray(cv2.cvtColor(cv2.resize(c, (w, h), interpolation=cv2.INTER_LANCZOS4), cv2.COLOR_BGR2RGB))


def make(out, quote, panels, line1, line2, credit):
    """panels: [(画像パス, 幅の割合, 撮影情報), ...] 左から順に端から端まで並べる"""
    im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im)
    x = 0; tot = sum(p[1] for p in panels)
    for k, (path, frac, cap, *fo) in enumerate(panels):
        pw = W - x if k == len(panels) - 1 else int(W * frac / tot)
        im.paste(face_cover(path, pw, BOT - TOP, focus=fo[0] if fo else None), (x, TOP))
        if k: d.line((x, TOP, x, BOT), fill=BLACK, width=6)
        cf = F(17); cw = d.textlength(cap, font=cf)
        d.rectangle((x + 6, BOT - 28, x + 14 + cw, BOT - 4), fill=(0, 0, 0))
        d.text((x + 10, BOT - 28), cap, font=cf, fill=WHITE)
        x += pw
    ctext(d, 2, quote, 92, WHITE, 9)
    ctext(d, BOT + 6, line1, 76, WHITE, 8)
    ctext(d, BOT + 88, line2, 70, YELLOW, 8)
    lf = F(18); lw = d.textlength("日本が誇る皇室物語", font=lf)
    d.rectangle((W - lw - 22, TOP + 6, W - 6, TOP + 34), fill=BLACK)
    d.text((W - lw - 14, TOP + 7), "日本が誇る皇室物語", font=lf, fill=YELLOW)
    if credit:
        d.text((8, H - 22), credit, font=F(14), fill=(200, 200, 200))
    im.save(out); print(out)


if __name__ == "__main__":
    S = "/tmp/claude-0/-home-user--/43a7a50c-dc00-57d9-956c-aa12a4cfeb48/scratchpad/sample/"
    A = str(Path(__file__).resolve().parents[1] / "assets/KB-20261123-06") + "/"
    O = str(Path(__file__).resolve().parents[1] / "samples/long_aiko_2countries") + "/"
    make(O + "thumb_A.png", "「改めて深く感謝いたします」",
         [(A + "A115.jpg", 0.36, "愛子さま 令和7年12月1日公表"), (S + "lao_601_3.jpeg", 0.34, "2025.11.18 ラオス 晩餐会のおことば"),
          (S + "lao_600_1.jpeg", 0.30, "2025.11.18 バーシーセレモニー", (0.5, 0.4))],
         "2つの国で込められた感謝とは？", "ラオスとシンガポールのおことば", "")
    make(O + "thumb_B.png", "「東日本大震災などの大きな試練」",
         [(S + "lao_599_1.jpeg", 0.5, "2025.11.18 ラオス 国家主席表敬"), (S + "lao_609_1.jpeg", 0.5, "2025.11.20 ラオス 午餐会のおことば")],
         "1年で2回、おことばに出てきた言葉", "令和7年ラオス・令和8年シンガポール", "")
    make(O + "thumb_C.png", "「私の祖父母である上皇上皇后両陛下」",
         [(A + "A020.jpg", 0.40, "愛子さま 2026.6.22 ©Naoya Ikegami/SUNTORY HALL"), (S + "jg.jpg", 0.60, "イメージ:ジュロン地区の日本庭園 FN-082/CC BY-SA 4.0")],
         "56年前に祖父母が植えられた木とは？", "シンガポールでのおことばから", "")
