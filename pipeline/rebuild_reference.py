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


def _small_gray(f, w=270):
    """比較用の縮小画像(色も含めて比較するためBGRのまま)。"""
    h = round(f.shape[0] * w / f.shape[1])
    return cv2.resize(f, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)


def _residual(fa, fb, M):
    """aをMでbに重ねたときの不一致(字幕帯を除く平均絶対差, 0-255)。"""
    ga, gb = _small_gray(fa), _small_gray(fb)
    sc = ga.shape[1] / fa.shape[1]
    Ms = M.copy(); Ms[:, 2] *= sc
    wa = cv2.warpAffine(ga, Ms, (gb.shape[1], gb.shape[0]), borderValue=(-1, -1, -1))
    h = gb.shape[0]
    valid = wa[..., 0] >= 0
    valid[int(h * 0.45):int(h * 0.75)] = False
    return float(np.abs(wa - gb)[valid].mean()) if valid.any() else 255.0


def entrance_frames(chunks, fps, n_total, win=0.45):
    """字幕が滑り込み・拡大・回転しながら出てくる最初の win 秒のコマ番号(素材に使わない)。"""
    bad = set()
    for c in chunks:
        a, b = int(c["start"] * fps), int((c["start"] + win) * fps)
        bad.update(range(max(0, a - 2), min(n_total, b + 1)))
    return bad


def subtitle_masks_from_ass(job, chunks, W, H, dil=31):
    """書き起こしデータから字幕を実際に描画し、各チャンクの字幕位置マスク(画面座標)を作る。
    参考動画と同じ文字・同じ位置なので、薄い(フェード中の)字幕も確実に覆える。"""
    import tempfile
    from . import subtitles
    masks = []
    tmp = job.subs / "mask_frames"
    tmp.mkdir(parents=True, exist_ok=True)
    subtitles.write_ass(job, chunks)
    ass = str(job.ass).replace(":", "\\:")
    for i, c in enumerate(chunks):
        t = (c["start"] + c["end"]) / 2
        p = tmp / f"m{i:03d}.png"
        if not p.exists():
          run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:d=60:r=30",
               "-vf", f"ass='{ass}':fontsdir=/usr/share/fonts/opentype/noto", "-ss", f"{t:.3f}", "-frames:v", "1", str(p)])
        g = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        m = (g > 10).astype(np.uint8) * 255
        # 幅・高さの実測差(数%)を見込んで大きめに広げる
        m = cv2.dilate(m, np.ones((dil, int(dil * 2.2)), np.uint8))
        m = m | np.roll(m, -90, axis=1)  # 左から滑り込む出始めの位置も覆う
        masks.append((c["start"], c["end"], m))
    return masks


def plan_shots(ref: str, cuts: list[float], fps: float, nframes: int, log, chunks=None, step: int = 3,
               split_thr: float = 14.0, ass_masks=None) -> list[dict]:
    """各カットを(隠れたカットがあれば分割して)コマ単位の動きと復元素材(プレート)に変換する。"""
    cap = cv2.VideoCapture(ref)
    bounds = [0] + [int(round(c * fps)) for c in cuts] + [nframes]
    avoid = entrance_frames(chunks or [], fps, nframes)
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
        # 1) キーごとに動きを推定し、合わない所で分割(隠れたカット・色調切替)
        keys = list(range(0, n, step)) + ([n - 1] if (n - 1) % step else [])
        segs = [[0]]
        Ms = {}
        for k0, k1 in zip(keys[:-1], keys[1:]):
            M = estimate_motion(frames[k0], frames[k1])
            r = _residual(frames[k0], frames[k1], M) if _sane(M) else 255
            if r > split_thr:
                segs.append([k1])
            else:
                segs[-1].append(k1)
                Ms[(k0, k1)] = M
        for si, sk in enumerate(segs):
            a0 = sk[0]
            a1 = (segs[si + 1][0] if si + 1 < len(segs) else n)
            sub = list(range(a0, a1))
            T = {a0: np.eye(3)}
            for k0, k1 in zip(sk[:-1], sk[1:]):
                T[k1] = _to3(Ms[(k0, k1)]) @ T[k0]
            ks = sorted(T)
            allT = []
            for j in sub:
                lo = max([x for x in ks if x <= j], default=ks[0])
                hi = min([x for x in ks if x >= j], default=ks[-1])
                u = 0 if hi == lo else (j - lo) / (hi - lo)
                allT.append(T[lo] + (T[hi] - T[lo]) * u)
            scales = [float(np.sqrt(t[0, 0] ** 2 + t[1, 0] ** 2)) for t in allT]
            clean = [j for j in sub if (s + j) not in avoid] or sub
            b = min(clean, key=lambda j: scales[j - a0])
            Tb_inv = np.linalg.inv(allT[b - a0])
            rel = {j: allT[j - a0] @ Tb_inv for j in sub}
            use_keys = [k for k in ks if (s + k) not in avoid] or [b]
            if b not in use_keys:
                use_keys.append(b)
            extra = None
            if ass_masks:
                t0, t1 = (s + a0) / fps, (s + a1) / fps
                for (cs, ce, m) in ass_masks:
                    if cs < t1 and ce > t0:
                        extra = m if extra is None else (extra | m)
            plate, O, info = stitch_plate(frames, rel, use_keys, b, extra_mask=extra, mask_keys=ks)
            tr = [(rel[j] @ np.linalg.inv(O))[:2].tolist() for j in sub]
            holes = info.pop("holes")
            shots.append({"index": i + 1, "part": si, "start_frame": s + a0, "end_frame": s + a1, "base_offset": b,
                          "zoom_total": round(max(scales) / min(scales), 4), **info, "holes": holes,
                          "plate_size": [plate.shape[1], plate.shape[0]], "transforms": tr, "base": plate})
            log.info(f"  カット{i + 1:2d}{'-' + str(si + 1) if len(segs) > 1 else '  '} {(s + a0) / fps:6.2f}-{(s + a1) / fps:6.2f}s "
                     f"ズーム量 x{max(scales) / min(scales):.3f} 合成{info['used_frames']}コマ/除外{info['rejected_frames']}")
    return shots


