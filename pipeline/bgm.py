"""ステージ6: BGM。

audio/bgm/ に利用許可済みの音源(.mp3/.wav/.m4a)と同名 .json(権利情報, usage_ok:true)があればそれを使う。
無ければ、著作権上の問題がないオリジナルBGM(和風ペンタトニックの柔らかいパッド+琴風の撥弦)を数値合成する。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .common import ROOT, Job, get_logger, load_json, settings
from .tts import write_wav

SR = 48000


def _pluck(freq: float, dur: float, rng) -> np.ndarray:
    """Karplus-Strong による琴風の音。"""
    n = int(SR * dur)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n, np.float32)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out * np.exp(-np.linspace(0, 3.5, n))


def synth_bgm(duration: float, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(SR * (duration + 1))
    t = np.arange(n) / SR
    # D 都節/陽音階系のペンタトニック(D E G A B)
    base = 146.83
    scale = [1, 9 / 8, 4 / 3, 3 / 2, 5 / 3, 2, 9 / 4, 8 / 3, 3]
    chords = [[0, 3, 5], [2, 4, 7], [1, 3, 6], [0, 2, 5]]
    pad = np.zeros(n, np.float32)
    bar = 4.0
    for b in range(int(duration / bar) + 2):
        ch = chords[b % len(chords)]
        s0 = int(b * bar * SR)
        if s0 >= n:
            break
        seg = np.arange(int(bar * 1.5 * SR))
        env = np.minimum(1, seg / (SR * 1.2)) * np.exp(-seg / (SR * 4.5))
        for k in ch:
            f = base * scale[k] / 2
            tone = (np.sin(2 * np.pi * f * seg / SR) + 0.3 * np.sin(2 * np.pi * 2 * f * seg / SR + 0.3)) * env
            e = min(n, s0 + len(seg))
            pad[s0:e] += 0.12 * tone[: e - s0]
    # 撥弦のフレーズ(まばら)
    pl = np.zeros(n, np.float32)
    step = 0.5
    for i in range(int(duration / step)):
        if rng.random() < 0.38:
            k = int(rng.integers(3, len(scale)))
            note = _pluck(base * scale[k], 2.2, rng)
            s0 = int(i * step * SR)
            if s0 >= n:
                break
            e = min(n, s0 + len(note))
            pl[s0:e] += 0.22 * note[: e - s0]
    x = pad + pl
    # 簡易リバーブ
    for d, g in ((0.113, 0.3), (0.171, 0.22), (0.257, 0.15)):
        k = int(d * SR)
        x[k:] += g * x[:-k]
    x = x[: int(SR * duration)]
    return (x / (np.abs(x).max() + 1e-9) * 0.7).astype(np.float32)


def prepare(job: Job, duration: float, enabled: bool | None = None) -> Path | None:
    log = get_logger(job)
    cfg = settings()["bgm"]
    if enabled is False or (enabled is None and not cfg["enabled"]):
        log.info("BGM: なし")
        return None
    for f in sorted((ROOT / cfg["dir"]).glob("*")):
        if f.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac") and not f.name.startswith("generated_"):
            meta = load_json(f.with_suffix(".json"), None)
            if meta and meta.get("usage_ok"):
                log.info(f"BGM: ライブラリ音源 {f.name} ({meta.get('license', '')})")
                job.mark("bgm", True, source=str(f.relative_to(ROOT)), license=meta.get("license"))
                return f
    out = job.audio / "bgm.wav"
    write_wav(out, synth_bgm(duration))
    log.info(f"BGM: オリジナル合成音源 → {out}")
    job.mark("bgm", True, source="generated (original)")
    return out
