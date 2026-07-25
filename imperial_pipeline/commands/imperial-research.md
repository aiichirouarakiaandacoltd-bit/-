---
description: 工程1〜5（入力整理・重複確認・調査・事実台帳・素材権利台帳）を実行する
argument-hint: <project_slug>
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, WebSearch, WebFetch
---

# /imperial-research — 調査工程（工程1〜5）

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

## 手順

### 0. 下書きを生成する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage draft
```

**`ENVIRONMENT.md` の `network_status` を確認すること。**
アクセス不可なら、工程3はテンプレート生成のみとし、全項目へ【アクセス未確認】を付す。
**架空の調査結果を作らない。**

### 1. imperial-researcher を起動する（工程1〜3）

担当：`research/01_入力整理.md`／`research/02_既存動画重複確認.md`／
`research/03_調査結果.md`／`research/04_出典一覧.csv`

- 情報源は第1優先（宮内庁公式など）から着手する
- 実際にアクセスして確認したURLだけを出典一覧へ書く
- 過去動画データが無ければ工程2は「判定不能」で通過させ、止めない

### 2. imperial-fact-checker を起動する（工程4）

担当：`research/05_事実台帳.csv`

- researcher の出力をそのまま信用しない。一次資料を自分で確認する
- 事実IDは `F001` から連番
- 「台本で使用する記述」を、台本にそのまま書ける形で書く
- 確認状態は厳しい側へ倒す

### 3. rights-reviewer を起動する（工程5）

担当：`research/06_素材権利台帳.csv`

- まず `library/approved_materials.csv` を確認する
- ライブラリが空なら、図解・テロップ中心を前提に設計する
- 素材IDは `M001` から連番
- 確認できないものは「要確認」「使用非推奨」。**格上げしない**
- 代替案の欄を空にしない

### 4. 検査する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage check
```

`audit/00_機械検出レポート.md` を確認し、必須列の欠落・ID重複・
未確認タグの件数を報告する。

## 報告

- 事実台帳の件数と確認状態の内訳
- 素材台帳の件数と利用可否の内訳
- 【アクセス未確認】等のタグを付した項目
- 次のコマンド：`/imperial-plan $ARGUMENTS`
