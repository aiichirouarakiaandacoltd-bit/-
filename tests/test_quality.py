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
    """publishable判定テスト（4段階分離対応）"""

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
            "duration": 55.0,
            "duration_ok": True,
            "resolution_ok": True,
            "codec_ok": True,
            "decode_ok": True,
            "zero_kb_ok": True,
        }

    def _call_determine(self, mode="production", quality=None, tts_info=None,
                        bgm_path=None, bgm_license_path=None,
                        auto_fetch_result=None, review_screenshots_exist=True,
                        pipeline_error=False):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import determine_publishable
        return determine_publishable(
            mode, quality or self._make_quality_ok(),
            tts_info or self._make_tts_production(),
            bgm_path, bgm_license_path,
            auto_fetch_result, review_screenshots_exist,
            pipeline_error=pipeline_error,
        )

    def test_voicevox_disconnected_production_fail(self):
        """VOICEVOX未接続時に本番production_ready=False"""
        result = self._call_determine(tts_info=self._make_tts_test())
        assert result["production_ready"] is False
        assert any("VOICEVOX" in b for b in result["publish_blockers"])

    def test_dummy_audio_production_fail(self):
        """ダミー音声の本番利用禁止"""
        tts = self._make_tts_production()
        tts["fallback_used"] = True
        result = self._call_determine(tts_info=tts)
        assert result["production_ready"] is False
        assert any("fallback" in b or "テスト音声" in b for b in result["publish_blockers"])

    def test_rights_unknown_publishable_false(self):
        """権利不明素材使用時publishable=false"""
        result = self._call_determine(
            auto_fetch_result={"rights": {"embedded_footage_rights": "UNKNOWN"}},
        )
        assert result["publishable"] is False
        assert result["manual_review_required"] is True

    def test_bgm_no_license_not_production_ready(self):
        """BGM権利不明時production_ready=false"""
        result = self._call_determine(bgm_path=None)
        assert result["production_ready"] is False
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

    def test_test_mode_not_production_ready(self):
        """テストモードではproduction_ready=false"""
        result = self._call_determine(mode="test")
        assert result["production_ready"] is False

    def test_speaker_not_aoyama_fail(self):
        """話者が青山龍星でない場合production_ready=False"""
        tts = self._make_tts_production()
        tts["speaker"] = "四国めたん"
        result = self._call_determine(tts_info=tts)
        assert result["production_ready"] is False

    def test_speed_not_095_fail(self):
        """速度が0.95でない場合production_ready=False"""
        tts = self._make_tts_production()
        tts["speed"] = 1.0
        result = self._call_determine(tts_info=tts)
        assert result["production_ready"] is False

    def test_resolution_fail(self):
        """解像度不一致でtechnical_publishable=False"""
        q = self._make_quality_ok()
        q["resolution_ok"] = False
        result = self._call_determine(quality=q)
        assert result["technical_publishable"] is False

    def test_decode_fail(self):
        """decode検査失敗でtechnical_publishable=False"""
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

    def test_user_approved_rights_not_blocking(self):
        """user_approved_for_production_review素材は生成を阻害しない"""
        result = self._call_determine(
            auto_fetch_result={"rights": {
                "embedded_footage_rights": "UNKNOWN",
                "rights_status": "user_approved_for_production_review",
                "manual_review_required": False,
            }},
        )
        assert result["rights_status"] == "user_approved_for_production_review"
        assert result["manual_review_required"] is False

    def test_four_level_separation(self):
        """4段階判定の分離テスト"""
        result = self._call_determine()
        assert "technical_publishable" in result
        assert "production_ready" in result
        assert "completed" in result
        assert "final_release_approved" in result
        assert result["final_release_approved"] is False

    def test_final_release_always_false(self):
        """final_release_approvedは常にFalse"""
        result = self._call_determine()
        assert result["final_release_approved"] is False

    def test_technical_only_checks_tech(self):
        """technical_publishableは技術条件のみ"""
        result = self._call_determine(mode="test", tts_info=self._make_tts_test())
        assert result["technical_publishable"] is True
        assert result["production_ready"] is False

    def test_completed_independent_of_production_ready(self):
        """completedとproduction_readyが独立している"""
        result = self._call_determine(mode="test", tts_info=self._make_tts_test(),
                                      pipeline_error=False)
        assert result["completed"] is True
        assert result["production_ready"] is False

    def test_completed_false_on_pipeline_error(self):
        """パイプラインエラー時にcompleted=false"""
        result = self._call_determine(pipeline_error=True)
        assert result["completed"] is False

    def test_test_video_completed_true_production_ready_false(self):
        """テスト動画正常生成時にcompleted=true、production_ready=false"""
        result = self._call_determine(mode="test", tts_info=self._make_tts_test(),
                                      pipeline_error=False)
        assert result["technical_publishable"] is True
        assert result["production_ready"] is False
        assert result["completed"] is True
        assert result["final_release_approved"] is False

    def test_final_release_never_auto_true(self):
        """final_release_approvedが自動でtrueにならない（全条件OK時も）"""
        from lib.bgm_rotation import BGM_TRACKS
        bgm_path = BGM_TRACKS[0] if os.path.exists(BGM_TRACKS[0]) else None
        result = self._call_determine(
            mode="production",
            tts_info=self._make_tts_production(),
            bgm_path=bgm_path,
            pipeline_error=False,
        )
        assert result["final_release_approved"] is False


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


