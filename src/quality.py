"""Quality inspection for generated videos."""
import json
import subprocess
from pathlib import Path

import config as cfg


def inspect_video(video_path):
    """Run ffprobe and return video metadata."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def decode_test(video_path):
    """Run full decode test to check for errors."""
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", str(video_path),
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return {
        "returncode": result.returncode,
        "errors": result.stderr.strip() if result.stderr.strip() else None,
    }


def run_quality_check(video_path, video_type, test_mode=False,
                      bgm_used=False, voicevox_used=False):
    """Run all quality checks and return a report."""
    path = Path(video_path)
    report = {
        "file": str(path),
        "type": video_type,
        "test_mode": test_mode,
        "checks": [],
        "passed": True,
    }

    def add_check(name, ok, detail=""):
        report["checks"].append({"name": name, "passed": ok, "detail": detail})
        if not ok:
            report["passed"] = False

    if not path.exists():
        add_check("file_exists", False, "file not found")
        return report

    size = path.stat().st_size
    add_check("file_not_zero", size > 0, f"{size} bytes")

    probe = inspect_video(video_path)
    if probe is None:
        add_check("ffprobe", False, "ffprobe failed")
        return report
    add_check("ffprobe", True)

    streams = probe.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    add_check("has_video_stream", len(video_streams) > 0,
              f"{len(video_streams)} video stream(s)")
    add_check("has_audio_stream", len(audio_streams) > 0,
              f"{len(audio_streams)} audio stream(s)")

    if video_streams:
        vs = video_streams[0]
        w = int(vs.get("width", 0))
        h = int(vs.get("height", 0))
        codec = vs.get("codec_name", "")

        if video_type == "long":
            exp_w, exp_h = cfg.LONG_WIDTH, cfg.LONG_HEIGHT
        else:
            exp_w, exp_h = cfg.SHORTS_WIDTH, cfg.SHORTS_HEIGHT

        add_check("resolution", w == exp_w and h == exp_h,
                  f"{w}x{h} (expected {exp_w}x{exp_h})")
        add_check("video_codec", codec == "h264", f"{codec} (expected h264)")

        fps_str = vs.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            actual_fps = round(int(num) / int(den), 2)
        except (ValueError, ZeroDivisionError):
            actual_fps = 0
        add_check("fps", abs(actual_fps - 30) < 1, f"{actual_fps} (expected 30)")

    if audio_streams:
        a_codec = audio_streams[0].get("codec_name", "")
        add_check("audio_codec", a_codec == "aac", f"{a_codec} (expected aac)")

    duration = float(probe.get("format", {}).get("duration", 0))
    if video_type == "long":
        dur_ok = cfg.LONG_MIN_DURATION <= duration <= cfg.LONG_MAX_DURATION
        add_check("duration", dur_ok,
                  f"{duration:.1f}s (expected {cfg.LONG_MIN_DURATION}-{cfg.LONG_MAX_DURATION}s)")
    else:
        dur_ok = cfg.SHORTS_MIN_DURATION <= duration <= cfg.SHORTS_MAX_DURATION
        add_check("duration", dur_ok,
                  f"{duration:.1f}s (expected {cfg.SHORTS_MIN_DURATION}-{cfg.SHORTS_MAX_DURATION}s)")

    if not test_mode:
        add_check("voicevox_used", voicevox_used, "VOICEVOX required in production")
        add_check("bgm_used", bgm_used, "BGM required in production")

    decode = decode_test(video_path)
    add_check("decode_test", decode["returncode"] == 0,
              decode["errors"] or "no errors")

    return report


def save_quality_report(reports, output_path):
    """Save quality report as JSON."""
    Path(output_path).write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
    )
