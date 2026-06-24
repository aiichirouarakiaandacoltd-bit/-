# YouTube運営秘書システム

「日本が誇る皇室物語」チャンネルの運営を支援する自動化システムです。
毎日の公式情報確認から、企画候補化、優先順位付け、制作TODO化、過去動画との重複確認までを行います。

**重要: 自動投稿は行いません。最終判断、台本確定、投稿判断は必ず荒木が行います。**

## チャンネル方針

「公式事実で、静かな感動を。」

- 対象視聴者: 55歳以上、特に65歳以上女性
- 公式情報のみ使用（個人ブログ、Wikipedia、週刊誌、まとめサイトは不可）

## セットアップ

### 前提条件

- Python 3.10以上

### インストール

```bash
pip install -r requirements.txt
```

## 使い方

### 毎日の公式情報リサーチ

```bash
python src/official_research.py
```

宮内庁公式HPから新着情報を取得し、以下を自動生成します:
- 新着情報一覧
- 人物別分類
- AI企画ランキング（100点満点）
- 過去動画との重複判定
- 本日のTODO
- Markdownレポート（`outputs/daily_official_research/` に保存）

### 人物別確認

```bash
# 人物一覧
python src/research_dashboard.py --list

# 特定人物の過去90日間の情報
python src/research_dashboard.py --person 愛子さま --days 90

# 全人物サマリー
python src/research_dashboard.py --all --days 30
```

### 企画管理

```bash
# 企画を追加
python src/project_manager.py add --title "愛子さまが地方公務で見せた一礼" --person "愛子さま" --format Shorts --source-url "公式URL"

# 企画一覧
python src/project_manager.py list

# ステータスでフィルタ
python src/project_manager.py list --status 企画候補

# 企画を更新
python src/project_manager.py update --id KOSHI-0001 --status 外注依頼済み

# 企画詳細
python src/project_manager.py show --id KOSHI-0001
```

## ディレクトリ構成

```
src/
├── official_research.py       # メイン実行スクリプト
├── fetch_kunaicho.py          # 宮内庁公式HP取得
├── fetch_instagram.py         # Instagram確認（手動）
├── fetch_youtube.py           # YouTube確認（手動）
├── fetch_government.py        # 政府関連サイト（Phase 5）
├── person_database.py         # 人物別データベース
├── idea_ranker.py             # AI企画ランキング
├── duplicate_checker.py       # 重複判定
├── todo_generator.py          # TODO自動生成
├── project_manager.py         # 企画管理システム
├── research_report_generator.py # レポート生成
└── research_dashboard.py      # 人物別ダッシュボード
config/
├── official_sources.yaml      # 公式情報ソース定義
├── person_keywords.yaml       # 人物キーワード・禁止/推奨表現
└── ranking_rules.yaml         # 企画ランキング評価ルール
data/
├── raw/                       # 生データ
└── processed/
    ├── person_database.json   # 人物別データベース
    ├── project_database.json  # 企画管理データベース
    └── fetched_urls.json      # 取得済みURLデータベース
outputs/
└── daily_official_research/   # 日次レポート出力先
```

## 企画ステータス

| ステータス | 説明 |
|---|---|
| 企画候補 | リサーチから生まれた候補 |
| 採用 | 荒木が採用を決定 |
| 台本作成中 | 台本を作成中 |
| 編集指示書作成中 | 外注用の指示書を作成中 |
| 外注依頼済み | 外注者に依頼済み |
| 編集中 | 外注者が編集中 |
| 修正中 | 修正対応中 |
| 投稿待ち | 投稿準備完了 |
| 投稿済み | YouTube/TikTokに投稿済み |
| 成績分析済み | 投稿後の数値分析完了 |
| 不採用 | 不採用 |

## AI企画ランキング評価項目（100点満点）

| 項目 | 配点 |
|---|---|
| 速報性 | 12点 |
| 65歳以上女性視聴者との相性 | 12点 |
| 人物人気 | 10点 |
| 安全性 | 10点 |
| 権利リスクの低さ | 10点 |
| 公式素材の使いやすさ | 8点 |
| Shorts適性 | 8点 |
| 長尺適性 | 8点 |
| 感情訴求 | 8点 |
| TikTok適性 | 6点 |
| 検索需要 | 4点 |
| 制作しやすさ | 4点 |

## 実装フェーズ

- **Phase 1** (実装済み): 宮内庁HP新着取得、公式URL保存、レポート生成、URL重複防止
- **Phase 2** (実装済み): Instagram/YouTube手動確認欄、人物別分類
- **Phase 3** (実装済み): AI企画ランキング、TODO自動生成、フォーマット判定
- **Phase 4** (実装済み): 人物別データベース、重複判定、企画管理システム
- **Phase 5** (未実装): 首相官邸/外務省/自治体/訪問先の追加、週次レポート、投稿後数値分析

## エラー時の対処

| エラー | 原因 | 対処 |
|---|---|---|
| 公式URL取得エラー | ネットワーク障害またはサイト変更 | 手動でURLを確認 |
| 取得元が公式か判定できない | 不明なソース | 手動で公式性を確認 |
| 既に取得済みのURL | 重複取得の防止 | 正常動作（スキップ） |
| 禁止表現が含まれる | タイトル/台本に禁止表現 | 警告に従い表現を修正 |
| 権利不明素材 | 素材の出典が不明 | 公式素材のみ使用 |

## 今後の拡張設計

- `config/official_sources.yaml` にソースを追加するだけで新しい取得先を追加可能
- `config/person_keywords.yaml` に人物を追加するだけで分類対象を拡張可能
- `config/ranking_rules.yaml` でスコア配分を調整可能
- 各fetchモジュールは独立しており、個別に差し替え可能
- データベースはJSON形式で、外部ツールとの連携も容易

## 既存システムとの関係

`YouTube収益改善外注管理システム/` (Next.js) は独立して動作します。本システムで企画化した案件を、外注管理システムで進行管理する運用フローを想定しています。

## ライセンス

Private - 非公開
