#!/usr/bin/env python3
"""Imperial Video Automation - Main entry point.

Usage:
    python main.py                  # Production mode
    python main.py --test-mode      # Test mode (fallback audio, TEST_ONLY marking)
    python main.py --preflight-only # Run preflight checks only
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as cfg
from src.preflight import run_preflight
from src.script_writer import (
    generate_long_script, generate_shorts_script,
    flatten_lines, script_to_text,
)
from src.voicevox import (
    synthesize_script, generate_test_script_audio, get_wav_duration,
)
from src.materials import (
    generate_all_visuals, filter_ok_materials,
    save_materials_json, generate_rights_report,
)
from src.subtitle import generate_srt
from src.composer import (
    create_concat_video, burn_subtitles, mix_bgm,
    get_video_duration, take_screenshot,
)
from src.quality import run_quality_check, save_quality_report


def setup_logging(log_path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("imperial")


def build_video(script_data, video_type, test_mode, logger, bgm_used_ref):
    """Build a single video (long or shorts)."""
    is_shorts = video_type == "shorts"
    if is_shorts:
        width, height, fps = cfg.SHORTS_WIDTH, cfg.SHORTS_HEIGHT, cfg.SHORTS_FPS
        out_dir = cfg.OUTPUT_TEST_DIR if test_mode else cfg.OUTPUT_SHORTS_DIR
    else:
        width, height, fps = cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg.LONG_FPS
        out_dir = cfg.OUTPUT_TEST_DIR if test_mode else cfg.OUTPUT_LONG_DIR

    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = out_dir / f"work_{video_type}"
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"[{video_type}] Generating script...")
    lines = flatten_lines(script_data)

    script_path = out_dir / "script.txt"
    script_path.write_text(script_to_text(script_data), encoding="utf-8")

    narration_path = out_dir / "narration.txt"
    narration_path.write_text("\n".join(lines), encoding="utf-8")

    logger.info(f"[{video_type}] Generating audio ({len(lines)} lines)...")
    audio_dir = work_dir / "audio"
    voicevox_used = False

    if test_mode:
        audio_results = generate_test_script_audio(
            lines, audio_dir,
            progress_callback=lambda i, t: logger.info(f"  Audio {i}/{t}")
        )
        logger.info(f"[{video_type}] Test audio generated (sine wave)")
    else:
        audio_results = synthesize_script(
            lines, audio_dir,
            progress_callback=lambda i, t: logger.info(f"  Audio {i}/{t}")
        )
        voicevox_used = True
        logger.info(f"[{video_type}] VOICEVOX audio generated")

    total_audio_duration = sum(r["duration"] for r in audio_results)
    logger.info(f"[{video_type}] Total audio duration: {total_audio_duration:.1f}s")

    if is_shorts:
        target_min, target_max = cfg.SHORTS_MIN_DURATION, cfg.SHORTS_MAX_DURATION
    else:
        target_min, target_max = cfg.LONG_MIN_DURATION, cfg.LONG_MAX_DURATION

    if is_shorts and total_audio_duration < target_min:
        pad_needed = target_min - total_audio_duration + 1.0
        logger.info(f"[{video_type}] Audio too short, adding {pad_needed:.1f}s padding")
        audio_results[-1]["duration"] += pad_needed

    if not is_shorts and total_audio_duration < target_min:
        pad_per_line = (target_min - total_audio_duration + 10) / len(audio_results)
        for r in audio_results:
            r["duration"] += pad_per_line
        total_audio_duration = sum(r["duration"] for r in audio_results)
        logger.info(f"[{video_type}] Padded audio to {total_audio_duration:.1f}s")

    logger.info(f"[{video_type}] Generating subtitles...")
    srt_path = out_dir / "subtitles.srt"
    generate_srt(audio_results, srt_path)

    logger.info(f"[{video_type}] Generating visuals...")
    visual_dir = work_dir / "visuals"
    all_materials, image_paths = generate_all_visuals(script_data, width, height, visual_dir)

    ok_materials, excluded = filter_ok_materials(all_materials)
    if excluded:
        logger.warning(f"[{video_type}] Excluded {len(excluded)} non-OK materials")

    materials_path = out_dir / "materials.json"
    save_materials_json(all_materials, materials_path)

    rights_path = out_dir / "rights_report.md"
    generate_rights_report(all_materials, rights_path)

    logger.info(f"[{video_type}] Building image-audio pairs...")
    narration_images = [ip for ip in image_paths if ip["type"] == "narration_bg"]

    pairs = []
    for i, ar in enumerate(audio_results):
        if i < len(narration_images):
            img = narration_images[i]["path"]
        else:
            img = narration_images[-1]["path"]
        pairs.append({
            "image": img,
            "audio": ar["path"],
            "duration": ar["duration"],
        })

    logger.info(f"[{video_type}] Composing {len(pairs)} segments...")
    raw_video = create_concat_video(pairs, work_dir / "raw.mp4", width, height, fps)

    logger.info(f"[{video_type}] Burning subtitles...")
    font_path = cfg.FONT_PATH
    subtitled_video = work_dir / "subtitled.mp4"
    burn_subtitles(raw_video, srt_path, subtitled_video, font_path, is_shorts=is_shorts)

    final_name = "final_shorts.mp4" if is_shorts else "final_long.mp4"
    if test_mode:
        final_name = f"TEST_ONLY_{final_name}"
    final_path = out_dir / final_name

    bgm_actually_used = False
    if not test_mode:
        if not cfg.BGM_FILE.exists():
            raise RuntimeError(
                f"Production mode requires BGM file: {cfg.BGM_FILE}\n"
                "Place UNL1337.wav in assets/bgm/ and retry."
            )
        logger.info(f"[{video_type}] Mixing BGM (UNL1337.wav)...")
        vid_duration = get_video_duration(subtitled_video)
        mix_bgm(subtitled_video, cfg.BGM_FILE, final_path, vid_duration)
        bgm_actually_used = True
    elif cfg.BGM_FILE.exists():
        logger.info(f"[{video_type}] Mixing BGM (test mode, UNL1337.wav available)...")
        vid_duration = get_video_duration(subtitled_video)
        mix_bgm(subtitled_video, cfg.BGM_FILE, final_path, vid_duration)
        bgm_actually_used = True
    else:
        logger.info(f"[{video_type}] Test mode: no BGM available, copying subtitled video as final")
        import shutil
        shutil.copy2(subtitled_video, final_path)

    bgm_used_ref["used"] = bgm_actually_used

    logger.info(f"[{video_type}] Taking screenshots...")
    ss_dir = cfg.SCREENSHOTS_DIR
    ss_dir.mkdir(parents=True, exist_ok=True)
    vid_dur = get_video_duration(final_path)
    prefix = f"{'test_' if test_mode else ''}{video_type}"
    for label, t in [("beginning", 5), ("middle", vid_dur / 2), ("ending", max(5, vid_dur - 10))]:
        ss_path = ss_dir / f"{prefix}_{label}.jpg"
        try:
            take_screenshot(final_path, ss_path, t)
        except Exception as e:
            logger.warning(f"Screenshot {label} failed: {e}")

    logger.info(f"[{video_type}] Running quality check...")
    qr = run_quality_check(
        final_path, video_type, test_mode=test_mode,
        bgm_used=bgm_actually_used, voicevox_used=voicevox_used,
        output_dir=out_dir,
    )

    return {
        "final_path": str(final_path),
        "quality_report": qr,
        "materials": all_materials,
        "voicevox_used": voicevox_used,
        "bgm_used": bgm_actually_used,
        "script_data": script_data,
    }


def generate_description(long_result, shorts_result, test_mode):
    """Generate YouTube description."""
    lines = []
    if test_mode:
        lines.append("【TEST_ONLY - テスト生成動画】")
        lines.append("")

    long_script = long_result["script_data"]
    lines.append(long_script["title"])
    lines.append("")
    lines.append(f"チャンネル「{cfg.CHANNEL_NAME}」をご視聴いただきありがとうございます。")
    lines.append("")
    lines.append("【目次】")
    for section in long_script["sections"]:
        lines.append(f"・{section['label']}")
    lines.append("")

    if long_result["bgm_used"]:
        lines.append(cfg.BGM_CREDIT)
        lines.append("")

    lines.append("#皇室 #日本 #伝統 #令和 #天皇陛下")
    return "\n".join(lines)


def generate_credits(long_result, shorts_result):
    """Generate credits file."""
    lines = ["【クレジット】", ""]
    lines.append(f"チャンネル: {cfg.CHANNEL_NAME}")
    lines.append("制作: 自動動画生成システム")
    lines.append("")

    if long_result["bgm_used"] or shorts_result["bgm_used"]:
        lines.append("【BGM】")
        lines.append(cfg.BGM_CREDIT)
        lines.append("")

    lines.append("【素材】")
    lines.append("全素材は自作（和紙背景、テキストカード等）")
    lines.append("")
    lines.append("※ 本動画に皇族のAI生成画像は一切使用しておりません。")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Imperial Video Automation")
    parser.add_argument("--test-mode", action="store_true", help="Use fallback audio")
    parser.add_argument("--preflight-only", action="store_true", help="Run preflight only")
    args = parser.parse_args()

    cfg.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = cfg.LOGS_DIR / f"execution_{timestamp}.log"
    logger = setup_logging(log_path)

    logger.info("=" * 60)
    logger.info(f"Imperial Video Automation - {'TEST MODE' if args.test_mode else 'PRODUCTION'}")
    logger.info("=" * 60)

    logger.info("Running preflight checks...")
    preflight_ok, checks = run_preflight(test_mode=args.test_mode)

    if args.preflight_only:
        sys.exit(0 if preflight_ok else 1)

    if not preflight_ok:
        logger.error("Preflight failed. Aborting.")
        sys.exit(1)

    start_time = time.time()
    status = {
        "mode": "test" if args.test_mode else "production",
        "started": datetime.now().isoformat(),
        "status": "running",
    }

    try:
        logger.info("Phase 1: Long-format video")
        long_script = generate_long_script()
        long_bgm_ref = {"used": False}
        long_result = build_video(long_script, "long", args.test_mode, logger, long_bgm_ref)

        logger.info("Phase 2: Shorts video")
        shorts_script = generate_shorts_script()
        shorts_bgm_ref = {"used": False}
        shorts_result = build_video(shorts_script, "shorts", args.test_mode, logger, shorts_bgm_ref)

        if args.test_mode:
            out_dir = cfg.OUTPUT_TEST_DIR
        else:
            out_dir = cfg.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Generating description and credits...")
        desc = generate_description(long_result, shorts_result, args.test_mode)
        desc_path = out_dir / "description.txt"
        desc_path.write_text(desc, encoding="utf-8")

        credits_text = generate_credits(long_result, shorts_result)
        credits_path = out_dir / "credits.txt"
        credits_path.write_text(credits_text, encoding="utf-8")

        quality_reports = [long_result["quality_report"], shorts_result["quality_report"]]
        qr_path = out_dir / "quality_report.json"
        from src.quality import save_quality_report
        save_quality_report(quality_reports, qr_path)

        all_passed = all(r["passed"] for r in quality_reports)

        elapsed = time.time() - start_time
        status.update({
            "completed": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 1),
            "status": "success" if all_passed else "quality_check_failed",
            "test_mode": args.test_mode,
            "long_video": long_result["final_path"],
            "shorts_video": shorts_result["final_path"],
            "quality_passed": all_passed,
            "voicevox_used": long_result["voicevox_used"],
            "bgm_used": long_result["bgm_used"],
        })
        status_path = out_dir / "status.json"
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        # Copy execution log
        import shutil
        shutil.copy2(log_path, out_dir / "execution.log")

        logger.info("=" * 60)
        if all_passed:
            logger.info("ALL QUALITY CHECKS PASSED")
        else:
            logger.warning("SOME QUALITY CHECKS FAILED")
            for r in quality_reports:
                for c in r["checks"]:
                    if not c["passed"]:
                        logger.warning(f"  FAIL: {r['type']} - {c['name']}: {c['detail']}")

        logger.info(f"Long video:   {long_result['final_path']}")
        logger.info(f"Shorts video: {shorts_result['final_path']}")
        logger.info(f"Elapsed: {elapsed:.1f}s")
        logger.info("=" * 60)

        if not all_passed:
            sys.exit(1)

    except Exception as e:
        logger.error(f"FATAL: {e}", exc_info=True)
        status["status"] = "error"
        status["error"] = str(e)
        try:
            out_dir = cfg.OUTPUT_TEST_DIR if args.test_mode else cfg.OUTPUT_DIR
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "status.json").write_text(
                json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
