"""Generates YouTube description, fixed comment, analytics template, improvement report."""
from pathlib import Path
from .base import call_claude, build_system_context

DESCRIPTION_PROMPT = """以下の動画のYouTube説明欄を作成してください。

テーマ: {theme}
シリーズ: {series}
動画の概要: {summary}
タイトル（選定済）: {title}

## 出力形式

### YouTube説明欄本文

（以下の要素を含める）
1. 導入文（2〜3行、動画の核心を伝える）
2. 動画の内容・章構成
3. 関連動画・シリーズ誘導（プレースホルダー形式で）
4. チャンネル登録・高評価のお願い（押しつけがましくなく）
5. ハッシュタグ（20個程度）

### ハッシュタグ案（YouTubeに最適化）

## ルール
- 最初の2〜3行が検索結果に表示されるため特に重要
- ハッシュタグは日本語メインで設定
- URLはプレースホルダー形式（[チャンネルURL]等）で記載
"""

FIXED_COMMENT_PROMPT = """以下のテーマの動画投稿後、固定コメントとして設置するコメント案を作成してください。

テーマ: {theme}
動画概要: {summary}

## 出力形式

### 固定コメント案（3パターン）

**パターン1：視聴者への質問型**
コメント文章（150文字以内）

**パターン2：補足情報型**
コメント文章（150文字以内）

**パターン3：シリーズ誘導型**
コメント文章（150文字以内）

## ルール
- 視聴者コメントを誘発する問いかけを含める
- 「あなたの〜の記憶を教えてください」などの参加型
- 絵文字は最小限（1〜2個程度）
- 長すぎない（読まれやすい長さ）
"""

ANALYTICS_TEMPLATE_PROMPT = """YouTube動画「{theme}」投稿後のアナリティクス分析テンプレートを作成してください。

## 出力形式

### 投稿後分析テンプレート

#### 基本データ記録（投稿後1週間・1ヶ月・3ヶ月）

| 指標 | 1週間後 | 1ヶ月後 | 3ヶ月後 | 目標値 |
|-----|-------|-------|-------|------|
| 再生回数 | | | | |
| 視聴時間（総計） | | | | |
| 平均視聴率（%） | | | | |
| インプレッション数 | | | | |
| クリック率（%） | | | | |
| チャンネル登録者増加数 | | | | |
| いいね数 | | | | |
| コメント数 | | | | |
| シェア数 | | | | |

#### 視聴者層データ
- 年齢層分布（目標：40代以上が過半数）:
- 性別比率:
- 視聴デバイス:
- 流入経路:

#### 視聴維持率の重要ポイント
どの時点で視聴者が離脱したかを記録・分析する項目

| タイムコード | 視聴維持率 | 変化の理由（推測） |
|------------|---------|---------------|

#### サムネイルA/Bテスト記録

#### 改善ポイントメモ欄

#### 次回動画への反映事項
"""

IMPROVEMENT_REPORT_PROMPT = """YouTubeアナリティクスデータを取り込んで改善レポートを作成するためのテンプレートを作成してください。

このテンプレートは、アナリティクスデータを記入した後に改善提案を導き出すためのものです。

## 出力形式

### 改善レポートテンプレート

#### 動画基本情報
- 動画タイトル:
- 投稿日:
- テーマ:
- シリーズ:

#### パフォーマンス評価

**クリック率評価**
- 実績値:    %
- 業界平均:  2〜5%
- 評価:
- 改善アクション:

**平均視聴率評価**
- 実績値:    %
- チャンネル目標: 50%以上
- 評価:
- 改善アクション:

#### 離脱ポイント分析
最大離脱ポイントのタイムコードと、その前後の台本・編集内容を照合するセクション

#### コメント傾向分析
- 共感型コメント数:
- 質問型コメント数:
- 訂正・補足型コメント数:
- 次回動画リクエスト:

#### 次回動画への7つの改善提案
1.
2.
3.
4.
5.
6.
7.

#### シリーズ全体への示唆
このデータがシリーズ全体の制作方針に与える示唆
"""


def generate_youtube_materials(
    theme: str, series: str, summary: str, title: str, out_dir: Path
) -> dict:
    system = build_system_context()

    description = call_claude(
        system,
        DESCRIPTION_PROMPT.format(
            theme=theme, series=series, summary=summary, title=title
        ),
        max_tokens=2000,
    )

    fixed_comment = call_claude(
        system,
        FIXED_COMMENT_PROMPT.format(theme=theme, summary=summary),
        max_tokens=1500,
    )

    analytics = call_claude(
        system,
        ANALYTICS_TEMPLATE_PROMPT.format(theme=theme),
        max_tokens=2000,
    )

    improvement = call_claude(
        system,
        IMPROVEMENT_REPORT_PROMPT.format(theme=theme),
        max_tokens=2000,
    )

    for folder, name, content in [
        ("14_youtube_description", "description.md", description),
        ("15_fixed_comment", "fixed_comment.md", fixed_comment),
        ("16_analytics_template", "analytics_template.md", analytics),
        ("17_improvement_report", "improvement_report_template.md", improvement),
    ]:
        (out_dir / folder).mkdir(exist_ok=True)
        (out_dir / folder / name).write_text(content, encoding="utf-8")

    return {
        "description": description,
        "fixed_comment": fixed_comment,
        "analytics": analytics,
        "improvement": improvement,
    }
