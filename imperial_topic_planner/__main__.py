"""CLI entry point: python -m imperial_topic_planner."""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config as cfg
from .topics import generate_candidates
from .writers import (
    write_fact_source_plan,
    write_long_video_plan,
    write_package_summary,
    write_rejected_topics,
    write_risk_check_report,
    write_selected_topics,
    write_shorts_plan,
    write_title_thumbnail_plan,
    write_topic_candidates,
)


def main():
    parser = argparse.ArgumentParser(
        description="皇室系YouTube企画作成システム",
    )
    parser.add_argument("--production", action="store_true",
                        help="本番モードで実行")
    parser.add_argument("--test", action="store_true",
                        help="テストモードで実行")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="出力ディレクトリ（省略時は自動生成）")
    args = parser.parse_args()

    if args.production:
        mode = "production"
    else:
        mode = "test"

    project_root = Path(__file__).resolve().parent.parent
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "output" / "topic_plans" / f"{timestamp}_plan"
    output_dir.mkdir(parents=True, exist_ok=True)

    log_path = output_dir / "execution.log"
    logger = logging.getLogger("imperial_topic_planner")
    logger.setLevel(logging.INFO)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    fh = logging.FileHandler(str(log_path), encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(sh)

    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"企画作成開始 モード={mode}")
    logger.info(f"チャンネル: {cfg.CHANNEL_NAME}")
    logger.info(f"出力先: {output_dir}")
    logger.info("=" * 60)

    logger.info("[1/9] 企画候補生成...")
    result = generate_candidates()
    candidates = result["candidates"]
    selected = result["selected"]
    rejected = result["rejected"]
    logger.info(f"  候補: {len(candidates)}本, 採用: {len(selected)}本, 不採用: {len(rejected)}本")

    logger.info("[2/9] 01_topic_candidates.md 生成...")
    write_topic_candidates(candidates, output_dir)

    logger.info("[3/9] 02_selected_topics.md 生成...")
    write_selected_topics(selected, output_dir)

    logger.info("[4/9] 03_rejected_topics.md 生成...")
    write_rejected_topics(rejected, output_dir)

    logger.info("[5/9] 04_fact_source_plan.md 生成...")
    write_fact_source_plan(selected, output_dir)

    logger.info("[6/9] 05_long_video_plan.md / 06_shorts_plan.md 生成...")
    write_long_video_plan(selected, output_dir)
    write_shorts_plan(selected, output_dir)

    logger.info("[7/9] 07_title_thumbnail_plan.md 生成...")
    write_title_thumbnail_plan(selected, output_dir)

    logger.info("[8/9] 08_risk_check_report.md 生成...")
    write_risk_check_report(selected, output_dir)

    logger.info("[9/9] 09_package_summary.md 生成...")
    summary = write_package_summary(selected, rejected, mode, output_dir)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"企画作成完了 ({elapsed:.1f}秒)")
    logger.info(f"  package_complete: {summary['package_complete']}")
    logger.info(f"  production_ready: {summary['production_ready']}")
    logger.info(f"  採用: {summary['selected_count']}本")
    logger.info(f"  不採用: {summary['rejected_count']}本")
    logger.info("=" * 60)

    generated = sorted(f.name for f in output_dir.iterdir() if f.is_file())
    logger.info(f"生成ファイル ({len(generated)}件):")
    for fname in generated:
        size = (output_dir / fname).stat().st_size
        logger.info(f"  {fname} ({size} bytes)")

    zero_files = [f.name for f in output_dir.iterdir()
                  if f.is_file() and f.stat().st_size == 0]
    if zero_files:
        logger.warning(f"0KBファイル検出: {zero_files}")

    return 0 if summary["package_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
