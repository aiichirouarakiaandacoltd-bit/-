#!/usr/bin/env python3
"""
昭和・平成 なぜそうだったのか — 動画自動生成システム Ver1.0

使い方:
    python create_video.py --theme "テーマ名"
    python create_video.py --theme "テーマ名" --dry-run
    python create_video.py --theme "テーマ名" --voicevox-speed 0.87
    python create_video.py --theme "テーマ名" --no-video

出力先:
    videos/NNN_slug/ （自動採番）
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

SYSTEM_VERSION = "Ver1.0"
VIDEOS_BASE = BASE_DIR / "videos"
LOGS_DIR = BASE_DIR / "logs"


# ─────────────────────────────────────────────────────────────────────────────
# エラー表示ヘルパー
# ─────────────────────────────────────────────────────────────────────────────

def _err(title: str, cause: str, action: str):
    bar = "━" * 50
    print(f"\n{bar}")
    print(f"エラー内容: {title}")
    print(f"原因      : {cause}")
    print(f"荒木さんが次にやること:")
    for line in action.splitlines():
        print(f"  {line}")
    print(f"{bar}\n")


def _step(n: int, total: int, msg: str):
    print(f"\n[{n}/{total}] {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# 実行ログ
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionLog:
    def __init__(self, theme: str, dry_run: bool):
        self.data = {
            "system_version": SYSTEM_VERSION,
            "timestamp": datetime.now().isoformat(),
            "theme": theme,
            "dry_run": dry_run,
            "output_folder": None,
            "voicevox_connected": False,
            "voicevox_speed": None,
            "bgm_found": False,
            "bgm_path": None,
            "video_generated": False,
            "status": "running",
            "errors": [],
            "files_generated": {},
        }

    def set(self, **kwargs):
        self.data.update(kwargs)

    def add_error(self, msg: str):
        self.data["errors"].append({"time": datetime.now().isoformat(), "message": msg})

    def add_file(self, key: str, path):
        if path:
            self.data["files_generated"][key] = str(path)

    def save(self):
        LOGS_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = "".join(c if c.isalnum() else "_" for c in self.data["theme"])[:20]
        log_path = LOGS_DIR / f"{ts}_{slug}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"  [ログ] → {log_path.relative_to(BASE_DIR)}")
        return log_path


# ─────────────────────────────────────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"昭和・平成 なぜそうだったのか — 動画自動生成システム {SYSTEM_VERSION}"
    )
    parser.add_argument("--theme", required=True, help="動画テーマ")
    parser.add_argument("--output", default=None,
                        help="出力先ベースディレクトリ（デフォルト: ./videos/）")
    parser.add_argument("--bgm", default="./assets/bgm/UNL1337.wav", help="BGMファイルパス")
    parser.add_argument("--no-video", action="store_true", help="動画レンダリングをスキップ")
    parser.add_argument("--dry-run", action="store_true",
                        help="APIコール・動画生成をスキップ（動作確認用）")
    parser.add_argument("--voicevox-speed", type=float, default=None,
                        help="VOICEVOX話速（0.85〜0.90 推奨）")
    args = parser.parse_args()

    theme = args.theme
    dry_run = args.dry_run
    skip_video = args.no_video or dry_run

    log = ExecutionLog(theme, dry_run)

    # ── バナー ─────────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"  昭和・平成 なぜそうだったのか")
    print(f"  動画自動生成システム {SYSTEM_VERSION}")
    print("=" * 60)
    print(f"  テーマ: {theme}")
    if dry_run:
        print("  モード: DRY-RUN（音声・動画生成をスキップ）")
    print()

    # ── config ────────────────────────────────────────────────────────────
    from modules.config import REQUIRE_VOICEVOX, REQUIRE_BGM, VOICEVOX_SPEED_SCALE
    import modules.config as _cfg

    if args.voicevox_speed is not None:
        _cfg.VOICEVOX_SPEED_SCALE = args.voicevox_speed

    speed = _cfg.VOICEVOX_SPEED_SCALE
    bgm_path = str(Path(args.bgm).resolve())
    bgm_exists = os.path.exists(bgm_path)

    log.set(voicevox_speed=speed, bgm_path=bgm_path, bgm_found=bgm_exists)

    # ── 出力フォルダ作成 ───────────────────────────────────────────────────
    from modules.output_packager import make_video_dir, _estimate_duration_sec, _fmt_sec

    base_dir = Path(args.output).resolve() if args.output else VIDEOS_BASE
    try:
        root = make_video_dir(base_dir, theme)
    except Exception as e:
        _err(
            "出力フォルダの作成に失敗しました",
            str(e),
            f"{base_dir} への書き込み権限を確認してください",
        )
        log.add_error(f"フォルダ作成失敗: {e}")
        log.set(status="failed")
        log.save()
        return 1

    log.set(output_folder=str(root))
    print(f"  出力先: {root.relative_to(BASE_DIR)}")

    tmp_dir = root / "_tmp"
    tmp_dir.mkdir(exist_ok=True)

    TOTAL_STEPS = 10

    # ── 事前チェック ───────────────────────────────────────────────────────
    _step(1, TOTAL_STEPS, "事前チェック")

    from modules.narration import _voicevox_available
    voicevox_ok = _voicevox_available() if not dry_run else False
    log.set(voicevox_connected=voicevox_ok)

    if not dry_run:
        if not voicevox_ok:
            if REQUIRE_VOICEVOX:
                _err(
                    "VOICEVOXに接続できません",
                    "VOICEVOXアプリが起動していないか、ポート50021が使用できません",
                    "1. VOICEVOXアプリを起動してください\n"
                    "2. 確認URL: http://127.0.0.1:50021\n"
                    "3. 再度コマンドを実行してください",
                )
                log.add_error("VOICEVOX未接続")
                log.set(status="failed")
                log.save()
                return 1
            else:
                print("  [警告] VOICEVOX未起動 → espeak-ngを使用（REQUIRE_VOICEVOX=False）")
        else:
            print(f"  [OK] VOICEVOX 接続確認 / 話者: 青山龍星 / 話速: {speed}")

        if not skip_video and not bgm_exists:
            if REQUIRE_BGM:
                _err(
                    "BGMファイルが見つかりません",
                    f"指定パス: {bgm_path}",
                    "1. assets/bgm/UNL1337.wav にBGMファイルを配置してください\n"
                    "2. または --bgm オプションで別パスを指定してください",
                )
                log.add_error(f"BGMファイル未配置: {bgm_path}")
                log.set(status="failed")
                log.save()
                return 1
            else:
                print(f"  [警告] BGMファイルが見つかりません → BGMなしで続行")
        elif bgm_exists:
            print(f"  [OK] BGM 確認: {Path(bgm_path).name}")
    else:
        print("  [DRY-RUN] VOICEVOX・BGMチェックをスキップ")

    # ── 台本生成 ───────────────────────────────────────────────────────────
    _step(2, TOTAL_STEPS, "台本を生成中...")
    try:
        from modules.script_generator import generate_script
        script = generate_script(theme)
    except Exception as e:
        _err("台本生成に失敗しました", str(e),
             "modules/script_generator.py を確認してください")
        log.add_error(f"台本生成失敗: {e}")
        log.set(status="failed")
        log.save()
        return 1

    print(f"  タイトル: {script['title']}")
    chapters = script.get("chapters", {})
    total_narr = "".join(d.get("narration", "") for d in chapters.values())
    est_sec = _estimate_duration_sec(total_narr, speed)
    print(f"  推定尺: {_fmt_sec(est_sec)}（話速{speed}基準）")

    # ── ナレーション生成 ───────────────────────────────────────────────────
    _step(3, TOTAL_STEPS,
          "ナレーション音声を生成中..." if not dry_run else "ナレーション生成をスキップ（dry-run）")

    audio_files = {}
    audio_durations = {}
    narration_wav = root / "05_voice" / "narration.wav"
    has_narration = False

    if not dry_run:
        try:
            from modules.narration import generate_chapter_narrations
            narration_dir = tmp_dir / "narration"
            audio_files = generate_chapter_narrations(script, str(narration_dir))
        except Exception as e:
            _err("音声生成に失敗しました", str(e),
                 "VOICEVOXが起動していることを確認してください")
            log.add_error(f"音声生成失敗: {e}")
            skip_video = True

        for chapter_name, audio_path in audio_files.items():
            if audio_path and os.path.exists(audio_path):
                try:
                    from moviepy import AudioFileClip
                    clip = AudioFileClip(audio_path)
                    audio_durations[chapter_name] = clip.duration
                    clip.close()
                    print(f"  {chapter_name}: {audio_durations[chapter_name]:.1f}秒")
                except Exception:
                    audio_durations[chapter_name] = chapters[chapter_name].get("duration", 60.0)
            else:
                audio_durations[chapter_name] = chapters[chapter_name].get("duration", 60.0)

        # ナレーション.wav 統合
        first_audio = next((p for p in audio_files.values() if p and os.path.exists(p)), None)
        if first_audio:
            try:
                import subprocess as _sp, importlib
                ffmpeg_mod = importlib.import_module("modules.video_renderer")
                ffmpeg_bin = ffmpeg_mod._get_ffmpeg()
                narr_paths = [audio_files[ch] for ch in script["chapters"]
                              if audio_files.get(ch) and os.path.exists(audio_files.get(ch))]
                import tempfile as _tmp2
                with _tmp2.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                              encoding="utf-8") as _f:
                    _f.write("\n".join(f"file '{p}'" for p in narr_paths))
                    _concat = _f.name
                _sp.run(
                    [ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", _concat,
                     "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le", str(narration_wav)],
                    capture_output=True, check=True,
                )
                os.unlink(_concat)
                has_narration = narration_wav.exists()
                if has_narration:
                    print(f"  [統合音声] → 05_voice/narration.wav")
                    log.add_file("narration", str(narration_wav))
            except Exception as e:
                log.add_error(f"音声統合失敗: {e}")
                print(f"  [警告] 音声統合に失敗: {e}")
    else:
        audio_durations = {ch: chapters[ch].get("duration", 60.0) for ch in chapters}
        print("  [DRY-RUN] スキップ")

    # ── 字幕生成 ───────────────────────────────────────────────────────────
    _step(4, TOTAL_STEPS,
          "字幕（SRT）を生成中..." if not dry_run else "字幕生成をスキップ（dry-run）")

    srt_path = None
    subtitle_entries = []

    if not dry_run:
        try:
            from modules.subtitle import generate_srt, get_subtitle_entries
            srt_path = str(root / "06_subtitles" / "subtitles.srt")
            generate_srt(script, audio_durations, srt_path)
            subtitle_entries = get_subtitle_entries(script, audio_durations)
            print(f"  → 06_subtitles/subtitles.srt")
            log.add_file("subtitle", srt_path)
        except Exception as e:
            _err("字幕生成に失敗しました", str(e),
                 "modules/subtitle.py を確認してください")
            log.add_error(f"字幕生成失敗: {e}")
    else:
        print("  [DRY-RUN] スキップ")

    # ── スライド画像生成 ───────────────────────────────────────────────────
    _step(5, TOTAL_STEPS,
          "スライド画像を生成中..." if not dry_run else "スライド生成をスキップ（dry-run）")

    all_slides = {}

    if not dry_run:
        try:
            from modules.image_generator import generate_all_slides
            slides_dir = tmp_dir / "slides"
            all_slides = generate_all_slides(script, str(slides_dir))
            total_slides = sum(len(v) for v in all_slides.values())
            print(f"  合計 {total_slides} 枚のスライドを生成")
        except Exception as e:
            _err("スライド画像生成に失敗しました", str(e),
                 "Pillowライブラリとフォントファイルを確認してください")
            log.add_error(f"スライド生成失敗: {e}")
    else:
        print("  [DRY-RUN] スキップ")

    # ── サムネイル生成 ─────────────────────────────────────────────────────
    _step(6, TOTAL_STEPS,
          "サムネイルを生成中..." if not dry_run else "サムネイル生成をスキップ（dry-run）")

    thumbnail_path = root / "03_thumbnail" / "thumbnail.png"

    if not dry_run:
        try:
            from modules.thumbnail import generate_thumbnail
            generate_thumbnail(script["title"], script.get("subtitle", ""),
                               str(thumbnail_path))
            print(f"  → 03_thumbnail/thumbnail.png")
            log.add_file("thumbnail", str(thumbnail_path))
        except Exception as e:
            _err("サムネイル生成に失敗しました", str(e),
                 "modules/thumbnail.py を確認してください")
            log.add_error(f"サムネイル生成失敗: {e}")
    else:
        print("  [DRY-RUN] スキップ")

    # ── 動画レンダリング ───────────────────────────────────────────────────
    _step(7, TOTAL_STEPS,
          "MP4動画をレンダリング中... (数分かかります)" if not skip_video
          else ("動画レンダリングをスキップ（--no-video）" if args.no_video
                else "動画レンダリングをスキップ（dry-run）"))

    video_path = root / "11_video" / "output.mp4"
    video_exists = False
    video_error = ""

    if not skip_video:
        try:
            from modules.video_renderer import render_video
            bgm_actual = bgm_path if bgm_exists else None
            render_video(
                script, all_slides, audio_files, audio_durations,
                subtitle_entries, bgm_actual, str(video_path),
            )
            if video_path.exists() and video_path.stat().st_size > 0:
                video_exists = True
                mb = video_path.stat().st_size // (1024 * 1024)
                print(f"  → 11_video/output.mp4 ({mb}MB)")
                log.add_file("video", str(video_path))
                log.set(video_generated=True)
            else:
                video_error = "output.mp4 が0KBまたは存在しません"
                _err("動画ファイルが0KBです", video_error,
                     "FFmpegのログを確認してください")
                log.add_error(video_error)
        except Exception as e:
            video_error = str(e)
            _err("動画レンダリングに失敗しました", str(e),
                 "FFmpegがインストールされているか確認: ffmpeg -version")
            log.add_error(f"動画レンダリング失敗: {e}")
    else:
        print("  スキップ")

    # ── Markdownファイル生成 ───────────────────────────────────────────────
    _step(8, TOTAL_STEPS, "制作パッケージを生成中...")

    from modules.output_packager import (
        write_research_md, write_titles_md, write_thumbnail_ideas_md,
        write_script_md, write_voice_check_md, write_bgm_check_md,
        write_ai_image_prompts_md, write_description_md, write_fixed_comment_md,
        write_rights_check_md, write_video_check_md, write_upload_checklist_md,
    )

    file_map: dict[str, str] = {}

    def _safe_write(key, fn, *a, **kw):
        try:
            p = fn(*a, **kw)
            file_map[key] = str(p)
            log.add_file(key, str(p))
            return p
        except Exception as e:
            _err(f"{key} ファイルの生成に失敗しました", str(e),
                 "output_packager.py を確認してください")
            log.add_error(f"{key} 生成失敗: {e}")
            return None

    _safe_write("research",        write_research_md,       script, root, dry_run)
    _safe_write("titles",          write_titles_md,          script, root, dry_run)
    _safe_write("thumbnail_ideas", write_thumbnail_ideas_md, script, root, dry_run)
    _safe_write("script",          write_script_md,          script, root, dry_run)
    _safe_write("voice_check",     write_voice_check_md,
                root, voicevox_ok, speed, audio_durations, dry_run)
    _safe_write("bgm_check",       write_bgm_check_md,       root, bgm_path, bgm_exists, dry_run)
    _safe_write("prompts",         write_ai_image_prompts_md, script, root, dry_run)
    _safe_write("description",     write_description_md,     script, root, dry_run)
    _safe_write("fixed_comment",   write_fixed_comment_md,   script, root, dry_run)
    _safe_write("rights_check",    write_rights_check_md,    script, root, dry_run)
    _safe_write("video_check",     write_video_check_md,
                root, video_exists, bgm_path, bgm_exists, has_narration, video_error, dry_run)
    _safe_write("upload_checklist", write_upload_checklist_md, script, root, dry_run)

    if has_narration and narration_wav.exists():
        file_map["narration"] = str(narration_wav)
    if srt_path and os.path.exists(srt_path):
        file_map["subtitle"] = srt_path
    if video_exists:
        file_map["video"] = str(video_path)

    print(f"  {len(file_map)} ファイル生成完了")

    # ── summary.md 生成 ────────────────────────────────────────────────────
    _step(9, TOTAL_STEPS, "summary.md を生成中...")
    from modules.output_packager import write_summary_md
    try:
        summary_path = write_summary_md(
            root=root, theme=theme, script=script, speed=speed,
            bgm_path=bgm_path, bgm_exists=bgm_exists,
            audio_durations=audio_durations, voicevox_ok=voicevox_ok,
            video_exists=video_exists, file_map=file_map, dry_run=dry_run,
        )
        log.add_file("summary", str(summary_path))
        print(f"  → summary.md")
    except Exception as e:
        _err("summary.md の生成に失敗しました", str(e),
             "output_packager.py を確認してください")
        log.add_error(f"summary生成失敗: {e}")

    # ── 実行ログ保存 ───────────────────────────────────────────────────────
    _step(10, TOTAL_STEPS, "実行ログを保存中...")
    log.set(status="success" if not log.data["errors"] else "completed_with_warnings")
    log_path = log.save()

    # ── 完了メッセージ ─────────────────────────────────────────────────────
    rel_root = root.relative_to(BASE_DIR)
    print("\n" + "=" * 60)
    if not log.data["errors"]:
        print("✅ 動画生成パッケージを作成しました。")
    else:
        print("⚠️  動画生成パッケージを作成しました（一部エラーあり）。")
    print(f"テーマ      : {theme}")
    print(f"出力フォルダ: {rel_root}")
    print(f"システム    : 動画自動生成システム {SYSTEM_VERSION}")
    print()
    print("確認する順番:")
    print(f"  1. {rel_root / 'summary.md'}")
    print(f"  2. {rel_root / '04_script' / 'script.md'}")
    print(f"  3. {rel_root / '05_voice' / 'voice_check.md'}")
    print(f"  4. {rel_root / '10_rights_check' / 'rights_check.md'}")
    print(f"  5. {rel_root / '12_upload_package' / 'upload_checklist.md'}")
    if video_exists:
        print(f"  6. {rel_root / '11_video' / 'output.mp4'} （最初から最後まで視聴）")
    print()
    print("投稿前に必ず、数字・日付・固有名詞・権利表記を確認してください。")
    print("（このシステムは自動投稿しません。投稿は必ず荒木さんが手動で行ってください）")
    print("=" * 60)

    if log.data["errors"]:
        print(f"\n⚠️  エラー {len(log.data['errors'])} 件 → ログ: {log_path.relative_to(BASE_DIR)}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[中断] 処理を中断しました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n予期しないエラーが発生しました:")
        traceback.print_exc()
        sys.exit(1)
