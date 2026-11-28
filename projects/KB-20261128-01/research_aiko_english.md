# 事実確認メモ KB-20261128-01「愛子さまとシンガポールの英語」

確認日: 2026-11-28 / 作成: 事実確認(調査係) / 状態: 下書き(コミットしていない)

## 0. 読み方

- **区分**
  - 公式事実 = 宮内庁のページの本文・ご日程に書かれていること
  - 報道 = 報道機関が伝えたこと。**今回は記事本文を取得できず、見出しだけを確認した**(取得できなかった理由は 5章)。報道の行で「」に入れたのは**見出しの文字そのまま**で、記事本文の引用ではない
  - 分析 = 公式事実や報道を当チームが並べたり数えたりした整理
  - 未確認 = 主要な出典では確かめられなかったこと。動画・台本では断定しない
- **方法**: 宮内庁のページは 2026-11-28 に curl で取り直した。ルビ(`<rt>` `<rp>`)とタグを除いた本文と、下表の「原文の引用」を機械照合している(空白の違いは無視)。報道の見出しは Google ニュースの RSS 検索(2026-11-28 取得)で確認した。URL 欄の news.google.com のリンクは、その RSS に載っていた記事へのリンク。
- 「」の中は原文そのまま。言い換えはしていない。宮内庁の原文にある全角の読点・かっこ・「御」「ご」の書き分けもそのまま残した。

### 出典の略号

| 略号 | 出典名 | URL |
|---|---|---|
| SG | 宮内庁「愛子内親王殿下のシンガポールご訪問時のおことばなど（令和8年）」(午餐会のおことば・ご感想) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/2026sgp.html |
| SGI | 宮内庁「シンガポールご訪問（令和8年）」(閣議了解・御日程の概要・**ご日程**) | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/index.html |
| N2611 | 宮内庁「天皇ご一家のご日程」(令和8年11月のページ) | https://www.kunaicho.go.jp/watch/activity/schedule01/202611/index.html |
| EMP24 | 宮内庁「天皇陛下お誕生日に際し（令和6年）」会見年月日：令和6年2月21日 | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/emperor2024.html |
| GBR24 | 宮内庁「英国ご訪問に際し（令和6年）」会見年月日：令和6年6月19日 | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/gbr2024.html |
| EMP26 | 宮内庁「天皇陛下お誕生日に際し（令和8年）」会見年月日：令和8年2月19日 | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/emperor2026.html |
| SK | 宮内庁「愛子内親王殿下ご成年をお迎えになっての記者会見」(令和4年3月17日) | https://www.kunaicho.go.jp/watch/activity/activity01/activity01-r040317.html |
| GRAD | 宮内庁「愛子内親王殿下学習院大学ご卒業に際しての文書回答」 | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/graduation.html |
| JOB | 宮内庁「愛子内親王殿下日本赤十字社ご就職に際しての文書回答」 | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/employment.html |
| LAOK | 宮内庁「愛子内親王殿下のラオスご訪問時のおことばなど（令和7年）」 | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/lao2025.html |

### 11/26 の調べ(KB-20261126-01・04 など)から変わったこと(重要)

1. **宮内庁にシンガポールの日ごとの「ご日程」が載った**(SGI の下半分)。11/26 の facts.md の「詳しいご日程は宮内庁に未掲載。日付と順番は言わない」は、**今は SGI を出典に日付と順番を言える**ように変わった。
2. SGI のご日程には `ターマン大統領表敬（大統領府）` `ターマン大統領主催午餐会ご臨席（大統領府）` と **「大統領府」** が載っている。一方、おことば(SG)の見出しは `ターマン大統領主催午餐会（イスタナ）` のまま。11/26 の決まり「大統領府は宮内庁の原文にないので使わない」(KB-20261126-01 F9)は見直しが必要。**どちらの言葉も、どのページの言葉かを添えて使う。**
3. SGI では日本庭園の訪問は `11月20日（金）` の午前。台帳 KB-20261126-04 の A156(Commons、撮影日 2026-11-18)は、備考で「日本庭園ご訪問の日は宮内庁に未掲載のため『ご訪問時の写真ではない』とは言えない」としていた。**撮影日が 11/18 で、ご訪問(11/20)の日ではないことが、公式のご日程で分かるようになった**(分析)。

---

## 1. シンガポールで英語を話された場面

