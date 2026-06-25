"""音声合成エンジン

VOICEVOX優先。利用不可の場合はgTTSにフォールバック。
最終運用ではVOICEVOXに統一すること。

VOICEVOX設定:
  - 話者: 青山龍星 (speaker_id=13)
  - 速度: 0.85-0.90x
  - エンドポイント: http://127.0.0.1:50021
"""

import io
import subprocess
import tempfile
import wave
from pathlib import Path

import requests

from . import config


def _voicevox_available() -> bool:
    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/speakers", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


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
        capture_output=True,
        check=True,
    )
    mp3_path.unlink(missing_ok=True)

    if output_path.suffix == ".wav":
        return wav_path

    final_path = output_path
    if final_path != wav_path:
        wav_path.rename(final_path)
    return final_path


def synthesize(text: str, output_path: Path, speed: float | None = None) -> Path:
    if _voicevox_available():
        print("[TTS] VOICEVOX使用（青山龍星）")
        return synthesize_voicevox(text, output_path, speed)

    try:
        print("[TTS] VOICEVOX未検出 → gTTSフォールバック")
        return synthesize_gtts(text, output_path)
    except Exception:
        pass

    print("[TTS] gTTS不可 → espeak-ngフォールバック")
    print("[TTS] ※最終運用ではVOICEVOXに統一してください")
    return synthesize_espeak(text, output_path, speed)


def synthesize_sections(
    sections: list[dict],
    output_dir: Path,
    speed: float | None = None,
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
        synthesize(text, out_path, speed)

        duration = get_audio_duration(out_path)
        results.append({
            "index": i,
            "type": sec.get("type", "body"),
            "text": text,
            "audio_path": str(out_path),
            "duration": duration,
        })
        print(f"[TTS]   → {duration:.1f}秒")

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
