"""画像素材生成モジュール（Pillow使用）"""
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from src.config import FONT_PATH, LONG_VIDEO, SHORTS_VIDEO

logger = logging.getLogger(__name__)

COLORS = {
    "bg_warm": (45, 35, 25),
    "bg_dark": (30, 25, 20),
    "bg_sepia": (62, 48, 38),
    "text_white": (255, 255, 255),
    "text_cream": (245, 235, 210),
    "text_gold": (218, 185, 120),
    "accent_orange": (210, 140, 60),
    "accent_red": (180, 60, 50),
    "overlay": (0, 0, 0, 160),
}


def _get_font(size):
    if FONT_PATH and os.path.exists(FONT_PATH):
        return ImageFont.truetype(FONT_PATH, size)
    return ImageFont.load_default()


def _draw_text_with_border(draw, position, text, font, fill, border_color=(0, 0, 0), border_width=3):
    x, y = position
    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=border_color)
    draw.text(position, text, font=font, fill=fill)


def _draw_centered_text(draw, y, text, font, fill, width, border=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (width - tw) // 2
    if border:
        _draw_text_with_border(draw, (x, y), text, font, fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)


def generate_title_card(title, era, output_path, video_type="long"):
    """タイトルカード生成"""
    if video_type == "long":
        w, h = LONG_VIDEO["width"], LONG_VIDEO["height"]
    else:
        w, h = SHORTS_VIDEO["width"], SHORTS_VIDEO["height"]

    img = Image.new("RGB", (w, h), COLORS["bg_warm"])
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (w, h // 8)], fill=COLORS["bg_dark"])
    draw.rectangle([(0, h - h // 8), (w, h)], fill=COLORS["bg_dark"])

    if video_type == "long":
        font_title = _get_font(64)
        font_era = _get_font(36)
        font_channel = _get_font(28)
    else:
        font_title = _get_font(52)
        font_era = _get_font(30)
        font_channel = _get_font(24)

    _draw_centered_text(draw, h // 2 - 80, title, font_title, COLORS["text_cream"], w)
    _draw_centered_text(draw, h // 2 + 20, era, font_era, COLORS["text_gold"], w)
    _draw_centered_text(draw, h - h // 8 + 20, "昭和・平成 なぜそうだったのか", font_channel, COLORS["text_cream"], w, border=False)

    img.save(output_path, quality=95)
    logger.info(f"タイトルカード生成: {output_path}")
    return output_path


def generate_section_image(section_title, description, era_label, output_path, video_type="long"):
    """セクション画像生成"""
    if video_type == "long":
        w, h = LONG_VIDEO["width"], LONG_VIDEO["height"]
    else:
        w, h = SHORTS_VIDEO["width"], SHORTS_VIDEO["height"]

    img = Image.new("RGB", (w, h), COLORS["bg_sepia"])
    draw = ImageDraw.Draw(img)

    for i in range(0, h, 40):
        opacity = 10 + (i % 80)
        draw.line([(0, i), (w, i)], fill=(opacity, opacity - 5, opacity - 10), width=1)

    if video_type == "long":
        font_section = _get_font(48)
        font_desc = _get_font(32)
        font_era = _get_font(28)
    else:
        font_section = _get_font(40)
        font_desc = _get_font(28)
        font_era = _get_font(24)

    if era_label:
        draw.rectangle([(w - 300, 20), (w - 20, 70)], fill=COLORS["accent_orange"])
        draw.text((w - 290, 25), era_label, font=font_era, fill=COLORS["text_white"])

    _draw_centered_text(draw, h // 3, section_title, font_section, COLORS["text_cream"], w)

    if description:
        lines = _wrap_text(description, 20 if video_type == "shorts" else 30)
        y = h // 2
        for line in lines[:3]:
            _draw_centered_text(draw, y, line, font_desc, COLORS["text_cream"], w)
            y += 50

    draw.text((20, h - 40), "※イメージ", font=_get_font(18), fill=(180, 170, 150))

    img.save(output_path, quality=95)
    logger.info(f"セクション画像生成: {output_path}")
    return output_path


def generate_comparison_image(left_label, right_label, left_desc, right_desc, output_path):
    """比較画像生成（左：当時 右：現代）"""
    w, h = LONG_VIDEO["width"], LONG_VIDEO["height"]
    img = Image.new("RGB", (w, h), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (w // 2 - 5, h)], fill=COLORS["bg_sepia"])
    draw.rectangle([(w // 2 + 5, 0), (w, h)], fill=(40, 50, 60))

    font_label = _get_font(40)
    font_desc = _get_font(28)

    _draw_centered_text(draw, 40, left_label, font_label, COLORS["text_gold"], w // 2)
    _draw_centered_text(draw, 40, right_label, font_label, (150, 200, 255), w // 2)
    draw.text((w // 2 + 5 + (w // 2 - draw.textbbox((0, 0), right_label, font=font_label)[2]) // 2, 40),
              right_label, font=font_label, fill=(150, 200, 255))

    left_lines = _wrap_text(left_desc, 15)
    y = h // 3
    for line in left_lines[:4]:
        _draw_centered_text(draw, y, line, font_desc, COLORS["text_cream"], w // 2)
        y += 45

    right_lines = _wrap_text(right_desc, 15)
    y = h // 3
    for line in right_lines[:4]:
        x_offset = w // 2 + 5
        bbox = draw.textbbox((0, 0), line, font=font_desc)
        tw = bbox[2] - bbox[0]
        x = x_offset + (w // 2 - tw) // 2
        _draw_text_with_border(draw, (x, y), line, font_desc, (220, 230, 240))
        y += 45

    draw.text((20, h - 40), "※イメージ", font=_get_font(18), fill=(180, 170, 150))
    img.save(output_path, quality=95)
    logger.info(f"比較画像生成: {output_path}")
    return output_path


def generate_era_timeline(eras, output_path):
    """年表画像生成"""
    w, h = LONG_VIDEO["width"], LONG_VIDEO["height"]
    img = Image.new("RGB", (w, h), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)

    font_title = _get_font(36)
    font_era = _get_font(24)
    font_desc = _get_font(20)

    _draw_centered_text(draw, 30, "年表", font_title, COLORS["text_gold"], w)

    line_y = 120
    x_start = 100
    x_end = w - 100
    draw.line([(x_start, line_y), (x_end, line_y)], fill=COLORS["accent_orange"], width=3)

    spacing = (x_end - x_start) // max(len(eras) - 1, 1)
    for i, era in enumerate(eras):
        x = x_start + i * spacing
        draw.ellipse([(x - 8, line_y - 8), (x + 8, line_y + 8)], fill=COLORS["accent_orange"])
        draw.text((x - 40, line_y + 20), era.get("year", ""), font=font_era, fill=COLORS["text_gold"])
        desc_lines = _wrap_text(era.get("desc", ""), 12)
        y = line_y + 55
        for dl in desc_lines[:3]:
            draw.text((x - 60, y), dl, font=font_desc, fill=COLORS["text_cream"])
            y += 28

    img.save(output_path, quality=95)
    return output_path


def generate_all_images(theme, sections, output_dir, video_type="long"):
    """テーマに必要な全画像を生成"""
    images = []
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    title_path = os.path.join(img_dir, "title.png")
    generate_title_card(theme, "昭和〜平成", title_path, video_type)
    images.append({"type": "title", "path": title_path})

    for i, section in enumerate(sections):
        path = os.path.join(img_dir, f"section_{i:02d}.png")
        generate_section_image(
            section.get("title", f"セクション{i+1}"),
            section.get("visual", ""),
            section.get("era", ""),
            path,
            video_type,
        )
        images.append({"type": "section", "path": path, "section": section.get("title", "")})

    if video_type == "long":
        comp_path = os.path.join(img_dir, "comparison.png")
        generate_comparison_image(
            "当時", "現代",
            "テレビに布をかけ\nほこりから守っていた",
            "薄型テレビに\nカバーは不要に",
            comp_path,
        )
        images.append({"type": "comparison", "path": comp_path})

        timeline_path = os.path.join(img_dir, "timeline.png")
        generate_era_timeline([
            {"year": "1953年", "desc": "テレビ放送開始"},
            {"year": "1958年", "desc": "普及率約10%"},
            {"year": "1960年", "desc": "カラー放送開始"},
            {"year": "1965年", "desc": "普及率約90%"},
            {"year": "昭和50年代", "desc": "価格低下"},
            {"year": "平成〜", "desc": "液晶テレビ普及"},
        ], timeline_path)
        images.append({"type": "timeline", "path": timeline_path})

    return images


def _wrap_text(text, max_chars):
    if not text:
        return []
    lines = []
    current = ""
    for char in text:
        current += char
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines
