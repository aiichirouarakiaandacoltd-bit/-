#!/usr/bin/env python3
"""
main.py - Entry point for showa-heisei-video-automation
YouTube channel: 昭和・平成 なぜそうだったのか

Usage:
  python main.py --topic "なぜ昔のテレビには布をかけていたのか"
  python main.py --topic "なぜ昔のテレビには布をかけていたのか" --mode test
  python main.py --topic "なぜ昔のテレビには布をかけていたのか" --test-mode
  python main.py --script-file inputs/script.txt --mode production
  python main.py --preflight
  python main.py --preflight --mode test
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime

import yaml

# ---------------------------------------------------------------------------
# Project root and path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from modules.preflight import run_preflight, format_preflight_report
from modules.planner import run_planner
from modules.researcher import run_researcher
from modules.scriptwriter import run_scriptwriter

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(project_root):
    """Load settings.yaml and speakers.yaml."""
    settings_path = os.path.join(project_root, "config", "settings.yaml")
    speakers_path = os.path.join(project_root, "config", "speakers.yaml")

    with open(settings_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    with open(speakers_path, "r", encoding="utf-8") as f:
        speakers_config = yaml.safe_load(f)

    return config, speakers_config


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(output_dir):
    """Configure logging to both console and file."""
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "execution.log")

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler (detailed)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root_logger.addHandler(fh)

    # Console handler (info and above)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    root_logger.addHandler(ch)

    return log_path


# ---------------------------------------------------------------------------
# Output directory creation
# ---------------------------------------------------------------------------

def create_output_dir(project_root, mode):
    """Create timestamped output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = "production" if mode == "production" else "test"
    output_dir = os.path.join(project_root, "outputs", base, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# ---------------------------------------------------------------------------
# Status and report generation
# ---------------------------------------------------------------------------

def write_status(output_dir, status_data):
    """Write status.json."""
    path = os.path.join(output_dir, "status.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2, default=str)
    return path


def write_summary(output_dir, summary_data):
    """Write summary.md."""
    path = os.path.join(output_dir, "summary.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 制作サマリー\n\n")
        f.write(f"## 基本情報\n")
        f.write(f"- トピック: {summary_data.get('topic', 'N/A')}\n")
        f.write(f"- モード: {summary_data.get('mode', 'N/A')}\n")
        f.write(f"- 実行日時: {summary_data.get('timestamp', 'N/A')}\n")
        f.write(f"- 出力先: {summary_data.get('output_dir', 'N/A')}\n\n")

        if "evaluation" in summary_data:
            ev = summary_data["evaluation"]
            f.write(f"## トピック評価\n")
            f.write(f"- スコア: {ev.get('total_score', 'N/A')}/{ev.get('max_score', 'N/A')}\n")
            f.write(f"- 結果: {'合格' if ev.get('passed') else '不合格'}\n\n")

        if "titles" in summary_data:
            f.write(f"## タイトル\n")
            f.write(f"- メイン: {summary_data['titles'].get('main_title', 'N/A')}\n\n")

        if "research" in summary_data:
            rs = summary_data["research"]
            f.write(f"## リサーチ\n")
            f.write(f"- 調査方法: {rs.get('research_method', 'N/A')}\n")
            f.write(f"- 使用可能事実: {rs.get('usable_count', 0)}件\n\n")

        if "scripts" in summary_data:
            sc = summary_data["scripts"]
            f.write(f"## 台本\n")
            dur = sc.get("durations", {})
            f.write(f"- 長尺: 推定{dur.get('long_minutes', 0):.1f}分\n")
            f.write(f"- Shorts 1: 推定{dur.get('short_01_seconds', 0):.0f}秒\n")
            f.write(f"- Shorts 2: 推定{dur.get('short_02_seconds', 0):.0f}秒\n\n")

        if "pipeline_steps" in summary_data:
            f.write(f"## パイプライン実行状況\n")
            for step in summary_data["pipeline_steps"]:
                status_mark = "完了" if step.get("success") else "スキップ/エラー"
                f.write(f"- {step['name']}: {status_mark}\n")
                if step.get("note"):
                    f.write(f"  - {step['note']}\n")
            f.write("\n")

        if "errors" in summary_data and summary_data["errors"]:
            f.write(f"## エラー\n")
            for err in summary_data["errors"]:
                f.write(f"- {err}\n")
            f.write("\n")

    return path


# ---------------------------------------------------------------------------
# Pipeline steps (stubs for unimplemented stages)
# ---------------------------------------------------------------------------

def run_voicevox_generation(config, speakers_config, scripts, output_dir, mode):
    """VOICEVOX audio generation step."""
    logger = logging.getLogger("voicevox")
    if mode == "test":
        logger.info("テストモード: VOICEVOX音声生成をスキップします")
        return {"success": True, "skipped": True, "note": "テストモード: スキップ"}

    logger.info("VOICEVOX音声生成: 将来のバージョンで実装予定")
    return {"success": True, "skipped": True, "note": "未実装: 将来バージョンで対応"}


def run_subtitle_generation(config, scripts, output_dir, mode):
    """Subtitle generation step."""
    logger = logging.getLogger("subtitles")
    if mode == "test":
        logger.info("テストモード: 字幕生成をスキップします")
        return {"success": True, "skipped": True, "note": "テストモード: スキップ"}

    logger.info("字幕生成: 将来のバージョンで実装予定")
    return {"success": True, "skipped": True, "note": "未実装: 将来バージョンで対応"}


def run_image_generation(topic, scripts, output_dir, mode):
    """Image/material generation step."""
    logger = logging.getLogger("images")
    if mode == "test":
        logger.info("テストモード: 画像生成をスキップします")
        return {"success": True, "skipped": True, "note": "テストモード: スキップ"}

    logger.info("画像・素材生成: 将来のバージョンで実装予定")
    return {"success": True, "skipped": True, "note": "未実装: 将来バージョンで対応"}


def run_bgm_handling(config, output_dir, mode):
    """BGM handling step."""
    logger = logging.getLogger("bgm")
    bgm_dir = os.path.join(PROJECT_ROOT, "assets", "bgm")
    audio_exts = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}

    if os.path.isdir(bgm_dir):
        bgm_files = [
            f for f in os.listdir(bgm_dir)
            if os.path.splitext(f)[1].lower() in audio_exts
        ]
        if bgm_files:
            logger.info(f"BGMファイル検出: {len(bgm_files)}件")
            return {
                "success": True,
                "skipped": False,
                "bgm_files": bgm_files,
                "note": f"BGM {len(bgm_files)}件検出",
            }

    if mode == "test":
        logger.info("テストモード: BGMなしで続行")
        return {"success": True, "skipped": True, "note": "テストモード: BGMなし"}

    logger.warning("BGMファイルが見つかりません")
    return {"success": True, "skipped": True, "note": "BGMファイルなし"}


def run_video_composition(config, output_dir, mode):
    """Video composition step (long + 2 shorts)."""
    logger = logging.getLogger("video")
    if mode == "test":
        logger.info("テストモード: 動画合成をスキップします")
        return {"success": True, "skipped": True, "note": "テストモード: スキップ"}

    logger.info("動画合成: 将来のバージョンで実装予定")
    return {"success": True, "skipped": True, "note": "未実装: 将来バージョンで対応"}


def run_quality_checks(config, output_dir, mode):
    """Quality checks step."""
    logger = logging.getLogger("quality")
    if mode == "test":
        logger.info("テストモード: 品質チェックをスキップします")
        return {"success": True, "skipped": True, "note": "テストモード: スキップ"}

    logger.info("品質チェック: 将来のバージョンで実装予定")
    return {"success": True, "skipped": True, "note": "未実装: 将来バージョンで対応"}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(topic, script_file, mode, config, speakers_config, output_dir):
    """Execute the full production pipeline."""
    logger = logging.getLogger("pipeline")
    logger.info(f"パイプライン開始: モード={mode}")
    if topic:
        logger.info(f"トピック: {topic}")
    if script_file:
        logger.info(f"スクリプトファイル: {script_file}")

    summary_data = {
        "topic": topic or "(スクリプトファイルから)",
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "output_dir": output_dir,
        "pipeline_steps": [],
        "errors": [],
    }

    status_data = {
        "status": "running",
        "mode": mode,
        "topic": topic,
        "started_at": datetime.now().isoformat(),
        "steps": {},
    }

    # -----------------------------------------------------------------------
    # Step 1: Planning / Evaluation (topic mode only)
    # -----------------------------------------------------------------------
    if topic and not script_file:
        logger.info("=" * 60)
        logger.info("ステップ1: トピック評価・企画")
        logger.info("=" * 60)
        try:
            planner_result = run_planner(topic, config, output_dir)
            evaluation = planner_result["evaluation"]
            titles = planner_result["titles"]
            summary_data["evaluation"] = evaluation
            summary_data["titles"] = titles
            status_data["steps"]["planning"] = {
                "status": "completed",
                "score": evaluation["total_score"],
                "passed": evaluation["passed"],
            }
            summary_data["pipeline_steps"].append({
                "name": "トピック評価・企画",
                "success": True,
                "note": f"スコア {evaluation['total_score']}/{evaluation['max_score']}",
            })

            if not evaluation["passed"]:
                logger.warning(
                    f"トピック評価不合格: {evaluation['total_score']}/"
                    f"{evaluation['max_score']} (基準: {evaluation['threshold']})"
                )
                logger.warning("パイプラインを続行しますが、トピックの見直しを検討してください")

        except Exception as e:
            logger.error(f"企画ステップでエラー: {e}")
            summary_data["errors"].append(f"企画エラー: {e}")
            summary_data["pipeline_steps"].append({
                "name": "トピック評価・企画",
                "success": False,
                "note": str(e),
            })
            status_data["steps"]["planning"] = {"status": "error", "error": str(e)}
    else:
        summary_data["pipeline_steps"].append({
            "name": "トピック評価・企画",
            "success": True,
            "note": "スクリプトファイルモード: スキップ",
        })

    # -----------------------------------------------------------------------
    # Step 2: Research and fact-check
    # -----------------------------------------------------------------------
    research_data = None
    if topic:
        logger.info("=" * 60)
        logger.info("ステップ2: リサーチ・ファクトチェック")
        logger.info("=" * 60)
        try:
            research_data = run_researcher(topic, mode, output_dir)
            summary_data["research"] = {
                "research_method": research_data["research_results"]["research_method"],
                "usable_count": len(research_data["usable_facts"]),
                "fact_stats": research_data["fact_stats"],
            }
            status_data["steps"]["research"] = {
                "status": "completed",
                "usable_facts": len(research_data["usable_facts"]),
            }
            summary_data["pipeline_steps"].append({
                "name": "リサーチ・ファクトチェック",
                "success": True,
                "note": f"使用可能事実 {len(research_data['usable_facts'])}件",
            })
        except Exception as e:
            logger.error(f"リサーチステップでエラー: {e}")
            summary_data["errors"].append(f"リサーチエラー: {e}")
            summary_data["pipeline_steps"].append({
                "name": "リサーチ・ファクトチェック",
                "success": False,
                "note": str(e),
            })
            status_data["steps"]["research"] = {"status": "error", "error": str(e)}

    # -----------------------------------------------------------------------
    # Step 3: Script writing
    # -----------------------------------------------------------------------
    script_data = None
    logger.info("=" * 60)
    logger.info("ステップ3: 台本作成")
    logger.info("=" * 60)

    if script_file:
        # Load existing script
        try:
            with open(script_file, "r", encoding="utf-8") as f:
                script_content = f.read()
            logger.info(f"スクリプトファイル読み込み完了: {script_file}")
            # Extract topic from script if not provided
            if not topic:
                # Try to extract from first heading
                for line in script_content.split("\n"):
                    if line.startswith("# ") and "なぜ" in line:
                        topic = line.lstrip("# ").strip()
                        break
                if not topic:
                    topic = "（スクリプトファイルから読み込み）"
            summary_data["topic"] = topic
            summary_data["pipeline_steps"].append({
                "name": "台本作成",
                "success": True,
                "note": "スクリプトファイルから読み込み",
            })
            status_data["steps"]["scriptwriting"] = {"status": "completed"}
        except Exception as e:
            logger.error(f"スクリプト読み込みエラー: {e}")
            summary_data["errors"].append(f"スクリプト読み込みエラー: {e}")
            summary_data["pipeline_steps"].append({
                "name": "台本作成",
                "success": False,
                "note": str(e),
            })
            status_data["steps"]["scriptwriting"] = {"status": "error", "error": str(e)}
    elif research_data:
        try:
            script_data = run_scriptwriter(topic, research_data, mode, output_dir)
            summary_data["scripts"] = {
                "durations": script_data["durations"],
                "files": list(script_data["file_paths"].keys()),
            }
            status_data["steps"]["scriptwriting"] = {
                "status": "completed",
                "durations": script_data["durations"],
            }
            summary_data["pipeline_steps"].append({
                "name": "台本作成",
                "success": True,
                "note": (
                    f"長尺 {script_data['durations']['long_minutes']:.1f}分, "
                    f"Shorts 1 {script_data['durations']['short_01_seconds']:.0f}秒, "
                    f"Shorts 2 {script_data['durations']['short_02_seconds']:.0f}秒"
                ),
            })
        except Exception as e:
            logger.error(f"台本作成エラー: {e}")
            summary_data["errors"].append(f"台本作成エラー: {e}")
            summary_data["pipeline_steps"].append({
                "name": "台本作成",
                "success": False,
                "note": str(e),
            })
            status_data["steps"]["scriptwriting"] = {"status": "error", "error": str(e)}
    else:
        logger.warning("リサーチデータなし: 台本作成をスキップ")
        summary_data["pipeline_steps"].append({
            "name": "台本作成",
            "success": False,
            "note": "リサーチデータなしのためスキップ",
        })

    # -----------------------------------------------------------------------
    # Step 4: VOICEVOX audio generation
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ4: VOICEVOX音声生成")
    logger.info("=" * 60)
    try:
        vv_result = run_voicevox_generation(
            config, speakers_config, script_data, output_dir, mode
        )
        status_data["steps"]["voicevox"] = {"status": "completed" if vv_result["success"] else "error"}
        summary_data["pipeline_steps"].append({
            "name": "VOICEVOX音声生成",
            "success": vv_result["success"],
            "note": vv_result.get("note", ""),
        })
    except Exception as e:
        logger.error(f"VOICEVOX音声生成エラー: {e}")
        summary_data["errors"].append(f"VOICEVOX音声生成エラー: {e}")
        summary_data["pipeline_steps"].append({
            "name": "VOICEVOX音声生成", "success": False, "note": str(e),
        })

    # -----------------------------------------------------------------------
    # Step 5: Subtitle generation
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ5: 字幕生成")
    logger.info("=" * 60)
    try:
        sub_result = run_subtitle_generation(config, script_data, output_dir, mode)
        status_data["steps"]["subtitles"] = {"status": "completed" if sub_result["success"] else "error"}
        summary_data["pipeline_steps"].append({
            "name": "字幕生成",
            "success": sub_result["success"],
            "note": sub_result.get("note", ""),
        })
    except Exception as e:
        logger.error(f"字幕生成エラー: {e}")
        summary_data["errors"].append(f"字幕生成エラー: {e}")
        summary_data["pipeline_steps"].append({
            "name": "字幕生成", "success": False, "note": str(e),
        })

    # -----------------------------------------------------------------------
    # Step 6: Image/material generation
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ6: 画像・素材生成")
    logger.info("=" * 60)
    try:
        img_result = run_image_generation(topic, script_data, output_dir, mode)
        status_data["steps"]["images"] = {"status": "completed" if img_result["success"] else "error"}
        summary_data["pipeline_steps"].append({
            "name": "画像・素材生成",
            "success": img_result["success"],
            "note": img_result.get("note", ""),
        })
    except Exception as e:
        logger.error(f"画像生成エラー: {e}")
        summary_data["errors"].append(f"画像生成エラー: {e}")
        summary_data["pipeline_steps"].append({
            "name": "画像・素材生成", "success": False, "note": str(e),
        })

    # -----------------------------------------------------------------------
    # Step 7: BGM handling
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ7: BGM処理")
    logger.info("=" * 60)
    try:
        bgm_result = run_bgm_handling(config, output_dir, mode)
        status_data["steps"]["bgm"] = {"status": "completed" if bgm_result["success"] else "error"}
        summary_data["pipeline_steps"].append({
            "name": "BGM処理",
            "success": bgm_result["success"],
            "note": bgm_result.get("note", ""),
        })
    except Exception as e:
        logger.error(f"BGM処理エラー: {e}")
        summary_data["errors"].append(f"BGM処理エラー: {e}")
        summary_data["pipeline_steps"].append({
            "name": "BGM処理", "success": False, "note": str(e),
        })

    # -----------------------------------------------------------------------
    # Step 8: Video composition (long + 2 shorts)
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ8: 動画合成")
    logger.info("=" * 60)
    try:
        vid_result = run_video_composition(config, output_dir, mode)
        status_data["steps"]["video"] = {"status": "completed" if vid_result["success"] else "error"}
        summary_data["pipeline_steps"].append({
            "name": "動画合成",
            "success": vid_result["success"],
            "note": vid_result.get("note", ""),
        })
    except Exception as e:
        logger.error(f"動画合成エラー: {e}")
        summary_data["errors"].append(f"動画合成エラー: {e}")
        summary_data["pipeline_steps"].append({
            "name": "動画合成", "success": False, "note": str(e),
        })

    # -----------------------------------------------------------------------
    # Step 9: Quality checks
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ9: 品質チェック")
    logger.info("=" * 60)
    try:
        qc_result = run_quality_checks(config, output_dir, mode)
        status_data["steps"]["quality"] = {"status": "completed" if qc_result["success"] else "error"}
        summary_data["pipeline_steps"].append({
            "name": "品質チェック",
            "success": qc_result["success"],
            "note": qc_result.get("note", ""),
        })
    except Exception as e:
        logger.error(f"品質チェックエラー: {e}")
        summary_data["errors"].append(f"品質チェックエラー: {e}")
        summary_data["pipeline_steps"].append({
            "name": "品質チェック", "success": False, "note": str(e),
        })

    # -----------------------------------------------------------------------
    # Step 10: Report generation
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("ステップ10: レポート生成")
    logger.info("=" * 60)

    status_data["status"] = "completed"
    status_data["completed_at"] = datetime.now().isoformat()
    status_data["errors"] = summary_data["errors"]

    status_path = write_status(output_dir, status_data)
    summary_path = write_summary(output_dir, summary_data)

    logger.info(f"ステータス出力: {status_path}")
    logger.info(f"サマリー出力: {summary_path}")

    summary_data["pipeline_steps"].append({
        "name": "レポート生成",
        "success": True,
        "note": f"status.json, summary.md 出力完了",
    })

    return summary_data


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="昭和・平成 なぜそうだったのか - 動画制作自動化ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py --topic "なぜ昔のテレビには布をかけていたのか"
  python main.py --topic "なぜ昔のテレビには布をかけていたのか" --mode test
  python main.py --topic "なぜ昔のテレビには布をかけていたのか" --test-mode
  python main.py --script-file inputs/my_script.txt
  python main.py --preflight
  python main.py --preflight --mode test
        """
    )
    parser.add_argument(
        "--topic", type=str, default=None,
        help="動画のトピック（例: 「なぜ昔のテレビには布をかけていたのか」）"
    )
    parser.add_argument(
        "--script-file", type=str, default=None,
        help="既存の台本ファイルパス"
    )
    parser.add_argument(
        "--mode", type=str, choices=["production", "test"], default="production",
        help="実行モード (production/test, デフォルト: production)"
    )
    parser.add_argument(
        "--test-mode", action="store_true",
        help="テストモードで実行（--mode test のエイリアス）"
    )
    parser.add_argument(
        "--preflight", action="store_true",
        help="プリフライトチェックのみ実行"
    )

    args = parser.parse_args()

    # --test-mode overrides --mode
    if args.test_mode:
        args.mode = "test"

    return args


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Main entry point."""
    args = parse_args()

    # Load config
    try:
        config, speakers_config = load_config(PROJECT_ROOT)
    except Exception as e:
        print(f"エラー: 設定ファイルの読み込みに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir = create_output_dir(PROJECT_ROOT, args.mode)

    # Setup logging
    log_path = setup_logging(output_dir)

    logger = logging.getLogger("main")
    logger.info("=" * 60)
    logger.info(f"昭和・平成 なぜそうだったのか - 動画制作自動化ツール")
    logger.info(f"モード: {args.mode}")
    logger.info(f"出力先: {output_dir}")
    logger.info("=" * 60)

    # -----------------------------------------------------------------------
    # Preflight mode
    # -----------------------------------------------------------------------
    if args.preflight:
        logger.info("プリフライトチェックを実行します")
        results = run_preflight(
            config, speakers_config, PROJECT_ROOT,
            mode=args.mode, script_file=args.script_file
        )
        report = format_preflight_report(results)
        print("\n" + report)
        logger.info("プリフライトチェック完了")

        # Save results
        preflight_path = os.path.join(output_dir, "preflight_results.json")
        with open(preflight_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"結果保存: {preflight_path}")

        if not results["passed"]:
            sys.exit(1)
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Validate arguments
    # -----------------------------------------------------------------------
    if not args.topic and not args.script_file:
        print("エラー: --topic または --script-file を指定してください", file=sys.stderr)
        logger.error("トピックまたはスクリプトファイルが指定されていません")
        sys.exit(1)

    if args.script_file and not os.path.isfile(args.script_file):
        abs_path = os.path.join(PROJECT_ROOT, args.script_file)
        if os.path.isfile(abs_path):
            args.script_file = abs_path
        else:
            print(f"エラー: スクリプトファイルが見つかりません: {args.script_file}",
                  file=sys.stderr)
            logger.error(f"スクリプトファイル未検出: {args.script_file}")
            sys.exit(1)

    # -----------------------------------------------------------------------
    # Run pipeline
    # -----------------------------------------------------------------------
    try:
        summary = run_pipeline(
            topic=args.topic,
            script_file=args.script_file,
            mode=args.mode,
            config=config,
            speakers_config=speakers_config,
            output_dir=output_dir,
        )

        error_count = len(summary.get("errors", []))
        if error_count > 0:
            logger.warning(f"パイプライン完了（エラー {error_count}件あり）")
            logger.warning("詳細は summary.md と status.json を確認してください")
        else:
            logger.info("パイプライン正常完了")

        logger.info(f"出力先: {output_dir}")
        logger.info(f"ログ: {log_path}")

    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました")
        print("\n中断されました。", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        logger.error(f"パイプラインで予期しないエラーが発生しました: {e}")
        logger.error(traceback.format_exc())
        print(f"\nエラーが発生しました: {e}", file=sys.stderr)
        print(f"詳細はログを確認してください: {log_path}", file=sys.stderr)

        # Still write status on failure
        try:
            write_status(output_dir, {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat(),
            })
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
