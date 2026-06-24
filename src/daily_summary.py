"""
デイリーサマリー CLI
python -m src.daily_summary [--open] [--date YYYY-MM-DD] [--run]

--open  : レポートをテキストエディタ / ブラウザで開く
--date  : 表示する日付（デフォルト: 今日）
--run   : レポートが存在しない場合、リサーチを実行してから表示
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("outputs/daily_official_research")


def _latest_report(today: str = None) -> Path | None:
    """指定日または最新のレポートファイルを返す"""
    if today:
        path = OUTPUT_DIR / f"{today}_research.md"
        return path if path.exists() else None

    reports = sorted(OUTPUT_DIR.glob("*_research.md"), reverse=True)
    return reports[0] if reports else None


def _open_file(path: Path):
    """OSに応じてファイルを開く"""
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    else:
        # Linux: xdg-open → fallback to terminal output
        try:
            result = subprocess.run(["xdg-open", str(path)], capture_output=True)
            if result.returncode != 0:
                _print_report(path)
        except FileNotFoundError:
            _print_report(path)


def _print_report(path: Path):
    """レポートをターミナルに出力する"""
    content = path.read_text(encoding="utf-8")
    print(content)


def _print_summary_only(path: Path):
    """レポートからサマリーセクションのみ抽出して表示する"""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    in_summary = False
    in_ranking = False
    summary_lines = []
    ranking_lines = []
    todo_lines = []
    in_todo = False

    for line in lines:
        if line.startswith("## 📊 本日のサマリー"):
            in_summary = True
            in_ranking = False
            in_todo = False
        elif line.startswith("## 🏅 アイデアランキング"):
            in_summary = False
            in_ranking = True
            in_todo = False
        elif line.startswith("### ✅ TODO自動生成") or line.startswith("### TODO自動生成"):
            in_ranking = False
            in_todo = True
        elif line.startswith("## ") and in_todo:
            in_todo = False
        elif line.startswith("## ") and (in_summary or in_ranking):
            in_summary = False
            in_ranking = False

        if in_summary:
            summary_lines.append(line)
        if in_ranking and len(ranking_lines) < 40:
            ranking_lines.append(line)
        if in_todo and len(todo_lines) < 60:
            todo_lines.append(line)

    date_str = path.stem.replace("_research", "")
    print(f"\n{'=' * 60}")
    print(f"  皇室物語 デイリーサマリー — {date_str}")
    print(f"{'=' * 60}")

    if summary_lines:
        print("\n".join(summary_lines[1:]))  # ヘッダー行をスキップ

    if ranking_lines:
        print("\n" + "\n".join(ranking_lines[:35]))

    if todo_lines:
        print("\n" + "\n".join(todo_lines[:50]))

    print(f"\nレポート全文: {path}")
    print("=" * 60)


def _cli():
    parser = argparse.ArgumentParser(description="皇室物語 デイリーサマリー")
    parser.add_argument("--open", action="store_true", help="レポートをエディタで開く")
    parser.add_argument("--date", default=None, help="表示する日付 YYYY-MM-DD（デフォルト: 最新）")
    parser.add_argument("--run", action="store_true", help="レポートが無い場合にリサーチを実行")
    args = parser.parse_args()

    today = args.date or datetime.now().strftime("%Y-%m-%d")
    report_path = _latest_report(args.date)

    # レポートが存在しない場合
    if not report_path:
        if args.run:
            print(f"  レポートが見つかりません。リサーチを実行します...")
            from src.official_research import run
            run(today=today)
            report_path = _latest_report(args.date)
        else:
            print(f"  レポートが見つかりません: {OUTPUT_DIR / f'{today}_research.md'}")
            print(f"  生成するには: python -m src.daily_summary --run")
            print(f"  または: python -m src.official_research")
            # 最新のレポートがあれば代わりに表示
            latest = _latest_report()
            if latest:
                print(f"\n  最新のレポート ({latest.stem}) を表示します:")
                report_path = latest
            else:
                sys.exit(1)

    if not report_path or not report_path.exists():
        print("  レポートの生成に失敗しました。")
        sys.exit(1)

    if args.open:
        print(f"  レポートを開きます: {report_path}")
        _open_file(report_path)
    else:
        _print_summary_only(report_path)


if __name__ == "__main__":
    _cli()
