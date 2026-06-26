# Instagram投稿生成・予約管理システム

**ライフセーブ21プラス（株式会社ナチュラルウィル）** のInstagram運用を効率化するためのCLIツールです。

> 家全体の水を浄水するオール浄水システム／オールナノバブル水。
> キッチン、洗面、浴室、シャワー、洗濯まで、毎日使う水だからこそ住まい全体で整える。

このツールは

```
投稿案作成 → 画像文言・キャプション生成 → 人間確認 → 投稿予約データ出力
```

までを支援します。**完全自動投稿は行いません。**

## 安全性・コンプライアンス方針

- **Instagramの規約に違反する自動操作・スクレイピング・非公式ログインは一切行いません。**
  本ツールは投稿「案」と「予約用データ（CSV/JSON）」を生成するだけです。実際の投稿は
  人間が確認したうえで、Meta公式API または Buffer等の公式予約サービスを通じて行う想定です。
- **薬機法・景品表示法・誇大広告リスクを避ける**ため、生成文面は効果を断定しない表現に統一し、
  禁止表現を自動でチェック・警告し、**代替表現**を提案します。
  （健康効果・治療効果・美容効果は断定しません。）

## 必要環境

- Python 3.9+（標準ライブラリのみで動作）
- 任意: `PyYAML`（`config.yaml` を読むために推奨。無くても既定値で動作）
- 任意: `pytest`（テスト実行用）
- **外部APIキーは不要**です（MVPはテンプレート生成で動作）。

```bash
pip install -r requirements.txt   # PyYAML / pytest（任意）
```

## クイックスタート

```bash
python main.py --help

# 投稿案を生成（カルーセル）
python main.py generate --theme "家中の水を見直す" --format carousel

# 投稿案を生成（リール台本）
python main.py generate --theme "シャワーの塩素が気になる方へ" --format reel

# 投稿カレンダーを生成（4週・週3投稿）
python main.py calendar --weeks 4 --frequency 3

# 文章のリスクチェック
python main.py risk-check --file generated_posts/sample.md

# posts.json からカレンダー/レポートを出力
python main.py export --format csv
```

## コマンド一覧

| コマンド | 説明 | 主なオプション |
|----------|------|----------------|
| `generate` | テーマ×フォーマットから投稿案を生成 | `--theme`, `--format {feed,carousel,reel,story}`, `--no-save` |
| `calendar` | 投稿カレンダーを生成しCSV/JSON出力 | `--weeks`, `--frequency`, `--start YYYY-MM-DD`, `--export {csv,json}` |
| `risk-check` | 文章の禁止表現をチェック | `--file <path>`, `--text "<文章>"` |
| `export` | posts.json からCSV/JSON・リスクレポート出力 | `--format {csv,json}` |
| `themes` | 登録テーマ一覧を表示 | — |
| `status` | 投稿ステータスを更新（人間確認フロー） | `--id <投稿ID>`, `--set <status>` |

### 投稿フォーマット

- `feed` … 通常のフィード投稿
- `carousel` … カルーセル投稿（5〜7枚構成）
- `reel` … リール台本（30〜45秒：フック/本文/画面テキスト/ナレーション/CTA）
- `story` … ストーリーズ投稿案

### 投稿ステータス（人間確認フロー）

```
draft → review → approved → scheduled → posted
                          ↘ rejected
```

`status` コマンドで遷移させます（人間が確認・承認する前提）。

```bash
python main.py status --id whole-house-water-carousel-xxxxxxxx --set approved
```

## 生成・保存されるファイル

| ファイル | 内容 |
|----------|------|
| `posts.json` | 生成した全投稿の構造化データ（マスター） |
| `calendar.csv` | 投稿予定表（日付・種別・テーマ・キャプション・ハッシュタグ・ステータス・リスク） |
| `calendar.json` | カレンダーのJSON版（`--export json` 時） |
| `risk_report.md` | リスクチェック結果のまとめレポート |
| `generated_posts/*.md` | 各投稿案のMarkdown（人間がレビューしやすい形式） |

## 登録テーマ（`data/themes.json`）

