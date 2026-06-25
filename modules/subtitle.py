"""
字幕生成モジュール (Subtitle generation module)
音声セグメントの実測デュレーションに基づいてSRT/ASSファイルを生成する。
"""

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 日本語の自然な分割ポイント（助詞・句読点）
PARTICLE_SPLIT_CHARS = set("はがをにでともへ")
PUNCTUATION_SPLIT_CHARS = set("、。！？!?，")


@dataclass
class AudioSegment:
    """音声セグメント情報。"""
    text: str
    wav_path: str
    actual_duration_seconds: float


def format_srt_timestamp(seconds: float) -> str:
    """秒数をSRTタイムスタンプ形式 (HH:MM:SS,mmm) に変換する。

    Args:
        seconds: 変換する秒数（0以上）

    Returns:
        SRT形式のタイムスタンプ文字列

    Raises:
        ValueError: 秒数が負の場合
    """
    if seconds < 0:
        raise ValueError(f"タイムスタンプに負の値は使用できません: {seconds}")

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    # 丸めで1000msになった場合の繰り上げ処理
    if millis >= 1000:
        millis = 0
        secs += 1
        if secs >= 60:
            secs = 0
            minutes += 1
            if minutes >= 60:
                minutes = 0
                hours += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_ass_timestamp(seconds: float) -> str:
    """秒数をASSタイムスタンプ形式 (H:MM:SS.cc) に変換する。

    Args:
        seconds: 変換する秒数（0以上）

    Returns:
        ASS形式のタイムスタンプ文字列

    Raises:
        ValueError: 秒数が負の場合
    """
    if seconds < 0:
        raise ValueError(f"タイムスタンプに負の値は使用できません: {seconds}")

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int(round((seconds - int(seconds)) * 100))
    # 丸めで100csになった場合の繰り上げ処理
    if centisecs >= 100:
        centisecs = 0
        secs += 1
        if secs >= 60:
            secs = 0
            minutes += 1
            if minutes >= 60:
                minutes = 0
                hours += 1
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"


def split_text_for_subtitle(
    text: str,
    max_chars_per_line: int = 20,
    max_lines: int = 2,
) -> list[str]:
    """日本語テキストを字幕表示用に自然な位置で分割する。

    分割優先順位:
      1. 句読点（、。！？）の直後
      2. 助詞（は、が、を、に、で、と、も、へ）の直後
      3. max_chars_per_line での強制分割

    Args:
        text: 分割対象の日本語テキスト
        max_chars_per_line: 1行あたりの最大文字数
        max_lines: 最大行数

    Returns:
        分割されたテキスト行のリスト
    """
    if not text or not text.strip():
        return [""]

    text = text.strip()

    # テキストが1行に収まる場合はそのまま返す
    if len(text) <= max_chars_per_line:
        return [text]

    lines: list[str] = []
    remaining = text

    while remaining and len(lines) < max_lines:
        if len(remaining) <= max_chars_per_line:
            lines.append(remaining)
            remaining = ""
            break

        # max_chars_per_line 以内で最良の分割位置を探す
        best_split = -1
        chunk = remaining[:max_chars_per_line]

        # 優先度1: 句読点の直後で分割
        for i in range(len(chunk) - 1, 0, -1):
            if chunk[i - 1] in PUNCTUATION_SPLIT_CHARS:
                best_split = i
                break

        # 優先度2: 助詞の直後で分割（句読点が見つからなかった場合）
        if best_split == -1:
            for i in range(len(chunk) - 1, 0, -1):
                if chunk[i - 1] in PARTICLE_SPLIT_CHARS:
                    # 助詞の前後の文脈を確認（連続する助詞文字を避ける）
                    # 少なくとも3文字以上の位置で分割する
                    if i >= 3:
                        best_split = i
                        break

        # 分割位置が見つからなければ強制的にmax_chars_per_lineで切る
        if best_split == -1:
            best_split = max_chars_per_line

        lines.append(remaining[:best_split])
        remaining = remaining[best_split:]

    # max_lines を超えた残りは最終行に結合
    if remaining and lines:
        lines[-1] = lines[-1] + remaining
    elif remaining:
        lines.append(remaining)

    return lines


