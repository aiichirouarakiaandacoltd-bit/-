"""フォルダ生成・テンプレート出力・履歴退避.

再実行時の方針（第0章 0-3 の4）:
  - 既存の成果物は既定では上書きしない（サブエージェントが書いた内容を守る）
  - --refresh 指定時のみ、旧版を _history/YYYYMMDD_HHMM/ へ退避してから再出力する
  - 最終パッケージは毎回作り直す（旧版は同じく _history/ へ退避する）
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ENC = "utf-8"
CSV_ENC = "utf-8-sig"
NEWLINE = "\n"

# Windowsで使用できない文字（ファイル名検査に使用）
WINDOWS_FORBIDDEN = set(':*?"<>|')

PROJECT_SUBDIRS = (
    "input",
    "research",
    "planning",
    "scripts",
    "production",
    "audit",
    "FINAL_EDITOR_PACKAGE",
    "_history",
)


@dataclass(frozen=True)
class Artifact:
    """テンプレートと成果物の対応."""

    step: int          # 工程番号（--steps での再開に使用）
    template: str      # templates/ 配下のファイル名
    target: str        # projects/<slug>/ からの相対パス
    kind: str          # "md" | "csv"
    owner: str         # 記入を担当するサブエージェント


ARTIFACTS: tuple[Artifact, ...] = (
    Artifact(1, "01_入力整理.md", "research/01_入力整理.md", "md", "imperial-researcher"),
    Artifact(2, "02_既存動画重複確認.md", "research/02_既存動画重複確認.md", "md", "imperial-researcher"),
    Artifact(3, "03_調査結果.md", "research/03_調査結果.md", "md", "imperial-researcher"),
    Artifact(3, "04_出典一覧.csv", "research/04_出典一覧.csv", "csv", "imperial-researcher"),
    Artifact(4, "05_事実台帳.csv", "research/05_事実台帳.csv", "csv", "imperial-fact-checker"),
    Artifact(5, "06_素材権利台帳.csv", "research/06_素材権利台帳.csv", "csv", "rights-reviewer"),
    Artifact(6, "07_企画評価.md", "planning/07_企画評価.md", "md", "production-director"),
    Artifact(7, "08_タイトル・サムネイル案.md", "planning/08_タイトル・サムネイル案.md", "md", "production-director"),
    Artifact(8, "09_長尺構成.md", "planning/09_長尺構成.md", "md", "imperial-writer"),
    Artifact(9, "10A_長尺台本_監査用.md", "scripts/10A_長尺台本_監査用.md", "md", "imperial-writer"),
    Artifact(9, "10B_長尺台本_編集者用.md", "scripts/10B_長尺台本_編集者用.md", "md", "imperial-writer"),
    Artifact(10, "11_Shorts台本.md", "scripts/11_Shorts台本.md", "md", "imperial-shorts-writer"),
    Artifact(11, "12_長尺素材設計.csv", "production/12_長尺素材設計.csv", "csv", "production-director"),
    Artifact(12, "13_Shorts素材設計.csv", "production/13_Shorts素材設計.csv", "csv", "production-director"),
    Artifact(13, "14_図解・テロップ指示.md", "production/14_図解・テロップ指示.md", "md", "production-director"),
    Artifact(14, "15_サムネイル制作指示.md", "production/15_サムネイル制作指示.md", "md", "production-director"),
    Artifact(15, "16_投稿設定.md", "production/16_投稿設定.md", "md", "production-director"),
    Artifact(16, "17_編集者向け制作指示書.md", "production/17_編集者向け制作指示書.md", "md", "production-director"),
    Artifact(17, "18_最終監査結果.md", "audit/18_最終監査結果.md", "md", "final-auditor"),
    Artifact(18, "19_荒木承認用サマリー.md", "audit/19_荒木承認用サマリー.md", "md", "final-auditor"),
)

SAMPLE_BANNER = "> **【サンプル・ダミーデータ／実制作に使用しないこと】**"


# ---------------------------------------------------------------------
# パス
# ---------------------------------------------------------------------
def project_dir(root: Path, slug: str) -> Path:
    return Path(root) / "projects" / slug


def history_dir(root: Path, slug: str, stamp: str | None = None) -> Path:
    stamp = stamp or datetime.now().strftime("%Y%m%d_%H%M")
    return project_dir(root, slug) / "_history" / stamp


def check_filename(path: Path) -> list[str]:
    """Windowsで使えない文字を検出する."""
    problems = []
    for part in Path(path).parts:
        bad = WINDOWS_FORBIDDEN & set(part)
        if bad:
            problems.append(f"{part} に使用できない文字が含まれます: {''.join(sorted(bad))}")
    return problems


def ensure_project_dirs(root: Path, slug: str) -> Path:
    base = project_dir(root, slug)
    for name in PROJECT_SUBDIRS:
        (base / name).mkdir(parents=True, exist_ok=True)
    return base


# ---------------------------------------------------------------------
# 描画コンテキスト
# ---------------------------------------------------------------------
def build_context(settings: dict, project, network_status: str,
                  past_videos_status: str, approval: dict | None = None) -> dict:
    """テンプレートのプレースホルダへ埋める値を作る."""
    cpm = int(settings.get("chars_per_minute", 300) or 300)
    length_min = project.target_length_min
    length_max = project.target_length_max
    approval = approval or {}

    def _s(value, fallback: str) -> str:
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    return {
        "GENERATED_AT": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "SAMPLE_BANNER": SAMPLE_BANNER if project.sample_mode else "",
        "PROJECT_NAME": _s(project.project_name, "【未入力】"),
        "PROJECT_SLUG": _s(project.project_slug, "【未入力】"),
        "CHANNEL": _s(project.get("channel"), settings.get("channel_name", "")),
        "MAIN_PERSON": _s(project.get("main_person"), "【人物確認が必要】"),
        "THEME": _s(project.get("theme"), "【未確認】"),
        "WORKING_TITLE": _s(project.get("working_title"), "【未定】"),
        "EDITOR_NAME": _s(project.get("editor_name"), "【要入力】"),
        "PUBLICATION_TARGET_DATE": _s(project.get("publication_target_date"), "【未定】"),
        "NOTES": _s(project.get("notes"), ""),
        "LONG_MIN": str(length_min),
        "LONG_MAX": str(length_max),
        "TARGET_CHARS_MIN": f"{length_min * cpm:,}",
        "TARGET_CHARS_MAX": f"{length_max * cpm:,}",
        "CHARS_PER_MINUTE": str(cpm),
        "SHORTS_COUNT": str(project.shorts_count),
        "SHORTS_MIN_SEC": str(settings.get("shorts_min_seconds", 50)),
        "SHORTS_MAX_SEC": str(settings.get("shorts_max_seconds", 60)),
        "CUT_MIN": str(settings.get("cut_seconds_min", 3)),
        "CUT_MAX": str(settings.get("cut_seconds_max", 5)),
        "VOICE_NAME": str(settings.get("voice_name", "青山龍星")),
        "VOICE_SPEED": str(settings.get("voice_speed", 0.88)),
        "VOICE_SPEED_MIN": str(settings.get("voice_speed_min", 0.85)),
        "VOICE_SPEED_MAX": str(settings.get("voice_speed_max", 0.90)),
        "BGM_FILE": str(settings.get("bgm_file", "UNL1337.wav")),
        "BGM_CREDIT": str(settings.get("bgm_credit", "【要確認・正式表記を荒木が入力】")),
        "CONTACT": str(settings.get("contact", "【お問い合わせ先：要入力】")),
        "THUMBNAIL_TEXT_MIN": str(settings.get("thumbnail_text_min", 4)),
        "THUMBNAIL_TEXT_MAX": str(settings.get("thumbnail_text_max", 14)),
        "LONG_ROWS_MAX": str(settings.get("long_visual_rows_max", 120)),
        "SHORTS_ROWS_MAX": str(settings.get("shorts_visual_rows_max", 20)),
        "NETWORK_STATUS": network_status,
        "PAST_VIDEOS_STATUS": past_videos_status,
        "APPROVED_TITLE": _s(approval.get("selected_title"), "【承認後に確定】"),
        "APPROVED_THUMBNAIL": _s(approval.get("selected_thumbnail"), "【承認後に確定】"),
    }


_PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def render(text: str, context: dict) -> str:
    """{{KEY}} を置換する。未知のキーはそのまま残す（欠落に気付けるようにする）."""
    def _sub(match: re.Match) -> str:
        key = match.group(1)
        if key in context:
            return str(context[key])
        return match.group(0)

    return _PLACEHOLDER.sub(_sub, text)


# ---------------------------------------------------------------------
# 機械記入ブロック
# ---------------------------------------------------------------------
def replace_machine_block(text: str, name: str, content: str) -> tuple[str, bool]:
    """<!-- MACHINE_BLOCK:name:START --> 〜 END の中身を差し替える."""
    pattern = re.compile(
        r"(<!-- MACHINE_BLOCK:" + re.escape(name) + r":START -->)(.*?)(<!-- MACHINE_BLOCK:"
        + re.escape(name) + r":END -->)",
        re.DOTALL,
    )
    if not pattern.search(text):
        return text, False
    replaced = pattern.sub(lambda m: m.group(1) + "\n" + content + "\n" + m.group(3), text)
    return replaced, True


def update_machine_block(path: Path, name: str, content: str) -> bool:
    """ファイル内の機械記入ブロックを更新する."""
    path = Path(path)
    if not path.exists():
        return False
    text = path.read_text(encoding=ENC)
    new_text, found = replace_machine_block(text, name, content)
    if found and new_text != text:
        write_text(path, new_text)
    return found


# ---------------------------------------------------------------------
# 書き込み
# ---------------------------------------------------------------------
def write_text(path: Path, text: str) -> None:
    """UTF-8・改行LFで書き出す."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    with path.open("w", encoding=ENC, newline=NEWLINE) as handle:
        handle.write(text)


