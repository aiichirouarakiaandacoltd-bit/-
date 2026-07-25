"""必須項目・必須列の欠落検出.

config/required_fields.yaml の定義に従い、
  - Markdown : 必須見出しの有無
  - CSV      : 必須列の有無・順序、行数上限、確認状態の値域
を検査する。修正は行わず、報告のみ行う。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import id_assigner

ENC = "utf-8"
CSV_ENC = "utf-8-sig"

_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Issue:
    path: str
    severity: str   # "欠落" | "警告"
    detail: str


@dataclass
class RequiredResult:
    issues: list[Issue] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)

    @property
    def blocking(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "欠落"]

    def to_markdown(self) -> str:
        lines = [
            f"検査ファイル数：{len(self.checked)}／"
            f"欠落 {len(self.blocking)}件、警告 {len(self.issues) - len(self.blocking)}件",
        ]
        if self.missing_files:
            lines.append("")
            lines.append("未生成のファイル：")
            lines.extend(f"- {name}" for name in self.missing_files)
        if not self.issues:
            lines.append("")
            lines.append("必須項目の欠落は検出されなかった。")
            return "\n".join(lines)
        lines.extend([
            "",
            "| ファイル | 種別 | 内容 |",
            "| --- | --- | --- |",
        ])
        for issue in self.issues:
            lines.append(f"| {issue.path} | {issue.severity} | {issue.detail} |")
        return "\n".join(lines)


def _headings(text: str) -> list[str]:
    return [match.group(1).strip() for match in _HEADING.finditer(text)]


def _normalize(value: str) -> str:
    """見出し比較用に、番号や記号を落とす."""
    value = value.strip()
    value = re.sub(r"^[0-9０-９]+[\.．、）\)]?\s*", "", value)
    value = value.replace(" ", "").replace("　", "")
    return value


def check_markdown(path: Path, required_headings: list[str], label: str) -> list[Issue]:
    text = Path(path).read_text(encoding=ENC)
    present = [_normalize(heading) for heading in _headings(text)]
    issues: list[Issue] = []
    for heading in required_headings:
        if _normalize(str(heading)) not in present:
            issues.append(Issue(label, "欠落", f"必須見出しがありません：{heading}"))
    # 未置換のプレースホルダ検出
    for placeholder in sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text))):
        issues.append(Issue(label, "警告", f"未置換のプレースホルダ：{placeholder}"))
    return issues


def check_csv(path: Path, spec: dict, label: str, enums: dict | None = None) -> list[Issue]:
    issues: list[Issue] = []
    header = id_assigner.read_csv_header(path)
    required = [str(column) for column in (spec.get("columns") or [])]

    if header != required:
        missing = [column for column in required if column not in header]
        extra = [column for column in header if column not in required]
        if missing:
            issues.append(Issue(label, "欠落", f"必須列がありません：{', '.join(missing)}"))
        if extra:
            issues.append(Issue(label, "警告", f"定義外の列があります：{', '.join(extra)}"))
        if not missing and not extra:
            issues.append(Issue(label, "警告", "列の順序が定義と異なります。"))

    rows = id_assigner.read_csv_rows(path)
    max_rows = spec.get("max_rows")
    if max_rows and len(rows) > int(max_rows):
        issues.append(
            Issue(label, "欠落", f"行数が上限を超えています：{len(rows)}行（上限 {max_rows}行）")
        )

    enums = enums or {}
    for column, allowed in enums.items():
        if column not in header:
            continue
        allowed_values = {str(value) for value in allowed}
        for index, row in enumerate(rows, start=2):
            value = (row.get(column) or "").strip()
            if value and value not in allowed_values:
                issues.append(
                    Issue(label, "警告", f"{index}行目 {column} の値が定義外です：{value}")
                )
    return issues


def check_project(project_root: Path, required_fields: dict) -> RequiredResult:
    project_root = Path(project_root)
    result = RequiredResult()
    enums = required_fields.get("enum") or {}

    for relative, spec in (required_fields.get("markdown") or {}).items():
        path = project_root / relative
        if not path.exists():
            result.missing_files.append(relative)
            continue
        result.checked.append(relative)
        result.issues.extend(
            check_markdown(path, spec.get("headings") or [], relative)
        )

    for relative, spec in (required_fields.get("csv") or {}).items():
        if relative.startswith("library/"):
            continue  # ライブラリはプロジェクト外
        path = project_root / relative
        if not path.exists():
            result.missing_files.append(relative)
            continue
        result.checked.append(relative)
        result.issues.extend(check_csv(path, spec, relative, enums))

    return result


def check_library(library_csv: Path, required_fields: dict) -> list[Issue]:
    spec = (required_fields.get("csv") or {}).get("library/approved_materials.csv")
    if not spec or not Path(library_csv).exists():
        return []
    return check_csv(Path(library_csv), spec, "library/approved_materials.csv")
