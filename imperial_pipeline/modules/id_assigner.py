"""ID採番と整合性検査.

  事実ID   F001 〜   research/05_事実台帳.csv
  素材ID   M001 〜   research/06_素材権利台帳.csv
  出典ID   S001 〜   research/04_出典一覧.csv
  図解ID   Z001 〜   production/14_図解・テロップ指示.md
  ライブラリ素材ID L001 〜  library/approved_materials.csv
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

CSV_ENC = "utf-8-sig"

PREFIXES = {
    "fact": "F",
    "material": "M",
    "source": "S",
    "figure": "Z",
    "library": "L",
}

_ID_PATTERN = re.compile(r"^([A-Z])(\d{3,})$")


def read_csv_rows(path: str | Path) -> list[dict]:
    """CSVを辞書のリストとして読む。存在しなければ空リスト."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding=CSV_ENC, newline="") as handle:
        return [row for row in csv.DictReader(handle)]


def read_csv_header(path: str | Path) -> list[str]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding=CSV_ENC, newline="") as handle:
        for row in csv.reader(handle):
            return [cell.strip() for cell in row]
    return []


def format_id(prefix: str, number: int, width: int = 3) -> str:
    return f"{prefix}{number:0{width}d}"


def collect_ids(rows: list[dict], column: str) -> list[str]:
    values = []
    for row in rows:
        value = (row.get(column) or "").strip()
        if value:
            values.append(value)
    return values


def next_id(rows: list[dict], column: str, prefix: str) -> str:
    """既存の最大番号の次を返す."""
    max_number = 0
    for value in collect_ids(rows, column):
        match = _ID_PATTERN.match(value)
        if match and match.group(1) == prefix:
            max_number = max(max_number, int(match.group(2)))
    return format_id(prefix, max_number + 1)


def audit_ids(rows: list[dict], column: str, prefix: str) -> dict:
    """重複・欠番・書式違反を検出する（修正はしない）."""
    values = collect_ids(rows, column)
    duplicates: list[str] = []
    invalid: list[str] = []
    numbers: list[int] = []
    seen: set[str] = set()

    for value in values:
        if value in seen:
            if value not in duplicates:
                duplicates.append(value)
        seen.add(value)
        match = _ID_PATTERN.match(value)
        if not match or match.group(1) != prefix:
            invalid.append(value)
        else:
            numbers.append(int(match.group(2)))

    gaps: list[str] = []
    if numbers:
        for number in range(1, max(numbers) + 1):
            if number not in numbers:
                gaps.append(format_id(prefix, number))

    return {
        "count": len(values),
        "duplicates": duplicates,
        "invalid": invalid,
        "gaps": gaps,
        "next": next_id(rows, column, prefix),
    }


def extract_referenced_ids(text: str, kind: str = "fact") -> list[str]:
    """台本本文から【事実ID：F003】【素材ID：M012】形式のIDを抽出する.

    引用行（行頭 ">"）とHTMLコメント行は、テンプレートの記載例や注意書きであり
    本文ではないため対象外とする。
    IDは `F001` のような英字1文字＋3桁以上の数字の形式に限る。
    """
    label = "事実ID" if kind == "fact" else "素材ID"
    prefix = PREFIXES["fact"] if kind == "fact" else PREFIXES["material"]
    pattern = re.compile(r"【" + label + r"[：:]\s*([^】]+)】")
    strict = re.compile(r"^" + prefix + r"\d{3,}$")

    body_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(">") or stripped.startswith("<!--"):
            continue
        body_lines.append(line)
    body = "\n".join(body_lines)

    found: list[str] = []
    for match in pattern.finditer(body):
        for token in re.split(r"[,、\s/／]+", match.group(1)):
            token = token.strip()
            if strict.match(token) and token not in found:
                found.append(token)
    return found


def cross_check_script_ids(script_text: str, fact_rows: list[dict],
                           material_rows: list[dict]) -> dict:
    """台本が参照するIDが台帳に存在するか、確認状態が十分かを検査する."""
    fact_index = {
        (row.get("事実ID") or "").strip(): row for row in fact_rows if row.get("事実ID")
    }
    material_index = {
        (row.get("素材ID") or "").strip(): row for row in material_rows if row.get("素材ID")
    }

    referenced_facts = extract_referenced_ids(script_text, "fact")
    referenced_materials = extract_referenced_ids(script_text, "material")

    missing_facts = [i for i in referenced_facts if i not in fact_index]
    missing_materials = [i for i in referenced_materials if i not in material_index]

    unusable_facts = []
    needs_more_check = []
    for fact_id in referenced_facts:
        row = fact_index.get(fact_id)
        if not row:
            continue
        state = (row.get("確認状態") or "").strip()
        if state == "使用不可":
            unusable_facts.append(fact_id)
        elif state in ("要追加確認", "一次資料未確認", ""):
            needs_more_check.append(f"{fact_id}（{state or '確認状態未記入'}）")

    unusable_materials = []
    for material_id in referenced_materials:
        row = material_index.get(material_id)
        if not row:
            continue
        usage = (row.get("YouTube利用可否") or "").strip()
        if usage in ("使用禁止", "使用非推奨", "要確認", ""):
            unusable_materials.append(f"{material_id}（{usage or '利用可否未記入'}）")

    unused_facts = [i for i in fact_index if i not in referenced_facts]

    return {
        "referenced_facts": referenced_facts,
        "referenced_materials": referenced_materials,
        "missing_facts": missing_facts,
        "missing_materials": missing_materials,
        "unusable_facts": unusable_facts,
        "needs_more_check": needs_more_check,
        "unusable_materials": unusable_materials,
        "unused_facts": unused_facts,
    }
