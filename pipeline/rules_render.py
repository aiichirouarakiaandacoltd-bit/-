"""制作ルール(2026-11-21版)準拠の生成(G4)。scenes.json → 音声・字幕・映像 → MP4。

入力 : projects/<制作番号>/scenes.json(G3で確定・荒木承認済み)、ledger.csv、env_check.json
出力 : projects/<制作番号>/output/<制作番号>_<縦型|横型>_internal.mp4、scenes.json に start/end/subtitle を記入

scenes.json(配列)の1場面:
  {"scene": "01-1", "chapter": "疑問", "role": "question|answer|body",
   "narration": "完成ナレーション", "image": "A003", "crop": "全身|顔の寄り|手元・装い",
   "motion": "ゆっくり拡大|ゆっくり縮小|左へパン|右へパン", "person_label": "愛子内親王殿下",
   "caption": "2026年10月29日 園遊会(赤坂御苑)",
   "compare": {"images": ["A002", "A005"], "labels": ["天皇陛下", "..."]}   # 比較場面だけ(左右並び)
  }
仕様: 第4章(切替・最長表示・同一画像3回まで)、第5章(尺・画面・fps・音声0.90・字幕・BGM -18〜-24dB)。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import subprocess
import wave
from pathlib import Path

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

from .common import ROOT, load_json, save_json

FONT_DIR = Path("/usr/local/share/fonts/noto-sans-jp")
FONT_B = str(FONT_DIR / "NotoSansJP-Bold.ttf")
FONT_R = str(FONT_DIR / "NotoSansJP-Regular.ttf")
VV = "http://127.0.0.1:50021"
SPEED = 0.90
SPEC = {
    "縦型": {"W": 1080, "H": 1920, "max_dur": 59.0, "cut": (2.0, 4.0), "max_show": 5.0, "line": 7, "sub_size": 140,
             "sub_y": 0.66, "person_ratio": 0.95, "cuts": (15, 25), "images": 12},
    "横型": {"W": 1920, "H": 1080, "max_dur": 720.0, "cut": (4.0, 6.0), "max_show": 8.0, "line": 13, "sub_size": 130,
             "sub_y": 0.84, "person_ratio": 0.90, "cuts": (100, 150), "images": 60},
}
NAVY, GOLD, WHITE = (22, 36, 58), (216, 188, 114), (255, 255, 255)


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------- 音声(VOICEVOX エンジン・青山龍星・0.90) ----------------
def speaker_id() -> int:
    from .env_check import ensure_voicevox
    if not ensure_voicevox():
        raise RuntimeError("VOICEVOX エンジンを起動できません(python -m pipeline.env_check で確認)")
    sp = requests.get(VV + "/speakers", timeout=10).json()
    return next(s["id"] for p in sp if p["name"] == "青山龍星" for s in p["styles"] if s["name"] == "ノーマル")


def tts(text: str, sid: int, readings: dict) -> np.ndarray:
    t = text
    for k in sorted(readings, key=len, reverse=True):
        t = t.replace(k, readings[k])
    t = re.sub(r"[「」『』【】]", "", t)
    q = requests.post(VV + "/audio_query", params={"text": t, "speaker": sid}, timeout=60).json()
    q["speedScale"] = SPEED
    q["outputSamplingRate"] = 48000
    q["prePhonemeLength"] = 0.05
    q["postPhonemeLength"] = 0.12
    w = requests.post(VV + "/synthesis", params={"speaker": sid}, json=q, timeout=300).content
    with wave.open(io.BytesIO(w)) as f:
        x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
        ch = f.getnchannels()
    return x.reshape(-1, ch).mean(1) if ch > 1 else x


# ---------------- 字幕 ----------------
def _split_long(u: str, line: int) -> list[str]:
    """長い文節を単語の切れ目で line 字以内に分ける。かっこ・句読点・小書き文字・数字の途中では切らない。"""
    import pyopenjtalk
    import unicodedata
    words, pos = [], 0
    for w in pyopenjtalk.run_frontend(u):
        t = w["string"]
        n = len(t)
        if unicodedata.normalize("NFKC", u[pos:pos + n]) != unicodedata.normalize("NFKC", t):
            return [u]  # 原文と位置合わせできない時は分けない
        words.append(u[pos:pos + n])
        pos += n
    if pos < len(u):
        words.append(u[pos:])
    out, cur = [], ""
    for w in words:
        stick = w[:1] in "」』…、，。ぁぃぅぇぉっゃゅょァィゥェォッャュョー" or (cur[-1:] in "「『") or (cur[-1:].isdigit() and w[:1].isdigit())
        if cur and not stick and len(cur + w) > line:
            out.append(cur)
            cur = w
        else:
            cur += w
    if cur:
        out.append(cur)
    # 1〜2字だけの断片は前につなぐ
    merged = []
    for x in out:
        if merged and len(x) <= 2:
            merged[-1] += x
        else:
            merged.append(x)
    return merged


def _bunsetsu_q(text: str) -> list[str]:
    """かぎかっこ・省略記号を含む文も文節に分ける(解析器はかっこで始まる文を1つの塊にしてしまうため、
    かっこを外して分けてから元の位置に戻す。開きかっこは次の文節、閉じかっこ・…は前の文節に付ける)。"""
    from .subtitles import bunsetsu
    if not text:
        return []
    marks = "「」『』…"
    clean = "".join(c for c in text if c not in marks)
    units = bunsetsu(clean) if clean else []
    out, k, used = [], 0, 0
    pending = ""
    for c in text:
        if c in "「『":
            if used and out:  # 文節の途中のかっこはその文節に付ける
                out[-1] += c
            else:
                pending += c
            continue
        if c in "」』…":
            if out:
                out[-1] += c
            else:
                pending += c
            continue
        if k < len(units) and used == 0:
            out.append(pending)
            pending = ""
        out[-1] += c
        used += 1
        if k < len(units) and used >= len(units[k]):
            k += 1
            used = 0
    if pending:
        out.append(pending)
    return [u for u in out if u]


def split_sub(text: str, line: int) -> list[list[str]]:
    """全文を、1行 line 字以内・最大2行の字幕に分ける。
    文節(言葉のまとまり)の途中では改行しない。数字と単位(「11月17日」など)も分けない。
    1つの文節が line 字を超える時だけ、その行は書き出し時に自動で縮小される。"""
    units = []
    for u in _bunsetsu_q(text):
        if units and ((units[-1][-1:].isdigit() and (u[:1].isdigit() or u[:1] in "月日年時分歳回人周%％"))
                      or u[:1] in "、。ぁぃぅぇぉっゃゅょァィゥェォッャュョー」』）"):
            units[-1] += u  # 数字の途中・単位・句読点・小書き文字の前では切らない
        else:
            units.append(u)
    fixed = []
    for u in units:  # 「そして11月17日、」のように長くなった塊は、数字の前の言葉を切り離す
        m = re.match(r"^(\D{2,}?)(\d.*)$", u)
        if len(u) > line and m:
            fixed += [m.group(1), m.group(2)]
        else:
            fixed.append(u)
    units = []
    for u in fixed:  # 1つの文節が1行に収まらない時は、単語の切れ目で分ける(字幕を縮めないため)
        units += _split_long(u, line) if len(u) > line + 1 else [u]
    lines, cur = [], ""
    for u in units:
        if cur and (len(cur + u) > line or cur.endswith("。")):
            lines.append(cur)
            cur = u
        else:
            cur += u
    if cur:
        lines.append(cur)
    out, i = [], 0
    while i < len(lines):
        a = re.sub(r"。$", "", lines[i])
        if i + 1 < len(lines) and not lines[i].endswith("。"):
            out.append([a, re.sub(r"。$", "", lines[i + 1])])
            i += 2
        else:
            out.append([a])
            i += 1
    return out


def ass_time(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def write_ass(path: Path, subs: list[dict], sp: dict):
    W, H = sp["W"], sp["H"]
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans JP,{sp['sub_size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,9,2,5,30,30,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for s in subs:
        # 文字は最大限大きく。ただし最長の行が画面幅(左右30pxと縁取りを除く)に収まらない時だけ縮める
        # 実際の文字幅で測り、はみ出す時だけ縮める(かっこ・読点は幅が狭いので字数より正確)
        from PIL import ImageFont
        _f = ImageFont.truetype(str(next(Path("/usr/local/share/fonts").rglob("NotoSansJP-Bold.ttf"))), sp["sub_size"])
        widest = max(_f.getlength(l) for l in s["lines"])
        fs = min(sp["sub_size"], int((W - 60 - 18) * sp["sub_size"] / max(1.0, widest)))
        ev.append(f"Dialogue: 0,{ass_time(s['start'])},{ass_time(s['end'])},Sub,,0,0,0,,"
                  f"{{\\an5\\pos({W // 2},{int(H * sp['sub_y'])})\\fs{fs}}}" + "\\N".join(s["lines"]))
    path.write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")


# ---------------- 画像の切り抜き・動き・表示 ----------------
_CASC = None


def faces(img):
    global _CASC
    if _CASC is None:
        _CASC = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sc = min(1.0, 1000 / max(g.shape))
    f = _CASC.detectMultiScale(cv2.resize(g, None, fx=sc, fy=sc), 1.1, 6, minSize=(24, 24))
    return [tuple(int(v / sc) for v in x) for x in f]


LAST_BAND = None  # 直前の plate がぼかし背景+帯の時: (帯の上端, 帯の高さ, 写真, 背景)


def plate(img_path: str, crop: str, W: int, H: int, Z: float = 1.12, sub_y: float = 0.70,
          keep_all: bool = False, main=None) -> tuple[np.ndarray, tuple]:
    """変形なしで W*Z x H*Z の素材を作る。顔は字幕帯より上に置く。全体が入らない横長写真はぼかし背景+全体表示。"""
    global LAST_BAND
    LAST_BAND = None
    img = cv2.imread(img_path)
    ih, iw = img.shape[:2]
    PW, PH = int(W * Z), int(H * Z)
    fs = faces(img)
    ar = PW / PH
    if main is None and fs and not keep_all:  # focus.json 未登録: 最大の顔を主役とみなす(当てっこ係の登録が優先)
        x, y, w, h = max(fs, key=lambda f: f[2] * f[3])
        main = ((x + w / 2) / iw, (y + h / 2) / ih)
    if main:  # 主役の位置(focus.json・目視登録)を基準にする
        cx, cy = main[0] * iw, main[1] * ih
        hit = [f for f in fs if f[0] <= cx <= f[0] + f[2] and f[1] <= cy <= f[1] + f[3]]
        fh = hit[0][3] if hit else ih * 0.10
        x0 = x1 = cx; y0 = y1 = cy
        fs = fs or [(int(cx), int(cy), 1, 1)]
    elif fs:
        x0 = min(f[0] for f in fs); x1 = max(f[0] + f[2] for f in fs)
        y0 = min(f[1] for f in fs); y1 = max(f[1] + f[3] for f in fs)
        fh = max(f[3] for f in fs)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    else:
        x0 = x1 = cx = iw / 2; cy = ih * 0.4; fh = ih * 0.15; y0 = y1 = cy
    if crop == "顔の寄り" and fs:
        ch = min(ih, fh / 0.18)
        if main is not None:  # 主役の位置が登録済み(複数名なら中心): 写真の高さの55%まで寄る(拡大しすぎて粗くしない)
            ch = max(ch, ih * 0.55)
    elif crop == "手元・装い" and fs:
        ch = min(ih, fh / 0.10)
        cy = cy + fh * 2.2
    else:
        ch = ih
    cw = ch * ar
    if cw > iw:
        cw = iw
        ch = cw / ar
    target_face_y = 0.30 if W < H else 0.38
    if not keep_all and ((x1 - x0) <= cw * 0.9 or iw / ih <= ar * 1.3):
        left = min(max(cx - cw / 2, 0), iw - cw)
        top = min(max(cy - target_face_y * ch, 0), ih - ch)
        out = cv2.resize(img[int(top):int(top + ch), int(left):int(left + cw)], (PW, PH), interpolation=cv2.INTER_LANCZOS4)
        focus = ((cx - left) * PW / cw, (cy - top) * PH / ch)
    else:  # 横長で人物が入りきらない → ぼかし背景 + 全体
        bg = cv2.resize(img, (int(iw * PH / ih), PH))
        bx = (bg.shape[1] - PW) // 2
        bg = cv2.GaussianBlur(bg[:, bx:bx + PW], (0, 0), 25) * 0.55
        fw = PW
        fh2 = int(ih * fw / iw)
        fg = cv2.resize(img, (fw, fh2), interpolation=cv2.INTER_LANCZOS4)
        top = max(int(PH * (0.40 if W < H else 0.45) - fh2 / 2), 0)
        out = bg.astype(np.uint8)
        # 主役が画面の中央に来るよう写真を左右にずらす(はみ出した側はぼかし背景)
        sx = 0  # 荒木指示 2026-11-22: 写真を横にずらさない(隙間を作らない)
        a0, a1 = max(0, sx), min(PW, sx + fw)
        out[top:top + fh2, a0:a1] = fg[:PH - top, a0 - sx:a1 - sx]
        focus = (cx * fw / iw + sx, cy * fw / iw + top)
        LAST_BAND = (top, min(fh2, PH - top), fg[:PH - top], out.copy())
    return out, focus


def _motion_z(motion: str, e: float) -> float:
    if motion == "ゆっくり縮小":
        return 1.07 - 0.05 * e
    if motion in ("左へパン", "右へパン"):
        return 1.05
    return 1.02 + 0.05 * e


def _band_frames(band, focus, n: int, W: int, H: int, motion: str):
    top, bh, fg, bg = band
    PH, PW = bg.shape[:2]
    fw = fg.shape[1]
    fx, fy = focus[0], focus[1] - top
    for k in range(n):
        u = k / max(1, n - 1)
        e = 0.5 - 0.5 * math.cos(math.pi * u)
        z = _motion_z(motion, e)
        ww, wh = fw / z, bh / z
        cx = fx + (-1 if motion == "左へパン" else 1 if motion == "右へパン" else 0) * ww * 0.03 * e
        cx = min(max(cx, ww / 2), fw - ww / 2)
        cy = min(max(fy, wh / 2), bh - wh / 2)
        x0, y0 = cx - ww / 2, cy - wh / 2
        M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
        inner = cv2.warpAffine(fg[:bh], M, (fw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        fr = bg.copy()
        fr[top:top + bh, :fw] = inner
        yield cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)


def frames_for(pl: np.ndarray, focus, n: int, W: int, H: int, motion: str, band=None):
    """控えめな動き(荒木指示 2026-11-22): 少しのズーム(2〜7%)とごく小さなパン。
    窓は常に素材の内側に収め、写真の外(隙間・引き伸ばし)を見せない。主役の位置を基準にする。
    ぼかし背景+写真の帯の時は、帯の位置と大きさを固定し、帯の内側だけを動かす(帯の端が動いて見えないように)。"""
    if band is not None:
        yield from _band_frames(band, focus, n, W, H, motion)
        return
    PH, PW = pl.shape[:2]
    Z = PW / W
    for k in range(n):
        u = k / max(1, n - 1)
        e = 0.5 - 0.5 * math.cos(math.pi * u)
        if motion == "ゆっくり縮小":
            z = 1.07 - 0.05 * e
        elif motion in ("左へパン", "右へパン"):
            z = 1.05
        else:
            z = 1.02 + 0.05 * e
        ww = PW / Z / z
        wh = PH / Z / z
        cx = focus[0]
        if motion == "左へパン":
            cx = focus[0] - ww * 0.03 * e
        elif motion == "右へパン":
            cx = focus[0] + ww * 0.03 * e
        cy = focus[1] + wh * 0.12
        cx = min(max(cx, ww / 2), PW - ww / 2)
        cy = min(max(cy, wh / 2), PH - wh / 2)
        a = ww / W
        M = np.float32([[1 / a, 0, -(cx - ww / 2) / a], [0, 1 / a, -(cy - wh / 2) / a]])
        yield cv2.warpAffine(pl, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


VIDEO_EXT = (".mp4", ".mov", ".webm", ".m4v", ".mkv")


def is_video(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXT


def video_frames(path: str, start: float, n: int, W: int, H: int):
    """実写映像(第4-2章): 指定区間を30fpsで読み、歪めずに画面いっぱいへ切り抜く。短ければ区間の頭に戻る。"""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    first = int(start * fps)
    cache, last = {}, None
    for k in range(n):
        idx = first + int(k * fps / 30.0)
        if total and idx >= total:
            idx = first + (idx - first) % max(1, total - first)
        if idx not in cache:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, fr = cap.read()
            cache = {idx: fr if ok else last}
        fr = cache[idx]
        if fr is None:
            fr = np.zeros((H, W, 3), np.uint8)
        h, w = fr.shape[:2]
        s = max(W / w, H / h)
        fr = cv2.resize(fr, (int(w * s + 0.5), int(h * s + 0.5)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        y0, x0 = (fr.shape[0] - H) // 2, (fr.shape[1] - W) // 2
        last = fr[y0:y0 + H, x0:x0 + W]
        yield last
    cap.release()


def overlay(W: int, H: int, labels: list[tuple[str, int]], caption: str, credit: str) -> np.ndarray:
    """人物名(人物ごと)・撮影の日付/場所/行事(隅に小さく)・音声クレジット。RGBA。"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    vert = W < H
    fs_name = 32 if vert else 30  # 荒木指示 2026-11-21: 人物名・撮影情報は極力小さく(字幕を主役にする)
    for text, cx in labels:
        f = font(FONT_B, fs_name)
        tw = d.textlength(text, font=f)
        x = min(max(cx - tw / 2, 24), W - tw - 24)
        y = int(H * (0.13 if vert else 0.06))
        d.rounded_rectangle((x - 10, y - 5, x + tw + 10, y + fs_name + 12), 8, fill=NAVY + (200,), outline=GOLD + (255,), width=2)
        d.text((x, y), text, font=f, fill=WHITE)
    if caption:
        # 撮影情報: 画面からはみ出さないよう、長い時は少し縮め、それでも入らなければ2行に折り返す
        size = 22 if vert else 20
        maxw = W - 60
        f = font(FONT_R, size)
        while d.textlength(caption, font=f) > maxw and size > 18:
            size -= 1
            f = font(FONT_R, size)
        lines = [caption]
        if d.textlength(caption, font=f) > maxw:
            lines, cur = [], ""
            for ch in caption:
                if d.textlength(cur + ch, font=f) > maxw:
                    lines.append(cur)
                    cur = ch
                else:
                    cur += ch
            lines.append(cur)
            lines = lines[:3]
        tw = max(d.textlength(l, font=f) for l in lines)
        lh = size + 9
        x, y = 24, int(H * (0.165 if vert else 0.16))
        if not vert:
            x, y = W - tw - 40, int(H * 0.06) + 10
        d.rounded_rectangle((x - 6, y - 3, x + tw + 6, y + lh * len(lines)), 6, fill=(0, 0, 0, 140))
        for i, l in enumerate(lines):
            d.text((x, y + i * lh), l, font=f, fill=WHITE)
    f = font(FONT_R, 20)
    tw = d.textlength(credit, font=f)
    d.text((W - tw - 24, int(H * 0.035) if vert else H - 44), credit, font=f, fill=(255, 255, 255, 200),
           stroke_width=2, stroke_fill=(0, 0, 0, 180))
    return np.array(im)


