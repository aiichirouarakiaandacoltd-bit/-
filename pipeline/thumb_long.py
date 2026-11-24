"""長尺(横型)の表紙 1280×720(荒木指示 2026-11-24 第3版)。
参考: 荒木さん提供の型(明朝の極太・金のグラデーション文字・金の帯・人物1〜2名を大きく・短いワンフレーズ)。
型 R(右に人物1名・左に文字) / 型 D(左右に人物2名・中央に大きな金の一言)。赤・絵文字・作り台詞は使わない。"""
import sys, cv2, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pipeline.rules_render import faces
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
W, H = 1280, 720
NAVY = (8, 20, 48)
WHITE = (255, 255, 255)


def F(n): return ImageFont.truetype(SERIF, n, index=0)


def photo(path, w, h, focus=None, zoom=4.2, fy=0.36):
    img = cv2.imread(path); ih, iw = img.shape[:2]
    if focus:
        cx, cy = focus[0] * iw, focus[1] * ih; ch = ih * focus[2] if len(focus) > 2 else ih
    else:
        fs = faces(img)
        if fs:
            x, y, fw, fh = max(fs, key=lambda f: f[2] * f[3]); cx, cy = x + fw / 2, y + fh / 2; ch = min(ih, fh * zoom)
        else:
            cx, cy, ch = iw / 2, ih * 0.4, ih
    cw = ch * w / h
    if cw > iw: cw = iw; ch = cw * h / w
    if ch > ih: ch = ih; cw = ch * w / h
    l = min(max(cx - cw / 2, 0), iw - cw); t = min(max(cy - fy * ch, 0), ih - ch)
    c = img[int(t):int(t + ch), int(l):int(l + cw)]
    return Image.fromarray(cv2.cvtColor(cv2.resize(c, (w, h), interpolation=cv2.INTER_LANCZOS4), cv2.COLOR_BGR2RGB))


def place(path, pw, ph, target, fh_t, focus=None):
    """人物のお顔を、文字と重ならない決まった位置(target=(x,y)・パネル内)に、決まった大きさ(fh_t=顔の高さpx)で置く。
    写真が足りない所は同じ写真のぼかしで埋める(見切れの隙間を作らない)。focus=(x割合,y割合,顔の高さ割合) で手動指定可"""
    img = cv2.imread(path); ih, iw = img.shape[:2]
    if focus:
        cx, cy, fh = focus[0] * iw, focus[1] * ih, focus[2] * ih
    else:
        fs = faces(img)
        if not fs and iw < 1000:  # 小さい写真は拡大して検出し直す
            k = 1000 / iw; fs = [(x / k, y / k, w / k, h / k) for (x, y, w, h) in faces(cv2.resize(img, None, fx=k, fy=k))]
        if not fs:
            raise SystemExit(f"{path}: お顔を検出できません。focus=(x割合,y割合,顔の高さ割合)で指定してください")
        x, y, fw, fh = max(fs, key=lambda f: f[2] * f[3]); cx, cy = x + fw / 2, y + fh / 2
    s = fh_t / fh
    big = cv2.resize(img, (max(1, int(iw * s)), max(1, int(ih * s))), interpolation=cv2.INTER_LANCZOS4)
    ox, oy = int(target[0] - cx * s), int(target[1] - cy * s)
    cs = max(pw / iw, ph / ih)
    bg = cv2.GaussianBlur(cv2.resize(img, (int(iw * cs) + 2, int(ih * cs) + 2)), (0, 0), 18)
    canvas = bg[:ph, :pw].copy()
    x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(pw, ox + big.shape[1]), min(ph, oy + big.shape[0])
    canvas[y0:y1, x0:x1] = big[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    fw_t = fh_t  # 顔の幅はおよそ高さと同じ
    place.last_face = (target[0] - fw_t / 2, target[1] - fh_t / 2, fw_t, fh_t)
    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def check_faces(path, face_boxes, text_boxes):
    """置いたお顔(頭の範囲)が、文字の枠と重ならず、画面の外に見切れていないかを確かめる"""
    bad = []
    for (x, y, w, h) in face_boxes:
        hx0, hy0, hx1, hy1 = x - w * 0.25, y - h * 0.55, x + w * 1.25, y + h * 1.15   # 髪と顎を含む頭の範囲
        if hx0 < 0 or hy0 < 0 or hx1 > W or hy1 > H:
            bad.append(f"見切れ 頭{(int(hx0), int(hy0), int(hx1), int(hy1))}")
        for (a, b, c, d) in text_boxes:
            if hx0 < c and hx1 > a and hy0 < d and hy1 > b:
                bad.append(f"文字と重なり 頭{(int(hx0), int(hy0), int(hx1), int(hy1))} 文字{(a, b, c, d)}")
    print(path, "顔の位置 OK" if not bad else bad)
    return not bad

def grad(w, h, stops, horizontal=False):
    n = w if horizontal else h
    arr = np.zeros((n, 3))
    for i in range(n):
        p = i / max(1, n - 1)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= p <= b:
                t = (p - a) / max(1e-6, b - a); arr[i] = [ca[k] + (cb[k] - ca[k]) * t for k in range(3)]; break
    if horizontal:
        g = np.tile(arr[None, :, :], (h, 1, 1))
    else:
        g = np.tile(arr[:, None, :], (1, w, 1))
    return Image.fromarray(g.astype(np.uint8))


GOLD = [(0, (255, 246, 190)), (0.45, (240, 200, 80)), (0.55, (200, 150, 30)), (1, (255, 225, 120))]


def text(im, xy, s, size, fill="white", stroke=(8, 20, 48), sw=6, shadow=True, anchor="la", maxw=None):
    d = ImageDraw.Draw(im)
    while maxw and d.textlength(s, font=F(size)) > maxw and size > 24:
        size -= 2
    f = F(size)
    if shadow:
        sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).text((xy[0] + 5, xy[1] + 6), s, font=f, fill=200, stroke_width=sw + 2, anchor=anchor)
        im.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(6)))
    if fill == "gold":
        mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).text(xy, s, font=f, fill=255, anchor=anchor)
        d.text(xy, s, font=f, fill=stroke, stroke_width=sw, stroke_fill=stroke, anchor=anchor)
        bb = mask.getbbox(); g = grad(bb[2] - bb[0], bb[3] - bb[1], GOLD)
        full = Image.new("RGB", im.size); full.paste(g, (bb[0], bb[1])); im.paste(full, (0, 0), mask)
    else:
        d.text(xy, s, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)
    return size


