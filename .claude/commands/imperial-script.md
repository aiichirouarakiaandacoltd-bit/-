---
description: 工程9〜10（長尺台本・Shorts台本）を執筆し、事実と表現の検証を通す
argument-hint: <project_slug>
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

# /imperial-script — 台本工程（工程9〜10）

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

**このコマンドの要点は、執筆したエージェント自身に合格を出させないことである。**
必ず検証の2工程を通すこと。

## 手順

### 1. imperial-writer を起動する（工程9）

担当：`scripts/10A_長尺台本_監査用.md`／`scripts/10B_長尺台本_編集者用.md`

- 書けるのは `research/05_事実台帳.csv` にある事実だけ
- 監査用（10A）は事実記述の直後に【事実ID：F〇〇〇】を付す
- 編集者用（10B）は本文からIDを外し、章末の参考情報欄へまとめる
- **10Aと10Bで本文の文言を変えない**
- 一文は短く、主語を省略せず、専門用語には短い説明を付ける

### 2. imperial-shorts-writer を起動する（工程10）

担当：`scripts/11_Shorts台本.md`

- 長尺の単純要約にしない
- Shortsだけで話を完結させない
- **ただし誤解させる切り取りは禁止する**
- 長尺への誘導を明確に入れる

### 3. imperial-fact-checker を起動する（検証）

- 事実IDが付いていない事実記述を洗い出す
- 台帳の記述より踏み込んだ書き方になっていないか確認する
- 分類Bが断定形になっていないか確認する
- 指摘は「どの行を、何に、なぜ」の形で出す

### 4. imperial-safety-reviewer を起動する（検証）

- 内心断定／対立煽り／誇張／敬称漏れ／品位／炎上リスクを検出する
- 4分類（使用可能／留保表現に変更／根拠追加が必要／使用禁止）で判定する

### 5. 差し戻しを反映する

imperial-writer / imperial-shorts-writer が修正する。
**検証したエージェントが直接書き換えない。**

### 6. 検査する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage check
```

`audit/00_機械検出レポート.md` で次を確認する。

- 「2. 禁止表現の検出」…使用禁止相当が0件か
- 「4. 台本と台帳の突合」…台帳に無いIDを参照していないか、
  確認状態が「使用不可」の事実を参照していないか
- 長尺台本の文字数が目標範囲に入っているか

指摘が残っている間は 3〜6 を繰り返す。

## 報告

- 文字数（機械計測値）と目標との差
- 差し戻し件数と、その対応結果
- 根拠不足で書けなかった内容
- 次のコマンド：`/imperial-production $ARGUMENTS`
