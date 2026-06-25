"""システム設定"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BGM_DIR = os.path.join(ASSETS_DIR, "bgm")
FONT_DIR = os.path.join(ASSETS_DIR, "fonts")

LONG_VIDEO = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "aspect": "16:9",
    "codec": "libx264",
    "audio_codec": "aac",
}

SHORTS_VIDEO = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "aspect": "9:16",
    "codec": "libx264",
    "audio_codec": "aac",
}

VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
VOICEVOX_SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "3"))

TTS_ENGINE = os.environ.get("TTS_ENGINE", "gtts")

FONT_PATH = None
for candidate in [
    os.path.join(FONT_DIR, "NotoSansJP-Bold.ttf"),
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]:
    if os.path.exists(candidate):
        FONT_PATH = candidate
        break

BGM_VOLUME = 0.20
NARRATION_VOLUME = 1.0
AUDIO_SAMPLE_RATE = 44100
