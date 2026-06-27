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

    def test_package_structure_complete(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["package_structure_complete"] is True

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

    def test_package_structure_complete(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["package_structure_complete"] is True

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
                {"fact_id": "F1", "claim": "テスト事実A", "status": cfg.FactStatus.CONFIRMED,
                 "usable_in_script": True, "narration_lead": "テスト事実Aについてお伝えします。"},
                {"fact_id": "F2", "claim": "テスト事実B", "status": cfg.FactStatus.CONFIRMED,
                 "usable_in_script": True, "narration_lead": "次にテスト事実Bです。"},
            ],
        }
        text = _build_long_script_text("テストテーマ", research_data)
        assert "ご視聴" in text
        assert "【オープニング】" in text
        assert "【エンディング】" in text
        assert "テスト事実A" in text


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
                       "07_ng_check_report.md", "08_bgm_plan.md",
                       "09_package_summary.md"]:
                (d / f).write_text("test", encoding="utf-8")
            (d / "metadata.json").write_text("{}", encoding="utf-8")
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

    def test_fact_check_status_ignores_non_blocking_facts(self):
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
                       "07_ng_check_report.md", "08_bgm_plan.md",
                       "09_package_summary.md"]:
                (d / f).write_text("test", encoding="utf-8")
            (d / "metadata.json").write_text("{}", encoding="utf-8")
            bgm = {"file_name": "UNL1337.wav", "provider": "箕輪レコーズ",
                    "license_status": "contracted",
                    "contract_evidence": "テスト契約",
                    "contract_evidence_verified": True,
                    "content_id_status": "confirmed",
                    "local_file_verified": True,
                    "credit_text": "楽曲提供：箕輪レコーズ",
                    "download_or_reference_url": None}
            status = validate_package(d, data, {"findings": []}, bgm, topic)
            assert status["fact_check_status"] == "all_confirmed"
            f007 = [f for f in data["facts"] if f["fact_id"] == "F007"]
            assert len(f007) == 1
            assert f007[0]["blocking"] is False
            assert f007[0]["required_for_content"] is False


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


class TestBGMContractedWarnings:
    def test_contracted_bgm_warnings_not_blocking(self):
        """contracted BGM with contract_evidence → verification items are warnings, not issues."""
        from src.validators import _validate_bgm_config
        bgm = {
            "file_name": "UNL1337.wav",
            "provider": "箕輪レコーズ",
            "license_status": "contracted",
            "contract_evidence": "箕輪レコーズとの楽曲使用契約に基づく",
            "credit_text": "楽曲提供：箕輪レコーズ",
            "contract_evidence_verified": False,
            "content_id_status": "unconfirmed",
            "local_file_verified": False,
            "download_or_reference_url": None,
        }
        issues, warnings = _validate_bgm_config(bgm)
        assert len(issues) == 0, f"Should have no issues but got: {issues}"
        assert len(warnings) >= 1, "Should have warnings for unverified items"

    def test_contracted_bgm_production_ready(self):
        """contracted BGM + evidence → production_ready=true achievable."""
        from src.validators import validate_package
        from src.research import research_topic
        import tempfile
        topic = "なぜ「愛子」と「敬宮」なのか――『孟子』に記された御名と御称号の由来"
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            data = research_topic(topic, str(d))
            for f in ["01_research_report.md", "02_narration_script.md",
                       "03_editing_instructions.md", "04_materials_list.md",
                       "05_posting_package.md", "06_bgm_and_credits.md",
                       "07_ng_check_report.md", "08_bgm_plan.md",
                       "09_package_summary.md"]:
                (d / f).write_text("出典：参考", encoding="utf-8")
            (d / "metadata.json").write_text("{}", encoding="utf-8")
            bgm = {
                "file_name": "UNL1337.wav",
                "provider": "箕輪レコーズ",
                "license_status": "contracted",
                "contract_evidence": "箕輪レコーズとの楽曲使用契約に基づく",
                "credit_text": "楽曲提供：箕輪レコーズ",
                "contract_evidence_verified": False,
                "content_id_status": "unconfirmed",
                "local_file_verified": False,
                "download_or_reference_url": None,
            }
            status = validate_package(
                d, data, {"findings": []}, bgm, topic,
                mode="production", rights_data={"overall_status": "OK", "has_review": False},
            )
            assert len(status["bgm_issues"]) == 0
            assert len(status["bgm_warnings"]) >= 1


class TestHonorificsExpanded:
    def test_masako_bare_name_detected(self):
        """雅子 without honorific is detected."""
        from src.ng_check import check_ng_expressions
        import tempfile
        script = "雅子が出席された。出典あり。"
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, [], "", d)
            findings = [f for f in result["findings"]
                        if f["category"] == "敬称・敬語" and "雅子" in f["item"]]
            assert len(findings) >= 1

    def test_masako_with_honorific_not_flagged(self):
        """雅子さま / 雅子皇后陛下 should not be flagged."""
        from src.ng_check import check_ng_expressions
        import tempfile
        script = "雅子さまが出席された。雅子皇后陛下のお言葉。出典あり。"
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, [], "", d)
            findings = [f for f in result["findings"]
                        if f["category"] == "敬称・敬語" and "雅子" in f["item"]]
            assert len(findings) == 0, f"False positive: {findings}"

    def test_auto_fix_first_and_subsequent(self):
        """Auto-fix: first occurrence → formal, subsequent → さま."""
        from src.ng_check import auto_fix_honorifics
        text = "愛子が誕生した。愛子は成長された。"
        fixed = auto_fix_honorifics(text)
        assert "愛子内親王殿下" in fixed
        assert "愛子さま" in fixed
        assert fixed.index("愛子内親王殿下") < fixed.index("愛子さま")

    def test_auto_fix_preserves_quoted(self):
        """Auto-fix: 御名『愛子』 is not modified."""
        from src.ng_check import auto_fix_honorifics
        text = '御名「愛子」と御称号「敬宮」の由来'
        fixed = auto_fix_honorifics(text)
        assert '御名「愛子」' in fixed
        assert '御称号「敬宮」' in fixed

    def test_hisahito_bare_name_detected(self):
        """悠仁 without honorific is detected."""
        from src.ng_check import check_ng_expressions
        import tempfile
        script = "悠仁が入学された。出典あり。"
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, [], "", d)
            findings = [f for f in result["findings"]
                        if f["category"] == "敬称・敬語" and "悠仁" in f["item"]]
            assert len(findings) >= 1
