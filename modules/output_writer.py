"""
YouTube投稿用テキストファイル出力モジュール
"""

from pathlib import Path
from .config import CHANNEL_NAME, CHANNEL_CONCEPT


def write_title(script: dict, output_dir: str) -> str:
    path = str(Path(output_dir) / "title.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(script.get("title", "タイトル未設定"))
    return path


def write_description(script: dict, output_dir: str) -> str:
    chapters = script.get("chapters", {})
    desc_lines = []
    desc_lines.append(script.get("subtitle", ""))
    desc_lines.append("")
    desc_lines.append("━" * 20)
    desc_lines.append("【この動画で分かること】")
    desc_lines.append("━" * 20)

    for i, (ch_name, ch_data) in enumerate(chapters.items()):
        desc_lines.append(f"✔ {ch_data.get('headline', ch_name)}")

    desc_lines.append("")
    desc_lines.append("━" * 20)
    desc_lines.append("【目次】")
    desc_lines.append("━" * 20)

    timecodes = {"共感": "0:00", "発見": "1:30", "考察": "4:30", "令和比較": "8:00", "余韻": "10:30"}
    for i, (ch_name, ch_data) in enumerate(chapters.items()):
        tc = timecodes.get(ch_name, f"{i*2}:00")
        desc_lines.append(f"{tc} 第{i+1}章：{ch_name}｜{ch_data.get('headline', '')}")

    desc_lines.append("")
    desc_lines.append("━" * 20)
    desc_lines.append(f"チャンネル：{CHANNEL_NAME}")
    desc_lines.append(CHANNEL_CONCEPT)
    desc_lines.append("━" * 20)
    desc_lines.append("#昭和 #平成 #なぜそうだったのか #昭和平成 #日本文化 #教養 #懐かしい #昭和の記憶")

    path = str(Path(output_dir) / "description.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(desc_lines))
    return path


def write_pinned_comment(script: dict, output_dir: str) -> str:
    title = script.get("title", "この動画")
    lines = [
        "【あなたの記憶を教えてください】",
        "",
        f"「{title}」を見て、",
        "あなたのご家庭ではどうでしたか？",
        "",
        "💬 当時の思い出",
        "💬 今との違いを感じること",
        "💬 子供や孫に伝えたいこと",
        "",
        "ぜひコメントで教えてください。",
        "",
        "━" * 20,
        f"▶ チャンネル登録はこちら",
        "━" * 20,
    ]
    path = str(Path(output_dir) / "pinned_comment.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def write_rights_check(script: dict, output_dir: str) -> str:
    lines = [
        f"# 権利確認チェックリスト",
        f"タイトル: {script.get('title', '')}",
        "",
        "## 映像素材",
        "- [ ] AI生成画像には「再現イメージ」テロップを表示済み",
        "- [ ] 実在人物の実写写真を使用していない",
        "- [ ] テレビ映像・著作権保護コンテンツを使用していない",
        "",
        "## 音声",
        "- [ ] BGMは著作権フリー音源を使用",
        "- [ ] 実際のCM音楽・楽曲を使用していない",
        "- [ ] ナレーションはAI生成音声（VOICEVOX/gTTS）",
        "",
        "## テキスト",
        "- [ ] 事実の断定に「とされています」等の表現を使用",
        "- [ ] 特定企業・個人の誹謗中傷なし",
        "- [ ] 著作権保護されたフレーズの無断引用なし",
        "",
        "## 最終確認",
        "- [ ] 荒木による内容確認完了",
        "- [ ] 投稿前の最終チェック完了",
        "",
        "※ 自動投稿禁止。荒木が手動で確認・投稿すること。",
    ]
    path = str(Path(output_dir) / "rights_check.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def write_all_outputs(script: dict, output_dir: str) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    results["title"] = write_title(script, str(output_dir))
    results["description"] = write_description(script, str(output_dir))
    results["pinned_comment"] = write_pinned_comment(script, str(output_dir))
    results["rights_check"] = write_rights_check(script, str(output_dir))

    for key, path in results.items():
        print(f"  [{key}] → {path}")

    return results
