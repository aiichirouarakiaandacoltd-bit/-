"""動画編集・MP4生成モジュール"""
import os
import subprocess
import json
import logging
from PIL import Image
from pydub import AudioSegment
from src.config import LONG_VIDEO, SHORTS_VIDEO, FONT_PATH, AUDIO_SAMPLE_RATE

logger = logging.getLogger(__name__)


def _get_subtitle_filter(srt_path, video_type="long"):
    """字幕焼き込み用FFmpegフィルタを生成"""
    if not os.path.exists(srt_path):
        return ""
    font_spec = ""
    if FONT_PATH and os.path.exists(FONT_PATH):
        escaped_font = FONT_PATH.replace(":", "\\\\:")
        font_spec = f"FontName={escaped_font},"
    if video_type == "long":
        fontsize = 36
        margin_v = 60
    else:
        fontsize = 32
        margin_v = 120
    escaped_srt = srt_path.replace(":", "\\\\:").replace("'", "\\\\'")
    return f"subtitles='{escaped_srt}':{font_spec}force_style='FontSize={fontsize},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,MarginV={margin_v}'"


def create_slideshow_video(images, durations, output_path, video_config):
    """画像スライドショー動画を生成"""
    w, h, fps = video_config["width"], video_config["height"], video_config["fps"]

    concat_file = output_path.replace(".mp4", "_concat.txt")
    temp_clips = []

    for i, (img_path, duration) in enumerate(zip(images, durations)):
        temp_path = output_path.replace(".mp4", f"_clip{i:03d}.mp4")
        temp_clips.append(temp_path)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_path,
            "-t", str(duration),
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z='min(zoom+0.0005,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration*fps)}:s={w}x{h}:fps={fps}",
            "-c:v", video_config["codec"],
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            temp_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning(f"ズームパン失敗、単純スケールにフォールバック: clip {i}")
            cmd_simple = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", img_path,
                "-t", str(duration),
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black",
                "-c:v", video_config["codec"],
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                temp_path,
            ]
            subprocess.run(cmd_simple, capture_output=True, text=True, timeout=120)

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip}'\n")

    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", video_config["codec"],
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        output_path,
    ]
    subprocess.run(cmd_concat, capture_output=True, text=True, timeout=300)

    for clip in temp_clips:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(concat_file):
        os.remove(concat_file)

    logger.info(f"スライドショー動画生成: {output_path}")
    return output_path


def merge_video_audio(video_path, audio_path, output_path, srt_path=None, video_type="long"):
    """映像と音声を結合し、字幕を焼き込み"""
    audio = AudioSegment.from_wav(audio_path)
    audio_duration = len(audio) / 1000.0

    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "json", video_path]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
    video_duration = audio_duration
    try:
        probe_data = json.loads(probe_result.stdout)
        video_duration = float(probe_data["format"]["duration"])
    except (json.JSONDecodeError, KeyError):
        pass

    vf_filters = []
    if srt_path and os.path.exists(srt_path):
        sub_filter = _get_subtitle_filter(srt_path, video_type)
        if sub_filter:
            vf_filters.append(sub_filter)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-ac", "2",
        "-shortest",
        "-pix_fmt", "yuv420p",
    ]

    if vf_filters:
        cmd.extend(["-vf", ",".join(vf_filters)])

    cmd.append(output_path)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.warning(f"字幕焼き込み失敗、字幕なしで結合: {result.stderr[:500]}")
        cmd_nosub = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-c:a", "aac",
            "-b:a", "192k", "-ar", str(AUDIO_SAMPLE_RATE),
            "-ac", "2", "-shortest", "-pix_fmt", "yuv420p",
            output_path,
        ]
        subprocess.run(cmd_nosub, capture_output=True, text=True, timeout=600)

    logger.info(f"映像音声結合完了: {output_path}")
    return output_path


def build_long_video(images_info, audio_path, srt_path, output_dir):
    """長尺動画を構築"""
    audio = AudioSegment.from_wav(audio_path)
    total_duration = len(audio) / 1000.0

    image_paths = [img["path"] for img in images_info]
    if not image_paths:
        logger.error("画像がありません")
        return None

    duration_per_image = total_duration / len(image_paths)
    durations = [duration_per_image] * len(image_paths)

    temp_video = os.path.join(output_dir, "temp_slideshow.mp4")
    create_slideshow_video(image_paths, durations, temp_video, LONG_VIDEO)

    final_path = os.path.join(output_dir, "final_long.mp4")
    merge_video_audio(temp_video, audio_path, final_path, srt_path, "long")

    if os.path.exists(temp_video):
        os.remove(temp_video)

    return final_path


def build_shorts_video(images_info, audio_path, srt_path, output_dir, index=1):
    """Shorts動画を構築"""
    audio = AudioSegment.from_wav(audio_path)
    total_duration = len(audio) / 1000.0

    image_paths = [img["path"] for img in images_info]
    if not image_paths:
        logger.error("画像がありません")
        return None

    duration_per_image = total_duration / len(image_paths)
    durations = [duration_per_image] * len(image_paths)

    idx = f"{index:02d}"
    temp_video = os.path.join(output_dir, f"temp_shorts_{idx}.mp4")
    create_slideshow_video(image_paths, durations, temp_video, SHORTS_VIDEO)

    final_path = os.path.join(output_dir, f"final_short_{idx}.mp4")
    merge_video_audio(temp_video, audio_path, final_path, srt_path, "shorts")

    if os.path.exists(temp_video):
        os.remove(temp_video)

    return final_path
