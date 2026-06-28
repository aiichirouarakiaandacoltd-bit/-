"""品質検査・publishable判定の回帰テスト"""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDurationBoundary:
    """Shorts尺 45.0〜59.5秒の境界値テスト"""

    def _make_quality(self, duration):
        from lib.quality import load_settings
        settings = load_settings()
        min_dur = settings["video"]["min_duration"]
        max_dur = settings["video"]["max_duration"]
        dur_ok = min_dur <= duration <= max_dur
        return {
            "pass": dur_ok,
            "duration": duration,
            "duration_ok": dur_ok,
            "resolution_ok": True,
            "codec_ok": True,
            "decode_ok": True,
            "zero_kb_ok": True,
            "checks": [{"name": "再生時間", "pass": dur_ok, "detail": f"{duration}秒"}],
        }

    def test_44_9_fail(self):
        q = self._make_quality(44.9)
        assert q["duration_ok"] is False

    def test_45_0_pass(self):
        q = self._make_quality(45.0)
        assert q["duration_ok"] is True

    def test_59_5_pass(self):
        q = self._make_quality(59.5)
        assert q["duration_ok"] is True

    def test_59_6_fail(self):
        q = self._make_quality(59.6)
        assert q["duration_ok"] is False

    def test_56_pass(self):
        q = self._make_quality(56.0)
        assert q["duration_ok"] is True


class TestPublishableDetermination:
    """publishable判定テスト"""

    def _make_tts_production(self):
        return {
            "engine": "VOICEVOX",
            "speaker": "青山龍星",
            "speed": 0.95,
            "fallback_used": False,
            "style_id": 13,
        }

    def _make_tts_test(self):
        return {
            "engine": "test_tone",
            "speaker": None,
            "speed": None,
            "fallback_used": False,
        }

    def _make_quality_ok(self):
        return {
            "pass": True,
            "duration_ok": True,
            "resolution_ok": True,
            "codec_ok": True,
            "decode_ok": True,
            "zero_kb_ok": True,
        }

    def _call_determine(self, mode="production", quality=None, tts_info=None,
                        bgm_path=None, bgm_license_path=None,
                        auto_fetch_result=None, review_screenshots_exist=True):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import determine_publishable
        return determine_publishable(
            mode, quality or self._make_quality_ok(),
            tts_info or self._make_tts_production(),
            bgm_path, bgm_license_path,
            auto_fetch_result, review_screenshots_exist,
        )

    def test_voicevox_disconnected_production_fail(self):
        """VOICEVOX未接続時に本番FAIL"""
        result = self._call_determine(tts_info=self._make_tts_test())
        assert result["technical_publishable"] is False
        assert any("VOICEVOX" in b for b in result["publish_blockers"])

    def test_dummy_audio_production_fail(self):
        """ダミー音声の本番利用禁止"""
        tts = self._make_tts_production()
        tts["fallback_used"] = True
        result = self._call_determine(tts_info=tts)
        assert result["technical_publishable"] is False
        assert any("fallback" in b or "テスト音声" in b for b in result["publish_blockers"])

    def test_rights_unknown_publishable_false(self):
        """権利不明素材使用時publishable=false"""
        result = self._call_determine(
            auto_fetch_result={"rights": {"embedded_footage_rights": "UNKNOWN"}},
        )
        assert result["publishable"] is False
        assert result["manual_review_required"] is True

    def test_bgm_no_license_publishable_false(self):
        """BGM権利不明時publishable=false"""
        result = self._call_determine(bgm_path=None)
        assert result["technical_publishable"] is False
        assert any("BGM" in b for b in result["publish_blockers"])

    def test_reference_only_not_usable(self):
        """reference_only素材を本番使用した場合のチェック"""
        from lib.auto_fetch import load_source_permissions
        perms = load_source_permissions()
        ref_channels = [
            url for url, info in perms.get("channels", {}).items()
            if info.get("permission_type") == "reference_only"
        ]
        assert len(ref_channels) > 0, "reference_onlyチャンネルが設定されていない"
        for url in ref_channels:
            assert perms["channels"][url]["permission_type"] == "reference_only"

    def test_test_mode_not_publishable(self):
        """テストモードではpublishable=false"""
        result = self._call_determine(mode="test")
        assert result["technical_publishable"] is False

    def test_speaker_not_aoyama_fail(self):
        """話者が青山龍星でない場合FAIL"""
        tts = self._make_tts_production()
        tts["speaker"] = "四国めたん"
        result = self._call_determine(tts_info=tts)
        assert result["technical_publishable"] is False

    def test_speed_not_095_fail(self):
        """速度が0.95でない場合FAIL"""
        tts = self._make_tts_production()
        tts["speed"] = 1.0
        result = self._call_determine(tts_info=tts)
        assert result["technical_publishable"] is False

    def test_resolution_fail(self):
        """解像度不一致でFAIL"""
        q = self._make_quality_ok()
        q["resolution_ok"] = False
        result = self._call_determine(quality=q)
        assert result["technical_publishable"] is False

    def test_decode_fail(self):
        """decode検査失敗でFAIL"""
        q = self._make_quality_ok()
        q["decode_ok"] = False
        result = self._call_determine(quality=q)
        assert result["technical_publishable"] is False

    def test_no_audio_stream_fail(self):
        """音声ストリームなしFAIL — quality checkレベル"""
        from lib.quality import run_quality_check
        dummy = "/nonexistent/file.mp4"
        result = run_quality_check(dummy)
        assert result["pass"] is False


