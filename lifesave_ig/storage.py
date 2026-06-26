"""保存・出力ユーティリティ。

posts.json / calendar.csv / risk_report.md / generated_posts/*.md を書き出す。
ファイルが0KBにならないよう、必ず内容のあるデータを書き込む。
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from . import config


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def _slugify_filename(post: Dict[str, Any]) -> str:
    base = f"{post.get('theme_id', 'post')}_{post.get('format', 'feed')}"
    return base.replace("/", "-").replace(" ", "_")


# --------------------------------------------------------------------
# posts.json
# --------------------------------------------------------------------
def load_posts(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    path = config.resolve(cfg["output"]["posts_json"])
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("posts", [])
    except Exception:
        return []


def save_posts(cfg: Dict[str, Any], posts: List[Dict[str, Any]]) -> Path:
    path = config.resolve(cfg["output"]["posts_json"])
    for p in posts:
        p.setdefault("created_at", _now_iso())
        p["updated_at"] = _now_iso()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    return path


def upsert_posts(cfg: Dict[str, Any], new_posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """idをキーに既存posts.jsonへ追記/更新する。"""
    existing = load_posts(cfg)
    by_id = {p.get("id"): p for p in existing}
    for np_ in new_posts:
        pid = np_.get("id")
        if pid in by_id:
            np_.setdefault("created_at", by_id[pid].get("created_at"))
        by_id[pid] = np_
    merged = list(by_id.values())
    save_posts(cfg, merged)
    return merged


# --------------------------------------------------------------------
# generated_posts/*.md
# --------------------------------------------------------------------
def post_to_markdown(post: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# {post.get('title', '(無題)')}")
    lines.append("")
    lines.append(f"- ID: `{post.get('id', '')}`")
    lines.append(f"- テーマ: {post.get('theme', '')}")
    lines.append(f"- フォーマット: {post.get('format', '')}")
    lines.append(f"- ステータス: {post.get('status', 'draft')}")
    if post.get("scheduled_date"):
        lines.append(f"- 投稿予定日: {post['scheduled_date']}")
    lines.append("")

    lines.append("## 画像内テキスト")
    lines.append("")
    lines.append(post.get("image_text", "") or "(なし)")
    lines.append("")

    # カルーセル
    if post.get("slides"):
        lines.append("## カルーセル構成")
        lines.append("")
        for s in post["slides"]:
            lines.append(f"### {s.get('no')}枚目：{s.get('role','')}")
            lines.append("")
            lines.append(f"**画像内テキスト**: {s.get('image_text','')}")
            lines.append("")
            if s.get("note"):
                lines.append(f"> メモ: {s['note']}")
                lines.append("")

    # リール
    if post.get("reel"):
        reel = post["reel"]
        lines.append("## リール台本")
        lines.append("")
        lines.append(f"- 尺: {reel.get('duration_sec','')}")
        lines.append(f"- 冒頭3秒フック: {reel.get('hook_3s','')}")
        lines.append("")
        for sc in reel.get("scenes", []):
            lines.append(f"### {sc.get('time','')}")
            lines.append("")
            lines.append(f"- 画面テキスト: {sc.get('on_screen','')}")
            lines.append(f"- ナレーション: {sc.get('narration','')}")
            if sc.get("note"):
                lines.append(f"- メモ: {sc['note']}")
            lines.append("")

    # ストーリーズ
    if post.get("story"):
        lines.append("## ストーリーズ構成")
        lines.append("")
        for fr in post["story"].get("frames", []):
            lines.append(f"- {fr.get('no')}枚目: {fr.get('image_text','')} "
                         f"（{fr.get('interaction','')}）")
        lines.append("")

    # キャプション
    lines.append("## キャプション")
    lines.append("")
    lines.append(post.get("caption", ""))
    lines.append("")

    # ハッシュタグ
    lines.append("## ハッシュタグ")
    lines.append("")
    lines.append(" ".join(post.get("hashtags", [])))
    lines.append("")

    # CTA
    lines.append("## CTA")
    lines.append("")
    lines.append(post.get("cta", ""))
    lines.append("")

    # リスクチェック
    risk = post.get("risk", {})
    lines.append("## 注意表現チェック結果")
    lines.append("")
    if risk.get("ok", True):
        lines.append("✅ 問題のある表現は検出されませんでした。")
    else:
        lines.append(f"⚠️ {risk.get('hit_count', 0)}件の注意表現が検出されました。")
        lines.append("")
        for h in risk.get("hits", []):
            lines.append(f"- 「{h.get('matched_text')}」: {h.get('reason')}")
            if h.get("alternatives"):
                lines.append(f"  - 代替案: {' / '.join(h['alternatives'])}")
    lines.append("")
    return "\n".join(lines)


def save_post_markdown(cfg: Dict[str, Any], post: Dict[str, Any]) -> Path:
    out_dir = config.resolve(cfg["output"]["generated_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = _slugify_filename(post) + ".md"
    path = out_dir / fname
    with open(path, "w", encoding="utf-8") as f:
        f.write(post_to_markdown(post))
    return path


# --------------------------------------------------------------------
# calendar.csv
# --------------------------------------------------------------------
CSV_FIELDS = ["date", "format", "theme", "title", "caption", "hashtags", "status", "risk", "id"]


def save_calendar_csv(cfg: Dict[str, Any], posts: List[Dict[str, Any]]) -> Path:
    path = config.resolve(cfg["output"]["calendar_csv"])
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for p in posts:
            writer.writerow({
                "date": p.get("scheduled_date", ""),
                "format": p.get("format", ""),
                "theme": p.get("theme", ""),
                "title": p.get("title", ""),
                "caption": (p.get("caption", "") or "").replace("\n", " "),
                "hashtags": " ".join(p.get("hashtags", [])),
                "status": p.get("status", "draft"),
                "risk": p.get("risk", {}).get("level", "ok"),
                "id": p.get("id", ""),
            })
    return path


def export_calendar_json(cfg: Dict[str, Any], posts: List[Dict[str, Any]]) -> Path:
    path = config.resolve("calendar.json")
    rows = [{
        "date": p.get("scheduled_date", ""),
        "format": p.get("format", ""),
        "theme": p.get("theme", ""),
        "title": p.get("title", ""),
        "hashtags": p.get("hashtags", []),
        "status": p.get("status", "draft"),
        "risk": p.get("risk", {}).get("level", "ok"),
        "id": p.get("id", ""),
    } for p in posts]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return path


# --------------------------------------------------------------------
# risk_report.md
# --------------------------------------------------------------------
def save_risk_report(cfg: Dict[str, Any], posts: List[Dict[str, Any]]) -> Path:
    path = config.resolve(cfg["output"]["risk_report"])
    total = len(posts)
    flagged = [p for p in posts if not p.get("risk", {}).get("ok", True)]
    lines: List[str] = []
    lines.append("# リスクチェックレポート")
    lines.append("")
    lines.append(f"- 商品: {cfg['product'].get('name')}")
    lines.append(f"- 生成日時: {_now_iso()}")
    lines.append(f"- 対象投稿数: {total}")
    lines.append(f"- 要確認（警告あり）: {len(flagged)}")
    lines.append("")
    lines.append("対象法令の観点: 薬機法（医薬品的効能効果の標ぼう） / "
                 "景品表示法（優良誤認・誇大広告）")
    lines.append("")

    if not flagged:
        lines.append("## 結果")
        lines.append("")
        lines.append("✅ すべての投稿で注意表現は検出されませんでした。")
        lines.append("")
    else:
        lines.append("## 要確認の投稿")
        lines.append("")
        for p in flagged:
            lines.append(f"### {p.get('title','')}（`{p.get('id','')}`）")
            lines.append("")
            lines.append(f"- テーマ: {p.get('theme','')} / フォーマット: {p.get('format','')}")
            for h in p.get("risk", {}).get("hits", []):
                lines.append(f"- ⚠️ 「{h.get('matched_text')}」 — {h.get('reason')}")
                if h.get("alternatives"):
                    lines.append(f"  - 代替案: {' / '.join(h['alternatives'])}")
            lines.append("")
    return _write(path, "\n".join(lines))


def _write(path: Path, content: str) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
