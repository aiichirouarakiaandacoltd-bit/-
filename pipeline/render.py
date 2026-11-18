"""ステージ7: 動画編集・書き出し。

- ショット設計: シーン境界でカット(参考動画: 平均3.5秒, 1.2〜6秒)。長いシーンは別素材/別構図に分割
- 9:16化: 顔検出(OpenCV)で人物を画面上部(字幕帯の上)に配置。収まらない横長写真はぼかし背景+全体表示
  (顔や体型を変形させない: 拡大縮小は縦横同率のみ)
- 動き: ゆっくりズームイン(1.00→1.09)+顔方向への軽いパン。サブピクセル補間で滑らかに
- 冒頭フック: 対象人物を赤い円で囲み矢印で示す(参考動画の注目演出)
- 素材が無いシーン: オリジナル図解テロップカード
- 自動取得写真には「資料写真」とクレジットを小さく表示
- 字幕(ASS)焼き込み、ナレーション+BGMのラウドネス調整、H.264/AAC 1080x1920 30fps
"""
from __future__ import annotations

import math
import os
import re
import subprocess
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .common import ROOT, Job, find_font, get_logger, load_json, media_duration, run, save_json, settings, style

W, H = 1080, 1920


# ---------------- 顔検出・プレート作成 ----------------
@lru_cache(maxsize=1)
def _cascade():
    import cv2
    return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def detect_faces(img: Image.Image) -> list[tuple[int, int, int, int]]:
    import cv2
    g = np.array(img.convert("L"))
    scale = 900 / max(g.shape)
    small = cv2.resize(g, None, fx=scale, fy=scale) if scale < 1 else g
    s = scale if scale < 1 else 1.0
    faces = _cascade().detectMultiScale(small, scaleFactor=1.1, minNeighbors=6, minSize=(int(24), int(24)))
    out = [(int(x / s), int(y / s), int(w / s), int(h / s)) for x, y, w, h in faces]
    # 小さすぎる誤検出を除外(最大顔の35%未満)
    if out:
        mx = max(f[2] for f in out)
        out = [f for f in out if f[2] >= mx * 0.35]
    return out


def _load(path: str) -> Image.Image:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def make_plate(path: str, variant: str, Z: float, rules: dict) -> dict:
    """ズーム用に出力より Z 倍大きいプレートを作る。戻り値: plate画像, 焦点(顔中心), 顔枠"""
    im = _load(path)
    faces = detect_faces(im)
    PW, PH = int(W * Z), int(H * Z)
    iw, ih = im.size
    target_ar = PW / PH
    fy_t = rules["framing"]["face_target_y"]
    if faces:
        x0 = min(f[0] for f in faces); x1 = max(f[0] + f[2] for f in faces)
        y0 = min(f[1] for f in faces); y1 = max(f[1] + f[3] for f in faces)
        fcx, fcy = (x0 + x1) / 2, (y0 + y1) / 2
        fh = max(f[3] for f in faces)
    else:
        fcx, fcy, fh = iw / 2, ih * 0.4, None
        x0 = x1 = fcx
    # クロップ窓(縦9:16)
    if variant == "close" and faces:
        ch = min(ih, fh * 5.0)  # 顔が画面高の約20%
    else:
        ch = ih
    cw = ch * target_ar
    if cw > iw:
        cw = iw
        ch = cw / target_ar
    fits = (x1 - x0) <= cw * 0.85
    mode = "crop" if (fits or iw / ih <= target_ar * 1.35) else "blur_bg"
    if mode == "crop":
        cx = min(max(fcx, cw / 2), iw - cw / 2)
        top = fcy - fy_t * ch
        top = min(max(top, 0), ih - ch)
        box = (cx - cw / 2, top, cx + cw / 2, top + ch)
        plate = im.resize((PW, PH), Image.LANCZOS, box=box)
        sx = PW / cw
        focus = ((fcx - box[0]) * sx, (fcy - box[1]) * sx)
        fboxes = [((f[0] - box[0]) * sx, (f[1] - box[1]) * sx, f[2] * sx, f[3] * sx) for f in faces]
    else:
        bg = im.resize((max(1, int(iw * PH / ih)), PH), Image.LANCZOS)
        bx = (bg.width - PW) // 2
        bg = bg.crop((bx, 0, bx + PW, PH)).filter(ImageFilter.GaussianBlur(28))
        bg = Image.eval(bg, lambda v: int(v * 0.55))
        fw = PW
        fh2 = int(ih * fw / iw)
        fg = im.resize((fw, fh2), Image.LANCZOS)
        top = int(PH * 0.36 - fh2 / 2)
        top = max(int(PH * 0.06), top)
        bg.paste(fg, (0, top))
        plate = bg
        sx = fw / iw
        focus = (fcx * sx, fcy * sx + top)
        fboxes = [(f[0] * sx, f[1] * sx + top, f[2] * sx, f[3] * sx) for f in faces]
    return {"img": plate, "focus": focus, "faces": fboxes, "mode": mode, "upscale": PW / (cw if mode == "crop" else iw)}


