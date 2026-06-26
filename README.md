# imperial-video-automation

**外注向け制作パッケージ自動生成システム**

YouTube チャンネル「日本が誇る皇室物語」の動画制作に必要な、外注者へそのまま渡せる制作パッケージ（台本、素材URL、制作指示書、投稿用文面等）を一括生成します。

**これはMP4自動生成システムではありません。** 動画の実制作は外注者が行います。

## 必要環境

- Python 3.9+

FFmpeg、VOICEVOX、BGMファイルは不要です（制作指示書に情報として記載するのみ）。

## 生成物一覧

| ファイル | 内容 |
|---------|------|
| `01_research_report.md` | 出典調査・ファクトチェック結果 |
| `02_narration_script.md` | 長尺台本 + Shorts台本2本 |
| `03_editing_instructions.md` | 動画制作指示書 + サムネイル制作指示書 |
| `04_materials_list.md` | 素材候補URL + 権利レポート |
| `05_posting_package.md` | タイトル候補・概要欄・固定コメント・クレジット |
| `06_bgm_and_credits.md` | BGM指定・使用条件・クレジット設定 |
| `07_ng_check_report.md` | NG表現・煽り・断定・権利リスクの検査結果 |
| `08_bgm_plan.md` | BGM選定プラン・検索条件・候補一覧 |
| `09_package_summary.md` | パッケージ概要・判定・不足項目 |
| `metadata.json` | 完成判定・不足項目・生成ファイル一覧 |

## 実行方法

```bash
# ヘルプ
python main.py --help

# テストモード（動作確認用、仮データ可）
python main.py generate --test
python main.py generate --test --theme "テーマ"

# プロダクションモード（出典確認必須）
python main.py generate --production
python main.py generate --production --theme "テーマ"
```

出力先: `output/packages/<run_id>/`

## test mode と production mode の違い

| 項目 | test | production |
|------|------|-----------|
| 出典不足時 | 仮データで生成、要確認マーク付き | 下書きパッケージを生成、production_ready=false |
| production_ready | 常にfalse | 全条件を満たした場合のみtrue |
| 外注者へ渡せるか | いいえ（テスト用） | 条件付きで可能 |

## production_ready=false の意味

出典の確認が不足している、BGM URLが未設定、NG表現チェックでFAILがある、等の理由で外注者へそのまま渡せない状態です。`metadata.json` の `missing_items` を確認し、不足項目を解消してください。

## 外注者へ渡すファイル

`09_package_summary.md` で判定を確認した上で、以下を外注者へ渡してください：
- `02_narration_script.md`（台本）
- `03_editing_instructions.md`（制作指示書）
- `04_materials_list.md`（素材・権利情報）
- `05_posting_package.md`（投稿用文面）
- `06_bgm_and_credits.md`（BGM設定）

## 荒木側で確認すべき項目

1. 出典の最終確認（特にPARTIAL/UNCONFIRMEDの事実）
2. 素材URLの権利確認
3. BGM正式URLの設定（`bgm_config.json`）
4. NG表現チェック結果の確認
5. 外注者へ渡す前の内容最終確認

## BGM採用条件

BGMは以下の4条件をすべて満たすもののみ採用する：

1. **商用利用可**
2. **YouTube収益化可**
3. **公式ページURLあり**
4. **作曲者条件確認済み**

### 投稿後の確認事項

- 初回投稿後、YouTube Studioで著作権申し立ての有無を確認する
- 申し立てが出た場合は、BGMを差し替え、該当楽曲を使用停止リストに入れる

## 本番完成条件

- 必須ファイルがすべて存在
- 0KBファイルなし
- ファクトチェックで UNCONFIRMED/REJECTED が台本に混入していない
- NG表現チェックで FAIL なし
- BGM URL設定済み
- 権利レポートで NG 素材が指示書に混入していない

## Windows

```
run_package_test.bat  -- テスト実行
```

## 禁止事項

- 皇族・王族のAI生成顔の使用
- 顔合成、表情変更、服装変更、年齢変更
- 実在人物を別人で代用
- 皇族の内心断定
- 根拠のない煽り
- 権利不明素材の使用

## Legacy

`legacy_mp4_generator/` に以前のMP4自動生成コードを保管しています。現在の本番運用では使用しません。
