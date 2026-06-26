"""Material URL management and rights checking.

Generates material_urls.csv and rights_report.md for outsourcing packages.
Ensures no URLs are fabricated and rights statuses are honestly assessed.
"""

import csv
from pathlib import Path

import config as cfg


# ---------------------------------------------------------------------------
# Rights-check categories
# ---------------------------------------------------------------------------

RIGHTS_CATEGORIES = [
    "人物写真（肖像権）",
    "報道写真（プレス）",
    "公式SNS素材",
    "公式YouTube素材",
    "一般風景",
    "建造物外観",
    "国旗",
    "航空機",
    "室内・内装",
    "ストック素材",
    "BGM・音楽",
    "引用・テキスト",
    "クレジット表記",
]


# ---------------------------------------------------------------------------
# Default material generation
# ---------------------------------------------------------------------------

def _generate_default_materials(topic, research_data):
    """Generate default material entries based on topic and research data."""
    materials = []
    sources = research_data.get("sources", [])

    materials.append({
        "material_id": "MAT-001",
        "scene": "導入・タイトル",
        "person_or_subject": topic,
        "source_name": "テロップ・テキストカード",
        "source_url": "",
        "source_type": "自作",
        "rights_status": "OK",
        "usage_note": "タイトルテキストのみで構成",
        "image_or_video": "image",
        "credit_required": False,
        "alternative": "",
    })

    materials.append({
        "material_id": "MAT-002",
        "scene": "背景イメージ",
        "person_or_subject": "和紙背景イメージ",
        "source_name": "ストック素材サイト",
        "source_url": "",
        "source_type": "ストック素材",
        "rights_status": "REVIEW",
        "usage_note": "商用利用可能なストック素材を使用。ライセンス確認必須",
        "image_or_video": "image",
        "credit_required": False,
        "alternative": "単色背景・グラデーション",
    })

    for i, src in enumerate(sources[:5]):
        materials.append({
            "material_id": f"MAT-{i+3:03d}",
            "scene": "解説パート",
            "person_or_subject": src.get("source_name", ""),
            "source_name": src.get("source_name", ""),
            "source_url": src.get("source_url", ""),
            "source_type": src.get("source_type", "要確認"),
            "rights_status": "REVIEW",
            "usage_note": "出典として参照。画像使用には別途確認が必要",
            "image_or_video": "image",
            "credit_required": True,
            "alternative": "テロップで情報を表示",
        })

    materials.append({
        "material_id": f"MAT-{len(materials)+1:03d}",
        "scene": "エンディング",
        "person_or_subject": "エンディングカード",
        "source_name": "自作",
        "source_url": "",
        "source_type": "自作",
        "rights_status": "OK",
        "usage_note": "チャンネル名・登録誘導テキスト",
        "image_or_video": "image",
        "credit_required": False,
        "alternative": "",
    })

    return materials


