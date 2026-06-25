# ザ・ダンク 動画制作自動化システム

バスケットボールYouTube Shortsチャンネル「ザ・ダンク」の動画制作を自動化するシステムです。

## 機能

- 台本自動生成（技術解説・戦術解説・比較・記録など）
- VOICEVOX音声合成
- 字幕焼き込み（ASS形式）
- BGMミキシング
- コート図・テキストカード自動生成
- 品質検査（ffprobe・decode検査・0KB検査）
- 投稿用メタデータ生成
- 選手名正規化

## セットアップ

### 必要なソフトウェア

- Python 3.9以上
- FFmpeg（ffprobe含む）
- VOICEVOX（本番モード）
- Pillow（`pip install Pillow`）

### フォルダ構成

```
the-dunk-video-automation/
├── main.py              # メインエントリーポイント
├── config/              # 設定ファイル
├── inputs/              # 入力素材
│   ├── owned_videos/    # 権利OK動画
│   ├── licensed_videos/ # ライセンス済み動画
│   ├── images/          # 画像素材
│   ├── scripts/         # 台本ファイル
│   └── topics/          # 企画ファイル
├── outputs/             # 出力（本番・テスト分離）
│   ├── production/
│   └── test/
├── output/              # 最終動画（final.mp4）
├── lib/                 # ライブラリ
└── screenshots/         # 確認用スクリーンショット
```

## 使い方

### Windows

1. VOICEVOXを起動する
2. 権利OK素材を `inputs/owned_videos/` へ置く
3. `check_environment.bat` をダブルクリック → PASSを確認
4. `run_production.bat` をダブルクリック
5. `output/final.mp4` を確認

### コマンドライン

```bash
# テストモード（VOICEVOX不要）
python main.py

# テーマ指定
python main.py --topic "河村勇輝のノールックパスが凄い理由" --mode production

# 選手指定
python main.py --player "河村勇輝" --mode production

# ローカル動画指定
python main.py --video inputs/owned_videos/sample.mp4 --mode production

# 台本指定
python main.py --script-file inputs/scripts/script.txt --video inputs/owned_videos/sample.mp4
```

## モード

- **production**: VOICEVOX必須、権利確認済みBGM必須、全品質チェック
- **test**: テスト音声使用可、技術検証用（TEST ONLY、投稿不可）

## 動画仕様

- 9:16（1080×1920）
- 30fps
- 45〜59.5秒
- H.264 / AAC
- 字幕焼き込み

## 権利について

- `owned` / `owned_alias` / `licensed` 素材のみ完成MP4に使用可能
- `reference_only` 素材は企画分析・参考専用
- 第三者素材の無断取得・使用禁止
