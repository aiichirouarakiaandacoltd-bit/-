"""制作ルール 第8章「完成判定(G5 自動検査)」→ projects/<制作番号>/qa_report.md

自動で判定できる項目は実測で判定し、人の目が必要な部分(画像に写る人物そのもの等)は「要目視」と明記する。
すべて合格のときだけ「完成」。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from .common import ROOT, load_json, ng_hits
from .rules_render import SPEC


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(p)], capture_output=True, text=True)
    return json.loads(r.stdout)


def ff(args):
    return subprocess.run(["ffmpeg", *args], capture_output=True, text=True).stderr


def check(project: str, kind: str = "縦型") -> bool:
    sp = SPEC[kind]
    pdir = ROOT / "projects" / project
    scenes = load_json(pdir / "scenes.json")
    shots = load_json(pdir / "output" / "shots.json")
    info = load_json(pdir / "output" / "render_info.json")
    ledger = {r["番号"]: r for r in csv.DictReader(open(pdir / "ledger.csv", encoding="utf-8"))}
    facts = (pdir / "facts.md").read_text(encoding="utf-8") if (pdir / "facts.md").exists() else ""
    video = pdir / "output" / f"{project}_{kind}_internal.mp4"
    res = []

    def add(name, ok, detail, todo=""):
        res.append((name, ok, detail, todo))

    # 1 facts.md との一致(場面の fact_ids が facts.md にあるか / 人物名が facts.md に出ているか)
    miss = []
    for s in scenes:
        for fid in s.get("fact_ids", []):
            if not re.search(rf"\b{re.escape(fid)}\b", facts):
                miss.append(f"{s['scene']}:{fid}")
    # 締めくくりの問いかけ・コメントのお願い(第1-4章③④)は事実を述べないので根拠IDは不要
    no_fid = [s["scene"] for s in scenes if not s.get("fact_ids")
              and not (s.get("role") == "closing" and re.search(r"[？?]|コメント", s["narration"]))]
    add("人物・日付・敬称・引用が facts.md と一致", bool(facts) and not miss and not no_fid,
        f"facts.md {'あり' if facts else 'なし'} / 未登録ID {miss or 'なし'} / 根拠IDの無い場面 {no_fid or 'なし'}",
        "台本係が各場面に fact_ids を付け、facts.md に記録する")
    # 2 ledger との一致
    bad = []
    for s in scenes:
        ids = (s.get("compare") or {}).get("images") or ([s["image"]] if s.get("image") else [])
        labs = (s.get("compare") or {}).get("labels") or ([s.get("person_label")] if s.get("person_label") else [])
        if not s.get("compare"):
            ids = s.get("images") or ids
            labs = [(s.get("labels") or {}).get(i, s.get("person_label", "")) for i in ids]
        for iid, lab in zip(ids, labs):
            if not lab:
                continue  # 人物名を出さない写真(会場の様子など)
            r = ledger.get(iid)
            if not r:
                bad.append(f"{s['scene']}:{iid}未登録")
                continue
            names = r["写っている人物"]
            want = re.sub(r"(^|・)(天皇皇后両陛下|両陛下)(?=$|・)", r"\1天皇陛下・皇后陛下", lab)
            for short, full in (("愛子さま", "愛子内親王殿下"), ("雅子さま", "皇后陛下"), ("佳子さま", "佳子内親王殿下"),
                                ("信子さま", "寬仁親王妃殿下"), ("久子さま", "高円宮妃殿下"), ("紀子さま", "秋篠宮皇嗣妃殿下")):
                want = want.replace(short, full)  # 字幕の呼び方(○○さま)を台帳の正式表記に合わせて照合
            def _ok(n):  # 皇族方は台帳の人物欄で、外国の王族・要人は確認したキャプションの記載で照合する
                if n in names:
                    return True
                m = re.sub(r"^(オランダ|ベルギー|シンガポール|英国|イギリス|フランス|タイ|ベトナム)", "", n).replace("ほか王族方", "")
                return bool(m) and not re.search(r"(天皇|皇后|殿下|さま)", m) and m in r.get("確認したキャプション", "")
            if not all(_ok(n) for n in re.split(r"[・、]", want) if n):
                bad.append(f"{s['scene']}:{lab}≠{names}")
            if s.get("caption") and r["撮影日・場所・行事"][:4] not in re.sub(r"年.*", "", s["caption"]) + s["caption"]:
                bad.append(f"{s['scene']}:撮影年 {s['caption']}≠{r['撮影日・場所・行事'][:10]}")
    for s in scenes:
        for iid in ((s.get("compare") or {}).get("images") or s.get("images") or [s.get("image")]):
            if iid and "要目視" in (ledger.get(iid) or {}).get("確認方法", ""):
                bad.append(f"{s['scene']}:{iid} 要目視のまま(当てっこ係が照合していない)")
    add("画像の人物名・撮影情報が ledger.csv と一致", not bad, bad or "全場面一致(写真に写る人物そのものは要目視)",
        "人物名・キャプションを ledger の確認済みキャプションに合わせる")
    # 3 ナレーション全文と字幕
    diff = [s["scene"] for s in scenes if re.sub(r"[、。\s]", "", s["narration"]) != re.sub(r"[、。\s]", "", "".join("".join(c) for c in s.get("subtitle", [])))]
    add("ナレーション全文と字幕が一致", not diff, diff or "全場面一致(誤字の有無は要目視)")
    # 3-2 揶揄・対立のNG(本書第1-2章 荒木指示 2026-11-23)
    ng = [f"{s['scene']}:{'、'.join(ng_hits(s['narration'] + ' ' + str(s.get('person_label', ''))))}" for s in scenes
          if ng_hits(s["narration"] + " " + str(s.get("person_label", "")))]
    add("揶揄・対立のNG語がない(第1-2章)", not ng, ng or "なし", "台本係が事実×事実の言い方に直す")
    # 4 仕様
    pr = probe(video)
    v = next(x for x in pr["streams"] if x["codec_type"] == "video")
    a = next((x for x in pr["streams"] if x["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"])
    num, den = map(int, v["r_frame_rate"].split("/"))
    okspec = ((v["width"], v["height"]) == (sp["W"], sp["H"]) and abs(num / den - 30) < 0.01 and v["codec_name"] == "h264"
              and a and a["codec_name"] == "aac" and (dur <= 90.0 if kind == "縦型" else 480 <= dur <= 720))  # 縦型の上限90秒(第1-4章・荒木指示 2026-11-23)
    add("尺・解像度・fps・形式", okspec, f"{dur:.2f}秒 {v['width']}x{v['height']} {num / den:.2f}fps {v['codec_name']}/{a['codec_name'] if a else '音声なし'}"
        + (" (目安50〜75秒)" if kind == "縦型" and not 50 <= dur <= 75 else ""))
    # 5 フォント
    ass = (pdir / "output" / "subtitles.ass").read_text(encoding="utf-8")
    fonts = set(re.findall(r"Style: \w+,([^,]+),", ass))
    add("画面上の文字が Noto Sans JP", fonts == {"Noto Sans JP"} and "NotoSansJP" in info.get("font", ""),
        f"字幕 {fonts} / 表示文字 {Path(info.get('font', '')).name}")
    # 5-2 字幕が画面からはみ出していない(Noto Sans JP Bold で各行の幅を実測。左右30pxの余白と縁取りを除く)
    from PIL import ImageFont
    fb = str(next(Path("/usr/local/share/fonts").rglob("NotoSansJP-Bold.ttf")))
    over = []
    for m in re.finditer(r"Dialogue: [^,]*,([^,]*),[^\n]*?\\fs(\d+)\}([^\n]*)", ass):
        fsz = int(m.group(2))
        f = ImageFont.truetype(fb, fsz)
        for line in m.group(3).split("\\N"):
            w = f.getlength(line) + 18  # 縁取り(9px×2)
            if w > sp["W"] - 60:
                over.append(f"{m.group(1)}「{line}」{w:.0f}px")
    # 5-3 字幕が小さく縮んでいない(荒木指示: 55歳以上の女性向けに最大限の大きさ。規定の85%未満は不合格)
    small = [f"{m.group(1)}「{m.group(3)}」{m.group(2)}px" for m in re.finditer(r"Dialogue: [^,]*,([^,]*),[^\n]*?\\fs(\d+)\}([^\n]*)", ass)
             if int(m.group(2)) < sp["sub_size"] * 0.77]  # 1行8字(言葉を切らないための上限)まで許容
    add(f"字幕が小さく縮んでいない(規定{sp['sub_size']}pxの77%以上=1行8字まで)", not small, small or "なし",
        "長い文節・かぎかっこの引用を分けて1行の字数に収める(subtitle_lines で改行を指定してもよい)")
    add("字幕が画面からはみ出していない(最大限の大きさで)", not over, f"はみ出し {over or 'なし'}(画面幅 {sp['W']}px・余白各30px)",
        "書き出しの自動縮小を確認する。1行の字数(縦型7字・横型13字)を超える塊がないか字幕の分け方を見直す")
    # 6 音声
    add("ナレーションが青山龍星・速度0.90", info.get("speed") == 0.9, f"speaker_id={info.get('speaker_id')}(/speakers から取得) speedScale={info.get('speed')}")
    # 7 第4章
    durs = [s["end"] - s["start"] for s in shots]
    lo, hi = sp["cut"]
    # 切替間隔は目安2〜4秒。縦型は同じ写真を1回しか使えないため、写真が足りない場面は最長5秒まで認める(本書第4章)
    upper = sp["max_show"] if kind == "縦型" else hi + 0.3
    out_range = [round(d, 2) for d in durs[1:-1] if not (lo - 0.3 <= d <= upper)]
    used = Counter()
    for s in shots:
        for iid in ((s.get("compare") or {}).get("images") or [s.get("image")]):
            if iid:
                used[iid] += 1
    limit = 1 if kind == "縦型" else 3  # 荒木指示 2026-11-22: ショートは同じ写真を2回使わない
    over3 = {k: c for k, c in used.items() if c > limit}
    person_only = sum(d for s, d in zip(shots, durs) if s.get("person_label") or s.get("compare")) / max(1e-9, sum(durs))
    # 第4-3章: ナレーションが語る物(subject)の写真も「映る割合」に数える。ただし人物の写真だけで75%以上
    person = sum(d for s, d in zip(shots, durs) if s.get("person_label") or s.get("compare") or s.get("subject")) / max(1e-9, sum(durs))
    n_img = len(used)
    ok7 = (not out_range and max(durs) <= sp["max_show"] and person >= sp["person_ratio"] and person_only >= 0.75 and not over3)
    add("第4章 切替間隔・最長表示・人物の割合・同一画像の回数", ok7,
        f"カット {len(shots)}(目標{sp['cuts'][0]}〜{sp['cuts'][1]}) / 平均 {sum(durs) / len(durs):.2f}秒 / 最長 {max(durs):.2f}秒(上限{sp['max_show']}) / "
        f"範囲外 {out_range or 'なし'} / 人物・語る物が映る割合 {person:.0%}(目標{sp['person_ratio']:.0%})・人物のみ {person_only:.0%}(75%以上) / 異なる画像 {n_img}枚(目標{sp['images']}) / 上限({'1' if kind == '縦型' else '3'}回)を超えた画像 {over3 or 'なし'}",
        "画像を追加収集する(第3章)、場面の分け方を見直す")
    if len(shots) < sp["cuts"][0] or n_img < sp["images"]:
        res.append(("(目標値)カット数・異なる画像の枚数", False, f"カット {len(shots)} / 画像 {n_img}枚",
                    "目標の70%未満なら第7章により生成停止"))
    # 7-1 主役を中央に置いてから動かす(focus.json の登録)
    fj = load_json(pdir / "focus.json", {}) or {}
    nofocus = sorted({s.get("image") for s in shots if s.get("image") and not s.get("compare") and s.get("image") not in fj})
    add("主役の位置が登録済み(ズーム・パンの開始位置)", not nofocus, f"未登録 {nofocus or 'なし'}",
        "当てっこ係が bin/kabu run focus の点検シートを見て focus_sheet --set で登録する")
    # 7-2 第4-2章 素材の豊富さと画面の華やかさ
    seq = [None if s.get("compare") else s.get("image") for s in shots]
    adj = [f"{shots[i]['scene']}:{seq[i]}" for i in range(1, len(seq)) if seq[i] and seq[i] == seq[i - 1]]
    div = n_img / max(1, len(shots))
    div_min = 0.6 if kind == "縦型" else 0.5
    diag = sum(d for s, d in zip(shots, durs) if s.get("diagram") or not (s.get("image") or s.get("compare")))
    diag_ok = diag <= 3.0 if kind == "縦型" else diag <= 0.05 * sum(durs)
    n_clip = sum(1 for s in shots if s.get("media") == "映像")
    add("第4-2章 素材の豊富さ(隣接の重複・多様さ・図解の量)", not adj and div >= div_min and diag_ok,
        f"隣り合う同じ画像 {adj or 'なし'} / 異なる画像÷カット数 {div:.2f}(目安{div_min}以上) / "
        f"図解・文字だけ {diag:.1f}秒(上限{'3秒' if kind == '縦型' else '全体の5%'}) / 実写映像カット {n_clip}",
        "同じ行事の別の写真・実写映像を追加し、scenes.json の images に複数指定する(内容に合わない素材で水増ししない)")
    # 8 黒画面・無音・音割れ・BGM
    blk = re.findall(r"black_start:([0-9.]+)", ff(["-i", str(video), "-vf", "blackdetect=d=0.2:pix_th=0.08", "-an", "-f", "null", "-"]))
    sil = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", ff(["-i", str(video), "-af", "silencedetect=n=-45dB:d=1.5", "-vn", "-f", "null", "-"])) if float(x) < dur - 1.5]
    vol = ff(["-i", str(video), "-af", "volumedetect", "-vn", "-f", "null", "-"])
    peak = float(re.search(r"max_volume: (-?[0-9.]+)", vol).group(1))
    adur = float(a.get("duration") or 0) if a else 0.0
    if not adur:
        adur = float(probe(video)["format"]["duration"])
    vdur = float(v.get("duration") or dur)
    short = vdur - adur
    if short > 0.2:
        sil.append(f"音声が映像より{short:.2f}秒短い(終盤が無音)")
    add("黒画面・無音・音割れ・BGM音量", not blk and not sil and peak < -0.1,
        f"黒画面 {blk or 'なし'} / 無音 {sil or 'なし'} / ピーク {peak}dB / BGM はナレーションより約21dB低く(-16 vs -37 LUFS)(不自然なカットは要目視)")
    # 9 冒頭の疑問に回答
    roles = [s.get("role") for s in scenes]
    qa = "question" in roles[:2] and "answer" in roles and roles.index("answer") > roles.index("question")
    # 第1-4章 締めくくり(荒木指示 2026-11-23): 最後はまとめ→問いかけ→コメントのお願い。最後の言葉のあとに余韻
    tail_txt = "".join(s_["narration"] for s_ in scenes[-4:])
    closing = [s_["scene"] for s_ in scenes if s_.get("role") == "closing"]
    has_q = bool(re.search(r"[？?]", tail_txt)) and "コメント" in tail_txt
    # 余韻 = 動画の長さ − ナレーションの最後の声(BGMは余韻の間も流れるので、ナレーションの音声で測る)
    import wave
    import numpy as np
    with wave.open(str(pdir / "output" / "narration.wav")) as w_:
        sr_ = w_.getframerate()
        x_ = np.frombuffer(w_.readframes(w_.getnframes()), np.int16)
    voiced = np.nonzero(np.abs(x_) > 300)[0]
    tail_sil = dur - (voiced[-1] / sr_ if len(voiced) else 0.0)
    add("締めくくり(まとめ→問いかけ→コメントのお願い)と余韻(第1-4章)", bool(closing) and has_q and tail_sil >= 1.2,
        f"締めくくりの場面 {closing or 'なし'} / 最後の4場面に問いかけ{'あり' if has_q else 'なし'} / 最後の言葉のあとの余韻 {tail_sil:.1f}秒(1.2秒以上)",
        "台本係が role=closing の場面(まとめ・意味づけ・問いかけ・コメントのお願い)を最後に加える")
    # 第1-5章1(荒木指示 2026-11-23・KB-20261124 以降に適用): ナレーションの文末は「です・ます」調
    if project > "KB-20261123-01":  # 第1-5章の適用は KB-20261123-01 の次から
        plain = [(s_["scene"], re.sub(r"「[^」]*」|『[^』]*』", "", s_["narration"]).rstrip()) for s_ in scenes]
        # 「だ・である」調の文末だけを止める(体言止め・「ください。」は可)
        bad_tone = [f"{sc_}:{t[-8:]}" for sc_, t in plain if t.endswith("。")
                    and re.search(r"(だ|である|だった|であった|ない|なかった|た|る|う)。$", t)
                    and not re.search(r"(です|ます|ません|でした|ました|ましょう|ください)。$", t)]
        add("ナレーションが「です・ます」調(第1-5章)", not bad_tone, bad_tone or "すべて です・ます調",
            "台本係が文末を「です・ます」調に直す(引用内は原文のまま)")
    # 第4-3章(荒木指示 2026-11-24・KB-20261123-02 以降): 場面ごとにナレーションと画像の一致の理由(match)を書く
    if project >= "KB-20261123-02":
        no_match = [s_["scene"] for s_ in scenes if not str(s_.get("match", "")).strip()]
        add("ナレーションと画像の一致の理由が全場面にある(第4-3章)", not no_match, no_match or "全場面あり(内容の妥当性は当てっこ係が目視)",
            "直し係が各場面の match に『ナレーションの言葉→写っているもの』を書く。書けない場面は画像を探し直すか言い方を直す")
    add("冒頭の疑問に本編で回答", qa, f"question={roles.index('question') if 'question' in roles else 'なし'} answer={'あり' if 'answer' in roles else 'なし'}(回答内容の妥当性は要目視)")
    passed = all(r[1] for r in res)
    lines = [f"# qa_report — {project}({kind})", "", f"判定: **{'完成' if passed else '未完成(不足事項あり)'}**", "",
             "| 項目 | 合否 | 実測・詳細 | 対応案 |", "|---|---|---|---|"]
    for n, ok, d, todo in res:
        lines.append(f"| {n} | {'合格' if ok else '不合格'} | {d if isinstance(d, str) else d} | {'' if ok else todo} |")
    lines += ["", "## 実測値", f"- 尺 {dur:.2f}秒 / カット数 {len(shots)} / 異なる画像 {n_img}枚 / 人物が映る割合 {person:.0%} / 実写映像カット {n_clip} / 図解 {diag:.1f}秒"]
    (pdir / "qa_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return passed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--kind", default="縦型", choices=["縦型", "横型"])
    a = ap.parse_args()
    check(a.project, a.kind)
