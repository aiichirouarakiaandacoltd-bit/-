"""VOICEVOX speech synthesis with dynamic speaker ID lookup."""
import json
import struct
import urllib.request
import urllib.parse
import wave
from pathlib import Path

import config as cfg


class VoicevoxError(Exception):
    pass


def get_speaker_id():
    """Dynamically look up the style ID for 青山龍星."""
    url = f"{cfg.VOICEVOX_HOST}/speakers"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            speakers = json.loads(resp.read())
    except Exception as e:
        raise VoicevoxError(f"Cannot connect to VOICEVOX at {cfg.VOICEVOX_HOST}: {e}")

    for speaker in speakers:
        if speaker["name"] == cfg.VOICEVOX_SPEAKER_NAME:
            styles = speaker.get("styles", [])
            if styles:
                return styles[0]["id"]
            raise VoicevoxError(f"{cfg.VOICEVOX_SPEAKER_NAME} found but has no styles")

    available = [s["name"] for s in speakers]
    raise VoicevoxError(
        f"{cfg.VOICEVOX_SPEAKER_NAME} not found in VOICEVOX. "
        f"Available speakers: {', '.join(available[:15])}"
    )


def synthesize_line(text, speaker_id, output_path):
    """Synthesize a single line of text to a WAV file."""
    query_url = (
        f"{cfg.VOICEVOX_HOST}/audio_query?"
        f"text={urllib.parse.quote(text)}&speaker={speaker_id}"
    )
    req = urllib.request.Request(query_url, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        query = json.loads(resp.read())

    query["speedScale"] = cfg.VOICEVOX_SPEED

    synth_url = f"{cfg.VOICEVOX_HOST}/synthesis?speaker={speaker_id}"
    data = json.dumps(query).encode("utf-8")
    req = urllib.request.Request(
        synth_url, data=data, method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        wav_data = resp.read()

    Path(output_path).write_bytes(wav_data)
    return output_path


def synthesize_script(lines, output_dir, progress_callback=None):
    """Synthesize all lines and return list of WAV paths with durations."""
    speaker_id = get_speaker_id()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, line in enumerate(lines):
        wav_path = output_dir / f"line_{i:04d}.wav"
        synthesize_line(line, speaker_id, wav_path)
        duration = get_wav_duration(wav_path)
        results.append({"index": i, "text": line, "path": str(wav_path), "duration": duration})
        if progress_callback:
            progress_callback(i + 1, len(lines))

    return results


def get_wav_duration(wav_path):
    """Get duration of a WAV file in seconds."""
    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / rate


def generate_test_audio(text, output_path, duration=None):
    """Generate a simple sine wave WAV for test mode."""
    import math
    sample_rate = 24000
    if duration is None:
        duration = max(1.0, len(text) * 0.15)
    n_samples = int(sample_rate * duration)
    freq = 440
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        envelope = min(1.0, min(t / 0.01, (duration - t) / 0.01))
        val = int(0.3 * envelope * 32767 * math.sin(2 * math.pi * freq * t))
        val = max(-32768, min(32767, val))
        samples.append(struct.pack("<h", val))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(samples))
    return output_path


def generate_test_script_audio(lines, output_dir, progress_callback=None):
    """Generate test audio for all lines."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, line in enumerate(lines):
        wav_path = output_dir / f"line_{i:04d}.wav"
        generate_test_audio(line, wav_path)
        duration = get_wav_duration(wav_path)
        results.append({"index": i, "text": line, "path": str(wav_path), "duration": duration})
        if progress_callback:
            progress_callback(i + 1, len(lines))

    return results
