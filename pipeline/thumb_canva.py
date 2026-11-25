"""デザイナー(重要)の道具: 表紙(Canva)の準備と仕上げ。本書第5章・第9章②。

  python -m pipeline.thumb_canva --project P --prepare     # 中心画像の切り抜き + Canva操作計画(canva_plan.json)
  python -m pipeline.thumb_canva --project P --fetch URL   # Canvaの書き出しURLから thumb/thumb_canva.png を保存して寸法を検査

入力: publish.yaml の thumb(upper/middle/lower/center_image・任意で second_image)、focus.json(主役の位置)、ledger.csv
型: 写真1枚 = S-A(枠 936×680・y545)/ 写真2枚 = S-B(左右 446×490・y560)。中段は1行に収まる文字サイズを計算する。
Canvaの操作(デザイナー(重要)が MCP で実行): テンプレート DAHatUQFKSI を copy-design → read-design(open_transaction)で
要素を文字で特定(「導入」=上段、「最大の訴求」=中段、「疑問・補足」=下段、写真枠=画像の shape)→ create-upload-url と curl で写真を送る →
edit-design(update_fill・replace_text・format_text・resize/position)→ commit → export-design(png 1080×1920)→ --fetch。
テンプレート本体は変更しない。赤は使わない。人物の顔・表情は加工しない(切り抜きのみ)。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import requests
import yaml
from PIL import Image

from .common import ROOT, load_json, save_json

TEMPLATE = "DAHatUQFKSI"
LAYOUT = {
    "S-A": {"frames": [{"left": 72, "top": 545, "width": 936, "height": 680}], "middle_top": 1260, "lower_top": 1400},
    "S-B": {"frames": [{"left": 72, "top": 560, "width": 446, "height": 490}, {"left": 542, "top": 560, "width": 446, "height": 490}],
            "middle_top": 1090, "lower_top": 1240},
}
MIDDLE_W = 980  # 中段の文字枠(左50〜右1030)

# 表紙パターンA(バランス型・第9章②)の配置。荒木指示 2026-11-25「下段のタイトルが下部過ぎる」により、
# 下段は中段のすぐ下(中段の文字枠の下端から LOWER_GAP)に置き、最下部(旧 y1753)に離さない。
# 全体を縦の中央寄りに(ロゴ上端 y154 と下段下端の下の余白がほぼ同じ)。KB-20261123-03〜06・KB-20261125-02〜04 の
# 既存の canva_plan.json は変えず、PATTERN_A_FROM 以降の新しい制作番号から plan に "pattern_A" を出す。
PATTERN_A_FROM = "KB-20261125-05"
LOWER_GAP = 70  # 中段の文字枠の下端 → 下段の文字枠の上端(約60〜90pxの範囲)
PATTERN_A = {"logo_top": 154, "upper_top": 256, "line1_top": 399,
             "photo": {"left": 90, "top": 450, "width": 900, "height": 880},
             "caption_top": 1346, "line2_top": 1419, "middle_top": 1479, "text_left": 20, "text_width": 1040}


def pattern_a(middle_size: int, lower_size: int = 74) -> dict:
    """パターンAの各要素の y 座標。下段 = 中段の下端 + LOWER_GAP(文字枠の高さ = 文字サイズ × 約1.2)。"""
    A = dict(PATTERN_A)
    size = min(108, middle_size)
    middle_bottom = A["middle_top"] + round(size * 1.2)
    lower_top = middle_bottom + LOWER_GAP
    A.update({"middle_font_size": size, "lower_font_size": lower_size, "lower_top": lower_top,
              "lower_bottom": lower_top + round(lower_size * 1.2),
              "note": "下段は中段のすぐ下に置き、最下部に離さない(荒木指示 2026-11-25)。区切り線・写真・撮影情報も上の座標へ"})
    return A


def crop(src: Path, focus, ar: float, out: Path, fill: float = 0.80):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    fx, fy = focus or (0.5, 0.4)
    ch = H * fill
    cw = ch * ar
    if cw > W:
        cw, ch = W, W / ar
    left = min(max(fx * W - cw / 2, 0), W - cw)
    top = min(max(fy * H - ch * 0.25, 0), H - ch)
    im.crop((int(left), int(top), int(left + cw), int(top + ch))).save(out, quality=95)
    return out


def prepare(project: str) -> Path:
    pdir = ROOT / "projects" / project
    pub = yaml.safe_load((pdir / "publish.yaml").read_text(encoding="utf-8"))
    th = pub["thumb"]
    imgs = [th["center_image"]] + ([th["second_image"]] if th.get("second_image") else [])
    layout = "S-B" if len(imgs) == 2 else "S-A"
    L = LAYOUT[layout]
    ledger = {r["番号"]: r for r in csv.DictReader(open(pdir / "ledger.csv", encoding="utf-8"))}
    fj = load_json(pdir / "focus.json", {}) or {}
    tdir = pdir / "thumb"
    tdir.mkdir(exist_ok=True)
    photos = []
    for i, fr in zip(imgs, L["frames"]):
        out = crop(ROOT / ledger[i]["ファイル名"], fj.get(i), fr["width"] / fr["height"], tdir / f"{i}_{layout}.jpg",
                   fill=0.80 if layout == "S-A" else 0.72)
        photos.append({"ledger": i, "file": str(out.relative_to(ROOT)), "frame": fr,
                       "alt": f"{ledger[i]['写っている人物']} {ledger[i]['撮影日・場所・行事'][:10]}({ledger[i]['掲載サイト名']})"})
    n = len(th["middle"].replace(" ", ""))
    middle_size = max(60, min(132, int(MIDDLE_W / max(1, n) * 0.92)))
    plan = {"template": TEMPLATE, "layout": layout, "photos": photos,
            "texts": {"upper": th["upper"], "middle": th["middle"], "lower": th["lower"]},
            "middle": {"font_size": middle_size, "left": 50, "top": L["middle_top"], "width": MIDDLE_W},
            "lower": {"left": 96, "top": L["lower_top"]},
            "steps": [
                "copy-design(TEMPLATE)→ 新しい design_id を thumb.yaml の canva に記録",
                "read-design(open_transaction)で要素を特定: 文字『導入』=上段 / 『最大の訴求』=中段 / 『疑問・補足』=下段 / 画像 shape(left72)=左枠, (left542)=右枠",
                "写真ごとに create-upload-url → curl -X POST -H 'Content-Type: application/octet-stream' --data-binary @file → mediaId",
                "S-A: 右枠を delete_element、左枠を resize_element(936×680)・position_element(72,545)",
                "update_fill(各枠, mediaId, alt)・replace_text(上段/中段/下段)・format_text(中段 font_size)・resize_element(中段 width)・position_element(中段・下段)",
                "サムネイルで顔が枠に収まり、中段が1行、文字同士が重ならないことを確認 → commit",
                "export-design(png, 1080×1920)→ python -m pipeline.thumb_canva --project P --fetch <URL>",
            ]}
    if project >= PATTERN_A_FROM:
        plan["pattern_A"] = pattern_a(middle_size)
        plan["steps"].insert(-2, "パターンA: pattern_A の座標で position_element(ロゴ・上段・金の細線2本・写真・撮影情報・中段・下段)。"
                                 "下段は中段のすぐ下(lower_top)。最下部に置かない")
    path = save_json(tdir / "canva_plan.json", plan)
    ty = pdir / "thumb.yaml"
    cur = yaml.safe_load(ty.read_text(encoding="utf-8")) if ty.exists() else {}
    cur.update({"layout": layout, "texts": plan["texts"], "photos": [{"ledger": p["ledger"]} for p in photos]})
    ty.write_text(yaml.safe_dump(cur, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=1))
    return path


def fetch(project: str, url: str) -> bool:
    pdir = ROOT / "projects" / project
    out = pdir / "thumb" / "thumb_canva.png"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)
    im = Image.open(out)
    ok = im.size == (1080, 1920)
    # 赤を使わない(本書第5章): 文字・背景の色に強い赤がないか、写真枠の外側だけを簡易検査
    px = im.convert("RGB").resize((108, 192))
    reds = sum(1 for y in list(range(0, 50)) + list(range(130, 192)) for x in range(108)
               if (lambda c: c[0] > 180 and c[1] < 80 and c[2] < 80)(px.getpixel((x, y))))
    print(f"保存: {out} {im.size} 赤の画素(写真枠の外) {reds}")
    return ok and reds == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--fetch")
    a = ap.parse_args()
    if a.prepare:
        prepare(a.project)
    if a.fetch:
        sys.exit(0 if fetch(a.project, a.fetch) else 1)