def stitch_plate(frames, rel, keys, b, max_ratio=2.4, consist_thr=12.0, extra_mask=None, mask_keys=None):
    """コマを基準座標につなぎ合わせて元の写真(プレート)を復元する。
    - 字幕: カット内で字幕が出た範囲の和集合(画面座標)を全コマで除外
    - 動く被写体: 基準コマと重ねて一致しないコマは使わない(二重写し防止)"""
    h, w = frames[0].shape[:2]
    union = np.zeros((h, w), np.uint8)
    for k in (mask_keys or keys):  # 字幕の検出は全キー(出始めのコマも含む)で行う
        union |= full_mask(frames[k])
    if extra_mask is not None:
        union |= extra_mask
    union = cv2.dilate(union, np.ones((21, 21), np.uint8))
    valid0 = (union == 0).astype(np.uint8) * 255
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float64).T
    pts = np.hstack([(np.linalg.inv(rel[k]) @ corners)[:2] for k in keys])
    x0, y0 = np.floor(pts.min(1)).astype(int)
    x1, y1 = np.ceil(pts.max(1)).astype(int)
    x0, y0 = max(x0, -int(w * (max_ratio - 1) / 2)), max(y0, -int(h * (max_ratio - 1) / 2))
    x1, y1 = min(max(x1, w), w + int(w * (max_ratio - 1) / 2)), min(max(y1, h), h + int(h * (max_ratio - 1) / 2))
    x0, y0 = min(x0, 0), min(y0, 0)
    CW, CH = x1 - x0, y1 - y0
    O = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64)
    plate = np.zeros((CH, CW, 3), np.uint8)
    filled = np.zeros((CH, CW), bool)
    base_w = None
    used, rejected = 0, 0
    for k in sorted(keys, key=lambda k: abs(k - b)):
        M = (O @ np.linalg.inv(rel[k]))[:2]
        wf = cv2.warpAffine(frames[k], M, (CW, CH), flags=cv2.INTER_LANCZOS4)
        wv = cv2.warpAffine(valid0, M, (CW, CH), flags=cv2.INTER_NEAREST) > 0
        if base_w is None:
            base_w, base_v = wf.astype(np.float32), wv
        else:
            ov = wv & base_v
            if ov.sum() > 1000:
                d = np.abs(wf.astype(np.float32) - base_w)[ov].mean()
                if d > consist_thr:
                    rejected += 1
                    continue
        take = wv & ~filled
        if take.any():
            used += 1
        plate[take] = wf[take]
        filled |= take
        if filled.all():
            break
    holes = (~filled).astype(np.uint8) * 255
    if holes.any():
        plate = cv2.inpaint(plate, holes, 7, cv2.INPAINT_TELEA)
    return plate, O, {"used_frames": used, "rejected_frames": rejected, "hole_ratio": round(float((~filled).mean()), 4),
                      "holes": holes}


