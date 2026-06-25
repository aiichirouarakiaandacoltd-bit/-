"""
素材管理モジュール (Material/Asset Management Module)

昭和・平成動画自動制作システム用の素材生成・権利管理モジュール。
Pillowを使用してテキストカード、タイムライン、比較チャート等の画像素材を生成し、
全素材の権利情報をJSON/Markdown/テキスト形式で追跡・出力する。
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger(__name__)

# --- 解像度定数 ---
RESOLUTION_LONG: Tuple[int, int] = (1920, 1080)
RESOLUTION_SHORTS: Tuple[int, int] = (1080, 1920)

# --- フォントパス ---
FONT_PATH_PRIMARY = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_PATH_FALLBACKS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# --- 配色 (ノスタルジックな暖色系) ---
COLOR_SEPIA_BG = (62, 47, 35)           # 濃いセピア背景
COLOR_SEPIA_LIGHT = (210, 180, 140)     # 薄いセピア
COLOR_WARM_WHITE = (255, 248, 235)      # 温かみのある白
COLOR_WARM_CREAM = (245, 235, 215)      # クリーム色
COLOR_GOLD = (218, 165, 32)             # ゴールド
COLOR_DARK_BROWN = (80, 50, 30)         # 濃い茶色
COLOR_ACCENT_RED = (180, 60, 40)        # アクセント赤
COLOR_ACCENT_NAVY = (40, 60, 100)       # アクセント紺
COLOR_SHADOW = (30, 20, 10)             # 影色
COLOR_SUBTITLE_BG = (0, 0, 0, 180)     # 字幕背景 (半透明黒)

# --- グラデーション方向 ---
GRADIENT_VERTICAL = "vertical"
GRADIENT_HORIZONTAL = "horizontal"
GRADIENT_DIAGONAL = "diagonal"


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """
    指定サイズのNoto Sans CJK JPフォントを読み込む。
    プライマリフォントが見つからない場合はフォールバックを試行する。

    Args:
        size: フォントサイズ (ピクセル)
        bold: Boldフォントを優先するか

    Returns:
        読み込まれたフォントオブジェクト

    Raises:
        RuntimeError: すべてのフォントパスで読み込みに失敗した場合
    """
    paths_to_try = [FONT_PATH_PRIMARY] + FONT_PATH_FALLBACKS

    for font_path in paths_to_try:
        if os.path.isfile(font_path):
            try:
                font = ImageFont.truetype(font_path, size)
                return font
            except (OSError, IOError) as e:
                logger.warning(f"フォント読み込み失敗: {font_path} - {e}")
                continue

    # すべてのフォントが見つからない場合、デフォルトフォントを使用
    logger.warning(
        "日本語フォントが見つかりません。デフォルトフォントを使用します。"
        "日本語テキストが正しく表示されない場合があります。"
    )
    try:
        return ImageFont.load_default()
    except Exception:
        raise RuntimeError(
            "フォントの読み込みに失敗しました。"
            f"Noto Sans CJK JPを {FONT_PATH_PRIMARY} にインストールしてください。"
        )


def create_gradient_background(
    size: Tuple[int, int],
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    direction: str = GRADIENT_VERTICAL,
) -> Image.Image:
    """
    グラデーション背景画像を生成する。

    Args:
        size: 画像サイズ (width, height)
        color1: 開始色 (R, G, B)
        color2: 終了色 (R, G, B)
        direction: グラデーション方向

    Returns:
        グラデーション背景の Image オブジェクト
    """
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            if direction == GRADIENT_VERTICAL:
                ratio = y / max(height - 1, 1)
            elif direction == GRADIENT_HORIZONTAL:
                ratio = x / max(width - 1, 1)
            elif direction == GRADIENT_DIAGONAL:
                ratio = (x + y) / max(width + height - 2, 1)
            else:
                ratio = y / max(height - 1, 1)

            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            pixels[x, y] = (r, g, b)

    return image


def _create_solid_background(
    size: Tuple[int, int],
    color: Tuple[int, int, int],
) -> Image.Image:
    """単色背景画像を生成する。"""
    return Image.new("RGB", size, color)


def _create_pattern_background(
    size: Tuple[int, int],
    base_color: Tuple[int, int, int],
    pattern_type: str = "dots",
) -> Image.Image:
    """
    微細パターン付き背景画像を生成する。

    Args:
        size: 画像サイズ
        base_color: ベース色
        pattern_type: パターン種類 ("dots", "lines", "crosshatch")

    Returns:
        パターン付き背景の Image オブジェクト
    """
    image = Image.new("RGB", size, base_color)
    draw = ImageDraw.Draw(image)
    width, height = size

    # パターン色（ベース色より少し暗め/明るめ）
    pattern_color = (
        max(0, base_color[0] - 15),
        max(0, base_color[1] - 12),
        max(0, base_color[2] - 10),
    )

    if pattern_type == "dots":
        spacing = 30
        dot_radius = 2
        for y in range(0, height, spacing):
            offset = spacing // 2 if (y // spacing) % 2 == 1 else 0
            for x in range(offset, width, spacing):
                draw.ellipse(
                    [x - dot_radius, y - dot_radius,
                     x + dot_radius, y + dot_radius],
                    fill=pattern_color,
                )

    elif pattern_type == "lines":
        spacing = 20
        for y in range(0, height, spacing):
            draw.line([(0, y), (width, y)], fill=pattern_color, width=1)

    elif pattern_type == "crosshatch":
        spacing = 40
        for i in range(-height, width + height, spacing):
            draw.line([(i, 0), (i + height, height)], fill=pattern_color, width=1)
            draw.line([(i, height), (i + height, 0)], fill=pattern_color, width=1)

    return image


def _draw_decorative_border(
    draw: ImageDraw.Draw,
    size: Tuple[int, int],
    border_color: Tuple[int, int, int] = COLOR_GOLD,
    margin: int = 40,
    width: int = 3,
) -> None:
    """装飾的な枠線を描画する。"""
    w, h = size
    # 外枠
    draw.rectangle(
        [margin, margin, w - margin, h - margin],
        outline=border_color,
        width=width,
    )
    # 内側に細い線
    inner_margin = margin + 8
    draw.rectangle(
        [inner_margin, inner_margin, w - inner_margin, h - inner_margin],
        outline=border_color,
        width=1,
    )


def _draw_text_with_shadow(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int] = COLOR_WARM_WHITE,
    shadow_color: Tuple[int, int, int] = COLOR_SHADOW,
    shadow_offset: int = 3,
) -> None:
    """影付きテキストを描画する。"""
    x, y = position
    # 影
    draw.text((x + shadow_offset, y + shadow_offset), text,
              font=font, fill=shadow_color)
    # 本体
    draw.text((x, y), text, font=font, fill=fill)


def _get_text_size(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> Tuple[int, int]:
    """テキストのバウンディングボックスサイズを取得する。"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.Draw,
) -> List[str]:
    """
    テキストを指定幅に収まるように折り返す。

    Args:
        text: 折り返すテキスト
        font: 使用フォント
        max_width: 最大幅 (ピクセル)
        draw: ImageDraw オブジェクト

    Returns:
        折り返されたテキスト行のリスト
    """
    lines: List[str] = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        tw, _ = _get_text_size(draw, test_line, font)
        if tw <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


