"""投稿生成のユニットテスト。"""
import pytest

from lifesave_ig.generator import PostGenerator, FORMATS


@pytest.fixture(scope="module")
def gen():
    return PostGenerator()


def test_all_formats_generate(gen):
    for fmt in FORMATS:
        post = gen.generate("家中の水を見直す", fmt)
        assert post["format"] == fmt
        assert post["title"]
        assert post["image_text"]
        assert post["caption"]
        assert post["hashtags"], "ハッシュタグが空"
        assert post["cta"]
        assert "risk" in post
        assert post["status"] in ("draft", "review", "approved",
                                  "scheduled", "posted", "rejected")


def test_carousel_has_5_to_7_slides(gen):
    post = gen.generate("家中の水を見直す", "carousel")
    assert "slides" in post
    assert 5 <= len(post["slides"]) <= 7


def test_reel_has_hook_and_scenes(gen):
    post = gen.generate("シャワーの塩素が気になる方へ", "reel")
    reel = post["reel"]
    assert reel["hook_3s"]
    assert len(reel["scenes"]) >= 3
    # 冒頭3秒のフックが含まれる
    assert any("0-3" in sc["time"] for sc in reel["scenes"])


def test_story_has_frames(gen):
    post = gen.generate("無料相談誘導", "story")
    assert post["story"]["frames"]


def test_generated_content_is_low_risk(gen):
    """テンプレ生成物自体が禁止表現を含まないこと（重要）。"""
    for theme in gen.themes:
        for fmt in FORMATS:
            post = gen.generate(theme["name"], fmt)
            assert post["risk"]["ok"], (
                f"生成物にリスク表現: {theme['name']}/{fmt} -> "
                f"{[h['matched_text'] for h in post['risk']['hits']]}"
            )


def test_unknown_theme_raises(gen):
    with pytest.raises(ValueError):
        gen.generate("存在しないテーマXYZ", "feed")


def test_unknown_format_raises(gen):
    with pytest.raises(ValueError):
        gen.generate("家中の水を見直す", "tiktok")


def test_find_theme_by_id_and_name(gen):
    assert gen.find_theme("whole-house-water")["name"] == "家中の水を見直す"
    assert gen.find_theme("家中の水を見直す")["id"] == "whole-house-water"
    assert gen.find_theme("お風呂") is not None  # 部分一致
