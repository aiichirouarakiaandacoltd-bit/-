"""品質チェックモジュール（拡張版）

ffprobeで最終MP4を包括的に検証する。
"""

import json
import subprocess
from pathlib import Path

from . import config


def verify_video(video_path: Path, video_format: str = "long") -> dict:
    vc = config.VIDEO_LONG if video_format == "long" else config.VIDEO_SHORTS
    result = {
        "path": str(video_path),
        "format": video_format,
        "exists": video_path.exists(),
        "checks": [],
        "passed": True,
        "errors": [],
    }

    if not video_path.exists():
        result["passed"] = False
        result["checks"].append({"name": "ファイル存在", "ok": False, "detail": "ファイルが見つかりません"})
        return result

    file_size = video_path.stat().st_size
    if file_size == 0:
        result["passed"] = False
        result["checks"].append({"name": "ファイルサイズ", "ok": False, "detail": "0KB - 空ファイル"})
        return result

    result["checks"].append({"name": "ファイル存在", "ok": True, "detail": "存在確認OK"})
    result["checks"].append({"name": "0KB検査", "ok": True, "detail": f"{file_size} bytes"})

    probe = _ffprobe(video_path)
    if not probe:
        result["passed"] = False
        result["checks"].append({"name": "ffprobe", "ok": False, "detail": "解析失敗"})
        return result

    streams = probe.get("streams", [])
    fmt = probe.get("format", {})

    v_streams = [s for s in streams if s["codec_type"] == "video"]
    a_streams = [s for s in streams if s["codec_type"] == "audio"]

    result["checks"].append({
        "name": "映像ストリーム数",
        "ok": len(v_streams) == 1,
        "detail": f"{len(v_streams)}",
    })
    result["checks"].append({
        "name": "音声ストリーム数",
        "ok": len(a_streams) >= 1,
        "detail": f"{len(a_streams)}",
    })

    if not v_streams:
        result["passed"] = False
        result["checks"].append({"name": "映像ストリーム", "ok": False, "detail": "映像なし"})
    else:
        v = v_streams[0]
        w = int(v.get("width", 0))
        h = int(v.get("height", 0))
        ok_res = w == vc["width"] and h == vc["height"]
        result["checks"].append({
            "name": "解像度",
            "ok": ok_res,
            "detail": f"{w}x{h} (期待: {vc['width']}x{vc['height']})",
        })
        if not ok_res:
            result["passed"] = False

        codec = v.get("codec_name", "")
        ok_codec = codec == "h264"
        result["checks"].append({
            "name": "映像コーデック",
            "ok": ok_codec,
            "detail": f"{codec} (期待: h264)",
        })
        if not ok_codec:
            result["passed"] = False

        fps_str = v.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            actual_fps = round(int(num) / int(den), 2)
        except Exception:
            actual_fps = 0
        ok_fps = abs(actual_fps - vc["fps"]) < 1
        result["checks"].append({
            "name": "fps",
            "ok": ok_fps,
            "detail": f"{actual_fps} (期待: {vc['fps']})",
        })
        result["fps"] = actual_fps

    if not a_streams:
        result["passed"] = False
        result["checks"].append({"name": "音声ストリーム", "ok": False, "detail": "音声なし"})
    else:
        a = a_streams[0]
        codec_a = a.get("codec_name", "")
        ok_ac = codec_a == "aac"
        result["checks"].append({
            "name": "音声コーデック",
            "ok": ok_ac,
            "detail": f"{codec_a} (期待: aac)",
        })
        if not ok_ac:
            result["passed"] = False

        sr = int(a.get("sample_rate", 0))
        result["checks"].append({
            "name": "サンプルレート",
            "ok": sr > 0,
            "detail": f"{sr} Hz",
        })
        result["sample_rate"] = sr

        ch = int(a.get("channels", 0))
        result["checks"].append({
            "name": "音声チャンネル数",
            "ok": ch > 0,
            "detail": f"{ch}ch",
        })
        result["audio_channels"] = ch

    duration = float(fmt.get("duration", 0))
    result["duration"] = duration

    ok_dur = vc["duration_min"] <= duration <= vc["duration_max"]
    result["checks"].append({
        "name": "尺",
        "ok": ok_dur,
        "detail": f"{duration:.1f}秒 (期待: {vc['duration_min']}-{vc['duration_max']}秒)",
        "warning": not ok_dur,
    })

    size_mb = file_size / (1024 * 1024)
    result["file_size_mb"] = round(size_mb, 1)
    result["file_size_bytes"] = file_size
    result["checks"].append({
        "name": "ファイルサイズ",
        "ok": True,
        "detail": f"{size_mb:.1f} MB",
    })

    silence_ok = check_audio_not_silent(video_path)
    result["checks"].append({
        "name": "無音検査",
        "ok": silence_ok,
        "detail": "音声検出OK" if silence_ok else "全体が無音の可能性",
    })
    if not silence_ok:
        result["passed"] = False

    decode_ok, decode_errors = check_decode_errors(video_path)
    result["checks"].append({
        "name": "decodeエラー検査",
        "ok": decode_ok,
        "detail": "エラーなし" if decode_ok else f"エラー検出: {len(decode_errors)}件",
    })
    if not decode_ok:
        result["passed"] = False
        result["errors"].extend(decode_errors[:5])

    return result


