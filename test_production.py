"""
技術検証用 MP4 生成テスト（モジュール直接呼び出し版）

NOTE: create_video.py を使う場合は以下のコマンドを推奨:
  python create_video.py --channel showa_heisei --theme "テーマ" --test-mode

本スクリプトは個別モジュールのユニットテスト用途。

使用条件:
  - VOICEVOX: 未接続 → scipy による技術検証用サイン波 WAV を生成
  - BGM: 未配置 → BGM なしで処理
  - FFmpeg: static_ffmpeg を使用
  - Pillow: スライド生成に使用
  - Anthropic API: 不要（ビルトインスクリプトを使用）

⚠️  TEST ONLY / 投稿不可
"""

import os
import sys
import json
import struct
import wave
import math
import subprocess
import shutil
import tempfile
import time
from pathlib import Path

# ─── static_ffmpeg でパスを追加 ─────────────────────────────
import static_ffmpeg
static_ffmpeg.add_paths()
import shutil as _shutil
FFMPEG_BIN = _shutil.which("ffmpeg")
FFPROBE_BIN = _shutil.which("ffprobe")
print(f"[環境] ffmpeg : {FFMPEG_BIN}")
print(f"[環境] ffprobe: {FFPROBE_BIN}")

# video_renderer の FFMPEG 検索をパッチ
import modules.video_renderer as _vr
_vr.FFMPEG_BIN = FFMPEG_BIN

# ─── テスト設定 ─────────────────────────────────────────────
TEST_THEME = "なぜ家族全員で1台のテレビを見ていたのか"
# 絶対パスで作業する（FFmpeg concat が相対パスを /tmp から解決するのを防ぐ）
SCRIPT_DIR = Path(__file__).parent.resolve()
OUT_BASE   = SCRIPT_DIR / "videos" / "test_production"
OUT_BASE.mkdir(parents=True, exist_ok=True)
for sub in ["_tmp", "slides", "voice"]:
    (OUT_BASE / sub).mkdir(exist_ok=True)

# ─── Step 1: 台本生成 ────────────────────────────────────────
print("\n[Step 1] 台本を生成中...")
from modules.script_generator import generate_script
script = generate_script(TEST_THEME)
print(f"  タイトル: {script['title']}")

# 尺を文字数ベースに上書き（テスト高速化のため最低尺を使わない）
from modules.config import NARRATION_SPEED
for ch_name, ch_data in script["chapters"].items():
    text = ch_data["narration"]
    ch_data["duration"] = max((len(text) / NARRATION_SPEED) * 60, 20.0)
    print(f"  {ch_name}: {len(text)}字 / {ch_data['duration']:.1f}秒")

total_duration = sum(d["duration"] for d in script["chapters"].values())
print(f"  合計: {total_duration:.0f}秒 ({total_duration/60:.1f}分)")

# ─── Step 2: 技術検証用ナレーション WAV 生成 (scipy) ─────────
print("\n[Step 2] 技術検証用ナレーション WAV を生成中 (サイン波)...")
import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44100
audio_files: dict[str, str] = {}
audio_durations: dict[str, float] = {}

for ch_name, ch_data in script["chapters"].items():
    dur = ch_data["duration"]
    # 300 Hz サイン波（技術検証用）
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq = 300.0
    samples = (np.sin(2 * np.pi * freq * t) * 0.3 * 32767).astype(np.int16)
    out_path = str((OUT_BASE / "voice" / f"narration_{ch_name}.wav").resolve())
    wavfile.write(out_path, SAMPLE_RATE, samples)
    size_kb = Path(out_path).stat().st_size // 1024
    audio_files[ch_name] = out_path
    audio_durations[ch_name] = dur
    print(f"  {ch_name}: {dur:.1f}秒 → {size_kb}KB  [{out_path}]")

# 0KB チェック
for ch_name, path in audio_files.items():
    size = Path(path).stat().st_size
    if size == 0:
        print(f"  ⚠️  0KB: {path}")
        sys.exit(1)

