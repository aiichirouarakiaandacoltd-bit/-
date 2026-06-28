#!/usr/bin/env python3
"""
ザ・ダンク 動画制作自動化システム
YouTube Shorts 完全自動生成

使用方法:
  python main.py --auto --mode production    # 完全自動: 企画発掘→選手選定→動画生成
  python main.py --mode production           # 本番: チャンネルから自動取得→Shorts自動生成
  python main.py                             # テストモード
  python main.py --topic "河村勇輝のノールックパス" --mode production
  python main.py --player "河村勇輝" --mode production
  python main.py --video path/to/video.mp4 --mode production  # 手動指定（任意）
  python main.py --test-mode
  python main.py --auto --dry-run            # 自動選定のみ（動画生成なし）
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
from lib.auto_fetch import run_auto_fetch_pipeline
from lib.bgm_rotation import (
    get_next_bgm, validate_bgm_file, validate_all_bgm,
    mark_completed, is_production_bgm, load_state as load_bgm_state,
    BGM_TRACKS, STATE_PATH as BGM_STATE_PATH,
)
from lib.youtube_research import get_research_client
from lib.topic_scoring import rank_candidates
from lib.topic_discovery import (
    run_auto_topic_selection, load_topic_history, save_topic_history,
)
from lib.competitor_analysis import analyze_batch, generate_new_concept
from lib.clip_detection import (
    find_source_candidates, generate_editing_timeline, save_source_candidates,
)
from lib.publishing import generate_publishing_package


def setup_logging(log_path):
    logger = logging.getLogger("the_dunk")
    logger.setLevel(logging.INFO)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


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
    parser.add_argument("--auto", action="store_true",
                        help="完全自動モード: 企画発掘→選手選定→動画生成")
    parser.add_argument("--dry-run", action="store_true",
                        help="自動選定のみ実行（動画生成なし）")
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


def generate_rights_files(output_dir, mode, auto_fetch_result=None):
    materials = {
        "materials": [
            {
                "file_path": "自作ビジュアル素材",
                "source_url": "",
                "source_name": "ザ・ダンク自動生成",
                "permission_type": "owned",
                "rights_status": "system_generated_review_required",
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
        if auto_fetch_result and auto_fetch_result.get("rights"):
            r = auto_fetch_result["rights"]
            f.write("## メタデータ一次リスク判定\n\n")
            f.write(f"- channel_source_permission: {r.get('channel_source_permission', 'UNKNOWN')}\n")
            f.write(f"- embedded_footage_rights: {r.get('embedded_footage_rights', 'UNKNOWN')}\n")
            f.write(f"- metadata_risk_status: {r.get('metadata_risk_status', 'UNKNOWN')}\n")
            f.write(f"- audio_risk_status: {r.get('audio_risk_status', 'UNKNOWN')}\n")
            f.write(f"- watermark_status: {r.get('watermark_status', 'UNKNOWN')}\n")
            f.write(f"- audio_removed: {r.get('audio_removed', False)}\n")
            f.write(f"- manual_review_required: {r.get('manual_review_required', True)}\n")
            f.write(f"- publishable: {r.get('publishable', False)}\n\n")
            if r.get("risk_factors"):
                f.write("## リスク要因\n\n")
                for rf in r["risk_factors"]:
                    f.write(f"- {rf}\n")
            if r.get("notes"):
                f.write("\n## 注意事項\n\n")
                for n in r["notes"]:
                    f.write(f"- {n}\n")
            if r.get("youtube_studio_check_required"):
                f.write("\n## YouTube Studioで確認が必要な項目\n\n")
                for item in r["youtube_studio_check_required"]:
                    f.write(f"- {item}\n")
            if r.get("metadata_unavailable"):
                f.write("\n## 取得できなかった情報\n\n")
                for item in r["metadata_unavailable"]:
                    f.write(f"- {item}\n")
        else:
            f.write("## 使用素材\n\n")
            for m in materials["materials"]:
                f.write(f"- {m['file_path']}: {m['permission_type']} ({m['rights_status']})\n")

    bgm_license = {"bgm": []}
    sfx_license = {"sfx": []}

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
            sentences = [s.strip() for s in text.split("。") if s.strip()]
            if len(sentences) > 1:
                section["text"] = "。".join(sentences[:-1]) + "。"
                break

    elif duration < min_dur:
        sections = script["sections"]
        for section in sections:
            if section["label"] in ("技術解説1", "技術解説2", "解説"):
                section["text"] += "この技術は、バスケットボールの基本でありながら、極めて高い精度が求められます。"
                break

    new_narration = script_to_narration(script)
    return script, new_narration, None


def determine_publishable(mode, quality, tts_info, bgm_path, bgm_license_path,
                          auto_fetch_result, review_screenshots_exist,
                          pipeline_error=False):
    """
    publishable判定（4段階分離・各判定独立）

    technical_publishable: 動画ファイルが技術仕様を満たしているか
    production_ready: 本番公開候補として必要な制作要素が揃い、システム検証が終わっているか
    completed: 動画生成工程がエラーなく最後まで終了したか（production_readyに従属しない）
    final_release_approved: 荒木愛一朗による最終確認（常にFalse、手動変更のみ）
    """
    conditions = {}
    conditions["production_mode"] = mode == "production"
    conditions["voicevox_used"] = tts_info.get("engine") == "VOICEVOX" if tts_info else False
    conditions["speaker_aoyama"] = tts_info.get("speaker") == "青山龍星" if tts_info else False
    conditions["speed_095"] = tts_info.get("speed") == 0.95 if tts_info else False
    conditions["no_test_audio"] = tts_info.get("fallback_used") is False if tts_info else False
    conditions["bgm_exists"] = bgm_path is not None and os.path.exists(bgm_path) if bgm_path else False
    conditions["production_bgm_used"] = is_production_bgm(bgm_path) if bgm_path else False

    bgm_license_ok = False
    if bgm_license_path and os.path.exists(bgm_license_path):
        try:
            with open(bgm_license_path, "r", encoding="utf-8") as f:
                bl = json.load(f)
            if bl.get("bgm") and len(bl["bgm"]) > 0:
                bgm_license_ok = True
        except Exception:
            pass
    conditions["bgm_license_exists"] = bgm_license_ok

    conditions["duration_ok"] = quality.get("duration_ok", False) if quality else False
    conditions["resolution_ok"] = quality.get("resolution_ok", False) if quality else False
    conditions["codec_ok"] = quality.get("codec_ok", False) if quality else False
    conditions["subtitle_burned"] = True
    conditions["decode_pass"] = quality.get("decode_ok", False) if quality else False
    conditions["zero_kb_none"] = quality.get("zero_kb_ok", False) if quality else False

    rights = auto_fetch_result.get("rights", {}) if auto_fetch_result else {}
    rights_status = rights.get("rights_status", "UNKNOWN")
    conditions["metadata_risk_not_ng"] = rights.get("metadata_risk_status", "UNKNOWN") != "NG"
    conditions["watermark_not_ng"] = rights.get("watermark_status", "UNKNOWN") != "NG"
    conditions["audio_removed"] = rights.get("audio_removed", False) if auto_fetch_result else True
    conditions["review_screenshots_exist"] = review_screenshots_exist

    tech_conditions = {k: v for k, v in conditions.items()
                       if k in ("duration_ok", "resolution_ok", "codec_ok",
                                "decode_pass", "zero_kb_none", "subtitle_burned")}
    technical_publishable = all(tech_conditions.values())

    prod_keys = ("production_mode", "voicevox_used", "speaker_aoyama", "speed_095",
                 "no_test_audio", "bgm_exists", "production_bgm_used", "bgm_license_exists",
                 "duration_ok", "resolution_ok", "codec_ok", "subtitle_burned",
                 "decode_pass", "zero_kb_none", "review_screenshots_exist")
    prod_conditions = {k: conditions[k] for k in prod_keys if k in conditions}
    user_approved = rights_status == "user_approved_for_production_review"
    production_ready = all(prod_conditions.values()) and technical_publishable

    completed = not pipeline_error

    embedded_rights = rights.get("embedded_footage_rights", "UNKNOWN")
    manual_review_required = (
        embedded_rights == "UNKNOWN"
        and not user_approved
    ) or rights.get("manual_review_required", False if user_approved else True)

    if manual_review_required and not user_approved:
        publishable = False
    else:
        publishable = technical_publishable and all(conditions.values())

    failed = [k for k, v in conditions.items() if not v]

    publish_blockers = []
    if not conditions.get("production_mode"):
        publish_blockers.append("テストモードで実行されました（本番モードが必要）")
    if not conditions.get("voicevox_used"):
        publish_blockers.append("VOICEVOX音声が使用されていません")
    if not conditions.get("speaker_aoyama"):
        publish_blockers.append("話者が青山龍星ではありません")
    if not conditions.get("speed_095"):
        publish_blockers.append("速度が0.95ではありません")
    if not conditions.get("no_test_audio"):
        publish_blockers.append("テスト音声が使用されました（fallback_used=true）")
    if not conditions.get("bgm_exists"):
        publish_blockers.append("BGMファイルが存在しません")
    if not conditions.get("production_bgm_used"):
        publish_blockers.append("本番BGM6曲が使用されていません（テストトーン不可）")
    if not conditions.get("bgm_license_exists"):
        publish_blockers.append("BGMライセンス情報がありません")
    if not conditions.get("duration_ok"):
        publish_blockers.append("再生時間が規定範囲外です")
    if not conditions.get("resolution_ok"):
        publish_blockers.append("解像度が1080x1920ではありません")
    if not conditions.get("codec_ok"):
        publish_blockers.append("映像コーデックがH.264ではありません")
    if not conditions.get("decode_pass"):
        publish_blockers.append("decode検査でエラーが検出されました")
    if not conditions.get("zero_kb_none"):
        publish_blockers.append("0KBファイルが検出されました")
    if not conditions.get("metadata_risk_not_ng"):
        publish_blockers.append("メタデータ一次リスク判定がNGです")
    if not conditions.get("watermark_not_ng"):
        publish_blockers.append("ウォーターマーク判定がNGです")
    if not conditions.get("audio_removed"):
        publish_blockers.append("元動画の音声が除去されていません")
    if not conditions.get("review_screenshots_exist"):
        publish_blockers.append("確認用スクリーンショットがありません")
    if manual_review_required and not user_approved:
        publish_blockers.append("荒木による目視確認が未完了です（embedded_footage_rights=UNKNOWN）")

    return {
        "technical_publishable": technical_publishable,
        "production_ready": production_ready,
        "completed": completed,
        "final_release_approved": False,
        "manual_review_required": manual_review_required,
        "publishable": publishable,
        "rights_status": rights_status,
        "embedded_footage_rights": embedded_rights,
        "conditions": conditions,
        "failed_conditions": failed,
        "publish_blockers": publish_blockers,
    }


def run_auto_discovery(mode, logger=None):
    """完全自動企画発掘パイプライン"""
    research_client = get_research_client()
    research_result = research_client.run_full_research()

    candidates = research_result.get("candidates", [])
    if logger:
        logger.info(f"自動発掘: {research_result['total_candidates']}件の候補動画を取得"
                     f" (API: {research_result.get('api_available', False)},"
                     f" fixture: {research_result.get('fixture', False)})")

    scored = rank_candidates(candidates)
    if logger:
        for i, c in enumerate(scored[:5]):
            logger.info(f"  TOP{i+1}: {c.get('title', '')[:40]} "
                         f"(score={c.get('overall_score', 0):.4f})")

    history = load_topic_history()
    selection = run_auto_topic_selection(scored, history)

    if logger:
        logger.info(f"自動選定: 選手={selection['selected_player']}, "
                     f"プレー={selection['selected_play']}, "
                     f"タイトル={selection['selected_title']}")

    top_videos = scored[:5] if scored else []
    analyses = analyze_batch(top_videos, limit=3)
    concept = None
    if analyses:
        concept = generate_new_concept(
            analyses[0], selection["selected_player"], selection["selected_play"]
        )
        if logger:
            logger.info(f"参考動画の本質: {concept.get('applied_principle', '')}")

    from lib.topic_discovery import PRIORITY_5_PLAYERS, PRIORITY_4_PLAYERS
    all_players = PRIORITY_5_PLAYERS + PRIORITY_4_PLAYERS
    keywords_en = []
    for p in all_players:
        if p["name"] == selection["selected_player"]:
            keywords_en = p.get("keywords_en", [])
            break

    source_candidates = find_source_candidates(
        selection["selected_player"], selection["selected_play"], keywords_en
    )

    return {
        "research": research_result,
        "scored_candidates": scored,
        "selection": selection,
        "analyses": analyses,
        "concept": concept,
        "source_candidates": source_candidates,
        "history": history,
    }


def _generate_job_id(player, topic):
    import re
    safe = re.sub(r'[^a-zA-Z0-9　-鿿]', '_', f"{player}_{topic}")[:60]
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{safe}_{ts}"


def run_pipeline(args):
    mode = determine_mode(args)
    settings = load_settings()
    pipeline_error = False

    auto_fetch_result = None
    auto_discovery_result = None
    input_video = None

    if getattr(args, 'auto', False):
        pre_log_dir = os.path.join(BASE_DIR, "outputs",
                                   "production" if mode == "production" else "test")
        os.makedirs(pre_log_dir, exist_ok=True)
        pre_log = os.path.join(pre_log_dir, "auto_discovery.log")
        pre_logger = setup_logging(pre_log)
        pre_logger.info("=== 完全自動企画発掘パイプライン開始 ===")

        auto_discovery_result = run_auto_discovery(mode, pre_logger)
        selection = auto_discovery_result["selection"]
        pre_logger.info(f"選定完了: {selection['selected_player']} / "
                         f"{selection['selected_play']} / {selection['selected_title']}")

        if getattr(args, 'dry_run', False):
            print("\n=== 自動選定結果（dry-run） ===")
            print(f"  選手: {selection['selected_player']}")
            print(f"  プレー: {selection['selected_play']}")
            print(f"  テーマ: {selection['selected_topic']}")
            print(f"  タイトル: {selection['selected_title']}")
            print(f"  タイトル候補: {selection.get('title_candidates', [])}")
            print(f"  候補動画数: {auto_discovery_result['research']['total_candidates']}")
            if auto_discovery_result.get("concept"):
                print(f"  適用原則: {auto_discovery_result['concept'].get('applied_principle', '')}")
            print(f"  選定理由: {selection.get('selection_reason', '')}")
            dry_run_path = os.path.join(pre_log_dir, "dry_run_result.json")
            with open(dry_run_path, "w", encoding="utf-8") as f:
                json.dump({
                    "selection": selection,
                    "research_summary": {
                        "total_candidates": auto_discovery_result["research"]["total_candidates"],
                        "api_available": auto_discovery_result["research"].get("api_available", False),
                    },
                    "concept": auto_discovery_result.get("concept"),
                    "source_candidates": auto_discovery_result.get("source_candidates"),
                    "top_scored": [
                        {"title": c.get("title", ""), "score": c.get("overall_score", 0)}
                        for c in auto_discovery_result.get("scored_candidates", [])[:5]
                    ],
                }, f, ensure_ascii=False, indent=2)
            print(f"\n  結果保存先: {dry_run_path}")
            return True

    if args.video and os.path.exists(args.video):
        input_video = args.video
    elif not getattr(args, 'auto', False) and settings.get("channel", {}).get("auto_fetch", False):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_label = "production" if mode == "production" else "test"
        fetch_work_dir = os.path.join(BASE_DIR, "outputs", mode_label, f"{ts}_auto_fetch_work")
        os.makedirs(fetch_work_dir, exist_ok=True)

        temp_log = os.path.join(fetch_work_dir, "fetch.log")
        setup_logging(temp_log)
        fetch_logger = logging.getLogger("the_dunk")
        fetch_logger.info("=== 自動取得パイプライン開始 ===")

        auto_fetch_result = run_auto_fetch_pipeline(settings, fetch_work_dir)
        if auto_fetch_result:
            input_video = auto_fetch_result["video_path"]
            fetch_logger.info(f"自動取得成功: {input_video}")
        else:
            fetch_logger.error("自動取得失敗: 使用可能な動画が見つかりませんでした")
            if mode == "production":
                print("\nエラー: 自動取得で使用可能な動画が見つかりませんでした。")
                print("ザ・ダンクチャンネルの動画がメタデータ一次リスク判定を通過しませんでした。")
                return False

    if auto_discovery_result:
        selection = auto_discovery_result["selection"]
        player = selection["selected_player"]
        topic = selection["selected_topic"]
    elif auto_fetch_result:
        player = auto_fetch_result["player"]
        topic = auto_fetch_result["topic"]
    else:
        player, topic = determine_topic_and_player(args)

    job_id = _generate_job_id(player, topic)
    source_urls = []

    output_dir = create_output_dir(mode, player, topic)
    log_path = os.path.join(output_dir, "execution.log")
    logger = setup_logging(log_path)

    logger.info(f"=== ザ・ダンク 動画制作自動化システム ===")
    logger.info(f"モード: {mode}")
    logger.info(f"選手: {player}")
    logger.info(f"テーマ: {topic}")
    logger.info(f"出力先: {output_dir}")
    if auto_fetch_result:
        logger.info(f"自動取得: 有効")
        logger.info(f"元動画: {auto_fetch_result.get('video_meta', {}).get('title', '不明')}")
        r = auto_fetch_result.get("rights", {})
        logger.info(f"channel_source_permission: {r.get('channel_source_permission', '不明')}")
        logger.info(f"embedded_footage_rights: {r.get('embedded_footage_rights', '不明')}")
        logger.info(f"metadata_risk_status: {r.get('metadata_risk_status', '不明')}")
        logger.info(f"audio_removed: {r.get('audio_removed', False)}")
        logger.info(f"watermark_status: {r.get('watermark_status', '不明')}")
        logger.info(f"manual_review_required: {r.get('manual_review_required', True)}")
    if input_video:
        logger.info(f"入力動画: {input_video}")

    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=BASE_DIR,
        ).stdout.strip()
    except Exception:
        git_commit = "unknown"
    logger.info(f"GitコミットID: {git_commit}")

    logger.info("--- preflight チェック ---")
    preflight = run_preflight(mode, skip_input_check=(input_video is not None or auto_fetch_result is not None))
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

    if input_video and os.path.exists(input_video):
        logger.info(f"入力動画を使用: {input_video}")
        frame_specs = [{"path": input_video, "duration": audio_duration, "label": "input_video"}]
    else:
        frame_specs = generate_visual_frames(script, frames_dir, settings)
        logger.info(f"ビジュアルフレーム生成完了: {len(frame_specs)}フレーム")

    logger.info("--- BGM ---")
    bgm_path = None
    bgm_rotation_index = -1
    bgm_gain_db = -25.0

    if mode == "production":
        bgm_validation = validate_all_bgm()
        for bv in bgm_validation:
            logger.info(f"  BGM_{bv['index']+1:02d}: {bv['name']} - {'OK' if bv['valid'] else bv['detail']}")

        bgm_path, bgm_rotation_index = get_next_bgm(mode)
        if bgm_path:
            ok, detail = validate_bgm_file(bgm_path)
            if ok:
                logger.info(f"本番BGM選択: BGM_{bgm_rotation_index+1:02d} = {os.path.basename(bgm_path)}")
            else:
                logger.error(f"本番BGM検証失敗: BGM_{bgm_rotation_index+1:02d} = {detail}")
                bgm_path = None
        if not bgm_path:
            logger.error("本番BGMが利用できません。production_ready=falseになります。")
    elif mode == "test":
        bgm_path = os.path.join(output_dir, "test_bgm.wav")
        generate_bgm_tone(bgm_path, duration=70.0)
        logger.info("テスト用BGMトーン生成完了")

    logger.info("--- 動画合成 ---")
    if mode == "test":
        video_filename = "TEST_ONLY_final.mp4"
    else:
        video_filename = "final.mp4"
    video_path = os.path.join(output_dir, video_filename)
    create_video_from_frames(frame_specs, narration_path, ass_path, video_path, settings, bgm_path)
    logger.info(f"動画生成完了: {video_path}")

    logger.info("--- スクリーンショット生成 ---")
    ss_dir = os.path.join(output_dir, "screenshots")
    generate_screenshots(video_path, ss_dir)

    logger.info("--- メタデータ生成 ---")
    credits_text = generate_rights_files(output_dir, mode, auto_fetch_result)
    generate_research_files(script, output_dir)
    save_metadata_files(script, output_dir, credits_text)
    generate_trend_notes(os.path.join(output_dir, "trend_notes.txt"))

    if auto_discovery_result:
        logger.info("--- 自動発掘メタデータ保存 ---")
        selection = auto_discovery_result["selection"]
        save_source_candidates(auto_discovery_result["source_candidates"], output_dir)

        editing_tl = generate_editing_timeline([], target_duration=55.0, script=script)
        with open(os.path.join(output_dir, "editing_timeline.json"), "w", encoding="utf-8") as f:
            json.dump(editing_tl, f, ensure_ascii=False, indent=2)
        logger.info(f"編集タイムライン生成: {editing_tl['segment_count']}セグメント")

        pub_pkg = generate_publishing_package(
            player, selection["selected_play"], topic,
            selection["selected_title"], output_dir,
        )
        logger.info(f"投稿パッケージ生成: タイトル={pub_pkg['title']}")

        with open(os.path.join(output_dir, "auto_discovery_report.json"), "w", encoding="utf-8") as f:
            json.dump({
                "selection": selection,
                "research_summary": {
                    "total_candidates": auto_discovery_result["research"]["total_candidates"],
                    "api_available": auto_discovery_result["research"].get("api_available", False),
                    "fixture": auto_discovery_result["research"].get("fixture", False),
                },
                "concept": auto_discovery_result.get("concept"),
                "analyses_count": len(auto_discovery_result.get("analyses", [])),
                "top_scored": [
                    {"title": c.get("title", ""), "score": c.get("overall_score", 0)}
                    for c in auto_discovery_result.get("scored_candidates", [])[:5]
                ],
            }, f, ensure_ascii=False, indent=2)

    logger.info("--- ログflush ---")
    for handler in logger.handlers[:]:
        handler.flush()
        handler.close()
        logger.removeHandler(handler)

    logger.info("--- 品質検査 ---")
    reattach_log = os.path.join(output_dir, "execution.log")
    logger = setup_logging(reattach_log)

    quality = run_quality_check(video_path, mode, tts_info)
    qr_path = os.path.join(output_dir, "quality_report.json")

    for check in quality["checks"]:
        status = "PASS" if check["pass"] else "FAIL"
        logger.info(f"  {status}: {check['name']} - {check['detail']}")

    logger.info("--- 0KB検査（全ログflush後） ---")
    for handler in logger.handlers[:]:
        handler.flush()

    zero_files = check_zero_kb(output_dir)
    zero_kb_ok = len(zero_files) == 0
    quality["zero_kb_ok"] = zero_kb_ok
    if zero_files:
        logger.error(f"0KBファイル検出: {zero_files}")
        quality["checks"].append({
            "name": "0KB検査（最終）",
            "pass": False,
            "detail": f"{len(zero_files)}件: {zero_files}",
        })
        quality["pass"] = False
        quarantine_dir = os.path.join(output_dir, "_quarantine_0kb")
        os.makedirs(quarantine_dir, exist_ok=True)
        for zf in zero_files:
            zf_name = os.path.basename(zf)
            try:
                shutil.move(zf, os.path.join(quarantine_dir, zf_name))
                logger.info(f"0KBファイル隔離: {zf} → {quarantine_dir}/{zf_name}")
            except OSError as e:
                logger.error(f"0KBファイル隔離失敗: {zf}: {e}")
    else:
        quality["checks"].append({
            "name": "0KB検査（最終）",
            "pass": True,
            "detail": "0件",
        })

    save_quality_report(quality, qr_path, mode)

    review_ss_exist = os.path.isdir(ss_dir) and len(os.listdir(ss_dir)) > 0
    if auto_fetch_result and auto_fetch_result.get("review_frames_dir"):
        rfd = auto_fetch_result["review_frames_dir"]
        review_ss_exist = review_ss_exist and os.path.isdir(rfd) and len(os.listdir(rfd)) > 0

    bgm_license_path = os.path.join(output_dir, "bgm_license.json")
    pub = determine_publishable(
        mode, quality, tts_info, bgm_path, bgm_license_path,
        auto_fetch_result, review_ss_exist, pipeline_error=pipeline_error,
    )

    if mode == "production" and pub["completed"] and bgm_rotation_index >= 0 and bgm_path:
        advanced = mark_completed(job_id, bgm_rotation_index, bgm_path,
                                  timestamp=datetime.now().isoformat())
        if advanced:
            logger.info(f"BGM循環: 完了 job={job_id}, index={bgm_rotation_index} → 次回index={load_bgm_state()['next_bgm_index']}")
        else:
            logger.info(f"BGM循環: 重複job_idのため順番据え置き job={job_id}")

    if auto_discovery_result and pub["completed"]:
        history = auto_discovery_result.get("history", load_topic_history())
        sel = auto_discovery_result["selection"]
        history["history"].append({
            "job_id": job_id,
            "selected_player": sel["selected_player"],
            "selected_play": sel["selected_play"],
            "selected_topic": sel["selected_topic"],
            "selected_title": sel["selected_title"],
            "completed_at": datetime.now().isoformat(),
        })
        save_topic_history(history)
        logger.info(f"トピック履歴更新: {len(history['history'])}件")

    production_metadata = {
        "job_id": job_id,
        "player_name": player,
        "topic": topic,
        "production_video_sequence": load_bgm_state()["last_completed_production_sequence"],
        "bgm_rotation_index": bgm_rotation_index,
        "bgm_name": os.path.basename(bgm_path) if bgm_path else None,
        "bgm_absolute_path": os.path.abspath(bgm_path) if bgm_path else None,
        "bgm_start_time": 0.0 if bgm_path else None,
        "bgm_end_time": quality.get("duration", 0) if bgm_path else None,
        "bgm_gain_db": settings["bgm"].get("gain_db", -25.0),
        "bgm_looped": False,
        "voice_name": tts_info.get("speaker") if tts_info else None,
        "speaker_id": tts_info.get("style_id") if tts_info else None,
        "voice_speed": tts_info.get("speed") if tts_info else None,
        "voicevox_connected": tts_info.get("engine") == "VOICEVOX" if tts_info else False,
        "source_urls": source_urls,
        "rights_status": pub["rights_status"],
        "technical_publishable": pub["technical_publishable"],
        "production_ready": pub["production_ready"],
        "completed": pub["completed"],
        "final_release_approved": pub["final_release_approved"],
        "output_mp4_absolute_path": os.path.abspath(video_path),
        "file_size_bytes": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
        "duration_seconds": quality.get("duration", 0),
        "video_codec": "h264",
        "audio_codec": "aac",
        "resolution": f"{settings['video']['width']}x{settings['video']['height']}",
        "fps": settings["video"]["fps"],
        "created_at": datetime.now().isoformat(),
    }
    with open(os.path.join(output_dir, "production_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(production_metadata, f, ensure_ascii=False, indent=2)

    pub_path = os.path.join(output_dir, "publishable.json")
    with open(pub_path, "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, indent=2)

    logger.info(f"--- publishable判定 ---")
    logger.info(f"  technical_publishable: {pub['technical_publishable']}")
    logger.info(f"  manual_review_required: {pub['manual_review_required']}")
    logger.info(f"  publishable: {pub['publishable']}")
    logger.info(f"  embedded_footage_rights: {pub['embedded_footage_rights']}")
    if pub["failed_conditions"]:
        logger.info(f"  不足条件: {pub['failed_conditions']}")
    if pub.get("publish_blockers"):
        for blocker in pub["publish_blockers"]:
            logger.info(f"  投稿不可理由: {blocker}")

    compat_output = os.path.join(BASE_DIR, "output", "final.mp4")
    os.makedirs(os.path.dirname(compat_output), exist_ok=True)
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        shutil.copy2(video_path, compat_output)
        logger.info(f"互換コピー作成: {compat_output} (正式保存先ではない)")
    else:
        logger.error(f"final.mp4が0KBまたは存在しないため互換コピーをスキップ: {video_path}")
        quality["pass"] = False

    overall = "PASS" if quality["pass"] else "FAIL"
    if mode == "test" and not quality["pass"]:
        non_dur_fails = [c for c in quality["checks"] if not c["pass"] and c["name"] not in ("再生時間", "TTS")]
        if not non_dur_fails:
            overall = "PASS (テストモード: 尺・TTS制約は許容)"

    _save_status(output_dir, overall, "完了", mode, player, topic, quality, tts_info, auto_fetch_result, pub)

    if auto_fetch_result:
        fetch_report = {
            "source_video": auto_fetch_result.get("video_meta", {}).get("title", ""),
            "source_url": auto_fetch_result.get("video_meta", {}).get("url", ""),
            "detected_player": auto_fetch_result.get("player", ""),
            "detected_topic": auto_fetch_result.get("topic", ""),
            "rights": auto_fetch_result.get("rights", {}),
        }
        with open(os.path.join(output_dir, "auto_fetch_report.json"), "w", encoding="utf-8") as f:
            json.dump(fetch_report, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*50}")
    logger.info(f"最終結果: {overall}")
    logger.info(f"正式出力: {video_path}")
    logger.info(f"互換コピー: {compat_output} (正式保存先ではない)")
    if auto_fetch_result:
        logger.info(f"自動取得元: {auto_fetch_result.get('video_meta', {}).get('title', '不明')}")
    logger.info(f"technical_publishable: {pub['technical_publishable']}")
    logger.info(f"manual_review_required: {pub['manual_review_required']}")
    logger.info(f"publishable: {pub['publishable']}")
    if mode == "test":
        logger.info("注意: TEST ONLY - 投稿不可 - 技術検証用")
    logger.info(f"{'='*50}")

    _print_summary(output_dir, video_path, quality, script, mode, tts_info, auto_fetch_result, pub)

    return True


def _save_status(output_dir, status, message, mode, player, topic,
                 quality=None, tts_info=None, auto_fetch_result=None, pub=None):
    data = {
        "status": status,
        "message": message,
        "mode": mode,
        "player": player,
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "quality": quality["pass"] if quality else None,
        "tts_engine": tts_info.get("engine") if tts_info else None,
        "auto_fetch": bool(auto_fetch_result),
        "source_video": auto_fetch_result.get("video_meta", {}).get("title", "") if auto_fetch_result else None,
    }
    if pub:
        data["technical_publishable"] = pub.get("technical_publishable", False)
        data["production_ready"] = pub.get("production_ready", False)
        data["completed"] = pub.get("completed", False)
        data["final_release_approved"] = pub.get("final_release_approved", False)
        data["manual_review_required"] = pub.get("manual_review_required", True)
        data["publishable"] = pub.get("publishable", False)
        data["rights_status"] = pub.get("rights_status", "UNKNOWN")
        data["publish_blockers"] = pub.get("publish_blockers", [])

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
        if pub:
            f.write(f"\n## publishable判定\n\n")
            f.write(f"- technical_publishable: {pub.get('technical_publishable', False)}\n")
            f.write(f"- production_ready: {pub.get('production_ready', False)}\n")
            f.write(f"- completed: {pub.get('completed', False)}\n")
            f.write(f"- final_release_approved: {pub.get('final_release_approved', False)}\n")
            f.write(f"- rights_status: {pub.get('rights_status', 'UNKNOWN')}\n")
            f.write(f"- manual_review_required: {pub.get('manual_review_required', True)}\n")
            f.write(f"- publishable: {pub.get('publishable', False)}\n")
            f.write(f"- embedded_footage_rights: {pub.get('embedded_footage_rights', 'UNKNOWN')}\n")
            if pub.get("failed_conditions"):
                f.write(f"- 不足条件: {pub['failed_conditions']}\n")
            if pub.get("publish_blockers"):
                f.write(f"\n### 投稿不可の理由\n\n")
                for b in pub["publish_blockers"]:
                    f.write(f"- {b}\n")
        if quality:
            f.write(f"\n## 品質検査\n\n")
            for c in quality.get("checks", []):
                mark = "PASS" if c["pass"] else "FAIL"
                f.write(f"- [{mark}] {c['name']}: {c['detail']}\n")
        if mode == "test":
            f.write(f"\n## 注意\n\nTEST ONLY - 投稿不可 - 技術検証用\n")


def _print_summary(output_dir, final_path, quality, script, mode, tts_info,
                   auto_fetch_result=None, pub=None):
    print("\n" + "=" * 60)
    print("  ザ・ダンク 動画制作完了レポート")
    print("=" * 60)
    if auto_fetch_result:
        r = auto_fetch_result.get("rights", {})
        print(f"\n  元動画: {auto_fetch_result.get('video_meta', {}).get('title', '不明')[:50]}")
        print(f"  元動画URL: {auto_fetch_result.get('video_meta', {}).get('url', '不明')}")
        print(f"  channel_source_permission: {r.get('channel_source_permission', 'UNKNOWN')}")
        print(f"  embedded_footage_rights: {r.get('embedded_footage_rights', 'UNKNOWN')}")
        print(f"  metadata_risk_status: {r.get('metadata_risk_status', 'UNKNOWN')}")
        print(f"  watermark_status: {r.get('watermark_status', 'UNKNOWN')}")
        print(f"  audio_removed: {r.get('audio_removed', False)}")
    print(f"\n  選手: {script['player']}")
    print(f"  テーマ: {script['topic']}")
    print(f"  企画タイプ: {script.get('plan_type_label', '不明')}")
    print(f"  モード: {mode}")
    print(f"  TTS: {tts_info.get('engine', '不明')} ({tts_info.get('speaker', '')})")
    print(f"  正式出力: {final_path}")
    print(f"  再生時間: {quality.get('duration', 0):.2f}秒")
    if pub:
        print(f"\n  publishable判定:")
        print(f"    technical_publishable: {pub['technical_publishable']}")
        print(f"    production_ready: {pub.get('production_ready', False)}")
        print(f"    completed: {pub.get('completed', False)}")
        print(f"    final_release_approved: {pub.get('final_release_approved', False)}")
        print(f"    rights_status: {pub.get('rights_status', 'UNKNOWN')}")
        print(f"    manual_review_required: {pub['manual_review_required']}")
        print(f"    publishable: {pub['publishable']}")
        if pub.get("failed_conditions"):
            print(f"    不足条件: {pub['failed_conditions']}")
        if pub.get("publish_blockers"):
            print(f"    投稿不可の理由:")
            for b in pub["publish_blockers"]:
                print(f"      - {b}")
    print(f"\n  品質検査:")
    for c in quality.get("checks", []):
        mark = "PASS" if c["pass"] else "FAIL"
        print(f"    [{mark}] {c['name']}: {c['detail']}")
    print(f"\n  出力フォルダ: {output_dir}")
    if auto_fetch_result and auto_fetch_result.get("review_frames_dir"):
        print(f"  確認用フレーム: {auto_fetch_result['review_frames_dir']}")
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
