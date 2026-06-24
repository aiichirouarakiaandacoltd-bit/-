"""
チャンネル設定 / 昭和・平成 なぜそうだったのか
"""

CHANNEL_NAME = "昭和・平成 なぜそうだったのか"
CHANNEL_CONCEPT = "昭和・平成の日本人は、なぜそう行動したのかを解説する教養チャンネル"

CHAPTERS = ["共感", "発見", "考察", "令和比較", "余韻"]

CHAPTER_DURATIONS = {
    "共感":    90,
    "発見":   180,
    "考察":   210,
    "令和比較": 150,
    "余韻":    90,
}

VIDEO_SPEC = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "codec": "libx264",
    "audio_codec": "aac",
    "bitrate": "5000k",
}

NARRATION_SPEED = 240  # chars/minute

FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

CHAPTER_COLORS = {
    "共感":    ((40, 15, 5),   (180, 80, 20)),
    "発見":    ((5, 25, 50),   (20, 100, 180)),
    "考察":    ((15, 10, 40),  (80, 50, 160)),
    "令和比較": ((5, 40, 20),   (20, 140, 60)),
    "余韻":    ((30, 20, 10),  (140, 90, 30)),
}

VOICEVOX_URL = "http://localhost:50021"
VOICEVOX_SPEAKER = 13  # 青山龍星

BGM_VOLUME_DB = -28
NARRATION_VOLUME_DB = 0

SLIDE_DURATION = 4.0   # seconds per image slide
TRANSITION_DURATION = 0.5
