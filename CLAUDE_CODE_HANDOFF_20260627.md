# CLAUDE_CODE_HANDOFF_20260627

引き継ぎドキュメント — 2026-06-27 セッション終了時点

---

## A. Git状態

- **ブランチ**: `claude/festive-brahmagupta-m2vgt2`
- **最終コミット（push済）**: `abeb84a` — T001オランダ・ベルギー公式訪問の制作パッケージ生成を実装
- **リモート同期**: `origin/claude/festive-brahmagupta-m2vgt2` と同期済み（本ハンドオフコミット前時点）

### 未コミット変更ファイル（5件）

| ファイル | 変更内容 | 状態 |
|---------|---------|------|
| `main.py` | Shorts03対応（consolidate_scripts range拡大、auto_fix対象追加）、consolidate_materials書き直し | 完了・テスト通過 |
| `src/materials.py` | 素材運用方針に基づく全面書き直し（場面別指示書方式へ移行） | 完了・テスト通過 |
| `src/research.py` | shorts_03_textパススルー追加、新テーマ3件のナレッジベース追加 | 部分完了（後述） |
| `src/script_writer.py` | エンディングテキスト変更（1行） | 完了・テスト通過 |
| `src/validators.py` | core_facts_confirmed汎用化、BGM警告によるproduction_ready制御、rights_overall既定値変更 | 完了・テスト通過 |

### テスト結果

```
49 passed, 5 warnings in 0.34s
```

全49テスト合格。

---

## B. 完了済み作業

### B1. Shorts 03 対応（全体）
- `src/script_writer.py`: `_build_shorts_03_text()` 追加、`generate_shorts_scripts()` で3本目出力
- `src/research.py`: `research_topic()` で `shorts_03_text` をパススルー
- `main.py`: `consolidate_scripts` の range を `(1, 4)` に拡大、auto_fix対象に追加
- `src/validators.py`: Shorts 03 の尺検証追加（2本 or 3本に対応）

### B2. core_facts_confirmed 汎用化
- `src/validators.py`: ハードコード（F002/F003）から「confirmed + verified_excerpt + usable_in_script が2件以上」に変更

### B3. BGM警告によるproduction_ready制御
- `src/validators.py`: `len(bgm_warnings) == 0` を `production_ready` 条件に追加
- サマリーの警告ラベルを「production_readyには影響しない」→「荒木側確認完了までproduction_ready=Falseを維持」に修正

### B4. 素材運用方針の変更（materials.py全面書き直し）
- `src/materials.py`:
  - 旧: URL自動収集 + 権利個別判定 → 新: 場面別素材指示書生成
  - `ALLOWED_SOURCES`（9項目）、`PROHIBITED_SOURCES`（7項目）定数追加
  - `_build_scene_materials()`: section_configからシーン別指示行を構築
  - `generate_materials_md()`: 04_materials_list.md を構造化Markdownで出力
  - `generate_rights_report()`: 常に `{"overall_status": "OK", "has_ng": False, "has_review": False}` を返却
- `main.py`: `consolidate_materials()` を書き直し（既存04ファイルにrights_report.mdを追記する方式）
- `src/validators.py`: `rights_overall` デフォルトを `"REVIEW"` → `"OK"` に変更

### B5. T001ナレッジベース（前セッションで完了、abeb84aに含む）
- テーマ: 天皇皇后両陛下オランダ・ベルギー公式訪問
- 長尺: 2399字 / 7.8分 ✓
- Shorts01: 245字 / 47.7秒 ✓
- Shorts02: 257字 / 50.1秒 ✓
- Shorts03: あり（前セッションで追加）
- facts 7件、sources 7件、section_config 5章

---

## C. 未完了・既知の問題

### C1. 新テーマ3件のナレーション不足（重大）

以下3テーマは `src/research.py` の `_BUILTIN_TOPICS` に追加済みだが、各factの `narration_lead` / `narration_after` テキストが短すぎ、長尺スクリプトが目標尺（7〜9分）に大幅に届かない。

| テーマ | 現在の長尺 | 目標 | 不足 |
|-------|-----------|------|------|
| 愛子内親王殿下の成年に際する記者会見 | 1145字 / 3.7分 | 7分 | 約1000字追加必要 |
| 天皇陛下のお誕生日記者会見 | 1106字 / 3.6分 | 7分 | 約1050字追加必要 |
| 天皇皇后両陛下の英国公式訪問 | 1201字 / 3.9分 | 7分 | 約950字追加必要 |

**対処方法**: 各factの `narration_lead` と `narration_after` を、宮内庁公式ページの記録に基づいて大幅に拡充する必要がある。1 factあたり約200字の追加が目安。

### C2. 新テーマ3件のShorts尺不足

| テーマ | Shorts01 | Shorts02 | Shorts03 | 目標 |
|-------|---------|---------|---------|------|
| 愛子内親王… | 33.3秒 | 28.8秒 | なし | 45〜59.5秒 |
| 天皇陛下… | 30.0秒 | 26.9秒 | なし | 45〜59.5秒 |
| 英国公式… | 31.4秒 | 31.2秒 | なし | 45〜59.5秒 |

**対処方法**: 各テーマに `shorts_01_text`, `shorts_02_text`（および任意で `shorts_03_text`）を pre-written テキストとして追加し、45秒以上になるよう調整する。T001の実装を参考にすること。

