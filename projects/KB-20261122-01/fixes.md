# 直し記録 KB-20261122-01

## 2026-11-22 直し係(rules_check.md の指摘)
- A020 追加:宮内庁 kou26aomori06.jpg(26aomori3.html「会場の様子」・卓球競技)を assets/KB-20261122-01/A020.jpg に保存、ledger.csv に A020 行(人物なし・1000px)
- scenes.json 03-1:images [A009, A006] → [A020, A006]、image A009 → A006、captions を追加(会場全体→観戦のお姿。A020 区間 約2.06秒)
- scenes.json 07-1:images [A013, A010] → [A014, A010]、image A013 → A014、captions 更新(回答章の冒頭を 01-2・06-1 で未使用の画像に)
- script.md:場面表 03-1・03-2(A008→A009)・07-1、写真枚数、要確認を scenes.json に合わせた
- rules_check.md:A006 照合済みを追記、直し係の対応と「判定: 合格」に更新
- ナレーションは変えていない(measure_narration 合計 55.78秒)

## 2026-11-22 直し係(output/frames_check.md の指摘: 03-2 の A009 でお顔が見分けられない)
- scenes.json 03-1:images [A020, A006] → [A020, A009]、image A006 → A020、crop 全身 → 全体、captions を A020・A009 に、labels は A020 のみ ""(A009 は天皇皇后両陛下。A009 は会場全体として使う)
- scenes.json 03-2:image A009 → A006(お顔がはっきり写る卓球観戦の写真)、crop 顔の寄りのまま、caption は同じ会場の撮影情報
- 確認:カット順 A005→A020→A009→A006→A010 で隣り合う同じ写真なし。最多は A017・A001・A010・A014 の各2回(3回以内)。A006・A009 は focus.json 登録済み
- script.md:場面表 03-1・03-2 と要確認を scenes.json に合わせた。ナレーションは変えていない
- 再書き出しは未実施(書き出し係の render 待ち)
