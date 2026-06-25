#!/usr/bin/env python3
"""
動画自動生成システム Ver1.0

使い方:
    # 本番（VOICEVOX + 権利確認済み BGM が必要）
    python create_video.py --channel showa_heisei --theme "テーマ名"
    python create_video.py --channel showa_heisei --theme "テーマ名" --voicevox-speed 0.92
    python create_video.py --channel imperial      --theme "テーマ名"

    # 動画レンダリングのみスキップ（音声・字幕は生成）
    python create_video.py --channel showa_heisei --theme "テーマ名" --no-video

    # Markdown のみ確認（VOICEVOX・BGM 不要）
    python create_video.py --channel showa_heisei --theme "テーマ名" --dry-run

    # 技術検証用（VOICEVOX 未接続時にサイン波を使用 / 投稿不可）
    python create_video.py --channel showa_heisei --theme "テーマ名" --test-mode

出力先:
    videos/NNN_slug/ （自動採番）
"""

import argparse
import json
import os
import subprocess
import sys
import traceback
import wave
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

SYSTEM_VERSION = "Ver1.0"
VIDEOS_BASE    = BASE_DIR / "videos"
LOGS_DIR       = BASE_DIR / "logs"


# ─────────────────────────────────────────────────────────────────────────────
# ユーティリティ
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


def _get_wav_duration(path: str) -> float:
    """WAV ファイルの実再生時間（秒）を返す。失敗時は 0.0。"""
    try:
        with wave.open(str(path), "r") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def _find_bgm(bgm_dir: Path, bgm_override: str | None) -> tuple[Path | None, bool]:
    """
    BGM ファイルを探して (path_or_None, is_override) を返す。
    --bgm が指定されている場合はそのパスを使う（権利チェックは警告のみ）。
    指定なしの場合は bgm_dir から最初の WAV を探す。
    """
    if bgm_override:
        p = Path(bgm_override).resolve()
        return (p if p.exists() else None), True
    wav_files = sorted(bgm_dir.glob("*.wav")) if bgm_dir.exists() else []
    return (wav_files[0] if wav_files else None), False


def _check_bgm_rights(bgm_path: Path | None, channel: str) -> tuple[bool, str]:
    """
    BGM ファイルがレジストリに登録され、指定チャンネルへの使用が許可されているか確認する。
    戻り値: (ok: bool, message: str)
    """
    if bgm_path is None:
        return False, f"assets/bgm/{channel}/ に BGM ファイルが見つかりません"

    registry_path = BASE_DIR / "assets" / "bgm" / "bgm_registry.json"
    if not registry_path.exists():
        return False, f"BGM レジストリが見つかりません: {registry_path}"

    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    file_name = bgm_path.name
    record = next(
        (b for b in registry.get("bgm_files", []) if b["file_name"] == file_name),
        None,
    )

    if record is None:
        return False, (
            f"{file_name} は bgm_registry.json に未登録です。\n"
            f"権利情報を確認の上、レジストリに追加してから使用してください。"
        )

    if channel not in record.get("allowed_channels", []):
        allowed = "、".join(record["allowed_channels"]) or "なし"
        return False, (
            f"{file_name} はチャンネル '{channel}' への使用が許可されていません。\n"
            f"許可チャンネル: {allowed}\n"
            f"備考: {record.get('note', '')}"
        )

    credit = f" クレジット: 「{record['credit_text']}」" if record.get("credit_required") else ""
    return True, f"{file_name} / {record['source']} / {record['license']}{credit}"


