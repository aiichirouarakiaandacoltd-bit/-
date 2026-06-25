"""Central configuration for imperial-video-automation."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Directories
ASSETS_DIR = PROJECT_ROOT / "assets"
BGM_DIR = ASSETS_DIR / "bgm"
IMAGES_DIR = ASSETS_DIR / "images"
INPUT_DIR = PROJECT_ROOT / "input"
INPUT_IMAGES_DIR = INPUT_DIR / "images"
INPUT_SCRIPTS_DIR = INPUT_DIR / "scripts"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_LONG_DIR = OUTPUT_DIR / "long"
OUTPUT_SHORTS_DIR = OUTPUT_DIR / "shorts"
OUTPUT_TEST_DIR = OUTPUT_DIR / "test"
LOGS_DIR = PROJECT_ROOT / "logs"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

# BGM
BGM_FILE = BGM_DIR / "UNL1337.wav"
BGM_CREDIT = "楽曲提供：箕輪レコーズ"

# VOICEVOX
VOICEVOX_HOST = os.environ.get("VOICEVOX_HOST", "http://localhost:50021")
VOICEVOX_SPEAKER_NAME = "青山龍星"
VOICEVOX_SPEED = 0.88

# Video specs - Long
LONG_WIDTH = 1920
LONG_HEIGHT = 1080
LONG_FPS = 30
LONG_MIN_DURATION = 480
LONG_MAX_DURATION = 720

# Video specs - Shorts
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
SHORTS_FPS = 30
SHORTS_MIN_DURATION = 45
SHORTS_MAX_DURATION = 59.5

# Font
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FALLBACK_FONTS = [
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]

# Channel
CHANNEL_NAME = "日本が誇る皇室物語"
