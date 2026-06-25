import os
import wave


def generate_srt(narration_text, audio_path, output_path):
    sentences = [s.strip() for s in narration_text.split("\n") if s.strip()]
    total_duration = _get_audio_duration(audio_path)

    char_counts = [len(s) for s in sentences]
    total_chars = sum(char_counts)
    if total_chars == 0:
        total_chars = 1

    pause_duration = 0.3
    total_pause = pause_duration * (len(sentences) - 1) if len(sentences) > 1 else 0
    speech_duration = total_duration - total_pause

    entries = []
    current_time = 0.0

    for i, sentence in enumerate(sentences):
        ratio = char_counts[i] / total_chars
        seg_dur = speech_duration * ratio

        start = current_time
        end = current_time + seg_dur

        chunks = _split_subtitle(sentence, max_chars=20)
        chunk_dur = seg_dur / len(chunks) if chunks else seg_dur

        for j, chunk in enumerate(chunks):
            c_start = start + chunk_dur * j
            c_end = start + chunk_dur * (j + 1)
            entries.append({
                "index": len(entries) + 1,
                "start": c_start,
                "end": c_end,
                "text": chunk,
            })

        current_time = end + pause_duration

    srt_lines = []
    for e in entries:
        srt_lines.append(str(e["index"]))
        srt_lines.append(f"{_fmt_time(e['start'])} --> {_fmt_time(e['end'])}")
        srt_lines.append(e["text"])
        srt_lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    return entries


def _split_subtitle(text, max_chars=20):
    if len(text) <= max_chars:
        return [text]

    chunks = []
    delimiters = ["。", "、", "。", "，", ".", ","]
    remaining = text

    while len(remaining) > max_chars:
        split_pos = -1
        for d in delimiters:
            pos = remaining[:max_chars].rfind(d)
            if pos > 0:
                split_pos = pos + len(d)
                break
        if split_pos <= 0:
            split_pos = max_chars
        chunks.append(remaining[:split_pos].strip())
        remaining = remaining[split_pos:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


def _get_audio_duration(audio_path):
    if audio_path.endswith(".wav"):
        with wave.open(audio_path, "r") as wf:
            return wf.getnframes() / wf.getframerate()
    return 55.0


def _fmt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_ass_filter(srt_entries, settings):
    font = settings["subtitle"]["font_name"]
    size = settings["subtitle"]["font_size"]
    color = settings["subtitle"]["font_color"].lstrip("#")
    outline_color = settings["subtitle"]["outline_color"].lstrip("#")
    outline_w = settings["subtitle"]["outline_width"]

    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    or_, og, ob = int(outline_color[0:2], 16), int(outline_color[2:4], 16), int(outline_color[4:6], 16)
    primary = f"&H00{b:02X}{g:02X}{r:02X}"
    outline_c = f"&H00{ob:02X}{og:02X}{or_:02X}"

    pos_y = int(1920 * settings["subtitle"]["position_y_ratio"])

    ass_lines = []
    ass_lines.append("[Script Info]")
    ass_lines.append("Title: ザ・ダンク 字幕")
    ass_lines.append("ScriptType: v4.00+")
    ass_lines.append("PlayResX: 1080")
    ass_lines.append("PlayResY: 1920")
    ass_lines.append("")
    ass_lines.append("[V4+ Styles]")
    ass_lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
    ass_lines.append(
        f"Style: Default,{font},{size},{primary},&H000000FF,{outline_c},&H80000000,1,0,0,0,100,100,0,0,1,{outline_w},1,2,40,40,{1920 - pos_y},1"
    )
    ass_lines.append("")
    ass_lines.append("[Events]")
    ass_lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")

    for e in srt_entries:
        start = _fmt_ass_time(e["start"])
        end = _fmt_ass_time(e["end"])
        text = e["text"].replace("\n", "\\N")
        ass_lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return "\n".join(ass_lines)


def _fmt_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
