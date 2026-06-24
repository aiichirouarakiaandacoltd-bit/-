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

# VOICEVOX 詳細設定（create_video.py --voicevox-speed 等でも上書き可）
VOICEVOX_SPEED_SCALE = 0.87        # 話速（0.85〜0.90 推奨）
VOICEVOX_PITCH_SCALE = 0.0         # ピッチ（-0.15〜0.15）
VOICEVOX_INTONATION_SCALE = 1.1    # 抑揚（0.0〜2.0）
VOICEVOX_VOLUME_SCALE = 1.0        # 音量スケール（0.0〜2.0）
VOICEVOX_PRE_PHONEME_LENGTH = 0.15 # 開始前無音（秒）
VOICEVOX_POST_PHONEME_LENGTH = 0.4  # 終了後無音（秒）
VOICEVOX_PAUSE_LENGTH_SCALE = 1.3  # 句読点ポーズ倍率（0.0〜10.0）

# BGM・ナレーション音量設定
BGM_VOLUME_DB = -28.0              # BGM音量（dB）
NARRATION_VOLUME_DB = 0.0          # ナレーション音量（dB、0=原音）
BGM_FADE_IN_SEC = 2.0              # BGMフェードイン（秒）
BGM_FADE_OUT_SEC = 3.0             # BGMフェードアウト（秒）

# 本番品質チェック
# True = VOICEVOXに接続できない場合はエラー停止（代替音声への無断切替を禁止）
REQUIRE_VOICEVOX = True
# True = BGMファイルが存在しない場合はエラー停止
REQUIRE_BGM = True

SLIDE_DURATION = 4.0   # seconds per image slide
TRANSITION_DURATION = 0.5
