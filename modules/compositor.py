"""
Video composition module for showa-heisei-video-automation.
Builds final MP4 videos from image sequences, narration audio,
ASS subtitles, and BGM using FFmpeg filter_complex pipelines.
"""

import os
import subprocess
import shutil
import tempfile
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type aliases for clarity
# ---------------------------------------------------------------------------
ImageEntry = dict[str, Any]   # {"image_path": str, "duration_seconds": float, "label": str}
VideoConfig = dict[str, Any]  # Subset of settings.yaml


# ---------------------------------------------------------------------------
# Helper: get image dimensions via ffprobe
# ---------------------------------------------------------------------------

def _probe_image_size(image_path: str) -> tuple[int, int]:
    """Return (width, height) of an image using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        image_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        parts = result.stdout.strip().split("x")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception as e:
        logger.warning(f"画像サイズ取得失敗 ({image_path}): {e}")
    return 0, 0


def _probe_audio_duration(audio_path: str) -> float:
    """Return duration in seconds of an audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        audio_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"音声長取得失敗 ({audio_path}): {e}")
    return 0.0


# ---------------------------------------------------------------------------
# Image preparation
# ---------------------------------------------------------------------------

def prepare_image_for_format(
    image_path: str,
    target_width: int,
    target_height: int,
    temp_dir: str,
) -> str:
    """
    Resize and pad an image so it fits *target_width x target_height*
    without exceeding 1.1x the original size and preserving aspect ratio.

    For 9:16 (shorts) the image is centre-cropped/padded to portrait.
    Returns path to the prepared image inside *temp_dir*.
    """
    src_w, src_h = _probe_image_size(image_path)
    if src_w == 0 or src_h == 0:
        logger.warning(f"画像サイズ不明のため元画像をそのまま使用: {image_path}")
        return image_path

    # Determine scale factor keeping aspect ratio
    scale_w = target_width / src_w
    scale_h = target_height / src_h
    scale = min(scale_w, scale_h)

    # Cap enlargement at 1.1x
    if scale > 1.1:
        scale = 1.1

    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    # Ensure even dimensions
    new_w = new_w if new_w % 2 == 0 else new_w + 1
    new_h = new_h if new_h % 2 == 0 else new_h + 1

    basename = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(temp_dir, f"{basename}_{target_width}x{target_height}.png")

    vf = (
        f"scale={new_w}:{new_h}:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
    )

    cmd = [
        "ffmpeg", "-y", "-v", "warning",
        "-i", image_path,
        "-vf", vf,
        "-frames:v", "1",
        out_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        return out_path
    except subprocess.CalledProcessError as e:
        logger.error(f"画像前処理失敗 ({image_path}): {e.stderr}")
        raise RuntimeError(f"画像前処理に失敗しました: {image_path}") from e


# ---------------------------------------------------------------------------
# Filter builders
# ---------------------------------------------------------------------------

def build_image_sequence_filter(
    images: list[ImageEntry],
    target_width: int,
    target_height: int,
    fps: int,
) -> tuple[str, int]:
    """
    Build zoompan + xfade filter chain for an image sequence.

    Each image gets a gentle Ken Burns effect (slow zoom 1.0 -> 1.05 or
    slow pan) and consecutive images are cross-faded over 0.5 s.

    Returns:
        (filter_string, number_of_image_inputs)
    """
    crossfade_duration = 0.5
    parts: list[str] = []
    n = len(images)

    for i, img in enumerate(images):
        dur = img["duration_seconds"]
        total_frames = int(dur * fps)

        # Alternate between zoom-in and slow pan for variety
        if i % 2 == 0:
            # Slow zoom 1.0 -> 1.05
            zoom_expr = "min(zoom+0.00005,1.05)"
            x_expr = f"iw/2-(iw/zoom/2)"
            y_expr = f"ih/2-(ih/zoom/2)"
        else:
            # Slow pan left-to-right
            max_pan = int(target_width * 0.05)
            zoom_expr = "1.03"
            x_expr = f"if(eq(on,0),0,min(x+{max(max_pan / max(total_frames, 1), 0.01):.4f},{max_pan}))"
            y_expr = f"ih/2-(ih/zoom/2)"

        zp = (
            f"[{i}:v]zoompan="
            f"z='{zoom_expr}':"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"d={total_frames}:"
            f"s={target_width}x{target_height}:"
            f"fps={fps},"
            f"setpts=PTS-STARTPTS,setsar=1"
            f"[v{i}]"
        )
        parts.append(zp)

    # Chain xfade transitions
    if n == 1:
        # Single image, no xfade needed
        filter_str = ";".join(parts)
        # Rename output label
        filter_str = filter_str.replace(f"[v0]", "[vout]")
        return filter_str, n

    # Build xfade chain
    # Accumulate offset for each transition
    current_label = "v0"
    offset_acc = images[0]["duration_seconds"] - crossfade_duration

    for i in range(1, n):
        next_label = f"v{i}"
        out_label = f"vx{i}" if i < n - 1 else "vout"
        xf = (
            f"[{current_label}][{next_label}]xfade="
            f"transition=fade:"
            f"duration={crossfade_duration}:"
            f"offset={offset_acc:.3f},"
            f"setpts=PTS-STARTPTS"
            f"[{out_label}]"
        )
        parts.append(xf)
        offset_acc += images[i]["duration_seconds"] - crossfade_duration
        current_label = out_label

    filter_str = ";".join(parts)
    return filter_str, n


def build_subtitle_filter(ass_path: str) -> str:
    """Return the ass filter string for subtitle burn-in via libass."""
    # Escape colons and backslashes for FFmpeg filter syntax on all platforms
    escaped = ass_path.replace("\\", "/").replace(":", "\\:")
    return f"ass='{escaped}'"


def build_audio_mix_filter(
    narration_input_idx: int,
    bgm_input_idx: int,
    config: dict[str, Any],
) -> str:
    """
    Build audio mixing filter: narration at full volume, BGM ducked.

    Uses sidechaincompress when ducking is enabled, otherwise simple
    volume adjustment on the BGM track. Output label: [aout].
    """
    bgm_cfg = config.get("bgm", {})
    volume_ratio = bgm_cfg.get("volume_ratio", 0.20)
    ducking_enabled = bgm_cfg.get("ducking_enabled", True)
    ducking_threshold_db = bgm_cfg.get("ducking_threshold", -20)
    ducking_ratio = bgm_cfg.get("ducking_ratio", 0.15)

    if ducking_enabled:
        # sidechaincompress: BGM is compressed when narration is loud
        # First lower BGM volume, then apply sidechain
        parts = [
            f"[{bgm_input_idx}:a]volume={volume_ratio}[bgm_vol]",
            (
                f"[bgm_vol][{narration_input_idx}:a]sidechaincompress="
                f"threshold={ducking_threshold_db}dB:"
                f"ratio={1 / max(ducking_ratio, 0.01):.1f}:"
                f"attack=0.1:release=0.5"
                f"[bgm_ducked]"
            ),
            (
                f"[{narration_input_idx}:a][bgm_ducked]amix="
                f"inputs=2:duration=first:dropout_transition=2"
                f"[aout]"
            ),
        ]
    else:
        parts = [
            f"[{bgm_input_idx}:a]volume={volume_ratio}[bgm_vol]",
            (
                f"[{narration_input_idx}:a][bgm_vol]amix="
                f"inputs=2:duration=first:dropout_transition=2"
                f"[aout]"
            ),
        ]

    return ";".join(parts)


# ---------------------------------------------------------------------------
# FFmpeg command builder & runner
# ---------------------------------------------------------------------------

def build_ffmpeg_command(
    images: list[ImageEntry],
    audio_path: str,
    subtitle_ass: str,
    bgm_path: str,
    output_path: str,
    video_config: dict[str, Any],
    full_config: dict[str, Any],
) -> list[str]:
    """
    Build the complete ffmpeg command with filter_complex for:
      - Image sequence with Ken Burns + xfade
      - Subtitle overlay (ass filter)
      - Audio mixing (narration + BGM with ducking)
    """
    width = video_config["width"]
    height = video_config["height"]
    fps = video_config["fps"]
    codec_video = video_config.get("codec_video", "libx264")
    codec_audio = video_config.get("codec_audio", "aac")
    pix_fmt = video_config.get("pix_fmt", "yuv420p")

    # --- inputs ---
    cmd: list[str] = ["ffmpeg", "-y"]

    # Image inputs: one -loop 1 -t <dur> -i <path> per image
    for img in images:
        cmd.extend([
            "-loop", "1",
            "-t", f"{img['duration_seconds']:.3f}",
            "-i", img["image_path"],
        ])

    n_images = len(images)

    # Narration audio input
    narration_idx = n_images
    cmd.extend(["-i", audio_path])

    # BGM audio input
    bgm_idx = n_images + 1
    cmd.extend(["-stream_loop", "-1", "-i", bgm_path])

    # --- filter_complex ---
    img_filter, _ = build_image_sequence_filter(images, width, height, fps)
    sub_filter = build_subtitle_filter(subtitle_ass)
    audio_filter = build_audio_mix_filter(narration_idx, bgm_idx, full_config)

    # Chain: image sequence -> subtitle burn-in
    video_chain = f"{img_filter};[vout]{sub_filter}[vfinal]"

    filter_complex = f"{video_chain};{audio_filter}"

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", "[aout]",
        "-c:v", codec_video,
        "-preset", "medium",
        "-crf", "20",
        "-c:a", codec_audio,
        "-b:a", "192k",
        "-r", str(fps),
        "-pix_fmt", pix_fmt,
        "-movflags", "+faststart",
        "-shortest",
        output_path,
    ])

    return cmd