def blend(fr: np.ndarray, ov: np.ndarray) -> np.ndarray:
    a = ov[..., 3:4].astype(np.float32) / 255
    rgb = ov[..., :3][..., ::-1].astype(np.float32)
    return (fr.astype(np.float32) * (1 - a) + rgb * a).astype(np.uint8)


# ---------------- 本体 ----------------
def build(project: str, kind: str = "縦型") -> Path:
    sp = SPEC[kind]
    W, H = sp["W"], sp["H"]
    pdir = ROOT / "projects" / project
    scenes = load_json(pdir / "scenes.json")
    ledger = {r["番号"]: r for r in csv.DictReader(open(pdir / "ledger.csv", encoding="utf-8"))}
    readings = {k: v for k, v in (load_json(ROOT / "config" / "reading_dict.json", {}) or {}).items() if not k.startswith("_")}
    readings.update(load_json(pdir / "readings.json", {}) or {})
    mains = {k: v for k, v in (load_json(pdir / "focus.json", {}) or {}).items() if not k.startswith("_")}
    sid = speaker_id()
    out_dir = pdir / "output"
    out_dir.mkdir(exist_ok=True)
    # 1) 音声(場面ごとに合成・実測)
    sr = 48000
    gap = 0.12
    t = 0.25
    pieces = [np.zeros(int(sr * t), np.float32)]
    for s in scenes:
        x = tts(s["narration"], sid, readings)
        s["start_sec"] = round(t, 3)
        t += len(x) / sr
        pieces += [x, np.zeros(int(sr * gap), np.float32)]
        t += gap
        s["end_sec"] = round(t, 3)
    pieces.append(np.zeros(int(sr * 0.6), np.float32))
    total = t + 0.6
    narr = np.concatenate(pieces)
    narr = narr / (np.abs(narr).max() + 1e-9) * 0.89
    wav = out_dir / "narration.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((narr * 32767).astype(np.int16).tobytes())
    # 2) 場面を切替間隔の上限で分割(同じ画像なら切り抜き/動きを変える)
    shots = []
    crops = ["全身", "顔の寄り", "手元・装い"]
    motions = ["ゆっくり拡大", "左へパン", "ゆっくり縮小", "右へパン"]
    for i, s in enumerate(scenes):
        a = 0.0 if i == 0 else s["start_sec"]
        b = scenes[i + 1]["start_sec"] if i + 1 < len(scenes) else total
        imgs = s.get("images") or ([s["image"]] if s.get("image") else [])
        n = max(1, math.ceil((b - a) / sp["cut"][1]))
        if kind == "縦型" and imgs and len(imgs) < n:
            # ショートは同じ写真を2回使わない: 写真の枚数までカットを減らす(1カットは最長 max_show 秒)
            n = max(len(imgs), math.ceil((b - a) / sp["max_show"]))
        off = 0
        if imgs and shots and len(imgs) > 1 and imgs[0] == shots[-1]["image"]:
            off = 1  # 第4-2章: 隣り合うカットに同じ画像を使わない
        for k in range(n):
            img = imgs[(k + off) % len(imgs)] if imgs else None
            c0 = s.get("crop", "全身")
            if k == 0 or c0 not in crops:
                crop = c0  # 「全体」は人物名と画面を一致させるため切り替えない
            elif len(imgs) > 1 and img != imgs[off % len(imgs)]:
                crop = c0  # 別の画像に切り替わるときは指定どおりの切り抜き
            else:
                crop = crops[(crops.index(c0) + k) % 3]
            motion = s.get("motion", "ゆっくり拡大") if k == 0 else motions[(motions.index(s.get("motion", "ゆっくり拡大")) + k) % 4]
            shots.append({"scene": s["scene"], "start": a + (b - a) * k / n, "end": a + (b - a) * (k + 1) / n,
                          "image": img, "crop": crop, "motion": motion, "compare": s.get("compare"),
                          # 写真ごとの人物名(例: 人物の写らない会場写真は "")。無ければ場面の人物名
                          "person_label": (s.get("labels") or {}).get(img, s.get("person_label", "")),
                          "caption": (s.get("captions") or {}).get(img) or s.get("caption", ""),
                          "clip_start": float((s.get("clip") or {}).get("start", 0)) + (b - a) * k / n,
                          "diagram": bool(s.get("diagram"))})
    # 3) 映像
    raw = out_dir / "video_nosub.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "30",
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(raw)],
                          stdin=subprocess.PIPE)
    credit = "VOICEVOX:青山龍星"
    fcount = 0
    for sh in shots:
        n = int(round(sh["end"] * 30)) - fcount
        if n <= 0:
            continue
        if sh["compare"]:
            ids, labs = sh["compare"]["images"], sh["compare"]["labels"]
            half = W // 2 - 6
            subs = []
            for j, iid in enumerate(ids[:2]):
                pl, fo = plate(str(ROOT / ledger[iid]["ファイル名"]), sh["crop"], half, H, main=mains.get(iid))
                subs.append(list(frames_for(pl, fo, n, half, H, sh["motion"], band=LAST_BAND)))
            sh["media"] = "写真"
            ov = overlay(W, H, [(labs[0], W // 4), (labs[1], 3 * W // 4)], sh["caption"], credit)
            for k in range(n):
                fr = np.full((H, W, 3), NAVY[::-1], np.uint8)
                fr[:, :half] = subs[0][k]
                fr[:, W - half:] = subs[1][k]
                ff.stdin.write(blend(fr, ov).tobytes())
        else:
            # 人物名が複数(「両陛下」「・」区切り)の場面は写真全体を見せ、名前と画面を一致させる
            # 写真全体を見せるのは「全体」指定の時と、複数名を「全身」で見せる時だけ(「顔の寄り」は主役の位置を中心に寄る)
            many = ("両" in sh["person_label"] or "・" in sh["person_label"] or "、" in sh["person_label"])
            # 複数名の場面は、お一人ずつのお顔が切れないよう常に写真全体を見せる(主役の中心を画面中央へ)。
            # 引きすぎてお顔が見分けられない写真は、当てっこ係のコマ点検で差し替える
            multi = sh["crop"] == "全体" or many
            src = str(ROOT / ledger[sh["image"]]["ファイル名"])
            labels = [(sh["person_label"], W // 2)] if sh["person_label"] else []
            ov = overlay(W, H, labels, sh["caption"], credit)
            if is_video(src):
                sh["media"] = "映像"
                gen = video_frames(src, sh["clip_start"], n, W, H)
            else:
                sh["media"] = "写真"
                pl, fo = plate(src, sh["crop"], W, H, keep_all=multi, main=mains.get(sh["image"]))
                gen = frames_for(pl, fo, n, W, H, sh["motion"], band=LAST_BAND)
            for fr in gen:
                ff.stdin.write(blend(fr, ov).tobytes())
        fcount += n
    ff.stdin.close()
    ff.wait()
    # 4) 字幕(全文・1行の目安字数・最大2行)
    subs = []
    from .tts import mora_count
    for s in scenes:
        chunks = s.get("subtitle_lines") or split_sub(s["narration"], sp["line"])  # 指定があれば手動の改行を優先
        if s.get("subtitle_lines"):
            flat = re.sub(r"[。\s]", "", "".join("".join(c) for c in chunks))
            assert flat == re.sub(r"[。\s]", "", s["narration"]), f"{s['scene']}: subtitle_lines がナレーションと一致しない"
        ms = [max(1, mora_count("".join(c))) for c in chunks]
        a, b = s["start_sec"], s["end_sec"] - 0.06
        acc = a
        s["subtitle"] = []
        for c, m in zip(chunks, ms):
            e = acc + (b - a) * m / sum(ms)
            subs.append({"start": acc, "end": e, "lines": c})
            s["subtitle"].append(c)
            acc = e
    ass = out_dir / "subtitles.ass"
    write_ass(ass, subs, sp)
    # 5) 合成(BGM UNL1337 をナレーションより約21dB下げる)
    env = load_json(pdir / "env_check.json", {}) or {}
    bgm = ROOT / (env.get("bgm") or "assets/bgm/UNL1337.wav")
    final = out_dir / f"{project}_{kind}_internal.mp4"
    assp = str(ass).replace(":", "\\:")
    fc = (f"[0:v]ass='{assp}':fontsdir={FONT_DIR},format=yuv420p[v];"
          f"[1:a]aresample=48000,apad=pad_dur=4,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[n];"
          f"[2:a]aresample=48000,atrim=0:{total + 4:.2f},loudnorm=I=-37:TP=-9:LRA=11,aresample=48000,afade=t=in:d=1,afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5[b];"
          f"[n][b]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.70:level=disabled,atrim=0:{total:.3f}[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(wav), "-stream_loop", "-1", "-i", str(bgm),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-r", "30", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(final)],
                   check=True)
    # 6) scenes.json に実測の時刻と字幕を記入
    for s in scenes:
        s["start"] = f"{int(s['start_sec'] // 60)}:{s['start_sec'] % 60:05.2f}"
        s["end"] = f"{int(s['end_sec'] // 60)}:{s['end_sec'] % 60:05.2f}"
    save_json(pdir / "scenes.json", scenes)
    save_json(out_dir / "shots.json", shots)
    save_json(out_dir / "render_info.json", {"kind": kind, "speaker_id": sid, "speed": SPEED, "duration": round(total, 3),
                                             "font": FONT_B, "bgm": str(bgm.relative_to(ROOT)), "bgm_gain_db": -37})
    print(f"書き出し: {final} ({total:.2f}秒, {len(shots)}カット)")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--kind", default="縦型", choices=["縦型", "横型"])
    a = ap.parse_args()
    build(a.project, a.kind)
