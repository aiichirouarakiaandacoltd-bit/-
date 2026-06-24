# 昭和平成 日本再発見 — 動画制作自動化システム

荒木さんがテーマを1つ入力するだけで、YouTube動画制作に必要な17種類のファイルを自動生成するシステム。

---

## クイックスタート

```bash
# 1. セットアップ
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"

# 2. テーマを入力して全素材を生成
python -m generator.main generate \
  --theme "なぜ銭湯は消えたのか" \
  --series "消えた日本シリーズ"

# 3. 生成ファイルを確認
ls videos/
```

---

## 自動生成される17ファイル

| # | ファイル | 内容 |
|---|---------|------|
| 01 | plan.md | 企画案（問い・ターゲット・構成骨格） |
| 02 | titles.md | タイトル案10個 |
| 03 | thumbnail_text.md | サムネイル文言案10個 |
| 04 | script.md | 動画台本（映像指示付き・12分） |
| 05 | narration.md | ナレーション原稿（ルビ・間付き） |
| 06 | subtitles.srt | SRT字幕データ |
| 07 | materials_list.md | 素材リスト（シーン別） |
| 08 | prompts.md | AI画像生成プロンプト |
| 09 | sources.md | 実物画像収集候補 |
| 10 | rights_check.md | 権利確認チェックリスト |
| 11 | editing_structure.md | 動画編集タイムライン |
| 12 | bgm_se.md | BGM・SE指示書 |
| 13 | thumbnail_prompt.md | サムネイル生成プロンプト |
| 14 | description.md | YouTube説明欄（コピペ用） |
| 15 | fixed_comment.md | 固定コメント案 |
| 16 | analytics_template.md | アナリティクス記録テンプレート |
| 17 | improvement_report_template.md | 改善レポートテンプレート |

---

## ドキュメント

- [システム設計書](docs/system_design.md) — フォルダ構成・フロー・ツール選定
- [制作ガイド](docs/production_guide.md) — 荒木さん向け作業手順

---

## パイロット動画

`videos/001_dagashiya/` — **「なぜ駄菓子屋は消えたのか」**（消えた日本シリーズ）

全17ファイル生成済み。台本・ナレーション・字幕・AI画像プロンプトが確認できます。

---

## チャンネルコンセプト

**昭和平成を生きた私たちの記憶を、令和の今の視点で再発見する。**

- 「歴史解説」ではなく「記憶解説」
- 単なる懐古ではなく、失われた日本の価値の再発見
- 全動画に「令和比較」を必ず入れる

---

## 初期10本の制作計画

| シリーズ | 本数 |
|---------|-----|
| 消えた日本 | 3本 |
| 昭和平成テレビ文化 | 3本 |
| 昭和平成の暮らし | 3本 |
| 芸能・音楽・文化系テスト | 1本 |
