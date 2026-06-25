"""台本生成モジュール

トピック入力から台本（JSON）を生成する。
事実ベースの構成で、禁止表現チェック・権利チェックを含む。

出力形式:
{
  "title": "動画タイトル",
  "description": "概要欄テキスト",
  "sections": [
    {"type": "opening", "text": "...", "duration_hint": 15},
    {"type": "body", "text": "...", "duration_hint": 60, "image_hint": "..."},
    ...
    {"type": "ending", "text": "...", "duration_hint": 10}
  ],
  "tags": ["皇室", "..."],
  "format": "long" | "shorts",
  "rights_status": "OK"
}
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from . import config


def check_forbidden(text: str) -> list[str]:
    found = []
    for expr in config.FORBIDDEN_EXPRESSIONS:
        if expr in text:
            found.append(expr)
    return found


def check_content_rules(text: str) -> list[str]:
    warnings = []
    speculation_patterns = [
        r"と思われる.*だろう",
        r"に違いない",
        r"きっと.*はず",
        r"内心では",
        r"本心は",
    ]
    for pat in speculation_patterns:
        if re.search(pat, text):
            warnings.append(f"推測表現の可能性: '{pat}'")
    return warnings


def create_long_script(
    topic: str,
    main_text: str,
    title: str = "",
    persons: list[str] | None = None,
    source_urls: list[str] | None = None,
) -> dict:
    if not title:
        title = topic

    forbidden = check_forbidden(main_text)
    if forbidden:
        print(f"[WARNING] 禁止表現が検出されました: {', '.join(forbidden)}")
        print("[WARNING] 該当箇所を修正してください。")

    content_warnings = check_content_rules(main_text)
    for w in content_warnings:
        print(f"[WARNING] {w}")

    paragraphs = [p.strip() for p in main_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [main_text]

    sections = []

    sections.append({
        "type": "opening",
        "text": f"こんにちは。{config.CHANNEL_NAME}チャンネルです。今回は、{topic}についてお伝えいたします。",
        "duration_hint": 12,
        "image_hint": "チャンネルロゴ or トピック関連画像",
    })

    for i, para in enumerate(paragraphs):
        sections.append({
            "type": "body",
            "text": para,
            "duration_hint": max(10, len(para) // 5),
            "image_hint": f"本文セクション{i+1}に関連する画像",
        })

    sections.append({
        "type": "ending",
        "text": "最後までご視聴いただきありがとうございます。チャンネル登録と高評価をよろしくお願いいたします。",
        "duration_hint": 10,
        "image_hint": "チャンネル登録誘導画像",
    })

    script = {
        "title": title,
        "description": _build_description(title, persons, source_urls),
        "sections": sections,
        "tags": _build_tags(topic, persons),
        "format": "long",
        "rights_status": "OK" if not forbidden else "REVIEW",
        "persons": persons or [],
        "source_urls": source_urls or [],
        "created_at": datetime.now().isoformat(),
        "forbidden_check": forbidden,
        "content_warnings": content_warnings,
    }

    return script


def create_shorts_script(
    topic: str,
    main_text: str,
    title: str = "",
    persons: list[str] | None = None,
) -> dict:
    if not title:
        title = topic

    forbidden = check_forbidden(main_text)
    if forbidden:
        print(f"[WARNING] 禁止表現が検出されました: {', '.join(forbidden)}")

    char_limit = 250
    if len(main_text) > char_limit:
        print(f"[WARNING] Shorts台本が{len(main_text)}文字です（推奨: {char_limit}文字以内）")

    sections = [
        {
            "type": "hook",
            "text": main_text[:80] if len(main_text) > 80 else main_text,
            "duration_hint": 5,
        },
        {
            "type": "body",
            "text": main_text,
            "duration_hint": 40,
            "image_hint": "トピック関連画像",
        },
        {
            "type": "ending",
            "text": "チャンネル登録お願いします",
            "duration_hint": 5,
        },
    ]

    return {
        "title": title,
        "description": f"#{config.CHANNEL_NAME} #皇室 #Shorts",
        "sections": sections,
        "tags": _build_tags(topic, persons),
        "format": "shorts",
        "rights_status": "OK" if not forbidden else "REVIEW",
        "persons": persons or [],
        "created_at": datetime.now().isoformat(),
        "forbidden_check": forbidden,
    }


def _build_description(
    title: str,
    persons: list[str] | None,
    source_urls: list[str] | None,
) -> str:
    lines = [title, ""]
    if persons:
        lines.append(f"関連人物: {'、'.join(persons)}")
        lines.append("")
    lines.append(f"{config.BGM_CREDIT}")
    lines.append("")
    if source_urls:
        lines.append("参考・出典:")
        for url in source_urls:
            lines.append(f"  {url}")
        lines.append("")
    lines.append(f"#{config.CHANNEL_NAME} #皇室")
    return "\n".join(lines)


def _build_tags(topic: str, persons: list[str] | None) -> list[str]:
    tags = ["皇室", config.CHANNEL_NAME]
    if persons:
        tags.extend(persons)
    keywords = [w for w in topic.split() if len(w) > 1]
    tags.extend(keywords[:5])
    return list(dict.fromkeys(tags))


def save_script(script: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    fmt = script.get("format", "long")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", script["title"])[:50]
    filename = f"{timestamp}_{fmt}_{safe_title}.json"
    path = output_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print(f"[OK] 台本保存: {path}")
    return path


def load_script(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="台本生成")
    parser.add_argument("--topic", required=True, help="動画のトピック")
    parser.add_argument("--text-file", required=True, help="本文テキストファイル")
    parser.add_argument("--title", default="", help="動画タイトル")
    parser.add_argument("--format", choices=["long", "shorts"], default="long")
    parser.add_argument("--persons", nargs="*", default=[], help="関連人物")
    parser.add_argument("--source-urls", nargs="*", default=[], help="出典URL")
    parser.add_argument("--output-dir", default=str(config.OUTPUTS_DIR))
    args = parser.parse_args()

    with open(args.text_file, "r", encoding="utf-8") as f:
        main_text = f.read()

    if args.format == "long":
        script = create_long_script(
            topic=args.topic,
            main_text=main_text,
            title=args.title,
            persons=args.persons,
            source_urls=args.source_urls,
        )
    else:
        script = create_shorts_script(
            topic=args.topic,
            main_text=main_text,
            title=args.title,
            persons=args.persons,
        )

    out_dir = Path(args.output_dir)
    save_script(script, out_dir)

    if script.get("forbidden_check"):
        print("[!] 禁止表現あり。台本修正後に再実行してください。")
        sys.exit(1)
    if script.get("rights_status") != "OK":
        print("[!] 権利ステータスがOKではありません。確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
