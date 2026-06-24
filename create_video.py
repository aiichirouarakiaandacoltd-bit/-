#!/usr/bin/env python3
"""
昭和・平成 なぜそうだったのか — 動画自動生成システム

使い方:
    python create_video.py --theme "なぜ家族全員で1台のテレビを見ていたのか"

オプション:
    --theme     動画テーマ（必須）
    --output    出力ディレクトリ（デフォルト: ./output）
    --bgm       BGMファイルパス（デフォルト: ./assets/bgm/UNL1337.wav）
    --no-video  動画レンダリングをスキップ（テキスト・画像のみ生成）
"""

import argparse
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


def main():
    parser = argparse.ArgumentParser(
        description="昭和・平成 なぜそうだったのか — 動画自動生成システム"
    )
    parser.add_argument("--theme", required=True, help="動画テーマ")
    parser.add_argument("--output", default="./output", help="出力ディレクトリ")
    parser.add_argument("--bgm", default="./assets/bgm/UNL1337.wav", help="BGMファイルパス")
    parser.add_argument("--no-video", action="store_true", help="動画レンダリングをスキップ")
    parser.add_argument(
        "--voicevox-speed", type=float, default=None,
        help="VOICEVOX話速（0.85〜0.90 推奨、省略時はconfig.pyの値を使用）"
    )
    args = parser.parse_args()

    from modules.config import REQUIRE_VOICEVOX, REQUIRE_BGM, VOICEVOX_SPEED_SCALE
    import modules.config as _cfg

    # VOICEVOX話速の上書き
    if args.voicevox_speed is not None:
        _cfg.VOICEVOX_SPEED_SCALE = args.voicevox_speed

    theme = args.theme
    output_dir = Path(args.output).resolve()
    bgm_path = str(Path(args.bgm).resolve())
    skip_video = args.no_video

    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_dir / "_tmp"
    tmp_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("昭和・平成 なぜそうだったのか — 動画自動生成システム")
    print("=" * 60)
    print(f"テーマ: {theme}")
    print(f"出力先: {output_dir.resolve()}")
    print("=" * 60)

    # ── 事前チェック（失敗時は即停止）────────────────────
    # VOICEVOX 接続確認（--no-video でも narration は生成するため常にチェック）
    from modules.narration import _voicevox_available
    if not _voicevox_available():
        if REQUIRE_VOICEVOX:
            print(
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "エラー: VOICEVOXに接続できません（http://localhost:50021）\n\n"
                "解決方法:\n"
                "  1. VOICEVOXアプリを起動してください\n"
                "  2. 起動後、再度コマンドを実行してください\n\n"
                "開発用の代替音声（低品質）を使用する場合:\n"
                "  modules/config.py の REQUIRE_VOICEVOX = False に変更してください\n"
                "  ※代替音声で生成した動画は本番投稿に使用しないでください\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            return 1
        else:
            print("  [警告] VOICEVOX未起動 → 開発用espeak-ngを使用します（REQUIRE_VOICEVOX=False）")
    else:
        print(f"  [確認] VOICEVOX 接続OK / 話者: 青山龍星 / 話速: {_cfg.VOICEVOX_SPEED_SCALE}")

    # BGMファイル確認（動画レンダリング時のみ必要）
    if not skip_video and not os.path.exists(bgm_path):
        if REQUIRE_BGM:
            print(
                f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"エラー: BGMファイルが見つかりません\n"
                f"  パス: {bgm_path}\n\n"
                f"解決方法:\n"
                f"  1. {bgm_path} にBGMファイルを配置してください\n"
                f"  2. または --bgm オプションで別のパスを指定してください\n\n"
                f"BGMなしで生成する場合:\n"
                f"  modules/config.py の REQUIRE_BGM = False に変更してください\n"
                f"  ※BGMなしで生成した動画は本番投稿に使用しないでください\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            return 1
        else:
            print(f"  [警告] BGMファイルが見つかりません → BGMなしで続行（REQUIRE_BGM=False）")

    print("\n[1/8] 台本を生成中...")
    from modules.script_generator import generate_script
    script = generate_script(theme)
    print(f"  タイトル: {script['title']}")
    total_duration = sum(ch.get("duration", 60) for ch in script["chapters"].values())
    print(f"  推定尺: {total_duration:.0f}秒 ({total_duration/60:.1f}分)")

    print("\n[2/8] ナレーション音声を生成中...")
    from modules.narration import generate_chapter_narrations
    narration_dir = tmp_dir / "narration"
    audio_files = generate_chapter_narrations(script, str(narration_dir))

    audio_durations = {}
    for chapter_name, audio_path in audio_files.items():
        if audio_path and os.path.exists(audio_path):
            from moviepy import AudioFileClip
            clip = AudioFileClip(audio_path)
            audio_durations[chapter_name] = clip.duration
            clip.close()
            print(f"  {chapter_name}: {audio_durations[chapter_name]:.1f}秒")
        else:
            audio_durations[chapter_name] = script["chapters"][chapter_name].get("duration", 60.0)
            print(f"  {chapter_name}: {audio_durations[chapter_name]:.0f}秒（推定）")

    print("\n[3/8] 字幕（SRT）を生成中...")
    from modules.subtitle import generate_srt, get_subtitle_entries
    srt_path = str(output_dir / "subtitle.srt")
    generate_srt(script, audio_durations, srt_path)
    subtitle_entries = get_subtitle_entries(script, audio_durations)

    print("\n[4/8] スライド画像を生成中...")
    from modules.image_generator import generate_all_slides
    slides_dir = tmp_dir / "slides"
    all_slides = generate_all_slides(script, str(slides_dir))
    total_slides = sum(len(v) for v in all_slides.values())
    print(f"  合計 {total_slides} 枚のスライドを生成")

    narration_out = str(output_dir / "narration.wav")
    first_audio = next((p for p in audio_files.values() if p and os.path.exists(p)), None)
    if first_audio:
        import subprocess as _sp, importlib
        ffmpeg_mod = importlib.import_module("modules.video_renderer")
        ffmpeg_bin = ffmpeg_mod._get_ffmpeg()
        narration_paths = [audio_files.get(ch) for ch in script["chapters"] if audio_files.get(ch) and os.path.exists(audio_files.get(ch))]
        concat_lines = [f"file '{p}'" for p in narration_paths]
        import tempfile as _tmp
        with _tmp.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as _f:
            _f.write("\n".join(concat_lines)); _concat_file = _f.name
        _sp.run([ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", _concat_file,
                 "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", narration_out], capture_output=True)
        os.unlink(_concat_file)
        print(f"  [ナレーション統合] → {narration_out}")

    print("\n[5/8] サムネイルを生成中...")
    from modules.thumbnail import generate_thumbnail
    thumbnail_path = str(output_dir / "thumbnail.png")
    generate_thumbnail(script["title"], script.get("subtitle", ""), thumbnail_path)

    print("\n[6/8] YouTube投稿用テキストを生成中...")
    from modules.output_writer import write_all_outputs
    text_files = write_all_outputs(script, str(output_dir))

    if not skip_video:
        print("\n[7/8] MP4動画をレンダリング中... (数分かかります)")
        from modules.video_renderer import render_video
        video_path = str(output_dir / "final_video.mp4")
        bgm_actual = bgm_path if os.path.exists(bgm_path) else None
        render_video(
            script,
            all_slides,
            audio_files,
            audio_durations,
            subtitle_entries,
            bgm_actual,
            video_path,
        )
    else:
        print("\n[7/8] 動画レンダリングをスキップ（--no-video）")
        video_path = None

    print("\n[8/8] 完了チェック")
    print("=" * 60)
    output_files = {
        "final_video.mp4":    output_dir / "final_video.mp4",
        "thumbnail.png":      output_dir / "thumbnail.png",
        "subtitle.srt":       output_dir / "subtitle.srt",
        "narration.wav":      output_dir / "narration.wav",
        "title.txt":          output_dir / "title.txt",
        "description.txt":    output_dir / "description.txt",
        "pinned_comment.txt": output_dir / "pinned_comment.txt",
        "rights_check.txt":   output_dir / "rights_check.txt",
    }

    all_ok = True
    for name, path in output_files.items():
        exists = path.exists()
        size = f"({path.stat().st_size // 1024}KB)" if exists else ""
        status = "✓" if exists else ("SKIP" if name == "final_video.mp4" and skip_video else "✗")
        print(f"  [{status}] {name} {size}")
        if not exists and name != "final_video.mp4":
            all_ok = False

    print("=" * 60)
    if all_ok or skip_video:
        print("生成完了！荒木さんが内容を確認してからYouTubeに投稿してください。")
        print("（自動投稿は行いません）")
    else:
        print("一部ファイルの生成に失敗しました。ログを確認してください。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
