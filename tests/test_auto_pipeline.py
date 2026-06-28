"""自動企画発掘・選手選定・動画生成パイプラインのテスト"""
import json
import os
import sys
import unittest
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class TestYouTubeResearch(unittest.TestCase):
    """YouTube調査モジュールのテスト"""

    def test_fixture_client_available(self):
        from lib.youtube_research import FixtureResearchClient
        client = FixtureResearchClient()
        self.assertTrue(client.is_available)

    def test_fixture_search_returns_results(self):
        from lib.youtube_research import FixtureResearchClient
        client = FixtureResearchClient()
        result = client.search_videos("河村勇輝 ノールックパス")
        self.assertIn("results", result)
        self.assertGreater(len(result["results"]), 0)

    def test_fixture_result_has_required_fields(self):
        from lib.youtube_research import FixtureResearchClient
        client = FixtureResearchClient()
        result = client.search_videos("NBA")
        for video in result["results"]:
            self.assertIn("video_id", video)
            self.assertIn("title", video)
            self.assertIn("view_count", video)
            self.assertIn("published_at", video)
            self.assertIn("url", video)

    def test_fixture_full_research(self):
        from lib.youtube_research import FixtureResearchClient
        client = FixtureResearchClient()
        result = client.run_full_research()
        self.assertIn("total_candidates", result)
        self.assertIn("candidates", result)
        self.assertGreater(result["total_candidates"], 0)

    def test_get_research_client_returns_fixture_without_api(self):
        from lib.youtube_research import get_research_client
        client = get_research_client(api_key=None)
        self.assertTrue(client.is_available)

    def test_fixture_no_duplicate_ids(self):
        from lib.youtube_research import FixtureResearchClient
        client = FixtureResearchClient()
        result = client.run_full_research()
        ids = [c["video_id"] for c in result["candidates"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestTopicScoring(unittest.TestCase):
    """候補採点モジュールのテスト"""

    def _make_video(self, **overrides):
        base = {
            "video_id": "test001",
            "title": "テスト動画",
            "description": "",
            "view_count": 100000,
            "like_count": 3000,
            "comment_count": 200,
            "published_at": "2026-06-01T00:00:00Z",
            "channel_subscriber_count": None,
        }
        base.update(overrides)
        return base

    def test_score_returns_overall(self):
        from lib.topic_scoring import score_candidate
        scores = score_candidate(self._make_video())
        self.assertIn("overall_score", scores)
        self.assertGreaterEqual(scores["overall_score"], 0)
        self.assertLessEqual(scores["overall_score"], 1.0)

    def test_score_has_all_dimensions(self):
        from lib.topic_scoring import score_candidate
        scores = score_candidate(self._make_video())
        expected_keys = [
            "trend_score", "velocity_score", "small_channel_breakout_score",
            "shorts_fit_score", "explanation_value_score", "repeatability_score",
            "source_availability_score", "rights_risk_score",
        ]
        for key in expected_keys:
            self.assertIn(key, scores)

    def test_high_views_high_trend(self):
        from lib.topic_scoring import score_candidate
        now = datetime(2026, 6, 15)
        high = score_candidate(self._make_video(view_count=5000000), now)
        low = score_candidate(self._make_video(view_count=1000), now)
        self.assertGreater(high["trend_score"], low["trend_score"])

    def test_rank_candidates_sorted(self):
        from lib.topic_scoring import rank_candidates
        videos = [
            self._make_video(video_id="a", view_count=100),
            self._make_video(video_id="b", view_count=5000000),
        ]
        ranked = rank_candidates(videos)
        self.assertGreater(ranked[0]["overall_score"], ranked[1]["overall_score"])

    def test_rights_risk_penalizes_copyright(self):
        from lib.topic_scoring import score_candidate
        clean = score_candidate(self._make_video(title="Great dunk"))
        risky = score_candidate(self._make_video(title="copyright removed blocked"))
        self.assertGreater(clean["rights_risk_score"], risky["rights_risk_score"])


class TestTopicDiscovery(unittest.TestCase):
    """自動企画発掘モジュールのテスト"""

    def test_select_player_returns_name(self):
        from lib.topic_discovery import select_player
        result = select_player(history={"history": []})
        self.assertIn("selected_player", result)
        self.assertTrue(len(result["selected_player"]) > 0)

    def test_select_player_recency_penalty(self):
        from lib.topic_discovery import select_player, PRIORITY_5_PLAYERS
        first_player = PRIORITY_5_PLAYERS[0]["name"]
        history = {"history": [
            {"selected_player": first_player} for _ in range(5)
        ]}
        result = select_player(history=history)
        self.assertNotEqual(result["selected_player"], first_player)

    def test_select_topic_returns_play(self):
        from lib.topic_discovery import select_topic
        result = select_topic("河村勇輝", history={"history": []})
        self.assertIn("selected_play", result)
        self.assertIn("selected_topic", result)

    def test_generate_title_candidates_count(self):
        from lib.topic_discovery import generate_title_candidates
        candidates = generate_title_candidates("河村勇輝", "ノールックパス", "テスト")
        self.assertEqual(len(candidates), 5)

    def test_title_contains_player_name(self):
        from lib.topic_discovery import generate_title_candidates
        candidates = generate_title_candidates("河村勇輝", "ノールックパス", "テスト")
        for c in candidates:
            self.assertIn("河村勇輝", c["title"])

    def test_title_scoring_has_6_dimensions(self):
        from lib.topic_discovery import generate_title_candidates
        candidates = generate_title_candidates("河村勇輝", "ノールックパス", "テスト")
        for c in candidates:
            scores = c["scores"]
            self.assertIn("clarity", scores)
            self.assertIn("specificity", scores)
            self.assertIn("curiosity", scores)
            self.assertIn("shorts_fit", scores)
            self.assertIn("truthfulness", scores)
            self.assertIn("originality", scores)
            self.assertIn("total", scores)

    def test_banned_words_reduce_score(self):
        from lib.topic_discovery import _score_title
        clean = _score_title("河村勇輝のパスが凄い理由", "河村勇輝", "パス")
        banned = _score_title("河村勇輝の衝撃ヤバすぎるプレー", "河村勇輝", "プレー")
        self.assertGreater(clean["truthfulness"], banned["truthfulness"])

    def test_select_best_title_no_duplicate(self):
        from lib.topic_discovery import generate_title_candidates, select_best_title
        candidates = generate_title_candidates("河村勇輝", "ノールックパス", "テスト")
        result = select_best_title(candidates, history={"history": []})
        self.assertIn("selected_title", result)

    def test_run_auto_topic_selection(self):
        from lib.topic_discovery import run_auto_topic_selection
        result = run_auto_topic_selection(history={"history": []})
        self.assertIn("selected_player", result)
        self.assertIn("selected_play", result)
        self.assertIn("selected_topic", result)
        self.assertIn("selected_title", result)

    def test_topic_history_persistence(self):
        from lib.topic_discovery import load_topic_history
        history = load_topic_history()
        self.assertIn("history", history)
        self.assertIsInstance(history["history"], list)


class TestCompetitorAnalysis(unittest.TestCase):
    """参考動画分析モジュールのテスト"""

    def _make_video(self):
        return {
            "video_id": "test001",
            "title": "なぜレブロンのダンクは止められないのか",
            "description": "レブロン・ジェームズのダンクを解説します。スロー再生あり。",
            "view_count": 2000000,
            "like_count": 40000,
            "comment_count": 1500,
        }

    def test_analyze_returns_all_fields(self):
        from lib.competitor_analysis import analyze_video_elements
        analysis = analyze_video_elements(self._make_video())
        expected = [
            "video_id", "original_title", "viewer_promise", "click_reason",
            "main_question", "opening_hook_pattern", "retention_devices",
            "visual_change_pattern", "emotional_trigger", "comment_interest",
            "transferable_principle", "elements_not_to_copy",
        ]
        for key in expected:
            self.assertIn(key, analysis)

    def test_elements_not_to_copy_always_present(self):
        from lib.competitor_analysis import analyze_video_elements
        analysis = analyze_video_elements(self._make_video())
        self.assertGreater(len(analysis["elements_not_to_copy"]), 0)
        self.assertIn("タイトルの固有名詞をそのまま使用", analysis["elements_not_to_copy"])

    def test_generate_new_concept(self):
        from lib.competitor_analysis import analyze_video_elements, generate_new_concept
        analysis = analyze_video_elements(self._make_video())
        concept = generate_new_concept(analysis, "河村勇輝", "ノールックパス")
        self.assertIn("applied_principle", concept)
        self.assertIn("new_question", concept)
        self.assertEqual(concept["target_player"], "河村勇輝")

    def test_batch_analysis(self):
        from lib.competitor_analysis import analyze_batch
        videos = [self._make_video() for _ in range(3)]
        results = analyze_batch(videos, limit=2)
        self.assertEqual(len(results), 2)


class TestClipDetection(unittest.TestCase):
    """素材候補探索・クリップ検出モジュールのテスト"""

    def test_find_source_candidates(self):
        from lib.clip_detection import find_source_candidates
        result = find_source_candidates("河村勇輝", "ノールックパス",
                                         keywords_en=["Yuki Kawamura"])
        self.assertIn("candidates", result)
        self.assertGreater(result["candidate_count"], 0)
        self.assertFalse(result["auto_download_enabled"])

    def test_source_candidates_require_manual_review(self):
        from lib.clip_detection import find_source_candidates
        result = find_source_candidates("八村塁", "ダンク")
        for c in result["candidates"]:
            self.assertTrue(c["requires_manual_review"])
            self.assertEqual(c["rights_status"], "candidate_source")

    def test_no_fabricated_urls(self):
        from lib.clip_detection import find_source_candidates
        result = find_source_candidates("河村勇輝", "ノールックパス")
        for c in result["candidates"]:
            self.assertEqual(c["url"], "")

    def test_editing_timeline_without_clips(self):
        from lib.clip_detection import generate_editing_timeline
        script = {
            "sections": [
                {"label": "フック", "text": "テスト"},
                {"label": "解説", "text": "テスト解説"},
                {"label": "CTA", "text": "登録"},
            ]
        }
        timeline = generate_editing_timeline([], target_duration=55.0, script=script)
        self.assertIn("timeline", timeline)
        self.assertEqual(timeline["output_resolution"], "1080x1920")

    def test_editing_timeline_with_clips(self):
        from lib.clip_detection import generate_editing_timeline
        clips = [
            {"start_time": 0, "end_time": 5, "duration": 5, "label": "h01"},
            {"start_time": 10, "end_time": 18, "duration": 8, "label": "h02"},
        ]
        timeline = generate_editing_timeline(clips, target_duration=30.0)
        self.assertGreater(timeline["segment_count"], 0)


class TestPublishing(unittest.TestCase):
    """投稿パッケージ生成モジュールのテスト"""

    def test_generate_description(self):
        from lib.publishing import generate_description
        desc = generate_description("河村勇輝", "テスト", "テストタイトル", "ノールックパス")
        self.assertIn("河村勇輝", desc)
        self.assertIn("ノールックパス", desc)

    def test_generate_hashtags_contains_player(self):
        from lib.publishing import generate_hashtags
        tags = generate_hashtags("河村勇輝", "ノールックパス")
        self.assertTrue(any("河村" in t for t in tags))

    def test_generate_hashtags_max_limit(self):
        from lib.publishing import generate_hashtags
        tags = generate_hashtags("河村勇輝", "ノールックパス", max_tags=5)
        self.assertLessEqual(len(tags), 5)

    def test_generate_hashtags_no_duplicates(self):
        from lib.publishing import generate_hashtags
        tags = generate_hashtags("河村勇輝", "ノールックパス")
        self.assertEqual(len(tags), len(set(tags)))

    def test_generate_pinned_comment(self):
        from lib.publishing import generate_pinned_comment
        comment = generate_pinned_comment("河村勇輝", "ノールックパス", "テスト")
        self.assertIn("河村勇輝", comment)
        self.assertIn("ノールックパス", comment)

    def test_publishing_package_creates_files(self):
        import tempfile
        from lib.publishing import generate_publishing_package
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = generate_publishing_package(
                "河村勇輝", "ノールックパス", "テスト", "テストタイトル", tmpdir
            )
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "title.txt")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "description.txt")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "hashtags.txt")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "pinned_comment.txt")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "publishing_package.json")))


