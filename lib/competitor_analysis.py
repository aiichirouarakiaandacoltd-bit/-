"""参考動画の要素分解モジュール - 模倣ではなく構造的要素を抽出"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def analyze_video_elements(video):
    """参考動画から構造的要素を分解する"""
    title = video.get("title", "")
    description = video.get("description", "")
    view_count = video.get("view_count", 0)
    like_count = video.get("like_count", 0)
    comment_count = video.get("comment_count", 0)

    analysis = {
        "video_id": video.get("video_id", ""),
        "original_title": title,
        "viewer_promise": _extract_viewer_promise(title, description),
        "click_reason": _extract_click_reason(title, view_count, like_count),
        "main_question": _extract_main_question(title),
        "opening_hook_pattern": _classify_hook_pattern(title),
        "retention_devices": _identify_retention_devices(title, description),
        "visual_change_pattern": _estimate_visual_pattern(description),
        "emotional_trigger": _identify_emotion(title, description),
        "comment_interest": _estimate_comment_interest(title, comment_count, view_count),
        "transferable_principle": _extract_principle(title, description),
        "elements_not_to_copy": _identify_non_transferable(title),
    }
    return analysis


def generate_new_concept(analysis, target_player, target_play):
    """要素分解結果から新しい企画コンセプトを生成"""
    principle = analysis.get("transferable_principle", "")
    hook = analysis.get("opening_hook_pattern", "")
    question = analysis.get("main_question", "")

    new_question = question.replace(
        _extract_subject(analysis.get("original_title", "")),
        target_player
    ) if question else f"なぜ{target_player}の{target_play}は成功するのか"

    return {
        "source_video_id": analysis.get("video_id", ""),
        "applied_principle": principle,
        "new_question": new_question,
        "suggested_hook_pattern": hook,
        "target_player": target_player,
        "target_play": target_play,
        "concept_note": f"参考動画の本質「{principle}」を{target_player}の{target_play}に応用",
    }


def analyze_batch(candidates, limit=5):
    """複数の候補動画をバッチ分析"""
    results = []
    for video in candidates[:limit]:
        analysis = analyze_video_elements(video)
        results.append(analysis)
    return results


def _extract_viewer_promise(title, desc):
    if any(w in title for w in ["理由", "なぜ", "why", "how"]):
        return "疑問への回答を約束"
    if any(w in title for w in ["ベスト", "トップ", "best", "top"]):
        return "厳選されたハイライトを約束"
    if any(w in title for w in ["解説", "分析", "breakdown"]):
        return "専門的な解説を約束"
    return "注目プレーの紹介を約束"


def _extract_click_reason(title, views, likes):
    reasons = []
    if any(w in title for w in ["なぜ", "理由", "why"]):
        reasons.append("知的好奇心")
    if any(w in title for w in ["ダンク", "ブロック", "dunk", "block"]):
        reasons.append("迫力あるプレー")
    if views > 1000000:
        reasons.append("高再生数による社会的証明")
    if likes and views and likes / max(views, 1) > 0.03:
        reasons.append("高いエンゲージメント率")
    return "、".join(reasons) if reasons else "プレーへの興味"


def _extract_main_question(title):
    if "なぜ" in title:
        return title
    if "理由" in title:
        return title
    if "?" in title or "？" in title:
        return title
    return f"このプレーはなぜ成功したのか"


def _classify_hook_pattern(title):
    if any(w in title for w in ["なぜ", "理由", "why"]):
        return "question_hook"
    if any(w in title for w in ["ベスト", "トップ", "top"]):
        return "ranking_hook"
    if any(w in title for w in ["驚異", "衝撃", "insane"]):
        return "surprise_hook"
    return "play_showcase_hook"


def _identify_retention_devices(title, desc):
    devices = []
    if any(w in (title + desc).lower() for w in ["スロー", "slow"]):
        devices.append("slow_motion")
    if any(w in (title + desc).lower() for w in ["リプレイ", "replay", "もう一度"]):
        devices.append("replay")
    if any(w in (title + desc).lower() for w in ["解説", "breakdown", "分析"]):
        devices.append("expert_analysis")
    if any(w in (title + desc).lower() for w in ["比較", "vs", "compare"]):
        devices.append("comparison")
    if not devices:
        devices.append("highlight_compilation")
    return devices


def _estimate_visual_pattern(desc):
    if any(w in desc.lower() for w in ["スロー", "拡大", "zoom"]):
        return "mixed_speed_with_zoom"
    return "standard_highlight_edit"


def _identify_emotion(title, desc):
    if any(w in title for w in ["驚", "衝撃", "insane", "crazy"]):
        return "驚き"
    if any(w in title for w in ["感動", "泣ける"]):
        return "感動"
    if any(w in title for w in ["クラッチ", "clutch", "逆転"]):
        return "興奮・緊張"
    return "知的好奇心"


def _estimate_comment_interest(title, comments, views):
    if comments and views:
        ratio = comments / max(views, 1)
        if ratio > 0.001:
            return "高い議論性"
    return "標準的な反応"


def _extract_principle(title, desc):
    if any(w in title for w in ["なぜ", "理由"]):
        return "「なぜ」という問いで視聴者の知的好奇心を引く"
    if any(w in title for w in ["止められない", "unstoppable"]):
        return "不可能に見える成功の裏にある技術を解き明かす"
    if any(w in title for w in ["ベスト", "トップ"]):
        return "厳選されたプレーによる満足感"
    return "具体的な1プレーの技術的分析"


def _identify_non_transferable(title):
    items = []
    items.append("タイトルの固有名詞をそのまま使用")
    items.append("動画構成の直接的な模倣")
    items.append("サムネイルの複製")
    if any(w in title for w in ["ベスト", "トップ", "best", "top"]):
        items.append("ランキング形式の直接コピー")
    return items


def _extract_subject(title):
    for sep in ["の", "は", "が", "'s", " "]:
        if sep in title:
            return title.split(sep)[0]
    return title[:10]