def _default_aiko_materials():
    """Return default material rows for the 愛子/敬宮 name-origin topic."""
    return [
        {
            "material_id": "MAT-001",
            "scene": "導入・タイトル",
            "person_or_subject": "タイトルテキストカード",
            "source_name": "自作テロップ",
            "source_url": "",
            "source_type": "自作",
            "rights_status": "OK",
            "usage_note": "テーマ名と「日本が誇る皇室物語」ロゴを配置",
            "image_or_video": "image",
            "credit_required": False,
            "alternative": "",
        },
        {
            "material_id": "MAT-002",
            "scene": "宮内庁公式情報の紹介",
            "person_or_subject": "宮内庁公式情報テキストカード",
            "source_name": "自作テロップ（宮内庁公式サイト情報を引用表示）",
            "source_url": "",
            "source_type": "自作",
            "rights_status": "OK",
            "usage_note": "宮内庁公式サイトの記者会見原文をテロップとして表示。画像は使用しない",
            "image_or_video": "image",
            "credit_required": False,
            "alternative": "",
        },
        {
            "material_id": "MAT-003",
            "scene": "『孟子』の教え解説",
            "person_or_subject": "孟子原文テキストカード",
            "source_name": "自作テロップ（古典原文を引用表示）",
            "source_url": "",
            "source_type": "自作",
            "rights_status": "OK",
            "usage_note": "著作権切れの古典原文をテロップとして自作表示。出典を明記",
            "image_or_video": "image",
            "credit_required": False,
            "alternative": "",
        },
        {
            "material_id": "MAT-004",
            "scene": "背景イメージ",
            "person_or_subject": "和紙・筆文字風背景",
            "source_name": "ストック素材サイト",
            "source_url": "",
            "source_type": "ストック素材",
            "rights_status": "REVIEW",
            "usage_note": "商用利用可・ロイヤリティフリーのストック素材を使用。購入・ライセンス確認必須。「イメージ」ラベル表示",
            "image_or_video": "image",
            "credit_required": False,
            "alternative": "単色背景・グラデーション（自作で代替可能）",
        },
        {
            "material_id": "MAT-005",
            "scene": "エンディング",
            "person_or_subject": "チャンネルロゴ・エンドカード",
            "source_name": "自作素材",
            "source_url": "",
            "source_type": "自作",
            "rights_status": "OK",
            "usage_note": "チャンネル名・登録誘導テキスト",
            "image_or_video": "image",
            "credit_required": False,
            "alternative": "",
        },
    ]


# ---------------------------------------------------------------------------
# CSV generation
# ---------------------------------------------------------------------------

MATERIAL_CSV_FIELDNAMES = [
    "material_id",
    "scene",
    "person_or_subject",
    "source_name",
    "source_url",
    "source_type",
    "rights_status",
    "usage_note",
    "image_or_video",
    "credit_required",
    "alternative",
]


