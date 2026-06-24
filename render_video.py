#!/usr/bin/env python3
"""
レンダリング専用スクリプト
既存の台本・音声・スライドからMP4を書き出す

使い方:
    python render_video.py --output ./output --bgm ./assets/bgm/UNL1337.wav
"""

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


def main():
    parser = argparse.ArgumentParser(description="MP4レンダリング専用スクリプト")
    parser.add_argument("--output", default="./output", help="出力ディレクトリ")
    parser.add_argument("--bgm", default="./assets/bgm/UNL1337.wav", help="BGMファイルパス")
    parser.add_argument("--theme", default="なぜ家族全員で1台のテレビを見ていたのか", help="テーマ（台本再生成用）")
    args = parser.parse_args()

    output_dir = Path(args.output)
    tmp_dir = output_dir / "_tmp"

    from modules.script_generator import generate_script
    from modules.subtitle import get_subtitle_entries
    from modules.video_renderer import render_video

    script = generate_script(args.theme)

    audio_files = {}
    audio_durations = {}
    narration_dir = tmp_dir / "narration"
    if narration_dir.exists():
        for chapter_name in script["chapters"]:
            wav_path = narration_dir / f"narration_{chapter_name}.wav"
            if wav_path.exists():
                audio_files[chapter_name] = str(wav_path)
                from moviepy import AudioFileClip
                clip = AudioFileClip(str(wav_path))
                audio_durations[chapter_name] = clip.duration
                clip.close()
            else:
                audio_files[chapter_name] = None
                audio_durations[chapter_name] = script["chapters"][chapter_name].get("duration", 60.0)

    all_slides = {}
    slides_dir = tmp_dir / "slides"
    if slides_dir.exists():
        for chapter_name in script["chapters"]:
            chapter_slides = sorted(slides_dir.glob(f"slide_{chapter_name}_*.png"))
            all_slides[chapter_name] = [str(p) for p in chapter_slides]
        ending = list(slides_dir.glob("slide_ending.png"))
        if ending:
            all_slides["_ending"] = [str(ending[0])]

    if not all_slides:
        print("スライドが見つかりません。先に create_video.py を実行してください。")
        return 1

    subtitle_entries = get_subtitle_entries(script, audio_durations)
    bgm_path = args.bgm if os.path.exists(args.bgm) else None

    video_path = str(output_dir / "final_video.mp4")
    render_video(script, all_slides, audio_files, audio_durations, subtitle_entries, bgm_path, video_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
