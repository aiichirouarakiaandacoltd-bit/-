"""リスクチェック（薬機法・景品表示法・誇大広告）。

禁止表現データ（forbidden_expressions.json）を正規表現で照合し、
ヒットした表現・理由・代替表現を返す。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from . import config


@dataclass
class RiskHit:
    rule_id: str
    matched_text: str
    pattern: str
    category: str
    reason: str
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "matched_text": self.matched_text,
            "category": self.category,
            "reason": self.reason,
            "alternatives": self.alternatives,
        }


@dataclass
class RiskResult:
    ok: bool
    hits: List[RiskHit] = field(default_factory=list)

    @property
    def level(self) -> str:
        return "ok" if self.ok else "warning"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "level": self.level,
            "hit_count": len(self.hits),
            "hits": [h.to_dict() for h in self.hits],
        }


class RiskChecker:
    def __init__(self, cfg: Dict[str, Any] | None = None):
        self.cfg = cfg or config.load_config()
        data = config.load_json(self.cfg["data"]["forbidden"])
        self.categories: Dict[str, str] = data.get("categories", {})
        self._rules: List[Dict[str, Any]] = data.get("rules", [])
        # 事前コンパイル
        for r in self._rules:
            r["_re"] = re.compile(r["pattern"], re.IGNORECASE)

    def check(self, text: str) -> RiskResult:
        if not text:
            return RiskResult(ok=True, hits=[])
        hits: List[RiskHit] = []
        for r in self._rules:
            for m in r["_re"].finditer(text):
                hits.append(
                    RiskHit(
                        rule_id=r["id"],
                        matched_text=m.group(0),
                        pattern=r["pattern"],
                        category=r.get("category", ""),
                        reason=r.get("reason", ""),
                        alternatives=r.get("alternatives", []),
                    )
                )
        return RiskResult(ok=len(hits) == 0, hits=hits)

    def check_many(self, texts: List[str]) -> RiskResult:
        """複数テキストをまとめてチェックする（重複ヒットはまとめる）。"""
        all_hits: List[RiskHit] = []
        seen = set()
        for t in texts:
            for h in self.check(t).hits:
                key = (h.rule_id, h.matched_text)
                if key not in seen:
                    seen.add(key)
                    all_hits.append(h)
        return RiskResult(ok=len(all_hits) == 0, hits=all_hits)


def category_label(checker: RiskChecker, category: str) -> str:
    return checker.categories.get(category, category)
