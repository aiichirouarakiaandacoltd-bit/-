"""デイリーサマリー統合レポート生成モジュール

official_research / research_dashboard / project_manager / contractors の
情報を統合し、HTML レポートを生成してブラウザで開く。

使い方:
  python -m src.daily_summary          # HTML 生成のみ
  python -m src.daily_summary --open   # 生成後にブラウザで開く
"""

import argparse
import html as html_mod
import json
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data" / "processed"
OUTPUTS_DIR = ROOT / "outputs" / "daily_reports"

# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_yaml(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_person_db() -> dict:
    return _load_json(DATA_DIR / "person_database.json")


def load_project_db() -> dict:
    return _load_json(DATA_DIR / "project_database.json")


def load_fetched_urls() -> dict:
    return _load_json(DATA_DIR / "fetched_urls.json")


def load_contractors() -> dict:
    return _load_yaml(CONFIG_DIR / "contractors.yaml")


def load_ranking_rules() -> dict:
    return _load_yaml(CONFIG_DIR / "ranking_rules.yaml")


def load_person_keywords() -> dict:
    return _load_yaml(CONFIG_DIR / "person_keywords.yaml")


def load_daily_research_md(date_str: str) -> str:
    md_path = ROOT / "outputs" / "daily_official_research" / f"{date_str}_official_research.md"
    if md_path.exists():
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# ---------------------------------------------------------------------------
# セクション生成ヘルパー
# ---------------------------------------------------------------------------

def _h(text: str) -> str:
    return html_mod.escape(str(text))


def _section_research(date_str: str) -> str:
    md = load_daily_research_md(date_str)
    if not md:
        return "<p>本日のリサーチレポートはまだ生成されていません。<br><code>python src/official_research.py</code> を実行してください。</p>"

    lines = md.split("\n")
    out = []
    for line in lines:
        line_e = _h(line)
        if line.startswith("# "):
            continue
        elif line.startswith("### "):
            out.append(f"<h4>{_h(line[4:])}</h4>")
        elif line.startswith("## "):
            out.append(f"<h3>{_h(line[3:])}</h3>")
        elif line.startswith("- [ ] "):
            out.append(f'<label class="todo"><input type="checkbox"> {_h(line[6:])}</label><br>')
        elif line.startswith("- "):
            out.append(f"<li>{_h(line[2:])}</li>")
        elif line.startswith("---"):
            out.append("<hr>")
        elif line.startswith("**") and line.endswith("**"):
            out.append(f"<p><strong>{_h(line[2:-2])}</strong></p>")
        elif line.strip():
            out.append(f"<p>{line_e}</p>")

    return "\n".join(out)


def _section_persons(days: int = 30) -> str:
    db = load_person_db()
    persons = db.get("persons", {})
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    rows = []
    for name, info in persons.items():
        entries = info.get("entries", [])
        recent = [e for e in entries if e.get("date", "") >= cutoff]
        total = len(entries)
        recent_count = len(recent)
        latest = recent[0].get("event_name", "")[:40] if recent else "-"
        rows.append(f"""
        <tr>
          <td>{_h(name)}</td>
          <td>{_h(info.get('category', ''))}</td>
          <td class="num">{recent_count}</td>
          <td class="num">{total}</td>
          <td>{_h(latest)}</td>
        </tr>""")

    if not rows:
        return "<p>人物データベースにエントリがありません。</p>"

    return f"""
    <table>
      <thead><tr><th>人物</th><th>分類</th><th>過去{days}日</th><th>全期間</th><th>最新</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""


def _section_projects() -> str:
    db = load_project_db()
    projects = db.get("projects", [])

    if not projects:
        return "<p>企画データがありません。</p>"

    status_groups: dict[str, list] = {}
    for p in projects:
        s = p.get("status", "不明")
        status_groups.setdefault(s, []).append(p)

    parts = []
    for status, items in status_groups.items():
        rows = ""
        for p in items:
            persons_str = "・".join(p.get("persons", [])) or "-"
            rows += f"""
            <tr>
              <td><code>{_h(p['id'])}</code></td>
              <td>{_h(p['title'])}</td>
              <td>{_h(persons_str)}</td>
              <td>{_h(p.get('format', ''))}</td>
              <td>{_h(p.get('assignee', '') or '-')}</td>
            </tr>"""

        parts.append(f"""
        <h4>{_h(status)}（{len(items)}件）</h4>
        <table>
          <thead><tr><th>ID</th><th>タイトル</th><th>人物</th><th>形式</th><th>担当</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""")

    return "\n".join(parts)


def _section_contractors() -> str:
    data = load_contractors()
    contractors = data.get("contractors", {})

    if not contractors:
        return "<p>外注者データがありません。</p>"

    rows = []
    for name, info in contractors.items():
        tasks = "、".join(info.get("available_tasks", []))
        long_p = f"¥{info['long_video_price']:,}" if info.get("long_video_price") else "-"
        shorts_p = f"¥{info['shorts_price']:,}" if info.get("shorts_price") else "-"
        thumb = "○" if info.get("thumbnail_capable") else "-"
        status = info.get("continuation_status", "")
        rows.append(f"""
        <tr>
          <td><strong>{_h(name)}</strong></td>
          <td>{_h(tasks)}</td>
          <td class="num">{long_p}</td>
          <td class="num">{shorts_p}</td>
          <td class="center">{thumb}</td>
          <td>{_h(status)}</td>
        </tr>""")

    return f"""
    <table>
      <thead><tr><th>外注者</th><th>担当業務</th><th>長尺単価</th><th>Shorts単価</th><th>サムネ</th><th>ステータス</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""


