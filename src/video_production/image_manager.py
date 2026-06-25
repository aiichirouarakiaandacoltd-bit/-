"""画像管理モジュール（拡張版）

セクションごとの背景画像を管理する。
AI生成による実在皇族の顔画像は禁止。
rights_status が OK のもののみ使用。
REVIEW/NG素材は除外してログに記録。
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config


def create_placeholder_image(
    text: str,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    bg_color: tuple = (30, 30, 60),
    text_color: tuple = (255, 255, 255),
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    display_text = text[:40]
    bbox = draw.textbbox((0, 0), display_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (width - tw) // 2
    y = (height - th) // 2
    draw.text((x, y), display_text, fill=text_color, font=font)

    credit = f"© {config.CHANNEL_NAME}"
    try:
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except OSError:
        font_sm = font
    draw.text((20, height - 40), credit, fill=(150, 150, 150), font=font_sm)

    img.save(str(output_path), quality=95)
    return output_path


def create_text_card(
    lines: list[str],
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    bg_color: tuple = (20, 20, 50),
    text_color: tuple = (240, 240, 240),
    accent_color: tuple = (200, 160, 80),
) -> Path:
    """文字カード生成。人物画像を使わない安全な素材。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font

    border_w = 4
    draw.rectangle(
        [40, 40, width - 40, height - 40],
        outline=accent_color, width=border_w,
    )

    y_offset = height // 2 - len(lines) * 30
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        color = accent_color if i == 0 else text_color
        draw.text((x, y_offset + i * 60), line, fill=color, font=font)

    credit = f"© {config.CHANNEL_NAME}"
    bbox2 = draw.textbbox((0, 0), credit, font=font_sm)
    draw.text((width - bbox2[2] - 30, height - 50), credit, fill=(100, 100, 100), font=font_sm)

    img.save(str(output_path), quality=95)
    return output_path


def prepare_section_images(
    sections: list[dict],
    output_dir: Path,
    video_config: dict | None = None,
    materials: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """戻り値: (使用画像リスト, 除外素材リスト)"""
    vc = video_config or config.VIDEO_LONG
    w, h = vc["width"], vc["height"]
    output_dir.mkdir(parents=True, exist_ok=True)

    mat_map = {}
    excluded = []
    if materials:
        for mat in materials:
            idx = mat.get("section_index")
            rights = mat.get("rights_status", "REVIEW")

            if rights != "OK":
                excluded.append({
                    "section_index": idx,
                    "image_path": mat.get("image_path", ""),
                    "rights_status": rights,
                    "reason": f"権利ステータスが{rights}のため除外",
                    "source_name": mat.get("source_name", ""),
                })
                print(f"[IMG] 素材除外: セクション{idx} - rights={rights} ({mat.get('source_name', '')})")
                continue

            if idx is not None:
                mat_map[idx] = mat

    results = []
    for i, sec in enumerate(sections):
        img_path = output_dir / f"section_{i:03d}.png"

        if i in mat_map:
            mat = mat_map[i]
            src = Path(mat["image_path"])
            if src.exists() and src.stat().st_size > 0:
                _resize_image(src, img_path, w, h)
                print(f"[IMG] セクション {i}: 素材使用 ({mat.get('source_name', '')})")
                results.append({
                    "index": i,
                    "image_path": str(img_path),
                    "width": w,
                    "height": h,
                    "source": "material",
                    "source_name": mat.get("source_name", ""),
                    "credit_required": mat.get("credit_required", False),
                    "credit_text": mat.get("credit_text", ""),
                    "rights_status": "OK",
                })
                continue
            else:
                print(f"[IMG] セクション {i}: 素材ファイル不正 → プレースホルダー")

        user_img = sec.get("image_path")
        if user_img and Path(user_img).exists():
            rights = sec.get("rights_status", "REVIEW")
            if rights == "OK":
                _resize_image(Path(user_img), img_path, w, h)
                print(f"[IMG] セクション {i}: ユーザー画像使用")
                results.append({
                    "index": i, "image_path": str(img_path),
                    "width": w, "height": h, "source": "user",
                    "rights_status": "OK",
                })
                continue
            else:
                excluded.append({
                    "section_index": i, "image_path": user_img,
                    "rights_status": rights,
                    "reason": f"権利ステータスが{rights}のため除外",
                })
                print(f"[IMG] セクション {i}: rights={rights} → 除外 → プレースホルダー")

        img_hint = sec.get("image_hint", sec.get("text", "")[:30])
        create_placeholder_image(img_hint, img_path, w, h)
        print(f"[IMG] セクション {i}: プレースホルダー生成")
        results.append({
            "index": i, "image_path": str(img_path),
            "width": w, "height": h, "source": "placeholder",
            "rights_status": "OK",
        })

    return results, excluded


def _resize_image(src: Path, dst: Path, width: int, height: int) -> Path:
    img = Image.open(str(src))

    src_ratio = img.width / img.height
    dst_ratio = width / height

    if src_ratio > dst_ratio:
        new_h = height
        new_w = int(height * src_ratio)
    else:
        new_w = width
        new_h = int(width / src_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - width) // 2
    top = (new_h - height) // 2
    img = img.crop((left, top, left + width, top + height))

    img.save(str(dst), quality=95)
    return dst


def create_title_card(
    title: str,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    return create_text_card(
        lines=[title[:30], "", config.CHANNEL_NAME],
        output_path=output_path,
        width=width,
        height=height,
    )


def generate_credits_file(
    image_sections: list[dict],
    excluded: list[dict],
    output_path: Path,
    bgm_used: bool = False,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# クレジット情報 - {config.CHANNEL_NAME}", ""]
    if bgm_used:
        lines.append(f"{config.BGM_CREDIT}")
        lines.append("")

    credits_needed = [s for s in image_sections if s.get("credit_required")]
    if credits_needed:
        lines.append("## 使用素材クレジット")
        for s in credits_needed:
            lines.append(f"- セクション{s['index']}: {s.get('credit_text', '')}")
        lines.append("")

    if excluded:
        lines.append("## 除外素材")
        for e in excluded:
            lines.append(
                f"- セクション{e.get('section_index', '?')}: "
                f"rights={e.get('rights_status', '?')} - {e.get('reason', '')}"
            )
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path
