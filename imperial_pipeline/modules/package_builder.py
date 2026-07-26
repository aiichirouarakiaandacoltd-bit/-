"""最終フォルダ（FINAL_EDITOR_PACKAGE）の生成.

方針（第0章 0-3 の2）:
  権利未確認素材が残っていても生成を止めない。
  未確認素材は「使用禁止」と明記し、代替案を併記したうえで生成する。

  生成をブロックするのは次の場合のみ。
    ・重大な人物誤認、日付誤認が解消されていない
      （＝台本が確認状態「使用不可」の事実を参照している／最終監査が「不合格」）
    ・存在しない出典URLが含まれている（sample_mode では警告へ緩和）
    ・皇族方のAI生成顔、顔加工素材が含まれている
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import approval_builder, id_assigner, scaffold

ENC = "utf-8"
CSV_ENC = "utf-8-sig"

# (最終版ファイル名, 元ファイル, 種別)
FINAL_MAP: tuple[tuple[str, str, str], ...] = (
    ("01_編集者向け制作指示書_最終版.md", "production/17_編集者向け制作指示書.md", "md"),
    ("02_長尺台本_最終版.md", "scripts/10B_長尺台本_編集者用.md", "md"),
    ("03_Shorts台本_最終版.md", "scripts/11_Shorts台本.md", "md"),
    ("04_長尺素材設計_最終版.csv", "production/12_長尺素材設計.csv", "csv"),
    ("05_Shorts素材設計_最終版.csv", "production/13_Shorts素材設計.csv", "csv"),
    ("06_素材権利台帳_最終版.csv", "research/06_素材権利台帳.csv", "csv"),
    ("07_サムネイル制作指示_最終版.md", "production/15_サムネイル制作指示.md", "md"),
    ("08_投稿設定_最終版.md", "production/16_投稿設定.md", "md"),
    ("09_出典一覧_最終版.csv", "research/04_出典一覧.csv", "csv"),
)

CHECKLIST_TEMPLATE = "10_納品前チェックリスト.md"
CHECKLIST_NAME = "10_納品前チェックリスト.md"

_INTERNAL_BLOCK = re.compile(r"<!--\s*INTERNAL:START\s*-->.*?<!--\s*INTERNAL:END\s*-->",
                             re.DOTALL)
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*)$")
_AUDIT_STATUS = re.compile(r"<!--\s*AUDIT_STATUS:\s*(.+?)\s*-->")


@dataclass
class PackageResult:
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    written: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return bool(self.blockers)


# ---------------------------------------------------------------------
# 内部情報の除去
# ---------------------------------------------------------------------
def strip_internal(text: str, internal_headings: list[str]) -> str:
    """INTERNALブロックと内部見出しセクションを除去する."""
    text = _INTERNAL_BLOCK.sub("", text)

    keywords = [str(word) for word in (internal_headings or [])]
    if not keywords:
        return text

    output: list[str] = []
    skip_level = 0
    for line in text.splitlines():
        match = _HEADING_LINE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2)
            if skip_level and level <= skip_level:
                skip_level = 0
            if not skip_level and any(word in title for word in keywords):
                skip_level = level
                continue
        if skip_level:
            continue
        output.append(line)
    return "\n".join(output)


_SCAN_OFF_REGION = re.compile(r"<!--\s*SCAN:OFF\s*-->.*?<!--\s*SCAN:ON\s*-->", re.DOTALL)
_SCAN_MARKER = re.compile(r"^[ \t]*<!--\s*SCAN:(OFF|ON)\s*-->[ \t]*\n?", re.MULTILINE)


def scan_forbidden_words(text: str, words: list[str]) -> list[str]:
    """契約・金銭に関わる語の混入を検出する（SCAN:OFF 範囲は対象外）."""
    target = _SCAN_OFF_REGION.sub("", text)
    return [str(word) for word in (words or []) if str(word) in target]


def strip_scan_markers(text: str) -> str:
    """検出制御用のコメント行を最終版から取り除く."""
    return _SCAN_MARKER.sub("", text)


# ---------------------------------------------------------------------
# 承認内容の反映
# ---------------------------------------------------------------------
def apply_approval_text(text: str, approval: dict) -> str:
    """承認されたタイトル・サムネイルを最終版へ反映する.

    未確定マーカーは3系統ありうる。
      1. `{{APPROVED_TITLE}}` … テンプレートが未描画のまま残った場合
      2. `【承認後に確定：タイトル】` … 下書き生成時に描画された現行のマーカー
      3. `【承認後に確定】` … 旧版のマーカー（タイトルとサムネイルで共通だった）
    3は同じ文字列のためどちらを埋めるべきか判別できない。
    行内に「サムネイル」の語があるかどうかで振り分ける。
    """
    title = str(approval.get("selected_title") or "").strip()
    thumbnail = str(approval.get("selected_thumbnail") or "").strip()

    if title:
        text = text.replace("{{APPROVED_TITLE}}", title)
        text = text.replace("【承認後に確定：タイトル】", title)
    if thumbnail:
        text = text.replace("{{APPROVED_THUMBNAIL}}", thumbnail)
        text = text.replace("【承認後に確定：サムネイル】", thumbnail)

    if not (title or thumbnail):
        return text

    lines = text.splitlines()
    current_heading = ""
    for index, line in enumerate(lines):
        heading = _HEADING_LINE.match(line)
        if heading:
            current_heading = heading.group(2)
        if "【承認後に確定】" not in line:
            continue
        # 行内と、その行が属する見出しの両方を見て振り分ける。
        # 「## サムネイル」節の「- 採用案：」のように、
        # 行だけでは判別できない書き方があるため。
        context = f"{line} {current_heading}"
        if "サムネイル" in context and thumbnail:
            lines[index] = line.replace("【承認後に確定】", thumbnail)
        elif title:
            lines[index] = line.replace("【承認後に確定】", title)
    return "\n".join(lines)


def _csv_from_rows(header: list[str], rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in header})
    return buffer.getvalue()


def apply_rejected_materials(header: list[str], rows: list[dict],
                             rejected: list[str]) -> tuple[list[dict], list[str]]:
    """荒木愛一朗が却下した素材と、未確認素材を「使用禁止」として明記する."""
    rejected_set = {str(item).strip() for item in (rejected or []) if str(item).strip()}
    notes: list[str] = []

    for row in rows:
        material_id = (row.get("素材ID") or "").strip()
        usage = (row.get("YouTube利用可否") or "").strip()
        alternative = (row.get("代替案") or "").strip()

        if material_id and material_id in rejected_set:
            row["YouTube利用可否"] = "使用禁止"
            row["注意事項"] = _append_note(
                row.get("注意事項"), "荒木愛一朗の判断により使用禁止。代替案に従うこと。"
            )
            if not alternative:
                row["代替案"] = "【代替案未設定】図解またはテロップ中心画面へ切り替えること"
            notes.append(f"{material_id}：承認により使用禁止")
            continue

        if usage in ("要確認", "", "使用非推奨"):
            row["YouTube利用可否"] = "使用禁止"
            reason = "権利未確認のため使用禁止" if usage in ("要確認", "") else "使用非推奨のため使用禁止"
            row["注意事項"] = _append_note(row.get("注意事項"), f"{reason}。代替案に従うこと。")
            if not alternative:
                row["代替案"] = "【代替案未設定】図解またはテロップ中心画面へ切り替えること"
            notes.append(f"{material_id or '（IDなし）'}：{reason}")

    return rows, notes


def apply_rejected_to_visual(header: list[str], rows: list[dict],
                             forbidden_ids: set[str]) -> list[dict]:
    """長尺素材設計側にも使用禁止を反映する."""
    for row in rows:
        material_id = (row.get("素材ID") or "").strip()
        state = (row.get("権利確認状態") or "").strip()
        if (material_id and material_id in forbidden_ids) or state in ("要確認", "", "使用非推奨"):
            row["権利確認状態"] = "使用禁止"
            row["禁止事項"] = _append_note(
                row.get("禁止事項"), "この素材は使用しないこと。代替素材列に従う。"
            )
            if not (row.get("代替素材") or "").strip():
                row["代替素材"] = "図解またはテロップ中心画面"
    return rows


def _append_note(existing, addition: str) -> str:
    existing = str(existing or "").strip()
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing} / {addition}"


# ---------------------------------------------------------------------
# 事前検査
# ---------------------------------------------------------------------
def preflight(project_root: Path, fact_rows: list[dict], material_rows: list[dict],
              cross_check: dict, sample_mode: bool) -> PackageResult:
    result = PackageResult()
    project_root = Path(project_root)

    # 1. 重大な人物誤認・日付誤認が解消されていない
    unusable = cross_check.get("unusable_facts") or []
    if unusable:
        result.blockers.append(
            "台本が確認状態「使用不可」の事実を参照している："
            + "、".join(unusable)
            + "（該当箇所を削除するか、事実台帳の確認状態を更新すること）"
        )
    missing_facts = cross_check.get("missing_facts") or []
    if missing_facts:
        result.blockers.append(
            "台本が参照する事実IDが事実台帳に存在しない：" + "、".join(missing_facts)
        )

    audit_path = project_root / "audit" / "18_最終監査結果.md"
    if audit_path.exists():
        match = _AUDIT_STATUS.search(audit_path.read_text(encoding=ENC))
        status = match.group(1).strip() if match else "未判定"
        if status == "不合格":
            result.blockers.append("最終監査結果の判定が「不合格」である。")
        elif status == "未判定":
            result.warnings.append(
                "最終監査結果が「未判定」のまま。final-auditor による監査を実施すること。"
            )
    else:
        result.warnings.append("audit/18_最終監査結果.md が存在しない。")

    # 2. 存在しない出典URL
    fake_urls = approval_builder.find_fake_urls(project_root)
    if fake_urls:
        message = "架空URLの疑いがある記述：" + "、".join(fake_urls)
        if sample_mode:
            result.warnings.append("【サンプル】" + message + "（sample_mode のため警告に留める）")
        else:
            result.blockers.append(message)

    # 3. 皇族方のAI生成顔・顔加工素材
    ai_faces = approval_builder.find_ai_face_materials(material_rows)
    if ai_faces:
        result.blockers.append(
            "皇族方のAI生成顔・顔加工素材の疑いがある素材が含まれている："
            + "、".join(ai_faces)
        )

    # 設定値の未入力（ブロックしないが、このまま公開すると義務を果たせない）
    for item in approval_builder.find_unresolved_settings(project_root):
        result.warnings.append(f"**公開前に必須**：{item}")

    # 10Aと10Bの本文が食い違ったまま編集者へ渡らないようにする
    compare = approval_builder.compare_script_bodies(project_root)
    if compare.get("match") is False:
        result.warnings.append(
            f"長尺台本 10A と 10B の本文が一致していない：{compare['detail']}"
        )

    # 参考情報（ブロックしない）
    if not fact_rows:
        result.warnings.append("事実台帳が空である。編集者へ渡す前に内容を確認すること。")
    if not material_rows:
        result.warnings.append("素材権利台帳が空である。素材設計が図解中心になっているか確認すること。")

    return result


# ---------------------------------------------------------------------
# 生成
# ---------------------------------------------------------------------
def build(root: Path, slug: str, settings: dict, context: dict, approval: dict,
          fact_rows: list[dict], material_rows: list[dict], cross_check: dict,
          sample_mode: bool, stamp: str, log=None) -> PackageResult:
    root = Path(root)
    project_root = scaffold.project_dir(root, slug)
    final_dir = project_root / "FINAL_EDITOR_PACKAGE"

    result = preflight(project_root, fact_rows, material_rows, cross_check, sample_mode)
    if result.blocked:
        if log:
            for reason in result.blockers:
                log.block(f"最終パッケージ生成をブロック: {reason}")
        return result

    # 旧版を退避
    if final_dir.exists():
        existing = [path for path in final_dir.glob("*") if path.is_file()]
        if existing:
            scaffold.backup_to_history(root, slug, existing, stamp, log)
    final_dir.mkdir(parents=True, exist_ok=True)

    internal_headings = settings.get("internal_headings") or []
    forbidden_words = settings.get("final_package_forbidden_words") or []
    rejected = approval.get("rejected_materials") or []
    forbidden_ids: set[str] = set()

    for final_name, source_relative, kind in FINAL_MAP:
        source = project_root / source_relative
        target = final_dir / final_name
        if not source.exists():
            result.missing_sources.append(source_relative)
            if log:
                log.warn(f"元ファイルが無いため最終版を作成できない: {source_relative}")
            continue

        if kind == "md":
            text = source.read_text(encoding=ENC)
            text = strip_internal(text, internal_headings)
            text = apply_approval_text(text, approval)
            text = re.sub(r"<!-- artifact: .*? -->\n?", "", text)
            text = _add_final_header(text, final_name, context, sample_mode)
            leaked = scan_forbidden_words(text, forbidden_words)
            if leaked:
                result.warnings.append(
                    f"{final_name} に契約・金銭に関わる語が含まれている：{', '.join(leaked)}"
                )
            scaffold.write_text(target, strip_scan_markers(text))
        else:
            header = id_assigner.read_csv_header(source)
            rows = id_assigner.read_csv_rows(source)
            if final_name.startswith("06_"):
                rows, notes = apply_rejected_materials(header, rows, rejected)
                forbidden_ids = {
                    (row.get("素材ID") or "").strip()
                    for row in rows
                    if (row.get("YouTube利用可否") or "").strip() == "使用禁止"
                }
                for note in notes:
                    result.warnings.append(f"素材権利台帳（最終版）：{note}")
            elif final_name.startswith("04_"):
                rows = apply_rejected_to_visual(header, rows, forbidden_ids)
            scaffold.write_csv_text(target, _csv_from_rows(header, rows) if header else "")

        result.written.append(final_name)
        if log:
            log.info(f"最終版を出力: FINAL_EDITOR_PACKAGE/{final_name}")

    # 納品前チェックリスト
    checklist_source = root / "templates" / CHECKLIST_TEMPLATE
    if checklist_source.exists():
        text = scaffold.render(checklist_source.read_text(encoding=ENC), context)
        text = re.sub(r"<!-- artifact: .*? -->\n?", "", text)
        scaffold.write_text(final_dir / CHECKLIST_NAME, strip_scan_markers(text))
        result.written.append(CHECKLIST_NAME)
        if log:
            log.info(f"最終版を出力: FINAL_EDITOR_PACKAGE/{CHECKLIST_NAME}")
    else:
        result.missing_sources.append(f"templates/{CHECKLIST_TEMPLATE}")

    return result


def _add_final_header(text: str, final_name: str, context: dict, sample_mode: bool) -> str:
    """最終版であることと、主資料の位置づけを冒頭へ明記する."""
    banner = scaffold.SAMPLE_BANNER + "\n\n" if sample_mode else ""
    if final_name.startswith("01_"):
        note = (
            "> **この文書が編集者向けの主資料です。**"
            "同じフォルダ内の他ファイルは、本書から参照される添付資料です。\n"
            "> 不明点は推測で進めず、荒木愛一朗へ確認してください。\n\n"
        )
    else:
        note = (
            "> 本ファイルは `01_編集者向け制作指示書_最終版.md` の添付資料です。\n\n"
        )
    header = f"<!-- final_package: {final_name} / generated_at: {context.get('GENERATED_AT')} -->\n"
    # 既存のサンプルバナー行を重複させない
    if sample_mode and scaffold.SAMPLE_BANNER in text:
        banner = ""
    return header + banner + note + text.lstrip("\n")
