"""分析係の道具(公開後 G7): CTRの実測を記録し、目標20%との差とタイトルの型ごとの傾向を出す。

  python -m pipeline.ctr_log --project P --video-id XXXX --ctr 12.3 --impressions 15000 --views 4200
  python -m pipeline.ctr_log --report     # data/ctr_log.csv の全件から型ごとの平均CTRを出す

数値は分析係が vidIQ(vidiq_video_stats / vidiq_channel_analytics_extended 等)または YouTube Studio から取る。
取れない値は 0 のまま記録せず、取れた値だけ入れる。タイトルの型は publish.yaml の title から自動で判定する。
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path

import yaml

from .common import ROOT

LOG = ROOT / "data" / "ctr_log.csv"
COLS = ["記録日", "制作番号", "動画ID", "タイトル", "型", "CTR%", "インプレッション", "再生数", "目標20%との差"]
TARGET = 20.0


def title_type(t: str) -> str:
    kinds = []
    if t.startswith("【"):
        kinds.append("【導入】")
    if re.search(r"[？?]", t):
        kinds.append("疑問文")
    if re.search(r"なぜ|理由|とは", t):
        kinds.append("謎かけ")
    if re.search(r"記録|宮内庁|公式", t):
        kinds.append("根拠の示唆")
    return "+".join(kinds) or "その他"


def add(project: str, video_id: str, ctr: float, impressions: int, views: int):
    pub = yaml.safe_load((ROOT / "projects" / project / "publish.yaml").read_text(encoding="utf-8"))
    LOG.parent.mkdir(exist_ok=True)
    new = not LOG.exists()
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if new:
            w.writeheader()
        w.writerow({"記録日": dt.date.today().isoformat(), "制作番号": project, "動画ID": video_id, "タイトル": pub["title"],
                    "型": title_type(pub["title"]), "CTR%": ctr, "インプレッション": impressions or "", "再生数": views or "",
                    "目標20%との差": round(ctr - TARGET, 1)})
    print(f"記録: {project} CTR {ctr}%(目標{TARGET}%との差 {ctr - TARGET:+.1f})")


def report():
    rows = list(csv.DictReader(open(LOG, encoding="utf-8"))) if LOG.exists() else []
    by = {}
    for r in rows:
        by.setdefault(r["型"], []).append(float(r["CTR%"]))
    lines = ["# CTRの記録(目標20%)", "", "| 型 | 本数 | 平均CTR | 目標以上 |", "|---|---|---|---|"]
    for k, v in sorted(by.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        lines.append(f"| {k} | {len(v)} | {sum(v) / len(v):.1f}% | {sum(1 for x in v if x >= TARGET)} |")
    (ROOT / "data" / "ctr_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--video-id")
    ap.add_argument("--ctr", type=float)
    ap.add_argument("--impressions", type=int, default=0)
    ap.add_argument("--views", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.project and a.ctr is not None:
        add(a.project, a.video_id or "", a.ctr, a.impressions, a.views)
    if a.report or (a.project and a.ctr is not None):
        report()
