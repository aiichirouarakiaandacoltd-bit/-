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

IMPERIAL_HONORIFIC_RULES = [
    {
        "name": "愛子",
        "pattern": r"(?<!「)愛子(?!さま|内親王|殿下|」)",
        "correct": "愛子さま / 愛子内親王殿下",
        "first_fix": "愛子内親王殿下",
        "subsequent_fix": "愛子さま",
        "context_skip": ["御名", "御称号", "命名", "名前"],
    },
    {
        "name": "雅子",
        "pattern": r"(?<!「)雅子(?!さま|皇后|陛下|妃|殿下|」)",
        "correct": "雅子さま / 雅子皇后陛下",
        "first_fix": "雅子皇后陛下",
        "subsequent_fix": "雅子さま",
        "context_skip": ["御名", "名前"],
    },
    {
        "name": "徳仁",
        "pattern": r"(?<!「)徳仁(?!天皇|陛下|親王|殿下|」)",
        "correct": "徳仁天皇陛下",
        "first_fix": "徳仁天皇陛下",
        "subsequent_fix": "徳仁天皇陛下",
        "context_skip": ["御名", "名前"],
    },
    {
        "name": "佳子",
        "pattern": r"(?<!「)佳子(?!さま|内親王|殿下|」)",
        "correct": "佳子さま / 佳子内親王殿下",
        "first_fix": "佳子内親王殿下",
        "subsequent_fix": "佳子さま",
        "context_skip": ["御名", "名前"],
    },
    {
        "name": "眞子",
        "pattern": r"(?<!「)眞子(?!さま|内親王|殿下|さん|」)",
        "correct": "眞子さま / 眞子内親王殿下",
        "first_fix": "眞子内親王殿下",
        "subsequent_fix": "眞子さま",
        "context_skip": ["御名", "名前"],
    },
    {
        "name": "悠仁",
        "pattern": r"(?<!「)悠仁(?!さま|親王|殿下|」)",
        "correct": "悠仁さま / 悠仁親王殿下",
        "first_fix": "悠仁親王殿下",
        "subsequent_fix": "悠仁さま",
        "context_skip": ["御名", "名前"],
    },
    {
        "name": "秋篠宮",
        "pattern": r"(?<!「)秋篠宮(?!さま|殿下|皇嗣|家|の|」)",
        "correct": "秋篠宮さま / 秋篠宮皇嗣殿下",
        "first_fix": "秋篠宮皇嗣殿下",
        "subsequent_fix": "秋篠宮さま",
        "context_skip": [],
    },
    {
        "name": "紀子",
        "pattern": r"(?<!「)紀子(?!さま|妃|殿下|」)",
        "correct": "紀子さま / 紀子妃殿下",
        "first_fix": "紀子妃殿下",
        "subsequent_fix": "紀子さま",
        "context_skip": ["御名", "名前"],
    },
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
        general_patterns = [
            (r"(?<!「)天皇(?!陛下|皇后|の|」)", "天皇陛下"),
            (r"(?<!「)皇后(?!陛下|両陛下|の|」)", "皇后陛下"),
        ]
        for pattern, correct in general_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = match.start()
                if _is_in_quoted_block(text, start):
                    continue
                context_before = text[max(0, start - 20):start]
                context_after = text[match.end():match.end() + 10]
                if "「" in context_before or "」" in context_after:
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

        for rule in IMPERIAL_HONORIFIC_RULES:
            matches = list(re.finditer(rule["pattern"], text))
            for match in matches:
                start = match.start()
                if _is_in_quoted_block(text, start):
                    continue
                context_before = text[max(0, start - 20):start]
                context_after = text[match.end():match.end() + 10]
                if "「" in context_before or "」" in context_after:
                    continue
                skip = False
                for ctx in rule["context_skip"]:
                    if ctx in context_before:
                        skip = True
                        break
                if "御称号" in context_before:
                    skip = True
                if skip:
                    continue
                matched_text = match.group(0)
                findings.append({
                    "item": matched_text,
                    "location": location,
                    "category": "敬称・敬語",
                    "verdict": "REVIEW",
                    "detail": (
                        f"「{matched_text}」に敬称が不足している可能性があります。"
                        f"正しくは「{rule['correct']}」等の敬称を使用してください。"
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

    # 10. Shorts content duplication check
    shorts_texts = []
    for key in ("shorts_01_text", "shorts_02_text"):
        st = research_data.get(key, "")
        if st:
            shorts_texts.append(st)
    if len(shorts_texts) == 2:
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, shorts_texts[0], shorts_texts[1]).ratio()
        if ratio > 0.7:
            findings.append({
                "item": "Shorts①②内容重複",
                "location": "shorts",
                "category": "Shorts重複",
                "verdict": "REVIEW",
                "detail": f"Shorts①と②の類似度が{ratio:.0%}です。内容の差別化を確認してください。",
            })
        else:
            findings.append({
                "item": "Shorts①②内容重複",
                "location": "shorts",
                "category": "Shorts重複",
                "verdict": "PASS",
                "detail": f"Shorts①と②の類似度は{ratio:.0%}で、十分に差別化されています。",
            })
    elif script_text:
        findings.append({
            "item": "Shorts①②内容重複",
            "location": "shorts",
            "category": "Shorts重複",
            "verdict": "PASS",
            "detail": "Shorts台本が1本以下のため重複チェック不要。",
        })

    # 11. Excessive repetition check
    if script_text:
        phrase_counts = {}
        for line in script_text.split("\n"):
            stripped = line.strip()
            if len(stripped) >= 8:
                for other_line in script_text.split("\n"):
                    if other_line.strip() == stripped and stripped:
                        phrase_counts[stripped] = phrase_counts.get(stripped, 0) + 1
        repeated = {k: v for k, v in phrase_counts.items() if v >= 4 and not k.startswith("【") and k != "=" * 60}
        if repeated:
            for phrase, count in list(repeated.items())[:3]:
                findings.append({
                    "item": f"反復: {phrase[:30]}",
                    "location": "script",
                    "category": "同一表現過剰反復",
                    "verdict": "REVIEW",
                    "detail": f"「{phrase[:40]}」が{count}回繰り返されています。",
                })
        else:
            findings.append({
                "item": "同一表現過剰反復",
                "location": "script",
                "category": "同一表現過剰反復",
                "verdict": "PASS",
                "detail": "過剰な表現反復は検出されませんでした。",
            })

    # 12. AI person image instruction check
    if script_text:
        ai_image_patterns = ["AI生成.*人物", "AI.*肖像", "AIで.*顔"]
        ai_found = False
        for pattern in ai_image_patterns:
            if re.search(pattern, script_text):
                ai_found = True
                findings.append({
                    "item": pattern,
                    "location": "script",
                    "category": "AI人物画像指示",
                    "verdict": "FAIL",
                    "detail": "台本内にAI生成人物画像の指示が含まれています。",
                })
        if not ai_found:
            findings.append({
                "item": "AI人物画像指示",
                "location": "script",
                "category": "AI人物画像指示",
                "verdict": "PASS",
                "detail": "AI生成人物画像の指示は検出されませんでした。",
            })

    # Add PASS findings for categories that had no issues
    checked_categories = {f["category"] for f in findings}

    if "禁止表現" not in checked_categories and script_text:
        findings.append({
            "item": "禁止表現チェック",
            "location": "全体",
            "category": "禁止表現",
            "verdict": "PASS",
            "detail": "禁止表現は検出されませんでした。",
        })

    if "内心描写" not in checked_categories and script_text:
        findings.append({
            "item": "内心描写チェック",
            "location": "全体",
            "category": "内心描写",
            "verdict": "PASS",
            "detail": "皇族の内心断定表現は検出されませんでした。",
        })

    if "誇張表現" not in checked_categories and script_text:
        findings.append({
            "item": "誇張表現チェック",
            "location": "全体",
            "category": "誇張表現",
            "verdict": "PASS",
            "detail": "誇張表現は検出されませんでした。",
        })

    if "対立・攻撃表現" not in checked_categories and script_text:
        findings.append({
            "item": "対立・攻撃表現チェック",
            "location": "全体",
            "category": "対立・攻撃表現",
            "verdict": "PASS",
            "detail": "対立・攻撃的表現は検出されませんでした。",
        })

    if "事実と推測の混在" not in checked_categories and script_text:
        findings.append({
            "item": "事実と推測の混在チェック",
            "location": "全体",
            "category": "事実と推測の混在",
            "verdict": "PASS",
            "detail": "推測表現の混在は検出されませんでした。",
        })

    if "敬称・敬語" not in checked_categories and script_text:
        findings.append({
            "item": "敬称・敬語チェック",
            "location": "全体",
            "category": "敬称・敬語",
            "verdict": "PASS",
            "detail": "敬称の不足は検出されませんでした。",
        })

    # --- Tally results ---
    has_fail = any(f["verdict"] == "FAIL" for f in findings)
    has_review = any(f["verdict"] == "REVIEW" for f in findings)
    fail_count = sum(1 for f in findings if f["verdict"] == "FAIL")
    review_count = sum(1 for f in findings if f["verdict"] == "REVIEW")
    pass_count = sum(1 for f in findings if f["verdict"] == "PASS")
    total_checks = len(findings)

    result = {
        "findings": findings,
        "has_fail": has_fail,
        "has_review": has_review,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "review_count": review_count,
        "total_checks": total_checks,
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


def auto_fix_honorifics(text):
    """Auto-fix missing honorifics in text.

    First occurrence of each name uses the formal form (e.g. 愛子内親王殿下),
    subsequent occurrences use the shorter form (e.g. 愛子さま).
    Names in quoted blocks or preceded by context words like 御名/御称号 are
    left unchanged.
    """
    fixed = text
    for rule in IMPERIAL_HONORIFIC_RULES:
        replacements = []
        first_done = False
        for match in re.finditer(rule["pattern"], fixed):
            start = match.start()
            if _is_in_quoted_block(fixed, start):
                continue
            context_before = fixed[max(0, start - 20):start]
            context_after = fixed[match.end():match.end() + 10]
            if "「" in context_before or "」" in context_after:
                continue
            skip = False
            for ctx in rule["context_skip"]:
                if ctx in context_before:
                    skip = True
                    break
            if "御称号" in context_before:
                skip = True
            if skip:
                continue
            replacement = rule["first_fix"] if not first_done else rule["subsequent_fix"]
            replacements.append((match.start(), match.end(), replacement))
            first_done = True
        for start, end, replacement in reversed(replacements):
            fixed = fixed[:start] + replacement + fixed[end:]
    return fixed
