"""BGM configuration management."""
import json
from pathlib import Path

import config as cfg


def load_bgm_config():
    """Load BGM settings from config file or use defaults."""
    defaults = {
        "file_name": "UNL1337.wav",
        "title": None,
        "provider": "箕輪レコーズ",
        "download_or_reference_url": None,
        "license_status": "licensed",
        "commercial_use": True,
        "youtube_monetization": True,
        "credit_text": "楽曲提供：箕輪レコーズ",
        "usage_note": "別BGMへの変更禁止。実際に使用した場合のみクレジットを記載",
        "missing_items": [],
    }

    config_path = cfg.BGM_CONFIG_PATH
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                custom = json.load(f)
            if isinstance(custom, dict) and "bgm" in custom:
                custom = custom["bgm"]
            for k, v in custom.items():
                if v is not None:
                    defaults[k] = v
        except (json.JSONDecodeError, KeyError):
            pass

    if not defaults.get("download_or_reference_url"):
        defaults["missing_items"] = ["箕輪レコーズBGMの正式な取得・確認URL"]

    return defaults


def generate_bgm_and_credits(bgm_config, output_dir):
    """Generate 06_bgm_and_credits.md."""
    output_dir = Path(output_dir)
    lines = []
    lines.append("# BGM・クレジット設定")
    lines.append("")
    lines.append("## BGM指定")
    lines.append("")
    lines.append(f"- ファイル名: {bgm_config.get('file_name', 'UNL1337.wav')}")
    lines.append(f"- 提供元: {bgm_config.get('provider', '箕輪レコーズ')}")

    title = bgm_config.get("title")
    if title:
        lines.append(f"- 楽曲タイトル: {title}")
    else:
        lines.append("- 楽曲タイトル: 未設定")

    url = bgm_config.get("download_or_reference_url")
    if url:
        lines.append(f"- 取得・確認URL: {url}")
    else:
        lines.append("- 取得・確認URL: **未設定（荒木側で設定が必要）**")

    lines.append(f"- ライセンス: {bgm_config.get('license_status', '要確認')}")
    lines.append(f"- 商用利用: {'可' if bgm_config.get('commercial_use') else '要確認'}")
    lines.append(f"- YouTube収益化: {'可' if bgm_config.get('youtube_monetization') else '要確認'}")
    lines.append("")
    lines.append("## 使用ルール")
    lines.append("")
    lines.append("- 別BGMへの変更は禁止")
    lines.append("- 実際に使用した場合のみクレジットを記載")
    lines.append(f"- クレジット表記: {bgm_config.get('credit_text', '楽曲提供：箕輪レコーズ')}")
    lines.append("")

    missing = bgm_config.get("missing_items", [])
    if missing:
        lines.append("## 荒木側で確認が必要な項目")
        lines.append("")
        for item in missing:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## BGM設定JSON")
    lines.append("")
    lines.append("```json")
    json_out = {k: v for k, v in bgm_config.items()}
    lines.append(json.dumps(json_out, ensure_ascii=False, indent=2))
    lines.append("```")

    content = "\n".join(lines)
    (output_dir / "06_bgm_and_credits.md").write_text(content, encoding="utf-8")
    return bgm_config
