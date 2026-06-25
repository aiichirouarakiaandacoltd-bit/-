"""動画製作パイプライン（厳格版）

本番モード（デフォルト）:
  - VOICEVOX（青山龍星）必須
  - BGM（UNL1337.wav）必須
  - 利用不可ならエラー終了

テストモード（--test-mode）:
  - espeak-ngフォールバック許可
  - BGMなしでも続行可能
  - ファイル名に TEST_ONLY 付与
  - 出力先: outputs/videos_test/

使い方:
  # 本番モード
  python -m src.video_production \
    --topic "テーマ" --text-file draft.txt --format long

  # テストモード
  python -m src.video_production \
    --topic "テーマ" --text-file draft.txt --format long --test-mode

※ 最終判断・台本確定・投稿判断は荒木が行います。自動投稿は行いません。
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from . import config
from .script_generator import (
    create_long_script, create_shorts_script,
    save_script, load_script, shorten_script_for_duration,
)
from .tts_engine import (
    synthesize_sections, VOICEVOXNotAvailableError,
)
from .subtitle_generator import generate_srt, verify_subtitles
from .image_manager import (
    prepare_section_images, create_title_card,
    generate_credits_file, create_text_card,
)
from .video_composer import compose_video
from .quality_checker import (
    verify_video, scan_zero_kb_files,
    capture_screenshots, print_report,
)
from .preflight import run_preflight, print_preflight_report


class PipelineError(Exception):
    pass


def _setup_logger(project_dir: Path) -> logging.Logger:
    logger = logging.getLogger("video_pipeline")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fh = logging.FileHandler(project_dir / "execution.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger


def _delete_zero_kb_files(directory: Path) -> int:
    count = 0
    if not directory.exists():
        return count
    for f in directory.rglob("*"):
        if f.is_file() and f.stat().st_size == 0:
            f.unlink()
            count += 1
    return count


def run_pipeline(
    topic: str,
    main_text: str,
    video_format: str = "long",
    title: str = "",
    persons: list[str] | None = None,
    source_urls: list[str] | None = None,
    bgm_path: Path | None = None,
    output_base: Path | None = None,
    script_path: Path | None = None,
    test_mode: bool = False,
    materials: list[dict] | None = None,
) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic[:30].replace(" ", "_").replace("/", "_")

    if test_mode:
        mode_tag = "TEST_ONLY"
        base = output_base or config.OUTPUTS_TEST_DIR
    else:
        mode_tag = "prod"
        base = output_base or config.OUTPUTS_DIR

    project_name = f"{timestamp}_{video_format}_{mode_tag}_{safe_topic}"
    project_dir = base / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    dirs = {
        "scripts": project_dir / "scripts",
        "audio": project_dir / "audio",
        "images": project_dir / "images",
        "subtitles": project_dir / "subtitles",
        "final": project_dir / "final",
        "screenshots": project_dir / "screenshots",
    }
    for d in dirs.values():
        d.mkdir(exist_ok=True)

    log = _setup_logger(project_dir)

    log.info("=" * 60)
    log.info("動画製作パイプライン開始")
    log.info(f"モード: {'テスト（TEST ONLY）' if test_mode else '本番'}")
    log.info(f"プロジェクト: {project_name}")
    log.info(f"フォーマット: {video_format}")
    log.info("=" * 60)

    execution_info = {
        "project_name": project_name,
        "mode": "test" if test_mode else "production",
        "video_format": video_format,
        "topic": topic,
        "title": title or topic,
        "started_at": datetime.now().isoformat(),
        "tts_engine": None,
        "tts_speaker_id": None,
        "tts_speaker_name": None,
        "tts_speed": None,
        "bgm_file": None,
        "bgm_mixed": False,
        "materials_used": 0,
        "materials_excluded": 0,
        "duration_adjustments": 0,
    }

    # === Phase 0: 統合事前検証 ===
    log.info("[Phase 0] 統合事前検証...")
    bgm_file = bgm_path or (config.BGM_DIR / config.BGM_FILE)
    preflight = run_preflight(test_mode=test_mode, bgm_path=bgm_file)
    print_preflight_report(preflight)

    for c in preflight["checks"]:
        status = "OK" if c["ok"] else "NG"
        log.info(f"  事前検証 {c['name']}: {status} - {c['detail']}")

    if not preflight["passed"]:
        msg = "事前検証FAILED:\n" + "\n".join(f"  - {e}" for e in preflight["errors"])
        log.error(msg)
        _save_final_report(project_dir, execution_info, "FAILED", msg)
        raise PipelineError(msg)

    if preflight["bgm"] and preflight["bgm"]["exists"] and preflight["bgm"]["readable"]:
        bgm_path = Path(preflight["bgm"]["path"])
    else:
        bgm_path = None
        if not test_mode:
            msg = "本番モード: BGMファイルが利用できません"
            log.error(msg)
            _save_final_report(project_dir, execution_info, "FAILED", msg)
            raise PipelineError(msg)
        log.info("  BGM未配置 → BGMなしで続行（テストモード）")

    bgm_actually_used = bgm_path is not None and bgm_path.exists()

    # === Phase 1: 台本 ===
    log.info("[Phase 1/6] 台本生成...")
    if script_path:
        script = load_script(script_path)
        log.info(f"  既存台本: {script_path}")
    elif video_format == "long":
        script = create_long_script(
            topic=topic, main_text=main_text, title=title,
            persons=persons, source_urls=source_urls,
        )
    else:
        script = create_shorts_script(
            topic=topic, main_text=main_text, title=title,
            persons=persons,
        )

    if test_mode:
        test_prefix = "【テスト用】"
        if not script["title"].startswith(test_prefix):
            script["title"] = test_prefix + script["title"]

    script_file = save_script(script, dirs["scripts"])

    if script.get("rights_status") != "OK":
        log.warning(f"権利ステータス: {script['rights_status']}")
    if script.get("forbidden_check"):
        msg = f"禁止表現検出: {script['forbidden_check']}"
        log.error(msg)
        _save_final_report(project_dir, execution_info, "FAILED", msg)
        raise PipelineError(msg)

    # === Phase 2: 音声合成（尺自動調整ループ付き） ===
    log.info("[Phase 2/6] 音声合成...")

    vc = config.VIDEO_LONG if video_format == "long" else config.VIDEO_SHORTS
    if video_format == "shorts":
        dur_target_max = config.SHORTS_TARGET_MAX
    else:
        dur_target_max = vc["duration_max"]
    dur_min = vc["duration_min"]
    max_retries = config.DURATION_ADJUST_MAX_RETRIES

    audio_sections = None
    total_audio_dur = 0.0

    for attempt in range(max_retries + 1):
        try:
            audio_sections = synthesize_sections(
                script["sections"], dirs["audio"],
                speed=config.VOICEVOX_SPEED,
                test_mode=test_mode,
            )
        except VOICEVOXNotAvailableError as e:
            log.error(str(e))
            _save_final_report(project_dir, execution_info, "FAILED", str(e))
            raise PipelineError(str(e))

        if not audio_sections:
            msg = "音声生成に失敗しました。"
            log.error(msg)
            _save_final_report(project_dir, execution_info, "FAILED", msg)
            raise PipelineError(msg)

        total_audio_dur = sum(s["duration"] for s in audio_sections)
        log.info(f"  音声合成 試行{attempt + 1}: {total_audio_dur:.1f}秒")

        if total_audio_dur <= dur_target_max:
            break

        if attempt < max_retries:
            log.info(f"  尺超過 ({total_audio_dur:.1f}秒 > {dur_target_max}秒) → 台本短縮 試行{attempt + 2}")
            execution_info["duration_adjustments"] = attempt + 1
            script = shorten_script_for_duration(script, dur_target_max, total_audio_dur)

            deleted = _delete_zero_kb_files(dirs["audio"])
            if deleted > 0:
                log.info(f"  0KBファイル{deleted}件削除")
            for f in dirs["audio"].glob("*.wav"):
                f.unlink(missing_ok=True)
        else:
            log.warning(f"  尺調整{max_retries}回試行後も超過: {total_audio_dur:.1f}秒")

    tts_info = audio_sections[0]
    execution_info["tts_engine"] = tts_info.get("tts_engine")
    execution_info["tts_speaker_id"] = tts_info.get("tts_speaker_id")
    execution_info["tts_speaker_name"] = tts_info.get("tts_speaker_name")
    execution_info["tts_speed"] = tts_info.get("tts_speed")

    log.info(f"  総音声時間: {total_audio_dur:.1f}秒")
    log.info(f"  TTSエンジン: {execution_info['tts_engine']}")
    log.info(f"  話者: {execution_info['tts_speaker_name']} (ID={execution_info['tts_speaker_id']})")
    log.info(f"  速度: {execution_info['tts_speed']}")
    if execution_info["duration_adjustments"] > 0:
        log.info(f"  尺調整回数: {execution_info['duration_adjustments']}")

    # === Phase 3: 字幕生成 ===
    log.info("[Phase 3/6] 字幕生成...")
    srt_path = dirs["subtitles"] / "subtitles.srt"
    generate_srt(audio_sections, srt_path, video_format=video_format)

    sub_check = verify_subtitles(srt_path, video_format)
    for c in sub_check["checks"]:
        status = "OK" if c["ok"] else "NG"
        log.info(f"  字幕検査 {c['name']}: {status} - {c['detail']}")

    # === Phase 4: 画像準備 ===
    log.info("[Phase 4/6] 画像準備...")
    image_sections, excluded_materials = prepare_section_images(
        script["sections"], dirs["images"], vc, materials=materials,
    )

    execution_info["materials_used"] = sum(1 for s in image_sections if s.get("source") == "material")
    execution_info["materials_excluded"] = len(excluded_materials)

    if excluded_materials:
        log.warning(f"  除外素材: {len(excluded_materials)}件")
        for ex in excluded_materials:
            log.warning(f"    - セクション{ex.get('section_index')}: {ex.get('reason')}")

    title_card = dirs["images"] / "title_card.png"
    create_title_card(script["title"], title_card, vc["width"], vc["height"])

    credits_path = project_dir / "credits.txt"
    generate_credits_file(
        image_sections, excluded_materials, credits_path,
        bgm_used=bgm_actually_used,
    )

    # === Phase 5: 動画合成 ===
    log.info("[Phase 5/6] 動画合成...")
    final_mp4 = dirs["final"] / f"{project_name}.mp4"

    if bgm_actually_used:
        execution_info["bgm_file"] = str(bgm_path)
        execution_info["bgm_mixed"] = True
        log.info(f"  BGM: {bgm_path.name} ({config.BGM_CREDIT})")
    else:
        log.info("  BGM: なし")

    compose_video(
        audio_sections=audio_sections,
        image_sections=image_sections,
        srt_path=srt_path,
        output_path=final_mp4,
        video_format=video_format,
        bgm_path=bgm_path if bgm_actually_used else None,
    )

    # 0KBファイル削除
    deleted_zero = _delete_zero_kb_files(project_dir)
    if deleted_zero > 0:
        log.info(f"  0KBファイル{deleted_zero}件を削除")

    # === Phase 6: 品質チェック（厳格版） ===
    log.info("[Phase 6/6] 品質チェック...")

    zero_files = scan_zero_kb_files(project_dir)

    qc = verify_video(
        final_mp4,
        video_format=video_format,
        test_mode=test_mode,
        tts_engine=execution_info["tts_engine"],
        bgm_mixed=bgm_actually_used,
        zero_kb_count=len(zero_files),
        excluded_review_ng=len(excluded_materials),
    )
    print_report(qc)

    for c in qc["checks"]:
        log.info(f"  QC {c['name']}: {'OK' if c['ok'] else 'NG'} - {c['detail']}")

    qc_path = project_dir / "quality_report.json"
    with open(qc_path, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)

    screenshots = capture_screenshots(final_mp4, dirs["screenshots"])
    log.info(f"  スクリーンショット: {len(screenshots)}枚")

    if zero_files:
        log.warning(f"  0KBファイル検出: {len(zero_files)}件")
        for zf in zero_files:
            log.warning(f"    - {zf['path']}")

    desc_path = project_dir / "description.txt"
    desc_text = script.get("description", "")
    if not bgm_actually_used and config.BGM_CREDIT in desc_text:
        desc_text = desc_text.replace(f"{config.BGM_CREDIT}\n\n", "")
        desc_text = desc_text.replace(f"{config.BGM_CREDIT}\n", "")
        desc_text = desc_text.replace(config.BGM_CREDIT, "")
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write(desc_text)

    rights_path = project_dir / "rights_report.md"
    _generate_rights_report(rights_path, image_sections, excluded_materials, materials)

    summary_path = project_dir / "summary.md"
    _generate_summary(
        summary_path, execution_info, qc, sub_check,
        audio_sections, image_sections, excluded_materials,
        zero_files, screenshots, final_mp4, srt_path,
        bgm_actually_used,
    )

    execution_info["completed_at"] = datetime.now().isoformat()
    overall_pass = qc["passed"]
    status = "PASSED" if overall_pass else "FAILED"

    _save_final_report(project_dir, execution_info, status)

    log.info("")
    log.info("=" * 60)
    log.info(f"完了！ - {status}")
    log.info(f"  MP4: {final_mp4}")
    log.info(f"  SRT: {srt_path}")
    log.info(f"  概要欄: {desc_path}")
    log.info(f"  品質: {status}")
    log.info(f"  モード: {'テスト（TEST ONLY）' if test_mode else '本番'}")
    log.info(f"  TTS: {execution_info['tts_engine']}")
    if test_mode:
        log.info("  ※ TEST ONLY: このファイルは本番投稿には使用できません")
    log.info("=" * 60)
    log.info("※ 最終判断・台本確定・投稿判断は荒木が行います。自動投稿は行いません。")

    return {
        "status": "completed",
        "overall_result": status,
        "test_mode": test_mode,
        "project_dir": str(project_dir),
        "mp4": str(final_mp4),
        "srt": str(srt_path),
        "description": str(desc_path),
        "summary": str(summary_path),
        "credits": str(credits_path),
        "rights_report": str(rights_path),
        "quality_report": str(qc_path),
        "screenshots": [str(s) for s in screenshots],
        "quality_check": qc,
        "execution_info": execution_info,
        "zero_kb_files": zero_files,
    }


def _save_final_report(project_dir: Path, info: dict, status: str, error: str = ""):
    info["final_status"] = status
    if error:
        info["error"] = error
    with open(project_dir / "status.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def _generate_rights_report(
    path: Path, used: list[dict], excluded: list[dict],
    materials: list[dict] | None,
):
    lines = ["# 素材権利レポート", ""]
    lines.append(f"生成日時: {datetime.now().isoformat()}")
    lines.append("")

    lines.append("## 使用素材")
    for s in used:
        src = s.get("source", "placeholder")
        rights = s.get("rights_status", "OK")
        name = s.get("source_name", "-")
        lines.append(f"- セクション{s['index']}: {src} | rights={rights} | {name}")
    lines.append("")

    if excluded:
        lines.append("## 除外素材（REVIEW/NG）")
        for e in excluded:
            lines.append(
                f"- セクション{e.get('section_index', '?')}: "
                f"rights={e.get('rights_status')} | {e.get('reason')}"
            )
        lines.append("")

    lines.append("## 注意事項")
    lines.append("- 実在皇族・王族のAI生成顔画像は禁止")
    lines.append("- rights_status=OK以外の素材は完成MP4に含めない")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _generate_summary(
    path: Path, info: dict, qc: dict, sub_check: dict,
    audio_sections: list[dict], image_sections: list[dict],
    excluded: list[dict], zero_files: list[dict],
    screenshots: list[Path], mp4_path: Path, srt_path: Path,
    bgm_used: bool = False,
):
    lines = ["# 動画製作サマリー", ""]
    lines.append("## 基本情報")
    lines.append(f"- プロジェクト: {info.get('project_name', '')}")
    lines.append(f"- モード: {info.get('mode', '')}")
    lines.append(f"- テーマ: {info.get('topic', '')}")
    lines.append(f"- タイトル: {info.get('title', '')}")
    lines.append(f"- フォーマット: {info.get('video_format', '')}")
    lines.append(f"- 開始: {info.get('started_at', '')}")
    if info.get("duration_adjustments", 0) > 0:
        lines.append(f"- 尺調整回数: {info['duration_adjustments']}")
    lines.append("")

    lines.append("## 使用音声")
    lines.append(f"- エンジン: {info.get('tts_engine', '不明')}")
    lines.append(f"- 話者: {info.get('tts_speaker_name', '不明')}")
    lines.append(f"- 話者ID: {info.get('tts_speaker_id', '不明')}")
    lines.append(f"- 速度: {info.get('tts_speed', '不明')}")
    lines.append("")

    lines.append("## BGM")
    if bgm_used:
        lines.append(f"- ファイル: {info.get('bgm_file', '不明')}")
        lines.append(f"- クレジット: {config.BGM_CREDIT}")
    else:
        lines.append("- 使用: なし")
    lines.append("")

    lines.append("## 素材")
    lines.append(f"- 使用素材数: {info.get('materials_used', 0)}")
    lines.append(f"- 除外素材数: {info.get('materials_excluded', 0)}")
    if excluded:
        for e in excluded:
            lines.append(f"  - 除外: セクション{e.get('section_index')} - {e.get('reason')}")
    lines.append("")

    lines.append("## 品質チェック結果")
    for c in qc.get("checks", []):
        icon = "OK" if c["ok"] else "NG"
        lines.append(f"- [{icon}] {c['name']}: {c['detail']}")
    lines.append("")

    lines.append("## 字幕検査")
    for c in sub_check.get("checks", []):
        icon = "OK" if c["ok"] else "NG"
        lines.append(f"- [{icon}] {c['name']}: {c['detail']}")
    lines.append("")

    if zero_files:
        lines.append("## 0KBファイル")
        for zf in zero_files:
            lines.append(f"- {zf['path']}")
        lines.append("")

    lines.append("## スクリーンショット")
    for ss in screenshots:
        lines.append(f"- {ss}")
    lines.append("")

    lines.append("---")
    lines.append("※ 最終判断・台本確定・投稿判断は荒木が行います。自動投稿は行いません。")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="動画製作パイプライン - 日本が誇る皇室物語",
    )
    parser.add_argument("--topic", required=True, help="動画のトピック")
    parser.add_argument("--text-file", help="本文テキストファイル")
    parser.add_argument("--script-path", help="既存台本JSONファイル")
    parser.add_argument("--title", default="", help="動画タイトル")
    parser.add_argument("--format", choices=["long", "shorts"], default="long",
                        dest="video_format")
    parser.add_argument("--persons", nargs="*", default=[])
    parser.add_argument("--source-urls", nargs="*", default=[])
    parser.add_argument("--bgm", help="BGMファイルパス")
    parser.add_argument("--output-dir", help="出力ディレクトリ")
    parser.add_argument("--test-mode", action="store_true",
                        help="テストモード: espeak-ngフォールバック許可、BGM任意")
    parser.add_argument("--materials-json", help="素材定義JSONファイル")

    args = parser.parse_args()

    if args.script_path:
        main_text = ""
    elif args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            main_text = f.read()
    else:
        print("[ERROR] --text-file または --script-path を指定してください。")
        sys.exit(1)

    bgm = Path(args.bgm) if args.bgm else None
    out = Path(args.output_dir) if args.output_dir else None

    materials = None
    if args.materials_json:
        with open(args.materials_json, "r", encoding="utf-8") as f:
            materials = json.load(f)

    try:
        result = run_pipeline(
            topic=args.topic,
            main_text=main_text,
            video_format=args.video_format,
            title=args.title,
            persons=args.persons,
            source_urls=args.source_urls,
            bgm_path=bgm,
            output_base=out,
            script_path=Path(args.script_path) if args.script_path else None,
            test_mode=args.test_mode,
            materials=materials,
        )
    except PipelineError as e:
        print(f"\n[PIPELINE ERROR] {e}")
        sys.exit(1)

    if result.get("overall_result") != "PASSED":
        print("[WARNING] 品質チェックに不合格項目があります。")
        sys.exit(1)


if __name__ == "__main__":
    main()
