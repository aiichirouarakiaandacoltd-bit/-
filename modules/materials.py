"""
素材管理モジュール (Material/Asset Management Module)

昭和・平成動画自動制作システム用の素材生成・権利管理モジュール。
Pillowを使用してテキストカード、タイムライン、比較チャート等の画像素材を生成し、
全素材の権利情報をJSON/Markdown/テキスト形式で追跡・出力する。

チャンネル: 昭和・平成 なぜそうだったのか
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 解像度定数
# ---------------------------------------------------------------------------
RESOLUTION_LONG: Tuple[int, int] = (1920, 1080)
RESOLUTION_SHORTS: Tuple[int, int] = (1080, 1920)

# ---------------------------------------------------------------------------
# フォントパス
# ---------------------------------------------------------------------------
FONT_TITLE = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BODY_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_BODY_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

FONT_FALLBACKS = [
    FONT_TITLE,
    FONT_BODY_BOLD,
    FONT_BODY_REGULAR,
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# ---------------------------------------------------------------------------
# 配色 (ノスタルジックな暖色系)
# ---------------------------------------------------------------------------
# 背景色
BG_WARM_CREAM = (245, 230, 208)       # #F5E6D0
BG_SEPIA = (212, 167, 106)            # #D4A76A
BG_DARK_WARM = (61, 43, 31)           # #3D2B1F
BG_MUTED_NAVY = (44, 62, 80)          # #2C3E50

# テキスト色
TEXT_WARM_WHITE = (255, 248, 240)      # #FFF8F0
TEXT_DARK_BROWN = (61, 43, 31)         # #3D2B1F

# アクセント色
ACCENT_WARM_RED = (192, 57, 43)        # #C0392B
ACCENT_GOLD = (212, 167, 106)         # #D4A76A

# 影色
SHADOW_COLOR = (30, 20, 10)

CHANNEL_NAME = "昭和・平成 なぜそうだったのか"


# ===========================================================================
# フォントユーティリティ
# ===========================================================================

def _load_font(size: int, role: str = "title") -> ImageFont.FreeTypeFont:
    """
    指定サイズ・ロールのフォントを読み込む。

    Args:
        size: フォントサイズ (px)
        role: "title" (Black) / "body" (Bold) / "regular" (Regular)

    Returns:
        読み込まれたフォントオブジェクト
    """
    primary = {
        "title": FONT_TITLE,
        "body": FONT_BODY_BOLD,
        "regular": FONT_BODY_REGULAR,
    }.get(role, FONT_TITLE)

    paths = [primary] + [p for p in FONT_FALLBACKS if p != primary]

    for path in paths:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError) as exc:
                logger.warning("フォント読み込み失敗: %s - %s", path, exc)
                continue

    logger.warning(
        "日本語フォントが見つかりません。デフォルトフォントを使用します。"
    )
    try:
        return ImageFont.load_default()
    except Exception:
        raise RuntimeError(
            f"フォントの読み込みに失敗しました。"
            f"Noto Sans CJK JP を {FONT_TITLE} にインストールしてください。"
        )


# ===========================================================================
# 描画ヘルパー
# ===========================================================================

def _resolve_resolution(
    resolution: Optional[Tuple[int, int]],
    format_type: str = "long",
) -> Tuple[int, int]:
    """resolution 引数を解決する。None の場合は format_type から判定。"""
    if resolution is not None:
        return resolution
    return RESOLUTION_SHORTS if format_type == "shorts" else RESOLUTION_LONG


def _gradient_bg(
    size: Tuple[int, int],
    top: Tuple[int, int, int],
    bottom: Tuple[int, int, int],
) -> Image.Image:
    """縦方向グラデーション背景を生成する。"""
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        r = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * r) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return img


def _solid_bg(
    size: Tuple[int, int],
    color: Tuple[int, int, int],
) -> Image.Image:
    """単色背景を生成する。"""
    return Image.new("RGB", size, color)


def _text_size(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> Tuple[int, int]:
    """テキストの (width, height) を返す。"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.Draw,
) -> List[str]:
    """テキストを max_width に収まるよう文字単位で折り返す。"""
    lines: List[str] = []
    cur = ""
    for ch in text:
        test = cur + ch
        tw, _ = _text_size(draw, test, font)
        if tw <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines or [text]


