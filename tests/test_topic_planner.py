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
    """テストモード（サンプルデータ）での動作確認."""

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

    def test_scoring_max_100(self):
        from imperial_topic_planner.topics import generate_candidates_from_input, _build_test_sample_input
        input_data = _build_test_sample_input()
        result = generate_candidates_from_input(input_data)
        for c in result["candidates"]:
            assert sum(c["scores"].values()) <= 100, f"{c['id']} exceeds 100"

    def test_below_threshold_not_selected(self):
        from imperial_topic_planner.topics import generate_candidates_from_input, _build_test_sample_input
        from imperial_topic_planner.config import PASS_THRESHOLD
        input_data = _build_test_sample_input()
        result = generate_candidates_from_input(input_data)
        for c in result["selected"]:
            assert c["total_score"] >= PASS_THRESHOLD, \
                f"{c['id']} score {c['total_score']} < {PASS_THRESHOLD} but selected"

    def test_no_prohibited_in_selected(self):
        from imperial_topic_planner.topics import generate_candidates_from_input, _build_test_sample_input
        from imperial_topic_planner.config import PROHIBITED_EXPRESSIONS
        input_data = _build_test_sample_input()
        result = generate_candidates_from_input(input_data)
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

    def test_topic_plan_json_exists(self):
        pkg = find_latest_plan()
        plan_path = pkg / "topic_plan.json"
        assert plan_path.exists()
        assert plan_path.stat().st_size > 0
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        assert "topics" in plan
        assert "production_ready" in plan

    def test_topic_plan_json_not_production_ready_for_sample(self):
        pkg = find_latest_plan()
        plan = json.loads((pkg / "topic_plan.json").read_text(encoding="utf-8"))
        assert plan["production_ready"] is False


class TestTopicPlannerSampleBlocked:
    """サンプルデータがproduction_readyにならないことの確認."""

    @pytest.fixture(autouse=True, scope="class")
    def _run_production_with_sample(self):
        result = run_planner("--production")
        assert result.returncode in (0, 1), f"--production failed:\n{result.stderr}"

    def test_sample_not_production_ready(self):
        pkg = find_latest_plan()
        content = (pkg / "09_package_summary.md").read_text(encoding="utf-8")
        assert "production_ready: False" in content

    def test_sample_not_production_ready_json(self):
        pkg = find_latest_plan()
        plan = json.loads((pkg / "topic_plan.json").read_text(encoding="utf-8"))
        assert plan["production_ready"] is False


class TestTopicPlannerWithInput:
    """--input を使用した動作確認."""

    @pytest.fixture(autouse=True, scope="class")
    def _run_with_input(self, tmp_path_factory):
        tmp_dir = tmp_path_factory.mktemp("topic_input")
        input_file = tmp_dir / "topic_input.json"
        input_data = {
            "competitor_channels": [
                {"url": "https://www.youtube.com/@example-ch", "name": "テストCh"},
            ],
            "reference_videos": [
                {
                    "url": "https://www.youtube.com/watch?v=ref1",
                    "title": "愛子さまの公務",
                    "channel": "テストCh",
                    "theme": "愛子さま",
                    "views": 100000,
                    "published": "2026-05-01",
                    "subscribers_at_publish": 5000,
                    "ctr_estimate": 8.0,
                    "avg_watch_time_pct": 45,
                    "is_shorts": False,
                    "drove_long_views": True,
                },
            ],
            "own_channel_videos": [],
            "banned_themes": ["テスト禁止テーマ"],
            "official_sources": [
                {"url": "https://www.kunaicho.go.jp/test", "name": "宮内庁テスト", "type": "宮内庁"},
            ],
            "topic_ideas": [
                {
                    "title": "愛子内親王殿下の公務記録",
                    "center_pin": "公式行事の記録",
                    "theme_keywords": ["愛子さま", "公務"],
                    "official_source_urls": ["https://www.kunaicho.go.jp/test"],
                    "viewer_reason": "関心が高い",
                    "long_reason": "時系列で構成可能",
                    "shorts_reason": "個別エピソード切り出し可能",
                    "expected_emotion": "感動",
                    "rights_risk": "低",
                },
                {
                    "title": "テスト禁止テーマに関する企画",
                    "center_pin": "禁止テーマ",
                    "theme_keywords": ["テスト禁止テーマ"],
                    "official_source_urls": [],
                    "viewer_reason": "テスト用",
                    "long_reason": "",
                    "shorts_reason": "",
                    "expected_emotion": "テスト",
                    "rights_risk": "高",
                },
            ],
        }
        input_file.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")
        result = run_planner("--production", "--input", str(input_file))
        assert result.returncode == 0, f"--input failed:\n{result.stderr}"

    def test_all_files_exist(self):
        from imperial_topic_planner.config import OUTPUT_FILES
        pkg = find_latest_plan()
        assert pkg is not None
        for fname in OUTPUT_FILES:
            assert (pkg / fname).exists(), f"Missing: {fname}"

    def test_banned_theme_rejected(self):
        pkg = find_latest_plan()
        content = (pkg / "03_rejected_topics.md").read_text(encoding="utf-8")
        assert "テスト禁止テーマ" in content

    def test_topic_plan_json_structure(self):
        pkg = find_latest_plan()
        plan = json.loads((pkg / "topic_plan.json").read_text(encoding="utf-8"))
        assert isinstance(plan["topics"], list)
        for topic in plan["topics"]:
            assert "id" in topic
            assert "title" in topic
            assert "total_score" in topic
            assert "scores" in topic
            assert "official_source_urls" in topic

    def test_risk_check_done(self):
        pkg = find_latest_plan()
        content = (pkg / "08_risk_check_report.md").read_text(encoding="utf-8")
        assert "総合リスク判定" in content

    def test_no_zero_byte_files(self):
        pkg = find_latest_plan()
        zero = [f.name for f in pkg.iterdir() if f.is_file() and f.stat().st_size == 0]
        assert zero == [], f"0KB files: {zero}"


