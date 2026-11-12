"""工程③④ 音声作成・ナレーション
台本の各カットを1文ずつAI音声にし、1本のナレーション音声と
タイムライン（各カットの開始・長さ）を書き出す。

engine = "voicevox"   : VOICEVOX Core（話者・読み上げ速度は script.json で固定）
engine = "pyopenjtalk": 予備（VOICEVOXが使えない環境用。目標尺に合わせて速さを自動調整）
"""
import glob
import json
import os
import subprocess

import numpy as np
from scipy.io import wavfile

from common import BUILD, ROOT, load_script, reading

SR = 48000


def trim(x, sr):
    a = np.abs(x)
    idx = np.where(a > a.max() * 0.02)[0]
    return x[max(idx[0] - int(0.02 * sr), 0): idx[-1] + int(0.06 * sr)]


def to_sr(x, sr):
    if sr == SR:
        return x
    from scipy.signal import resample_poly
    g = np.gcd(sr, SR)
    return resample_poly(x, SR // g, sr // g)


def atempo(w, factor):
    """声の高さを変えずに速さだけ変える（ffmpeg atempo）。"""
    src, dst = BUILD / "tmp_in.wav", BUILD / "tmp_out.wav"
    wavfile.write(src, SR, w.astype(np.float32))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f"atempo={factor:.5f}",
                    "-ar", str(SR), str(dst)], check=True)
    return wavfile.read(dst)[1].astype(np.float32)


def voicevox(cuts, cfg):
    import pyopenjtalk  # 辞書の場所を借りる
    dic = glob.glob(os.path.join(os.path.dirname(pyopenjtalk.__file__), "open_jtalk_dic*"))[0]
    vdir = BUILD / "voice_raw"
    vdir.mkdir(parents=True, exist_ok=True)
    job = {"dict_dir": dic, "speaker": cfg["speaker"], "speed_scale": cfg["speed_scale"],
           "items": [{"text": reading(c), "out": str(vdir / f"cut_{c['id']:02d}.wav")} for c in cuts]}
    jp = BUILD / "voicevox_jobs.json"
    jp.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ, LD_LIBRARY_PATH=os.path.expanduser(cfg["onnxruntime_lib"]))
    subprocess.run([os.path.expanduser(cfg["python"]), str(ROOT / "pipeline" / "voicevox_synth.py"), str(jp)],
                   check=True, env=env)
    waves = []
    for it in job["items"]:
        sr, x = wavfile.read(it["out"])
        x = x.astype(np.float32) / 32768.0
        waves.append(to_sr(trim(x, sr), sr).astype(np.float32))
    return waves


def openjtalk(cuts, cfg, gap, target):
    import pyopenjtalk
    speed = cfg.get("speed", 1.0)
    for _ in range(3):
        waves = []
        for c in cuts:
            x, sr = pyopenjtalk.tts(reading(c), speed=speed)
            waves.append(trim(x / 32768.0, sr).astype(np.float32))
        speech = sum(len(w) for w in waves) / SR
        if abs(speech + gap * len(cuts) - target) < 0.3:
            break
        speed *= speech / (target - gap * len(cuts))
    return waves


def place(cuts, waves, min_gap):
    """各文を「カット開始」か「前の文の終了＋間」の遅いほうから始める。"""
    starts, prev_end = [], -1.0
    for c, w in zip(cuts, waves):
        s = max(c["src"][0], prev_end + min_gap) if prev_end >= 0 else c["src"][0]
        starts.append(s)
        prev_end = s + len(w) / SR
    return starts, prev_end


def flow(cuts, cfg):
    total = cuts[-1]["src"][1]
    gap = cfg.get("min_gap_sec", 0.08)
    for sp in cfg["speed_candidates"]:
        waves = voicevox(cuts, dict(cfg, speed_scale=sp))
        starts, end = place(cuts, waves, gap)
        delay = max(s - c["src"][0] for s, c in zip(starts, cuts))
        print(f"speed={sp:.2f} narration_end={end:.2f}s / {total:.2f}s  max_delay={delay:.2f}s")
        if end <= total - 0.05:
            break
    n = int(round(total * SR))
    track = np.zeros(n, np.float32)
    timeline = []
    (BUILD / "voice").mkdir(parents=True, exist_ok=True)
    for c, w, s in zip(cuts, waves, starts):
        i = int(round(s * SR))
        w = w[: max(0, n - i)]
        track[i:i + len(w)] += w
        wavfile.write(BUILD / "voice" / f"cut_{c['id']:02d}.wav", SR, w)
        timeline.append({"id": c["id"], "start": round(c["src"][0], 3), "dur": round(c["src"][1] - c["src"][0], 3),
                         "speech_start": round(s, 3), "speech": round(len(w) / SR, 3)})
    track = track / max(np.abs(track).max(), 1e-9) * 0.9
    wavfile.write(BUILD / "narration_raw.wav", SR, track)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(BUILD / "narration_raw.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", str(SR), "-ac", "1",
                    str(BUILD / "narration.wav")], check=True)
    (BUILD / "timeline.json").write_text(json.dumps({"engine": "voicevox", "timing": "flow", "speed_scale": sp,
                                                     "total": total, "cuts": timeline},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"speed_scale={sp} total={total:.2f}s -> build/timeline.json, build/narration.wav")


def main():
    sc = load_script()
    cfg = sc["meta"]["tts"]
    cuts = sc["cuts"]
    gap = cfg["gap_sec"]
    if cfg["engine"] == "voicevox" and cfg.get("timing") == "flow":
        return flow(cuts, cfg)
    if cfg["engine"] == "voicevox":
        waves = voicevox(cuts, cfg)
    else:
        waves = openjtalk(cuts, cfg, gap, cfg["target_total_sec"])

    (BUILD / "voice").mkdir(parents=True, exist_ok=True)
    timeline, track, t = [], [], 0.0
    match = cfg.get("timing") == "match_source"
    for c, w in zip(cuts, waves):
        tempo = 1.0
        if match:
            slot = c["src"][1] - c["src"][0]
            room = slot - cfg.get("min_gap_sec", 0.08)
            if len(w) / SR > room:
                tempo = (len(w) / SR) / room
                w = atempo(w, tempo)
            seg = int(round(slot * SR))
            w = w[:seg]
        else:
            seg = len(w) + int(gap * SR)
        buf = np.zeros(seg, np.float32)
        buf[: len(w)] = w
        track.append(buf)
        wavfile.write(BUILD / "voice" / f"cut_{c['id']:02d}.wav", SR, w)
        timeline.append({"id": c["id"], "start": round(t, 3), "speech": round(len(w) / SR, 3), "dur": round(seg / SR, 3), "tempo": round(tempo, 3)})
        t += seg / SR

    raw = np.concatenate(track)
    raw = raw / max(np.abs(raw).max(), 1e-9) * 0.9
    wavfile.write(BUILD / "narration_raw.wav", SR, raw.astype(np.float32))
    # 音量をそろえる（ナレーション −14 LUFS 目安）
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(BUILD / "narration_raw.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", str(SR), "-ac", "1",
                    str(BUILD / "narration.wav")], check=True)
    (BUILD / "timeline.json").write_text(json.dumps({"engine": cfg["engine"], "total": t, "cuts": timeline},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"engine={cfg['engine']} total={t:.2f}s -> build/timeline.json, build/narration.wav")


if __name__ == "__main__":
    main()