### 1-A. 公式に確かめられる英語(宮内庁の原文に英語で載っているもの)

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| E1 | 午餐会のおことばの日付・場所 | 公式事実 | SG | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/2026sgp.html | 「令和8年11月18日（水）」「ターマン大統領主催午餐会（イスタナ）」 |
| E2 | おことばの最初の呼びかけ | 公式事実 | SG | 同上 | 「ターマン大統領閣下」「御列席の皆様、」 |
| E3 | 呼びかけの直後の4つの言葉。**4つ目が英語** | 公式事実 | SG | 同上 | 「Selamat Tengah hari （スラマッ・トゥンガ・ハリ）」「大家好（ダージャーハオ）」「வணக்கம்（ワナッカム）」「Good Afternoon」「（マレー語、華語、タミル語、英語でそれぞれこんにちは）」 |
| E4 | おことばの最後の乾杯の言葉は英語。宮内庁の訳は「乾杯」 | 公式事実 | SG | 同上 | 「結びに、シンガポール共和国のますますの御発展と国民の幸せ、そして、大統領閣下を始め、本日お集まりの皆様の御健勝を祈念いたしまして、杯を挙げたいと存じます。」「To your health.（乾杯）」 |
| E5 | 同じ日の午前に大統領表敬、午後に午餐会(会場はご日程の表記で「大統領府」) | 公式事実 | SGI | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/index.html | 「11月18日（水）」「ターマン大統領表敬（大統領府）」「ターマン大統領主催午餐会ご臨席（大統領府）」 |
| E6 | 宮内庁に載っている英語は E3 の「Good Afternoon」と E4 の「To your health.」の2つだけ。おことばの本文は日本語で載っている。**本文を実際に何語で述べられたかは、宮内庁のページに書かれていない** | 分析 | SG | 同上 | (原文に該当する記載なし) |
| E7 | 報道の見出しは、午餐会のあいさつを「4つの公用語」で始めたと伝えた。本文が何語だったかは見出しからは分からない | 報道 | TBS NEWS DIG(2026-11-18) | https://news.google.com/rss/articles/CBMiV0FVX3lxTFAwaVE3NDlYanFydkNUSXcyN1J6aG1TOXJ1NktvdWd2RVp1TjA0LVo0eEc1X3ljMTdLdmRDTjZJNVNsY2pNUnk3OTJ4Z3FRbnhJSnNCRjNjUQ?oc=5 | 見出し「シンガポール公式訪問中の愛子さま 大統領を表敬訪問し昼食会に出席 4つの公用語で挨拶も」 |
| E7b | 同上 | 報道 | FNNプライムオンライン(2026-11-18) | https://news.google.com/rss/articles/CBMiTkFVX3lxTE9JWF9mTjR1b1VmejlSRDcwMVlQSXZ1Y2dOT1VYQUh4bFgwRWFtX0g4TTkydHcxelUtRjZXM0hvVXNoUFpQNXRlX0FtR3dmdw?oc=5 | 見出し「愛子さま 振り袖姿でシンガポール大統領を表敬 4つの公用語交え挨拶」 |

### 1-B. 英語で懇談された場面(報道。英語の原文は未確認)

