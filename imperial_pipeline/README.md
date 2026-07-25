# 日本が誇る皇室物語 / 制作支援システム

YouTubeチャンネル「日本が誇る皇室物語」のために、
企画・調査・事実確認・長尺台本・Shorts台本・素材設計・サムネイル設計・投稿文・
編集者向け制作指示書・最終監査までを一気通貫で扱う制作支援システムです。

---

## 1. このシステムの目的

荒木愛一朗がテーマまたは参考情報を入力し、システムが成果物一式を生成し、
荒木愛一朗が承認すれば、**そのまま動画編集者へ安全に渡せる状態にすること**が目的です。

**これは完全自動投稿システムではありません。**
品質・事実・権利・皇室への敬意を犠牲にした自動化は行いません。

### 役割分担

| 担当 | 内容 |
| --- | --- |
| Python（本リポジトリ） | フォルダ生成／テンプレート出力／CSV整形／禁止表現の機械検出／必須項目の欠落検出／ID採番／履歴退避／承認内容の反映／最終フォルダ生成／実行ログ |
| サブエージェント（`agents/`） | 調査／事実判定／台本執筆／企画評価／監査 |
| 荒木愛一朗 | 承認、最終判断、権利の最終確認 |

Pythonは事実判定も執筆も監査も行いません。**外部APIを呼びません。APIキーは不要です。**

---

## 2. 必要環境

| 項目 | 要件 |
| --- | --- |
| OS | Windows / macOS / Linux |
| Python | 3.11 以上 |
| 依存 | 標準ライブラリ ＋ PyYAML のみ |
| ネットワーク | Pythonの実行には不要 |
| 有料サービス | 不要（課金を伴う機能は含みません） |

```bash
python -m pip install pyyaml
```

**PyYAMLが導入できない場合も動作します。**
`modules/input_parser.py` に最小限の自作YAMLパーサを内蔵しており、
PyYAMLが見つからない場合は自動的にそちらへ切り替わります
（実行時に「簡易パーサで動作しています」と警告が出ます）。
簡易パーサは本システムの設定ファイル・入力ファイルの書式にのみ対応します。
複雑なYAML記法（アンカー、複数行文字列など）は使わないでください。

構築時に確認した実行環境は `ENVIRONMENT.md` に記録しています。

---

## 3. 初期設定

`config/` の4ファイルを確認します。**最初に必ず確認すべき項目**は次の5点です。

| ファイル | 項目 | 内容 |
| --- | --- | --- |
| `config/settings.yaml` | `chars_per_minute` | **暫定値 300**。VOICEVOX「青山龍星」話速0.88で実測して更新すること（後述） |
| `config/settings.yaml` | `bgm_credit` | 箕輪レコーズの正式表記。初期値は【要確認・正式表記を荒木が入力】 |
| `config/settings.yaml` | `contact` | 問い合わせ先。初期値は【お問い合わせ先：要入力】 |
| `config/honorifics.yaml` | `status: 要確認` の項目 | 皇族方の表記の統一方針を確定させること |
| `library/approved_materials.csv` | 全行 | 使用可能と確認済みの素材を登録すること（初期状態は空） |

### chars_per_minute について（重要）

`chars_per_minute: 300` は**実測に基づかない暫定値**です。
この値から 12〜14分＝3,600〜4,200字 を逆算していますが、
実際の尺は VOICEVOX の読み上げ速度に依存します。

更新手順：

1. 完成した台本をVOICEVOX「青山龍星」・話速 0.88 で読み上げる
2. 「読み上げた文字数 ÷ 実測した分数」を計算する
3. `config/settings.yaml` の `chars_per_minute` をその値へ書き換える

更新するまで、目標文字数はあくまで目安です。

---

## 4. 入力ファイルの書き方

### 新規プロジェクトの作成

```bash
python run_imperial_pipeline.py --init my_project_slug
```

`projects/my_project_slug/input/project_input.yaml` が作られます。

### project_input.yaml

```yaml
project_name: 愛子さま 初の単独地方ご訪問
project_slug: aiko_solo_visit
channel: 日本が誇る皇室物語
main_person: 愛子さま
theme: 初めての単独地方ご訪問で、どのようなご活動をされたのかを時系列で伝える
working_title:
target_length_min: 12
target_length_max: 14
shorts_count: 1
reference_urls: []
reference_files: []
must_include: []
must_not_include: []
publication_target_date: 2026-08-10
editor_name: 
sample_mode: false
notes:
```

