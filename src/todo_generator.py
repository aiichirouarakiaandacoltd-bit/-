"""自動TODO生成モジュール (Phase 3)"""

from datetime import datetime


def generate_todos(ranked_entries: list[dict], duplicates_map: dict = None) -> str:
    """ランキング結果からTODOリストを生成する"""
    if duplicates_map is None:
        duplicates_map = {}

    priority_high = []
    priority_medium = []
    priority_low = []

    for entry in ranked_entries:
        score = entry.get("total_score", 0)
        content = entry.get("content", "")[:50]
        persons = entry.get("persons", [])
        recommendation = entry.get("recommendation", "")
        warnings = entry.get("warnings", [])

        if warnings:
            priority_high.append(f"⚠ 「{content}」の禁止表現を修正する")

        if score >= 70:
            person_str = "・".join(persons) if persons else "不明"
            if "Shorts" in recommendation:
                priority_high.append(f"「{content}」をShorts化する（{person_str}）")
            if "長尺" in recommendation:
                priority_high.append(f"「{content}」を長尺候補として検討する（{person_str}）")

            priority_high.append(f"「{content}」の公式URLを確認する")

            if entry.get("scores", {}).get("公式素材の使いやすさ", 0) >= 6:
                priority_high.append("公式素材（写真・映像）の使用可否を確認する")

        elif score >= 50:
            priority_medium.append(f"「{content}」を企画候補として保留する")
            if persons:
                priority_medium.append(f"外注者へ依頼する場合の指示書を準備する")

        else:
            priority_low.append(f"「{content}」は追加公式情報待ち")

    # Instagram/YouTube手動確認
    priority_medium.append("宮内庁公式Instagramの新規投稿を確認する")
    priority_medium.append("宮内庁公式YouTubeの新規動画を確認する")

    lines = [
        f"# 本日のTODO（{datetime.now().strftime('%Y年%m月%d日')}）",
        "",
    ]

    if priority_high:
        lines.append("## 最優先")
        for item in priority_high:
            lines.append(f"- [ ] {item}")
        lines.append("")

    if priority_medium:
        lines.append("## 次点")
        for item in priority_medium:
            lines.append(f"- [ ] {item}")
        lines.append("")

    if priority_low:
        lines.append("## 保留")
        for item in priority_low:
            lines.append(f"- [ ] {item}")
        lines.append("")

    if not priority_high and not priority_medium and not priority_low:
        lines.append("本日の新着企画候補はありません。")
        lines.append("")
        lines.append("## 定例確認")
        lines.append("- [ ] 宮内庁公式HPを確認する")
        lines.append("- [ ] 宮内庁公式Instagramを確認する")
        lines.append("- [ ] 宮内庁公式YouTubeを確認する")

    return "\n".join(lines)


if __name__ == "__main__":
    test_ranked = [
        {
            "content": "天皇皇后両陛下がオランダ国王夫妻と交流された",
            "total_score": 75,
            "persons": ["天皇皇后両陛下"],
            "recommendation": "Shorts先行 → 長尺化 → TikTok転用",
            "scores": {"公式素材の使いやすさ": 8},
            "warnings": [],
        },
    ]
    print(generate_todos(test_ranked))
