"""字幕生成モジュール

音声セクションデータからSRTファイルを生成する。
"""

import re
from pathlib import Path

from . import config


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _split_text_lines(text: str, max_chars: int = 20) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[。、！？])", text)
    lines = []
    current = ""
    for s in sentences:
        if len(current + s) <= max_chars:
            current += s
        else:
            if current:
                lines.append(current)
            current = s
    if current:
        lines.append(current)

    return lines if lines else [text]


def generate_srt(
    audio_sections: list[dict],
    output_path: Path,
    max_chars_per_line: int = 20,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    idx = 1
    current_time = 0.0

    for sec in audio_sections:
        text = sec.get("text", "").strip()
        duration = sec.get("duration", 5.0)

        if not text:
            current_time += duration
            continue

        chunks = _split_text_for_subtitle(text, max_chars_per_line, duration)

        for chunk_text, chunk_dur in chunks:
            start = current_time
            end = current_time + chunk_dur
            start_str = _format_srt_time(start)
            end_str = _format_srt_time(end)

            entries.append(f"{idx}\n{start_str} --> {end_str}\n{chunk_text}\n")
            idx += 1
            current_time = end

        pause = 0.5
        current_time += pause

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

    print(f"[OK] SRT生成: {output_path} ({idx - 1}エントリ)")
    return output_path


def _split_text_for_subtitle(
    text: str, max_chars: int, total_duration: float
) -> list[tuple[str, float]]:
    sentences = re.split(r"(?<=[。！？])", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [(text, total_duration)]

    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return [(text, total_duration)]

    result = []
    for s in sentences:
        ratio = len(s) / total_chars
        dur = max(1.0, total_duration * ratio)

        lines = _split_text_lines(s, max_chars)
        display = "\n".join(lines)
        result.append((display, dur))

    return result


def generate_ffmpeg_subtitles_filter(
    srt_path: Path,
    video_format: str = "long",
) -> str:
    font_size = (
        config.SUBTITLE_FONT_SIZE_LONG
        if video_format == "long"
        else config.SUBTITLE_FONT_SIZE_SHORTS
    )

    escaped = str(srt_path).replace("\\", "\\\\").replace(":", "\\:")
    return (
        f"subtitles='{escaped}'"
        f":force_style='FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"Outline=2,"
        f"Shadow=1,"
        f"Alignment=2,"
        f"MarginV=60'"
    )
