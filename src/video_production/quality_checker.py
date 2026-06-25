"""品質チェックモジュール

ffprobeで最終MP4を検証する。
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
    }

    if not video_path.exists():
        result["passed"] = False
        result["checks"].append({"name": "ファイル存在", "ok": False, "detail": "ファイルが見つかりません"})
        return result

    probe = _ffprobe(video_path)
    if not probe:
        result["passed"] = False
        result["checks"].append({"name": "ffprobe", "ok": False, "detail": "解析失敗"})
        return result

    streams = probe.get("streams", [])
    fmt = probe.get("format", {})

    v_stream = next((s for s in streams if s["codec_type"] == "video"), None)
    a_stream = next((s for s in streams if s["codec_type"] == "audio"), None)

    if v_stream:
        w = int(v_stream.get("width", 0))
        h = int(v_stream.get("height", 0))
        ok = w == vc["width"] and h == vc["height"]
        result["checks"].append({
            "name": "解像度",
            "ok": ok,
            "detail": f"{w}x{h} (期待: {vc['width']}x{vc['height']})",
        })
        if not ok:
            result["passed"] = False

        codec = v_stream.get("codec_name", "")
        ok_codec = codec == "h264"
        result["checks"].append({
            "name": "映像コーデック",
            "ok": ok_codec,
            "detail": f"{codec} (期待: h264)",
        })
        if not ok_codec:
            result["passed"] = False
    else:
        result["passed"] = False
        result["checks"].append({"name": "映像ストリーム", "ok": False, "detail": "映像なし"})

    if a_stream:
        codec = a_stream.get("codec_name", "")
        ok_a = codec == "aac"
        result["checks"].append({
            "name": "音声コーデック",
            "ok": ok_a,
            "detail": f"{codec} (期待: aac)",
        })
        if not ok_a:
            result["passed"] = False
    else:
        result["passed"] = False
        result["checks"].append({"name": "音声ストリーム", "ok": False, "detail": "音声なし"})

    duration = float(fmt.get("duration", 0))
    result["duration"] = duration

    if video_format == "long":
        ok_dur = vc["duration_min"] <= duration <= vc["duration_max"]
        detail = f"{duration:.1f}秒 (期待: {vc['duration_min']}-{vc['duration_max']}秒)"
    else:
        ok_dur = vc["duration_min"] <= duration <= vc["duration_max"]
        detail = f"{duration:.1f}秒 (期待: {vc['duration_min']}-{vc['duration_max']}秒)"

    result["checks"].append({
        "name": "尺",
        "ok": ok_dur,
        "detail": detail,
        "warning": not ok_dur,
    })

    size_mb = video_path.stat().st_size / (1024 * 1024)
    result["file_size_mb"] = round(size_mb, 1)
    result["checks"].append({
        "name": "ファイルサイズ",
        "ok": True,
        "detail": f"{size_mb:.1f} MB",
    })

    return result


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