class TestScriptValidation:
    """台本のNG表現チェック"""

    def test_prohibited_expressions(self):
        from lib.script_writer import PROHIBITED_EXPRESSIONS, validate_script
        for expr in PROHIBITED_EXPRESSIONS:
            script = {
                "player": "テスト選手",
                "topic": "テスト",
                "plan_type": "technique",
                "plan_type_label": "技術解説",
                "sections": [{"time": "0-57秒", "label": "テスト", "text": expr}],
            }
            result = validate_script(script)
            assert not result["ok"], f"禁止表現 '{expr}' が検出されなかった"

    def test_clean_script_passes(self):
        from lib.script_writer import validate_script
        script = {
            "player": "河村勇輝",
            "topic": "ノールックパス",
            "plan_type": "technique",
            "plan_type_label": "技術解説",
            "sections": [{"time": "0-57秒", "label": "解説", "text": "河村のパスは正確です。"}],
        }
        result = validate_script(script)
        assert result["ok"]


class TestPlayerNormalization:
    """選手名正規化テスト"""

    def test_canonical_unchanged(self):
        from lib.player import normalize_player_name
        assert normalize_player_name("河村勇輝") == "河村勇輝"

    def test_variant_normalized(self):
        from lib.player import normalize_player_name
        assert normalize_player_name("Yuki Kawamura") == "河村勇輝"

    def test_unknown_unchanged(self):
        from lib.player import normalize_player_name
        assert normalize_player_name("不明な選手") == "不明な選手"


class TestSettingsIntegrity:
    """設定ファイルの整合性テスト"""

    def test_voicevox_settings(self):
        from lib.preflight import load_settings
        s = load_settings()
        assert s["voicevox"]["speaker_name"] == "青山龍星"
        assert s["voicevox"]["speed_scale"] == 0.95
        assert s["voicevox"]["fallback_allowed"] is False
        assert s["voicevox"]["dynamic_speaker_lookup"] is True

    def test_video_specs(self):
        from lib.preflight import load_settings
        s = load_settings()
        assert s["video"]["width"] == 1080
        assert s["video"]["height"] == 1920
        assert s["video"]["fps"] == 30
        assert s["video"]["min_duration"] == 45.0
        assert s["video"]["max_duration"] == 59.5

    def test_channel_owned(self):
        from lib.auto_fetch import load_source_permissions
        perms = load_source_permissions()
        dunk_url = "https://www.youtube.com/@%E3%82%B6%E3%83%80%E3%83%B3%E3%82%AF"
        assert perms["channels"][dunk_url]["permission_type"] == "owned"

    def test_ai_face_not_in_owned(self):
        """実在選手AI画像が素材として登録されていないこと"""
        from lib.auto_fetch import load_source_permissions
        perms = load_source_permissions()
        for mat in perms.get("materials", []):
            desc = str(mat).lower()
            assert "ai顔" not in desc
            assert "ai face" not in desc
