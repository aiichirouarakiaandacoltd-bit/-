"""
BGM management module for showa-heisei-video-automation.
Handles BGM file scanning, license validation, audio mixing, and credit generation.
"""

import json
import logging
import math
import os
import struct
import subprocess
import wave
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg")

LICENSE_TEMPLATE_ENTRY = {
    "file_name": "example.mp3",
    "source": "DOVA-SYNDROME",
    "source_url": "https://dova-s.jp/bgm/playXXXX.html",
    "license": "DOVA-SYNDROME利用規約",
    "commercial_use": True,
    "youtube_monetization": True,
    "credit_required": True,
    "credit_text": "BGM: 楽曲名 by 作曲者名 (DOVA-SYNDROME)",
    "content_id_risk": "none",
    "allowed_channels": "all",
}


@dataclass
class BgmLicenseEntry:
    """BGM楽曲のライセンス情報を保持するデータクラス。"""

    file_name: str
    source: str
    source_url: str
    license: str
    commercial_use: bool
    youtube_monetization: bool
    credit_required: bool
    credit_text: str
    content_id_risk: str  # "none", "low", "medium", "high"
    allowed_channels: Union[List[str], str] = "all"

    def __post_init__(self) -> None:
        valid_risks = ("none", "low", "medium", "high")
        if self.content_id_risk not in valid_risks:
            raise ValueError(
                f"content_id_risk が不正です: '{self.content_id_risk}' "
                f"(許可値: {valid_risks})"
            )
        if not isinstance(self.allowed_channels, (list, str)):
            raise TypeError(
                f"allowed_channels はリストまたは 'all' でなければなりません: "
                f"{type(self.allowed_channels)}"
            )

    @property
    def is_commercially_safe(self) -> bool:
        """商用利用およびYouTube収益化が許可されているか判定する。"""
        return self.commercial_use and self.youtube_monetization

    def is_allowed_for_channel(self, channel_name: str) -> bool:
        """指定チャンネルでの使用が許可されているか判定する。"""
        if self.allowed_channels == "all":
            return True
        if isinstance(self.allowed_channels, list):
            return channel_name in self.allowed_channels
        return False


class BGMError(Exception):
    """BGM関連のエラー基底クラス。"""
    pass


class BGMNotFoundError(BGMError):
    """有効なBGMファイルが見つからない場合のエラー。"""
    pass


class BGMLicenseError(BGMError):
    """ライセンス情報に問題がある場合のエラー。"""
    pass


class BGMMixError(BGMError):
    """音声ミキシング処理に失敗した場合のエラー。"""
    pass


class BGMManager:
    """BGMファイルの管理、ライセンス検証、ミキシングを行うクラス。"""

    def __init__(
        self,
        bgm_dir: str,
        config: Optional[Dict[str, Any]] = None,
        channel_name: str = "",
    ) -> None:
        self.bgm_dir = Path(bgm_dir)
        self.config = config or {}
        self.channel_name = channel_name

        # BGM設定をconfigから取得（デフォルト値付き）
        bgm_config = self.config.get("bgm", {})
        self.volume_ratio: float = bgm_config.get("volume_ratio", 0.20)
        self.ducking_enabled: bool = bgm_config.get("ducking_enabled", True)
        self.ducking_threshold: float = bgm_config.get("ducking_threshold", -20)
        self.ducking_ratio: float = bgm_config.get("ducking_ratio", 0.15)

        self._license_entries: Optional[List[BgmLicenseEntry]] = None
        self._used_bgm_files: List[str] = []

    @property
    def license_entries(self) -> List[BgmLicenseEntry]:
        """ライセンス情報を遅延読み込みして返す。"""
        if self._license_entries is None:
            self._license_entries = load_license_info(str(self.bgm_dir))
        return self._license_entries

    def select_and_mix(
        self,
        narration_path: str,
        output_path: str,
        mode: str = "production",
        duration: Optional[float] = None,
    ) -> str:
        """BGM選択からミキシングまでを一括実行する。

        Args:
            narration_path: ナレーション音声ファイルのパス
            output_path: 出力先パス
            mode: "production" または "test"
            duration: テストモード時のBGM長さ（秒）

        Returns:
            出力ファイルのパス
        """
        bgm_path = select_bgm(
            str(self.bgm_dir),
            mode=mode,
            duration=duration or 60.0,
            channel_name=self.channel_name,
        )

        if mode == "production":
            # 使用したBGMファイル名を記録
            bgm_filename = os.path.basename(bgm_path)
            if bgm_filename not in self._used_bgm_files:
                self._used_bgm_files.append(bgm_filename)

        mix_audio(narration_path, bgm_path, output_path, self.config)
        logger.info("BGMミキシング完了: %s", output_path)
        return output_path

    def get_credits(self) -> str:
        """使用済みBGMのクレジットテキストを取得する。"""
        return get_bgm_credits(str(self.bgm_dir), self._used_bgm_files)


