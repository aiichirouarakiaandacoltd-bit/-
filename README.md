# 昭和・平成 なぜそうだったのか — 動画自動生成システム Ver1.0

テーマを1行入力するだけで、YouTube動画制作パッケージ（台本・音声・字幕・素材指示・説明欄・権利チェックなど）を自動生成するシステム。

> **このシステムは自動投稿しません。** 投稿・台本確定・最終判断は必ず荒木さんが手動で行ってください。

---

## システム概要

| 項目 | 内容 |
|------|------|
| チャンネル | 昭和・平成 なぜそうだったのか |
| 動画形式 | 横型（1920×1080、H.264/AAC） |
| 標準尺 | 8〜12分 |
| ナレーション | VOICEVOX 青山龍星（speaker ID: 13） |
| BGM | 箕輪レコーズ フリー音源（UNL1337.wav）|
| 台本構成 | 共感→発見→考察→令和比較→余韻（5章） |

---

## 初回セットアップ

### 1. Python環境

Python 3.10 以上を推奨します。

```bash
python --version   # Python 3.10+ であることを確認
```

### 2. 必要ライブラリのインストール

```bash
pip install -r requirements.txt
```

主な依存ライブラリ：

| ライブラリ | 用途 |
|-----------|------|
| anthropic | Claude API（台本生成） |
| Pillow | スライド画像・サムネイル生成 |
| requests | VOICEVOX HTTP API 通信 |
| numpy | 音声処理 |
| scipy | WAVファイル操作 |
| python-dotenv | 環境変数読み込み |

### 3. 環境変数の設定

`.env` ファイルをプロジェクトルートに作成してください：

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

### 4. VOICEVOX の起動方法

