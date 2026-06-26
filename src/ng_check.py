"""NG expression and content checker.

Scans script text, title candidates, and descriptions for prohibited
expressions, inner-feelings assertions, exaggeration, factual errors,
and other policy violations.
"""

import re
from pathlib import Path

import config as cfg


# ---------------------------------------------------------------------------
# Extended prohibited patterns (beyond config.PROHIBITED_EXPRESSIONS)
# ---------------------------------------------------------------------------

EXTRA_PROHIBITED_EXPRESSIONS = [
    "世界が絶賛",
    "神対応",
    "衝撃",
    "激震",
    "日本中が涙",
    "世界が震えた",
    "全米が泣いた",
    "前代未聞",
    "歴史的快挙",
    "大スクープ",
    "独占入手",
    "関係者激白",
    "極秘情報",
    "禁断の真実",
    "闇に葬られた",
]

INNER_FEELINGS_PATTERNS = [
    "胸を痛めた",
    "涙をこらえた",
    "心から願っていた",
    "密かに決意した",
    "内心では",
    "本心では",
    "心の中で",
    "実は.*望んでい",
    ".*は激怒している",
    "密かに喜んでいた",
    "本心は.*だった",
]

CONFRONTATION_PATTERNS = [
    r".*vs\s*.*",
    r".*VS\s*.*",
    r".*対\s*.*の確執",
    r".*を批判",
    r".*を攻撃",
    r".*の陰謀",
    r".*が仕組んだ",
]


def _is_in_quoted_block(text, pos):
    """Return True if *pos* falls inside a 『…』 or 「…」 quoted block."""
    for open_ch, close_ch in [("『", "』"), ("「", "」")]:
        depth = 0
        for i, ch in enumerate(text):
            if i == pos and depth > 0:
                return True
            if ch == open_ch:
                depth += 1
            elif ch == close_ch and depth > 0:
                depth -= 1
    return False


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

