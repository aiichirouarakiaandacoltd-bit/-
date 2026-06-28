"""
ザ・ダンク チャンネル動画自動取得・候補選定モジュール

yt-dlpを使用してザ・ダンクチャンネルの動画一覧を取得し、
優先選手・プレータイプに基づいて候補を自動選定する。
選定した動画を自動ダウンロードし、メタデータ一次リスク判定を行う。
荒木側の手動作業は不要。
"""

import json
import logging
import os
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger("the_dunk")

PLAYER_PRIORITY_ORDER = [
    "河村勇輝",
    "八村塁",
    "レブロン・ジェームズ",
    "ステフィン・カリー",
    "ビクター・ウェンバンヤマ",
    "富樫勇樹",
    "富永啓生",
    "渡邊雄太",
    "比江島慎",
]

PLAY_PRIORITY = {
    "豪快ダンク": 15, "ダンク": 12, "ポスタライズ": 14,
    "ノールック": 14, "ノールックパス": 14,
    "ブザービーター": 15, "ブザービート": 15,
    "クラッチ": 13, "ゲームウィナー": 13, "ゲームウィニング": 13,
    "神アシスト": 13, "アシスト": 8,
    "記録更新": 12, "歴代": 10, "新記録": 12,
    "アリウープ": 11, "クロスオーバー": 10,
    "ステップバック": 10, "ユーロステップ": 10,
    "ブロック": 9, "スティール": 8,
    "トリプルダブル": 11, "スーパープレー": 10,
    "ハイライト": 7, "解説": 6, "分析": 6, "技術": 7,
    "戦術": 7, "ピック": 5,
    "dunk": 12, "block": 9, "assist": 8, "crossover": 10,
    "buzzer beater": 15, "game winner": 13, "no look": 14,
    "clutch": 13,
}

BROADCAST_MARKERS = [
    "テレビ", "放送", "中継", "実況", "tv ", "broadcast",
    "nba rakuten", "wowow", "nhk ", "bs1", "bsプレミアム",
    "地上波", "cs放送", "ケーブルテレビ",
]

WATERMARK_MARKERS = [
    "espn", "nba tv", "tnt ", "abc ", "fox sports",
    "sky sports", "bt sport", "dazn", "nba.com",
]

THIRD_PARTY_BGM_MARKERS = [
    "music by", "song:", "bgm:", "track:", "♪",
    "licensed music", "copyright music",
    "楽曲提供", "music credit", "使用楽曲",
]

EXCLUSION_KEYWORDS = [
    "nba公式", "nba official", "nba japan",
    "nba rakuten", "rakuten nba",
    "b.league", "bリーグ", "b league",
    "fiba", "jba",
]


