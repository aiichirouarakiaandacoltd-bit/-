"""参考動画「0から再構築」モード(私的検証用・公開禁止)。

参考動画の映像・音声は使わずに、次をこのシステムで新たに生成して組み立てる:
  - ナレーション: VOICEVOX 青山龍星(ノーマル)。発話区間ごとに話速を合わせて新規合成
  - テロップ: 書き起こしデータ + 実測した色で描画
  - カメラワーク: 各カットの拡大率・移動量を参考動画から測定し、静止画から再現
  - カット割り: 参考動画と同じ時刻
写真素材のみ、元写真が入手できないため参考動画の各カットから字幕を除いた静止画を用いる。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import cv2
import numpy as np

from .common import ROOT, Job, ffprobe, get_logger, load_json, run, save_json
from .trace_reference import clean_frame, full_mask


def read_frame(cap, idx):
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    return f if ok else None


def estimate_motion(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """フレームaからbへの相似変換(2x3)。字幕帯は除外して特徴点で推定。"""
    h, w = a.shape[:2]
    mask = np.full((h, w), 255, np.uint8)
    mask[int(h * 0.45):int(h * 0.75)] = 0
    orb = cv2.ORB_create(2000)
    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    ka, da = orb.detectAndCompute(ga, mask)
    kb, db = orb.detectAndCompute(gb, mask)
    if da is None or db is None or len(ka) < 20 or len(kb) < 20:
        return np.array([[1, 0, 0], [0, 1, 0]], np.float64)
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(m) < 15:
        return np.array([[1, 0, 0], [0, 1, 0]], np.float64)
    pa = np.float32([ka[x.queryIdx].pt for x in m])
    pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=3)
    return M if M is not None else np.array([[1, 0, 0], [0, 1, 0]], np.float64)


def _to3(M):
    return np.vstack([M, [0, 0, 1]])


def _sane(M):
    sc = float(np.sqrt(M[0, 0] ** 2 + M[1, 0] ** 2))
    return 0.9 < sc < 1.1 and abs(M[0, 2]) < 120 and abs(M[1, 2]) < 120


def plan_shots(ref: str, cuts: list[float], fps: float, nframes: int, log, step: int = 3) -> list[dict]:
    """各カットの動きを、近いコマ同士(step コマおき)の推定を積み重ねてコマ単位で求める。
    基準(素材)= 最も引いた(拡大率が最小の)コマ。各コマ = 基準静止画を変換したもの、として表す。"""
    cap = cv2.VideoCapture(ref)
    bounds = [0] + [int(round(c * fps)) for c in cuts] + [nframes]
    shots = []
    for i, (s, e) in enumerate(zip(bounds[:-1], bounds[1:])):
        cap.set(cv2.CAP_PROP_POS_FRAMES, s)
        frames = []
        for _ in range(e - s):
            ok, f = cap.read()
            if not ok:
                break
            frames.append(f)
        n = len(frames)
        keys = list(range(0, n, step)) + ([n - 1] if (n - 1) % step else [])
        T = {0: np.eye(3)}  # T[k]: コマ0 → コマk(座標の写像)
        prev = 0
        bad = 0
        for k in keys[1:]:
            M = estimate_motion(frames[prev], frames[k])
            if not _sane(M):
                bad += 1
                M = np.array([[1, 0, 0], [0, 1, 0]], np.float64)
            T[k] = _to3(M) @ T[prev]
            prev = k
        # 中間コマは前後のキーを線形補間
        ks = sorted(T)
        allT = []
        for j in range(n):
            k0 = max(x for x in ks if x <= j)
            k1 = min(x for x in ks if x >= j)
            u = 0 if k1 == k0 else (j - k0) / (k1 - k0)
            allT.append(T[k0] + (T[k1] - T[k0]) * u)
        scales = [float(np.sqrt(t[0, 0] ** 2 + t[1, 0] ** 2)) for t in allT]
        b = int(np.argmin(scales))
        Tb_inv = np.linalg.inv(allT[b])
        rel = [t @ Tb_inv for t in allT]  # 基準コマ → 各コマ(3x3)
        plate, O = stitch_plate(frames, rel, keys, b)
        # 描画用: 素材(プレート)座標 → 各コマ
        tr = [(r @ np.linalg.inv(O))[:2].tolist() for r in rel]
        shots.append({"index": i + 1, "start_frame": s, "end_frame": s + n, "base_offset": b,
                      "zoom_total": round(max(scales) / min(scales), 4), "rejected_pairs": bad,
                      "plate_size": [plate.shape[1], plate.shape[0]], "transforms": tr, "base": plate})
        log.info(f"  カット{i + 1:2d} {s / fps:6.2f}-{(s + n) / fps:6.2f}s ズーム量 x{max(scales) / min(scales):.3f} "
                 f"(素材=+{b}コマ目, 除外{bad})")
    return shots


def stitch_plate(frames, rel, keys, b, max_ratio=2.0):
    """カット内のコマを基準座標につなぎ合わせ、元の写真全体(プレート)を復元する。
    字幕部分は他のコマの同じ位置で埋め、どのコマにも無い所だけ修復する。"""
    h, w = frames[0].shape[:2]
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float64).T
    pts = np.hstack([(np.linalg.inv(rel[k]) @ corners)[:2] for k in keys])
    x0, y0 = np.floor(pts.min(1)).astype(int)
    x1, y1 = np.ceil(pts.max(1)).astype(int)
    x0, y0 = max(x0, -int(w * (max_ratio - 1) / 2)), max(y0, -int(h * (max_ratio - 1) / 2))
    x1, y1 = min(x1, w + int(w * (max_ratio - 1) / 2)), min(y1, h + int(h * (max_ratio - 1) / 2))
    CW, CH = x1 - x0, y1 - y0
    O = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64)
    plate = np.zeros((CH, CW, 3), np.uint8)
    filled = np.zeros((CH, CW), bool)
    for k in sorted(keys, key=lambda k: abs(k - b)):
        f = frames[k]
        valid = (full_mask(f) == 0).astype(np.uint8) * 255
        valid = cv2.erode(valid, np.ones((3, 3), np.uint8))
        M = (O @ np.linalg.inv(rel[k]))[:2]
        wf = cv2.warpAffine(f, M, (CW, CH), flags=cv2.INTER_LANCZOS4)
        wv = cv2.warpAffine(valid, M, (CW, CH), flags=cv2.INTER_NEAREST) > 0
        take = wv & ~filled
        plate[take] = wf[take]
        filled |= take
        if filled.all():
            break
    holes = (~filled).astype(np.uint8) * 255
    if holes.any():
        plate = cv2.inpaint(plate, holes, 5, cv2.INPAINT_TELEA)
    return plate, O


def render_shot_frames(shot, still, n, W, H):
    for k in range(n):
        M = np.array(shot["transforms"][min(k, len(shot["transforms"]) - 1)])
        yield cv2.warpAffine(still, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=str(ROOT / "references" / "reference_02.mp4"))
    ap.add_argument("--subs", default=str(ROOT / "references" / "reference_02_subs.json"))
    ap.add_argument("--segments", default=str(ROOT / "references" / "reference_02_segments.json"))
    ap.add_argument("--job", default="rebuild_reference_02")
    a = ap.parse_args()
    job = Job(a.job)
    log = get_logger(job)
    log.info("=== 0から再構築(私的検証用・公開禁止) ===")
    info = ffprobe(a.ref)
    vs = next(x for x in info["streams"] if x["codec_type"] == "video")
    W, H = int(vs["width"]), int(vs["height"])
    num, den = map(int, vs["r_frame_rate"].split("/"))
    fps = num / den
    nframes = int(vs.get("nb_frames") or round(float(vs["duration"]) * fps))
    total = float(info["format"]["duration"])
    analysis = load_json(ROOT / "templates" / "reference_analysis_reference_02.json")

    # 1) カメラワーク測定と素材静止画
    log.info("カメラワークを測定中…")
    shots = plan_shots(a.ref, analysis["cuts"]["cut_times"], fps, nframes, log)
    stills_dir = job.assets / "stills"
    stills_dir.mkdir(parents=True, exist_ok=True)
    for s in shots:
        still = s.pop("base")
        p = stills_dir / f"shot{s['index']:02d}.png"
        cv2.imwrite(str(p), still)
        s["still"] = str(p.relative_to(ROOT))
    save_json(job.output / "rebuild_shots.json", [{k: v for k, v in x.items() if k != "transforms"} for x in shots])

    # 2) 映像(静止画+測定したカメラワーク)
    raw = job.output / "video_nosub.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", vs["r_frame_rate"], "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
                           "-pix_fmt", "yuv420p", str(raw)], stdin=subprocess.PIPE)
    for s in shots:
        still = cv2.imread(str(ROOT / s["still"]))
        for fr in render_shot_frames(s, still, s["end_frame"] - s["start_frame"], W, H):
            ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    log.info("映像を生成")

    # 3) ナレーション(VOICEVOX 青山龍星)
    from .tts import apply_readings, trim, write_wav
    from .vv_core import synth
    segs = load_json(a.segments)
    extra = {"浩宮さま": "ヒロノミヤサマ", "礼宮さま": "アヤノミヤサマ", "庇い": "カバイ", "仲立ち": "ナカダチ",
             "秋篠宮殿下": "アキシノノミヤデンカ"}
    sr = 24000
    narr = np.zeros(int(total * sr) + sr, np.float32)
    report = []
    for s in segs:
        text = apply_readings(s["text"], extra)
        target = s["end"] - s["start"]
        x = trim(synth(text, pitch=-0.03, intonation=0.8))
        speed = min(1.35, max(0.85, (len(x) / sr) / target))
        x = trim(synth(text, speed=speed, pitch=-0.03, intonation=0.8))
        i0 = int(s["start"] * sr)
        narr[i0:i0 + len(x)] += x[: len(narr) - i0]
        report.append({"start": s["start"], "target": round(target, 2), "got": round(len(x) / sr, 2), "speed": round(speed, 3), "text": s["text"]})
    narr = narr[: int(total * sr)]
    narr = narr / (np.abs(narr).max() + 1e-9) * 0.9
    wav = job.audio / "narration_voicevox.wav"
    import pipeline.tts as T
    T.SR = sr
    write_wav(wav, narr, sr)
    save_json(job.output / "narration_report.json", report)
    log.info(f"ナレーション(VOICEVOX:青山龍星) {len(segs)}区間 / 話速 中央値 {np.median([r['speed'] for r in report]):.2f}")

    # 4) テロップ + 合成(参考動画のラウドネスに合わせる)
    from . import subtitles
    subtitles.write_ass(job, load_json(a.subs)["chunks"])
    ass = str(job.ass).replace(":", "\\:")
    lufs = analysis["audio"]["integrated_lufs"]
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(wav),
         "-filter_complex", f"[0:v]ass='{ass}':fontsdir=/usr/share/fonts/opentype/noto,format=yuv420p[v];"
                            f"[1:a]aresample=44100,loudnorm=I={lufs}:TP=-1.5:LRA=7,aformat=channel_layouts=stereo[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-profile:v", "high",
         "-r", vs["r_frame_rate"], "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(job.video)])
    raw.unlink(missing_ok=True)
    log.info(f"完了: {job.video}")


if __name__ == "__main__":
    main()
