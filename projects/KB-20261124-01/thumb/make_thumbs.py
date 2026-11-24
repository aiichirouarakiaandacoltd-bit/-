"""KB-20261124-01 の長尺の表紙 3パターン(第5-2章・templates/thumb_long_template.md の型D)。
python3 projects/KB-20261124-01/thumb/make_thumbs.py で thumb_A.png・thumb_B.png・thumb_C.png(1280×720)を書き出す。
写真は宮内庁(英国ご訪問 報告 7日目・写真内の表記 John Cairns)。切り抜き・拡大縮小のみ。文字はそれぞれのタイトルの言葉から取る。
2026-11-24 直し係: 競合の深掘り調査の反映で作り直し。
  A = お二人が同じガウンで並ぶ A049 を、お二人が入る幅で1枚(型Dの写真1枚版・文字は上の帯と下の金の一言の2か所)
  B = 型D(左: 市内を歩かれるお二人 A050 / 右: 授与式の会場 A048)
  C = 型D(左: ベイリオル・コレッジのお二人 A047 / 右: マートン・コレッジの桜の植樹式 A051)。お顔が小さい A052 は使わない"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline import thumb_long as T
from pipeline.thumb_long import type_D, place, text, grad, credit, check_faces, W, H, NAVY

A = str(ROOT / "assets/KB-20261124-01") + "/"
O = str(Path(__file__).resolve().parent) + "/"


def type_D_wide(out, img, mid, face_h, faces_src, top, big, cap, target=(640, 285)):
    """型Dの写真1枚版(お二人が1枚に並ぶ写真用): 写真を画面いっぱいに置き、文字は上の帯(白)と下の金の一言の2か所だけ。
    mid=(x割合,y割合,顔の高さ割合): お二人のお顔の中間点と、お顔の高さ。faces_src=[(x割合,y割合)]: お一人ずつのお顔の中心(見切れ・文字との重なりの検査用)"""
    im = place(img, W, H, target, face_h, mid)
    iw, ih = Image.open(img).size
    s = face_h / (mid[2] * ih)
    faces_ = [(target[0] + (fx - mid[0]) * iw * s - face_h / 2, target[1] + (fy - mid[1]) * ih * s - face_h / 2, face_h, face_h)
              for fx, fy in faces_src]
    im.paste(grad(W, 100, [(0, (6, 14, 36)), (1, (16, 32, 68))]), (0, 0))
    ImageDraw.Draw(im).rectangle((0, 100, W, 105), fill=(216, 188, 114))      # 金の細い帯(上の帯の縁)
    text(im, (W // 2, 50), top, 80, anchor="mm", maxw=1220, shadow=False)
    text(im, (W // 2, 590), big, 150, fill="gold", sw=9, anchor="mm", maxw=1200)
    credit(im, cap, [(40, 505, 1240, 680)]); im.save(out)
    assert check_faces(out, faces_, [(0, 0, W, 105), (40, 505, 1240, 720)]), out


# A 実際のお言葉×疑問(型Dの写真1枚版): 名誉学位授与式で同じガウンをお召しになり並んで歩かれるお二人(A049)
type_D_wide(O + "thumb_A.png", A + "A049.jpg", (0.605, 0.44, 0.10), 140, [(0.49, 0.435), (0.722, 0.45)],
            "陛下が会見で「雅子にも」", "同じ博士号とは？",
            "写真: 宮内庁(写真内の表記 John Cairns) 2024.6.28 オックスフォード 名誉学位授与式")
# B 数字・事実型(型D): 同じ日にオックスフォード市内を歩かれるお二人(A050)と、名誉学位授与式の会場(A048・場所として)
type_D(O + "thumb_B.png", A + "A050.jpg", (0.345, 0.49, 0.062), A + "A048.jpg", (0.512, 0.52, 0.20, "scene"),
       "平成3年と令和6年", "同じ博士号", "お二人が同じガウンで臨まれた日",
       "写真: 宮内庁(写真内の表記 John Cairns) 2024.6.28 オックスフォード市内・名誉学位授与式")
# C 実際のお言葉×物語(型D): ベイリオル・コレッジのお二人(A047)と、マートン・コレッジの桜の植樹式(A051・場所として)
type_D(O + "thumb_C.png", A + "A047.jpg", (0.235, 0.36, 0.165), A + "A051.jpg", (0.545, 0.42, 0.243, "scene"),
       "陛下が語られた", "「唯一避ける話題」", "雅子さまと語り合う留学の思い出",
       "写真: 宮内庁(写真内の表記 John Cairns) 2024.6.28 ベイリオル・コレッジ/マートン・コレッジ")
