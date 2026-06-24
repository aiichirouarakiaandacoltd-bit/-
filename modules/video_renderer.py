"""
MP4動画レンダリングモジュール
FFmpegを直接使用して高速レンダリング
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from .config import VIDEO_SPEC, BGM_VOLUME_DB

FFMPEG_BIN = None


def _get_ffmpeg() -> str:
    global FFMPEG_BIN
    if FFMPEG_BIN:
        return FFMPEG_BIN
    try:
        import imageio_ffmpeg
        FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
        return FFMPEG_BIN
    except Exception:
        pass
    for candidate in ["ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        try:
            subprocess.run([candidate, "-version"], capture_output=True, check=True)
            FFMPEG_BIN = candidate
            return FFMPEG_BIN
        except Exception:
            pass
    raise RuntimeError("FFmpegが見つかりません")


def _run_ffmpeg(args: list[str], desc: str = ""):
    ffmpeg = _get_ffmpeg()
    cmd = [ffmpeg] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg エラー ({desc}):\n{result.stderr[-2000:]}")
    return result


def _concat_images_to_video(
    slide_paths: list[str],
    durations: list[float],
    output_path: str,
    W: int = 1920,
    H: int = 1080,
    fps: int = 30,
) -> str:
    ffmpeg = _get_ffmpeg()
    concat_lines = []
    for slide_path, duration in zip(slide_paths, durations):
        concat_lines.append(f"file '{slide_path}'")
        concat_lines.append(f"duration {duration:.3f}")
    if slide_paths:
        concat_lines.append(f"file '{slide_paths[-1]}'")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("\n".join(concat_lines))
        concat_file = f.name

    try:
        cmd = [
            ffmpeg, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-r", str(fps),
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg 画像結合エラー:\n{result.stderr[-2000:]}")
    finally:
        os.unlink(concat_file)

    return output_path


def _concat_audio_files(audio_paths: list[str], output_path: str) -> str:
    ffmpeg = _get_ffmpeg()
    valid = [p for p in audio_paths if p and os.path.exists(p)]
    if not valid:
        return None

    if len(valid) == 1:
        cmd = [ffmpeg, "-y", "-i", valid[0], "-acodec", "pcm_s16le", output_path]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    concat_lines = [f"file '{p}'" for p in valid]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("\n".join(concat_lines))
        concat_file = f.name

    try:
        cmd = [
            ffmpeg, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-acodec", "pcm_s16le",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg 音声結合エラー:\n{result.stderr[-2000:]}")
    finally:
        os.unlink(concat_file)

    return output_path


def _mix_audio_with_bgm(
    narration_path: str,
    bgm_path: str | None,
    output_path: str,
    duration: float,
) -> str:
    ffmpeg = _get_ffmpeg()

    if not bgm_path or not os.path.exists(bgm_path):
        if narration_path and os.path.exists(narration_path):
            import shutil
            shutil.copy(narration_path, output_path)
        return output_path

    bgm_volume = 10 ** (BGM_VOLUME_DB / 20)

    cmd = [
        ffmpeg, "-y",
        "-i", narration_path,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex",
        f"[1:a]volume={bgm_volume:.4f},atrim=duration={duration:.3f}[bgm];[0:a][bgm]amix=inputs=2:duration=first[out]",
        "-map", "[out]",
        "-acodec", "aac",
        "-ar", "44100",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  BGMミックス失敗（ナレーションのみ使用）: {result.stderr[-500:]}")
        import shutil
        shutil.copy(narration_path, output_path)

    return output_path


def _merge_video_audio(video_path: str, audio_path: str, output_path: str) -> str:
    ffmpeg = _get_ffmpeg()

    if not audio_path or not os.path.exists(audio_path):
        import shutil
        shutil.copy(video_path, output_path)
        return output_path

    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 動画+音声マージエラー:\n{result.stderr[-2000:]}")
    return output_path


def render_video(
    script: dict,
    all_slides: dict[str, list[str]],
    audio_files: dict[str, str | None],
    audio_durations: dict[str, float],
    subtitle_entries: list[dict],
    bgm_path: str | None,
    output_path: str,
) -> str:
    W, H = VIDEO_SPEC["width"], VIDEO_SPEC["height"]
    FPS = VIDEO_SPEC["fps"]

    output_path = str(output_path)
    tmp_dir = Path(output_path).parent / "_tmp" / "render"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    print("\n[レンダリング開始]")

    all_chapter_slides = []
    all_chapter_durations = []
    chapter_names_order = list(script["chapters"].keys())

    for chapter_name in chapter_names_order:
        slides = all_slides.get(chapter_name, [])
        total_dur = audio_durations.get(chapter_name, 60.0)

        chapter_title_slides = [s for s in slides if "_00_title" in s]
        other_slides = [s for s in slides if "_00_title" not in s]

        title_dur = 3.0
        if chapter_title_slides:
            all_chapter_slides.extend(chapter_title_slides)
            all_chapter_durations.extend([title_dur] * len(chapter_title_slides))
            content_dur = max(0, total_dur - title_dur)
        else:
            content_dur = total_dur

        if other_slides:
            per_slide = content_dur / len(other_slides)
            per_slide = max(per_slide, 3.0)
            all_chapter_slides.extend(other_slides)
            all_chapter_durations.extend([per_slide] * len(other_slides))

        print(f"  第{chapter_names_order.index(chapter_name)+1}章「{chapter_name}」: {len(slides)}枚 / {total_dur:.0f}秒")

    ending_slides = all_slides.get("_ending", [])
    if ending_slides:
        all_chapter_slides.extend(ending_slides)
        all_chapter_durations.extend([8.0] * len(ending_slides))

    total_video_duration = sum(all_chapter_durations)
    print(f"\n  総スライド数: {len(all_chapter_slides)} / 推定尺: {total_video_duration:.0f}秒 ({total_video_duration/60:.1f}分)")

    print("\n  [1] 画像を動画化中...")
    video_no_audio = str(tmp_dir / "video_no_audio.mp4")
    _concat_images_to_video(all_chapter_slides, all_chapter_durations, video_no_audio, W, H, FPS)
    print(f"     完了 ({Path(video_no_audio).stat().st_size // 1024 // 1024}MB)")

    print("\n  [2] ナレーション音声を結合中...")
    narration_paths = [audio_files.get(ch) for ch in chapter_names_order]
    combined_narration = str(tmp_dir / "narration_combined.wav")
    combined_audio_path = _concat_audio_files(narration_paths, combined_narration)

    if combined_audio_path and bgm_path and os.path.exists(bgm_path):
        print("\n  [3] BGMをミックス中...")
        mixed_audio = str(tmp_dir / "audio_mixed.aac")
        combined_audio_path = _mix_audio_with_bgm(
            combined_audio_path, bgm_path, mixed_audio, total_video_duration
        )
    elif bgm_path and not os.path.exists(bgm_path):
        print(f"\n  [3] BGMファイルが見つかりません: {bgm_path} → スキップ")

    print(f"\n  [4] 動画と音声を結合して MP4 書き出し中...")
    print(f"     出力先: {output_path}")

    if combined_audio_path and os.path.exists(combined_audio_path):
        _merge_video_audio(video_no_audio, combined_audio_path, output_path)
    else:
        import shutil
        shutil.copy(video_no_audio, output_path)

    size_mb = Path(output_path).stat().st_size // 1024 // 1024
    print(f"\n  [完了] {output_path} ({size_mb}MB)")
    return output_path