def check_ng_expressions(script_text, title_candidates, description,
                         output_dir, research_data=None):
    """Check all text content for NG expressions and policy violations.

    Parameters
    ----------
    script_text : str
        Full script / narration text.
    title_candidates : list[str]
        Candidate titles for the video.
    description : str
        YouTube description text.
    output_dir : str | Path
        Directory to write the report into.
    research_data : dict, optional
        Research data for cross-checking facts (dates, places, names).

    Returns
    -------
    dict
        Results with ``findings`` list, ``has_fail``, ``has_review``,
        ``pass_count``, ``fail_count``, ``review_count``.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if research_data is None:
        research_data = {}

    findings = []

    # Combine all prohibited expressions
    all_prohibited = list(cfg.PROHIBITED_EXPRESSIONS) + EXTRA_PROHIBITED_EXPRESSIONS

    # Combine all inner-feelings patterns
    all_inner = list(cfg.NG_INNER_FEELINGS) + INNER_FEELINGS_PATTERNS

    # --- Check each text source ---
    text_sources = [
        ("script", script_text),
        ("description", description),
    ]
    for idx, title in enumerate(title_candidates):
        text_sources.append((f"title_candidate_{idx + 1}", title))

    for location, text in text_sources:
        if not text:
            continue

        # 1. Prohibited expressions
        for expr in all_prohibited:
            if expr in text:
                findings.append({
                    "item": expr,
                    "location": location,
                    "category": "禁止表現",
                    "verdict": "FAIL",
                    "detail": f"禁止表現「{expr}」が含まれています。削除または言い換えが必要です。",
                })

        # 2. Inner feelings assertions
        for pattern in all_inner:
            if re.search(pattern, text):
                match = re.search(pattern, text)
                matched_text = match.group(0) if match else pattern
                findings.append({
                    "item": matched_text,
                    "location": location,
                    "category": "内心描写",
                    "verdict": "FAIL",
                    "detail": (
                        f"皇族の内心を断定する表現「{matched_text}」が含まれています。"
                        "公式に確認できない内面描写は禁止です。"
                    ),
                })

        # 3. Exaggeration patterns
        exaggeration_patterns = [
            r"史上[最初]",
            r"日本[一初]の",
            r"世界[一初]の",
            r"誰もが.*した",
            r"全[国民員]が",
            r"空前の",
            r"前例のない",
        ]
        for pattern in exaggeration_patterns:
            if re.search(pattern, text):
                match = re.search(pattern, text)
                matched_text = match.group(0) if match else pattern
                findings.append({
                    "item": matched_text,
                    "location": location,
                    "category": "誇張表現",
                    "verdict": "REVIEW",
                    "detail": (
                        f"誇張の可能性がある表現「{matched_text}」。"
                        "事実に基づく表現か確認してください。"
                    ),
                })

        # 4. Confrontation / attack patterns
        for pattern in CONFRONTATION_PATTERNS:
            if re.search(pattern, text):
                match = re.search(pattern, text)
                matched_text = match.group(0) if match else pattern
                findings.append({
                    "item": matched_text,
                    "location": location,
                    "category": "対立・攻撃表現",
                    "verdict": "FAIL",
                    "detail": (
                        f"特定の皇族への対立・攻撃的表現「{matched_text}」。"
                        "チャンネル方針に反します。"
                    ),
                })

        # 5. Speculation markers mixed with facts
        speculation_markers = [
            "と思われる",
            "と見られている",
            "という噂",
            "関係者によると",
            "情報筋によれば",
        ]
        for marker in speculation_markers:
            if marker in text:
                findings.append({
                    "item": marker,
                    "location": location,
                    "category": "事実と推測の混在",
                    "verdict": "REVIEW",
                    "detail": (
                        f"推測表現「{marker}」が使用されています。"
                        "事実と推測を明確に区別してください。"
                    ),
                })

        # 6. Disrespect check — missing honorifics for imperial family
        disrespect_patterns = [
            (r"(?<!「)天皇(?!陛下|皇后|の|」)", "天皇陛下"),
            (r"(?<!「)皇后(?!陛下|両陛下|の|」)", "皇后陛下"),
            (r"(?<!「)愛子(?!さま|内親王|殿下|」)", "愛子さま / 愛子内親王殿下"),
        ]
        for pattern, correct in disrespect_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = match.start()
                end = match.end()
                if _is_in_quoted_block(text, start):
                    continue
                context_before = text[max(0, start - 20):start]
                context_after = text[end:end + 10]
                if "「" in context_before or "」" in context_after:
                    continue
                if "御名" in context_before or "御称号" in context_before:
                    continue
                if "命名" in context_before:
                    continue
                if "名前" in context_before:
                    continue
                matched_text = match.group(0)
                findings.append({
                    "item": matched_text,
                    "location": location,
                    "category": "敬称・敬語",
                    "verdict": "REVIEW",
                    "detail": (
                        f"「{matched_text}」に敬称が不足している可能性があります。"
                        f"正しくは「{correct}」等の敬称を使用してください。"
                    ),
                })

    # 7. Missing attribution check
    if script_text and "出典" not in script_text and "参考" not in script_text:
        findings.append({
            "item": "出典表記",
            "location": "script",
            "category": "出典未記載",
            "verdict": "REVIEW",
            "detail": "台本内に出典・参考文献への言及がありません。引用がある場合は出典を明記してください。",
        })

    # 8. Title-content consistency
    META_TERMS = {"解説", "丁寧", "わかりやすく", "意外な", "背景", "知らない", "知っておきたい"}
    if title_candidates and script_text:
        for idx, title in enumerate(title_candidates):
            title_terms = [t for t in re.findall(r'[一-鿿぀-ゟ゠-ヿ]{3,}', title)
                           if t not in META_TERMS
                           and not any(m in t for m in META_TERMS)]
            missing_terms = [t for t in title_terms if t not in script_text]
            if len(missing_terms) > len(title_terms) // 2 and title_terms:
                findings.append({
                    "item": f"タイトル候補{idx + 1}",
                    "location": f"title_candidate_{idx + 1}",
                    "category": "タイトルと内容の不一致",
                    "verdict": "REVIEW",
                    "detail": (
                        f"タイトル「{title}」のキーワードが台本に不足しています。"
                        f"不足: {', '.join(missing_terms)}"
                    ),
                })

    # 9. Date/place cross-check with research_data
    facts = research_data.get("facts", [])
    for fact in facts:
        status = fact.get("status", "")
        text_snippet = fact.get("text", "")
        if status in (cfg.FactStatus.UNCONFIRMED, cfg.FactStatus.REJECTED):
            if text_snippet and text_snippet in script_text:
                verdict = "FAIL" if status == cfg.FactStatus.REJECTED else "REVIEW"
                findings.append({
                    "item": text_snippet,
                    "location": "script",
                    "category": "日付・場所の正確性",
                    "verdict": verdict,
                    "detail": (
                        f"ファクトチェックで「{status}」と判定された内容が"
                        "台本に含まれています。確認または削除が必要です。"
                    ),
                })

    # --- Tally results ---
    has_fail = any(f["verdict"] == "FAIL" for f in findings)
    has_review = any(f["verdict"] == "REVIEW" for f in findings)
    fail_count = sum(1 for f in findings if f["verdict"] == "FAIL")
    review_count = sum(1 for f in findings if f["verdict"] == "REVIEW")
    pass_count = sum(1 for f in findings if f["verdict"] == "PASS")

    result = {
        "findings": findings,
        "has_fail": has_fail,
        "has_review": has_review,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "review_count": review_count,
        "total_checks": len(findings),
        "package_blocked": has_fail,
    }

    # Write report
    _write_ng_report(result, output_dir)

    return result


def _write_ng_report(result, output_dir):
    """Write ``ng_expression_report.md`` summarising all findings."""
    output_dir = Path(output_dir)

    lines = [
        "# NG表現チェックレポート",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        "",
        "## サマリ",
        "",
        f"- 総チェック項目数: {result['total_checks']}",
        f"- FAIL: {result['fail_count']}",
        f"- REVIEW: {result['review_count']}",
        f"- PASS: {result['pass_count']}",
        f"- パッケージ完成可否: {'**不可（FAILあり）**' if result['package_blocked'] else 'OK'}",
        "",
    ]

    if result["findings"]:
        # Group by category
        categories = {}
        for f in result["findings"]:
            cat = f["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f)

        for cat, items in categories.items():
            lines.append(f"## {cat}")
            lines.append("")
            for item in items:
                mark = {"FAIL": "FAIL", "REVIEW": "REVIEW", "PASS": "PASS"}.get(
                    item["verdict"], "?"
                )
                lines.append(f"### [{mark}] {item['item']}")
                lines.append("")
                lines.append(f"- 検出場所: {item['location']}")
                lines.append(f"- 判定: **{mark}**")
                lines.append(f"- 詳細: {item['detail']}")
                lines.append("")
    else:
        lines += [
            "## 検出結果",
            "",
            "NG表現は検出されませんでした。",
            "",
        ]

    lines += [
        "## 判定基準",
        "",
        "- **FAIL**: パッケージに含めることができません。修正が必須です。",
        "- **REVIEW**: 確認が必要です。問題がなければ続行可能です。",
        "- **PASS**: 問題ありません。",
        "",
        "## 注意事項",
        "",
        "- FAILが1件でもある場合、パッケージは未完成と判定されます",
        "- 皇族の内心を断定する表現は一律禁止です",
        "- 事実と推測を混在させないでください",
        "- 敬称の省略に注意してください",
        "",
    ]

    report_path = output_dir / "ng_expression_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
