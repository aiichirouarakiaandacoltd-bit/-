#!/usr/bin/env python3
"""昭和・平成 なぜそうだったのか - 自動動画制作システム"""
import os
import sys
import json
import logging
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import INPUT_DIR, OUTPUT_DIR, LONG_VIDEO, SHORTS_VIDEO
from src.idea_generator import generate_idea_analysis, auto_suggest_themes, score_theme
from src.researcher import generate_research, generate_fact_check
from src.script_writer import generate_long_script, generate_shorts_scripts
from src.tts_engine import generate_voice_by_segments
from src.subtitle import generate_srt
from src.image_generator import generate_all_images
from src.bgm_manager import get_or_create_bgm, mix_audio
from src.video_editor import build_long_video, build_shorts_video
from src.metadata_generator import (
    generate_titles, generate_description, generate_hashtags,
    generate_pinned_comment, generate_thumbnail_text,
    generate_source_list, generate_rights_check,
)
from src.validator import validate_video, print_validation_report


def setup_logging(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "execution.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def load_input():
    input_path = os.path.join(INPUT_DIR, "input.json")
    if not os.path.exists(input_path):
        return None
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_next_video_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing = [d for d in os.listdir(OUTPUT_DIR) if d.startswith("video_")]
    if not existing:
        return os.path.join(OUTPUT_DIR, "video_001")
    nums = []
    for d in existing:
        try:
            nums.append(int(d.split("_")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(nums) + 1 if nums else 1
    return os.path.join(OUTPUT_DIR, f"video_{next_num:03d}")


def run_pipeline(theme=None, config=None):
    """メインパイプライン実行"""
    if config is None:
        config = {}

    output_dir = get_next_video_dir()
    os.makedirs(output_dir, exist_ok=True)
    logger = setup_logging(output_dir)
    logger.info(f"=== 動画制作パイプライン開始 ===")
    logger.info(f"出力先: {output_dir}")

    # --- 入力保存 ---
    input_data = config.copy()
    if theme:
        input_data["theme"] = theme
    input_path = os.path.join(output_dir, "input.json")
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, ensure_ascii=False, indent=2)

    # --- フェーズ1: 企画生成 ---
    if not theme:
        logger.info("テーマ未指定 → 自動企画モード")
        candidates = auto_suggest_themes(10)
        theme = candidates[0]["theme"]
        logger.info(f"最高得点企画を採用: {theme} ({score_theme(candidates[0])}点)")

    logger.info(f"テーマ: {theme}")
    fmt = config.get("format", "long_and_shorts")
    shorts_count = config.get("shorts_count", 2)

    # --- フェーズ2: 企画分析 ---
    logger.info("--- 企画分析 ---")
    analysis = generate_idea_analysis(theme, output_dir)
    logger.info(f"企画スコア: {analysis['total_score']}点 ({'採用' if analysis['adopted'] else '不採用'})")

    # --- フェーズ3: 調査 ---
    logger.info("--- 調査実行 ---")
    research = generate_research(theme, output_dir)
    logger.info(f"調査事実数: {research['total_facts']} (高信頼: {research['high_reliability_count']})")

    # --- フェーズ4: ファクトチェック ---
    logger.info("--- ファクトチェック ---")
    fact_check = generate_fact_check(theme, research, output_dir)
    logger.info(f"検証済み: {fact_check['verified_count']}/{fact_check['total']}")

    # --- フェーズ5: 台本生成 ---
    logger.info("--- 台本生成 ---")
    long_script = generate_long_script(theme, output_dir)
    narration_lines = [l for l in long_script["narration"] if l.strip()]
    logger.info(f"長尺台本: {len(narration_lines)}行")

    shorts_scripts = []
    if fmt in ("long_and_shorts", "shorts"):
        shorts_scripts = generate_shorts_scripts(theme, shorts_count, output_dir)
        logger.info(f"Shorts台本: {len(shorts_scripts)}本")

    # --- フェーズ6: 音声生成 ---
    logger.info("--- 音声生成 ---")
    voice_long_path = os.path.join(output_dir, "voice_long.wav")
    voice_long_path, long_segments = generate_voice_by_segments(narration_lines, voice_long_path)
    logger.info(f"長尺音声: {voice_long_path}")

    shorts_voices = []
    for i, short in enumerate(shorts_scripts):
        short_lines = [l for l in short["narration"] if l.strip()]
        voice_path = os.path.join(output_dir, f"voice_short_{i+1:02d}.wav")
        voice_path, short_segs = generate_voice_by_segments(short_lines, voice_path)
        shorts_voices.append({"path": voice_path, "segments": short_segs})
        logger.info(f"Shorts音声{i+1}: {voice_path}")

    # --- フェーズ7: 字幕生成 ---
    logger.info("--- 字幕生成 ---")
    srt_long_path = os.path.join(output_dir, "subtitle_long.srt")
    generate_srt(long_segments, srt_long_path)

    for i, sv in enumerate(shorts_voices):
        srt_path = os.path.join(output_dir, f"subtitle_short_{i+1:02d}.srt")
        generate_srt(sv["segments"], srt_path)

    # --- フェーズ8: 素材生成 ---
    logger.info("--- 素材生成 ---")
    sections = long_script.get("sections", [])
    long_images = generate_all_images(theme, sections, output_dir, "long")
    logger.info(f"長尺画像: {len(long_images)}枚")

    shorts_images_list = []
    for i, short in enumerate(shorts_scripts):
        short_sections = [{"title": short.get("title", ""), "visual": "", "era": ""}]
        for j, line in enumerate(short["narration"][:4]):
            short_sections.append({"title": line[:15], "visual": line, "era": ""})
        short_img_dir = os.path.join(output_dir, f"images_short_{i+1:02d}")
        os.makedirs(short_img_dir, exist_ok=True)
        temp_output = os.path.join(output_dir, f"_temp_short_{i+1:02d}")
        os.makedirs(temp_output, exist_ok=True)
        short_images = generate_all_images(short.get("title", theme), short_sections, temp_output, "shorts")
        for img in short_images:
            new_path = os.path.join(short_img_dir, os.path.basename(img["path"]))
            shutil.move(img["path"], new_path)
            img["path"] = new_path
        shutil.rmtree(temp_output, ignore_errors=True)
        shorts_images_list.append(short_images)
        logger.info(f"Shorts画像{i+1}: {len(short_images)}枚")

    # --- フェーズ9: BGM ---
    logger.info("--- BGM準備 ---")
    from pydub import AudioSegment
    voice_audio = AudioSegment.from_wav(voice_long_path)
    voice_duration = len(voice_audio)

    bgm_path = get_or_create_bgm(voice_duration, output_dir)
    logger.info(f"BGM: {bgm_path}")

    mixed_long_path = os.path.join(output_dir, "mixed_long.wav")
    mix_audio(voice_long_path, bgm_path, mixed_long_path)

    shorts_mixed = []
    for i, sv in enumerate(shorts_voices):
        short_bgm = get_or_create_bgm(len(AudioSegment.from_wav(sv["path"])), output_dir)
        mixed_path = os.path.join(output_dir, f"mixed_short_{i+1:02d}.wav")
        mix_audio(sv["path"], short_bgm, mixed_path)
        shorts_mixed.append(mixed_path)

    # --- フェーズ10: 動画編集 ---
    logger.info("--- 動画編集・MP4生成 ---")
    final_long = build_long_video(long_images, mixed_long_path, srt_long_path, output_dir)
    logger.info(f"長尺動画: {final_long}")

    final_shorts = []
    for i in range(len(shorts_scripts)):
        srt_short = os.path.join(output_dir, f"subtitle_short_{i+1:02d}.srt")
        final_short = build_shorts_video(
            shorts_images_list[i], shorts_mixed[i], srt_short, output_dir, i + 1
        )
        if final_short:
            final_shorts.append(final_short)
            logger.info(f"Shorts動画{i+1}: {final_short}")

    # --- フェーズ11: メタデータ生成 ---
    logger.info("--- メタデータ生成 ---")
    generate_titles(theme, output_dir)
    generate_description(theme, research.get("sources", []), output_dir)
    generate_hashtags(theme, analysis.get("category", "暮らし"), output_dir)
    generate_pinned_comment(theme, output_dir)
    generate_thumbnail_text(theme, output_dir)
    generate_source_list(long_images, output_dir)
    generate_rights_check(long_images, output_dir)

    # --- フェーズ12: 技術検証 ---
    logger.info("--- 技術検証 ---")
    all_passed = True

    if final_long and os.path.exists(final_long):
        long_result = validate_video(final_long, LONG_VIDEO, "long")
        print_validation_report(long_result)
        if not long_result["passed"]:
            all_passed = False
            logger.error(f"長尺動画検証失敗: {long_result['errors']}")

    for short_path in final_shorts:
        if os.path.exists(short_path):
            short_result = validate_video(short_path, SHORTS_VIDEO, "shorts")
            print_validation_report(short_result)
            if not short_result["passed"]:
                all_passed = False
                logger.error(f"Shorts検証失敗: {short_result['errors']}")

    # --- 一時ファイル削除 ---
    for f in os.listdir(output_dir):
        if f.startswith(("mixed_", "temp_", "bgm.wav")):
            fp = os.path.join(output_dir, f)
            if os.path.isfile(fp):
                os.remove(fp)

    # --- 完了報告 ---
    logger.info(f"\n{'='*60}")
    logger.info(f"=== パイプライン完了 ===")
    logger.info(f"テーマ: {theme}")
    logger.info(f"出力先: {output_dir}")
    if final_long:
        logger.info(f"長尺動画: {final_long}")
    for sp in final_shorts:
        logger.info(f"Shorts: {sp}")
    logger.info(f"検証結果: {'全て合格' if all_passed else '要確認'}")
    logger.info(f"{'='*60}")

    return {
        "output_dir": output_dir,
        "theme": theme,
        "long_video": final_long,
        "shorts_videos": final_shorts,
        "all_passed": all_passed,
    }


def main():
    input_data = load_input()
    theme = None
    config = {}

    if input_data:
        theme = input_data.get("theme")
        config = input_data

    if len(sys.argv) > 1:
        theme = sys.argv[1]

    result = run_pipeline(theme, config)

    if result["all_passed"]:
        print(f"\n完了: {result['output_dir']}")
        sys.exit(0)
    else:
        print(f"\n警告あり: {result['output_dir']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
