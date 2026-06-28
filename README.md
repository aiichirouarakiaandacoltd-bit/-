# ザ・ダンク 動画制作自動化システム

バスケットボールYouTube Shortsチャンネル「ザ・ダンク」の動画制作を自動化するシステムです。

## 機能

- ザ・ダンクチャンネル動画の自動取得・候補選定
- 優先選手・プレータイプに基づく自動スコアリング
- 動画の自動ダウンロード・メタデータ一次リスク判定
- 音声除去・9:16リサイズ・セグメント切り出し
- 台本自動生成（技術解説・戦術解説・比較・記録など）
- VOICEVOX音声合成（本番話者: 青山龍星、速度: 0.95）
- 字幕焼き込み（ASS形式）
- BGMミキシング
- コート図・テキストカード自動生成
- 品質検査（ffprobe・decode検査・0KB検査）
- publishable三段階判定（technical_publishable / manual_review_required / publishable）
- 投稿用メタデータ生成
- 選手名正規化

## セットアップ

### 必要なソフトウェア

- Python 3.9以上
- FFmpeg（ffprobe含む） — 動画合成・品質検査に必須
- VOICEVOX — 本番モードの音声合成に必須。事前に起動しておくこと（http://localhost:50021）
- yt-dlp（`pip install yt-dlp`） — YouTube動画の自動取得に必須
- Pillow（`pip install Pillow`） — コート図・テキストカード生成に必須

### フォルダ構成

```
the-dunk-video-automation/
├── main.py                       # メインエントリーポイント
├── run_local_production_test.bat  # ローカル本番テスト（19ステップ）
├── run_production.bat             # 本番実行
├── run_test.bat                   # テスト実行
├── check_environment.bat          # 環境チェック
├── config/                        # 設定ファイル
│   ├── settings.json
│   ├── source_permissions.json
│   └── player_aliases.json
├── inputs/                        # 入力素材
│   ├── owned_videos/
│   ├── licensed_videos/
│   ├── images/
│   ├── scripts/
│   └── topics/
├── outputs/                       # 出力（正式保存先）
│   ├── production/<run_id>/       # 本番出力
│   │   ├── final.mp4              # 正式出力MP4
│   │   ├── publishable.json       # publishable判定結果
│   │   ├── quality_report.json    # 品質検査レポート
│   │   ├── status.json            # 実行ステータス
│   │   ├── rights_report.md       # 権利レポート
│   │   ├── execution.log          # 実行ログ
│   │   ├── summary.md             # サマリー
│   │   ├── screenshots/           # 確認用スクリーンショット
│   │   └── ...
│   └── test/<run_id>/             # テスト出力
│       └── TEST_ONLY_final.mp4
├── output/                        # 互換コピー（正式保存先ではない）
│   └── final.mp4
└── lib/                           # ライブラリ
```

## 出力パス

- **正式出力**: `outputs/production/<run_id>/final.mp4`
- **テスト出力**: `outputs/test/<run_id>/TEST_ONLY_final.mp4`
- **互換コピー**: `output/final.mp4`（正式保存先ではない。過去互換のためのコピー。0KB検証後にのみ作成）

`output/final.mp4` は最新の成果物へのコピーであり、正式保存先ではありません。正式な出力は必ず `outputs/production/<run_id>/final.mp4` を参照してください。

## 使い方

### Windows（ローカル本番テスト）— 初心者向け手順

以下の手順で、初めてでも迷わずにテストを実行できます。

1. **VOICEVOXを起動する**
   - VOICEVOXアプリケーションを起動し、画面が表示されるまで待つ
   - http://localhost:50021/version にブラウザでアクセスして応答を確認（任意）

2. **コマンドプロンプトを開く**
   - Windowsキー → `cmd` と入力 → Enter

3. **リポジトリフォルダへ移動する**
   ```
   cd C:\Users\あなたのユーザー名\the-dunk-video-automation
   ```

4. **run_local_production_test.bat を実行する**
   ```
   run_local_production_test.bat
   ```
   またはエクスプローラーで `run_local_production_test.bat` をダブルクリック

5. **出力された final.mp4 を確認する**
   - バッチファイルの最終出力に表示されるパスの `final.mp4` を開いて目視確認
   - `outputs/production/` 内の最新フォルダに保存されている

6. **metadata / report を確認する**
   - `publishable.json`: publishable判定結果と投稿不可の理由
   - `quality_report.json`: 品質検査の全項目
   - `rights_report.md`: 権利レポート
   - `status.json`: 実行ステータス
   - `summary.md`: 全体サマリー