def _match(a, b, nfeat=5000):
    """プレートa→bの相似変換と一致点数(同じ写真かの判定用)。"""
    orb = cv2.ORB_create(nfeat)
    ka, da = orb.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None)
    kb, db = orb.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
    if da is None or db is None:
        return None, 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    good = []
    for m in bf.knnMatch(da, db, k=2):
        if len(m) == 2 and m[0].distance < 0.75 * m[1].distance:
            good.append(m[0])
    if len(good) < 30:
        return None, 0
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=4)
    return M, int(inl.sum()) if inl is not None else 0


def cross_fill(stills: list[dict], log, min_inliers=60, consist=20.0):
    """同じ写真が別カットにも使われていれば、位置を合わせてそこから穴を本物の絵で埋める。"""
    for s in stills:
        if not s.get("holes_file"):
            continue
        A = cv2.imread(str(ROOT / s["still"]))
        HA = cv2.imread(str(ROOT / s["holes_file"]), cv2.IMREAD_GRAYSCALE) > 0
        before = HA.mean()
        for t in stills:
            if t is s or (t["index"] == s["index"] and t.get("part") == s.get("part")):
                continue
            B = cv2.imread(str(ROOT / t["still"]))
            M, n = _match(B, A)
            if M is None or n < min_inliers:
                continue
            HB = cv2.imread(str(ROOT / t["holes_file"]), cv2.IMREAD_GRAYSCALE) > 0 if t.get("holes_file") \
                else np.zeros(B.shape[:2], bool)
            wb = cv2.warpAffine(B, M, (A.shape[1], A.shape[0]), flags=cv2.INTER_LANCZOS4)
            ok = cv2.warpAffine((~HB).astype(np.uint8) * 255, M, (A.shape[1], A.shape[0]), flags=cv2.INTER_NEAREST) > 0
            ov = ok & ~HA
            if ov.sum() < 5000 or np.abs(wb.astype(np.float32) - A.astype(np.float32))[ov].mean() > consist:
                continue  # 同じ写真でも色調が違う(白黒/青など)場合は使わない
            take = HA & ok
            if take.any():
                k = cv2.GaussianBlur(take.astype(np.float32), (0, 0), 2)[..., None]
                A = (wb * k + A * (1 - k)).astype(np.uint8)
                HA = HA & ~take
                log.info(f"  カット{s['index']}-{s.get('part', 0) + 1} の穴を カット{t['index']}-{t.get('part', 0) + 1} の同じ写真で補完 (一致点{n})")
        if HA.mean() < before:
            p = ROOT / s["still"].replace(".png", "_xf.png")
            cv2.imwrite(str(p), A)
            cv2.imwrite(str(ROOT / s["holes_file"]), HA.astype(np.uint8) * 255)
            s["still"] = str(p.relative_to(ROOT))
            s["hole_ratio"] = round(float(HA.mean()), 4)


def cover_plate(img, W, H, margin=1.10):
    """縦横比を保ったまま W*margin x H*margin を覆うように拡大し中央を切り出す(変形なし)。"""
    PW, PH = int(W * margin), int(H * margin)
    h, w = img.shape[:2]
    sc = max(PW / w, PH / h)
    r = cv2.resize(img, (int(w * sc + 0.5), int(h * sc + 0.5)), interpolation=cv2.INTER_LANCZOS4)
    y0, x0 = (r.shape[0] - PH) // 2, (r.shape[1] - PW) // 2
    return r[y0:y0 + PH, x0:x0 + PW]


def kenburns(n, W, H, PW, PH, z0=1.0, z1=1.07):
    out = []
    for k in range(n):
        u = k / max(1, n - 1)
        z = z0 + (z1 - z0) * u
        sc = (W / PW) * z
        tx, ty = W / 2 - sc * PW / 2, H / 2 - sc * PH / 2
        out.append([[sc, 0, tx], [0, sc, ty]])
    return out


