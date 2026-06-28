"""Material instruction sheet and rights guidance for outsourcing packages.

Generates 04_materials_list.md as a scene-by-scene material instruction
sheet that outsourcers can use to select and record materials.

Claude Code does NOT:
- Search or collect material URLs automatically
- Judge copyright/licensing for individual materials
- Select person photos or video clips
- Download material files

Instead, it generates clear instructions per scene so the outsourcer
can select appropriate materials from approved sources.
"""

from pathlib import Path

import config as cfg


ALLOWED_SOURCES = [
    "宮内庁公式ページ",
    "宮内庁公式Instagram",
    "宮内庁公式YouTube",
    "外国王室・政府・自治体・公的機関の公式ページ",
    "Wikimedia Commonsの個別ファイルページ（作者・ライセンス・クレジット条件を確認）",
    "商用利用・YouTube収益化可能と確認済みのストック素材",
    "自作テキストカード",
    "単色背景",
    "グラデーション背景",
]

PROHIBITED_SOURCES = [
    "皇族・王族のAI生成画像",
    "実在人物の顔、服装、表情、年齢を変更した合成画像",
    "出典不明画像",
    "まとめサイトや個人転載ページの画像",
    "利用条件不明の報道写真",
    "テレビ番組やニュース映像の無断転載",
    "商用利用不可または収益化不可のストック素材",
]


def _collect_candidate_urls(research_data, scene_key):
    """Collect candidate URLs from research data facts for a given scene."""
    urls = []
    facts = research_data.get("facts", [])
    material_hints = research_data.get("material_hints", {})
    hint = material_hints.get(scene_key, {})

    candidate_urls = hint.get("candidate_urls", [])
    if candidate_urls:
        return candidate_urls

    if scene_key == "opening":
        seen = set()
        for f in facts[:2]:
            url = f.get("source_url")
            name = f.get("source_name", "")
            publisher = f.get("official_publisher", "")
            if url and url not in seen:
                seen.add(url)
                urls.append({"url": url, "description": f"{publisher}公式 - {name}",
                             "rights_status": "usable" if publisher else "review"})
        return urls

    section_config = research_data.get("section_config", [])
    facts_by_id = {f["fact_id"]: f for f in facts if f.get("usable_in_script")}

    if scene_key.startswith("ch"):
        ch_idx = int(scene_key[2:]) - 1
        if ch_idx < len(section_config):
            fact_ids = section_config[ch_idx].get("fact_ids", [])
            seen = set()
            for fid in fact_ids:
                fact = facts_by_id.get(fid)
                if fact:
                    url = fact.get("source_url")
                    name = fact.get("source_name", "")
                    publisher = fact.get("official_publisher", "")
                    if url and url not in seen:
                        seen.add(url)
                        urls.append({"url": url, "description": f"{publisher}公式 - {name}",
                                     "rights_status": "usable" if publisher else "review"})
    return urls


