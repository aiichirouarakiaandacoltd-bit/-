---
description: 工程6〜8（企画評価・タイトル/サムネイル案・長尺構成）を実行する
argument-hint: <project_slug>
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

# /imperial-plan — 企画工程（工程6〜8）

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

## 前提の確認

`research/05_事実台帳.csv` に確認済みの事実が入っていること。
空のまま企画評価を行わない。事実が無ければ `/imperial-research` へ戻る。

## 手順

### 1. production-director を起動する（工程6）

担当：`planning/07_企画評価.md`

- 配点は `config/settings.yaml` の `scoring`（合計100点）
- 点数だけでなく、伸びる理由／クリック理由／継続理由／見せ場／リスク／
  修正案／結論を必ず書く
- **重大な事実・権利問題があれば、点数にかかわらず制作停止を提案する**

判定が「原則見送り（64以下）」または制作停止提案の場合、
**ここで止めて荒木愛一朗へ報告する。** 先の工程へ進まない。

### 2. production-director を起動する（工程7）

担当：`planning/08_タイトル・サムネイル案.md`

- タイトル10案（本命／安全重視／感情重視／事実重視／検索重視）
- サムネイル5案。文言は4〜14文字程度
- タイトルとサムネイルで同じ言葉を繰り返さない
- 使用画像候補は素材IDで指定する

### 3. imperial-safety-reviewer を起動する

タイトル・サムネイル案を検証する。

- 煽り、対立、内心断定、虚偽がないか
- 本編に無い情報を書いていないか
- 視聴者を欺く構成になっていないか

問題があれば production-director へ差し戻す。

### 4. imperial-writer を起動する（工程8）

担当：`planning/09_長尺構成.md`

- センターピンを1文で決める
- 章ごとに役割と事実IDを割り当てる
- 感情の流れは、テーマに合うものを選ぶ（型に当てはめない）
- 冒頭30秒でテーマと視聴理由を提示する設計にする

### 5. 検査する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage check
```

## 報告

- 企画評価の合計点と判定
- 推奨タイトル・サムネイルの組み合わせ
- 章構成と想定文字数の配分
- 次のコマンド：`/imperial-script $ARGUMENTS`
