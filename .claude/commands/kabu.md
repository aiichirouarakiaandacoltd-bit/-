---
description: 皇室物語の動画を、係(サブエージェント)で制作ルール(docs/production_rules.md)どおりに制作する指揮。企画係が最新動向→競合調査→題材確定し、タイトルと概要の承認(1回だけ)後は完成まで自動。引数は任意「縦型/横型」(例: /kabu 縦型)
---
あなたはメイン(/kabu の指揮)です。**docs/production_rules.md(2026-11-21版)を正とし、旧版は参照しない。**
成果物は Claude塾の内部学習教材専用。外部への公開・配布・共有は一切しない。
荒木さんの承認は **G0(タイトルと概要)の1回だけ**(2026-11-21 荒木指示)。G0の承認がない限り次へ進まない(代行しない)。**G0の承認後は、荒木さんに承認を求めず、G6まで完成させる。** 停止条件(本書第7章)に当たった時だけ止めて報告する。

**競合調査と企画の型(本書第1-3章・2026-11-23):** 優先企画型 A型 行事×一場面×疑問＞B型 人物×過去×現在＞C型 条件付き比較。優先人物は愛子さま・雅子さま。
**動画の設計式(本書第1-2章・2026-11-23 荒木指示):** 強い疑問 × 確認できる事実 × 人物の物語 × 比較(事実×事実のみ) × 独自の解説。揶揄・対立はNG。G0の plan.md には5要素の表を入れて提示する。

## 係のモデル(2026-11-22 荒木指示)
当面は全係を設定どおり(Opus中心)で呼ぶ。Fableは11/27以降に荒木さんがプランをアップグレードしてから、重要な係(企画・事実確認・台本・タイトル・当てっこ・決まりの確認・確認・分析・型の分析)をFableに戻す。
Fableに戻した後に「requires usage credits」等で失敗した時は、同じ依頼を model: "opus" で呼び直す(止めない・荒木さんに聞かない)。

## 手順
1. 引数 `$ARGUMENTS` から縦型/横型(省略時 縦型)を読み、`bin/kabu new --kind <縦型|横型> --job <制作番号>` で案件を作る(制作番号は例 KB-YYYYMMDD-01。テーマは企画係が決める。荒木さんがテーマを指定した場合は --topic に入れ、企画係はそれを優先する)。
2. 以後くり返す: `bin/kabu next` を見て、
   - kind=tool → `bin/kabu run <工程>` → 成功なら `bin/kabu done <工程>`
   - kind=agent / check → 担当の係を Agent ツールで呼ぶ(下表)。check で「判定: 不合格」なら `bin/kabu fail <工程> --note "<直し指示>"`
   - kind=gate(G0のみ)→ plan.md の**タイトル(コードブロック)と概要**を荒木さんに示して承認を待つ。承認を得たら `bin/kabu approve G0 --note "荒木さん承認 <日時>"`。以後、承認は求めない
3. 停止条件(本書第7章)に当たったら生成を止め、不足事項・理由・必要な対応を報告する。
4. G5 の qa_report.md が全項目合格のときだけ「完成」と報告する。
5. 完成後は G6(本書第9章): タイトル→表紙3段・中心画像→説明文。**タイトルと説明文はそれぞれコードブロックで荒木さんに提示し、一括コピーできる形にする。** 投稿はしない。

