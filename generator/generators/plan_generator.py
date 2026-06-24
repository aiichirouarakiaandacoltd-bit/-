"""Generates video plan, titles (x10), thumbnail text (x10)."""
from pathlib import Path
from .base import call_claude, build_system_context


PLAN_PROMPT = """以下のテーマで動画企画案を作成してください。

テーマ: {theme}
シリーズ: {series}

## 出力形式

### 1. 企画案
以下の項目を記述:
- 動画タイトル（仮）
- 動画の核となる問い
- ターゲット視聴者の記憶ポイント（「この視聴者が共感するのは〜」）
- 発見ポイント（「視聴者が知らないかもしれない事実」）
- 令和比較ポイント（「現代と何を比べるか」）
- 差別化ポイント（なぜこの動画が他と違うか）
- 推定視聴者層（具体的に）
- 尺の目安（分）
- 構成の骨格（5段階：共感→発見→考察→令和比較→余韻）

### 2. タイトル案10個
検索流入・クリック率・チャンネルコンセプトのバランスを考えた10個。
煽りすぎず、でも気になるタイトル。
番号付きでリスト。

### 3. サムネイル文言案10個
サムネイルに載せる文言（短文・インパクトあり）10個。
各案に「メインテキスト」と「サブテキスト」を分けて記載。
"""


TITLES_SEP = "### 2. タイトル案10個"
THUMBNAIL_SEP = "### 3. サムネイル文言案10個"


def generate_plan(theme: str, series: str, out_dir: Path) -> dict:
    system = build_system_context()
    user = PLAN_PROMPT.format(theme=theme, series=series)
    result = call_claude(system, user, max_tokens=3000)

    # Split into sections
    parts = result.split("###")
    plan_text = result
    titles_text = ""
    thumb_text = ""

    for part in parts:
        if part.strip().startswith("2. タイトル案"):
            titles_text = "### " + part
        elif part.strip().startswith("3. サムネイル文言案"):
            thumb_text = "### " + part

    (out_dir / "01_plan").mkdir(exist_ok=True)
    (out_dir / "02_titles").mkdir(exist_ok=True)
    (out_dir / "03_thumbnail_text").mkdir(exist_ok=True)

    (out_dir / "01_plan" / "plan.md").write_text(result, encoding="utf-8")
    (out_dir / "02_titles" / "titles.md").write_text(titles_text or result, encoding="utf-8")
    (out_dir / "03_thumbnail_text" / "thumbnail_text.md").write_text(
        thumb_text or result, encoding="utf-8"
    )

    return {"plan": plan_text, "titles": titles_text, "thumbnail_text": thumb_text}
