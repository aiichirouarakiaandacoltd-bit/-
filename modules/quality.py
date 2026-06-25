"""
Quality inspection module for showa-heisei-video-automation.
Runs comprehensive quality checks on output videos and generates reports.
"""

import json
import subprocess
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityResult:
    """個別の品質チェック結果を保持するデータクラス。"""
    check_name: str
    passed: bool
    details: str
    severity: str = "error"  # "error", "warning", "info"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# デフォルトの動画仕様
DEFAULT_VIDEO_SPECS = {
    "long": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "min_duration": 480,
        "max_duration": 720,
        "video_codec": "h264",
        "audio_codec": "aac",
        "pixel_format": "yuv420p",
    },
    "shorts": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "min_duration": 45,
        "max_duration": 59.5,
        "video_codec": "h264",
        "audio_codec": "aac",
        "pixel_format": "yuv420p",
    },
}


def _run_ffprobe(video_path: str, entries: str) -> dict[str, Any]:
    """ffprobeを実行して動画情報を取得する。

    Args:
        video_path: 動画ファイルのパス。
        entries: 取得するエントリ (例: "stream=width,height,codec_name")。

    Returns:
        ffprobeの出力をパースした辞書。

    Raises:
        RuntimeError: ffprobeの実行に失敗した場合。
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", entries,
        "-of", "json",
        str(video_path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffprobeの実行に失敗しました: {result.stderr.strip()}"
            )
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"ffprobeがタイムアウトしました: {video_path}"
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"ffprobeの出力をパースできません: {e}"
        )


def _get_stream_info(video_path: str) -> dict[str, Any]:
    """動画と音声の全ストリーム情報を取得する。"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffprobeの実行に失敗しました: {result.stderr.strip()}"
            )
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobeがタイムアウトしました: {video_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"ffprobeの出力をパースできません: {e}")


def _parse_frame_rate(rate_str: str) -> float:
    """フレームレート文字列 (例: "30/1") を浮動小数点数に変換する。"""
    if "/" in rate_str:
        num, den = rate_str.split("/")
        if float(den) == 0:
            return 0.0
        return float(num) / float(den)
    return float(rate_str)


