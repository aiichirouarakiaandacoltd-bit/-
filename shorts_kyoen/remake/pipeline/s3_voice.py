"""工程③④ 音声作成・ナレーション
台本の各カットをAI音声（pyopenjtalk）で1文ずつ生成し、
目標の尺に収まるよう話す速さを自動調整して、1本のナレーション音声と
タイムライン（各カットの開始・長さ）を書き出す。
"""
import json
import subprocess

import numpy as np
import pyopenjtalk
from scipy.io import wavfile

from common import BUILD, load_script, reading

SR = 48000


def synth(text, speed, half_tone):
    x, sr = pyopenjtalk.tts(text, speed=speed, half_tone=half_tone)
    assert sr == SR
    # 前後の無音を詰める
    a = np.abs(x)
    idx = np.where(a > a.max() * 0.02)[0]
    x = x[max(idx[0] - int(0.02 * SR), 0): idx[-1] + int(0.06 * SR)]
    return x.astype(np.float32)


def main():
    sc = load_script()
    cfg = sc["meta"]["tts"]
    cuts = sc["cuts"]
    gap, target = cfg["gap_sec"], cfg["target_total_sec"]
    speed = cfg["speed"]

    # 話す速さを2回まで補正して、総尺を目標に合わせる
    for _ in range(3):
        waves = [synth(reading(c), speed, cfg["half_tone"]) for c in cuts]
        speech = sum(len(w) for w in waves) / SR
        total = speech + gap * len(cuts)
        print(f"speed={speed:.3f} speech={speech:.2f}s total={total:.2f}s")
        if abs(total - target) < 0.3:
            break
        speed *= speech / (target - gap * len(cuts))

    (BUILD / "voice").mkdir(parents=True, exist_ok=True)
    timeline, track, t = [], [], 0.0
    for c, w in zip(cuts, waves):
        dur = len(w) / SR
        seg = len(w) + int(gap * SR)
        buf = np.zeros(seg, np.float32)
        buf[: len(w)] = w
        track.append(buf)
        wavfile.write(BUILD / "voice" / f"cut_{c['id']:02d}.wav", SR, (w / 32768).astype(np.float32))
        timeline.append({"id": c["id"], "start": round(t, 3), "speech": round(dur, 3), "dur": round(seg / SR, 3)})
        t += seg / SR

    raw = np.concatenate(track) / 32768.0
    raw = raw / max(np.abs(raw).max(), 1e-9) * 0.9
    wavfile.write(BUILD / "narration_raw.wav", SR, raw.astype(np.float32))
    # 音量をそろえる（ナレーション −14 LUFS 目安）
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(BUILD / "narration_raw.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", str(SR), "-ac", "1",
                    str(BUILD / "narration.wav")], check=True)
    (BUILD / "timeline.json").write_text(json.dumps({"speed": speed, "total": t, "cuts": timeline},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"timeline total={t:.2f}s -> build/timeline.json, build/narration.wav")


if __name__ == "__main__":
    main()
