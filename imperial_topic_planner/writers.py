"""各出力ファイルの生成."""

from . import config as cfg


def write_topic_candidates(candidates, output_dir):
    lines = [
        "# 企画候補一覧",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        f"対象視聴者: {cfg.TARGET_AUDIENCE}",
        "",
        f"候補数: {len(candidates)}本",
        "",
    ]
    for c in candidates:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append(f"- センターピン: {c['center_pin']}")
        lines.append(f"- 視聴者が見たい理由: {c['viewer_reason']}")
        lines.append(f"- 公式根拠候補:")
        for src in c.get("official_sources", []):
            lines.append(f"  - {src}")
        if not c.get("official_sources"):
            lines.append("  - （なし）")
        lines.append(f"- 長尺化できる理由: {c['long_reason']}")
        lines.append(f"- Shorts化できる理由: {c['shorts_reason']}")
        lines.append(f"- 想定される感情: {c['expected_emotion']}")
        lines.append(f"- 権利リスク: {c['rights_risk']}")
        lines.append(f"- 採点: {c['total_score']}点 / 100点")
        scores = c["scores"]
        for key, label in [
            ("viewer_fit", "視聴者適合性"),
            ("official_facts", "公式事実の強さ"),
            ("emotion", "感動要素"),
            ("rights_safety", "権利安全性"),
            ("long_video", "長尺化しやすさ"),
            ("shorts", "Shorts化しやすさ"),
            ("outsource", "外注しやすさ"),
        ]:
            lines.append(f"  - {label}: {scores[key]} / {cfg.SCORING_WEIGHTS[key]}")
        lines.append(f"- 判定: **{c['status']}**")
        if c.get("reject_reason"):
            lines.append(f"- 不採用理由: {c['reject_reason']}")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "01_topic_candidates.md").write_text(content, encoding="utf-8")


def write_selected_topics(selected, output_dir):
    lines = [
        "# 採用企画",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"採用数: {len(selected)}本",
        "",
    ]
    for c in selected:
        short_topic = c["title"].split("――")[0] if "――" in c["title"] else c["title"]
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append(f"### 正式企画タイトル")
        lines.append(f"{c['title']}")
        lines.append("")
        lines.append(f"### 長尺動画の方向性")
        lines.append(f"{c['long_reason']}")
        lines.append("")
        lines.append(f"### Shorts 3本の方向性")
        lines.append(f"1. {short_topic}の概要紹介（45〜60秒）")
        lines.append(f"2. 印象的な場面の切り出し（45〜60秒）")
        lines.append(f"3. 長尺動画への導線（45〜60秒）")
        lines.append("")
        lines.append(f"### 想定タイトル5案")
        lines.append(f"1. {c['title']}")
        lines.append(f"2. 【公式記録】{short_topic}")
        lines.append(f"3. {short_topic}｜静かに語られる記録")
        lines.append(f"4. 知っていますか？{short_topic}")
        lines.append(f"5. {short_topic}を丁寧に解説します")
        lines.append("")
        lines.append(f"### サムネ文言5案")
        lines.append(f"1. {short_topic}")
        lines.append(f"2. 公式記録で振り返る")
        lines.append(f"3. 心に残る一場面")
        lines.append(f"4. 受け継がれる思い")
        lines.append(f"5. 日本らしい気品")
        lines.append("")
        lines.append(f"### 冒頭30秒の方向性")
        lines.append(f"テーマの背景を簡潔に提示し、「今回は{short_topic}について、公式記録をもとにお伝えします」と導入する")
        lines.append("")
        lines.append(f"### 視聴維持の山場")
        lines.append(f"公式記録の中でも特に印象的な場面を中盤に配置し、視聴者の関心を維持する")
        lines.append("")
        lines.append(f"### ラストの余韻")
        lines.append(f"「{short_topic}の記録は、今も私たちの心に静かに語りかけています」のような余韻で締める")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "02_selected_topics.md").write_text(content, encoding="utf-8")


def write_rejected_topics(rejected, output_dir):
    lines = [
        "# 不採用企画",
        "",
        f"不採用数: {len(rejected)}本",
        "",
    ]
    for c in rejected:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append(f"- 採点: {c['total_score']}点 / 100点")
        lines.append(f"- 不採用理由: {c['reject_reason']}")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "03_rejected_topics.md").write_text(content, encoding="utf-8")


