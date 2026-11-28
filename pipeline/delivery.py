"""納品の組み立て(荒木指示 2026-11-28: 納品はこの順番で並べる)

  ① 長尺動画
  ② タイトル(ハッシュタグ付き)
  ③ タイトルに連動したサムネイル(②の下や横に③を置く)
  ④ 長尺動画の説明文
  ⑤ ショート動画
  ⑥ タイトル(ハッシュタグ付き)
  ⑦ カバー2種類
  ⑧ ショート動画の説明文

使い方:
  python -m pipeline.delivery delivery.yaml
delivery.yaml の書き方は templates/delivery_template.yaml。
出力: delivery/<name>/ に番号付きのファイルと、①〜⑧の順に並べた 0_納品ページ.html。
"""
from __future__ import annotations

import base64
import html
import io
import shutil
import sys
from pathlib import Path

import yaml
from PIL import Image

from .common import ROOT


def _img_uri(p: Path, w: int) -> str:
    im = Image.open(p).convert("RGB")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    b = io.BytesIO(); im.save(b, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def _copy(src: str | None, dst: Path) -> str:
    """動画・画像を納品フォルダへ。無ければ『未完成』と返す(止めずに一覧で目立たせる)。"""
    if not src:
        return "未完成"
    s = (ROOT / src) if not Path(src).is_absolute() else Path(src)
    if not s.exists():
        return f"未完成(見つからない: {src})"
    dst = dst.with_suffix(s.suffix)
    try:
        if dst.exists(): dst.unlink()
        dst.hardlink_to(s)
    except OSError:
        shutil.copy2(s, dst)
    return dst.name


def _read_text(v: str) -> str:
    p = ROOT / v
    return p.read_text(encoding="utf-8").strip() if (len(v) < 300 and p.exists()) else v.strip()


def build(cfg_path: str) -> Path:
    cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    out = ROOT / "delivery" / cfg["name"]
    out.mkdir(parents=True, exist_ok=True)
    L, shorts = cfg["long"], cfg.get("shorts", [])
    sec, problems = [], []

    def card(no: str, head: str, body: str) -> None:
        sec.append(f'<section><h2><span class="no">{no}</span>{head}</h2>{body}</section>')

    def copybox(key: str, text: str) -> str:
        return (f'<div class="t"><pre id="{key}">{html.escape(text)}</pre>'
                f'<button data-t="{key}">コピー</button></div>')

    # ① 長尺動画
    v = _copy(L.get("video"), out / "1_長尺動画")
    if v.startswith("未完成"): problems.append("① 長尺動画: " + v)
    card("①", "長尺動画", f"<p class='file'>{html.escape(v)}</p>")
    # ②③ タイトルと、連動したサムネイル(横に並べる)
    rows, titles_txt = [], []
    for t in L["ab_tests"]:
        tid, title = t["id"], t["title"].strip()
        if len(title) > 99: problems.append(f"② タイトル{tid}: {len(title)}文字(99文字を超える)")
        if "#" not in title: problems.append(f"② タイトル{tid}: ハッシュタグがない")
        th = ROOT / t["thumb"]
        name = _copy(t["thumb"], out / f"3_長尺_サムネイル_{tid}")
        img = f'<img src="{_img_uri(th, 640)}" alt="サムネイル{tid}">' if th.exists() else "<p>未完成</p>"
        if not th.exists(): problems.append(f"③ サムネイル{tid}: 未完成")
        rows.append(f'<div class="pair"><div><h3>パターン{tid}</h3>{copybox("title" + tid, title)}</div>'
                    f'<figure>{img}<figcaption>{html.escape(name)}</figcaption></figure></div>')
        titles_txt.append(f"【パターン{tid}】\n{title}\n(サムネイル: {name})")
    (out / "2_長尺_タイトル.txt").write_text("\n\n".join(titles_txt) + "\n", encoding="utf-8")
    card("②③", "タイトル(ハッシュタグ付き)と、連動したサムネイル", "".join(rows))
    # ④ 長尺の説明文
    desc = _read_text(L.get("description", "")) if L.get("description") else ""
    if not desc: problems.append("④ 長尺の説明文: 未完成")
    (out / "4_長尺_説明文.txt").write_text(desc + "\n", encoding="utf-8")
    card("④", "長尺動画の説明文", copybox("desc_long", desc or "未完成"))
    # ⑤〜⑧ ショート(複数本なら 5-1, 5-2 …)
    for i, S in enumerate(shorts, 1):
        sfx = f"-{i}" if len(shorts) > 1 else ""
        v = _copy(S.get("video"), out / f"5{sfx}_ショート動画")
        if v.startswith("未完成"): problems.append(f"⑤{sfx} ショート動画: " + v)
        card(f"⑤{sfx}", "ショート動画", f"<p class='file'>{html.escape(v)}</p>")
        title = S["title"].strip()
        if len(title) > 99: problems.append(f"⑥{sfx} タイトル: {len(title)}文字(99文字を超える)")
        if "#" not in title: problems.append(f"⑥{sfx} タイトル: ハッシュタグがない")
        (out / f"6{sfx}_ショート_タイトル.txt").write_text(title + "\n", encoding="utf-8")
        card(f"⑥{sfx}", "タイトル(ハッシュタグ付き)", copybox(f"title_s{i}", title))
        figs = []
        covers = S.get("covers", [])
        if len(covers) != 2: problems.append(f"⑦{sfx} カバー: {len(covers)}枚(2種類必要)")
        for j, c in enumerate(covers, 1):
            cp = ROOT / c["file"]
            name = _copy(c["file"], out / f"7{sfx}_ショート_カバー{j}")
            img = f'<img src="{_img_uri(cp, 400)}" alt="カバー{j}">' if cp.exists() else "<p>未完成</p>"
            figs.append(f'<figure>{img}<figcaption>{j} {html.escape(c.get("label", ""))}<br>{html.escape(name)}</figcaption></figure>')
        card(f"⑦{sfx}", "カバー2種類", f'<div class="covers">{"".join(figs)}</div>')
        d = _read_text(S.get("description", "")) if S.get("description") else ""
        if not d: problems.append(f"⑧{sfx} ショートの説明文: 未完成")
        (out / f"8{sfx}_ショート_説明文.txt").write_text(d + "\n", encoding="utf-8")
        card(f"⑧{sfx}", "ショート動画の説明文", copybox(f"desc_s{i}", d or "未完成"))

    warn = ("<div class='warn'><b>そろっていないもの</b><ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in problems)
            + "</ul></div>") if problems else ""
    page = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(cfg['name'])} 納品</title>