def _section_fetched_urls() -> str:
    data = load_fetched_urls()
    urls = data.get("urls", [])

    if not urls:
        return "<p>取得済みURLはありません。</p>"

    recent = sorted(urls, key=lambda u: u.get("fetched_at", ""), reverse=True)[:20]
    rows = []
    for u in recent:
        rows.append(f"""
        <tr>
          <td><a href="{_h(u['url'])}" target="_blank">{_h(u['url'][:60])}</a></td>
          <td>{_h(u.get('source', ''))}</td>
          <td>{_h(u.get('fetched_at', '')[:16])}</td>
        </tr>""")

    return f"""
    <p>合計 {len(urls)} URL 取得済み（直近20件を表示）</p>
    <table>
      <thead><tr><th>URL</th><th>ソース</th><th>取得日時</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""


# ---------------------------------------------------------------------------
# HTML 生成
# ---------------------------------------------------------------------------

CSS = """
:root { --bg: #f8f9fa; --card: #fff; --border: #dee2e6; --accent: #1a56db; --text: #1f2937; --muted: #6b7280; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Hiragino Kaku Gothic ProN","Meiryo",sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; }
.container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
header { background: var(--accent); color: #fff; padding: 24px 0; margin-bottom: 24px; }
header .container { display: flex; justify-content: space-between; align-items: center; }
header h1 { font-size: 1.3rem; font-weight: 700; }
header .date { font-size: 0.9rem; opacity: 0.85; }
.section { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 20px 24px; margin-bottom: 16px; }
.section h2 { font-size: 1.1rem; color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 6px; margin-bottom: 14px; }
.section h3 { font-size: 1rem; margin: 12px 0 6px; }
.section h4 { font-size: 0.95rem; margin: 10px 0 4px; color: #374151; }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; margin: 8px 0; }
th, td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
th { background: #f1f5f9; font-weight: 600; white-space: nowrap; }
td.num { text-align: right; }
td.center { text-align: center; }
li { margin-left: 20px; }
hr { border: none; border-top: 1px solid var(--border); margin: 12px 0; }
code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
a { color: var(--accent); }
label.todo { display: inline-block; margin: 2px 0; }
.footer { text-align: center; color: var(--muted); font-size: 0.8rem; padding: 16px 0; }
p { margin: 4px 0; }
strong { color: #b91c1c; }
@media print { body { background: #fff; } .section { break-inside: avoid; } }
"""


def build_html(date_str: str) -> str:
    today_jp = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y年%m月%d日")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = [
        ("公式情報リサーチ", _section_research(date_str)),
        ("人物別データベース（過去30日）", _section_persons(30)),
        ("企画管理", _section_projects()),
        ("外注者一覧", _section_contractors()),
        ("取得済みURL", _section_fetched_urls()),
    ]

    body_parts = []
    for title, content in sections:
        body_parts.append(f"""
    <div class="section">
      <h2>{_h(title)}</h2>
      {content}
    </div>""")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>デイリーサマリー - {_h(today_jp)}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="container">
    <h1>YouTube運営秘書 デイリーサマリー</h1>
    <span class="date">{_h(today_jp)}｜生成: {_h(now)}</span>
  </div>
</header>
<div class="container">
{"".join(body_parts)}
</div>
<div class="footer">
  ※ 最終判断・台本確定・投稿判断は荒木が行います。自動投稿は行いません。<br>
  YouTube運営秘書システム v1.0
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="デイリーサマリー HTML レポート生成")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="対象日付 (YYYY-MM-DD)")
    parser.add_argument("--open", action="store_true",
                        help="生成後にブラウザで開く")
    args = parser.parse_args()

    date_str = args.date

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / f"{date_str}_daily_summary.html"

    print(f"[INFO] デイリーサマリーを生成中... ({date_str})")
    html_content = build_html(date_str)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] {out_path}")

    if args.open:
        url = out_path.resolve().as_uri()
        print(f"[INFO] ブラウザで開きます: {url}")
        try:
            webbrowser.open(url)
        except Exception:
            if sys.platform == "win32":
                subprocess.run(["start", "", str(out_path)], shell=True)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(out_path)])
            else:
                subprocess.run(["xdg-open", str(out_path)])


if __name__ == "__main__":
    main()