### C3. validators.pyの残存コード

`rights_ok` と `rights_has_review` の変数・条件分岐が残っている。素材方針変更により `generate_rights_report()` が常に `OK` / `has_review=False` を返すため**機能的には問題ない**が、コードの可読性のため将来的にクリーンアップが望ましい。

### C4. BGM関連（設計通りの制限）

`config.py` の BGM_SETTINGS:
- `local_file_verified: False` — UNL1337.wav の実ファイル確認が未完了
- `contract_evidence_verified: False` — 契約証跡の確認が未完了
- `content_id_status: "unconfirmed"` — Content ID 条件の確認が未完了

これらが False/unconfirmed である限り `production_ready = False` となる（設計通り）。荒木側で確認後に `config.py` を手動更新する。

---

## D. ファイル構成

### 主要ファイル

```
main.py                          # CLI エントリポイント
config.py                        # 設定定数
src/
  research.py                    # ナレッジベース + research_topic()
  script_writer.py               # 長尺 + Shorts 台本生成
  instructions.py                # 編集指示書 + サムネイル指示書
  materials.py                   # 場面別素材指示書 + 権利ガイド
  ng_check.py                    # NG表現チェック + 敬称自動補正
  posting.py                     # 投稿用文面生成
  bgm_config.py                  # BGM設定読み込み + クレジット生成
  validators.py                  # パッケージ検証 + ステータスJSON
tests/
  test_generate.py               # 24テスト
  test_topic_planner.py          # 25テスト
imperial_topic_planner/          # 企画立案モジュール（別系統）
```

### 生成パッケージ構成（11ファイル）

```
01_research_report.md            # 出典調査・ファクトチェック
02_narration_script.md           # 長尺 + Shorts 台本
03_editing_instructions.md       # 編集指示書 + サムネイル指示書
04_materials_list.md             # 場面別素材指示書 + 権利ガイド
05_posting_package.md            # 投稿用文面（タイトル・説明・タグ等）
06_bgm_credits.md                # BGMクレジット情報
07_ng_check_report.md            # NG表現チェック結果
08_bgm_plan.md                   # BGMプラン
09_package_summary.md            # パッケージサマリー
execution.log                    # 実行ログ
metadata.json                    # ステータスJSON
```

---

## E. 登録済みテーマ一覧（_BUILTIN_TOPICS）

| # | テーマキー | 長尺 | Shorts | 状態 |
|---|-----------|------|--------|------|
| 1 | なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来 | 7.5分 ✓ | 2本 ✓ | 実用可能（BGM確認除く） |
| 2 | 天皇皇后両陛下オランダ・ベルギー公式訪問――公式記録に残る友好の記録 | 7.8分 ✓ | 3本 ✓ | 実用可能（BGM確認除く） |
| 3 | 愛子内親王殿下の成年に際する記者会見――… | 3.7分 ✗ | 不足 ✗ | ナレーション拡充必要 |
| 4 | 天皇陛下のお誕生日記者会見――… | 3.6分 ✗ | 不足 ✗ | ナレーション拡充必要 |
| 5 | 天皇皇后両陛下の英国公式訪問――… | 3.9分 ✗ | 不足 ✗ | ナレーション拡充必要 |

---

## F. 制約・禁止事項（次セッションへの申し送り）

1. 架空URLは絶対に生成しない
2. 皇族の内心やご両親の感情を推測・断定しない
3. `local_file_verified=true` は実ファイル確認時のみ設定
4. Python の `None` を文章に出力しない
5. 契約音源本体をGitHubへpushしない
6. BGM実ファイル確認済みでも契約証跡・Content ID未確認なら `production_ready=false` 維持
7. テスト通過のための基準緩和禁止
8. 45秒未満のShortsを合格扱いにしない
9. REVIEWを削除するだけの形式的修正禁止
10. 検索結果の要約、AI内蔵知識、Wikipedia、個人ブログ、まとめサイト、報道記事だけを根拠に confirmed へ変更しない

---

## G. 次セッションでの推奨作業順序

1. **未コミット変更のコミット・プッシュ**（本ハンドオフと一緒にコミット済みの場合はスキップ）
2. **テーマ3〜5のナレーション拡充**（C1, C2の対処）
   - 各factの narration_lead / narration_after を宮内庁公式記録に基づいて拡充
   - 各テーマに shorts_01_text / shorts_02_text を pre-written で追加
   - 長尺7分以上、Shorts45秒以上を達成
3. **全テーマの再生成テスト**（5テーマ × `python main.py generate --production --theme "..."`)
4. **validators.pyのクリーンアップ**（C3の残存コード除去、任意）
5. **BGM確認**（荒木側作業 — config.pyの3フラグ更新）

---

## H. コマンドリファレンス

```bash
# テスト実行
python -m pytest tests/ -q

# パッケージ生成（テストモード）
python main.py generate --test --theme "テーマ名"

# パッケージ生成（本番モード）
python main.py generate --production --theme "テーマ名"

# 敬称自動補正付き
python main.py generate --production --auto-fix-honorifics --theme "テーマ名"

# 企画立案モジュール
python -m imperial_topic_planner
```

---

*生成日時: 2026-06-27*
*ブランチ: claude/festive-brahmagupta-m2vgt2*
*テスト: 49 passed*