7. **publishable判定を確認する**
   - `publishable=true`: 荒木による目視確認後に投稿可能
   - `publishable=false`: `publish_blockers` に記載された理由を確認。投稿不可
   - `technical_publishable=true` かつ `manual_review_required=true`: 技術的条件は満たしているが目視確認が未完了

### Windows（完全自動モード）

1. VOICEVOXを起動する
2. `check_environment.bat` をダブルクリック → PASSを確認
3. `run_production.bat` をダブルクリック → チャンネルから自動取得・Shorts生成
4. `outputs/production/<run_id>/final.mp4` を確認してから投稿

### コマンドライン

```bash
# 本番モード（完全自動: チャンネルから動画取得→Shorts生成）
python main.py --mode production

# テストモード（VOICEVOX不要）
python main.py

# テーマ指定
python main.py --topic "河村勇輝のノールックパスが凄い理由" --mode production

# 選手指定
python main.py --player "河村勇輝" --mode production

# ローカル動画指定
python main.py --video inputs/owned_videos/sample.mp4 --mode production

# 台本指定
python main.py --script-file inputs/scripts/script.txt --video inputs/owned_videos/sample.mp4
```

## モード

- **production**: VOICEVOX必須（青山龍星・速度0.95・動的ID取得・代替音声禁止）、権利確認済みBGM必須、全品質チェック
- **test**: テスト音声使用可、技術検証用（TEST ONLY、投稿不可）

## 動画仕様

- 9:16（1080×1920）
- 30fps
- 45〜59.5秒
- H.264 / AAC
- 字幕焼き込み

## publishable判定

パイプライン完了後、以下の三段階で投稿可否を判定します。

### technical_publishable

以下の全条件を満たした場合に `true`:

- production モードで実行
- VOICEVOX音声使用（青山龍星、速度0.95、フォールバック不使用）
- BGMファイルとライセンス情報が存在
- 解像度 1080x1920、コーデック H.264、再生時間 規定範囲内
- decode検査 PASS
- 0KBファイルなし
- メタデータ一次リスク判定が NG でない
- ウォーターマーク判定が NG でない
- 元動画の音声が除去済み
- 確認用スクリーンショットが存在

### manual_review_required

`embedded_footage_rights` が `UNKNOWN` の場合は常に `true`。荒木による目視確認が必要。

### publishable

`technical_publishable=true` かつ `manual_review_required=false` の場合のみ `true`。

### publishable=false の場合

`publishable.json` の `publish_blockers` フィールドに、投稿できない具体的な理由が日本語で記録されます。`status.json` と `summary.md` にも同様の情報が含まれます。

## 権利について

- `owned` / `owned_alias` / `licensed` 素材のみ完成MP4に使用可能
- `reference_only` 素材は企画分析・参考専用
- 第三者素材の無断取得・使用禁止

## メタデータ一次リスク判定

自動パイプラインでは yt-dlp から取得可能なメタデータ（タイトル・説明文・タグ）のみでリスク判定を行います。これは確定的な権利判定ではありません。

- `channel_source_permission`: チャンネル所有権（owned/reference_only）
- `embedded_footage_rights`: 動画内の第三者映像（常に UNKNOWN - フレーム解析なしでは判定不可）
- `metadata_risk_status`: メタデータキーワードによるリスク評価（LOW_RISK/HIGH_RISK/NG/UNKNOWN）
- `audio_risk_status`: 音声リスク（REMOVED/LOW_RISK/HIGH_RISK/NG/UNKNOWN）
- `watermark_status`: ウォーターマーク有無（常に UNKNOWN - フレーム解析なしでは判定不可）
- `manual_review_required`: 荒木による目視確認が必要か（embedded_footage_rights=UNKNOWN の場合は常に true）
- `publishable`: 最終投稿可否（manual_review_required=true の場合は常に false）

## 本番 Ver1.0 完成条件

以下の全てが Windows ローカル環境で確認できた時点で Ver1.0 完成とします。

1. `python main.py --mode production` が正常終了する
2. `outputs/production/<run_id>/final.mp4` が生成され、0KB ではない
3. ffprobe で解像度 1080x1920、H.264、AAC、30fps、再生時間 45-59.5秒 が確認できる
4. decode検査が PASS
5. 0KBファイルが出力フォルダ内に存在しない
6. `publishable.json` が生成され、判定結果が明確に記録されている
7. `publishable=false` の場合でも、`publish_blockers` に理由が記録されている
8. VOICEVOX音声（青山龍星・速度0.95）が使用されている
9. 上記が `run_local_production_test.bat` で一括確認できる
