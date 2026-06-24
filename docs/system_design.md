# システム設計書：昭和平成 日本再発見 動画制作自動化

---

## 1. 推奨フォルダ構成

```
/（リポジトリルート）
├── system/
│   ├── config/
│   │   ├── channel_config.json      # チャンネル設定・禁止事項・トーン
│   │   ├── series_config.json       # シリーズ別設定
│   │   └── tone_guide.json          # トーン・文体ガイドライン
│   ├── templates/                   # （将来：Jinja2テンプレート）
│   └── prompts/                     # （将来：プロンプトテンプレート）
│
├── generator/
│   ├── main.py                      # CLIエントリーポイント
│   ├── config.py                    # 設定読み込み
│   └── generators/
│       ├── base.py                  # Claude API呼び出しベース
│       ├── plan_generator.py        # ①企画・タイトル・サムネイル文言
│       ├── script_generator.py      # ②台本・ナレーション
│       ├── subtitle_generator.py    # ③字幕
│       ├── materials_generator.py   # ④素材リスト・AI画像プロンプト・調査
│       ├── editing_generator.py     # ⑤編集構成・BGM・サムネイルプロンプト
│       └── youtube_generator.py     # ⑥説明欄・コメント・アナリティクス
│
├── videos/
│   └── [video_id]/                  # 動画1本ごとのフォルダ
│       ├── input.json               # テーマ・シリーズ・設定
│       ├── 01_plan/plan.md
│       ├── 02_titles/titles.md
│       ├── 03_thumbnail_text/thumbnail_text.md
│       ├── 04_script/script.md
│       ├── 05_narration/narration.md
│       ├── 06_subtitles/subtitles.srt
│       ├── 07_materials/materials_list.md
│       ├── 08_ai_image_prompts/prompts.md
│       ├── 09_research_sources/sources.md
│       ├── 10_rights_check/rights_check.md
│       ├── 11_editing_structure/editing_structure.md
│       ├── 12_bgm_se/bgm_se.md
│       ├── 13_thumbnail_prompt/thumbnail_prompt.md
│       ├── 14_youtube_description/description.md
│       ├── 15_fixed_comment/fixed_comment.md
│       ├── 16_analytics_template/analytics_template.md
│       └── 17_improvement_report/improvement_report_template.md
│
├── docs/
│   ├── system_design.md             # 本ファイル
│   ├── production_guide.md          # 荒木さん向け制作ガイド
│   └── pilot_guide.md               # パイロット動画制作手順
│
├── requirements.txt                 # Python依存ライブラリ
└── README.md
```

---

## 2. 必要なファイル一覧

### システムコア
| ファイル | 役割 | 優先度 |
|---------|-----|--------|
| `system/config/channel_config.json` | チャンネル全体設定 | 必須 |
| `system/config/series_config.json` | 各シリーズの設定 | 必須 |
| `system/config/tone_guide.json` | トーン・禁止表現・推奨表現 | 必須 |
| `generator/main.py` | CLI（テーマ入力 → 自動生成） | 必須 |
| `generator/config.py` | 設定読み込み | 必須 |
| `generator/generators/*.py` | 各出力物の生成ロジック | 必須 |
| `requirements.txt` | Python環境設定 | 必須 |

### 動画1本あたり（自動生成）
計17ファイル（01_plan〜17_improvement_report）

---

## 3. 入力テンプレート

### `input.json` 形式

```json
{
  "video_id": "001_dagashiya",
  "theme": "なぜ駄菓子屋は消えたのか",
  "series": "消えた日本シリーズ",
  "length_min": 12,
  "status": "draft",
  "created": "2026-06-24"
}
```

### CLIからの入力方法
```bash
python -m generator.main generate \
  --theme "なぜ駄菓子屋は消えたのか" \
  --series "消えた日本シリーズ" \
  --length 12
```

---

## 4. 出力テンプレート（17項目）