宮内庁のご日程で**その場面があったこと**は公式事実。**英語で話されたこと・その言葉**は、報道の見出しでしか確かめられていない。

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| T1 | 11月18日 午前、ターマン大統領を表敬 | 公式事実 | SGI | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/index.html | 「ターマン大統領表敬（大統領府）」 |
| T2 | 表敬で大統領と英語で懇談(記帳のあと) | 報道 | 日テレNEWS NNN | https://news.google.com/rss/articles/CBMifEFVX3lxTE9TSXJjYks0ZDRMVUNUZzkzRzZ5ZE9zRmZMVS16WUhvSFZSS3BFaFQ0cnBNa3E1OXc2WUJzV3RxOUc0ZlVicVJSUDU3dkFrbzBkQVBvem9UZk9FX0twcVRsM2JfaGJpNXZpdm5Tb2RCRTBXMEU2a2V1UXpOd20?oc=5 | 見出し「【速報】愛子さま振り袖姿でシンガポール・ターマン大統領を表敬訪問 「愛子」と記帳した後、英語で大統領と懇談 公式訪問2日目」 |
| T3 | 同じ日の昼食会の報道でも「英語で懇談」 | 報道 | 日テレNEWS NNN | https://news.google.com/rss/articles/CBMifEFVX3lxTE5zTjNzN3IzdjhUMlBkLWhCR0NkaE9uZHJacFlZc0N5d3JtOUhuT0FDTXB3NUZTRXhNV2R5bDVoRjQycUZTUlVZRy1nMmd1R2FpTVFHRFFJM1pKRHBOdDJ5QUQ0ZEJHcVBxUnpsVjRnN1hRM29VZi0wUkRyRWc?oc=5 | 見出し「愛子さま、シンガポール大統領主催の昼食会でお言葉 大統領と英語で懇談も（2026年11月17日掲載）｜日テレNEWS NNN」(※見出しの「11月17日掲載」は見出しの表記のまま。ご日程では表敬・午餐会は18日) |
| T4 | 大統領との英語は「通訳なしで55秒」 | 報道 | ABEMA TIMES(Yahoo!ニュース配信) | https://news.google.com/rss/articles/CBMif0FVX3lxTE9QQnlhVjR4eWdiM3c2QXhGN3BEVXhUTXk4S2p4aXF5eGVjTDI0bmlJRUc5VTZTY0s1elk2c3ZnNDFwNzIwMVhBUFNnSnUzcHhtcEV0alM5c05pU3l6SHVWRWpyMzdXbFEyWkdhTVFZVFRfcHpnU21HRUtXOGZmY2c?oc=5 | 見出し「愛子さま“通訳なしで55秒”の英語挨拶、上品な和服姿でのコミュニケーション力に「カンペも見ないで素晴らしい」「キレイでわかりやすい」SNSで反響 シンガポール公式訪問（ABEMA TIMES）」(※「カンペも〜」はSNSの声の引用。愛子さまの言葉ではない) |
| T5 | 同(通訳もメモもなし) | 報道 | ライブドアニュース(配信元は見出しから不明) | https://news.google.com/rss/articles/CBMiXkFVX3lxTE95dEtUalM2Ym9kQnU0SXI4c2k4M2JWLW4xQm9KdWlUYnVHbXB5WHMtT2dMLVJ6TWtZM3pGazlBVGRqd2FWYUhieVN3eTZGX3dBeGNvYWZoeFUwcm9nbWc?oc=5 | 見出し「愛子さま、通訳もメモもなく英語でシンガポールの大統領と懇談 称賛広がる (2026年11月19日掲載)」 |
| T6 | 大統領に英語で何と言われたか(英語の原文と和訳) | **未確認** | — | — | 主要報道の本文を取得できなかった。手がかりは個人の YouTube チャンネルの説明文だけ(下の U1)。使わない |
| L1 | 11月19日 午後、リー上級大臣とご接見 | 公式事実 | SGI | 同 SGI | 「リー上級大臣ご接見（大統領府）」 |
| L2 | リー上級大臣と英語で懇談。見出しの言葉は日本語(英語の原文ではない) | 報道 | 日テレNEWS NNN | https://news.google.com/rss/articles/CBMifEFVX3lxTE9EWjZEUmZ4Z19rd0ctUG9wWG5hTDV1aDdCTmwxYU9pUG9SeV9TQ20wYnFXU1V1ZklnZ0VRamMtR2xteG9JdFozMGRNdFFyS2dRU1dVczRzUDl6bE1lNHdfZXdSREhQZ0dUU3lyWWhWN1N2SDhsMFFlUlNkMFo?oc=5 | 見出し「愛子さま シンガポール“建国の父”長男と英語で懇談 「長年の尽力に敬意と感謝」 両陛下・上皇ご夫妻と親交あるリー・シェンロン上級大臣」 |
| L3 | 「長年の尽力に敬意と感謝」の英語の原文、だれの言葉か(愛子さまか、記者の要約か) | **未確認** | — | — | 見出しだけでは分からない |
| G1 | 11月19日 午前、ガン首相代行とご接見 | 公式事実 | SGI | 同 SGI | 「ガン首相代行ご接見（大統領府）」 |
| G2 | 首相代行に「約1分の英語」。見出しの「」は ABEMA の和訳 | 報道 | ABEMA TIMES | https://news.google.com/rss/articles/CBMiVEFVX3lxTFB0VHpVS3NUQk5LVF9JUWV2Qno4NVVhQ3BqMl9hSTVsSlZ6Vm5RRTRQWTFiNG9Ha0hURUtGaDYxOW9QQzlNaDNLVkYwbmpqU1lWVWx6Zg?oc=5 | 見出し「愛子さま「滞在を楽しんでいます」約1分の英語で“初めてのシンガポール”への想いを語られる 首相代行に「素晴らしい関係が今後も成長し続けることを…」シンガポール」 |
| G2b | 同じ内容の別の見出し(ABEMA の番組ページ) | 報道 | ABEMA(わたしとニュース) | https://news.google.com/rss/articles/CBMiWEFVX3lxTE5jTFRSbDE3R1g5aS1Yd0pCcTlaU2pkenZvaXRWS0Ywc1Atay1wZzc0RWNjMU1TVGE4YUY1VEtodXBRdE1rUWhmb1Yza2RieENDVnlmeEdrRHQ?oc=5 | 見出し「愛子さま「ここでの滞在を楽しんでいます」約1分の英語で“初めてのシンガポール”への想いを語られる 「私達の素晴らしい関係が今後も成長し続けることを願っています」」 |
| G3 | G2 の英語の原文 | **未確認** | — | — | 和訳の言い回しが2本の見出しで違う(「滞在を楽しんでいます」/「ここでの滞在を楽しんでいます」)。英語の原文は見つからなかった。**和訳を愛子さまの言葉として「」で出すなら「ABEMA の訳」と明記する** |
| M1 | 博物館など、取材カメラのない場所でも英語で自ら質問されていた(同行記者の話) | 報道 | ABEMA TIMES(2026-11-27) | https://news.google.com/rss/articles/CBMiVEFVX3lxTE5raGdkWHE5SWFjbmNUbzJaZEd5Z3V5SlRTaHFNa01HQzNHcmhaaVF0NEJJbzRCU0NQUkpEeVFBX0FGYnhiN2NGMWZGT0NYSmRLeVVhRQ?oc=5 | 見出し「注目集めた愛子さまの “英語力”「自然にスラスラ…」取材カメラがない場所でも発揮!? 「ご自身で質問を」 現地同行記者が明かすシンガポール訪問舞台ウラ」 |
| M2 | どこで・だれに・何を英語で質問されたか | **未確認** | — | — | 見出しに場所の名前はない。「博物館」と書いているのは個人の YouTube チャンネルの説明文だけ |
| M3 | 出発前の勉強と英語力について、同行記者に聞いた番組 | 報道 | ABEMA(わたしとニュース・2026-11-26) | https://news.google.com/rss/articles/CBMiWEFVX3lxTE82Y1dzd2pPNnVmaU8yQjhYVFlub2d5Y3BQYmhFRkZ2Qm9OOWdjZ2dFdC1nYmM1aUVackVwVUQxMjl0dUVkYTNsc0lkTWFjS1E3MDNaemdPeHU?oc=5 | 見出し「愛子さま訪問の舞台裏 シンガポールに同行の記者に聞く 出発前の“猛勉強”&英語力の理由 平日は日赤出勤でテレワークもご活用→ご一家の美術館観覧は終業後に」 |

