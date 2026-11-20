"""サムネ・タイトル係の道具。

 --extract : 完成動画(字幕なし版)から、主役人物が写る候補フレームを5枚程度選ぶ(タイムコード付き)
 --render  : thumb.yaml(係が決めた文言・型・採用フレーム)から、Canvaテンプレートと同じ寸法でPNGを作る
             + Canva用の写真(枠の比率に合わせて顔位置を整えた切り抜き)と canva_plan.json を出す
型(テンプレート: 日本が誇る皇室物語｜Shorts S-A・S-B・S-C型):
  S-A = 写真1枚(主役が1枚に一緒に写る、または主役1名)
  S-B = 写真2枠(左右に別の写真。異なる日時の写真を同席に見せないよう間隔を空ける)
色: 濃紺 #16243A / 金 #D8BC72 / 白 #FFFFFF。人物の顔や表情は加工しない(切り抜き・拡大縮小のみ)。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import cv2
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

from .common import ROOT, Job, find_font, get_logger, load_json, save_json

NAVY, GOLD, WHITE = "#16243A", "#D8BC72", "#FFFFFF"
W, H = 1080, 1920
CANVA_TEMPLATE_ID = "DAHatUQFKSI"
LAYOUTS = {
    "S-B": {"frames": [(72, 560, 446, 490), (542, 560, 446, 490)], "upper_y": 430, "photo_bottom": 1050},
    "S-A": {"frames": [(72, 560, 936, 600)], "upper_y": 430, "photo_bottom": 1160},
}
TEXT_W = 840
SIZES = {"upper": 82, "middle": 132, "lower": 80}


# ---------------- フレーム候補 ----------------
def _faces(img):
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    f = casc.detectMultiScale(g, 1.1, 6, minSize=(60, 60))
    return [tuple(map(int, x)) for x in f]


def extract(job: Job, subjects: list[str], n: int = 5) -> dict:
    log = get_logger(job)
    src = job.output / "video_nosub.mp4"
    if not src.exists():
        src = job.video
    shots = load_json(job.output / "shots.json", []) or []
    script = load_json(job.script, {}) or {}
    vis = {s["id"]: s.get("visual", {}) for s in script.get("scenes", [])}
    cap = cv2.VideoCapture(str(src))
    out = job.output / "thumbs" / "candidates"
    out.mkdir(parents=True, exist_ok=True)
    cands = []
    for k, sh in enumerate(shots):
        subj = vis.get(sh.get("scene"), {}).get("subject", "")
        rel = sum(1 for p in subjects if p and (p in subj or subj in p))
        for u in (0.3, 0.6):
            t = sh["start"] + (sh["end"] - sh["start"]) * u
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, f = cap.read()
            if not ok:
                continue
            faces = _faces(f)
            sharp = float(cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
            big = max([w * h for _, _, w, h in faces], default=0) / (W * H)
            score = 3 * rel + min(len(faces), 2) * 1.5 + min(big * 60, 3) + min(sharp / 60, 2) - (sh.get("type") == "card") * 10
            cands.append({"shot": k, "scene": sh.get("scene"), "subject": subj, "t": round(t, 2),
                          "timecode": f"{int(t // 60):02d}:{t % 60:06.3f}", "faces": len(faces), "face_boxes": faces,
                          "sharpness": round(sharp, 1), "score": round(score, 2), "file": sh.get("file", ""),
                          "credit": sh.get("credit", ""), "_img": f})
    cands.sort(key=lambda c: c["score"], reverse=True)
    picked, used = [], set()
    for c in cands:
        if c["shot"] in used:
            continue
        used.add(c["shot"])
        picked.append(c)
        if len(picked) >= n:
            break
    tiles = []
    for i, c in enumerate(picked, 1):
        p = out / f"cand{i}.png"
        cv2.imwrite(str(p), c.pop("_img"))
        c["id"] = f"cand{i}"
        c["png"] = str(p.relative_to(ROOT))
        im = cv2.resize(cv2.imread(str(p)), (270, 480))
        cv2.putText(im, f"cand{i} {c['timecode']}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        tiles.append(im)
    for c in cands:
        c.pop("_img", None)
    if tiles:
        cv2.imwrite(str(out / "sheet.jpg"), np.hstack(tiles))
    res = {"source_video": str(src.relative_to(ROOT)), "subjects": subjects, "candidates": picked}
    save_json(out / "candidates.json", res)
    log.info(f"サムネ候補 {len(picked)}枚 → {out}")
    return res


# ---------------- 文字組み ----------------
def _font(size):
    return ImageFont.truetype(find_font(("NotoSansCJK-Black.ttc", "NotoSansCJK-Bold.ttc")), size)


def _width(text, size):
    return _font(size).getlength(text)


def _breakpoints(text: str) -> list[int]:
    """文節の切れ目(改行してよい位置)。"""
    try:
        from .subtitles import bunsetsu
        parts = bunsetsu(text)
        pts, acc = [], 0
        for p in parts[:-1]:
            acc += len(p)
            pts.append(acc)
        if "".join(parts) == text:
            return [i for i in pts if 0 < i < len(text) and text[i] not in "…？！、。」』）”"]
    except Exception:
        pass
    return [i + 1 for i, ch in enumerate(text[:-1]) if ch in "がのにもはをとで…、"]


def wrap(text: str, size: int, max_w: int = TEXT_W, max_lines: int = 2, min_size: int = 48) -> tuple[list[str], int]:
    """文言は一字一句変えず、改行位置(文節の切れ目)と文字サイズだけで収める。"""
    while size >= min_size:
        if _width(text, size) <= max_w:
            return [text], size
        if max_lines >= 2:
            ok = [(max(_width(text[:i], size), _width(text[i:], size)), i) for i in _breakpoints(text)]
            ok = [x for x in ok if x[0] <= max_w]
            if ok:
                i = min(ok)[1]
                return [text[:i], text[i:]], size
        size -= 2
    return [text], size


def _draw_text(d, lines, size, color, y, stroke=0):
    f = _font(size)
    lh = int(size * 1.15)
    for k, ln in enumerate(lines):
        d.text((W / 2, y + k * lh), ln, font=f, fill=color, anchor="ma", stroke_width=stroke, stroke_fill=NAVY)
    return y + lh * len(lines)


def crop_for_frame(img_path: str, fw: int, fh: int, face_y=0.36) -> Image.Image:
    """枠の比率で切り抜く(変形なし)。顔が複数あれば全員が入る位置、なければ中央。"""
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    faces = _faces(img)
    ar = fw / fh
    if w / h > ar:
        ch, cw = h, int(h * ar)
    else:
        cw, ch = w, int(w / ar)
    if faces:
        x0 = min(x for x, _, _, _ in faces); x1 = max(x + fw_ for x, _, fw_, _ in faces)
        y0 = min(y for _, y, _, _ in faces); y1 = max(y + fh_ for _, y, _, fh_ in faces)
        # 顔が小さければ寄る(顔の幅が枠の1/3程度)
        span = max(x1 - x0, (y1 - y0) * ar)
        cw = int(min(cw, max(span * 1.9, cw * 0.55)))
        ch = int(cw / ar)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    else:
        cx, cy = w / 2, h * 0.45
    left = int(min(max(cx - cw / 2, 0), w - cw))
    top = int(min(max(cy - face_y * ch, 0), h - ch))
    crop = img[top:top + ch, left:left + cw]
    crop = cv2.resize(crop, (fw * 2, fh * 2), interpolation=cv2.INTER_LANCZOS4)  # Canva用に2倍解像度
    return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))


def render_variant(job: Job, v: dict, texts: dict, cands: dict, outdir: Path, idx: int) -> dict:
    layout = v.get("layout", "S-B")
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 300), "日本が誇る皇室物語", font=_font(30), fill=GOLD, anchor="ma")
    d.rectangle((462, 352, 562, 355), fill=GOLD)
    up_lines, up_size = wrap(texts["upper"], v.get("upper_size", 100), max_lines=1)
    mid_lines, mid_size = wrap(texts["middle"], v.get("middle_size", SIZES["middle"]))
    lo_lines, lo_size = wrap(texts["lower"], v.get("lower_size", 92), max_lines=1)
    lh = lambda n, sz: int(sz * 1.15) * n
    y_up = 372
    top = y_up + lh(1, up_size) + 24
    bottom_limit = 1560  # 中央の重要領域(目安 y430〜1500前後)を大きく外れない
    block = 40 + lh(len(mid_lines), mid_size) + 14 + lh(1, lo_size)
    ph_h = int(min(max(bottom_limit - block - top, 420), 820))
    frames = ([(72, top, 446, ph_h), (562, top, 446, ph_h)] if layout == "S-B" else [(72, top, 936, ph_h)])
    _draw_text(d, up_lines, up_size, WHITE, y_up)
    photos = []
    for k, (fx, fy, fw, fh) in enumerate(frames):
        cid = v["photos"][k]
        c = cands[cid]
        ph = crop_for_frame(str(ROOT / c["png"]), fw, fh)
        p = outdir / f"v{idx}_photo{k + 1}.png"
        ph.save(p)
        im.paste(ph.resize((fw, fh), Image.LANCZOS), (fx, fy))
        photos.append({"frame": k + 1, "box": [fx, fy, fw, fh], "file": str(p.relative_to(ROOT)), "candidate": cid,
                       "timecode": c["timecode"], "source": c.get("file", ""), "credit": c.get("credit", "")})
    pb = top + ph_h
    tcs = " / ".join(p["timecode"] for p in photos)
    d.text((frames[-1][0] + frames[-1][2], pb + 6), f"本編より {tcs}", font=_font(20), fill="#9AA6B8", anchor="ra")
    y_mid = pb + 40
    y = _draw_text(d, mid_lines, mid_size, GOLD, y_mid)
    y_lo = y + 14
    y_end = _draw_text(d, lo_lines, lo_size, WHITE, y_lo)
    png = outdir / f"thumb_v{idx}.png"
    im.save(png)
    return {"variant": idx, "layout": layout, "png": str(png.relative_to(ROOT)), "photos": photos,
            "upper": {"lines": up_lines, "size": up_size, "y": y_up},
            "middle": {"lines": mid_lines, "size": mid_size, "y": y_mid},
            "lower": {"lines": lo_lines, "size": lo_size, "y": y_lo}, "content_bottom": y_end,
            "note": v.get("reason", "")}


def check_variant(r: dict, texts: dict) -> list[str]:
    errs = []
    for k in ("upper", "middle", "lower"):
        if "".join(r[k]["lines"]) != texts[k]:
            errs.append(f"{k}: 文言が一字一句一致しない")
    if r["middle"]["size"] < max(r["upper"]["size"], r["lower"]["size"]):
        errs.append("中段が最大になっていない")
    if r["content_bottom"] > 1600:
        errs.append(f"文字が下にはみ出し気味 (y={r['content_bottom']})")
    return errs


def render(job: Job) -> dict:
    log = get_logger(job)
    ty = yaml.safe_load(open(job.output / "thumb.yaml", encoding="utf-8"))
    cands = {c["id"]: c for c in load_json(job.output / "thumbs" / "candidates" / "candidates.json")["candidates"]}
    outdir = job.output / "thumbs"
    texts = ty["texts"]
    results = []
    for i, v in enumerate(ty["variants"], 1):
        r = render_variant(job, v, texts, cands, outdir, i)
        r["qc"] = check_variant(r, texts)
        results.append(r)
        log.info(f"サムネ案{i} ({r['layout']}) → {r['png']} {'OK' if not r['qc'] else r['qc']}")
    plan = {"template_design_id": CANVA_TEMPLATE_ID, "title": ty.get("title", ""), "texts": texts,
            "colors": {"navy": NAVY, "gold": GOLD, "white": WHITE}, "variants": results,
            "adopted": ty.get("adopted", 1)}
    save_json(outdir / "canva_plan.json", plan)
    # 3案を並べた比較シート
    ims = [Image.open(ROOT / r["png"]).resize((360, 640)) for r in results]
    sheet = Image.new("RGB", (360 * len(ims) + 20 * (len(ims) - 1), 640), "#000000")
    for k, x in enumerate(ims):
        sheet.paste(x, (k * 380, 0))
    sheet.save(outdir / "compare.png")
    return plan


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--subject", default=None, help="主役人物(カンマ区切り)")
    a = ap.parse_args()
    j = Job(a.job)
    if a.extract:
        subj = a.subject
        if not subj:
            st = load_json(ROOT / "state" / j.id / "state.json", {}) or {}
            subj = st.get("subject") or ""
        res = extract(j, [s.strip() for s in re.split(r"[,、]", subj) if s.strip()])
        print(json.dumps([{k: c[k] for k in ("id", "timecode", "subject", "faces", "score")} for c in res["candidates"]],
                         ensure_ascii=False, indent=1))
    if a.render:
        plan = render(j)
        print(json.dumps([{k: r[k] for k in ("variant", "layout", "png", "qc")} for r in plan["variants"]], ensure_ascii=False, indent=1))