| # | ファイル | 内容 | 担当ジェネレーター |
|---|---------|-----|-----------------|
| 01 | plan.md | 企画案（核となる問い・ターゲット・構成骨格） | plan_generator |
| 02 | titles.md | タイトル案10個（A/Bテスト候補付き） | plan_generator |
| 03 | thumbnail_text.md | サムネイル文言案10個 | plan_generator |
| 04 | script.md | 動画台本（映像指示+ナレーション込み） | script_generator |
| 05 | narration.md | ナレーション原稿のみ（ルビ・間・収録メモ付き） | script_generator |
| 06 | subtitles.srt | SRT字幕データ | subtitle_generator |
| 07 | materials_list.md | 素材リスト（シーン別・タイプ別・優先度） | materials_generator |
| 08 | prompts.md | AI画像生成プロンプト（Midjourney/DALL-E） | materials_generator |
| 09 | sources.md | 実物画像・資料収集候補（アーカイブ・有料サイト） | materials_generator |
| 10 | rights_check.md | 権利確認チェックリスト | materials_generator |
| 11 | editing_structure.md | 動画編集タイムライン・テロップ・エンドカード設計 | editing_generator |
| 12 | bgm_se.md | BGM・SE指示書（フリー素材サイト付き） | editing_generator |
| 13 | thumbnail_prompt.md | サムネイル生成プロンプト（3パターン） | editing_generator |
| 14 | description.md | YouTube説明欄（コピペ用・ハッシュタグ付き） | youtube_generator |
| 15 | fixed_comment.md | 固定コメント案（3パターン） | youtube_generator |
| 16 | analytics_template.md | 投稿後アナリティクス記録テンプレート | youtube_generator |
| 17 | improvement_report_template.md | 改善レポートテンプレート | youtube_generator |

---

## 5. 自動生成フロー

```
荒木さん：テーマ入力
      ↓
[Phase 1] 企画生成
  └── plan_generator.py
       → 企画案・タイトル10個・サムネイル文言10個

[Phase 2] 台本生成
  └── script_generator.py（企画案を参照）
       → 動画台本（12分・5段構成）
       → ナレーション原稿

[Phase 3] 字幕生成
  └── subtitle_generator.py（ナレーションを参照）
       → SRTファイル

[Phase 4] 素材・調査
  └── materials_generator.py（台本を参照）
       → 素材リスト
       → AI画像プロンプト
       → 実物画像収集候補
       → 権利確認メモ

[Phase 5] 編集・サムネイル
  └── editing_generator.py
       → 編集構成タイムライン
       → BGM・SE指示
       → サムネイル生成プロンプト

[Phase 6] YouTube素材
  └── youtube_generator.py
       → 説明欄
       → 固定コメント
       → アナリティクステンプレート
       → 改善レポートテンプレート

      ↓
荒木さん：全ファイルを確認・修正
      ↓
AI画像生成・実物素材収集
      ↓
動画編集（DaVinci Resolve等）
      ↓
荒木さん：最終確認・投稿
```

---

## 6. 使用するツール候補

### 自動生成エンジン
| ツール | 用途 | 費用感 |
|-------|-----|--------|
| **Claude API（claude-opus-4-8）** | テキスト生成全般 | APIトークン課金 |
| Python + Click | CLIインターフェース | 無料 |
| Rich | ターミナル出力 | 無料 |

### AI画像生成
| ツール | 用途 | 費用感 |
|-------|-----|--------|
| **Midjourney** | 高品質な昭和日本の再現画像 | 月額$10〜 |
| **DALL-E 3（ChatGPT Plus）** | 補助的な画像生成 | 月額$20 |
| Adobe Firefly | 商用利用に安心 | Adobe CC契約者 |

### 動画編集
| ツール | 用途 | 費用感 |
|-------|-----|--------|
| **DaVinci Resolve** | メイン編集 | 無料版で十分 |
| Adobe Premiere Pro | Adobe CC契約者 | CC契約 |

### サムネイル制作
| ツール | 用途 | 費用感 |
|-------|-----|--------|
| **Canva** | テンプレート活用・素早い制作 | 無料（Pro推奨） |
| Photoshop | 高度な編集 | Adobe CC契約 |

### BGM・SE
| サイト | 特徴 | 費用感 |
|-------|-----|--------|
| DOVA-SYNDROME | 豊富・商用可 | 無料 |
| 甘茶の音楽工房 | ノスタルジー系が豊富 | 無料 |
| Pixabay Music | クレジット不要多数 | 無料 |

---

## 7. 動画生成までの処理手順

1. **テーマ入力**（荒木さん）
   ```bash
   python -m generator.main generate --theme "銭湯が消えた理由"
   ```

2. **全ファイル自動生成**（約10〜15分）
   - 17ファイルが `videos/[id]/` に生成される

