"""
字幕（SRT）生成モジュール
ナレーションテキストと音声長から字幕タイミングを計算する
"""

import re
from pathlib import Path
from .config import NARRATION_SPEED


def text_to_duration(text: str) -> float:
    char_count = len(text.replace("\n", "").replace(" ", ""))
    return (char_count / NARRATION_SPEED) * 60


def split_into_subtitle_chunks(text: str, max_chars: int = 28) -> list[str]:
    sentences = re.split(r"(?<=[。！？\n])", text)
    chunks = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        while len(sentence) > max_chars:
            split_at = max_chars
            for punct in ["、", "，", " "]:
                idx = sentence[:max_chars].rfind(punct)
                if idx > max_chars // 2:
                    split_at = idx + 1
                    break
            chunks.append(sentence[:split_at].strip())
            sentence = sentence[split_at:].strip()
        if sentence:
            chunks.append(sentence)
    return chunks


def seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(script: dict, audio_durations: dict, output_path: str) -> str:
    entries = []
    idx = 1
    current_time = 0.0

    for chapter_name, chapter_data in script["chapters"].items():
        chapter_audio_duration = audio_durations.get(chapter_name, chapter_data.get("duration", 60))

        chapter_title_text = f"【第{list(script['chapters'].keys()).index(chapter_name)+1}章：{chapter_name}】"
        entries.append({
            "idx": idx,
            "start": current_time,
            "end": current_time + 2.5,
            "text": chapter_title_text,
        })
        idx += 1
        current_time += 2.5

        narration_text = chapter_data["narration"]
        chunks = split_into_subtitle_chunks(narration_text)

        content_duration = max(0, chapter_audio_duration - 2.5)
        total_chars = sum(len(c) for c in chunks)

        for chunk in chunks:
            if not chunk:
                continue
            char_ratio = len(chunk) / max(total_chars, 1)
            duration = content_duration * char_ratio
            duration = max(duration, 1.5)

            entries.append({
                "idx": idx,
                "start": current_time,
                "end": current_time + duration,
                "text": chunk,
            })
            idx += 1
            current_time += duration

    srt_lines = []
    for entry in entries:
        srt_lines.append(str(entry["idx"]))
        srt_lines.append(
            f"{seconds_to_srt_time(entry['start'])} --> {seconds_to_srt_time(entry['end'])}"
        )
        srt_lines.append(entry["text"])
        srt_lines.append("")

    srt_content = "\n".join(srt_lines)

    output_path = str(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"  [字幕] {len(entries)} エントリを生成 → {output_path}")
    return output_path


def get_subtitle_entries(script: dict, audio_durations: dict) -> list[dict]:
    entries = []
    current_time = 0.0

    for chapter_name, chapter_data in script["chapters"].items():
        chapter_audio_duration = audio_durations.get(chapter_name, chapter_data.get("duration", 60))
        chapter_title_text = f"【第{list(script['chapters'].keys()).index(chapter_name)+1}章：{chapter_name}】"
        entries.append({
            "start": current_time,
            "end": current_time + 2.5,
            "text": chapter_title_text,
            "is_chapter": True,
            "chapter": chapter_name,
        })
        current_time += 2.5

        narration_text = chapter_data["narration"]
        chunks = split_into_subtitle_chunks(narration_text)
        content_duration = max(0, chapter_audio_duration - 2.5)
        total_chars = sum(len(c) for c in chunks)

        for chunk in chunks:
            if not chunk:
                continue
            char_ratio = len(chunk) / max(total_chars, 1)
            duration = content_duration * char_ratio
            duration = max(duration, 1.5)
            entries.append({
                "start": current_time,
                "end": current_time + duration,
                "text": chunk,
                "is_chapter": False,
                "chapter": chapter_name,
            })
            current_time += duration

    return entries
