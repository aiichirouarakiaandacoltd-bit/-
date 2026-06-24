"""
スライド画像生成モジュール (Pillow)
各章の背景スライドを1920x1080 PNGとして生成する
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import FONT_BOLD, FONT_REGULAR, CHAPTER_COLORS, CHAPTERS

W, H = 1920, 1080


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _draw_gradient(draw: ImageDraw.ImageDraw, color_top: tuple, color_bottom: tuple):
    for y in range(H):
        ratio = y / H
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple = (255, 255, 255),
    shadow_offset: int = 4,
):
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    current = ""
    for char in text:
        test = current + char
        bbox = font.getbbox(test)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def generate_chapter_title_slide(chapter_name: str, chapter_num: int, output_path: str) -> str:
    colors = CHAPTER_COLORS.get(chapter_name, ((20, 20, 40), (60, 60, 120)))
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw, colors[0], colors[1])

    accent_h = 6
    accent_color = (255, 200, 50)
    draw.rectangle([(0, H // 2 - 100), (W, H // 2 - 100 + accent_h)], fill=accent_color)

    font_num = _get_font(60)
    num_text = f"第{chapter_num}章"
    bbox = font_num.getbbox(num_text)
    x = (W - (bbox[2] - bbox[0])) // 2
    _draw_text_with_shadow(draw, num_text, x, H // 2 - 190, font_num, fill=(255, 220, 100))

    font_title = _get_font(120)
    bbox = font_title.getbbox(chapter_name)
    x = (W - (bbox[2] - bbox[0])) // 2
    _draw_text_with_shadow(draw, chapter_name, x, H // 2 - 80, font_title)

    font_channel = _get_font(36, bold=False)
    channel = "昭和・平成 なぜそうだったのか"
    bbox = font_channel.getbbox(channel)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x, H - 80), channel, font=font_channel, fill=(200, 200, 200))

    img.save(output_path, "PNG")
    return output_path


def generate_content_slide(
    chapter_name: str,
    headline: str,
    chapter_num: int,
    slide_num: int,
    output_path: str,
    is_reiwa_comparison: bool = False,
) -> str:
    colors = CHAPTER_COLORS.get(chapter_name, ((20, 20, 40), (60, 60, 120)))
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    dark_top = tuple(max(0, c - 10) for c in colors[0])
    dark_bot = tuple(max(0, c - 10) for c in colors[1])
    _draw_gradient(draw, dark_top, dark_bot)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 80))
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), mask=overlay.split()[3])

    bar_color = (255, 200, 50)
    draw.rectangle([(80, 40), (80 + 8, 140)], fill=bar_color)

    font_chapter_label = _get_font(32)
    chapter_label = f"第{chapter_num}章：{chapter_name}"
    draw.text((110, 48), chapter_label, font=font_chapter_label, fill=(255, 200, 50))

    font_headline = _get_font(72)
    max_text_w = W - 160
    lines = _wrap_text(headline, font_headline, max_text_w)
    y_start = 200
    for line in lines[:3]:
        bbox = font_headline.getbbox(line)
        _draw_text_with_shadow(draw, line, 80, y_start, font_headline)
        y_start += (bbox[3] - bbox[1]) + 20

    if is_reiwa_comparison:
        draw.rectangle([(W - 320, H - 120), (W - 40, H - 40)], fill=(20, 100, 40, 200))
        font_tag = _get_font(36)
        draw.text((W - 290, H - 100), "令和との比較", font=font_tag, fill=(100, 255, 120))

    font_channel = _get_font(28, bold=False)
    channel = "昭和・平成 なぜそうだったのか"
    draw.text((80, H - 60), channel, font=font_channel, fill=(160, 160, 160))

    img.save(output_path, "PNG")
    return output_path


def generate_ai_image_placeholder(
    chapter_name: str,
    description: str,
    chapter_num: int,
    output_path: str,
) -> str:
    colors = CHAPTER_COLORS.get(chapter_name, ((20, 20, 40), (60, 60, 120)))
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    muted_top = tuple(min(255, c + 20) for c in colors[0])
    muted_bot = tuple(min(255, c + 30) for c in colors[1])
    _draw_gradient(draw, muted_top, muted_bot)

    draw.rectangle([(0, 0), (W, H)], outline=(80, 80, 80), width=3)

    font_desc = _get_font(52)
    max_w = W - 300
    lines = _wrap_text(description, font_desc, max_w)
    total_h = sum(font_desc.getbbox(l)[3] for l in lines) + 20 * len(lines)
    y = (H - total_h) // 2
    for line in lines[:4]:
        bbox = font_desc.getbbox(line)
        x = (W - (bbox[2] - bbox[0])) // 2
        _draw_text_with_shadow(draw, line, x, y, font_desc, fill=(230, 230, 230))
        y += (bbox[3] - bbox[1]) + 20

    font_watermark = _get_font(40)
    wm_text = "再現イメージ"
    bbox = font_watermark.getbbox(wm_text)
    wm_w = bbox[2] - bbox[0]
    draw.rectangle(
        [(W - wm_w - 40, H - 80), (W - 20, H - 20)],
        fill=(0, 0, 0, 160),
    )
    draw.text((W - wm_w - 30, H - 74), wm_text, font=font_watermark, fill=(255, 255, 100))

    font_channel = _get_font(28, bold=False)
    draw.text((30, H - 60), "昭和・平成 なぜそうだったのか", font=font_channel, fill=(160, 160, 160))

    img.save(output_path, "PNG")
    return output_path


def generate_ending_slide(title: str, output_path: str) -> str:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw, (5, 5, 15), (30, 20, 10))

    font_big = _get_font(52)
    lines = _wrap_text(title, font_big, W - 200)
    total_h = sum(font_big.getbbox(l)[3] + 16 for l in lines)
    y = (H - total_h) // 2 - 80
    for line in lines:
        bbox = font_big.getbbox(line)
        x = (W - (bbox[2] - bbox[0])) // 2
        _draw_text_with_shadow(draw, line, x, y, font_big)
        y += (bbox[3] - bbox[1]) + 16

    font_sub = _get_font(44)
    for i, sub_text in enumerate(["チャンネル登録・高評価お願いします", "コメントでご意見をお聞かせください"]):
        bbox = font_sub.getbbox(sub_text)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x, H // 2 + 60 + i * 70), sub_text, font=font_sub, fill=(200, 180, 100))

    font_channel = _get_font(36)
    channel = "昭和・平成 なぜそうだったのか"
    bbox = font_channel.getbbox(channel)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x, H - 80), channel, font=font_channel, fill=(150, 150, 150))

    img.save(output_path, "PNG")
    return output_path


IMAGE_DESCRIPTIONS = {
    "共感": [
        "昭和の居間　家族がテレビを囲む",
        "ブラウン管テレビ　夕方の光",
        "家族の団欒　夕食とテレビ",
    ],
    "発見": [
        "昭和30年代　テレビの登場",
        "チャンネルを回す子供",
        "砂嵐のブラウン管",
        "昭和の街頭テレビ",
    ],
    "考察": [
        "集中してテレビを見る家族",
        "感情を共有する昭和の家族",
        "子供の頃の記憶　臨界期",
    ],
    "令和比較": [
        "令和のバラバラ視聴　スマートフォン",
        "個人化するメディア消費",
        "失われた共通言語",
    ],
    "余韻": [
        "夕暮れの昭和の居間",
        "記憶に残る家族の時間",
    ],
}


def generate_all_slides(script: dict, output_dir: str) -> dict[str, list[str]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_slides = {}

    chapter_names = list(script["chapters"].keys())

    for i, (chapter_name, chapter_data) in enumerate(script["chapters"].items()):
        chapter_num = i + 1
        slides = []

        title_path = str(output_dir / f"slide_{chapter_name}_00_title.png")
        generate_chapter_title_slide(chapter_name, chapter_num, title_path)
        slides.append(title_path)

        descriptions = IMAGE_DESCRIPTIONS.get(chapter_name, ["昭和・平成の記憶", "時代の風景"])
        is_reiwa = chapter_name == "令和比較"

        for j, desc in enumerate(descriptions[:3]):
            content_path = str(output_dir / f"slide_{chapter_name}_{j+1:02d}_content.png")
            generate_ai_image_placeholder(chapter_name, desc, chapter_num, content_path)
            slides.append(content_path)

            if j == 0:
                headline_path = str(output_dir / f"slide_{chapter_name}_{j+1:02d}_headline.png")
                generate_content_slide(
                    chapter_name,
                    chapter_data.get("headline", chapter_name),
                    chapter_num,
                    j,
                    headline_path,
                    is_reiwa_comparison=is_reiwa,
                )
                slides.insert(-1, headline_path)

        all_slides[chapter_name] = slides
        print(f"  [スライド] {chapter_name}: {len(slides)}枚 生成完了")

    ending_path = str(output_dir / "slide_ending.png")
    generate_ending_slide(script.get("title", ""), ending_path)
    all_slides["_ending"] = [ending_path]

    return all_slides
