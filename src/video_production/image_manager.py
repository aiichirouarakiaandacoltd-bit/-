"""画像管理モジュール

セクションごとの背景画像を管理する。
AI生成による実在皇族の顔画像は禁止。
rights_status が OK のもののみ使用。
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
    draw.text((20, height - 40), credit, fill=(150, 150, 150), font=font)

    img.save(str(output_path), quality=95)
    return output_path


def prepare_section_images(
    sections: list[dict],
    output_dir: Path,
    video_config: dict | None = None,
) -> list[dict]:
    vc = video_config or config.VIDEO_LONG
    w, h = vc["width"], vc["height"]
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, sec in enumerate(sections):
        img_hint = sec.get("image_hint", sec.get("text", "")[:30])
        img_path = output_dir / f"section_{i:03d}.png"

        user_img = sec.get("image_path")
        if user_img and Path(user_img).exists():
            rights = sec.get("rights_status", "REVIEW")
            if rights == "OK":
                _resize_image(Path(user_img), img_path, w, h)
                print(f"[IMG] セクション {i}: ユーザー画像使用")
            else:
                print(f"[IMG] セクション {i}: 権利ステータス={rights} → プレースホルダー使用")
                create_placeholder_image(img_hint, img_path, w, h)
        else:
            create_placeholder_image(img_hint, img_path, w, h)
            print(f"[IMG] セクション {i}: プレースホルダー生成")

        results.append({
            "index": i,
            "image_path": str(img_path),
            "width": w,
            "height": h,
        })

    return results


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
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (width, height), (10, 10, 40))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 52)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = font_large

    bbox = draw.textbbox((0, 0), title[:30], font=font_large)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    draw.text((x, height // 2 - 30), title[:30], fill="white", font=font_large)

    ch = config.CHANNEL_NAME
    bbox2 = draw.textbbox((0, 0), ch, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((width - tw2) // 2, height // 2 + 50), ch, fill=(200, 200, 200), font=font_small)

    img.save(str(output_path), quality=95)
    return output_path