def check_video_specs(
    video_path: str,
    expected_specs: dict[str, Any],
) -> list[QualityResult]:
    """ffprobeで動画の仕様を検証する。

    Args:
        video_path: 検査する動画ファイルのパス。
        expected_specs: 期待される仕様の辞書。

    Returns:
        QualityResultのリスト。
    """
    results: list[QualityResult] = []
    path = Path(video_path)

    if not path.exists():
        results.append(QualityResult(
            check_name="ファイル存在チェック",
            passed=False,
            details=f"ファイルが見つかりません: {video_path}",
            severity="error",
        ))
        return results

    if path.stat().st_size == 0:
        results.append(QualityResult(
            check_name="ファイルサイズチェック",
            passed=False,
            details=f"ファイルサイズが0バイトです: {video_path}",
            severity="error",
        ))
        return results

    try:
        info = _get_stream_info(video_path)
    except RuntimeError as e:
        results.append(QualityResult(
            check_name="ffprobe実行",
            passed=False,
            details=str(e),
            severity="error",
        ))
        return results

    streams = info.get("streams", [])
    format_info = info.get("format", {})

    # ビデオストリームの存在チェック
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    has_video = len(video_streams) > 0
    results.append(QualityResult(
        check_name="ビデオストリーム存在",
        passed=has_video,
        details="ビデオストリームが存在します" if has_video else "ビデオストリームがありません",
        severity="error",
    ))

    # オーディオストリームの存在チェック
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    has_audio = len(audio_streams) > 0
    results.append(QualityResult(
        check_name="オーディオストリーム存在",
        passed=has_audio,
        details="オーディオストリームが存在します" if has_audio else "オーディオストリームがありません",
        severity="error",
    ))

    if not has_video:
        return results

    vs = video_streams[0]

    # 解像度チェック
    actual_w = vs.get("width", 0)
    actual_h = vs.get("height", 0)
    expected_w = expected_specs.get("width", 1920)
    expected_h = expected_specs.get("height", 1080)
    res_ok = actual_w == expected_w and actual_h == expected_h
    results.append(QualityResult(
        check_name="解像度チェック",
        passed=res_ok,
        details=(
            f"解像度: {actual_w}x{actual_h} "
            f"(期待値: {expected_w}x{expected_h})"
        ),
        severity="error",
    ))

    # FPSチェック
    rate_str = vs.get("r_frame_rate", "0/1")
    actual_fps = _parse_frame_rate(rate_str)
    expected_fps = expected_specs.get("fps", 30)
    fps_ok = abs(actual_fps - expected_fps) < 0.5
    results.append(QualityResult(
        check_name="FPSチェック",
        passed=fps_ok,
        details=f"FPS: {actual_fps:.2f} (期待値: {expected_fps})",
        severity="error",
    ))

    # ビデオコーデックチェック
    actual_vcodec = vs.get("codec_name", "不明")
    expected_vcodec = expected_specs.get("video_codec", "h264")
    vcodec_ok = actual_vcodec == expected_vcodec
    results.append(QualityResult(
        check_name="ビデオコーデックチェック",
        passed=vcodec_ok,
        details=f"ビデオコーデック: {actual_vcodec} (期待値: {expected_vcodec})",
        severity="error",
    ))

    # ピクセルフォーマットチェック
    actual_pix = vs.get("pix_fmt", "不明")
    expected_pix = expected_specs.get("pixel_format", "yuv420p")
    pix_ok = actual_pix == expected_pix
    results.append(QualityResult(
        check_name="ピクセルフォーマットチェック",
        passed=pix_ok,
        details=f"ピクセルフォーマット: {actual_pix} (期待値: {expected_pix})",
        severity="error",
    ))

    # オーディオコーデックチェック
    if has_audio:
        # オーディオストリームのコーデックを別途取得
        audio_codec = audio_streams[0].get("codec_name", "不明")
        expected_acodec = expected_specs.get("audio_codec", "aac")
        acodec_ok = audio_codec == expected_acodec
        results.append(QualityResult(
            check_name="オーディオコーデックチェック",
            passed=acodec_ok,
            details=f"オーディオコーデック: {audio_codec} (期待値: {expected_acodec})",
            severity="error",
        ))

    # 尺チェック
    duration_str = format_info.get("duration", "0")
    try:
        actual_duration = float(duration_str)
    except (ValueError, TypeError):
        actual_duration = 0.0
    min_dur = expected_specs.get("min_duration", 0)
    max_dur = expected_specs.get("max_duration", float("inf"))
    dur_ok = min_dur <= actual_duration <= max_dur
    results.append(QualityResult(
        check_name="尺チェック",
        passed=dur_ok,
        details=(
            f"尺: {actual_duration:.1f}秒 "
            f"(範囲: {min_dur}-{max_dur}秒)"
        ),
        severity="error",
    ))

    return results


def check_decode(video_path: str) -> QualityResult:
    """デコードテストを実行して動画の整合性を検証する。

    ffmpeg -v error -i file.mp4 -f null - を実行し、
    エラーがなければPASSとする。

    Args:
        video_path: テストする動画ファイルのパス。

    Returns:
        デコードテストの結果。
    """
    path = Path(video_path)
    if not path.exists():
        return QualityResult(
            check_name="デコードテスト",
            passed=False,
            details=f"ファイルが見つかりません: {video_path}",
            severity="error",
        )

    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", str(video_path),
        "-f", "null",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        errors = result.stderr.strip()
        if errors:
            return QualityResult(
                check_name="デコードテスト",
                passed=False,
                details=f"デコードエラーが検出されました: {errors[:500]}",
                severity="error",
            )
        return QualityResult(
            check_name="デコードテスト",
            passed=True,
            details="デコードテストに合格しました",
            severity="info",
        )
    except subprocess.TimeoutExpired:
        return QualityResult(
            check_name="デコードテスト",
            passed=False,
            details=f"デコードテストがタイムアウトしました: {video_path}",
            severity="error",
        )
    except FileNotFoundError:
        return QualityResult(
            check_name="デコードテスト",
            passed=False,
            details="ffmpegが見つかりません。インストールしてください。",
            severity="error",
        )


