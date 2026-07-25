---
description: 皇室物語の新規プロジェクトを作成し、入力ファイルの記入を支援する
argument-hint: <project_slug> [テーマ]
allowed-tools: Read, Write, Edit, Bash
---

# /imperial-new — 新規プロジェクトの作成

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

引数：`$ARGUMENTS`（1つ目＝project_slug、2つ目以降＝テーマ）

## 手順

1. `imperial_pipeline/` ディレクトリで次を実行する

```
python run_imperial_pipeline.py --init <project_slug>
```

2. `projects/<slug>/input/project_input.yaml` を開き、引数から分かる範囲を記入する

- `project_slug` は半角英数字・アンダースコア・ハイフンのみ
- `target_length_minutes` のような文字列型は使わない。min / max の数値2項目
- **分からない項目を推測で埋めない。** 空欄のままでよい

3. 過去動画データがあれば `projects/<slug>/input/past_videos.csv` へ記入するよう案内する
   （無くても処理は止まらない）

4. 記入内容を荒木愛一朗へ提示し、不足があれば確認する

5. 次のコマンドを案内する

```
/imperial-research <project_slug>
```

## 注意

- 既存の `project_input.yaml` がある場合、**上書きしない**（`--init` は既存を保護する）
- サンプルとして動かす場合は `sample_mode: true` を指定する
