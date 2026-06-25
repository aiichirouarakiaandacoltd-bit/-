"""動画検証モジュール"""
import os
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


def validate_video(video_path, expected_config, video_type="long"):
    """ffprobeで動画を検証"""
    results = {
        "file": video_path,
        "type": video_type,
        "checks": [],
        "passed": True,
        "errors": [],
    }

    if not os.path.exists(video_path):
        results["passed"] = False
        results["errors"].append("ファイルが存在しません")
        return results

    file_size = os.path.getsize(video_path)
    if file_size == 0:
        results["passed"] = False
        results["errors"].append("0KBファイルです")
        return results
    results["checks"].append({"check": "ファイルサイズ", "value": f"{file_size / 1024 / 1024:.1f}MB", "passed": True})

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels,duration",
        "-show_entries", "format=duration,size",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        results["passed"] = False
        results["errors"].append(f"ffprobe実行エラー: {result.stderr[:200]}")
        return results

    try:
        probe_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        results["passed"] = False
        results["errors"].append("ffprobe出力パースエラー")
        return results

    streams = probe_data.get("streams", [])
    video_stream = None
    audio_stream = None
    for s in streams:
        if s.get("codec_type") == "video":
            video_stream = s
        elif s.get("codec_type") == "audio":
            audio_stream = s

    if not video_stream:
        results["passed"] = False
        results["errors"].append("映像ストリームがありません")
    else:
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        codec = video_stream.get("codec_name", "")

        w_ok = width == expected_config["width"]
        h_ok = height == expected_config["height"]
        results["checks"].append({"check": "解像度", "value": f"{width}x{height}", "expected": f"{expected_config['width']}x{expected_config['height']}", "passed": w_ok and h_ok})
        if not (w_ok and h_ok):
            results["errors"].append(f"解像度不一致: {width}x{height}")

        codec_ok = codec == "h264"
        results["checks"].append({"check": "コーデック", "value": codec, "expected": "h264", "passed": codec_ok})
        if not codec_ok:
            results["errors"].append(f"コーデック不一致: {codec}")

        fps_str = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            fps = 0
        fps_ok = abs(fps - expected_config["fps"]) < 1
        results["checks"].append({"check": "フレームレート", "value": f"{fps:.1f}fps", "expected": f"{expected_config['fps']}fps", "passed": fps_ok})

    if not audio_stream:
        results["passed"] = False
        results["errors"].append("音声ストリームがありません")
    else:
        audio_codec = audio_stream.get("codec_name", "")
        audio_ok = audio_codec == "aac"
        results["checks"].append({"check": "音声コーデック", "value": audio_codec, "expected": "aac", "passed": audio_ok})
        if not audio_ok:
            results["errors"].append(f"音声コーデック不一致: {audio_codec}")

        channels = int(audio_stream.get("channels", 0))
        ch_ok = channels == 2
        results["checks"].append({"check": "チャンネル", "value": f"{channels}ch", "expected": "2ch(ステレオ)", "passed": ch_ok})

    format_data = probe_data.get("format", {})
    duration = float(format_data.get("duration", 0))
    results["checks"].append({"check": "再生時間", "value": f"{duration:.1f}秒", "passed": duration > 0})

    if video_type == "long":
        duration_ok = 30 < duration
        if not duration_ok:
            results["errors"].append(f"長尺動画が短すぎます: {duration:.1f}秒")
    elif video_type == "shorts":
        duration_ok = 10 < duration < 120
        if not duration_ok:
            results["errors"].append(f"Shorts動画の長さが範囲外: {duration:.1f}秒")

    results["duration_seconds"] = duration
    results["file_size_mb"] = file_size / 1024 / 1024
    results["passed"] = len(results["errors"]) == 0

    return results


def print_validation_report(results):
    """検証結果を表示"""
    status = "✅ PASS" if results["passed"] else "❌ FAIL"
    logger.info(f"\n{'='*60}")
    logger.info(f"検証結果: {status}")
    logger.info(f"ファイル: {results['file']}")
    logger.info(f"タイプ: {results['type']}")
    logger.info(f"{'='*60}")

    for check in results.get("checks", []):
        mark = "✅" if check["passed"] else "❌"
        expected = f" (期待値: {check['expected']})" if "expected" in check else ""
        logger.info(f"  {mark} {check['check']}: {check['value']}{expected}")

    if results["errors"]:
        logger.info(f"\nエラー:")
        for err in results["errors"]:
            logger.info(f"  ❌ {err}")

    return results["passed"]
