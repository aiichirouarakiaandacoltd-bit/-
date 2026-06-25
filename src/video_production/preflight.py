"""統合事前検証モジュール

パイプライン実行前に全環境を一括チェックし、結果をまとめて返す。
一項目ずつ止めるのではなく、全項目を検査してから判定する。
"""

import shutil
import subprocess
from pathlib import Path

import requests

from . import config


def run_preflight(
    test_mode: bool = False,
    bgm_path: Path | None = None,
) -> dict:
    """全環境チェックを実行し結果dictを返す。"""
    result = {
        "checks": [],
        "passed": True,
        "errors": [],
        "voicevox": None,
        "bgm": None,
    }

    def _ok(name, detail):
        result["checks"].append({"name": name, "ok": True, "detail": detail})

    def _fail(name, detail):
        result["checks"].append({"name": name, "ok": False, "detail": detail})
        result["errors"].append(f"{name}: {detail}")
        result["passed"] = False

    def _warn(name, detail):
        result["checks"].append({"name": name, "ok": True, "detail": f"[WARN] {detail}"})

    if shutil.which("ffmpeg"):
        _ok("FFmpeg", "インストール済み")
    else:
        _fail("FFmpeg", "見つかりません")

    if shutil.which("ffprobe"):
        _ok("ffprobe", "インストール済み")
    else:
        _fail("ffprobe", "見つかりません")

    try:
        r = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True, timeout=10,
        )
        if "subtitles" in r.stdout or "ass" in r.stderr.lower():
            _ok("libass（字幕）", "利用可能")
        else:
            _warn("libass（字幕）", "subtitlesフィルタが未確認")
    except Exception:
        _warn("libass（字幕）", "確認不可")

    if shutil.which("espeak-ng"):
        _ok("espeak-ng", "インストール済み")
    else:
        if test_mode:
            _fail("espeak-ng", "テストモードで必要ですが見つかりません")
        else:
            _warn("espeak-ng", "未インストール（本番では不要）")

    vv_info = {"available": False, "speaker_found": False, "style_id": None, "version": None}
    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/version", timeout=3)
        if r.status_code == 200:
            vv_info["version"] = r.text.strip().strip('"')
    except Exception:
        pass

    try:
        r = requests.get(f"{config.VOICEVOX_HOST}/speakers", timeout=5)
        if r.status_code == 200:
            vv_info["available"] = True
            speakers = r.json()
            for sp in speakers:
                if sp.get("name") == config.VOICEVOX_SPEAKER_NAME:
                    for style in sp.get("styles", []):
                        if style.get("name") == config.VOICEVOX_STYLE_NAME:
                            vv_info["speaker_found"] = True
                            vv_info["style_id"] = style["id"]
                            break
                    break
    except Exception:
        pass

    result["voicevox"] = vv_info

    if vv_info["available"]:
        _ok("VOICEVOX API", f"接続OK (v{vv_info['version']})")
        if vv_info["speaker_found"]:
            _ok("VOICEVOX話者", f"{config.VOICEVOX_SPEAKER_NAME} (ID={vv_info['style_id']})")
        else:
            if not test_mode:
                _fail("VOICEVOX話者", f"{config.VOICEVOX_SPEAKER_NAME}が見つかりません")
            else:
                _warn("VOICEVOX話者", f"{config.VOICEVOX_SPEAKER_NAME}未検出（テストモード: espeak-ng使用）")
    else:
        if not test_mode:
            _fail("VOICEVOX API", f"接続不可: {config.VOICEVOX_HOST}")
        else:
            _warn("VOICEVOX API", f"接続不可（テストモード: espeak-ng使用）")

    bgm_file = bgm_path or (config.BGM_DIR / config.BGM_FILE)
    bgm_info = {"path": str(bgm_file), "exists": False, "nonzero": False, "readable": False}

    if bgm_file.exists():
        bgm_info["exists"] = True
        size = bgm_file.stat().st_size
        bgm_info["nonzero"] = size > 0
        if size > 0:
            try:
                subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(bgm_file)],
                    capture_output=True, text=True, check=True, timeout=10,
                )
                bgm_info["readable"] = True
            except Exception:
                pass

    result["bgm"] = bgm_info

    if bgm_info["exists"] and bgm_info["nonzero"] and bgm_info["readable"]:
        _ok("BGMファイル", f"{bgm_file.name}")
    else:
        if not test_mode:
            _fail("BGMファイル", f"利用不可: {bgm_file}")
        else:
            _warn("BGMファイル", f"未配置: {bgm_file}（テストモード: BGMなしで続行）")

    for d in [config.OUTPUTS_DIR, config.OUTPUTS_TEST_DIR]:
        try:
            d.mkdir(parents=True, exist_ok=True)
            test_file = d / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            _ok(f"書き込み権限 ({d.name})", "OK")
        except Exception as e:
            _fail(f"書き込み権限 ({d.name})", str(e))

    return result


def print_preflight_report(result: dict):
    print(f"\n{'='*50}")
    print("環境事前検証レポート")
    print(f"{'='*50}")

    for check in result["checks"]:
        icon = "OK" if check["ok"] else "NG"
        print(f"  [{icon}] {check['name']}: {check['detail']}")

    status = "PASSED" if result["passed"] else "FAILED"
    print(f"\n  結果: {status}")
    if result["errors"]:
        print(f"  エラー数: {len(result['errors'])}")
        for e in result["errors"]:
            print(f"    - {e}")
    print(f"{'='*50}\n")
