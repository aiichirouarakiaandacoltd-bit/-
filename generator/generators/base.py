"""Base generator with Claude API call helper."""
import anthropic
from generator.config import get_channel_config, get_tone_guide, get_model


def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=get_model(),
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def build_system_context() -> str:
    ch = get_channel_config()["channel"]
    tone = get_tone_guide()
    prohibited = "・".join(ch["prohibited"])
    preferred = "・".join(tone["preferred_expressions"])
    return f"""あなたは「{ch['name']}」チャンネルの動画制作アシスタントです。

【チャンネルコンセプト】
{ch['concept']}

【ターゲット視聴者】
{ch['target_audience']['primary_age']}（{', '.join(ch['target_audience']['generations'])}）

【動画構成】
1.共感 → 2.発見 → 3.考察 → 4.令和比較 → 5.余韻

【トーン】
{ch['tone']['style']}。煽らない。懐かしさ・発見・考察・少しの寂しさ・余韻を重視。
「歴史解説」ではなく「記憶解説」として書く。

【禁止表現】
{prohibited}

【推奨表現】
{preferred}

【重要ルール】
・事実不明な情報は断定せず「〜と言われています」と書く
・AI生成画像には『再現イメージ』の注記を必ず指示する
・全動画に必ず令和比較を入れる
・単なる懐古で終わらせない
"""