def _calculate_cumulative_times(
    segments: list[AudioSegment],
    pause_duration: float,
) -> list[tuple[float, float]]:
    """各セグメントの開始時刻と終了時刻を累積計算する。

    Args:
        segments: 音声セグメントのリスト
        pause_duration: セグメント間の休止時間（秒）

    Returns:
        (start_time, end_time) タプルのリスト
    """
    times: list[tuple[float, float]] = []
    current_time = 0.0

    for i, segment in enumerate(segments):
        start_time = current_time
        end_time = start_time + segment.actual_duration_seconds
        times.append((start_time, end_time))
        current_time = end_time
        # 最後のセグメント以外はポーズを追加
        if i < len(segments) - 1:
            current_time += pause_duration

    return times


def verify_subtitle_timing(
    segments: list[AudioSegment],
    subtitle_end_time: float,
    tolerance: float = 2.0,
) -> bool:
    """字幕の最終タイムスタンプと音声の総デュレーションを検証する。

    Args:
        segments: 音声セグメントのリスト
        subtitle_end_time: 字幕ファイルの最終タイムスタンプ（秒）
        tolerance: 許容誤差（秒）

    Returns:
        検証成功ならTrue

    Raises:
        ValueError: 誤差が許容範囲を超えた場合
    """
    total_audio_duration = sum(s.actual_duration_seconds for s in segments)
    difference = abs(subtitle_end_time - total_audio_duration)

    logger.info(
        f"字幕タイミング検証: 音声総時間={total_audio_duration:.3f}秒, "
        f"字幕最終時刻={subtitle_end_time:.3f}秒, 差分={difference:.3f}秒"
    )

    if difference > tolerance:
        raise ValueError(
            f"字幕タイミング検証に失敗しました。"
            f"音声総時間({total_audio_duration:.3f}秒)と"
            f"字幕最終時刻({subtitle_end_time:.3f}秒)の差分が"
            f"許容範囲({tolerance}秒)を超えています: {difference:.3f}秒"
        )

    logger.info("字幕タイミング検証: OK")
    return True


def generate_srt(
    segments: list[AudioSegment],
    output_path: str,
    pause_duration: float = 0.3,
    max_chars_per_line: int = 20,
    max_lines: int = 2,
) -> float:
    """SRTファイルを生成する。

    Args:
        segments: 音声セグメントのリスト
        output_path: 出力SRTファイルパス
        pause_duration: セグメント間の休止時間（秒）
        max_chars_per_line: 1行あたりの最大文字数
        max_lines: 最大行数

    Returns:
        最終字幕の終了時刻（秒）

    Raises:
        ValueError: セグメントが空の場合
        OSError: ファイル書き込みに失敗した場合
    """
    if not segments:
        raise ValueError("字幕を生成するセグメントがありません。")

    times = _calculate_cumulative_times(segments, pause_duration)
    subtitle_end_time = 0.0

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            entry_index = 1
            for segment, (start, end) in zip(segments, times):
                lines = split_text_for_subtitle(
                    segment.text, max_chars_per_line, max_lines
                )
                display_text = "\n".join(lines)
                start_ts = format_srt_timestamp(start)
                end_ts = format_srt_timestamp(end)

                f.write(f"{entry_index}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{display_text}\n")
                f.write("\n")

                entry_index += 1
                subtitle_end_time = end

    except OSError as e:
        raise OSError(f"SRTファイルの書き込みに失敗しました: {output_path} - {e}") from e

    logger.info(f"SRTファイル生成完了: {output_path} ({entry_index - 1}エントリ)")
    return subtitle_end_time