1. [VOICEVOX 公式サイト](https://voicevox.hiroshiba.jp/) からインストール
2. VOICEVOX を起動する（タスクトレイに常駐）
3. デフォルトで `http://localhost:50021` で起動します
4. 動作確認：
   ```bash
   curl http://localhost:50021/version
   ```

> ⚠️ VOICEVOX が起動していない場合、システムはエラーで停止します。無断でespeak-ng等への切り替えは行いません。

### 5. BGMファイルの配置

```
assets/
└── bgm/
    └── UNL1337.wav     ← ここに配置（箕輪レコーズ フリー音源）
```

- BGMファイルが存在しない場合、システムはエラーで停止します
- 代替BGMに無断切り替えは行いません

---

## 基本コマンド

### 動画パッケージの生成

```bash
# 基本（VOICEVOX + BGM が必要）
python create_video.py --theme "なぜ昭和の子供は外で遊んでいたのか"

# 話速を変更する場合（デフォルト: 0.87）
python create_video.py --theme "テーマ名" --voicevox-speed 0.90

# BGMファイルを手動指定
python create_video.py --theme "テーマ名" --bgm /path/to/bgm.wav

# 動画レンダリングのみスキップ（音声・字幕は生成）
python create_video.py --theme "テーマ名" --no-video
```

### dry-run（台本・企画確認用）

```bash
# VOICEVOX・BGM不要。台本・タイトル案・サムネイル案などのMarkdownのみ生成
python create_video.py --theme "テスト動画" --dry-run
```

dry-runでは以下がスキップされます：
- VOICEVOX接続チェック・音声生成
- BGMチェック
- スライド画像生成
- サムネイル生成
- 動画レンダリング

---

## 出力ファイル構成

実行すると `videos/NNN_テーマ名/` フォルダが自動作成されます（NNNは連番）。

```
videos/010_テーマ名_xxxx/
├── summary.md                          ← まずここを確認
├── 01_research/
│   └── research.md                     ← 調査メモ・参考情報
├── 02_titles/
│   └── titles.md                       ← タイトル案10個
├── 03_thumbnail/
│   ├── thumbnail_ideas.md              ← サムネイル案5個
│   └── thumbnail.png                   ← 生成サムネイル（本番時）
├── 04_script/
│   └── script.md                       ← 台本（5章構成）
├── 05_voice/
│   ├── narration.wav                   ← ナレーション音声（本番時）
│   └── voice_check.md                  ← 音声チェック用メモ
├── 06_subtitles/
│   └── subtitles.srt                   ← 字幕（本番時）
├── 07_bgm/
│   └── bgm_check.md                    ← BGMチェック用メモ
├── 08_ai_image_prompts/
│   └── prompts.md                      ← AI画像生成プロンプト
├── 09_description/
│   ├── description.md                  ← YouTube説明欄
│   └── fixed_comment.md                ← 固定コメント案
├── 10_rights_check/
│   └── rights_check.md                 ← 権利確認チェックリスト
├── 11_video/
│   ├── output.mp4                      ← 完成動画（本番時）
│   └── video_check.md                  ← 動画チェック用メモ
└── 12_upload_package/
    └── upload_checklist.md             ← 投稿前チェックリスト
```

---

## 実運用フロー（荒木さん向け）

1. **テーマを決める** — チャンネルコンセプトに合うか確認
2. **dry-runを実行** — `python create_video.py --theme "テーマ" --dry-run`
3. **台本を確認** — `04_script/script.md` の内容・事実・数字を確認
4. **タイトル・サムネイル案を確認** — `02_titles/titles.md` / `03_thumbnail/`
5. **本番実行** — VOICEVOX起動・BGM配置済みで `python create_video.py --theme "テーマ"`
6. **音声を確認** — `05_voice/narration.wav` を再生して読み間違い確認
7. **動画を確認** — `11_video/output.mp4` を最初から最後まで視聴
8. **権利確認** — `10_rights_check/rights_check.md` のチェックボックスを確認
9. **投稿チェックリスト** — `12_upload_package/upload_checklist.md` を確認
10. **手動投稿** — YouTubeスタジオから荒木さんが手動で投稿

---

## 実行ログ

実行ログは `logs/` フォルダに保存されます：

```
logs/
└── 20260625_060251_テーマ名.json
```

---

## 重要な制約事項

### 自動投稿禁止
このシステムは自動投稿機能を持ちません。最終確認と投稿は必ず荒木さんが手動で行ってください。

### VOICEVOX必須
- VOICEVOX に接続できない場合はエラーで停止します
- espeak-ng など代替音声への無断切り替えは行いません

### BGM必須
- BGMファイル（`assets/bgm/UNL1337.wav`）が存在しない場合はエラーで停止します
- BGMなしの動画を無断生成しません

### 実在人物の顔生成禁止
- AI画像プロンプト（`08_ai_image_prompts/prompts.md`）には実在人物の顔生成指示を含みません
- 「再現イメージ」テロップが必要な場面は台本内に明記します

### 情報の取り扱い
- 推測と事実を混在させません
- 事実確認できない内容は「未確認」と明記します
- 数字・固有名詞・日付は必ず荒木さんが確認してください

---

## 皇室物語 YouTube運営秘書システム

皇室関連チャンネル（`src/` ディレクトリ）の機能：

```bash
# 宮内庁HP・YouTube RSS から最新情報を収集・スコアリング
python -m src.official_research

# デイリーサマリーを表示
python -m src.daily_summary

# プロジェクト管理（KOSHI-XXXX）
python -m src.project_manager list
python -m src.project_manager add --title "タイトル" --url "URL"
```

---

## ファイル一覧

| ファイル | 説明 |
|---------|------|
| `create_video.py` | メインスクリプト |
| `modules/config.py` | チャンネル設定（話者・BGM音量等） |
| `modules/output_packager.py` | 12フォルダ構造の生成 |
| `modules/script_generator.py` | Claude API による台本生成 |
| `modules/narration_generator.py` | VOICEVOX ナレーション生成 |
| `modules/subtitle_generator.py` | SRT字幕生成 |
| `modules/slide_generator.py` | スライド画像生成（Pillow） |
| `modules/thumbnail_generator.py` | サムネイル生成 |
| `modules/video_renderer.py` | FFmpeg 動画レンダリング |
| `modules/output_writer.py` | テキストファイル出力（旧） |

---

## Ver1.0 更新内容

- 出力フォルダを `videos/NNN_テーマ名/` の12フォルダ構成に変更
- `summary.md` を自動生成（確認すべきファイルの優先順を案内）
- `--dry-run` フラグで VOICEVOX・BGM 不要のテスト実行が可能
- エラー表示に「原因」「荒木さんが次にやること」を明示
- 実行ログを `logs/` に JSON 形式で保存
- VOICEVOX・BGM の強制チェック（無断フォールバック禁止）
