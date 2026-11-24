"""当てっこ係の道具: 主役の位置(focus.json)の登録と、要目視写真の照合。

  python -m pipeline.focus_sheet --project P --sheet            # 場面で使う写真の点検シート(格子つき)を作る
  python -m pipeline.focus_sheet --project P --set A001=0.33,0.39 A027=0.41,0.28   # 主役の顔の中心(幅・高さの割合)
  python -m pipeline.focus_sheet --project P --verify A033 A035 # 要目視の写真を、写真を見て照合済みにする
  python -m pipeline.focus_sheet --project P --check            # 未登録・要目視の残りを一覧(残りがあれば終了コード1)

点検シート: projects/<P>/output/focus/sheet_XX.jpg。写真ごとに 10×10 の格子(列 0〜9 = 幅の 0.05〜0.95、行 0〜9 = 高さ)と、
顔検出の枠(番号と中心座標)を描く。係はシートを見て、人物名が1人の場面はその方のお顔、複数名の場面は表示する方々の中心を登録する。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

from .common import ROOT, load_json, save_json
from .rules_render import faces

FONT = "/usr/local/share/fonts/noto-sans-jp/NotoSansJP-Bold.ttf"


def used_images(pdir: Path) -> list[str]:
    out = []
    for s in load_json(pdir / "scenes.json", []) or []:
        for i in (s.get("compare") or {}).get("images") or s.get("images") or [s.get("image")]:
            if i and i not in out:
                out.append(i)
    return out


def ledger(pdir: Path) -> tuple[list[dict], list[str]]:
    with open(pdir / "ledger.csv", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r), r.fieldnames


def labels_for(pdir: Path) -> dict[str, set]:
    lab = {}
    for s in load_json(pdir / "scenes.json", []) or []:
        for i in (s.get("images") or [s.get("image")]):
            if i:
                # 写真ごとの人物名(labels)があればそれを出す(書き出しと同じ。場面の人物名を全写真に付けると、
                # 人物の写らない写真・お一人の写真に別の名前が付いて見える。2026-11-24 当てっこ係の指摘)
                lab.setdefault(i, set()).add((s.get("labels") or {}).get(i, s.get("person_label", "")))
    return lab


def sheet(project: str) -> list[Path]:
    pdir = ROOT / "projects" / project
    rows = {r["番号"]: r for r in ledger(pdir)[0]}
    labs = labels_for(pdir)
    ids = used_images(pdir) or list(rows)
    out = pdir / "output" / "focus"
    out.mkdir(parents=True, exist_ok=True)
    f, fs = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 18)
    W, H, cols = 640, 520, 3
    paths = []
    for k in range(0, len(ids), 6):
        part = ids[k:k + 6]
        S = Image.new("RGB", (W * cols, (H + 70) * ((len(part) + cols - 1) // cols)), "white")
        d = ImageDraw.Draw(S)
        for j, i in enumerate(part):
            r = rows[i]
            img = cv2.imread(str(ROOT / r["ファイル名"]))
            ih, iw = img.shape[:2]
            p = Image.open(ROOT / r["ファイル名"]).convert("RGB").resize((W, H))
            dd = ImageDraw.Draw(p)
            for g in range(1, 10):
                dd.line([(W * g / 10, 0), (W * g / 10, H)], fill=(255, 255, 255), width=1)
                dd.line([(0, H * g / 10), (W, H * g / 10)], fill=(255, 255, 255), width=1)
            for g in range(10):
                dd.text((W * g / 10 + 3, 2), str(g), fill="yellow", font=fs, stroke_width=2, stroke_fill="black")
                dd.text((3, H * g / 10 + 2), str(g), fill="yellow", font=fs, stroke_width=2, stroke_fill="black")
            for n, (x, y, w, h) in enumerate(faces(img)):
                sx, sy = W / iw, H / ih
                dd.rectangle([x * sx, y * sy, (x + w) * sx, (y + h) * sy], outline="cyan", width=3)
                dd.text((x * sx, (y + h) * sy), f"{n}:{(x + w / 2) / iw:.2f},{(y + h / 2) / ih:.2f}", fill="cyan", font=fs,
                        stroke_width=2, stroke_fill="black")
            x0, y0 = (j % cols) * W, (j // cols) * (H + 70)
            S.paste(p, (x0, y0))
            d.text((x0 + 4, y0 + H + 4), f"{i} 名前:{'/'.join(sorted(labs.get(i, []))) or '-'} 確認:{r.get('確認方法', '')}",
                   fill="black", font=fs)
            d.text((x0 + 4, y0 + H + 32), r["確認したキャプション"][:44], fill=(90, 90, 90), font=fs)
        path = out / f"sheet_{k // 6 + 1:02d}.jpg"
        S.save(path, quality=85)
        paths.append(path)
    print("\n".join(map(str, paths)))
    return paths


def set_focus(project: str, items: list[str]):
    pdir = ROOT / "projects" / project
    fp = pdir / "focus.json"
    fj = load_json(fp, {}) or {"_note": "主役の位置(写真の幅・高さに対する割合 x,y)。人物名が1人の場面はその方のお顔、複数名の場面は表示する方々の中心。当てっこ係が点検シートで登録。"}
    for it in items:
        k, v = it.split("=")
        x, y = (float(a) for a in v.split(","))
        assert 0 <= x <= 1 and 0 <= y <= 1, it
        fj[k] = [round(x, 3), round(y, 3)]
    save_json(fp, fj)
    print(f"focus.json: {len(items)}件登録")


def verify(project: str, ids: list[str]):
    pdir = ROOT / "projects" / project
    rows, cols = ledger(pdir)
    n = 0
    for r in rows:
        if r["番号"] in ids and "要目視" in r.get("確認方法", ""):
            r["確認方法"] = "ページ説明文＋目視確認済(当てっこ係)"
            n += 1
    with open(pdir / "ledger.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"目視確認済: {n}件")


def check(project: str) -> bool:
    pdir = ROOT / "projects" / project
    fj = load_json(pdir / "focus.json", {}) or {}
    rows = {r["番号"]: r for r in ledger(pdir)[0]}
    ids = used_images(pdir)
    miss = [i for i in ids if i not in fj]
    pend = [i for i in ids if "要目視" in rows.get(i, {}).get("確認方法", "")]
    print(json.dumps({"未登録の主役位置": miss, "要目視のまま": pend}, ensure_ascii=False))
    return not miss and not pend


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--set", nargs="*")
    ap.add_argument("--verify", nargs="*")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.sheet:
        sheet(a.project)
    if a.set:
        set_focus(a.project, a.set)
    if a.verify:
        verify(a.project, a.verify)
    if a.check:
        sys.exit(0 if check(a.project) else 1)