def _build_ass_header(
    format_type: str,
    config: dict[str, Any],
) -> str:
    """ASSファイルのヘッダー部分を構築する。

    Args:
        format_type: "long" または "shorts"
        config: 設定辞書

    Returns:
        ASSヘッダー文字列
    """
    sub_config = config.get("subtitles", {})
    vid_config = config.get("video", {}).get(format_type, {})

    font_family = sub_config.get("font_family", "Noto Sans CJK JP Black")
    text_color = sub_config.get("text_color", "FFFFFF")
    outline_color = sub_config.get("outline_color", "000000")
    outline_width = sub_config.get("outline_width", 3)

    play_res_x = vid_config.get("width", 1920 if format_type == "long" else 1080)
    play_res_y = vid_config.get("height", 1080 if format_type == "long" else 1920)

    if format_type == "shorts":
        font_size = sub_config.get("font_size_shorts", 56)
        margin_bottom = sub_config.get("margin_bottom_shorts", 300)
        margin_top = sub_config.get("margin_top_shorts", 150)
        margin_right = sub_config.get("margin_right_shorts", 100)
        margin_left = 0
        # Shorts: 安全エリア内での下部中央配置
        alignment = 2  # 下部中央
    else:
        font_size = sub_config.get("font_size_long", 48)
        margin_bottom = sub_config.get("margin_bottom_long", 60)
        margin_top = 0
        margin_left = 0
        margin_right = 0
        alignment = 2  # 下部中央

    # ASSカラーは &HAABBGGRR 形式
    # text_color "FFFFFF" -> &H00FFFFFF (白、不透明)
    # outline_color "000000" -> &H00000000 (黒、不透明)
    primary_color = _rgb_hex_to_ass_color(text_color)
    outline_ass_color = _rgb_hex_to_ass_color(outline_color)
    # 影の色（半透明黒）
    back_color = "&H80000000"

    header = f"""[Script Info]
Title: Showa Heisei Video Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_family},{font_size},{primary_color},&H000000FF,{outline_ass_color},{back_color},-1,0,0,0,100,100,0,0,1,{outline_width},0,{alignment},{margin_left},{margin_right},{margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return header


def _rgb_hex_to_ass_color(hex_color: str) -> str:
    """RGB HEXカラー文字列をASS形式 (&H00BBGGRR) に変換する。

    Args:
        hex_color: "FFFFFF" 形式のRGB HEX文字列

    Returns:
        "&H00BBGGRR" 形式のASS色文字列
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"無効なカラーコード: {hex_color} (6桁のHEX形式が必要です)")

    r = hex_color[0:2]
    g = hex_color[2:4]
    b = hex_color[4:6]
    # ASS形式: &H00BBGGRR（アルファ00=不透明）
    return f"&H00{b}{g}{r}"


def generate_ass(
    segments: list[AudioSegment],
    output_path: str,
    format_type: str,
    config: dict[str, Any],
    pause_duration: float = 0.3,
    max_chars_per_line: int = 20,
    max_lines: int = 2,
) -> float:
    """ASSファイルを生成する（ffmpegでの字幕焼き込み用）。

    Args:
        segments: 音声セグメントのリスト
        output_path: 出力ASSファイルパス
        format_type: "long" または "shorts"
        config: 設定辞書（subtitles, video セクションを含む）
        pause_duration: セグメント間の休止時間（秒）
        max_chars_per_line: 1行あたりの最大文字数
        max_lines: 最大行数

    Returns:
        最終字幕の終了時刻（秒）

    Raises:
        ValueError: セグメントが空、またはformat_typeが不正な場合
        OSError: ファイル書き込みに失敗した場合
    """
    if not segments:
        raise ValueError("字幕を生成するセグメントがありません。")

    if format_type not in ("long", "shorts"):
        raise ValueError(
            f"無効なフォーマットタイプ: {format_type} ('long' または 'shorts' を指定してください)"
        )

    times = _calculate_cumulative_times(segments, pause_duration)
    header = _build_ass_header(format_type, config)
    subtitle_end_time = 0.0

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            for segment, (start, end) in zip(segments, times):
                lines = split_text_for_subtitle(
                    segment.text, max_chars_per_line, max_lines
                )
                # ASS形式では改行は \N で表現
                display_text = r"\N".join(lines)
                start_ts = format_ass_timestamp(start)
                end_ts = format_ass_timestamp(end)

                f.write(
                    f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{display_text}\n"
                )
                subtitle_end_time = end

    except OSError as e:
        raise OSError(f"ASSファイルの書き込みに失敗しました: {output_path} - {e}") from e

    logger.info(f"ASSファイル生成完了: {output_path} (フォーマット: {format_type})")
    return subtitle_end_time