- `target_length_minutes: 12-14` のような**文字列型は使えません**。min / max の数値2項目に分けます。
- 未入力項目を無理に埋めないでください。空欄のまま実行できます。
- 情報が不足していても処理は止まりません。重大な不足は承認用サマリーへ集約されます。
- `project_slug` は半角英数字・アンダースコア・ハイフンのみ（フォルダ名になります）。
- `sample_mode: true` にすると、全生成物の冒頭に
  **【サンプル・ダミーデータ／実制作に使用しないこと】** が表示されます。

### past_videos.csv（工程2で使用・任意）

`projects/<slug>/input/past_videos.csv`

```csv
公開日,タイトル,テーマ,主要人物,結論,URL
```

このファイルが無い場合、工程2は「判定不能（過去動画データ未提供）」として通過し、
**処理は停止しません。**

---

## 5. 実行方法（2段階）

### 第1段階：下書き生成

```bash
python run_imperial_pipeline.py projects/<slug>/input/project_input.yaml --stage draft
```

- 全工程のテンプレートを `projects/<slug>/` 配下へ出力します
- 機械検出（禁止表現・必須項目・ID整合・重複参考判定）を実行します
- `audit/00_機械検出レポート.md` を出力します
- 承認用サマリーの集計欄を自動記入します

**既存の成果物は上書きしません。** サブエージェントが書き込んだ内容は保持されます。
テンプレートから作り直したい場合のみ `--refresh` を付けてください。
その場合、旧版は `projects/<slug>/_history/YYYYMMDD_HHMM/` へ退避されます。

工程単位で再実行することもできます。

```bash
python run_imperial_pipeline.py <input> --stage draft --steps 9,10 --refresh
```

### 検査のみ（生成物を変更しない）

```bash
python run_imperial_pipeline.py projects/<slug>/input/project_input.yaml --stage check
```

### 第2段階：承認後の最終版生成

```bash
python run_imperial_pipeline.py projects/<slug>/input/project_input.yaml \
    --stage final --approval projects/<slug>/input/approval.yaml
```

---

## 6. 生成されるファイル一覧

```
projects/<slug>/
├─ input/
│  ├─ project_input.yaml          企画入力
│  ├─ past_videos.csv             過去動画データ（任意）
│  └─ approval.yaml               承認ファイル
├─ research/
│  ├─ 01_入力整理.md               工程1
│  ├─ 02_既存動画重複確認.md        工程2
│  ├─ 03_調査結果.md               工程3
│  ├─ 04_出典一覧.csv              工程3
│  ├─ 05_事実台帳.csv              工程4（F001〜）
│  └─ 06_素材権利台帳.csv           工程5（M001〜）
├─ planning/
│  ├─ 07_企画評価.md               工程6
│  ├─ 08_タイトル・サムネイル案.md   工程7
│  └─ 09_長尺構成.md               工程8
├─ scripts/
│  ├─ 10A_長尺台本_監査用.md        工程9（事実ID・素材ID付き）
│  ├─ 10B_長尺台本_編集者用.md      工程9（ID無し・編集者用）
│  └─ 11_Shorts台本.md            工程10
├─ production/
│  ├─ 12_長尺素材設計.csv           工程11（最大120行）
│  ├─ 13_Shorts素材設計.csv         工程12（最大20行）
│  ├─ 14_図解・テロップ指示.md       工程13
│  ├─ 15_サムネイル制作指示.md       工程14
│  ├─ 16_投稿設定.md               工程15
│  └─ 17_編集者向け制作指示書.md     工程16
├─ audit/
│  ├─ 00_機械検出レポート.md         Pythonが自動生成
│  ├─ 18_最終監査結果.md            工程17
│  └─ 19_荒木承認用サマリー.md       第8章
├─ FINAL_EDITOR_PACKAGE/          承認後に生成
└─ _history/YYYYMMDD_HHMM/        上書き前の退避
```

---

## 6-2. サブエージェントとスラッシュコマンド

### 導入

```bash
python run_imperial_pipeline.py --install-agents
```

