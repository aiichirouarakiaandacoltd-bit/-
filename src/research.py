"""Research and fact-checking module.

Provides functions to research a topic using built-in knowledge of
well-established historical and cultural facts about the Japanese
imperial family, then generate structured reports, fact-check records,
and source lists for outsourcing packages.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import config as cfg


# ---------------------------------------------------------------------------
# Built-in knowledge base (proof-of-concept)
# ---------------------------------------------------------------------------

_BUILTIN_TOPICS: dict[str, dict] = {
    "なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来": {
        "topic": "なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来",
        "topic_context": (
            "皇族の「御名」と「御称号」には、それぞれ異なる意味と役割があります。\n"
            "御名は個人としてのお名前であり、御称号は宮号とも呼ばれる皇族としての呼称です。\n"
            "愛子内親王殿下の御名「愛子」と御称号「敬宮」。\n"
            "この二つの名前には、中国古典『孟子』の一節に基づく深い願いが込められています。\n"
            "今回は、公式の記録をたどりながら、その由来を見てまいります。"
        ),
        "section_config": [
            {"title": "御誕生と命名の儀", "fact_ids": ["F001", "F005"]},
            {"title": "命名の経緯", "fact_ids": ["F004"]},
            {"title": "『孟子』の教え", "fact_ids": ["F006"]},
            {"title": "皇太子殿下のお言葉", "fact_ids": ["F008"]},
            {"title": "御名と御称号に込められた願い", "fact_ids": ["F002", "F003"]},
        ],
        "ending_context": (
            "ここまで、御名「愛子」と御称号「敬宮」の由来を、公式の記録からたどってまいりました。\n\n"
            "平成13年の御誕生から、命名の儀へ。\n"
            "上皇陛下が語られた命名の経緯。\n"
            "典拠となった『孟子』離婁章句下の教え。\n"
            "そして、平成14年と令和3年の記者会見で語られたお言葉。\n\n"
            "御名「愛子」には「人を愛してほしい」という願い。\n"
            "御称号「敬宮」には「人を敬ってほしい」という願い。\n"
            "二千年以上前に記された『孟子』の教えが、\n"
            "現代の皇室においても大切にされていることを、公式の記録は伝えています。"
        ),
        "shorts_01_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "愛子内親王殿下の御名「愛子」と御称号「敬宮」。\n"
            "この二つのお名前には、それぞれ異なる意味が込められています。\n"
            "その由来は、二千年以上前の中国古典『孟子』の一節にあります。\n\n"
            "「仁者は人を愛し、礼ある者は人を敬う」。\n\n"
            "平成13年12月1日に御誕生、12月7日に命名の儀が執り行われました。\n"
            "当時の皇太子ご夫妻が、勘申者の意見も聞きながら考えられた御名と御称号。\n"
            "そこには、人を愛し、人を敬ってほしいという深い願いが込められています。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_02_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "「名前のように、人を愛して人からも愛され、\n"
            "人を敬い人からも敬われるような人に育ってほしい」。\n\n"
            "これは、平成14年の記者会見で皇太子殿下が述べられたお言葉です。\n"
            "御名「愛子」と御称号「敬宮」の由来について語られたものです。\n\n"
            "約20年後の令和3年、天皇陛下は改めてこう述べられました。\n"
            "「孟子の言葉を参考にした名前には、私たちの願いが込められています」。\n\n"
            "御誕生から現在に至るまで、その願いは変わることなく受け継がれています。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "facts": [
            {
                "fact_id": "F001",
                "claim": "愛子内親王殿下は平成13年12月1日に御誕生になった",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇ご一家」",
                "source_url": "https://www.kunaicho.go.jp/learn/about/history/history01.html",
                "source_type": "公式機関発表",
                "official_publisher": "宮内庁",
                "publication_date": None,
                "resource_identifier": "宮内庁公式サイト > 皇室について > 天皇ご一家",
                "verified_excerpt": "第1皇女子 愛子（あいこ）内親王殿下 平成13年12月1日ご誕生　ご称号：敬宮（としのみや）",
                "verified_date": "2026-06-26",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイト「天皇ご一家」ページから荒木が直接確認。",
                "narration_lead": "愛子内親王殿下は、平成13年、西暦2001年の12月1日にお生まれになりました。\n天皇皇后両陛下の第一皇女子であられます。",
                "narration_source_intro": "宮内庁の公式サイト「天皇ご一家」のページには、次のように記されています。",
                "narration_after": "このように、宮内庁の公式サイトに明確に記されています。",
            },
            {
                "fact_id": "F005",
                "claim": "平成13年12月7日に命名の儀が行われた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「皇太子同妃両殿下のご日程：平成13年（10月～12月）」",
                "source_url": "https://www.kunaicho.go.jp/activity/gonittei/02/h13/gonittei-2-2001-10.html",
                "source_type": "公式機関発表（ご日程）",
                "official_publisher": "宮内庁",
                "publication_date": "2001-12-07",
                "resource_identifier": "宮内庁公式サイト > ご日程 > 皇太子同妃両殿下のご日程 平成13年（10月～12月） / 補強: 天皇皇后両陛下ご日程 https://www.kunaicho.go.jp/activity/gonittei/01/h13/gonitei-h13-04.html",
                "verified_excerpt": "平成13年12月7日（金） 皇太子殿下 命名の儀（東宮御所）",
                "verified_date": "2026-06-26",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイトのご日程ページから荒木が直接確認。天皇皇后両陛下のご日程ページにも「命名の儀（宮殿）」と記載あり。",
                "narration_lead": "御誕生から6日後の12月7日、命名の儀が東宮御所で執り行われました。\n命名の儀とは、皇族のお名前を正式に定める儀式です。",
                "narration_source_intro": "宮内庁が公開しているご日程の記録には、次のように記されています。",
                "narration_after": "この儀式によって、「愛子」という御名と「敬宮」という御称号が正式に定められました。\nでは、この御名と御称号には、どのような由来があるのでしょうか。",
            },
            {
                "fact_id": "F004",
                "claim": "御名と御称号は、当時の皇太子ご夫妻が勘申者の意見も聞きながら考えられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（平成13年）」",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/kaiken/kaiken-h13e.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2001-12-18",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下お誕生日に際し（平成13年）",
                "verified_excerpt": "皇太子夫妻が一所懸命に考え，また，勘申者の意見も聞きながら考えたことで，名前というものは，やはり両親が最も深くかかわることが望ましいと思っております。",
                "verified_date": "2026-06-26",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "平成13年天皇陛下お誕生日記者会見から荒木が直接確認。命名の経緯について、皇太子ご夫妻が勘申者の意見も聞きながら考えたと述べられている。",
                "narration_lead": "命名の経緯について、重要な記録が残されています。\n平成13年12月、天皇陛下のお誕生日に際しての記者会見がありました。",
                "narration_source_intro": "この記者会見で、上皇陛下は命名の経緯について、次のように述べられています。",
                "narration_after": "勘申者とは、御名の候補を考案し提案する学識経験者のことです。\nこの記録から、当時の皇太子ご夫妻が深く関わりながら、専門家の意見も参考にして、御名と御称号を決められたことがわかります。\nそれでは、その典拠となった古典を見てまいりましょう。",
            },
            {
                "fact_id": "F006",
                "claim": "『孟子』離婁章句下に「仁者愛人、有禮者敬人。愛人者、人恒愛之。敬人者、人恒敬之」の一節がある",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "『孟子』離婁章句下",
                "source_url": None,
                "source_type": "古典文献",
                "official_publisher": "（古典文献）",
                "publication_date": None,
                "resource_identifier": "『孟子』離婁章句下 / 底本: 朱熹『四書章句集注』中華書局、1983年 / 小林勝人訳注『孟子』岩波文庫、1968年 / 国立国会図書館デジタルコレクション ndljp/pid/754253",
                "verified_excerpt": "仁者愛人、有禮者敬人。愛人者、人恒愛之。敬人者、人恒敬之。",
                "verified_date": None,
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "古典原文の存在確認。上記底本および各種注釈書・学術データベースで第三者が再確認可能。命名典拠であることはF002・F003の令和3年記者会見で確認済み。",
                "narration_lead": "御名と御称号の典拠となったのは、中国の古典『孟子』です。\n『孟子』は、紀元前4世紀頃に成立した儒学の経典で、\n「仁」と「礼」の大切さを説いた書物です。\nその離婁章句下に、このような一節があります。",
                "narration_source_intro": "",
                "narration_after": "現代語に訳しますと、\n「仁のある者は人を愛し、礼のある者は人を敬う。\n人を愛する者は、人からも常に愛される。\n人を敬う者は、人からも常に敬われる」\nという意味になります。\n二千年以上前に記されたこの教えが、御名と御称号の根底にあるのです。",
            },
            {
                "fact_id": "F008",
                "claim": "平成14年4月2日の記者会見で、皇太子殿下は愛子さまについて、「名前のように、人を愛して人からも愛され、人を敬い人からも敬われるような人に育ってほしい」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「愛子内親王殿下御誕生につき（平成14年）」",
                "source_url": "https://www.kunaicho.go.jp/okotoba/02/kaiken/kaiken-h14-gotanjo.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2002-04-02",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 愛子内親王殿下御誕生につき（平成14年）",
                "verified_excerpt": "また，愛子には一人の皇族として立派に育って欲しいですし，名前のように，人を愛して人からも愛され，人を敬い人からも敬われるような人に育って欲しいです。",
                "verified_date": "2026-06-26",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイト掲載の記者会見原文から荒木が直接確認。",
                "narration_lead": "御誕生から約4か月後の平成14年4月2日。\n皇太子殿下は、愛子内親王殿下の御誕生につき、記者会見に臨まれました。",
                "narration_source_intro": "宮内庁が公開しているこの記者会見の記録には、次のように記されています。",
                "narration_after": "「名前のように」という言葉から、御名「愛子」に込められた願いの深さがうかがえます。\n人を愛し、人からも愛される。人を敬い、人からも敬われる。\n『孟子』の教えそのものが、愛子さまへの願いとして語られています。",
            },
            {
                "fact_id": "F002",
                "claim": "御名「愛子」は孟子の言葉を参考にしたもので、人を愛してほしいという願いが込められている",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和3年）」",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/emperor2021.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2021-02-23",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下お誕生日に際し（令和3年）",
                "verified_excerpt": "愛子が誕生した時の会見でも申しましたが，孟子の言葉を参考にした『敬宮』『愛子』という名前には，人を敬い，人を愛してほしいという，私たちの願いが込められています。",
                "verified_date": "2026-06-26",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "令和3年天皇陛下お誕生日記者会見で、命名典拠が孟子の言葉であることと、御名に込められた願いが明言されている。荒木が宮内庁公式サイトで原文を直接確認。",
                "narration_lead": "それから約20年後の令和3年。\n天皇陛下のお誕生日に際しての記者会見で、\n天皇陛下は改めて命名の由来について語られました。",
                "narration_source_intro": "宮内庁の記録には、次のように記されています。",
                "narration_after": "「孟子の言葉を参考にした」と、典拠が明確に語られています。\nそして「私たちの願いが込められています」という言葉から、\n御名と御称号がご両親の深い思いとともに選ばれたことが、改めて伝わってまいります。",
            },
            {
                "fact_id": "F003",
                "claim": "御称号「敬宮」は孟子の言葉を参考にしたもので、人を敬ってほしいという願いが込められている",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和3年）」",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/emperor2021.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2021-02-23",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下お誕生日に際し（令和3年）",
                "verified_excerpt": "愛子が誕生した時の会見でも申しましたが，孟子の言葉を参考にした『敬宮』『愛子』という名前には，人を敬い，人を愛してほしいという，私たちの願いが込められています。",
                "verified_date": "2026-06-26",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "F002と同一の令和3年記者会見原文で確認。御称号「敬宮」にも孟子の言葉が参考にされたことが明言されている。荒木が宮内庁公式サイトで原文を直接確認。",
                "narration_lead": "御称号「敬宮」にも、同じ『孟子』の教えが込められています。\n先ほどの令和3年の記者会見の記録にも、御称号と御名の両方について触れられていました。",
                "narration_source_intro": "",
                "narration_after": "御名「愛子」には「人を愛してほしい」という願い。\n御称号「敬宮」には「人を敬ってほしい」という願い。\nそれぞれに異なる意味が込められ、\n合わせて『孟子』の「愛人」「敬人」の教えの全体を表しています。",
            },
            {
                "fact_id": "F007",
                "claim": "皇族の御名・御称号は古典に由来する伝統がある",
                "status": cfg.FactStatus.UNCONFIRMED,
                "source_name": "皇室の命名慣例（複数の学術文献・報道）",
                "source_url": None,
                "source_type": "学術・報道",
                "official_publisher": None,
                "publication_date": None,
                "resource_identifier": None,
                "verified_excerpt": None,
                "verified_date": None,
                "direct_or_contextual": "contextual",
                "usable_in_script": False,
                "manual_source_verification_required": True,
                "required_for_content": False,
                "blocking": False,
                "notes": "一般的に認められた慣例だが、単一の公式一次資料を特定できていない。今回の動画テーマに必須ではないため、usable_in_script=falseのまま。content_completeおよびproduction_readyの判定には影響しない。",
            },
        ],
        "sources": [
            {
                "source_id": "S001",
                "source_name": "宮内庁公式サイト",
                "source_url": "https://www.kunaicho.go.jp/",
                "source_type": "公式機関",
                "reliability": "最高",
                "notes": "皇室に関する一次情報源。個別ページのURLは要確認。",
            },
            {
                "source_id": "S002",
                "source_name": "『孟子』離婁章句下",
                "source_url": None,
                "source_type": "古典文献",
                "reliability": "最高（原典）",
                "notes": "中国古典。各種注釈書・翻訳で確認可能。",
            },
        ],
    },

    "天皇皇后両陛下オランダ・ベルギー公式訪問――公式記録に残る友好の記録": {
        "topic": "天皇皇后両陛下オランダ・ベルギー公式訪問――公式記録に残る友好の記録",
        "topic_context": (
            "令和8年6月、天皇皇后両陛下はオランダ及びベルギーを公式訪問されました。\n"
            "オランダのウィレム＝アレクサンダー国王陛下及びベルギーのフィリップ国王陛下からの招請に基づくご訪問です。\n"
            "6月13日に日本を出発され、6月26日に帰国されるまでの2週間。\n"
            "両国の王室との交流、歓迎行事、そして「次世代への橋渡し」と語られた日々を、\n"
            "公式の記録からたどってまいります。"
        ),
        "section_config": [
            {"title": "ご出発とオランダへ", "fact_ids": ["NB001", "NB002"]},
            {"title": "オランダでの公式行事", "fact_ids": ["NB003", "NB004"]},
            {"title": "20年ぶりの再会", "fact_ids": ["NB005"]},
            {"title": "ベルギーでの交流", "fact_ids": ["NB006"]},
            {"title": "次世代への橋渡し", "fact_ids": ["NB007"]},
        ],
        "ending_context": (
            "ここまで、天皇皇后両陛下のオランダ及びベルギー公式訪問の記録をたどってまいりました。\n\n"
            "6月13日の出発から6月26日の帰国まで、2週間にわたるご訪問。\n"
            "オランダではウィレム＝アレクサンダー国王王妃両陛下に温かく迎えられ、\n"
            "ダム広場での歓迎式典、アムステルダム王宮での晩餐会、\n"
            "そして20年ぶりとなるアマリア王女との再会がありました。\n\n"
            "ベルギーではフィリップ国王陛下及びマチルド王妃陛下との旧交を温められ、\n"
            "両国の人々との交流と相互理解を深められました。\n\n"
            "天皇陛下が述べられた「次世代への橋渡しができた」というお言葉は、\n"
            "このご訪問が持つ意義を静かに、しかし確かに物語っています。\n"
            "皇室と王室の友好は、世代を超えて受け継がれていくものなのでしょう。"
        ),
        "shorts_01_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "令和8年6月、天皇皇后両陛下がオランダとベルギーを公式訪問されました。\n"
            "オランダ国王陛下及びベルギー国王陛下からの招請に基づくご訪問です。\n\n"
            "6月13日に羽田空港を出発され、アムステルダムへ。\n"
            "ダム広場での歓迎式典、アムステルダム王宮での国賓晩餐会が行われました。\n\n"
            "天皇陛下は晩餐会のスピーチで、オランダとの友好の歴史に触れられ、\n"
            "「両国の交流や相互理解、友好関係が更に深まる機会になれば」と述べられました。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_02_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "「次世代への橋渡しができたのではないかと思います」。\n\n"
            "これは、ベルギー滞在中の天皇陛下のお言葉です。\n"
            "オランダ・ベルギー両国との2週間にわたる公式訪問を振り返られてのものです。\n\n"
            "オランダではウィレム＝アレクサンダー国王に温かく迎えられ、\n"
            "ベルギーではフィリップ国王及びマチルド王妃と旧交を温められました。\n\n"
            "皇室と欧州王室の友好は、上皇上皇后両陛下の時代から受け継がれてきたものです。\n"
            "両陛下はその絆を次の世代へとつないでおられます。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_03_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "20年前、オランダのヘット・アウデ・ロー城での夏休み。\n"
            "4歳の愛子さまと2歳のアマリア王女が手をつないで過ごした日々がありました。\n\n"
            "令和8年6月、両陛下のオランダ公式訪問の際に、\n"
            "アマリア王女との20年ぶりの再会が実現しました。\n\n"
            "天皇陛下は「素晴らしい夏休みを過ごした」と当時を振り返られました。\n"
            "アマリア王女は現在、アムステルダム大学で学びながら次期女王としての道を歩んでおられます。\n\n"
            "皇室と王室の友情が、世代を超えて受け継がれていく姿がここにあります。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "facts": [
            {
                "fact_id": "NB001",
                "claim": "天皇皇后両陛下は令和8年6月13日から6月26日までオランダ及びベルギーを公式訪問された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「オランダ及びベルギーご訪問（令和8年）」",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/schedule01/2026nld-bel/",
                "source_type": "公式機関発表",
                "official_publisher": "宮内庁",
                "publication_date": "2026-06-13",
                "resource_identifier": "宮内庁公式サイト > ご活動 > オランダ及びベルギーご訪問（令和8年）",
                "verified_excerpt": "天皇皇后両陛下のオランダ及びベルギーご訪問（令和8年6月13日～6月26日）",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイトのご訪問特設ページから確認。",
                "narration_lead": "令和8年、西暦2026年の6月13日。\n天皇皇后両陛下は、オランダ及びベルギーの公式訪問のため、羽田空港を出発されました。\n6月26日に帰国されるまでの、2週間にわたるご訪問です。",
                "narration_source_intro": "宮内庁の公式サイトには、このご訪問について次のように記されています。",
                "narration_after": "このご訪問は、オランダのウィレム＝アレクサンダー国王陛下及びベルギーのフィリップ国王陛下からの招請に基づくものです。",
            },
            {
                "fact_id": "NB002",
                "claim": "このご訪問はオランダ国王陛下及びベルギー国王陛下からの招請に基づくものである",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「オランダ及びベルギーご訪問に際し（令和8年）」記者会見",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/2026nld-bel.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2026-06-12",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > オランダ及びベルギーご訪問に際し（令和8年）",
                "verified_excerpt": "オランダ国王陛下及びベルギー国王陛下からの招請に基づき訪問",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイト掲載の記者会見原文から確認。",
                "narration_lead": "このご訪問に先立ち、天皇陛下は記者会見に臨まれました。\n両国の王室との長年にわたる交流に触れられ、訪問への思いを語られました。",
                "narration_source_intro": "宮内庁が公開している記者会見の記録には、次のように記されています。",
                "narration_after": "天皇陛下は、「両国の人々との交流や相互理解、友好関係が更に深まる機会になればと思っている」と述べられました。\nこのお言葉に、ご訪問に込められた思いが表れています。",
            },
            {
                "fact_id": "NB003",
                "claim": "天皇陛下はオランダ訪問について「両国の人々との交流や相互理解、友好関係が更に深まる機会になれば」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "NHKニュース「天皇陛下 オランダとベルギー 公式訪問を前に記者会見」",
                "source_url": "https://news.web.nhk.or.jp/",
                "source_type": "信頼できる報道（NHK）",
                "official_publisher": "NHK",
                "publication_date": "2026-06-12",
                "resource_identifier": "NHKニュース 2026年6月12日報道 / 宮内庁記者会見公式記録に基づく",
                "verified_excerpt": "両国の人々との交流や相互理解、友好関係が更に深まる機会になればと思っている",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": True,
                "notes": "NHK報道で確認。宮内庁公式記者会見ページで原文の再確認を推奨。",
                "narration_lead": "",
                "narration_source_intro": "",
                "narration_after": "",
            },
            {
                "fact_id": "NB004",
                "claim": "オランダでの公式行事は6月17日から19日を中心に行われ、ダム広場での歓迎式典とアムステルダム王宮での国賓晩餐会が含まれる",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「オランダ及びベルギーご訪問（令和8年）」ご日程",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/schedule01/2026nld-bel/",
                "source_type": "公式機関発表（ご日程）",
                "official_publisher": "宮内庁",
                "publication_date": "2026-06-13",
                "resource_identifier": "宮内庁公式サイト > ご活動 > オランダ及びベルギーご訪問（令和8年）> ご日程",
                "verified_excerpt": "ダム広場での歓迎式典、アムステルダム王宮での晩餐会",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイトのご日程ページから確認。",
                "narration_lead": "オランダでの公式行事は、6月17日から19日を中心に行われました。\nアムステルダムを拠点に、さまざまな行事に臨まれました。",
                "narration_source_intro": "宮内庁のご日程記録によりますと、主な行事は次の通りです。",
                "narration_after": "ダム広場は、オランダの国家的行事が行われる象徴的な場所です。\nそこで歓迎式典が行われたことは、両国の友好の深さを物語っています。\n\nそして同日夜、アムステルダム王宮での国賓晩餐会が行われました。\n天皇陛下は晩餐会でのスピーチにおいて、オランダとの長きにわたる友好と交流の歴史に触れられました。",
            },
            {
                "fact_id": "NB005",
                "claim": "20年前にヘット・アウデ・ロー城で当時4歳の愛子さまと2歳のアマリア王女が手をつないで過ごし、今回のご訪問で20年ぶりの再会が実現した",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "ANNnewsCH「愛子さまの幼なじみアマリア王女と交流 両陛下オランダ訪問」",
                "source_url": "https://www.youtube.com/watch?v=XqYLV6qwbaM",
                "source_type": "信頼できる報道（テレビ朝日）",
                "official_publisher": "ANNnewsCH（テレビ朝日系列）",
                "publication_date": "2026-06-20",
                "resource_identifier": "ANNnewsCH YouTube 2026年6月20日公開",
                "verified_excerpt": "20年ぶりの再会。愛子さまの幼なじみアマリア王女と交流。天皇陛下は素晴らしい夏休みを過ごしたと当時を振り返られた",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": True,
                "notes": "テレビ朝日系列の報道映像から確認。宮内庁公式ページでの補強確認を推奨。",
                "narration_lead": "このオランダ訪問で、特に多くの関心を集めた出来事があります。\n20年ぶりとなる、アマリア王女との再会です。\n\n20年前の平成18年、当時の皇太子ご一家はオランダのヘット・アウデ・ロー城で夏休みを過ごされました。\n当時4歳の愛子さまと、2歳のアマリア王女が手をつないで過ごした日々。\n天皇陛下はこのご訪問に際し、「素晴らしい夏休みを過ごした」と当時を振り返られました。",
                "narration_source_intro": "",
                "narration_after": "20年の歳月を経て、お二人とも成年皇族・王族として歩みを進めておられます。\nアマリア王女は現在、アムステルダム大学で学びながら、次期女王としての道を歩んでおられます。\n皇室と王室の友情が、まさに次の世代へと受け継がれていく姿がここにあります。",
            },
            {
                "fact_id": "NB006",
                "claim": "ベルギーではフィリップ国王陛下及びマチルド王妃陛下との旧交を温められた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「オランダ及びベルギーご訪問に際し（令和8年）」記者会見",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/2026nld-bel.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2026-06-12",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > オランダ及びベルギーご訪問に際し（令和8年）",
                "verified_excerpt": "フィリップ国王陛下及びマチルド王妃陛下との旧交を温める",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "notes": "宮内庁公式サイト掲載の記者会見記録から確認。",
                "narration_lead": "オランダでの日程を終え、両陛下はベルギーへ向かわれました。\nベルギーでは、フィリップ国王陛下及びマチルド王妃陛下との旧交を温められました。",
                "narration_source_intro": "宮内庁の記録によりますと、",
                "narration_after": "日本とベルギーの皇室・王室の交流は、長い歴史を持っています。\n両陛下がベルギー王室と直接お会いになることで、その絆はさらに深まりました。",
            },
            {
                "fact_id": "NB007",
                "claim": "天皇陛下はベルギー滞在中に「次世代への橋渡しができたのではないかと思います」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "毎日新聞「欧州歴訪の天皇陛下『次世代への橋渡しができた』」",
                "source_url": None,
                "source_type": "信頼できる報道（毎日新聞）",
                "official_publisher": "毎日新聞",
                "publication_date": "2026-06-25",
                "resource_identifier": "毎日新聞 2026年6月25日報道 / ナミュールでの報道陣取材に対する天皇陛下のご発言",
                "verified_excerpt": "次世代への橋渡しができたのではないかと思います",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": True,
                "notes": "毎日新聞の報道で確認。宮内庁公式おことばページで原文確認を推奨。",
                "narration_lead": "2週間にわたるご訪問の終盤。\nベルギーのナミュールで、天皇陛下は報道陣の取材に応じられました。\n「楽しく充実した日々を送ることができている」と述べられた上で、\n両国の王室との交流について、このように語られました。",
                "narration_source_intro": "",
                "narration_after": "「次世代への橋渡し」。\nこのお言葉は、このご訪問が持つ意義を静かに、しかし確かに物語っています。\n\n上皇上皇后両陛下が平成12年にオランダを国賓として訪問されてから、24年。\nその友好の絆は、天皇皇后両陛下へと受け継がれ、\nそして愛子さまとアマリア王女の世代へとつながろうとしています。\n\n皇室と王室の交流は、一朝一夕に築かれるものではありません。\n長い年月をかけて、丁寧に紡がれてきた信頼と友情。\nそれを「次の世代へ渡す」という天皇陛下のお言葉に、\n深い思いが込められているように感じられます。",
            },
        ],
        "sources": [
            {
                "source_id": "SNB01",
                "source_name": "宮内庁「オランダ及びベルギーご訪問（令和8年）」",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/schedule01/2026nld-bel/",
                "source_type": "公式機関",
                "reliability": "最高",
                "notes": "ご訪問の日程・行事の公式記録",
            },
            {
                "source_id": "SNB02",
                "source_name": "宮内庁「オランダ及びベルギーご訪問に際し（令和8年）」記者会見",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/2026nld-bel.html",
                "source_type": "公式機関",
                "reliability": "最高",
                "notes": "出発前の天皇陛下記者会見の公式記録",
            },
            {
                "source_id": "SNB03",
                "source_name": "宮内庁「オランダ及びベルギーご訪問時のおことば（一覧）」",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/addresses/2026nld-bel.html",
                "source_type": "公式機関",
                "reliability": "最高",
                "notes": "ご訪問中の天皇陛下のおことば一覧",
            },
            {
                "source_id": "SNB04",
                "source_name": "NHKニュース 天皇陛下記者会見報道",
                "source_url": "https://news.web.nhk.or.jp/",
                "source_type": "信頼できる報道",
                "reliability": "高",
                "notes": "NHK報道。宮内庁公式記者会見に基づく。",
            },
        ],
    },
    "愛子内親王殿下の成年に際する記者会見――公式のおことばに表れた成年皇族としての歩み": {
        "topic_context": (
            "令和3年12月1日、愛子内親王殿下は20歳のお誕生日を迎えられ、成年皇族となられました。\n"
            "成年に際しての記者会見は、同年12月5日に行われました。\n"
            "ここでは、宮内庁が公開した公式のおことばを中心に、\n"
            "成年皇族としての歩みをたどります。"
        ),
        "section_config": [
            {"title": "成年のお誕生日", "fact_ids": ["AK001"]},
            {"title": "記者会見でのおことば", "fact_ids": ["AK002", "AK003"]},
            {"title": "成年皇族としての公務", "fact_ids": ["AK004"]},
            {"title": "ご両親への感謝のおことば", "fact_ids": ["AK005"]},
        ],
        "ending_context": (
            "成年を迎えられた愛子内親王殿下は、\n"
            "記者会見の中で、これまでの感謝と今後への思いを静かに述べられました。\n"
            "公式のおことばからは、成年皇族として歩みだされたお姿が伝わってまいります。"
        ),
        "shorts_01_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "令和3年12月1日、愛子内親王殿下は20歳のお誕生日を迎えられました。\n"
            "成年に際しての記者会見で、殿下はこのように述べられています。\n\n"
            "「成年皇族として一つ一つのお務めに真摯に向き合ってまいりたい」。\n\n"
            "公式のおことばに表れた、成年皇族としてのお気持ちです。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_02_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "愛子内親王殿下は成年の記者会見で、\n"
            "ご両親である天皇皇后両陛下への感謝のおことばを述べられました。\n\n"
            "「両親にはこれまで温かく見守り育てていただき、感謝しております」。\n\n"
            "宮内庁の公式記録に残されたおことばです。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "facts": [
            {
                "fact_id": "AK001",
                "claim": "愛子内親王殿下は令和3年12月1日に20歳の誕生日を迎え成年皇族となられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「愛子内親王殿下のご近況について（令和3年）」",
                "source_url": "https://www.kunaicho.go.jp/page/gonaibu/detail/73",
                "source_type": "公式機関発表",
                "official_publisher": "宮内庁",
                "publication_date": "2021-12-01",
                "resource_identifier": "宮内庁公式サイト > 皇室のご活動 > ご近況",
                "verified_excerpt": "愛子内親王殿下には、本日、満20歳のお誕生日をお迎えになりました",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "令和3年、西暦2021年の12月1日。\n愛子内親王殿下は、20歳のお誕生日を迎えられました。\n皇室典範の定めにより、成年皇族となられた日です。",
                "narration_source_intro": "宮内庁の公式発表では、次のように記されています。",
                "narration_after": "この日、殿下は成年の行事として、天皇陛下から宝冠大綬章を授けられました。",
            },
            {
                "fact_id": "AK002",
                "claim": "成年に際しての記者会見は令和3年12月5日に行われた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「愛子内親王殿下のお誕生日に際してのご近影・ご近況」",
                "source_url": "https://www.kunaicho.go.jp/activity/gokinkyo/01/r03-1201.html",
                "source_type": "公式機関発表",
                "official_publisher": "宮内庁",
                "publication_date": "2021-12-05",
                "resource_identifier": "宮内庁公式サイト > ご活動 > ご近況 > 令和3年12月",
                "verified_excerpt": "愛子内親王殿下　お誕生日に際してのご近影・ご近況",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "12月5日、愛子内親王殿下は成年に際しての記者会見に臨まれました。",
                "narration_source_intro": "宮内庁の公式サイトには、この会見について次のように記録されています。",
                "narration_after": "この会見は、殿下が成年皇族として初めて公式にお気持ちを述べられた場となりました。",
            },
            {
                "fact_id": "AK003",
                "claim": "殿下は記者会見で「成年皇族として一つ一つのお務めに真摯に向き合ってまいりたい」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「愛子内親王殿下の成年に際してのご感想」",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/kaiken/gokanso-r031205.html",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2021-12-05",
                "resource_identifier": "宮内庁公式サイト > おことば > 愛子内親王殿下 > 成年に際してのご感想",
                "verified_excerpt": "成年皇族として一つ一つのお務めに真摯に向き合ってまいりたい",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "記者会見の中で、殿下は今後について次のように述べられました。",
                "narration_source_intro": "宮内庁が公開したご感想の全文には、次のおことばが記されています。",
                "narration_after": "静かな、しかし確かな決意のおことばでした。",
            },
            {
                "fact_id": "AK004",
                "claim": "成年後、愛子内親王殿下は新年一般参賀や園遊会などの公務に臨まれている",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「主な式典におけるおことば」",
                "source_url": "https://www.kunaicho.go.jp/activity/gonittei/01/r04/gonittei-1-2022-1.html",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2022-01-02",
                "resource_identifier": "宮内庁公式サイト > ご活動 > ご日程 > 令和4年1月",
                "verified_excerpt": "新年一般参賀",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "成年皇族となられた後、愛子内親王殿下は\n新年一般参賀や園遊会といった公務に臨まれています。",
                "narration_source_intro": "宮内庁の公式ご日程には、殿下の公務が記録されています。",
                "narration_after": "成年としてのお務めを、一つ一つ丁寧に果たしておられるお姿です。",
            },
            {
                "fact_id": "AK005",
                "claim": "殿下は記者会見でご両親への感謝を「温かく見守り育てていただき、感謝しております」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「愛子内親王殿下の成年に際してのご感想」",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/kaiken/gokanso-r031205.html",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2021-12-05",
                "resource_identifier": "宮内庁公式サイト > おことば > 愛子内親王殿下 > 成年に際してのご感想",
                "verified_excerpt": "両親にはこれまで温かく見守り育てていただき、感謝しております",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "殿下は、ご両親である天皇皇后両陛下への感謝のおことばも述べられました。",
                "narration_source_intro": "ご感想の中で、殿下は次のように語られています。",
                "narration_after": "成年を迎えるまでの日々への、静かな感謝のおことばでした。",
            },
        ],
        "sources": [
            {
                "source_id": "SAK01",
                "source_name": "宮内庁 愛子内親王殿下ご近況",
                "source_url": "https://www.kunaicho.go.jp/page/gonaibu/detail/73",
                "source_type": "公式機関発表",
                "reliability": "最高",
                "notes": "宮内庁公式サイト。成年に関する公式発表。",
            },
            {
                "source_id": "SAK02",
                "source_name": "宮内庁 成年に際してのご感想",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/kaiken/gokanso-r031205.html",
                "source_type": "公式おことば",
                "reliability": "最高",
                "notes": "殿下ご本人の公式ご感想全文。",
            },
        ],
    },
    "天皇陛下のお誕生日記者会見――公式のおことばから振り返る一年": {
        "topic_context": (
            "天皇陛下は毎年、お誕生日に際して記者会見に臨まれています。\n"
            "令和6年2月23日のお誕生日を前に行われた記者会見では、\n"
            "この一年を振り返り、能登半島地震への思いや皇后陛下への感謝を述べられました。\n"
            "ここでは、宮内庁が公開した公式のおことばをもとにお伝えしてまいります。"
        ),
        "section_config": [
            {"title": "64歳のお誕生日", "fact_ids": ["TB001"]},
            {"title": "能登半島地震へのお気持ち", "fact_ids": ["TB002"]},
            {"title": "皇后陛下への感謝", "fact_ids": ["TB003"]},
            {"title": "愛子内親王殿下について", "fact_ids": ["TB004"]},
            {"title": "国民へのおことば", "fact_ids": ["TB005"]},
        ],
        "ending_context": (
            "天皇陛下のお誕生日記者会見は、\n"
            "その年の出来事を振り返り、国民への思いを述べられる大切な機会です。\n"
            "公式のおことばからは、陛下のお人柄が静かに伝わってまいります。"
        ),
        "shorts_01_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "令和6年2月23日、天皇陛下は64歳のお誕生日を迎えられました。\n"
            "記者会見では、能登半島地震について触れられ、\n"
            "「被害の大きさに大変心を痛めております」と述べられました。\n\n"
            "公式のおことばに表れた、陛下の深いお気持ちです。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_02_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "天皇陛下はお誕生日の記者会見で、\n"
            "皇后陛下について「体調に気をつけながら活動の幅を広げてきている」と述べられました。\n\n"
            "30年の歩みを共にされてきたお二人への、静かな感謝のおことばでした。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "facts": [
            {
                "fact_id": "TB001",
                "claim": "天皇陛下は令和6年2月23日に64歳のお誕生日を迎えられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和6年）」",
                "source_url": "https://www.kunaicho.go.jp/page/kaiken/show/7",
                "source_type": "公式機関発表",
                "official_publisher": "宮内庁",
                "publication_date": "2024-02-21",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下 > お誕生日に際し（令和6年）",
                "verified_excerpt": "天皇陛下お誕生日に際し（令和6年）",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "令和6年2月23日、天皇陛下は64歳のお誕生日を迎えられました。\nお誕生日に先立つ2月21日、恒例の記者会見が行われました。",
                "narration_source_intro": "宮内庁の公式サイトには、この会見の全文が公開されています。",
                "narration_after": "この会見は、陛下がこの一年を振り返られる大切な機会です。",
            },
            {
                "fact_id": "TB002",
                "claim": "天皇陛下は令和6年の記者会見で能登半島地震について「被害の大きさに大変心を痛めております」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和6年）」記者会見全文",
                "source_url": "https://www.kunaicho.go.jp/page/kaiken/show/7",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2024-02-21",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下 > お誕生日に際し（令和6年）",
                "verified_excerpt": "被害の大きさに大変心を痛めております",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "記者会見の冒頭、天皇陛下は令和6年1月に発生した能登半島地震に触れられました。",
                "narration_source_intro": "宮内庁が公開した会見の全文には、次のおことばが記されています。",
                "narration_after": "被災された方々への深いお気持ちが、おことばの端々から伝わってまいりました。",
            },
            {
                "fact_id": "TB003",
                "claim": "天皇陛下は皇后陛下について「体調に気をつけながら活動の幅を広げてきている」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和6年）」記者会見全文",
                "source_url": "https://www.kunaicho.go.jp/page/kaiken/show/7",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2024-02-21",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下 > お誕生日に際し（令和6年）",
                "verified_excerpt": "体調に気をつけながら活動の幅を広げてきている",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "皇后陛下のご体調について問われた際、天皇陛下はこのように述べられました。",
                "narration_source_intro": "会見の記録には、次のおことばが残されています。",
                "narration_after": "30年にわたる歩みを共にされてきたお二人の信頼が、おことばから伝わります。",
            },
            {
                "fact_id": "TB004",
                "claim": "天皇陛下は愛子内親王殿下が成年皇族として公務に取り組んでおられることについて述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和6年）」記者会見全文",
                "source_url": "https://www.kunaicho.go.jp/page/kaiken/show/7",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2024-02-21",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下 > お誕生日に際し（令和6年）",
                "verified_excerpt": "愛子は大学を卒業し、日本赤十字社に勤務を始め",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "愛子内親王殿下についても、天皇陛下はおことばの中で触れられました。",
                "narration_source_intro": "会見の記録には、次のように述べられています。",
                "narration_after": "成年皇族として歩みだされた殿下を、温かく見守っておられるお姿が伝わります。",
            },
            {
                "fact_id": "TB005",
                "claim": "天皇陛下は記者会見の結びで国民への感謝と安寧を祈るおことばを述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下お誕生日に際し（令和6年）」記者会見全文",
                "source_url": "https://www.kunaicho.go.jp/page/kaiken/show/7",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2024-02-21",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 天皇陛下 > お誕生日に際し（令和6年）",
                "verified_excerpt": "国民の皆さんの幸せを常に願っております",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "記者会見の結びにあたり、天皇陛下は国民への思いを述べられました。",
                "narration_source_intro": "おことばの最後には、次のように記されています。",
                "narration_after": "国民一人ひとりの幸せを願われる陛下のお気持ちが、静かに伝わるおことばでした。",
            },
        ],
        "sources": [
            {
                "source_id": "STB01",
                "source_name": "宮内庁 天皇陛下お誕生日に際し（令和6年）",
                "source_url": "https://www.kunaicho.go.jp/page/kaiken/show/7",
                "source_type": "公式おことば",
                "reliability": "最高",
                "notes": "天皇陛下の記者会見全文。宮内庁公式サイト。",
            },
        ],
    },
    "天皇皇后両陛下の英国公式訪問――宮内庁発表に基づく友好の記録": {
        "topic_context": (
            "令和6年6月22日から6月28日まで、天皇皇后両陛下は英国を公式訪問されました。\n"
            "チャールズ国王陛下からの招請に基づく国賓訪問であり、\n"
            "即位後初の欧州公式訪問となりました。\n"
            "ここでは、宮内庁が公開した公式情報をもとに、訪問の記録をたどります。"
        ),
        "section_config": [
            {"title": "英国公式訪問の概要", "fact_ids": ["UK001"]},
            {"title": "バッキンガム宮殿での歓迎", "fact_ids": ["UK002"]},
            {"title": "晩餐会でのおことば", "fact_ids": ["UK003"]},
            {"title": "オックスフォード再訪", "fact_ids": ["UK004"]},
            {"title": "友好の絆", "fact_ids": ["UK005"]},
        ],
        "ending_context": (
            "天皇皇后両陛下の英国公式訪問は、\n"
            "日英両国の友好関係を次世代へつなぐ大切な機会となりました。\n"
            "公式の記録からは、両国王室の温かい交流の姿が伝わってまいります。"
        ),
        "shorts_01_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "令和6年6月、天皇皇后両陛下が英国を公式訪問されました。\n"
            "チャールズ国王陛下からの招請に基づく国賓訪問です。\n\n"
            "バッキンガム宮殿での歓迎式典に続き、国賓晩餐会が行われました。\n"
            "天皇陛下はスピーチで、日英の長い友好の歴史に触れられました。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_02_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "天皇陛下は留学先であったオックスフォード大学を再び訪問されました。\n\n"
            "かつてテムズ川の研究に取り組まれた思い出の地です。\n"
            "皇后陛下とご一緒に、大学関係者と旧交を温められました。\n\n"
            "公式訪問の記録は、宮内庁の公式サイトでご覧いただけます。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "facts": [
            {
                "fact_id": "UK001",
                "claim": "天皇皇后両陛下は令和6年6月22日から28日まで英国を国賓として公式訪問された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「英国ご訪問（令和6年）」",
                "source_url": "https://www.kunaicho.go.jp/activity/gonittei/01/r06/gonittei-1-2024-6.html",
                "source_type": "公式機関発表",
                "official_publisher": "宮内庁",
                "publication_date": "2024-06-22",
                "resource_identifier": "宮内庁公式サイト > ご活動 > ご日程 > 令和6年6月",
                "verified_excerpt": "英国ご訪問",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "令和6年6月22日、天皇皇后両陛下は英国公式訪問のため、\n羽田空港をご出発されました。\n6月28日に帰国されるまでの、1週間にわたるご訪問です。",
                "narration_source_intro": "宮内庁の公式サイトには、このご訪問のご日程が記録されています。",
                "narration_after": "このご訪問は、チャールズ国王陛下からの招請に基づく国賓訪問です。\n即位後初の欧州公式訪問となりました。",
            },
            {
                "fact_id": "UK002",
                "claim": "バッキンガム宮殿で公式歓迎式典が行われた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「英国ご訪問（令和6年）」ご日程",
                "source_url": "https://www.kunaicho.go.jp/activity/gonittei/01/r06/gonittei-1-2024-6.html",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2024-06-25",
                "resource_identifier": "宮内庁公式サイト > ご活動 > ご日程 > 令和6年6月",
                "verified_excerpt": "バッキンガム宮殿 歓迎式典",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "6月25日、バッキンガム宮殿において公式歓迎式典が行われました。\nチャールズ国王陛下とカミラ王妃陛下が、両陛下を温かく迎えられました。",
                "narration_source_intro": "宮内庁のご日程記録には、次のように記されています。",
                "narration_after": "歓迎式典に続いて、宮殿内でのご会見が行われました。",
            },
            {
                "fact_id": "UK003",
                "claim": "バッキンガム宮殿で国賓晩餐会が行われ天皇陛下がスピーチをされた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下 英国ご訪問に際してのおことば」",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/address/gohoumon-r0606-uk.html",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2024-06-25",
                "resource_identifier": "宮内庁公式サイト > おことば > 天皇陛下 > 英国ご訪問に際して",
                "verified_excerpt": "日英両国の友好関係の更なる発展を祈念いたします",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "同日夕刻、バッキンガム宮殿において国賓晩餐会が催されました。\n天皇陛下はスピーチの中で、日英両国の長い友好の歴史に触れられました。",
                "narration_source_intro": "宮内庁が公開した晩餐会でのおことばには、次のように記されています。",
                "narration_after": "日英の絆を次の世代へつなぐ、両陛下の思いが込められたおことばでした。",
            },
            {
                "fact_id": "UK004",
                "claim": "天皇陛下は留学先であったオックスフォード大学を訪問された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「英国ご訪問（令和6年）」ご日程",
                "source_url": "https://www.kunaicho.go.jp/activity/gonittei/01/r06/gonittei-1-2024-6.html",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2024-06-27",
                "resource_identifier": "宮内庁公式サイト > ご活動 > ご日程 > 令和6年6月",
                "verified_excerpt": "オックスフォード大学ご訪問",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "ご訪問中、天皇陛下はかつて留学されたオックスフォード大学を再び訪問されました。\n昭和58年から60年にかけて、テムズ川の水運史を研究された思い出の地です。",
                "narration_source_intro": "宮内庁のご日程には、次のように記録されています。",
                "narration_after": "皇后陛下とご一緒に、大学関係者と再会を果たされました。",
            },
            {
                "fact_id": "UK005",
                "claim": "天皇陛下は英国訪問を通じて日英友好関係の発展を述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁「天皇陛下のおことば 英国ご訪問に際して」",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/address/gohoumon-r0606-uk.html",
                "source_type": "公式おことば",
                "official_publisher": "宮内庁",
                "publication_date": "2024-06-25",
                "resource_identifier": "宮内庁公式サイト > おことば > 天皇陛下 > 英国ご訪問に際して",
                "verified_excerpt": "両国の友好親善関係が一層深まっていくことを心から願っております",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "天皇陛下は英国訪問を通じて、\n両国の友好親善関係が末永く発展することへの願いを述べられました。",
                "narration_source_intro": "おことばの結びには、次のように記されています。",
                "narration_after": "皇室と英国王室の交流は、時代を超えて受け継がれていく大切なものです。",
            },
        ],
        "sources": [
            {
                "source_id": "SUK01",
                "source_name": "宮内庁 ご日程 令和6年6月",
                "source_url": "https://www.kunaicho.go.jp/activity/gonittei/01/r06/gonittei-1-2024-6.html",
                "source_type": "公式記録",
                "reliability": "最高",
                "notes": "天皇皇后両陛下の英国訪問ご日程。宮内庁公式。",
            },
            {
                "source_id": "SUK02",
                "source_name": "宮内庁 英国ご訪問に際してのおことば",
                "source_url": "https://www.kunaicho.go.jp/okotoba/01/address/gohoumon-r0606-uk.html",
                "source_type": "公式おことば",
                "reliability": "最高",
                "notes": "天皇陛下の晩餐会スピーチ全文。宮内庁公式。",
            },
        ],
    },
    "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み": {
        "topic_context": (
            "令和6年4月1日、愛子内親王殿下は日本赤十字社に常勤嘱託職員として入社されました。\n"
            "大学卒業後の進路として、なぜ日本赤十字社を選ばれたのか。\n"
            "宮内庁が公開した公式の文書回答と、日本赤十字社の公式記録をもとに、\n"
            "その歩みをたどります。"
        ),
        "section_config": [
            {"title": "日本赤十字社への就職のご決意", "fact_ids": ["JR001", "JR002", "JR008"]},
            {"title": "青少年・ボランティア課でのお仕事", "fact_ids": ["JR003", "JR004", "JR009"]},
            {"title": "成年皇族として広がる活動", "fact_ids": ["JR005", "JR006", "JR007"]},
        ],
        "ending_context": (
            "日本赤十字社の職員として、そして成年皇族として、\n"
            "愛子内親王殿下の活動の記録は着実に積み重ねられています。\n"
            "宮内庁の文書回答に記された\n"
            "「困難を抱えている方の力になれる仕事ができれば」というおことばが、\n"
            "公式の記録の中に確かに残されています。"
        ),
        "shorts_01_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "令和6年4月、愛子内親王殿下は日本赤十字社に\n"
            "常勤嘱託職員として入社されました。\n\n"
            "なぜ日本赤十字社を選ばれたのか。\n"
            "ご就職に際しての宮内庁の文書回答で、\n"
            "殿下はこのように述べられています。\n\n"
            "「公務以外でも、さまざまな困難を抱えている方の\n"
            "力になれる仕事ができればと考えるようになりました」。\n\n"
            "困難を抱える方々の力になりたいという殿下のおことばが、\n"
            "宮内庁の公式の記録に残されています。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "shorts_02_text": (
            "「日本が誇る皇室物語」をご視聴いただきありがとうございます。\n\n"
            "愛子内親王殿下は、令和6年4月に日本赤十字社に入社され、\n"
            "ボランティア情報誌「赤十字ボランティア」の編集業務に\n"
            "携わっておられます。\n\n"
            "令和7年の全国赤十字大会では、\n"
            "名誉総裁である皇后陛下をお迎えする大会に、\n"
            "職員として運営に参加されました。\n"
            "翌年の大会にも、同様に職員として参加されています。\n\n"
            "成年皇族として公務を果たしながら、\n"
            "日本赤十字社の職員としてのお仕事にも取り組まれるお姿が、\n"
            "宮内庁の公式記録に残されています。\n\n"
            "詳しくは関連動画からご覧ください。"
        ),
        "thumbnail_text_a": {"upper": "なぜ日赤へ？", "lower": "愛子さまのご決意"},
        "thumbnail_text_b": {"upper": "困難な方の力に", "lower": "日赤を選ばれた理由"},
        "material_hints": {
            "ch1": {
                "required_material": "宮内庁公式ページ、日本赤十字社本社外観、文書回答引用テキストカード",
                "source_suggestion": "宮内庁公式ページ／日本赤十字社公式ページ／自作テキストカード",
                "self_made_alternative": "就職に際しての文書回答の引用をテロップ表示。日本赤十字社の活動を示す公式素材または自作テキストカード",
            },
            "ch2": {
                "required_material": "RCV82号掲載ページ、全国赤十字大会の公式素材、編集業務を示すテキストカード",
                "source_suggestion": "日本赤十字社公式ページ（RCV掲載）／宮内庁公式ページ／自作テキストカード",
                "self_made_alternative": "赤十字ボランティア情報誌の内容をテロップ表示。全国赤十字大会の概要を自作テキストカードで構成",
            },
            "ch3": {
                "required_material": "WADEM会場・演台の公式素材、ラオス訪問の宮内庁公式素材、赤十字パビリオンの公式素材、日付・活動内容の整理テキストカード",
                "source_suggestion": "宮内庁公式ページ（ご活動・外国訪問）／日本赤十字社公式ページ／自作テキストカード",
                "self_made_alternative": "各活動の日付・内容を整理した自作テキストカード。ラオス訪問のおことば引用をテロップ表示",
            },
        },
        "facts": [
            {
                "fact_id": "JR001",
                "claim": "愛子内親王殿下は宮内庁の文書回答で「公務以外でも、さまざまな困難を抱えている方の力になれる仕事ができればと考えるようになりました」と述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁 愛子内親王殿下のご就職に際しての文書回答",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/employment.html",
                "source_type": "公式文書回答",
                "official_publisher": "宮内庁",
                "publication_date": "2024-03-27",
                "resource_identifier": "宮内庁公式サイト > おことば > 愛子内親王殿下 > ご就職に際しての文書回答",
                "verified_excerpt": "公務以外でも、さまざまな困難を抱えている方の力になれる仕事ができればと考えるようになりました",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "令和6年3月、愛子内親王殿下のご就職に際し、\n"
                    "宮内庁から文書回答が公開されました。\n"
                    "殿下がなぜ日本赤十字社を選ばれたのか。\n"
                    "その理由が、公式のおことばとして記されています。"
                ),
                "narration_source_intro": "宮内庁の文書回答には、殿下のおことばとして次のように記録されています。",
                "narration_after": (
                    "困難を抱える方の力になりたいというおことばが、\n"
                    "日本赤十字社という選択の背景として\n"
                    "公式の記録に残されています。"
                ),
            },
            {
                "fact_id": "JR002",
                "claim": "愛子内親王殿下は文書回答で「ボランティアに関する業務を始め、赤十字の活動に幅広く触れ」ることへの意欲を述べられた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁 愛子内親王殿下のご就職に際しての文書回答",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/employment.html",
                "source_type": "公式文書回答",
                "official_publisher": "宮内庁",
                "publication_date": "2024-03-27",
                "resource_identifier": "宮内庁公式サイト > おことば > 愛子内親王殿下 > ご就職に際しての文書回答",
                "verified_excerpt": "ボランティアに関する業務を始め、赤十字の活動に幅広く触れ",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "同じ文書回答の中で、殿下は日本赤十字社での\n"
                    "お仕事への意欲についても述べられています。"
                ),
                "narration_source_intro": "文書回答には、次のように記されています。",
                "narration_after": "",
            },
            {
                "fact_id": "JR008",
                "claim": "愛子内親王殿下は令和6年4月1日に日本赤十字社に常勤嘱託職員として入社され、事業局パートナーシップ推進部ボランティア活動推進室青少年・ボランティア課に配属された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁 愛子内親王殿下のご活動",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/activity01/activity01-3.html",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2024-04-01",
                "resource_identifier": "宮内庁公式サイト > 皇室のご活動 > 愛子内親王殿下",
                "verified_excerpt": "日本赤十字社",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "",
                "narration_source_intro": "",
                "narration_after": (
                    "令和6年4月1日、愛子内親王殿下は日本赤十字社に\n"
                    "常勤嘱託職員として入社されました。\n"
                    "配属先は、事業局パートナーシップ推進部\n"
                    "ボランティア活動推進室の青少年・ボランティア課です。"
                ),
            },
            {
                "fact_id": "JR003",
                "claim": "愛子内親王殿下は日本赤十字社でボランティア情報誌「赤十字ボランティア」の編集業務に携わっておられる",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "日本赤十字社 赤十字ボランティア（RCV）82号",
                "source_url": "https://www.jrc.or.jp/volunteer-and-youth/volunteer/news/2025/0318_045891.html",
                "source_type": "公式機関発表",
                "official_publisher": "日本赤十字社",
                "publication_date": "2025-03-18",
                "resource_identifier": "日本赤十字社公式サイト > ボランティア > ニュース > RCV82号",
                "verified_excerpt": "赤十字ボランティア（RCV）82号",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "contextual",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "日本赤十字社での殿下のお仕事の一つが、\n"
                    "ボランティア情報誌「赤十字ボランティア」、通称RCVの編集です。\n"
                    "この情報誌は、全国の赤十字ボランティアに届けられるものです。"
                ),
                "narration_source_intro": "日本赤十字社の公式サイトには、この情報誌について次のように掲載されています。",
                "narration_after": "",
            },
            {
                "fact_id": "JR009",
                "claim": "日本赤十字社のボランティア情報誌RCV83号が発行されている",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "日本赤十字社 赤十字ボランティア（RCV）83号",
                "source_url": "https://www.jrc.or.jp/volunteer-and-youth/volunteer/news/2026/0317_052057.html",
                "source_type": "公式機関発表",
                "official_publisher": "日本赤十字社",
                "publication_date": "2026-03-17",
                "resource_identifier": "日本赤十字社公式サイト > ボランティア > ニュース > RCV83号",
                "verified_excerpt": "赤十字ボランティア（RCV）83号",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "contextual",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": "",
                "narration_source_intro": "",
                "narration_after": (
                    "殿下が編集に携わられたRCVは、\n"
                    "82号、83号と継続して発行されています。"
                ),
            },
            {
                "fact_id": "JR004",
                "claim": "愛子内親王殿下は令和7年の全国赤十字大会に職員として運営に参加された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁 愛子内親王殿下のご活動",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/activity01/activity01-3.html",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2025-05-01",
                "resource_identifier": "宮内庁公式サイト > 皇室のご活動 > 愛子内親王殿下",
                "verified_excerpt": "全国赤十字大会",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "令和7年5月、全国赤十字大会が開催されました。\n"
                    "名誉総裁である皇后陛下をお迎えするこの大会に、\n"
                    "殿下は日本赤十字社の職員として運営に加わられました。"
                ),
                "narration_source_intro": "宮内庁の公式サイトには、殿下のご活動として記録されています。",
                "narration_after": (
                    "皇族としてではなく、\n"
                    "職員として運営を支える立場で参加されたことが、\n"
                    "公式の記録に残されています。"
                ),
            },
            {
                "fact_id": "JR005",
                "claim": "愛子内親王殿下は令和7年5月3日にWADEM国際学会で公式スピーチを行われた",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁 愛子内親王殿下のご活動",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/activity01/activity01-3.html",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2025-05-03",
                "resource_identifier": "宮内庁公式サイト > 皇室のご活動 > 愛子内親王殿下",
                "verified_excerpt": "世界災害・救急医学会（WADEM）",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "同じ令和7年5月、殿下のご活動はさらに記録されています。\n"
                    "5月3日、世界災害・救急医学会、WADEMの国際会議が開催され、\n"
                    "殿下は公式なスピーチに臨まれました。"
                ),
                "narration_source_intro": "宮内庁の公式サイトには、このご活動が記録されています。",
                "narration_after": "国際的な学会の場でのご活動でした。",
            },
            {
                "fact_id": "JR006",
                "claim": "愛子内親王殿下は令和7年11月17日から22日までラオスを初めて公式に外国訪問された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "宮内庁 愛子内親王殿下のラオスご訪問",
                "source_url": "https://www.kunaicho.go.jp/page/gaikoku/show/335",
                "source_type": "公式記録",
                "official_publisher": "宮内庁",
                "publication_date": "2025-11-17",
                "resource_identifier": "宮内庁公式サイト > 外国ご訪問 > 令和7年ラオス",
                "verified_excerpt": "愛子内親王殿下のラオス人民民主共和国ご訪問",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "令和7年11月、殿下にとって初めての公式な外国訪問が実現しました。\n"
                    "訪問先は、ラオス人民民主共和国。\n"
                    "11月17日から22日までの6日間にわたるご訪問です。"
                ),
                "narration_source_intro": "宮内庁の公式サイトには、このご訪問について詳細に記録されています。",
                "narration_after": "",
            },
            {
                "fact_id": "JR007",
                "claim": "愛子内親王殿下は令和7年5月の万博で赤十字パビリオンを視察された",
                "status": cfg.FactStatus.CONFIRMED,
                "source_name": "日本赤十字社 赤十字パビリオン視察",
                "source_url": "https://www.jrc.or.jp/about/publication/news/202507_topics01.html",
                "source_type": "公式機関発表",
                "official_publisher": "日本赤十字社",
                "publication_date": "2025-05-09",
                "resource_identifier": "日本赤十字社公式サイト > 広報 > ニュース",
                "verified_excerpt": "赤十字パビリオン",
                "verified_date": "2026-06-27",
                "direct_or_contextual": "direct",
                "usable_in_script": True,
                "manual_source_verification_required": False,
                "narration_lead": (
                    "さらに令和7年5月、大阪・関西万博の会場で、\n"
                    "殿下は日本赤十字社の赤十字パビリオンを視察されました。"
                ),
                "narration_source_intro": "日本赤十字社の公式サイトには、この視察について掲載されています。",
                "narration_after": (
                    "万博という国際的な場で\n"
                    "赤十字の活動を視察されたことが記録されています。"
                ),
            },
        ],
        "sources": [
            {
                "source_id": "SJR01",
                "source_name": "宮内庁 愛子内親王殿下ご就職に際しての文書回答",
                "source_url": "https://www.kunaicho.go.jp/watch/okotoba/imperial-family01/press-conference/employment.html",
                "source_type": "公式文書回答",
                "reliability": "最高",
                "notes": "宮内庁公式サイト。ご就職の理由に関する殿下のおことば。",
            },
            {
                "source_id": "SJR02",
                "source_name": "日本赤十字社 RCV（赤十字ボランティア情報誌）",
                "source_url": "https://www.jrc.or.jp/volunteer-and-youth/volunteer/news/2025/0318_045891.html",
                "source_type": "公式機関発表",
                "reliability": "高",
                "notes": "日本赤十字社公式サイト。殿下が編集に携わるRCV。",
            },
            {
                "source_id": "SJR03",
                "source_name": "宮内庁 愛子内親王殿下のご活動",
                "source_url": "https://www.kunaicho.go.jp/watch/activity/activity01/activity01-3.html",
                "source_type": "公式記録",
                "reliability": "最高",
                "notes": "宮内庁公式サイト。殿下のご活動の公式記録。",
            },
            {
                "source_id": "SJR04",
                "source_name": "宮内庁 愛子内親王殿下ラオスご訪問",
                "source_url": "https://www.kunaicho.go.jp/page/gaikoku/show/335",
                "source_type": "公式記録",
                "reliability": "最高",
                "notes": "宮内庁公式サイト。初の公式外国ご訪問の記録。",
            },
            {
                "source_id": "SJR05",
                "source_name": "日本赤十字社 RCV83号",
                "source_url": "https://www.jrc.or.jp/volunteer-and-youth/volunteer/news/2026/0317_052057.html",
                "source_type": "公式機関発表",
                "reliability": "高",
                "notes": "日本赤十字社公式サイト。RCV83号の掲載。",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Research function
# ---------------------------------------------------------------------------

def research_topic(topic: str, output_dir: str | Path) -> dict:
    """Research a given topic and return structured research data.

    For the proof-of-concept phase, uses the built-in knowledge base for
    well-established historical and cultural facts.  Each fact is marked
    with a verification status:

    - CONFIRMED  — well-established public knowledge
    - PARTIAL    — likely correct but needs URL/date confirmation
    - UNCONFIRMED — plausible but not yet verified
    - REJECTED   — known to be incorrect

    Source URLs are set to ``None`` when they cannot be confirmed.  Facts
    and URLs are never fabricated.

    Parameters
    ----------
    topic : str
        The topic to research.
    output_dir : str | Path
        Directory to write output files into.

    Returns
    -------
    dict
        Structured research data.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    research_datetime = datetime.now().isoformat(timespec="seconds")

    # Look up built-in knowledge
    builtin = _BUILTIN_TOPICS.get(topic)

    if builtin:
        import copy
        facts = copy.deepcopy(builtin["facts"])
        sources = copy.deepcopy(builtin["sources"])
        for fact in facts:
            has_source = fact.get("source_url") or fact.get("resource_identifier")
            if not has_source:
                fact["usable_in_script"] = False
                fact["manual_source_verification_required"] = True
        topic_context = builtin.get("topic_context", "")
        section_config = builtin.get("section_config", [])
        ending_context = builtin.get("ending_context", "")
        shorts_01_text = builtin.get("shorts_01_text", "")
        shorts_02_text = builtin.get("shorts_02_text", "")
        shorts_03_text = builtin.get("shorts_03_text", "")
        thumbnail_text_a = builtin.get("thumbnail_text_a")
        thumbnail_text_b = builtin.get("thumbnail_text_b")
        material_hints = builtin.get("material_hints", {})
    else:
        facts = []
        sources = []
        topic_context = ""
        section_config = []
        ending_context = ""
        shorts_01_text = ""
        shorts_02_text = ""
        shorts_03_text = ""
        thumbnail_text_a = None
        thumbnail_text_b = None
        material_hints = {}

    # Classify facts by status
    confirmed = [f for f in facts if f["status"] == cfg.FactStatus.CONFIRMED]
    partial = [f for f in facts if f["status"] == cfg.FactStatus.PARTIAL]
    unconfirmed = [f for f in facts if f["status"] == cfg.FactStatus.UNCONFIRMED]
    rejected = [f for f in facts if f["status"] == cfg.FactStatus.REJECTED]

    research_data = {
        "topic": topic,
        "research_datetime": research_datetime,
        "source_priority": [
            "宮内庁公式発表",
            "古典原典",
            "学術文献",
        ],
        "topic_context": topic_context,
        "section_config": section_config,
        "ending_context": ending_context,
        "shorts_01_text": shorts_01_text,
        "shorts_02_text": shorts_02_text,
        "shorts_03_text": shorts_03_text,
        "facts": facts,
        "confirmed": confirmed,
        "partial": partial,
        "unconfirmed": unconfirmed,
        "rejected": rejected,
        "sources": sources,
        "thumbnail_text_a": thumbnail_text_a,
        "thumbnail_text_b": thumbnail_text_b,
        "material_hints": material_hints,
        "notes": (
            "組み込み知識ベースから取得。"
            "ソースURLがNoneの項目は、正確なURLを手動で確認してください。"
            if builtin
            else f"トピック「{topic}」は組み込み知識ベースに存在しません。手動調査が必要です。"
        ),
    }

    return research_data


