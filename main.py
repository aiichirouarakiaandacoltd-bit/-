#!/usr/bin/env python3
"""Imperial Video Automation - 外注向け制作パッケージ生成システム

Usage:
    python main.py --theme "テーマ" --mode test
    python main.py --theme "テーマ" --mode production
    python main.py --help
"""
import argparse
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg


def setup_logging(output_dir):
    log_path = output_dir / "execution.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("imperial"), log_path


def generate_run_id(theme):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = theme[:30].replace(" ", "_").replace("/", "_").replace("\\", "_")
    return f"{ts}_{safe}"


def consolidate_research(output_dir, logger):
    """Merge research_report.md, fact_check.json, sources.csv into 01_research_report.md."""
    parts = []

    report_path = output_dir / "research_report.md"
    if report_path.exists():
        parts.append(report_path.read_text(encoding="utf-8"))

    fc_path = output_dir / "fact_check.json"
    if fc_path.exists():
        parts.append("\n---\n\n## ファクトチェック詳細（JSON）\n")
        parts.append("```json")
        parts.append(fc_path.read_text(encoding="utf-8"))
        parts.append("```")

    src_path = output_dir / "sources.csv"
    if src_path.exists():
        parts.append("\n---\n\n## 出典一覧（CSV）\n")
        parts.append("```csv")
        parts.append(src_path.read_text(encoding="utf-8"))
        parts.append("```")

    if parts:
        (output_dir / "01_research_report.md").write_text(
            "\n".join(parts), encoding="utf-8"
        )
        logger.info("01_research_report.md 生成完了")


def consolidate_scripts(output_dir, logger):
    """Merge long_script.txt + shorts scripts into 02_narration_script.md."""
    parts = ["# ナレーション台本\n"]

    long_path = output_dir / "long_script.txt"
    if long_path.exists():
        parts.append("## 長尺台本\n")
        parts.append(long_path.read_text(encoding="utf-8"))

    for i in range(1, 3):
        sp = output_dir / f"shorts_{i:02d}_script.txt"
        if sp.exists():
            parts.append(f"\n---\n\n## Shorts {i:02d} 台本\n")
            parts.append(sp.read_text(encoding="utf-8"))

    if len(parts) > 1:
        (output_dir / "02_narration_script.md").write_text(
            "\n".join(parts), encoding="utf-8"
        )
        logger.info("02_narration_script.md 生成完了")


def consolidate_instructions(output_dir, logger):
    """Merge video + thumbnail instructions into 03_editing_instructions.md."""
    parts = []

    vi_path = output_dir / "video_editing_instructions.md"
    if vi_path.exists():
        parts.append(vi_path.read_text(encoding="utf-8"))

    ti_path = output_dir / "thumbnail_instructions.md"
    if ti_path.exists():
        parts.append("\n---\n")
        parts.append(ti_path.read_text(encoding="utf-8"))

    if parts:
        (output_dir / "03_editing_instructions.md").write_text(
            "\n".join(parts), encoding="utf-8"
        )
        logger.info("03_editing_instructions.md 生成完了")


def consolidate_materials(output_dir, logger):
    """Merge material_urls.csv + rights_report.md into 04_materials_list.md."""
    parts = ["# 素材・権利情報\n"]

    csv_path = output_dir / "material_urls.csv"
    if csv_path.exists():
        parts.append("## 素材URL一覧\n")
        parts.append("```csv")
        parts.append(csv_path.read_text(encoding="utf-8"))
        parts.append("```\n")

    rr_path = output_dir / "rights_report.md"
    if rr_path.exists():
        parts.append("---\n")
        parts.append(rr_path.read_text(encoding="utf-8"))

    if len(parts) > 1:
        (output_dir / "04_materials_list.md").write_text(
            "\n".join(parts), encoding="utf-8"
        )
        logger.info("04_materials_list.md 生成完了")


def rename_ng_report(output_dir, logger):
    """Rename ng_expression_report.md to 07_ng_check_report.md."""
    src = output_dir / "ng_expression_report.md"
    if src.exists():
        content = src.read_text(encoding="utf-8")
        (output_dir / "07_ng_check_report.md").write_text(content, encoding="utf-8")
        logger.info("07_ng_check_report.md 生成完了")