`agents/` と `commands/` の定義を、リポジトリ直下の `.claude/agents/` と
`.claude/commands/` へ複製します。**正本は `imperial_pipeline/` 側**です。
定義を変更したら、このコマンドを再実行してください。

### サブエージェント（8種）

| エージェント | 担当 |
| --- | --- |
| imperial-researcher | 工程1〜3。公式情報の収集、時系列整理、出典URL管理 |
| imperial-fact-checker | 工程4。一次資料との突合、事実と解釈の分類、架空情報の検出 |
| imperial-writer | 工程8・9。長尺構成と長尺台本 |
| imperial-shorts-writer | 工程10。Shorts台本、長尺への誘導、縦型設計 |
| imperial-safety-reviewer | 表現検証。内心断定、対立煽り、誇張、敬称漏れ、炎上リスク |
| rights-reviewer | 工程5。素材の権利状態整理、代替素材提案 |
| production-director | 工程6・7・11〜16。素材設計、図解、サムネイル指示、制作指示書 |
| final-auditor | 工程17・第8章。全成果物の突合、合否判定、承認用サマリー |

**writer が書いた台本は、fact-checker と safety-reviewer が別途検証します。**
同一エージェントが自らの出力を無検証で合格にしない設計です。

共通の前提は `agents/共通ルール.md`、工程ごとの合格基準は
`agents/生成指針_工程別.md` にまとめています。

### スラッシュコマンド

```
/imperial-new <slug> [テーマ]   新規プロジェクト作成
/imperial-research <slug>       工程1〜5（調査・事実台帳・素材権利台帳）
/imperial-plan <slug>           工程6〜8（企画評価・タイトル案・構成）
/imperial-script <slug>         工程9〜10（長尺台本・Shorts台本＋検証）
/imperial-production <slug>     工程11〜16（素材設計〜制作指示書）
/imperial-audit <slug>          工程17・承認用サマリー
/imperial-final <slug>          最終版の生成（承認後）
/imperial-status <slug>         進捗と未確認事項の確認
```

## 7. 承認方法

1. `audit/19_荒木承認用サマリー.md` を開きます
2. 「6. 荒木愛一朗が判断する項目」（最大10件）に回答します
3. `projects/<slug>/input/approval.yaml` を記入します

```yaml
approval_status: approved
selected_title: 採用するタイトル全文
selected_thumbnail: サムネイル案3
approved_risks: []
rejected_materials: [M004]
revision_notes:
```

`approval_status` が `approved` 以外の場合、最終版は生成されません（終了コード 2）。

---

## 8. 承認後の最終版生成

```
FINAL_EDITOR_PACKAGE/
├─ 01_編集者向け制作指示書_最終版.md   ← 主資料。これ1点で作業を開始できる
├─ 02_長尺台本_最終版.md
├─ 03_Shorts台本_最終版.md
├─ 04_長尺素材設計_最終版.csv
├─ 05_Shorts素材設計_最終版.csv
├─ 06_素材権利台帳_最終版.csv
├─ 07_サムネイル制作指示_最終版.md
├─ 08_投稿設定_最終版.md
├─ 09_出典一覧_最終版.csv
└─ 10_納品前チェックリスト.md
```

最終版で自動的に行われる処理：

- 内部情報の除去（内部採点、企画評価、未採用案、内部リスク評価、推論過程など）
- 承認されたタイトル・サムネイルの反映
- `rejected_materials` に挙げた素材を **使用禁止** として明記
- 権利が「要確認」「使用非推奨」のままの素材を **使用禁止** へ変更し、代替案を併記
- 契約・金銭に関わる語が混入していないかの検査（混入時は警告）

**権利未確認素材が残っていても、最終パッケージの生成は止まりません。**
未確認素材は「使用禁止」と明記され、代替案が併記されます。

### 生成がブロックされる条件（これのみ）

| 条件 | 対応 |
| --- | --- |
| 台本が確認状態「使用不可」の事実を参照している | 該当箇所を削除するか、事実台帳を更新する |
| 台本が参照する事実IDが台帳に存在しない | 事実台帳へ追加するか、参照を修正する |
| 存在しない出典URL（架空URL）が含まれている | 該当URLを削除する（`sample_mode: true` では警告に緩和） |
| 皇族方のAI生成顔・顔加工素材が含まれている | 素材を削除する |
| 最終監査結果の判定が「不合格」 | 指摘事項を修正して再監査する |

