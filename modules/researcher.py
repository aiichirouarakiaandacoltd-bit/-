"""
Research and fact-check module for showa-heisei-video-automation.
Gathers, structures, and verifies facts about Showa/Heisei era topics.
"""

import os
import csv
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PRIORITY_SOURCES = [
    "国立国会図書館デジタルコレクション",
    "総務省統計局",
    "NHKアーカイブス",
    "内閣府",
    "経済産業省",
    "文部科学省",
    "国立歴史民俗博物館",
    "日本放送協会（NHK）放送文化研究所",
    "家電メーカー公式社史",
    "新聞縮刷版（朝日・読売・毎日）",
]

# Built-in knowledge base for test mode / offline fallback
# evidence_type: "direct" = 布かけ習慣の直接的根拠, "background" = テレビ普及等の周辺背景
# usable_in_script_as: CONFIRMED+出典あり→事実断定, PARTIAL→限定表現のみ, UNCONFIRMED/REJECTED→不可
KNOWLEDGE_BASE = {
    "テレビ_布": {
        "facts": [
            {
                "fact_id": "TV_CLOTH_001",
                "claim": "1950年代後半〜1960年代、白黒テレビの価格は一般家庭の月収3〜6ヶ月分に相当した",
                "status": "PARTIAL",
                "source_type": "経済史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "全国",
                "period_scope": "昭和30年代〜40年代（1955-1970頃）",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "具体的な価格は年代・機種により異なる。出典URLなし。"
                         "限定表現で使用：「月収数ヶ月分に相当したとも言われています」",
            },
            {
                "fact_id": "TV_CLOTH_002",
                "claim": "真空管テレビは発熱が大きく、ほこりが静電気で付着しやすかった。"
                         "布カバーはほこりよけとしての実用面もあったと考えられる",
                "status": "PARTIAL",
                "source_type": "技術史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "direct",
                "regional_scope": "全国",
                "period_scope": "昭和20年代後半〜40年代（1953-1970頃）",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "真空管の発熱と静電気は技術的に妥当だが、布かけ理由として"
                         "断定できる一次資料の確認は未実施。"
                         "限定表現：「ほこりよけも一因と考えられます」",
            },
            {
                "fact_id": "TV_CLOTH_003",
                "claim": "昭和30〜40年代、テレビは応接間や茶の間の中心に置かれ、"
                         "家具としての位置づけがあった",
                "status": "PARTIAL",
                "source_type": "生活文化史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "全国（都市部中心に普及）",
                "period_scope": "昭和30年代〜50年代（1955-1980頃）",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "テレビの設置場所は家庭の間取りや地域差がある。出典なし。"
                         "限定表現：「家庭によっては応接間の中心に置かれることもありました」",
            },
            {
                "fact_id": "TV_CLOTH_004",
                "claim": "テレビだけでなく、ミシンや電話機にも布カバーをかける習慣があった。"
                         "高価な物を大切にする意識があったと考えられる",
                "status": "PARTIAL",
                "source_type": "生活文化史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "direct",
                "regional_scope": "全国",
                "period_scope": "昭和全期",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "布カバー文化は家電に限らず広く存在したと言われるが"
                         "体系的な研究資料の確認は未実施。"
                         "限定表現：「高価な物を大切にする意識も一因と考えられます」",
            },
            {
                "fact_id": "TV_CLOTH_005",
                "claim": "テレビの技術は真空管方式からブラウン管（CRT）、"
                         "そして液晶・プラズマへと変遷した",
                "status": "PARTIAL",
                "source_type": "技術史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "全国（世界共通の技術変遷）",
                "period_scope": "昭和28年〜平成期",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "技術変遷自体は公知の事実だが、本ナレッジベースでは"
                         "出典URL・資料識別情報を保持していないためPARTIAL。"
                         "出典確認後にCONFIRMEDへ昇格可能",
            },
            {
                "fact_id": "TV_CLOTH_006",
                "claim": "NHKの本放送開始は1953年（昭和28年）。テレビ普及率は"
                         "1960年頃に約50%、1964年の東京オリンピック前後で約90%に達した",
                "status": "PARTIAL",
                "source_type": "放送史・統計",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "全国",
                "period_scope": "昭和28年〜40年代",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "NHK放送開始は公知の事実。普及率の数値は統計により差異あり。"
                         "本番用には総務省統計局またはNHK放送文化研究所の"
                         "一次資料での確認を推奨。"
                         "限定表現：「およそ90%に達したとされています」",
            },
            {
                "fact_id": "TV_CLOTH_007",
                "claim": "1980年代以降、テレビが安価になり一家に複数台が一般的になると、"
                         "布カバーをかける習慣は徐々に薄れたと言われている",
                "status": "PARTIAL",
                "source_type": "生活文化史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "direct",
                "regional_scope": "全国",
                "period_scope": "昭和50年代後半〜平成初期",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "布カバー習慣の衰退時期は家庭により異なる。出典なし。"
                         "限定表現：「家庭によっては、この頃から布をかけなくなったようです」",
            },
            {
                "fact_id": "TV_CLOTH_008",
                "claim": "初期のテレビ受像機は木製キャビネットに収められ、"
                         "高級家具のような外観だった",
                "status": "PARTIAL",
                "source_type": "工業デザイン史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "全国（世界共通の傾向）",
                "period_scope": "昭和28年〜40年代",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "初期テレビの木製筐体は博物館等の実物資料でも確認できるが、"
                         "本ナレッジベースでは出典URL未保持のためPARTIAL。"
                         "国立科学博物館等の資料で確認後にCONFIRMED昇格可能",
            },
            {
                "fact_id": "TV_CLOTH_009",
                "claim": "街頭テレビは1953年の放送開始直後に広まり、"
                         "力道山のプロレス中継が有名な契機となった",
                "status": "PARTIAL",
                "source_type": "放送文化史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "都市部中心",
                "period_scope": "昭和28年〜30年代前半",
                "usable_in_script": True,
                "script_expression": "limited",
                "notes": "街頭テレビの普及状況は地域差が大きい。出典なし。"
                         "限定表現：「街頭テレビが広まるきっかけの一つとされています」",
            },
            {
                "fact_id": "TV_CLOTH_010",
                "claim": "当時のテレビ修理は専門の技術者が家庭を訪問して行うのが一般的で、"
                         "故障は大きな出費を伴った",
                "status": "UNCONFIRMED",
                "source_type": "生活文化史",
                "source_name": "",
                "source_url": "",
                "source_date": "",
                "verified_excerpt": "",
                "verified_date": "",
                "evidence_type": "background",
                "regional_scope": "全国",
                "period_scope": "昭和30年代〜50年代",
                "usable_in_script": False,
                "script_expression": "prohibited",
                "notes": "当時を知る人の証言として語られるが、"
                         "体系的な資料での確認は未実施。台本使用不可",
            },
        ],
    },
}