<style>
/* VOICE: plain delivery sheet / IDEA: a numbered hand-off checklist ①〜⑧ / PICTURE: thumbnails beside titles / COLOUR: white, ink, gold number / TYPE+LAYOUT: Noto Sans JP, one column */
:root{{color-scheme:light dark;--bg:light-dark(#fff,#111);--ink:light-dark(#111,#eee);--line:light-dark(#ddd,#333);--box:light-dark(#f4f4f2,#1c1c1c)}}
:root[data-theme=light]{{color-scheme:light}}:root[data-theme=dark]{{color-scheme:dark}}
*{{box-sizing:border-box;min-width:0}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Noto Sans JP",sans-serif}}
main{{max-width:1100px;margin:auto;padding:clamp(20px,4vw,48px) max(4vw,14px)}}h1{{font-size:clamp(22px,4vw,30px);margin:0 0 6px}}
section{{border-top:1px solid var(--line);padding:22px 0}}h2{{font-size:20px;margin:0 0 10px}}h3{{font-size:16px;margin:0 0 6px}}
.no{{display:inline-block;min-width:2.2em;color:#b8862e;font-weight:700}}.file{{font-weight:700}}
.pair{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:16px;margin:0 0 20px;align-items:start}}
@media(max-width:700px){{.pair{{grid-template-columns:minmax(0,1fr)}}}}
.t{{display:flex;gap:8px;align-items:flex-start;background:var(--box);padding:10px;border-radius:6px;flex-wrap:wrap}}
pre{{flex:1 1 280px;margin:0;white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 "Noto Sans JP",sans-serif;max-height:320px;overflow:auto}}
button{{min-height:44px;padding:0 16px;font:inherit;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);cursor:pointer}}
img{{width:100%;height:auto;display:block;border-radius:4px}}figure{{margin:0}}figcaption{{font-size:13px;margin-top:4px}}
.covers{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;max-width:560px}}
.warn{{background:#fff3c4;color:#111;padding:12px 16px;border-radius:6px;margin:12px 0}}
</style><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap"></head><body><main>
<h1>{html.escape(cfg['name'])} 納品</h1><p>①長尺動画 → ②タイトル → ③サムネイル → ④説明文 → ⑤ショート動画 → ⑥タイトル → ⑦カバー2種類 → ⑧説明文 の順です。</p>
{warn}{''.join(sec)}</main><script>{{for(const b of document.querySelectorAll("button[data-t]"))b.addEventListener("click",async()=>{{const t=document.getElementById(b.dataset.t).textContent;try{{await navigator.clipboard.writeText(t);b.textContent="コピーしました"}}catch(e){{b.textContent="長押しで選んでコピー"}}}})}}</script></body></html>"""
    (out / "0_納品ページ.html").write_text(page, encoding="utf-8")
    print(out)
    for p in problems: print("要確認:", p)
    return out


if __name__ == "__main__":
    build(sys.argv[1])
