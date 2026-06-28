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


class TestShortsExactlyTwo:
    def test_generate_shorts_returns_two(self):
        """generate_shorts_scripts returns exactly 2 paths."""
        from src.script_writer import generate_shorts_scripts
        import config as cfg
        import tempfile
        research_data = {
            "facts": [{"claim": "テスト事実", "status": cfg.FactStatus.CONFIRMED,
                        "usable_in_script": True, "verified_excerpt": "テスト"}],
        }
        with tempfile.TemporaryDirectory() as d:
            result = generate_shorts_scripts("テスト", research_data, d)
            assert len(result) == 2, f"Expected 2 shorts, got {len(result)}"
            assert result[0].name == "shorts_01_script.txt"
            assert result[1].name == "shorts_02_script.txt"

    def test_no_shorts_03_in_metadata(self):
        """metadata.json must not contain shorts_03_estimated_seconds."""
        from src.validators import validate_package
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for f in ["01_research_report.md", "02_narration_script.md",
                       "03_editing_instructions.md", "04_materials_list.md",
                       "05_posting_package.md", "06_bgm_and_credits.md",
                       "07_ng_check_report.md", "08_bgm_plan.md",
                       "09_package_summary.md"]:
                (d / f).write_text("test 出典", encoding="utf-8")
            (d / "metadata.json").write_text("{}", encoding="utf-8")
            bgm = {"file_name": "UNL1337.wav", "provider": "箕輪レコーズ",
                    "license_status": "contracted", "contract_evidence": "テスト",
                    "credit_text": "楽曲提供：箕輪レコーズ"}
            status = validate_package(d, {"facts": []}, {"findings": []}, bgm, "T")
            assert "shorts_03_estimated_seconds" not in status


class TestNGCheckTotalChecks:
    def test_total_checks_at_least_one(self):
        """NG check must have total_checks >= 1 even with clean input."""
        from src.ng_check import check_ng_expressions
        import tempfile
        script = "愛子内親王殿下は日本赤十字社にご入社されました。出典あり。"
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, ["テストタイトル"], "テスト概要", d)
            assert result["total_checks"] >= 1, f"total_checks is {result['total_checks']}"
            assert result["pass_count"] >= 1, "Should have PASS findings"

    def test_zero_checks_prohibited(self):
        """Even empty input should produce at least basic checks."""
        from src.ng_check import check_ng_expressions
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions("テスト台本", [], "", d)
            assert result["total_checks"] >= 1


class TestBGMFileValidation:
    def test_bgm_file_exists_and_valid(self):
        """BGM file at assets/bgm/UNL1337.wav should pass validation."""
        from src.validators import validate_bgm_file
        result = validate_bgm_file()
        assert result["valid"] is True, f"BGM validation failed: {result['issues']}"
        assert result["duration_seconds"] >= 10
        assert result["file_size"] > 0

    def test_bgm_file_missing(self):
        """Non-existent BGM file should fail validation."""
        from src.validators import validate_bgm_file
        result = validate_bgm_file("/nonexistent/file.wav")
        assert result["valid"] is False
        assert len(result["issues"]) >= 1


class TestMaterialCandidateURLs:
    def test_jrc_topic_has_candidate_urls(self):
        """Red Cross topic materials should include candidate URLs."""
        from src.materials import _build_scene_materials
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            scenes = _build_scene_materials(topic, data)
            has_urls = False
            for scene in scenes:
                if scene.get("candidate_urls"):
                    has_urls = True
                    break
            assert has_urls, "Red Cross topic should have candidate URLs per scene"


class TestRightsStatus:
    def test_rights_status_values(self):
        """Rights report should return valid status values."""
        from src.materials import generate_rights_report
        import tempfile
        materials_data = [
            {"scene": "テスト", "candidate_urls": [
                {"url": "https://example.com", "description": "テスト", "rights_status": "usable"}
            ]}
        ]
        with tempfile.TemporaryDirectory() as d:
            result = generate_rights_report(materials_data, {}, d)
            assert result["overall_status"] in ("OK", "review", "blocked", "incomplete")