def load_source_permissions():
    path = os.path.join(BASE_DIR, "config", "source_permissions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_player_aliases():
    path = os.path.join(BASE_DIR, "config", "player_aliases.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_channel_videos(channel_url, max_videos=30):
    """yt-dlpでチャンネルの動画一覧を取得する（メタデータのみ、ダウンロードしない）"""
    env = os.environ.copy()
    env.pop("HTTPS_PROXY", None)
    env.pop("HTTP_PROXY", None)
    env.pop("https_proxy", None)
    env.pop("http_proxy", None)

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-download",
        "--playlist-end", str(max_videos),
        f"{channel_url}/videos",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, env=env
        )
    except subprocess.TimeoutExpired:
        logger.error("チャンネル動画一覧取得タイムアウト")
        return []
    except FileNotFoundError:
        logger.error("yt-dlpがインストールされていません。pip install yt-dlp を実行してください。")
        return []

    if result.returncode != 0:
        logger.error(f"yt-dlp動画一覧取得エラー: {result.stderr[:500]}")
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            videos.append({
                "id": data.get("id", ""),
                "title": data.get("title", ""),
                "url": data.get("url", "") or data.get("webpage_url", "") or f"https://www.youtube.com/watch?v={data.get('id', '')}",
                "duration": data.get("duration"),
                "view_count": data.get("view_count"),
                "upload_date": data.get("upload_date", ""),
                "description": data.get("description", ""),
            })
        except json.JSONDecodeError:
            continue

    logger.info(f"チャンネルから{len(videos)}件の動画を取得")
    return videos


def fetch_video_details(video_url):
    """個別動画の詳細メタデータを取得"""
    env = os.environ.copy()
    env.pop("HTTPS_PROXY", None)
    env.pop("HTTP_PROXY", None)
    env.pop("https_proxy", None)
    env.pop("http_proxy", None)

    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        video_url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    except subprocess.TimeoutExpired:
        logger.error(f"動画詳細取得タイムアウト: {video_url}")
        return None
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        logger.error(f"動画詳細取得エラー: {result.stderr[:300]}")
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def score_video(video, player_aliases):
    """動画の候補スコアを算出（高いほど優先）"""
    score = 0
    title = video.get("title", "")
    description = video.get("description", "")
    combined_text = f"{title} {description}"
    combined_lower = combined_text.lower()

    for rank, canonical_name in enumerate(PLAYER_PRIORITY_ORDER):
        priority_score = (len(PLAYER_PRIORITY_ORDER) - rank) * 10

        if canonical_name in combined_text:
            score += priority_score
            break

        for player_key, info in player_aliases.items():
            p_canonical = info.get("canonical", player_key)
            if p_canonical != canonical_name:
                continue
            variants = info.get("variants", [])
            nicknames = info.get("nicknames", [])
            for name in variants + nicknames:
                if name in combined_text:
                    score += priority_score
                    break
            break

    for keyword, kw_score in PLAY_PRIORITY.items():
        if keyword.lower() in combined_lower:
            score += kw_score

    jp_vs_keywords = ["対決", "vs", "対戦", "日本人", "japanese"]
    for kw in jp_vs_keywords:
        if kw.lower() in combined_lower:
            score += 8
            break

    duration = video.get("duration")
    if duration:
        if 30 <= duration <= 180:
            score += 5
        elif 180 < duration <= 600:
            score += 3
        elif duration > 600:
            score += 1

    view_count = video.get("view_count")
    if view_count:
        if view_count > 1000000:
            score += 10
        elif view_count > 100000:
            score += 7
        elif view_count > 10000:
            score += 4
        elif view_count > 1000:
            score += 2

    return score


def select_candidates(videos, player_aliases, max_candidates=10):
    """スコアに基づいて上位候補を選出"""
    scored = []
    for v in videos:
        s = score_video(v, player_aliases)
        scored.append((s, v))

    scored.sort(key=lambda x: x[0], reverse=True)

    candidates = []
    for score, video in scored[:max_candidates]:
        candidates.append({**video, "score": score})
        logger.info(f"候補: [{score}点] {video.get('title', '')[:60]}")

    return candidates


def download_video(video_url, output_dir, video_id=None):
    """動画をダウンロードする"""
    os.makedirs(output_dir, exist_ok=True)

    env = os.environ.copy()
    env.pop("HTTPS_PROXY", None)
    env.pop("HTTP_PROXY", None)
    env.pop("https_proxy", None)
    env.pop("http_proxy", None)

    if video_id:
        existing = os.path.join(output_dir, f"{video_id}.mp4")
        if os.path.exists(existing) and os.path.getsize(existing) > 0:
            logger.info(f"既にダウンロード済み: {existing}")
            return existing

    output_template = os.path.join(
        output_dir,
        f"{video_id}.%(ext)s" if video_id else "%(id)s.%(ext)s"
    )

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        video_url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
    except subprocess.TimeoutExpired:
        logger.error(f"ダウンロードタイムアウト: {video_url}")
        return None
    except FileNotFoundError:
        logger.error("yt-dlpがインストールされていません")
        return None

    if result.returncode != 0:
        logger.error(f"ダウンロードエラー: {result.stderr[:300]}")
        return None

    if video_id:
        expected = os.path.join(output_dir, f"{video_id}.mp4")
        if os.path.exists(expected) and os.path.getsize(expected) > 0:
            logger.info(f"ダウンロード完了: {expected}")
            return expected

    for f in os.listdir(output_dir):
        fpath = os.path.join(output_dir, f)
        if os.path.isfile(fpath) and f.endswith(".mp4") and os.path.getsize(fpath) > 0:
            logger.info(f"ダウンロード完了: {fpath}")
            return fpath

    return None


def extract_segment(input_path, output_path, start_sec, duration_sec):
    """動画からセグメントを切り出す"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", input_path,
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        logger.error("セグメント切り出しタイムアウト")
        return None

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path
    return None


def strip_audio(input_path, output_path):
    """動画から音声を完全除去する（元音声・第三者BGM・放送実況の排除）"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-an",
        "-c:v", "copy",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path
    return None


def scale_to_shorts(input_path, output_path, width=1080, height=1920, fps=30):
    """動画を9:16 Shorts形式にリサイズ・クロップする"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"fps={fps}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path
    return None


def get_video_duration(path):
    """ffprobeで動画の長さを取得"""
    try:
        r = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json", path,
        ], capture_output=True, text=True, timeout=10)
        data = json.loads(r.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return None


def get_video_info(path):
    """ffprobeで動画情報を取得"""
    try:
        r = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-show_streams", "-show_format",
            "-of", "json", path,
        ], capture_output=True, text=True, timeout=10)
        return json.loads(r.stdout)
    except Exception:
        return None


def generate_review_frames(video_path, output_dir):
    """
    透かし・ロゴ確認用フレームを自動生成する。
    冒頭・中盤・終盤から複数フレームを抽出し、画面四隅が確認可能な
    スクリーンショットを保存する。

    高度なロゴ認識は行わない。荒木側が短時間で目視確認できる形で出力する。
    """
    os.makedirs(output_dir, exist_ok=True)
    duration = get_video_duration(video_path)
    if not duration or duration < 1:
        return []

    timestamps = {
        "review_frame_00_start.png": 0.5,
        "review_frame_01_early.png": min(3.0, duration * 0.1),
        "review_frame_02_quarter.png": duration * 0.25,
        "review_frame_03_middle.png": duration * 0.5,
        "review_frame_04_three_quarter.png": duration * 0.75,
        "review_frame_05_late.png": max(0.5, duration - 3.0),
        "review_frame_06_end.png": max(0.5, duration - 0.5),
    }

    generated = []
    for filename, ts in timestamps.items():
        out = os.path.join(output_dir, filename)
        try:
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(ts),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                out
            ], capture_output=True, timeout=10)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                generated.append(out)
        except Exception:
            pass

    logger.info(f"確認用フレーム生成: {len(generated)}枚 → {output_dir}")
    return generated


def metadata_risk_assessment(video_meta):
    """
    メタデータ一次リスク判定

    タイトル・説明文・タグ等のキーワードから行うリスク判定。
    権利OKの確定判定ではない。
    """
    result = {
        "metadata_risk_status": "REVIEW",
        "audio_risk_status": "REVIEW",
        "risk_factors": [],
        "metadata_available": {},
        "metadata_unavailable": [
            "YouTube Studio内の著作権申し立て（非公開情報）",
            "Content ID照合結果",
            "収益化制限状態",
            "地域ブロック情報（詳細）",
            "YouTube Studioの手動審査結果",
        ],
        "youtube_studio_check_required": [
            "著作権申し立て履歴",
            "Content ID一致情報",
            "収益化制限の有無",
            "地域ブロックの有無",
            "コミュニティガイドライン違反の有無",
        ],
    }

    if not video_meta:
        result["metadata_risk_status"] = "UNKNOWN"
        result["audio_risk_status"] = "UNKNOWN"
        return result

    title = video_meta.get("title", "")
    desc = video_meta.get("description", "")
    combined = f"{title} {desc}"
    combined_lower = combined.lower()

    result["metadata_available"] = {
        "title": title,
        "upload_date": video_meta.get("upload_date", ""),
        "duration": video_meta.get("duration"),
        "view_count": video_meta.get("view_count"),
        "description_length": len(desc),
    }

    has_third_party_bgm = False
    for marker in THIRD_PARTY_BGM_MARKERS:
        if marker.lower() in combined_lower:
            has_third_party_bgm = True
            result["risk_factors"].append(f"第三者BGMキーワード検出: {marker}")
            break

    has_broadcast = False
    for marker in BROADCAST_MARKERS:
        if marker.lower() in combined_lower:
            has_broadcast = True
            result["risk_factors"].append(f"放送関連キーワード検出: {marker}")
            break

    has_watermark_keyword = False
    for marker in WATERMARK_MARKERS:
        if marker.lower() in combined_lower:
            has_watermark_keyword = True
            result["risk_factors"].append(f"他社ロゴ関連キーワード検出: {marker}")
            break

    has_exclusion = False
    for kw in EXCLUSION_KEYWORDS:
        if kw.lower() in combined_lower:
            has_exclusion = True
            result["risk_factors"].append(f"禁止ソースキーワード: {kw}")
            break

    if has_third_party_bgm or has_broadcast:
        result["audio_risk_status"] = "NG"
    else:
        result["audio_risk_status"] = "LOW_RISK"

    if has_exclusion:
        result["metadata_risk_status"] = "NG"
    elif has_third_party_bgm or has_broadcast or has_watermark_keyword:
        result["metadata_risk_status"] = "HIGH_RISK"
    elif not result["risk_factors"]:
        result["metadata_risk_status"] = "LOW_RISK"

    copyright_info = video_meta.get("license", "")
    if copyright_info:
        result["metadata_available"]["license"] = copyright_info
    else:
        result["metadata_unavailable"].append("ライセンス情報（メタデータに含まれず）")

    return result


def build_rights_report(video_meta, video_path, channel_url, audio_removed, review_frames_dir):
    """
    素材ごとの権利状態レポートを構築する。

    channel_source_permission: チャンネル所有権
    embedded_footage_rights: 動画内の第三者映像の権利（明確な根拠なし = UNKNOWN）
    metadata_risk_status: メタデータ一次リスク判定
    audio_risk_status: 音声リスク判定
    watermark_status: 透かし状態（フレーム分析なし = UNKNOWN）
    manual_review_required: 荒木側の確認が必要か
    publishable: 最終投稿可否
    """
    permissions = load_source_permissions()

    report = {
        "channel_source_permission": "UNKNOWN",
        "embedded_footage_rights": "UNKNOWN",
        "metadata_risk_status": "UNKNOWN",
        "audio_risk_status": "UNKNOWN",
        "watermark_status": "UNKNOWN",
        "audio_removed": audio_removed,
        "manual_review_required": True,
        "technical_publishable": False,
        "publishable": False,
        "risk_factors": [],
        "metadata_available": {},
        "metadata_unavailable": [],
        "youtube_studio_check_required": [],
        "review_frames_dir": review_frames_dir,
        "review_frames_generated": False,
        "notes": [],
    }

    if channel_url:
        ch_info = permissions.get("channels", {}).get(channel_url, {})
        ptype = ch_info.get("permission_type", "review_required")
        if ptype == "owned":
            report["channel_source_permission"] = "owned"
        else:
            report["channel_source_permission"] = ptype
            report["risk_factors"].append(f"チャンネル権限: {ptype}（自動取得禁止）")
            report["metadata_risk_status"] = "NG"
            return report

    report["embedded_footage_rights"] = "UNKNOWN"
    report["notes"].append(
        "動画内の第三者映像について明確な権利根拠がないため UNKNOWN。"
        "荒木側の確認が必要。"
    )

    meta_risk = metadata_risk_assessment(video_meta)
    report["metadata_risk_status"] = meta_risk["metadata_risk_status"]
    report["audio_risk_status"] = meta_risk["audio_risk_status"]
    report["risk_factors"].extend(meta_risk["risk_factors"])
    report["metadata_available"] = meta_risk["metadata_available"]
    report["metadata_unavailable"] = meta_risk["metadata_unavailable"]
    report["youtube_studio_check_required"] = meta_risk["youtube_studio_check_required"]

    report["watermark_status"] = "UNKNOWN"
    report["notes"].append(
        "透かし・ロゴの判定: メタデータキーワード検索のみ実施。"
        "実映像フレーム分析は未実施のため UNKNOWN。"
        "review_framesフォルダの確認用フレームで目視確認してください。"
    )

    if review_frames_dir and os.path.isdir(review_frames_dir):
        frames = [f for f in os.listdir(review_frames_dir) if f.endswith(".png")]
        report["review_frames_generated"] = len(frames) > 0
        report["review_frames_count"] = len(frames)

    if audio_removed:
        report["notes"].append("元音声はFFmpegで完全除去済み。ただし音声除去は映像自体の権利を解決しない。")

    report["manual_review_required"] = True
    report["publishable"] = False

    return report


def select_segments(video_path, narration_duration, num_segments=3):
    """動画からShortsに使うセグメント位置を自動選定"""
    total_dur = get_video_duration(video_path)
    if not total_dur or total_dur < 5:
        return []

    usable = total_dur - 2
    if usable <= narration_duration:
        return [{"start": 1.0, "duration": min(usable, narration_duration)}]

    seg_dur = narration_duration / num_segments
    segments = []
    available_range = usable - seg_dur

    if available_range <= 0:
        return [{"start": 1.0, "duration": narration_duration}]

    step = available_range / num_segments
    for i in range(num_segments):
        start = 1.0 + i * step
        segments.append({"start": round(start, 2), "duration": round(seg_dur, 2)})

    return segments


def extract_topic_from_video(video_meta, player_aliases):
    """動画メタデータからテーマと選手を推定する"""
    title = video_meta.get("title", "")
    description = video_meta.get("description", "")
    combined = f"{title} {description}"

    detected_player = None
    detected_priority_rank = len(PLAYER_PRIORITY_ORDER) + 1

    for rank, canonical_name in enumerate(PLAYER_PRIORITY_ORDER):
        if canonical_name in combined:
            if rank < detected_priority_rank:
                detected_player = canonical_name
                detected_priority_rank = rank
            continue

        for player_key, info in player_aliases.items():
            p_canonical = info.get("canonical", player_key)
            if p_canonical != canonical_name:
                continue
            variants = info.get("variants", [])
            nicknames = info.get("nicknames", [])
            for name in variants + nicknames:
                if name in combined and rank < detected_priority_rank:
                    detected_player = canonical_name
                    detected_priority_rank = rank
                    break
            break

    if not detected_player:
        detected_player = "NBAスター選手"

    play_patterns = [
        (r"豪快.*ダンク|ダンク.*豪快", "豪快ダンク"),
        (r"ダンク", "ダンク"), (r"ポスタライズ", "ポスタライズダンク"),
        (r"ノールック", "ノールックパス"),
        (r"ブザービーター|ブザービート", "ブザービーター"),
        (r"クラッチ|ゲームウィナー|ゲームウィニング", "クラッチプレー"),
        (r"アシスト", "神アシスト"),
        (r"記録更新|新記録|歴代", "記録更新"),
        (r"アリウープ", "アリウープ"),
        (r"クロスオーバー", "クロスオーバー"),
        (r"ステップバック", "ステップバックシュート"),
        (r"ユーロステップ", "ユーロステップ"),
        (r"ブロック", "ブロック"),
        (r"スティール", "スティール"),
        (r"戦術|ピック", "戦術解説"),
        (r"技術|テクニック", "技術解説"),
    ]
    detected_play = "スーパープレー"
    for pattern, play_name in play_patterns:
        if re.search(pattern, combined):
            detected_play = play_name
            break

    topic = f"{detected_player}の{detected_play}が凄い理由"

    return detected_player, topic


def run_auto_fetch_pipeline(settings, output_dir):
    """
    完全自動取得パイプライン
    荒木側の手動作業: なし

    Returns:
        dict or None
    """
    channel_url = settings.get("channel", {}).get("channel_url", "")
    if not channel_url:
        logger.error("チャンネルURLが設定されていません。config/settings.json の channel.channel_url を設定してください。")
        return None

    player_aliases = load_player_aliases()
    max_videos = settings.get("channel", {}).get("max_fetch_videos", 30)

    logger.info("=" * 50)
    logger.info("自動取得パイプライン開始")
    logger.info(f"チャンネル: {settings.get('channel', {}).get('name', '')}")
    logger.info(f"取得上限: {max_videos}件")
    logger.info("=" * 50)

    logger.info("--- 動画一覧取得中 ---")
    videos = fetch_channel_videos(channel_url, max_videos=max_videos)
    if not videos:
        logger.error("チャンネルから動画を取得できませんでした")
        return None
    logger.info(f"取得完了: {len(videos)}件")

    logger.info("--- 候補選定中 ---")
    candidates = select_candidates(videos, player_aliases, max_candidates=10)
    if not candidates:
        logger.error("候補動画が見つかりませんでした")
        return None

    download_dir = os.path.join(output_dir, "_downloads")
    os.makedirs(download_dir, exist_ok=True)

    skipped = []

    for idx, candidate in enumerate(candidates):
        video_id = candidate.get("id", "")
        video_url = candidate.get("url", "")
        title = candidate.get("title", "")[:60]
        logger.info(f"--- 候補{idx+1}/{len(candidates)}: {title} ---")
        logger.info(f"  スコア: {candidate.get('score', 0)}点")
        logger.info(f"  再生数: {candidate.get('view_count', '不明')}")
        logger.info(f"  尺: {candidate.get('duration', '不明')}秒")

        logger.info("  メタデータ一次リスク判定...")
        meta_risk = metadata_risk_assessment(candidate)
        if meta_risk["metadata_risk_status"] == "NG":
            logger.warning(f"  メタデータ一次リスク判定NG: {meta_risk['risk_factors']}")
            skipped.append({"title": title, "reason": f"メタデータリスクNG: {', '.join(meta_risk['risk_factors'])}"})
            continue

        logger.info("  ダウンロード中...")
        downloaded = download_video(video_url, download_dir, video_id=video_id)
        if not downloaded:
            logger.warning("  ダウンロード失敗")
            skipped.append({"title": title, "reason": "ダウンロード失敗"})
            continue

        logger.info("  確認用フレーム生成中...")
        review_frames_dir = os.path.join(output_dir, "review_frames")
        review_frames = generate_review_frames(downloaded, review_frames_dir)

        logger.info("  元音声除去中...")
        stripped_path = os.path.join(download_dir, f"{video_id}_noaudio.mp4")
        stripped = strip_audio(downloaded, stripped_path)
        audio_removed = stripped is not None
        if not stripped:
            logger.warning("  音声除去失敗")
            stripped = downloaded
            audio_removed = False
        else:
            logger.info("  元音声除去完了")

        logger.info("  9:16 Shorts形式リサイズ中...")
        shorts_path = os.path.join(download_dir, f"{video_id}_shorts.mp4")
        width = settings["video"]["width"]
        height = settings["video"]["height"]
        fps = settings["video"]["fps"]
        resized = scale_to_shorts(stripped, shorts_path, width, height, fps)
        if not resized:
            logger.warning("  リサイズ失敗、音声除去済みファイルを使用")
            resized = stripped

        player, topic = extract_topic_from_video(candidate, player_aliases)

        logger.info(f"  選手推定: {player}")
        logger.info(f"  テーマ推定: {topic}")

        details = fetch_video_details(video_url)

        rights_report = build_rights_report(
            video_meta={**candidate, **(details or {})},
            video_path=downloaded,
            channel_url=channel_url,
            audio_removed=audio_removed,
            review_frames_dir=review_frames_dir,
        )

        with open(os.path.join(output_dir, "rights_report.json"), "w", encoding="utf-8") as f:
            json.dump(rights_report, f, ensure_ascii=False, indent=2)

        with open(os.path.join(output_dir, "skipped_candidates.json"), "w", encoding="utf-8") as f:
            json.dump(skipped, f, ensure_ascii=False, indent=2)

        logger.info("=" * 50)
        logger.info("自動取得パイプライン完了")
        logger.info(f"  選定動画: {candidate.get('title', '')}")
        logger.info(f"  選手: {player}")
        logger.info(f"  テーマ: {topic}")
        logger.info(f"  channel_source_permission: {rights_report['channel_source_permission']}")
        logger.info(f"  embedded_footage_rights: {rights_report['embedded_footage_rights']}")
        logger.info(f"  metadata_risk_status: {rights_report['metadata_risk_status']}")
        logger.info(f"  audio_risk_status: {rights_report['audio_risk_status']}")
        logger.info(f"  watermark_status: {rights_report['watermark_status']}")
        logger.info(f"  audio_removed: {rights_report['audio_removed']}")
        logger.info(f"  manual_review_required: {rights_report['manual_review_required']}")
        logger.info(f"  publishable: {rights_report['publishable']}")
        logger.info(f"  確認用フレーム: {review_frames_dir}")
        logger.info(f"  スキップ: {len(skipped)}件")
        logger.info("=" * 50)

        return {
            "video_path": resized,
            "player": player,
            "topic": topic,
            "video_meta": {**candidate, **(details or {})},
            "rights": rights_report,
            "original_path": downloaded,
            "skipped_candidates": skipped,
            "review_frames_dir": review_frames_dir,
        }

    with open(os.path.join(output_dir, "skipped_candidates.json"), "w", encoding="utf-8") as f:
        json.dump(skipped, f, ensure_ascii=False, indent=2)

    logger.error(f"全{len(candidates)}候補がメタデータ一次リスク判定またはダウンロード失敗で除外")
    for s in skipped:
        logger.error(f"  除外: {s['title']} → {s['reason']}")
    return None
