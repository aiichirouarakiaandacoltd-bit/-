"""Video composition: combine images, audio, subtitles, and BGM into final MP4."""
import subprocess
import tempfile
from pathlib import Path

import config as cfg
from src.subtitle import get_subtitle_filter_long, get_subtitle_filter_shorts


def _extend_audio_with_silence(audio_path, target_duration, output_path):
    """Extend an audio file with silence to reach target duration."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-af", f"apad=whole_dur={target_duration}",
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    _run_ffmpeg(cmd)
    return output_path


def create_concat_video(image_audio_pairs, output_path, width, height, fps):
    """Create a video from image+audio pairs using FFmpeg."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_path.parent / "tmp_segments"
    tmp_dir.mkdir(exist_ok=True)

    segment_paths = []
    for i, pair in enumerate(image_audio_pairs):
        seg_path = tmp_dir / f"seg_{i:04d}.mp4"
        img = pair["image"]
        audio = pair["audio"]
        duration = pair["duration"]

        actual_audio = audio
        from src.voicevox import get_wav_duration
        audio_dur = get_wav_duration(audio)
        if duration > audio_dur + 0.5:
            extended_path = tmp_dir / f"ext_audio_{i:04d}.wav"
            _extend_audio_with_silence(audio, duration, extended_path)
            actual_audio = str(extended_path)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(fps), "-t", str(duration),
            "-i", str(img),
            "-i", str(actual_audio),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            str(seg_path),
        ]
        _run_ffmpeg(cmd)
        segment_paths.append(seg_path)

    concat_file = tmp_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for seg in segment_paths:
            f.write(f"file '{seg}'\n")

    concat_output = output_path.parent / f"concat_raw_{output_path.stem}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(concat_output),
    ]
    _run_ffmpeg(cmd)

    import shutil as _shutil
    _shutil.rmtree(tmp_dir, ignore_errors=True)

    return concat_output


def burn_subtitles(input_path, srt_path, output_path, font_path, is_shorts=False):
    """Burn subtitles into video."""
    if is_shorts:
        sub_filter = get_subtitle_filter_shorts(srt_path, font_path)
    else:
        sub_filter = get_subtitle_filter_long(srt_path, font_path)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run_ffmpeg(cmd)
    return output_path


def mix_bgm(input_path, bgm_path, output_path, video_duration):
    """Mix BGM into video at low volume, with fade in/out."""
    fade_in = 3.0
    fade_out = 5.0
    fade_out_start = max(0, video_duration - fade_out)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-stream_loop", "-1",
        "-i", str(bgm_path),
        "-filter_complex",
        f"[1:a]volume=0.12,afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={fade_out_start}:d={fade_out},"
        f"atrim=0:{video_duration}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run_ffmpeg(cmd)
    return output_path


def get_video_duration(video_path):
    """Get video duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return float(result.stdout.strip())


def take_screenshot(video_path, output_path, timestamp):
    """Take a screenshot from video at given timestamp."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path),
    ]
    _run_ffmpeg(cmd)
    return output_path


def _run_ffmpeg(cmd, timeout=600):
    """Run an FFmpeg command and raise on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\nCommand: {' '.join(cmd)}\nStderr: {result.stderr}")
    return result
