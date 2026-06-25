"""
ナレーション音声生成モジュール

本番モード（REQUIRE_VOICEVOX=True、test_mode=False）:
  VOICEVOXのみ使用。接続できない場合はエラー停止。
  代替音声（espeak-ng、サイン波等）への無断切替禁止。

技術検証モード（test_mode=True）:
  VOICEVOX未起動時はサイン波WAVを生成。
  サイン波使用時は必ず「TEST ONLY」を明記すること。
  投稿不可。
"""

import os
import json
import time
import wave
import struct
import math
import requests
from pathlib import Path


class VoicevoxUnavailableError(RuntimeError):
    """VOICEVOXに接続できない場合のエラー（代替音声切替禁止）"""
    pass


# ──────────────────────────────────────────────────────────
# 音声デュレーション取得
# ──────────────────────────────────────────────────────────

def get_wav_duration(path: str) -> float:
    """WAVファイルの実再生時間（秒）を返す。読み取り失敗時は 0.0。"""
    try:
        with wave.open(str(path), "r") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


# ──────────────────────────────────────────────────────────
# メイン生成関数
# ──────────────────────────────────────────────────────────

def generate_narration(
    text: str,
    output_path: str,
    test_mode: bool = False,
    speaker: int = None,
    speed_scale: float = None,
) -> str:
    """
    テキストからナレーション WAV を生成する。

    Parameters
    ----------
    text        : ナレーションテキスト
    output_path : 出力 WAV ファイルパス
    test_mode   : True の場合、VOICEVOX 未接続時にサイン波を生成（投稿不可）
    speaker     : VOICEVOX 話者 ID（None → config.VOICEVOX_SPEAKER）
    speed_scale : 話速（None → config.VOICEVOX_SPEED_SCALE）
    """
    from .config import REQUIRE_VOICEVOX

    if _voicevox_available():
        print("  [TTS] VOICEVOX（青山龍星）を使用中...")
        return _voicevox_tts(text, output_path, speaker=speaker, speed_scale=speed_scale)

    if test_mode:
        print("  [TEST ONLY] VOICEVOX 未接続 → サイン波を生成（投稿不可）")
        return _generate_test_audio(text, output_path)

    if REQUIRE_VOICEVOX:
        raise VoicevoxUnavailableError(
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "エラー: VOICEVOXに接続できません（http://localhost:50021）\n\n"
            "解決方法:\n"
            "  1. VOICEVOXアプリを起動してください\n"
            "  2. 起動後、再度コマンドを実行してください\n\n"
            "注意:\n"
            "  代替音声（espeak-ng・サイン波等）への自動切替は行いません。\n"
            "  技術検証のみが目的の場合は --test-mode を指定してください。\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    # REQUIRE_VOICEVOX=False の開発モード（明示的に設定した場合のみ）
    print("  [TTS] VOICEVOX 未起動 → espeak-ng（開発用）を使用中...")
    print("  ※ REQUIRE_VOICEVOX=False モードです。本番品質ではありません。")
    return _espeak_tts(text, output_path)


def _voicevox_available() -> bool:
    try:
        r = requests.get("http://localhost:50021/speakers", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _voicevox_tts(
    text: str,
    output_path: str,
    speaker: int = None,
    speed_scale: float = None,
) -> str:
    from .config import (
        VOICEVOX_URL, VOICEVOX_SPEAKER,
        VOICEVOX_SPEED_SCALE, VOICEVOX_PITCH_SCALE,
        VOICEVOX_INTONATION_SCALE, VOICEVOX_VOLUME_SCALE,
        VOICEVOX_PRE_PHONEME_LENGTH, VOICEVOX_POST_PHONEME_LENGTH,
        VOICEVOX_PAUSE_LENGTH_SCALE,
    )

    spk  = speaker     if speaker     is not None else VOICEVOX_SPEAKER
    spd  = speed_scale if speed_scale is not None else VOICEVOX_SPEED_SCALE

    r = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": spk},
        timeout=30,
    )
    r.raise_for_status()
    query = r.json()

    query["speedScale"]          = spd
    query["pitchScale"]          = VOICEVOX_PITCH_SCALE
    query["intonationScale"]     = VOICEVOX_INTONATION_SCALE
    query["volumeScale"]         = VOICEVOX_VOLUME_SCALE
    query["prePhonemeLength"]    = VOICEVOX_PRE_PHONEME_LENGTH
    query["postPhonemeLength"]   = VOICEVOX_POST_PHONEME_LENGTH
    query["pauseLengthScale"]    = VOICEVOX_PAUSE_LENGTH_SCALE

    r2 = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": spk},
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    r2.raise_for_status()

    out = str(output_path)
    if not out.endswith(".wav"):
        out = out.replace(".mp3", ".wav")

    with open(out, "wb") as f:
        f.write(r2.content)

    return out


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


def _generate_test_audio(text: str, output_path: str) -> str:
    """
    技術検証専用のサイン波 WAV を生成する。
    文字数から尺を推定し、300 Hz サイン波を書き出す。
    """
    try:
        import numpy as np
        from scipy.io import wavfile

        SAMPLE_RATE = 44100
        chars = max(len(text), 1)
        duration = (chars / 240.0) * 60.0  # 240文字/分 基準
        duration = max(duration, 5.0)

        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        samples = (np.sin(2 * math.pi * 300.0 * t) * 0.3 * 32767).astype(np.int16)

        out = str(output_path)
        if not out.endswith(".wav"):
            out = out.replace(".mp3", ".wav")

        wavfile.write(out, SAMPLE_RATE, samples)
        return out

    except ImportError:
        # scipy が無い場合は wave モジュールで無音 WAV を生成
        return _generate_silent_wav(text, output_path)


def _generate_silent_wav(text: str, output_path: str) -> str:
    """scipy が利用できない場合の無音 WAV フォールバック（技術検証用）。"""
    SAMPLE_RATE = 44100
    chars = max(len(text), 1)
    duration = max((chars / 240.0) * 60.0, 5.0)
    n_frames = int(SAMPLE_RATE * duration)

    out = str(output_path)
    if not out.endswith(".wav"):
        out = out.replace(".mp3", ".wav")

    with wave.open(out, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"\x00" * n_frames * 2 * 2)

    return out


# ──────────────────────────────────────────────────────────
# 章ごと一括生成
# ──────────────────────────────────────────────────────────

def generate_chapter_narrations(
    script: dict,
    output_dir: str,
    test_mode: bool = False,
    speaker: int = None,
    speed_scale: float = None,
) -> dict:
    """
    各章のナレーション音声を生成して {chapter_name: path} の辞書を返す。

    test_mode=True のとき、VOICEVOX 未接続でもサイン波で続行する。
    本番モードでは VOICEVOX 未接続時に VoicevoxUnavailableError を上げる。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = {}

    chapter_keys = list(script["chapters"].keys())
    for chapter_name, chapter_data in script["chapters"].items():
        idx = chapter_keys.index(chapter_name) + 1
        print(f"  [ナレーション生成] 第{idx}章：{chapter_name}")
        text = chapter_data["narration"]
        out_path = str((output_dir / f"narration_{chapter_name}.wav").resolve())

        try:
            result = generate_narration(
                text, out_path,
                test_mode=test_mode,
                speaker=speaker,
                speed_scale=speed_scale,
            )
            audio_files[chapter_name] = result
            time.sleep(0.3)
        except VoicevoxUnavailableError:
            raise
        except Exception as e:
            print(f"    警告: {chapter_name} のナレーション生成に失敗: {e}")
            audio_files[chapter_name] = None

    return audio_files
