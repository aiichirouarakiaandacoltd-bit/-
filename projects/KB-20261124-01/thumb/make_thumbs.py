"""KB-20261124-01 の長尺の表紙 3パターン(第5-2章・templates/thumb_long_template.md の型R/型D)。
python3 projects/KB-20261124-01/thumb/make_thumbs.py で thumb_A.png・thumb_B.png・thumb_C.png(1280×720)を書き出す。
写真は宮内庁(英国ご訪問 報告 7日目)。切り抜き・拡大縮小のみ。文字はそれぞれのタイトルの言葉から取る。"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.thumb_long import type_R, type_D

A = str(ROOT / "assets/KB-20261124-01") + "/"
O = str(Path(__file__).resolve().parent) + "/"

# A 強い疑問型(型R・人物1名): 名誉学位授与式の雅子さま(A049)
type_R(O + "thumb_A.png", A + "A049.jpg", (0.505, 0.43, 0.10), "雅子さま", "陛下と同じ大学から", "贈られたものとは？",
       "写真: 宮内庁 2024.6.28 オックスフォード 名誉学位授与式", face_h=200)
# B 数字・事実型(型D): 同じ日のオックスフォード市内のお二人(A050)と、その日の最後に英国をご出発のお二人(A053)
type_D(O + "thumb_B.png", A + "A050.jpg", (0.35, 0.49, 0.05), A + "A053.jpg", (0.565, 0.33, 0.082),
       "初めてお二人で", "雅子さま34年ぶり", "オックスフォードの一日",
       "写真: 宮内庁 2024.6.28 オックスフォード市内・ブライズ・ノートン空軍基地")
# C 人物の物語型(型D): マートン(陛下が過ごされたお部屋 A052)とベイリオル(A047)
type_D(O + "thumb_C.png", A + "A052.jpg", (0.655, 0.485, 0.075), A + "A047.jpg", (0.345, 0.34, 0.12),
       "お二人の留学の地", "マートンとベイリオル", "語られた思い出",
       "写真: 宮内庁 2024.6.28 マートン・コレッジ/ベイリオル・コレッジ")
