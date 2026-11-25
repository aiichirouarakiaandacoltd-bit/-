"""KB-20261125-01 の長尺の表紙 3パターン(第5-2章・第5-3章5・templates/thumb_long_template.md の型D)。
python3 projects/KB-20261125-01/thumb/make_thumbs.py で thumb_A.png・thumb_B.png・thumb_C.png(1280×720)を書き出す。
写真は宮内庁(ledger の確認方法が「キャプション」または「目視確認済(当てっこ係)」のものだけ)。切り抜き・拡大縮小のみ。

型D(左右2枚・お顔はパネル中央 x320・y305・高さ約175px)の決まりはそのままにして、第5-3章5
「表紙の文字は2か所・合計20字前後・最大の文字は2〜5字の語」に合わせ、文字を
  ① 上の帯(白・かぎかっこは宮内庁原文の一節を一字一句。帯の右に小さく出典)
  ② 下の一言(白の短い語＋金のグラデーションの大きな2〜5字の語を1行に)
の2か所にした(金の帯は文字が3か所目になるため使わない)。
  A = 左 雅子さま A025(令和7年 皇后陛下お誕生日のご近影)/右 愛子さま A057(令和7年 愛子内親王殿下お誕生日のご近影)
  B = 令和7年 新年のご一家のご近影 A073 から、左に雅子さま・右に愛子さま(お二人が同じ1枚に写る写真)
  C = 左 平成14年 東宮御所の雅子さまと1歳の愛子さま A065 /右 令和4年3月17日 ご成年の記者会見の愛子さま A061
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline import thumb_long as T
from pipeline.thumb_long import place, text, grad, credit, check_faces, F, W, H, NAVY

A = str(ROOT / "assets/KB-20261125-01") + "/"
O = str(Path(__file__).resolve().parent) + "/"
BAND = 104          # 上の帯の高さ
BASE = 668          # 下の一言のベースライン
SRC_GOLD = (232, 200, 110)


def panel(path, focus, fh=175, extra=(), target=(320, 305)):
    """型Dの決まった位置(パネル中央 x320・y305)に、お顔の高さ fh で置く。extra=同じ写真に写る主役の方のお顔(元の写真のpx)"""
    p = place(path, 640, H, target, fh, focus)
    faces = [place.last_face]
    if extra:
        import cv2
        ih, iw = cv2.imread(path).shape[:2]
        cx, cy, s = focus[0] * iw, focus[1] * ih, fh / (focus[2] * ih)
        faces += [(target[0] + (x - cx) * s, target[1] + (y - cy) * s, w * s, h * s) for (x, y, w, h) in extra]
    return p, faces


def d2(out, left, right, quote, src, parts, cap):
    im = Image.new("RGB", (W, H), NAVY)
    p1, f1 = panel(*left); p2, f2 = panel(*right)
    im.paste(p1, (0, 0)); im.paste(p2, (640, 0))
    ImageDraw.Draw(im).line((640, BAND, 640, H), fill=(10, 20, 45), width=6)
    faces = f1 + [(x + 640, y, w, h) for (x, y, w, h) in f2]
    # ① 上の帯: 白の一節(左寄せ)＋右に小さく出典
    im.paste(grad(W, BAND, [(0, (6, 14, 36)), (1, (16, 32, 68))]), (0, 0))
    d = ImageDraw.Draw(im)
    sw_src = d.textlength(src, font=F(28))
    qx1 = W - 24 - sw_src - 24
    qs = text(im, (24, BAND // 2), quote, 78, anchor="lm", maxw=qx1 - 24, shadow=False)
    text(im, (W - 24, BAND // 2 + 4), src, 28, fill=SRC_GOLD, sw=3, shadow=False, anchor="rm")
    # ② 下の一言: [(文字, 大きさ, "white"/"gold"), ...] を1行に(中央寄せ・同じベースライン)
    ws = [d.textlength(s, font=F(n)) for s, n, _ in parts]
    x = (W - sum(ws)) / 2; boxes = []
    for (s, n, fill), w in zip(parts, ws):
        text(im, (x, BASE), s, n, fill=fill, sw=9 if fill == "gold" else 8, anchor="ls")
        boxes.append(ImageDraw.Draw(im).textbbox((x, BASE), s, font=F(n), anchor="ls", stroke_width=9)); x += w
    bottom = (int(min(b[0] for b in boxes)), int(min(b[1] for b in boxes)), int(max(b[2] for b in boxes)), int(max(b[3] for b in boxes)))
    credit(im, cap, [bottom, (0, 0, W, BAND)])
    im.save(out)
    print(out, "帯の文字", qs, "px / 下の一言の枠", bottom)
    if not check_faces(out, faces, [(0, 0, W, BAND), bottom]):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


# A 実際のお言葉×疑問(題名A): 左 雅子さま(令和7年お誕生日のご近影 A025)/右 愛子さま(令和7年お誕生日のご近影 A057)
#   帯 =「あの幼かった愛子が」(令和3年 皇后陛下お誕生日のご感想の原文の一部)。下 = 7回のご感想のうち「6回」(題名Aの言葉そのまま)
d2(O + "thumb_A.png", (A + "A025.jpg", None), (A + "A057.jpg", None),
   "「あの幼かった愛子が」", "令和3年のご感想より",
   [("7回のご感想のうち", 84, "white"), ("6回", 190, "gold")],
   "写真: 宮内庁 令和7年 皇后陛下お誕生日のご近影(御所)/令和7年 愛子内親王殿下お誕生日のご近影")

# B 数字・事実型(題名B): 令和7年 新年をお迎えになったご一家のご近影(A073・御所)から、左に雅子さま・右に愛子さま
#   お二人が同じ1枚に写る写真(第5-3章5「相手と一緒の写真を優先」)。中央の天皇陛下のお顔はどちらのパネルにも入らない
d2(O + "thumb_B.png", (A + "A073.jpg", (546.5 / 1800, 357.5 / 1200, 133 / 1200)),
   (A + "A073.jpg", (1245.5 / 1800, 342.5 / 1200, 127 / 1200)),
   "18歳から24歳まで", "雅子さまのご感想に書かれた愛子さま",
   [("7回", 200, "gold"), ("のご感想", 112, "white")],
   "写真: 宮内庁 令和7年 新年をお迎えになったご一家のご近影(御所)")

# C 母と娘の物語型(題名C): 左 平成14年 東宮御所の雅子さまと1歳の愛子さま(A065・写真:宮内庁)/右 ご成年の記者会見(A061)
#   右の A061 は縦長の写真で、型Dの大きさ(175px)だとパネルの左右にぼかしの余白が出るため、お顔を約215px・y約333 にしてパネルの幅いっぱいにした
#   (頭の範囲は上の帯と下の一言の間に収まる。check_faces で確認)
#   左は雅子さまのお顔を型Dの位置に置き、抱かれている愛子さまのお顔も check_faces にかける。天皇陛下(当時 皇太子殿下)のお顔はパネルの外
#   帯 =「生まれてきてありがとう」(平成14年4月2日 御誕生につき記者会見の原文の一部)。下 = およそ「20年後」の言葉
d2(O + "thumb_C.png", (A + "A065.jpg", (222 / 338, 52 / 240, 52 / 240), 175, [(153, 56, 45, 45)]),
   (A + "A061.jpg", None, 215, (), (326, 333)),
   "「生まれてきてありがとう」", "平成14年の会見より",
   [("およそ", 92, "white"), ("20年後", 172, "gold"), ("の言葉", 92, "white")],
   "写真: 宮内庁 平成14年 東宮御所(1歳のお誕生日)/令和4年3月17日 ご成年の記者会見(御所大広間)")