class TestAutoDiscoveryIntegration(unittest.TestCase):
    """自動発掘パイプライン統合テスト"""

    def test_full_auto_discovery_pipeline(self):
        from main import run_auto_discovery
        result = run_auto_discovery("test")
        self.assertIn("research", result)
        self.assertIn("scored_candidates", result)
        self.assertIn("selection", result)
        self.assertIn("source_candidates", result)

        sel = result["selection"]
        self.assertIn("selected_player", sel)
        self.assertIn("selected_play", sel)
        self.assertIn("selected_title", sel)

    def test_auto_discovery_returns_analyses(self):
        from main import run_auto_discovery
        result = run_auto_discovery("test")
        self.assertIn("analyses", result)
        self.assertIsInstance(result["analyses"], list)

    def test_auto_discovery_returns_concept(self):
        from main import run_auto_discovery
        result = run_auto_discovery("test")
        if result.get("concept"):
            self.assertIn("applied_principle", result["concept"])
            self.assertIn("target_player", result["concept"])

    def test_auto_discovery_source_candidates_no_fabricated_urls(self):
        from main import run_auto_discovery
        result = run_auto_discovery("test")
        for c in result["source_candidates"]["candidates"]:
            self.assertEqual(c["url"], "")

    def test_selection_uses_priority_players(self):
        from main import run_auto_discovery
        from lib.topic_discovery import PRIORITY_5_PLAYERS, PRIORITY_4_PLAYERS
        result = run_auto_discovery("test")
        all_names = [p["name"] for p in PRIORITY_5_PLAYERS + PRIORITY_4_PLAYERS]
        self.assertIn(result["selection"]["selected_player"], all_names)


