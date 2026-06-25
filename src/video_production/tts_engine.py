"""音声合成エンジン

本番モード: VOICEVOX（青山龍星）必須。利用不可ならエラー終了。
テストモード (--test-mode): espeak-ngフォールバック許可。
"""

import subprocess
from pathlib import Path

import requests

from . import config


class TTSError(Exception):
    pass


class VOICEVOXNotAvailableError(TTSError):
    pass


class SpeakerNotFoundError(TTSError):
    pass


def _voicevox_available() -> bool:
    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/speakers", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def resolve_speaker_id() -> dict:
    """VOICEVOXから青山龍星のstyle IDを動的に取得する。"""
    result = {
        "speaker_name": config.VOICEVOX_SPEAKER_NAME,
        "style_name": config.VOICEVOX_STYLE_NAME,
        "style_id": None,
        "voicevox_version": None,
        "found": False,
        "errors": [],
    }

    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/version", timeout=3)
        if r.status_code == 200:
            result["voicevox_version"] = r.text.strip().strip('"')
    except Exception:
        pass

    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/speakers", timeout=5)
        if r.status_code != 200:
            result["errors"].append(f"speakers API: HTTP {r.status_code}")
            return result
    except Exception as e:
        result["errors"].append(f"speakers API接続不可: {e}")
        return result

    speakers = r.json()
    target_name = config.VOICEVOX_SPEAKER_NAME
    target_style = config.VOICEVOX_STYLE_NAME

    for sp in speakers:
        if sp.get("name") == target_name:
            for style in sp.get("styles", []):
                if style.get("name") == target_style:
                    result["style_id"] = style["id"]
                    result["found"] = True
                    return result
            styles = [s.get("name") for s in sp.get("styles", [])]
            result["errors"].append(
                f"話者「{target_name}」にスタイル「{target_style}」がありません。"
                f" 利用可能: {styles}"
            )
            return result

    all_names = [sp.get("name") for sp in speakers]
    result["errors"].append(
        f"話者「{target_name}」が見つかりません。別話者への自動変更は行いません。"
        f" 利用可能話者: {all_names[:10]}"
    )
    return result


def verify_voicevox() -> dict:
    """VOICEVOX接続確認。本番モードの事前チェック用。"""
    result = {
        "api_reachable": False,
        "speakers_fetched": False,
        "target_speaker_found": False,
        "speaker_name": config.VOICEVOX_SPEAKER_NAME,
        "style_name": config.VOICEVOX_STYLE_NAME,
        "style_id": None,
        "voicevox_version": None,
        "test_synthesis_ok": False,
        "test_wav_exists": False,
        "test_wav_nonzero": False,
        "test_wav_sample_rate": None,
        "test_wav_channels": None,
        "test_wav_duration": None,
        "errors": [],
    }

    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/speakers", timeout=5)
        if r.status_code != 200:
            result["errors"].append(f"VOICEVOX API応答: HTTP {r.status_code}")
            return result
        result["api_reachable"] = True
        result["speakers_fetched"] = True
    except Exception as e:
        result["errors"].append(f"VOICEVOX API接続不可: {config.VOICEVOX_HOST} ({e})")
        return result

    sp_info = resolve_speaker_id()
    result["voicevox_version"] = sp_info["voicevox_version"]
    if not sp_info["found"]:
        result["errors"].extend(sp_info["errors"])
        return result
    result["target_speaker_found"] = True
    result["style_id"] = sp_info["style_id"]

    import tempfile
    test_text = "テスト音声です"
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        test_path = Path(tmp.name)

    try:
        synthesize_voicevox(test_text, test_path, speaker_id=sp_info["style_id"])
        result["test_synthesis_ok"] = True

        if test_path.exists():
            result["test_wav_exists"] = True
            size = test_path.stat().st_size
            result["test_wav_nonzero"] = size > 0

            if size > 0:
                info = _get_audio_info(test_path)
                result["test_wav_sample_rate"] = info.get("sample_rate")
                result["test_wav_channels"] = info.get("channels")
                result["test_wav_duration"] = info.get("duration")
    except Exception as e:
        result["errors"].append(f"テスト音声生成失敗: {e}")
    finally:
        test_path.unlink(missing_ok=True)

    return result


