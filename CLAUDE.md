# Imperial Video Automation — CLAUDE.md

## プロジェクト概要

皇室系YouTubeチャンネル「日本が誇る皇室物語」の外注向け制作パッケージ（11ファイル）を自動生成するシステム。動画（MP4）は生成しない。

- チャンネル名: `日本が誇る皇室物語`
- チャンネル方針: `公式事実で、静かな感動を。`
- 対象視聴者: 55歳以上、特に65歳以上の女性、スマートフォン視聴中心

## 固定設定（変更禁止）

| 項目 | 値 |
|------|-----|
| BGMファイル | `assets/bgm/UNL1337.wav`（箕輪レコーズ契約音源、120秒） |
| ナレーション | VOICEVOX 青山龍星 speed 0.88 |
| 長尺目標尺 | 7〜9分（ナレーション文字数で判定、350×0.88=308文字/分） |
| Shorts本数 | **2本のみ**（3本目は生成禁止） |
| Shorts目標尺 | 45.0〜59.5秒 |
| Shorts①役割 | 長尺誘導（テーマ紹介→関連動画へ） |
| Shorts②役割 | 長尺補足（別角度の事実→関連動画へ） |

## Gitルール

- ブランチ: `claude/compassionate-tesla-gfca8e`
- **Gitに追加禁止**: `assets/bgm/UNL1337.wav`、`output/`配下の生成物、ZIP（.gitignoreで除外済み）
- BGMファイルはセッション開始時に `/root/.claude/uploads/` から `assets/bgm/UNL1337.wav` へコピーすること

## ファイル構成

```
config.py              — 全設定値（チャンネル名、BGM、VOICEVOX、動画仕様）
main.py                — CLI（generate --test / --production --theme "..."）
src/
  research.py          — _BUILTIN_TOPICS知識ベース + research_topic()
  script_writer.py     — 長尺台本 + Shorts①② 台本生成
  instructions.py      — 動画制作指示書 + サムネイル指示書
  materials.py         — 素材指示書 + 権利レポート
  posting.py           — タイトル5案 + 概要欄 + 固定コメント + クレジット
  bgm_config.py        — bgm_config.json読込 + BGM関連MD生成
  ng_check.py          — NG表現チェック（PASS/REVIEW/FAIL判定）
  validators.py        — パッケージ検証 + metadata.json + summary
tests/
  test_generate.py     — 39テスト
assets/bgm/
  UNL1337.wav          — 契約BGM（gitignored）
  README_bgm.txt       — BGM説明
```

## 出力ファイル（11件）

`output/packages/<timestamp>_<theme>/` に生成:

01. `01_research_report.md` — リサーチレポート + ファクトチェック + 出典CSV
02. `02_narration_script.md` — 長尺台本 + Shorts①② 台本
03. `03_editing_instructions.md` — 動画制作指示書 + サムネイル指示書
04. `04_materials_list.md` — 素材指示書 + 権利確認ガイド
05. `05_posting_package.md` — タイトル5案 + 概要欄 + 固定コメント
06. `06_bgm_and_credits.md` — BGM設定 + クレジット
07. `07_ng_check_report.md` — NG表現チェックレポート
08. `08_bgm_plan.md` — BGM選定プラン
09. `09_package_summary.md` — パッケージ概要
10. `metadata.json` — 機械可読ステータス
11. `execution.log` — 実行ログ

## production_ready=true の条件

以下をすべて満たすこと:

1. 11ファイルすべて存在し、0KBファイルなし
2. BGMファイルが存在・非ゼロ・有効WAV・10秒以上（`validate_bgm_file()`）
3. BGM設定に blocking issue なし（warning は許容）
4. BGM公開URLなしは **blocking にしない**（契約音源のため）
5. Content ID未確認は warning 表示のみ、blocking にしない
6. NGチェック total_checks ≥ 1（0件でPASSは禁止）
7. NGチェック FAIL = 0
8. REVIEW は production_ready を阻害しない
9. 権利ステータスが OK または review（blocked/incomplete は不可）
10. 台本がナレーション原稿になっている（テンプレートのままでない）
11. 長尺台本が目標尺（7分）以上
12. Shorts①② が各45秒以上
13. confirmed facts ≥ 2
14. クレジット二重表記なし
15. mode = "production"

## NGチェックの仕様

- 全チェック項目を PASS/REVIEW/FAIL で報告（PASS も記録）
- total_checks ≥ 1 を保証
- チェックカテゴリ: 禁止表現、内心描写、誇張表現、対立・攻撃表現、事実と推測の混在、敬称・敬語、出典未記載、タイトルと内容の不一致、Shorts重複、同一表現過剰反復、AI人物画像指示

## 素材指示書の仕様

- 場面ごとに具体的な候補URL（公式ページ）を `candidate_urls` として自動挿入
- 各URLに `rights_status`（usable/review/blocked）を付与
- 権利レポートは場面別に usable/review/blocked/incomplete の4段階判定

## タイトルの仕様

5案を5つの異なる方向性で生成:
1. 正攻法（テーマ直球）
2. 問いかけ型（知的好奇心）
3. 信頼性訴求型（出典明示）
4. 安心感型（シニア向け）
5. ストーリー型（物語性）

## 組み込みトピック（_BUILTIN_TOPICS）

現在6テーマ登録済み。各テーマは facts, sources, section_config, shorts_01/02_text, thumbnail_text_a/b, material_hints, hashtags を持つ。

1. なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来
2. 天皇皇后両陛下オランダ・ベルギー公式訪問――公式記録に残る友好の記録
3. 愛子内親王殿下の成年に際する記者会見――公式のおことばに表れた成年皇族としての歩み
4. 天皇陛下のお誕生日記者会見――公式のおことばから振り返る一年
5. 天皇皇后両陛下の英国公式訪問――宮内庁発表に基づく友好の記録
6. 愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み ← 本番テーマ

## テスト

```bash
python -m pytest tests/test_generate.py -v
```

39テスト。TestProductionRedCross クラスが日赤テーマの production_ready=true を検証。

## 本番実行

```bash
python main.py generate --production --theme "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
```

## 未完了・要注意事項

- **ZIP提出の検証不足**: 前回セッションで production 再実行後のZIPが古い出力を含んでいた疑い。次回は必ず production を明示的に再実行し、最新出力ディレクトリの metadata.json を grep/読込で production_ready=true を確認してからZIP化すること
- **ZIP作成手順**: `ls -td output/packages/*愛子* | head -1` ではなく、production 実行直後の stdout から出力パスを取得し、そのパスを直接使うこと
- `config.py` の `local_file_verified` と `contract_evidence_verified` は False のまま（荒木側で確認するもの。blocking にはならない）
- BGM公開URLなしは warning のみ（契約音源のため production_ready を阻害しない）

## 禁止事項

- Shorts 3本目の生成
- 皇族のAI生成画像の指示
- BGMファイル（.wav）のgit追加
- output/ 配下のgit追加
- 新機能提案・将来構想・大規模再設計（合格条件を満たしたら終了）
