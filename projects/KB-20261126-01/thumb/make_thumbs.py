"""KB-20261126-01(愛子さま25年の軌跡・長尺)の表紙 3パターン(第5-2章4・第5-3章5・第9章②・templates/thumb_long_template.md)。
python3 projects/KB-20261126-01/thumb/make_thumbs.py で thumb_A.png・thumb_B.png・thumb_C.png(1280×720)と
3枚を縮小して並べた一覧 overview.jpg を書き出す。

写真は宮内庁の掲載写真で台帳(ledger.csv)の照合済みのものだけ。切り抜き・拡大縮小のみ(反転・顔の加工・AI生成なし)。
過去の全 thumb.yaml(projects/*)と直近の本編(projects/KB-202611*/scenes.json)を取得元URLで照合し、4枚とも
表紙0回・本編0回(この長尺の本編でも0回)。皇族方以外の方は切り抜きで外す。献花・慰霊・被災地の写真は使わない。
  A102 令和7年11月 ラオ・フレンズ小児病院ご視察(ラオス。初めての外国公式訪問)。長辺1000px・撮影者表記なし
  A178/A169/A170 「愛子内親王殿下のお誕生日に際してのご近影」(A178 は長辺1000px、A169・A170 は長辺1800px・撮影者表記なし。年の裏付けがないため年は表示しない=事実確認 M6)
3枚で写真・構図・人物の左右・タイトルの位置を変えた(荒木指示 2026-11-25)。そろえるのは明朝の極太・金の文字・配色(赤なし)・クレジットの置き方だけ。
  A(題名A 25年の軌跡)= 縦長の写真2枚を額のように左に並べる(左 A178 ご近影・右 A102 ラオス)/文字は右。2か所・20字
  B(題名B 本命)      = 写真1枚・寄り・人物は右(A169 屋外の柿の木の前・左を向いてほほえまれる)/文字は左。2か所・20字
  C(題名C お言葉)    = 写真1枚いっぱい・引き・人物は中央(A170 御所の障子の前・穏やかな笑顔)/文字は下(引用)と左上。2か所・23字
"""
import sys
from pathlib import Path
import cv2
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.thumb_long import place, text, grad, credit, check_faces, F, W, H, NAVY

A = str(ROOT / "assets/KB-20261126-01") + "/"
O = str(Path(__file__).resolve().parent) + "/"
SRC_GOLD = (232, 200, 110)
CREDIT_RIGHT = 24


def bbox(im, xy, s, n, anchor, sw=9):
    return ImageDraw.Draw(im).textbbox(xy, s, font=F(n), anchor=anchor, stroke_width=sw)


def union(bs):
    return (int(min(b[0] for b in bs)), int(min(b[1] for b in bs)), int(max(b[2] for b in bs)), int(max(b[3] for b in bs)))


def line(im, x, base, parts, center=False):
    """[(文字, 大きさ, "white"/"gold"), ...] を同じベースラインで1行に。枠を返す"""
    d = ImageDraw.Draw(im)
    ws = [d.textlength(s, font=F(n)) for s, n, _ in parts]
    if center:
        x = x - sum(ws) / 2
    boxes = []
    for (s, n, fill), w in zip(parts, ws):
        text(im, (x, base), s, n, fill=fill, sw=9 if fill == "gold" else 8, anchor="ls")
        boxes.append(bbox(im, (x, base), s, n, "ls")); x += w
    return union(boxes)


def card(path, box, size):
    """元の写真の box=(x0,y0,x1,y1) を切り抜き、size に拡大縮小するだけ(縦横比は box と size で合わせる)"""
    img = cv2.imread(path)
    x0, y0, x1, y1 = box
    c = cv2.resize(img[y0:y1, x0:x1], size, interpolation=cv2.INTER_LANCZOS4)
    return Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)), size[0] / (x1 - x0)


def fail_if(cond, msg):
    if cond:
        raise SystemExit(msg)