def write_fact_source_plan(selected, output_dir):
    lines = [
        "# 出典・情報源計画",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        "",
        "## 優先情報源",
        "",
    ]
    for src in cfg.PRIORITY_SOURCES:
        lines.append(f"- {src}")
    lines.append("")
    lines.append("※ 未確認の情報は「未確認」と明記する。推測で埋めない。")
    lines.append("")

    for c in selected:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append("### 確認すべき情報源")
        lines.append("")
        source_categories = {
            "宮内庁": [],
            "公式SNS": [],
            "公的機関": [],
            "報道": [],
            "自治体": [],
            "海外王室公式": [],
            "その他": [],
        }
        for src in c.get("official_sources", []):
            if "宮内庁" in src and ("YouTube" in src or "Instagram" in src):
                source_categories["公式SNS"].append(src)
            elif "宮内庁" in src:
                source_categories["宮内庁"].append(src)
            elif any(k in src for k in ["外務省", "首相官邸", "環境省", "文化庁", "博物館", "大学"]):
                source_categories["公的機関"].append(src)
            elif any(k in src for k in ["NHK", "報道", "日テレ", "朝日", "読売", "毎日", "産経", "共同"]):
                source_categories["報道"].append(src)
            elif any(k in src for k in ["自治体"]):
                source_categories["自治体"].append(src)
            elif any(k in src for k in ["王室", "大使館", "英国"]):
                source_categories["海外王室公式"].append(src)
            else:
                source_categories["その他"].append(src)

        for cat, sources in source_categories.items():
            if sources:
                lines.append(f"- {cat}:")
                for s in sources:
                    lines.append(f"  - {s}")
            else:
                lines.append(f"- {cat}: 未確認")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "04_fact_source_plan.md").write_text(content, encoding="utf-8")


def write_long_video_plan(selected, output_dir):
    lines = [
        "# 長尺動画構成案",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        "",
    ]
    for c in selected:
        short_topic = c["title"].split("――")[0] if "――" in c["title"] else c["title"]
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append("### 構成")
        lines.append("")
        lines.append(f"1. **冒頭**: テーマの導入。「今回は{short_topic}について、公式記録をもとにお伝えします」")
        lines.append(f"2. **背景**: {c['center_pin']}の背景を解説")
        lines.append(f"3. **公式事実**: 公式記録に基づく事実を時系列で紹介")
        lines.append(f"4. **印象的な場面**: 公式記録の中でも特に心に残る場面を丁寧に描写")
        lines.append(f"5. **視聴者が共感するポイント**: {c['expected_emotion']}を喚起する構成")
        lines.append(f"6. **現在とのつながり**: 過去の記録が現在にどうつながっているかを示す")
        lines.append(f"7. **静かな余韻**: 穏やかなまとめで締めくくる")
        lines.append("")
        lines.append(f"### 想定尺")
        lines.append(f"7〜9分")
        lines.append("")
        lines.append(f"### 素材方針")
        lines.append(f"- テロップ・テキストカード中心")
        lines.append(f"- 公式記録の引用表示")
        lines.append(f"- 人物写真は使用しない（肖像権リスク回避）")
        lines.append(f"- 和風背景・単色背景を使用")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "05_long_video_plan.md").write_text(content, encoding="utf-8")


def write_shorts_plan(selected, output_dir):
    lines = [
        "# Shorts構成案",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        "",
    ]
    for c in selected:
        short_topic = c["title"].split("――")[0] if "――" in c["title"] else c["title"]
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        for i in range(1, 4):
            if i == 1:
                s_title = f"{short_topic}とは"
                hook = f"「{short_topic}」をご存知ですか？"
                body = "テーマの概要を簡潔に紹介し、公式記録の要点を伝える"
                last_word = "詳しくは関連動画からご覧ください"
            elif i == 2:
                s_title = f"{short_topic}の印象的な場面"
                hook = "公式記録に残る、心に残る一場面があります"
                body = "最も印象的なエピソードを一つ取り上げ、背景とともに紹介"
                last_word = "この記録は、今も多くの人の心に残っています"
            else:
                s_title = f"{short_topic}が伝えること"
                hook = "この記録が私たちに伝えることとは"
                body = "テーマの意義をまとめ、長尺動画への関心を喚起する"
                last_word = "長尺動画では、さらに詳しくお伝えしています"

            lines.append(f"### Shorts {i}: {s_title}")
            lines.append("")
            lines.append(f"- Shortsタイトル: {s_title}")
            lines.append(f"- 冒頭1秒の引き: {hook}")
            lines.append(f"- 本文構成: {body}")
            lines.append(f"- 最後の一言: {last_word}")
            lines.append(f"- 長尺への導線: 概要欄に長尺動画リンクを設置")
            lines.append(f"- 45〜60秒で成立する理由: 一つのポイントに絞り、テロップで補足するため尺内に収まる")
            lines.append("")

    content = "\n".join(lines)
    (output_dir / "06_shorts_plan.md").write_text(content, encoding="utf-8")


