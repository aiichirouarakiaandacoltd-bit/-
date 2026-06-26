"""リスクチェックのユニットテスト。"""
from lifesave_ig.risk import RiskChecker


def test_forbidden_expressions_are_flagged():
    checker = RiskChecker()
    bad_samples = [
        "この水でアトピーが治る",
        "肌荒れが改善するシャワー",
        "病気が治る奇跡の水",
        "免疫力アップで健康になる",
        "老化防止に効く万能水",
        "絶対に効果があります",
        "必ず変わる暮らし",
    ]
    for text in bad_samples:
        result = checker.check(text)
        assert not result.ok, f"検出されるべき: {text}"
        assert len(result.hits) >= 1
        # 代替表現が提示される
        assert any(h.alternatives for h in result.hits)


def test_recommended_expressions_pass():
    checker = RiskChecker()
    good_samples = [
        "塩素が気になる方へ",
        "家中の水を見直す",
        "シャワーやお風呂の水まで考える",
        "浄水＋ナノバブル水という選択",
        "毎日使う水だからこそ、住まい全体で整える",
        "詳しくはDMでご相談ください",
    ]
    for text in good_samples:
        result = checker.check(text)
        assert result.ok, f"問題なしのはず: {text} / hits={[h.matched_text for h in result.hits]}"


def test_empty_text_is_ok():
    checker = RiskChecker()
    assert checker.check("").ok
    assert checker.check_many([]).ok


def test_check_many_dedup():
    checker = RiskChecker()
    res = checker.check_many(["奇跡の水", "奇跡の水", "家中の水を見直す"])
    # 同一ヒットは1件にまとめられる
    matched = [h.matched_text for h in res.hits]
    assert matched.count("奇跡の水") == 1
