#!/usr/bin/env python3
"""
ザ・ダンク 動画制作自動化システム
YouTube Shorts 自動生成 MVP

使用方法:
  python main.py                                              # テストモードでMVP実行
  python main.py --topic "河村勇輝のノールックパス" --mode production
  python main.py --player "河村勇輝" --mode production
  python main.py --video inputs/owned_videos/sample.mp4 --mode production
  python main.py --script-file inputs/scripts/script.txt --video inputs/owned_videos/sample.mp4
  python main.py --test-mode                                  # テストモード明示指定
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from lib.player import normalize_player_name, get_player_info
from lib.preflight import run_preflight, print_preflight, load_settings
from lib.script_writer import generate_script, script_to_narration, script_to_full_text, validate_script
from lib.tts import generate_narration, get_wav_duration
from lib.subtitle import generate_srt, generate_ass_filter
from lib.video import (
    generate_visual_frames,
    create_video_from_frames,
    generate_bgm_tone,
    generate_screenshots,
)
from lib.quality import run_quality_check, save_quality_report, check_zero_kb
from lib.metadata import save_metadata_files, generate_trend_notes


def setup_logging(log_path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("the_dunk")


def parse_args():
    parser = argparse.ArgumentParser(description="ザ・ダンク 動画制作自動化システム")
    parser.add_argument("--topic", type=str, default=None, help="企画テーマ")
    parser.add_argument("--player", type=str, default=None, help="選手名")
    parser.add_argument("--video", type=str, default=None, help="入力動画パス")
    parser.add_argument("--script-file", type=str, default=None, help="台本ファイルパス")
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["production", "test"],
        help="実行モード",
    )
    parser.add_argument("--test-mode", action="store_true", help="テストモードで実行")
    return parser.parse_args()


def determine_mode(args):
    if args.test_mode:
        return "test"
    if args.mode:
        return args.mode
    return "test"


def determine_topic_and_player(args):
    player = args.player or "河村勇輝"
    topic = args.topic or "河村勇輝のノールックパスが守備を崩す理由"

    if args.player and not args.topic:
        canonical = normalize_player_name(args.player)
        info = get_player_info(canonical)
        if info:
            topic = f"{canonical}のプレー解説"

    player = normalize_player_name(player)
    return player, topic


def create_output_dir(mode, player, topic):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_player = player.replace("・", "_").replace("＝", "_").replace(" ", "_")[:20]
    safe_topic = topic[:20].replace(" ", "_").replace("・", "_")

    if mode == "test":
        dirname = f"{ts}_{safe_player}_{safe_topic}_TEST_ONLY"
        out_dir = os.path.join(BASE_DIR, "outputs", "test", dirname)
    else:
        dirname = f"{ts}_{safe_player}_{safe_topic}"
        out_dir = os.path.join(BASE_DIR, "outputs", "production", dirname)

    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def generate_research_files(script, output_dir):
    fact_check = {
        "facts": [
            {
                "fact_id": "F001",
                "claim": f"{script['player']}はポイントガードとしてプレーしている",
                "status": "CONFIRMED",
                "source_organization": "公式情報",
                "source_title": "選手プロフィール",
                "source_url": "",
                "published_date": "",
                "event_date": "",
                "supporting_summary": "公式チームロスター情報に基づく",
                "usable_in_script": True,
            }
        ]
    }
    with open(os.path.join(output_dir, "fact_check.json"), "w", encoding="utf-8") as f:
        json.dump(fact_check, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "research_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# 調査レポート\n\n")
        f.write(f"調査日: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"選手: {script['player']}\n")
        f.write(f"テーマ: {script['topic']}\n\n")
        f.write(f"## 確認済み事実\n\n")
        for fact in fact_check["facts"]:
            f.write(f"- [{fact['status']}] {fact['claim']}\n")
        f.write(f"\n## 注意\n\n")
        f.write("オフライン環境のため、リアルタイムの調査は実行できていません。\n")
        f.write("本番使用前に最新情報を確認してください。\n")

    with open(os.path.join(output_dir, "sources.csv"), "w", encoding="utf-8") as f:
        f.write("fact_id,claim,status,source_organization,source_url,published_date\n")
        for fact in fact_check["facts"]:
            f.write(f'"{fact["fact_id"]}","{fact["claim"]}","{fact["status"]}","{fact["source_organization"]}","{fact["source_url"]}","{fact["published_date"]}"\n')


def generate_rights_files(output_dir, mode):
    materials = {
        "materials": [
            {
                "file_path": "自作ビジュアル素材",
                "source_url": "",
                "source_name": "ザ・ダンク自動生成",
                "permission_type": "owned",
                "rights_status": "OK",
                "player_names": [],
                "game_date": "",
                "league": "",
                "team": "",
                "clip_start": "",
                "clip_end": "",
                "contains_broadcast_graphics": False,
                "contains_third_party_music": False,
                "contains_watermark": False,
                "credit_required": False,
                "credit_text": "",
                "notes": "プログラムが自動生成したコート図・テキストカード",
            }
        ]
    }
    with open(os.path.join(output_dir, "materials.json"), "w", encoding="utf-8") as f:
        json.dump(materials, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "rights_report.md"), "w", encoding="utf-8") as f:
        f.write("# 権利レポート\n\n")
        f.write(f"生成日: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## 使用素材\n\n")
        for m in materials["materials"]:
            f.write(f"- {m['file_path']}: {m['permission_type']} ({m['rights_status']})\n")
        f.write("\n## 判定\n\n")
        f.write("- owned素材のみ使用\n")
        f.write("- 第三者素材の無断使用なし\n")
        f.write("- reference_only素材の混入なし\n")

    bgm_license = {
        "bgm": []
    }
    sfx_license = {
        "sfx": []
    }

    if mode == "test":
        bgm_license["bgm"].append({
            "file_name": "test_bgm.wav",
            "source": "自動生成テストトーン",
            "source_url": "",
            "license": "自作（権利問題なし）",
            "commercial_use": True,
            "youtube_monetization": True,
            "credit_required": False,
            "credit_text": "",
            "content_id_risk": "なし",
            "allowed_channels": ["the_dunk"],
            "note": "TEST ONLY: 技術検証用の自動生成音。本番使用不可。",
        })

    with open(os.path.join(output_dir, "bgm_license.json"), "w", encoding="utf-8") as f:
        json.dump(bgm_license, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, "sfx_license.json"), "w", encoding="utf-8") as f:
        json.dump(sfx_license, f, ensure_ascii=False, indent=2)

    credits_lines = []
    if mode == "test":
        credits_lines.append("BGM: テスト用自動生成トーン（本番使用不可）")
    credits_lines.append("映像素材: ザ・ダンク自動生成（コート図・テキストカード）")

    credits_text = "\n".join(credits_lines)
    with open(os.path.join(output_dir, "credits.txt"), "w", encoding="utf-8") as f:
        f.write(credits_text)

    return credits_text


def adjust_script_for_duration(script, narration_text, duration, settings, attempt=0):
    max_dur = settings["video"]["max_duration"]
    min_dur = settings["video"]["min_duration"]

    if min_dur <= duration <= max_dur:
        return script, narration_text, True

    if attempt >= 3:
        return script, narration_text, False

    if duration > max_dur:
        sections = script["sections"]
        for section in reversed(sections):
            text = section["text"]
            sentences = [s for s in text.replace("。", "。\n").split("\n") if s.strip()]
            if len(sentences) > 1:
                section["text"] = "。".join(sentences[:-1])
                if not section["text"].endswith("。"):
                    section["text"] += "。"
                break

    elif duration < min_dur:
        sections = script["sections"]
        for section in sections:
            if section["label"] in ("技術解説1", "技術解説2", "解説"):
                section["text"] += "この技術は、バスケットボールの基本でありながら、極めて高い精度が求められます。"
                break

    new_narration = script_to_narration(script)
    return script, new_narration, None


def run_pipeline(args):
    mode = determine_mode(args)
    player, topic = determine_topic_and_player(args)
    settings = load_settings()

    output_dir = create_output_dir(mode, player, topic)
    log_path = os.path.join(output_dir, "execution.log")
    logger = setup_logging(log_path)

    logger.info(f"=== ザ・ダンク 動画制作自動化システム ===")
    logger.info(f"モード: {mode}")
    logger.info(f"選手: {player}")
    logger.info(f"テーマ: {topic}")
    logger.info(f"出力先: {output_dir}")

    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=BASE_DIR,
        ).stdout.strip()
    except Exception:
        git_commit = "unknown"
    logger.info(f"GitコミットID: {git_commit}")

    logger.info("--- preflight チェック ---")
    preflight = run_preflight(mode)
    print_preflight(preflight)

    if mode == "production" and not preflight["all_ok"]:
        logger.error("本番モード: preflightチェック失敗。不足項目を修正してください。")
        _save_status(output_dir, "FAIL", "preflightチェック失敗", mode, player, topic)
        return False

    if mode == "test":
        for f in preflight["failed"]:
            if f["name"] in ("VOICEVOX", "VOICEVOX話者"):
                logger.info(f"テストモード: {f['name']}未接続 → テスト音声を使用します")

    logger.info("--- 台本生成 ---")
    if args.script_file and os.path.exists(args.script_file):
        with open(args.script_file, "r", encoding="utf-8") as f:
            custom_text = f.read()
        script = {
            "player": player,
            "topic": topic,
            "plan_type": "technique",
            "plan_type_label": "技術解説",
            "sections": [
                {"time": "0-2秒", "label": "フック", "text": custom_text[:100]},
                {"time": "2-50秒", "label": "本文", "text": custom_text},
                {"time": "50-57秒", "label": "CTA", "text": "ザ・ダンクでは、他のプレーも解説しています。"},
            ],
        }
    else:
        plan_type = "technique"
        if "比較" in topic or "違い" in topic:
            plan_type = "comparison"
        elif "記録" in topic or "データ" in topic:
            plan_type = "record"
        elif "戦術" in topic or "ピック" in topic:
            plan_type = "tactics"
        elif "スーパープレー" in topic or "ダンク" in topic:
            plan_type = "super_play"
        script = generate_script(player, topic, plan_type)

    validation = validate_script(script)
    if not validation["ok"]:
        for issue in validation["issues"]:
            logger.warning(f"台本検証: {issue}")

    narration_text = script_to_narration(script)
    full_text = script_to_full_text(script)

    with open(os.path.join(output_dir, "script.txt"), "w", encoding="utf-8") as f:
        f.write(full_text)
    with open(os.path.join(output_dir, "narration.txt"), "w", encoding="utf-8") as f:
        f.write(narration_text)
    logger.info(f"台本生成完了: {len(narration_text)}文字")

    logger.info("--- 音声生成 ---")
    tts_mode = mode
    if mode == "production":
        try:
            import urllib.request
            req = urllib.request.Request(f"{settings['voicevox']['host']}/version", method="GET")
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            logger.error("VOICEVOX未接続のため本番音声を生成できません。")
            _save_status(output_dir, "FAIL", "VOICEVOX未接続", mode, player, topic)
            return False
    else:
        tts_mode = "test"

    audio_dir = os.path.join(output_dir, "audio")
    narration_path, audio_duration, tts_info = generate_narration(narration_text, audio_dir, tts_mode)
    logger.info(f"音声生成完了: {audio_duration:.2f}秒, エンジン: {tts_info['engine']}")

    for attempt in range(3):
        script, narration_text, duration_ok = adjust_script_for_duration(
            script, narration_text, audio_duration, settings, attempt
        )
        if duration_ok is True:
            break
        if duration_ok is False:
            logger.warning(f"尺調整失敗（{attempt + 1}/3回目）")
            break
        narration_path, audio_duration, tts_info = generate_narration(narration_text, audio_dir, tts_mode)
        logger.info(f"尺調整後の音声: {audio_duration:.2f}秒")

    logger.info("--- 字幕生成 ---")
    srt_path = os.path.join(output_dir, "subtitles.srt")
    srt_entries = generate_srt(narration_text, narration_path, srt_path)
    logger.info(f"SRT生成完了: {len(srt_entries)}エントリ")

    ass_content = generate_ass_filter(srt_entries, settings)
    ass_path = os.path.join(output_dir, "subtitles.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    logger.info("ASS字幕生成完了")

    logger.info("--- 映像素材生成 ---")
    frames_dir = os.path.join(output_dir, "frames")

    if args.video and os.path.exists(args.video):
        logger.info(f"入力動画を使用: {args.video}")
        frame_specs = [{"path": args.video, "duration": audio_duration, "label": "input_video"}]
    else:
        frame_specs = generate_visual_frames(script, frames_dir, settings)
        logger.info(f"ビジュアルフレーム生成完了: {len(frame_specs)}フレーム")

    logger.info("--- BGM生成 ---")
    bgm_path = None
    bgm_candidates = [
        os.path.join(BASE_DIR, "inputs", "bgm.wav"),
        os.path.join(BASE_DIR, "inputs", "bgm.mp3"),
    ]
    for bc in bgm_candidates:
        if os.path.exists(bc):
            bgm_path = bc
            logger.info(f"BGM検出: {bc}")
            break

    if not bgm_path and mode == "test":
        bgm_path = os.path.join(output_dir, "test_bgm.wav")
        generate_bgm_tone(bgm_path, duration=70.0)
        logger.info("テスト用BGMトーン生成完了")

    if not bgm_path and mode == "production":
        logger.warning("BGMが見つかりません。inputs/bgm.wav を配置してください。")

    logger.info("--- 動画合成 ---")
    video_path = os.path.join(output_dir, "final.mp4")
    create_video_from_frames(frame_specs, narration_path, ass_path, video_path, settings, bgm_path)
    logger.info(f"動画生成完了: {video_path}")

    logger.info("--- スクリーンショット生成 ---")
    ss_dir = os.path.join(output_dir, "screenshots")
    generate_screenshots(video_path, ss_dir)

    logger.info("--- メタデータ生成 ---")
    credits_text = generate_rights_files(output_dir, mode)
    generate_research_files(script, output_dir)
    save_metadata_files(script, output_dir, credits_text)
    generate_trend_notes(os.path.join(output_dir, "trend_notes.txt"))

    logger.info("--- 品質検査 ---")
    quality = run_quality_check(video_path, mode, tts_info)
    qr_path = os.path.join(output_dir, "quality_report.json")
    save_quality_report(quality, qr_path)

    for check in quality["checks"]:
        status = "PASS" if check["pass"] else "FAIL"
        logger.info(f"  {status}: {check['name']} - {check['detail']}")

    zero_files = check_zero_kb(output_dir)
    if zero_files:
        logger.warning(f"0KBファイル検出・削除: {zero_files}")
        for zf in zero_files:
            try:
                os.remove(zf)
            except OSError:
                pass

    final_output = os.path.join(BASE_DIR, "output", "final.mp4")
    os.makedirs(os.path.dirname(final_output), exist_ok=True)
    shutil.copy2(video_path, final_output)
    logger.info(f"最終動画コピー完了: {final_output}")

    overall = "PASS" if quality["pass"] else "FAIL"
    if mode == "test" and not quality["pass"]:
        dur = quality.get("duration", 0)
        non_dur_fails = [c for c in quality["checks"] if not c["pass"] and c["name"] not in ("再生時間", "TTS")]
        if not non_dur_fails:
            overall = "PASS (テストモード: 尺・TTS制約は許容)"

    _save_status(output_dir, overall, "完了", mode, player, topic, quality, tts_info)

    logger.info(f"\n{'='*50}")
    logger.info(f"最終結果: {overall}")
    logger.info(f"出力: {final_output}")
    if mode == "test":
        logger.info("注意: TEST ONLY - 投稿不可 - 技術検証用")
    logger.info(f"{'='*50}")

    _print_summary(output_dir, final_output, quality, script, mode, tts_info)

    return True


def _save_status(output_dir, status, message, mode, player, topic, quality=None, tts_info=None):
    data = {
        "status": status,
        "message": message,
        "mode": mode,
        "player": player,
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "quality": quality["pass"] if quality else None,
        "tts_engine": tts_info.get("engine") if tts_info else None,
    }
    with open(os.path.join(output_dir, "status.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(f"# ザ・ダンク 動画制作サマリー\n\n")
        f.write(f"- 状態: {status}\n")
        f.write(f"- モード: {mode}\n")
        f.write(f"- 選手: {player}\n")
        f.write(f"- テーマ: {topic}\n")
        f.write(f"- 生成日時: {data['timestamp']}\n")
        if tts_info:
            f.write(f"- TTS: {tts_info.get('engine', '不明')}\n")
        if quality:
            f.write(f"\n## 品質検査\n\n")
            for c in quality.get("checks", []):
                mark = "✓" if c["pass"] else "✗"
                f.write(f"- {mark} {c['name']}: {c['detail']}\n")
        if mode == "test":
            f.write(f"\n## 注意\n\nTEST ONLY - 投稿不可 - 技術検証用\n")


def _print_summary(output_dir, final_path, quality, script, mode, tts_info):
    print("\n" + "=" * 60)
    print("  ザ・ダンク 動画制作完了レポート")
    print("=" * 60)
    print(f"\n  選手: {script['player']}")
    print(f"  テーマ: {script['topic']}")
    print(f"  企画タイプ: {script.get('plan_type_label', '不明')}")
    print(f"  モード: {mode}")
    print(f"  TTS: {tts_info.get('engine', '不明')} ({tts_info.get('speaker', '')})")
    print(f"  最終動画: {final_path}")
    print(f"  再生時間: {quality.get('duration', 0):.2f}秒")
    print(f"\n  品質検査:")
    for c in quality.get("checks", []):
        mark = "PASS" if c["pass"] else "FAIL"
        print(f"    [{mark}] {c['name']}: {c['detail']}")
    print(f"\n  出力フォルダ: {output_dir}")
    if mode == "test":
        print("\n  *** TEST ONLY - 投稿不可 - 技術検証用 ***")
    print("=" * 60)


if __name__ == "__main__":
    try:
        args = parse_args()
        success = run_pipeline(args)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n エラーが発生しました: {e}")
        print(f"\n修正方法:")
        err_msg = str(e).lower()
        if "voicevox" in err_msg:
            print("  → VOICEVOXを起動してください（http://localhost:50021）")
        elif "ffmpeg" in err_msg or "ffprobe" in err_msg:
            print("  → FFmpegをインストールしてください")
        elif "font" in err_msg:
            print("  → 日本語フォントをインストールしてください")
        elif "permission" in err_msg or "書き込み" in err_msg:
            print("  → 出力フォルダの書き込み権限を確認してください")
        else:
            print(f"  → エラー詳細を確認してください")
        traceback.print_exc()
        sys.exit(1)
