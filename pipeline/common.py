"""共通ユーティリティ: パス、設定、ログ、ジョブ管理、ffprobe。"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = _dt.timezone(_dt.timedelta(hours=9))


def now_jst() -> _dt.datetime:
    return _dt.datetime.now(JST)


def load_json(path: Path | str, default=None):
    p = Path(path)
    if not p.exists():
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path | str, data) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return p


def settings() -> dict:
    return load_json(ROOT / "config" / "settings.json")


def style() -> dict:
    """参考動画の分析から得た編集ルール(templates/reference_style.json)。"""
    return load_json(ROOT / "templates" / "reference_style.json")


class Job:
    """1本の動画制作単位。各ステージの入出力パスを集約する。"""

    def __init__(self, job_id: str):
        self.id = job_id
        self.research = ROOT / "research" / job_id
        self.scripts = ROOT / "scripts" / job_id
        self.assets = ROOT / "assets" / "jobs" / job_id
        self.audio = ROOT / "audio" / "jobs" / job_id
        self.subs = ROOT / "subtitles" / job_id
        self.output = ROOT / "output" / job_id
        self.logs = ROOT / "logs"
        for d in (self.research, self.scripts, self.assets, self.audio, self.subs, self.output, self.logs):
            d.mkdir(parents=True, exist_ok=True)

    # 主要ファイル
    @property
    def candidates(self):
        return self.research / "candidates.json"

    @property
    def script(self):
        return self.scripts / "script.json"

    @property
    def asset_manifest(self):
        return self.assets / "manifest.json"

    @property
    def narration(self):
        return self.audio / "narration.wav"

    @property
    def timeline(self):
        return self.audio / "timeline.json"

    @property
    def ass(self):
        return self.subs / "subtitles.ass"

    @property
    def video(self):
        return self.output / f"{self.id}.mp4"

    @property
    def qa(self):
        return self.output / "qa_report.json"

    @property
    def status(self):
        return self.output / "status.json"

    def mark(self, stage: str, ok: bool, **info):
        st = load_json(self.status, {}) or {}
        st[stage] = {"ok": ok, "at": now_jst().isoformat(timespec="seconds"), **info}
        save_json(self.status, st)


def new_job_id(topic: str | None) -> str:
    slug = re.sub(r"[^0-9A-Za-z぀-ヿ一-鿿]+", "_", topic or "auto").strip("_")[:24]
    return f"{now_jst():%Y%m%d_%H%M%S}_{slug or 'auto'}"


def get_logger(job: Job | None = None, name="pipeline") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(fmt)
    log.addHandler(h)
    logdir = ROOT / "logs"
    logdir.mkdir(exist_ok=True)
    fname = f"{job.id}.log" if job else f"{now_jst():%Y%m%d}.log"
    fh = logging.FileHandler(logdir / fname, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    return log


def run(cmd: list[str], check=True, capture=True, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=capture, text=True, **kw)
    if check and r.returncode != 0:
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(map(str, cmd))[:300]}\n{(r.stderr or '')[-2000:]}")
    return r


def ffprobe(path: Path | str) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    return json.loads(r.stdout)


def media_duration(path: Path | str) -> float:
    return float(ffprobe(path)["format"]["duration"])


def find_font(prefer=("NotoSansCJK-Black.ttc", "NotoSansCJK-Bold.ttc", "ipag.ttf")) -> str:
    for base in ("/usr/share/fonts", "/usr/local/share/fonts", str(ROOT / "templates" / "fonts")):
        for p in Path(base).rglob("*"):
            if p.name in prefer:
                return str(p)
    raise FileNotFoundError("日本語フォントが見つかりません: apt-get install fonts-noto-cjk")