def run_ffmpeg(command: list[str]) -> None:
    """
    Execute an ffmpeg command with full logging.

    Raises RuntimeError on non-zero exit.
    """
    cmd_str = " ".join(command)
    logger.info(f"FFmpegコマンド実行:\n{cmd_str}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes max
        )
    except subprocess.TimeoutExpired:
        logger.error("FFmpegがタイムアウトしました (30分)")
        raise RuntimeError("FFmpegの実行がタイムアウトしました。処理時間が長すぎます。")
    except FileNotFoundError:
        logger.error("FFmpegが見つかりません。インストールされているか確認してください。")
        raise RuntimeError("FFmpegが見つかりません。インストールしてください。")

    if result.returncode != 0:
        stderr_tail = result.stderr[-2000:] if result.stderr else "(出力なし)"
        logger.error(f"FFmpeg失敗 (exit {result.returncode}):\n{stderr_tail}")
        raise RuntimeError(
            f"FFmpegがエラーで終了しました (exit code {result.returncode})。"
            f"詳細はログを確認してください。"
        )

    logger.info("FFmpeg正常終了")
    if result.stderr:
        # Log last few lines as debug
        for line in result.stderr.strip().splitlines()[-5:]:
            logger.debug(f"  ffmpeg: {line}")


# ---------------------------------------------------------------------------
# VideoCompositor class
# ---------------------------------------------------------------------------