def annotate_hook(plate: Image.Image, faces: list, focus) -> Image.Image:
    """冒頭の注目演出: 人物の顔を赤い円で囲み、右下から矢印。"""
    if not faces:
        return plate
    f = max(faces, key=lambda b: b[2])
    cx, cy = f[0] + f[2] / 2, f[1] + f[3] / 2
    r = f[2] * 1.05
    im = plate.copy()
    d = ImageDraw.Draw(im)
    red = (235, 40, 30)
    lw = max(10, int(plate.width * 0.011))
    d.ellipse((cx - r, cy - r * 1.15, cx + r, cy + r * 1.15), outline=red, width=lw)
    # 矢印(右下 → 円の縁)
    ang = math.radians(40)
    tip = (cx + r * 1.02 * math.cos(ang), cy + r * 1.17 * math.sin(ang))
    L = r * 2.0
    tail = (tip[0] + L * math.cos(ang), tip[1] + L * math.sin(ang))
    d.line([tail, tip], fill=red, width=int(lw * 1.6))
    hs = lw * 4.2
    for da in (-0.5, 0.5):
        p = (tip[0] + hs * math.cos(ang + da), tip[1] + hs * math.sin(ang + da))
        d.line([tip, p], fill=red, width=int(lw * 1.6))
    return im


# ---------------- 図解カード ----------------
def make_card(text: str, sub: str, Z: float, seed: int = 0) -> dict:
    PW, PH = int(W * Z), int(H * Z)
    y = np.linspace(0, 1, PH)[:, None]
    x = np.linspace(0, 1, PW)[None, :]
    base = np.stack(np.broadcast_arrays(12 + 18 * y + 6 * x, 22 + 26 * y + 0 * x, 48 + 40 * (1 - y) + 0 * x), axis=-1)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    gold = (212, 175, 90)
    # 控えめな同心円と斜線の装飾(オリジナル)
    cx, cy = PW * (0.25 + 0.5 * rng.random()), PH * 0.22
    for k in range(9):
        rr = PH * 0.06 * (k + 1)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=gold + (26,), width=3)
    for k in range(-6, 14):
        x0 = k * PW * 0.12
        d.line([(x0, PH), (x0 + PH * 0.5, 0)], fill=(255, 255, 255, 10), width=2)
    font = find_font()
    fs = int(PW * 0.13) if len(text) <= 6 else int(PW * 0.95 / max(1, len(text)))
    f1 = ImageFont.truetype(font, fs)
    f2 = ImageFont.truetype(find_font(("NotoSansCJK-Bold.ttc", "ipag.ttf")), int(PW * 0.05))
    ty = PH * 0.30
    d.line([(PW * 0.12, ty - fs * 0.9), (PW * 0.88, ty - fs * 0.9)], fill=gold + (220,), width=4)
    d.text((PW / 2, ty), text, font=f1, fill=(255, 255, 255), anchor="mm", stroke_width=int(fs * 0.06), stroke_fill=(20, 20, 40))
    if sub:
        d.text((PW / 2, ty + fs * 0.95), sub, font=f2, fill=gold, anchor="mm")
    d.line([(PW * 0.12, ty + fs * 1.55), (PW * 0.88, ty + fs * 1.55)], fill=gold + (220,), width=4)
    return {"img": img, "focus": (PW / 2, ty), "faces": [], "mode": "card", "upscale": 1.0}


