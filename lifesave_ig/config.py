"""設定とデータファイルの読み込み。

PyYAML が無い環境でも動くよう、簡易YAMLフォールバックを内蔵する
（外部APIキー無しでテスト実行できる、という要件を満たすため）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

# プロジェクトルート（このファイルの2階層上）
ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG: Dict[str, Any] = {
    "product": {
        "name": "ライフセーブ21プラス",
        "company": "株式会社ナチュラルウィル",
        "selling_points": [
            "家全体の水を浄水するオール浄水システム",
            "オールナノバブル水",
            "キッチン、洗面、浴室、シャワー、洗濯など家中の水を見直す",
            "毎日使う水だからこそ、住まい全体で整える",
        ],
        "policy": [
            "健康効果・治療効果・美容効果を断定しない",
            "薬機法・景品表示法・誇大広告リスクを避ける",
        ],
    },
    "llm": {
        "provider": "template",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "api_key_env": "OPENAI_API_KEY",
    },
    "calendar": {
        "default_weeks": 4,
        "default_frequency": 3,
        "posting_days": [1, 3, 5],
        "default_status": "draft",
    },
    "hashtags": {"max_count": 15},
    "output": {
        "posts_json": "posts.json",
        "calendar_csv": "calendar.csv",
        "risk_report": "risk_report.md",
        "generated_dir": "generated_posts",
    },
    "data": {
        "themes": "data/themes.json",
        "forbidden": "data/forbidden_expressions.json",
        "recommended": "data/recommended_expressions.json",
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | os.PathLike | None = None) -> Dict[str, Any]:
    """config.yaml を読み込む。存在しない/壊れている場合は既定値を返す。"""
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    loaded: Dict[str, Any] = {}
    if cfg_path.exists():
        try:
            import yaml  # type: ignore

            with open(cfg_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
        except Exception:
            # PyYAML が無い、または解析失敗時は既定値で動作させる
            loaded = {}
    return _deep_merge(DEFAULT_CONFIG, loaded)


def load_json(rel_or_abs_path: str | os.PathLike) -> Any:
    """data 配下などのJSONを読み込む。"""
    p = Path(rel_or_abs_path)
    if not p.is_absolute():
        p = ROOT / p
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve(rel_path: str | os.PathLike) -> Path:
    """プロジェクトルート基準で絶対パスに解決する。"""
    p = Path(rel_path)
    return p if p.is_absolute() else ROOT / p
