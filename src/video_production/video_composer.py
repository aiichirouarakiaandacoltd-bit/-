"""動画合成モジュール

画像 + 音声 + 字幕 + BGM → 最終MP4を生成する。
FFmpegベースで長尺・Shorts両対応。
"""

import subprocess
import tempfile
from pathlib import Path

from . import config


def compose_video(
    audio_sections: list[dict],
    image_sections: list[dict],
    srt_path: Path,
    output_path: Path,
    video_format: str = "long",
    bgm_path: Path | None = None,
    bgm_volume: float | None = None,
) -> Path:
    vc = config.VIDEO_LONG if video_format == "long" else config.VIDEO_SHORTS
    w, h, fps = vc["width"], vc["height"], vc["fps"]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    narration_path = _concat_narration(audio_sections, output_path.parent)
    narration_dur = _get_duration(narration_path)

    slideshow_path = _create_slideshow(
        audio_sections, image_sections, output_path.parent, w, h, fps
    )

    if bgm_path and bgm_path.exists():
        vol = bgm_volume or config.BGM_VOLUME
        mixed_audio = output_path.parent / "_mixed_audio.wav"
        _mix_audio(narration_path, bgm_path, mixed_audio, vol, narration_dur)
        final_audio = mixed_audio
    else:
        final_audio = narration_path

    no_sub_path = output_path.parent / "_nosub.mp4"
    _merge_video_audio(slideshow_path, final_audio, no_sub_path, vc)

    if srt_path.exists():
        _burn_subtitles(no_sub_path, srt_path, output_path, video_format)
    else:
        no_sub_path.rename(output_path)

    _cleanup_temp(output_path.parent)

    print(f"[OK] 動画生成完了: {output_path}")
    return output_path


def _concat_narration(audio_sections: list[dict], work_dir: Path) -> Path:
    list_file = work_dir / "_narration_list.txt"
    output = work_dir / "_narration_full.wav"

    silence = work_dir / "_pause.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         "anullsrc=r=24000:cl=mono:d=0.5",
         "-t", "0.5", str(silence)],
        capture_output=True, check=True,
    )

    with open(list_file, "w") as f:
        for i, sec in enumerate(audio_sections):
            f.write(f"file '{Path(sec['audio_path']).resolve()}'\n")
            if i < len(audio_sections) - 1:
                f.write(f"file '{silence.resolve()}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(output)],
        capture_output=True, check=True,
    )
    return output


def _create_slideshow(
    audio_sections: list[dict],
    image_sections: list[dict],
    work_dir: Path,
    width: int,
    height: int,
    fps: int,
) -> Path:
    img_map = {s["index"]: s["image_path"] for s in image_sections}
    segments = []
    segment_list = work_dir / "_segment_list.txt"

    for i, sec in enumerate(audio_sections):
        dur = sec.get("duration", 5.0) + 0.5
        img_path = img_map.get(sec["index"], img_map.get(i))

        if not img_path:
            continue

        seg_path = work_dir / f"_seg_{i:03d}.mp4"
        subprocess.run(
            ["ffmpeg", "-y",
             "-loop", "1", "-i", str(img_path),
             "-t", str(dur),
             "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
             "-c:v", "libx264", "-preset", "ultrafast",
             "-pix_fmt", "yuv420p", "-r", str(fps),
             "-an", str(seg_path)],
            capture_output=True, check=True,
        )
        segments.append(seg_path)

    with open(segment_list, "w") as f:
        for seg in segments:
            f.write(f"file '{seg.resolve()}'\n")

    output = work_dir / "_slideshow.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(segment_list),
         "-c", "copy", str(output)],
        capture_output=True, check=True,
    )
    return output


def _mix_audio(
    narration: Path, bgm: Path, output: Path,
    bgm_volume: float, duration: float,
) -> Path:
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(narration),
         "-stream_loop", "-1", "-i", str(bgm),
         "-filter_complex",
         f"[1:a]volume={bgm_volume},atrim=0:{duration},asetpts=PTS-STARTPTS[bgm];"
         f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[out]",
         "-map", "[out]",
         "-ar", "24000", "-ac", "1",
         str(output)],
        capture_output=True, check=True,
    )
    return output


def _merge_video_audio(video: Path, audio: Path, output: Path, vc: dict) -> Path:
    enc = config.ENCODING
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(video),
         "-i", str(audio),
         "-c:v", enc["vcodec"],
         "-preset", enc["preset"],
         "-crf", str(enc["crf"]),
         "-b:v", enc["video_bitrate"],
         "-c:a", enc["acodec"],
         "-b:a", enc["audio_bitrate"],
         "-shortest",
         "-pix_fmt", "yuv420p",
         str(output)],
        capture_output=True, check=True,
    )
    return output


def _burn_subtitles(
    video: Path, srt: Path, output: Path, video_format: str,
) -> Path:
    from .subtitle_generator import generate_ffmpeg_subtitles_filter
    sub_filter = generate_ffmpeg_subtitles_filter(srt, video_format)
    enc = config.ENCODING

    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(video),
         "-vf", sub_filter,
         "-c:v", enc["vcodec"],
         "-preset", enc["preset"],
         "-crf", str(enc["crf"]),
         "-c:a", "copy",
         "-pix_fmt", "yuv420p",
         str(output)],
        capture_output=True, check=True,
    )
    return output


def _get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def _cleanup_temp(work_dir: Path):
    for pattern in ["_seg_*.mp4", "_narration_*", "_pause.*",
                    "_concat_*", "_silence.*", "_slideshow.*",
                    "_nosub.*", "_mixed_*", "_segment_*", "_narration_list.*"]:
        for f in work_dir.glob(pattern):
            f.unlink(missing_ok=True)