def _draw_centered_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    y: int,
    image_width: int,
    fill: Tuple[int, int, int] = COLOR_WARM_WHITE,
    shadow: bool = True,
    shadow_color: Tuple[int, int, int] = COLOR_SHADOW,
    shadow_offset: int = 3,
) -> int:
    """
    テキストを水平中央揃えで描画する。

    Returns:
        描画後のY座標（次のテキストの開始位置）
    """
    tw, th = _get_text_size(draw, text, font)
    x = (image_width - tw) // 2

    if shadow:
        _draw_text_with_shadow(draw, (x, y), text, font, fill,
                               shadow_color, shadow_offset)
    else:
        draw.text((x, y), text, font=font, fill=fill)

    return y + th


def _draw_multiline_centered(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    center_y: int,
    image_width: int,
    max_text_width: int,
    line_spacing: int = 15,
    fill: Tuple[int, int, int] = COLOR_WARM_WHITE,
    shadow: bool = True,
) -> int:
    """
    複数行テキストを水平中央・垂直中央揃えで描画する。

    Args:
        draw: ImageDraw オブジェクト
        text: 描画するテキスト
        font: フォント
        center_y: 垂直中央のY座標
        image_width: 画像幅
        max_text_width: テキスト折り返し最大幅
        line_spacing: 行間 (ピクセル)
        fill: テキスト色
        shadow: 影を付けるか

    Returns:
        描画領域の下端Y座標
    """
    lines = _wrap_text(text, font, max_text_width, draw)

    # 全行の高さを計算
    line_heights = []
    for line in lines:
        _, th = _get_text_size(draw, line, font)
        line_heights.append(th)

    total_height = sum(line_heights) + line_spacing * max(0, len(lines) - 1)
    start_y = center_y - total_height // 2

    current_y = start_y
    for i, line in enumerate(lines):
        _draw_centered_text(draw, line, font, current_y, image_width,
                            fill=fill, shadow=shadow)
        current_y += line_heights[i] + line_spacing

    return current_y


