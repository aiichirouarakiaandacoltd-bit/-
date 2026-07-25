#!/usr/bin/env python3
"""日本が誇る皇室物語 / 制作支援システム 実行スクリプト.

    # 1. 新規プロジェクトの作成
    python run_imperial_pipeline.py --init <project_slug>

    # 2. 下書き一式の生成（テンプレート出力＋機械検出）
    python run_imperial_pipeline.py projects/<slug>/input/project_input.yaml --stage draft

    # 3. 検査のみ（生成物を変更しない）
    python run_imperial_pipeline.py projects/<slug>/input/project_input.yaml --stage check

    # 4. 承認後の最終版生成
    python run_imperial_pipeline.py projects/<slug>/input/project_input.yaml \
        --stage final --approval projects/<slug>/input/approval.yaml

本スクリプトは機械処理のみを行う。
調査・事実判定・台本執筆・企画評価・監査は行わない（サブエージェントの担当）。
外部APIを呼ばない。APIキーを必要としない。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from modules import (  # noqa: E402
    approval_builder,
    duplication_checker,
    forbidden_checker,
    id_assigner,
    input_parser,
    logger as logger_module,
    package_builder,
    required_checker,
    scaffold,
)

ENC = "utf-8"


# ---------------------------------------------------------------------
# 補助
# ---------------------------------------------------------------------
def load_configs() -> dict:
    config_dir = ROOT / "config"
    return {
        "settings": input_parser.load_yaml(config_dir / "settings.yaml"),
        "honorifics": input_parser.load_yaml(config_dir / "honorifics.yaml"),
        "forbidden": input_parser.load_yaml(config_dir / "forbidden_expressions.yaml"),
        "required": input_parser.load_yaml(config_dir / "required_fields.yaml"),
    }


def detect_network_status() -> str:
    """ENVIRONMENT.md の記載を読むだけ。ネットワークへは接続しない."""
    env_path = ROOT / "ENVIRONMENT.md"
    if not env_path.exists():
        return "【アクセス未確認】ENVIRONMENT.md が未作成"
    for line in env_path.read_text(encoding=ENC).splitlines():
        if line.strip().lower().startswith("<!-- network_status:"):
            value = line.split(":", 1)[1].replace("-->", "").strip()
            return value or "【アクセス未確認】"
    return "【アクセス未確認】ENVIRONMENT.md に network_status の記載なし"


def init_project(slug: str, log) -> int:
    if not slug or not slug.replace("_", "").replace("-", "").isalnum():
        log.error("project_slug は半角英数字・アンダースコア・ハイフンのみで指定してください。")
        return 1
    base = scaffold.ensure_project_dirs(ROOT, slug)
    target = base / "input" / "project_input.yaml"
    if target.exists():
        log.warn(f"既に存在します（上書きしません）: {target}")
    else:
        template = (ROOT / "templates" / "project_input.yaml").read_text(encoding=ENC)
        template = template.replace(
            "project_slug:            #", f"project_slug: {slug}   #"
        )
        scaffold.write_text(target, template)
        log.info(f"作成しました: {target}")
    scaffold.ensure_input_files(ROOT, slug, log)
    print()
    print(f"次の操作: {target} を記入してから、以下を実行してください。")
    print(f"  python run_imperial_pipeline.py projects/{slug}/input/project_input.yaml --stage draft")
    return 0


def parse_steps(value: str | None) -> set[int] | None:
    if not value:
        return None
    steps: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, _, end = part.partition("-")
            steps.update(range(int(start), int(end) + 1))
        else:
            steps.add(int(part))
    return steps or None


def gather_data(project_root: Path) -> dict:
    """台帳類を読み込む."""
    fact_rows = id_assigner.read_csv_rows(project_root / "research" / "05_事実台帳.csv")
    material_rows = id_assigner.read_csv_rows(project_root / "research" / "06_素材権利台帳.csv")
    source_rows = id_assigner.read_csv_rows(project_root / "research" / "04_出典一覧.csv")
    visual_rows = id_assigner.read_csv_rows(project_root / "production" / "12_長尺素材設計.csv")
    shorts_rows = id_assigner.read_csv_rows(project_root / "production" / "13_Shorts素材設計.csv")
    script_path = project_root / "scripts" / "10A_長尺台本_監査用.md"
    script_text = script_path.read_text(encoding=ENC) if script_path.exists() else ""
    return {
        "fact_rows": fact_rows,
        "material_rows": material_rows,
        "source_rows": source_rows,
        "visual_rows": visual_rows,
        "shorts_rows": shorts_rows,
        "script_text": script_text,
        "script_path": script_path,
    }


def run_checks(project_root: Path, configs: dict, data: dict, project) -> dict:
    """機械検出をまとめて実行する."""
    forbidden_result = forbidden_checker.scan_project(project_root, configs["forbidden"])
    required_result = required_checker.check_project(project_root, configs["required"])
    cross_check = id_assigner.cross_check_script_ids(
        data["script_text"], data["fact_rows"], data["material_rows"]
    )
    honorific_findings = forbidden_checker.check_honorifics(
        data["script_text"], configs["honorifics"]
    )
    char_count = approval_builder.count_script_chars(data["script_path"])
    cpm = int(configs["settings"].get("chars_per_minute", 300) or 300)

    flags = {
        "forbidden_blocking": len(forbidden_result.blocking),
        "forbidden_review": len(forbidden_result.review_needed),
        "required_missing": len(required_result.blocking),
        "unusable_facts": cross_check["unusable_facts"],
        "missing_facts": cross_check["missing_facts"],
        "unusable_materials": cross_check["unusable_materials"],
        "fake_urls": approval_builder.find_fake_urls(project_root),
        "ai_face": approval_builder.find_ai_face_materials(data["material_rows"]),
        "honorifics": honorific_findings,
        "tags": approval_builder.count_unconfirmed_tags(project_root),
        "char_count": char_count,
        "char_target": f"{project.target_length_min * cpm:,}〜{project.target_length_max * cpm:,}字",
    }
    return {
        "forbidden": forbidden_result,
        "required": required_result,
        "cross_check": cross_check,
        "flags": flags,
        "char_count": char_count,
    }


def id_audit_report(data: dict) -> str:
    lines = ["| 台帳 | 件数 | 重複 | 書式違反 | 欠番 | 次のID |", "| --- | --- | --- | --- | --- | --- |"]
    for label, rows, column, prefix in (
        ("事実台帳", data["fact_rows"], "事実ID", "F"),
        ("素材権利台帳", data["material_rows"], "素材ID", "M"),
        ("出典一覧", data["source_rows"], "出典ID", "S"),
    ):
        audit = id_assigner.audit_ids(rows, column, prefix)
        lines.append(
            f"| {label} | {audit['count']} | {'、'.join(audit['duplicates']) or 'なし'} | "
            f"{'、'.join(audit['invalid']) or 'なし'} | {'、'.join(audit['gaps']) or 'なし'} | "
            f"{audit['next']} |"
        )
    return "\n".join(lines)


def print_report(stage: str, checks: dict, extra_lines: list[str]) -> None:
    print()
    print("=" * 60)
    print(f"  実行結果（stage: {stage}）")
    print("=" * 60)
    forbidden = checks["forbidden"]
    required = checks["required"]
    print(f"  禁止表現の検出　　: 使用禁止相当 {len(forbidden.blocking)}件 / 要文脈確認 {len(forbidden.review_needed)}件")
    print(f"  必須項目の欠落　　: {len(required.blocking)}件")
    print(f"  未生成ファイル　　: {len(required.missing_files)}件")
    print(f"  長尺台本の文字数　: {checks['char_count']}字（目標 {checks['flags']['char_target']}）")
    for line in extra_lines:
        print(f"  {line}")
    print("=" * 60)


# ---------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="日本が誇る皇室物語 制作支援システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="?", help="projects/<slug>/input/project_input.yaml")
    parser.add_argument("--stage", choices=["draft", "check", "final"], default="draft")
    parser.add_argument("--approval", help="承認ファイル（--stage final で必須）")
    parser.add_argument("--init", metavar="SLUG", help="新規プロジェクトを作成する")
    parser.add_argument("--steps", help="対象工程（例: 1,2,3 または 1-5）")
    parser.add_argument("--refresh", action="store_true",
                        help="既存の成果物を _history へ退避してテンプレートから再生成する")
    parser.add_argument("--quiet", action="store_true", help="標準出力へのログを抑制する")
    args = parser.parse_args(argv)

    log = logger_module.RunLogger(ROOT / "logs", quiet=args.quiet)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")

    if args.init:
        log.section(f"新規プロジェクト作成: {args.init}")
        return init_project(args.init, log)

    if not args.input:
        parser.print_help()
        return 1

    log.section(f"開始 stage={args.stage}")

    # --- 設定 --------------------------------------------------------
    try:
        configs = load_configs()
    except FileNotFoundError as error:
        log.error(f"設定ファイルの読み込みに失敗しました: {error}")
        return 1
    settings = configs["settings"]

    if not input_parser.HAS_PYYAML:
        log.warn("PyYAML が見つからないため簡易パーサで動作しています（README参照）。")

    # --- 入力 --------------------------------------------------------
    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"入力ファイルが見つかりません: {input_path}")
        return 1
    try:
        project = input_parser.load_project_input(input_path)
    except Exception as error:  # 読み込み失敗は隠さない
        log.error(f"入力ファイルの読み込みに失敗しました: {error}")
        return 1

    input_spec = (configs["required"].get("input") or {}).get("input/project_input.yaml", {})
    validation = project.validate(
        input_spec.get("required") or ["project_name", "project_slug", "channel", "theme"],
        input_spec.get("recommended") or [],
    )
    for message in validation["errors"]:
        log.error(message)
    for message in validation["warnings"]:
        log.warn(message)

    slug = project.project_slug
    if not slug:
        log.error("project_slug が未入力のため処理を続行できません。")
        return 1

    project_root = scaffold.ensure_project_dirs(ROOT, slug)

    # 入力ファイルがプロジェクト外にある場合は input/ へ複製する
    canonical_input = project_root / "input" / "project_input.yaml"
    if input_path.resolve() != canonical_input.resolve():
        if canonical_input.exists():
            scaffold.backup_to_history(ROOT, slug, [canonical_input], stamp, log)
        shutil.copy2(input_path, canonical_input)
        log.info(f"入力ファイルを複製: {canonical_input.relative_to(ROOT)}")
    scaffold.ensure_input_files(ROOT, slug, log)

    if project.sample_mode:
        log.warn("sample_mode: true — 全生成物へ【サンプル・ダミーデータ】表示を付与します。")

    # --- 承認 --------------------------------------------------------
    approval: dict = {}
    if args.stage == "final":
        if not args.approval:
            log.error("--stage final には --approval が必要です。")
            return 1
        approval_path = Path(args.approval)
        if not approval_path.exists():
            log.error(f"承認ファイルが見つかりません: {approval_path}")
            return 1
        approval = input_parser.load_approval(approval_path)
        status = str(approval.get("approval_status") or "").strip().lower()
        if status != "approved":
            log.error(
                f"approval_status が approved ではありません（現在: {approval.get('approval_status')}）。"
                "最終版は生成しません。"
            )
            return 2
        log.info(f"承認を確認しました: title={approval.get('selected_title') or '【未指定】'}")

    # --- 文脈 --------------------------------------------------------
    network_status = detect_network_status()
    past_videos_path = project_root / "input" / "past_videos.csv"
    duplication = duplication_checker.check(
        past_videos_path,
        str(project.get("theme", "") or ""),
        str(project.get("working_title", "") or ""),
        str(project.get("main_person", "") or ""),
    )
    context = scaffold.build_context(
        settings, project, network_status, duplication["status"], approval
    )

    # --- テンプレート出力（draft のみ） ------------------------------
    emitted = {"created": [], "kept": [], "refreshed": [], "missing_template": []}
    if args.stage == "draft":
        steps = parse_steps(args.steps)
        emitted = scaffold.emit_artifacts(
            ROOT, slug, context, steps, args.refresh, stamp, log
        )
        log.info(
            f"テンプレート出力: 新規 {len(emitted['created'])}件 / "
            f"再生成 {len(emitted['refreshed'])}件 / 既存維持 {len(emitted['kept'])}件"
        )
        # 工程2の機械参考判定を書き込む
        scaffold.update_machine_block(
            project_root / "research" / "02_既存動画重複確認.md",
            "duplication",
            duplication_checker.to_markdown(duplication),
        )

    # --- 検査 --------------------------------------------------------
    data = gather_data(project_root)
    checks = run_checks(project_root, configs, data, project)

    # 台本の文字数を 10A へ反映
    scaffold.update_machine_block(
        data["script_path"], "charcount",
        f"{checks['char_count']}字（目標 {checks['flags']['char_target']}）",
    )

    # 機械検出レポート
    report = approval_builder.build_machine_report(
        project_root, checks["forbidden"], checks["required"], duplication,
        checks["cross_check"], checks["flags"], context["GENERATED_AT"], project.sample_mode,
    )
    report += "\n\n## 7. ID採番の状況\n\n" + id_audit_report(data) + "\n"
    library_issues = required_checker.check_library(
        ROOT / "library" / "approved_materials.csv", configs["required"]
    )
    report += "\n## 8. 安全素材ライブラリ\n\n"
    library_rows = id_assigner.read_csv_rows(ROOT / "library" / "approved_materials.csv")
    report += f"- 登録済み素材：{len(library_rows)}件\n"
    if len(library_rows) == 0:
        report += ("- **ライブラリが空である。** 素材設計は図解・テロップ中心で構成し、"
                   "「素材不足」を隠さず明記すること（第0章 0-4）。\n")
    for issue in library_issues:
        report += f"- {issue.severity}: {issue.detail}\n"
    scaffold.write_text(project_root / "audit" / "00_機械検出レポート.md", report)
    log.info("機械検出レポートを出力: audit/00_機械検出レポート.md")

    # 承認用サマリー・監査ファイルへの反映
    approval_builder.update_summary(
        project_root, data["fact_rows"], data["material_rows"],
        data["visual_rows"], checks["flags"], log,
    )

    for issue in checks["required"].blocking:
        log.warn(f"必須項目の欠落: {issue.path} — {issue.detail}")
    for hit in checks["forbidden"].blocking:
        log.warn(f"禁止表現: {hit.path}:{hit.line_no} 「{hit.term}」")

    # --- 最終版 ------------------------------------------------------
    extra_lines: list[str] = []
    exit_code = 0
    if args.stage == "final":
        log.section("最終パッケージの生成")
        result = package_builder.build(
            ROOT, slug, settings, context, approval,
            data["fact_rows"], data["material_rows"], checks["cross_check"],
            project.sample_mode, stamp, log,
        )
        if result.blocked:
            print()
            print("!" * 60)
            print("  最終パッケージの生成をブロックしました。")
            for reason in result.blockers:
                print(f"   - {reason}")
            print("!" * 60)
            exit_code = 3
        else:
            for warning in result.warnings:
                log.warn(warning)
            extra_lines.append(f"最終版ファイル　　: {len(result.written)}件を生成")
            if result.missing_sources:
                extra_lines.append(
                    f"元ファイル不足　　: {', '.join(result.missing_sources)}"
                )
            log.info(f"最終パッケージ生成完了: {len(result.written)}件")
    else:
        extra_lines.append(
            f"テンプレート　　　: 新規 {len(emitted['created'])} / "
            f"再生成 {len(emitted['refreshed'])} / 既存維持 {len(emitted['kept'])}"
        )

    print_report(args.stage, checks, extra_lines)

    if args.stage == "draft":
        print()
        print("  次の操作:")
        print("   1. サブエージェントで各工程を実行し、生成されたファイルを記入する")
        print("      （agents/ と commands/ の定義を参照）")
        print(f"   2. audit/19_荒木承認用サマリー.md を確認する")
        print(f"   3. projects/{slug}/input/approval.yaml を記入する")
        print(f"   4. python run_imperial_pipeline.py {args.input} "
              f"--stage final --approval projects/{slug}/input/approval.yaml")
        print()

    log.summary()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
