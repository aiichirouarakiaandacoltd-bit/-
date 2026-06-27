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
    else:
        facts = []
        sources = []
        topic_context = ""
        section_config = []
        ending_context = ""
        shorts_01_text = ""
        shorts_02_text = ""

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
        "facts": facts,
        "confirmed": confirmed,
        "partial": partial,
        "unconfirmed": unconfirmed,
        "rejected": rejected,
        "sources": sources,
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
