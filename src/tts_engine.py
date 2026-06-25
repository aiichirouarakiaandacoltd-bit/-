"""音声生成モジュール（VOICEVOX → espeak-ng フォールバック）"""
import os
import subprocess
import json
import logging
from pydub import AudioSegment
from src.config import VOICEVOX_URL, VOICEVOX_SPEAKER, TTS_ENGINE, AUDIO_SAMPLE_RATE

logger = logging.getLogger(__name__)


def _try_voicevox(text, output_path, speaker=VOICEVOX_SPEAKER):
    try:
        import urllib.request
        query_url = f"{VOICEVOX_URL}/audio_query?text={text}&speaker={speaker}"
        req = urllib.request.Request(query_url, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            query_data = resp.read()

        synth_url = f"{VOICEVOX_URL}/synthesis?speaker={speaker}"
        req2 = urllib.request.Request(synth_url, data=query_data, method="POST")
        req2.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req2, timeout=30) as resp2:
            wav_data = resp2.read()

        with open(output_path, "wb") as f:
            f.write(wav_data)
        return True
    except Exception as e:
        logger.debug(f"VOICEVOX unavailable: {e}")
        return False


def _use_espeak(text, output_path):
    """espeak-ngによるオフライン日本語音声生成"""
    cmd = [
        "espeak-ng",
        "-v", "ja",
        "-s", "130",
        "-p", "40",
        "-w", output_path,
        text,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"espeak-ng error: {result.stderr}")
        silence = AudioSegment.silent(duration=2000, frame_rate=AUDIO_SAMPLE_RATE)
        silence.export(output_path, format="wav")
        return

    audio = AudioSegment.from_wav(output_path)
    audio = audio.set_frame_rate(AUDIO_SAMPLE_RATE).set_channels(2)
    audio.export(output_path, format="wav")


def generate_voice(narration_lines, output_path):
    lines = [line.strip() for line in narration_lines if line.strip()]
    full_text = "。".join(lines).replace("。。", "。")

    if TTS_ENGINE == "voicevox" or TTS_ENGINE == "auto":
        if _try_voicevox(full_text, output_path):
            logger.info(f"VOICEVOX音声生成完了: {output_path}")
            return output_path

    _use_espeak(full_text, output_path)
    logger.info(f"espeak-ng音声生成完了: {output_path}")
    return output_path


def generate_voice_by_segments(narration_lines, output_path):
    """セグメント別に生成し結合（字幕同期用）"""
    lines = [line.strip() for line in narration_lines if line.strip()]
    segments = []
    combined = AudioSegment.empty()

    for i, line in enumerate(lines):
        seg_path = output_path.replace(".wav", f"_seg{i:03d}.wav")
        try:
            if TTS_ENGINE == "voicevox" or TTS_ENGINE == "auto":
                if _try_voicevox(line, seg_path):
                    seg = AudioSegment.from_wav(seg_path)
                    seg = seg.set_frame_rate(AUDIO_SAMPLE_RATE).set_channels(2)
                    segments.append({"line": line, "start_ms": len(combined), "duration_ms": len(seg)})
                    combined += seg
                    combined += AudioSegment.silent(duration=400, frame_rate=AUDIO_SAMPLE_RATE)
                    os.remove(seg_path)
                    continue

            _use_espeak(line, seg_path)
            seg = AudioSegment.from_wav(seg_path)
            segments.append({"line": line, "start_ms": len(combined), "duration_ms": len(seg)})
            combined += seg
            combined += AudioSegment.silent(duration=400, frame_rate=AUDIO_SAMPLE_RATE)
            os.remove(seg_path)
        except Exception as e:
            logger.error(f"セグメント{i}音声生成エラー: {e}")
            silence = AudioSegment.silent(duration=2000, frame_rate=AUDIO_SAMPLE_RATE)
            segments.append({"line": line, "start_ms": len(combined), "duration_ms": 2000, "error": str(e)})
            combined += silence

    combined = combined.set_frame_rate(AUDIO_SAMPLE_RATE).set_channels(2)
    combined.export(output_path, format="wav")

    seg_info_path = output_path.replace(".wav", "_segments.json")
    with open(seg_info_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    logger.info(f"セグメント別音声生成完了: {output_path} ({len(segments)}セグメント)")
    return output_path, segments
