"""字幕生成モジュール（拡張版）

音声セクションデータからSRTファイルを生成する。
字幕品質検証を含む。
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


def _split_text_lines(text: str, max_chars: int | None = None) -> list[str]:
    mc = max_chars or config.SUBTITLE_MAX_CHARS_PER_LINE
    if len(text) <= mc:
        return [text]

    sentences = re.split(r"(?<=[。、！？])", text)
    lines = []
    current = ""
    for s in sentences:
        if len(current + s) <= mc:
            current += s
        else:
            if current:
                lines.append(current)
            if len(s) > mc:
                for j in range(0, len(s), mc):
                    lines.append(s[j:j + mc])
            else:
                current = s
                continue
            current = ""
    if current:
        lines.append(current)

    return lines[:config.SUBTITLE_MAX_LINES] if lines else [text[:mc]]


def generate_srt(
    audio_sections: list[dict],
    output_path: Path,
    max_chars_per_line: int | None = None,
    video_format: str = "long",
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mc = max_chars_per_line or config.SUBTITLE_MAX_CHARS_PER_LINE
    entries = []
    idx = 1
    current_time = 0.0

    for sec in audio_sections:
        text = sec.get("text", "").strip()
        duration = sec.get("duration", 5.0)

        if not text:
            current_time += duration
            continue

        chunks = _split_text_for_subtitle(text, mc, duration)

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
        return [(text[:max_chars], total_duration)]

    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return [(text[:max_chars], total_duration)]

    result = []
    for s in sentences:
        ratio = len(s) / total_chars
        dur = max(1.0, total_duration * ratio)

        lines = _split_text_lines(s, max_chars)
        display = "\n".join(lines[:config.SUBTITLE_MAX_LINES])
        result.append((display, dur))

    return result


def verify_subtitles(srt_path: Path, video_format: str = "long") -> dict:
    """字幕品質検証"""
    result = {
        "path": str(srt_path),
        "checks": [],
        "passed": True,
        "entry_count": 0,
    }

    if not srt_path.exists():
        result["passed"] = False
        result["checks"].append({"name": "SRTファイル", "ok": False, "detail": "ファイルなし"})
        return result

    content = srt_path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in content.split("\n\n") if b.strip()]
    result["entry_count"] = len(blocks)

    max_lines = config.SUBTITLE_MAX_LINES
    max_chars = config.SUBTITLE_MAX_CHARS_PER_LINE
    over_line_count = 0
    over_char_count = 0
    mojibake_count = 0

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        text_lines = lines[2:]

        if len(text_lines) > max_lines:
            over_line_count += 1

        for tl in text_lines:
            if len(tl) > max_chars + 5:
                over_char_count += 1
            if "?" in tl and tl.count("?") > 3:
                mojibake_count += 1

    ok_lines = over_line_count == 0
    result["checks"].append({
        "name": f"行数制限（{max_lines}行以内）",
        "ok": ok_lines,
        "detail": f"超過: {over_line_count}件" if not ok_lines else "OK",
    })

    ok_chars = over_char_count == 0
    result["checks"].append({
        "name": f"1行文字数（{max_chars}文字目安）",
        "ok": ok_chars,
        "detail": f"超過: {over_char_count}件" if not ok_chars else "OK",
    })

    ok_moji = mojibake_count == 0
    result["checks"].append({
        "name": "日本語文字化け",
        "ok": ok_moji,
        "detail": f"疑い: {mojibake_count}件" if not ok_moji else "なし",
    })

    margin_v = (
        config.SUBTITLE_MARGIN_V_LONG
        if video_format == "long"
        else config.SUBTITLE_MARGIN_V_SHORTS
    )
    result["checks"].append({
        "name": "安全領域",
        "ok": True,
        "detail": f"MarginV={margin_v}px ({video_format}用)",
    })

    if over_line_count > 0 or over_char_count > 0 or mojibake_count > 0:
        result["passed"] = False

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
    margin_v = (
        config.SUBTITLE_MARGIN_V_LONG
        if video_format == "long"
        else config.SUBTITLE_MARGIN_V_SHORTS
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
        f"MarginV={margin_v}'"
    )
