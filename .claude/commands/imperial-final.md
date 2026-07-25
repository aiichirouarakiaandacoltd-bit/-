---
description: 承認後に最終パッケージ（FINAL_EDITOR_PACKAGE）を生成し、編集者へ渡せる状態にする
argument-hint: <project_slug>
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# /imperial-final — 最終版の生成

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

## 前提

`projects/$ARGUMENTS/input/approval.yaml` の `approval_status` が `approved` であること。
そうでない場合、最終版は生成されない（終了コード2）。**勝手に approved へ書き換えない。**

## 手順

### 1. 承認内容を確認する

`input/approval.yaml` を読み、次を荒木愛一朗の記入内容として確認する。

- `selected_title`（採用タイトル）
- `selected_thumbnail`（採用サムネイル）
- `rejected_materials`（使用を認めない素材ID）
- `revision_notes`（修正指示）

`revision_notes` に修正指示があれば、**先に該当工程へ差し戻して反映する。**
反映せずに最終版を作らない。

### 2. 最終版を生成する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml \
    --stage final --approval projects/$ARGUMENTS/input/approval.yaml
```

### 3. 結果を確認する

**終了コード0（成功）の場合**

`projects/$ARGUMENTS/FINAL_EDITOR_PACKAGE/` に10ファイルが生成される。

```
01_編集者向け制作指示書_最終版.md   ← 主資料
02_長尺台本_最終版.md
03_Shorts台本_最終版.md
04_長尺素材設計_最終版.csv
05_Shorts素材設計_最終版.csv
06_素材権利台帳_最終版.csv
07_サムネイル制作指示_最終版.md
08_投稿設定_最終版.md
09_出典一覧_最終版.csv
10_納品前チェックリスト.md
```

警告が出ていれば、その内容を必ず荒木愛一朗へ報告する。
特に次の警告は見逃さない。

- 「最終監査結果が未判定のまま」→ `/imperial-audit` を実施する
- 「素材権利台帳（最終版）：Mxxx：権利未確認のため使用禁止」→
  その素材は編集者へ「使うな」として渡る。代替案が入っているか確認する

**終了コード3（ブロック）の場合**

生成は行われていない。表示された理由に従って修正する。

| ブロック理由 | 対応 |
| --- | --- |
| 使用不可の事実を参照している | 該当箇所を削除するか、事実台帳を更新する |
| 台帳に無い事実IDを参照している | 事実台帳へ追加するか、参照を修正する |
| 架空URLが含まれている | 該当URLを削除する |
| AI生成顔・顔加工素材が含まれている | 素材を削除する |
| 最終監査結果が「不合格」 | 指摘を修正して再監査する |

**ブロックを迂回する方法を探さない。** ブロックは安全装置である。

### 4. 主資料を通読する

`01_編集者向け制作指示書_最終版.md` を、編集者になったつもりで最初から読む。

<!-- SCAN:OFF -->
- [ ] 何を作るのか、質問せずに分かるか
- [ ] 台本と素材が対応しているか
- [ ] 使用禁止素材が明確か
- [ ] BGM名とクレジットが入っているか
- [ ] 内部情報（採点、未採用案、内部リスク評価）が残っていないか
- [ ] 価格・納期・契約条件が混入していないか
<!-- SCAN:ON -->

## 報告

- 生成ファイル数と、警告の内容
- 使用禁止へ変換された素材の一覧
- 主資料の通読結果
- 荒木愛一朗が編集者へ渡す前に確認すべき事項