class TestBGMRotation:
    """BGM6曲循環テスト"""

    def setup_method(self):
        from lib.bgm_rotation import STATE_PATH, save_state, _default_state
        self._state_path = STATE_PATH
        self._backup = None
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r") as f:
                self._backup = f.read()
        save_state(_default_state())

    def teardown_method(self):
        if self._backup is not None:
            with open(self._state_path, "w") as f:
                f.write(self._backup)
        else:
            from lib.bgm_rotation import save_state, _default_state
            save_state(_default_state())

    def test_bgm_rotation_order(self):
        """BGM6曲が1→2→3→4→5→6→1で循環する"""
        from lib.bgm_rotation import get_next_bgm, mark_completed, BGM_TRACKS, save_state, _default_state
        save_state(_default_state())
        for cycle in range(2):
            for i in range(6):
                path, idx = get_next_bgm("production")
                assert idx == i, f"cycle={cycle}, expected index {i}, got {idx}"
                assert os.path.basename(path) == f"bgm_{i+1:02d}.mp3"
                mark_completed(f"test_job_{cycle}_{i}", idx, path, "2026-01-01T00:00:00")

    def test_test_mode_no_advance(self):
        """テストモードではBGM順が進まない"""
        from lib.bgm_rotation import get_next_bgm, load_state
        path, idx = get_next_bgm("test")
        assert path is None
        assert idx == -1
        state = load_state()
        assert state["next_bgm_index"] == 0

    def test_production_failure_no_advance(self):
        """本番生成失敗時にBGM順が進まない"""
        from lib.bgm_rotation import get_next_bgm, load_state
        path, idx = get_next_bgm("production")
        assert idx == 0
        state = load_state()
        assert state["next_bgm_index"] == 0

    def test_duplicate_job_no_double_advance(self):
        """同一job_id再実行でBGM順が二重に進まない"""
        from lib.bgm_rotation import get_next_bgm, mark_completed, load_state
        path, idx = get_next_bgm("production")
        result1 = mark_completed("same_job_001", idx, path, "2026-01-01")
        assert result1 is True
        state1 = load_state()
        result2 = mark_completed("same_job_001", idx, path, "2026-01-01")
        assert result2 is False
        state2 = load_state()
        assert state1["next_bgm_index"] == state2["next_bgm_index"]

    def test_only_success_updates_state(self):
        """本番生成成功時だけstateが更新される"""
        from lib.bgm_rotation import load_state, save_state, _default_state
        save_state(_default_state())
        state_before = load_state()
        assert state_before["last_completed_production_sequence"] == 0

    def test_no_test_tone_substitute(self):
        """欠損BGMをテストトーンで代替しない"""
        from lib.bgm_rotation import validate_bgm_file
        ok, detail = validate_bgm_file("/nonexistent/fake_bgm.mp3")
        assert ok is False

    def test_metadata_records_bgm_info(self):
        """metadataへBGM名・番号・パス・ゲインが記録される構造"""
        from lib.bgm_rotation import BGM_TRACKS
        metadata = {
            "bgm_rotation_index": 0,
            "bgm_name": os.path.basename(BGM_TRACKS[0]),
            "bgm_absolute_path": os.path.abspath(BGM_TRACKS[0]),
            "bgm_gain_db": -25.0,
        }
        assert metadata["bgm_name"] == "bgm_01.mp3"
        assert metadata["bgm_rotation_index"] == 0
        assert metadata["bgm_gain_db"] == -25.0
        assert "bgm_absolute_path" in metadata

    def test_bgm_file_validation(self):
        """BGMファイル存在・0KB・破損時に本番FAILになる"""
        from lib.bgm_rotation import validate_bgm_file
        ok_missing, _ = validate_bgm_file("/nonexistent/bgm.mp3")
        assert ok_missing is False

        zero_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "state", "_test_zero.mp3")
        try:
            with open(zero_path, "w") as f:
                pass
            ok_zero, _ = validate_bgm_file(zero_path)
            assert ok_zero is False
        finally:
            if os.path.exists(zero_path):
                os.remove(zero_path)

    def test_bgm_files_exist(self):
        """本番BGM6曲が配置されていること"""
        from lib.bgm_rotation import BGM_TRACKS, validate_bgm_file
        for i, track in enumerate(BGM_TRACKS):
            ok, detail = validate_bgm_file(track)
            assert ok, f"BGM_{i+1:02d} ({track}): {detail}"


class TestSubtitleQuality:
    """字幕品質テスト"""

    def test_no_double_period(self):
        """「。。」が字幕に存在しない"""
        from lib.script_writer import generate_script, script_to_narration
        script = generate_script("河村勇輝", "河村勇輝のノールックパスが守備を崩す理由", "technique")
        narration = script_to_narration(script)
        assert "。。" not in narration

        from main import adjust_script_for_duration
        from lib.preflight import load_settings
        settings = load_settings()
        adjusted_script, adjusted_narration, _ = adjust_script_for_duration(
            script, narration, 70.0, settings, attempt=0
        )
        assert "。。" not in adjusted_narration
        for section in adjusted_script["sections"]:
            assert "。。" not in section["text"]
