"""投稿カレンダーの生成。

週あたりの投稿本数（frequency）と週数（weeks）から投稿予定を作り、
テーマ・フォーマットを巡回させて割り当てる。日付は posting_days を基準に決める。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from .generator import PostGenerator

# 巡回させる投稿フォーマット（バランス重視）
FORMAT_CYCLE = ["carousel", "feed", "reel", "story"]


def _posting_dates(start: date, weeks: int, frequency: int, posting_days: List[int]) -> List[date]:
    """投稿日リストを生成する。

    posting_days（0=月〜6=日）を週ごとに使い、frequency 件/週になるよう選ぶ。
    """
    days = sorted(posting_days)[:max(frequency, 0)]
    if len(days) < frequency:
        # 足りなければ等間隔で補完
        days = sorted(set(days) | set(range(0, 7, max(1, 7 // max(frequency, 1)))))[:frequency]
    # start を含む週の月曜日を基準に
    week_monday = start - timedelta(days=start.weekday())
    dates: List[date] = []
    for w in range(weeks):
        for wd in days:
            d = week_monday + timedelta(weeks=w, days=wd)
            if d >= start:
                dates.append(d)
    dates.sort()
    return dates


class CalendarBuilder:
    def __init__(self, generator: Optional[PostGenerator] = None):
        self.gen = generator or PostGenerator()
        self.cfg = self.gen.cfg

    def build(self, weeks: Optional[int] = None, frequency: Optional[int] = None,
              start: Optional[date] = None) -> List[Dict[str, Any]]:
        cal_cfg = self.cfg.get("calendar", {})
        weeks = weeks or cal_cfg.get("default_weeks", 4)
        frequency = frequency or cal_cfg.get("default_frequency", 3)
        posting_days = cal_cfg.get("posting_days", [1, 3, 5])
        start = start or date.today()

        themes = self.gen.themes
        if not themes:
            return []

        dates = _posting_dates(start, weeks, frequency, posting_days)
        entries: List[Dict[str, Any]] = []
        for i, d in enumerate(dates):
            theme = themes[i % len(themes)]
            fmt = FORMAT_CYCLE[i % len(FORMAT_CYCLE)]
            post = self.gen.generate(theme["name"], fmt)
            post["scheduled_date"] = d.isoformat()
            post["status"] = "scheduled" if post["risk"]["ok"] else "review"
            entries.append(post)
        return entries