def synthesize_voicevox(
    text: str, output_path: Path,
    speed: float | None = None,
    speaker_id: int | None = None,
) -> Path:
    host = config.VOICEVOX_HOST
    sid = speaker_id
    if sid is None:
        sp_info = resolve_speaker_id()
        if not sp_info["found"]:
            raise SpeakerNotFoundError(
                f"青山龍星が見つかりません: {sp_info['errors']}"
            )
        sid = sp_info["style_id"]

    spd = speed or config.VOICEVOX_SPEED

    r = requests.post(
        f"{host}/audio_query",
        params={"text": text, "speaker": sid},
        timeout=30,
    )
    r.raise_for_status()
    query = r.json()
    query["speedScale"] = spd

    r2 = requests.post(
        f"{host}/synthesis",
        params={"speaker": sid},
        json=query,
        timeout=120,
    )
    r2.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(r2.content)

    return output_path


def synthesize_espeak(text: str, output_path: Path, speed: float | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path = output_path.with_suffix(".wav")

    wpm = int(130 * (speed or 0.88))
    subprocess.run(
        ["espeak-ng", "-v", "ja", "-s", str(wpm),
         "-w", str(wav_path), text],
        capture_output=True, check=True,
    )

    if output_path.suffix != ".wav" or output_path != wav_path:
        final = output_path.with_suffix(".wav")
        if wav_path != final:
            wav_path.rename(final)
        return final
    return wav_path


def synthesize(
    text: str, output_path: Path, speed: float | None = None,
    test_mode: bool = False, speaker_id: int | None = None,
) -> dict:
    """音声合成。戻り値は使用エンジン情報を含むdict。"""
    info = {
        "engine": None,
        "speaker_id": None,
        "speaker_name": None,
        "style_name": None,
        "speed": speed or config.VOICEVOX_SPEED,
        "output_path": str(output_path),
    }

    if _voicevox_available():
        sp_info = resolve_speaker_id()
        if sp_info["found"]:
            sid = speaker_id or sp_info["style_id"]
            info["engine"] = "VOICEVOX"
            info["speaker_id"] = sid
            info["speaker_name"] = config.VOICEVOX_SPEAKER_NAME
            info["style_name"] = sp_info["style_name"]
            info["voicevox_version"] = sp_info.get("voicevox_version")
            print(f"[TTS] VOICEVOX使用（{config.VOICEVOX_SPEAKER_NAME}）")
            synthesize_voicevox(text, output_path, speed, speaker_id=sid)
            return info
        elif not test_mode:
            raise SpeakerNotFoundError(
                f"本番モード: {sp_info['errors']}"
            )

    if not test_mode:
        raise VOICEVOXNotAvailableError(
            "本番モード: VOICEVOXが利用できません。\n"
            f"  接続先: {config.VOICEVOX_HOST}\n"
            "  本番モードではVOICEVOX（青山龍星）が必須です。\n"
            "  テストモードで実行するには --test-mode を指定してください。"
        )

    print("[TTS] [TEST ONLY] espeak-ngフォールバック（テストモード・投稿不可）")
    synthesize_espeak(text, output_path, speed)
    info["engine"] = "espeak-ng"
    info["speaker_name"] = "espeak-ng-ja"
    return info


def synthesize_sections(
    sections: list[dict],
    output_dir: Path,
    speed: float | None = None,
    test_mode: bool = False,
    speaker_id: int | None = None,
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for i, sec in enumerate(sections):
        text = sec.get("text", "")
        if not text.strip():
            continue

        filename = f"section_{i:03d}.wav"
        out_path = output_dir / filename

        print(f"[TTS] セクション {i}: {text[:30]}...")
        tts_info = synthesize(
            text, out_path, speed,
            test_mode=test_mode, speaker_id=speaker_id,
        )

        duration = get_audio_duration(out_path)
        results.append({
            "index": i,
            "type": sec.get("type", "body"),
            "text": text,
            "audio_path": str(out_path),
            "duration": duration,
            "tts_engine": tts_info["engine"],
            "tts_speaker_id": tts_info.get("speaker_id"),
            "tts_speaker_name": tts_info.get("speaker_name"),
            "tts_style_name": tts_info.get("style_name"),
            "tts_speed": tts_info.get("speed"),
        })
        print(f"[TTS]   → {duration:.1f}秒 ({tts_info['engine']})")

    return results


def get_audio_duration(path: Path) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _get_audio_info(path: Path) -> dict:
    import json as _json
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", str(path)],
            capture_output=True, text=True, check=True,
        )
        data = _json.loads(r.stdout)
        stream = next((s for s in data.get("streams", []) if s["codec_type"] == "audio"), {})
        fmt = data.get("format", {})
        return {
            "sample_rate": int(stream.get("sample_rate", 0)),
            "channels": int(stream.get("channels", 0)),
            "duration": float(fmt.get("duration", 0)),
        }
    except Exception:
        return {}
