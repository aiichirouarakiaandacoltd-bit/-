"""各出力ファイルの生成."""

import json

from . import config as cfg


SCORE_LABELS = [
    ("demand", "需要スコア"),
    ("competitor_growth", "競合伸長スコア"),
    ("reproducibility", "少登録者でも伸びる再現性"),
    ("channel_fit", "皇室チャンネル適合性"),
    ("official_evidence", "公式根拠の有無"),
    ("rights_safety", "権利リスク"),
    ("senior_fit", "65歳以上女性への適合性"),
    ("long_video", "長尺化可否"),
    ("shorts_potential", "Shorts展開可否"),
    ("production_cost", "推定制作コスト"),
]


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
        "## スコアリング基準",
        "",
        "- YouTube需要指標（CTR・平均視聴時間・リピーター率・Shorts→長尺導線）を重視",
        "- 少登録者チャンネルでも伸びた実績を再現性として評価",
        "- 公式根拠なし・権利リスク高・煽り依存は自動不採用",
        "",
    ]
    for c in candidates:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append(f"- センターピン: {c['center_pin']}")
        lines.append(f"- テーマキーワード: {', '.join(c.get('theme_keywords', []))}")
        lines.append(f"- 視聴者が見たい理由: {c['viewer_reason']}")
        lines.append(f"- 参考動画マッチ数: {c.get('matched_reference_count', 0)}本")
        lines.append(f"- 公式根拠候補:")
        for src in c.get("official_sources", []):
            lines.append(f"  - {src}")
        if not c.get("official_sources"):
            lines.append("  - （なし）")
        lines.append(f"- 長尺化: {c.get('long_reason', '未設定')}")
        lines.append(f"- Shorts展開: {c.get('shorts_reason', '未設定')}")
        lines.append(f"- 想定される感情: {c['expected_emotion']}")
        lines.append(f"- 権利リスク: {c['rights_risk']}")
        lines.append(f"- **合計: {c['total_score']}点 / 100点**")
        scores = c["scores"]
        for key, label in SCORE_LABELS:
            lines.append(f"  - {label}: {scores.get(key, 0)} / 10")
        lines.append(f"- 判定: **{c['status']}**")
        if c.get("reject_reason"):
            lines.append(f"- 理由: {c['reject_reason']}")
        lines.append("")

    (output_dir / "01_topic_candidates.md").write_text("\n".join(lines), encoding="utf-8")


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
        lines.append(f"### 採用根拠")
        lines.append(f"- 合計スコア: {c['total_score']}点")
        lines.append(f"- 需要スコア: {c['scores'].get('demand', 0)}")
        lines.append(f"- 競合伸長: {c['scores'].get('competitor_growth', 0)}")
        lines.append(f"- 再現性: {c['scores'].get('reproducibility', 0)}")
        lines.append(f"- 参考動画マッチ: {c.get('matched_reference_count', 0)}本")
        lines.append("")
        lines.append(f"### 長尺動画の方向性")
        lines.append(f"{c.get('long_reason', '')}")
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

    (output_dir / "02_selected_topics.md").write_text("\n".join(lines), encoding="utf-8")


def write_rejected_topics(rejected, held, output_dir):
    lines = [
        "# 不採用・保留企画",
        "",
    ]
    if held:
        lines.append(f"## 保留企画（{len(held)}本）")
        lines.append("")
        for c in held:
            lines.append(f"### {c['id']}: {c['title']}")
            lines.append(f"- 採点: {c['total_score']}点 / 100点")
            lines.append(f"- 理由: {c.get('reject_reason', '')}")
            lines.append("")

    lines.append(f"## 不採用企画（{len(rejected)}本）")
    lines.append("")
    for c in rejected:
        lines.append(f"### {c['id']}: {c['title']}")
        lines.append(f"- 採点: {c['total_score']}点 / 100点")
        lines.append(f"- 不採用理由: {c['reject_reason']}")
        lines.append("")

    (output_dir / "03_rejected_topics.md").write_text("\n".join(lines), encoding="utf-8")


