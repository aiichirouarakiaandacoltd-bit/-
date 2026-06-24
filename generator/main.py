#!/usr/bin/env python3
"""
昭和平成 日本再発見 — 動画制作自動化ジェネレーター
使い方: python -m generator.main generate --theme "なぜ駄菓子屋は消えたのか" --series "消えた日本シリーズ"
"""
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from generator.config import get_video_dir, ROOT
from generator.generators.plan_generator import generate_plan
from generator.generators.script_generator import generate_script
from generator.generators.subtitle_generator import generate_subtitles
from generator.generators.materials_generator import generate_materials
from generator.generators.editing_generator import generate_editing
from generator.generators.youtube_generator import generate_youtube_materials

console = Console()


@click.group()
def cli():
    """昭和平成 日本再発見 — 動画制作自動化ツール"""
    pass


@cli.command()
@click.option("--theme", "-t", required=True, help="動画テーマ（例：なぜ駄菓子屋は消えたのか）")
@click.option("--series", "-s", default="消えた日本シリーズ", help="シリーズ名")
@click.option("--video-id", "-id", default=None, help="動画ID（省略時は自動生成）")
@click.option("--length", "-l", default=12, type=int, help="目標動画尺（分）")
@click.option("--skip-to", default=None,
              help="指定フェーズから再開（plan/script/subtitles/materials/editing/youtube）")
