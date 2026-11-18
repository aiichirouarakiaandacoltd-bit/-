# 皇室ニュース Shorts 自動制作システム(日本が誇る皇室物語)

参考ショート動画の構成・字幕・テンポを分析して編集ルール化し、**ニュース調査 → 事実確認 → 台本 → 素材 → 音声 → 字幕 → 編集 → MP4 → 品質検査** を1コマンドで実行します。

## 使い方

```bash
./run.sh --setup                                      # 初回のみ(依存パッケージ・日本語フォント)
./run.sh --topic "佳子さまの最新ニュース" --duration 60  # テーマ指定で制作
./run.sh                                              # テーマ未指定: 候補ニュースから自動選定
./run.sh --job <ジョブID> --from tts                    # 途中のステージから再実行
./run.sh --job <ジョブID> --only render                 # 1ステージだけ再実行
./run.sh --script my_script.json                      # 手書きの台本で制作(調査・台本生成をスキップ)
./run.sh --analyze references/新しい参考動画.mp4          # 参考動画の自動分析
tools/setup_voicevox.sh                               # VOICEVOX を起動(起動していれば自動で青山龍星を使用)
```

完成品: `output/<ジョブID>/<ジョブID>.mp4`。同じフォルダに `qa_report.json`(品質検査)、`upload_metadata.txt`(タイトル・概要欄・出典・写真クレジット)、`contact_sheet.jpg` を出力します。

## ステージ構成(それぞれ単独で再実行可)

| ステージ | モジュール | 内容 | 出力 |
|---|---|---|---|
| research | `pipeline/research.py` | 宮内庁「新着情報」(一次情報)+ Googleニュース RSS(報道)を収集し、媒体の信頼度・社数・発言の有無・新しさでスコアリング。宮内庁の記事と報道を自動で紐付け | `research/<job>/candidates.json` |
| script | `pipeline/script_writer.py` | `claude -p`(Claude Code ヘッドレス)が WebSearch/WebFetch で記事を確認し、事実(発生日/公開日・一次/報道・確認状況)と台本をJSONで出力。発言の一字一句一致・出典の有無を機械検証し、NGなら再生成 | `scripts/<job>/script.json` |
| assets | `pipeline/assets.py` | Wikimedia Commons の自由ライセンス画像のみ自動取得(ja.wikipedia経由+Commons検索)。ライセンス・作者・URL・取得日時・使用シーン・判定を記録。関連性フィルタあり | `assets/jobs/<job>/manifest.json` |
| tts | `pipeline/tts.py` | VOICEVOX(青山龍星・1.0倍)→ 未起動なら Open JTalk(1.0倍)。文ごとに合成して実測し、上限超過なら台本を自動短縮して再合成。読み補正辞書 | `audio/jobs/<job>/narration.wav`, `timeline.json` |
| subtitles | `pipeline/subtitles.py` | 文節単位で2行×11字に分割、モーラ数按分で音声と同期、人物名の色分け+核心語の赤強調、ポップ/スライド/フェード登場 | `subtitles/<job>/subtitles.ass` |
| bgm | `pipeline/bgm.py` | `audio/bgm/` の利用許可済み音源、無ければオリジナルBGMを数値合成 | `audio/jobs/<job>/bgm.wav` |
| render | `pipeline/render.py` | 顔検出で人物を字幕帯の上に配置した9:16化、ズーム1.00→1.09+軽いパン、シーン同期カット、冒頭の赤丸+矢印、資料写真ラベル+クレジット、図解カード代替、字幕焼き込み、ラウドネス調整(-16LUFS) | `output/<job>/<job>.mp4` |
| qa | `pipeline/qa.py` | 解像度/fps/コーデック/尺/黒画面/無音/音量/字幕途切れ/字幕行数/テンポ/カット割り/素材判定/台本検証 | `output/<job>/qa_report.json` |

## 参考動画の分析結果(要約)

詳細: `templates/reference_analysis_reference_01.json`(自動測定)、`templates/reference_style.json`(編集ルール)

- 技術: 406×720(9:16)/29.97fps/H.264 High/AAC 44.1kHz/59.9秒/-17.9 LUFS。台詞間の無音部は約-62dBで **BGMはほぼ無し**
- カット: 17カット、平均3.53秒(1.07〜6.26秒)。ほぼ全て静止画+ゆっくりズームイン、ハードカット
- 字幕: 画面高57〜65%の中央、極太ゴシック白文字+黒縁、1〜2行・1行10〜11字、約50チャンク(平均約1.2秒)。人物名は人物ごとの固定色、強い語は赤(白縁+黒外縁)。登場はポップ/スライド/フェード
- 構成: 冒頭1秒で人物を赤丸と矢印で示す視覚フック → テーマ提示 → 定説 → 核心を時系列で積み上げ → 余韻を残す締め
- 注意: 参考動画の題材は匿名の「証言」に基づく未確認情報で、AI生成風の画像も含む。**同じ題材・同種の表現は採用しない**(事実確認できないため)

## 素材の権利ポリシー

- 自動取り込みは **CC0 / パブリックドメイン / CC BY / CC BY-SA** のみ。NC・ND・フェアユース・不明は却下(`manifest.json` の `rejected` に理由)
- **宮内庁サイトの皇族方の写真・映像は取り込まない**。宮内庁の規約で「使用前に広報室へ相談」とされているため(https://www.kunaicho.go.jp/copyright/)。候補URLだけ `candidates_need_permission` に記録
- 報道写真は使わない(出典表示や「代表撮影」の表記は利用許可ではない)
- 自動取得した人物写真には「資料写真」とクレジットを画面に表示し、概要欄にもクレジットを出力
- 許可を得た素材は `assets/library/` に画像と同名の `.json`(`{"title","tags":[],"source","rights_holder","license","usage_ok":true}`)を置くと最優先で使われる
- 不適切な素材は `assets/jobs/<job>/exclude.txt` にファイル名の一部を書いて `--from assets` で再実行

## 設定ファイル

- `config/settings.json` — 出力仕様、音声エンジン、BGM音量、LLMバックエンド、ライセンス許可リスト
- `config/reading_dict.json` — 読み補正(例: 佳子さま→カコサマ)。台本の `readings` も自動適用
- `config/sources.json` — 媒体の信頼度区分、人物キーワード、除外する見出し語(批判・憶測系)
- `templates/reference_style.json` — 参考動画から抽出した編集ルール(カット長、ズーム量、字幕サイズ・位置・色、構成テンプレート)
- `templates/script_prompt.md` — 台本生成の指示文

## 必要環境

Python 3.11+、ffmpeg(libass)、Noto Sans CJK JP、`requirements.txt`(OpenCVは4.x: 5.xはHaar顔検出が無い)、台本生成に `claude` CLI(または `ANTHROPIC_API_KEY`)。
ネットワーク: news.google.com, www.kunaicho.go.jp, ja.wikipedia.org, commons.wikimedia.org, upload.wikimedia.org, thumb.wikimedia.org(VOICEVOX取得時は github.com 等)。