def _draw_shadow_text(
    draw: ImageDraw.Draw,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int] = TEXT_WARM_WHITE,
    shadow: Tuple[int, int, int] = SHADOW_COLOR,
    offset: int = 3,
) -> None:
    """影付きテキストを描画する。"""
    x, y = pos
    draw.text((x + offset, y + offset), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def _draw_centered(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    y: int,
    img_w: int,
    fill: Tuple[int, int, int] = TEXT_WARM_WHITE,
    shadow: bool = True,
) -> int:
    """中央揃えでテキストを描画し、次の Y 座標を返す。"""
    tw, th = _text_size(draw, text, font)
    x = (img_w - tw) // 2
    if shadow:
        _draw_shadow_text(draw, (x, y), text, font, fill=fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)
    return y + th


def _draw_multiline_centered(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    center_y: int,
    img_w: int,
    max_text_w: int,
    spacing: int = 15,
    fill: Tuple[int, int, int] = TEXT_WARM_WHITE,
    shadow: bool = True,
) -> int:
    """複数行テキストを水平・垂直中央に描画する。"""
    lines = _wrap_text(text, font, max_text_w, draw)
    heights = [_text_size(draw, ln, font)[1] for ln in lines]
    total_h = sum(heights) + spacing * max(0, len(lines) - 1)
    cy = center_y - total_h // 2
    for i, ln in enumerate(lines):
        cy = _draw_centered(draw, ln, font, cy, img_w, fill=fill, shadow=shadow)
        if i < len(lines) - 1:
            cy += spacing
    return cy


def _decorative_border(
    draw: ImageDraw.Draw,
    size: Tuple[int, int],
    color: Tuple[int, int, int] = ACCENT_GOLD,
    margin: int = 40,
) -> None:
    """装飾的な二重枠線を描画する。"""
    w, h = size
    draw.rectangle([margin, margin, w - margin, h - margin],
                   outline=color, width=3)
    m2 = margin + 8
    draw.rectangle([m2, m2, w - m2, h - m2], outline=color, width=1)


def _add_image_label(image: Image.Image) -> Image.Image:
    """画像右下に「イメージ」ラベルを追加する。"""
    w, h = image.size
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    label = "イメージ"
    fsz = int(min(w, h) * 0.025)
    fnt = _load_font(fsz, "body")
    tw, th = _text_size(od, label, fnt)

    px, py = int(tw * 0.3), int(th * 0.3)
    mg = int(min(w, h) * 0.03)
    x1 = w - mg - tw - px * 2
    y1 = h - mg - th - py * 2
    x2 = w - mg
    y2 = h - mg

    od.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 180))
    od.text((x1 + px, y1 + py), label, font=fnt, fill=(255, 255, 255, 230))
    return Image.alpha_composite(image, overlay).convert("RGB")


def _ensure_dir(path: str) -> None:
    """出力先ディレクトリを作成する。"""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


# ===========================================================================
# 権利情報テンプレート
# ===========================================================================

def _make_rights_entry(
    file_path: str,
    image_type: str = "TEXT_CARD",
    notes: str = "",
) -> Dict[str, Any]:
    """自作テキストカード用の権利情報 dict を返す。"""
    return {
        "file_path": file_path,
        "source_name": "自作テキストカード",
        "source_url": "",
        "rights_status": "OK",
        "image_type": image_type,
        "generated_by_ai": False,
        "credit_required": False,
        "credit_text": "",
        "commercial_use": True,
        "youtube_use": True,
        "notes": notes,
    }


# ===========================================================================
# 素材生成関数
# ===========================================================================