def generate_material_urls_csv(topic, research_data, output_dir):
    """Write ``material_urls.csv`` listing candidate materials and rights info.

    Parameters
    ----------
    topic : str
        The video topic / title.
    research_data : dict
        Research data that may contain material hints.
    output_dir : str | Path
        Directory to write the CSV into.

    Returns
    -------
    list[dict]
        The material rows written to the CSV.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if "愛子" in topic and "敬宮" in topic:
        materials = _default_aiko_materials()
    else:
        materials = _generate_default_materials(topic, research_data)

    # Merge in any materials provided via research_data
    extra = research_data.get("materials", [])
    for item in extra:
        row = {}
        for field in MATERIAL_CSV_FIELDNAMES:
            row[field] = item.get(field, "")
        # Never fabricate URLs
        if row.get("source_url") and not _is_plausible_url(row["source_url"]):
            row["source_url"] = ""
            row["usage_note"] = (row.get("usage_note", "") +
                                 " URL未確認のため空欄に修正").strip()
        # Default rights_status
        if row.get("rights_status") not in ("OK", "REVIEW", "NG"):
            row["rights_status"] = "REVIEW"
        materials.append(row)

    csv_path = output_dir / "material_urls.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MATERIAL_CSV_FIELDNAMES)
        writer.writeheader()
        for mat in materials:
            writer.writerow({k: mat.get(k, "") for k in MATERIAL_CSV_FIELDNAMES})

    return materials


def _is_plausible_url(url):
    """Basic check that a URL looks like a real HTTP(S) URL."""
    if not isinstance(url, str):
        return False
    return url.startswith("http://") or url.startswith("https://")


# ---------------------------------------------------------------------------
# Rights report
# ---------------------------------------------------------------------------

def generate_rights_report(materials_data, ng_results, output_dir):
    """Write ``rights_report.md`` with per-item rights verdicts.

    Parameters
    ----------
    materials_data : list[dict]
        Material rows (from ``generate_material_urls_csv``).
    ng_results : dict
        NG check results (from ``ng_check.check_ng_expressions``).
    output_dir : str | Path
        Directory to write the report into.

    Returns
    -------
    dict
        Summary with overall_status and per-item verdicts.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    verdicts = []
    has_ng = False
    has_review = False

    for mat in materials_data:
        status = mat.get("rights_status", "REVIEW").upper()
        source_type = mat.get("source_type", "")
        material_id = mat.get("material_id", "")
        person_or_subject = mat.get("person_or_subject", "")

        verdict = {
            "material_id": material_id,
            "person_or_subject": person_or_subject,
            "source_type": source_type,
            "rights_status": status,
            "notes": [],
        }

        # Person photos need explicit permission beyond attribution
        if "人物" in source_type or "肖像" in source_type:
            verdict["notes"].append(
                "人物写真は肖像権の確認が必要。報道写真はクレジットだけでは不十分、"
                "使用許諾の取得が必要"
            )
            if status != "NG":
                verdict["rights_status"] = "REVIEW"

        # Press photos
        if "プレス" in source_type or "報道" in source_type:
            verdict["notes"].append(
                "報道写真は撮影者・通信社の使用許諾が必要。"
                "URLの記載だけでは使用権を主張できない"
            )
            if status == "OK":
                verdict["rights_status"] = "REVIEW"

        # General scenery / buildings -> needs イメージ label
        if source_type in ("一般風景", "建造物外観", "ストック素材"):
            verdict["notes"].append("使用時は「イメージ」ラベルを表示すること")

        # Don't mislabel official record photos as イメージ
        if source_type == "公式機関":
            verdict["notes"].append(
                "公式記録写真を「イメージ」と表示しないこと。"
                "出典を正確に記載"
            )

        if verdict["rights_status"] == "NG":
            has_ng = True
            verdict["notes"].append("NG素材のため指示書に含めないこと")
        elif verdict["rights_status"] == "REVIEW":
            has_review = True
            alt = mat.get("alternative", "")
            if alt:
                verdict["notes"].append(f"代替案: {alt}")

        verdicts.append(verdict)

    # Build report markdown
    lines = [
        "# 権利確認レポート",
        "",
        f"チャンネル: {cfg.CHANNEL_NAME}",
        f"チャンネル方針: {cfg.CHANNEL_PROMISE}",
        "",
        "## 確認カテゴリ",
        "",
    ]
    for cat in RIGHTS_CATEGORIES:
        lines.append(f"- {cat}")

    lines += ["", "## 素材別判定", ""]

    for v in verdicts:
        status_mark = {"OK": "OK", "REVIEW": "REVIEW", "NG": "NG"}.get(
            v["rights_status"], "REVIEW"
        )
        lines.append(f"### {v['material_id']}: {v['person_or_subject']}")
        lines.append("")
        lines.append(f"- 素材種別: {v['source_type']}")
        lines.append(f"- 判定: **{status_mark}**")
        for note in v["notes"]:
            lines.append(f"- {note}")
        lines.append("")

    # Summary
    if has_ng:
        overall = "NG"
    elif has_review:
        overall = "REVIEW"
    else:
        overall = "OK"

    lines += [
        "## 総合判定",
        "",
        f"**{overall}**",
        "",
    ]
    if has_ng:
        lines.append("NG素材が含まれています。該当素材を指示書から除外してください。")
        lines.append("")
    if has_review:
        lines.append("REVIEW素材があります。代替案の検討または権利確認を行ってください。")
        lines.append("")

    lines += [
        "## 注意事項",
        "",
        "- URLを記載しただけでは使用許諾を主張できません",
        "- 報道写真はクレジット表記だけでなく、明示的な使用許諾が必要です",
        "- 一般的な風景・建造物の素材には「イメージ」ラベルを付けてください",
        "- 公式記録写真を「イメージ」と誤表示しないでください",
        "",
    ]

    report_path = output_dir / "rights_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "overall_status": overall,
        "verdicts": verdicts,
        "has_ng": has_ng,
        "has_review": has_review,
    }
