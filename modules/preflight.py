"""
Preflight checker for showa-heisei-video-automation.
Verifies all dependencies, services, and resources before production run.
"""

import os
import sys
import shutil
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


def check_python_version():
    """Check Python version >= 3.9."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v.major >= 3 and v.minor >= 9:
        return True, f"Python {version_str}"
    return False, f"Python {version_str} (3.9以上が必要です)"


def check_required_packages():
    """Check that required Python packages are importable."""
    packages = {
        "yaml": "pyyaml",
        "requests": "requests",
        "PIL": "Pillow",
    }
    results = []
    for import_name, pip_name in packages.items():
        try:
            mod = __import__(import_name)
            version = getattr(mod, "__version__", "不明")
            results.append((True, f"{pip_name} ({version})"))
        except ImportError:
            results.append((False, f"{pip_name} 未インストール",
                            f"pip install {pip_name} を実行してください"))
    return results


def check_ffmpeg():
    """Check FFmpeg availability and version."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        first_line = result.stdout.split("\n")[0]
        # e.g. "ffmpeg version 6.1.1 ..."
        parts = first_line.split()
        version = parts[2] if len(parts) >= 3 else "不明"
        return True, f"FFmpeg {version}"
    except FileNotFoundError:
        return False, "FFmpeg 未インストール", "FFmpegをインストールしてください"
    except Exception as e:
        return False, f"FFmpeg エラー: {e}", "FFmpegのインストールを確認してください"


def check_ffprobe():
    """Check ffprobe availability and version."""
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True, text=True, timeout=10
        )
        first_line = result.stdout.split("\n")[0]
        parts = first_line.split()
        version = parts[2] if len(parts) >= 3 else "不明"
        return True, f"ffprobe {version}"
    except FileNotFoundError:
        return False, "ffprobe 未インストール", "FFmpegをインストールしてください（ffprobeが含まれます）"
    except Exception as e:
        return False, f"ffprobe エラー: {e}", "FFmpegのインストールを確認してください"


