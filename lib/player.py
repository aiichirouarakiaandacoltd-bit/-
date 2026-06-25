import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_aliases():
    path = os.path.join(BASE_DIR, "config", "player_aliases.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["aliases"]

def normalize_player_name(raw_name):
    aliases = load_aliases()
    for canonical, info in aliases.items():
        if raw_name == canonical:
            return canonical
        if raw_name in info.get("variants", []):
            return canonical
        if raw_name == info.get("nickname", ""):
            return canonical
    return raw_name

def get_player_info(name):
    canonical = normalize_player_name(name)
    aliases = load_aliases()
    return aliases.get(canonical)

def get_nickname(name):
    info = get_player_info(name)
    if info:
        return info.get("nickname", name)
    return name
