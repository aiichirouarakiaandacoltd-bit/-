---
description: 皇室物語の内部学習教材動画を、係(サブエージェント)で制作ルール(docs/production_rules.md)どおりに制作する指揮。引数「テーマ | 主役 | 縦型/横型」(例: /kabu 愛子さまの園遊会 | 愛子内親王殿下 | 縦型)
---
あなたはメイン(/kabu の指揮)です。**docs/production_rules.md(2026-11-21版)を正とし、旧版は参照しない。**
成果物は Claude塾の内部学習教材専用。外部への公開・配布・共有は一切しない。
荒木さんの承認は **G0(企画)と G3(台本)** の2か所。承認がない限り次へ進まない(代行しない)。

## 手順
1. 引数 `$ARGUMENTS` を「テーマ | 主役 | 縦型/横型(省略時 縦型)」に分け、
   `bin/kabu new --topic "<テーマ>" --subject "<主役>" --kind <縦型|横型> --job <制作番号>` で案件を作る(制作番号は例 KB-YYYYMMDD-01)。
2. 以後くり返す: `bin/kabu next` を見て、
   - kind=tool → `bin/kabu run <工程>` → 成功なら `bin/kabu done <工程>`
   - kind=agent / check → 担当の係を Agent ツールで呼ぶ(下表)。check で「判定: 不合格」なら `bin/kabu fail <工程> --note "<直し指示>"`
   - kind=gate(G0・G3)→ 成果物(plan.md / script.md・scenes.json)を荒木さんに示して承認を待つ。承認を得たら `bin/kabu approve G0|G3 --note "荒木さん承認 <日時>"`
3. 停止条件(本書第7章)に当たったら生成を止め、不足事項・理由・必要な対応を報告する。
4. G5 の qa_report.md が全項目合格のときだけ「完成」と報告する。

| 工程 | 係(subagent_type) | 出力 |
|---|---|---|
| env_check | (tool) | env_check.md(不合格なら停止) |
| research | tanashirabe | research/<番号>/candidates.json |
| plan(G0) | kikaku | plan.md(型A/B/C・疑問・回答の要旨・100点評価。80点以上で候補) |
| facts(G1) | jijitsu | facts.md(F1…の表。公式事実/報道/分析・出典URL) |
| images(G2) | seisaku → `bin/kabu run images --pages <宮内庁等の写真ページ> --commons <検索語>` | ledger.csv(キャプションで人物・行事を確認できたものだけ) |
| script(G3) | daihon | script.md(章ごとの完成ナレーション全文)+ scenes.json(第6章の項目を省略なく・fact_ids・role=question/body/answer) |
| rules_script | kimari | 本書で採点 |
| render(G4) | (tool)kakidashi | output/<番号>_<縦型|横型>_internal.mp4 |
| frames | atekko | 人物の取り違え・崩れの点検 |
| qa(G5) | (tool)→ kakunin が qa_report.md を読んで直し指示 | qa_report.md |
| thumb_* | thumb-title / designer-key | 表紙画像(人物1〜2人・短い疑問文・濃紺/金/白・赤なし)、Canva デザイン |

## scenes.json の場面(本書第6章)
`{"scene":"03-2","chapter":"…","role":"question|body|answer","narration":"完成ナレーション","fact_ids":["F3"],
  "image":"A015","crop":"全身|顔の寄り|手元・装い|全体","motion":"ゆっくり拡大|ゆっくり縮小|左へパン|右へパン",
  "person_label":"愛子内親王殿下","caption":"2026年10月29日 園遊会(赤坂御苑)"}`
比較場面は `"compare":{"images":["A002","A005"],"labels":["…","…"]}`。start/end/subtitle は G4 で実測値を記入する。
「前と同じ」「台帳参照」「以下同様」の省略は禁止。1場面のナレーションは縦型で2〜4秒(約10〜20字)を目安にし、
同じ画像は1本につき3回まで(使い回すときは切り抜きと動きを変える)。

## 表紙画像(Canva)
テンプレート `DAHatUQFKSI` を copy-design → 写真を create-upload-url でアップロード → 文字・写真を差し替え → commit → export。
テンプレート本体は変更しない。赤は使わない。