@lru_cache(maxsize=64)
def _label(text: str, credit: str) -> Image.Image:
    """左上の『資料写真』ラベル+クレジット(RGBA)。"""
    f1 = ImageFont.truetype(find_font(("NotoSansCJK-Bold.ttc", "ipag.ttf")), 34)
    f2 = ImageFont.truetype(find_font(("NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc", "ipag.ttf")), 24)
    im = Image.new("RGBA", (W, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tw = d.textlength(text, font=f1)
    d.rounded_rectangle((36, 150 - 120, 36 + tw + 28, 150 - 120 + 50), 8, fill=(0, 0, 0, 140))
    d.text((50, 150 - 120 + 25), text, font=f1, fill=(255, 255, 255, 235), anchor="lm")
    if credit:
        d.text((40, 150 - 120 + 76), credit[:70], font=f2, fill=(255, 255, 255, 210), anchor="lm",
               stroke_width=2, stroke_fill=(0, 0, 0, 200))
    return im


# ---------------- ショット設計 ----------------
def reference_bounds(timeline: dict, ref_analysis: dict, min_sec: float) -> list[float]:
    """参考動画のカット位置(尺に合わせて伸縮)を、近いシーン境界(±1.2秒)→文境界(±0.8秒)に吸着させる。"""
    dur = timeline["duration"]
    rdur = ref_analysis["technical"]["duration_sec"]
    scene_b = [sc["start"] for sc in timeline["scenes"][1:]]
    sent_b = [se["start"] for sc in timeline["scenes"] for se in sc["sentences"]][1:]
    out = [0.0]
    for c in ref_analysis["cuts"]["cut_times"]:
        t = c * dur / rdur
        near = min(scene_b, key=lambda b: abs(b - t), default=None)
        if near is not None and abs(near - t) <= 1.2:
            t = near
        else:
            near = min(sent_b, key=lambda b: abs(b - t), default=None)
            if near is not None and abs(near - t) <= 0.8:
                t = near
        if t - out[-1] >= min_sec * 0.8 and dur - t >= min_sec * 0.8:
            out.append(t)
    return out + [dur]


def plan_shots(job: Job, script: dict, timeline: dict, manifest: dict, rules: dict, ref_analysis: dict | None = None) -> list[dict]:
    sh = rules["shot"]
    if ref_analysis:
        return _plan_reference(script, timeline, manifest, rules, ref_analysis)
    picks = {s["scene"]: s["picks"] for s in manifest["scenes"]}
    files = manifest["files"]
    scene_by_id = {s["id"]: s for s in script["scenes"]}
    usage: dict[str, int] = {}
    shots = []
    scenes = timeline["scenes"]
    for i, sc in enumerate(scenes):
        start = 0.0 if i == 0 else sc["start"]
        end = scenes[i + 1]["start"] if i + 1 < len(scenes) else timeline["duration"]
        dur = end - start
        sp = scene_by_id[sc["id"]]
        v = sp.get("visual", {})
        p = list(picks.get(sc["id"], []))
        n = max(1, math.ceil(dur / sh["max_sec"]))
        if i == 0 and sc.get("role") == "hook" and dur > sh["hook_first_shot_sec"] + sh["min_sec"]:
            bounds = [start, start + sh["hook_first_shot_sec"]]
            rest = end - bounds[-1]
            m = max(1, math.ceil(rest / sh["max_sec"]))
            bounds += [bounds[-1] + rest * (k + 1) / m for k in range(m)]
        else:
            bounds = [start + dur * k / n for k in range(n + 1)]
        for k in range(len(bounds) - 1):
            if p:
                # 使用回数の少ない素材を優先(同じ写真の連続を避ける)
                p.sort(key=lambda f: usage.get(f, 0))
                f = p[0]
                usage[f] = usage.get(f, 0) + 1
                variant = "close" if usage[f] % 2 == 0 else "wide"
                rec = files.get(f, {})
                credit = f"{(rec.get('rights_holder') or '')[:30]} / {rec.get('license', '')}".strip(" /")
                shots.append({"scene": sc["id"], "start": bounds[k], "end": bounds[k + 1], "type": "image",
                              "file": str(ROOT / f), "variant": variant, "credit": credit,
                              "fallback_text": v.get("card_text") or v.get("subject", ""), "sub": v.get("card_sub", ""),
                              "label": "資料写真" if v.get("kind") in ("person", None) or "library" not in rec.get("found_via", "") else "",
                              "hook": i == 0 and k == 0 and sc.get("role") == "hook"})
            else:
                shots.append({"scene": sc["id"], "start": bounds[k], "end": bounds[k + 1], "type": "card",
                              "text": v.get("card_text") or v.get("subject", ""), "sub": v.get("card_sub", ""),
                              "hook": False})
    # 直前と同じ素材・同じ構図が続く場合は構図を変える
    for a, b in zip(shots, shots[1:]):
        if a.get("file") and a.get("file") == b.get("file") and a.get("variant") == b.get("variant"):
            b["variant"] = "close" if a["variant"] == "wide" else "wide"
    for s in shots:
        s["start"], s["end"] = round(s["start"], 3), round(s["end"], 3)
    return shots


def _plan_reference(script, timeline, manifest, rules, ref_analysis) -> list[dict]:
    """参考動画と同じカット割りモード: 区間の中央で話しているシーンの素材を使う。"""
    bounds = reference_bounds(timeline, ref_analysis, rules["shot"]["min_sec"])
    picks = {s["scene"]: s["picks"] for s in manifest["scenes"]}
    files = manifest["files"]
    scene_by_id = {s["id"]: s for s in script["scenes"]}
    usage: dict[str, int] = {}
    shots = []
    for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
        mid = (a + b) / 2
        sc = next((x for x in timeline["scenes"] if x["start"] <= mid < x["end"]), timeline["scenes"][-1])
        v = scene_by_id[sc["id"]].get("visual", {})
        p = list(picks.get(sc["id"], []))
        if p:
            p.sort(key=lambda f: usage.get(f, 0))
            f = p[0]
            usage[f] = usage.get(f, 0) + 1
            rec = files.get(f, {})
            shots.append({"scene": sc["id"], "start": round(a, 3), "end": round(b, 3), "type": "image",
                          "file": str(ROOT / f), "variant": "close" if usage[f] % 2 == 0 else "wide",
                          "credit": f"{(rec.get('rights_holder') or '')[:30]} / {rec.get('license', '')}".strip(" /"),
                          "fallback_text": v.get("card_text") or v.get("subject", ""), "sub": v.get("card_sub", ""),
                          "label": "資料写真" if "library" not in rec.get("found_via", "") else "",
                          "hook": k == 0})
        else:
            shots.append({"scene": sc["id"], "start": round(a, 3), "end": round(b, 3), "type": "card",
                          "text": v.get("card_text") or v.get("subject", ""), "sub": v.get("card_sub", ""), "hook": False})
    for x, y in zip(shots, shots[1:]):
        if x.get("file") and x.get("file") == y.get("file") and x.get("variant") == y.get("variant"):
            y["variant"] = "close" if x["variant"] == "wide" else "wide"
    return shots


# ---------------- フレーム生成 ----------------
_PLATES: dict = {}


def _ease(u: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0), 1))