# ---------------------------------------------------------------------------
# スキャン・ライセンス読み込み関数
# ---------------------------------------------------------------------------


def scan_bgm_files(bgm_dir: str) -> List[str]:
    """指定ディレクトリからBGMファイルを検索する。

    Args:
        bgm_dir: BGMファイルが格納されているディレクトリパス

    Returns:
        見つかったBGMファイルのフルパスリスト
    """
    bgm_path = Path(bgm_dir)
    if not bgm_path.is_dir():
        logger.warning("BGMディレクトリが存在しません: %s", bgm_dir)
        return []

    files: List[str] = []
    for entry in sorted(bgm_path.iterdir()):
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(str(entry))

    logger.info("BGMファイル %d 件を検出: %s", len(files), bgm_dir)
    return files


def load_license_info(bgm_dir: str) -> List[BgmLicenseEntry]:
    """bgm_license.json を読み込み、検証済みのライセンスエントリリストを返す。

    Args:
        bgm_dir: BGMディレクトリパス

    Returns:
        BgmLicenseEntry のリスト

    Raises:
        BGMLicenseError: ファイルが存在しない、またはフォーマットが不正な場合
    """
    license_path = Path(bgm_dir) / "bgm_license.json"

    if not license_path.is_file():
        raise BGMLicenseError(
            f"ライセンスファイルが見つかりません: {license_path}\n"
            f"generate_license_template() でテンプレートを生成してください。"
        )

    try:
        with open(license_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise BGMLicenseError(
            f"ライセンスファイルのJSON解析に失敗しました: {license_path}\n"
            f"エラー詳細: {e}"
        ) from e

    if not isinstance(data, list):
        raise BGMLicenseError(
            f"ライセンスファイルのルートはリストである必要があります: {license_path}"
        )

    required_fields = {
        "file_name", "source", "source_url", "license",
        "commercial_use", "youtube_monetization",
        "credit_required", "credit_text",
        "content_id_risk",
    }

    entries: List[BgmLicenseEntry] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise BGMLicenseError(
                f"ライセンスエントリ[{i}]が辞書ではありません: {type(item)}"
            )

        missing = required_fields - set(item.keys())
        if missing:
            raise BGMLicenseError(
                f"ライセンスエントリ[{i}] ({item.get('file_name', '不明')}) に "
                f"必須フィールドがありません: {missing}"
            )

        try:
            entry = BgmLicenseEntry(
                file_name=str(item["file_name"]),
                source=str(item["source"]),
                source_url=str(item["source_url"]),
                license=str(item["license"]),
                commercial_use=bool(item["commercial_use"]),
                youtube_monetization=bool(item["youtube_monetization"]),
                credit_required=bool(item["credit_required"]),
                credit_text=str(item["credit_text"]),
                content_id_risk=str(item["content_id_risk"]),
                allowed_channels=item.get("allowed_channels", "all"),
            )
            entries.append(entry)
        except (ValueError, TypeError) as e:
            raise BGMLicenseError(
                f"ライセンスエントリ[{i}] ({item.get('file_name', '不明')}) の "
                f"検証に失敗しました: {e}"
            ) from e

    logger.info("ライセンス情報 %d 件を読み込みました", len(entries))
    return entries


def get_valid_bgm(
    bgm_dir: str, channel_name: str = ""
) -> List[Tuple[str, BgmLicenseEntry]]:
    """商用利用可能かつYouTube収益化可能なBGMのみを返す。

    Args:
        bgm_dir: BGMディレクトリパス
        channel_name: チャンネル名（allowed_channels チェック用）

    Returns:
        (ファイルパス, ライセンスエントリ) のタプルリスト
    """
    available_files = scan_bgm_files(bgm_dir)
    if not available_files:
        return []

    try:
        license_entries = load_license_info(bgm_dir)
    except BGMLicenseError as e:
        logger.error("ライセンス情報の読み込みに失敗: %s", e)
        return []

    # ファイル名 -> ライセンスエントリのマッピング
    license_map: Dict[str, BgmLicenseEntry] = {
        entry.file_name: entry for entry in license_entries
    }

    valid: List[Tuple[str, BgmLicenseEntry]] = []
    for filepath in available_files:
        filename = os.path.basename(filepath)
        entry = license_map.get(filename)

        if entry is None:
            logger.warning(
                "BGMファイル '%s' のライセンス情報がありません。スキップします。",
                filename,
            )
            continue

        if not entry.is_commercially_safe:
            logger.info(
                "BGMファイル '%s' は商用利用または収益化が不可です。スキップします。",
                filename,
            )
            continue

        if channel_name and not entry.is_allowed_for_channel(channel_name):
            logger.info(
                "BGMファイル '%s' はチャンネル '%s' での使用が許可されていません。",
                filename,
                channel_name,
            )
            continue

        if entry.content_id_risk in ("medium", "high"):
            logger.warning(
                "BGMファイル '%s' のContent IDリスクが '%s' です。注意してください。",
                filename,
                entry.content_id_risk,
            )

        valid.append((filepath, entry))

    logger.info(
        "有効なBGM: %d / %d 件", len(valid), len(available_files)
    )
    return valid


# ---------------------------------------------------------------------------
# BGM選択・テストトーン生成
# ---------------------------------------------------------------------------


def select_bgm(
    bgm_dir: str,
    mode: str = "production",
    duration: float = 60.0,
    channel_name: str = "",
) -> str:
    """モードに応じてBGMを選択またはテストトーンを生成する。

    Args:
        bgm_dir: BGMディレクトリパス
        mode: "production" または "test"
        duration: テストBGMの長さ（秒）
        channel_name: チャンネル名

    Returns:
        選択されたBGMファイルのパス

    Raises:
        BGMNotFoundError: 本番モードで有効なBGMが見つからない場合
    """
    if mode == "test":
        test_output = os.path.join(bgm_dir, "_test_bgm_placeholder.wav")
        generate_test_bgm(test_output, duration)
        logger.info("テストモード: プレースホルダーBGMを生成しました: %s", test_output)
        return test_output

    # 本番モード
    valid_bgm = get_valid_bgm(bgm_dir, channel_name=channel_name)
    if not valid_bgm:
        raise BGMNotFoundError(
            "本番モードで使用可能なBGMファイルが見つかりません。\n"
            "assets/bgm/ に商用利用可能なBGMを追加し、\n"
            "bgm_license.json にライセンス情報を記載してください。\n"
            "不明なBGMの代用は安全上行いません。"
        )

    # Content IDリスクが低い順、ファイル名順でソートして最初のものを使用
    risk_order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    valid_bgm.sort(
        key=lambda x: (risk_order.get(x[1].content_id_risk, 99), x[1].file_name)
    )

    selected_path, selected_entry = valid_bgm[0]
    logger.info(
        "BGMを選択しました: %s (リスク: %s)",
        selected_entry.file_name,
        selected_entry.content_id_risk,
    )
    return selected_path


def generate_test_bgm(output_path: str, duration: float = 60.0) -> str:
    """テスト用の静かなサイン波BGMを生成する（TEST ONLY）。

    純粋なPython（wave + struct）で200Hzの低いサイン波を生成する。
    音量は非常に小さく設定される。

    Args:
        output_path: 出力WAVファイルのパス
        duration: 生成する長さ（秒）

    Returns:
        出力ファイルのパス
    """
    sample_rate = 44100
    frequency = 200.0  # Hz - 低い静かなトーン
    amplitude = 800  # 最大32767に対して非常に小さい値
    num_channels = 1
    sample_width = 2  # 16-bit

    num_samples = int(sample_rate * duration)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with wave.open(output_path, "w") as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)

        # チャンクごとに書き込んでメモリ使用量を抑える
        chunk_size = sample_rate  # 1秒分ずつ
        samples_written = 0

        while samples_written < num_samples:
            remaining = num_samples - samples_written
            current_chunk = min(chunk_size, remaining)
            frames = bytearray()

            for i in range(current_chunk):
                t = (samples_written + i) / sample_rate
                # フェードイン/フェードアウト（最初と最後の1秒）
                fade_in = min(1.0, (samples_written + i) / sample_rate)
                fade_out = min(1.0, (num_samples - samples_written - i) / sample_rate)
                fade = min(fade_in, fade_out)

                value = int(
                    amplitude * fade * math.sin(2.0 * math.pi * frequency * t)
                )
                frames.extend(struct.pack("<h", max(-32768, min(32767, value))))

            wav_file.writeframes(bytes(frames))
            samples_written += current_chunk

    logger.info(
        "テストBGM生成完了 (TEST ONLY): %s (%.1f秒, %dHz)",
        output_path,
        duration,
        frequency,
    )
    return output_path


