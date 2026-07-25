---
description: 工程17（最終監査）と承認用サマリーを作成し、荒木愛一朗の判断項目を整理する
argument-hint: <project_slug>
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

# /imperial-audit — 監査工程（工程17・第8章）

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

## 手順

### 1. 機械検出を実行する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage check
```

`audit/00_機械検出レポート.md` を全節読む。

### 2. final-auditor を起動する（工程17）

担当：`audit/18_最終監査結果.md`

4面から監査する。

| 面 | 観点 |
| --- | --- |
| 事実 | 人物名／敬称／日付／場所／行事名／発言／制度／数字／時系列／主語 |
| 権利 | 素材URL／権利者／利用条件／クレジット／加工可否／AI生成表記／一般イメージ表記／報道素材 |
| 台本 | 内心断定／対立煽り／誇張／重複／矛盾／説明不足／誤解の可能性／難解な表現／主語抜け／敬語 |
| 指示書 | 素材不足／URL抜け／BGM名抜け／クレジット抜け／Shorts導線抜け／サムネイル指示不足／納品物不足／判断に迷う箇所／重複／古い仕様の混入 |

判定を次の行へ書き込む。

```
<!-- AUDIT_STATUS: 合格 / 条件付き合格 / 不合格 -->
```

**重大な事実誤認、人物誤認、権利上の危険、架空情報が1件でもあれば「合格」にしない。**
「不合格」にすると最終版の生成が自動的にブロックされる。

### 3. 差し戻す

指摘があれば、該当エージェントへ差し戻す。
**final-auditor が自分で書き換えない。**

差し戻し後は該当コマンド（`/imperial-script` など）を再実行し、
再び 1〜2 を行う。

### 4. final-auditor を起動する（承認用サマリー）

担当：`audit/19_荒木承認用サマリー.md`

- 集計欄（3・4・5のフラグ）はPythonが記入済み。**書き換えない**
- 判断項目は **最大10件**。次に限定する
  最終タイトル／最終サムネイル／企画の方向性／重要な事実表現／
  権利未確定素材の扱い／公開可否に関わるリスク
- **細かい言い回しを大量に確認させない**
- 各項目に「推奨」を必ず書く。判断を丸投げしない
- 総合判定を書く

### 5. 荒木愛一朗へ提示する

`audit/19_荒木承認用サマリー.md` の内容を要約して提示し、
`input/approval.yaml` の記入を依頼する。

```yaml
approval_status: approved
selected_title: 
selected_thumbnail: 
approved_risks: []
rejected_materials: []
revision_notes: 
```

## 報告

- 監査判定（合格／条件付き合格／不合格）と理由
- 差し戻し件数
- 荒木愛一朗の判断項目の件数と概要
- 次のコマンド：`/imperial-final $ARGUMENTS`（承認後）