class MaterialGenerator:
    """
    素材画像を生成するクラス。

    タイトルカード、チャプターカード、年代カード、比較チャート、
    タイムライン、イメージプレースホルダー等を生成する。
    """

    def __init__(self, default_resolution: Tuple[int, int] = RESOLUTION_LONG):
        """
        Args:
            default_resolution: デフォルトの画像解像度 (width, height)
        """
        self.default_resolution = default_resolution
        logger.info(f"MaterialGenerator 初期化: 解像度 {default_resolution}")

    def generate_title_card(
        self,
        title: str,
        output_path: str,
        resolution: Optional[Tuple[int, int]] = None,
        subtitle: Optional[str] = None,
    ) -> str:
        """
        タイトルカード画像を生成する。

        Args:
            title: タイトルテキスト
            output_path: 出力ファイルパス
            resolution: 画像解像度 (None の場合デフォルト使用)
            subtitle: サブタイトルテキスト (任意)

        Returns:
            出力ファイルパス
        """
        res = resolution or self.default_resolution
        width, height = res
        logger.info(f"タイトルカード生成: '{title}' -> {output_path}")

        # グラデーション背景
        image = create_gradient_background(
            res, COLOR_SEPIA_BG, COLOR_DARK_BROWN, GRADIENT_VERTICAL
        )
        draw = ImageDraw.Draw(image)

        # 装飾枠
        border_margin = int(min(width, height) * 0.04)
        _draw_decorative_border(draw, res, COLOR_GOLD,
                                margin=border_margin, width=3)

        # チャンネル名 (上部)
        channel_font_size = int(min(width, height) * 0.028)
        channel_font = get_font(channel_font_size)
        channel_name = "昭和・平成 なぜそうだったのか"
        channel_y = int(height * 0.1)
        _draw_centered_text(draw, channel_name, channel_font, channel_y,
                            width, fill=COLOR_GOLD, shadow=True)

        # 装飾ライン
        line_y = int(height * 0.18)
        line_width_px = int(width * 0.5)
        line_x_start = (width - line_width_px) // 2
        draw.line(
            [(line_x_start, line_y), (line_x_start + line_width_px, line_y)],
            fill=COLOR_GOLD, width=2,
        )

        # タイトルテキスト（中央）
        title_font_size = int(min(width, height) * 0.065)
        title_font = get_font(title_font_size)
        max_text_width = int(width * 0.75)
        title_center_y = int(height * 0.45)

        _draw_multiline_centered(
            draw, title, title_font, title_center_y, width, max_text_width,
            line_spacing=int(title_font_size * 0.4),
            fill=COLOR_WARM_WHITE, shadow=True,
        )

        # サブタイトル
        if subtitle:
            sub_font_size = int(min(width, height) * 0.035)
            sub_font = get_font(sub_font_size)
            sub_y = int(height * 0.72)
            _draw_centered_text(draw, subtitle, sub_font, sub_y, width,
                                fill=COLOR_SEPIA_LIGHT, shadow=True)

        # 下部装飾ライン
        bottom_line_y = int(height * 0.85)
        draw.line(
            [(line_x_start, bottom_line_y),
             (line_x_start + line_width_px, bottom_line_y)],
            fill=COLOR_GOLD, width=2,
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PNG", quality=95)
        logger.info(f"タイトルカード保存完了: {output_path}")
        return output_path

    def generate_chapter_card(
        self,
        chapter_title: str,
        chapter_number: int,
        output_path: str,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        チャプター見出しカード画像を生成する。

        Args:
            chapter_title: チャプタータイトル
            chapter_number: チャプター番号
            output_path: 出力ファイルパス
            resolution: 画像解像度

        Returns:
            出力ファイルパス
        """
        res = resolution or self.default_resolution
        width, height = res
        logger.info(
            f"チャプターカード生成: 第{chapter_number}章 '{chapter_title}' -> {output_path}"
        )

        # パターン背景
        image = _create_pattern_background(res, COLOR_SEPIA_BG, "dots")
        draw = ImageDraw.Draw(image)

        # 左サイドのアクセントバー
        bar_width = int(width * 0.008)
        bar_x = int(width * 0.08)
        bar_y_start = int(height * 0.25)
        bar_y_end = int(height * 0.75)
        draw.rectangle(
            [bar_x, bar_y_start, bar_x + bar_width, bar_y_end],
            fill=COLOR_GOLD,
        )

        # チャプター番号
        num_font_size = int(min(width, height) * 0.12)
        num_font = get_font(num_font_size)
        num_text = f"{chapter_number:02d}"
        num_x = int(width * 0.12)
        num_y = int(height * 0.28)
        _draw_text_with_shadow(draw, (num_x, num_y), num_text, num_font,
                               fill=COLOR_GOLD, shadow_offset=4)

        # "Chapter" ラベル (小さめ)
        label_font_size = int(min(width, height) * 0.025)
        label_font = get_font(label_font_size)
        label_y = int(height * 0.25)
        draw.text((num_x, label_y), "Chapter", font=label_font,
                  fill=COLOR_SEPIA_LIGHT)

        # チャプタータイトル
        title_font_size = int(min(width, height) * 0.055)
        title_font = get_font(title_font_size)
        title_x = int(width * 0.12)
        title_y = int(height * 0.55)
        max_text_width = int(width * 0.75)

        lines = _wrap_text(chapter_title, title_font, max_text_width, draw)
        current_y = title_y
        for line in lines:
            _draw_text_with_shadow(draw, (title_x, current_y), line,
                                   title_font, fill=COLOR_WARM_WHITE,
                                   shadow_offset=3)
            _, th = _get_text_size(draw, line, title_font)
            current_y += th + int(title_font_size * 0.3)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PNG", quality=95)
        logger.info(f"チャプターカード保存完了: {output_path}")
        return output_path

    def generate_era_card(
        self,
        era_name: str,
        output_path: str,
        resolution: Optional[Tuple[int, int]] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        年代表示カード画像を生成する。

        Args:
            era_name: 年代名 (例: "昭和30年代")
            output_path: 出力ファイルパス
            resolution: 画像解像度
            description: 年代の補足説明 (任意)

        Returns:
            出力ファイルパス
        """
        res = resolution or self.default_resolution
        width, height = res
        logger.info(f"年代カード生成: '{era_name}' -> {output_path}")

        # グラデーション背景（暗めから明るめセピア）
        image = create_gradient_background(
            res, COLOR_DARK_BROWN, COLOR_SEPIA_BG, GRADIENT_DIAGONAL
        )
        draw = ImageDraw.Draw(image)

        # 中央の円形装飾
        center_x = width // 2
        center_y = height // 2
        circle_radius = int(min(width, height) * 0.25)
        draw.ellipse(
            [center_x - circle_radius, center_y - circle_radius,
             center_x + circle_radius, center_y + circle_radius],
            outline=COLOR_GOLD, width=3,
        )
        # 内側の円
        inner_radius = circle_radius - 10
        draw.ellipse(
            [center_x - inner_radius, center_y - inner_radius,
             center_x + inner_radius, center_y + inner_radius],
            outline=COLOR_GOLD, width=1,
        )

        # 年代テキスト（大きく中央に）
        era_font_size = int(min(width, height) * 0.08)
        era_font = get_font(era_font_size)
        era_tw, era_th = _get_text_size(draw, era_name, era_font)
        era_x = (width - era_tw) // 2
        era_y = center_y - era_th // 2
        _draw_text_with_shadow(draw, (era_x, era_y), era_name, era_font,
                               fill=COLOR_WARM_WHITE, shadow_offset=4)

        # 補足説明（あれば）
        if description:
            desc_font_size = int(min(width, height) * 0.03)
            desc_font = get_font(desc_font_size)
            desc_y = center_y + circle_radius + int(height * 0.05)
            _draw_centered_text(draw, description, desc_font, desc_y,
                                width, fill=COLOR_SEPIA_LIGHT, shadow=True)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PNG", quality=95)
        logger.info(f"年代カード保存完了: {output_path}")
        return output_path

    def generate_comparison_chart(
        self,
        title: str,
        items: List[Dict[str, Any]],
        output_path: str,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        比較チャート画像を生成する。

        Args:
            title: チャートタイトル
            items: 比較項目リスト。各項目は {"label": str, "value": str} 形式。
                   オプションで "bar_ratio" (0.0-1.0) を含めるとバーグラフを描画。
            output_path: 出力ファイルパス
            resolution: 画像解像度

        Returns:
            出力ファイルパス
        """
        res = resolution or self.default_resolution
        width, height = res
        logger.info(f"比較チャート生成: '{title}' ({len(items)}項目) -> {output_path}")

        # 背景
        image = _create_pattern_background(res, COLOR_SEPIA_BG, "lines")
        draw = ImageDraw.Draw(image)

        # 枠線
        border_margin = int(min(width, height) * 0.04)
        _draw_decorative_border(draw, res, COLOR_GOLD,
                                margin=border_margin, width=2)

        # タイトル
        title_font_size = int(min(width, height) * 0.05)
        title_font = get_font(title_font_size)
        title_y = int(height * 0.08)
        _draw_centered_text(draw, title, title_font, title_y, width,
                            fill=COLOR_WARM_WHITE, shadow=True)

        # 区切り線
        sep_y = int(height * 0.17)
        sep_margin = int(width * 0.1)
        draw.line([(sep_margin, sep_y), (width - sep_margin, sep_y)],
                  fill=COLOR_GOLD, width=2)

        # 項目描画エリア
        if not items:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path, "PNG", quality=95)
            return output_path

        items_start_y = int(height * 0.22)
        items_end_y = int(height * 0.90)
        available_height = items_end_y - items_start_y
        item_height = available_height // len(items)
        item_margin_x = int(width * 0.1)
        bar_max_width = int(width * 0.45)

        label_font_size = int(min(width, height) * 0.032)
        label_font = get_font(label_font_size)
        value_font_size = int(min(width, height) * 0.03)
        value_font = get_font(value_font_size)

        for i, item in enumerate(items):
            item_y = items_start_y + i * item_height
            label = item.get("label", "")
            value = item.get("value", "")
            bar_ratio = item.get("bar_ratio", None)

            # ラベル
            label_y = item_y + int(item_height * 0.15)
            _draw_text_with_shadow(draw, (item_margin_x, label_y), label,
                                   label_font, fill=COLOR_WARM_WHITE,
                                   shadow_offset=2)

            # バーグラフ（bar_ratioがある場合）
            if bar_ratio is not None:
                bar_y = label_y + int(label_font_size * 1.5)
                bar_height_px = int(item_height * 0.25)
                bar_width_px = int(bar_max_width * min(1.0, max(0.0, bar_ratio)))

                # バー背景
                draw.rectangle(
                    [item_margin_x, bar_y,
                     item_margin_x + bar_max_width, bar_y + bar_height_px],
                    fill=COLOR_DARK_BROWN, outline=COLOR_SEPIA_LIGHT, width=1,
                )
                # バー本体
                if bar_width_px > 0:
                    draw.rectangle(
                        [item_margin_x, bar_y,
                         item_margin_x + bar_width_px, bar_y + bar_height_px],
                        fill=COLOR_GOLD,
                    )

                # 値テキスト（バーの右側）
                value_x = item_margin_x + bar_max_width + int(width * 0.03)
                value_y = bar_y + (bar_height_px - value_font_size) // 2
                draw.text((value_x, value_y), value, font=value_font,
                          fill=COLOR_WARM_CREAM)
            else:
                # バーグラフなし: 値をラベルの右に表示
                value_x = int(width * 0.55)
                draw.text((value_x, label_y), value, font=value_font,
                          fill=COLOR_WARM_CREAM)

            # 項目間区切り線
            if i < len(items) - 1:
                sep_item_y = item_y + item_height - 2
                draw.line(
                    [(item_margin_x, sep_item_y),
                     (width - item_margin_x, sep_item_y)],
                    fill=(100, 80, 60), width=1,
                )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PNG", quality=95)
        logger.info(f"比較チャート保存完了: {output_path}")
        return output_path

    def generate_timeline(
        self,
        title: str,
        events: List[Dict[str, str]],
        output_path: str,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        タイムライン画像を生成する。

        Args:
            title: タイムラインのタイトル
            events: イベントリスト。各イベントは {"year": str, "event": str} 形式。
                    オプションで "value" (数値表示用) を含められる。
            output_path: 出力ファイルパス
            resolution: 画像解像度

        Returns:
            出力ファイルパス
        """
        res = resolution or self.default_resolution
        width, height = res
        logger.info(f"タイムライン生成: '{title}' ({len(events)}件) -> {output_path}")

        # グラデーション背景
        image = create_gradient_background(
            res, COLOR_SEPIA_BG, (45, 35, 25), GRADIENT_VERTICAL
        )
        draw = ImageDraw.Draw(image)

        # タイトル
        title_font_size = int(min(width, height) * 0.045)
        title_font = get_font(title_font_size)
        title_y = int(height * 0.06)
        _draw_centered_text(draw, title, title_font, title_y, width,
                            fill=COLOR_WARM_WHITE, shadow=True)

        if not events:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path, "PNG", quality=95)
            return output_path

        # タイムライン軸
        timeline_x = int(width * 0.15)
        timeline_start_y = int(height * 0.18)
        timeline_end_y = int(height * 0.92)
        timeline_height = timeline_end_y - timeline_start_y

        # 軸線
        draw.line(
            [(timeline_x, timeline_start_y),
             (timeline_x, timeline_end_y)],
            fill=COLOR_GOLD, width=3,
        )

        # イベント描画
        event_spacing = timeline_height // max(len(events), 1)
        year_font_size = int(min(width, height) * 0.032)
        year_font = get_font(year_font_size)
        event_font_size = int(min(width, height) * 0.028)
        event_font = get_font(event_font_size)
        value_font_size = int(min(width, height) * 0.024)
        value_font = get_font(value_font_size)

        dot_radius = int(min(width, height) * 0.008)
        max_event_width = int(width * 0.55)

        for i, event_data in enumerate(events):
            event_y = timeline_start_y + i * event_spacing + event_spacing // 2
            year = event_data.get("year", "")
            event_text = event_data.get("event", "")
            value_text = event_data.get("value", "")

            # 軸上のドット
            draw.ellipse(
                [timeline_x - dot_radius, event_y - dot_radius,
                 timeline_x + dot_radius, event_y + dot_radius],
                fill=COLOR_GOLD,
            )

            # 横線（ドットからイベントテキストへ）
            line_end_x = timeline_x + int(width * 0.06)
            draw.line(
                [(timeline_x + dot_radius, event_y),
                 (line_end_x, event_y)],
                fill=COLOR_GOLD, width=1,
            )

            # 年ラベル（軸の左側に配置、右揃え）
            year_tw, year_th = _get_text_size(draw, year, year_font)
            year_x = timeline_x - int(width * 0.02) - year_tw
            year_y = event_y - year_th // 2
            _draw_text_with_shadow(draw, (year_x, year_y), year, year_font,
                                   fill=COLOR_GOLD, shadow_offset=2)

            # イベントテキスト（軸の右側）
            event_x = line_end_x + int(width * 0.015)
            event_lines = _wrap_text(event_text, event_font,
                                     max_event_width, draw)
            current_ey = event_y - (len(event_lines) * (event_font_size + 5)) // 2
            for eline in event_lines:
                _draw_text_with_shadow(
                    draw, (event_x, current_ey), eline, event_font,
                    fill=COLOR_WARM_WHITE, shadow_offset=2,
                )
                current_ey += event_font_size + 5

            # 数値テキスト（あれば）
            if value_text:
                value_x = event_x
                draw.text((value_x, current_ey + 3), value_text,
                          font=value_font, fill=COLOR_SEPIA_LIGHT)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PNG", quality=95)
        logger.info(f"タイムライン保存完了: {output_path}")
        return output_path

    def generate_image_placeholder(
        self,
        label: str,
        output_path: str,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> str:
        """
        イメージラベル付きプレースホルダー画像を生成する。
        ノスタルジックなシーンの代替画像として使用。

        Args:
            label: プレースホルダーのラベルテキスト
            output_path: 出力ファイルパス
            resolution: 画像解像度

        Returns:
            出力ファイルパス
        """
        res = resolution or self.default_resolution
        width, height = res
        logger.info(f"イメージプレースホルダー生成: '{label}' -> {output_path}")

        # 温かみのある単色背景
        image = create_gradient_background(
            res, COLOR_WARM_CREAM, COLOR_SEPIA_LIGHT, GRADIENT_VERTICAL
        )
        draw = ImageDraw.Draw(image)

        # 中央にラベルテキスト
        label_font_size = int(min(width, height) * 0.045)
        label_font = get_font(label_font_size)
        max_text_width = int(width * 0.7)
        center_y = int(height * 0.45)
        _draw_multiline_centered(
            draw, label, label_font, center_y, width, max_text_width,
            fill=COLOR_DARK_BROWN, shadow=False,
        )

        # 「イメージ」ラベルを右下に追加
        image = self._add_image_label_to_image(image)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PNG", quality=95)
        logger.info(f"イメージプレースホルダー保存完了: {output_path}")
        return output_path

    def _add_image_label_to_image(self, image: Image.Image) -> Image.Image:
        """
        画像に「イメージ」ラベルオーバーレイを追加する (内部メソッド)。

        Args:
            image: 元画像

        Returns:
            ラベル追加後の画像
        """
        width, height = image.size
        # RGBA に変換してオーバーレイ
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        label_text = "イメージ"
        label_font_size = int(min(width, height) * 0.025)
        label_font = get_font(label_font_size)

        label_tw, label_th = _get_text_size(overlay_draw, label_text, label_font)

        padding_x = int(label_tw * 0.3)
        padding_y = int(label_th * 0.3)
        margin = int(min(width, height) * 0.03)

        box_x1 = width - margin - label_tw - padding_x * 2
        box_y1 = height - margin - label_th - padding_y * 2
        box_x2 = width - margin
        box_y2 = height - margin

        # 半透明黒背景
        overlay_draw.rectangle(
            [box_x1, box_y1, box_x2, box_y2],
            fill=(0, 0, 0, 180),
        )

        # テキスト
        text_x = box_x1 + padding_x
        text_y = box_y1 + padding_y
        overlay_draw.text((text_x, text_y), label_text, font=label_font,
                          fill=(255, 255, 255, 230))

        result = Image.alpha_composite(image, overlay)
        return result.convert("RGB")

    def add_image_label(
        self,
        image_path: str,
        label: str = "イメージ",
        output_path: Optional[str] = None,
    ) -> str:
        """
        既存画像に「イメージ」ラベルオーバーレイを追加する。

        Args:
            image_path: 元画像ファイルパス
            label: ラベルテキスト (デフォルト: "イメージ")
            output_path: 出力パス (None の場合、元画像を上書き)

        Returns:
            出力ファイルパス
        """
        if output_path is None:
            output_path = image_path

        logger.info(f"イメージラベル追加: '{label}' -> {image_path}")

        try:
            image = Image.open(image_path)
        except (OSError, IOError) as e:
            raise RuntimeError(f"画像ファイルを開けません: {image_path} - {e}")

        width, height = image.size

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        label_font_size = int(min(width, height) * 0.025)
        label_font = get_font(label_font_size)

        label_tw, label_th = _get_text_size(overlay_draw, label, label_font)

        padding_x = int(label_tw * 0.3)
        padding_y = int(label_th * 0.3)
        margin = int(min(width, height) * 0.03)

        box_x1 = width - margin - label_tw - padding_x * 2
        box_y1 = height - margin - label_th - padding_y * 2
        box_x2 = width - margin
        box_y2 = height - margin

        overlay_draw.rectangle(
            [box_x1, box_y1, box_x2, box_y2],
            fill=(0, 0, 0, 180),
        )

        text_x = box_x1 + padding_x
        text_y = box_y1 + padding_y
        overlay_draw.text((text_x, text_y), label, font=label_font,
                          fill=(255, 255, 255, 230))

        result = Image.alpha_composite(image, overlay)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        result.convert("RGB").save(output_path, "PNG", quality=95)
        logger.info(f"イメージラベル追加完了: {output_path}")
        return output_path

    def generate_topic_materials(
        self,
        topic: str,
        output_dir: str,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        テレビの布トピック用の全素材を一括生成するメインエントリーポイント。

        Args:
            topic: トピック名 (現在は "tv_cloth" のみ対応)
            output_dir: 出力ディレクトリ
            resolution: 画像解像度

        Returns:
            生成結果の辞書 {"materials": List, "tracker": MaterialTracker}
        """
        res = resolution or self.default_resolution
        os.makedirs(output_dir, exist_ok=True)
        tracker = MaterialTracker()

        logger.info(f"トピック素材一括生成開始: topic={topic}, output_dir={output_dir}")

        if topic == "tv_cloth":
            return self._generate_tv_cloth_materials(output_dir, res, tracker)
        else:
            logger.warning(f"未対応トピック: {topic}。デフォルトのタイトルカードのみ生成します。")
            title_path = os.path.join(output_dir, "title_card.png")
            self.generate_title_card(topic, title_path, res)
            tracker.add_material(
                file_path=title_path,
                source_name="自動生成",
                image_type="title_card",
                generated_by_ai=False,
                description=f"タイトルカード: {topic}",
            )
            return {
                "materials": tracker.get_all_materials(),
                "tracker": tracker,
            }

    def _generate_tv_cloth_materials(
        self,
        output_dir: str,
        resolution: Tuple[int, int],
        tracker: MaterialTracker,
    ) -> Dict[str, Any]:
        """テレビの布トピック用素材を生成する内部メソッド。"""

        generated_paths: List[str] = []

        # 1. タイトルカード
        title_path = os.path.join(output_dir, "title_card.png")
        self.generate_title_card(
            "なぜ昔のテレビには布をかけていたのか",
            title_path, resolution,
            subtitle="昭和の居間に必ずあった「テレビの布」の謎に迫る",
        )
        tracker.add_material(
            file_path=title_path,
            source_name="自動生成",
            image_type="title_card",
            generated_by_ai=False,
            description="メインタイトルカード",
        )
        generated_paths.append(title_path)

        # 2. チャプターカード
        chapters = [
            "テレビがやってきた日",
            "布をかけた本当の理由",
            "テレビと日本人の暮らし",
            "布文化の衰退",
            "現代に残る名残",
        ]
        for i, chapter_title in enumerate(chapters, 1):
            chapter_path = os.path.join(output_dir, f"chapter_{i:02d}.png")
            self.generate_chapter_card(chapter_title, i, chapter_path, resolution)
            tracker.add_material(
                file_path=chapter_path,
                source_name="自動生成",
                image_type="chapter_card",
                generated_by_ai=False,
                description=f"チャプター{i}: {chapter_title}",
            )
            generated_paths.append(chapter_path)

        # 3. タイムライン: テレビ普及率の推移
        timeline_path = os.path.join(output_dir, "timeline_tv_spread.png")
        timeline_events = [
            {"year": "1953", "event": "テレビ放送開始",
             "value": "普及率: ほぼ0%"},
            {"year": "1958", "event": "皇太子ご成婚パレード",
             "value": "普及率: 約10%"},
            {"year": "1964", "event": "東京オリンピック",
             "value": "普及率: 約90%"},
            {"year": "1970", "event": "カラーテレビ普及開始",
             "value": "普及率: 約95%"},
            {"year": "1975", "event": "カラー完全普及",
             "value": "カラー普及率: 約90%"},
            {"year": "1985", "event": "薄型化・軽量化進行",
             "value": "一家に複数台の時代"},
        ]
        self.generate_timeline(
            "テレビ普及率の推移", timeline_events, timeline_path, resolution
        )
        tracker.add_material(
            file_path=timeline_path,
            source_name="自動生成",
            image_type="timeline",
            generated_by_ai=False,
            description="テレビ普及率の推移タイムライン",
        )
        generated_paths.append(timeline_path)

        # 4. 比較チャート: 当時のテレビ価格 vs 月給
        comparison_path = os.path.join(output_dir, "comparison_price.png")
        comparison_items = [
            {"label": "テレビ価格 (1955年頃)",
             "value": "約17万円", "bar_ratio": 1.0},
            {"label": "サラリーマン月給 (1955年)",
             "value": "約1.5万円", "bar_ratio": 0.088},
            {"label": "テレビ価格 (1965年頃)",
             "value": "約6万円", "bar_ratio": 0.35},
            {"label": "サラリーマン月給 (1965年)",
             "value": "約3万円", "bar_ratio": 0.18},
        ]
        self.generate_comparison_chart(
            "当時のテレビ価格 vs 月給",
            comparison_items, comparison_path, resolution,
        )
        tracker.add_material(
            file_path=comparison_path,
            source_name="自動生成",
            image_type="comparison_chart",
            generated_by_ai=False,
            description="テレビ価格と月給の比較チャート",
        )
        generated_paths.append(comparison_path)

        # 5. 年代カード
        eras = [
            ("昭和30年代", "1955-1964: テレビ黎明期"),
            ("昭和40年代", "1965-1974: カラー化と大衆化"),
            ("昭和50年代", "1975-1984: 多チャンネル時代"),
            ("昭和60年代〜平成初期", "1985-1995: 布文化の終焉"),
        ]
        for era_name, description in eras:
            safe_name = era_name.replace("〜", "_").replace("・", "_")
            era_path = os.path.join(output_dir, f"era_{safe_name}.png")
            self.generate_era_card(era_name, era_path, resolution,
                                   description=description)
            tracker.add_material(
                file_path=era_path,
                source_name="自動生成",
                image_type="era_card",
                generated_by_ai=False,
                description=f"年代カード: {era_name}",
            )
            generated_paths.append(era_path)

        # 6. イメージプレースホルダー（ノスタルジックシーン）
        placeholder_path = os.path.join(output_dir, "nostalgic_scene.png")
        self.generate_image_placeholder(
            "昭和の居間 ― テレビに布がかけられた風景",
            placeholder_path, resolution,
        )
        tracker.add_material(
            file_path=placeholder_path,
            source_name="自動生成",
            image_type="image_placeholder",
            generated_by_ai=False,
            description="ノスタルジックシーンのイメージプレースホルダー",
        )
        generated_paths.append(placeholder_path)

        # 権利関連ファイル出力
        tracker.save_materials_json(
            os.path.join(output_dir, "materials.json")
        )
        tracker.save_rights_report(
            os.path.join(output_dir, "rights_report.md")
        )
        tracker.save_credits(
            os.path.join(output_dir, "credits.txt")
        )

        logger.info(
            f"テレビの布トピック素材生成完了: {len(generated_paths)}件の素材を生成しました"
        )

        return {
            "materials": tracker.get_all_materials(),
            "tracker": tracker,
        }


class MaterialTracker:
    """
    素材の権利情報を追跡・管理するクラス。

    各素材のファイルパス、出典、権利ステータス等を記録し、
    materials.json, rights_report.md, credits.txt として出力する。
    """

    def __init__(self) -> None:
        self._materials: List[Dict[str, Any]] = []
        logger.info("MaterialTracker 初期化")

    def add_material(
        self,
        file_path: str,
        source_name: str = "自動生成",
        source_url: Optional[str] = None,
        rights_status: str = "OK",
        image_type: str = "generated",
        generated_by_ai: bool = False,
        credit_required: bool = False,
        credit_text: Optional[str] = None,
        description: Optional[str] = None,
        license_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """
        素材を追跡リストに追加する。

        自己生成素材は常に rights_status="OK" となる。

        Args:
            file_path: 素材ファイルパス
            source_name: 出典名
            source_url: 出典URL (任意)
            rights_status: 権利ステータス ("OK", "REVIEW", "NG")
            image_type: 画像種類
            generated_by_ai: AI生成かどうか
            credit_required: クレジット表示が必要か
            credit_text: クレジットテキスト (任意)
            description: 素材の説明 (任意)
            license_type: ライセンス種類 (任意)
            notes: 備考 (任意)
        """
        # 自動生成素材は常にOK
        if source_name == "自動生成":
            rights_status = "OK"
            generated_by_ai = False
            credit_required = False

        if rights_status not in ("OK", "REVIEW", "NG"):
            logger.warning(
                f"不正な権利ステータス: '{rights_status}'。'REVIEW' に設定します。"
            )
            rights_status = "REVIEW"

        material: Dict[str, Any] = {
            "file_path": file_path,
            "source_name": source_name,
            "source_url": source_url,
            "rights_status": rights_status,
            "image_type": image_type,
            "generated_by_ai": generated_by_ai,
            "credit_required": credit_required,
            "credit_text": credit_text,
            "description": description,
            "license_type": license_type,
            "notes": notes,
            "added_at": datetime.now().isoformat(),
        }

        self._materials.append(material)
        logger.debug(f"素材追加: {file_path} (権利: {rights_status})")

    def get_all_materials(self) -> List[Dict[str, Any]]:
        """全素材情報を返す。"""
        return list(self._materials)

    def get_safe_materials(self) -> List[Dict[str, Any]]:
        """
        権利ステータスが "OK" の素材のみを返す。
        REVIEW/NG の素材は最終動画に使用しない。

        Returns:
            rights_status=="OK" の素材リスト
        """
        safe = [m for m in self._materials if m["rights_status"] == "OK"]
        logger.info(
            f"安全な素材: {len(safe)}/{len(self._materials)}件 "
            f"(除外: {len(self._materials) - len(safe)}件)"
        )
        return safe

    def get_materials_by_status(
        self, status: str
    ) -> List[Dict[str, Any]]:
        """指定ステータスの素材を返す。"""
        return [m for m in self._materials if m["rights_status"] == status]

    def get_materials_by_type(
        self, image_type: str
    ) -> List[Dict[str, Any]]:
        """指定種類の素材を返す。"""
        return [m for m in self._materials if m["image_type"] == image_type]

    def save_materials_json(self, output_path: str) -> str:
        """
        素材情報を materials.json として保存する。

        Args:
            output_path: 出力ファイルパス

        Returns:
            出力ファイルパス
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_materials": len(self._materials),
            "status_summary": {
                "OK": len(self.get_materials_by_status("OK")),
                "REVIEW": len(self.get_materials_by_status("REVIEW")),
                "NG": len(self.get_materials_by_status("NG")),
            },
            "materials": self._materials,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"素材情報JSON保存: {output_path}")
        return output_path

    def save_rights_report(self, output_path: str) -> str:
        """
        権利レポートを rights_report.md として保存する。

        Args:
            output_path: 出力ファイルパス

        Returns:
            出力ファイルパス
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        ok_materials = self.get_materials_by_status("OK")
        review_materials = self.get_materials_by_status("REVIEW")
        ng_materials = self.get_materials_by_status("NG")

        lines: List[str] = []
        lines.append("# 素材権利レポート")
        lines.append("")
        lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## サマリー")
        lines.append("")
        lines.append(f"- 総素材数: {len(self._materials)}")
        lines.append(f"- OK (使用可能): {len(ok_materials)}")
        lines.append(f"- REVIEW (要確認): {len(review_materials)}")
        lines.append(f"- NG (使用不可): {len(ng_materials)}")
        lines.append("")

        if ng_materials:
            lines.append("## NG素材 (使用不可)")
            lines.append("")
            lines.append("以下の素材は最終動画に使用できません。")
            lines.append("")
            for m in ng_materials:
                lines.append(f"- **{os.path.basename(m['file_path'])}**")
                lines.append(f"  - 出典: {m['source_name']}")
                if m.get("notes"):
                    lines.append(f"  - 備考: {m['notes']}")
            lines.append("")

        if review_materials:
            lines.append("## REVIEW素材 (要確認)")
            lines.append("")
            lines.append("以下の素材は権利確認が必要です。確認完了まで使用しないでください。")
            lines.append("")
            for m in review_materials:
                lines.append(f"- **{os.path.basename(m['file_path'])}**")
                lines.append(f"  - 出典: {m['source_name']}")
                if m.get("source_url"):
                    lines.append(f"  - URL: {m['source_url']}")
                if m.get("license_type"):
                    lines.append(f"  - ライセンス: {m['license_type']}")
                if m.get("notes"):
                    lines.append(f"  - 備考: {m['notes']}")
            lines.append("")

        lines.append("## OK素材 (使用可能)")
        lines.append("")
        if ok_materials:
            for m in ok_materials:
                lines.append(f"- **{os.path.basename(m['file_path'])}**")
                lines.append(f"  - 種類: {m['image_type']}")
                lines.append(f"  - 出典: {m['source_name']}")
                if m.get("description"):
                    lines.append(f"  - 説明: {m['description']}")
        else:
            lines.append("使用可能な素材はありません。")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("注意: REVIEW/NG素材は最終動画に含めないでください。")
        lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"権利レポート保存: {output_path}")
        return output_path

    def save_credits(self, output_path: str) -> str:
        """
        クレジット情報を credits.txt として保存する。

        Args:
            output_path: 出力ファイルパス

        Returns:
            出力ファイルパス
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        lines: List[str] = []
        lines.append("=" * 50)
        lines.append("クレジット / Credits")
        lines.append("=" * 50)
        lines.append("")

        credit_materials = [
            m for m in self._materials
            if m.get("credit_required") and m["rights_status"] == "OK"
        ]

        if credit_materials:
            lines.append("使用素材クレジット:")
            lines.append("")
            for m in credit_materials:
                credit = m.get("credit_text") or m.get("source_name", "不明")
                lines.append(f"  {os.path.basename(m['file_path'])}")
                lines.append(f"    クレジット: {credit}")
                if m.get("source_url"):
                    lines.append(f"    URL: {m['source_url']}")
                if m.get("license_type"):
                    lines.append(f"    ライセンス: {m['license_type']}")
                lines.append("")
        else:
            lines.append("外部素材のクレジット表示は不要です。")
            lines.append("すべての素材は自動生成されたものです。")
            lines.append("")

        lines.append("-" * 50)
        lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("制作: 昭和・平成 なぜそうだったのか")
        lines.append("=" * 50)
        lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"クレジットファイル保存: {output_path}")
        return output_path
