"""公開用テキスト(本書第9章): タイトル(99文字以内・ハッシュタグ付き)→ 表紙3段見出し → 説明文(フルバージョン)。

入力: projects/<P>/publish.yaml(タイトル係・説明文係が書く)
  title: "【…】…？… #愛子さま #皇室"
  thumb: {upper: "…", middle: "…", lower: "…", center_image: "A027"}
  question_topic: "この秋の愛子さまのご活動"
  closing_question: "皆さまの心に残ったのは、どの年のお言葉ですか。"(任意。動画の締めくくりの問いと同じにする。省略時は既定文)
  subject_area: "皇室、歴史、国際親善"
  related_orgs: "宮内庁、皇室、政府機関、…その他の関係団体"
  body: ["段落1", "段落2", ...]
  references: [{title: "宮内庁「…」", note: "…", url: "https://…"}]
  unconfirmed_note: "…"(省略時は既定文)
  hashtags: ["#愛子さま", ...]
出力: projects/<P>/publish/title.txt・description.txt・check.md
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

from .common import ROOT, ng_hits

TITLE_MAX = 99
DEFAULT_UNCONFIRMED = ("本動画では、宮内庁などの公式記録で確認できた出来事のみを紹介しており、"
                       "未確認の逸話や証言は含めていません。")


_ERA = {"令和": 2018, "平成": 1988, "昭和": 1925}


def _ledger_date(field: str) -> str:
    """台帳「撮影日・場所・行事」から、画像クレジットの期間に使う日付(YYYY-MM-DD)を取り出す。
    先頭が年月日ならそれを使う。ご近影のように撮影日が書けない写真は、
    「令和5年12月9日付のご感想のページに掲載」のように書かれた掲載ページの日付(和暦)を西暦に直して使う。
    どちらも無ければ先頭10文字をそのまま返す(期間の計算では数えない)。"""
    head = field[:10]
    if re.match(r"\d{4}-\d\d-\d\d", head):
        return head
    m = re.match(r"(令和|平成|昭和)(元|\d+)年(\d+)月(\d+)日", field) or re.search(r"(令和|平成|昭和)(元|\d+)年(\d+)月(\d+)日付", field)  # 先頭が和暦の年月日ならそれを使う
    if m:
        y = _ERA[m.group(1)] + (1 if m.group(2) == "元" else int(m.group(2)))
        return f"{y:04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    return head


def image_credits(pdir: Path) -> str:
    """表紙と本編で使った画像を台帳から集め、掲載元・提供元を出す。"""
    import json
    used = set()
    shots = pdir / "output" / "shots.json"
    if shots.exists():
        for s in json.loads(shots.read_text(encoding="utf-8")):
            for i in ((s.get("compare") or {}).get("images") or [s.get("image")]):
                if i:
                    used.add(i)
    ty = pdir / "thumb.yaml"
    if ty.exists():
        for ph in (yaml.safe_load(ty.read_text(encoding="utf-8")) or {}).get("photos", []):
            used.add(ph.get("ledger"))
    rows = [r for r in csv.DictReader(open(pdir / "ledger.csv", encoding="utf-8")) if r["番号"] in used]
    by_site: dict[str, set] = {}
    providers: set = set()
    supplied = []
    commons: dict = {}
    for r in rows:
        if r["掲載サイト名"] == "提供写真":
            supplied.append(r)
            continue
        if r["掲載サイト名"] == "Wikimedia Commons":  # 作者・ライセンスを表示(CCの表示義務)
            ma = re.search(r"作者 ([^/／)）]+?)\s*[/／)）]", r["確認したキャプション"])
            ml = re.search(r"(CC[ -][A-Z0-9 .\-]+?)(?:\(|（|$)", r["確認したキャプション"])
            commons.setdefault(f"{ma.group(1).strip() if ma else '作者不明'} {ml.group(1).strip() if ml else ''}".strip(), None)
            continue
        if "©" in r["確認したキャプション"]:
            providers.add(re.search(r"©[^)）、]+", r["確認したキャプション"]).group(0).strip())
        by_site.setdefault(r["掲載サイト名"], set()).add(_ledger_date(r["撮影日・場所・行事"]))
        m = re.search(r"写真(?:提供)?：([^）)]+)", r["確認したキャプション"])
        # 「写真：令和7年…ご近影」「写真：新年をお迎えになった…」のような題名の書式は提供者名ではないので除く(短い名前だけ)
        if m and len(m.group(1).strip()) <= 40 and not re.search(r"[「」]| / |ご近影|お迎え", m.group(1)):
            providers.add(m.group(1).strip())
    lines = []
    for site, dates in by_site.items():
        ds = sorted(d for d in dates if re.match(r"\d{4}-\d\d-\d\d", d))  # 掲載ページにも日付の記載がない写真(「令和7年 …。ページに日付の記載なし」)だけ期間に数えない
        jp = lambda d: f"{int(d[:4])}年{int(d[5:7])}月{int(d[8:10])}日"
        span = f"{jp(ds[0])}〜{jp(ds[-1])}" if len(ds) > 1 else (jp(ds[0]) if ds else "")
        lines.append(f"写真：{site}ウェブサイト（{span}の各行事ページ掲載写真）")
    if commons:
        lines.append("写真：Wikimedia Commons（" + "、".join(commons) + "）")
    seen_sup = set()
    for r in supplied:
        d = r["撮影日・場所・行事"]
        if d in seen_sup:
            continue
        seen_sup.add(d)
        when = f"{int(d[:4])}年{int(d[5:7])}月{int(d[8:10])}日" if re.match(r"\d{4}-\d\d-\d\d", d) else ""
        uses = "・".join(sorted({("表紙" if "表紙" in x["使用する場面"] else "動画") for x in supplied if x["撮影日・場所・行事"] == d}
                               | ({"動画"} if any("動画" in x["使用する場面"] for x in supplied if x["撮影日・場所・行事"] == d) else set())))
        lines.append(f"提供写真：{when} {d[10:].strip()}（{uses}。日付・場所は報道の写真説明で確認）".replace("： ", "："))
    if providers:
        lines.append("写真提供（掲載元の表記による）：" + "、".join(sorted(providers)))
    lines.append(f"使用画像 {len(rows)} 点。人物・日付・行事は掲載元の説明文で確認しています。")
    return "\n\n".join(lines)


def check_hashtags(tags: list[str]) -> list[str]:
    errs = []
    for t in tags:
        if not t.startswith("#") or re.search(r"[\s,、]", t[1:]):
            errs.append(f"ハッシュタグの形式: {t}")
    if len(set(tags)) != len(tags):
        errs.append("ハッシュタグの重複")
    return errs


def build(project: str) -> bool:
    pdir = ROOT / "projects" / project
    spec = yaml.safe_load((pdir / "publish.yaml").read_text(encoding="utf-8"))
    out = pdir / "publish"
    out.mkdir(exist_ok=True)
    errs, notes = [], []
    title = spec["title"].strip()
    # タイトル: 99文字以内・ハッシュタグ付き
    if len(title) > TITLE_MAX:
        errs.append(f"タイトルが{len(title)}文字(上限{TITLE_MAX})")
    if not re.search(r"#\S", title):
        errs.append("タイトルにハッシュタグがない")
    # 表紙3段はタイトルの文言を流用する
    th = spec.get("thumb", {})
    plain = re.sub(r"[【】「」『』\s]", "", title)
    for k in ("upper", "middle", "lower"):
        v = re.sub(r"[【】「」『』\s]", "", th.get(k, ""))
        if th.get("override") and v:  # 荒木の明示指示で3段を指定した時(本書第0章7 優先順位①)
            continue
        if not v or v not in plain:
            errs.append(f"表紙の{k}「{th.get(k)}」がタイトルに含まれていない")
    # 揶揄・対立のNG(本書第1-2章): タイトル・表紙3段・説明文本文
    for name, txt in [("タイトル", title), ("表紙", " ".join(str(th.get(k, "")) for k in ("upper", "middle", "lower"))),
                      ("説明文本文", " ".join(spec.get("body", [])))]:
        if ng_hits(txt):
            errs.append(f"{name}に揶揄・対立のNG語: {'、'.join(ng_hits(txt))}(本書第1-2章)")
    if not th.get("center_image"):
        errs.append("表紙の中心画像(center_image)が未確定")
    tags = spec["hashtags"]
    errs += check_hashtags(tags)
    # YouTubeは1本に61個以上のハッシュタグがあると全て無視する → タイトル込み・重複除きで60個まで
    total_tags = set(tags) | set(re.findall(r"#[^\s#,、]+", title))
    if len(total_tags) > 60:
        errs.append(f"ハッシュタグがタイトル込みで{len(total_tags)}個(上限60。超えるとYouTubeが全て無視する)")
    refs = "\n\n".join(f"{r['title']}\n\n{r['note']}\n\n{r['url']}" for r in spec["references"])
    body = "\n\n".join(b.replace("**", "") for b in spec["body"])  # YouTubeでは装飾にならないので記号は入れない
    tpl = (ROOT / "templates" / "description_template.md").read_text(encoding="utf-8")
    desc = (tpl.replace("{{TITLE}}", title)
               .replace("{{BODY}}", body)
               .replace("{{CLOSING_QUESTION}}", spec.get("closing_question")
                        or f"皆さまは、{spec['question_topic']}について、どのように感じられましたか。")  # 本書第1-5章4: 動画の締めくくりの問いとそろえる
               .replace("{{QUESTION_TOPIC}}", spec["question_topic"])
               .replace("{{REFERENCES}}", refs)
               .replace("{{IMAGE_CREDITS}}", image_credits(pdir))
               .replace("{{SUBJECT_AREA}}", spec.get("subject_area", "皇室、歴史、国際親善"))
               .replace("{{RELATED_ORGS}}", spec["related_orgs"])
               .replace("{{UNCONFIRMED_NOTE}}", spec.get("unconfirmed_note") or DEFAULT_UNCONFIRMED)
               .replace("{{HASHTAGS}}", ", ".join(tags) + ","))  # 最後のハッシュタグにもカンマ
    if "**" in desc or re.search(r"(?m)^#{1,6} ", desc):
        errs.append("説明文にマークダウン記号(** や 見出しの#)が残っている")
    if "{{" in desc:
        errs.append("説明文に未置換の項目がある")
    if not desc.rstrip().endswith(","):
        errs.append("ハッシュタグの末尾にカンマがない")
    if len(desc) > 5000:
        errs.append(f"説明文が{len(desc)}文字(YouTubeの上限5000)")
    notes.append(f"タイトル {len(title)}文字 / 説明文 {len(desc)}文字(上限5000) / ハッシュタグ 説明文{len(tags)}個・タイトル込み{len(total_tags)}個(上限60)")
    (out / "title.txt").write_text(title + "\n", encoding="utf-8")
    (out / "description.txt").write_text(desc, encoding="utf-8")
    rep = ["# 公開用テキスト検査 " + project, "", f"判定: **{'合格' if not errs else '不合格'}**", ""]
    rep += [f"- {n}" for n in notes] + [f"- 不合格: {e}" for e in errs]
    rep += ["", f"表紙3段: 上「{th.get('upper')}」/ 中「{th.get('middle')}」/ 下「{th.get('lower')}」/ 中心画像 {th.get('center_image')}"]
    if th.get("override"):
        rep.append(f"表紙3段の例外: {th['override']}")
    (out / "check.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))
    print("\n=== タイトル ===\n" + title + "\n\n=== 説明文 ===\n" + desc)
    return not errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    sys.exit(0 if build(a.project) else 1)
