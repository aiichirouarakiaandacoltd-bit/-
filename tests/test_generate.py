"""Smoke tests for package generation."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"
sys.path.insert(0, str(PROJECT_ROOT))


def run_main(*args):
    return subprocess.run(
        [sys.executable, str(MAIN_PY), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )


def find_latest_package():
    packages_dir = PROJECT_ROOT / "output" / "packages"
    dirs = sorted(
        (d for d in packages_dir.iterdir() if d.is_dir()),
        key=lambda d: d.name, reverse=True,
    )
    return dirs[0] if dirs else None


class TestHelp:
    def test_help_exits_zero(self):
        result = run_main("--help")
        assert result.returncode == 0
        assert "generate" in result.stdout


class TestGenerateTest:
    @pytest.fixture(autouse=True, scope="class")
    def _run_test_mode(self):
        result = run_main("generate", "--test")
        assert result.returncode == 0, f"generate --test failed:\n{result.stderr}"

    def test_no_zero_byte_files(self):
        pkg = find_latest_package()
        assert pkg is not None
        zero = [f.name for f in pkg.iterdir() if f.is_file() and f.stat().st_size == 0]
        assert zero == [], f"0KB files found: {zero}"

    def test_package_complete(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["package_complete"] is True

    def test_production_ready_false_in_test_mode(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["production_ready"] is False


class TestGenerateProduction:
    @pytest.fixture(autouse=True, scope="class")
    def _run_production_mode(self):
        result = run_main("generate", "--production")
        assert result.returncode == 0, f"generate --production failed:\n{result.stderr}"

    def test_no_zero_byte_files(self):
        pkg = find_latest_package()
        assert pkg is not None
        zero = [f.name for f in pkg.iterdir() if f.is_file() and f.stat().st_size == 0]
        assert zero == [], f"0KB files found: {zero}"

    def test_package_complete(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["package_complete"] is True

    def test_production_ready_false_for_default_theme(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["production_ready"] is False


class TestBug1ShortsHeader:
    def test_no_header_repetition(self):
        from src.script_writer import generate_shorts_scripts
        import config as cfg
        import tempfile
        research_data = {
            "facts": [{"claim": "テスト事実", "status": cfg.FactStatus.CONFIRMED,
                        "usable_in_script": True}],
        }
        with tempfile.TemporaryDirectory() as d:
            p1, p2 = generate_shorts_scripts("テスト", research_data, d)
            content = p1.read_text(encoding="utf-8")
            eq_lines = [l for l in content.split("\n") if l.strip() == "=" * 60]
            assert len(eq_lines) == 1, f"Expected 1 separator line, got {len(eq_lines)}"
            assert content.count("\n=\n=") == 0


class TestBug2NarrationProse:
    def test_long_script_is_prose(self):
        from src.script_writer import _build_long_script_text
        import config as cfg
        research_data = {
            "facts": [
                {"claim": "テスト事実A", "status": cfg.FactStatus.CONFIRMED,
                 "usable_in_script": True},
                {"claim": "テスト事実B", "status": cfg.FactStatus.CONFIRMED,
                 "usable_in_script": True},
            ],
        }
        text = _build_long_script_text("テストテーマ", research_data)
        assert "ご視聴" in text
        assert "【オープニング】" in text
        assert "【エンディング】" in text
        assert "まず、" in text or "そして、" in text


class TestBug3ChannelName:
    def test_channel_name_from_config(self):
        from src.validators import validate_package
        import config as cfg
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for f in ["01_research_report.md", "02_narration_script.md",
                       "03_editing_instructions.md", "04_materials_list.md",
                       "05_posting_package.md", "06_bgm_and_credits.md",
                       "07_ng_check_report.md", "08_bgm_plan.md"]:
                (d / f).write_text("test", encoding="utf-8")
            bgm = {"_channel": "ザ・ダンク", "download_or_reference_url": "https://x",
                    "title": "T", "commercial_use": True, "youtube_monetization": True,
                    "license_status": "free"}
            status = validate_package(d, {"facts": []}, {"findings": []}, bgm, "T")
            assert status["channel_name"] == cfg.CHANNEL_NAME


class TestBug4SourceUrlNull:
    def test_null_url_and_no_identifier_sets_unusable(self):
        from src.research import research_topic
        import tempfile
        topic = "なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            for fact in data["facts"]:
                has_source = fact.get("source_url") or fact.get("resource_identifier")
                if not has_source:
                    assert fact["usable_in_script"] is False
                    assert fact.get("manual_source_verification_required") is True

    def test_facts_have_verified_fields(self):
        from src.research import research_topic
        import tempfile
        topic = "なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            usable = [f for f in data["facts"] if f.get("usable_in_script")]
            assert len(usable) >= 1
            for fact in usable:
                assert fact.get("source_url") or fact.get("resource_identifier"), \
                    f"{fact['fact_id']} has no source_url or resource_identifier"
                assert fact.get("verified_excerpt"), \
                    f"{fact['fact_id']} missing verified_excerpt"
                assert not fact.get("manual_source_verification_required"), \
                    f"{fact['fact_id']} still requires manual verification"

    def test_fact_check_status_not_all_confirmed_when_manual_needed(self):
        from src.research import research_topic
        from src.validators import validate_package
        import tempfile
        topic = "なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来"
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            data = research_topic(topic, str(d))
            for f in ["01_research_report.md", "02_narration_script.md",
                       "03_editing_instructions.md", "04_materials_list.md",
                       "05_posting_package.md", "06_bgm_and_credits.md",
                       "07_ng_check_report.md", "08_bgm_plan.md"]:
                (d / f).write_text("test", encoding="utf-8")
            bgm = {"file_name": "UNL1337.wav", "provider": "箕輪レコーズ",
                    "download_or_reference_url": None}
            status = validate_package(d, data, {"findings": []}, bgm, topic)
            assert status["fact_check_status"] != "all_confirmed"
            assert status["fact_check_status"] == "manual_verification_required"


class TestBug5InstructionsBGM:
    def test_instructions_use_bgm_config(self):
        from src.instructions import generate_video_instructions
        import config as cfg
        import tempfile
        research_data = {"facts": []}
        bgm = {"file_name": "UNL1337.wav", "provider": "箕輪レコーズ"}
        with tempfile.TemporaryDirectory() as d:
            generate_video_instructions("T", research_data, d, bgm_config=bgm)
            content = (Path(d) / "video_editing_instructions.md").read_text(encoding="utf-8")
            assert "UNL1337.wav" in content
            assert "箕輪レコーズ" in content

    def test_bgm_config_rejects_wrong_channel(self):
        from src.bgm_config import load_bgm_config
        import config as cfg
        config = load_bgm_config()
        assert config.get("file_name") == cfg.BGM_SETTINGS["file_name"]
        assert config.get("provider") == cfg.BGM_SETTINGS["provider"]
        assert "Sports_Digest" not in config.get("file_name", "")
        assert "DOVA" not in config.get("provider", "")


class TestBug6CreditDuplication:
    def test_credit_text_output_as_is(self):
        from src.posting import _generate_credits_lines
        bgm = {"credit_text": "楽曲提供：箕輪レコーズ"}
        lines = _generate_credits_lines({}, bgm)
        text = "\n".join(lines)
        assert "楽曲提供：箕輪レコーズ" in text
        assert text.count("楽曲提供：箕輪レコーズ") == 1
        assert "BGM:" not in text
        assert "BGM: BGM:" not in text


class TestBug7NGFalsePositive:
    def test_quoted_name_not_flagged(self):
        from src.ng_check import check_ng_expressions
        import tempfile
        script = 'なぜ「愛子」と「敬宮」なのか'
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, [], "", d)
            honorific_findings = [f for f in result["findings"]
                                  if f["category"] == "敬称・敬語" and "愛子" in f["item"]]
            assert len(honorific_findings) == 0, f"False positive: {honorific_findings}"
