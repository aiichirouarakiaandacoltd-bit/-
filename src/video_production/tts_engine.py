"""音声合成エンジン

本番モード: VOICEVOX（青山龍星）必須。利用不可ならエラー終了。
テストモード (--test-mode): espeak-ng/gTTSフォールバック許可。

最終運用ではVOICEVOXに統一すること。
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


def verify_voicevox() -> dict:
    """VOICEVOX接続確認。本番モードの事前チェック用。"""
    result = {
        "api_reachable": False,
        "speakers_fetched": False,
        "target_speaker_found": False,
        "target_speaker_id": config.VOICEVOX_SPEAKER_ID,
        "target_speaker_name": config.VOICEVOX_SPEAKER_NAME,
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
    except Exception as e:
        result["errors"].append(f"VOICEVOX API接続不可: {config.VOICEVOX_HOST} ({e})")
        return result

    try:
        speakers = r.json()
        result["speakers_fetched"] = True

        found = False
        for sp in speakers:
            for style in sp.get("styles", []):
                if style.get("id") == config.VOICEVOX_SPEAKER_ID:
                    found = True
                    actual_name = sp.get("name", "")
                    result["actual_speaker_name"] = actual_name
                    break
            if found:
                break

        if not found:
            result["errors"].append(
                f"青山龍星 (speaker_id={config.VOICEVOX_SPEAKER_ID}) が見つかりません。"
                f"別話者への自動変更は行いません。"
            )
            return result
        result["target_speaker_found"] = True
    except Exception as e:
        result["errors"].append(f"話者一覧解析エラー: {e}")
        return result

    import tempfile
    test_text = "テスト音声です"
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        test_path = Path(tmp.name)

    try:
        synthesize_voicevox(test_text, test_path)
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


def synthesize_voicevox(text: str, output_path: Path, speed: float | None = None) -> Path:
    host = config.VOICEVOX_HOST
    speaker = config.VOICEVOX_SPEAKER_ID
    spd = speed or config.VOICEVOX_SPEED

    r = requests.post(
        f"{host}/audio_query",
        params={"text": text, "speaker": speaker},
        timeout=30,
    )
    r.raise_for_status()
    query = r.json()
    query["speedScale"] = spd

    r2 = requests.post(
        f"{host}/synthesis",
        params={"speaker": speaker},
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


def synthesize_gtts(text: str, output_path: Path) -> Path:
    from gtts import gTTS

    output_path.parent.mkdir(parents=True, exist_ok=True)

    mp3_path = output_path.with_suffix(".mp3")
    tts = gTTS(text=text, lang="ja", slow=False)
    tts.save(str(mp3_path))

    wav_path = output_path.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "24000", "-ac", "1", str(wav_path)],
        capture_output=True, check=True,
    )
    mp3_path.unlink(missing_ok=True)

    if output_path.suffix == ".wav":
        return wav_path
    final_path = output_path
    if final_path != wav_path:
        wav_path.rename(final_path)
    return final_path


def synthesize(
    text: str, output_path: Path, speed: float | None = None,
    test_mode: bool = False,
) -> dict:
    """音声合成。戻り値は使用エンジン情報を含むdict。"""
    info = {
        "engine": None,
        "speaker_id": None,
        "speaker_name": None,
        "speed": speed or config.VOICEVOX_SPEED,
        "output_path": str(output_path),
    }

    if _voicevox_available():
        info["engine"] = "VOICEVOX"
        info["speaker_id"] = config.VOICEVOX_SPEAKER_ID
        info["speaker_name"] = config.VOICEVOX_SPEAKER_NAME
        print(f"[TTS] VOICEVOX使用（{config.VOICEVOX_SPEAKER_NAME}）")
        synthesize_voicevox(text, output_path, speed)
        return info

    if not test_mode:
        raise VOICEVOXNotAvailableError(
            "本番モード: VOICEVOXが利用できません。\n"
            f"  接続先: {config.VOICEVOX_HOST}\n"
            "  本番モードではVOICEVOX（青山龍星）が必須です。\n"
            "  テストモードで実行するには --test-mode を指定してください。"
        )

    try:
        print("[TTS] VOICEVOX未検出 → gTTSフォールバック（テストモード）")
        synthesize_gtts(text, output_path)
        info["engine"] = "gTTS"
        info["speaker_name"] = "gTTS-ja"
        return info
    except Exception:
        for ext in [".mp3"]:
            leftover = output_path.with_suffix(ext)
            leftover.unlink(missing_ok=True)

    print("[TTS] gTTS不可 → espeak-ngフォールバック（テストモード）")
    synthesize_espeak(text, output_path, speed)
    info["engine"] = "espeak-ng"
    info["speaker_name"] = "espeak-ng-ja"
    return info


def synthesize_sections(
    sections: list[dict],
    output_dir: Path,
    speed: float | None = None,
    test_mode: bool = False,
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
        tts_info = synthesize(text, out_path, speed, test_mode=test_mode)

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


def concatenate_audio(audio_files: list[Path], output_path: Path, pause_ms: int = 500) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    list_file = output_path.parent / "_concat_list.txt"
    silence_path = output_path.parent / "_silence.wav"

    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"anullsrc=r=24000:cl=mono:d={pause_ms/1000}",
         "-t", str(pause_ms / 1000), str(silence_path)],
        capture_output=True, check=True,
    )

    with open(list_file, "w") as f:
        for i, audio in enumerate(audio_files):
            f.write(f"file '{audio.resolve()}'\n")
            if i < len(audio_files) - 1:
                f.write(f"file '{silence_path.resolve()}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(output_path)],
        capture_output=True, check=True,
    )

    list_file.unlink(missing_ok=True)
    silence_path.unlink(missing_ok=True)

    return output_path
