# 昭和・平成 なぜそうだったのか - 自動動画制作システム

昭和・平成の暮らし、文化、社会について「なぜ当時はそうだったのか」を解説するYouTube動画を、企画入力からMP4出力まで一気通貫で自動生成するシステムです。

## システム概要

- 企画生成・スコアリング → 調査 → ファクトチェック → 台本生成 → ナレーション音声生成 → 字幕SRT生成 → 画像素材生成 → BGM生成 → 動画編集 → MP4書き出し → ffprobe技術検証
- 長尺動画（16:9 / 1920×1080）とShorts動画（9:16 / 1080×1920）を1コマンドで生成
- テーマ未指定時は自動企画モードで最適テーマを選定

## 必要環境

- Python 3.9以上
- FFmpeg
- espeak-ng（オフラインTTS）
- VOICEVOX（任意、起動時に自動検出）

### Python依存ライブラリ

```
moviepy
pillow
pydub
numpy
```

## セットアップ

```bash
# FFmpeg
sudo apt-get install ffmpeg

# espeak-ng（オフラインTTS）
sudo apt-get install espeak-ng

# Python依存
pip install moviepy pillow pydub numpy

# VOICEVOX（任意）
# https://voicevox.hiroshiba.jp/ からダウンロード・起動
# 起動後、自動的に検出されます
```

### 使用フォント

以下の優先順位で自動検出:
1. `assets/fonts/NotoSansJP-Bold.ttf`（配置推奨）
2. IPAゴシック（システムフォント）

太字日本語ゴシックフォントを `assets/fonts/` に配置すると字幕品質が向上します。

### APIキー設定

外部APIは不要です。全機能がオフラインで動作します。
VOICEVOX使用時は `VOICEVOX_URL` 環境変数で接続先を指定（デフォルト: `http://localhost:50021`）。

### BGM取得方法

- `assets/bgm/` にWAV/MP3ファイルを配置すると自動使用
- ファイルがない場合はアンビエントBGMを自動生成（商用利用可）

## 入力方法

`input/input.json` を編集:

```json
{
  "theme": "なぜ昭和のテレビには布をかけていたのか",
  "format": "long_and_shorts",
  "long_minutes": 9,
  "shorts_count": 2,
  "target": "50歳以上の日本人",
  "tone": "懐かしく、落ち着いた解説",
  "priority": "常緑型"
}
```

## 実行方法

```bash
# 基本実行（input.jsonから読み込み）
python3 main.py

# テーマ直接指定
python3 main.py "なぜ給食で脱脂粉乳が出たのか"

# 自動企画モード（themeを空にする）
# input.jsonのthemeを空文字列にして実行
```

### 長尺生成

`format` を `"long"` に設定。

### Shorts生成

`format` を `"shorts"` に設定。`shorts_count` で本数指定。

### 長尺+Shorts一括生成

`format` を `"long_and_shorts"` に設定（デフォルト）。

## 素材ルール

- AI生成画像には「※イメージ」を表示
- 実在人物の顔をAI再現しない
- ウォーターマーク付き素材を使用しない
- 権利状態をOK/REVIEW/NGで管理

## 出力ファイル構成

```
output/video_001/
  input.json              # 入力設定
  idea_analysis.json      # 企画分析
  research.json           # 調査資料
  fact_check.json         # ファクトチェック
  script_long.txt         # 長尺台本
  script_short_01.txt     # Shorts台本
  narration_long.txt      # ナレーション原稿
  voice_long.wav          # 音声ファイル
  subtitle_long.srt       # 字幕SRT
  title_candidates.txt    # タイトル案
  description.txt         # 概要欄
  hashtags.txt            # ハッシュタグ
  pinned_comment.txt      # 固定コメント
  thumbnail_text.txt      # サムネイル文言
  source_list.csv         # 使用素材一覧
  rights_check.csv        # 権利確認一覧
  editing_plan.json       # 編集計画
  final_long.mp4          # 長尺完成動画
  final_short_01.mp4      # Shorts完成動画
  execution.log           # 実行ログ
```

## エラー対処

- 素材不足: 代替画像を自動生成
- 音声生成失敗: espeak-ng → 無音フォールバック
- BGM取得失敗: 自動生成BGM → BGMなし
- FFmpeg失敗: 詳細エラーをexecution.logに記録
- フォント不足: システムフォントにフォールバック

## 動画確認方法

ffprobe検証が自動実行されます。手動確認:

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,channels -show_entries format=duration -of json output/video_001/final_long.mp4
```

## 設定変更方法

- `src/config.py`: 解像度、FPS、音量、フォントパス等
- `input/input.json`: テーマ、形式、Shorts本数等
- 環境変数 `TTS_ENGINE`: `voicevox` / `espeak` / `auto`（デフォルト: `gtts`）
- 環境変数 `VOICEVOX_SPEAKER`: VOICEVOXの話者ID