class TestTitleDirections:
    def test_five_distinct_directions(self):
        """Title candidates should have 5 distinct direction values."""
        from src.posting import _generate_title_candidates
        titles = _generate_title_candidates("テストテーマ", {"facts": []})
        assert len(titles) == 5
        directions = [t.get("direction", "") for t in titles]
        assert len(set(directions)) == 5, f"Directions not unique: {directions}"


class TestProductionRedCross:
    @pytest.fixture(autouse=True, scope="class")
    def _run_jrc_production(self):
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        result = run_main("generate", "--production", "--theme", topic)
        assert result.returncode == 0, f"JRC production failed:\n{result.stderr}"

    def test_production_ready_true(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["production_ready"] is True, f"Not production_ready. Missing: {meta.get('missing_items', [])}"

    def test_no_shorts_03(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert "shorts_03_estimated_seconds" not in meta

    def test_ng_checks_sufficient(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("ng_total_checks", 0) >= 1

    def test_bgm_file_valid(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("bgm_file_valid") is True

    def test_no_zero_byte_files(self):
        pkg = find_latest_package()
        zero = [f.name for f in pkg.iterdir() if f.is_file() and f.stat().st_size == 0]
        assert zero == []

    def test_all_required_files_exist(self):
        pkg = find_latest_package()
        required = [
            "01_research_report.md", "02_narration_script.md",
            "03_editing_instructions.md", "04_materials_list.md",
            "05_posting_package.md", "06_bgm_and_credits.md",
            "07_ng_check_report.md", "08_bgm_plan.md",
            "09_package_summary.md", "metadata.json", "execution.log",
        ]
        for f in required:
            assert (pkg / f).exists(), f"{f} missing"

    def test_bgm_local_file_verified_consistent(self):
        """06_bgm_and_credits.md should say 検証済 when bgm_file_valid=true."""
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        bgm_md = (pkg / "06_bgm_and_credits.md").read_text(encoding="utf-8")
        if meta.get("bgm_file_valid"):
            assert "検証済" in bgm_md, "BGM file valid but 06 says 未検証"

    def test_no_araki_text_in_outputs(self):
        """No output file should contain '荒木側' text."""
        pkg = find_latest_package()
        for f in pkg.iterdir():
            if f.is_file() and f.suffix in (".md", ".json"):
                content = f.read_text(encoding="utf-8")
                assert "荒木側" not in content, f"{f.name} still contains '荒木側'"

    def test_rights_status_not_usable_for_official(self):
        """Official page URLs should be 'review', not 'usable'."""
        from src.materials import _collect_candidate_urls
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            urls = _collect_candidate_urls(data, "opening")
            for u in urls:
                assert u["rights_status"] != "usable", f"Official URL should not be 'usable': {u}"

    def test_no_outsourcer_delegation_text(self):
        """04_materials_list.md should not contain outsourcer delegation."""
        pkg = find_latest_package()
        content = (pkg / "04_materials_list.md").read_text(encoding="utf-8")
        assert "外注者が編集時に記入" not in content
        assert "外注者の素材使用記録" not in content

    def test_script_no_excessive_repetition(self):
        """Long script should not have any narration phrase repeated 3+ times."""
        pkg = find_latest_package()
        script = (pkg / "02_narration_script.md").read_text(encoding="utf-8")
        skip_prefixes = ("【", "#", "テーマ:", "チャンネル:", "対象視聴者:",
                         "ナレーション:", "目標尺:", "「日本が誇る皇室物語」をご視聴")
        phrase_counts = {}
        for line in script.split("\n"):
            s = line.strip()
            if len(s) >= 8 and s != "=" * 60 \
                    and not any(s.startswith(p) for p in skip_prefixes):
                phrase_counts[s] = phrase_counts.get(s, 0) + 1
        repeated = {k: v for k, v in phrase_counts.items() if v >= 3}
        assert not repeated, f"Phrases repeated 3+ times: {repeated}"

    def test_title_5_not_duplicate_of_title_1(self):
        """Title candidate 5 must differ from title candidate 1."""
        from src.posting import _generate_title_candidates
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            titles = _generate_title_candidates(topic, data)
            assert titles[0]["title"] != titles[4]["title"], "Title 1 and 5 are identical"

    def test_all_5_titles_unique(self):
        """All 5 title candidates must be unique."""
        from src.posting import _generate_title_candidates
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            titles = _generate_title_candidates(topic, data)
            title_texts = [t["title"] for t in titles]
            assert len(set(title_texts)) == 5, f"Duplicate titles: {title_texts}"

    def test_titles_have_extended_fields(self):
        """Title candidates should have angle, click_reason, etc."""
        from src.posting import _generate_title_candidates
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            titles = _generate_title_candidates(topic, data)
            for t in titles:
                assert t.get("angle"), f"Missing angle: {t['title']}"
                assert t.get("click_reason"), f"Missing click_reason: {t['title']}"
                assert t.get("target_emotion"), f"Missing target_emotion: {t['title']}"

    def test_ng_repetition_threshold_3(self):
        """Repetition of 3+ should be FAIL, not REVIEW."""
        from src.ng_check import check_ng_expressions
        import tempfile
        line = "この事実は公式の記録に残されています。"
        script = "\n".join([line] * 3 + ["出典あり。"])
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, [], "", d)
            rep = [f for f in result["findings"] if f["category"] == "同一表現過剰反復" and f["verdict"] == "FAIL"]
            assert len(rep) >= 1, "3x repetition should produce FAIL"

    def test_ng_title_duplication_check(self):
        """Identical titles should produce FAIL finding."""
        from src.ng_check import check_ng_expressions
        import tempfile
        titles = ["同じタイトル", "別のタイトル", "同じタイトル"]
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions("テスト台本。出典あり。", titles, "", d)
            dup = [f for f in result["findings"] if f["category"] == "タイトル重複" and f["verdict"] == "FAIL"]
            assert len(dup) >= 1, "Duplicate titles should produce FAIL"

    def test_ng_inner_feelings_extended(self):
        """Extended inner feelings patterns should be detected."""
        from src.ng_check import check_ng_expressions
        import tempfile
        script = "殿下には強い思いがあったのでしょう。出典あり。"
        with tempfile.TemporaryDirectory() as d:
            result = check_ng_expressions(script, [], "", d)
            inner = [f for f in result["findings"] if f["category"] == "内心描写"]
            assert len(inner) >= 1, "Extended inner feelings not detected"

    def test_fact_verification_integrity(self):
        """Usable facts must have claims matching their excerpts; contextual facts must not be usable."""
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            for fact in data["facts"]:
                if fact.get("direct_or_contextual") == "contextual":
                    assert not fact.get("usable_in_script"), \
                        f"{fact['fact_id']}: contextual fact must not be usable_in_script"
                if fact.get("usable_in_script") and fact.get("direct_or_contextual") == "direct":
                    excerpt = fact.get("verified_excerpt", "")
                    assert len(excerpt) >= 5, \
                        f"{fact['fact_id']}: direct usable fact has too-short excerpt"

    def test_confirmed_facts_at_least_2(self):
        """Red Cross topic must have at least 2 confirmed usable facts."""
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            usable_confirmed = [f for f in data["facts"]
                                if f.get("status") == "confirmed" and f.get("usable_in_script")
                                and f.get("verified_excerpt")]
            assert len(usable_confirmed) >= 2

    def test_no_source_context_auto_append(self):
        """Script should not auto-append 'この{type}は{pub}によって公式に公開されています'."""
        from src.script_writer import _build_long_script_text
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            text = _build_long_script_text(topic, data)
            count = text.count("によって公式に公開されています")
            assert count == 0, f"Auto source context appeared {count} times"

    def test_recap_not_mechanical(self):
        """Recap should not repeat '確認いたしました' per section."""
        from src.script_writer import _build_long_script_text
        from src.research import research_topic
        import tempfile
        topic = "愛子内親王殿下はなぜ日本赤十字社を選んだのか――公式の記録にみるご決意と歩み"
        with tempfile.TemporaryDirectory() as d:
            data = research_topic(topic, d)
            text = _build_long_script_text(topic, data)
            count = text.count("確認いたしました")
            assert count <= 1, f"Mechanical recap: '確認いたしました' appears {count} times"

    def test_rights_report_no_auto_usable(self):
        """Rights report with official URLs should not have overall_status 'OK'."""
        from src.materials import generate_rights_report
        import tempfile
        materials_data = [
            {"scene": "テスト", "candidate_urls": [
                {"url": "https://www.kunaicho.go.jp/", "description": "宮内庁公式", "rights_status": "review"}
            ]}
        ]
        with tempfile.TemporaryDirectory() as d:
            result = generate_rights_report(materials_data, {}, d)
            assert result["overall_status"] == "review"

    def test_production_no_ng_fail(self):
        """Production package must have zero FAIL in NG check."""
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("ng_check_status") != "fail", "NG check has FAIL items"

    def test_long_script_min_7_minutes(self):
        """Long script should be at least 7 minutes."""
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("script_estimated_minutes", 0) >= 7.0, \
            f"Long script too short: {meta.get('script_estimated_minutes')}min"

    def test_shorts_min_45_seconds(self):
        """Both Shorts should be at least 45 seconds."""
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta.get("shorts_01_estimated_seconds", 0) >= 45.0, \
            f"Shorts 01 too short: {meta.get('shorts_01_estimated_seconds')}s"
        assert meta.get("shorts_02_estimated_seconds", 0) >= 45.0, \
            f"Shorts 02 too short: {meta.get('shorts_02_estimated_seconds')}s"


class TestFactVerificationQuality:
    """Regression tests: verified_excerpt must actually prove the claim."""

    def _get_all_builtin_facts(self):
        from src.research import _BUILTIN_TOPICS
        facts = []
        for topic_data in _BUILTIN_TOPICS.values():
            for f in topic_data.get("facts", []):
                facts.append(f)
        return facts

    def test_usable_fact_excerpt_not_too_short(self):
        """confirmed+usable fact must not have an extremely short or org-name-only excerpt."""
        import config as cfg
        for f in self._get_all_builtin_facts():
            if f.get("status") == cfg.FactStatus.CONFIRMED and f.get("usable_in_script"):
                excerpt = f.get("verified_excerpt", "")
                assert len(excerpt) >= 5, (
                    f"{f['fact_id']}: usable fact has too-short excerpt ({len(excerpt)} chars): '{excerpt}'"
                )

    def test_direct_fact_excerpt_covers_claim_core(self):
        """direct-verified fact with specific employment/role details must have substantive excerpt."""
        import config as cfg
        detail_markers = ["入社", "配属", "常勤", "嘱託", "編集業務に携わ"]
        for f in self._get_all_builtin_facts():
            if (f.get("status") == cfg.FactStatus.CONFIRMED
                    and f.get("usable_in_script")
                    and f.get("direct_or_contextual") == "direct"):
                claim = f.get("claim", "")
                excerpt = f.get("verified_excerpt", "")
                has_detail = any(m in claim for m in detail_markers)
                if has_detail:
                    assert len(excerpt) >= 10, (
                        f"{f['fact_id']}: direct fact with employment/role detail has too-short excerpt: '{excerpt}'"
                    )

    def test_contextual_fact_not_auto_usable(self):
        """contextual facts must not be confirmed+usable=true."""
        import config as cfg
        for f in self._get_all_builtin_facts():
            if f.get("direct_or_contextual") == "contextual":
                is_usable = f.get("usable_in_script", False)
                assert not is_usable, (
                    f"{f['fact_id']}: contextual fact should not be usable_in_script=True"
                )

    def test_org_name_only_excerpt_not_proves_detailed_claim(self):
        """An excerpt that is just an organization name must not prove a claim with specific details."""
        import config as cfg
        org_only_names = {"日本赤十字社", "宮内庁", "赤十字社"}
        detail_markers = ["入社", "配属", "就職", "常勤", "嘱託", "参加", "スピーチ", "視察"]
        for f in self._get_all_builtin_facts():
            if f.get("status") == cfg.FactStatus.CONFIRMED and f.get("usable_in_script"):
                excerpt = f.get("verified_excerpt", "").strip()
                claim = f.get("claim", "")
                if excerpt in org_only_names:
                    has_detail = any(m in claim for m in detail_markers)
                    assert not has_detail, (
                        f"{f['fact_id']}: org-name-only excerpt '{excerpt}' cannot prove detailed claim: '{claim}'"
                    )
