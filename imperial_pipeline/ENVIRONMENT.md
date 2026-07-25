<!-- network_status: 【アクセス未確認】外部ネットワークへの直接接続は不可（プロキシが403を返す） -->
# 実行環境の記録

- 記録日時：2026-07-25
- 記録者：Claude Code（構築時に自動確認）

## 確認結果

| 項目 | 実測値 | 確認方法 |
| --- | --- | --- |
| OS | Linux 6.18.5（x86_64） | `uname -a` |
| Python | 3.11.15 | `python3 --version` |
| PyYAML | 6.0.1（利用可能） | `python3 -c "import yaml"` |
| 標準ライブラリのみで動作 | 可（PyYAML以外の追加依存なし） | 実装で確認 |
| 外部ネットワーク | **不可**（プロキシが CONNECT を403で拒否） | `urllib.request` / `curl` |
| 文字コード | すべて UTF-8 明示。CSVは utf-8-sig | 実装で確認 |
| 改行コード | LF（`\n`）に統一 | 実装で確認 |

### ネットワークの確認ログ（要約）

```
$ python3 -c "urllib.request.urlopen('https://www.kunaicho.go.jp/')"
URLError <urlopen error Tunnel connection failed: 403 Forbidden>

$ curl https://www.kunaicho.go.jp/
curl: (56) CONNECT tunnel failed, response 403
```

## この環境で何が起きるか

1. **Pythonからの外部アクセスは行わない**。
   そもそも本システムは仕様上、Pythonから外部APIを呼ばない（第0章 0-1）。
   したがってネットワーク不可でもパイプラインは正常に動作する。

2. **工程3（調査）はテンプレート生成のみとなる**（第0章 0-2）。
   この環境で調査を行う場合、全項目へ **【アクセス未確認】** を付す。
   **架空の調査結果を作らない。**

3. サブエージェントが Claude Code の WebFetch / WebSearch ツールを使える環境であれば、
   そちらの経路では調査できる場合がある。その場合も、
   - 取得できたURLと取得日を必ず `research/04_出典一覧.csv` へ記録する
   - 取得できなかったものは【アクセス未確認】を付す
   の2点を守ること。**確認できていないものを確認済みとして記載しない。**

4. `run_imperial_pipeline.py` は、このファイル1行目の
   `<!-- network_status: ... -->` を読んで生成物へ転記する。
   環境が変わった場合はこの行を書き換えること（Pythonは接続確認を行わない）。

## Windows環境で使う場合の注意

- ファイル名に `:` `*` `?` `"` `<` `>` `|` を使用しない（本システムは使用していない）。
- 生成されるファイル名には `・` が含まれる（例：`14_図解・テロップ指示.md`）。
  これはWindowsでも使用可能な文字である。
- CSVは `utf-8-sig` で出力しているため、Excelで開いても文字化けしない。
- 改行はLFで統一している。Excelでの編集後にCRLFへ変わっても検査は通る。

## 未確認事項

- VOICEVOX「青山龍星」の実測読み上げ速度（`chars_per_minute` の実測値）は
  **この環境では計測できない**。荒木愛一朗が実機で計測し、
  `config/settings.yaml` を更新すること。
