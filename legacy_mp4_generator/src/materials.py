"""Material rights management and image generation."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import config as cfg


def create_material_record(file_path, source_name, source_url="",
                           rights_status="OK", image_type="background",
                           generated_by_ai=False, credit_required=False,
                           credit_text=""):
    return {
        "file_path": str(file_path),
        "source_name": source_name,
        "source_url": source_url,
        "rights_status": rights_status,
        "image_type": image_type,
        "generated_by_ai": generated_by_ai,
        "credit_required": credit_required,
        "credit_text": credit_text,
    }


PROHIBITED_IMAGE_TYPES = [
    "ai_generated_royal_face",
    "face_composite",
    "expression_modified",
    "clothing_modified",
    "age_modified",
    "unverified_press_photo",
]


def validate_material(material):
    """Validate a single material record. Returns list of violation strings."""
    violations = []
    fp = material.get("file_path", "unknown")

    if not material.get("source_name"):
        violations.append(f"{fp}: source_name（出典・取得元）が未記録")

    if not material.get("rights_status"):
        violations.append(f"{fp}: rights_statusが未記録")
    elif material["rights_status"] not in ("OK", "REVIEW", "NG"):
        violations.append(
            f"{fp}: rights_statusが不正値 '{material['rights_status']}'"
            " (OK/REVIEW/NGのみ許可)"
        )

    if material.get("rights_status") != "OK":
        violations.append(
            f"{fp}: rights_status='{material.get('rights_status')}'"
            " — 完成MP4にはOKのみ使用可"
        )

    if material.get("generated_by_ai") and material.get("image_type") in (
        "royal_portrait", "royal_face", "ai_generated_royal_face",
    ):
        violations.append(f"{fp}: 皇族・王族のAI生成人物画像は使用禁止")

    if material.get("image_type") in PROHIBITED_IMAGE_TYPES:
        violations.append(
            f"{fp}: 禁止素材種別 '{material['image_type']}'"
            "（顔合成/表情変更/服装変更/年齢変更/権利不明報道写真）"
        )

    if material.get("image_type") == "press_photo" and not material.get("source_url"):
        violations.append(f"{fp}: 報道写真にsource_url（権利元URL）が未記録")

    if material.get("image_type") in ("press_photo", "archive_photo"):
        if not material.get("source_name") or not material.get("source_url"):
            violations.append(
                f"{fp}: 実在記録写真には出典（source_name）と"
                "取得元URL（source_url）が必須"
            )

    return violations


def validate_all_materials(materials):
    """Validate all materials for production use. Returns (ok, violations_list)."""
    all_violations = []
    for m in materials:
        all_violations.extend(validate_material(m))
    return len(all_violations) == 0, all_violations


def filter_ok_materials(materials):
    ok = [m for m in materials if m["rights_status"] == "OK"]
    excluded = [m for m in materials if m["rights_status"] != "OK"]
    return ok, excluded


def save_materials_json(materials, output_path):
    Path(output_path).write_text(json.dumps(materials, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_rights_report(materials, output_path):
    lines = ["# 素材権利レポート", "", f"総素材数: {len(materials)}", ""]
    for status in ["OK", "REVIEW", "NG"]:
        items = [m for m in materials if m["rights_status"] == status]
        lines.append(f"## {status} ({len(items)}件)")
        for m in items:
            lines.append(f"- {m['file_path']}: {m['source_name']}")
            if m["credit_required"]:
                lines.append(f"  クレジット: {m['credit_text']}")
        lines.append("")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def _get_font(size):
    for fp in [cfg.FONT_PATH] + cfg.FALLBACK_FONTS:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def generate_washi_background(width, height, output_path, color_base=(245, 240, 230)):
    """Generate a washi-paper-style background."""
    import random
    rng = random.Random(hash(str(output_path)) & 0xFFFFFFFF)
    img = Image.new("RGB", (width, height), color_base)
    draw = ImageDraw.Draw(img)
    for _ in range(width * height // 50):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        offset = rng.randint(-8, 8)
        c = tuple(max(0, min(255, v + offset)) for v in color_base)
        draw.point((x, y), fill=c)
    img.save(str(output_path), quality=95)
    return output_path


def generate_title_card(width, height, title, output_path,
                        bg_color=(30, 30, 60), text_color=(220, 200, 160)):
    """Generate a title card image."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    font_large = _get_font(width // 18)
    font_small = _get_font(width // 30)

    channel = cfg.CHANNEL_NAME
    _draw_centered_text(draw, channel, font_small, text_color, width, height // 3)
    _draw_centered_text(draw, title, font_large, text_color, width, height // 2)

    img.save(str(output_path), quality=95)
    return output_path


def generate_section_card(width, height, label, output_path,
                          bg_color=(40, 35, 55), text_color=(200, 180, 140)):
    """Generate a section header card."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font = _get_font(width // 14)
    _draw_centered_text(draw, label, font, text_color, width, height // 2)
    img.save(str(output_path), quality=95)
    return output_path


def generate_text_card(width, height, text, output_path,
                       bg_color=(245, 240, 230), text_color=(40, 30, 20)):
    """Generate a text card for narration display."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font = _get_font(width // 22)
    _draw_centered_text(draw, text, font, text_color, width, height // 2)
    img.save(str(output_path), quality=95)
    return output_path


def generate_ending_card(width, height, output_path):
    """Generate an ending card."""
    bg_color = (25, 25, 50)
    text_color = (220, 200, 160)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font_large = _get_font(width // 18)
    font_small = _get_font(width // 28)

    _draw_centered_text(draw, "ご視聴ありがとうございました", font_large, text_color, width, height * 2 // 5)
    _draw_centered_text(draw, "チャンネル登録・高評価よろしくお願いします", font_small, text_color, width, height * 3 // 5)
    img.save(str(output_path), quality=95)
    return output_path


def _draw_centered_text(draw, text, font, color, img_width, y):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (img_width - tw) // 2
    draw.text((x, y), text, fill=color, font=font)


def generate_all_visuals(script_data, width, height, output_dir):
    """Generate all visual assets for a script and return materials list."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    materials = []
    image_paths = []

    title_path = output_dir / "title.png"
    generate_title_card(width, height, script_data["title"], title_path)
    materials.append(create_material_record(
        title_path, "自作タイトルカード", rights_status="OK",
        image_type="title_card", generated_by_ai=False
    ))
    image_paths.append({"path": str(title_path), "section": "title", "type": "title"})

    bg_colors = [
        (245, 240, 230), (235, 230, 220), (240, 235, 225),
        (230, 225, 215), (238, 233, 223), (242, 237, 227),
        (248, 243, 233),
    ]

    line_index = 0
    for si, section in enumerate(script_data["sections"]):
        sec_path = output_dir / f"section_{si:02d}.png"
        generate_section_card(width, height, section["label"], sec_path)
        materials.append(create_material_record(
            sec_path, f"自作セクションカード: {section['label']}",
            rights_status="OK", image_type="section_card"
        ))
        image_paths.append({"path": str(sec_path), "section": section["section"], "type": "section_header"})

        for li, line in enumerate(section["lines"]):
            bg_path = output_dir / f"bg_{si:02d}_{li:02d}.png"
            color = bg_colors[(si + li) % len(bg_colors)]
            generate_washi_background(width, height, bg_path, color)
            materials.append(create_material_record(
                bg_path, "自作和紙背景", rights_status="OK", image_type="background"
            ))
            image_paths.append({
                "path": str(bg_path), "section": section["section"],
                "type": "narration_bg", "line_index": line_index
            })
            line_index += 1

    ending_path = output_dir / "ending.png"
    generate_ending_card(width, height, ending_path)
    materials.append(create_material_record(
        ending_path, "自作エンディングカード", rights_status="OK", image_type="ending_card"
    ))
    image_paths.append({"path": str(ending_path), "section": "ending", "type": "ending"})

    return materials, image_paths
