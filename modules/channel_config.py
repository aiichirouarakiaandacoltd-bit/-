"""
チャンネルプロファイル設定

チャンネルごとに VOICEVOX 設定・BGM ディレクトリ・動画仕様を分離管理する。
設定を混在させず、必ず --channel で指定する。
"""

from pathlib import Path

# プロジェクトルート（このファイルの親の親）
_BASE_DIR = Path(__file__).parent.parent

CHANNEL_PROFILES = {
    "showa_heisei": {
        "name":                   "昭和・平成 なぜそうだったのか",
        "concept":                "昭和・平成の日本人は、なぜそう行動したのかを解説する教養チャンネル",
        # VOICEVOX
        "voicevox_speaker":       13,
        "voicevox_speaker_name":  "青山龍星",
        "voicevox_speed_default": 0.92,
        "voicevox_speed_min":     0.90,
        "voicevox_speed_max":     0.95,
        "voicevox_pitch":         0.0,
        "voicevox_intonation":    1.1,
        "voicevox_volume":        1.0,
        "voicevox_pre_phoneme":   0.15,
        "voicevox_post_phoneme":  0.4,
        "voicevox_pause_scale":   1.3,
        # BGM
        "bgm_subdir":             "showa_heisei",
        "bgm_volume_db":          -28.0,
        "narration_volume_db":    0.0,
        "bgm_fade_in_sec":        2.0,
        "bgm_fade_out_sec":       3.0,
        # 動画仕様
        "video_width":            1920,
        "video_height":           1080,
        "video_fps":              30,
        # 本番尺（秒）
        "target_duration_min":    480,   # 8分
        "target_duration_max":    720,   # 12分
    },
    "imperial": {
        "name":                   "日本が誇る皇室物語",
        "concept":                "皇室の歴史と文化を丁寧に解説する教養チャンネル",
        # VOICEVOX
        "voicevox_speaker":       13,
        "voicevox_speaker_name":  "青山龍星",
        "voicevox_speed_default": 0.87,
        "voicevox_speed_min":     0.85,
        "voicevox_speed_max":     0.90,
        "voicevox_pitch":         0.0,
        "voicevox_intonation":    1.1,
        "voicevox_volume":        1.0,
        "voicevox_pre_phoneme":   0.15,
        "voicevox_post_phoneme":  0.4,
        "voicevox_pause_scale":   1.3,
        # BGM
        "bgm_subdir":             "imperial",
        "bgm_volume_db":          -28.0,
        "narration_volume_db":    0.0,
        "bgm_fade_in_sec":        2.0,
        "bgm_fade_out_sec":       3.0,
        # 動画仕様
        "video_width":            1920,
        "video_height":           1080,
        "video_fps":              30,
        # 本番尺（秒）
        "target_duration_min":    480,
        "target_duration_max":    720,
    },
}


def get_profile(channel: str) -> dict:
    """チャンネルプロファイルを取得する。不明なチャンネル名は ValueError を上げる。"""
    if channel not in CHANNEL_PROFILES:
        valid = "、".join(CHANNEL_PROFILES.keys())
        raise ValueError(
            f"不明なチャンネル: '{channel}'。有効な値: {valid}\n"
            f"例: --channel showa_heisei"
        )
    return CHANNEL_PROFILES[channel].copy()


def get_bgm_dir(channel: str, base_dir: Path = None) -> Path:
    """チャンネル用 BGM ディレクトリの絶対パスを返す。"""
    base = base_dir or _BASE_DIR
    profile = get_profile(channel)
    return base / "assets" / "bgm" / profile["bgm_subdir"]


def find_bgm_file(channel: str, base_dir: Path = None) -> Path | None:
    """チャンネル用 BGM ディレクトリから最初の WAV ファイルを返す。存在しなければ None。"""
    bgm_dir = get_bgm_dir(channel, base_dir)
    if not bgm_dir.exists():
        return None
    wav_files = sorted(bgm_dir.glob("*.wav"))
    return wav_files[0] if wav_files else None


def validate_speed(channel: str, speed: float) -> tuple[bool, str]:
    """
    指定速度がチャンネルの推奨範囲内かを検証する。
    戻り値: (ok: bool, message: str)
    """
    profile = get_profile(channel)
    lo = profile["voicevox_speed_min"]
    hi = profile["voicevox_speed_max"]
    if lo <= speed <= hi:
        return True, ""
    return False, (
        f"速度 {speed} はチャンネル '{channel}' の推奨範囲 {lo}〜{hi} の外です。\n"
        f"推奨速度（デフォルト）: {profile['voicevox_speed_default']}"
    )
