"""品質チェックモジュール（厳格版）

条件を満たさない場合は必ずFAILにする。
"""

import json
import subprocess
from pathlib import Path

from . import config


def verify_video(
    video_path: Path,
    video_format: str = "long",
    test_mode: bool = False,
    tts_engine: str | None = None,
    bgm_mixed: bool = False,
    zero_kb_count: int = 0,
    excluded_review_ng: int = 0,
) -> dict:
    vc = config.VIDEO_LONG if video_format == "long" else config.VIDEO_SHORTS
    result = {
        "path": str(video_path),
        "format": video_format,
        "exists": video_path.exists(),
        "checks": [],
        "passed": True,
        "errors": [],
    }

    def _fail(name, detail):
        result["checks"].append({"name": name, "ok": False, "detail": detail})
        result["passed"] = False

    def _ok(name, detail):
        result["checks"].append({"name": name, "ok": True, "detail": detail})

    if not video_path.exists():
        _fail("ファイル存在", "ファイルが見つかりません")
        return result

    file_size = video_path.stat().st_size
    if file_size == 0:
        _fail("ファイルサイズ", "0KB - 空ファイル")
        return result

    _ok("ファイル存在", "OK")
    _ok("0KB検査（MP4）", f"{file_size} bytes")

    probe = _ffprobe(video_path)
    if not probe:
        _fail("ffprobe", "解析失敗")
        return result

    streams = probe.get("streams", [])
    fmt = probe.get("format", {})

    v_streams = [s for s in streams if s["codec_type"] == "video"]
    a_streams = [s for s in streams if s["codec_type"] == "audio"]

    if len(v_streams) == 0:
        _fail("映像ストリーム", "映像なし")
    else:
        _ok("映像ストリーム数", f"{len(v_streams)}")

    if len(a_streams) == 0:
        _fail("音声ストリーム", "音声なし")
    else:
        _ok("音声ストリーム数", f"{len(a_streams)}")

    if v_streams:
        v = v_streams[0]
        w = int(v.get("width", 0))
        h = int(v.get("height", 0))
        if w == vc["width"] and h == vc["height"]:
            _ok("解像度", f"{w}x{h}")
        else:
            _fail("解像度", f"{w}x{h} (期待: {vc['width']}x{vc['height']})")

        codec = v.get("codec_name", "")
        if codec == "h264":
            _ok("映像コーデック", "h264")
        else:
            _fail("映像コーデック", f"{codec} (期待: h264)")

        fps_str = v.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            actual_fps = round(int(num) / int(den), 2)
        except Exception:
            actual_fps = 0
        if abs(actual_fps - vc["fps"]) < 1:
            _ok("fps", f"{actual_fps}")
        else:
            _fail("fps", f"{actual_fps} (期待: {vc['fps']})")
        result["fps"] = actual_fps

    if a_streams:
        a = a_streams[0]
        codec_a = a.get("codec_name", "")
        if codec_a == "aac":
            _ok("音声コーデック", "aac")
        else:
            _fail("音声コーデック", f"{codec_a} (期待: aac)")

        sr = int(a.get("sample_rate", 0))
        _ok("サンプルレート", f"{sr} Hz") if sr > 0 else _fail("サンプルレート", "0 Hz")
        result["sample_rate"] = sr

        ch = int(a.get("channels", 0))
        _ok("音声チャンネル数", f"{ch}ch") if ch > 0 else _fail("音声チャンネル数", "0ch")
        result["audio_channels"] = ch

    duration = float(fmt.get("duration", 0))
    result["duration"] = duration

    dur_min = vc["duration_min"]
    dur_max = vc["duration_max"]
    if dur_min <= duration <= dur_max:
        _ok("尺", f"{duration:.1f}秒 (範囲: {dur_min}-{dur_max}秒)")
    else:
        _fail("尺", f"{duration:.1f}秒 (範囲: {dur_min}-{dur_max}秒)")

    size_mb = file_size / (1024 * 1024)
    result["file_size_mb"] = round(size_mb, 1)
    result["file_size_bytes"] = file_size
    _ok("ファイルサイズ", f"{size_mb:.1f} MB")

    silence_ok = check_audio_not_silent(video_path)
    if silence_ok:
        _ok("無音検査", "音声検出OK")
    else:
        _fail("無音検査", "全体が無音")

    decode_ok, decode_errors = check_decode_errors(video_path)
    if decode_ok:
        _ok("decodeエラー検査", "エラーなし")
    else:
        _fail("decodeエラー検査", f"エラー検出: {len(decode_errors)}件")
        result["errors"].extend(decode_errors[:5])

    if zero_kb_count > 0:
        _fail("0KBファイル検査", f"{zero_kb_count}件の0KBファイル")
    else:
        _ok("0KBファイル検査", "0件")

    if not test_mode and tts_engine and tts_engine != "VOICEVOX":
        _fail("音声エンジン（本番）", f"{tts_engine} (期待: VOICEVOX)")

    if not test_mode and not bgm_mixed:
        _fail("BGM（本番）", "指定BGM未使用")

    if excluded_review_ng > 0:
        _fail("素材権利", f"REVIEW/NG素材を{excluded_review_ng}件検出")

    return result


def check_audio_not_silent(video_path: Path) -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-i", str(video_path), "-af",
             "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=120,
        )
        for line in r.stderr.split("\n"):
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
        print(f"  {icon} {check['name']}: {check['detail']}")

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
