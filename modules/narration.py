"""
ナレーション音声生成モジュール
優先: VOICEVOX (青山龍星 / speaker 13)
代替: gTTS (Google Text-to-Speech)
"""

import os
import json
import time
import tempfile
import requests
from pathlib import Path


def generate_narration(text: str, output_path: str, use_voicevox: bool = True) -> str:
    if use_voicevox and _voicevox_available():
        print("  [TTS] VOICEVOX を使用中...")
        return _voicevox_tts(text, output_path)
    else:
        print("  [TTS] VOICEVOX 未起動 → gTTS (Google TTS) を使用中...")
        return _gtts_tts(text, output_path)


def _voicevox_available() -> bool:
    try:
        r = requests.get("http://localhost:50021/speakers", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _voicevox_tts(text: str, output_path: str, speaker_id: int = 13) -> str:
    from .config import VOICEVOX_URL, VOICEVOX_SPEAKER
    speaker_id = VOICEVOX_SPEAKER

    r = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": speaker_id},
        timeout=30,
    )
    r.raise_for_status()
    query = r.json()

    query["speedScale"] = 1.0
    query["pitchScale"] = 0.0
    query["intonationScale"] = 1.1
    query["volumeScale"] = 1.0
    query["prePhonemeLength"] = 0.1
    query["postPhonemeLength"] = 0.2

    r2 = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": speaker_id},
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r2.raise_for_status()

    output_path = str(output_path)
    if not output_path.endswith(".wav"):
        output_path = output_path.replace(".mp3", ".wav")

    with open(output_path, "wb") as f:
        f.write(r2.content)

    return output_path


def _gtts_tts(text: str, output_path: str) -> str:
    try:
        from gtts import gTTS
        from pydub import AudioSegment

        mp3_path = str(output_path).replace(".wav", ".mp3")
        tts = gTTS(text=text, lang="ja", slow=False)
        tts.save(mp3_path)

        wav_path = str(output_path)
        if not wav_path.endswith(".wav"):
            wav_path = mp3_path.replace(".mp3", ".wav")

        audio = AudioSegment.from_mp3(mp3_path)
        audio = audio.set_frame_rate(44100).set_channels(1)
        audio.export(wav_path, format="wav")

        if os.path.exists(mp3_path) and mp3_path != wav_path:
            os.remove(mp3_path)

        return wav_path
    except Exception:
        return _espeak_tts(text, output_path)


def _espeak_tts(text: str, output_path: str) -> str:
    import subprocess

    wav_path = str(output_path)
    if not wav_path.endswith(".wav"):
        wav_path = wav_path.replace(".mp3", ".wav")

    text_safe = text.replace('"', "'").replace("——", "。").replace("—", "。")

    result = subprocess.run(
        ["espeak-ng", "-v", "ja", "-s", "130", "-p", "45", "-a", "180", "-w", wav_path],
        input=text_safe,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"espeak-ng failed: {result.stderr}")

    if not os.path.exists(wav_path):
        raise RuntimeError("espeak-ng: 出力ファイルが生成されませんでした")

    return wav_path


def generate_chapter_narrations(script: dict, output_dir: str) -> dict:
    """各章のナレーション音声を生成して辞書で返す"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = {}

    for chapter_name, chapter_data in script["chapters"].items():
        print(f"  [ナレーション生成] 第{list(script['chapters'].keys()).index(chapter_name)+1}章：{chapter_name}")
        text = chapter_data["narration"]
        out_path = output_dir / f"narration_{chapter_name}.wav"

        try:
            result = generate_narration(text, str(out_path))
            audio_files[chapter_name] = result
            time.sleep(0.3)
        except Exception as e:
            print(f"    警告: {chapter_name} のナレーション生成に失敗: {e}")
            audio_files[chapter_name] = None

    return audio_files