# ---------------------------------------------------------------------------
# ライセンステンプレート生成
# ---------------------------------------------------------------------------


def generate_license_template(bgm_dir: str) -> str:
    """bgm_license.json のテンプレートを生成する。

    既存のBGMファイルが存在する場合、それらのファイル名を含むエントリを生成する。

    Args:
        bgm_dir: BGMディレクトリパス

    Returns:
        生成されたテンプレートファイルのパス
    """
    license_path = Path(bgm_dir) / "bgm_license.json"

    if license_path.exists():
        logger.warning(
            "bgm_license.json は既に存在します: %s (上書きしません)", license_path
        )
        return str(license_path)

    existing_files = scan_bgm_files(bgm_dir)
    entries: List[Dict[str, Any]] = []

    if existing_files:
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            entry = dict(LICENSE_TEMPLATE_ENTRY)
            entry["file_name"] = filename
            entry["credit_text"] = f"BGM: {filename} by 作曲者名 (ソース名)"
            entries.append(entry)
    else:
        entries.append(dict(LICENSE_TEMPLATE_ENTRY))

    os.makedirs(bgm_dir, exist_ok=True)

    with open(license_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    logger.info("ライセンステンプレートを生成しました: %s", license_path)
    return str(license_path)


# ---------------------------------------------------------------------------
# ffmpegミキシング
# ---------------------------------------------------------------------------


def _get_audio_duration(filepath: str) -> float:
    """ffprobeで音声ファイルの長さ（秒）を取得する。

    Args:
        filepath: 音声ファイルのパス

    Returns:
        再生時間（秒）

    Raises:
        BGMMixError: ffprobeの実行に失敗した場合
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise BGMMixError(
                f"ffprobeの実行に失敗しました: {filepath}\n"
                f"stderr: {result.stderr.strip()}"
            )
        return float(result.stdout.strip())
    except FileNotFoundError:
        raise BGMMixError(
            "ffprobeが見つかりません。FFmpegをインストールしてください。"
        )
    except subprocess.TimeoutExpired:
        raise BGMMixError(f"ffprobeがタイムアウトしました: {filepath}")
    except ValueError as e:
        raise BGMMixError(
            f"ffprobeの出力を数値に変換できませんでした: {filepath}\n"
            f"エラー詳細: {e}"
        ) from e


def build_ffmpeg_mix_filter(
    narration_path: str,
    bgm_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """ffmpegのfilter_complex文字列とコマンド引数を構築する。

    BGMをナレーションの長さに合わせてループし、ボリューム調整とダッキングを適用する。

    Args:
        narration_path: ナレーション音声ファイルのパス
        bgm_path: BGMファイルのパス
        output_path: 出力ファイルのパス
        config: 設定辞書

    Returns:
        dict with keys:
            "filter_complex": str - filter_complex文字列
            "command": list - ffmpegコマンド引数リスト
    """
    config = config or {}
    bgm_config = config.get("bgm", {})
    volume_ratio: float = bgm_config.get("volume_ratio", 0.20)
    ducking_enabled: bool = bgm_config.get("ducking_enabled", True)
    ducking_threshold: float = bgm_config.get("ducking_threshold", -20)
    ducking_ratio: float = bgm_config.get("ducking_ratio", 0.15)

    narration_duration = _get_audio_duration(narration_path)

    # filter_complex を構築
    # [0:a] = ナレーション, [1:a] = BGM
    filters: List[str] = []

    # BGMをループしてナレーション長に合わせる
    # aloop はサンプル数指定のため、-stream_loop で代替
    # BGMのボリュームを調整
    bgm_volume_filter = f"[1:a]volume={volume_ratio}[bgm_vol]"
    filters.append(bgm_volume_filter)

    if ducking_enabled:
        # サイドチェインコンプレッサーでダッキング
        # ナレーション音声をサイドチェイン入力としてBGMを圧縮
        sidechain_filter = (
            f"[bgm_vol][0:a]sidechaincompress="
            f"threshold={10 ** (ducking_threshold / 20):.6f}:"
            f"ratio={1 / ducking_ratio:.1f}:"
            f"attack=0.1:release=0.5[bgm_ducked]"
        )
        filters.append(sidechain_filter)
        mix_filter = "[0:a][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2[mixed]"
    else:
        mix_filter = "[0:a][bgm_vol]amix=inputs=2:duration=first:dropout_transition=2[mixed]"

    filters.append(mix_filter)
    filter_complex = ";".join(filters)

    # BGMのループ回数を計算
    bgm_duration = _get_audio_duration(bgm_path)
    loop_count = max(0, math.ceil(narration_duration / bgm_duration) - 1)

    command = [
        "ffmpeg",
        "-y",
        "-i", narration_path,
        "-stream_loop", str(loop_count),
        "-i", bgm_path,
        "-filter_complex", filter_complex,
        "-map", "[mixed]",
        "-codec:a", "aac",
        "-b:a", "192k",
        output_path,
    ]

    return {
        "filter_complex": filter_complex,
        "command": command,
    }


def mix_audio(
    narration_path: str,
    bgm_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """ffmpegを実行してナレーションとBGMをミキシングする。

    Args:
        narration_path: ナレーション音声ファイルのパス
        bgm_path: BGMファイルのパス
        output_path: 出力ファイルのパス
        config: 設定辞書

    Returns:
        出力ファイルのパス

    Raises:
        BGMMixError: ミキシングに失敗した場合
    """
    if not os.path.isfile(narration_path):
        raise BGMMixError(
            f"ナレーションファイルが見つかりません: {narration_path}"
        )
    if not os.path.isfile(bgm_path):
        raise BGMMixError(f"BGMファイルが見つかりません: {bgm_path}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    mix_info = build_ffmpeg_mix_filter(
        narration_path, bgm_path, output_path, config
    )
    command = mix_info["command"]

    logger.info("ffmpegミキシングコマンド: %s", " ".join(command))

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except FileNotFoundError:
        raise BGMMixError(
            "ffmpegが見つかりません。FFmpegをインストールしてください。"
        )
    except subprocess.TimeoutExpired:
        raise BGMMixError(
            "ffmpegの実行がタイムアウトしました（10分超過）。"
            "音声ファイルが大きすぎる可能性があります。"
        )

    if result.returncode != 0:
        raise BGMMixError(
            f"ffmpegミキシングに失敗しました (exit code: {result.returncode})\n"
            f"stderr: {result.stderr.strip()}"
        )

    if not os.path.isfile(output_path):
        raise BGMMixError(
            f"ミキシング出力ファイルが生成されませんでした: {output_path}"
        )

    logger.info("ミキシング完了: %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# クレジット
# ---------------------------------------------------------------------------


def get_bgm_credits(
    bgm_dir: str, used_files: Optional[List[str]] = None
) -> str:
    """使用済みBGMのクレジットテキストを生成する。

    実際に使用したBGMのみのクレジットを出力する。
    使用していないBGMや存在しないBGMのクレジットは絶対に出力しない。

    Args:
        bgm_dir: BGMディレクトリパス
        used_files: 実際に使用したBGMファイル名のリスト。
                     None の場合は空文字列を返す。

    Returns:
        クレジットテキスト（改行区切り）。使用BGMがない場合は空文字列。
    """
    if not used_files:
        return ""

    try:
        entries = load_license_info(bgm_dir)
    except BGMLicenseError as e:
        logger.warning("クレジット生成中にライセンス読み込みエラー: %s", e)
        return ""

    license_map = {entry.file_name: entry for entry in entries}
    credits: List[str] = []

    for filename in used_files:
        entry = license_map.get(filename)
        if entry is None:
            logger.warning(
                "使用済みBGM '%s' のライセンス情報がありません。"
                "クレジットをスキップします。",
                filename,
            )
            continue

        if entry.credit_required and entry.credit_text:
            credits.append(entry.credit_text)

    if not credits:
        return ""

    return "\n".join(credits)
