"""Generates video editing structure, BGM/SE instructions, thumbnail prompt."""
from pathlib import Path
from .base import call_claude, build_system_context

EDITING_PROMPT = """以下の動画台本をもとに、動画編集用の構成データを作成してください。

テーマ: {theme}
台本の概要: {script_summary}

## 出力形式

### タイムライン構成

| タイムコード | セクション | 映像内容 | テロップ | 効果・トランジション |
|------------|---------|---------|---------|-----------------|
| 00:00-00:10 | オープニング | 〜 | 〜 | フェードイン |

### テロップスタイル指定
- フォント推奨:
- 文字色:
- 背景:
- 位置:

### トランジション設定
- セクション間:
- 素材切り替え:

### 字幕設定
- フォント:
- サイズ:
- 色:
- 位置:

### エンドスクリーン設計
- 表示内容:
- 推奨次の動画:

### チャンネルアート・ブランディング
- チャンネルロゴ表示タイミング:
- エンドカード仕様:
"""

BGM_PROMPT = """テーマ「{theme}」の動画（約{length}分）のBGM・SE指示書を作成してください。

## 出力形式

### BGM指示

| セクション | 雰囲気 | テンポ | 推奨ジャンル | 音量（%） | フリー音源候補 |
|----------|-------|-------|------------|---------|-------------|

### SE（効果音）指示

| タイミング | SE内容 | 効果 | フリーSE候補 |
|----------|-------|-----|------------|

### 推奨フリー音楽素材サイト
- Pixabay Music (pixabay.com/music/)
- DOVA-SYNDROME (dova-s.jp)
- 魔王魂 (maoudamashii.jokersounds.com)
- 甘茶の音楽工房 (amachamusic.chagasi.com)

### 重要注意事項
- YouTube音楽ライブラリ以外の楽曲は必ず利用規約確認
- 著作権フリーでもYouTube収益化での使用制限がある場合あり
- 実際の昭和平成の楽曲は原則使用しない（著作権上のリスク）
"""

THUMBNAIL_GEN_PROMPT = """テーマ「{theme}」のYouTubeサムネイル生成プロンプトを作成してください。

サムネイルテキスト案: {thumbnail_texts}

## 出力形式

### Midjourneyプロンプト（推奨案3パターン）

**パターン1：ノスタルジック写真風**
```
[プロンプト]
```
使用するテキスト: [サムネイルテキスト案から選択]

**パターン2：昭和の雰囲気イラスト風**
```
[プロンプト]
```

**パターン3：令和×昭和コントラスト**
```
[プロンプト]
```

### DALL-E プロンプト（代替案）
```
[プロンプト]
```

### Canvaテンプレート活用案
- 推奨テンプレートタイプ:
- フォント推奨:
- カラーパレット:

### サムネイル制作ルール
- サイズ: 1280×720px（16:9）
- テキストは動画全体の20%以内に収める
- 顔・表情が見える画像はCTR向上に有効
- AI生成画像には「再現イメージ」テキストを小さく表示
"""


def generate_editing(theme: str, script_summary: str, thumbnail_texts: str,
                     length_min: int, out_dir: Path) -> dict:
    system = build_system_context()

    editing = call_claude(
        system,
        EDITING_PROMPT.format(theme=theme, script_summary=script_summary),
        max_tokens=2500,
    )

    bgm_se = call_claude(
        system,
        BGM_PROMPT.format(theme=theme, length=length_min),
        max_tokens=2000,
    )

    thumbnail = call_claude(
        system,
        THUMBNAIL_GEN_PROMPT.format(theme=theme, thumbnail_texts=thumbnail_texts),
        max_tokens=2500,
    )

    for folder, name, content in [
        ("11_editing_structure", "editing_structure.md", editing),
        ("12_bgm_se", "bgm_se.md", bgm_se),
        ("13_thumbnail_prompt", "thumbnail_prompt.md", thumbnail),
    ]:
        (out_dir / folder).mkdir(exist_ok=True)
        (out_dir / folder / name).write_text(content, encoding="utf-8")

    return {"editing": editing, "bgm_se": bgm_se, "thumbnail": thumbnail}