def _init_worker(shots, rules):
    global _SHOTS, _RULES
    _SHOTS, _RULES = shots, rules


def _plate_for(idx: int):
    if idx in _PLATES:
        return _PLATES[idx]
    s = _SHOTS[idx]
    Z = _RULES["shot"]["zoom_end"] + _RULES["shot"]["pan_max_ratio"]
    if s["type"] == "card":
        pl = make_card(s["text"], s.get("sub", ""), Z, seed=idx)
    else:
        try:
            pl = make_plate(s["file"], s.get("variant", "wide"), Z, _RULES)
        except Exception as e:  # 素材が壊れていても止めずに図解カードで代替(理由は標準エラーに出す)
            import sys
            print(f"[render] 素材読み込み失敗 {s['file']}: {e!r} → 図解カードで代替", file=sys.stderr)
            pl = make_card(s.get("text") or s.get("fallback_text", ""), s.get("sub", ""), Z, seed=idx)
        if s.get("hook"):
            pl["img"] = annotate_hook(pl["img"], pl["faces"], pl["focus"])
    pl["Z"] = Z
    if len(_PLATES) > 3:
        _PLATES.clear()
    _PLATES[idx] = pl
    return pl


def _frame(args):
    idx, t = args
    s = _SHOTS[idx]
    pl = _plate_for(idx)
    sh = _RULES["shot"]
    Z = pl["Z"]
    PW, PH = pl["img"].size
    u = (t - s["start"]) / max(1e-3, s["end"] - s["start"])
    e = _ease(u) * 0.85 + u * 0.15
    z = sh["zoom_start"] + (sh["zoom_end"] - sh["zoom_start"]) * e  # 1.00→1.09
    # 窓サイズ: z=1 でプレート全体(構図どおり)を表示し、z に応じて寄る
    ww = PW / z
    wh = ww * H / W
    # 中心: プレート中心 → 焦点方向へ軽くパン
    fx, fy = pl["focus"]
    k = 0.35 * e
    cx = PW / 2 + (fx - PW / 2) * k
    cy = PH / 2 + (fy - PH / 2) * k * 0.6
    cx = min(max(cx, ww / 2), PW - ww / 2)
    cy = min(max(cy, wh / 2), PH - wh / 2)
    a = ww / W
    data = (a, 0, cx - ww / 2, 0, a, cy - wh / 2)
    fr = pl["img"].transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC)
    if s.get("label"):
        lab = _label(s["label"], s.get("credit", ""))
        fr.paste(lab, (0, 60), lab)
    if s.get("hook") and t - s["start"] < 0.12:  # 冒頭の白フラッシュ
        al = 1 - (t - s["start"]) / 0.12
        fr = Image.blend(fr, Image.new("RGB", fr.size, (255, 255, 255)), al * 0.85)
    return fr.tobytes()