家中の水を見直す / お風呂の水まで浄水 / シャワーの塩素が気になる方へ /
キッチンだけでなく住まい全体へ / ナノバブル水という選択 / 戸建て向け提案 /
マンション向け提案 / よくある質問 / 導入前の不安解消 / 無料相談誘導

テーマは `data/themes.json` に追記するだけで増やせます。

## リスクチェックの仕組み

- `data/forbidden_expressions.json` … 禁止・要注意表現（正規表現）と理由・代替表現
- `data/recommended_expressions.json` … 推奨フレーズ・CTA・ハッシュタグ

例として次のような表現を自動検出して警告します：
アトピーが治る／肌荒れが改善する／病気が治る／健康になる／老化防止／免疫力アップ／
医療効果／絶対に効果がある／必ず変わる／奇跡の水／万能水 など。

検出時は理由とともに**代替表現**を提案します。

## ディレクトリ構成

```
.
├── main.py                      # CLIエントリポイント
├── config.yaml                  # 設定（商品・LLM・カレンダー・出力先）
├── requirements.txt
├── README.md
├── lifesave_ig/                 # ロジック本体（Web化を見据えてCLIから分離）
│   ├── __init__.py
│   ├── config.py                # 設定・データ読み込み
│   ├── risk.py                  # リスクチェック
│   ├── llm.py                   # LLMプロバイダ抽象化（template / openai）
│   ├── generator.py             # 投稿生成（各フォーマット）
│   ├── calendar_gen.py          # 投稿カレンダー生成
│   └── storage.py               # 保存・出力（json/csv/md）
├── data/
│   ├── themes.json
│   ├── forbidden_expressions.json
│   └── recommended_expressions.json
├── generated_posts/             # 生成された投稿Markdown（sample.md 同梱）
├── posts.json                   # （実行で生成）
├── calendar.csv                 # （実行で生成）
├── risk_report.md               # （実行で生成）
└── tests/                       # ユニットテスト（pytest）
```

## テスト

```bash
pytest
```

## 設計方針（拡張性）

- **ロジックとCLIを分離**（`lifesave_ig/` パッケージ）。将来のWeb管理画面（FastAPI/Flask等）から
  同じ関数を呼び出せます。
- **LLMプロバイダを抽象化**（`lifesave_ig/llm.py`）。既定は `template`（APIキー不要）。
  `config.yaml` の `llm.provider` を `openai` にし、`OPENAI_API_KEY` を設定すると差し替え可能
  （MVPでは安全側にフォールバック）。

## 将来: Meta公式API連携の追加実装方針

現状は「予約用データ（CSV/JSON）」の出力までです。実投稿を自動化する場合の方針：

1. **Instagram Graph API（Meta公式）連携**
   - Facebookページに紐づくInstagramビジネスアカウントが必要。
   - 投稿は2ステップ: `POST /{ig-user-id}/media`（メディアコンテナ作成）→
     `POST /{ig-user-id}/media_publish`（公開）。カルーセルは子メディアを作成して束ねる。
   - 長期アクセストークンの取得・更新（リフレッシュ）処理を実装。
   - `lifesave_ig/` に `publisher.py` を追加し、`posts.json` の `status == "approved"` の投稿を
     対象に発行する。**人間承認後のみ実行**するフローを維持。
2. **予約投稿は外部公式サービス連携も選択肢**
   - Buffer / Meta Business Suite の予約機能向けに、現状のCSV/JSONをそのままインポート可能な
     形式へ整える（`storage.py` にエクスポータを追加）。
3. **画像生成・添付**
   - 現状は「画像内テキスト案」まで。画像生成（Canva API等）や手動デザインの差し込み口を
     `media` フィールドとして `posts.json` に追加。
4. **認証情報の管理**
   - APIトークンは環境変数 / シークレットマネージャで管理し、リポジトリには保存しない。
5. **レート制限・エラーハンドリング・監査ログ**
   - 公開APIのレート制限に合わせたキューイングと、発行結果の記録（`posted_log.json`）。

いずれの場合も、**規約違反となる非公式自動化は行わず、公式APIまたは公式予約サービス経由**に
限定する設計とします。
