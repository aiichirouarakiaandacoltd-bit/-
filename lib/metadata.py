import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_titles(script):
    player = script["player"]
    topic = script["topic"]

    main_title = topic
    alternatives = [
        f"{player}のプレーを技術視点で解説",
        f"なぜ{player}は止められないのか",
        f"{player}の技術が凄い理由を解説します",
        f"この動き、見えていますか？{player}の技術解説",
    ]
    opening_texts = [
        topic,
        f"{player}の技術を解説します",
        f"この動き、気づいていましたか？",
    ]
    thumbnail_texts = [
        f"{player}の技術",
        topic[:15] if len(topic) > 15 else topic,
        f"なぜ止められない？",
    ]
    return {
        "main_title": main_title,
        "alternatives": alternatives,
        "opening_texts": opening_texts,
        "thumbnail_texts": thumbnail_texts,
    }


def generate_description(script, titles, credits_text=""):
    player = script["player"]
    topic = script["topic"]
    plan_label = script.get("plan_type_label", "解説")

    lines = []
    lines.append(f"{topic}")
    lines.append("")
    lines.append(f"#{player} #{script.get('plan_type_label', 'バスケ解説')}")
    lines.append("")
    lines.append(f"ザ・ダンクでは、バスケットボールのプレーを技術・戦術の視点から解説しています。")
    lines.append("")
    if credits_text:
        lines.append("【使用素材・BGM】")
        lines.append(credits_text)
        lines.append("")
    lines.append("#バスケ #NBA #Bリーグ #ザダンク #shorts")
    return "\n".join(lines)


def generate_hashtags(script):
    player = script["player"]
    tags = [
        "#shorts",
        "#バスケ",
        "#basketball",
        "#NBA",
        "#Bリーグ",
        "#ザダンク",
        f"#{player.replace('・', '').replace('＝', '')}",
    ]
    plan_type = script.get("plan_type", "")
    if plan_type == "technique":
        tags.append("#技術解説")
    elif plan_type == "tactics":
        tags.append("#戦術解説")
    elif plan_type == "super_play":
        tags.append("#スーパープレー")
    return tags


def generate_fixed_comment(script):
    player = script["player"]
    return f"ザ・ダンクをご覧いただきありがとうございます。\n{player}のプレーについて、あなたはどう見ましたか？\nコメントで教えてください。"


def save_metadata_files(script, output_dir, credits_text=""):
    os.makedirs(output_dir, exist_ok=True)
    titles = generate_titles(script)

    with open(os.path.join(output_dir, "title_candidates.txt"), "w", encoding="utf-8") as f:
        f.write(f"【本命タイトル】\n{titles['main_title']}\n\n")
        f.write("【比較用タイトル】\n")
        for i, t in enumerate(titles["alternatives"], 1):
            f.write(f"{i}. {t}\n")
        f.write("\n")

    with open(os.path.join(output_dir, "opening_text_candidates.txt"), "w", encoding="utf-8") as f:
        f.write("【冒頭テロップ候補】\n")
        for i, t in enumerate(titles["opening_texts"], 1):
            f.write(f"{i}. {t}\n")

    with open(os.path.join(output_dir, "thumbnail_plan.md"), "w", encoding="utf-8") as f:
        f.write(f"# サムネイル計画\n\n")
        f.write(f"選手: {script['player']}\n")
        f.write(f"テーマ: {script['topic']}\n\n")
        f.write("## テキスト候補\n\n")
        for i, t in enumerate(titles["thumbnail_texts"], 1):
            f.write(f"{i}. {t}\n")
        f.write("\n## 条件\n\n")
        f.write("- 選手を大きく表示\n- 太字・黒フチ\n- スマートフォンで読めるサイズ\n- 1秒で内容が分かる\n")

    desc = generate_description(script, titles, credits_text)
    with open(os.path.join(output_dir, "description.txt"), "w", encoding="utf-8") as f:
        f.write(desc)

    comment = generate_fixed_comment(script)
    with open(os.path.join(output_dir, "fixed_comment.txt"), "w", encoding="utf-8") as f:
        f.write(comment)

    hashtags = generate_hashtags(script)
    with open(os.path.join(output_dir, "hashtags.txt"), "w", encoding="utf-8") as f:
        f.write(" ".join(hashtags))

    return titles


def generate_trend_notes(output_path):
    lines = []
    lines.append("# トレンドノート")
    lines.append(f"調査日: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("## 注意")
    lines.append("インターネット接続がないため、リアルタイムトレンド調査は実行できませんでした。")
    lines.append("オンライン環境で再実行するか、手動でトレンド情報を入力してください。")
    lines.append("")
    lines.append("## 常時有効なトピック")
    lines.append("")
    topics = [
        ("河村勇輝", "B.LEAGUE、日本代表での活躍", "常時", "採用可"),
        ("八村塁", "NBA レイカーズでのパフォーマンス", "常時", "採用可"),
        ("ビクター・ウェンバンヤマ", "ブロック、スパン、新人記録", "常時", "採用可"),
        ("ステフィン・カリー", "3ポイント記録、シュートフォーム", "常時", "採用可"),
        ("レブロン・ジェームズ", "キャリア記録、レイカーズ", "常時", "採用可"),
        ("富永啓生", "NBA挑戦、3ポイント", "常時", "採用可"),
    ]
    for name, topic, freshness, status in topics:
        lines.append(f"- 選手: {name}")
        lines.append(f"  話題: {topic}")
        lines.append(f"  鮮度: {freshness}")
        lines.append(f"  採用: {status}")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path
