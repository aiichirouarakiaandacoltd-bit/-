# Imperial Video Automation

「日本が誇る皇室物語」チャンネル用の動画自動生成システム。

## 必要環境

- Python 3.9+
- FFmpeg (libass対応)
- VOICEVOX (本番モード)
- BGMファイル: `assets/bgm/UNL1337.wav` (本番モード)
- 日本語フォント (IPAGothic等)

## セットアップ

```bash
pip install -r requirements.txt
```

## 使い方 (Windows)

1. VOICEVOXを起動する
2. `UNL1337.wav` を `assets/bgm/` に配置する
3. `check_environment.bat` をダブルクリックして環境確認
4. `run_production.bat` をダブルクリックして動画生成
5. `output/` フォルダの完成MP4を確認

## コマンドライン

```bash
# 環境チェックのみ
python main.py --preflight-only

# テストモード (VOICEVOX/BGM不要)
python main.py --test-mode

# 本番モード (VOICEVOX・BGM必須)
python main.py
```

## 出力ファイル

| ファイル | 内容 |
|---|---|
| `final_long.mp4` | 長尺動画 (1920x1080, 480-720秒) |
| `final_shorts.mp4` | Shorts動画 (1080x1920, 45-59.5秒) |
| `script.txt` | 台本 |
| `narration.txt` | ナレーション文 |
| `subtitles.srt` | 字幕ファイル |
| `description.txt` | 概要欄テキスト |
| `credits.txt` | クレジット |
| `materials.json` | 素材一覧 |
| `rights_report.md` | 素材権利レポート |
| `quality_report.json` | 品質検査結果 |
| `execution.log` | 実行ログ |
| `status.json` | 実行ステータス |

## 禁止事項

- 皇族・王族のAI生成顔の使用
- 顔合成、表情変更、服装変更、年齢変更
- 実在人物を別人で代用
- 皇族の内心断定
- 根拠のない煽り
- 権利不明素材の使用
