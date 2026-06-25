"""Subtitle generation and burn-in based on actual audio durations."""
from pathlib import Path


def generate_srt(audio_results, output_path, gap=0.1):
    """Generate SRT file from audio results with real durations."""
    entries = []
    current_time = 0.0

    for i, item in enumerate(audio_results):
        start = current_time
        end = start + item["duration"]
        entries.append({
            "index": i + 1,
            "start": start,
            "end": end,
            "text": item["text"],
        })
        current_time = end + gap

    lines = []
    for e in entries:
        lines.append(str(e["index"]))
        lines.append(f"{_format_time(e['start'])} --> {_format_time(e['end'])}")
        lines.append(_wrap_subtitle(e["text"]))
        lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    return entries


def _wrap_subtitle(text, max_chars=20):
    """Wrap text to fit within 2 lines."""
    if len(text) <= max_chars:
        return text
    mid = len(text) // 2
    best = mid
    for offset in range(len(text) // 2):
        for pos in [mid + offset, mid - offset]:
            if 0 < pos < len(text) and text[pos] in "、。，．・　 ":
                best = pos + 1
                break
        else:
            continue
        break
    return text[:best] + "\n" + text[best:]


def _format_time(seconds):
    """Format seconds as SRT timestamp."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_subtitle_filter_long(srt_path, font_path):
    """Get FFmpeg subtitle filter for long-format (1920x1080)."""
    srt_escaped = str(srt_path).replace(":", r"\:").replace("'", r"\'")
    font_escaped = str(font_path).replace(":", r"\:").replace("'", r"\'")
    return (
        f"subtitles='{srt_escaped}'"
        f":force_style='FontName=IPAGothic,FontSize=28,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"BorderStyle=1,Outline=3,Shadow=1,"
        f"Alignment=2,MarginV=60,"
        f"Bold=1'"
    )


def get_subtitle_filter_shorts(srt_path, font_path):
    """Get FFmpeg subtitle filter for Shorts (1080x1920), avoiding bottom UI."""
    srt_escaped = str(srt_path).replace(":", r"\:").replace("'", r"\'")
    font_escaped = str(font_path).replace(":", r"\:").replace("'", r"\'")
    return (
        f"subtitles='{srt_escaped}'"
        f":force_style='FontName=IPAGothic,FontSize=24,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        f"BorderStyle=1,Outline=3,Shadow=1,"
        f"Alignment=2,MarginV=320,MarginR=80,"
        f"Bold=1'"
    )
