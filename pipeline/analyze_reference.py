"""参考動画の自動分析。

技術情報・カット割り・字幕切替タイミング・音量・無音区間(文の区切り)を測定し JSON 保存する。
目視で確認した字幕デザイン等の定性分析は templates/reference_style.json に記述し、
後続の編集処理はそちらを参照する。

使い方: python -m pipeline.analyze_reference references/reference_01.mp4
"""
from __future__ import annotations

import argparse
import re
import statistics
from pathlib import Path

import numpy as np

from .common import ROOT, ffprobe, run, save_json, now_jst


def _scene_cuts(path: Path, thr: float) -> list[float]:
    r = run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
             f"select='gt(scene,{thr})',metadata=print:file=-", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stdout)]


def _loudness(path: Path) -> dict:
    r = run(["ffmpeg", "-i", str(path), "-af", "ebur128", "-f", "null", "-"], check=False)
    txt = r.stderr[r.stderr.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[0-9.]+)", txt).group(1)) if re.search(k + r":\s+(-?[0-9.]+)", txt) else None
    return {"integrated_lufs": g("I"), "loudness_range_lu": g("LRA")}


def _silences(path: Path, db=-35, d=0.2) -> list[dict]:
    r = run(["ffmpeg", "-i", str(path), "-af", f"silencedetect=n={db}dB:d={d}", "-f", "null", "-"], check=False)
    st = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    return [{"start": round(a, 2), "end": round(b, 2), "dur": round(b - a, 2)} for a, b in zip(st, en)]


def _gap_level(path: Path, gaps: list[dict]) -> float | None:
    lv = []
    for g in gaps:
        if g["dur"] < 0.15:
            continue
        r = run(["ffmpeg", "-ss", str(g["start"] + 0.03), "-t", str(max(0.1, g["dur"] - 0.06)), "-i", str(path),
                 "-af", "astats=metadata=0", "-f", "null", "-"], check=False)
        m = re.search(r"RMS level dB: (-?[0-9.inf]+)", r.stderr)
        if m and "inf" not in m.group(1):
            lv.append(float(m.group(1)))
    return round(statistics.median(lv), 1) if lv else None


def _subtitle_changes(path: Path, w: int, h: int, band=(0.50, 0.70), fps=10, cuts=()) -> list[float]:
    """字幕帯域の画素差分ピークから字幕切替時刻を推定(カット点は除外)。"""
    y0, y1 = int(h * band[0]), int(h * band[1])
    sw, sh = 160, max(8, int(160 * (y1 - y0) / w))
    import subprocess
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        f"fps={fps},crop={w}:{y1 - y0}:0:{y0},scale={sw}:{sh},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    arr = np.frombuffer(p.stdout, dtype=np.uint8)
    n = arr.size // (sw * sh)
    fr = arr[: n * sw * sh].reshape(n, sh, sw).astype(np.float32)
    # 字幕は高コントラスト(白文字+黒縁)なのでエッジ量の変化を見る
    diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    thr = np.percentile(diff, 80)
    times = []
    for i in range(1, len(diff) - 1):
        if diff[i] > thr and diff[i] >= diff[i - 1] and diff[i] >= diff[i + 1]:
            t = (i + 1) / fps
            if all(abs(t - c) > 0.25 for c in cuts) and (not times or t - times[-1] > 0.45):
                times.append(round(t, 2))
    return times


def analyze(path: Path) -> dict:
    info = ffprobe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    num, den = map(int, v["r_frame_rate"].split("/"))
    w, h = int(v["width"]), int(v["height"])
    cuts = _scene_cuts(path, 0.2)
    bounds = [0.0] + cuts + [dur]
    shots = [{"index": i + 1, "start": round(s, 2), "end": round(e, 2), "dur": round(e - s, 2)}
             for i, (s, e) in enumerate(zip(bounds[:-1], bounds[1:]))]
    durs = [s["dur"] for s in shots]
    sil = _silences(path)
    subs = _subtitle_changes(path, w, h, cuts=cuts)
    sub_bounds = sorted(set([0.0] + subs + cuts + [dur]))
    sub_durs = [b - a2 for a2, b in zip(sub_bounds[:-1], sub_bounds[1:]) if b - a2 > 0.3]
    return {
        "file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "analyzed_at": now_jst().isoformat(timespec="seconds"),
        "technical": {
            "duration_sec": round(dur, 3),
            "width": w, "height": h,
            "aspect_ratio": f"{w}:{h} (~9:16)" if abs(w / h - 9 / 16) < 0.02 else f"{w}:{h}",
            "fps": round(num / den, 3),
            "video_codec": f"{v['codec_name']} {v.get('profile', '')}".strip(),
            "video_bitrate_kbps": round(int(v.get("bit_rate", 0)) / 1000),
            "audio_codec": f"{a['codec_name']} {a.get('profile', '')}".strip() if a else None,
            "audio_sample_rate": int(a["sample_rate"]) if a else None,
            "audio_channels": a.get("channels") if a else None,
        },
        "audio": {
            **_loudness(path),
            "pauses_over_0_2s": sil,
            "pause_count": len(sil),
            "median_level_in_pauses_db": _gap_level(path, sil),
        },
        "cuts": {
            "cut_times": [round(c, 2) for c in cuts],
            "shot_count": len(shots),
            "avg_shot_sec": round(statistics.mean(durs), 2),
            "median_shot_sec": round(statistics.median(durs), 2),
            "min_shot_sec": round(min(durs), 2),
            "max_shot_sec": round(max(durs), 2),
            "shots": shots,
        },
        "subtitles_auto": {
            "estimated_change_times": subs,
            "estimated_chunk_count": len(sub_durs),
            "avg_chunk_sec": round(statistics.mean(sub_durs), 2) if sub_durs else None,
            "method": "字幕帯域(画面高50-70%)の画素差分ピーク。目視確認値は reference_style.json 参照。",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?", default=str(ROOT / "references" / "reference_01.mp4"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    p = Path(a.video).resolve()
    res = analyze(p)
    out = Path(a.out) if a.out else ROOT / "templates" / f"reference_analysis_{p.stem}.json"
    save_json(out, res)
    t, c = res["technical"], res["cuts"]
    print(f"saved {out}")
    print(f"{t['width']}x{t['height']} {t['fps']}fps {t['duration_sec']}s / shots={c['shot_count']} avg={c['avg_shot_sec']}s "
          f"/ loud={res['audio']['integrated_lufs']}LUFS / sub_chunks~{res['subtitles_auto']['estimated_chunk_count']}")


if __name__ == "__main__":
    main()
