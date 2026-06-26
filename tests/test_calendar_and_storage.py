"""カレンダー生成と保存処理のユニットテスト。"""
import csv
import json
from datetime import date

import pytest

from lifesave_ig import config
from lifesave_ig.calendar_gen import CalendarBuilder, _posting_dates
from lifesave_ig import storage


def test_posting_dates_count():
    start = date(2026, 1, 5)  # 月曜
    dates = _posting_dates(start, weeks=4, frequency=3, posting_days=[1, 3, 5])
    assert len(dates) == 12  # 4週 x 3本
    assert dates == sorted(dates)


def test_calendar_build_count():
    builder = CalendarBuilder()
    posts = builder.build(weeks=2, frequency=3, start=date(2026, 1, 5))
    assert len(posts) == 6
    for p in posts:
        assert p["scheduled_date"]
        assert p["status"] in ("scheduled", "review")
        assert p["risk"]["ok"] in (True, False)


def test_storage_roundtrip(tmp_path):
    cfg = config.load_config()
    # 出力先を一時ディレクトリへ
    cfg["output"]["posts_json"] = str(tmp_path / "posts.json")
    cfg["output"]["calendar_csv"] = str(tmp_path / "calendar.csv")
    cfg["output"]["risk_report"] = str(tmp_path / "risk_report.md")
    cfg["output"]["generated_dir"] = str(tmp_path / "generated_posts")

    builder = CalendarBuilder()
    posts = builder.build(weeks=1, frequency=3, start=date(2026, 1, 5))

    storage.save_posts(cfg, posts)
    csv_path = storage.save_calendar_csv(cfg, posts)
    report_path = storage.save_risk_report(cfg, posts)
    for p in posts:
        storage.save_post_markdown(cfg, p)

    # ファイルが0KBでないこと
    assert (tmp_path / "posts.json").stat().st_size > 0
    assert csv_path.stat().st_size > 0
    assert report_path.stat().st_size > 0

    # posts.json が読み戻せる
    loaded = storage.load_posts(cfg)
    assert len(loaded) == len(posts)

    # CSV にヘッダと行がある
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(posts)
    assert "date" in rows[0] and "status" in rows[0]

    # Markdown が生成されている
    md_files = list((tmp_path / "generated_posts").glob("*.md"))
    assert len(md_files) >= 1
    assert md_files[0].stat().st_size > 0


def test_markdown_contains_sections():
    cfg = config.load_config()
    builder = CalendarBuilder()
    post = builder.gen.generate("家中の水を見直す", "carousel")
    md = storage.post_to_markdown(post)
    assert "## キャプション" in md
    assert "## ハッシュタグ" in md
    assert "## 注意表現チェック結果" in md
    assert "## カルーセル構成" in md
