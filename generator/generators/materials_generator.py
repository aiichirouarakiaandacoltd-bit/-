"""Generates image/video material lists, AI image prompts, research sources, rights check."""
from pathlib import Path
from .base import call_claude, build_system_context

MATERIALS_PROMPT = """以下の動画台本をもとに、必要な画像・映像素材リストを作成してください。

テーマ: {theme}
台本:
{script}

## 出力形式

### 素材リスト（シーン順）

| シーン番号 | 内容説明 | 素材タイプ | 推奨入手方法 | 優先度 |
|-----------|---------|-----------|------------|--------|
| 1 | 〜 | 実物画像/AI生成/映像/テキスト | 〜 | 高/中/低 |

素材タイプ:
- 実物画像：実際の写真（要権利確認）
- AI生成：Midjourney/DALL-E等で生成（再現イメージ表示必須）
- 公開資料：国立公文書館、国立国会図書館等の公開資料
- テキスト：テロップのみで対応
- 映像：動画クリップ
"""

AI_PROMPT_TEMPLATE = """以下の動画テーマと台本をもとに、AI画像生成プロンプトを作成してください。

テーマ: {theme}
必要なシーン: {scenes}

## 出力形式

各シーンについて:

### シーン[番号]: [シーン名]
**Midjourney プロンプト（英語）:**
```
[英語プロンプト], photorealistic, Showa era Japan, 1960s-1980s, nostalgic atmosphere, detailed, --ar 16:9 --v 6
```
**DALL-E プロンプト（日本語可）:**
```
[日本語でも可能なプロンプト]
```
**注意事項:** 再現イメージ表示が必要

## プロンプト作成ルール
- 実在の人物・著名人は含めない
- 著作権のあるキャラクターは含めない
- 「昭和〜年代の日本」という時代設定を明記
- 必ずアスペクト比16:9を指定
- photorealisticまたはcinematic styleを推奨
"""

RESEARCH_PROMPT = """テーマ「{theme}」の動画制作に必要な実物画像・資料画像の収集候補をリストアップしてください。

## 出力形式

### 公開アーカイブ・無料素材

| 素材内容 | 推奨入手先 | URL/検索キーワード | 利用条件 |
|---------|----------|-----------------|---------|

### 有料素材サイト（購入検討候補）

| 素材内容 | サイト名 | 検索キーワード | 参考価格帯 |
|---------|---------|--------------|---------|

### 地域・博物館・図書館へのコンタクト候補

| 機関名 | 期待できる素材 | 問い合わせ方法 |
|-------|-------------|-------------|

### 注意事項
著作権・肖像権に関する注意点を記載
"""

RIGHTS_PROMPT = """テーマ「{theme}」の動画制作における権利確認チェックリストを作成してください。

## 出力形式

### 使用予定素材の権利確認チェックリスト

#### 画像・映像
- [ ] 確認項目1
- [ ] 確認項目2

#### 音楽・BGM

#### ナレーション・テキスト

#### 商標・ロゴ

### リスクレベル評価
各カテゴリのリスクレベルを高/中/低で評価し、対処法を記載

### 禁止事項（このテーマ固有）
このテーマに特有の権利上の注意点

### 推奨アクション
制作前に必ず行うべき確認事項
"""


def generate_materials(theme: str, script: str, out_dir: Path) -> dict:
    system = build_system_context()

    materials = call_claude(
        system,
        MATERIALS_PROMPT.format(theme=theme, script=script[:2000]),
        max_tokens=2500,
    )

    ai_prompts = call_claude(
        system,
        AI_PROMPT_TEMPLATE.format(theme=theme, scenes=script[:1500]),
        max_tokens=3000,
    )

    research = call_claude(
        system,
        RESEARCH_PROMPT.format(theme=theme),
        max_tokens=2000,
    )

    rights = call_claude(
        system,
        RIGHTS_PROMPT.format(theme=theme),
        max_tokens=2000,
    )

    for folder, name, content in [
        ("07_materials", "materials_list.md", materials),
        ("08_ai_image_prompts", "prompts.md", ai_prompts),
        ("09_research_sources", "sources.md", research),
        ("10_rights_check", "rights_check.md", rights),
    ]:
        (out_dir / folder).mkdir(exist_ok=True)
        (out_dir / folder / name).write_text(content, encoding="utf-8")

    return {
        "materials": materials,
        "ai_prompts": ai_prompts,
        "research": research,
        "rights": rights,
    }
