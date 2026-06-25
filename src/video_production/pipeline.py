"""動画製作パイプライン

トピック → 台本 → 音声 → 字幕 → 画像 → 合成 → 検証
の全工程を統合実行する。

使い方:
  python -m src.video_production.pipeline \
    --topic "愛子さまの公務" \
    --text-file scripts/draft.txt \
    --format long

※ 最終判断・台本確定・投稿判断は荒木が行います。自動投稿は行いません。
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import config
from .script_generator import create_long_script, create_shorts_script, save_script, load_script
from .tts_engine import synthesize_sections
from .subtitle_generator import generate_srt
from .image_manager import prepare_section_images, create_title_card
from .video_composer import compose_video
from .quality_checker import verify_video, print_report


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
) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic[:30].replace(" ", "_").replace("/", "_")
    project_name = f"{timestamp}_{video_format}_{safe_topic}"

    base = output_base or config.OUTPUTS_DIR
    project_dir = base / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    dirs = {
        "scripts": project_dir / "scripts",
        "audio": project_dir / "audio",
        "images": project_dir / "images",
        "subtitles": project_dir / "subtitles",
        "final": project_dir / "final",
    }
    for d in dirs.values():
        d.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"動画製作パイプライン開始")
    print(f"プロジェクト: {project_name}")
    print(f"フォーマット: {video_format}")
    print(f"{'='*60}\n")

    # Phase 1: 台本
    print("[Phase 1/6] 台本生成...")
    if script_path:
        script = load_script(script_path)
        print(f"  既存台本を読み込み: {script_path}")
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
        print("[!] 権利ステータスがOKではありません。確認後に続行してください。")
        _save_status(project_dir, "stopped", "rights_check_required", script)
        return {"status": "stopped", "reason": "rights_check", "project_dir": str(project_dir)}

    if script.get("forbidden_check"):
        print(f"[!] 禁止表現: {script['forbidden_check']}")
        print("[!] 台本を修正後、--script-path で再実行してください。")
        _save_status(project_dir, "stopped", "forbidden_expressions", script)
        return {"status": "stopped", "reason": "forbidden", "project_dir": str(project_dir)}

    # Phase 2: 音声合成
    print("\n[Phase 2/6] 音声合成...")
    audio_sections = synthesize_sections(
        script["sections"], dirs["audio"], speed=config.VOICEVOX_SPEED,
    )

    if not audio_sections:
        print("[ERROR] 音声生成に失敗しました。")
        _save_status(project_dir, "error", "tts_failed", script)
        return {"status": "error", "reason": "tts_failed", "project_dir": str(project_dir)}

    total_audio_dur = sum(s["duration"] for s in audio_sections)
    print(f"  総音声時間: {total_audio_dur:.1f}秒")

    # Phase 3: 字幕生成
    print("\n[Phase 3/6] 字幕生成...")
    srt_path = dirs["subtitles"] / "subtitles.srt"
    generate_srt(audio_sections, srt_path)

    # Phase 4: 画像準備
    print("\n[Phase 4/6] 画像準備...")
    vc = config.VIDEO_LONG if video_format == "long" else config.VIDEO_SHORTS
    image_sections = prepare_section_images(
        script["sections"], dirs["images"], vc,
    )

    title_card = dirs["images"] / "title_card.png"
    create_title_card(script["title"], title_card, vc["width"], vc["height"])

    # Phase 5: 動画合成
    print("\n[Phase 5/6] 動画合成...")
    final_mp4 = dirs["final"] / f"{project_name}.mp4"

    if not bgm_path:
        default_bgm = config.BGM_DIR / config.BGM_FILE
        if default_bgm.exists():
            bgm_path = default_bgm
            print(f"  BGM: {config.BGM_FILE} ({config.BGM_CREDIT})")

    compose_video(
        audio_sections=audio_sections,
        image_sections=image_sections,
        srt_path=srt_path,
        output_path=final_mp4,
        video_format=video_format,
        bgm_path=bgm_path,
    )

    # Phase 6: 品質チェック
    print("\n[Phase 6/6] 品質チェック...")
    qc = verify_video(final_mp4, video_format)
    print_report(qc)

    qc_path = project_dir / "quality_check.json"
    with open(qc_path, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)

    # 概要欄テキスト保存
    desc_path = project_dir / "description.txt"
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write(script.get("description", ""))

    _save_status(project_dir, "completed", "ok", script, qc)

    print(f"\n{'='*60}")
    print(f"完了！")
    print(f"  MP4: {final_mp4}")
    print(f"  SRT: {srt_path}")
    print(f"  概要欄: {desc_path}")
    print(f"  品質チェック: {'PASSED' if qc['passed'] else 'FAILED'}")
    print(f"{'='*60}")
    print(f"\n※ 最終判断・台本確定・投稿判断は荒木が行います。自動投稿は行いません。")

    return {
        "status": "completed",
        "project_dir": str(project_dir),
        "mp4": str(final_mp4),
        "srt": str(srt_path),
        "description": str(desc_path),
        "quality_check": qc,
    }


def _save_status(
    project_dir: Path, status: str, reason: str,
    script: dict, qc: dict | None = None,
):
    info = {
        "status": status,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
        "title": script.get("title", ""),
        "format": script.get("format", ""),
        "quality_check": qc,
    }
    with open(project_dir / "status.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


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
    )

    if result["status"] != "completed":
        sys.exit(1)


if __name__ == "__main__":
    main()
