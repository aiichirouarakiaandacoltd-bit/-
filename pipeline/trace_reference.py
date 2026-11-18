"""参考動画トレース再現モード(非公開・検証用)。

参考動画の映像から焼き込み字幕を画像処理で消去し(全フレーム)、1080x1920へ拡大、
読み取った字幕データ(templates/trace/<name>_subs.json)をこのシステムの字幕エンジンで再描画し、
参考動画の音声を合わせて書き出す。

※ 出力は第三者の著作物の複製物であり、内容も未確認情報を含む。私的な検証用途に限り、
  YouTube・SNS等で公開しないこと。
"""
from __future__ import annotations

import os
import subprocess

import cv2
import numpy as np

BAND = (0.47, 0.74)


def subtitle_mask(bgr: np.ndarray) -> np.ndarray:
    """字幕(明るい塗り+黒い縁取り)の画素マスク。"""
    h, w = bgr.shape[:2]
    y0, y1 = int(h * BAND[0]), int(h * BAND[1])
    band = bgr[y0:y1]
    hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)
    v, s = hsv[..., 2], hsv[..., 1]
    bright = ((v > 185) & (s < 70)) | ((v > 150) & (s > 120))
    dark = v < 55
    k = np.ones((5, 5), np.uint8)
    white = (v > 200) & (s < 45)
    vivid = (s > 140) & (v > 160)
    k3 = np.ones((3, 3), np.uint8)
    edge = (cv2.dilate(bright.astype(np.uint8), k) & cv2.dilate(dark.astype(np.uint8), k)) | \
           (vivid.astype(np.uint8) & cv2.dilate(white.astype(np.uint8), k3)) | \
           (white.astype(np.uint8) & cv2.dilate(vivid.astype(np.uint8), k3))
    # 文字の塊 → 行の外接矩形を求め、その中の「明るい/暗い/高彩度」画素を全部消す(色付き強調語も含む)
    # 文字は「明暗の境界」が細かく密集する。境界密度の高い所だけを文字候補にする(服や建物の輪郭線を除外)
    dens = cv2.blur(edge.astype(np.float32), (17, 17))
    edge = (edge.astype(bool) & (dens > 0.15)).astype(np.uint8)
    blob = cv2.morphologyEx(edge, cv2.MORPH_CLOSE, np.ones((11, 25), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(blob)
    keep = np.zeros_like(blob)
    textish = ((v > 140) | (v < 75) | (s > 110)).astype(np.uint8)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 80 or bw < 12 or bh > (y1 - y0) * 0.95:
            continue
        xa, ya = max(0, x - 6), max(0, y - 6)
        xb, yb = min(w, x + bw + 6), min(y1 - y0, y + bh + 6)
        keep[ya:yb, xa:xb] |= textish[ya:yb, xa:xb]
    keep = cv2.dilate(keep, np.ones((5, 5), np.uint8))
    full = np.zeros((h, w), np.uint8)
    full[y0:y1] = keep * 255
    return full


def full_mask(bgr: np.ndarray) -> np.ndarray:
    """原寸の字幕マスク(0/255)。高解像度にも対応。"""
    h, w = bgr.shape[:2]
    if w <= 500:
        return subtitle_mask(bgr)
    small = cv2.resize(bgr, (406, round(h * 406 / w)), interpolation=cv2.INTER_AREA)
    m = subtitle_mask(small)
    if not m.any():
        return np.zeros((h, w), np.uint8)
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
    region = cv2.dilate(m, np.ones((45, 261), np.uint8)) > 0
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    textish = (hsv[..., 2] > 140) | (hsv[..., 2] < 75) | (hsv[..., 1] > 110)
    m = ((m > 0) | (region & textish)).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((9, 9), np.uint8))


def clean_frame(bgr: np.ndarray) -> np.ndarray:
    h, w = bgr.shape[:2]
    if w > 500:
        # 高解像度: 判定は参考動画と同じ 406 幅で行い、マスクを拡大して原寸で修復
        small = cv2.resize(bgr, (406, round(h * 406 / w)), interpolation=cv2.INTER_AREA)
        m = subtitle_mask(small)
        if not m.any():
            return bgr
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
        # 周辺を原寸で再判定(色付き強調語や縁取りの取りこぼしを拾う)
        region = cv2.dilate(m, np.ones((45, 261), np.uint8)) > 0  # 字幕は横一列: 行全体に広げる
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        vv, ss = hsv[..., 2], hsv[..., 1]
        textish = (vv > 140) | (vv < 75) | (ss > 110)
        m = ((m > 0) | (region & textish)).astype(np.uint8) * 255
        m = cv2.dilate(m, np.ones((7, 7), np.uint8))
        return cv2.inpaint(bgr, m, 5, cv2.INPAINT_TELEA)
    m = subtitle_mask(bgr)
    if m.any():
        return cv2.inpaint(bgr, m, 6, cv2.INPAINT_TELEA)
    return bgr


def build_background(src: str, out: str, W=1080, H=1920, passes=2, log=print) -> None:
    """全フレームの字幕を消去し、指定サイズで書き出す(元が1080幅以上なら原寸のまま)。"""
    cap = cv2.VideoCapture(src)
    sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    native = sw >= 1080
    if native:
        W, H = sw, sh
    fps = cap.get(cv2.CAP_PROP_FPS)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", f"{fps:.5f}", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    from multiprocessing import Pool

    def frames():
        while True:
            ok, fr = cap.read()
            if not ok:
                return
            yield fr

    k = 0
    pool = Pool(max(1, (os.cpu_count() or 2)))
    for f in pool.imap(_clean_n, ((fr, passes) for fr in frames()), chunksize=4):
        if native:
            big = f
        else:
            big = cv2.resize(f, (W, H), interpolation=cv2.INTER_LANCZOS4)
            blur = cv2.GaussianBlur(big, (0, 0), 1.6)
            big = cv2.addWeighted(big, 1.45, blur, -0.45, 0)  # 拡大による甘さを補う軽いシャープ
        ff.stdin.write(big.tobytes())
        k += 1
        if k % 300 == 0:
            log(f"  背景 {k}/{n} フレーム")
    pool.close()
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("背景映像のエンコード失敗")


def _clean_n(args):
    fr, n = args
    for _ in range(n):
        fr = clean_frame(fr)
    return fr


def main():
    import argparse
    from .common import Job, ROOT, get_logger, load_json, run, settings
    from . import subtitles

    ap = argparse.ArgumentParser(description="参考動画トレース再現(私的検証用・公開禁止)")
    ap.add_argument("--ref", default=str(ROOT / "references" / "reference_01.mp4"))
    ap.add_argument("--subs", default=str(ROOT / "references" / "reference_01_subs.json"))
    ap.add_argument("--job", default="trace_reference_01")
    ap.add_argument("--exact", action="store_true",
                    help="完全一致モード: 映像を加工せず(字幕も元のまま)1080x1920/30fpsへ変換し、元の音声をそのまま使う")
    a = ap.parse_args()
    job = Job(a.job)
    log = get_logger(job)
    cfg = settings()["output"]
    if a.exact:
        log.info("=== 完全一致モード(私的検証用・公開禁止) ===")
        from .common import ffprobe
        vs = next(x for x in ffprobe(a.ref)["streams"] if x["codec_type"] == "video")
        num, den = map(int, vs["r_frame_rate"].split("/"))
        if int(vs["width"]) >= 1080:
            # 高解像度の元動画: 画面サイズ・フレームレートを変えずにそのまま再エンコード(完全一致を優先)
            vf = "format=yuv420p"
            log.info(f"元動画の仕様を維持: {vs['width']}x{vs['height']} {num / den:.3f}fps")
        else:
            vf = f"scale=1080:1920:flags=lanczos,fps={cfg['fps']},format=yuv420p"
        run(["ffmpeg", "-y", "-v", "error", "-i", a.ref,
             "-vf", vf,
             "-c:v", "libx264", "-preset", "slow", "-crf", "10", "-profile:v", "high",
             "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(job.video)])
        log.info(f"完了: {job.video}")
        return
    log.info("=== トレース再現(私的検証用・公開禁止) ===")
    bg = job.output / "background_clean.mp4"
    if not bg.exists():
        log.info("焼き込み字幕を全フレーム消去して 1080x1920 に拡大中…")
        build_background(a.ref, str(bg), log=log.info)
    chunks = load_json(a.subs)["chunks"]
    subtitles.write_ass(job, chunks)
    log.info(f"字幕 {len(chunks)}チャンクを再描画")
    ass = str(job.ass).replace(":", "\\:")
    from .common import ffprobe
    vs = next(x for x in ffprobe(a.ref)["streams"] if x["codec_type"] == "video")
    if int(vs["width"]) >= 1080:
        # 元が高画質: 画面サイズ・fps・音声(無加工コピー)・尺を元動画と完全に揃える
        run(["ffmpeg", "-y", "-v", "error", "-i", str(bg), "-i", a.ref,
             "-filter_complex", f"[0:v]ass='{ass}':fontsdir=/usr/share/fonts/opentype/noto,format=yuv420p[v]",
             "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-profile:v", "high",
             "-r", vs["r_frame_rate"], "-c:a", "copy", "-movflags", "+faststart", str(job.video)])
    else:
        cfg = settings()["output"]
        run(["ffmpeg", "-y", "-v", "error", "-i", str(bg), "-i", a.ref,
             "-filter_complex", f"[0:v]ass='{ass}':fontsdir=/usr/share/fonts/opentype/noto,fps={cfg['fps']},format=yuv420p[v];"
                                f"[1:a]aresample=48000,loudnorm=I={cfg['target_loudness_lufs']}:TP=-1.5:LRA=11[a]",
             "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(job.video)])
    log.info(f"完了: {job.video}")


if __name__ == "__main__":
    main()