def gold_band(im, box, s, size):
    x0, y0, x1, y1 = box
    band = grad(x1 - x0, y1 - y0, [(0, (190, 140, 30)), (0.3, (255, 235, 150)), (0.7, (240, 200, 90)), (1, (180, 130, 25))], horizontal=True)
    im.paste(band, (x0, y0))
    text(im, ((x0 + x1) // 2, (y0 + y1) // 2), s, size, fill=NAVY, stroke=(255, 240, 190), sw=2, shadow=False, anchor="mm", maxw=x1 - x0 - 30)


def credit(im, s):
    d = ImageDraw.Draw(im); f = ImageFont.truetype("/usr/local/share/fonts/noto-sans-jp/NotoSansJP-Bold.ttf", 15)
    w = d.textlength(s, font=f); d.rectangle((W - w - 16, H - 24, W, H), fill=(0, 0, 0)); d.text((W - w - 8, H - 23), s, font=f, fill=(220, 220, 220))


def type_R(out, img, focus, big, band, line, cap, big_fill="white", face_h=240):
    """人物1名(荒木さんと調整中の型): 写真 約5.5割(右)・文字 約4.5割(左)。スマホで55歳以上の女性が読める大きさ"""
    PW = 704
    im = Image.new("RGB", (W, H), NAVY)
    ph = place(img, PW + 120, H, (400, 330), face_h, focus); im.paste(ph, (W - PW - 120, 0))
    fx, fy, fw, fh = place.last_face; faces_ = [(fx + W - PW - 120, fy, fw, fh)]
    fade = grad(W, H, [(0, (255, 255, 255)), (0.45, (255, 255, 255)), (0.55, (0, 0, 0)), (1, (0, 0, 0))], horizontal=True).convert("L")
    im = Image.composite(grad(W, H, [(0, (6, 16, 40)), (1, (20, 40, 80))]), im, fade)
    text(im, (30, 60), big, 150, fill=big_fill, sw=8, maxw=600)
    gold_band(im, (20, 285, 640, 395), band, 84)
    text(im, (30, 430), line, 96, sw=8, maxw=620)
    credit(im, cap); im.save(out)
    check_faces(out, faces_, [(20, 40, 640, 250), (20, 285, 640, 395), (20, 420, 660, 560)])


def type_D(out, img1, f1, img2, f2, top, big, band, cap):
    """人物2名(または人物と場所): 写真 約5.5割(中央の高さ)・文字 約4.5割(上の帯と下)。下部の濃紺グラデーションは使わない"""
    im = Image.new("RGB", (W, H), NAVY)
    p1 = place(img1, 640, H, (320, 305), 175, f1); fa = place.last_face
    p2 = place(img2, 640, H, (320, 305), 175, f2); fb = place.last_face
    im.paste(p1, (0, 0)); im.paste(p2, (640, 0))
    ImageDraw.Draw(im).line((640, 0, 640, H), fill=(10, 20, 45), width=6)
    faces_ = ([fa] if f1 is None or len(f1) < 4 else []) + ([(fb[0] + 640, fb[1], fb[2], fb[3])] if f2 is None or len(f2) < 4 else [])
    im.paste(grad(W, 100, [(0, (6, 14, 36)), (1, (16, 32, 68))]), (0, 0))
    text(im, (W // 2, 50), top, 80, anchor="mm", maxw=1220, shadow=False)
    text(im, (W // 2, 538), big, 140, fill="gold", sw=9, anchor="mm", maxw=1060)
    gold_band(im, (150, 640, 1130, 714), band, 62)
    credit(im, cap); im.save(out)
    check_faces(out, faces_, [(0, 0, W, 100), (110, 465, 1170, 720)])


if __name__ == "__main__":
    S = "/tmp/claude-0/-home-user--/43a7a50c-dc00-57d9-956c-aa12a4cfeb48/scratchpad/sample/"
    A = str(Path(__file__).resolve().parents[1] / "assets/KB-20261123-06") + "/"
    O = str(Path(__file__).resolve().parents[1] / "samples/long_aiko_2countries") + "/"
    type_R(O + "thumb_A.png", A + "A115.jpg", None, "愛子さま", "2つの国のおことば", "込めた感謝とは？",
           "写真: 宮内庁 令和7年12月1日公表")
    type_R(O + "thumb_B.png", A + "A118.jpg", (0.53, 0.33, 0.17), "1年で2回", "東日本大震災への感謝", "2つのおことば",
           "写真: 宮内庁 令和7年12月1日公表(御所にて)", big_fill="gold", face_h=180)
    type_D(O + "thumb_C.png", A + "A020.jpg", None, S + "jg.jpg", (0.5, 0.5, 0.21, "scene"),
           "祖父母が植えた木", "56年前", "シンガポールで語られた3代", "写真: 宮内庁 2026.6.22 ©Naoya Ikegami/SUNTORY HALL / イメージ: 日本庭園 FN-082 CC BY-SA 4.0")