### 1-C. 植樹式のあとの記者への受け答え(英語ではない可能性が高い。言語は未確認)

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| R1 | 11月20日 午前、ジュロン日本庭園の植樹式 | 公式事実 | SGI | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/index.html | 「11月20日（金）」「ジュロン日本庭園植樹式ご臨席、ご視察」 |
| R2 | 植樹のあと、記者の質問に答えられた(20日) | 報道 | 共同(西日本新聞me の写真説明) | https://news.google.com/rss/articles/CBMiV0FVX3lxTE8yOGNOUThHY1RkMllNdGFwSzZhTmMwam1qYTI5ODZCWVBVbTJRTC12eTZGR2ZBa01KOUFMMFRWV2ZoSGN0LVJJckcxWjhDNWZEbzRPeHBCaw?oc=5 | 見出し「記念植樹を終え、記者の質問に答えられる愛子さま＝20日、シンガポール（代表撮影・共同）」 |
| R3 | 感想の言葉(日本語で報じられている) | 報道 | 日テレNEWS NNN | https://news.google.com/rss/articles/CBMifEFVX3lxTE9jQS0zR3luZnFpUzUzaU9veWRXM3pzT2E4UmFzLWVjUm5LYThUNENKd2RtaEFOQWw3MW5rMmUwMW53X1h4UzZobDFsZnZrODB0SGwwM0R4ajBYZ3YyS2haNDhaeldRQ25MVTU4TTFZYmF5U1B5cWhVWlpuN0w?oc=5 | 見出し「【速報】愛子さま シンガポール訪問の感想を語る「新しい経験に満ちた実り多い滞在」 外国公式訪問で初めて 日本庭園でフクギの植樹式 “友好の象徴”ソテツもご覧」 |
| R4 | 同じ場面で、英語で話しかけられて笑顔で応じた一幕があった | 報道 | ABEMA(わたしとニュース) | https://news.google.com/rss/articles/CBMiWEFVX3lxTE9BZGZNZFA5bDg4TW9XeTZKQnk1eVllV1RXQ2ZicVJBMnlhelFvRWUwQXhndFRFaXZpOEYyS2VEXzVieHFKOHJ4TG1IWEdvSVcwdmgzQ2NwZkY?oc=5 | 見出し「愛子さまのお言葉をノーカットで 植樹後に記者の質問にご回答 シンガポール訪問に感謝の思い「実り多い滞在を...」英語で話しかけられ笑顔でご対応の一幕も」 |
| R5 | NHK 国際放送の英語の見出し | 報道 | NHK WORLD-JAPAN | https://news.google.com/rss/articles/CBMiY0FVX3lxTE1UY0VkVGlrSXBMWnVyNzl6VHJkMEVLY3FGQTJoMW9GckQxQXk1eWR1RWpCTXFmVDlPdjN4VnVEcndMTmNSMXBybG1ZbnBIeEdGdk5QM1VrWXRWaDdNZ2lQdHhIQQ?oc=5 | 見出し「Japan's Princess Aiko calls her Singapore visit 'fruitful'」 |
| R6 | 記者への受け答えが何語だったか。だれが英語で話しかけたか。何と答えられたか | **未確認** | — | — | 日テレ・ABEMA の見出しは日本語の言葉を「」で引いている。英語の答えだったという報道は見つからない。**「英語で記者に答えた」と言わない** |

### 1-D. 公式文書に「話した」と書かれている場面(何語かは書かれていない)

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| D1 | 交流に携わる人々と「直接お話しする機会」があった(ご感想) | 公式事実 | SG | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/2026sgp.html | 「今回の訪問では、幅広い分野で日本とシンガポールの友好親善に携わってこられた方々と直接お話しする機会にも恵まれ、両国の絆が長きにわたる人々の交流を通じて育まれ、深められてきたことを実感いたしました。」 |
| D2 | D1 に当たりそうなご日程(どの場面を指すかはご感想に書かれていない) | 公式事実 | SGI | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/index.html | 「歓迎行事ご臨席（日本人会館）、日本人会館ご視察」「在留邦人代表とのご接見（日本人会館）」「日本とゆかりのあるシンガポール人とのご接見（大使公邸）」(いずれも 11月19日（木）午後) |
| D3 | ご感想の全文に「英語」「言葉」「通訳」という語は1回も出てこない | 分析 | SG(ご感想) | 同上 | (機械で数えた結果: 英語 0回・言葉 0回・通訳 0回) |

### 1-E. 使わない手がかり(個人の YouTube チャンネル)

