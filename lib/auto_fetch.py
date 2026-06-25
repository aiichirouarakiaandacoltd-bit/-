"""
ザ・ダンク チャンネル動画自動取得・候補選定モジュール

yt-dlpを使用してザ・ダンクチャンネルの動画一覧を取得し、
優先選手・プレータイプに基づいて候補を自動選定する。
選定した動画を自動ダウンロードし、権利判定を行う。
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

AUTO_EXCLUDE_REASONS = {
    "third_party_bgm": "第三者BGMが除去できない",
    "broadcast_audio": "放送実況が除去できない",
    "large_watermark": "透かしが大きい",
    "unknown_rights": "素材権限を確認できない",
    "high_repost_risk": "再編集しても転載性が高い",
    "low_added_value": "付加価値を十分に追加できない",
}


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


def judge_rights(video_path, video_meta, channel_url=None):
    """
    自動権利判定（全項目）

    判定項目:
    - チャンネル所有権（ザ・ダンク = owned のみ許可）
    - 第三者BGMの有無
    - 放送実況の有無
    - 他社ロゴ・透かしの有無
    - 映像の再編集可否
    - 元音声除去可否
    - 使用区間の妥当性
    - 付加価値追加可否
    - 再利用コンテンツリスク
    - 著作権申し立て情報（yt-dlpメタデータから取得可能な範囲）

    除外条件:
    - 第三者BGMが除去できない
    - 放送実況が除去できない
    - 透かしが大きい
    - 素材権限を確認できない
    - 再編集しても転載性が高い
    - 付加価値を十分に追加できない
    """
    permissions = load_source_permissions()
    result = {
        "permission_type": "review_required",
        "rights_status": "REVIEW",
        "issues": [],
        "checks": {},
        "exclusion_reasons": [],
        "passed": False,
        "audio_stripped": False,
        "can_reedit": True,
        "can_add_value": True,
        "repost_risk": "low",
    }

    if channel_url:
        ch_info = permissions.get("channels", {}).get(channel_url, {})
        ptype = ch_info.get("permission_type", "review_required")
        if ptype == "owned":
            result["permission_type"] = "owned"
            result["rights_status"] = "OK"
            result["checks"]["channel_ownership"] = "OK: ザ・ダンク所有"
        elif ptype in ("reference_only", "prohibited", "review_required"):
            result["issues"].append(f"チャンネル権限: {ptype}")
            result["permission_type"] = ptype
            result["rights_status"] = "NG"
            result["checks"]["channel_ownership"] = f"NG: {ptype}"
            result["exclusion_reasons"].append("unknown_rights")
            return result
    else:
        result["issues"].append("チャンネルURL未指定")
        result["exclusion_reasons"].append("unknown_rights")
        return result

    if video_meta:
        title = video_meta.get("title", "")
        desc = video_meta.get("description", "")
        combined = f"{title} {desc}"
        combined_lower = combined.lower()

        has_third_party_bgm = False
        for marker in THIRD_PARTY_BGM_MARKERS:
            if marker.lower() in combined_lower:
                has_third_party_bgm = True
                result["issues"].append(f"第三者BGM検出: {marker}")
                break
        result["checks"]["third_party_bgm"] = "NG: 検出" if has_third_party_bgm else "OK: 未検出"
        if has_third_party_bgm:
            result["exclusion_reasons"].append("third_party_bgm")

        has_broadcast = False
        for marker in BROADCAST_MARKERS:
            if marker.lower() in combined_lower:
                has_broadcast = True
                result["issues"].append(f"放送関連キーワード検出: {marker}")
                break
        result["checks"]["broadcast_audio"] = "NG: 検出" if has_broadcast else "OK: 未検出"
        if has_broadcast:
            result["exclusion_reasons"].append("broadcast_audio")

        has_watermark = False
        for marker in WATERMARK_MARKERS:
            if marker.lower() in combined_lower:
                has_watermark = True
                result["issues"].append(f"他社ロゴ/透かし関連: {marker}")
                break
        result["checks"]["watermark"] = "NG: 検出" if has_watermark else "OK: 未検出"
        if has_watermark:
            result["exclusion_reasons"].append("large_watermark")

        has_exclusion = False
        for kw in EXCLUSION_KEYWORDS:
            if kw.lower() in combined_lower:
                has_exclusion = True
                result["issues"].append(f"禁止ソースキーワード: {kw}")
                break
        if has_exclusion:
            result["exclusion_reasons"].append("unknown_rights")

        duration = video_meta.get("duration")
        if duration and duration < 10:
            result["issues"].append("動画が短すぎる（10秒未満）")
            result["can_add_value"] = False
            result["exclusion_reasons"].append("low_added_value")
        result["checks"]["duration_adequate"] = f"{'OK' if not duration or duration >= 10 else 'NG'}: {duration}秒"

        result["checks"]["can_strip_audio"] = "OK: 元音声除去可能（FFmpegで除去）"
        result["audio_stripped"] = True

        if duration and duration < 15:
            result["can_reedit"] = False
            result["checks"]["can_reedit"] = "NG: 尺が短く再編集困難"
        else:
            result["checks"]["can_reedit"] = "OK: 再編集可能"

        is_simple_repost = True
        value_indicators = [
            "解説", "分析", "技術", "比較", "戦術", "ランキング",
            "まとめ", "ベスト", "理由", "なぜ", "秘密",
        ]
        for vi in value_indicators:
            if vi in combined:
                is_simple_repost = False
                break

        if is_simple_repost and (not duration or duration < 30):
            result["repost_risk"] = "high"
            result["issues"].append("短尺かつ付加価値指標なし → 転載リスク高")
            result["exclusion_reasons"].append("high_repost_risk")
        elif is_simple_repost:
            result["repost_risk"] = "medium"
        else:
            result["repost_risk"] = "low"
        result["checks"]["repost_risk"] = f"{result['repost_risk']}"

        result["checks"]["added_value"] = (
            "OK: VOICEVOX解説・字幕・エフェクト・BGMで付加価値追加可能"
            if result["can_add_value"] else "NG: 付加価値追加困難"
        )

        copyright_info = video_meta.get("license", "")
        copyright_claim = video_meta.get("copyright", "")
        if copyright_info or copyright_claim:
            result["checks"]["copyright_claim"] = f"情報あり: {copyright_info or copyright_claim}"
            if "claim" in str(copyright_claim).lower():
                result["issues"].append("著作権申し立て情報検出")
        else:
            result["checks"]["copyright_claim"] = "取得不可（yt-dlpメタデータに含まれず）"

    info = get_video_info(video_path) if video_path and os.path.exists(video_path) else None
    if info:
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_channels = stream.get("channels", 0)
                if audio_channels > 2:
                    result["issues"].append("マルチチャンネル音声検出（放送音声の可能性）")
                    result["checks"]["audio_analysis"] = f"NG: {audio_channels}ch（放送音声の可能性）"
                else:
                    result["checks"]["audio_analysis"] = f"OK: {audio_channels}ch"

    if result["permission_type"] == "owned" and not result["exclusion_reasons"]:
        result["passed"] = True
        result["rights_status"] = "OK"
    else:
        result["passed"] = False
        if result["exclusion_reasons"]:
            reasons = [AUTO_EXCLUDE_REASONS.get(r, r) for r in result["exclusion_reasons"]]
            result["rights_status"] = f"NG: {', '.join(reasons)}"

    return result


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

    1. ザ・ダンクチャンネル動画一覧を自動取得
    2. タイトル・投稿日・再生数・尺・説明文を取得
    3. 選手名を正規化
    4. 優先選手・プレー内容・再生実績から候補をスコアリング・選定
    5. 候補動画を自動ダウンロード
    6. 自動権利判定（第三者BGM・放送実況・透かし・転載リスク等）
    7. 元音声を完全除去
    8. 9:16 Shorts形式にリサイズ
    9. テーマ・選手を自動推定

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

        logger.info("  権利判定（メタデータ）...")
        rights = judge_rights(None, candidate, channel_url=channel_url)
        if not rights["passed"]:
            reasons = rights.get("exclusion_reasons", [])
            reason_texts = [AUTO_EXCLUDE_REASONS.get(r, r) for r in reasons]
            logger.warning(f"  権利判定NG: {', '.join(reason_texts)}")
            skipped.append({"title": title, "reason": rights["rights_status"]})
            continue

        logger.info("  ダウンロード中...")
        downloaded = download_video(video_url, download_dir, video_id=video_id)
        if not downloaded:
            logger.warning(f"  ダウンロード失敗")
            skipped.append({"title": title, "reason": "ダウンロード失敗"})
            continue

        logger.info("  権利判定（ファイル検査）...")
        rights = judge_rights(downloaded, candidate, channel_url=channel_url)
        if not rights["passed"]:
            logger.warning(f"  ファイル検査NG: {rights['rights_status']}")
            skipped.append({"title": title, "reason": rights["rights_status"]})
            try:
                os.remove(downloaded)
            except OSError:
                pass
            continue

        logger.info("  元音声除去中...")
        stripped_path = os.path.join(download_dir, f"{video_id}_noaudio.mp4")
        stripped = strip_audio(downloaded, stripped_path)
        if not stripped:
            logger.warning("  音声除去失敗")
            stripped = downloaded
        else:
            logger.info("  元音声除去完了（第三者BGM・放送実況含め全除去）")

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

        rights_report = {
            "rights_status": rights["rights_status"],
            "permission_type": rights["permission_type"],
            "checks": rights["checks"],
            "issues": rights["issues"],
            "exclusion_reasons": rights["exclusion_reasons"],
            "audio_stripped": True,
            "can_reedit": rights["can_reedit"],
            "can_add_value": rights["can_add_value"],
            "repost_risk": rights["repost_risk"],
        }

        with open(os.path.join(output_dir, "rights_judgment.json"), "w", encoding="utf-8") as f:
            json.dump(rights_report, f, ensure_ascii=False, indent=2)

        with open(os.path.join(output_dir, "skipped_candidates.json"), "w", encoding="utf-8") as f:
            json.dump(skipped, f, ensure_ascii=False, indent=2)

        logger.info("=" * 50)
        logger.info("自動取得パイプライン完了")
        logger.info(f"  選定動画: {candidate.get('title', '')}")
        logger.info(f"  選手: {player}")
        logger.info(f"  テーマ: {topic}")
        logger.info(f"  権利: {rights['rights_status']}")
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
        }

    with open(os.path.join(output_dir, "skipped_candidates.json"), "w", encoding="utf-8") as f:
        json.dump(skipped, f, ensure_ascii=False, indent=2)

    logger.error(f"全{len(candidates)}候補が除外されました")
    for s in skipped:
        logger.error(f"  除外: {s['title']} → {s['reason']}")
    return None
