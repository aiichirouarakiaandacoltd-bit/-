"""既存動画との重複の機械参考判定（工程2の補助）.

外部APIを使わず、文字N-gramの一致率で類似度を出すだけの参考値である。
最終判定は imperial-researcher と荒木愛一朗が行う。

past_videos.csv が無い場合は「判定不能（過去動画データ未提供）」を返し、
処理は停止しない（第6章）。
"""

from __future__ import annotations

import re
from pathlib import Path

from . import id_assigner

# 類似度の閾値（参考値）
THRESHOLD_HIGH = 0.60    # 大幅重複の疑い
THRESHOLD_MID = 0.35     # 一部重複の疑い

_NOISE = re.compile(r"[\s　、。，．,\.・！？!?「」『』（）\(\)\[\]【】〜\-—…:：;；\"']")


def _normalize(text: str) -> str:
    return _NOISE.sub("", str(text or ""))


def _bigrams(text: str) -> set[str]:
    text = _normalize(text)
    if len(text) < 2:
        return {text} if text else set()
    return {text[i:i + 2] for i in range(len(text) - 1)}


def similarity(left: str, right: str) -> float:
    """Dice係数（0.0〜1.0）."""
    a, b = _bigrams(left), _bigrams(right)
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def check(past_videos_csv: Path, theme: str, working_title: str,
          main_person: str) -> dict:
    path = Path(past_videos_csv)
    if not path.exists():
        return {
            "status": "判定不能（過去動画データ未提供）",
            "available": False,
            "matches": [],
            "max_score": 0.0,
            "note": f"{path.name} が存在しないため、機械判定を行わなかった。",
        }

    rows = id_assigner.read_csv_rows(path)
    if not rows:
        return {
            "status": "判定不能（過去動画データが空）",
            "available": True,
            "matches": [],
            "max_score": 0.0,
            "note": f"{path.name} にデータ行がない。",
        }

    query_theme = f"{theme} {working_title}".strip()
    matches = []
    for row in rows:
        title = row.get("タイトル") or ""
        past_theme = row.get("テーマ") or ""
        person = row.get("主要人物") or ""
        conclusion = row.get("結論") or ""

        title_score = similarity(query_theme, title)
        theme_score = similarity(theme, past_theme)
        person_match = bool(
            main_person and person and (
                _normalize(main_person) in _normalize(person)
                or _normalize(person) in _normalize(main_person)
            )
        )
        conclusion_score = similarity(theme, conclusion)
        overall = max(title_score, theme_score, conclusion_score)
        if person_match:
            overall = min(1.0, overall + 0.10)

        matches.append({
            "公開日": row.get("公開日") or "",
            "タイトル": title,
            "テーマ": past_theme,
            "主要人物": person,
            "URL": row.get("URL") or "",
            "タイトル類似度": round(title_score, 3),
            "テーマ類似度": round(theme_score, 3),
            "結論類似度": round(conclusion_score, 3),
            "人物一致": "一致" if person_match else "-",
            "総合": round(overall, 3),
        })

    matches.sort(key=lambda item: item["総合"], reverse=True)
    top = matches[:5]
    max_score = matches[0]["総合"] if matches else 0.0

    if max_score >= THRESHOLD_HIGH:
        status = "大幅重複の疑い（要確認）"
    elif max_score >= THRESHOLD_MID:
        status = "一部重複の疑い（要確認）"
    else:
        status = "重複の機械的な兆候なし"

    return {
        "status": status,
        "available": True,
        "matches": top,
        "all_count": len(matches),
        "max_score": max_score,
        "note": "文字2-gramの一致率による参考値。最終判定はサブエージェントと荒木愛一朗が行う。",
    }


def to_markdown(result: dict) -> str:
    lines = [
        f"- 機械参考判定：**{result['status']}**",
        f"- 最大類似度：{result.get('max_score', 0.0)}",
        f"- 過去動画件数：{result.get('all_count', 0)}",
        f"- 備考：{result.get('note', '')}",
    ]
    matches = result.get("matches") or []
    if matches:
        lines.extend([
            "",
            "| 公開日 | 過去タイトル | 主要人物 | タイトル類似度 | テーマ類似度 | 結論類似度 | 人物一致 | 総合 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for match in matches:
            lines.append(
                f"| {match['公開日']} | {match['タイトル']} | {match['主要人物']} | "
                f"{match['タイトル類似度']} | {match['テーマ類似度']} | {match['結論類似度']} | "
                f"{match['人物一致']} | {match['総合']} |"
            )
    lines.append("")
    lines.append(
        "> 類似度は文字の一致率にすぎず、切り口の重複を判定するものではない。"
        "数値が低くても、結論や構成が同じであれば重複と判断すること。"
    )
    return "\n".join(lines)