| # | 内容 | 区分 | 出典 | 扱い |
|---|---|---|---|---|
| U1 | 大統領表敬での英語の書き起こしらしい文: 「Thank you very much for your kind invitation and your kind words So welcome I'm honored to visit Singapore by your kind ...」 | 未確認 | YouTube 検索結果の説明文。チャンネル「皇室の素晴らしい物語」(競合)、動画 ID XPNChGq9WNg | 報道機関の書き起こしではない。字幕の自動生成の可能性もある。**台本・字幕に使わない**。日テレ NEWS の「【完全版】…＜和訳つき＞」(動画 ID KRViI91FrKY)に和訳があるが、動画ページは取得できなかった |
| U2 | 「It is a great honor」「大変光栄に思います」 | 未確認 | 個人チャンネル「人生の心つづり」(FcGtykZLOAg) | 使わない |
| U3 | 「もう通訳は必要ありません」(リー氏の言葉とするもの)など | 未確認(根拠なし) | 個人チャンネル | 使わない。報道で裏付けがない |

---

## 2. ご感想(令和8年11月21日)のうち、交流・人・学びにかかわる文

ご感想は**文書**。「書かれた」「つづられた」と言い、「語られた」とは言わない(11/26 の決まりと同じ)。

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| K1 | 題と日付 | 公式事実 | SG | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/2026sgp.html | 「シンガポールご訪問を終えてのご感想」「令和8年11月21日（土）」「シンガポールご訪問を終えて」 |
| K2 | 迎えてくれた人々への感謝 | 公式事実 | SG | 同上 | 「大統領、ガン首相代行及びリー上級大臣を始めとするシンガポール政府の方々に温かくお迎えいただき、大統領に午餐会を催していただくなど、心のこもったおもてなしをいただいたことに深く感謝申し上げます。」「また、行く先々でシンガポールの国民の皆様を始め、多くの方に歓迎していただいたことにも、心から御礼を申し上げます。」 |
| K3 | 多様な民族の文化 | 公式事実 | SG | 同上 | 「ラオパサ・ホーカーセンターでは、様々な民族の文化が共存するシンガポールの多様性に富んだ社会の一端に触れることができました。」 |
| K4 | 医療スタッフへの感銘 | 公式事実 | SG | 同上 | 「また、KKH小児血液がんセンターでは、高度な医療の実現を目指して進められている研究や、患者さんとその家族に寄り添う医療スタッフの方々のきめ細かい配慮に感銘を受けました。」 |
| K5 | 交流が受け継がれること | 公式事実 | SG | 同上 | 「これらの温かいお心遣いをうれしく思い、改めて感謝いたしますとともに、これからもこうした両国の交流が、友好の証として世代を超えて受け継がれていくことを願っております。」 |
| K6 | 人々との対話 | 公式事実 | SG | 同上 | D1 と同じ文 |
| K7 | 日本人学校の子どもたち | 公式事実 | SG | 同上 | 「また、日本人学校（チャンギ校）では、シンガポールで学ぶ日本の子どもたちとも交流し、このような子どもたちの両国への思いを肌で感じるとともに、今後、日本とシンガポールの架け橋となっていってくれることを頼もしく感じました。」 |
| K8 | 人柄と学び | 公式事実 | SG | 同上 | 「今回の訪問は、私にとって2度目の外国公式訪問となりましたが、ターマン大統領を始め、シンガポールの皆様の温かいお人柄と細やかなお心遣いにより、シンガポールの歴史や豊かな文化、緑あふれる自然など、この国ならではの魅力に触れ、多くのことを学ぶ貴重な機会となりました。」 |
| K9 | 結びの文 | 公式事実 | SG | 同上 | 「この度の訪問を契機として、日本とシンガポールの国民が世代を超えて交流を重ね、友好と信頼の絆が一層深まっていくことを心から願っております。」 |
| K10 | (参考)午餐会のおことばでの、学び合いと若い世代の交流 | 公式事実 | SG(11月18日 おことば) | 同上 | 「今後とも、日本とシンガポール両国の国民が、世代を超えて先人たちからの努力と知恵のバトンを繋ぎ、お互いの歴史や文化を学び合いながら、友好と信頼の絆を一層深めていくとともに、両国が、平和な世界を共に築いていく良きパートナーであり続けることを心から願っております。」「この度の私の訪問が、これまでの友好の歩みを若い世代が受け継ぎ、交流を更に広げていく一助となれば、うれしく思います。」 |

---