class TestConfigFiles(unittest.TestCase):
    """設定ファイルの整合性テスト"""

    def test_research_config_exists(self):
        path = os.path.join(BASE_DIR, "config", "research_config.json")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        self.assertIn("search_queries_ja", config)
        self.assertIn("search_queries_en", config)
        self.assertGreater(len(config["search_queries_ja"]), 0)

    def test_scoring_weights_sum_to_one(self):
        path = os.path.join(BASE_DIR, "config", "scoring_weights.json")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            weights = json.load(f)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_topic_history_exists(self):
        path = os.path.join(BASE_DIR, "state", "topic_history.json")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("history", data)


class TestProhibitions(unittest.TestCase):
    """禁止事項のテスト"""

    def test_no_fabricated_urls_in_source_candidates(self):
        from lib.clip_detection import find_source_candidates
        result = find_source_candidates("八村塁", "ダンク")
        for c in result["candidates"]:
            url = c.get("url", "")
            if url:
                self.fail(f"URLが創作されています: {url}")

    def test_no_rights_claim_in_analysis(self):
        from lib.competitor_analysis import analyze_video_elements
        video = {"video_id": "t", "title": "test", "description": "test",
                 "view_count": 100, "like_count": 10, "comment_count": 5}
        analysis = analyze_video_elements(video)
        full_text = json.dumps(analysis, ensure_ascii=False)
        forbidden = ["著作権確認済み", "権利問題なし", "完全に合法", "自由利用可能", "権利侵害なし"]
        for phrase in forbidden:
            self.assertNotIn(phrase, full_text)

    def test_final_release_never_true(self):
        from main import determine_publishable
        pub = determine_publishable(
            "production", {"duration_ok": True, "resolution_ok": True,
                           "codec_ok": True, "decode_ok": True, "zero_kb_ok": True},
            {"engine": "VOICEVOX", "speaker": "青山龍星", "speed": 0.95,
             "fallback_used": False},
            "/tmp/test.mp3", None, None, True, pipeline_error=False
        )
        self.assertFalse(pub["final_release_approved"])

    def test_elements_not_to_copy_includes_anti_copy(self):
        from lib.competitor_analysis import analyze_video_elements
        video = {"video_id": "t", "title": "ベスト NBA ダンク",
                 "description": "", "view_count": 100, "like_count": 10,
                 "comment_count": 5}
        analysis = analyze_video_elements(video)
        non_copy = analysis["elements_not_to_copy"]
        self.assertIn("動画構成の直接的な模倣", non_copy)
        self.assertIn("サムネイルの複製", non_copy)


if __name__ == "__main__":
    unittest.main()
