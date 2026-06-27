"""入力データの読み込みとバリデーション.

topic_input.json の想定構造:

{
  "competitor_channels": [
    {"url": "https://www.youtube.com/@...", "name": "チャンネル名"}
  ],
  "reference_videos": [
    {
      "url": "https://www.youtube.com/watch?v=...",
      "title": "動画タイトル",
      "channel": "チャンネル名",
      "theme": "テーマキーワード",
      "views": 150000,
      "published": "2026-05-01",
      "subscribers_at_publish": 5000,
      "ctr_estimate": 8.5,
      "avg_watch_time_pct": 45,
      "is_shorts": false,
      "drove_long_views": true
    }
  ],
  "own_channel_videos": [
    {
      "url": "https://www.youtube.com/watch?v=...",
      "title": "自チャンネルの動画",
      "views": 5000,
      "published": "2026-04-15",
      "ctr": 6.2,
      "avg_watch_time_pct": 52,
      "repeat_viewers_pct": 30
    }
  ],
  "banned_themes": [
    "皇位継承問題",
    "週刊誌検証"
  ],
  "official_sources": [
    {"url": "https://www.kunaicho.go.jp/...", "name": "宮内庁公式", "type": "宮内庁"},
    {"url": "https://www.youtube.com/@KunijichoJP", "name": "宮内庁YouTube", "type": "公式SNS"}
  ],
  "topic_ideas": [
    {
      "title": "企画タイトル案",
      "center_pin": "このテーマの核",
      "theme_keywords": ["愛子さま", "成年"],
      "official_source_urls": ["https://..."],
      "viewer_reason": "視聴者が見たい理由",
      "long_reason": "長尺化できる理由",
      "shorts_reason": "Shorts化できる理由",
      "expected_emotion": "想定感情",
      "rights_risk": "低",
      "notes": ""
    }
  ]
}
"""

import json
from pathlib import Path


INPUT_SCHEMA_KEYS = {
    "competitor_channels",
    "reference_videos",
    "own_channel_videos",
    "banned_themes",
    "official_sources",
    "topic_ideas",
}


def load_input(path):
    """Load and validate topic_input.json."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    errors = validate_input(data)
    if errors:
        raise ValueError(
            "入力データにエラーがあります:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    return data


def validate_input(data):
    """Return list of validation errors (empty = valid)."""
    errors = []
    if not isinstance(data, dict):
        return ["入力はJSONオブジェクトである必要があります"]

    if "topic_ideas" not in data or not data["topic_ideas"]:
        errors.append("topic_ideas が空です（1件以上の企画案が必要）")

    for i, idea in enumerate(data.get("topic_ideas", [])):
        if not idea.get("title"):
            errors.append(f"topic_ideas[{i}]: title が未設定")
        if not idea.get("center_pin"):
            errors.append(f"topic_ideas[{i}]: center_pin が未設定")

    if "official_sources" not in data or not data["official_sources"]:
        errors.append("official_sources が空です（公式根拠URLが必要）")

    return errors


def extract_themes_from_references(data):
    """参考動画からテーマキーワードを抽出."""
    themes = {}
    for vid in data.get("reference_videos", []):
        theme = vid.get("theme", "")
        if not theme:
            continue
        if theme not in themes:
            themes[theme] = {"count": 0, "total_views": 0, "videos": []}
        themes[theme]["count"] += 1
        themes[theme]["total_views"] += vid.get("views", 0)
        themes[theme]["videos"].append(vid)
    return themes


def compute_reference_demand(vid):
    """参考動画1本の需要指標を0-10で算出."""
    views = vid.get("views", 0)
    subs = vid.get("subscribers_at_publish", 1)
    ctr = vid.get("ctr_estimate", 0)
    watch_pct = vid.get("avg_watch_time_pct", 0)
    drove_long = vid.get("drove_long_views", False)

    view_ratio = min(views / max(subs, 1), 50) / 50
    ctr_norm = min(ctr, 15) / 15
    watch_norm = min(watch_pct, 70) / 70
    long_bonus = 1.0 if drove_long else 0.0

    raw = (view_ratio * 3 + ctr_norm * 3 + watch_norm * 2.5 + long_bonus * 1.5)
    return round(min(raw, 10), 1)
