"""素材候補探索・ハイライト区間検出モジュール"""
import json
import os
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_source_candidates(player_name, play, keywords_en=None):
    """選手とプレーに基づいて素材候補URLリストを生成（実際のダウンロードは行わない）"""
    candidates = []

    search_terms = [
        f"{player_name} {play}",
        f"{player_name} highlights",
    ]
    if keywords_en:
        for kw in keywords_en[:3]:
            search_terms.append(f"{kw} {play}")

    for term in search_terms:
        candidates.append({
            "search_query": term,
            "source_type": "candidate_source",
            "rights_status": "candidate_source",
            "requires_manual_review": True,
            "url": "",
            "note": "素材URLは荒木愛一朗が手動で確認・承認する必要があります",
        })

    return {
        "player": player_name,
        "play": play,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "auto_download_enabled": False,
        "note": "素材の最終選定と権利確認は荒木愛一朗が行います",
    }


def detect_highlights_from_video(video_path, max_clips=5):
    """動画からハイライト区間を検出する（音量・動きベース）"""
    if not video_path or not os.path.exists(video_path):
        return {"clips": [], "error": "動画ファイルが見つかりません"}

    duration = _get_duration(video_path)
    if duration <= 0:
        return {"clips": [], "error": "動画の長さを取得できません"}

    volume_peaks = _detect_volume_peaks(video_path, duration)

    clips = []
    for i, peak in enumerate(volume_peaks[:max_clips]):
        start = max(0, peak - 3.0)
        end = min(duration, peak + 5.0)
        clips.append({
            "clip_index": i,
            "start_time": round(start, 2),
            "end_time": round(end, 2),
            "duration": round(end - start, 2),
            "detection_method": "volume_peak",
            "confidence": 0.6,
            "label": f"highlight_{i+1:02d}",
        })

    return {
        "video_path": video_path,
        "video_duration": round(duration, 2),
        "clip_count": len(clips),
        "clips": clips,
    }


def generate_editing_timeline(clips, target_duration=55.0, script=None):
    """検出クリップから縦型編集タイムラインを生成"""
    if not clips:
        return _generate_fallback_timeline(target_duration, script)

    timeline = []
    current_time = 0.0
    remaining = target_duration

    if script and script.get("sections"):
        hook_section = script["sections"][0]
        hook_duration = min(3.0, remaining)
        timeline.append({
            "timeline_index": 0,
            "start": 0.0,
            "end": hook_duration,
            "source": "title_card",
            "effect": "zoom_in",
            "crop": "center_vertical",
            "text_overlay": hook_section.get("text", "")[:30],
            "speed": 1.0,
        })
        current_time = hook_duration
        remaining -= hook_duration

    for i, clip in enumerate(clips):
        if remaining <= 0:
            break

        clip_dur = min(clip["duration"], remaining, 8.0)

        effect = "none"
        speed = 1.0
        if i == 0:
            effect = "slow_motion"
            speed = 0.5
            clip_dur = min(clip_dur * 2, remaining)
        elif i == len(clips) - 1:
            effect = "zoom_in"

        timeline.append({
            "timeline_index": len(timeline),
            "start": round(current_time, 2),
            "end": round(current_time + clip_dur, 2),
            "source_clip": clip.get("label", f"clip_{i}"),
            "source_start": clip["start_time"],
            "source_end": clip["start_time"] + clip_dur * speed,
            "effect": effect,
            "crop": "dynamic_vertical",
            "speed": speed,
        })
        current_time += clip_dur
        remaining -= clip_dur

    if remaining > 2.0 and script:
        timeline.append({
            "timeline_index": len(timeline),
            "start": round(current_time, 2),
            "end": round(current_time + remaining, 2),
            "source": "end_card",
            "effect": "fade_out",
            "crop": "center_vertical",
            "text_overlay": "ザ・ダンク",
            "speed": 1.0,
        })

    return {
        "total_duration": round(target_duration, 2),
        "segment_count": len(timeline),
        "timeline": timeline,
        "crop_mode": "dynamic_vertical",
        "output_resolution": "1080x1920",
    }


def _generate_fallback_timeline(target_duration, script=None):
    """クリップがない場合のフォールバックタイムライン（自作ビジュアル用）"""
    timeline = []
    sections = script.get("sections", []) if script else []

    if not sections:
        sections = [
            {"label": "フック", "text": ""},
            {"label": "解説", "text": ""},
            {"label": "CTA", "text": ""},
        ]

    section_dur = target_duration / len(sections)
    current = 0.0

    for i, section in enumerate(sections):
        dur = min(section_dur, target_duration - current)
        if dur <= 0:
            break
        timeline.append({
            "timeline_index": i,
            "start": round(current, 2),
            "end": round(current + dur, 2),
            "source": "generated_visual",
            "effect": "ken_burns" if i % 2 == 0 else "none",
            "crop": "center_vertical",
            "text_overlay": section.get("text", "")[:30],
            "speed": 1.0,
            "section_label": section.get("label", ""),
        })
        current += dur

    return {
        "total_duration": round(target_duration, 2),
        "segment_count": len(timeline),
        "timeline": timeline,
        "crop_mode": "center_vertical",
        "output_resolution": "1080x1920",
        "note": "素材動画なし: 自作ビジュアルベースのタイムライン",
    }


def _get_duration(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _detect_volume_peaks(video_path, duration, segment_seconds=5.0):
    """音量ピークを検出してタイムスタンプリストを返す"""
    peaks = []
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "frame=pkt_pts_time",
             "-of", "csv=p=0", "-f", "lavfi",
             f"amovie={video_path},astats=metadata=1:reset=1"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            num_segments = int(duration / segment_seconds)
            for i in range(min(num_segments, 10)):
                peaks.append(segment_seconds * i + segment_seconds / 2)
            return peaks
    except Exception:
        num_segments = int(duration / segment_seconds)
        for i in range(min(num_segments, 10)):
            peaks.append(segment_seconds * i + segment_seconds / 2)

    if not peaks:
        num_segments = int(duration / segment_seconds)
        for i in range(min(num_segments, 10)):
            peaks.append(segment_seconds * i + segment_seconds / 2)

    return peaks


def save_source_candidates(candidates_result, output_dir):
    """素材候補情報をファイルに保存"""
    path = os.path.join(output_dir, "source_candidates.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(candidates_result, f, ensure_ascii=False, indent=2)
    return path
