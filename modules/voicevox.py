"""
VOICEVOX TTS モジュール - 昭和・平成動画自動生成システム用
音声合成（VOICEVOX API連携）およびテスト用音声生成を提供する。
"""

import json
import logging
import math
import os
import struct
import subprocess
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import requests
import yaml

logger = logging.getLogger(__name__)

# テストモード用の警告マーク
TEST_WATERMARK = "TEST ONLY - 投稿不可 - 技術検証用"

# テスト音声の推定パラメータ: 1文字あたりの秒数（日本語）
CHARS_PER_SECOND = 5.0
TEST_SAMPLE_RATE = 44100
TEST_FREQUENCY = 440  # Hz


@dataclass
class AudioSegment:
    """生成された音声セグメントの情報。"""
    text: str
    wav_path: str
    actual_duration_seconds: float
    is_test: bool = False


@dataclass
class AudioResult:
    """音声生成の全体結果。"""
    segments: List[AudioSegment] = field(default_factory=list)
    concatenated_path: Optional[str] = None
    total_duration_seconds: float = 0.0
    is_test: bool = False


def _load_config(config_dir: Optional[str] = None) -> dict:
    """settings.yaml を読み込む。"""
    if config_dir is None:
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config"
        )
    settings_path = os.path.join(config_dir, "settings.yaml")
    if not os.path.isfile(settings_path):
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {settings_path}"
        )
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_speakers_config(config_dir: Optional[str] = None) -> dict:
    """speakers.yaml を読み込む。"""
    if config_dir is None:
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config"
        )
    speakers_path = os.path.join(config_dir, "speakers.yaml")
    if not os.path.isfile(speakers_path):
        raise FileNotFoundError(
            f"スピーカー設定ファイルが見つかりません: {speakers_path}"
        )
    with open(speakers_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class VoicevoxClient:
    """VOICEVOX APIクライアント。"""

    def __init__(self, host: str = "http://localhost:50021",
                 speed_scale: float = 0.92,
                 speed_min: float = 0.90,
                 speed_max: float = 0.95):
        self.host = host.rstrip("/")
        self.speed_scale = self._clamp_speed(speed_scale, speed_min, speed_max)
        self.speed_min = speed_min
        self.speed_max = speed_max
        self._session = requests.Session()
        logger.info(
            "VoicevoxClient初期化: host=%s, speed_scale=%.2f",
            self.host, self.speed_scale
        )

    def _clamp_speed(self, speed: float, speed_min: float,
                     speed_max: float) -> float:
        """速度を許容範囲内にクランプする。"""
        clamped = max(speed_min, min(speed_max, speed))
        if clamped != speed:
            logger.warning(
                "speedScaleを範囲内に調整しました: %.2f -> %.2f (範囲: %.2f-%.2f)",
                speed, clamped, speed_min, speed_max
            )
        return clamped

    def get_speakers(self) -> list:
        """VOICEVOX APIからスピーカー一覧を取得する。"""
        url = f"{self.host}/speakers"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            speakers = resp.json()
            logger.info("スピーカー一覧取得成功: %d件", len(speakers))
            return speakers
        except requests.ConnectionError:
            raise ConnectionError(
                f"VOICEVOXに接続できません。VOICEVOXが起動しているか確認してください: {self.host}"
            )
        except requests.HTTPError as e:
            raise RuntimeError(
                f"VOICEVOXスピーカー一覧の取得に失敗しました: {e}"
            )
        except requests.RequestException as e:
            raise RuntimeError(
                f"VOICEVOXへのリクエストでエラーが発生しました: {e}"
            )

    def find_speaker_style_id(self, speaker_name: str,
                              style_name: str) -> int:
        """
        スピーカー名とスタイル名からstyle_idを動的に取得する。
        見つからない場合はエラーを発生させる（サイレントに別スピーカーに置き換えない）。
        """
        speakers = self.get_speakers()

        # スピーカー名で検索
        target_speaker = None
        for speaker in speakers:
            if speaker.get("name") == speaker_name:
                target_speaker = speaker
                break

        if target_speaker is None:
            available_names = [s.get("name", "不明") for s in speakers]
            raise ValueError(
                f"スピーカー「{speaker_name}」が見つかりません。"
                f"利用可能なスピーカー: {', '.join(available_names)}"
            )

        # スタイル名で検索
        for style in target_speaker.get("styles", []):
            if style.get("name") == style_name:
                style_id = style["id"]
                logger.info(
                    "スピーカー検出: %s (%s) -> style_id=%d",
                    speaker_name, style_name, style_id
                )
                return style_id

        available_styles = [
            s.get("name", "不明") for s in target_speaker.get("styles", [])
        ]
        raise ValueError(
            f"スピーカー「{speaker_name}」にスタイル「{style_name}」が見つかりません。"
            f"利用可能なスタイル: {', '.join(available_styles)}"
        )

    def generate_audio_query(self, text: str, style_id: int) -> dict:
        """テキストから音声合成用クエリを生成する。"""
        url = f"{self.host}/audio_query"
        params = {"text": text, "speaker": style_id}
        try:
            resp = self._session.post(url, params=params, timeout=30)
            resp.raise_for_status()
            query = resp.json()
            logger.debug("audio_query生成成功: text=%s...", text[:20])
            return query
        except requests.ConnectionError:
            raise ConnectionError(
                f"VOICEVOXに接続できません: {self.host}"
            )
        except requests.HTTPError as e:
            raise RuntimeError(
                f"audio_queryの生成に失敗しました (text={text[:20]}...): {e}"
            )
        except requests.RequestException as e:
            raise RuntimeError(
                f"audio_queryリクエストでエラーが発生しました: {e}"
            )

    def adjust_query_speed(self, query: dict) -> dict:
        """クエリのspeedScaleを設定値に調整する。"""
        original_speed = query.get("speedScale", 1.0)
        query["speedScale"] = self.speed_scale
        logger.debug(
            "speedScale調整: %.2f -> %.2f", original_speed, self.speed_scale
        )
        return query

    def synthesize(self, query: dict, style_id: int,
                   output_path: str) -> str:
        """音声合成を実行し、WAVファイルとして保存する。"""
        url = f"{self.host}/synthesis"
        params = {"speaker": style_id}
        headers = {"Content-Type": "application/json"}
        try:
            resp = self._session.post(
                url,
                params=params,
                headers=headers,
                data=json.dumps(query),
                timeout=120
            )
            resp.raise_for_status()
        except requests.ConnectionError:
            raise ConnectionError(
                f"VOICEVOXに接続できません: {self.host}"
            )
        except requests.HTTPError as e:
            raise RuntimeError(
                f"音声合成に失敗しました: {e}"
            )
        except requests.RequestException as e:
            raise RuntimeError(
                f"音声合成リクエストでエラーが発生しました: {e}"
            )

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        logger.info("音声ファイル保存: %s (%d bytes)", output_path, len(resp.content))
        return output_path

    def generate_segment(self, text: str, style_id: int,
                         output_path: str) -> AudioSegment:
        """
        テキストからWAVファイルを生成し、AudioSegmentを返す。
        1. audio_queryの生成
        2. speedScaleの調整
        3. 音声合成の実行
        4. 実際のWAV長さを計測
        """
        # 1. audio_query生成
        query = self.generate_audio_query(text, style_id)

        # 2. speedScale調整
        query = self.adjust_query_speed(query)

        # 3. 音声合成
        self.synthesize(query, style_id, output_path)

        # 4. 実際の長さを計測
        duration = get_wav_duration(output_path)

        return AudioSegment(
            text=text,
            wav_path=output_path,
            actual_duration_seconds=duration,
            is_test=False
        )


def get_wav_duration(wav_path: str) -> float:
    """ffprobeを使用してWAVファイルの実際の長さ（秒）を取得する。"""
    if not os.path.isfile(wav_path):
        raise FileNotFoundError(
            f"WAVファイルが見つかりません: {wav_path}"
        )
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                wav_path
            ],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(
                f"ffprobeの実行に失敗しました (returncode={result.returncode}): {stderr}"
            )
        duration_str = result.stdout.strip()
        if not duration_str:
            raise RuntimeError(
                f"ffprobeから長さ情報を取得できませんでした: {wav_path}"
            )
        duration = float(duration_str)
        logger.debug("WAV長さ取得: %s -> %.3f秒", wav_path, duration)
        return duration
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffprobeが見つかりません。FFmpegをインストールしてください。"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"ffprobeがタイムアウトしました: {wav_path}"
        )
    except ValueError:
        raise RuntimeError(
            f"ffprobeの出力を数値に変換できません: '{duration_str}'"
        )