def write_fact_source_plan(selected, input_data, output_dir):
    lines = [
        "# 出典・情報源計画",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        "",
        "## 登録済み公式情報源",
        "",
    ]
    for src in input_data.get("official_sources", []):
        lines.append(f"- [{src.get('type', '')}] {src.get('name', '')}: {src.get('url', '')}")
    lines.append("")
    lines.append("※ 未確認の情報は「未確認」と明記する。推測で埋めない。")
    lines.append("")

    for c in selected:
        lines.append(f"## {c['id']}: {c['title']}")
        lines.append("")
        lines.append("### 確認すべき情報源")
        lines.append("")
        for src in c.get("official_sources", []):
            lines.append(f"- {src}")
        if not c.get("official_sources"):
            lines.append("- 公式根拠が未登録。official_sourcesへの追加が必要")
        lines.append("")

    (output_dir / "04_fact_source_plan.md").write_text("\n".join(lines), encoding="utf-8")


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
        lines.append(f"### 想定尺: 7〜9分")
        lines.append("")
        lines.append(f"### 素材方針")
        lines.append(f"- テロップ・テキストカード中心")
        lines.append(f"- 公式記録の引用表示")
        lines.append(f"- 人物写真は使用しない（肖像権リスク回避）")
        lines.append(f"- 和風背景・単色背景を使用")
        lines.append("")

    (output_dir / "05_long_video_plan.md").write_text("\n".join(lines), encoding="utf-8")


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
        for i, (s_title, hook, body, last_word) in enumerate([
            (f"{short_topic}とは",
             f"「{short_topic}」をご存知ですか？",
             "テーマの概要を簡潔に紹介し、公式記録の要点を伝える",
             "詳しくは関連動画からご覧ください"),
            (f"{short_topic}の印象的な場面",
             "公式記録に残る、心に残る一場面があります",
             "最も印象的なエピソードを一つ取り上げ、背景とともに紹介",
             "この記録は、今も多くの人の心に残っています"),
            (f"{short_topic}が伝えること",
             "この記録が私たちに伝えることとは",
             "テーマの意義をまとめ、長尺動画への関心を喚起する",
             "長尺動画では、さらに詳しくお伝えしています"),
        ], 1):
            lines.append(f"### Shorts {i}: {s_title}")
            lines.append("")
            lines.append(f"- Shortsタイトル: {s_title}")
            lines.append(f"- 冒頭1秒の引き: {hook}")
            lines.append(f"- 本文構成: {body}")
            lines.append(f"- 最後の一言: {last_word}")
            lines.append(f"- 長尺への導線: 概要欄に長尺動画リンクを設置")
            lines.append(f"- 45〜60秒で成立する理由: 一つのポイントに絞り、テロップで補足するため尺内に収まる")
            lines.append("")

    (output_dir / "06_shorts_plan.md").write_text("\n".join(lines), encoding="utf-8")


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

    (output_dir / "07_title_thumbnail_plan.md").write_text("\n".join(lines), encoding="utf-8")


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
        s = c["scores"]
        risk_assessments = {
            "事実誤認リスク": "低（公式記録に基づく）" if s.get("official_evidence", 0) >= 6 else "中（追加確認が必要）",
            "権利リスク": risk_level,
            "収益化リスク": "低（広告適合性に問題なし）" if is_low else "中（慎重な構成が必要）",
            "炎上リスク": "低（中立的な構成）" if is_low else "中（対立軸に注意）",
            "高齢視聴者との不一致": "低（適合性が高い）" if s.get("senior_fit", 0) >= 7 else "中（視聴者層を意識した構成が必要）",
            "外注者の作業負担": "低（テロップ中心）" if s.get("production_cost", 0) >= 7 else "中（素材指示を明確にする必要あり）",
            "素材調達難易度": "低（公式記録・テロップで構成可能）" if is_low else "中（一部素材の確認が必要）",
        }
        for category in cfg.RISK_CATEGORIES:
            lines.append(f"- {category}: {risk_assessments.get(category, '未評価')}")
        overall = "低" if all("低" in v for v in risk_assessments.values()) else "中"
        lines.append(f"- **総合リスク判定: {overall}**")
        lines.append("")

    (output_dir / "08_risk_check_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_package_summary(result, input_data, mode, output_dir):
    selected = result["selected"]
    held = result["held"]
    rejected = result["rejected"]
    candidates = result["candidates"]

    has_input = bool(input_data.get("topic_ideas"))
    is_sample = all(c.get("data_source") == "test_sample" for c in candidates) if candidates else True

    has_prohibited_in_selected = any(c.get("has_prohibited") for c in selected)
    has_empty_evidence = any(c["scores"].get("official_evidence", 0) == 0 for c in selected)

    package_complete = (
        len(selected) > 0
        and not has_prohibited_in_selected
        and not has_empty_evidence
        and has_input
    )

    production_ready = (
        package_complete
        and mode == "production"
        and not is_sample
    )

    lines = [
        "# 企画パッケージ概要",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        f"モード: {mode}",
        f"入力データ: {'あり' if has_input else 'なし'}",
        f"サンプルデータ使用: {'はい' if is_sample else 'いいえ'}",
        "",
        "## YouTube需要分析",
        "",
        f"- 競合チャンネル数: {len(input_data.get('competitor_channels', []))}",
        f"- 参考動画数: {len(input_data.get('reference_videos', []))}",
        f"- 自チャンネル動画数: {len(input_data.get('own_channel_videos', []))}",
        f"- 採用禁止テーマ数: {len(input_data.get('banned_themes', []))}",
        f"- 登録済み公式情報源数: {len(input_data.get('official_sources', []))}",
        "",
        "## 結果サマリ",
        "",
        f"- 候補企画数: {len(candidates)}本",
        f"- 採用企画数: {len(selected)}本",
        f"- 保留企画数: {len(held)}本",
        f"- 不採用企画数: {len(rejected)}本",
        "",
        "## 判定",
        "",
        f"- package_complete: {package_complete}",
        f"- production_ready: {production_ready}",
        "",
    ]

    if not production_ready and mode == "production":
        lines.append("## production_ready=false の理由")
        lines.append("")
        if is_sample:
            lines.append("- サンプルデータでは本番判定できません。--input で実データを指定してください")
        if not has_input:
            lines.append("- 入力データがありません")
        if len(selected) == 0:
            lines.append("- 採用企画が0本")
        if has_prohibited_in_selected:
            lines.append("- 採用企画に禁止表現が含まれている")
        if has_empty_evidence:
            lines.append("- 採用企画に公式根拠なしのものがある")
        lines.append("")

    priority = [c for c in selected if c["total_score"] >= cfg.PRIORITY_THRESHOLD]
    if priority:
        lines.append("## 最優先で制作すべき企画")
        lines.append("")
        for c in priority[:3]:
            lines.append(f"- {c['id']}: {c['title']}（{c['total_score']}点）")
        lines.append("")

    normal = [c for c in selected if c["total_score"] < cfg.PRIORITY_THRESHOLD]
    if normal:
        lines.append("## 次に制作すべき企画")
        lines.append("")
        for c in normal:
            lines.append(f"- {c['id']}: {c['title']}（{c['total_score']}点）")
        lines.append("")

    (output_dir / "09_package_summary.md").write_text("\n".join(lines), encoding="utf-8")

    return {
        "package_complete": package_complete,
        "production_ready": production_ready,
        "selected_count": len(selected),
        "held_count": len(held),
        "rejected_count": len(rejected),
        "is_sample": is_sample,
    }


def write_topic_plan_json(result, input_data, mode, summary, output_dir):
    """制作パッケージ入力用の topic_plan.json を生成."""
    selected = result["selected"]
    plan = {
        "channel": cfg.CHANNEL_NAME,
        "mode": mode,
        "production_ready": summary["production_ready"],
        "package_complete": summary["package_complete"],
        "selected_count": summary["selected_count"],
        "held_count": summary["held_count"],
        "rejected_count": summary["rejected_count"],
        "topics": [],
    }
    for c in selected:
        topic_entry = {
            "id": c["id"],
            "title": c["title"],
            "center_pin": c["center_pin"],
            "theme_keywords": c.get("theme_keywords", []),
            "total_score": c["total_score"],
            "scores": c["scores"],
            "official_source_urls": c.get("official_source_urls", []),
            "rights_risk": c["rights_risk"],
            "long_reason": c.get("long_reason", ""),
            "shorts_reason": c.get("shorts_reason", ""),
            "expected_emotion": c.get("expected_emotion", ""),
        }
        plan["topics"].append(topic_entry)

    path = output_dir / "topic_plan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan
