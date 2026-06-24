"""Generates SRT subtitle data from narration script."""
from pathlib import Path
from .base import call_claude

SRT_PROMPT = """以下のナレーション原稿からSRT形式の字幕データを生成してください。

ナレーション原稿:
{narration}

## ルール
- SRT形式で出力
- 1字幕あたり最大2行・1行最大20文字
- 動画全体で約{length}分（{total_sec}秒）を想定
- 読み上げ速度は1秒あたり約4文字
- 各字幕の表示時間は読み上げ速度から自動計算
- セクション（第1部〜第5部）の境目には2〜3秒の間を入れる

## 出力形式（SRT）
1
00:00:00,000 --> 00:00:04,000
字幕テキスト1行目
字幕テキスト2行目

2
00:00:04,000 --> 00:00:08,000
...
"""


def generate_subtitles(narration: str, length_min: int, out_dir: Path) -> str:
    total_sec = length_min * 60
    user = SRT_PROMPT.format(
        narration=narration, length=length_min, total_sec=total_sec
    )
    srt = call_claude(
        "あなたはプロの字幕制作者です。正確なSRT形式で出力してください。",
        user,
        max_tokens=4000,
    )

    (out_dir / "06_subtitles").mkdir(exist_ok=True)
    (out_dir / "06_subtitles" / "subtitles.srt").write_text(srt, encoding="utf-8")

    return srt