3. **企画確認**（荒木さん）
   - `01_plan/plan.md` を確認。方向性を修正

4. **台本確認・修正**（荒木さん）
   - `04_script/script.md` を確認・微修正
   - 不正確な数字・事実を確認

5. **素材収集**（荒木さん）
   - `07_materials/` の素材リストを元に収集
   - `08_ai_image_prompts/` のプロンプトでAI画像生成
   - `09_research_sources/` を元に実物画像を収集

6. **権利確認**（荒木さん）
   - `10_rights_check/rights_check.md` のチェックリストを実施

7. **動画編集**（荒木さん）
   - `11_editing_structure/` のタイムラインを参照
   - `12_bgm_se/` の指示でBGM選定
   - `05_narration/` のナレーション収録またはTTS使用

8. **最終確認・投稿**（荒木さん）
   - `14_youtube_description/` の説明欄をコピペ
   - 投稿後に `15_fixed_comment/` の固定コメントを設置

---

## 8. サムネイル生成までの処理手順

1. `13_thumbnail_prompt/thumbnail_prompt.md` を開く
2. **A案（推奨）** のMidjourneyプロンプトをコピー
3. Midjourneyで背景画像を生成（`--ar 16:9`）
4. Canvaに取り込み、テキストを追加
   - サムネイル文言は `03_thumbnail_text/thumbnail_text.md` から選択
5. AI画像使用時は「再現イメージ」を左下に追加
6. **A案・B案の2種類を用意**してA/Bテスト
7. 投稿時にどちらか1つをアップロード。1週間後にもう一方に切り替えてCTRを比較

---

## 9. YouTube分析連携の設計

### 投稿直後〜1週間
- `16_analytics_template/analytics_template.md` を開く
- YouTubeアナリティクスから数値を転記
- CTRが4%未満 → サムネイルをB案に切り替え

### 1ヶ月後
- 視聴者層・離脱ポイントを分析
- `17_improvement_report/improvement_report_template.md` に記入

### 分析から次回制作へのフィードバックループ
```
投稿 → 分析 → 改善レポート記入 → 次回テーマ選定 → 改善された制作 → 投稿
```

### 将来的な自動化拡張（Phase 2）
- YouTube Data API v3 との連携
- アナリティクスデータの自動取込
- 改善提案の自動生成（Claude APIが分析レポートを自動作成）

---

## 10. 最初のパイロット動画制作手順

### テーマ：「消えた日本」なぜ駄菓子屋は消えたのか

**ステップ1（完了）** システム全体設計とファイル生成
- 本システムの全ファイルを作成済み
- `videos/001_dagashiya/` に全17ファイルを手動生成済み

**ステップ2（荒木さん）** ファイル確認
- `04_script/script.md` — 台本の内容・事実確認
- `02_titles/titles.md` — タイトルを1本選ぶ
- `03_thumbnail_text/thumbnail_text.md` — サムネイル文言を選ぶ

**ステップ3（荒木さん）** AI画像生成
- `08_ai_image_prompts/prompts.md` のプロンプトでMidjourneyまたはDALL-E使用
- 生成画像を `videos/001_dagashiya/assets/ai_images/` に保存

**ステップ4（荒木さん）** 実物画像収集
- `09_research_sources/sources.md` を参照
- 優先度「高」の素材を収集

**ステップ5（荒木さん）** BGM選定
- `12_bgm_se/bgm_se.md` を参照
- DOVA-SYNDROME または甘茶の音楽工房から選定

**ステップ6（荒木さん）** ナレーション収録 or TTS
- `05_narration/narration.md` を元に収録
- TTS使用の場合：VOICEVOX、CoeFont、ElevenLabs等を検討

**ステップ7（荒木さん）** 動画編集
- `11_editing_structure/editing_structure.md` のタイムラインを参照
- `06_subtitles/subtitles.srt` を字幕として読み込み

**ステップ8（荒木さん）** 最終確認・投稿
- `10_rights_check/rights_check.md` のチェックリストを実施
- タイトル・説明欄（`14_youtube_description/description.md`）を設定
- 投稿後に `15_fixed_comment/fixed_comment.md` の固定コメントを設置

**ステップ9（1週間後）** 分析
- `16_analytics_template/analytics_template.md` にデータ記入
