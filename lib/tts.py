import json
import os
import struct
import subprocess
import math
import wave
import urllib.request
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_settings():
    path = os.path.join(BASE_DIR, "config", "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_speaker_id(host, speaker_name):
    req = urllib.request.Request(f"{host}/speakers", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        speakers = json.loads(resp.read().decode("utf-8"))
    for sp in speakers:
        if sp["name"] == speaker_name:
            if sp["styles"]:
                first = sp["styles"][0]
                return first["id"], sp["name"], first["name"]
            return None, speaker_name, None
    return None, speaker_name, None


def synthesize_voicevox(text, output_path, speaker_id, speed_scale=0.95, host="http://localhost:50021"):
    params = urllib.parse.urlencode({"text": text, "speaker": speaker_id})
    req = urllib.request.Request(
        f"{host}/audio_query?{params}",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        query = json.loads(resp.read().decode("utf-8"))

    query["speedScale"] = speed_scale

    synth_params = urllib.parse.urlencode({"speaker": speaker_id})
    body = json.dumps(query).encode("utf-8")
    req2 = urllib.request.Request(
        f"{host}/synthesis?{synth_params}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req2, timeout=60) as resp:
        wav_data = resp.read()

    with open(output_path, "wb") as f:
        f.write(wav_data)

    if os.path.getsize(output_path) == 0:
        raise RuntimeError(f"VOICEVOX出力が0KBです: {output_path}")
    return output_path


def generate_test_tone(text, output_path, sample_rate=24000):
    duration = max(2.0, len(text) * 0.15)
    n_samples = int(sample_rate * duration)
    freq = 440.0
    amplitude = 8000

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        envelope = min(1.0, min(t / 0.01, (duration - t) / 0.01))
        value = int(amplitude * envelope * math.sin(2 * math.pi * freq * t))
        value = max(-32768, min(32767, value))
        samples.append(value)

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return output_path


def generate_narration(narration_text, output_dir, mode="production"):
    settings = load_settings()
    os.makedirs(output_dir, exist_ok=True)

    sentences = [s.strip() for s in narration_text.split("\n") if s.strip()]
    wav_files = []
    tts_info = {"engine": None, "speaker": None, "style": None, "style_id": None, "speed": None}

    if mode == "production":
        if settings["voicevox"].get("fallback_allowed", False):
            raise RuntimeError(
                "fallback_allowedがtrueに設定されています。本番モードではfalseにしてください。"
            )

        host = settings["voicevox"]["host"]
        speaker_name = settings["voicevox"]["speaker_name"]
        speed = settings["voicevox"]["speed_scale"]

        sid, resolved_name, resolved_style = resolve_speaker_id(host, speaker_name)
        if sid is None:
            raise RuntimeError(
                f"VOICEVOX話者「{speaker_name}」が /speakers から見つかりません。"
                "VOICEVOXを起動し、config/settings.jsonの話者名を確認してください。"
                "別話者へのフォールバックは禁止されています。"
            )

        tts_info = {
            "engine": "VOICEVOX",
            "speaker": resolved_name,
            "style": resolved_style,
            "style_id": sid,
            "speed": speed,
            "fallback_used": False,
        }

        for i, sentence in enumerate(sentences):
            wav_path = os.path.join(output_dir, f"narration_{i:03d}.wav")
            synthesize_voicevox(sentence, wav_path, sid, speed, host)
            wav_files.append(wav_path)
    else:
        tts_info = {
            "engine": "test_tone",
            "speaker": None,
            "style": None,
            "style_id": None,
            "speed": None,
            "fallback_used": False,
        }
        for i, sentence in enumerate(sentences):
            wav_path = os.path.join(output_dir, f"narration_{i:03d}.wav")
            generate_test_tone(sentence, wav_path)
            wav_files.append(wav_path)

    combined_path = os.path.join(output_dir, "narration_combined.wav")
    concatenate_wav(wav_files, combined_path)

    duration = get_wav_duration(combined_path)
    return combined_path, duration, tts_info


def concatenate_wav(wav_files, output_path):
    if not wav_files:
        raise RuntimeError("結合するWAVファイルがありません。")

    with wave.open(wav_files[0], "r") as first:
        params = first.getparams()

    all_frames = bytearray()
    pause_samples = int(params.framerate * 0.3)
    pause_bytes = b"\x00\x00" * pause_samples * params.nchannels

    for i, wf_path in enumerate(wav_files):
        with wave.open(wf_path, "r") as wf:
            all_frames.extend(wf.readframes(wf.getnframes()))
        if i < len(wav_files) - 1:
            all_frames.extend(pause_bytes)

    with wave.open(output_path, "w") as out:
        out.setparams(params)
        out.writeframes(bytes(all_frames))


def get_wav_duration(wav_path):
    with wave.open(wav_path, "r") as wf:
        return wf.getnframes() / wf.getframerate()