def _run_ffprobe(mp4_path: str) -> dict:
    """ffprobe で MP4 を検証し、結果を辞書で返す。"""
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
        import shutil
        ffprobe = shutil.which("ffprobe")
    except Exception:
        ffprobe = "ffprobe"

    cmd = [ffprobe, "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", mp4_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": result.stderr}

    probe     = json.loads(result.stdout)
    fmt       = probe.get("format", {})
    streams   = probe.get("streams", [])
    v_stream  = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream  = next((s for s in streams if s.get("codec_type") == "audio"), None)

    fps = None
    if v_stream:
        r = v_stream.get("r_frame_rate", "0/1")
        num, den = (int(x) for x in r.split("/"))
        fps = round(num / den, 2) if den else 0

    duration = float(fmt.get("duration", 0))
    return {
        "ok":            bool(v_stream and a_stream),
        "duration_sec":  duration,
        "size_bytes":    int(fmt.get("size", 0)),
        "video_codec":   v_stream.get("codec_name") if v_stream else None,
        "width":         v_stream.get("width")       if v_stream else None,
        "height":        v_stream.get("height")      if v_stream else None,
        "fps":           fps,
        "pix_fmt":       v_stream.get("pix_fmt")     if v_stream else None,
        "audio_codec":   a_stream.get("codec_name")  if a_stream else None,
        "sample_rate":   a_stream.get("sample_rate") if a_stream else None,
        "channels":      a_stream.get("channels")    if a_stream else None,
        "bitrate_kbps":  int(fmt.get("bit_rate", 0)) // 1000,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 実行ログ
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionLog:
    def __init__(self, theme: str, channel: str, dry_run: bool, test_mode: bool):
        self.data = {
            "system_version":   SYSTEM_VERSION,
            "timestamp":        datetime.now().isoformat(),
            "theme":            theme,
            "channel":          channel,
            "dry_run":          dry_run,
            "test_mode":        test_mode,
            "output_folder":    None,
            "voicevox_connected": False,
            "voicevox_speaker": None,
            "voicevox_speed":   None,
            "bgm_found":        False,
            "bgm_path":         None,
            "bgm_rights_ok":    False,
            "video_generated":  False,
            "ffprobe":          None,
            "production_pass":  False,
            "status":           "running",
            "errors":           [],
            "files_generated":  {},
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
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        description=f"動画自動生成システム {SYSTEM_VERSION}"
    )
    parser.add_argument("--channel", required=True,
                        choices=["showa_heisei", "imperial"],
                        help="チャンネルプロファイル（showa_heisei / imperial）")
    parser.add_argument("--theme", required=True, help="動画テーマ")
    parser.add_argument("--output", default=None,
                        help="出力先ベースディレクトリ（デフォルト: ./videos/）")
    parser.add_argument("--bgm", default=None,
                        help="BGM ファイルを直接指定（省略時はチャンネル BGM フォルダから自動選択）")
    parser.add_argument("--no-video", action="store_true",
                        help="動画レンダリングをスキップ")
    parser.add_argument("--dry-run", action="store_true",
                        help="VOICEVOX・動画生成をスキップ（Markdown のみ生成）")
    parser.add_argument("--test-mode", action="store_true",
                        help="技術検証モード: VOICEVOX 未接続時にサイン波を使用（投稿不可）")
    parser.add_argument("--voicevox-speed", type=float, default=None,
                        help="VOICEVOX 話速を上書き（チャンネルのデフォルト値を変更）")
    args = parser.parse_args()

    channel   = args.channel
    theme     = args.theme
    dry_run   = args.dry_run
    test_mode = args.test_mode
    skip_video = args.no_video or dry_run

    # ── チャンネルプロファイル読み込み ────────────────────────────────────
    from modules.channel_config import get_profile, get_bgm_dir, validate_speed
    try:
        profile = get_profile(channel)
    except ValueError as e:
        print(f"エラー: {e}")
        return 1

    # ── 話速決定・検証 ──────────────────────────────────────────────────────
    speed = args.voicevox_speed if args.voicevox_speed else profile["voicevox_speed_default"]
    speed_ok, speed_msg = validate_speed(channel, speed)
    if not speed_ok and not dry_run:
        print(f"  [警告] {speed_msg}")

    # ── config モジュールにチャンネル設定を適用 ──────────────────────────
    import modules.config as _cfg
    _cfg.VOICEVOX_SPEED_SCALE       = speed
    _cfg.VOICEVOX_SPEAKER           = profile["voicevox_speaker"]
    _cfg.BGM_VOLUME_DB              = profile["bgm_volume_db"]
    _cfg.NARRATION_VOLUME_DB        = profile["narration_volume_db"]
    _cfg.BGM_FADE_IN_SEC            = profile["bgm_fade_in_sec"]
    _cfg.BGM_FADE_OUT_SEC           = profile["bgm_fade_out_sec"]
    _cfg.VIDEO_SPEC["width"]        = profile["video_width"]
    _cfg.VIDEO_SPEC["height"]       = profile["video_height"]
    _cfg.VIDEO_SPEC["fps"]          = profile["video_fps"]

    log = ExecutionLog(theme, channel, dry_run, test_mode)
    log.set(voicevox_speaker=profile["voicevox_speaker"], voicevox_speed=speed)

    # ── バナー ────────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"  {profile['name']}")
    print(f"  動画自動生成システム {SYSTEM_VERSION}")
    print("=" * 60)
    print(f"  テーマ      : {theme}")
    print(f"  チャンネル  : {channel}")
    print(f"  話速        : {speed}（{profile['voicevox_speaker_name']}）")
    if dry_run:
        print("  モード      : DRY-RUN（音声・動画生成をスキップ）")
    elif test_mode:
        print("  モード      : ⚠️  TEST ONLY（VOICEVOX 未接続時にサイン波を使用）")
        print("               投稿不可のMP4が生成されます。")
    print()

    # ── BGM パス決定 ─────────────────────────────────────────────────────
    bgm_dir  = get_bgm_dir(channel, BASE_DIR)
    bgm_path, is_override = _find_bgm(bgm_dir, args.bgm)
    bgm_exists = bgm_path is not None and bgm_path.exists()
    log.set(bgm_path=str(bgm_path) if bgm_path else None, bgm_found=bgm_exists)

    # ── 出力フォルダ作成 ──────────────────────────────────────────────────
    from modules.output_packager import make_video_dir, _estimate_duration_sec, _fmt_sec

    base_dir = Path(args.output).resolve() if args.output else VIDEOS_BASE
    try:
        root = make_video_dir(base_dir, theme)
    except Exception as e:
        _err("出力フォルダの作成に失敗しました", str(e),
             f"{base_dir} への書き込み権限を確認してください")
        log.add_error(f"フォルダ作成失敗: {e}")
        log.set(status="failed")
        log.save()
        return 1

    log.set(output_folder=str(root))
    print(f"  出力先: {root.relative_to(BASE_DIR)}")

    tmp_dir = root / "_tmp"
    tmp_dir.mkdir(exist_ok=True)

    TOTAL_STEPS = 11  # ffprobe 検証を追加

    # ── Step 1: 事前チェック ───────────────────────────────────────────────
    _step(1, TOTAL_STEPS, "事前チェック")

    from modules.narration import _voicevox_available
    voicevox_ok = _voicevox_available() if not dry_run else False
    log.set(voicevox_connected=voicevox_ok)

    if not dry_run:
        if voicevox_ok:
            print(f"  [OK] VOICEVOX 接続確認")
            print(f"       話者: {profile['voicevox_speaker_name']} / ID: {profile['voicevox_speaker']} / 話速: {speed}")
        else:
            if test_mode:
                print(f"  [TEST ONLY] VOICEVOX 未接続 → サイン波で続行")
                print(f"              ⚠️  生成 MP4 は投稿不可です")
            else:
                _err(
                    "VOICEVOXに接続できません",
                    "VOICEVOXアプリが起動していないか、ポート50021が使用できません",
                    "1. VOICEVOXアプリを起動してください\n"
                    "2. 確認URL: http://127.0.0.1:50021/version\n"
                    "3. 再度コマンドを実行してください\n"
                    "技術検証のみの場合: --test-mode を追加してください（投稿不可）",
                )
                log.add_error("VOICEVOX未接続")
                log.set(status="failed")
                log.save()
                return 1

        # BGM チェック
        if not skip_video:
            if not bgm_exists:
                if not test_mode:
                    _err(
                        "BGMファイルが見つかりません",
                        f"チャンネル {channel} 用 BGM: {bgm_dir}/*.wav が存在しません",
                        f"1. {bgm_dir}/ に BGM ファイルを配置してください\n"
                        f"2. assets/bgm/bgm_registry.json に権利情報を登録してください\n"
                        f"3. または --bgm /path/to/file.wav で直接指定してください\n"
                        f"権利確認が取れていない BGM ファイルは使用しないでください",
                    )
                    log.add_error(f"BGMファイル未配置: {bgm_dir}")
                    log.set(status="failed")
                    log.save()
                    return 1
                else:
                    print(f"  [TEST ONLY] BGM 未配置 → BGM なしで続行（投稿不可）")
            else:
                bgm_rights_ok, bgm_rights_msg = _check_bgm_rights(bgm_path, channel)
                log.set(bgm_rights_ok=bgm_rights_ok)

                if is_override:
                    print(f"  [BGM] --bgm 直接指定: {bgm_path.name}（レジストリ確認スキップ）")
                elif bgm_rights_ok:
                    print(f"  [OK] BGM: {bgm_rights_msg}")
                else:
                    if not test_mode:
                        _err(
                            "BGMの権利確認ができません",
                            bgm_rights_msg,
                            "assets/bgm/bgm_registry.json を確認し、\n"
                            "チャンネルへの使用許可を確認してから使用してください",
                        )
                        log.add_error(f"BGM権利未確認: {bgm_rights_msg}")
                        log.set(status="failed")
                        log.save()
                        return 1
                    else:
                        print(f"  [TEST ONLY] BGM 権利未確認: {bgm_rights_msg}")
    else:
        print("  [DRY-RUN] VOICEVOX・BGM チェックをスキップ")

    # ── Step 2: 台本生成 ──────────────────────────────────────────────────
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

    target_min = profile["target_duration_min"]
    target_max = profile["target_duration_max"]
    if est_sec < target_min:
        print(f"  [注意] 推定尺 {_fmt_sec(est_sec)} < 目標 {_fmt_sec(target_min)}。"
              f"VOICEVOXで実尺測定後に確認してください。")
    elif est_sec > target_max:
        print(f"  [注意] 推定尺 {_fmt_sec(est_sec)} > 目標 {_fmt_sec(target_max)}。"
              f"台本の冗長部分を削ることを検討してください。")

    # ── Step 3: ナレーション生成 ─────────────────────────────────────────
    _step(3, TOTAL_STEPS,
          "ナレーション音声を生成中..." if not dry_run else "ナレーション生成をスキップ（dry-run）")

    audio_files: dict[str, str | None] = {}
    audio_durations: dict[str, float] = {}
    narration_wav = root / "05_voice" / "narration.wav"
    has_narration = False
    using_test_audio = False

    if not dry_run:
        try:
            from modules.narration import generate_chapter_narrations, VoicevoxUnavailableError
            narration_dir = tmp_dir / "narration"
            audio_files = generate_chapter_narrations(
                script, str(narration_dir),
                test_mode=test_mode,
                speaker=profile["voicevox_speaker"],
                speed_scale=speed,
            )
            using_test_audio = (not voicevox_ok) and test_mode

        except VoicevoxUnavailableError as e:
            _err("VOICEVOXに接続できません", str(e),
                 "VOICEVOXを起動してください")
            log.add_error(f"VOICEVOX接続失敗: {e}")
            log.set(status="failed")
            log.save()
            return 1
        except Exception as e:
            _err("音声生成に失敗しました", str(e),
                 "VOICEVOXが起動していることを確認してください")
            log.add_error(f"音声生成失敗: {e}")
            skip_video = True

        # ── Step 4 組み込み: 実音声尺を WAV ファイルから取得 ──────────────
        for ch_name, audio_path in audio_files.items():
            if audio_path and os.path.exists(audio_path):
                real_dur = _get_wav_duration(audio_path)
                if real_dur > 0:
                    audio_durations[ch_name] = real_dur
                    print(f"  {ch_name}: {real_dur:.1f}秒（実測）")
                else:
                    audio_durations[ch_name] = chapters[ch_name].get("duration", 60.0)
                    print(f"  {ch_name}: {audio_durations[ch_name]:.1f}秒（推定）")
            else:
                audio_durations[ch_name] = chapters[ch_name].get("duration", 60.0)

        # 実音声合計と目標尺の確認
        total_actual = sum(audio_durations.values())
        print(f"\n  実音声合計: {_fmt_sec(total_actual)}")
        if total_actual < target_min:
            print(f"  [尺不足] {_fmt_sec(total_actual)} < 目標 {_fmt_sec(target_min)}")
            print(f"  → 台本の「根拠ある背景説明・普及過程・なぜ習慣が変わったか」を追加してください")
        elif total_actual > target_max:
            print(f"  [尺超過] {_fmt_sec(total_actual)} > 目標 {_fmt_sec(target_max)}")
            print(f"  → 重複表現・冗長な導入・同じ結論の繰り返しを削ってください")
        else:
            print(f"  [OK] 尺 {_fmt_sec(total_actual)} は目標範囲内（{_fmt_sec(target_min)}〜{_fmt_sec(target_max)}）")

        # ナレーション.wav 統合
        valid_audio = [audio_files[ch] for ch in script["chapters"]
                       if audio_files.get(ch) and os.path.exists(str(audio_files.get(ch)))]
        if valid_audio:
            try:
                try:
                    import static_ffmpeg
                    static_ffmpeg.add_paths()
                    import shutil as _sh
                    ffmpeg_bin = _sh.which("ffmpeg")
                except Exception:
                    ffmpeg_bin = "ffmpeg"

                import tempfile as _tmp2
                with _tmp2.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                               encoding="utf-8") as _f:
                    _f.write("\n".join(f"file '{p}'" for p in valid_audio))
                    _concat = _f.name
                subprocess.run(
                    [ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", _concat,
                     "-ar", "44100", "-ac", "2", "-acodec", "pcm_s16le",
                     str(narration_wav)],
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

    # ── Step 4: 字幕生成（実音声尺基準） ─────────────────────────────────
    _step(4, TOTAL_STEPS,
          "字幕（SRT）を生成中...（実音声尺基準）" if not dry_run
          else "字幕生成をスキップ（dry-run）")

    srt_path = None
    subtitle_entries = []

    if not dry_run:
        try:
            from modules.subtitle import generate_srt, get_subtitle_entries
            srt_path = str((root / "06_subtitles" / "subtitles.srt").resolve())
            generate_srt(script, audio_durations, srt_path)
            subtitle_entries = get_subtitle_entries(script, audio_durations)
            print(f"  → 06_subtitles/subtitles.srt（実音声尺基準）")
            log.add_file("subtitle", srt_path)
        except Exception as e:
            _err("字幕生成に失敗しました", str(e),
                 "modules/subtitle.py を確認してください")
            log.add_error(f"字幕生成失敗: {e}")
    else:
        print("  [DRY-RUN] スキップ")

    # ── Step 5: スライド画像生成 ─────────────────────────────────────────
    _step(5, TOTAL_STEPS,
          "スライド画像を生成中..." if not dry_run else "スライド生成をスキップ（dry-run）")

    all_slides: dict = {}

    if not dry_run:
        try:
            from modules.image_generator import generate_all_slides
            slides_dir = (tmp_dir / "slides").resolve()
            all_slides_raw = generate_all_slides(script, str(slides_dir))
            # 絶対パスに統一（FFmpeg concat から正しく参照できるよう）
            all_slides = {
                k: [str(Path(p).resolve()) for p in v]
                for k, v in all_slides_raw.items()
            }
            total_slides = sum(len(v) for v in all_slides.values())
            print(f"  合計 {total_slides} 枚のスライドを生成")
        except Exception as e:
            _err("スライド画像生成に失敗しました", str(e),
                 "Pillow ライブラリとフォントファイルを確認してください")
            log.add_error(f"スライド生成失敗: {e}")
    else:
        print("  [DRY-RUN] スキップ")

    # ── Step 6: サムネイル生成 ────────────────────────────────────────────
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

    # ── Step 7: 動画レンダリング ─────────────────────────────────────────
    _step(7, TOTAL_STEPS,
          "MP4動画をレンダリング中... (数分かかります)" if not skip_video
          else ("動画レンダリングをスキップ（--no-video）" if args.no_video
                else "動画レンダリングをスキップ（dry-run）"))

    video_path   = root / "11_video" / "output.mp4"
    video_exists = False
    video_error  = ""

    if not skip_video:
        try:
            # static_ffmpeg をパス追加（ない場合は無視）
            try:
                import static_ffmpeg
                static_ffmpeg.add_paths()
                import modules.video_renderer as _vr, shutil as _sh2
                _vr.FFMPEG_BIN = _sh2.which("ffmpeg")
            except Exception:
                pass

            from modules.video_renderer import render_video
            bgm_actual = bgm_path if (bgm_exists and not test_mode) else \
                         (bgm_path if bgm_exists else None)
            render_video(
                script, all_slides, audio_files, audio_durations,
                subtitle_entries, str(bgm_actual) if bgm_actual else None,
                str(video_path.resolve()),
                srt_path=srt_path,
            )
            if video_path.exists() and video_path.stat().st_size > 0:
                video_exists = True
                mb = video_path.stat().st_size // (1024 * 1024)
                print(f"  → 11_video/output.mp4 ({mb}MB)")
                log.add_file("video", str(video_path))
                log.set(video_generated=True)
            else:
                video_error = "output.mp4 が 0 KB または存在しません"
                _err("動画ファイルが 0 KB です", video_error,
                     "FFmpeg のログを確認してください")
                log.add_error(video_error)
        except Exception as e:
            video_error = str(e)
            _err("動画レンダリングに失敗しました", str(e),
                 "FFmpeg がインストールされているか確認: ffmpeg -version")
            log.add_error(f"動画レンダリング失敗: {e}")
    else:
        print("  スキップ")

    # ── Step 8: Markdown ファイル生成 ─────────────────────────────────────
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

    _safe_write("research",         write_research_md,          script, root, dry_run)
    _safe_write("titles",           write_titles_md,             script, root, dry_run)
    _safe_write("thumbnail_ideas",  write_thumbnail_ideas_md,    script, root, dry_run)
    _safe_write("script",           write_script_md,             script, root, dry_run)
    _safe_write("voice_check",      write_voice_check_md,
                root, voicevox_ok, speed, audio_durations, dry_run)
    _safe_write("bgm_check",        write_bgm_check_md,
                root, str(bgm_path) if bgm_path else None, bgm_exists, dry_run)
    _safe_write("prompts",          write_ai_image_prompts_md,   script, root, dry_run)
    _safe_write("description",      write_description_md,        script, root, dry_run)
    _safe_write("fixed_comment",    write_fixed_comment_md,      script, root, dry_run)
    _safe_write("rights_check",     write_rights_check_md,       script, root, dry_run)
    _safe_write("video_check",      write_video_check_md,
                root, video_exists, str(bgm_path) if bgm_path else None,
                bgm_exists, has_narration, video_error, dry_run)
    _safe_write("upload_checklist", write_upload_checklist_md,   script, root, dry_run)

    if has_narration and narration_wav.exists():
        file_map["narration"] = str(narration_wav)
    if srt_path and os.path.exists(srt_path):
        file_map["subtitle"] = srt_path
    if video_exists:
        file_map["video"] = str(video_path)

    print(f"  {len(file_map)} ファイル生成完了")

    # ── Step 9: summary.md 生成 ───────────────────────────────────────────
    _step(9, TOTAL_STEPS, "summary.md を生成中...")
    from modules.output_packager import write_summary_md
    try:
        summary_path = write_summary_md(
            root=root, theme=theme, script=script, speed=speed,
            bgm_path=str(bgm_path) if bgm_path else None,
            bgm_exists=bgm_exists,
            audio_durations=audio_durations,
            voicevox_ok=voicevox_ok,
            video_exists=video_exists, file_map=file_map,
            dry_run=dry_run,
        )
        log.add_file("summary", str(summary_path))
        print(f"  → summary.md")
        # test_mode 警告を summary.md に追記
        if test_mode and not dry_run:
            with open(summary_path, "a", encoding="utf-8") as _f:
                _f.write(
                    "\n\n---\n\n"
                    "## ⛔ TEST ONLY — 投稿不可\n\n"
                    "このファイルは `--test-mode` で生成されました。\n"
                    "VOICEVOX 未接続のため、音声はサイン波（技術検証用）です。\n"
                    "**このまま YouTube に投稿しないでください。**\n\n"
                    "本番投稿用 MP4 を生成するには：\n"
                    f"```\npython create_video.py --channel {channel} "
                    f"--theme \"{theme}\" --voicevox-speed {speed}\n```\n"
                )
    except Exception as e:
        _err("summary.md の生成に失敗しました", str(e),
             "output_packager.py を確認してください")
        log.add_error(f"summary 生成失敗: {e}")

    # ── Step 10: ffprobe 検証 ─────────────────────────────────────────────
    _step(10, TOTAL_STEPS, "MP4 を ffprobe で検証中...")

    ffprobe_result = None
    if video_exists:
        ffprobe_result = _run_ffprobe(str(video_path.resolve()))
        log.set(ffprobe=ffprobe_result)

        if ffprobe_result.get("ok"):
            dur   = ffprobe_result["duration_sec"]
            res   = f"{ffprobe_result['width']}×{ffprobe_result['height']}"
            fps_v = ffprobe_result["fps"]
            vcodec = ffprobe_result["video_codec"]
            acodec = ffprobe_result["audio_codec"]
            sr    = ffprobe_result["sample_rate"]
            ch    = ffprobe_result["channels"]
            print(f"  [OK] {res} / {fps_v}fps / {vcodec} / {acodec} {sr}Hz {ch}ch")
            print(f"       再生時間: {_fmt_sec(dur)} ({dur:.1f}秒)")

            # 本番 PASS 判定
            dur_ok    = target_min <= dur <= target_max
            res_ok    = (ffprobe_result["width"] == profile["video_width"] and
                         ffprobe_result["height"] == profile["video_height"])
            fps_ok    = abs(fps_v - profile["video_fps"]) < 0.5
            codec_ok  = vcodec == "h264" and acodec == "aac"
            sr_ok     = str(sr) == "44100"
            ch_ok     = int(ch) == 2

            production_pass = (
                voicevox_ok and bgm_exists and not test_mode
                and dur_ok and res_ok and fps_ok and codec_ok and sr_ok and ch_ok
            )
            log.set(production_pass=production_pass)

            if not dur_ok:
                print(f"  [FAIL] 尺 {_fmt_sec(dur)} は目標範囲外（{_fmt_sec(target_min)}〜{_fmt_sec(target_max)}）")
            if not (res_ok and fps_ok and codec_ok):
                print(f"  [FAIL] スペック不適合: res={res} fps={fps_v} vcodec={vcodec} acodec={acodec}")
        else:
            print(f"  [FAIL] ffprobe エラー: {ffprobe_result.get('error', 'unknown')}")
            log.add_error(f"ffprobe 失敗: {ffprobe_result.get('error')}")
    else:
        print("  動画が生成されていないため、ffprobe スキップ")

    # ── Step 11: 実行ログ保存 ─────────────────────────────────────────────
    _step(11, TOTAL_STEPS, "実行ログを保存中...")
    log.set(status="success" if not log.data["errors"] else "completed_with_warnings")
    log_path = log.save()

    # ── 完了メッセージ ────────────────────────────────────────────────────
    rel_root = root.relative_to(BASE_DIR)
    print("\n" + "=" * 60)
    if test_mode and not dry_run:
        print("⚠️  [TEST ONLY] 動画生成パッケージを作成しました。")
        print("   音声はサイン波です。このまま投稿しないでください。")
    elif not log.data["errors"]:
        print("✅ 動画生成パッケージを作成しました。")
    else:
        print("⚠️  動画生成パッケージを作成しました（一部エラーあり）。")

    print(f"テーマ      : {theme}")
    print(f"チャンネル  : {channel} / {profile['name']}")
    print(f"出力フォルダ: {rel_root}")
    print(f"システム    : 動画自動生成システム {SYSTEM_VERSION}")

    if ffprobe_result and ffprobe_result.get("ok"):
        dur = ffprobe_result["duration_sec"]
        print(f"再生時間    : {_fmt_sec(dur)} ({dur:.1f}秒)")
        production_pass = log.data.get("production_pass", False)
        print(f"本番PASS    : {'✅ YES' if production_pass else '❌ NO（未完了項目あり）'}")

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
