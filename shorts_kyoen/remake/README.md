# 饗宴の儀Shorts 再制作パイプライン（自動化の練習用）

`./run.sh` を実行すると、①〜⑧の工程を順に処理して `output/final.mp4`（1080×1920、約68秒）を書き出します。

| 工程 | 担当 | 入力 → 出力 |
|---|---|---|
| ① 企画作成 | `script.json` の `meta` | 尺・画面サイズ・色・字幕の体裁 |
| ② 台本作成 | `script.json` の `cuts` | 27カットの字幕文・キーワード色・読み・素材区間 |
| ③ 音声作成 | `pipeline/s3_voice.py` | 台本 → カットごとのAI音声（`build/voice/`） |
| ④ ナレーション | `pipeline/s3_voice.py` | 話す速さを自動調整して目標尺に合わせる → `build/narration.wav`、`build/timeline.json` |
| ⑤ 字幕作成 | `pipeline/s5_subtitles.py` | タイムライン → 色分け字幕 `build/subtitles.ass`、確認用 `build/subtitles.srt` |
| ⑥ 画像収集 | `pipeline/s6_images.py` | 自作の背景（金・ピンク）、赤丸と矢印、ぼかしマスク、BGM |
| ⑦ 動画収集 | `pipeline/s7_footage.py` | 素材動画の区間を切り出し、ナレーションの長さに合わせて速度を調整し、全画面か上下帯つきのレイアウトに組む |
| ⑧ 動画編集 | `pipeline/s8_edit.py` | 結合、字幕の焼き込み、ナレーションとBGMのミックス（BGMはナレーション中に自動で下げる） |

## 別の動画に使い回す方法
1. `input/` に素材動画を置き、`script.json` の `source_video` を変更する。
2. `cuts` を書き換える（字幕は `[[語|色名]]` で色分け、誤読する語は `reading` に読みを書く）。
3. 字幕が焼き込まれていない元素材を使う場合は、`source_subtitle_mask` を削除する。
4. `./run.sh` を実行する。

## 必要な環境
- python3：pyopenjtalk、numpy、scipy、pillow
- ffmpeg（libass付き）
- フォント：Noto Sans CJK JP Black（SIL OFL）

## 今回の制約
- 元の素材映像（字幕なし）が手元にないため、⑦の素材には添付された完成動画を使い、焼き込み字幕の帯をぼかして消しています。元素材に差し替えると、ぼかし帯もなくなります。
- 音声は無料のオフライン音声合成（pyopenjtalk）を使っているため、機械的な声です。本番では、商用利用できる音声合成エンジンに `s3_voice.py` の `synth()` だけ差し替えてください。
- BGMは自作の簡易パッド音です。
