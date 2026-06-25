"""BGM管理モジュール"""
import os
import math
import struct
import logging
from pydub import AudioSegment
from src.config import BGM_DIR, BGM_VOLUME, AUDIO_SAMPLE_RATE

logger = logging.getLogger(__name__)


def _generate_sine_wave(freq, duration_ms, sample_rate=44100, amplitude=0.15):
    """正弦波を生成（バイト列として返す）"""
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        value = amplitude * math.sin(2 * math.pi * freq * t)
        fade_in = min(1.0, i / (sample_rate * 0.5)) if i < sample_rate * 0.5 else 1.0
        fade_out = min(1.0, (num_samples - i) / (sample_rate * 0.5)) if (num_samples - i) < sample_rate * 0.5 else 1.0
        value *= fade_in * fade_out
        sample_int = int(value * 32767)
        samples.append(struct.pack("<h", max(-32768, min(32767, sample_int))))
    return b"".join(samples)


def generate_ambient_bgm(duration_ms, output_path):
    """穏やかなアンビエントBGMを生成"""
    sample_rate = AUDIO_SAMPLE_RATE
    chord_notes = [
        (261.63, 0.06),   # C4
        (329.63, 0.04),   # E4
        (392.00, 0.03),   # G4
        (523.25, 0.02),   # C5
    ]

    segment_duration = 8000
    num_segments = max(1, duration_ms // segment_duration + 1)

    combined_raw = b""
    for seg_i in range(num_segments):
        seg_dur = min(segment_duration, duration_ms - seg_i * segment_duration)
        if seg_dur <= 0:
            break
        num_samples = int(sample_rate * seg_dur / 1000)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            value = 0.0
            for freq, amp in chord_notes:
                lfo = 1.0 + 0.002 * math.sin(2 * math.pi * 0.1 * t)
                value += amp * math.sin(2 * math.pi * freq * lfo * t)
            fade_in = min(1.0, i / (sample_rate * 1.0))
            fade_out = min(1.0, (num_samples - i) / (sample_rate * 1.0))
            value *= fade_in * fade_out
            sample_int = int(value * 32767)
            samples.append(struct.pack("<h", max(-32768, min(32767, sample_int))))
        combined_raw += b"".join(samples)

    bgm = AudioSegment(
        data=combined_raw,
        sample_width=2,
        frame_rate=sample_rate,
        channels=1,
    )
    bgm = bgm.set_channels(2)
    bgm = bgm[:duration_ms]
    bgm = bgm - (20 * math.log10(1 / BGM_VOLUME) if BGM_VOLUME > 0 else 60)

    bgm.export(output_path, format="wav")
    logger.info(f"アンビエントBGM生成完了: {output_path} ({duration_ms}ms)")
    return output_path


def get_or_create_bgm(duration_ms, output_dir):
    """BGMを取得または生成"""
    existing_bgm = None
    for fname in os.listdir(BGM_DIR) if os.path.exists(BGM_DIR) else []:
        if fname.endswith((".wav", ".mp3")):
            existing_bgm = os.path.join(BGM_DIR, fname)
            break

    bgm_path = os.path.join(output_dir, "bgm.wav")

    if existing_bgm:
        logger.info(f"既存BGM使用: {existing_bgm}")
        bgm = AudioSegment.from_file(existing_bgm)
        bgm = bgm.set_frame_rate(AUDIO_SAMPLE_RATE).set_channels(2)
        while len(bgm) < duration_ms:
            bgm += bgm
        bgm = bgm[:duration_ms]
        bgm = bgm - (20 * math.log10(1 / BGM_VOLUME) if BGM_VOLUME > 0 else 60)
        bgm.export(bgm_path, format="wav")
        return bgm_path

    generate_ambient_bgm(duration_ms, bgm_path)
    return bgm_path


def mix_audio(voice_path, bgm_path, output_path):
    """ナレーション音声とBGMをミックス"""
    voice = AudioSegment.from_wav(voice_path)
    bgm = AudioSegment.from_wav(bgm_path)

    while len(bgm) < len(voice):
        bgm += bgm
    bgm = bgm[:len(voice)]

    mixed = voice.overlay(bgm)
    mixed.export(output_path, format="wav")
    logger.info(f"音声ミックス完了: {output_path}")
    return output_path
