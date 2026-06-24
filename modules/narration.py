"""
ナレーション音声生成モジュール

本番モード（REQUIRE_VOICEVOX=True）:
  VOICEVOXのみ使用。接続できない場合はエラー停止。

開発モード（REQUIRE_VOICEVOX=False）:
  VOICEVOX未起動時はespeak-ngへフォールバック（本番品質ではない）。
"""

import os
import json
import time
import requests
from pathlib import Path


class VoicevoxUnavailableError(RuntimeError):
    """VOICEVOXに接続できない場合のエラー（代替音声切替禁止）"""
    pass


def generate_narration(text: str, output_path: str) -> str:
    from .config import REQUIRE_VOICEVOX

    if _voicevox_available():
        print("  [TTS] VOICEVOX（青山龍星）を使用中...")
        return _voicevox_tts(text, output_path)

    if REQUIRE_VOICEVOX:
        raise VoicevoxUnavailableError(
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "エラー: VOICEVOXに接続できません（http://localhost:50021）\n\n"
            "解決方法:\n"
            "  1. VOICEVOXアプリを起動してください\n"
            "  2. 起動後、再度コマンドを実行してください\n\n"
            "開発用の代替音声（低品質）を使用する場合:\n"
            "  modules/config.py の REQUIRE_VOICEVOX = False に変更してください\n"
            "  ※代替音声で生成した動画は完成版と誤認するため、本番投稿には使用しないでください\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    print("  [TTS] VOICEVOX 未起動 → espeak-ng（開発用）を使用中...")
    print("  ※ REQUIRE_VOICEVOX=False モードです。本番品質ではありません。")
    return _espeak_tts(text, output_path)


def _voicevox_available() -> bool:
    try:
        r = requests.get("http://localhost:50021/speakers", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _voicevox_tts(text: str, output_path: str) -> str:
    from .config import (
        VOICEVOX_URL, VOICEVOX_SPEAKER,
        VOICEVOX_SPEED_SCALE, VOICEVOX_PITCH_SCALE,
        VOICEVOX_INTONATION_SCALE, VOICEVOX_VOLUME_SCALE,
        VOICEVOX_PRE_PHONEME_LENGTH, VOICEVOX_POST_PHONEME_LENGTH,
        VOICEVOX_PAUSE_LENGTH_SCALE,
    )

    r = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": VOICEVOX_SPEAKER},
        timeout=30,
    )
    r.raise_for_status()
    query = r.json()

    query["speedScale"] = VOICEVOX_SPEED_SCALE
    query["pitchScale"] = VOICEVOX_PITCH_SCALE
    query["intonationScale"] = VOICEVOX_INTONATION_SCALE
    query["volumeScale"] = VOICEVOX_VOLUME_SCALE
    query["prePhonemeLength"] = VOICEVOX_PRE_PHONEME_LENGTH
    query["postPhonemeLength"] = VOICEVOX_POST_PHONEME_LENGTH
    query["pauseLengthScale"] = VOICEVOX_PAUSE_LENGTH_SCALE

    r2 = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": VOICEVOX_SPEAKER},
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    r2.raise_for_status()

    output_path = str(output_path)
    if not output_path.endswith(".wav"):
        output_path = output_path.replace(".mp3", ".wav")

    with open(output_path, "wb") as f:
        f.write(r2.content)

    return output_path


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
    """各章のナレーション音声を生成して辞書で返す。VOICEVOX必須モードでは失敗時に停止。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = {}

    chapter_keys = list(script["chapters"].keys())
    for chapter_name, chapter_data in script["chapters"].items():
        idx = chapter_keys.index(chapter_name) + 1
        print(f"  [ナレーション生成] 第{idx}章：{chapter_name}")
        text = chapter_data["narration"]
        out_path = output_dir / f"narration_{chapter_name}.wav"

        try:
            result = generate_narration(text, str(out_path))
            audio_files[chapter_name] = result
            time.sleep(0.3)
        except VoicevoxUnavailableError:
            raise  # VOICEVOX接続エラーは上位に伝播させる
        except Exception as e:
            print(f"    警告: {chapter_name} のナレーション生成に失敗: {e}")
            audio_files[chapter_name] = None

    return audio_files