def generate_test_audio(text: str, output_path: str) -> AudioSegment:
    """
    テストモード用のサイン波音声を生成する。
    テキスト長から長さを推定し、440Hzのサイン波をWAVとして書き出す。
    テスト音声には「TEST ONLY - 投稿不可 - 技術検証用」のマークを付与する。
    """
    # テキスト長から長さを推定
    char_count = len(text)
    estimated_duration = max(1.0, char_count / CHARS_PER_SECOND)

    logger.info(
        "%s テスト音声生成: text=%s... (%d文字, 推定%.1f秒)",
        TEST_WATERMARK, text[:20], char_count, estimated_duration
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # サイン波を生成
    num_samples = int(TEST_SAMPLE_RATE * estimated_duration)
    amplitude = 16000  # 16-bit PCMの半分程度の振幅

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)  # モノラル
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(TEST_SAMPLE_RATE)

        # サイン波データを生成して書き込み
        frames = bytearray()
        for i in range(num_samples):
            t = i / TEST_SAMPLE_RATE
            value = int(
                amplitude * math.sin(2.0 * math.pi * TEST_FREQUENCY * t)
            )
            frames.extend(struct.pack("<h", value))

        wf.writeframes(bytes(frames))

    # 実際の長さをffprobeで計測（ffprobeが利用可能な場合）
    try:
        actual_duration = get_wav_duration(output_path)
    except (FileNotFoundError, RuntimeError) as e:
        logger.warning(
            "ffprobeでの長さ計測に失敗しました。推定値を使用します: %s", e
        )
        actual_duration = estimated_duration

    logger.info(
        "テスト音声保存: %s (%.3f秒)", output_path, actual_duration
    )

    return AudioSegment(
        text=text,
        wav_path=output_path,
        actual_duration_seconds=actual_duration,
        is_test=True
    )