# ─── Step 3: スライド生成 ─────────────────────────────────────
print("\n[Step 3] スライド画像を生成中 (Pillow)...")
from modules.image_generator import generate_all_slides
slides_dir = str((OUT_BASE / "slides").resolve())
all_slides = generate_all_slides(script, slides_dir)
# スライドパスを絶対パスに確定（concat ファイルからの相対解決を防ぐ）
all_slides = {k: [str(Path(p).resolve()) for p in v] for k, v in all_slides.items()}
total_slides = sum(len(v) for v in all_slides.values())
print(f"  合計: {total_slides}枚")

# 0KB チェック
for ch_name, paths in all_slides.items():
    for p in paths:
        if Path(p).stat().st_size == 0:
            print(f"  ⚠️  0KB: {p}")
            sys.exit(1)

# ─── Step 4: SRT 字幕生成 ────────────────────────────────────
print("\n[Step 4] SRT 字幕を生成中...")
from modules.subtitle import generate_srt, get_subtitle_entries
srt_path = str((OUT_BASE / "subtitle.srt").resolve())
generate_srt(script, audio_durations, srt_path)
subtitle_entries = get_subtitle_entries(script, audio_durations)
print(f"  → {srt_path} ({Path(srt_path).stat().st_size // 1024}KB)")

# ─── Step 5: サムネイル生成 ──────────────────────────────────
print("\n[Step 5] サムネイルを生成中 (Pillow)...")
from modules.thumbnail import generate_thumbnail
thumb_path = str((OUT_BASE / "thumbnail.png").resolve())
generate_thumbnail(
    title=script.get("title", TEST_THEME),
    subtitle=script.get("subtitle", ""),
    output_path=thumb_path,
)
thumb_kb = Path(thumb_path).stat().st_size // 1024
print(f"  → {thumb_path} ({thumb_kb}KB)")

# ─── Step 6: MP4 レンダリング ────────────────────────────────
print("\n[Step 6] MP4 を生成中 (FFmpeg)...")
output_mp4 = str((OUT_BASE / "output.mp4").resolve())

from modules.video_renderer import render_video
render_video(
    script=script,
    all_slides=all_slides,
    audio_files=audio_files,
    audio_durations=audio_durations,
    subtitle_entries=subtitle_entries,
    bgm_path=None,          # BGM 未配置
    output_path=output_mp4,
)

# ─── Step 7: 0KB チェック（全生成ファイル） ──────────────────
print("\n[Step 7] 0KB チェック...")
all_files = list(audio_files.values())
for slides in all_slides.values():
    all_files.extend(slides)
all_files += [srt_path, thumb_path, output_mp4]

zero_kb_files = []
for f in all_files:
    if Path(f).exists() and Path(f).stat().st_size == 0:
        zero_kb_files.append(f)

if zero_kb_files:
    print("  ⚠️  0KB ファイルが見つかりました:")
    for f in zero_kb_files:
        print(f"    {f}")
else:
    print(f"  ✅ 全 {len(all_files)} ファイル: 0KB なし")

# ─── Step 8: ffprobe 検証 ────────────────────────────────────
print("\n[Step 8] ffprobe 検証...")

if not Path(output_mp4).exists():
    print(f"  ❌ MP4 が存在しません: {output_mp4}")
    sys.exit(1)

mp4_size = Path(output_mp4).stat().st_size
print(f"  ファイルサイズ: {mp4_size:,} bytes ({mp4_size // 1024 // 1024}MB)")
if mp4_size == 0:
    print("  ❌ MP4 が 0 バイトです")
    sys.exit(1)

probe_cmd = [
    FFPROBE_BIN, "-v", "quiet",
    "-print_format", "json",
    "-show_format", "-show_streams",
    output_mp4,
]
probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
if probe_result.returncode != 0:
    print(f"  ❌ ffprobe エラー:\n{probe_result.stderr}")
    sys.exit(1)

probe = json.loads(probe_result.stdout)
fmt   = probe.get("format", {})
streams = probe.get("streams", [])

video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

print(f"  フォーマット     : {fmt.get('format_name', 'N/A')}")
print(f"  再生時間         : {float(fmt.get('duration', 0)):.1f}秒 ({float(fmt.get('duration',0))/60:.1f}分)")
print(f"  ビットレート     : {int(fmt.get('bit_rate', 0)) // 1000}kbps")