def generate(theme: str, series: str, video_id: str, length: int, skip_to: str):
    """テーマを入力して全制作素材を自動生成する"""
    if video_id is None:
        from slugify import slugify
        video_id = slugify(theme, allow_unicode=True, separator="_")[:30]

    out_dir = get_video_dir(video_id)
    input_data = {
        "theme": theme,
        "series": series,
        "video_id": video_id,
        "length_min": length,
    }
    (out_dir / "input.json").write_text(
        json.dumps(input_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    console.print(Panel.fit(
        f"[bold cyan]テーマ:[/] {theme}\n"
        f"[bold cyan]シリーズ:[/] {series}\n"
        f"[bold cyan]出力先:[/] videos/{video_id}/\n"
        f"[bold cyan]目標尺:[/] {length}分",
        title="[bold]昭和平成 日本再発見 — 制作開始[/]",
    ))

    phases = ["plan", "script", "subtitles", "materials", "editing", "youtube"]
    skip = False
    if skip_to:
        skip = True

    plan_result = {}
    script_result = {}

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:

        # Phase 1: 企画・タイトル・サムネイル文言
        if skip and skip_to == "plan":
            skip = False
        if not skip:
            task = progress.add_task("[cyan]① 企画案・タイトル・サムネイル文言を生成中...", total=None)
            plan_result = generate_plan(theme, series, out_dir)
            progress.update(task, description="[green]① 企画案・タイトル・サムネイル文言 ✓")
            console.print("[green]  → 01_plan/ 02_titles/ 03_thumbnail_text/ 生成完了")
        else:
            plan_result = _load_existing_plan(out_dir)

        # Phase 2: 台本・ナレーション
        if skip and skip_to == "script":
            skip = False
        if not skip:
            task = progress.add_task("[cyan]② 台本・ナレーション原稿を生成中...", total=None)
            plan_summary = plan_result.get("plan", theme)[:500]
            script_result = generate_script(theme, plan_summary, length, out_dir)
            progress.update(task, description="[green]② 台本・ナレーション原稿 ✓")
            console.print("[green]  → 04_script/ 05_narration/ 生成完了")
        else:
            script_result = _load_existing_script(out_dir)

        # Phase 3: 字幕
        if skip and skip_to == "subtitles":
            skip = False
        if not skip:
            task = progress.add_task("[cyan]③ 字幕データを生成中...", total=None)
            generate_subtitles(script_result.get("narration", ""), length, out_dir)
            progress.update(task, description="[green]③ 字幕データ ✓")
            console.print("[green]  → 06_subtitles/ 生成完了")

        # Phase 4: 素材・AI画像プロンプト・リサーチ・権利確認
        if skip and skip_to == "materials":
            skip = False
        if not skip:
            task = progress.add_task("[cyan]④ 素材リスト・AI画像プロンプトを生成中...", total=None)
            generate_materials(theme, script_result.get("script", ""), out_dir)
            progress.update(task, description="[green]④ 素材・AI画像プロンプト・権利確認 ✓")
            console.print("[green]  → 07〜10 生成完了")

        # Phase 5: 編集構成・BGM・サムネイル
        if skip and skip_to == "editing":
            skip = False
        if not skip:
            task = progress.add_task("[cyan]⑤ 編集構成・BGM・サムネイルプロンプトを生成中...", total=None)
            thumb_texts = plan_result.get("thumbnail_text", "")[:500]
            script_summary = script_result.get("script", "")[:800]
            generate_editing(theme, script_summary, thumb_texts, length, out_dir)
            progress.update(task, description="[green]⑤ 編集構成・BGM・サムネイル ✓")
            console.print("[green]  → 11〜13 生成完了")

        # Phase 6: YouTube説明欄・固定コメント・アナリティクス
        if skip and skip_to == "youtube":
            skip = False
        if not skip:
            task = progress.add_task("[cyan]⑥ YouTube素材・アナリティクステンプレートを生成中...", total=None)
            title_line = _extract_first_title(plan_result.get("titles", ""))
            generate_youtube_materials(theme, series,
                                       script_result.get("script", "")[:400],
                                       title_line, out_dir)
            progress.update(task, description="[green]⑥ YouTube素材・アナリティクス ✓")
            console.print("[green]  → 14〜17 生成完了")

    console.print(Panel.fit(
        f"[bold green]全17ファイルの生成が完了しました！[/]\n"
        f"出力先: [cyan]videos/{video_id}/[/]\n\n"
        f"[yellow]次のステップ:[/]\n"
        f"1. 04_script/script.md を確認・修正\n"
        f"2. 08_ai_image_prompts/prompts.md でAI画像を生成\n"
        f"3. 09_research_sources/sources.md で実物画像を収集\n"
        f"4. 10_rights_check/rights_check.md で権利確認\n"
        f"5. 動画編集→荒木さんによる最終確認→投稿",
        title="[bold]制作完了[/]",
    ))


def _load_existing_plan(out_dir: Path) -> dict:
    plan_file = out_dir / "01_plan" / "plan.md"
    titles_file = out_dir / "02_titles" / "titles.md"
    thumb_file = out_dir / "03_thumbnail_text" / "thumbnail_text.md"
    return {
        "plan": plan_file.read_text(encoding="utf-8") if plan_file.exists() else "",
        "titles": titles_file.read_text(encoding="utf-8") if titles_file.exists() else "",
        "thumbnail_text": thumb_file.read_text(encoding="utf-8") if thumb_file.exists() else "",
    }


def _load_existing_script(out_dir: Path) -> dict:
    script_file = out_dir / "04_script" / "script.md"
    narration_file = out_dir / "05_narration" / "narration.md"
    return {
        "script": script_file.read_text(encoding="utf-8") if script_file.exists() else "",
        "narration": narration_file.read_text(encoding="utf-8") if narration_file.exists() else "",
    }


def _extract_first_title(titles_text: str) -> str:
    for line in titles_text.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            return line.split(".", 1)[1].strip()
    return titles_text[:80]


@cli.command()
def list_videos():
    """生成済み動画一覧を表示する"""
    videos_dir = ROOT / "videos"
    if not videos_dir.exists():
        console.print("[yellow]まだ動画が生成されていません[/]")
        return

    for video_dir in sorted(videos_dir.iterdir()):
        if not video_dir.is_dir():
            continue
        input_file = video_dir / "input.json"
        if input_file.exists():
            data = json.loads(input_file.read_text(encoding="utf-8"))
            console.print(f"[cyan]{video_dir.name}[/] — {data.get('theme', '?')} ({data.get('series', '?')})")
        else:
            console.print(f"[cyan]{video_dir.name}[/]")


if __name__ == "__main__":
    cli()
