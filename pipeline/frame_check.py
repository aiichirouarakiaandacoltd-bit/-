"""当てっこ係の道具: 書き出した動画をコマごとに点検する。

機械で判定できる項目を数値で出し、目視用の点検シート(0.5秒ごと)を作る。
 - 黒・単色コマ / 静止しすぎ(素材の欠落)
 - ボケ(シャープさが極端に低い)
 - ちらつき(前後のコマとの差が急に大きい)
 - 字幕が顔に重なっていないか
出力: output/<job>/frames/report.json, sheet_*.jpg
"""
from __future__ import annotations

import argparse
import json

import cv2
import numpy as np

from .common import Job, get_logger, load_json, save_json


def check(job: Job, step_sec: float = 0.5) -> dict:
    log = get_logger(job)
    out = job.output / "frames"
    out.mkdir(exist_ok=True)
    cap = cv2.VideoCapture(str(job.video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    chunks = load_json(job.subs / "chunks.json", []) or []
    sub_y0, sub_y1 = int(H * 0.53), int(H * 0.70)
    issues, thumbs, prev = [], [], None
    flick = []
    for i in range(n):
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (270, 480)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            flick.append(float(np.abs(g - prev).mean()))
        prev = g
        if i % max(1, int(fps * step_sec)):
            continue
        t = i / fps
        sharp = float(cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        if g.std() < 4:
            issues.append({"t": round(t, 2), "kind": "単色・黒コマ", "detail": f"std={g.std():.1f}"})
        if sharp < 6:
            issues.append({"t": round(t, 2), "kind": "ボケ", "detail": f"sharpness={sharp:.1f}"})
        on = any(c["start"] <= t < c["end"] for c in chunks)
        if on:
            faces = casc.detectMultiScale(cv2.cvtColor(cv2.resize(f, (540, 960)), cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(30, 30))
            for (x, y, w, h) in faces:
                cy0, cy1 = y * 2, (y + h) * 2
                if cy1 > sub_y0 and cy0 < sub_y1 and h * 2 > H * 0.05:
                    issues.append({"t": round(t, 2), "kind": "字幕が顔に重なる", "detail": f"face y={cy0}-{cy1}"})
        thumbs.append((t, cv2.resize(f, (180, 320))))
    # ちらつき: 直前10コマの中央値の4倍以上の急変(カット点は除く)
    shots = load_json(job.output / "shots.json", []) or []
    cuts = {round(s["start"] * fps) for s in shots}
    for k in range(10, len(flick)):
        base = np.median(flick[k - 10:k]) + 0.5
        if flick[k] > base * 4 and flick[k] > 8 and all(abs(k + 1 - c) > 2 for c in cuts):
            issues.append({"t": round((k + 1) / fps, 2), "kind": "ちらつき", "detail": f"diff={flick[k]:.1f}"})
    # 点検シート(10x6 = 30秒ごと)
    for s in range(0, len(thumbs), 60):
        tiles = []
        for t, im in thumbs[s:s + 60]:
            im = im.copy()
            cv2.putText(im, f"{t:.1f}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            tiles.append(im)
        while len(tiles) % 10:
            tiles.append(np.zeros_like(tiles[0]))
        rows = [np.hstack(tiles[r:r + 10]) for r in range(0, len(tiles), 10)]
        cv2.imwrite(str(out / f"sheet_{s // 60 + 1}.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    rep = {"video": str(job.video), "frames": n, "issues": issues, "passed": not issues,
           "sheets": sorted(str(p) for p in out.glob("sheet_*.jpg"))}
    save_json(out / "report.json", rep)
    log.info(f"コマ点検: {len(issues)}件 → {out / 'report.json'}")
    return rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    r = check(Job(a.job))
    print(json.dumps({"passed": r["passed"], "issues": r["issues"][:20], "sheets": r["sheets"]}, ensure_ascii=False, indent=1))
