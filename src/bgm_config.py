"""BGM configuration management — search-criteria-based design.

BGM selection is driven by bgm_config.json, not hardcoded.
To change the BGM track, edit bgm_config.json — no code changes required.
"""
import json
from pathlib import Path

import config as cfg


def load_bgm_config():
    """Load BGM settings from bgm_config.json.

    Supports two formats:
    - Legacy flat: {"file_name": "...", "provider": "...", ...}
    - Search-based: {"search_criteria": {...}, "selected": {...}, "candidates": [...]}
    """
    config_path = cfg.BGM_CONFIG_PATH

    defaults = {
        "file_name": cfg.BGM_SETTINGS["file_name"],
        "title": None,
        "provider": cfg.BGM_SETTINGS["provider"],
        "download_or_reference_url": None,
        "license_status": "licensed",
        "commercial_use": True,
        "youtube_monetization": True,
        "credit_required": True,
        "credit_text": cfg.BGM_SETTINGS["credit_text"],
        "usage_note": "別BGMへの変更禁止。実際に使用した場合のみクレジットを記載",
        "missing_items": [],
    }

    if not config_path.exists():
        defaults["missing_items"] = ["bgm_config.jsonが未作成"]
        return defaults

    try:
        with open(config_path, encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        defaults["missing_items"] = ["bgm_config.jsonの読み込みエラー"]
        return defaults

    if "selected" in raw and isinstance(raw["selected"], dict):
        return _load_search_based(raw)

    if isinstance(raw, dict) and "bgm" in raw:
        raw = raw["bgm"]
    for k, v in raw.items():
        if v is not None:
            defaults[k] = v

    if not defaults.get("download_or_reference_url"):
        defaults["missing_items"] = ["BGMの正式な取得・確認URL"]

    return defaults


def _load_search_based(raw):
    """Parse search-criteria-based config into the standard dict."""
    selected = raw["selected"]
    criteria = raw.get("search_criteria", {})
    candidates = raw.get("candidates", [])

    missing = []
    if not selected.get("download_or_reference_url"):
        missing.append("BGMの取得・確認URL")
    if not selected.get("title"):
        missing.append("BGM楽曲タイトル")
    if selected.get("commercial_use") is not True:
        missing.append("商用利用可の確認")
    if selected.get("youtube_monetization") is not True:
        missing.append("YouTube収益化可の確認")

    return {
        "file_name": selected.get("file_name", ""),
        "title": selected.get("title"),
        "provider": selected.get("provider", ""),
        "composer": selected.get("composer", ""),
        "download_or_reference_url": selected.get("download_or_reference_url"),
        "license_status": selected.get("license_status", "unknown"),
        "license_url": selected.get("license_url"),
        "commercial_use": selected.get("commercial_use", False),
        "youtube_monetization": selected.get("youtube_monetization", False),
        "content_id_risk": selected.get("content_id_risk", "unknown"),
        "credit_required": selected.get("credit_required", True),
        "credit_text": selected.get("credit_text", ""),
        "usage_note": selected.get("usage_note", ""),
        "duration_seconds": selected.get("duration_seconds"),
        "vocals": selected.get("vocals", False),
        "missing_items": missing,
        "_search_criteria": criteria,
        "_candidates": candidates,
        "_channel": raw.get("channel", ""),
    }


def generate_bgm_and_credits(bgm_config, output_dir):
    """Generate 06_bgm_and_credits.md."""
    output_dir = Path(output_dir)
    lines = []
    lines.append("# BGM・クレジット設定")
    lines.append("")
    lines.append("## BGM指定")
    lines.append("")

    title = bgm_config.get("title")
    if title:
        lines.append(f"- 楽曲タイトル: {title}")
    else:
        lines.append("- 楽曲タイトル: 未設定")

    composer = bgm_config.get("composer")
    if composer:
        lines.append(f"- 作曲者: {composer}")

    lines.append(f"- 提供元: {bgm_config.get('provider', '未設定')}")

    file_name = bgm_config.get("file_name")
    if file_name:
        lines.append(f"- ファイル名: {file_name}")

    url = bgm_config.get("download_or_reference_url")
    if url:
        lines.append(f"- 取得・確認URL: {url}")
    else:
        lines.append("- 取得・確認URL: **未設定（荒木側で設定が必要）**")

    lines.append(f"- ライセンス: {bgm_config.get('license_status', '要確認')}")
    lines.append(f"- 商用利用: {'可' if bgm_config.get('commercial_use') else '要確認'}")
    lines.append(f"- YouTube収益化: {'可' if bgm_config.get('youtube_monetization') else '要確認'}")
    lines.append(f"- Content IDリスク: {bgm_config.get('content_id_risk', '要確認')}")

    credit_req = bgm_config.get("credit_required")
    if credit_req is False:
        lines.append("- クレジット表記: 任意（推奨）")
    else:
        lines.append("- クレジット表記: 必須")

    lines.append("")
    lines.append("## 使用ルール")
    lines.append("")
    usage = bgm_config.get("usage_note", "")
    if usage:
        lines.append(f"- {usage}")
    lines.append("- 別BGMへの変更は禁止")
    lines.append("- 実際に使用した場合のみクレジットを記載")
    lines.append(f"- クレジット表記: {bgm_config.get('credit_text', '要設定')}")
    lines.append("")

    missing = bgm_config.get("missing_items", [])
    if missing:
        lines.append("## 荒木側で確認が必要な項目")
        lines.append("")
        for item in missing:
            lines.append(f"- {item}")
        lines.append("")

    safe_config = {k: v for k, v in bgm_config.items() if not k.startswith("_")}
    lines.append("## BGM設定JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(safe_config, ensure_ascii=False, indent=2))
    lines.append("```")

    content = "\n".join(lines)
    (output_dir / "06_bgm_and_credits.md").write_text(content, encoding="utf-8")
    return bgm_config


def generate_bgm_plan(bgm_config, output_dir):
    """Generate 08_bgm_plan.md with search criteria, candidates, and selection details."""
    output_dir = Path(output_dir)
    lines = []
    lines.append("# BGM選定プラン")
    lines.append("")

    channel = bgm_config.get("_channel", "")
    if channel:
        lines.append(f"## 対象チャンネル")
        lines.append(f"{channel}")
        lines.append("")

    criteria = bgm_config.get("_search_criteria", {})
    if criteria:
        lines.append("## 検索条件")
        lines.append("")
        genre = criteria.get("genre", [])
        if genre:
            lines.append(f"- ジャンル: {', '.join(genre)}")
        mood = criteria.get("mood", [])
        if mood:
            lines.append(f"- ムード: {', '.join(mood)}")
        bpm_min = criteria.get("bpm_min")
        bpm_max = criteria.get("bpm_max")
        if bpm_min and bpm_max:
            lines.append(f"- BPM範囲: {bpm_min}〜{bpm_max}")
        if criteria.get("vocals") is False:
            lines.append("- ボーカル: なし（インストのみ）")
        if criteria.get("loopable"):
            lines.append("- ループ再生: 可")
        if criteria.get("commercial_use_required"):
            lines.append("- 商用利用: 必須")
        if criteria.get("youtube_monetization_required"):
            lines.append("- YouTube収益化: 必須")
        sources = criteria.get("priority_sources", [])
        if sources:
            lines.append(f"- 検索ソース: {', '.join(sources)}")
        lines.append("")

    lines.append("## 採用BGM")
    lines.append("")
    title = bgm_config.get("title", "未選定")
    composer = bgm_config.get("composer", "")
    provider = bgm_config.get("provider", "")
    lines.append(f"- 楽曲名: {title}")
    if composer:
        lines.append(f"- 作曲者: {composer}")
    lines.append(f"- 提供元: {provider}")
    url = bgm_config.get("download_or_reference_url")
    if url:
        lines.append(f"- URL: {url}")
    lines.append(f"- ライセンス: {bgm_config.get('license_status', '要確認')}")
    license_url = bgm_config.get("license_url")
    if license_url:
        lines.append(f"- ライセンス詳細: {license_url}")
    lines.append(f"- 商用利用: {'可' if bgm_config.get('commercial_use') else '不可/要確認'}")
    lines.append(f"- YouTube収益化: {'可' if bgm_config.get('youtube_monetization') else '不可/要確認'}")
    lines.append(f"- Content IDリスク: {bgm_config.get('content_id_risk', '要確認')}")

    credit_req = bgm_config.get("credit_required")
    if credit_req is False:
        lines.append("- クレジット: 任意（推奨）")
    else:
        lines.append("- クレジット: 必須")

    lines.append(f"- クレジット表記: {bgm_config.get('credit_text', '要設定')}")
    dur = bgm_config.get("duration_seconds")
    if dur:
        mins, secs = divmod(dur, 60)
        lines.append(f"- 再生時間: {int(mins)}:{int(secs):02d}")
    lines.append("")

    candidates = bgm_config.get("_candidates", [])
    if candidates:
        lines.append("## 候補一覧")
        lines.append("")
        for i, c in enumerate(candidates, 1):
            status_label = {"adopted": "採用", "alternative": "代替候補"}.get(
                c.get("status", ""), c.get("status", "")
            )
            lines.append(f"### {i}. {c.get('title', '不明')} [{status_label}]")
            if c.get("composer"):
                lines.append(f"- 作曲者: {c['composer']}")
            if c.get("provider"):
                lines.append(f"- 提供元: {c['provider']}")
            if c.get("url"):
                lines.append(f"- URL: {c['url']}")
            if c.get("genre"):
                lines.append(f"- ジャンル: {c['genre']}")
            if c.get("bpm"):
                lines.append(f"- BPM: {c['bpm']}")
            if c.get("duration"):
                lines.append(f"- 再生時間: {c['duration']}")
            if c.get("reason"):
                lines.append(f"- 選定理由: {c['reason']}")
            lines.append("")

    lines.append("## BGM変更手順")
    lines.append("")
    lines.append("BGMを変更する場合は `bgm_config.json` の `selected` セクションを編集してください。")
    lines.append("コードの変更は不要です。")
    lines.append("")
    lines.append("```")
    lines.append('1. bgm_config.json の "selected" を新しいBGM情報に書き換え')
    lines.append('2. "candidates" に新しい候補を追加（任意）')
    lines.append("3. python main.py --theme <テーマ> --mode test で動作確認")
    lines.append("4. production_ready=true を確認後、本番実行")
    lines.append("```")

    content = "\n".join(lines)
    (output_dir / "08_bgm_plan.md").write_text(content, encoding="utf-8")
    return content