def render_video(job: Job, shots: list[dict], duration: float, rules: dict, log) -> Path:
    fps = settings()["output"]["fps"]
    nframes = int(round(duration * fps))
    tasks = []
    si = 0
    for n in range(nframes):
        t = n / fps
        while si + 1 < len(shots) and t >= shots[si]["end"]:
            si += 1
        tasks.append((si, t))
    raw = job.output / "video_nosub.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
                           "-pix_fmt", "yuv420p", str(raw)], stdin=subprocess.PIPE)
    procs = max(1, (os.cpu_count() or 2))
    # ショット単位で連続したフレームをまとめて同じワーカーに渡す(プレートのキャッシュを効かせる)
    with Pool(procs, initializer=_init_worker, initargs=(shots, rules)) as pool:
        for k, buf in enumerate(pool.imap(_frame, tasks, chunksize=15)):
            ff.stdin.write(buf)
            if k % 300 == 0:
                log.info(f"  フレーム {k}/{nframes}")
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg(映像エンコード)失敗")
    return raw


# ---------------- 音声ミックス ----------------
def _measure_lufs(path: Path) -> float:
    r = run(["ffmpeg", "-i", str(path), "-af", "ebur128", "-f", "null", "-"], check=False)
    m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -23.0


def mix_audio(job: Job, bgm: Path | None, duration: float, log) -> Path:
    out = settings()["output"]
    target = out["target_loudness_lufs"]
    voice_i = _measure_lufs(job.narration)
    g_v = target - voice_i
    inputs = ["-i", str(job.narration)]
    fl = f"[0:a]aresample=48000,volume={g_v:.2f}dB,apad=whole_dur={duration:.3f}[v]"
    if bgm and bgm.exists():
        b = settings()["bgm"]
        bgm_i = _measure_lufs(bgm)
        g_b = (target - b["volume_db_below_voice"]) - bgm_i
        inputs += ["-stream_loop", "-1", "-i", str(bgm)]
        fl += (f";[1:a]aresample=48000,atrim=0:{duration:.3f},volume={g_b:.2f}dB,"
               f"afade=t=in:d={b['fade_in']},afade=t=out:st={max(0, duration - b['fade_out']):.3f}:d={b['fade_out']}[b]"
               f";[v][b]amix=inputs=2:duration=first:normalize=0[m];[m]alimiter=limit=0.89:level=false[a]")
        log.info(f"  音量: ナレーション {voice_i:.1f}→{target}LUFS, BGM {bgm_i:.1f}→{target - b['volume_db_below_voice']}LUFS")
    else:
        fl += ";[v]alimiter=limit=0.89:level=false[a]"
    mixed = job.audio / "mix.wav"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fl, "-map", "[a]", "-t", f"{duration:.3f}",
         "-ac", "2", "-ar", "48000", str(mixed)])
    return mixed