## 3. 背景: 英語の学び・国際交流について(公式の言葉を優先)

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| B1 | 陛下の言葉: 大学で英語のほかスペイン語を履修。高校生の時にイートン校へ夏の短期留学(語学の勉強も) | 公式事実 | EMP24(天皇陛下 お誕生日の記者会見 令和6年2月21日・関連質問2のお答え) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/emperor2024.html | 「大学では、本人も興味があって、英語以外に第二外国語、スペイン語を履修しましたけれども、これはまたこれで非常に良かったのではないかなと思いますし、それから高校生の時に、イートン校に短期留学でしたけれども夏の間お友達と一緒に留学をして、その際はもちろん語学の勉強もありましたけれども、オックスフォードを含めて、イギリスの中を何か所か回って、イギリスに対する理解も深めることができたと思いますし、もうちょっと遡りますと小さい時にオランダに連れて行ったということもありますので、そういうことを通して、海外に対する関心とか理解というものが深められていったのではないかと思います。」 |
| B2 | 陛下の言葉: 外国からのお客様との同席を通じて外国への理解を深めてほしい | 公式事実 | EMP24(同じお答えの前の段落) | 同上 | 「愛子は私たちの元で育てましたけれども、海外からのお客様、特に王族の方々などがお見えになった時には、愛子もできるだけ、都合のつく限りは同席してもらって、そしてその外国の王族の方々などとも、王族に限りませんけれども、色々な方と交流を深めて、そして外国に対する、日本の国以外に対する、外国についても色々理解と知識を深めていってもらいたいというようなことで、今までも育ててきたように思います。」 |
| B3 | 陛下の言葉(英国ご訪問前の会見): イートン校の短期留学を懐かしく思っている | 公式事実 | GBR24(令和6年6月19日・問1のお答え) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/gbr2024.html | 「また、愛子も、高校生の時にイートン校に短期留学した時のことを懐かしく思っており、その時の滞在中の思い出などについて家族で話をすることもあります。」 |
| B4 | 陛下の言葉: 海外の方々と接する機会を通じて国際親善に努めてほしい | 公式事実 | GBR24(問3のお答え) | 同上 | 「2月には、ケニアの大統領御夫妻をお迎えしての宮中午餐に出席しました。今後は、公的にも私的にも、海外の方々と接する機会が増えてくると思います。そのような機会を通じて視野を広げるとともに、国際親善に努めていくことができるよう願っております。」 |
| B5 | ご本人の言葉: 初めての宮中午餐で外国の賓客と話したこと | 公式事実 | JOB(文書回答・問2) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/employment.html | 「2月には、初めて宮中午餐に出席させていただきました。外国の賓客の方とお食事の席を御一緒することには、始まる前は緊張もありましたが、お客様が気さくに話し掛けてくださり、和やかな雰囲気の中で、お互いの国の気候や食文化などについてお話しできたことが心に残りました。」「そして、このような場は、相手の方の国の風土や文化について理解を深めることができる貴重な機会であるとともに、日本の魅力を外国に発信できる、両国にとって意義深い時間であると身をもって感じました。」(※何語で話したかは書かれていない) |
| B6 | 陛下の言葉(令和8年): ラオスに向けて準備し、帰国後に話してくれた | 公式事実 | EMP26(令和8年2月19日) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/emperor2026.html | 「愛子も、ラオスの歴史や文化に関心を持って準備をし、心を込めて務めを果たしてくれたことをうれしく思っています。帰国後には、ラオスでの様々な経験や出会った方々のことなどを私たちに話してくれました。」 |
| B7 | 成年会見(令和4年)には、語学・英語についてのご本人の言葉はない。問4で「海外留学」を聞かれ、進路は未定と答えられた | 公式事実 | SK(問4) | https://www.kunaicho.go.jp/watch/activity/activity01/activity01-r040317.html | 質問「海外留学や大学院進学など今後の進路について，夢や目標をお聞かせください。」/お答え「最後に，私の今後の進路につきましては，現時点ではまだ考えがまとまっておらず，これからの大学生活を通して，知識を広げながら自分の興味を深めていく中で，決めていくことができればと思います。」(成年会見の読点は全角カンマ「，」) |
| B8 | 卒業の文書回答でも海外留学を聞かれ、具体的には考えていないと答えられた | 公式事実 | GRAD(文書回答) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/graduation.html | 質問「将来的な海外留学や、大学院進学の希望はお持ちでしょうか。」/お答え「将来の勉学については、現在のところ具体的には考えておりませんが、来月より日本赤十字社の嘱託職員として勤務させていただくことになりましたので、皇族としての務めを果たしながら、社会人としての自覚と責任を持って、少しでも社会のお役に立てるよう、公務と仕事の両立に努めていきたいと思っております。」 |
| B9 | ラオスでは現地の言葉であいさつ(英語ではない)。宮内庁はラオ語の文字と和訳を添えている | 公式事実 | LAOK(令和7年11月18日 晩餐会) | https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/lao2025.html | 「サバイディー（ສະບາຍດີ）（こんばんは）。」「（どうもありがとうございました。乾杯いたしましょう）。」 |
| B10 | **イートン校の短期留学は「2016年」ではなく 2018年(平成30年)夏**(報道)。宮内庁(B1・B3)は「高校生の時」「夏の間」とだけ書き、年は書いていない | 報道 | 日本経済新聞(2018-07-22) | https://news.google.com/rss/articles/CBMibEFVX3lxTE96aFBxX0lSX1o0ejhSazc1VmthdGZKM2xodHh4WlQ4V1dKWmxFTTJpdHRHYVh6MThyekI4WXBwaXZuc3VDc2VVY0FxQ05VYmhtaW9JaERhd1JSdVVOTGFlQ0lEcFcyMkl3TGYxVg?oc=5 | 見出し「愛子さま短期留学で英国へ 8月9日帰国」 |
| B10b | 同上 | 報道 | テレ朝NEWS(2018-07-07) | https://news.google.com/rss/articles/CBMickFVX3lxTFBNc2FyQkZhWHVXNTdTZEZTdGhRN3U3bURYSHd0dXdLNjAxNmdTTVB0YllfbVFhb25XV0FOZ24xMFhDS3A5UHctRFRNT2h1MFN0NnBBSE1ZY1hpaml3WWZ6eEo2dktjSzhUbDMtTFIySjVVZw?oc=5 | 見出し「愛子さまが英イートン校留学へ 初のお一人で海外」 |
| B10c | (参考)ウィキペディアの記述。時事通信 2018-07-22 を出典にしている。ウィキペディアは同じ記事のラオスの月(「7月」)やシンガポールのリンク先(ペルー)を誤っているので、**出典にしない** | 参考(未確認扱い) | ja.wikipedia「愛子内親王」 | https://ja.wikipedia.org/wiki/%E6%84%9B%E5%AD%90%E5%86%85%E8%A6%AA%E7%8E%8B | 「[[2018年]]（平成30年）7月22日～8月9日、[[イギリス]]に短期[[留学]]（学習院女子高等科の海外研修プログラム）。」 |
| B11 | 大学で英語とスペイン語を選択(2020年の報道)。B1 の陛下の言葉と合う | 報道 | 朝日新聞(2020-05-25) | https://news.google.com/rss/articles/CBMiZkFVX3lxTE5GVVRncHJLME16X0RGNWFJNTBsc0VTOVJaTU1sQXlzclBTa1l3MnMyZG5yZk5ZMG9jYVlGLXpiN1l5eXptSUcteV94TkdRcE1WQ05VMXdfR05kaEVSVWhSaVZJcVN0dw?oc=5 | 見出し「愛子さま、英語とスペイン語を選択 皇室25日～31日」 |
| B12 | ケニア大統領夫妻との宮中午餐(2024年2月)で英語で歓談 | 報道 | TBS NEWS DIG(2024-02-09) | https://news.google.com/rss/articles/CBMiVkFVX3lxTFBNbXRrOGQ3RjhxRTAwV2Q5Unl3U3pRNlFaMWlucmhqY2Q0dHJJRC1FUWhMQWdvX0JXUDFOVGFRaU1CSDloSHFCZW4tV09zcmZPempKd1RR?oc=5 | 見出し「愛子さま“宮殿の昼食会”でケニア閣僚と英語で歓談 外国賓客を招いた宮殿での午餐出席は初めて」 |
| B13 | 鴨場接待(2025年2月)で各国大使に英語であいさつ | 報道 | FNNプライムオンライン(2025-02-14) | https://news.google.com/rss/articles/CBMiTEFVX3lxTFBPcDU3U0xBQ0gwM25CLXVrbnEwWnFsdEd4SFJ5bnQtX1RFZG8tUWZTNWtHYlNXejJPM1I1d1VGdVNwU01pWGtIRFp6RTY?oc=5 | 見出し「愛子さま「I hope you will enjoy」鴨場接待デビューで各国大使と英語であいさつ 佳子さまに手順確認し放鳥にチャレンジ 陛下プロポーズの地で」 |
| B14 | ご帰国後、天皇皇后両陛下が(側近を通じて)感想を述べられた | 報道 | テレビ朝日系(ANN)(2026-11-27) | https://news.google.com/rss/articles/CBMif0FVX3lxTE84eURCWjRKakI3YVg1N0tyN3FCbFRKUmpMMkx2VENVOXZvNjk5MDRROHdTaDI1YnhQdl9UV0RPZWZUc1Blb1A4ZXNVNGFzVHRhdE1pU2RYNUNpM2lSaTlESkZiakJybmhGcXBLOTlmc3cxN2FTRHI5amR4ZU1MVWs?oc=5 | 見出し「愛子さまのシンガポール訪問 天皇皇后両陛下が感想（テレビ朝日系（ANN））」。**感想の中身は未確認**(宮内庁のサイトには 11/28 時点で載っていない。英語に触れたかも不明) |