def _match_topic_to_knowledge(topic):
    """Match topic string to knowledge base entries."""
    if "テレビ" in topic and "布" in topic:
        return KNOWLEDGE_BASE.get("テレビ_布")
    # Partial matches
    for key, value in KNOWLEDGE_BASE.items():
        parts = key.split("_")
        if any(p in topic for p in parts):
            return value
    return None


def attempt_web_research(topic):
    """
    Attempt web research for a topic.
    Returns list of additional facts or empty list on failure.
    """
    try:
        import requests
        # Try a simple connectivity check
        requests.get("https://www.google.com", timeout=5)
        logger.info("インターネット接続確認: 成功")
        # In a production system, this would call search APIs,
        # scrape authoritative sources, etc.
        # For now, we note that web research would be performed here.
        logger.info("Web研究機能: 将来のバージョンで検索API連携予定")
        return []
    except Exception as e:
        logger.warning(f"インターネット接続確認: 失敗 ({e})")
        logger.info("オフラインモードで内蔵知識ベースを使用します")
        return []


def research_topic(topic, mode="production"):
    """
    Research a topic and return structured facts.

    Args:
        topic: Topic string
        mode: "production" or "test"

    Returns:
        dict with:
            facts: list of fact dicts
            internet_available: bool
            research_method: str
            source_count: int
    """
    logger.info(f"リサーチ開始: {topic}")

    # Try web research
    web_facts = attempt_web_research(topic)
    internet_available = len(web_facts) > 0

    # Use built-in knowledge base
    knowledge = _match_topic_to_knowledge(topic)

    facts = []
    if knowledge:
        facts = [dict(f) for f in knowledge["facts"]]  # Deep copy
        logger.info(f"内蔵知識ベースから {len(facts)} 件の事実を取得")

    if web_facts:
        facts.extend(web_facts)

    # Add metadata about research method
    if not internet_available and not knowledge:
        logger.warning("インターネット未接続かつ内蔵知識なし: 一般的な構造のみ生成")
        facts = _generate_generic_research_structure(topic)

    if mode == "test":
        for fact in facts:
            if not fact.get("notes"):
                fact["notes"] = "テストモードで生成"

    research_method = "内蔵知識ベース"
    if internet_available:
        research_method = "Web研究 + 内蔵知識ベース"
    elif not knowledge:
        research_method = "一般的構造生成（知識ベース該当なし）"

    # Count unique sources
    source_names = set(f.get("source_name", "") for f in facts)
    source_names.discard("")

    return {
        "facts": facts,
        "internet_available": internet_available,
        "research_method": research_method,
        "source_count": len(source_names),
        "topic": topic,
    }