# ---------------- A: 縦長の写真2枚(左)・文字(右) ----------------
def make_A(out):
    CW, CH, Y0 = 360, 600, 60
    X1, X2 = 24, 24 + CW + 16
    im = grad(W, H, [(0, (6, 16, 40)), (1, (20, 40, 80))])
    # 左の額: A178 ご近影(667×1000・正面を向いた穏やかな笑顔。2026-11-26 荒木指示で下を向いた A168 から差し替え)。
    # お顔(元の写真のpx・OpenCV の顔検出)x240〜399・y197〜356。切り抜き x100〜544・y50〜790(縦横比 0.6)。scale 約0.81(縮小)
    b1 = (100, 50, 544, 790)
    p1, s1 = card(A + "A178.jpg", b1, (CW, CH))
    f1 = (X1 + (240 - b1[0]) * s1, Y0 + (197 - b1[1]) * s1, 159 * s1, 159 * s1)
    # 右の額: A102 ラオス(1000×666)。愛子さまのお顔 x約569〜637・y約125〜231。
    # 切り抜きは x528〜700・y38〜325 だけ(左の母子・左上の男性・右後ろの随行の方の髪 x725〜・奥の方々 y330〜 を入れない)。scale 約2.1
    b2 = (528, 38, 700, 38 + 287)
    p2, s2 = card(A + "A102.jpg", b2, (CW, CH))
    f2 = (X2 + (569 - b2[0]) * s2, Y0 + (125 - b2[1]) * s2, 68 * s2, 106 * s2)
    for x, p in ((X1, p1), (X2, p2)):
        ImageDraw.Draw(im).rectangle((x - 4, Y0 - 4, x + CW + 3, Y0 + CH + 3), fill=SRC_GOLD)
        im.paste(p, (x, Y0))
    # 写真の下に小さく(写真の説明。文字の数に入れない)
    text(im, (X1 + CW // 2, Y0 + CH + 26), "お誕生日のご近影", 24, fill=SRC_GOLD, sw=2, shadow=False, anchor="mm")
    text(im, (X2 + CW // 2, Y0 + CH + 26), "令和7年 ラオスにて", 24, fill=SRC_GOLD, sw=2, shadow=False, anchor="mm")
    TX = X2 + CW + 34
    # ① 愛子さま / 25年(金・最大)の軌跡
    t1 = line(im, TX + 6, 150, [("愛子さま", 92, "white")])
    t2 = line(im, TX, 360, [("25年", 170, "gold")])
    t3 = line(im, TX + 150, 455, [("の軌跡", 92, "white")])
    # ② 金の細線の下に ご自身の言葉で/たどる
    ImageDraw.Draw(im).rectangle((TX + 6, 500, W - 28, 504), fill=SRC_GOLD)
    t4 = line(im, TX + 6, 590, [("ご自身の言葉で", 64, "white")])
    t5 = line(im, TX + 6, 670, [("たどる", 64, "white")])
    tboxes = [union([t1, t2, t3]), union([t4, t5])]
    for tb in tboxes:
        fail_if(tb[0] < X2 + CW or tb[2] > W - 8, f"{out}: 文字が写真か画面の外にはみ出しています {tb}")
    credit(im, "写真: 宮内庁 左 愛子内親王殿下のお誕生日に際してのご近影/右 令和7年11月 ラオ・フレンズ小児病院ご視察(ラオス)",
           tboxes, right=CREDIT_RIGHT)
    im.save(out)
    print(out, "文字", tboxes, "お顔", [tuple(int(v) for v in f) for f in (f1, f2)], "拡大率", round(s1, 2), round(s2, 2))
    fail_if(not check_faces(out, [f1, f2], tboxes), f"{out}: お顔が文字と重なるか見切れています")


# ---------------- B: 写真1枚・寄り・人物は右/文字は左 ----------------
def make_B(out):
    PX = 470
    im = Image.new("RGB", (W, H), NAVY)
    # A169(1800×1200)。お顔(検出器)=(905,257,183,183)。顔の高さ 240px(型Rの決まり)= 拡大率 約1.3
    ph = place(A + "A169.jpg", W - PX, H, (900 - PX, 330), 240, (996.5 / 1800, 348.5 / 1200, 183 / 1200))
    fx, fy, fw, fh = place.last_face; faces = [(fx + PX, fy, fw, fh)]
    im.paste(ph, (PX, 0))
    fade = grad(W, H, [(0, (255,) * 3), (0.38, (255,) * 3), (0.47, (0,) * 3), (1, (0,) * 3)], horizontal=True).convert("L")
    im = Image.composite(grad(W, H, [(0, (6, 16, 40)), (1, (20, 40, 80))]), im, fade)
    # ① 愛子さま(小さめ・下に金の細線)/成年から5年
    t1 = line(im, 30, 112, [("愛子さま", 68, "white")])
    ImageDraw.Draw(im).rectangle((32, t1[3] + 2, t1[2] - 8, t1[3] + 6), fill=SRC_GOLD)
    t2 = line(im, 26, 262, [("成年から", 92, "white"), ("5", 124, "gold"), ("年", 92, "white")])
    # ② 「初めて」(金・最大)/はいくつ？
    t3 = line(im, 14, 470, [("「初めて」", 132, "gold")])
    t4 = line(im, 30, 630, [("はいくつ？", 104, "white")])
    tboxes = [union([t1, t2]), union([t3, t4])]
    for tb in tboxes:
        fail_if(tb[0] < 4 or tb[2] > 700, f"{out}: 文字が写真の側にはみ出しています {tb}")
    credit(im, "写真: 宮内庁 愛子内親王殿下のお誕生日に際してのご近影", tboxes, right=CREDIT_RIGHT)
    im.save(out)
    print(out, "文字", tboxes, "お顔", [tuple(int(v) for v in f) for f in faces])
    fail_if(not check_faces(out, faces, tboxes), f"{out}: お顔が文字と重なるか見切れています")


# ---------------- C: 写真1枚いっぱい・引き・人物は中央/文字は下(引用)と左上 ----------------
def make_C(out):
    # A170(1800×1200)。お顔(検出器)=(768,192,196,196)。顔の高さ 150px = 縮小 約0.77(引き)
    im = place(A + "A170.jpg", W, H, (640, 220), 150, (866 / 1800, 290 / 1200, 196 / 1200))
    faces = [place.last_face]
    # ① 左上: 25歳のお誕生日に
    t1 = line(im, 26, 92, [("25歳のお誕生日に", 56, "white")])
    # ② 下: 「私も受け継いで(金)/いくことができれば」 + 誰の言葉か(小さな札。文字の数に入れない)
    q1 = line(im, W / 2, 560, [("「私も", 84, "white"), ("受け継いで", 128, "gold")], center=True)
    q2 = line(im, W / 2, 680, [("いくことができれば」", 84, "white")], center=True)
    qb = union([q1, q2])
    who, src = "愛子さま", "シンガポールご訪問を終えてのご感想より"
    d = ImageDraw.Draw(im)
    wx, wy = 26, 420
    ww = d.textlength(who, font=F(40)) + 14 + d.textlength(src, font=F(26))
    d.rounded_rectangle((wx - 10, wy - 46, wx + ww + 12, wy + 12), radius=8, fill=NAVY)
    text(im, (wx, wy), who, 40, sw=4, shadow=False, anchor="ls")
    b1 = bbox(im, (wx, wy), who, 40, "ls", 4)
    text(im, (b1[2] + 14, wy), src, 26, fill=SRC_GOLD, sw=3, shadow=False, anchor="ls")
    wb = (wx - 10, wy - 46, int(wx + ww + 12), wy + 12)
    fail_if(wb[3] > qb[1] + 4 and wb[2] > qb[0], f"{out}: 名前の札が引用と重なっています {wb} {qb}")
    fail_if(qb[0] < 8 or qb[2] > W - 8, f"{out}: 引用がはみ出しています {qb}")
    tboxes = [t1, qb, wb]
    credit(im, "写真: 宮内庁 愛子内親王殿下のお誕生日に際してのご近影", tboxes, right=CREDIT_RIGHT)
    im.save(out)
    print(out, "左上", t1, "引用", qb, "名前", wb, "お顔", [tuple(int(v) for v in f) for f in faces])
    fail_if(not check_faces(out, faces, tboxes), f"{out}: お顔が文字と重なるか見切れています")


make_A(O + "thumb_A.png")
make_B(O + "thumb_B.png")
make_C(O + "thumb_C.png")

sheet = Image.new("RGB", (3 * 440 + 40, 248 + 20), (30, 30, 30))
for k, n in enumerate("ABC"):
    sheet.paste(Image.open(O + f"thumb_{n}.png").resize((440, 248), Image.LANCZOS), (10 + k * 450, 10))
sheet.save(O + "overview.jpg", quality=90)
print(O + "overview.jpg")
