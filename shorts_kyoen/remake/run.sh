#!/usr/bin/env bash
# 全工程を順に実行する。前提：python3（pyopenjtalk numpy scipy pillow）、ffmpeg（libass付き）、
# フォント Noto Sans CJK JP Black がインストール済み。素材動画は input/orig.mp4 に置く。
set -euo pipefail
cd "$(dirname "$0")/pipeline"
mkdir -p ../build ../output
python3 s3_voice.py       # ③④ 音声作成・ナレーション → build/narration.wav, timeline.json
python3 s5_subtitles.py   # ⑤ 字幕作成 → build/subtitles.ass, .srt
python3 s6_images.py      # ⑥ 画像（背景・赤丸矢印）・BGM → build/img, bgm.wav
python3 s7_footage.py     # ⑦ 動画素材の切り出し → build/clips
python3 s8_edit.py        # ⑧ 編集・書き出し → output/final.mp4