---

## 4. 宮内庁のシンガポールご訪問の写真

| # | 事実 | 区分 | 出典名 | URL | 原文の引用(verbatim) |
|---|---|---|---|---|---|
| P1 | **宮内庁にシンガポールご訪問の写真は、11/28 時点で1枚も載っていない** | 公式事実(掲載がないことの確認) | SGI・SG・宮内庁トップの新着 | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/index.html | SGI・SG のページにある画像は共有ボタンのアイコン(`icon_facebook.svg` `icon_line.svg`)だけ。ご日程の行に写真ページへのリンクがない |
| P2 | ラオス(令和7年)は `2025lao/595.html`〜`615.html` に1行ずつ写真ページがある。同じ形で `2026sgp/616.html`〜`900.html` を試したが、**すべて 404**(ページなし) | 分析 | 宮内庁 | https://www.kunaicho.go.jp/watch/activity/schedule01/2026sgp/ | (比較: `2025lao/611.html` は 200 で表示される) |
| P3 | 宮内庁トップの新着で、シンガポール関係は 11月21日のご感想だけ(11/28 時点) | 公式事実 | 宮内庁トップ | https://www.kunaicho.go.jp/ | 「令和8年11月21日」「愛子内親王殿下のシンガポールご訪問を終えてのご感想」 |
| P4 | 同じ新着に、11月20日付で一部コンテンツを一時停止したお知らせがある(写真の掲載が遅れている理由かどうかは**未確認**) | 公式事実(お知らせの存在) | 宮内庁トップ | https://www.kunaicho.go.jp/info/systemmainte-r081120-1.html | 「PHPの脆弱性対応に伴う一部コンテンツの一時停止について」(11月20日)、「PHPの脆弱性対応に伴い一時停止していた一部コンテンツの復旧について」(11月20日) |
| P5 | 既存の台帳(KB-20261126-01・04・07 ほか)にも、宮内庁のシンガポールご訪問写真はない。シンガポール関係はすべて Wikimedia Commons の場所の写真(A150〜A156・A165・A166)と、宮内庁の令和7年12月1日の掲載「愛子内親王殿下のお誕生日に際してのご近影」(A157〜A160)。キャプション・ライセンスは各 ledger.csv のとおり | 分析(台帳の確認) | projects/KB-20261126-01/ledger.csv ほか | /home/user/-/projects/KB-20261126-04/ledger.csv | (台帳の文: A156「撮影日はご滞在期間(11月17日〜21日)の2日目に当たり、日本庭園ご訪問の日は宮内庁に未掲載のため…」→ 冒頭の「変わったこと 3」のとおり見直す) |
| P6 | 動画の愛子さまの写真: 今は「宮内庁の既存の写真に実際の撮影日を出す」(BATCH-SGP の決まり)のままにする。報道写真(共同の代表撮影など)は使わない | 分析 | research/batches/BATCH-SGP-20261126.yaml | — | 「宮内庁のシンガポールの写真は未掲載。」「報道写真・映像は使わない」 |