def _build_scene_materials(topic, research_data):
    """Build scene-by-scene material instruction rows from research data."""
    scenes = []
    section_config = research_data.get("section_config", [])
    facts_by_id = {f["fact_id"]: f for f in research_data.get("facts", [])
                   if f.get("usable_in_script")}

    material_hints = research_data.get("material_hints", {})
    opening_hint = material_hints.get("opening", {})

    opening_urls = _collect_candidate_urls(research_data, "opening")

    scenes.append({
        "material_id": "MAT-001",
        "scene": "オープニング（0:00〜）",
        "script_content": f"テーマ「{topic}」の導入",
        "required_material": opening_hint.get("required_material", "タイトルテキストカード、チャンネルロゴ"),
        "source_suggestion": opening_hint.get("source_suggestion", "自作テキストカード／単色背景"),
        "prohibited": "皇族のAI生成画像",
        "self_made_alternative": opening_hint.get("self_made_alternative", "テーマ名と「日本が誇る皇室物語」ロゴをテキストカードで構成"),
        "candidate_urls": opening_urls,
        "outsourcer_url": "",
    })

    for ch_idx, section in enumerate(section_config):
        title = section.get("title", "")
        fact_ids = section.get("fact_ids", [])
        content_summary = []
        for fid in fact_ids:
            fact = facts_by_id.get(fid)
            if fact:
                claim = fact.get("claim", "")
                if claim:
                    content_summary.append(claim)

        ch_key = f"ch{ch_idx + 1}"
        hint = material_hints.get(ch_key, {})
        ch_urls = _collect_candidate_urls(research_data, ch_key)

        scenes.append({
            "material_id": f"MAT-{ch_idx + 2:03d}",
            "scene": f"第{ch_idx + 1}章「{title}」",
            "script_content": "／".join(content_summary) if content_summary else title,
            "required_material": hint.get("required_material", "テーマに合った背景画像またはテキストカード"),
            "source_suggestion": hint.get("source_suggestion", "宮内庁公式ページ／公的機関の公式ページ／自作テキストカード"),
            "prohibited": hint.get("prohibited", "AI生成画像／出典不明画像／報道写真の無断使用"),
            "self_made_alternative": hint.get("self_made_alternative", "公式情報をテロップで引用表示。背景は単色またはグラデーション"),
            "candidate_urls": ch_urls,
            "outsourcer_url": "",
        })

    if not section_config:
        main_urls = _collect_candidate_urls(research_data, "ch1")
        scenes.append({
            "material_id": "MAT-002",
            "scene": "本編",
            "script_content": "テーマに関する解説",
            "required_material": "テーマに合った背景画像またはテキストカード",
            "source_suggestion": "宮内庁公式ページ／公的機関の公式ページ／自作テキストカード",
            "prohibited": "AI生成画像／出典不明画像／報道写真の無断使用",
            "self_made_alternative": "公式情報をテロップで引用表示。背景は単色またはグラデーション",
            "candidate_urls": main_urls,
            "outsourcer_url": "",
        })

    next_id = len(scenes) + 1
    scenes.append({
        "material_id": f"MAT-{next_id:03d}",
        "scene": "エンディング",
        "script_content": "チャンネル登録誘導・次回予告",
        "required_material": "エンドカード、チャンネルロゴ",
        "source_suggestion": "自作テキストカード",
        "prohibited": "なし",
        "self_made_alternative": "チャンネル名・登録誘導テキストを自作",
        "candidate_urls": [],
        "outsourcer_url": "",
    })

    return scenes


