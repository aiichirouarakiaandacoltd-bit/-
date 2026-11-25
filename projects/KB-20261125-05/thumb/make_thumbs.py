"""KB-20261125-05 の長尺の表紙 3パターン(第5-2章・第5-3章・第9章②・templates/thumb_long_template.md)。
python3 projects/KB-20261125-05/thumb/make_thumbs.py で thumb_A.png・thumb_B.png・thumb_C.png(1280×720)と
3枚を縮小して並べた一覧 abc_overview.jpg を書き出す。

写真は宮内庁(台帳の【表紙候補】のうち、撮影者・提供者の表記なし・長辺1000px)。切り抜き・拡大縮小のみ(左右反転もしない)。
過去の全 thumb.yaml の写真(取得元URL)と重ならないこと、dHash で過去の表紙の写真と別物であることを確かめた。
かぎかっこ内は令和8年2月19日 お誕生日の記者会見(宮内庁掲載の全文)の一部を一字一句(facts.md F9・F10・F16)。
誰の言葉か分かるよう、引用のそばに小さく「天皇陛下」と出典「お誕生日会見より」(文字の数に入れない)。

3枚で写真・構図・人物の左右・タイトルの位置を変えた(荒木指示 2026-11-25「構図が全部一緒ではABテストにならない」)。
  A(題名A・陛下と愛子さま)= 文字 左4.7割・写真 右5.3割に縦長のパネル2枚(左 天皇陛下 A003 令和8年 お誕生日のご近影/右 愛子さま A020 令和7年 お誕生日のご近影・本を手に)。
      タイトルは「左」(横書き): 言わば/「未知の旅」(金・最大)/のように ＋ 細い金の線の下に 愛子さまのお話とは？  2か所・23字
  B(題名B・社会人として一歩一歩成長・日赤)= 写真 左・文字 右(Aと左右を逆に)。愛子さまお一人 A022(机でペンを手に・ジャケット姿)。
      タイトルは「右」(横書き3行): 「社会人として/一歩一歩(金・最大)/成長」＋金の帯「日本赤十字社で2年目」  2か所・22字
  C(題名C・ご一家)= 写真1枚いっぱい(3名・寄り・帯なし)。令和8年 新年のご一家のご近影 A012(陛下が中央・左 雅子さま・右 愛子さま)。
      タイトルは「下」(横書き1行): 「愛子と3人で過ごす時間」(金の大きな「3人」)。左上に 天皇ご一家の1年  2か所・19字
  過去の長尺の表紙(KB-20261125-01: A=型D上の帯/B=写真右・文字左/C=写真左・右の縦書き、KB-20261124-01: 型D×3)とも並べて見比べた。
そろえているのは 明朝の極太・金の文字・配色(赤なし・下部の濃紺グラデーションなし)・クレジットの置き方だけ。
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.thumb_long import place, text, grad, credit, check_faces, gold_band, F, W, H, NAVY

A = str(ROOT / "assets/KB-20261125-05") + "/"
O = str(Path(__file__).resolve().parent) + "/"
SRC_GOLD = (232, 200, 110)
CREDIT_RIGHT = 24
SRC = "お誕生日会見より"
WHO = "天皇陛下"


def bbox(im, xy, s, n, anchor, sw=9):
    return ImageDraw.Draw(im).textbbox(xy, s, font=F(n), anchor=anchor, stroke_width=sw)


def union(bs):
    return (int(min(b[0] for b in bs)), int(min(b[1] for b in bs)), int(max(b[2] for b in bs)), int(max(b[3] for b in bs)))


def line(im, x, base, parts, center=False):
    """[(文字, 大きさ, "white"/"gold"), ...] を同じベースラインで1行に。center=True なら x を中心に置く。枠を返す"""
    d = ImageDraw.Draw(im)
    ws = [d.textlength(s, font=F(n)) for s, n, _ in parts]
    if center:
        x = x - sum(ws) / 2
    boxes = []
    for (s, n, fill), w in zip(parts, ws):
        text(im, (x, base), s, n, fill=fill, sw=9 if fill == "gold" else 8, anchor="ls")
        boxes.append(bbox(im, (x, base), s, n, "ls")); x += w
    return union(boxes)


def who_tag(im, x, y, anchor="ls", plate=False):
    """誰の言葉か(小さな名前の札「天皇陛下」＋金の小さな出典)。文字の数に入れない。枠を返す。
    plate=True なら濃紺の札を敷く(白いお召し物の上でも金の小さな出典が読めるように)"""
    if plate:
        w = ImageDraw.Draw(im).textlength(WHO, font=F(40)) + 14 + ImageDraw.Draw(im).textlength(SRC, font=F(28))
        ImageDraw.Draw(im).rounded_rectangle((x - 12, y - 46, x + w + 14, y + 14), radius=8, fill=(8, 20, 48))
    text(im, (x, y), WHO, 40, sw=4, shadow=False, anchor=anchor)
    b1 = bbox(im, (x, y), WHO, 40, anchor, 4)
    ImageDraw.Draw(im).rectangle((b1[0] + 4, b1[3] + 1, b1[2] - 4, b1[3] + 4), fill=SRC_GOLD)
    sx = b1[2] + 14
    text(im, (sx, y), SRC, 28, fill=SRC_GOLD, sw=3, shadow=False, anchor="ls")
    b = union([b1, bbox(im, (sx, y), SRC, 28, "ls", 3)])
    return (b[0] - 12, b[1] - 6, b[2] + 14, b[3] + 8) if plate else b


def overlap(a, b, pad=0):
    return a[0] < b[2] + pad and a[2] + pad > b[0] and a[1] < b[3] + pad and a[3] + pad > b[1]


# ---------------- A: 文字 左・写真 右に2枚(天皇陛下/愛子さま)・タイトルは左 ----------------
def make_A(out):
    TX = 600             # 写真の左端(ここから右に 340px のパネルを2枚。写真 約5.3割・文字 約4.7割)
    PW = 340
    im = Image.new("RGB", (W, H), NAVY)
    p1 = place(A + "A003.jpg", PW, H, (PW // 2, 245), 170, None); f1 = place.last_face
    p2 = place(A + "A020.jpg", PW, H, (PW // 2, 245), 150, (516 / 1000, 171 / 666, 98 / 666)); f2 = place.last_face
    im.paste(p1, (TX, 0)); im.paste(p2, (TX + PW, 0))
    ImageDraw.Draw(im).line((TX + PW, 0, TX + PW, H), fill=(10, 20, 45), width=6)
    faces = [(f1[0] + TX, f1[1], f1[2], f1[3]), (f2[0] + TX + PW, f2[1], f2[2], f2[3])]
    fade = grad(W, H, [(0, (255,) * 3), (0.44, (255,) * 3), (0.49, (0,) * 3), (1, (0,) * 3)], horizontal=True).convert("L")
    im = Image.composite(grad(W, H, [(0, (6, 16, 40)), (1, (20, 40, 80))]), im, fade)
    # ① 左: 名前の札(小)＋ 言わば/「未知の旅」(金・最大)/のように(横書き3行)
    wb = who_tag(im, 30, 70)
    b1 = line(im, 26, 196, [("言わば", 84, "white")])
    b2 = line(im, 20, 352, [("「", 64, "gold"), ("未知の旅", 108, "gold"), ("」", 64, "gold")])
    b3 = line(im, 26, 470, [("のように", 84, "white")])
    # ② 左下: 愛子さまのお話とは？(白)。上に細い金の線
    ImageDraw.Draw(im).rectangle((28, 540, 570, 544), fill=SRC_GOLD)
    b4 = line(im, 26, 628, [("愛子さまのお話とは？", 55, "white")])
    tboxes = [wb, union([b1, b2, b3]), b4]
    for tb in tboxes:
        if tb[2] > TX - 4:
            raise SystemExit(f"{out}: 文字が写真の側にはみ出しています {tb}")
    credit(im, "写真: 宮内庁 令和8年 天皇陛下お誕生日のご近影(御所)/令和7年 愛子内親王殿下お誕生日のご近影(御所)",
           tboxes, right=CREDIT_RIGHT)
    im.save(out)
    print(out, "名前", wb, "引用", tboxes[1], "下の一言", b4)
    if not check_faces(out, faces, tboxes):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


# ---------------- B: 写真 左・文字 右(愛子さまお一人)・タイトルは右 ----------------
def make_B(out):
    PW = 760
    im = Image.new("RGB", (W, H), NAVY)
    # A022 のお顔は検出器が拾わないため手で指定(元の写真で 中心 x500・y245・高さ約140px。髪の上端 y約105・顎 y約310)
    ph = place(A + "A022.jpg", PW, H, (360, 300), 220, (500 / 1000, 245 / 666, 140 / 666)); im.paste(ph, (0, 0))
    faces = [place.last_face]
    fade = grad(W, H, [(0, (0,) * 3), (0.50, (0,) * 3), (0.58, (255,) * 3), (1, (255,) * 3)], horizontal=True).convert("L")
    im = Image.composite(grad(W, H, [(0, (20, 40, 80)), (1, (6, 16, 40))], horizontal=True), im, fade)
    X = 700
    wb = who_tag(im, X + 4, 70)
    b1 = line(im, X, 196, [("「社会人として", 74, "white")])
    b2 = line(im, X, 352, [("一歩一歩", 132, "gold")])
    b3 = line(im, X, 470, [("成長」", 84, "white")])
    band = (X - 10, 532, W - 20, 618)
    gold_band(im, band, "日本赤十字社で2年目", 54)
    tboxes = [wb, union([b1, b2, b3]), band]
    for tb in tboxes:
        if tb[0] < 640 or tb[2] > W - 8:
            raise SystemExit(f"{out}: 文字が写真の側か画面の外にはみ出しています {tb}")
    credit(im, "写真: 宮内庁 令和7年 愛子内親王殿下お誕生日のご近影(御所)", tboxes, right=CREDIT_RIGHT)
    im.save(out)
    print(out, "名前", wb, "引用", tboxes[1], "金の帯", band)
    if not check_faces(out, faces, tboxes):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


# ---------------- C: 写真1枚いっぱい(ご一家3名)・タイトルは下 ----------------
def make_C(out):
    # A012(1000×666)のお顔(検出器・元の写真のpx): 皇后陛下・天皇陛下・愛子内親王殿下
    FACES = [(298, 165, 72, 72), (487, 152, 73, 73), (652, 160, 68, 68)]
    S = 2.15
    cx, cy = 523, 188                     # 陛下のお顔の中心(元の写真)
    T = (668, 300)                        # 表紙での位置(右端を元の写真の x約808 にして、右の棚の赤い飾り人形を入れない)
    ph = place(A + "A012.jpg", W, H, T, 73 * S, (cx / 1000, cy / 666, 73 / 666))
    im = ph.copy()
    faces = [(T[0] + (x - cx) * S, T[1] + (y - cy) * S, w * S, h * S) for (x, y, w, h) in FACES]
    # ① 左上: 天皇ご一家の1年(白・小さめ)
    tb = line(im, 28, 92, [("天皇ご一家の1年", 64, "white")])
    # ② 下: 名前の札＋「愛子と3人で過ごす時間」(金の大きな「3人」)
    qb = line(im, W / 2, 662, [("「愛子と", 80, "white"), ("3人", 150, "gold"), ("で過ごす時間」", 80, "white")], center=True)
    wb = who_tag(im, qb[0] + 18, qb[1] - 14, plate=True)
    if qb[0] < 8 or qb[2] > W - 8:
        raise SystemExit(f"{out}: 下の引用がはみ出しています {qb}")
    tboxes = [tb, qb, wb]
    credit(im, "写真: 宮内庁 令和8年 新年をお迎えになったご一家のご近影(御所)", tboxes, right=CREDIT_RIGHT)
    im.save(out)
    print(out, "左上", tb, "引用", qb, "名前", wb)
    if not check_faces(out, faces, tboxes):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


make_A(O + "thumb_A.png")
make_B(O + "thumb_B.png")
make_C(O + "thumb_C.png")

# 3枚を縮小して並べた一覧(ひと目で別の表紙に見えるかの確認用)
sheet = Image.new("RGB", (3 * 440 + 40, 248 + 20), (30, 30, 30))
for k, n in enumerate("ABC"):
    sheet.paste(Image.open(O + f"thumb_{n}.png").resize((440, 248), Image.LANCZOS), (10 + k * 450, 10))
sheet.save(O + "abc_overview.jpg", quality=90)
print(O + "abc_overview.jpg")