ブロック時は終了コード 3 で停止し、理由が表示されます。

---

## 9. エラー時の対応

| 症状 | 原因 | 対応 |
| --- | --- | --- |
| `project_slug が未入力のため処理を続行できません` | 入力ファイルの必須項目未記入 | `project_slug` を記入する |
| `target_length_minutes は廃止されました` | 旧仕様の書式 | `target_length_min` / `target_length_max` へ分離する |
| `簡易パーサで動作しています` | PyYAML未導入 | `pip install pyyaml`（そのままでも動作します） |
| `テンプレートが見つかりません` | `templates/` の欠損 | リポジトリを再取得する |
| `approval_status が approved ではありません` | 承認未完了 | `approval.yaml` を記入する |
| 最終版生成がブロックされた | 上表の条件に該当 | 表示された理由に従って修正する |
| 生成物を消してしまった | — | `projects/<slug>/_history/` から復元する |

すべての実行は `logs/run_YYYYMMDD.log` と `logs/run_YYYYMMDD.jsonl` に記録されます。
エラーは隠さずログへ残します。

---

## 10. 未確認情報の扱い

推測で補完しません。次のタグを使用します。

【未確認】【一次資料未確認】【権利条件要確認】【素材URL未取得】
【人物確認が必要】【日付確認が必要】【使用非推奨】【アクセス未確認】【サンプル・ダミーデータ】

- 未確認項目があっても他工程は止まりません
- タグの出現数は `audit/00_機械検出レポート.md` に集計されます
- 承認用サマリーへ集約して報告されます
- **架空の調査結果を作りません。** ネットワークにアクセスできない環境では、
  工程3はテンプレート生成のみとし、全項目へ【アクセス未確認】を付します

---

## 11. 権利確認の限界（必ずお読みください）

**本システムは素材の権利について最終判断を行いません。**

- Pythonが行うのは、台帳に記入された文字列の集計と検出だけです
- サブエージェントが行うのは、確認できた条件の整理と代替案の提示だけです
- **利用可否の最終判断は、荒木愛一朗が権利者の表示を直接確認して行ってください**

方針（第0章 0-4）：

1. 「使えそうな素材を探して権利を判定する」設計を採りません
2. 「使用可能と確認済みの素材ライブラリを先に持ち、その範囲内で設計する」設計です
3. 公式サイトに掲載されているという理由だけで使用可能と判断しません
4. 報道写真・報道映像は原則「使用非推奨」です
5. 皇族方のAI生成顔、顔の合成・変形・若返り・老化は、いかなる場合も生成・提案しません
6. 素材が不足する場合は「素材不足」と明記し、自社作成図解・テロップ中心画面・地図・年表へ切り替えます

---

## 12. 自動投稿を行わない理由

1. **事実の最終確認を人が行う必要があるため。**
   皇室に関する記述は、日付・人物・場所・行事名の1文字の誤りが誤情報になります。
2. **権利の最終判断を機械が行えないため。**
   利用条件の解釈は権利者の表示を人が読んで判断する必要があります。
3. **敬意の判断が機械化できないため。**
   表現が敬意を欠いていないかは、文脈を含めた人の判断が必要です。
4. **誤りが公開されると回復できないため。**
   投稿後の訂正では、既に視聴した方へ誤情報が残ります。
5. **チャンネルの軸「公式事実で、静かな感動を。」を守るため。**

生成物は必ず荒木愛一朗が確認し、承認したうえで編集者へ渡してください。

---

## 13. 荒木愛一朗が入力・確認すべき設定項目（まとめ）

- [ ] `config/settings.yaml` の `chars_per_minute` … VOICEVOX青山龍星・話速0.88での実測値へ更新
- [ ] `config/settings.yaml` の `bgm_credit` … 箕輪レコーズの正式表記
- [ ] `config/settings.yaml` の `contact` … 問い合わせ先メールアドレス
- [ ] `config/honorifics.yaml` … `status: 要確認` の表記統一方針を確定
- [ ] `library/approved_materials.csv` … 初期素材の登録