def write_csv_text(path: Path, text: str) -> None:
    """CSVは utf-8-sig（Excel対策）・改行LFで書き出す."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    with path.open("w", encoding=CSV_ENC, newline=NEWLINE) as handle:
        handle.write(text)


def backup_to_history(root: Path, slug: str, targets: list[Path], stamp: str,
                      log=None) -> int:
    """上書き前に旧版を _history/<stamp>/ へ退避する."""
    base = project_dir(root, slug)
    dest_root = history_dir(root, slug, stamp)
    moved = 0
    for target in targets:
        target = Path(target)
        if not target.exists():
            continue
        try:
            relative = target.relative_to(base)
        except ValueError:
            relative = Path(target.name)
        dest = dest_root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
        moved += 1
        if log:
            log.info(f"退避: {relative} -> _history/{stamp}/{relative}")
    return moved


# ---------------------------------------------------------------------
# テンプレート出力
# ---------------------------------------------------------------------
def emit_artifacts(root: Path, slug: str, context: dict, steps: set[int] | None,
                   refresh: bool, stamp: str, log=None) -> dict:
    """テンプレートを成果物として出力する.

    戻り値: {"created": [...], "kept": [...], "refreshed": [...], "missing_template": [...]}
    """
    templates_dir = Path(root) / "templates"
    base = project_dir(root, slug)
    result = {"created": [], "kept": [], "refreshed": [], "missing_template": []}

    to_backup = []
    if refresh:
        for artifact in ARTIFACTS:
            if steps and artifact.step not in steps:
                continue
            target = base / artifact.target
            if target.exists():
                to_backup.append(target)
        if to_backup:
            backup_to_history(root, slug, to_backup, stamp, log)

    for artifact in ARTIFACTS:
        if steps and artifact.step not in steps:
            continue
        template_path = templates_dir / artifact.template
        target = base / artifact.target

        problems = check_filename(Path(artifact.target))
        if problems and log:
            for problem in problems:
                log.warn(f"ファイル名の警告: {problem}")

        if not template_path.exists():
            result["missing_template"].append(artifact.template)
            if log:
                log.error(f"テンプレートが見つかりません: {artifact.template}")
            continue

        if target.exists() and not refresh:
            result["kept"].append(artifact.target)
            continue

        # CSVテンプレートはBOM付きで保存しているため utf-8-sig で読む（BOMの二重付与を防ぐ）
        text = template_path.read_text(encoding=CSV_ENC if artifact.kind == "csv" else ENC)
        rendered = render(text, context)
        if artifact.kind == "csv":
            write_csv_text(target, rendered)
        else:
            write_text(target, rendered)

        if target in to_backup:
            result["refreshed"].append(artifact.target)
        else:
            result["created"].append(artifact.target)
        if log:
            log.info(f"出力: {artifact.target}")

    return result


def ensure_input_files(root: Path, slug: str, log=None) -> list[str]:
    """input/ に past_videos.csv / approval.yaml のひな形を用意する（既存は触らない）."""
    templates_dir = Path(root) / "templates"
    base = project_dir(root, slug) / "input"
    base.mkdir(parents=True, exist_ok=True)
    created = []
    for template_name, kind in (("past_videos.csv", "csv"), ("approval.yaml", "md")):
        target = base / template_name
        source = templates_dir / template_name
        if target.exists() or not source.exists():
            continue
        text = source.read_text(encoding=CSV_ENC if kind == "csv" else ENC)
        if kind == "csv":
            write_csv_text(target, text)
        else:
            write_text(target, text)
        created.append(str(target))
        if log:
            log.info(f"入力ひな形を作成: input/{template_name}")
    return created
