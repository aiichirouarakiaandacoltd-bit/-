"""動画製作 共通設定"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = ROOT / "assets"
BGM_DIR = ASSETS_DIR / "bgm"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUTS_DIR = ROOT / "outputs" / "videos"
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data" / "processed"

VIDEO_LONG = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "duration_min": 480,
    "duration_max": 720,
    "format": "long",
}

VIDEO_SHORTS = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration_min": 45,
    "duration_max": 60,
    "format": "shorts",
}

VOICEVOX_SPEAKER_ID = 13  # 青山龍星
VOICEVOX_SPEAKER_NAME = "青山龍星"
VOICEVOX_SPEED = 0.88
VOICEVOX_HOST = "http://127.0.0.1:50021"

BGM_FILE = "UNL1337.wav"
BGM_CREDIT = "楽曲提供：箕輪レコーズ"
BGM_VOLUME = 0.08

CHANNEL_NAME = "日本が誇る皇室物語"

SUBTITLE_MAX_LINES = 2
SUBTITLE_MAX_CHARS_PER_LINE = 20
SUBTITLE_FONT_SIZE_LONG = 42
SUBTITLE_FONT_SIZE_SHORTS = 36
SUBTITLE_FONT_COLOR = "white"
SUBTITLE_BG_COLOR = (0, 0, 0, 180)
SUBTITLE_MARGIN_V_LONG = 60
SUBTITLE_MARGIN_V_SHORTS = 320
SUBTITLE_POSITION_LONG = ("center", 0.85)
SUBTITLE_POSITION_SHORTS = ("center", 0.55)

ENCODING = {
    "vcodec": "libx264",
    "acodec": "aac",
    "video_bitrate": "4M",
    "audio_bitrate": "192k",
    "audio_sample_rate": 44100,
    "audio_channels": 2,
    "preset": "medium",
    "crf": 20,
}

FORBIDDEN_EXPRESSIONS = [
    "衝撃", "激震", "世界が絶賛", "日本中が涙", "神対応",
    "皇室崩壊", "皇室の闇", "暴露", "スクープ", "極秘情報",
    "ヤバい", "ヤバすぎる", "炎上", "崩壊",
]

RIGHTS_STATUS = {
    "OK": "使用可",
    "REVIEW": "確認中",
    "NG": "使用不可",
}

MATERIAL_FIELDS = [
    "image_path", "source_name", "source_url",
    "rights_status", "image_type", "credit_required", "credit_text",
]