def generate_title_card(
    topic: str,
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    タイトルカード画像を生成する。

    Args:
        topic: 動画トピック (タイトルテキスト)
        resolution: 画像解像度 (width, height)
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("タイトルカード生成: '%s' -> %s", topic, output_path)

    img = _gradient_bg(resolution, BG_DARK_WARM, (30, 20, 12))
    draw = ImageDraw.Draw(img)

    margin = int(min(w, h) * 0.04)
    _decorative_border(draw, resolution, ACCENT_GOLD, margin)

    # チャンネル名
    ch_sz = int(min(w, h) * 0.028)
    ch_fnt = _load_font(ch_sz, "body")
    ch_y = int(h * 0.10)
    _draw_centered(draw, CHANNEL_NAME, ch_fnt, ch_y, w, fill=ACCENT_GOLD)

    # 装飾ライン
    line_y = int(h * 0.18)
    lw = int(w * 0.5)
    lx = (w - lw) // 2
    draw.line([(lx, line_y), (lx + lw, line_y)], fill=ACCENT_GOLD, width=2)

    # タイトル
    t_sz = int(min(w, h) * 0.065)
    t_fnt = _load_font(t_sz, "title")
    mtw = int(w * 0.75)
    _draw_multiline_centered(
        draw, topic, t_fnt, int(h * 0.45), w, mtw,
        spacing=int(t_sz * 0.4), fill=TEXT_WARM_WHITE,
    )

    # 下部ライン
    bl_y = int(h * 0.85)
    draw.line([(lx, bl_y), (lx + lw, bl_y)], fill=ACCENT_GOLD, width=2)

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("タイトルカード保存完了: %s", output_path)
    return output_path


def generate_chapter_card(
    chapter_num: int,
    chapter_title: str,
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    チャプター見出しカード (第N章) を生成する。

    Args:
        chapter_num: チャプター番号
        chapter_title: チャプタータイトル
        resolution: 画像解像度
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("チャプターカード生成: 第%d章 '%s' -> %s",
                chapter_num, chapter_title, output_path)

    # ドットパターン背景
    img = _solid_bg(resolution, BG_DARK_WARM)
    draw = ImageDraw.Draw(img)
    pat_color = (max(0, BG_DARK_WARM[0] - 12),
                 max(0, BG_DARK_WARM[1] - 10),
                 max(0, BG_DARK_WARM[2] - 8))
    sp = 30
    for py in range(0, h, sp):
        off = sp // 2 if (py // sp) % 2 else 0
        for px in range(off, w, sp):
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=pat_color)

    # 左アクセントバー
    bw = int(w * 0.008)
    bx = int(w * 0.08)
    draw.rectangle([bx, int(h * 0.25), bx + bw, int(h * 0.75)], fill=ACCENT_GOLD)

    # 章ラベル
    lbl_sz = int(min(w, h) * 0.025)
    lbl_fnt = _load_font(lbl_sz, "body")
    lbl_y = int(h * 0.25)
    num_x = int(w * 0.12)
    draw.text((num_x, lbl_y), f"第{chapter_num}章", font=lbl_fnt,
              fill=BG_SEPIA)

    # 章番号 (大きく)
    n_sz = int(min(w, h) * 0.12)
    n_fnt = _load_font(n_sz, "title")
    n_y = int(h * 0.28)
    _draw_shadow_text(draw, (num_x, n_y), f"{chapter_num:02d}", n_fnt,
                      fill=ACCENT_GOLD, offset=4)

    # チャプタータイトル
    t_sz = int(min(w, h) * 0.055)
    t_fnt = _load_font(t_sz, "title")
    t_x = int(w * 0.12)
    t_y = int(h * 0.55)
    mtw = int(w * 0.75)
    for ln in _wrap_text(chapter_title, t_fnt, mtw, draw):
        _draw_shadow_text(draw, (t_x, t_y), ln, t_fnt,
                          fill=TEXT_WARM_WHITE, offset=3)
        _, lh = _text_size(draw, ln, t_fnt)
        t_y += lh + int(t_sz * 0.3)

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("チャプターカード保存完了: %s", output_path)
    return output_path


def generate_era_card(
    era_text: str,
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    年代表示カード (昭和30年代 など) を生成する。

    Args:
        era_text: 年代テキスト (例: "昭和30年代")
        resolution: 画像解像度
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("年代カード生成: '%s' -> %s", era_text, output_path)

    img = _gradient_bg(resolution, TEXT_DARK_BROWN, BG_DARK_WARM)
    draw = ImageDraw.Draw(img)

    cx, cy = w // 2, h // 2
    cr = int(min(w, h) * 0.25)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                 outline=ACCENT_GOLD, width=3)
    ir = cr - 10
    draw.ellipse([cx - ir, cy - ir, cx + ir, cy + ir],
                 outline=ACCENT_GOLD, width=1)

    e_sz = int(min(w, h) * 0.08)
    e_fnt = _load_font(e_sz, "title")
    ew, eh = _text_size(draw, era_text, e_fnt)
    _draw_shadow_text(draw, ((w - ew) // 2, cy - eh // 2),
                      era_text, e_fnt, fill=TEXT_WARM_WHITE, offset=4)

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("年代カード保存完了: %s", output_path)
    return output_path


def generate_timeline_image(
    items: List[Dict[str, str]],
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    タイムライン画像を生成する。

    Args:
        items: タイムライン項目リスト。各項目は {"year": str, "text": str} 形式。
        resolution: 画像解像度
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("タイムライン生成: %d 件 -> %s", len(items), output_path)

    img = _gradient_bg(resolution, BG_DARK_WARM, (45, 35, 25))
    draw = ImageDraw.Draw(img)

    # タイトル
    ttl_sz = int(min(w, h) * 0.045)
    ttl_fnt = _load_font(ttl_sz, "title")
    ttl_y = int(h * 0.06)
    _draw_centered(draw, "タイムライン", ttl_fnt, ttl_y, w,
                   fill=TEXT_WARM_WHITE)

    if not items:
        _ensure_dir(output_path)
        img.save(output_path, "PNG", quality=95)
        return output_path

    # 軸
    ax_x = int(w * 0.15)
    ax_top = int(h * 0.18)
    ax_bot = int(h * 0.92)
    ax_h = ax_bot - ax_top
    draw.line([(ax_x, ax_top), (ax_x, ax_bot)], fill=ACCENT_GOLD, width=3)

    ev_sp = ax_h // max(len(items), 1)
    y_fnt = _load_font(int(min(w, h) * 0.032), "title")
    t_fnt = _load_font(int(min(w, h) * 0.028), "body")
    dr = int(min(w, h) * 0.008)
    max_tw = int(w * 0.55)

    for i, item in enumerate(items):
        ey = ax_top + i * ev_sp + ev_sp // 2
        year = item.get("year", "")
        text = item.get("text", "")

        # ドット
        draw.ellipse([ax_x - dr, ey - dr, ax_x + dr, ey + dr],
                     fill=ACCENT_GOLD)
        # 横線
        le = ax_x + int(w * 0.06)
        draw.line([(ax_x + dr, ey), (le, ey)], fill=ACCENT_GOLD, width=1)

        # 年ラベル (軸左)
        yw, yh = _text_size(draw, year, y_fnt)
        yx = ax_x - int(w * 0.02) - yw
        _draw_shadow_text(draw, (yx, ey - yh // 2), year, y_fnt,
                          fill=ACCENT_GOLD, offset=2)

        # テキスト (軸右)
        tx = le + int(w * 0.015)
        lines = _wrap_text(text, t_fnt, max_tw, draw)
        ty = ey - (len(lines) * (int(min(w, h) * 0.028) + 5)) // 2
        for ln in lines:
            _draw_shadow_text(draw, (tx, ty), ln, t_fnt,
                              fill=TEXT_WARM_WHITE, offset=2)
            ty += int(min(w, h) * 0.028) + 5

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("タイムライン保存完了: %s", output_path)
    return output_path


def generate_comparison_card(
    left_label: str,
    left_value: str,
    right_label: str,
    right_value: str,
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    左右比較カードを生成する。

    Args:
        left_label: 左側ラベル (例: "テレビ価格")
        left_value: 左側値
        right_label: 右側ラベル (例: "平均月収")
        right_value: 右側値
        resolution: 画像解像度
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("比較カード生成: '%s' vs '%s' -> %s",
                left_label, right_label, output_path)

    img = _gradient_bg(resolution, BG_DARK_WARM, BG_MUTED_NAVY)
    draw = ImageDraw.Draw(img)

    margin = int(min(w, h) * 0.04)
    _decorative_border(draw, resolution, ACCENT_GOLD, margin)

    # VS テキスト
    vs_sz = int(min(w, h) * 0.06)
    vs_fnt = _load_font(vs_sz, "title")
    _draw_centered(draw, "VS", vs_fnt, int(h * 0.44), w, fill=ACCENT_WARM_RED)

    # 中央縦線
    draw.line([(w // 2, int(h * 0.15)), (w // 2, int(h * 0.85))],
              fill=ACCENT_GOLD, width=2)

    # 左側
    lbl_sz = int(min(w, h) * 0.04)
    val_sz = int(min(w, h) * 0.055)
    lbl_fnt = _load_font(lbl_sz, "body")
    val_fnt = _load_font(val_sz, "title")

    half = w // 2
    # 左ラベル
    llw, _ = _text_size(draw, left_label, lbl_fnt)
    _draw_shadow_text(draw, ((half - llw) // 2, int(h * 0.28)),
                      left_label, lbl_fnt, fill=ACCENT_GOLD, offset=2)
    # 左値
    lvw, _ = _text_size(draw, left_value, val_fnt)
    _draw_shadow_text(draw, ((half - lvw) // 2, int(h * 0.58)),
                      left_value, val_fnt, fill=TEXT_WARM_WHITE, offset=3)

    # 右ラベル
    rlw, _ = _text_size(draw, right_label, lbl_fnt)
    _draw_shadow_text(draw, (half + (half - rlw) // 2, int(h * 0.28)),
                      right_label, lbl_fnt, fill=ACCENT_GOLD, offset=2)
    # 右値
    rvw, _ = _text_size(draw, right_value, val_fnt)
    _draw_shadow_text(draw, (half + (half - rvw) // 2, int(h * 0.58)),
                      right_value, val_fnt, fill=TEXT_WARM_WHITE, offset=3)

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("比較カード保存完了: %s", output_path)
    return output_path


def generate_image_placeholder(
    description: str,
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    「イメージ」ラベル付きプレースホルダー画像を生成する。

    Args:
        description: プレースホルダーの説明テキスト
        resolution: 画像解像度
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("イメージプレースホルダー生成: '%s' -> %s", description, output_path)

    img = _gradient_bg(resolution, BG_WARM_CREAM, BG_SEPIA)
    draw = ImageDraw.Draw(img)

    lbl_sz = int(min(w, h) * 0.045)
    lbl_fnt = _load_font(lbl_sz, "body")
    mtw = int(w * 0.7)
    _draw_multiline_centered(
        draw, description, lbl_fnt, int(h * 0.45), w, mtw,
        fill=TEXT_DARK_BROWN, shadow=False,
    )

    img = _add_image_label(img)

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("イメージプレースホルダー保存完了: %s", output_path)
    return output_path


def generate_transition_card(
    text: str,
    resolution: Tuple[int, int],
    output_path: str,
) -> str:
    """
    トランジション (場面転換) カードを生成する。

    Args:
        text: トランジションテキスト
        resolution: 画像解像度
        output_path: 出力 PNG パス

    Returns:
        出力ファイルパス
    """
    w, h = resolution
    logger.info("トランジションカード生成: '%s' -> %s", text, output_path)

    img = _solid_bg(resolution, BG_DARK_WARM)
    draw = ImageDraw.Draw(img)

    # 上下に細いゴールドライン
    ly = int(h * 0.40)
    lw_ = int(w * 0.6)
    lx = (w - lw_) // 2
    draw.line([(lx, ly), (lx + lw_, ly)], fill=ACCENT_GOLD, width=1)

    by = int(h * 0.60)
    draw.line([(lx, by), (lx + lw_, by)], fill=ACCENT_GOLD, width=1)

    # テキスト
    t_sz = int(min(w, h) * 0.05)
    t_fnt = _load_font(t_sz, "body")
    _draw_multiline_centered(
        draw, text, t_fnt, h // 2, w, int(w * 0.7),
        fill=TEXT_WARM_WHITE, shadow=True,
    )

    _ensure_dir(output_path)
    img.save(output_path, "PNG", quality=95)
    logger.info("トランジションカード保存完了: %s", output_path)
    return output_path


# ===========================================================================
# 権利管理 (MaterialTracker)
# ===========================================================================

class MaterialTracker:
    """
    素材の権利情報を追跡・管理するクラス。

    全素材に対して権利 JSON を保持し、materials.json / rights_report.md /
    credits.txt を出力する。REVIEW / NG ステータスの素材は最終動画に使用しない。
    """

    def __init__(self) -> None:
        self._materials: List[Dict[str, Any]] = []

    # ----- 追加 -----

    def add(self, entry: Dict[str, Any]) -> None:
        """権利情報 dict を追加する。"""
        if entry.get("rights_status") not in ("OK", "REVIEW", "NG"):
            entry["rights_status"] = "REVIEW"
        self._materials.append(entry)

    def add_self_generated(
        self,
        file_path: str,
        image_type: str = "TEXT_CARD",
        notes: str = "",
    ) -> None:
        """自作テキストカード素材を追加する (常に OK)。"""
        self.add(_make_rights_entry(file_path, image_type, notes))

    # ----- 参照 -----

    def get_all(self) -> List[Dict[str, Any]]:
        """全素材を返す。"""
        return list(self._materials)

    def get_ok(self) -> List[Dict[str, Any]]:
        """rights_status == 'OK' の素材のみ返す。"""
        return [m for m in self._materials if m["rights_status"] == "OK"]

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """指定ステータスの素材を返す。"""
        return [m for m in self._materials if m["rights_status"] == status]

    def get_by_type(self, image_type: str) -> List[Dict[str, Any]]:
        """指定種類の素材を返す。"""
        return [m for m in self._materials if m["image_type"] == image_type]

    # ----- 出力 -----

    def save_materials_json(self, path: str) -> str:
        """materials.json を出力する。"""
        _ensure_dir(path)
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_materials": len(self._materials),
            "status_summary": {
                s: len(self.get_by_status(s)) for s in ("OK", "REVIEW", "NG")
            },
            "materials": self._materials,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("materials.json 保存: %s", path)
        return path

    def save_rights_report(self, path: str) -> str:
        """rights_report.md を出力する。"""
        _ensure_dir(path)
        ok = self.get_by_status("OK")
        review = self.get_by_status("REVIEW")
        ng = self.get_by_status("NG")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "# 素材権利レポート", "",
            f"生成日時: {now}", "",
            "## サマリー", "",
            f"- 総素材数: {len(self._materials)}",
            f"- OK (使用可能): {len(ok)}",
            f"- REVIEW (要確認): {len(review)}",
            f"- NG (使用不可): {len(ng)}", "",
        ]

        if ng:
            lines += ["## NG素材 (使用不可)", "",
                       "以下の素材は最終動画に使用できません。", ""]
            for m in ng:
                lines.append(f"- **{os.path.basename(m['file_path'])}**")
                lines.append(f"  - 出典: {m['source_name']}")
                if m.get("notes"):
                    lines.append(f"  - 備考: {m['notes']}")
            lines.append("")

        if review:
            lines += ["## REVIEW素材 (要確認)", "",
                       "以下の素材は権利確認が必要です。確認完了まで使用しないでください。", ""]
            for m in review:
                lines.append(f"- **{os.path.basename(m['file_path'])}**")
                lines.append(f"  - 出典: {m['source_name']}")
                if m.get("source_url"):
                    lines.append(f"  - URL: {m['source_url']}")
                if m.get("notes"):
                    lines.append(f"  - 備考: {m['notes']}")
            lines.append("")

        lines += ["## OK素材 (使用可能)", ""]
        if ok:
            for m in ok:
                lines.append(f"- **{os.path.basename(m['file_path'])}**")
                lines.append(f"  - 種類: {m['image_type']}")
                lines.append(f"  - 出典: {m['source_name']}")
                if m.get("notes"):
                    lines.append(f"  - 備考: {m['notes']}")
        else:
            lines.append("使用可能な素材はありません。")
        lines += ["", "---", "",
                   "注意: REVIEW/NG素材は最終動画に含めないでください。", ""]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("rights_report.md 保存: %s", path)
        return path

    def save_credits(self, path: str) -> str:
        """credits.txt を出力する。"""
        _ensure_dir(path)
        credit_mats = [
            m for m in self._materials
            if m.get("credit_required") and m["rights_status"] == "OK"
        ]
        lines = [
            "=" * 50,
            "クレジット / Credits",
            "=" * 50, "",
        ]
        if credit_mats:
            lines.append("使用素材クレジット:")
            lines.append("")
            for m in credit_mats:
                ct = m.get("credit_text") or m.get("source_name", "不明")
                lines.append(f"  {os.path.basename(m['file_path'])}")
                lines.append(f"    クレジット: {ct}")
                if m.get("source_url"):
                    lines.append(f"    URL: {m['source_url']}")
                lines.append("")
        else:
            lines += [
                "外部素材のクレジット表示は不要です。",
                "すべての素材は自動生成されたものです。", "",
            ]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines += [
            "-" * 50,
            f"生成日時: {now}",
            f"制作: {CHANNEL_NAME}",
            "=" * 50, "",
        ]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("credits.txt 保存: %s", path)
        return path


# ===========================================================================
# 一括生成
# ===========================================================================

def generate_all_materials(
    topic: str,
    script_chapters: List[str],
    output_dir: str,
    format_type: str = "long",
) -> List[Dict[str, Any]]:
    """
    指定トピック・チャプター構成に基づき全素材を一括生成する。

    Args:
        topic: 動画トピック
        script_chapters: チャプタータイトルのリスト
        output_dir: 出力ディレクトリ
        format_type: "long" (1920x1080) or "shorts" (1080x1920)

    Returns:
        生成された素材 dict のリスト (権利情報付き)。
        各 dict は _make_rights_entry() 形式。
    """
    res = RESOLUTION_SHORTS if format_type == "shorts" else RESOLUTION_LONG
    os.makedirs(output_dir, exist_ok=True)
    tracker = MaterialTracker()
    logger.info(
        "素材一括生成開始: topic='%s', chapters=%d, format=%s",
        topic, len(script_chapters), format_type,
    )

    # 1. タイトルカード
    title_path = os.path.join(output_dir, "title_card.png")
    generate_title_card(topic, res, title_path)
    tracker.add_self_generated(title_path, "TITLE_CARD", f"タイトル: {topic}")

    # 2. チャプターカード
    for i, ch_title in enumerate(script_chapters, 1):
        ch_path = os.path.join(output_dir, f"chapter_{i:02d}.png")
        generate_chapter_card(i, ch_title, res, ch_path)
        tracker.add_self_generated(
            ch_path, "CHAPTER_CARD", f"第{i}章: {ch_title}",
        )

    # 3. トランジションカード (各章間)
    if len(script_chapters) > 1:
        for i in range(len(script_chapters) - 1):
            tr_path = os.path.join(output_dir, f"transition_{i + 1:02d}.png")
            generate_transition_card("・  ・  ・", res, tr_path)
            tracker.add_self_generated(
                tr_path, "TRANSITION_CARD",
                f"トランジション: 第{i + 1}章→第{i + 2}章",
            )

    # 権利関連ファイル出力
    tracker.save_materials_json(os.path.join(output_dir, "materials.json"))
    tracker.save_rights_report(os.path.join(output_dir, "rights_report.md"))
    tracker.save_credits(os.path.join(output_dir, "credits.txt"))

    materials = tracker.get_all()
    logger.info("素材一括生成完了: %d 件", len(materials))
    return materials


# ===========================================================================
# テストトピック用一括生成
# ===========================================================================

def generate_test_topic_materials(
    output_dir: str,
    format_type: str = "long",
) -> List[Dict[str, Any]]:
    """
    テストトピック「なぜ昔のテレビには布をかけていたのか」用の全素材を生成する。

    タイトルカード、チャプターカード6枚、年代カード3枚、
    タイムライン、比較カード、イメージプレースホルダーを含む。

    Args:
        output_dir: 出力ディレクトリ
        format_type: "long" or "shorts"

    Returns:
        生成された素材 dict のリスト
    """
    res = RESOLUTION_SHORTS if format_type == "shorts" else RESOLUTION_LONG
    os.makedirs(output_dir, exist_ok=True)
    tracker = MaterialTracker()
    topic = "なぜ昔のテレビには布をかけていたのか"

    logger.info("テストトピック素材生成開始: format=%s", format_type)

    # --- タイトルカード ---
    title_path = os.path.join(output_dir, "title_card.png")
    generate_title_card(topic, res, title_path)
    tracker.add_self_generated(title_path, "TITLE_CARD", topic)

    # --- チャプターカード ---
    chapters = [
        "当時のテレビのある風景",
        "布をかけていた理由",
        "技術と価格の背景",
        "地域と家庭による違い",
        "変化の始まり",
        "現代との違い",
    ]
    for i, ch in enumerate(chapters, 1):
        p = os.path.join(output_dir, f"chapter_{i:02d}.png")
        generate_chapter_card(i, ch, res, p)
        tracker.add_self_generated(p, "CHAPTER_CARD", f"第{i}章: {ch}")

    # --- 年代カード ---
    eras = ["昭和30年代", "昭和40年代", "昭和50年代"]
    for era in eras:
        safe = era.replace("・", "_")
        p = os.path.join(output_dir, f"era_{safe}.png")
        generate_era_card(era, res, p)
        tracker.add_self_generated(p, "ERA_CARD", era)

    # --- タイムライン: テレビ普及率 ---
    tl_path = os.path.join(output_dir, "timeline_tv_penetration.png")
    tl_items = [
        {"year": "1955", "text": "テレビ普及率 0.9%"},
        {"year": "1960", "text": "テレビ普及率 44.7%"},
        {"year": "1965", "text": "テレビ普及率 90%"},
        {"year": "1975", "text": "テレビ普及率 95%+"},
    ]
    generate_timeline_image(tl_items, res, tl_path)
    tracker.add_self_generated(tl_path, "TIMELINE", "テレビ普及率の推移")

    # --- 比較カード: テレビ価格 vs 平均月収 ---
    cmp_path = os.path.join(output_dir, "comparison_price_vs_salary.png")
    generate_comparison_card(
        "テレビ価格", "約17万円 (1955年)",
        "平均月収", "約1.5万円 (1955年)",
        res, cmp_path,
    )
    tracker.add_self_generated(cmp_path, "COMPARISON_CARD", "テレビ価格 vs 平均月収")

    # --- イメージプレースホルダー ---
    ph_path = os.path.join(output_dir, "placeholder_tv_scene.png")
    generate_image_placeholder(
        "昭和の居間 ― テレビに布がかけられた風景",
        res, ph_path,
    )
    tracker.add_self_generated(ph_path, "IMAGE_PLACEHOLDER", "居間のイメージ")

    # --- トランジションカード ---
    tr_path = os.path.join(output_dir, "transition_01.png")
    generate_transition_card("・  ・  ・", res, tr_path)
    tracker.add_self_generated(tr_path, "TRANSITION_CARD", "場面転換")

    # --- 権利ファイル出力 ---
    tracker.save_materials_json(os.path.join(output_dir, "materials.json"))
    tracker.save_rights_report(os.path.join(output_dir, "rights_report.md"))
    tracker.save_credits(os.path.join(output_dir, "credits.txt"))

    materials = tracker.get_all()
    logger.info("テストトピック素材生成完了: %d 件", len(materials))
    return materials
