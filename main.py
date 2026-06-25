#!/usr/bin/env python3
"""
main.py - 昭和・平成 なぜそうだったのか - 動画制作自動化ツール

Usage:
  python main.py --topic "なぜ昔のテレビには布をかけていたのか" --mode test
  python main.py --topic "なぜ昔のテレビには布をかけていたのか" --mode production
  python main.py --script-file inputs/script.txt --mode production
  python main.py --preflight
"""

import argparse
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime

import yaml

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from modules.preflight import run_preflight, format_preflight_report
from modules.planner import run_planner
from modules.researcher import run_researcher
from modules.scriptwriter import run_scriptwriter
from modules.voicevox import generate_audio as voicevox_generate_audio
from modules.subtitle import generate_all_subtitles, AudioSegment as SubAudioSegment
from modules.materials import generate_test_topic_materials, generate_all_materials
from modules.compositor import VideoCompositor
from modules.quality import QualityChecker, generate_screenshots, generate_report
from modules.reporter import generate_all_reports


def load_config(project_root):
    settings_path = os.path.join(project_root, "config", "settings.yaml")
    speakers_path = os.path.join(project_root, "config", "speakers.yaml")
    with open(settings_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    with open(speakers_path, "r", encoding="utf-8") as f:
        speakers_config = yaml.safe_load(f)
    return config, speakers_config


def setup_logging(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "execution.log")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root_logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    root_logger.addHandler(ch)
    return log_path


def sanitize_topic(topic):
    s = re.sub(r'[\s　]+', '_', topic or "unknown")
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    return s[:60]


def create_output_dir(project_root, mode, topic=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = "production" if mode == "production" else "test"
    suffix = f"_{sanitize_topic(topic)}" if topic else ""
    if mode == "test":
        suffix += "_TEST_ONLY"
    output_dir = os.path.join(project_root, "outputs", base, f"{timestamp}{suffix}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def extract_narration_texts(script_data, key):
    key_map = {"long": "narration_long", "short_01": "narration_short_01", "short_02": "narration_short_02"}
    narration_key = key_map.get(key, f"narration_{key}")
    scripts = script_data.get("scripts", {})
    narration = scripts.get(narration_key, "")
    if not narration:
        narration = scripts.get(f"script_{key}", "")
    if not narration:
        narration = scripts.get(key, "")
    lines = [l.strip() for l in narration.split("\n") if l.strip()]
    lines = [l for l in lines if not l.startswith("[") and not l.startswith("【")
             and not l.startswith("#") and not l.startswith("---")]
    sentences = []
    for line in lines:
        parts = [s.strip() for s in re.split(r'(?<=[。！？])', line) if s.strip()]
        sentences.extend(parts)
    return sentences if sentences else ["テスト音声です。"]


def check_zero_kb_files(output_dir):
    zero_files = []
    for root, _dirs, files in os.walk(output_dir):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.getsize(fp) == 0 and not f.startswith(".git"):
                zero_files.append(fp)
                os.remove(fp)
    return zero_files


def run_pipeline(topic, script_file, mode, config, speakers_config, output_dir):
    logger = logging.getLogger("pipeline")
    logger.info("パイプライン開始: モード=%s", mode)
    if topic:
        logger.info("トピック: %s", topic)

    steps_log = []
    errors = []
    status_data = {"mode": mode, "topic": topic, "started_at": datetime.now().isoformat(), "output_dir": output_dir}

    def log_step(name, success, note=""):
        steps_log.append({"name": name, "success": success, "note": note})
        logger.info("  %s %s: %s", "✓" if success else "✗", name, note)

    # ===== Step 1: Planning =====
    logger.info("=" * 60)
    logger.info("ステップ1: トピック評価・企画")
    logger.info("=" * 60)
    if topic and not script_file:
        try:
            planner_result = run_planner(topic, config, output_dir)
            ev = planner_result["evaluation"]
            log_step("トピック評価", True, "スコア %d/%d" % (ev["total_score"], ev["max_score"]))
            status_data["planning"] = {"score": ev["total_score"], "passed": ev["passed"]}
        except Exception as e:
            errors.append("企画エラー: %s" % e)
            log_step("トピック評価", False, str(e))
    else:
        log_step("トピック評価", True, "スキップ")

    # ===== Step 2: Research =====
    logger.info("=" * 60)
    logger.info("ステップ2: リサーチ・ファクトチェック")
    logger.info("=" * 60)
    research_data = None
    if topic:
        try:
            research_data = run_researcher(topic, mode, output_dir)
            usable = len(research_data.get("usable_facts", []))
            log_step("リサーチ", True, "使用可能事実 %d件" % usable)
            status_data["facts"] = research_data.get("fact_stats", {})
        except Exception as e:
            errors.append("リサーチエラー: %s" % e)
            log_step("リサーチ", False, str(e))

    # ===== Step 3: Script Writing =====
    logger.info("=" * 60)
    logger.info("ステップ3: 台本作成")
    logger.info("=" * 60)
    script_data = None
    if script_file:
        try:
            with open(script_file, "r", encoding="utf-8") as f:
                content = f.read()
            script_data = {"scripts": {"long": content, "narration_long": content}}
            log_step("台本作成", True, "ファイルから読み込み")
        except Exception as e:
            errors.append("スクリプト読み込みエラー: %s" % e)
            log_step("台本作成", False, str(e))
    elif research_data:
        try:
            script_data = run_scriptwriter(topic, research_data, mode, output_dir)
            dur = script_data.get("durations", {})
            log_step("台本作成", True, "長尺 %.1f分, S1 %.0f秒, S2 %.0f秒" % (
                dur.get("long_minutes", 0), dur.get("short_01_seconds", 0), dur.get("short_02_seconds", 0)))
        except Exception as e:
            errors.append("台本作成エラー: %s" % e)
            log_step("台本作成", False, str(e))
    else:
        log_step("台本作成", False, "リサーチデータなし")

    if not script_data:
        logger.error("台本が生成できなかったため中止します。")
        return _finalize(output_dir, status_data, steps_log, errors, topic, mode)

    # ===== Step 4: Audio Generation =====
    logger.info("=" * 60)
    logger.info("ステップ4: 音声生成")
    logger.info("=" * 60)
    audio_dir = os.path.join(output_dir, "audio")
    audio_results = {}
    try:
        for label, key in [("long", "long"), ("short_01", "short_01"), ("short_02", "short_02")]:
            texts = extract_narration_texts(script_data, key)
            sub_dir = os.path.join(audio_dir, label)
            os.makedirs(sub_dir, exist_ok=True)
            result = voicevox_generate_audio(texts=texts, output_dir=sub_dir, mode=mode,
                                             config=config, speakers_config=speakers_config)
            audio_results[key] = result
            logger.info("  %s: %.1f秒, %dセグメント", label, result.total_duration_seconds, len(result.segments))
        tts_type = "テスト音声(サイン波)" if mode == "test" else "VOICEVOX"
        log_step("音声生成", True, "%s, %d種類" % (tts_type, len(audio_results)))
        status_data["voicevox"] = {"tts_type": tts_type, "is_test": mode == "test"}
    except Exception as e:
        errors.append("音声生成エラー: %s" % e)
        log_step("音声生成", False, str(e))

    if not audio_results:
        logger.error("音声なしのため中止します。")
        return _finalize(output_dir, status_data, steps_log, errors, topic, mode)

    # ===== Step 5: Subtitle Generation =====
    logger.info("=" * 60)
    logger.info("ステップ5: 字幕生成")
    logger.info("=" * 60)
    subtitle_files = {}
    try:
        long_result = audio_results.get("long")
        if long_result:
            long_segments = [SubAudioSegment(text=s.text, wav_path=s.wav_path,
                            actual_duration_seconds=s.actual_duration_seconds) for s in long_result.segments]
            shorts_segs = {}
            for key in ["short_01", "short_02"]:
                sr = audio_results.get(key)
                if sr:
                    shorts_segs[key] = [SubAudioSegment(text=s.text, wav_path=s.wav_path,
                                        actual_duration_seconds=s.actual_duration_seconds) for s in sr.segments]
            subtitle_files = generate_all_subtitles(segments=long_segments, output_dir=output_dir,
                                                    config=config, pause_duration=0.3,
                                                    shorts_segments=shorts_segs or None)
            log_step("字幕生成", True, "%dファイル" % len(subtitle_files))
    except Exception as e:
        errors.append("字幕生成エラー: %s" % e)
        log_step("字幕生成", False, str(e))

    # ===== Step 6: Material Generation =====
    logger.info("=" * 60)
    logger.info("ステップ6: 画像・素材生成")
    logger.info("=" * 60)
    materials_list = []
    try:
        mat_dir = os.path.join(output_dir, "materials")
        os.makedirs(mat_dir, exist_ok=True)
        is_tv_cloth = "テレビ" in (topic or "") and "布" in (topic or "")
        if is_tv_cloth:
            materials_list = generate_test_topic_materials(output_dir=mat_dir)
        else:
            materials_list = generate_all_materials(topic=topic or "テスト",
                                                    script_chapters=["導入", "背景", "変遷", "現代"],
                                                    output_dir=mat_dir)
        log_step("素材生成", True, "%d件" % len(materials_list))
        status_data["materials"] = {"total": len(materials_list), "ok": len(materials_list)}
    except Exception as e:
        errors.append("素材生成エラー: %s" % e)
        log_step("素材生成", False, str(e))

    # ===== Step 7: BGM =====
    logger.info("=" * 60)
    logger.info("ステップ7: BGM処理")
    logger.info("=" * 60)
    bgm_path = None
    bgm_dir = os.path.join(PROJECT_ROOT, "assets", "bgm")
    if os.path.isdir(bgm_dir):
        exts = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
        bgm_files = [f for f in os.listdir(bgm_dir) if os.path.splitext(f)[1].lower() in exts]
        lic_path = os.path.join(bgm_dir, "bgm_license.json")
        if bgm_files and os.path.isfile(lic_path):
            with open(lic_path, "r", encoding="utf-8") as f:
                lics = json.load(f)
            for lic in (lics if isinstance(lics, list) else []):
                if lic.get("commercial_use") and lic.get("youtube_monetization") and lic.get("file_name") in bgm_files:
                    bgm_path = os.path.join(bgm_dir, lic["file_name"])
                    break
    log_step("BGM処理", True, os.path.basename(bgm_path) if bgm_path else "BGMなし")
    status_data["bgm"] = {"file": os.path.basename(bgm_path) if bgm_path else None}

    # ===== Step 8: Video Composition =====
    logger.info("=" * 60)
    logger.info("ステップ8: 動画合成")
    logger.info("=" * 60)
    video_files = {}
    try:
        compositor = VideoCompositor(config)
        for vid_type, akey, skey, fname in [
            ("long", "long", "long_ass", "final_long.mp4"),
            ("short", "short_01", "short_01_ass", "final_short_01.mp4"),
            ("short", "short_02", "short_02_ass", "final_short_02.mp4"),
        ]:
            ar = audio_results.get(akey)
            if not ar or not ar.concatenated_path:
                continue
            ass_path = subtitle_files.get(skey, "")
            mat_list = []
            for m in materials_list:
                fp = m.get("file_path", "")
                if fp and os.path.isfile(fp):
                    mat_list.append({"image_path": fp, "duration_seconds": 4.0, "label": ""})
            if not mat_list:
                md = os.path.join(output_dir, "materials")
                if os.path.isdir(md):
                    for img in sorted(os.listdir(md)):
                        if img.endswith(".png"):
                            mat_list.append({"image_path": os.path.join(md, img), "duration_seconds": 4.0, "label": img})
            if not mat_list:
                continue
            dur = ar.total_duration_seconds
            if dur > 0:
                per = max(3.0, min(6.0, dur / len(mat_list)))
                for m in mat_list:
                    m["duration_seconds"] = per
            out = os.path.join(output_dir, fname)
            if vid_type == "long":
                compositor.compose_long(mat_list, ar.concatenated_path, ass_path, bgm_path or "", out)
            else:
                compositor.compose_short(mat_list, ar.concatenated_path, ass_path, bgm_path or "", out)
            video_files[fname] = out
            logger.info("  %s: %.1fMB", fname, os.path.getsize(out) / 1048576 if os.path.isfile(out) else 0)
        log_step("動画合成", bool(video_files), "%d本" % len(video_files) if video_files else "なし")
    except Exception as e:
        errors.append("動画合成エラー: %s" % e)
        log_step("動画合成", False, str(e))

    # ===== Step 9: Quality Checks =====
    logger.info("=" * 60)
    logger.info("ステップ9: 品質チェック")
    logger.info("=" * 60)
    try:
        checker = QualityChecker(output_dir=output_dir, config=config, status=status_data)
        qc_results = checker.run_full_check()
        ss_dir = os.path.join(output_dir, "screenshots")
        os.makedirs(ss_dir, exist_ok=True)
        for vn, vp in video_files.items():
            try:
                generate_screenshots(vp, ss_dir, "shorts" if "short" in vn else "long")
            except Exception:
                pass
        generate_report(qc_results, os.path.join(output_dir, "quality_report.json"))
        fails = [r for r in qc_results if not r.passed and r.severity == "error"]
        log_step("品質チェック", not fails, "PASS" if not fails else "FAIL(%d)" % len(fails))
        status_data["quality"] = {"overall": "PASS" if not fails else "FAIL", "failed": len(fails)}
    except Exception as e:
        errors.append("品質チェックエラー: %s" % e)
        log_step("品質チェック", False, str(e))

    # ===== Step 10: 0KB Check =====
    logger.info("=" * 60)
    logger.info("ステップ10: 0KBファイル検査")
    logger.info("=" * 60)
    zf = check_zero_kb_files(output_dir)
    log_step("0KB検査", True, "%d件削除" % len(zf) if zf else "なし")

    # ===== Step 11: Reports =====
    logger.info("=" * 60)
    logger.info("ステップ11: レポート生成")
    logger.info("=" * 60)
    try:
        execution_data = {
            "topic": topic,
            "mode": mode,
            "sources": [],
            "material_credits": [],
            "bgm_credits": [],
            "materials_list": [],
            "bgm_info": {},
            "shorts_info": [],
        }
        execution_data.update(status_data)
        generate_all_reports(output_dir=output_dir, execution_data=execution_data)
        log_step("レポート生成", True, "完了")
    except Exception as e:
        errors.append("レポート生成エラー: %s" % e)
        log_step("レポート生成", False, str(e))

    return _finalize(output_dir, status_data, steps_log, errors, topic, mode)


def _finalize(output_dir, status_data, steps_log, errors, topic, mode):
    logger = logging.getLogger("pipeline")
    status_data.update({"completed_at": datetime.now().isoformat(), "errors": errors, "overall_pass": not errors})
    with open(os.path.join(output_dir, "status.json"), "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2, default=str)
    with open(os.path.join(output_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("# 制作サマリー\n\n- トピック: %s\n- モード: %s\n- 出力先: %s\n\n## 結果\n\n" % (topic, mode, output_dir))
        for s in steps_log:
            f.write("- %s %s: %s\n" % ("✓" if s["success"] else "✗", s["name"], s["note"]))
        if errors:
            f.write("\n## エラー\n\n")
            for e in errors:
                f.write("- %s\n" % e)
    logger.info("パイプライン%s", "正常完了" if not errors else "完了（エラー%d件）" % len(errors))
    logger.info("出力先: %s", output_dir)
    return status_data


def parse_args():
    p = argparse.ArgumentParser(description="昭和・平成動画自動化")
    p.add_argument("--topic", type=str)
    p.add_argument("--script-file", type=str)
    p.add_argument("--mode", choices=["production", "test"], default="production")
    p.add_argument("--test-mode", action="store_true")
    p.add_argument("--preflight", action="store_true")
    a = p.parse_args()
    if a.test_mode:
        a.mode = "test"
    return a


def main():
    args = parse_args()
    try:
        config, speakers_config = load_config(PROJECT_ROOT)
    except Exception as e:
        print("エラー: 設定読み込み失敗: %s" % e, file=sys.stderr)
        sys.exit(1)

    output_dir = create_output_dir(PROJECT_ROOT, args.mode, args.topic)
    log_path = setup_logging(output_dir)
    logger = logging.getLogger("main")
    logger.info("=" * 60)
    logger.info("昭和・平成 なぜそうだったのか - 動画制作自動化ツール")
    logger.info("モード: %s / 出力先: %s", args.mode, output_dir)
    logger.info("=" * 60)

    if args.preflight:
        r = run_preflight(config, speakers_config, PROJECT_ROOT, mode=args.mode, script_file=args.script_file)
        print("\n" + format_preflight_report(r))
        sys.exit(0 if r["passed"] else 1)

    if not args.topic and not args.script_file:
        print("エラー: --topic または --script-file を指定してください", file=sys.stderr)
        sys.exit(1)

    try:
        run_pipeline(args.topic, args.script_file, args.mode, config, speakers_config, output_dir)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        logging.getLogger("main").error("予期しないエラー: %s\n%s", e, traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
