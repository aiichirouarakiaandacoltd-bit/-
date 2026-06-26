"""Smoke tests for package generation."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = PROJECT_ROOT / "main.py"


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

    def test_production_ready_true(self):
        pkg = find_latest_package()
        meta = json.loads((pkg / "metadata.json").read_text(encoding="utf-8"))
        assert meta["production_ready"] is True
