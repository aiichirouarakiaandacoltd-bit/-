"""字幕生成モジュール"""
import os
import json
import logging

logger = logging.getLogger(__name__)


def ms_to_srt_time(ms):
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def generate_srt(segments, output_path):
    """セグメント情報からSRTファイルを生成"""
    srt_lines = []
    for i, seg in enumerate(segments):
        start = seg["start_ms"]
        end = start + seg["duration_ms"]
        text = seg["line"]
        if not text.strip():
            continue

        if len(text) > 40:
            mid = len(text) // 2
            split_pos = text.find("、", mid - 10, mid + 10)
            if split_pos == -1:
                split_pos = text.find("。", mid - 10, mid + 10)
            if split_pos == -1:
                split_pos = mid
            text = text[:split_pos + 1] + "\n" + text[split_pos + 1:]

        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{ms_to_srt_time(start)} --> {ms_to_srt_time(end)}")
        srt_lines.append(text)
        srt_lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    logger.info(f"SRT生成完了: {output_path} ({len(segments)}エントリ)")
    return output_path


def generate_srt_from_narration(narration_lines, total_duration_ms, output_path):
    """ナレーション行と総時間から均等割りでSRT生成（セグメント情報がない場合）"""
    lines = [line.strip() for line in narration_lines if line.strip()]
    if not lines:
        return output_path

    char_count = sum(len(l) for l in lines)
    if char_count == 0:
        return output_path

    segments = []
    current_ms = 0
    for line in lines:
        ratio = len(line) / char_count
        duration = int(total_duration_ms * ratio)
        segments.append({"line": line, "start_ms": current_ms, "duration_ms": duration})
        current_ms += duration

    return generate_srt(segments, output_path)