| 工程 | 係(subagent_type) | 出力 |
|---|---|---|
| env_check | (tool) | env_check.md(不合格なら停止) |
| research(R1) | (tool)tanashirabe | research/<番号>/candidates.json |
| trends(R1) | kikaku | research/<番号>/trends.md(直近の皇室の動向) |
| competitors(R2) | kikaku | research/<番号>/competitors.md(伸びている競合動画・再生数は実測) |
| plan(G0) | kikaku | plan.md(題材と理由・タイトル・概要・100点評価)→ 荒木さん承認(唯一) |
| facts(G1) | jijitsu | facts.md(F1…の表。公式事実/報道/分析・出典URL) |
| images(G2) | seisaku → `bin/kabu run images --auto <人物名> --months <YYYYMM…>`(必要なら --pages/--commons) | ledger.csv(キャプション確認済み+要目視) |
| script(G3) | daihon | script.md(章ごとの完成ナレーション全文)+ scenes.json(第6章の項目を省略なく・fact_ids・role=question/body/answer) |
| rules_script | kimari | 本書で採点 |
| focus | atekko(当てっこ係) | 点検シート→ focus.json(主役位置)・要目視写真の照合(focus_sheet --check 合格) |
| render(G4) | (tool)kakidashi | output/<番号>_<縦型|横型>_internal.mp4 |
| frames | atekko | 人物の取り違え・崩れの点検 |
| qa(G5) | (tool)→ kakunin が qa_report.md を読んで直し指示 | qa_report.md |
| pub_title(G6①) | thumb-title(タイトル係) | publish.yaml の title(CTR20%以上を狙う99文字以内・ハッシュタグ付き) |
| thumb_title(G6②) | thumb-title(タイトル係) | タイトルから3段見出しを流用・中心画像を確定(publish.yaml の thumb, thumb.yaml) |
| thumb_render | designer-key | `bin/kabu run thumb_render` の canva_plan.json どおりに Canva を操作 → thumb_canva --fetch |
| pub_desc(G6③) | gaiyou(説明文係) | publish.yaml の本文・参考資料・ハッシュタグ |
| pub_check | (tool) | publish/title.txt・description.txt・check.md |

## scenes.json の場面(本書第6章)
`{"scene":"03-2","chapter":"…","role":"question|body|answer","narration":"完成ナレーション","fact_ids":["F3"],
  "image":"A015","crop":"全身|顔の寄り|手元・装い|全体","motion":"ゆっくり拡大|ゆっくり縮小|左へパン|右へパン",
  "person_label":"愛子内親王殿下","caption":"2026年10月29日 園遊会(赤坂御苑)"}`
字幕の改行を指定する時は `"subtitle_lines":[["1行目","2行目"],["次の字幕"]]`(つなげるとナレーションと一致すること)。
人物の写らない写真(会場の様子など)を並べる時は `"labels":{"A020":""}` で、その写真だけ人物名を出さない。
比較場面は `"compare":{"images":["A002","A005"],"labels":["…","…"]}`。start/end/subtitle は G4 で実測値を記入する。
「前と同じ」「台帳参照」「以下同様」の省略は禁止。1場面のナレーションは縦型で2〜4秒(約10〜20字)を目安にし、
**縦型は同じ画像を1本につき1回だけ(再使用禁止)**。横型は3回まで(使い回すときは切り抜きと動きを変える)。

## 素材の豊富さと画面の華やかさ(本書第4-2章・重要)
内容に合った実写映像・写真を可能な限り多く確保し、同じ画面の繰り返しや単調な図解を減らす。**量そのものを目的にしない**(内容と無関係な素材で水増ししない)。
- 長い場面は `"images":["A015","A016"]` で同じ行事の別素材を複数指定する(隣り合うカットに同じ画像を置かない)
- 実写映像(人物・行事を確認できる公式動画など)は ledger.csv の素材種別を「映像」にし、場面に `"clip":{"start":秒}` を書く
- 目安: 異なる画像÷カット数 縦型0.6以上・横型0.5以上/図解・文字だけの画面 縦型3秒以内・横型5%以内(G5で自動検査)
- 足りないときは同じ画像の繰り返しで埋めず、追加収集する。それでも足りなければ第7章で停止して報告

## 表紙画像(Canva)
テンプレート `DAHatUQFKSI` を copy-design → 写真を create-upload-url でアップロード → 文字・写真を差し替え → commit → export。
テンプレート本体は変更しない。赤は使わない。

## 公開後(G7)
分析係(bunseki)が CTR を実測し `bin/kabu run ctr --video-id <ID> --ctr <CTR%> --impressions <数> --views <数>` で記録する。
