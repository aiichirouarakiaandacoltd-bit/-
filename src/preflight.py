"""Pre-flight diagnostics: verify all dependencies before video generation."""
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

import config as cfg


def check_python():
    import sys
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 9
    return {"name": "Python", "ok": ok, "detail": f"{v.major}.{v.minor}.{v.micro}"}


def check_packages():
    missing = []
    for pkg in ["PIL", "numpy"]:
        try:
            __import__(pkg if pkg != "PIL" else "PIL")
        except ImportError:
            missing.append(pkg)
    ok = len(missing) == 0
    return {"name": "Python packages", "ok": ok,
            "detail": "all present" if ok else f"missing: {', '.join(missing)}"}


def check_ffmpeg():
    path = shutil.which("ffmpeg")
    ok = path is not None
    detail = path or "not found"
    if ok:
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            ver = r.stdout.split("\n")[0] if r.returncode == 0 else "unknown version"
            detail = ver
        except Exception:
            pass
    return {"name": "FFmpeg", "ok": ok, "detail": detail}


def check_ffprobe():
    path = shutil.which("ffprobe")
    return {"name": "ffprobe", "ok": path is not None, "detail": path or "not found"}


def check_subtitle_support():
    try:
        r = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True, timeout=5
        )
        has_drawtext = "drawtext" in r.stdout
        has_ass = "ass" in r.stdout or "subtitles" in r.stdout
        ok = has_drawtext or has_ass
        methods = []
        if has_drawtext:
            methods.append("drawtext")
        if has_ass:
            methods.append("libass/subtitles")
        return {"name": "Subtitle rendering", "ok": ok,
                "detail": ", ".join(methods) if ok else "no subtitle filter found"}
    except Exception as e:
        return {"name": "Subtitle rendering", "ok": False, "detail": str(e)}


def check_font():
    font = Path(cfg.FONT_PATH)
    if font.exists():
        return {"name": "Japanese font", "ok": True, "detail": str(font)}
    for f in cfg.FALLBACK_FONTS:
        if Path(f).exists():
            return {"name": "Japanese font", "ok": True, "detail": f"fallback: {f}"}
    return {"name": "Japanese font", "ok": False, "detail": "no Japanese font found"}


def check_voicevox():
    try:
        req = urllib.request.Request(f"{cfg.VOICEVOX_HOST}/speakers", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            speakers = json.loads(resp.read())
        for s in speakers:
            if s["name"] == cfg.VOICEVOX_SPEAKER_NAME:
                styles = s.get("styles", [])
                if styles:
                    return {"name": "VOICEVOX", "ok": True,
                            "detail": f"{cfg.VOICEVOX_SPEAKER_NAME} found (style_id={styles[0]['id']})"}
        names = [s["name"] for s in speakers]
        return {"name": "VOICEVOX", "ok": False,
                "detail": f"{cfg.VOICEVOX_SPEAKER_NAME} not found. Available: {', '.join(names[:10])}"}
    except Exception as e:
        return {"name": "VOICEVOX", "ok": False, "detail": f"connection failed: {e}"}


def check_bgm():
    exists = cfg.BGM_FILE.exists()
    if exists:
        size = cfg.BGM_FILE.stat().st_size
        return {"name": "BGM", "ok": size > 0, "detail": f"{cfg.BGM_FILE} ({size} bytes)"}
    return {"name": "BGM", "ok": False, "detail": f"{cfg.BGM_FILE} not found"}


def check_output_writable():
    for d in [cfg.OUTPUT_LONG_DIR, cfg.OUTPUT_SHORTS_DIR, cfg.OUTPUT_TEST_DIR, cfg.LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        test_file = d / ".write_test"
        try:
            test_file.write_text("ok")
            test_file.unlink()
        except Exception as e:
            return {"name": "Output writable", "ok": False, "detail": f"{d}: {e}"}
    return {"name": "Output writable", "ok": True, "detail": "all output dirs writable"}


def check_zero_kb_inputs():
    """Check for 0KB files in input directories."""
    zero_files = []
    for d in [cfg.INPUT_DIR, cfg.ASSETS_DIR]:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.stat().st_size == 0:
                    zero_files.append(str(f))
    if zero_files:
        return {"name": "0KB input files", "ok": False,
                "detail": f"{len(zero_files)} zero-byte file(s): {', '.join(zero_files[:5])}"}
    return {"name": "0KB input files", "ok": True, "detail": "no zero-byte input files"}


def check_voicevox_speed():
    """Verify VOICEVOX speed setting."""
    ok = cfg.VOICEVOX_SPEED == 0.88
    return {"name": "VOICEVOX speed", "ok": ok,
            "detail": f"speed={cfg.VOICEVOX_SPEED} (expected 0.88)"}


def check_mode_separation(test_mode):
    """Verify test and production output directories are separate."""
    test_dir = cfg.OUTPUT_TEST_DIR
    prod_long = cfg.OUTPUT_LONG_DIR
    prod_shorts = cfg.OUTPUT_SHORTS_DIR
    ok = (str(test_dir) != str(prod_long) and str(test_dir) != str(prod_shorts))
    return {"name": "Mode separation", "ok": ok,
            "detail": f"test={test_dir}, prod_long={prod_long}, prod_shorts={prod_shorts}"}


def check_materials_rights(materials=None):
    """Validate material rights for production use (10-point check)."""
    if materials is None:
        return {"name": "Material rights", "ok": True,
                "detail": "素材未提供（ビルド時に検証）"}

    from src.materials import validate_all_materials
    ok, violations = validate_all_materials(materials)
    if ok:
        return {"name": "Material rights", "ok": True,
                "detail": f"{len(materials)}素材、全てOK"}
    detail = f"{len(violations)}件の違反: " + "; ".join(violations[:5])
    if len(violations) > 5:
        detail += f" ... 他{len(violations) - 5}件"
    return {"name": "Material rights", "ok": False, "detail": detail}


def run_preflight(test_mode=False, materials=None):
    checks = [
        check_python(),
        check_packages(),
        check_ffmpeg(),
        check_ffprobe(),
        check_subtitle_support(),
        check_font(),
        check_voicevox(),
        check_voicevox_speed(),
        check_bgm(),
        check_output_writable(),
        check_zero_kb_inputs(),
        check_mode_separation(test_mode),
        check_materials_rights(materials),
    ]

    all_ok = True
    production_blockers = []
    for c in checks:
        status = "OK" if c["ok"] else "FAIL"
        print(f"  [{status}] {c['name']}: {c['detail']}")
        if not c["ok"]:
            if c["name"] in ("VOICEVOX", "BGM"):
                production_blockers.append(c["name"])
            elif c["name"] not in ("VOICEVOX", "BGM"):
                all_ok = False

    if test_mode:
        if not all_ok:
            print("\n[FAIL] Critical dependencies missing. Cannot proceed even in test mode.")
            return False, checks
        if production_blockers:
            print(f"\n[WARN] Production blockers: {', '.join(production_blockers)}")
            print("[INFO] Test mode: will use fallback audio. Output marked TEST_ONLY.")
        return True, checks
    else:
        if production_blockers:
            all_ok = False
        if not all_ok:
            print("\n[FAIL] Production preflight failed. Fix issues above before proceeding.")
            return False, checks
        print("\n[OK] All preflight checks passed.")
        return True, checks


if __name__ == "__main__":
    import sys
    test = "--test-mode" in sys.argv
    print("=" * 60)
    print(f"Preflight Check ({'TEST MODE' if test else 'PRODUCTION MODE'})")
    print("=" * 60)
    ok, _ = run_preflight(test_mode=test)
    sys.exit(0 if ok else 1)