def check_libass():
    """Check that FFmpeg has libass/subtitles filter support."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        if "ass" in output.lower() or "subtitles" in output.lower():
            return True, "libass (字幕フィルター対応)"
        return False, "libass 未対応", "FFmpegをlibass付きでビルドしてください"
    except Exception:
        return False, "libass 確認不可", "FFmpegのインストールを確認してください"


def check_japanese_font(config):
    """Check that the configured Japanese font file exists."""
    font_path = config.get("subtitles", {}).get(
        "font_path", "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
    )
    font_family = config.get("subtitles", {}).get(
        "font_family", "Noto Sans CJK JP Black"
    )
    if os.path.isfile(font_path):
        return True, f"日本語フォント ({font_family})"
    return (False,
            f"日本語フォント未検出 ({font_family})",
            f"フォントを {font_path} に配置してください")


def check_voicevox_connection(config):
    """Try connecting to VOICEVOX /version endpoint."""
    import requests
    host = config.get("voicevox", {}).get("host", "http://localhost:50021")
    try:
        resp = requests.get(f"{host}/version", timeout=5)
        if resp.status_code == 200:
            version = resp.text.strip().strip('"')
            return True, f"VOICEVOX {version} ({host})"
        return (False, "VOICEVOX応答異常",
                f"VOICEVOXを起動してください ({host})")
    except requests.ConnectionError:
        return (False, "VOICEVOX未接続",
                f"VOICEVOXを起動してください ({host})")
    except Exception as e:
        return (False, f"VOICEVOX接続エラー: {e}",
                f"VOICEVOXを起動してください ({host})")


def check_voicevox_speaker(config, speakers_config):
    """Check that the configured VOICEVOX speaker/style is available."""
    import requests
    host = config.get("voicevox", {}).get("host", "http://localhost:50021")
    primary = speakers_config.get("voicevox", {}).get("primary", {})
    target_speaker = primary.get("speaker_name", "四国めたん")
    target_style = primary.get("style_name", "ノーマル")

    try:
        resp = requests.get(f"{host}/speakers", timeout=5)
        if resp.status_code != 200:
            return (False, "VOICEVOXスピーカー一覧取得失敗",
                    "VOICEVOXの状態を確認してください")
        speakers = resp.json()
        for speaker in speakers:
            if speaker.get("name") == target_speaker:
                for style in speaker.get("styles", []):
                    if style.get("name") == target_style:
                        style_id = style.get("id", "?")
                        return (True,
                                f"VOICEVOXスピーカー: {target_speaker} "
                                f"({target_style}, ID:{style_id})")
                # Speaker found but style not found
                available = [s.get("name") for s in speaker.get("styles", [])]
                return (False,
                        f"VOICEVOXスタイル未検出: {target_style}",
                        f"利用可能スタイル: {', '.join(available)}")
        # Speaker not found
        available_speakers = [s.get("name") for s in speakers[:10]]
        return (False,
                f"VOICEVOXスピーカー未検出: {target_speaker}",
                f"利用可能スピーカー(一部): {', '.join(available_speakers)}")
    except requests.ConnectionError:
        return (False, "VOICEVOXスピーカー確認不可（未接続）",
                f"VOICEVOXを起動してください ({host})")
    except Exception as e:
        return (False, f"VOICEVOXスピーカー確認エラー: {e}",
                "VOICEVOXの状態を確認してください")


def check_bgm_files(project_root):
    """Check for BGM files in assets/bgm/."""
    bgm_dir = os.path.join(project_root, "assets", "bgm")
    if not os.path.isdir(bgm_dir):
        return (False, "BGMディレクトリなし",
                f"{bgm_dir} ディレクトリを作成してBGMファイルを配置してください")
    audio_exts = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
    bgm_files = [
        f for f in os.listdir(bgm_dir)
        if os.path.splitext(f)[1].lower() in audio_exts
    ]
    if bgm_files:
        return True, f"BGMファイル ({len(bgm_files)}件: {', '.join(bgm_files[:3])})"
    return (False, "BGMファイルなし",
            f"assets/bgm/ にBGMファイルを配置してください")


def check_bgm_license(project_root):
    """Check for BGM license file."""
    license_path = os.path.join(project_root, "assets", "bgm", "bgm_license.json")
    if os.path.isfile(license_path):
        try:
            with open(license_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else 1
            return True, f"BGM権利情報 ({count}件)"
        except (json.JSONDecodeError, Exception):
            return (False, "BGM権利情報 (JSONエラー)",
                    "assets/bgm/bgm_license.json のJSON形式を確認してください")
    return (False, "BGM権利情報なし",
            "assets/bgm/ にBGMファイルとbgm_license.jsonを配置してください")


def check_output_directory(project_root, mode):
    """Check output directory write permission."""
    if mode == "production":
        out_dir = os.path.join(project_root, "outputs", "production")
    else:
        out_dir = os.path.join(project_root, "outputs", "test")
    os.makedirs(out_dir, exist_ok=True)
    if os.access(out_dir, os.W_OK):
        return True, f"出力ディレクトリ書き込み可 ({out_dir})"
    return (False, f"出力ディレクトリ書き込み不可 ({out_dir})",
            f"{out_dir} の書き込み権限を確認してください")


def check_disk_space(project_root):
    """Check disk space (warn if < 1GB)."""
    try:
        usage = shutil.disk_usage(project_root)
        free_gb = usage.free / (1024 ** 3)
        if free_gb >= 1.0:
            return True, f"ディスク空き容量 {free_gb:.1f}GB"
        return (False, f"ディスク空き容量不足 ({free_gb:.2f}GB)",
                "ディスク空き容量を1GB以上確保してください")
    except Exception as e:
        return (False, f"ディスク容量確認エラー: {e}",
                "ディスク容量を手動で確認してください")


def check_script_file(script_file):
    """Check that script file exists if specified."""
    if not script_file:
        return True, "スクリプトファイル (指定なし、トピックモード)"
    if os.path.isfile(script_file):
        size = os.path.getsize(script_file)
        return True, f"スクリプトファイル ({script_file}, {size}bytes)"
    return (False, f"スクリプトファイル未検出 ({script_file})",
            f"指定されたスクリプトファイルを確認してください: {script_file}")


def run_preflight(config, speakers_config, project_root, mode="production",
                  script_file=None):
    """
    Run all preflight checks and return results dict.

    Returns:
        dict with keys:
            pass_items: list of str (passed check descriptions)
            fail_items: list of str (failed check descriptions)
            fixes: list of str (fix suggestions for failures)
            passed: bool (overall pass/fail)
    """
    pass_items = []
    fail_items = []
    fixes = []

    # Items that are warnings-only in test mode
    test_mode_warning_checks = set()

    def record(result, warning_only_in_test=False):
        """Record a check result (2-tuple for pass, 3-tuple for fail)."""
        if isinstance(result, list):
            for r in result:
                record(r, warning_only_in_test)
            return
        if result[0]:
            pass_items.append(result[1])
        else:
            if warning_only_in_test and mode == "test":
                pass_items.append(f"{result[1]} (警告のみ)")
            else:
                fail_items.append(result[1])
            if len(result) >= 3:
                fixes.append(result[2])

    # Run all checks
    record(check_python_version())
    record(check_required_packages())
    record(check_ffmpeg())
    record(check_ffprobe())
    record(check_libass())
    record(check_japanese_font(config))
    record(check_voicevox_connection(config), warning_only_in_test=True)
    record(check_voicevox_speaker(config, speakers_config),
           warning_only_in_test=True)
    record(check_bgm_files(project_root), warning_only_in_test=True)
    record(check_bgm_license(project_root), warning_only_in_test=True)
    record(check_output_directory(project_root, mode))
    record(check_disk_space(project_root))
    record(check_script_file(script_file))

    passed = len(fail_items) == 0

    return {
        "pass_items": pass_items,
        "fail_items": fail_items,
        "fixes": fixes,
        "passed": passed,
    }


def format_preflight_report(results):
    """Format preflight results as human-readable text."""
    lines = []

    if results["pass_items"]:
        lines.append("PASS:")
        for item in results["pass_items"]:
            lines.append(f"  - {item}")

    if results["fail_items"]:
        if lines:
            lines.append("")
        lines.append("FAIL:")
        for item in results["fail_items"]:
            lines.append(f"  - {item}")

    if results["fixes"]:
        lines.append("")
        lines.append("修正方法:")
        # Deduplicate fixes
        seen = set()
        for fix in results["fixes"]:
            if fix not in seen:
                seen.add(fix)
                lines.append(f"  - {fix}")

    lines.append("")
    if results["passed"]:
        lines.append("結果: すべてのチェックに合格しました。")
    else:
        lines.append("結果: 一部のチェックに失敗しました。上記の修正方法を参照してください。")

    return "\n".join(lines)