def render(job: Job, script: dict, timeline: dict, manifest: dict, bgm: Path | None, ref_analysis: dict | None = None) -> Path:
    log = get_logger(job)
    rules = style()["rules"]
    cfg = settings()["output"]
    duration = min(timeline["duration"], cfg["max_duration"])
    shots = plan_shots(job, script, timeline, manifest, rules, ref_analysis)
    if ref_analysis:
        log.info(f"参考動画カット割りモード: {ref_analysis['cuts']['shot_count']}カット → {len(shots)}カット")
    save_json(job.output / "shots.json", shots)
    log.info(f"ショット {len(shots)}本 (平均 {duration / len(shots):.2f}秒) を描画中…")
    raw = render_video(job, shots, duration, rules, log)
    mixed = mix_audio(job, bgm, duration, log)
    ass = str(job.ass).replace("\\", "/").replace(":", "\\:")
    fontsdir = "/usr/share/fonts/opentype/noto"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(mixed),
         "-filter_complex", f"[0:v]ass='{ass}':fontsdir={fontsdir},format=yuv420p[v]",
         "-map", "[v]", "-map", "1:a", "-c:v", cfg["vcodec"], "-preset", cfg["preset"], "-crf", str(cfg["crf"]),
         "-profile:v", "high", "-r", str(cfg["fps"]), "-c:a", cfg["acodec"], "-b:a", cfg["audio_bitrate"],
         "-movflags", "+faststart", "-t", f"{duration:.3f}", str(job.video)])
    raw.unlink(missing_ok=True)
    log.info(f"書き出し完了: {job.video} ({media_duration(job.video):.2f}秒)")
    job.mark("render", True, video=str(job.video.relative_to(ROOT)), shots=len(shots))
    return job.video


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    j = Job(a.job)
    b = j.audio / "bgm.wav"
    render(j, load_json(j.script), load_json(j.timeline), load_json(j.asset_manifest), b if b.exists() else None)
