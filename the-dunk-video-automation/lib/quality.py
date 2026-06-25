import json
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_settings():
    path = os.path.join(BASE_DIR, "config", "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_ffprobe(video_path):
    try:
        r = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path
        ], capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout)
    except Exception as e:
        return {"error": str(e)}


def run_decode_check(video_path):
    try:
        r = subprocess.run([
            "ffmpeg", "-v", "error",
            "-i", video_path,
            "-f", "null", "-"
        ], capture_output=True, text=True, timeout=120)
        errors = r.stderr.strip()
        return {"ok": len(errors) == 0, "errors": errors}
    except Exception as e:
        return {"ok": False, "errors": str(e)}


def check_zero_kb(directory):
    zero_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.getsize(fp) == 0:
                    zero_files.append(fp)
            except OSError:
                pass
    return zero_files


def run_quality_check(video_path, mode="production", tts_info=None):
    settings = load_settings()
    results = []
    overall_pass = True

    if not os.path.exists(video_path):
        return {
            "pass": False,
            "checks": [{"name": "ファイル存在", "pass": False, "detail": "ファイルが見つかりません"}],
        }

    file_size = os.path.getsize(video_path)
    results.append({
        "name": "ファイルサイズ",
        "pass": file_size > 0,
        "detail": f"{file_size / 1024 / 1024:.2f} MB",
    })
    if file_size == 0:
        overall_pass = False

    probe = run_ffprobe(video_path)
    if "error" in probe:
        results.append({"name": "ffprobe", "pass": False, "detail": probe["error"]})
        return {"pass": False, "checks": results}

    video_stream = None
    audio_stream = None
    for s in probe.get("streams", []):
        if s.get("codec_type") == "video" and not video_stream:
            video_stream = s
        elif s.get("codec_type") == "audio" and not audio_stream:
            audio_stream = s

    if not video_stream:
        results.append({"name": "映像ストリーム", "pass": False, "detail": "映像ストリームなし"})
        overall_pass = False
    else:
        w = int(video_stream.get("width", 0))
        h = int(video_stream.get("height", 0))
        ok = w == settings["video"]["width"] and h == settings["video"]["height"]
        results.append({"name": "解像度", "pass": ok, "detail": f"{w}x{h}"})
        if not ok:
            overall_pass = False

        codec = video_stream.get("codec_name", "")
        ok = codec == "h264"
        results.append({"name": "映像コーデック", "pass": ok, "detail": codec})
        if not ok:
            overall_pass = False

        pix_fmt = video_stream.get("pix_fmt", "")
        ok = pix_fmt == "yuv420p"
        results.append({"name": "ピクセルフォーマット", "pass": ok, "detail": pix_fmt})
        if not ok:
            overall_pass = False

        fps_str = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            fps = 0
        ok = abs(fps - settings["video"]["fps"]) < 1
        results.append({"name": "FPS", "pass": ok, "detail": f"{fps:.2f}"})
        if not ok:
            overall_pass = False

    if not audio_stream:
        results.append({"name": "音声ストリーム", "pass": False, "detail": "音声ストリームなし"})
        overall_pass = False
    else:
        a_codec = audio_stream.get("codec_name", "")
        ok = a_codec == "aac"
        results.append({"name": "音声コーデック", "pass": ok, "detail": a_codec})
        if not ok:
            overall_pass = False

    duration = float(probe.get("format", {}).get("duration", 0))
    min_dur = settings["video"]["min_duration"]
    max_dur = settings["video"]["max_duration"]
    ok = min_dur <= duration <= max_dur
    results.append({"name": "再生時間", "pass": ok, "detail": f"{duration:.2f}秒 (規定: {min_dur}-{max_dur}秒)"})
    if not ok:
        overall_pass = False

    decode = run_decode_check(video_path)
    results.append({"name": "decode検査", "pass": decode["ok"], "detail": decode["errors"] if decode["errors"] else "OK"})
    if not decode["ok"]:
        overall_pass = False

    output_dir = os.path.dirname(video_path)
    zero_files = check_zero_kb(output_dir)
    ok = len(zero_files) == 0
    results.append({"name": "0KB検査", "pass": ok, "detail": f"{len(zero_files)}件" + (f": {zero_files}" if zero_files else "")})
    if not ok:
        overall_pass = False
        for zf in zero_files:
            try:
                os.remove(zf)
            except OSError:
                pass

    if mode == "production" and tts_info:
        ok = tts_info.get("engine") == "VOICEVOX"
        results.append({"name": "TTS", "pass": ok, "detail": tts_info.get("engine", "不明")})
        if not ok:
            overall_pass = False

    return {"pass": overall_pass, "checks": results, "duration": duration, "probe": probe}


def save_quality_report(result, output_path):
    report = {
        "pass": result["pass"],
        "checks": result["checks"],
        "duration": result.get("duration"),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path