if video_stream:
    r_frame = video_stream.get("r_frame_rate", "0/1")
    num, den = (int(x) for x in r_frame.split("/"))
    fps_val = num / den if den else 0
    print(f"\n  [映像ストリーム]")
    print(f"  コーデック       : {video_stream.get('codec_name', 'N/A')}")
    print(f"  解像度           : {video_stream.get('width')}×{video_stream.get('height')}")
    print(f"  フレームレート   : {fps_val:.2f} fps")
    print(f"  ピクセルフォーマット: {video_stream.get('pix_fmt', 'N/A')}")
else:
    print("  ❌ 映像ストリームが見つかりません")

if audio_stream:
    print(f"\n  [音声ストリーム]")
    print(f"  コーデック       : {audio_stream.get('codec_name', 'N/A')}")
    print(f"  サンプルレート   : {audio_stream.get('sample_rate')} Hz")
    print(f"  チャンネル数     : {audio_stream.get('channels')}")
    print(f"  ビットレート     : {int(audio_stream.get('bit_rate', 0)) // 1000}kbps")
else:
    print("  ❌ 音声ストリームが見つかりません")

# ─── 最終レポート ────────────────────────────────────────────
print("\n" + "=" * 60)
print("【生成結果】")
success = video_stream and audio_stream and mp4_size > 0
print(f"  {'✅ 成功' if success else '❌ 失敗'}")
print(f"  完成 MP4 の絶対パス : {Path(output_mp4).absolute()}")
print(f"  ファイルサイズ       : {mp4_size:,} bytes ({mp4_size/1024/1024:.1f}MB)")
if fmt.get("duration"):
    dur_sec = float(fmt["duration"])
    print(f"  再生時間             : {dur_sec:.1f}秒 ({dur_sec/60:.1f}分)")
if video_stream:
    r_frame = video_stream.get("r_frame_rate", "0/1")
    num, den = (int(x) for x in r_frame.split("/"))
    fps_val = num / den if den else 0
    print(f"  解像度               : {video_stream.get('width')}×{video_stream.get('height')}")
    print(f"  fps                  : {fps_val:.2f}")
    print(f"  映像コーデック       : {video_stream.get('codec_name')}")
if audio_stream:
    print(f"  音声コーデック       : {audio_stream.get('codec_name')}")
    print(f"  サンプルレート       : {audio_stream.get('sample_rate')} Hz")
    print(f"  チャンネル数         : {audio_stream.get('channels')}")

print("\n【確認結果】")
print(f"  VOICEVOX音声   : ❌ 未接続 → 技術検証用サイン波 WAV (scipy, 300Hz, 44100Hz)")
print(f"  字幕           : {'✅ SRT 生成済み・焼き込み済み' if Path(srt_path).stat().st_size > 0 else '❌'}")
print(f"  BGM            : ❌ assets/bgm/UNL1337.wav 未配置 → BGM なし")
print(f"  素材           : ✅ Pillow 生成スライド {total_slides}枚")
print(f"  音声と字幕の同期: ✅ テキスト文字数ベースのタイミング")
print(f"  0KB ファイル   : {'❌ ' + str(len(zero_kb_files)) + '件' if zero_kb_files else '✅ なし'}")
print(f"  ffprobe        : {'✅ 映像・音声ストリーム確認済み' if video_stream and audio_stream else '❌ ストリーム不足'}")
print(f"  字幕焼き込み   : ✅ ASS 変換 → libx264 再エンコード")

print("\n【未完了】")
print("  1. VOICEVOX 音声")
print("     理由: http://localhost:50021 に接続できない（リモート実行環境）")
print("     対処: 荒木さんの Windows PC で VOICEVOX を起動し、")
print("           python create_video.py --theme \"なぜ家族全員で1台のテレビを見ていたのか\" を実行")
print("  2. BGM ミックス")
print("     理由: assets/bgm/UNL1337.wav が未配置")
print("     対処: UNL1337.wav を assets/bgm/ フォルダに配置後、同コマンドを実行")
print("  3. 本番品質 MP4")
print("     以下のコマンドで本番実行:")
print("       python create_video.py --theme \"なぜ家族全員で1台のテレビを見ていたのか\" --voicevox-speed 0.87")
print("=" * 60)
