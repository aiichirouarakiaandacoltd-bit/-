"""動画製作パイプライン（本番統合版）

本番モード（デフォルト）:
  - VOICEVOX（青山龍星）必須
  - BGM（UNL1337.wav）必須
  - 利用不可ならエラー終了

テストモード（--test-mode）:
  - espeak-ng/gTTSフォールバック許可
  - BGMなしでも続行可能

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
from .script_generator import create_long_script, create_shorts_script, save_script, load_script
from .tts_engine import (
    synthesize_sections, verify_voicevox, VOICEVOXNotAvailableError,
)
from .subtitle_generator import generate_srt, verify_subtitles
from .image_manager import (
    prepare_section_images, create_title_card,
    generate_credits_file, create_text_card,
)
from .video_composer import compose_video
from .quality_checker import (
    verify_video, verify_bgm_file, scan_zero_kb_files,
    capture_screenshots, print_report,
)


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
    mode_tag = "test" if test_mode else "prod"
    project_name = f"{timestamp}_{video_format}_{mode_tag}_{safe_topic}"

    base = output_base or config.OUTPUTS_DIR
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
    log.info(f"動画製作パイプライン開始")
    log.info(f"モード: {'テスト' if test_mode else '本番'}")
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
        "materials_used": 0,
        "materials_excluded": 0,
    }

    # === Phase 0: 事前検証 ===
    log.info("[Phase 0] 事前検証...")

    if not test_mode:
        log.info("  VOICEVOX接続確認...")
        vv = verify_voicevox()
        if not vv["api_reachable"]:
            msg = (
                f"本番モード: VOICEVOX APIに接続できません。\n"
                f"  接続先: {config.VOICEVOX_HOST}\n"
                f"  確認コマンド: curl {config.VOICEVOX_HOST}/speakers\n"
                f"  エラー: {'; '.join(vv['errors'])}"
            )
            log.error(msg)
            _save_final_report(project_dir, execution_info, "FAILED", msg)
            raise PipelineError(msg)

        if not vv["target_speaker_found"]:
            msg = (
                f"本番モード: 青山龍星 (speaker_id={config.VOICEVOX_SPEAKER_ID}) が見つかりません。\n"
                f"  別話者への自動変更は行いません。\n"
                f"  エラー: {'; '.join(vv['errors'])}"
            )
            log.error(msg)
            _save_final_report(project_dir, execution_info, "FAILED", msg)
            raise PipelineError(msg)

        log.info("  VOICEVOX: OK (青山龍星確認済み)")

        bgm_file = bgm_path or (config.BGM_DIR / config.BGM_FILE)
        bgm_check = verify_bgm_file(bgm_file)
        if not bgm_check["exists"] or not bgm_check["nonzero"] or not bgm_check["readable"]:
            msg = (
                f"本番モード: BGMファイルが利用できません。\n"
                f"  必須ファイル: {bgm_file}\n"
                f"  存在: {bgm_check['exists']}\n"
                f"  0KB: {not bgm_check['nonzero'] if bgm_check['exists'] else 'N/A'}\n"
                f"  読取可: {bgm_check['readable']}\n"
                f"  無断で別BGMを使用しません。\n"
                f"  エラー: {'; '.join(bgm_check['errors'])}"
            )
            log.error(msg)
            _save_final_report(project_dir, execution_info, "FAILED", msg)
            raise PipelineError(msg)

        log.info(f"  BGM: OK ({bgm_file.name})")
        bgm_path = bgm_file
    else:
        log.info("  テストモード: VOICEVOX/BGM必須チェックをスキップ")
        bgm_file = bgm_path or (config.BGM_DIR / config.BGM_FILE)
        if bgm_file.exists():
            bgm_path = bgm_file
        else:
            bgm_path = None
            log.info(f"  BGM未配置: {bgm_file} → BGMなしで続行")

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

    script_file = save_script(script, dirs["scripts"])

    if script.get("rights_status") != "OK":
        log.warning(f"権利ステータス: {script['rights_status']}")
    if script.get("forbidden_check"):
        msg = f"禁止表現検出: {script['forbidden_check']}"
        log.error(msg)
        _save_final_report(project_dir, execution_info, "FAILED", msg)
        raise PipelineError(msg)

    # === Phase 2: 音声合成 ===
    log.info("[Phase 2/6] 音声合成...")
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

    tts_info = audio_sections[0]
    execution_info["tts_engine"] = tts_info.get("tts_engine")
    execution_info["tts_speaker_id"] = tts_info.get("tts_speaker_id")
    execution_info["tts_speaker_name"] = tts_info.get("tts_speaker_name")
    execution_info["tts_speed"] = tts_info.get("tts_speed")

    total_audio_dur = sum(s["duration"] for s in audio_sections)
    log.info(f"  総音声時間: {total_audio_dur:.1f}秒")
    log.info(f"  TTSエンジン: {execution_info['tts_engine']}")
    log.info(f"  話者: {execution_info['tts_speaker_name']} (ID={execution_info['tts_speaker_id']})")
    log.info(f"  速度: {execution_info['tts_speed']}")

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
    vc = config.VIDEO_LONG if video_format == "long" else config.VIDEO_SHORTS
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
    generate_credits_file(image_sections, excluded_materials, credits_path)

    # === Phase 5: 動画合成 ===
    log.info("[Phase 5/6] 動画合成...")
    final_mp4 = dirs["final"] / f"{project_name}.mp4"

    if bgm_path and bgm_path.exists():
        execution_info["bgm_file"] = str(bgm_path)
        log.info(f"  BGM: {bgm_path.name} ({config.BGM_CREDIT})")

    compose_video(
        audio_sections=audio_sections,
        image_sections=image_sections,
        srt_path=srt_path,
        output_path=final_mp4,
        video_format=video_format,
        bgm_path=bgm_path,
    )

    # === Phase 6: 品質チェック ===
    log.info("[Phase 6/6] 品質チェック...")
    qc = verify_video(final_mp4, video_format)
    print_report(qc)

    for c in qc["checks"]:
        log.info(f"  QC {c['name']}: {'OK' if c['ok'] else 'NG'} - {c['detail']}")

    qc_path = project_dir / "quality_report.json"
    with open(qc_path, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)

    screenshots = capture_screenshots(final_mp4, dirs["screenshots"])
    log.info(f"  スクリーンショット: {len(screenshots)}枚")

    zero_files = scan_zero_kb_files(project_dir)
    if zero_files:
        log.warning(f"  0KBファイル検出: {len(zero_files)}件")
        for zf in zero_files:
            log.warning(f"    - {zf['path']}")

    desc_path = project_dir / "description.txt"
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write(script.get("description", ""))

    rights_path = project_dir / "rights_report.md"
    _generate_rights_report(rights_path, image_sections, excluded_materials, materials)

    summary_path = project_dir / "summary.md"
    _generate_summary(
        summary_path, execution_info, qc, sub_check,
        audio_sections, image_sections, excluded_materials,
        zero_files, screenshots, final_mp4, srt_path,
    )

    execution_info["completed_at"] = datetime.now().isoformat()
    overall_pass = qc["passed"] and not qc.get("errors")
    status = "PASSED" if overall_pass else "FAILED"

    _save_final_report(project_dir, execution_info, status)

    log.info("")
    log.info("=" * 60)
    log.info(f"完了！ - {status}")
    log.info(f"  MP4: {final_mp4}")
    log.info(f"  SRT: {srt_path}")
    log.info(f"  概要欄: {desc_path}")
    log.info(f"  品質: {status}")
    log.info(f"  モード: {'テスト' if test_mode else '本番'}")
    log.info(f"  TTS: {execution_info['tts_engine']}")
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
):
    lines = ["# 動画製作サマリー", ""]
    lines.append(f"## 基本情報")
    lines.append(f"- プロジェクト: {info.get('project_name', '')}")
    lines.append(f"- モード: {info.get('mode', '')}")
    lines.append(f"- テーマ: {info.get('topic', '')}")
    lines.append(f"- タイトル: {info.get('title', '')}")
    lines.append(f"- フォーマット: {info.get('video_format', '')}")
    lines.append(f"- 開始: {info.get('started_at', '')}")
    lines.append("")

    lines.append("## 使用音声")
    lines.append(f"- エンジン: {info.get('tts_engine', '不明')}")
    lines.append(f"- 話者: {info.get('tts_speaker_name', '不明')}")
    lines.append(f"- 話者ID: {info.get('tts_speaker_id', '不明')}")
    lines.append(f"- 速度: {info.get('tts_speed', '不明')}")
    lines.append("")

    lines.append("## BGM")
    lines.append(f"- ファイル: {info.get('bgm_file', '未使用')}")
    lines.append(f"- クレジット: {config.BGM_CREDIT}")
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
        icon = "✓" if c["ok"] else "✗"
        lines.append(f"- {icon} {c['name']}: {c['detail']}")
    lines.append("")

    lines.append("## 字幕検査")
    for c in sub_check.get("checks", []):
        icon = "✓" if c["ok"] else "✗"
        lines.append(f"- {icon} {c['name']}: {c['detail']}")
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
                        help="テストモード: espeak-ng/gTTSフォールバック許可、BGM任意")
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
        print("[WARNING] 品質チェックに一部不合格があります。")
        sys.exit(1)


if __name__ == "__main__":
    main()