def _generate_generic_research_structure(topic):
    """Generate generic research structure for unknown topics."""
    return [
        {
            "fact_id": "GENERIC_001",
            "claim": f"「{topic}」に関する具体的な事実の確認が必要です",
            "status": "UNCONFIRMED",
            "source_type": "未調査",
            "source_name": "",
            "source_url": "",
            "source_date": "",
            "regional_scope": "不明",
            "period_scope": "不明",
            "usable_in_script": False,
            "notes": "インターネット未接続のため調査未実施。"
                     "オンライン環境で再実行してください",
        },
    ]


def fact_check(facts):
    """
    Perform fact-checking on research results.
    CONFIRMED requires: source_url AND source_name both non-empty.
    Without both, downgrade to PARTIAL regardless of content.
    """
    checked = []
    stats = {
        "CONFIRMED": 0,
        "PARTIAL": 0,
        "UNCONFIRMED": 0,
        "REJECTED": 0,
    }

    for fact in facts:
        status = fact.get("status", "UNCONFIRMED")

        if status == "CONFIRMED":
            has_url = bool(fact.get("source_url", "").strip())
            has_name = bool(fact.get("source_name", "").strip())
            if not (has_url and has_name):
                fact["status"] = "PARTIAL"
                status = "PARTIAL"
                fact["script_expression"] = "limited"
                fact.setdefault("notes", "")
                if fact["notes"]:
                    fact["notes"] += "。"
                fact["notes"] += "出典URL・出典名が未確認のためPARTIALへ降格"

        stats[status] = stats.get(status, 0) + 1
        checked.append(fact)

    logger.info(
        f"ファクトチェック完了: CONFIRMED={stats['CONFIRMED']}, "
        f"PARTIAL={stats['PARTIAL']}, UNCONFIRMED={stats['UNCONFIRMED']}, "
        f"REJECTED={stats['REJECTED']}"
    )

    return checked, stats