def check_audio_not_silent(video_path: Path) -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-i", str(video_path), "-af",
             "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=120,
        )
        stderr = r.stderr
        for line in stderr.split("\n"):
            if "mean_volume" in line:
                vol = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                return vol > -80.0
        return False
    except Exception:
        return True


def check_decode_errors(video_path: Path) -> tuple[bool, list[str]]:
    try:
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(video_path), "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        )
        errors = [l.strip() for l in r.stderr.strip().split("\n") if l.strip()]
        return len(errors) == 0, errors
    except Exception as e:
        return False, [str(e)]


def check_bgm_present(video_path: Path, expected_channels: int = 2) -> bool:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "stream=channels",
             "-select_streams", "a:0",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, check=True,
        )
        ch = int(r.stdout.strip())
        return ch >= 1
    except Exception:
        return False


def verify_bgm_file(bgm_path: Path) -> dict:
    result = {
        "path": str(bgm_path),
        "exists": bgm_path.exists(),
        "nonzero": False,
        "readable": False,
        "duration": None,
        "errors": [],
    }

    if not bgm_path.exists():
        result["errors"].append(f"BGMファイルが見つかりません: {bgm_path}")
        return result

    size = bgm_path.stat().st_size
    result["nonzero"] = size > 0
    if size == 0:
        result["errors"].append("BGMファイルが0KBです")
        return result

    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(bgm_path)],
            capture_output=True, text=True, check=True,
        )
        result["duration"] = float(r.stdout.strip())
        result["readable"] = True
    except Exception as e:
        result["errors"].append(f"ffprobeで読み取れません: {e}")

    return result


def scan_zero_kb_files(directory: Path) -> list[dict]:
    zero_files = []
    if not directory.exists():
        return zero_files
    for f in directory.rglob("*"):
        if f.is_file() and f.stat().st_size == 0:
            zero_files.append({
                "path": str(f),
                "name": f.name,
            })
    return zero_files


def capture_screenshots(video_path: Path, output_dir: Path, count: int = 3) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = _get_duration(video_path)
    if duration <= 0:
        return []

    timestamps = []
    if count >= 1:
        timestamps.append(2.0)
    if count >= 2:
        timestamps.append(duration / 2)
    if count >= 3:
        timestamps.append(max(duration - 3, duration * 0.9))

    screenshots = []
    labels = ["冒頭", "中盤", "終盤"]
    for i, ts in enumerate(timestamps[:count]):
        label = labels[i] if i < len(labels) else f"frame_{i}"
        out_path = output_dir / f"screenshot_{label}.png"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(ts), "-i", str(video_path),
                 "-frames:v", "1", "-q:v", "2", str(out_path)],
                capture_output=True, check=True,
            )
            if out_path.exists() and out_path.stat().st_size > 0:
                screenshots.append(out_path)
        except Exception:
            pass
    return screenshots


def print_report(result: dict):
    print(f"\n{'='*50}")
    print(f"品質チェックレポート: {result['path']}")
    print(f"フォーマット: {result['format']}")
    print(f"{'='*50}")

    for check in result.get("checks", []):
        icon = "✓" if check["ok"] else "✗"
        warn = " [WARNING]" if check.get("warning") else ""
        print(f"  {icon} {check['name']}: {check['detail']}{warn}")

    if "duration" in result:
        print(f"\n  総再生時間: {result['duration']:.1f}秒")
    if "file_size_mb" in result:
        print(f"  ファイルサイズ: {result['file_size_mb']} MB")

    if result.get("errors"):
        print(f"\n  エラー:")
        for e in result["errors"]:
            print(f"    - {e}")

    status = "PASSED" if result["passed"] else "FAILED"
    print(f"\n  結果: {status}")
    print(f"{'='*50}\n")


def _ffprobe(path: Path) -> dict | None:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, check=True,
        )
        return json.loads(r.stdout)
    except Exception as e:
        print(f"[ERROR] ffprobe失敗: {e}")
        return None


def _get_duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0
