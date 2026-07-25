"""禁止表現の機械検出.

Pythonは検出のみを行う。最終判定は imperial-safety-reviewer と荒木愛一朗が行う。
検出結果の分類（config/forbidden_expressions.yaml の default_classification）:
    使用可能／留保表現に変更／根拠追加が必要／使用禁止
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ENC = "utf-8"
CSV_ENC = "utf-8-sig"

CLASSIFICATIONS = ("使用可能", "留保表現に変更", "根拠追加が必要", "使用禁止")


@dataclass
class Hit:
    path: str
    line_no: int
    line: str
    term: str
    category: str
    classification: str
    in_exception: bool = False

    def as_row(self) -> str:
        note = "（検出対象外）" if self.in_exception else ""
        snippet = self.line.strip()
        if len(snippet) > 60:
            snippet = snippet[:60] + "…"
        return f"| {self.path} | {self.line_no} | {self.term} | {self.category} | {self.classification}{note} | {snippet} |"


@dataclass
class CheckResult:
    hits: list[Hit] = field(default_factory=list)
    scanned_files: int = 0

    @property
    def blocking(self) -> list[Hit]:
        return [h for h in self.hits if h.classification == "使用禁止" and not h.in_exception]

    @property
    def review_needed(self) -> list[Hit]:
        return [
            h for h in self.hits
            if h.classification in ("根拠追加が必要", "留保表現に変更") and not h.in_exception
        ]

    def to_markdown(self) -> str:
        if not self.hits:
            return f"検出なし（{self.scanned_files}ファイルを走査）。"
        lines = [
            f"走査ファイル数：{self.scanned_files}／検出：{len(self.hits)}件"
            f"（使用禁止 {len(self.blocking)}件、要確認 {len(self.review_needed)}件）",
            "",
            "| ファイル | 行 | 検出語 | 分類元 | 機械判定 | 該当行 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        lines.extend(hit.as_row() for hit in self.hits)
        lines.append("")
        lines.append(
            "> 機械判定は候補である。文脈上問題がなければ「使用可能」と判断してよい。"
            "最終判定は imperial-safety-reviewer と荒木愛一朗が行う。"
        )
        return "\n".join(lines)


def _exception_line_numbers(lines: list[str], config: dict) -> set[int]:
    """検出対象外の行番号（1始まり）を返す.

    対象外とするのは次の3種類。
      1. 引用ブロック（行頭 ">"）・【引用】段落・引用用コードフェンス
      2. <!-- SCAN:OFF --> 〜 <!-- SCAN:ON --> で囲まれた範囲
         （禁止事項の列挙そのものを検出しないための領域指定）
    """
    patterns = config.get("exception_patterns") or {}
    prefixes = tuple(patterns.get("line_prefixes") or [">"])
    markers = tuple(patterns.get("paragraph_markers") or ["【引用】"])
    fences = tuple(patterns.get("fenced_blocks") or [])
    scan_off = str(patterns.get("scan_off") or "<!-- SCAN:OFF -->")
    scan_on = str(patterns.get("scan_on") or "<!-- SCAN:ON -->")

    exempt: set[int] = set()
    in_fence = False
    in_marked_paragraph = False
    scan_disabled = False

    for index, raw in enumerate(lines, start=1):
        stripped = raw.strip()

        if scan_disabled:
            exempt.add(index)
            if scan_on in stripped:
                scan_disabled = False
            continue
        if scan_off in stripped:
            scan_disabled = True
            exempt.add(index)
            continue

        if in_fence:
            exempt.add(index)
            if stripped.startswith("```"):
                in_fence = False
            continue
        if any(stripped.startswith(fence) for fence in fences):
            in_fence = True
            exempt.add(index)
            continue

        if stripped.startswith(prefixes):
            exempt.add(index)
            continue

        if any(marker in stripped for marker in markers):
            in_marked_paragraph = True
            exempt.add(index)
            continue

        if in_marked_paragraph:
            if stripped == "":
                in_marked_paragraph = False
            else:
                exempt.add(index)

    return exempt


def scan_text(text: str, path_label: str, config: dict) -> list[Hit]:
    lines = text.splitlines()
    exempt = _exception_line_numbers(lines, config)
    defaults = config.get("default_classification") or {}
    hits: list[Hit] = []

    word_categories = ("critical", "high_risk", "context_check", "clickbait")
    for category in word_categories:
        terms = config.get(category) or []
        classification = defaults.get(category, "根拠追加が必要")
        for term in terms:
            if not term:
                continue
            for line_no, line in enumerate(lines, start=1):
                if str(term) in line:
                    hits.append(Hit(
                        path=path_label,
                        line_no=line_no,
                        line=line,
                        term=str(term),
                        category=category,
                        classification=classification,
                        in_exception=line_no in exempt,
                    ))

    regex_classification = defaults.get("inner_state_patterns", "留保表現に変更")
    for pattern in config.get("inner_state_patterns") or []:
        try:
            compiled = re.compile(str(pattern))
        except re.error:
            continue
        for line_no, line in enumerate(lines, start=1):
            match = compiled.search(line)
            if match:
                hits.append(Hit(
                    path=path_label,
                    line_no=line_no,
                    line=line,
                    term=match.group(0),
                    category="inner_state_patterns",
                    classification=regex_classification,
                    in_exception=line_no in exempt,
                ))

    return hits


def scan_paths(paths: list[Path], config: dict, base: Path | None = None) -> CheckResult:
    result = CheckResult()
    for path in paths:
        path = Path(path)
        if not path.exists() or path.is_dir():
            continue
        encoding = CSV_ENC if path.suffix.lower() == ".csv" else ENC
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            text = path.read_text(encoding=ENC, errors="replace")
        label = str(path.relative_to(base)) if base else str(path)
        result.scanned_files += 1
        result.hits.extend(scan_text(text, label, config))
    result.hits.sort(key=lambda h: (h.path, h.line_no))
    return result


def scan_project(project_root: Path, config: dict,
                 subdirs: tuple[str, ...] = ("research", "planning", "scripts", "production")) -> CheckResult:
    """プロジェクトの成果物を走査する（audit/ と _history/ は対象外）."""
    project_root = Path(project_root)
    targets: list[Path] = []
    for name in subdirs:
        directory = project_root / name
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in (".md", ".csv"):
                targets.append(path)
    return scan_paths(targets, config, base=project_root)


def check_honorifics(text: str, honorifics: dict) -> list[str]:
    """表記ゆれ候補を検出する（統一表記への置換は行わない）."""
    findings: list[str] = []
    for person in honorifics.get("persons") or []:
        if not isinstance(person, dict):
            continue
        use = str(person.get("use") or "")
        for variant in person.get("variants") or []:
            variant = str(variant)
            if not variant or variant == use:
                continue
            # 統一表記の一部として現れる場合は誤検出になるため除外する
            if variant in use:
                continue
            if variant in text:
                findings.append(f"表記ゆれ候補「{variant}」→ 統一表記「{use}」")
    return sorted(set(findings))