def write_research_outputs(output_dir, research_results, fact_stats):
    """Write research_report.md, fact_check.json, sources.csv."""
    os.makedirs(output_dir, exist_ok=True)
    facts = research_results["facts"]

    # research_report.md
    report_path = os.path.join(output_dir, "research_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# リサーチレポート\n\n")
        f.write(f"## トピック\n{research_results['topic']}\n\n")
        f.write(f"## 調査方法\n{research_results['research_method']}\n\n")
        f.write(f"## インターネット接続\n"
                f"{'利用可能' if research_results['internet_available'] else '利用不可'}\n\n")
        f.write(f"## 事実確認サマリー\n")
        f.write(f"- 確認済み (CONFIRMED): {fact_stats.get('CONFIRMED', 0)}件\n")
        f.write(f"- 部分確認 (PARTIAL): {fact_stats.get('PARTIAL', 0)}件\n")
        f.write(f"- 未確認 (UNCONFIRMED): {fact_stats.get('UNCONFIRMED', 0)}件\n")
        f.write(f"- 却下 (REJECTED): {fact_stats.get('REJECTED', 0)}件\n\n")
        f.write(f"## 優先情報源\n")
        for src in PRIORITY_SOURCES:
            f.write(f"- {src}\n")
        f.write(f"\n## 事実一覧\n\n")
        for fact in facts:
            usable = "○" if fact.get("usable_in_script") else "×"
            f.write(f"### {fact['fact_id']} [{fact['status']}] (脚本使用: {usable})\n")
            f.write(f"**主張**: {fact['claim']}\n\n")
            f.write(f"- 出典種別: {fact.get('source_type', '不明')}\n")
            f.write(f"- 出典名: {fact.get('source_name') or '未確認'}\n")
            if fact.get("source_url"):
                f.write(f"- URL: {fact['source_url']}\n")
            else:
                f.write(f"- URL: 未確認\n")
            f.write(f"- 根拠分類: {fact.get('evidence_type', '不明')}\n")
            f.write(f"- 脚本表現: {fact.get('script_expression', '不明')}\n")
            f.write(f"- 地域範囲: {fact.get('regional_scope', '不明')}\n")
            f.write(f"- 時代範囲: {fact.get('period_scope', '不明')}\n")
            if fact.get("verified_excerpt"):
                f.write(f"- 確認済み引用: {fact['verified_excerpt']}\n")
            if fact.get("verified_date"):
                f.write(f"- 確認日: {fact['verified_date']}\n")
            if fact.get("notes"):
                f.write(f"- 備考: {fact['notes']}\n")
            f.write("\n")

    # fact_check.json
    fact_check_path = os.path.join(output_dir, "fact_check.json")
    with open(fact_check_path, "w", encoding="utf-8") as f:
        json.dump({
            "topic": research_results["topic"],
            "research_method": research_results["research_method"],
            "internet_available": research_results["internet_available"],
            "generated_at": datetime.now().isoformat(),
            "stats": fact_stats,
            "facts": facts,
        }, f, ensure_ascii=False, indent=2)

    # sources.csv
    sources_path = os.path.join(output_dir, "sources.csv")
    with open(sources_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "fact_id", "status", "evidence_type", "script_expression",
            "source_type", "source_name", "source_url", "source_date",
            "verified_excerpt", "verified_date",
            "regional_scope", "period_scope",
        ])
        for fact in facts:
            writer.writerow([
                fact.get("fact_id", ""),
                fact.get("status", ""),
                fact.get("evidence_type", ""),
                fact.get("script_expression", ""),
                fact.get("source_type", ""),
                fact.get("source_name", ""),
                fact.get("source_url", ""),
                fact.get("source_date", ""),
                fact.get("verified_excerpt", ""),
                fact.get("verified_date", ""),
                fact.get("regional_scope", ""),
                fact.get("period_scope", ""),
            ])

    logger.info(f"リサーチ出力完了: {report_path}, {fact_check_path}, {sources_path}")
    return report_path, fact_check_path, sources_path


def run_researcher(topic, mode, output_dir):
    """
    Main entry point for the researcher module.

    Args:
        topic: Topic string
        mode: "production" or "test"
        output_dir: Output directory path

    Returns:
        dict with research_results, fact_stats, usable_facts, and output paths
    """
    research_results = research_topic(topic, mode)
    checked_facts, fact_stats = fact_check(research_results["facts"])
    research_results["facts"] = checked_facts

    # Filter usable facts for script writing
    usable_facts = [
        f for f in checked_facts
        if f.get("usable_in_script") and f.get("status") in ("CONFIRMED", "PARTIAL")
    ]

    report_path, fact_check_path, sources_path = write_research_outputs(
        output_dir, research_results, fact_stats
    )

    return {
        "research_results": research_results,
        "fact_stats": fact_stats,
        "usable_facts": usable_facts,
        "report_path": report_path,
        "fact_check_path": fact_check_path,
        "sources_path": sources_path,
    }
