"""Generates full video script and narration text."""
from pathlib import Path
from .base import call_claude, build_system_context

SCRIPT_PROMPT = """以下のテーマで約{length}分の動画台本を作成してください。

テーマ: {theme}
企画概要: {plan_summary}

## 台本の形式

台本は以下の5段構成で作成してください:

【第1部：共感】（目安：全体の15%）
視聴者の記憶に刺さる具体的な描写から始める。
数字・映像指示・ナレーション指示を含む。

【第2部：発見】（目安：全体の25%）
歴史的事実・データ・当時の実態を語る。
不確かな数字は使わない。確認できた事実のみ使用。

【第3部：考察】（目安：全体の25%）
なぜそうなったかを多角的に考察する。
断定せず、複数の視点から語る。

【第4部：令和比較】（目安：全体の20%）
現代（2020年代）との比較。
失われたもの、残ったもの、変わったもの。

【第5部：余韻】（目安：全体の15%）
結論を押し付けず、余白を残す終わり方。
視聴者が自分の記憶を振り返れる問いかけ。

## 台本の書き方ルール
- 各行の形式:【映像指示】ナレーション原稿
- 映像指示は具体的に（例:【実物画像：昭和40年代の駄菓子屋店内】）
- AI生成画像使用箇所は【AI再現イメージ：〜】と明記
- テロップ指示は【テロップ：〜】と明記
- 間（ポーズ）は【間3秒】などと記載
- 1分あたり約240文字のナレーション量を目安にする
"""

NARRATION_PROMPT = """以下の動画台本から、ナレーション原稿だけを抽出・整理してください。

台本:
{script}

## 出力ルール
- 映像指示・テロップ指示を除いたナレーション文のみ
- 各段落（第1部〜第5部）のラベルは残す
- 読みやすく、声に出しやすい形で整理
- 漢字の読みが難しい場合はルビ（ふりがな）を括弧で添える
- 約{length}分分の原稿（{chars}文字目安）
"""


def generate_script(
    theme: str, plan_summary: str, length_min: int, out_dir: Path
) -> dict:
    system = build_system_context()
    user = SCRIPT_PROMPT.format(
        theme=theme, plan_summary=plan_summary, length=length_min
    )
    script = call_claude(system, user, max_tokens=6000)

    chars = length_min * 240
    narration_user = NARRATION_PROMPT.format(
        script=script, length=length_min, chars=chars
    )
    narration = call_claude(
        "あなたはプロのナレーター向け原稿編集者です。", narration_user, max_tokens=4000
    )

    (out_dir / "04_script").mkdir(exist_ok=True)
    (out_dir / "05_narration").mkdir(exist_ok=True)

    (out_dir / "04_script" / "script.md").write_text(script, encoding="utf-8")
    (out_dir / "05_narration" / "narration.md").write_text(narration, encoding="utf-8")

    return {"script": script, "narration": narration}
