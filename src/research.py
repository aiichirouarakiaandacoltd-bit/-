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
        "facts": [
            {
                "fact_id": "F001",
                "claim": "愛子内親王殿下は2001年（平成13年）12月1日に御誕生になった",
                "status": cfg.FactStatus.PARTIAL,
                "source_name": "官報 宮内庁告示第12号（平成13年12月1日）",
                "source_url": None,
                "source_type": "公式機関発表（官報）",
                "official_publisher": "宮内庁（官報掲載）",
                "publication_date": "2001-12-01",
                "resource_identifier": "官報 平成13年12月1日 宮内庁告示第12号 / 告示名: 皇太子徳仁親王妃雅子殿下御出産・内親王御誕生の件 / 公開主体: 宮内庁",
                "verified_excerpt": None,
                "verified_date": None,
                "direct_or_contextual": "direct",
                "usable_in_script": False,
                "manual_source_verification_required": True,
                "notes": "一次資料は特定済み（官報 宮内庁告示第12号、平成13年12月1日）。ネットワーク制限により官報原文を直接閲覧できず、verified_excerptを未取得。官報検索システムまたは国立国会図書館デジタルコレクションで原文確認が必要。",
            },
            {
                "fact_id": "F002",
                "claim": "御名「愛子」は『孟子』離婁章句下の一節に由来すると、命名の儀において公式に発表された",
                "status": cfg.FactStatus.PARTIAL,
                "source_name": "宮内庁 皇太子殿下記者会見「愛子内親王殿下御誕生につき」（平成14年4月2日）",
                "source_url": "https://www.kunaicho.go.jp/okotoba/02/kaiken/kaiken-h14-gotanjo.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2002-04-02",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 皇太子殿下記者会見「愛子内親王殿下御誕生につき」（平成14年4月2日） / 官報 宮内庁告示第15号（平成13年12月7日）も関連資料",
                "verified_excerpt": None,
                "verified_date": None,
                "direct_or_contextual": "direct",
                "usable_in_script": False,
                "manual_source_verification_required": True,
                "notes": "一次資料ページは特定済み（宮内庁公式サイト記者会見ページ）。ネットワーク制限によりページ本文を直接閲覧できず、verified_excerptを未取得。宮内庁サイトで皇太子殿下のお言葉の原文確認が必要。命名典拠の裏付けはこの記者会見の原文で確認可能。",
            },
            {
                "fact_id": "F003",
                "claim": "御称号「敬宮」（としのみや）も同じ『孟子』離婁章句下の一節に由来すると公式に発表された",
                "status": cfg.FactStatus.PARTIAL,
                "source_name": "宮内庁 皇太子殿下記者会見「愛子内親王殿下御誕生につき」（平成14年4月2日）",
                "source_url": "https://www.kunaicho.go.jp/okotoba/02/kaiken/kaiken-h14-gotanjo.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2002-04-02",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 皇太子殿下記者会見「愛子内親王殿下御誕生につき」（平成14年4月2日） / 官報 宮内庁告示第15号（平成13年12月7日）「敬宮と称される」",
                "verified_excerpt": None,
                "verified_date": None,
                "direct_or_contextual": "direct",
                "usable_in_script": False,
                "manual_source_verification_required": True,
                "notes": "一次資料ページは特定済み（F002と同一ページ）。ネットワーク制限によりページ本文を直接閲覧できず、verified_excerptを未取得。宮内庁サイトで原文確認が必要。",
            },
            {
                "fact_id": "F004",
                "claim": "御名・御称号は天皇陛下（当時皇太子殿下）がお選びになった",
                "status": cfg.FactStatus.PARTIAL,
                "source_name": "宮内庁 皇太子殿下記者会見「愛子内親王殿下御誕生につき」（平成14年4月2日）",
                "source_url": "https://www.kunaicho.go.jp/okotoba/02/kaiken/kaiken-h14-gotanjo.html",
                "source_type": "公式機関発表（記者会見）",
                "official_publisher": "宮内庁",
                "publication_date": "2002-04-02",
                "resource_identifier": "宮内庁公式サイト > おことば・記者会見 > 皇太子殿下記者会見「愛子内親王殿下御誕生につき」（平成14年4月2日）",
                "verified_excerpt": None,
                "verified_date": None,
                "direct_or_contextual": "contextual",
                "usable_in_script": False,
                "manual_source_verification_required": True,
                "notes": "一次資料ページは特定済み（F002と同一ページ）。ネットワーク制限によりページ本文を直接閲覧できず、verified_excerptを未取得。宮内庁サイトで原文確認が必要。",
            },
            {
                "fact_id": "F005",
                "claim": "宮内庁は2001年12月7日の命名の儀をもって御名・御称号を正式に発表した",
                "status": cfg.FactStatus.PARTIAL,
                "source_name": "官報 宮内庁告示第15号（平成13年12月7日）",
                "source_url": None,
                "source_type": "公式機関発表（官報）",
                "official_publisher": "宮内庁（官報掲載）",
                "publication_date": "2001-12-07",
                "resource_identifier": "官報 平成13年12月7日 宮内庁告示第15号 / 告示名: 内親王殿下の御名を愛子と命ぜられ敬宮と称される件 / 公開主体: 宮内庁 / 国立公文書館 天皇陛下御在位20周年記念公文書特別展示会 第45項にて展示実績あり",
                "verified_excerpt": None,
                "verified_date": None,
                "direct_or_contextual": "direct",
                "usable_in_script": False,
                "manual_source_verification_required": True,
                "notes": "一次資料は特定済み（官報 宮内庁告示第15号）。国立公文書館の御在位20周年記念展示資料（第45項）としても確認。ネットワーク制限により官報原文を直接閲覧できず、verified_excerptを未取得。官報検索システムまたは国立公文書館で原文確認が必要。",
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
                "notes": "古典原文の存在確認。上記底本および各種注釈書・学術データベースで第三者が再確認可能。この一節が命名典拠として採用された事実はF002・F003で別途検証が必要。",
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
                "notes": "一般的に認められた慣例だが、単一の公式一次資料を特定できていない。今回の動画テーマに必須ではないため、usable_in_script=falseのまま。",
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
            {
                "source_id": "S003",
                "source_name": "NHK報道（2001年12月命名発表時）",
                "source_url": None,
                "source_type": "公共放送",
                "reliability": "高",
                "notes": "放送アーカイブのURL未確認。",
            },
            {
                "source_id": "S004",
                "source_name": "主要全国紙報道（2001年12月）",
                "source_url": None,
                "source_type": "全国紙",
                "reliability": "高",
                "notes": "読売・朝日・毎日・産経・日経各紙。個別記事URLは要確認。",
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
    else:
        facts = []
        sources = []

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
            "NHK・共同通信・時事通信",
            "主要全国紙",
            "学術文献",
        ],
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