def cleanup_intermediate(output_dir):
    """Remove intermediate files, keeping only numbered outputs and metadata."""
    keep_prefixes = ("01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_",
                     "metadata.json", "execution.log")
    for f in output_dir.iterdir():
        if f.is_file() and not any(f.name.startswith(p) for p in keep_prefixes):
            f.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Imperial Video Automation - 外注向け制作パッケージ生成"
    )
    parser.add_argument("--theme", required=True, help="企画テーマ")
    parser.add_argument(
        "--mode", choices=["test", "production"], default="test",
        help="test: 動作確認用 / production: 本番用（出典確認必須）"
    )
    args = parser.parse_args()

    run_id = generate_run_id(args.theme)
    output_dir = cfg.OUTPUT_PACKAGES_DIR / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    logger, log_path = setup_logging(output_dir)

    logger.info("=" * 60)
    logger.info(f"制作パッケージ生成開始")
    logger.info(f"  テーマ: {args.theme}")
    logger.info(f"  モード: {args.mode}")
    logger.info(f"  出力先: {output_dir}")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        from src.research import (
            research_topic, generate_research_report,
            generate_fact_check, generate_sources_csv,
        )
        from src.script_writer import generate_long_script, generate_shorts_scripts
        from src.instructions import (
            generate_video_instructions, generate_thumbnail_instructions,
        )
        from src.materials import generate_material_urls_csv, generate_rights_report
        from src.ng_check import check_ng_expressions
        from src.posting import generate_posting_package
        from src.bgm_config import load_bgm_config, generate_bgm_and_credits
        from src.validators import (
            validate_package, write_status_json, generate_package_summary,
        )

        logger.info("[1/8] 出典調査・ファクトチェック...")
        research_data = research_topic(args.theme, output_dir)
        generate_research_report(research_data, output_dir)
        generate_fact_check(research_data, output_dir)
        generate_sources_csv(research_data, output_dir)
        consolidate_research(output_dir, logger)

        logger.info("[2/8] ナレーション台本作成...")
        generate_long_script(args.theme, research_data, output_dir)
        generate_shorts_scripts(args.theme, research_data, output_dir)
        consolidate_scripts(output_dir, logger)

        logger.info("[3/8] 編集指示書・サムネイル指示書作成...")
        generate_video_instructions(args.theme, research_data, output_dir)
        generate_thumbnail_instructions(args.theme, research_data, output_dir)
        consolidate_instructions(output_dir, logger)

        logger.info("[4/8] 素材候補・権利レポート作成...")
        materials_data = generate_material_urls_csv(args.theme, research_data, output_dir)

        logger.info("[5/8] 投稿用文面作成...")
        bgm_config = load_bgm_config()
        posting_result = generate_posting_package(
            args.theme, research_data, bgm_config, output_dir
        )

        logger.info("[6/8] BGM・クレジット設定...")
        generate_bgm_and_credits(bgm_config, output_dir)

        logger.info("[7/8] NG表現チェック...")
        long_script_path = output_dir / "long_script.txt"
        script_text = ""
        if long_script_path.exists():
            script_text = long_script_path.read_text(encoding="utf-8")

        title_candidates = [t["title"] for t in posting_result.get("titles", [])]

        desc_lines = []
        posting_path = output_dir / "05_posting_package.md"
        if posting_path.exists():
            desc_lines = [posting_path.read_text(encoding="utf-8")]

        ng_results = check_ng_expressions(
            script_text, title_candidates, "\n".join(desc_lines),
            output_dir, research_data=research_data,
        )

        ng_data = ng_results if isinstance(ng_results, dict) else {"findings": []}

        rights_data = generate_rights_report(materials_data, ng_data, output_dir)
        consolidate_materials(output_dir, logger)
        rename_ng_report(output_dir, logger)

        cleanup_intermediate(output_dir)

        logger.info("[8/8] パッケージ検証・サマリー生成...")
        status = validate_package(
            output_dir, research_data, ng_data, bgm_config,
            args.theme, topic_source="manual", mode=args.mode,
        )

        generate_package_summary(
            args.theme, research_data, ng_data, bgm_config, status, output_dir
        )
        write_status_json(status, output_dir)

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"制作パッケージ生成完了 ({elapsed:.1f}秒)")
        logger.info(f"  出力先: {output_dir}")
        logger.info(f"  package_complete: {status.get('package_complete')}")
        logger.info(f"  production_ready: {status.get('production_ready')}")
        logger.info(f"  manual_review_required: {status.get('manual_review_required')}")

        missing = status.get("missing_items", [])
        if missing:
            logger.info(f"  不足項目:")
            for item in missing:
                logger.info(f"    - {item}")

        logger.info("=" * 60)

        final_files = sorted(f.name for f in output_dir.iterdir() if f.is_file())
        logger.info(f"生成ファイル ({len(final_files)}件):")
        for f in final_files:
            size = (output_dir / f).stat().st_size
            logger.info(f"  {f} ({size} bytes)")

        zero_files = [f for f in final_files if (output_dir / f).stat().st_size == 0]
        if zero_files:
            logger.error(f"0KBファイル検出: {zero_files}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"エラー: {e}", exc_info=True)
        error_status = {
            "project_name": "imperial-video-automation",
            "topic": args.theme,
            "mode": args.mode,
            "package_complete": False,
            "production_ready": False,
            "error": str(e),
            "created_at": datetime.now().isoformat(),
        }
        (output_dir / "metadata.json").write_text(
            json.dumps(error_status, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
