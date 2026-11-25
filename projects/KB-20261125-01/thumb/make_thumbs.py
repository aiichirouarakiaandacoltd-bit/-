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
  C = 左 雅子さま A021(令和6年 皇后陛下お誕生日のご近影)/右 令和4年3月17日 ご成年の記者会見の愛子さま A061
2026-11-25 直し係(rules_check.md 12. G6 の指摘): B の帯右を出典の形にし、陛下のお召し物が出ない切り抜きに。C の左を A065(338px)から A021(1000px)に。クレジットの右余白を 24px に。
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
CREDIT_RIGHT = 24   # クレジットの右の余白(G6 の指摘で 20px以上に)


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
    credit(im, cap, [bottom, (0, 0, W, BAND)], right=CREDIT_RIGHT)
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
#   お二人が同じ1枚に写る写真(第5-3章5「相手と一緒の写真を優先」)。中央の天皇陛下はお顔もお召し物もどちらのパネルにも入れない:
#   元の写真で陛下のお召し物は x約690〜1090。左パネルの右端を x約686、右パネルの左端を x約1094 で切るため、
#   お顔の位置を境目寄り(左パネル x457・右パネル x209)に置く。大きさ(約175px)と高さ(y305)は型Dのまま
#   帯の右は出典(令和元年〜令和7年の7回のご感想 = K1〜K7)。文字は 上の帯10字＋下の一言6字＝16字の2か所
B_L, B_R = (546.5, 357.5, 133), (1245.5, 342.5, 127)
d2(O + "thumb_B.png", (A + "A073.jpg", (B_L[0] / 1800, B_L[1] / 1200, B_L[2] / 1200), 175, (), (round(640 - (686 - B_L[0]) * 175 / B_L[2]), 305)),
   (A + "A073.jpg", (B_R[0] / 1800, B_R[1] / 1200, B_R[2] / 1200), 175, (), (round((B_R[0] - 1094) * 175 / B_R[2]), 305)),
   "18歳から24歳まで", "令和元年〜令和7年のご感想より",
   [("7回", 200, "gold"), ("のご感想", 112, "white")],
   "写真: 宮内庁 令和7年 新年をお迎えになったご一家のご近影(御所)")

# C 母と娘の物語型(題名C): 左 雅子さま(令和6年 皇后陛下お誕生日のご近影 A021・長辺1000px)/右 ご成年の記者会見の愛子さま(A061)
#   左は G6 の指摘で A065(平成14年・長辺338px)から差し替え。台帳の平成14年の写真はどれも長辺240〜338pxで主役に使えないため、
#   「生まれてきてありがとう」を語られた雅子さまお一人のご近影にした(表紙A の A025・表紙B の A073 とは別の写真)。
#   言葉は平成14年・写真は令和6年なので、帯の出典「平成14年の会見より」とクレジット「令和6年」で年を分けて示す
#   右の A061 は縦長の写真で、型Dの大きさ(175px)だとパネルの左右にぼかしの余白が出るため、お顔を約215px・y約333 にしてパネルの幅いっぱいにした
#   (頭の範囲は上の帯と下の一言の間に収まる。check_faces で確認)
#   帯 =「生まれてきてありがとう」(平成14年4月2日 御誕生につき記者会見の原文の一部)。下 = およそ「20年後」の言葉
#   左の A021 は等倍(お顔 約175px)。型Dの x320 だとパネル右端に約28pxのぼかしの余白が出るため、x350 に置いて写真でパネルを埋めた
d2(O + "thumb_C.png", (A + "A021.jpg", None, 175, (), (350, 305)),
   (A + "A061.jpg", None, 215, (), (326, 333)),
   "「生まれてきてありがとう」", "平成14年の会見より",
   [("およそ", 92, "white"), ("20年後", 172, "gold"), ("の言葉", 92, "white")],
   "写真: 宮内庁 令和6年 皇后陛下お誕生日のご近影(御所)/令和4年3月17日 ご成年の記者会見(御所大広間)")