def write_title_thumbnail_plan(selected, output_dir):
    lines = [
        "# タイトル・サムネイル案",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        "",
        "## 禁止表現",
        "",
    ]
    for expr in cfg.PROHIBITED_EXPRESSIONS[:10]:
        lines.append(f"- {expr}")
    lines.append("")
    lines.append("## 推奨表現")
    lines.append("")
    for expr in cfg.RECOMMENDED_EXPRESSIONS:
        lines.append(f"- {expr}")
    lines.append("")

    for c in selected:
        short_topic = c["title"].split("――")[0] if "――" in c["title"] else c["title"]
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append("### 長尺用タイトル案（5本）")
        lines.append("")
        lines.append(f"1. {c['title']}")
        lines.append(f"2. 【公式記録】{short_topic}")
        lines.append(f"3. {short_topic}｜静かに語られる記録")
        lines.append(f"4. 知っていますか？{short_topic}")
        lines.append(f"5. {short_topic}を丁寧に解説します")
        lines.append("")
        lines.append("### サムネ文言（5本）")
        lines.append("")
        lines.append(f"1. {short_topic}")
        lines.append(f"2. 公式記録で振り返る")
        lines.append(f"3. 心に残る一場面")
        lines.append(f"4. 受け継がれる思い")
        lines.append(f"5. 日本らしい気品")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "07_title_thumbnail_plan.md").write_text(content, encoding="utf-8")


def write_risk_check_report(selected, output_dir):
    lines = [
        "# リスクチェックレポート",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        "",
    ]
    for c in selected:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")

        risk_level = c.get("rights_risk", "未評価")
        is_low = risk_level.startswith("低")
        is_mid = risk_level.startswith("中")

        risk_assessments = {
            "事実誤認リスク": "低（公式記録に基づく）" if c["scores"]["official_facts"] >= 15 else "中（追加確認が必要）",
            "権利リスク": risk_level,
            "収益化リスク": "低（広告適合性に問題なし）" if is_low else "中（慎重な構成が必要）",
            "炎上リスク": "低（中立的な構成）" if is_low else "中（対立軸に注意）",
            "高齢視聴者との不一致": "低（視聴者適合性が高い）" if c["scores"]["viewer_fit"] >= 16 else "中（視聴者層を意識した構成が必要）",
            "外注者の作業負担": "低（テロップ中心で素材探しが容易）" if c["scores"]["outsource"] >= 8 else "中（素材指示を明確にする必要あり）",
            "素材調達難易度": "低（公式記録・テロップで構成可能）" if is_low else "中（一部素材の確認が必要）",
        }

        for category in cfg.RISK_CATEGORIES:
            assessment = risk_assessments.get(category, "未評価")
            lines.append(f"- {category}: {assessment}")
        lines.append("")

        overall = "低" if all("低" in v for v in risk_assessments.values()) else "中"
        lines.append(f"- **総合リスク判定: {overall}**")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "08_risk_check_report.md").write_text(content, encoding="utf-8")


def write_package_summary(selected, rejected, mode, output_dir):
    priority_topics = [c for c in selected if c["total_score"] >= cfg.PRIORITY_THRESHOLD]
    normal_topics = [c for c in selected if c["total_score"] < cfg.PRIORITY_THRESHOLD]

    has_prohibited_in_selected = any(c["has_prohibited"] for c in selected)
    has_empty_sources = any(not c.get("official_sources") for c in selected)
    has_below_threshold = any(c["total_score"] < cfg.PASS_THRESHOLD for c in selected)

    package_complete = (
        len(selected) > 0
        and not has_prohibited_in_selected
        and not has_empty_sources
        and not has_below_threshold
    )

    production_ready = (
        package_complete
        and mode == "production"
    )

    lines = [
        "# 企画パッケージ概要",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        f"モード: {mode}",
        "",
        "## 結果サマリ",
        "",
        f"- 採用企画数: {len(selected)}本",
        f"- 保留企画数: 0本",
        f"- 不採用企画数: {len(rejected)}本",
        "",
        "## 判定",
        "",
        f"- package_complete: {package_complete}",
        f"- production_ready: {production_ready}",
        "",
    ]

    if priority_topics:
        lines.append("## 最優先で制作すべき企画")
        lines.append("")
        for c in priority_topics[:3]:
            lines.append(f"- {c['id']}: {c['title']}（{c['total_score']}点）")
        lines.append("")
        lines.append(f"理由: {cfg.PRIORITY_THRESHOLD}点以上の高採点で、公式事実が豊富、権利リスクが低く、すぐに制作着手できる")
        lines.append("")

    if normal_topics:
        lines.append("## 次に制作すべき企画")
        lines.append("")
        for c in normal_topics:
            lines.append(f"- {c['id']}: {c['title']}（{c['total_score']}点）")
        lines.append("")
        lines.append(f"理由: {cfg.PASS_THRESHOLD}点以上だが、優先企画の制作後に着手するのが効率的")
        lines.append("")

    if rejected:
        lines.append("## 制作を見送った企画")
        lines.append("")
        for c in rejected:
            lines.append(f"- {c['id']}: {c['title']}（{c['total_score']}点）― {c['reject_reason']}")
        lines.append("")

    content = "\n".join(lines)
    (output_dir / "09_package_summary.md").write_text(content, encoding="utf-8")

    return {
        "package_complete": package_complete,
        "production_ready": production_ready,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
    }