def generate_materials_md(topic, research_data, output_dir):
    """Write 04_materials_list.md as a scene-based material instruction sheet."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scenes = _build_scene_materials(topic, research_data)

    lines = [
        "# 素材指示書",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"テーマ: {topic}",
        "",
        "---",
        "",
        "## 使用可能な素材元",
        "",
    ]
    for src in ALLOWED_SOURCES:
        lines.append(f"- {src}")

    lines += [
        "",
        "## 使用禁止素材",
        "",
    ]
    for src in PROHIBITED_SOURCES:
        lines.append(f"- {src}")

    lines += [
        "",
        "## Wikimedia Commonsを使用する場合",
        "",
        "画像の直リンクではなく、個別ファイルページのURLを使用してください。",
        "個別ファイルページで以下を確認してください。",
        "",
        "- 作者・権利者",
        "- ライセンス（CC BY-SA等）",
        "- クレジット条件",
        "- ファイルの出典",
        "",
        "---",
        "",
        "## 場面別素材指示",
        "",
    ]

    for scene in scenes:
        lines.append(f"### {scene['material_id']}: {scene['scene']}")
        lines.append("")
        lines.append(f"- **台本内容**: {scene['script_content']}")
        lines.append(f"- **必要な素材**: {scene['required_material']}")
        lines.append(f"- **推奨素材元**: {scene['source_suggestion']}")
        lines.append(f"- **使用禁止**: {scene['prohibited']}")
        lines.append(f"- **自作代替**: {scene['self_made_alternative']}")
        candidate_urls = scene.get("candidate_urls", [])
        if candidate_urls:
            lines.append(f"- **候補URL**:")
            for cu in candidate_urls:
                rs = cu.get("rights_status", "review")
                lines.append(f"  - [{rs}] {cu.get('description', '')}: {cu.get('url', '')}")
        lines.append(f"- **使用URL**: {scene['outsourcer_url'] or '（外注者が編集時に記入）'}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 外注者の素材使用記録",
        "",
        "編集時に実際に使用した素材を以下の形式で記録してください。",
        "",
        "| 使用箇所 | 素材内容 | 素材元 | 使用URL |",
        "| ---- | ---- | --- | ----- |",
        "| （例）第1章 背景 | 宮内庁公式ページの写真 | 宮内庁公式 | https://... |",
        "| （例）オープニング | タイトルテキストカード | 自作 | 自作・URL不要 |",
        "",
        "自作テキストカード、単色背景、グラデーション背景は「自作・URL不要」と記録してください。",
        "",
    ]

    md_path = output_dir / "04_materials_list.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return scenes


def generate_material_urls_csv(topic, research_data, output_dir):
    """Generate scene-based material instructions.

    Returns scene data for rights report generation.
    This function name is kept for backward compatibility with main.py.
    """
    return generate_materials_md(topic, research_data, output_dir)


def generate_rights_report(materials_data, ng_results, output_dir):
    """Write rights_report.md with per-material rights status.

    Evaluates each scene's candidate URLs and assigns:
    - usable: public official source, clearly available
    - review: needs human confirmation of license
    - blocked: prohibited source type
    - incomplete: no candidate URL provided
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scene_statuses = []
    has_ng = False
    has_review = False
    has_incomplete = False

    scenes = materials_data if isinstance(materials_data, list) else []
    for scene in scenes:
        candidate_urls = scene.get("candidate_urls", [])
        scene_name = scene.get("scene", scene.get("material_id", ""))

        if not candidate_urls:
            scene_statuses.append({"scene": scene_name, "status": "incomplete",
                                   "detail": "候補URLなし（自作代替で対応可能）"})
            has_incomplete = True
            continue

        scene_status = "usable"
        for cu in candidate_urls:
            rs = cu.get("rights_status", "review")
            if rs == "blocked":
                has_ng = True
                scene_status = "blocked"
            elif rs == "review" and scene_status != "blocked":
                has_review = True
                scene_status = "review"

        scene_statuses.append({"scene": scene_name, "status": scene_status,
                               "detail": f"{len(candidate_urls)}件の候補URL"})

    if has_ng:
        overall = "blocked"
    elif has_review:
        overall = "review"
    elif has_incomplete and not any(s["status"] == "usable" for s in scene_statuses):
        overall = "incomplete"
    else:
        overall = "OK"

    lines = [
        "# 権利確認ガイド",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        "",
        "## 総合判定",
        "",
        f"**{overall}**",
        "",
        "## 場面別権利状況",
        "",
    ]

    for ss in scene_statuses:
        status_label = {"usable": "使用可", "review": "要確認", "blocked": "使用不可",
                        "incomplete": "候補なし"}.get(ss["status"], ss["status"])
        lines.append(f"- [{status_label}] {ss['scene']}: {ss['detail']}")

    lines += [
        "",
        "## 素材選定の原則",
        "",
        "- 使用可能な素材元のみから選定すること",
        "- 使用禁止素材を絶対に使用しないこと",
        "- Wikimedia Commonsは個別ファイルページでライセンスを確認すること",
        "- 権利不明の素材は使用しないこと",
        "- 自作テキストカード・単色背景で代替可能な場面は自作を優先すること",
        "",
        "## 注意事項",
        "",
        "- 皇族・王族のAI生成画像は一切使用禁止",
        "- 報道写真は利用条件が不明な場合は使用禁止",
        "- URLを記載しただけでは使用許諾を主張できません",
        "- 公式記録写真を「イメージ」と誤表示しないこと",
        "",
    ]

    report_path = output_dir / "rights_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "overall_status": overall,
        "has_ng": has_ng,
        "has_review": has_review,
    }
