#!/usr/bin/env python3
"""Instagram投稿生成・予約管理システム（CLI）

ライフセーブ21プラス / 株式会社ナチュラルウィル

投稿案作成 → 画像文言・キャプション生成 → 人間確認 → 投稿予約データ出力
までを支援するCLIツール。完全自動投稿は行わない（Instagram規約遵守）。

使用例:
  python main.py generate --theme "家中の水を見直す" --format carousel
  python main.py calendar --weeks 4 --frequency 3
  python main.py risk-check --file generated_posts/sample.md
  python main.py export --format csv
  python main.py themes
  python main.py status --id whole-house-water-carousel-xxxx --set approved
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from lifesave_ig import FORMATS, STATUSES, config
from lifesave_ig.calendar_gen import CalendarBuilder
from lifesave_ig.generator import PostGenerator
from lifesave_ig.risk import RiskChecker, category_label
from lifesave_ig import storage


def _print_risk(result, checker: RiskChecker) -> None:
    if result.ok:
        print("✅ 注意表現は検出されませんでした。")
        return
    print(f"⚠️ {len(result.hits)}件の注意表現を検出しました：")
    for h in result.hits:
        cat = category_label(checker, h.category)
        print(f"  - 「{h.matched_text}」［{cat}］")
        print(f"      理由: {h.reason}")
        if h.alternatives:
            print(f"      代替案: {' / '.join(h.alternatives)}")


# --------------------------------------------------------------------
# サブコマンド
# --------------------------------------------------------------------
def cmd_generate(args) -> int:
    gen = PostGenerator()
    try:
        post = gen.generate(args.theme, args.format)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    print(f"== 投稿案: {post['title']} ==")
    print(f"テーマ: {post['theme']} / フォーマット: {post['format']}")
    print(f"ステータス: {post['status']}")
    print()
    print("[画像内テキスト]")
    print(post["image_text"])
    print()
    print("[キャプション]")
    print(post["caption"])
    print()
    print("[ハッシュタグ]")
    print(" ".join(post["hashtags"]))
    print()
    print("[CTA]")
    print(post["cta"])
    print()
    print("[注意表現チェック結果]")
    _print_risk(gen.checker.check_many(gen._collect_texts(post)), gen.checker)

    if not args.no_save:
        md_path = storage.save_post_markdown(gen.cfg, post)
        storage.upsert_posts(gen.cfg, [post])
        print()
        print(f"保存しました: {md_path}")
        print(f"posts.json を更新しました")
    return 0


def cmd_calendar(args) -> int:
    builder = CalendarBuilder()
    start = date.fromisoformat(args.start) if args.start else None
    posts = builder.build(weeks=args.weeks, frequency=args.frequency, start=start)
    if not posts:
        print("投稿予定を生成できませんでした（テーマが空の可能性）。", file=sys.stderr)
        return 1

    cfg = builder.cfg
    # 保存
    storage.upsert_posts(cfg, posts)
    for p in posts:
        storage.save_post_markdown(cfg, p)
    csv_path = storage.save_calendar_csv(cfg, posts)
    report_path = storage.save_risk_report(cfg, posts)
    json_path = None
    if args.export == "json":
        json_path = storage.export_calendar_json(cfg, posts)

    print(f"投稿カレンダーを生成しました（{len(posts)}件）")
    print(f"  週数: {args.weeks or cfg['calendar']['default_weeks']} / "
          f"週あたり: {args.frequency or cfg['calendar']['default_frequency']}本")
    print()
    print(f"{'日付':<12}{'種別':<10}{'ステータス':<12}テーマ")
    for p in posts:
        print(f"{p['scheduled_date']:<12}{p['format']:<10}{p['status']:<12}{p['theme']}")
    print()
    print(f"出力: {csv_path}")
    if json_path:
        print(f"出力: {json_path}")
    print(f"出力: {report_path}")
    print(f"出力: posts.json / generated_posts/*.md")
    flagged = [p for p in posts if not p["risk"]["ok"]]
    if flagged:
        print(f"\n⚠️ {len(flagged)}件に注意表現があります。risk_report.md を確認してください。")
    return 0


def cmd_risk_check(args) -> int:
    checker = RiskChecker()
    if args.text:
        text = args.text
        label = "(--text)"
    elif args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = config.resolve(args.file)
        if not path.exists():
            print(f"エラー: ファイルが見つかりません: {path}", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
        label = str(path)
    else:
        print("エラー: --file または --text を指定してください。", file=sys.stderr)
        return 1

    print(f"リスクチェック対象: {label}")
    result = checker.check(text)
    _print_risk(result, checker)
    return 0 if result.ok else 2


def cmd_export(args) -> int:
    cfg = config.load_config()
    posts = storage.load_posts(cfg)
    if not posts:
        print("posts.json が空です。先に generate または calendar を実行してください。",
              file=sys.stderr)
        return 1
    if args.format == "json":
        path = storage.export_calendar_json(cfg, posts)
    else:
        path = storage.save_calendar_csv(cfg, posts)
    report = storage.save_risk_report(cfg, posts)
    print(f"{len(posts)}件の投稿を出力しました。")
    print(f"出力: {path}")
    print(f"出力: {report}")
    return 0


def cmd_themes(args) -> int:
    gen = PostGenerator()
    print(f"登録テーマ（{len(gen.themes)}件）:")
    for t in gen.themes:
        print(f"  - [{t['id']}] {t['name']}")
        print(f"      {t.get('summary','')}")
    return 0


def cmd_status(args) -> int:
    cfg = config.load_config()
    posts = storage.load_posts(cfg)
    target = next((p for p in posts if p.get("id") == args.id), None)
    if target is None:
        print(f"エラー: 該当する投稿が見つかりません: {args.id}", file=sys.stderr)
        return 1
    if args.set not in STATUSES:
        print(f"エラー: 不正なステータス: {args.set}（{', '.join(STATUSES)}）", file=sys.stderr)
        return 1
    old = target.get("status")
    target["status"] = args.set
    storage.save_posts(cfg, posts)
    storage.save_post_markdown(cfg, target)
    print(f"ステータスを更新しました: {args.id}: {old} → {args.set}")
    return 0


# --------------------------------------------------------------------
# パーサ
# --------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Instagram投稿生成・予約管理システム（ライフセーブ21プラス）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="投稿案を生成する")
    g.add_argument("--theme", required=True, help="投稿テーマ名 または テーマID")
    g.add_argument("--format", default="feed", choices=FORMATS,
                   help="投稿フォーマット（feed/carousel/reel/story）")
    g.add_argument("--no-save", action="store_true", help="ファイルに保存しない")
    g.set_defaults(func=cmd_generate)

    c = sub.add_parser("calendar", help="投稿カレンダーを生成する")
    c.add_argument("--weeks", type=int, default=None, help="生成する週数")
    c.add_argument("--frequency", type=int, default=None, help="週あたりの投稿本数")
    c.add_argument("--start", default=None, help="開始日 YYYY-MM-DD（既定: 本日）")
    c.add_argument("--export", choices=["csv", "json"], default="csv",
                   help="追加でcalendar.jsonも出力する場合は json")
    c.set_defaults(func=cmd_calendar)

    r = sub.add_parser("risk-check", help="文章のリスクチェックを行う")
    r.add_argument("--file", help="チェック対象ファイル（.md など）")
    r.add_argument("--text", help="チェック対象テキストを直接指定")
    r.set_defaults(func=cmd_risk_check)

    e = sub.add_parser("export", help="posts.json からカレンダー/レポートを出力する")
    e.add_argument("--format", choices=["csv", "json"], default="csv")
    e.set_defaults(func=cmd_export)

    sub.add_parser("themes", help="登録テーマ一覧を表示する").set_defaults(func=cmd_themes)

    s = sub.add_parser("status", help="投稿ステータスを更新する（人間確認フロー）")
    s.add_argument("--id", required=True, help="投稿ID")
    s.add_argument("--set", required=True, help=f"設定するステータス（{', '.join(STATUSES)}）")
    s.set_defaults(func=cmd_status)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