class TestScoringLogic:
    """スコアリングロジックの単体テスト."""

    def test_total_score_max_100(self):
        from imperial_topic_planner.topics import _score_topic
        idea = {
            "title": "テスト",
            "center_pin": "テスト",
            "theme_keywords": ["愛子さま"],
            "official_source_urls": ["https://example.com"],
            "rights_risk": "低",
            "long_reason": "あり",
            "shorts_reason": "あり",
        }
        input_data = {
            "reference_videos": [],
            "official_sources": [{"url": "https://example.com", "name": "テスト", "type": "宮内庁"}],
        }
        scores = _score_topic(idea, input_data, {})
        total = sum(scores.values())
        assert total <= 100, f"Total {total} exceeds 100"

    def test_banned_theme_is_rejected(self):
        from imperial_topic_planner.topics import _is_banned
        result, expr = _is_banned("皇位継承問題の解説", ["皇位継承"], ["皇位継承問題"])
        assert result is True

    def test_prohibited_expression_detected(self):
        from imperial_topic_planner.topics import _contains_prohibited
        result, expr = _contains_prohibited("衝撃の真実を暴露")
        assert result is True

    def test_reference_demand_score(self):
        from imperial_topic_planner.input_loader import compute_reference_demand
        vid = {
            "views": 200000,
            "subscribers_at_publish": 5000,
            "ctr_estimate": 10.0,
            "avg_watch_time_pct": 50,
            "drove_long_views": True,
        }
        score = compute_reference_demand(vid)
        assert 0 <= score <= 10

    def test_three_way_split(self):
        from imperial_topic_planner.topics import generate_candidates_from_input, _build_test_sample_input
        input_data = _build_test_sample_input()
        result = generate_candidates_from_input(input_data)
        assert "selected" in result
        assert "held" in result
        assert "rejected" in result
        assert len(result["rejected"]) >= 2, "banned/high-risk topics should be rejected"


class TestInputValidation:
    """入力バリデーションのテスト."""

    def test_missing_topic_ideas(self):
        from imperial_topic_planner.input_loader import validate_input
        errors = validate_input({"official_sources": [{"url": "x", "name": "y"}]})
        assert any("topic_ideas" in e for e in errors)

    def test_missing_official_sources(self):
        from imperial_topic_planner.input_loader import validate_input
        errors = validate_input({
            "topic_ideas": [{"title": "t", "center_pin": "c"}],
        })
        assert any("official_sources" in e for e in errors)

    def test_valid_input_no_errors(self):
        from imperial_topic_planner.input_loader import validate_input
        data = {
            "topic_ideas": [{"title": "タイトル", "center_pin": "核"}],
            "official_sources": [{"url": "https://example.com", "name": "テスト"}],
        }
        errors = validate_input(data)
        assert errors == []
