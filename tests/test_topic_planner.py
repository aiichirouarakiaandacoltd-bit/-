"""pytest for imperial_topic_planner."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_planner(*args):
    return subprocess.run(
        [sys.executable, "-m", "imperial_topic_planner", *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )


def find_latest_plan():
    plans_dir = PROJECT_ROOT / "output" / "topic_plans"
    if not plans_dir.exists():
        return None
    dirs = sorted(
        (d for d in plans_dir.iterdir() if d.is_dir()),
        key=lambda d: d.name, reverse=True,
    )
    return dirs[0] if dirs else None


class TestTopicPlannerTest:
    @pytest.fixture(autouse=True, scope="class")
    def _run_test_mode(self):
        result = run_planner("--test")
        assert result.returncode == 0, f"--test failed:\n{result.stderr}"

    def test_all_files_exist(self):
        from imperial_topic_planner.config import OUTPUT_FILES
        pkg = find_latest_plan()
        assert pkg is not None
        for fname in OUTPUT_FILES:
            assert (pkg / fname).exists(), f"Missing: {fname}"

    def test_no_zero_byte_files(self):
        pkg = find_latest_plan()
        zero = [f.name for f in pkg.iterdir() if f.is_file() and f.stat().st_size == 0]
        assert zero == [], f"0KB files: {zero}"

    def test_at_least_one_selected(self):
        pkg = find_latest_plan()
        content = (pkg / "02_selected_topics.md").read_text(encoding="utf-8")
        assert "採用数: 0本" not in content
        assert "## T" in content

    def test_scoring_is_100(self):
        from imperial_topic_planner.topics import generate_candidates
        result = generate_candidates()
        for c in result["candidates"]:
            assert sum(c["scores"].values()) <= 100, f"{c['id']} exceeds 100"

    def test_below_threshold_not_selected(self):
        from imperial_topic_planner.topics import generate_candidates
        from imperial_topic_planner.config import PASS_THRESHOLD
        result = generate_candidates()
        for c in result["selected"]:
            assert c["total_score"] >= PASS_THRESHOLD, \
                f"{c['id']} score {c['total_score']} < {PASS_THRESHOLD} but selected"

    def test_no_prohibited_in_selected(self):
        from imperial_topic_planner.topics import generate_candidates
        from imperial_topic_planner.config import PROHIBITED_EXPRESSIONS
        result = generate_candidates()
        for c in result["selected"]:
            for expr in PROHIBITED_EXPRESSIONS:
                assert expr not in c["title"], \
                    f"Prohibited '{expr}' in selected {c['id']}"

    def test_production_ready_false_in_test_mode(self):
        pkg = find_latest_plan()
        content = (pkg / "09_package_summary.md").read_text(encoding="utf-8")
        assert "production_ready: False" in content

    def test_execution_log_exists(self):
        pkg = find_latest_plan()
        log_path = pkg / "execution.log"
        assert log_path.exists()
        assert log_path.stat().st_size > 0


class TestTopicPlannerProduction:
    @pytest.fixture(autouse=True, scope="class")
    def _run_production_mode(self):
        result = run_planner("--production")
        assert result.returncode == 0, f"--production failed:\n{result.stderr}"

    def test_production_ready_true(self):
        pkg = find_latest_plan()
        content = (pkg / "09_package_summary.md").read_text(encoding="utf-8")
        assert "production_ready: True" in content

    def test_all_selected_have_sources(self):
        from imperial_topic_planner.topics import generate_candidates
        result = generate_candidates()
        for c in result["selected"]:
            assert len(c.get("official_sources", [])) > 0, \
                f"{c['id']} has no official sources"

    def test_risk_check_done(self):
        pkg = find_latest_plan()
        content = (pkg / "08_risk_check_report.md").read_text(encoding="utf-8")
        assert "総合リスク判定" in content
