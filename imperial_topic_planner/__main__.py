"""CLI entry point: python -m imperial_topic_planner."""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config as cfg
from .input_loader import load_input
from .topics import generate_candidates_from_input, _build_test_sample_input
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
    write_topic_plan_json,
)


def main():
    parser = argparse.ArgumentParser(
        description="皇室系YouTube企画作成システム",
    )
    parser.add_argument("--production", action="store_true",
                        help="本番モードで実行")
    parser.add_argument("--test", action="store_true",
                        help="テストモードで実行（サンプルデータ使用）")
    parser.add_argument("--input", type=str, default=None,
                        help="入力JSONファイルのパス（topic_input.json）")
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

    if args.input:
        logger.info(f"入力ファイル: {args.input}")
        input_data = load_input(args.input)
    else:
        logger.info("入力ファイル未指定 → サンプルデータ使用（production_readyにはなりません）")
        input_data = _build_test_sample_input()
        for idea in input_data.get("topic_ideas", []):
            idea["_is_sample"] = True

    data_origin = f"入力ファイル ({args.input})" if args.input else "サンプルデータ（テスト専用）"
    logger.info(f"データ由来: {data_origin}")
    logger.info(f"企画アイデア数: {len(input_data.get('topic_ideas', []))}件")

    logger.info("[1/10] 企画候補生成・採点・選別...")
    result = generate_candidates_from_input(input_data)
    candidates = result["candidates"]
    selected = result["selected"]
    held = result["held"]
    rejected = result["rejected"]

    if not args.input:
        for c in candidates:
            c["data_source"] = "test_sample"

    logger.info(f"  候補: {len(candidates)}本, 採用: {len(selected)}本, "
                f"保留: {len(held)}本, 不採用: {len(rejected)}本")
    for c in candidates:
        src = "入力JSON" if c.get("data_source") != "test_sample" else "サンプル"
        logger.info(f"  {c['id']}: {c['title']} [{src}] → {c['status']} ({c['total_score']}点)")

    logger.info("[2/10] 01_topic_candidates.md 生成...")
    write_topic_candidates(candidates, output_dir)

    logger.info("[3/10] 02_selected_topics.md 生成...")
    write_selected_topics(selected, output_dir)

    logger.info("[4/10] 03_rejected_topics.md 生成...")
    write_rejected_topics(rejected, held, output_dir)

    logger.info("[5/10] 04_fact_source_plan.md 生成...")
    write_fact_source_plan(selected, input_data, output_dir)

    logger.info("[6/10] 05_long_video_plan.md / 06_shorts_plan.md 生成...")
    write_long_video_plan(selected, output_dir)
    write_shorts_plan(selected, output_dir)

    logger.info("[7/10] 07_title_thumbnail_plan.md 生成...")
    write_title_thumbnail_plan(selected, output_dir)

    logger.info("[8/10] 08_risk_check_report.md 生成...")
    write_risk_check_report(selected, output_dir)

    logger.info("[9/10] 09_package_summary.md 生成...")
    summary = write_package_summary(result, input_data, mode, output_dir)

    logger.info("[10/10] topic_plan.json 生成...")
    write_topic_plan_json(result, input_data, mode, summary, output_dir)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"企画作成完了 ({elapsed:.1f}秒)")
    logger.info(f"  package_complete: {summary['package_complete']}")
    logger.info(f"  production_ready: {summary['production_ready']}")
    logger.info(f"  採用: {summary['selected_count']}本")
    logger.info(f"  保留: {summary['held_count']}本")
    logger.info(f"  不採用: {summary['rejected_count']}本")
    logger.info(f"  サンプルデータ: {'はい' if summary['is_sample'] else 'いいえ'}")
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
