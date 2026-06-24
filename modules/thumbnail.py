"""
サムネイル生成モジュール (1280x720 PNG)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import FONT_BOLD, FONT_REGULAR

TW, TH = 1280, 720


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    current = ""
    for char in text:
        test = current + char
        if font.getbbox(test)[2] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def generate_thumbnail(title: str, subtitle: str, output_path: str) -> str:
    img = Image.new("RGB", (TW, TH))
    draw = ImageDraw.Draw(img)

    for y in range(TH):
        ratio = y / TH
        r = int(20 + (60 - 20) * ratio)
        g = int(10 + (20 - 10) * ratio)
        b = int(5 + (10 - 5) * ratio)
        draw.line([(0, y), (TW, y)], fill=(r, g, b))

    for i in range(0, TW, 80):
        draw.line([(i, 0), (i + 400, TH)], fill=(255, 255, 255, 5), width=1)

    overlay_box = (0, TH // 2 - 20, TW, TH)
    overlay = Image.new("RGBA", (overlay_box[2] - overlay_box[0], overlay_box[3] - overlay_box[1]), (0, 0, 0, 120))
    img.paste(Image.new("RGB", overlay.size, (0, 0, 0)), (overlay_box[0], overlay_box[1]), mask=overlay.split()[3])

    font_main = _get_font(90)
    max_w = TW - 100
    title_lines = _wrap_text(title, font_main, max_w)

    y_start = 80
    for line in title_lines[:2]:
        bbox = font_main.getbbox(line)
        draw.text((52, y_start + 4), line, font=font_main, fill=(0, 0, 0, 200))
        draw.text((50, y_start), line, font=font_main, fill=(255, 255, 255))
        y_start += (bbox[3] - bbox[1]) + 20

    if subtitle:
        font_sub = _get_font(52, bold=False)
        sub_lines = _wrap_text(subtitle, font_sub, TW - 100)
        for line in sub_lines[:2]:
            bbox = font_sub.getbbox(line)
            draw.text((52, y_start + 4 + 20), line, font=font_sub, fill=(0, 0, 0, 180))
            draw.text((50, y_start + 20), line, font=font_sub, fill=(255, 220, 100))
            y_start += (bbox[3] - bbox[1]) + 12

    draw.rectangle([(0, TH - 80), (TW, TH)], fill=(180, 80, 10))
    font_channel = _get_font(44)
    channel_text = "昭和・平成 なぜそうだったのか"
    bbox = font_channel.getbbox(channel_text)
    cx = (TW - (bbox[2] - bbox[0])) // 2
    draw.text((cx, TH - 66), channel_text, font=font_channel, fill=(255, 255, 255))

    output_path = str(output_path)
    img.save(output_path, "PNG")
    print(f"  [サムネイル] 生成完了 → {output_path}")
    return output_path