def check_zero_files(directory: str) -> QualityResult:
    """出力ディレクトリ内の0バイトファイルを再帰的にチェックする。

    Args:
        directory: チェックするディレクトリのパス。

    Returns:
        0バイトファイルの有無に関する結果。
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return QualityResult(
            check_name="0バイトファイルチェック",
            passed=False,
            details=f"ディレクトリが見つかりません: {directory}",
            severity="error",
        )

    zero_files: list[str] = []
    try:
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size == 0:
                zero_files.append(str(file_path))
    except PermissionError as e:
        return QualityResult(
            check_name="0バイトファイルチェック",
            passed=False,
            details=f"ディレクトリの読み取り権限がありません: {e}",
            severity="error",
        )

    if zero_files:
        file_list = "\n  ".join(zero_files[:20])
        extra = ""
        if len(zero_files) > 20:
            extra = f"\n  ...他{len(zero_files) - 20}件"
        return QualityResult(
            check_name="0バイトファイルチェック",
            passed=False,
            details=f"0バイトファイルが{len(zero_files)}件見つかりました:\n  {file_list}{extra}",
            severity="error",
        )

    return QualityResult(
        check_name="0バイトファイルチェック",
        passed=True,
        details="0バイトファイルはありません",
        severity="info",
    )


def check_subtitle_burnin(ass_path: str) -> QualityResult:
    """字幕焼き込みの検証を行う。

    ASSファイルが存在し、正しい形式であることを確認する。

    Args:
        ass_path: ASSファイルのパス。

    Returns:
        字幕焼き込みの検証結果。
    """
    path = Path(ass_path)
    if not path.exists():
        return QualityResult(
            check_name="字幕焼き込みチェック",
            passed=False,
            details=f"ASSファイルが見つかりません: {ass_path}",
            severity="error",
        )

    if path.stat().st_size == 0:
        return QualityResult(
            check_name="字幕焼き込みチェック",
            passed=False,
            details=f"ASSファイルが空です: {ass_path}",
            severity="error",
        )

    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="shift_jis")
        except Exception as e:
            return QualityResult(
                check_name="字幕焼き込みチェック",
                passed=False,
                details=f"ASSファイルの読み込みに失敗しました: {e}",
                severity="error",
            )

    # ASSファイルの基本構造を検証
    has_script_info = "[Script Info]" in content
    has_events = "[Events]" in content
    has_dialogue = "Dialogue:" in content

    if not has_script_info:
        return QualityResult(
            check_name="字幕焼き込みチェック",
            passed=False,
            details="ASSファイルに[Script Info]セクションがありません",
            severity="error",
        )

    if not has_events:
        return QualityResult(
            check_name="字幕焼き込みチェック",
            passed=False,
            details="ASSファイルに[Events]セクションがありません",
            severity="error",
        )

    if not has_dialogue:
        return QualityResult(
            check_name="字幕焼き込みチェック",
            passed=False,
            details="ASSファイルにDialogue行がありません",
            severity="warning",
        )

    # Dialogue行の数をカウント
    dialogue_count = content.count("Dialogue:")
    return QualityResult(
        check_name="字幕焼き込みチェック",
        passed=True,
        details=f"ASSファイルが検証されました (Dialogue行: {dialogue_count}件)",
        severity="info",
    )


def check_production_constraints(status: dict[str, Any]) -> list[QualityResult]:
    """本番モードの制約を検証する。

    Args:
        status: パイプラインのステータス辞書。以下のキーを参照する:
            - voicevox: VOICEVOXの使用情報
            - bgm: BGMの使用情報とライセンス
            - materials: 素材リスト (ok/review/ng)
            - facts: ファクトチェック結果

    Returns:
        QualityResultのリスト。
    """
    results: list[QualityResult] = []

    # VOICEVOXの使用チェック
    voicevox_info = status.get("voicevox", {})
    voicevox_used = voicevox_info.get("used", False)
    is_test_audio = voicevox_info.get("test_audio", False)

    if voicevox_used and not is_test_audio:
        results.append(QualityResult(
            check_name="VOICEVOX使用チェック",
            passed=True,
            details=(
                f"VOICEVOXが使用されています "
                f"(話者: {voicevox_info.get('speaker', '不明')}, "
                f"スタイル: {voicevox_info.get('style', '不明')})"
            ),
            severity="info",
        ))
    else:
        reason = "テスト音声が使用されています" if is_test_audio else "VOICEVOXが使用されていません"
        results.append(QualityResult(
            check_name="VOICEVOX使用チェック",
            passed=False,
            details=f"本番音声が必要です: {reason}",
            severity="error",
        ))

    # BGMライセンスチェック
    bgm_info = status.get("bgm", {})
    bgm_file = bgm_info.get("file", "")
    bgm_license = bgm_info.get("license", "")

    if bgm_file and bgm_license:
        valid_licenses = [
            "CC0", "CC-BY", "CC BY", "CC-BY-SA", "CC BY-SA",
            "フリー", "ロイヤリティフリー", "royalty-free",
            "パブリックドメイン", "public domain",
            "商用利用可", "許諾済み",
        ]
        license_valid = any(
            lic.lower() in bgm_license.lower() for lic in valid_licenses
        )
        results.append(QualityResult(
            check_name="BGMライセンスチェック",
            passed=license_valid,
            details=(
                f"BGM: {bgm_file}, ライセンス: {bgm_license}"
                if license_valid
                else f"BGMライセンスが不明または無効です: {bgm_license}"
            ),
            severity="error" if not license_valid else "info",
        ))
    else:
        results.append(QualityResult(
            check_name="BGMライセンスチェック",
            passed=False,
            details="BGM情報またはライセンス情報がありません",
            severity="error",
        ))

    # REVIEW/NG素材チェック
    materials = status.get("materials", {})
    review_count = materials.get("review", 0)
    ng_count = materials.get("ng", 0)

    if isinstance(materials, list):
        # リスト形式の場合はステータスで分類
        review_count = sum(1 for m in materials if m.get("status") == "REVIEW")
        ng_count = sum(1 for m in materials if m.get("status") == "NG")

    no_problematic = review_count == 0 and ng_count == 0
    results.append(QualityResult(
        check_name="REVIEW/NG素材チェック",
        passed=no_problematic,
        details=(
            "REVIEW/NG素材はありません"
            if no_problematic
            else f"問題のある素材があります (REVIEW: {review_count}件, NG: {ng_count}件)"
        ),
        severity="error" if not no_problematic else "info",
    ))

    # ファクトチェック結果の検証
    facts = status.get("facts", {})
    unconfirmed = facts.get("unconfirmed", 0)
    rejected = facts.get("rejected", 0)

    if isinstance(facts, list):
        unconfirmed = sum(
            1 for f in facts if f.get("status") == "UNCONFIRMED"
        )
        rejected = sum(
            1 for f in facts if f.get("status") == "REJECTED"
        )

    facts_ok = rejected == 0 and unconfirmed == 0
    confirmed = facts.get("confirmed", 0) if isinstance(facts, dict) else 0
    partial = facts.get("partial", 0) if isinstance(facts, dict) else 0

    if isinstance(facts, list):
        confirmed = sum(
            1 for f in facts if f.get("status") == "CONFIRMED"
        )
        partial = sum(
            1 for f in facts if f.get("status") == "PARTIAL"
        )

    results.append(QualityResult(
        check_name="ファクトチェック結果",
        passed=facts_ok,
        details=(
            f"確認済み: {confirmed}件, 部分確認: {partial}件"
            if facts_ok
            else f"未確認: {unconfirmed}件, 却下: {rejected}件が残っています"
        ),
        severity="error" if rejected > 0 else ("warning" if unconfirmed > 0 else "info"),
    ))

    return results


def generate_screenshots(
    video_path: str,
    output_dir: str,
    format_type: str = "long",
) -> list[QualityResult]:
    """動画からスクリーンショットを抽出する。

    long動画: 開始(5秒), 中間, 終了(-5秒) の3枚
    shorts: 中間の1枚

    Args:
        video_path: 動画ファイルのパス。
        output_dir: スクリーンショットの出力先ディレクトリ。
        format_type: "long" または "shorts"。

    Returns:
        QualityResultのリスト。
    """
    results: list[QualityResult] = []
    path = Path(video_path)
    out_dir = Path(output_dir)

    if not path.exists():
        results.append(QualityResult(
            check_name="スクリーンショット生成",
            passed=False,
            details=f"動画ファイルが見つかりません: {video_path}",
            severity="warning",
        ))
        return results

    out_dir.mkdir(parents=True, exist_ok=True)

    # 動画の尺を取得
    try:
        probe_result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json", str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        duration_info = json.loads(probe_result.stdout)
        duration = float(duration_info.get("format", {}).get("duration", 0))
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as e:
        results.append(QualityResult(
            check_name="スクリーンショット生成",
            passed=False,
            details=f"動画の尺を取得できません: {e}",
            severity="warning",
        ))
        return results

    if duration <= 0:
        results.append(QualityResult(
            check_name="スクリーンショット生成",
            passed=False,
            details="動画の尺が0秒以下です",
            severity="warning",
        ))
        return results

    # スクリーンショットのタイムスタンプを決定
    video_stem = path.stem
    if format_type == "long":
        timestamps = {
            "start": 5.0,
            "middle": duration / 2,
            "end": max(duration - 5.0, 0),
        }
    else:
        timestamps = {
            "middle": duration / 2,
        }

    generated_files: list[str] = []
    for label, ts in timestamps.items():
        output_file = out_dir / f"{video_stem}_screenshot_{label}.png"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_file),
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and output_file.exists():
                generated_files.append(str(output_file))
            else:
                logger.warning(
                    "スクリーンショットの生成に失敗しました (%s, %.1f秒): %s",
                    label, ts, result.stderr.strip()[:200],
                )
        except subprocess.TimeoutExpired:
            logger.warning(
                "スクリーンショット生成がタイムアウトしました (%s, %.1f秒)",
                label, ts,
            )
        except FileNotFoundError:
            results.append(QualityResult(
                check_name="スクリーンショット生成",
                passed=False,
                details="ffmpegが見つかりません。インストールしてください。",
                severity="warning",
            ))
            return results

    expected_count = 3 if format_type == "long" else 1
    all_generated = len(generated_files) == expected_count
    results.append(QualityResult(
        check_name="スクリーンショット生成",
        passed=all_generated,
        details=(
            f"スクリーンショットを{len(generated_files)}/{expected_count}枚生成しました"
            + (f": {', '.join(generated_files)}" if generated_files else "")
        ),
        severity="warning" if not all_generated else "info",
    ))

    return results


def generate_report(
    results: list[QualityResult],
    output_path: str,
    mode: str = "test",
) -> None:
    """品質レポートをJSONファイルとして書き出す。

    Args:
        results: QualityResultのリスト。
        output_path: 出力ファイルのパス。
        mode: "production" or "test"。
    """
    overall_pass = all(
        r.passed for r in results if r.severity == "error"
    )
    is_production = mode == "production"

    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "overall_status": "PASS" if overall_pass else "FAIL",
        "overall_pass": overall_pass,
        "publishable": is_production and overall_pass,
        "test_only": not is_production,
        "total_checks": len(results),
        "passed_checks": sum(1 for r in results if r.passed),
        "failed_checks": sum(1 for r in results if not r.passed),
        "results": [r.to_dict() for r in results],
        "summary": "PASS" if overall_pass else "FAIL",
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("品質レポートを出力しました: %s", output_path)
    except OSError as e:
        logger.error("品質レポートの書き出しに失敗しました: %s", e)
        raise RuntimeError(f"品質レポートの書き出しに失敗しました: {e}")


class QualityChecker:
    """動画の品質検査を行うクラス。

    全ての品質チェックを統合し、レポートを生成する。
    """

    def __init__(
        self,
        output_dir: str,
        config: Optional[dict[str, Any]] = None,
        status: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Args:
            output_dir: 出力ディレクトリのパス。
            config: 動画設定 (video.long, video.shorts のキーを含む)。
            status: パイプラインのステータス辞書。
        """
        self.output_dir = Path(output_dir)
        self.config = config or {}
        self.status = status or {}
        self.results: list[QualityResult] = []

    def _get_specs(self, format_type: str) -> dict[str, Any]:
        """設定から動画仕様を取得する。設定がない場合はデフォルト値を使う。"""
        video_config = self.config.get("video", {})
        user_specs = video_config.get(format_type, {})

        defaults = DEFAULT_VIDEO_SPECS.get(format_type, DEFAULT_VIDEO_SPECS["long"])
        specs = dict(defaults)
        specs.update(user_specs)
        return specs

    def _find_video_files(self) -> dict[str, list[Path]]:
        """出力ディレクトリ内のMP4ファイルをlong/shortsに分類して返す。"""
        videos: dict[str, list[Path]] = {"long": [], "shorts": []}

        if not self.output_dir.exists():
            logger.warning("出力ディレクトリが存在しません: %s", self.output_dir)
            return videos

        for mp4 in self.output_dir.rglob("*.mp4"):
            mp4_str = str(mp4).lower()
            if "short" in mp4_str:
                videos["shorts"].append(mp4)
            else:
                videos["long"].append(mp4)

        return videos

    def _find_ass_files(self) -> list[Path]:
        """出力ディレクトリ内のASSファイルを検索する。"""
        if not self.output_dir.exists():
            return []
        return list(self.output_dir.rglob("*.ass"))

    def run_full_check(
        self,
        output_dir: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
        status: Optional[dict[str, Any]] = None,
    ) -> list[QualityResult]:
        """全ての品質チェックを実行する。

        Args:
            output_dir: 出力ディレクトリ (省略時はコンストラクタの値を使用)。
            config: 動画設定 (省略時はコンストラクタの値を使用)。
            status: ステータス辞書 (省略時はコンストラクタの値を使用)。

        Returns:
            全てのQualityResultのリスト。
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        if config:
            self.config = config
        if status:
            self.status = status

        self.results = []
        logger.info("品質検査を開始します: %s", self.output_dir)

        # 動画ファイルの検索
        videos = self._find_video_files()
        total_videos = sum(len(v) for v in videos.values())

        if total_videos == 0:
            self.results.append(QualityResult(
                check_name="動画ファイル検索",
                passed=False,
                details=f"MP4ファイルが見つかりません: {self.output_dir}",
                severity="error",
            ))
        else:
            self.results.append(QualityResult(
                check_name="動画ファイル検索",
                passed=True,
                details=(
                    f"MP4ファイルを{total_videos}件検出しました "
                    f"(long: {len(videos['long'])}件, shorts: {len(videos['shorts'])}件)"
                ),
                severity="info",
            ))

        # 各動画の仕様チェックとデコードテスト
        for format_type, video_list in videos.items():
            specs = self._get_specs(format_type)
            for video_path in video_list:
                logger.info(
                    "%s動画を検査中: %s", format_type, video_path.name,
                )
                # 仕様チェック
                spec_results = check_video_specs(str(video_path), specs)
                self.results.extend(spec_results)

                # デコードテスト
                decode_result = check_decode(str(video_path))
                self.results.append(decode_result)

                # スクリーンショット生成
                screenshot_dir = self.output_dir / "screenshots"
                screenshot_results = generate_screenshots(
                    str(video_path), str(screenshot_dir), format_type,
                )
                self.results.extend(screenshot_results)

        # 0バイトファイルチェック
        zero_result = check_zero_files(str(self.output_dir))
        self.results.append(zero_result)

        # 字幕焼き込みチェック
        ass_files = self._find_ass_files()
        if ass_files:
            for ass_file in ass_files:
                subtitle_result = check_subtitle_burnin(str(ass_file))
                self.results.append(subtitle_result)
        else:
            self.results.append(QualityResult(
                check_name="字幕焼き込みチェック",
                passed=False,
                details="ASSファイルが見つかりません",
                severity="warning",
            ))

        # 本番モード制約チェック
        mode = self.status.get("mode", "test")
        if mode == "production":
            production_results = check_production_constraints(self.status)
            self.results.extend(production_results)
        else:
            self.results.append(QualityResult(
                check_name="本番モードチェック",
                passed=True,
                details=f"テストモードで実行中のため、本番制約チェックをスキップしました (mode: {mode})",
                severity="info",
            ))

        # レポート生成
        report_path = self.output_dir / "quality_report.json"
        generate_report(self.results, str(report_path), mode=mode)

        overall = all(r.passed for r in self.results if r.severity == "error")
        logger.info(
            "品質検査が完了しました: %s (%d/%d チェック合格)",
            "PASS" if overall else "FAIL",
            sum(1 for r in self.results if r.passed),
            len(self.results),
        )

        return self.results

    @property
    def overall_pass(self) -> bool:
        """全てのエラーレベルチェックが合格しているか。"""
        if not self.results:
            return False
        return all(r.passed for r in self.results if r.severity == "error")