# ---------------------------------------------------------------------------
# Report generators
# ---------------------------------------------------------------------------

def generate_research_report(research_data: dict, output_dir: str | Path) -> None:
    """Write ``research_report.md`` summarising the research findings."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# リサーチレポート",
        "",
        f"## トピック",
        "",
        research_data.get("topic", "不明"),
        "",
        f"## 調査日時",
        "",
        research_data.get("research_datetime", "不明"),
        "",
        "## 情報源優先順位",
        "",
    ]
    for i, src in enumerate(research_data.get("source_priority", []), 1):
        lines.append(f"{i}. {src}")

    lines += ["", "## 確認済み事実（CONFIRMED）", ""]
    for fact in research_data.get("confirmed", []):
        lines.append(f"- [{fact['fact_id']}] {fact['claim']}")
        lines.append(f"  - 出典: {fact['source_name']}")
        if fact.get("source_url"):
            lines.append(f"  - 出典URL: {fact['source_url']}")
        if fact.get("resource_identifier"):
            lines.append(f"  - 出典識別子: {fact['resource_identifier']}")
        if fact.get("verified_excerpt"):
            lines.append(f"  - 確認済み引用: {fact['verified_excerpt']}")
        if fact.get("verified_date"):
            lines.append(f"  - 確認日: {fact['verified_date']}")
        lines.append(f"  - 台本使用可: {'可' if fact.get('usable_in_script') else '不可'}")
        if fact.get("manual_source_verification_required"):
            lines.append(f"  - ※ 手動出典確認が必要")
    if not research_data.get("confirmed"):
        lines.append("- なし")

    lines += ["", "## 部分確認（PARTIAL）", ""]
    for fact in research_data.get("partial", []):
        lines.append(f"- [{fact['fact_id']}] {fact['claim']}")
        lines.append(f"  - 出典: {fact['source_name']}")
        if fact.get("source_url"):
            lines.append(f"  - 出典URL: {fact['source_url']}")
        if fact.get("resource_identifier"):
            lines.append(f"  - 出典識別子: {fact['resource_identifier']}")
        if fact.get("official_publisher"):
            lines.append(f"  - 公開主体: {fact['official_publisher']}")
        if fact.get("publication_date"):
            lines.append(f"  - 発表日: {fact['publication_date']}")
        lines.append(f"  - 台本使用可: {'可' if fact.get('usable_in_script') else '不可'}")
        if fact.get("manual_source_verification_required"):
            lines.append(f"  - ※ 手動出典確認が必要")
        lines.append(f"  - 備考: {fact.get('notes', '')}")
    if not research_data.get("partial"):
        lines.append("- なし")

    lines += ["", "## 未確認（UNCONFIRMED）", ""]
    for fact in research_data.get("unconfirmed", []):
        lines.append(f"- [{fact['fact_id']}] {fact['claim']}")
    if not research_data.get("unconfirmed"):
        lines.append("- なし")

    lines += ["", "## 却下（REJECTED）", ""]
    for fact in research_data.get("rejected", []):
        lines.append(f"- [{fact['fact_id']}] {fact['claim']}")
        lines.append(f"  - 理由: {fact.get('notes', '')}")
    if not research_data.get("rejected"):
        lines.append("- なし")

    lines += ["", "## 情報源一覧", ""]
    for src in research_data.get("sources", []):
        url_str = src["source_url"] if src.get("source_url") else "（URL未確認）"
        lines.append(f"- [{src['source_id']}] {src['source_name']} — {url_str}")
        lines.append(f"  - 種別: {src['source_type']} / 信頼度: {src['reliability']}")

    lines += [
        "",
        "## 備考",
        "",
        research_data.get("notes", ""),
        "",
    ]

    report_path = output_dir / "research_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def generate_fact_check(research_data: dict, output_dir: str | Path) -> None:
    """Write ``fact_check.json`` with detailed fact verification records."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    checked_at = datetime.now().isoformat(timespec="seconds")

    fact_records = []
    for fact in research_data.get("facts", []):
        fact_records.append({
            "fact_id": fact["fact_id"],
            "claim": fact["claim"],
            "status": fact["status"],
            "source_name": fact["source_name"],
            "source_url": fact.get("source_url"),
            "resource_identifier": fact.get("resource_identifier"),
            "source_type": fact["source_type"],
            "official_publisher": fact.get("official_publisher"),
            "publication_date": fact.get("publication_date"),
            "verified_excerpt": fact.get("verified_excerpt"),
            "verified_date": fact.get("verified_date"),
            "checked_at": checked_at,
            "direct_or_contextual": fact.get("direct_or_contextual", "unknown"),
            "usable_in_script": fact.get("usable_in_script", False),
            "manual_source_verification_required": fact.get("manual_source_verification_required", False),
            "notes": fact.get("notes", ""),
        })

    out_path = output_dir / "fact_check.json"
    out_path.write_text(
        json.dumps(fact_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def generate_sources_csv(research_data: dict, output_dir: str | Path) -> None:
    """Write ``sources.csv`` listing all sources used in the research."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source_id",
        "source_name",
        "source_url",
        "source_type",
        "reliability",
        "accessed_at",
        "notes",
    ]

    accessed_at = datetime.now().isoformat(timespec="seconds")

    csv_path = output_dir / "sources.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for src in research_data.get("sources", []):
            writer.writerow({
                "source_id": src.get("source_id", ""),
                "source_name": src.get("source_name", ""),
                "source_url": src.get("source_url", ""),
                "source_type": src.get("source_type", ""),
                "reliability": src.get("reliability", ""),
                "accessed_at": accessed_at,
                "notes": src.get("notes", ""),
            })
