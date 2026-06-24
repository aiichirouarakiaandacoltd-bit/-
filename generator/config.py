"""Channel and system configuration loader."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_DIR = ROOT / "system" / "config"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_channel_config() -> dict:
    return load_json(CONFIG_DIR / "channel_config.json")


def get_series_config() -> dict:
    return load_json(CONFIG_DIR / "series_config.json")


def get_tone_guide() -> dict:
    return load_json(CONFIG_DIR / "tone_guide.json")


def get_video_dir(video_id: str) -> Path:
    d = ROOT / "videos" / video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_model() -> str:
    return os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
