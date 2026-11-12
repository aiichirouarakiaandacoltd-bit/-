"""各工程で共通に使う読み込み・パス・字幕マークアップ処理。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUTPUT = ROOT / "output"
MARK = re.compile(r"\[\[(.+?)\|(\w+)(?:\|(\w+))?\]\]")


def load_script():
    return json.loads((ROOT / "script.json").read_text(encoding="utf-8"))


def load_timeline():
    return json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))


def plain(line: str) -> str:
    """マークアップを外した字幕の文字列。"""
    return MARK.sub(lambda m: m.group(1), line)


def spans(line: str):
    """[(文字列, 色名 or None, 縁色名 or None), ...] に分解。"""
    out, pos = [], 0
    for m in MARK.finditer(line):
        if m.start() > pos:
            out.append((line[pos:m.start()], None, None))
        out.append((m.group(1), m.group(2), m.group(3)))
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], None, None))
    return out


def reading(cut) -> str:
    return cut.get("reading") or "".join(plain(t) for t in cut["text"])