→ 写真が載ったら、ラオスと同じく1ページずつキャプション(写真の下の説明文)を取り、台帳に入れる。今日の時点で台帳に足せる宮内庁の写真はない。

---

## 5. 調べたこと・調べられなかったこと(未確認の理由)

- **宮内庁**: SG・SGI・N2611・トップと新着・EMP24・GBR24・EMP26・SK・GRAD・JOB・LAOK・「愛子内親王殿下の主な式典におけるおことば」(令和7年・8年)を取得して確認。式典のおことば(令和8年8月17日 半導体物理国際会議、9月25日 世界医学検査学会など)は日本語で載っていて、英語で述べられたかの記載はない。
- **外務省** (www.mofa.go.jp): シンガポールのページ・報道発表を試したが **403(Access Denied)**。外務省の資料は確認できていない。
- **NHK**: 日本語記事は news.web.nhk に移っていて、ネットワークの許可がない(403)。www3.nhk.or.jp の RSS・NHK WORLD の JSON は 2026年8〜9月で止まっていて、今回の記事は取れなかった。NHK WORLD の英語見出し(R5)は Google ニュース経由で確認。
- **YouTube**: 検索結果のページ(題名・チャンネル名・説明文の冒頭)は取れた。**動画ページは Google の確認画面に回されて取れなかった**(日テレの「【完全版】…＜和訳つき＞」KRViI91FrKY、「英語で懇談も」RG3g4M4tMoo、NHK WORLD RcyQZWAjFZ4 など)。英語の原文と和訳は、これらの動画の映像・字幕で確かめるのがいちばん早い(人が見て書き起こす)。
- **文春** (bunshun.jp): サイト内検索のページがなく(404)、Google ニュースでも今回の英語の記事は見つからなかった。
- **Google ニュース RSS**: 見出し・配信元・日付だけが取れる。記事の本文(Yahoo!・ABEMA・日テレ・TBS・FNN・テレ朝・共同など)は接続先が許可されていないので取っていない(許可外の接続は試していない)。
- 検索した語: 「愛子さま シンガポール 英語」「愛子さま シンガポール 英語で」「愛子さま 英語 スピーチ」「愛子さま ガン首相代行 英語」「愛子さま 植樹 記者 質問 英語」「愛子さま イートン」「Princess Aiko Singapore」「Princess Aiko English Tharman」「Princess Aiko Gan Kim Yong」「Princess Aiko fruitful」ほか。

### まだ確かめられていないこと(動画・台本で断定しない)

1. 大統領(表敬)・リー上級大臣・ガン首相代行と話された**英語の原文**と、主要報道の和訳の全文(T6・L3・G3)
2. 「55秒」「約1分」の長さ(報道の見出しの数字。自分たちで測っていない)
3. カメラのない場所で英語で質問された場所・相手・中身(M2)
4. 植樹式のあとの受け答えの言語、英語で話しかけたのはだれか(R6)
5. 午餐会のおことばの本文を何語で述べられたか(E6)
6. 天皇皇后両陛下の感想(11/27 報道)の中身(B14)
7. 外務省の記録(取得できず)
8. 宮内庁のシンガポールご訪問の写真(未掲載)