def render_shot_frames(shot, still, n, W, H):
    for k in range(n):
        M = np.array(shot["transforms"][min(k, len(shot["transforms"]) - 1)])
        yield cv2.warpAffine(still, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=str(ROOT / "references" / "reference_02.mp4"))
    ap.add_argument("--subs", default=str(ROOT / "references" / "reference_02_subs.json"))
    ap.add_argument("--segments", default=str(ROOT / "references" / "reference_02_segments.json"))
    ap.add_argument("--job", default="rebuild_reference_02")
    ap.add_argument("--ai-shots", default=None,
                    help='AIで描き直すカットとプロンプトのJSON(下絵=復元素材, img2img)。例: assets/generated/ai_shots_reference_02.json')
    ap.add_argument("--ai-strength", type=float, default=0.35)
    ap.add_argument("--no-fill", action="store_true", help="字幕の裏の穴の補完(別カット+LaMa)をしない")
    ap.add_argument("--replace", default=None,
                    help='カットを生成画像等に差し替えるJSON。例: {"7": ["assets/generated/a.png"], "14": ["b.png", "c.png"]}')
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
    chunks = load_json(a.subs)["chunks"]
    log.info("字幕位置マスクを作成中…")
    ass_masks = subtitle_masks_from_ass(job, chunks, W, H)
    shots = plan_shots(a.ref, analysis["cuts"]["cut_times"], fps, nframes, log, chunks=chunks, ass_masks=ass_masks)
    stills_dir = job.assets / "stills"
    stills_dir.mkdir(parents=True, exist_ok=True)
    for s in shots:
        still = s.pop("base")
        holes = s.pop("holes", None)
        p = stills_dir / f"shot{s['index']:02d}_{s.get('part', 0)}.png"
        cv2.imwrite(str(p), still)
        if holes is not None and holes.any():
            hp = stills_dir / f"shot{s['index']:02d}_{s.get('part', 0)}_holes.png"
            cv2.imwrite(str(hp), holes)
            s["holes_file"] = str(hp.relative_to(ROOT))
        s["still"] = str(p.relative_to(ROOT))
    # 字幕の裏で写っていなかった穴を埋める: ①別カットの同じ写真 → ②LaMa(消去跡の補完AI)
    if not a.no_fill:
        log.info("字幕の裏の穴を補完中…")
        cross_fill(shots, log)
        from .lama_inpaint import inpaint as lama
        for s in shots:
            if not s.get("holes_file") or s.get("hole_ratio", 0) < 0.0005:
                continue
            src = cv2.imread(str(ROOT / s["still"]))
            holes = cv2.imread(str(ROOT / s["holes_file"]), cv2.IMREAD_GRAYSCALE)
            out = lama(src, holes)
            p = stills_dir / f"shot{s['index']:02d}_{s.get('part', 0)}_filled.png"
            cv2.imwrite(str(p), out)
            s["still"] = str(p.relative_to(ROOT))
            s["lama_filled_ratio"] = s.get("hole_ratio", 0)
    # AIで描き直し(下絵=復元素材)。カメラの動きは測定値のまま
    if a.ai_shots:
        from .ai_img2img import regenerate
        prompts = json.loads(open(a.ai_shots).read())
        for s in shots:
            pr = prompts.get(str(s["index"]))
            if not pr:
                continue
            src = cv2.imread(str(ROOT / s["still"]))
            out = regenerate(src, pr, strength=a.ai_strength, width=768, seed=s["index"] * 10 + s.get("part", 0))
            p = stills_dir / f"shot{s['index']:02d}_{s.get('part', 0)}_ai.png"
            cv2.imwrite(str(p), out)
            s["still"] = str(p.relative_to(ROOT))
            s["ai_regenerated"] = {"prompt": pr, "strength": a.ai_strength, "model": "stabilityai/sd-turbo img2img"}
            log.info(f"  カット{s['index']}-{s.get('part', 0) + 1} をAIで描き直し")
    # 差し替え(AI生成画像など): 参考動画と同じカット時刻で、ゆっくりズームを付ける
    if a.replace:
        rep = json.loads(open(a.replace).read()) if a.replace.endswith(".json") else json.loads(a.replace)
        new = []
        for s in shots:
            imgs = rep.get(str(s["index"]))
            if not imgs:
                new.append(s)
                continue
            n = s["end_frame"] - s["start_frame"]
            parts = np.array_split(np.arange(n), len(imgs))
            for j, (img, idx) in enumerate(zip(imgs, parts)):
                plate = cover_plate(cv2.imread(str(ROOT / img)), W, H, 1.10)
                p = stills_dir / f"shot{s['index']:02d}_{j}.png"
                cv2.imwrite(str(p), plate)
                new.append({"index": s["index"], "part": j, "start_frame": s["start_frame"] + int(idx[0]),
                            "end_frame": s["start_frame"] + int(idx[-1]) + 1, "replaced_by": img,
                            "transforms": kenburns(len(idx), W, H, plate.shape[1], plate.shape[0]),
                            "still": str(p.relative_to(ROOT))})
            log.info(f"  カット{s['index']} を差し替え: {imgs}")
        shots = new
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