def generate_all_subtitles(
    segments: list[AudioSegment],
    output_dir: str,
    config: dict[str, Any],
    pause_duration: float = 0.3,
    shorts_segments: dict[str, list[AudioSegment]] | None = None,
) -> dict[str, str]:
    """全字幕ファイル（SRT + ASS）を一括生成するメインエントリポイント。

    生成されるファイル:
      - subtitles_long.srt / subtitles_long.ass (ロング動画用)
      - subtitles_short_01.srt / subtitles_short_01.ass (ショート1用)
      - subtitles_short_02.srt / subtitles_short_02.ass (ショート2用)

    Args:
        segments: ロング動画用の音声セグメントリスト
        output_dir: 出力ディレクトリパス
        config: 設定辞書
        pause_duration: セグメント間の休止時間（秒）
        shorts_segments: ショート動画用セグメント辞書
            例: {"short_01": [...], "short_02": [...]}
            Noneの場合、ショート字幕は生成されない

    Returns:
        生成されたファイルパスの辞書
        例: {"long_srt": "/path/to/subtitles_long.srt", ...}

    Raises:
        ValueError: タイミング検証に失敗した場合
        OSError: ファイル書き込みに失敗した場合
    """
    sub_config = config.get("subtitles", {})
    max_chars = sub_config.get("max_chars_per_line", 20)
    max_lines_val = sub_config.get("max_lines", 2)

    os.makedirs(output_dir, exist_ok=True)
    output_files: dict[str, str] = {}

    # --- ロング動画用字幕 ---
    logger.info("ロング動画用字幕を生成中...")

    long_srt_path = os.path.join(output_dir, "subtitles_long.srt")
    long_ass_path = os.path.join(output_dir, "subtitles_long.ass")

    srt_end = generate_srt(
        segments, long_srt_path, pause_duration, max_chars, max_lines_val
    )
    ass_end = generate_ass(
        segments, long_ass_path, "long", config, pause_duration, max_chars, max_lines_val
    )

    # タイミング検証（ポーズ込みの最終時刻 vs 音声実時間）
    verify_subtitle_timing(segments, srt_end)
    output_files["long_srt"] = long_srt_path
    output_files["long_ass"] = long_ass_path
    logger.info(f"ロング動画字幕完了: SRT終了={srt_end:.3f}秒, ASS終了={ass_end:.3f}秒")

    # --- ショート動画用字幕 ---
    if shorts_segments is None:
        shorts_segments = {}

    # デフォルトのショートキー（short_01, short_02）
    default_shorts = {"short_01": [], "short_02": []}
    for key in default_shorts:
        if key not in shorts_segments:
            logger.info(f"ショート動画 '{key}' のセグメントが未指定です。スキップします。")
            continue

        short_segs = shorts_segments[key]
        if not short_segs:
            logger.warning(f"ショート動画 '{key}' のセグメントが空です。スキップします。")
            continue

        logger.info(f"ショート動画 '{key}' 用字幕を生成中...")

        srt_path = os.path.join(output_dir, f"subtitles_{key}.srt")
        ass_path = os.path.join(output_dir, f"subtitles_{key}.ass")

        short_srt_end = generate_srt(
            short_segs, srt_path, pause_duration, max_chars, max_lines_val
        )
        short_ass_end = generate_ass(
            short_segs, ass_path, "shorts", config, pause_duration, max_chars, max_lines_val
        )

        verify_subtitle_timing(short_segs, short_srt_end)
        output_files[f"{key}_srt"] = srt_path
        output_files[f"{key}_ass"] = ass_path
        logger.info(
            f"ショート動画 '{key}' 字幕完了: "
            f"SRT終了={short_srt_end:.3f}秒, ASS終了={short_ass_end:.3f}秒"
        )

    logger.info(f"全字幕ファイル生成完了: {len(output_files)}ファイル")
    return output_files
