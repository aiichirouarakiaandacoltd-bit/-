---
description: 工程11〜16（素材設計・図解・サムネイル指示・投稿設定・編集者向け制作指示書）を作成する
argument-hint: <project_slug>
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

# /imperial-production — 制作設計工程（工程11〜16）

> すべてのコマンドは `imperial_pipeline/` ディレクトリを作業ディレクトリとして実行する。
> 先に `imperial_pipeline/agents/共通ルール.md` を読むこと。

対象プロジェクト：`$ARGUMENTS`

## 手順

### 1. production-director を起動する（工程11・12）

担当：`production/12_長尺素材設計.csv`（最大120行）／
`production/13_Shorts素材設計.csv`（最大20行）

- 権利確認状態は素材権利台帳から転記する。**格上げしない**
- 素材が無い行は「素材不足」と明記する
- 「代替素材」欄を空にしない
- Shortsは長尺素材の単純流用にせず、縦型構図で設計する

### 2. production-director を起動する（工程13）

担当：`production/14_図解・テロップ指示.md`

- 1枚に4項目以内
- 日付は和暦（西暦）併記
- 根拠となる事実IDを書く

### 3. production-director を起動する（工程14・15）

担当：`production/15_サムネイル制作指示.md`／`production/16_投稿設定.md`

- 確認状態が「要確認」の画像を推奨しない
- BGMクレジットは `config/settings.yaml` の `bgm_credit` をそのまま使う
- 問い合わせ先が未入力なら【お問い合わせ先：要入力】と書く。**架空のアドレスを作らない**
- 出典は実際にアクセスして確認したURLだけを載せる

### 4. rights-reviewer を起動する（検証）

素材設計の権利確認状態が、素材権利台帳と一致しているか突き合わせる。
一般イメージに「イメージ」の明示があるか確認する。

### 5. production-director を起動する（工程16）

担当：`production/17_編集者向け制作指示書.md`

**合格基準：この1点で編集者が迷わず作業を開始できること。**

作成後、定義ファイルの自己点検チェックリスト12項目を実施する。
1つでも「いいえ」があれば完成していない。

**価格、納期、契約条件を書かない。**

### 6. imperial-safety-reviewer を起動する（検証）

投稿設定文とサムネイル指示の表現を検証する。

### 7. 検査する

```
python run_imperial_pipeline.py projects/$ARGUMENTS/input/project_input.yaml --stage check
```

CSVの行数上限超過、必須列の欠落、定義外の値がないか確認する。

## 報告

- 素材設計の行数と、「素材不足」の行数
- 制作指示書の自己点検結果
- BGMクレジット・問い合わせ先が未入力のままかどうか
- 次のコマンド：`/imperial-audit $ARGUMENTS`