class VideoCompositor:
    """
    Orchestrates video composition for long-format and shorts videos.

    Usage::

        compositor = VideoCompositor(config)
        compositor.compose_all(images, audio_path, subtitle_ass,
                               bgm_path, output_dir)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.video_long = config.get("video", {}).get("long", {})
        self.video_shorts = config.get("video", {}).get("shorts", {})

    # ------------------------------------------------------------------
    # Long format
    # ------------------------------------------------------------------

    def compose_long(
        self,
        images: list[ImageEntry],
        audio_path: str,
        subtitle_ass: str,
        bgm_path: str,
        output_path: str,
    ) -> str:
        """
        Compose the long-format (16:9) video.

        Args:
            images: List of dicts with image_path, duration_seconds, label.
            audio_path: Path to narration WAV/MP3.
            subtitle_ass: Path to ASS subtitle file.
            bgm_path: Path to BGM audio file.
            output_path: Desired output MP4 path.

        Returns:
            output_path on success.
        """
        logger.info(f"ロング動画合成開始: {len(images)}枚, 出力={output_path}")
        vcfg = self.video_long
        width = vcfg.get("width", 1920)
        height = vcfg.get("height", 1080)

        self._validate_inputs(images, audio_path, subtitle_ass, bgm_path)

        temp_dir = tempfile.mkdtemp(prefix="compositor_long_")
        try:
            prepared = self._prepare_images(images, width, height, temp_dir)
            cmd = build_ffmpeg_command(
                prepared, audio_path, subtitle_ass, bgm_path,
                output_path, vcfg, self.config,
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            run_ffmpeg(cmd)
            logger.info(f"ロング動画合成完了: {output_path}")
            return output_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Shorts format
    # ------------------------------------------------------------------

    def compose_short(
        self,
        images: list[ImageEntry],
        audio_path: str,
        subtitle_ass: str,
        bgm_path: str,
        output_path: str,
    ) -> str:
        """
        Compose a shorts (9:16) video.

        Images are reformatted to 1080x1920 using scale + crop/pad.

        Args:
            images: List of dicts with image_path, duration_seconds, label.
            audio_path: Path to narration WAV/MP3.
            subtitle_ass: Path to ASS subtitle file (should already be
                          formatted for shorts layout).
            bgm_path: Path to BGM audio file.
            output_path: Desired output MP4 path.

        Returns:
            output_path on success.
        """
        logger.info(f"ショート動画合成開始: {len(images)}枚, 出力={output_path}")
        vcfg = self.video_shorts
        width = vcfg.get("width", 1080)
        height = vcfg.get("height", 1920)

        self._validate_inputs(images, audio_path, subtitle_ass, bgm_path)

        temp_dir = tempfile.mkdtemp(prefix="compositor_short_")
        try:
            prepared = self._prepare_images(images, width, height, temp_dir)
            cmd = build_ffmpeg_command(
                prepared, audio_path, subtitle_ass, bgm_path,
                output_path, vcfg, self.config,
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            run_ffmpeg(cmd)
            logger.info(f"ショート動画合成完了: {output_path}")
            return output_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Compose all outputs
    # ------------------------------------------------------------------

    def compose_all(
        self,
        images: list[ImageEntry],
        audio_path: str,
        subtitles: dict[str, str],
        bgm_path: str,
        output_dir: str,
    ) -> dict[str, str]:
        """
        Orchestrate composition of all output formats.

        Args:
            images: Image sequence for the long video. Each shorts video
                    should be a subset; this method splits by label
                    convention (entries with label containing "shorts_1"
                    or "shorts_2").
            audio_path: Path to narration audio (long format).
            subtitles: Dict mapping format keys to ASS paths::

                {
                    "long": "path/to/long.ass",
                    "shorts_1": "path/to/shorts1.ass",
                    "shorts_2": "path/to/shorts2.ass",
                }

            bgm_path: Path to BGM audio file.
            output_dir: Directory to write output MP4s into.

        Returns:
            Dict mapping format keys to output file paths.
        """
        logger.info(f"全動画合成開始: 出力ディレクトリ={output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        outputs: dict[str, str] = {}

        # --- Long format ---
        long_ass = subtitles.get("long", "")
        if not long_ass:
            raise RuntimeError("ロング動画用の字幕ファイル(ASS)が指定されていません。")

        long_out = os.path.join(output_dir, "long.mp4")
        self.compose_long(images, audio_path, long_ass, bgm_path, long_out)
        outputs["long"] = long_out

        # --- Shorts ---
        for shorts_key in ("shorts_1", "shorts_2"):
            shorts_ass = subtitles.get(shorts_key)
            if not shorts_ass:
                logger.warning(
                    f"{shorts_key}用の字幕ファイルが未指定のためスキップします。"
                )
                continue

            # Collect images that belong to this shorts segment
            shorts_images = [
                img for img in images
                if shorts_key in img.get("label", "")
            ]
            if not shorts_images:
                logger.warning(
                    f"{shorts_key}用の画像が見つかりません。"
                    f"ラベルに'{shorts_key}'を含む画像を確認してください。"
                )
                continue

            # Shorts narration: look for a dedicated audio file next to the
            # long narration, falling back to the long narration itself.
            audio_dir = os.path.dirname(audio_path)
            shorts_audio_candidates = [
                os.path.join(audio_dir, f"{shorts_key}.wav"),
                os.path.join(audio_dir, f"{shorts_key}.mp3"),
                audio_path,  # fallback
            ]
            shorts_audio = next(
                (p for p in shorts_audio_candidates if os.path.isfile(p)),
                audio_path,
            )

            shorts_out = os.path.join(output_dir, f"{shorts_key}.mp4")
            self.compose_short(
                shorts_images, shorts_audio, shorts_ass, bgm_path, shorts_out,
            )
            outputs[shorts_key] = shorts_out

        logger.info(f"全動画合成完了: {list(outputs.keys())}")
        return outputs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_inputs(
        self,
        images: list[ImageEntry],
        audio_path: str,
        subtitle_ass: str,
        bgm_path: str,
    ) -> None:
        """Validate that all input files exist and images list is non-empty."""
        if not images:
            raise RuntimeError("画像リストが空です。最低1枚の画像が必要です。")

        for img in images:
            path = img.get("image_path", "")
            if not os.path.isfile(path):
                raise RuntimeError(f"画像ファイルが見つかりません: {path}")
            dur = img.get("duration_seconds", 0)
            if dur < 1.0 or dur > 30.0:
                logger.warning(
                    f"画像表示時間が範囲外です ({dur}秒): {path}。"
                    f"3〜6秒を推奨します。"
                )

        if not os.path.isfile(audio_path):
            raise RuntimeError(f"音声ファイルが見つかりません: {audio_path}")

        if not os.path.isfile(subtitle_ass):
            raise RuntimeError(f"字幕ファイル(ASS)が見つかりません: {subtitle_ass}")

        if not os.path.isfile(bgm_path):
            raise RuntimeError(f"BGMファイルが見つかりません: {bgm_path}")

    def _prepare_images(
        self,
        images: list[ImageEntry],
        target_width: int,
        target_height: int,
        temp_dir: str,
    ) -> list[ImageEntry]:
        """
        Prepare all images for the target format, returning a new list
        with updated image_path values pointing to the prepared files.
        """
        prepared: list[ImageEntry] = []
        for img in images:
            new_path = prepare_image_for_format(
                img["image_path"], target_width, target_height, temp_dir,
            )
            prepared.append({
                "image_path": new_path,
                "duration_seconds": img["duration_seconds"],
                "label": img.get("label", ""),
            })
        return prepared
