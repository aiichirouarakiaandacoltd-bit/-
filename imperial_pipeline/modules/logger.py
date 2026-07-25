"""実行ログ記録.

- logs/run_YYYYMMDD.log      … 人が読むテキストログ
- logs/run_YYYYMMDD.jsonl    … 機械処理用の1行JSON
- projects/<slug>/_history/  … 上書き前の退避（scaffold.py が使用）

個人情報・認証情報はログへ出さない。エラーは隠さず記録する。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ENC = "utf-8"

# ログへ出力してはならないキー名（値をマスクする）
_MASK_KEYS = {"token", "password", "secret", "api_key", "apikey", "mail", "email"}


def _mask(payload: dict) -> dict:
    masked = {}
    for key, value in payload.items():
        if any(word in key.lower() for word in _MASK_KEYS):
            masked[key] = "<masked>"
        else:
            masked[key] = value
    return masked


class RunLogger:
    """1回の実行に対応するロガー."""

    LEVELS = ("INFO", "WARN", "ERROR", "BLOCK")

    def __init__(self, log_dir: Path, run_id: str | None = None, quiet: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.started_at = datetime.now()
        self.run_id = run_id or self.started_at.strftime("%Y%m%d_%H%M%S")
        stamp = self.started_at.strftime("%Y%m%d")
        self.text_path = self.log_dir / f"run_{stamp}.log"
        self.json_path = self.log_dir / f"run_{stamp}.jsonl"
        self.quiet = quiet
        self.counts = {level: 0 for level in self.LEVELS}

    # -- 基本 ---------------------------------------------------------
    def log(self, level: str, message: str, **payload) -> None:
        level = level.upper()
        if level not in self.LEVELS:
            level = "INFO"
        self.counts[level] += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{now}] [{self.run_id}] [{level}] {message}"
        with self.text_path.open("a", encoding=ENC, newline="") as handle:
            handle.write(line + "\n")
        record = {
            "time": now,
            "run_id": self.run_id,
            "level": level,
            "message": message,
        }
        if payload:
            record.update(_mask(payload))
        with self.json_path.open("a", encoding=ENC, newline="") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        if not self.quiet:
            stream = sys.stderr if level in ("ERROR", "BLOCK") else sys.stdout
            print(line, file=stream)

    def info(self, message: str, **payload) -> None:
        self.log("INFO", message, **payload)

    def warn(self, message: str, **payload) -> None:
        self.log("WARN", message, **payload)

    def error(self, message: str, **payload) -> None:
        self.log("ERROR", message, **payload)

    def block(self, message: str, **payload) -> None:
        """最終パッケージ生成をブロックした理由を記録する."""
        self.log("BLOCK", message, **payload)

    # -- まとめ -------------------------------------------------------
    def section(self, title: str) -> None:
        self.info("=" * 8 + f" {title} " + "=" * 8)

    def summary(self) -> dict:
        elapsed = (datetime.now() - self.started_at).total_seconds()
        result = {
            "run_id": self.run_id,
            "elapsed_seconds": round(elapsed, 2),
            **self.counts,
        }
        self.info("実行サマリー", **result)
        return result