def _generate_silence_wav(output_path: str, duration: float,
                          sample_rate: int = 44100) -> str:
    """指定した長さの無音WAVファイルを生成する。"""
    num_samples = int(sample_rate * duration)
    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        silence = b"\x00\x00" * num_samples
        wf.writeframes(silence)
    return output_path


def concatenate_segments(segments: List[AudioSegment], output_path: str,
                         pause_duration: float = 0.5) -> str:
    """
    複数の音声セグメントを1つのWAVファイルに結合する。
    セグメント間にpause_duration秒の無音を挿入する。

    Args:
        segments: 結合する音声セグメントのリスト
        output_path: 結合後の出力パス
        pause_duration: セグメント間の無音時間（秒）

    Returns:
        結合後のファイルパス
    """
    if not segments:
        raise ValueError("結合するセグメントがありません。")

    if len(segments) == 1 and pause_duration <= 0:
        # セグメントが1つでポーズ不要なら、そのままコピー
        import shutil
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        shutil.copy2(segments[0].wav_path, output_path)
        logger.info("セグメント1件のためコピー: %s", output_path)
        return output_path

    # ffmpegのconcatフィルターで結合
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # 一時的な無音ファイルを作成（ポーズ用）
    temp_dir = os.path.dirname(os.path.abspath(output_path))
    silence_path = os.path.join(temp_dir, "_silence_pause.wav")
    concat_list_path = os.path.join(temp_dir, "_concat_list.txt")

    try:
        if pause_duration > 0:
            _generate_silence_wav(silence_path, pause_duration)

        # concat用のファイルリストを作成
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                # ffmpegのconcatではパスのシングルクォートをエスケープする
                safe_path = segment.wav_path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
                # 最後のセグメント以外にポーズを挿入
                if pause_duration > 0 and i < len(segments) - 1:
                    safe_silence = silence_path.replace("'", "'\\''")
                    f.write(f"file '{safe_silence}'\n")

        # ffmpegで結合
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            # -c copy が失敗する場合（フォーマット不一致）、再エンコードで再試行
            logger.warning(
                "concat(copy)失敗、再エンコードで再試行します: %s",
                result.stderr[:200]
            )
            cmd_reencode = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "1",
                output_path
            ]
            result2 = subprocess.run(
                cmd_reencode,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result2.returncode != 0:
                raise RuntimeError(
                    f"音声ファイルの結合に失敗しました: {result2.stderr[:300]}"
                )

        logger.info(
            "音声結合完了: %s (%d セグメント)", output_path, len(segments)
        )
        return output_path

    finally:
        # 一時ファイルのクリーンアップ
        for temp_file in [silence_path, concat_list_path]:
            if os.path.isfile(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass


def get_total_duration(segments: List[AudioSegment],
                       pause_duration: float = 0.5) -> float:
    """
    セグメントリストの合計時間（秒）を計算する。
    セグメント間のポーズ時間も含む。
    """
    if not segments:
        return 0.0
    total = sum(s.actual_duration_seconds for s in segments)
    if len(segments) > 1:
        total += pause_duration * (len(segments) - 1)
    return total


def generate_audio(texts: List[str], output_dir: str,
                   mode: str = "production",
                   config: Optional[dict] = None,
                   speakers_config: Optional[dict] = None,
                   pause_duration: float = 0.5) -> AudioResult:
    """
    テキストリストから音声を生成するメインエントリーポイント。

    Args:
        texts: 音声化するテキストのリスト
        output_dir: 出力ディレクトリ
        mode: "production" or "test"
        config: settings.yamlの内容（Noneの場合は自動読み込み）
        speakers_config: speakers.yamlの内容（Noneの場合は自動読み込み）
        pause_duration: セグメント間の無音時間（秒）

    Returns:
        AudioResult: 生成結果
    """
    if not texts:
        raise ValueError("音声化するテキストが指定されていません。")

    # 設定の読み込み
    if config is None:
        config = _load_config()
    if speakers_config is None:
        speakers_config = _load_speakers_config()

    voicevox_config = config.get("voicevox", {})
    primary_speaker = speakers_config.get("voicevox", {}).get("primary", {})
    speaker_name = primary_speaker.get("speaker_name", "四国めたん")
    style_name = primary_speaker.get("style_name", "ノーマル")

    os.makedirs(output_dir, exist_ok=True)

    is_test = (mode == "test")
    segments: List[AudioSegment] = []

    if is_test:
        logger.info(
            "===== %s =====", TEST_WATERMARK
        )
        logger.info(
            "テストモードで音声生成を開始します（%d セグメント）", len(texts)
        )

        for i, text in enumerate(texts):
            wav_path = os.path.join(output_dir, f"segment_{i:03d}.wav")
            segment = generate_test_audio(text, wav_path)
            segments.append(segment)
            logger.info(
                "  [%d/%d] %.1f秒 - %s...",
                i + 1, len(texts), segment.actual_duration_seconds,
                text[:30]
            )

    else:
        logger.info(
            "本番モードで音声生成を開始します（%d セグメント）", len(texts)
        )
        logger.info(
            "スピーカー: %s (%s)", speaker_name, style_name
        )

        # VOICEVOXクライアント初期化
        host = voicevox_config.get("host", "http://localhost:50021")
        speed_scale = voicevox_config.get("speed_scale", 0.92)
        speed_min = voicevox_config.get("speed_min", 0.90)
        speed_max = voicevox_config.get("speed_max", 0.95)

        client = VoicevoxClient(
            host=host,
            speed_scale=speed_scale,
            speed_min=speed_min,
            speed_max=speed_max
        )

        # スピーカーIDを動的に取得（ハードコードしない）
        style_id = client.find_speaker_style_id(speaker_name, style_name)
        logger.info("style_id=%d を使用します", style_id)

        for i, text in enumerate(texts):
            wav_path = os.path.join(output_dir, f"segment_{i:03d}.wav")
            logger.info(
                "  [%d/%d] 生成中: %s...", i + 1, len(texts), text[:30]
            )
            segment = client.generate_segment(text, style_id, wav_path)
            segments.append(segment)
            logger.info(
                "  [%d/%d] 完了: %.1f秒",
                i + 1, len(texts), segment.actual_duration_seconds
            )

    # 全セグメントの結合
    concatenated_path = os.path.join(output_dir, "narration_full.wav")
    concatenate_segments(segments, concatenated_path, pause_duration)

    # 合計時間の計算
    total_duration = get_total_duration(segments, pause_duration)

    # 結合ファイルの実際の長さも確認
    try:
        actual_total = get_wav_duration(concatenated_path)
        logger.info(
            "音声生成完了: 計算上=%.1f秒, 実測=%.1f秒",
            total_duration, actual_total
        )
        total_duration = actual_total
    except (FileNotFoundError, RuntimeError) as e:
        logger.warning(
            "結合ファイルの長さ計測に失敗しました。計算値を使用します: %s", e
        )

    result = AudioResult(
        segments=segments,
        concatenated_path=concatenated_path,
        total_duration_seconds=total_duration,
        is_test=is_test
    )

    logger.info(
        "音声生成結果: %dセグメント, 合計%.1f秒, 結合ファイル=%s",
        len(segments), total_duration, concatenated_path
    )
    if is_test:
        logger.warning("注意: %s", TEST_WATERMARK)

    return result


def pad_audio_to_duration(wav_path: str, target_seconds: float) -> float:
    """結合済みWAVを無音パディングで指定秒数まで延長する。既に十分な長さなら何もしない。"""
    current = get_wav_duration(wav_path)
    if current >= target_seconds:
        logger.info("パディング不要: %.1f秒 >= 目標%.1f秒", current, target_seconds)
        return current
    pad_seconds = target_seconds - current
    logger.info("無音パディング追加: %.1f秒 -> %.1f秒 (+%.1f秒)", current, target_seconds, pad_seconds)
    padded_path = wav_path + ".padded.wav"
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-af", f"apad=pad_dur={pad_seconds}",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        padded_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"音声パディングに失敗しました: {result.stderr[:300]}")
    os.replace(padded_path, wav_path)
    new_duration = get_wav_duration(wav_path)
    logger.info("パディング完了: 実測 %.1f秒", new_duration)
    return new_duration
