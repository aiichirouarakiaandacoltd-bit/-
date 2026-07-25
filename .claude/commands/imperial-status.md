---
description: プロジェクトの進捗と未確認事項を確認し、次にやるべきことを示す
argument-hint: <project_slug>
allowed-tools: Read, Bash, Grep, Glob
---

# /imperial-status — 進捗確認

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

## 手順

### 1. 機械検査を実行する（生成物は変更されない）

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage check
```

### 2. 次を確認して報告する

| 確認先 | 見るもの |
| --- | --- |
| `audit/00_機械検出レポート.md` 1節 | 必須項目の欠落、未生成ファイル |
| 同 2節 | 禁止表現（使用禁止相当の件数） |
| 同 4節 | 台本と台帳の突合結果 |
| 同 5節 | 重大リスクのフラグ |
| 同 6節 | 未確認タグの集計 |
| 同 7節 | ID採番の重複・欠番 |
| 同 8節 | 安全素材ライブラリの登録件数 |
| `audit/18_最終監査結果.md` | `AUDIT_STATUS` の値 |
| `input/approval.yaml` | `approval_status` の値 |

### 3. 工程の進捗を判定する

各成果物がテンプレートのままか、記入済みかを判定する。
**見出しだけあって中身が空のものを「完了」と報告しない。**

| 工程 | ファイル | 判定基準 |
| --- | --- | --- |
| 1〜3 | research/01〜04 | 見出しの下に記述があるか |
| 4 | research/05_事実台帳.csv | データ行が1行以上あるか |
| 5 | research/06_素材権利台帳.csv | データ行が1行以上あるか |
| 6〜8 | planning/07〜09 | 記述があるか |
| 9・10 | scripts/10A・10B・11 | 本文に記述があるか |
| 11〜16 | production/12〜17 | データ行・記述があるか |
| 17 | audit/18 | AUDIT_STATUS が未判定でないか |
| 承認 | audit/19・input/approval.yaml | approval_status |

### 4. 次にやるべきコマンドを1つ示す

```
/imperial-research → /imperial-plan → /imperial-script
→ /imperial-production → /imperial-audit → /imperial-final
```

## 報告の形式

```
【進捗】
完了した工程：
未着手の工程：
記入途中の工程：

【要対応】
使用禁止相当の禁止表現：  件
必須項目の欠落：  件
台帳に無いIDの参照：  件
未確認タグ：  件

【最終版生成の可否】
ブロック要因：あり／なし（ある場合はその内容）

【次の操作】
```
