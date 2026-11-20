---
description: 皇室ニュース動画を係(サブエージェント)で自動制作する指揮。引数「テーマ | 主役」(例: /kabu 雅子さまと久子さまの洋装 | 雅子さま,久子さま)
---
あなたはメイン(/kabu の指揮)です。組織図どおりに係を立て、`bin/kabu`(state.json)で工程を進めます。
承認者は荒木さん(テーマ・確認①・確認②・公開の4か所)。`--auto-approve` の案件ではメインが承認を代行し、理由を記録します。

## 手順
1. 引数 `$ARGUMENTS` を「テーマ | 主役」に分け、`bin/kabu new --topic "<テーマ>" --subject "<主役>"` で案件を作る(既にあれば `bin/kabu status`)。
2. 以後くり返す: `bin/kabu next` を見て、
   - kind=tool → `bin/kabu run <工程>`(棚調べ係・書き出し係に任せてもよい)→ 成功なら `bin/kabu done <工程>`
   - kind=agent / check → 担当の係を Agent ツールで呼ぶ(subagent_type は下表)。成果を読み、check で「判定: 不合格」なら `bin/kabu fail <工程> --note "<直し指示>"`、合格なら `bin/kabu done <工程>`
   - kind=gate → 荒木さんに承認を求める(auto_approve の案件は代行して `bin/kabu approve <テーマ|確認1|確認2|公開> --note "<代行の理由>"`)
   - 同じ工程の差し戻しが3回を超えたら止めて荒木さんに報告する。
3. 全工程が終わったら、完成動画・サムネPNG・Canvaリンク・publish.yaml・人が確認すべき点を報告する。

| 工程 | 係(subagent_type) |
|---|---|
| research | tanashirabe(棚調べ係) |
| brief | kikaku(企画係) |
| script | daihon(台本係) |
| factcheck | jijitsu(事実確認係) |
| rules_script / rules_publish | kimari(決まりの確認係) |
| assets・layout | seisaku(制作係)→ gamenwari(画面割り係)/ designer / designer-key / naoshi |
| tts・subtitles・render | kakidashi(書き出し係) |
| frames | atekko(当てっこ係) |
| review | kakunin(確認係) |
| video_review | douga-kakunin(動画の確認係) |
| shorts | short(ショート係) |
| thumb_frames・thumb_title | thumb-title(サムネ・タイトル係) |
| thumb_render | designer-key(デザイナー(重要))+ メインがCanvaを操作 |
| 公開後 | bunseki / tanashirabe / toorisugari / kata-bunseki |

## サムネ工程(thumb_frames → thumb_title → thumb_render)
1. `bin/kabu run thumb_frames` で候補フレーム5枚(output/<job>/thumbs/candidates/ の sheet.jpg・candidates.json。字幕なし映像から切り出し)。
2. サムネ・タイトル係が output/<job>/thumb.yaml を書く:
   ```yaml
   title: "動画タイトル"
   texts: {upper: "【…】", middle: "…", lower: "“…”"}   # 人の指定があれば一字一句そのまま
   adopted: 1                                           # 採用案
   variants:                                            # A/B/C 3案(YouTube Studio「テストと比較」用)
     - {layout: S-B, photos: [cand1, cand3], reason: "…"}
     - {layout: S-A, photos: [cand2], reason: "…"}
     - {layout: S-B, photos: [cand4, cand1], reason: "…"}
   ```
   と output/<job>/publish.yaml(タイトル3案・タグ・章・概要欄・出典・写真クレジット・VOICEVOX:青山龍星)。
3. `bin/kabu run thumb_render` で3案のPNG(thumbs/thumb_v*.png)、Canva用の写真(thumbs/v*_photo*.png)、canva_plan.json。
4. Canva(メインが操作): テンプレート `DAHatUQFKSI`(日本が誇る皇室物語｜3段テキスト基本)を copy-design → 写真を create-upload-url でアップロード(curl で生データをPOST)→ read-design(open_transaction)→ edit-design で写真枠の差し替え・上中下段の文字(一字一句)・文字サイズ/位置・デザイン名 → commit → export-design(PNG)。テンプレート本体は変更しない。書き出したPNGを thumbs/canva_v<n>.png に保存し、編集URLを canva_plan.json に記録。
5. 決まりの確認係がサムネ・投稿文を採点 → 公開承認。
