"""ステージ5: 字幕生成(ASS)。

- ナレーションの文を文節単位で分割し、1チャンク最大2行×11字に収める(参考動画: 約1.2秒/チャンク)
- チャンクの表示時間は、文の実測長を読みのモーラ数で按分して算出(音声との同期)
- 人物名は人物ごとの固定色、核心語は赤で強調(白縁+黒外縁の二重縁取り)
- 登場演出: ポップイン / スライドイン / フェード(参考動画の3種)
出力: subtitles/<job>/subtitles.ass, chunks.json
"""
from __future__ import annotations

import re

from .common import Job, get_logger, load_json, save_json, style
from .tts import apply_readings, mora_count

CONTENT_POS = {"名詞", "動詞", "形容詞", "副詞", "連体詞", "接続詞", "感動詞", "形容動詞"}


def bunsetsu(text: str) -> list[str]:
    """pyopenjtalk の形態素解析で文節に分割(簡易規則)。"""
    import pyopenjtalk
    import unicodedata
    njd = pyopenjtalk.run_frontend(text)
    # 解析器は数字等を書き換える(15→十五)ため、原文の文字列に位置合わせする
    toks = [unicodedata.normalize("NFKC", w["string"]) for w in njd]
    src = text
    pos = 0
    for k, w in enumerate(njd):
        t = toks[k]
        if src[pos:pos + len(t)] == t or unicodedata.normalize("NFKC", src[pos:pos + len(t)]) == t:
            w["string"] = src[pos:pos + len(t)]
            pos += len(t)
            continue
        nxt = None
        for t2 in toks[k + 1:]:
            if t2:
                f = src.find(t2, pos)
                if f >= pos:
                    nxt = f
                    break
        end = nxt if nxt is not None else len(src)
        w["string"] = src[pos:end]
        pos = end
    if pos < len(src) and njd:
        njd[-1]["string"] += src[pos:]
    out: list[str] = []
    prev_pos = None
    prev_detail = ""
    in_quote = False
    for w in njd:
        s, pos = w["string"], w["pos"]
        if not s:
            continue
        detail = w.get("pos_group1", "")
        start_new = (s in ("「", "『") and bool(out)) or (
            out and not in_quote and pos == "接頭詞" and prev_pos in ("助詞", "助動詞", "動詞", "記号")
        ) or (
            out
            and not in_quote
            and pos in CONTENT_POS
            and prev_pos is not None
            and (prev_pos in ("助詞", "助動詞", "記号") or (prev_pos in ("動詞", "形容詞") and pos != "動詞"))
            and detail not in ("非自立", "接尾")
            and prev_pos != "接頭詞"
            and s not in ("さま", "様", "さん")
        )
        if s in ("「", "『"):
            in_quote = True
        if s in ("」", "』"):
            in_quote = False
        if out and out[-1].endswith("、") and not start_new and s not in ("」", "』"):
            start_new = True
        if start_new or not out:
            out.append(s)
        else:
            out[-1] += s
        prev_pos = pos
        prev_detail = detail
    # かぎかっこの中は分割しない
    q: list[str] = []
    for b in out:
        if q and q[-1].count("「") + q[-1].count("『") > q[-1].count("」") + q[-1].count("』"):
            q[-1] += b
        else:
            q.append(b)
    out = q
    # 句読点は直前の文節にくっつける。全角記号のみの文節を除去
    merged: list[str] = []
    for b in out:
        if merged and re.fullmatch(r"[、。！？!?」』…]+", b):
            merged[-1] += b
        else:
            merged.append(b)
    return merged


def _visible_len(s: str) -> int:
    return len(re.sub(r"[、。]", "", s))


def _fits(parts: list[str], max_line: int) -> bool:
    if _visible_len("".join(parts)) <= max_line:
        return True
    for i in range(1, len(parts)):
        if _visible_len("".join(parts[:i])) <= max_line and _visible_len("".join(parts[i:])) <= max_line:
            return True
    return False


def pack_chunks(bs: list[str], max_line: int, target: int = 6, max_chunk: int = 14) -> list[list[str]]:
    chunks: list[list[str]] = []
    cur: list[str] = []
    for b in bs:
        cand = cur + [b]
        L = sum(_visible_len(x) for x in cand)
        if cur and (L > max_chunk or not _fits(cand, max_line) or (sum(_visible_len(x) for x in cur) >= target)):
            chunks.append(cur)
            cur = [b]
        else:
            cur = cand
        if cur and cur[-1].endswith("、") and sum(_visible_len(x) for x in cur) >= 7:
            chunks.append(cur)
            cur = []
    if cur:
        # 短すぎる最終チャンクは前に結合
        if chunks and sum(_visible_len(x) for x in cur) <= 4 and _fits(chunks[-1] + cur, max_line):
            chunks[-1] += cur
        else:
            chunks.append(cur)
    return chunks


def to_lines(parts: list[str], max_line: int) -> list[str]:
    text = "".join(parts)
    text_disp = re.sub(r"[、。]$", "", text)  # 文末の句点は表示しない(参考動画準拠)
    if _visible_len(text_disp) <= max_line:
        return [text_disp]
    # 文節境界のうち、2行がなるべく均等になる位置で改行
    best, best_score = None, 1e9
    acc = ""
    for i in range(1, len(parts)):
        acc = "".join(parts[:i])
        rest = "".join(parts[i:])
        l1, l2 = _visible_len(acc), _visible_len(re.sub(r"[、。]$", "", rest))
        score = abs(l1 - l2) + 100 * (max(l1, l2) > max_line)
        if score < best_score:
            best, best_score = i, score
    if best is not None and best_score < 100:
        return ["".join(parts[:best]), re.sub(r"[、。]$", "", "".join(parts[best:]))]
    return _hard_split(text_disp, max_line)


def _hard_split(t: str, max_line: int) -> list[str]:
    """1文節が長すぎる場合: 助詞・空白の直後で、英数字の途中を避けて中央付近で分割。"""
    mid = len(t) / 2
    best, bs = None, 1e9
    for i in range(1, len(t)):
        if t[i - 1].isascii() and t[i].isascii() and t[i - 1].isalnum() and t[i].isalnum():
            continue
        score = abs(i - mid) - (3 if t[i - 1] in "のでにをはがと、 " else 0)
        if score < bs:
            best, bs = i, score
    i = best or int(mid)
    return [t[:i].rstrip(), t[i:].lstrip()]


def _ass_color(hex_rgb: str, alpha="00") -> str:
    h = hex_rgb.lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def highlight_spans(line: str, terms: list[str], colors: dict, emph: str) -> list[tuple[str, str | None]]:
    """行を [(text, color|None)] に分割。長い語を優先。"""
    marks = [None] * len(line)
    for term in sorted(set(terms), key=len, reverse=True):
        if not term:
            continue
        for m in re.finditer(re.escape(term), line):
            if all(marks[k] is None for k in range(m.start(), m.end())):
                col = colors.get(term) or next((c for k, c in colors.items() if k in term), None) or emph
                for k in range(m.start(), m.end()):
                    marks[k] = col
    spans: list[tuple[str, str | None]] = []
    for ch, col in zip(line, marks):
        if spans and spans[-1][1] == col:
            spans[-1] = (spans[-1][0] + ch, col)
        else:
            spans.append((ch, col))
    return spans


def _t(sec: float) -> str:
    sec = max(0, sec)
    h, m = int(sec // 3600), int(sec % 3600 // 60)
    s = sec - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(job: Job, chunks: list[dict]) -> None:
    """チャンク列を ASS 字幕として書き出す(チャンクごとに色・登場演出・サイズの上書き可)。"""
    st = style()["rules"]["subtitle"]
    W, H = 1080, 1920
    colors = st["person_colors"]
    emph = st["emphasis_color"]
    font = st["font_candidates"][0]
    cy = int(H * st["center_y"])
    white, black = _ass_color(st["primary_color"]), _ass_color(st["outline_color"])
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Back,{font},{st['font_size']},{black},{black},{black},&H64000000&,0,0,0,0,{st.get('scale_x', 100)},{st.get('scale_y', 100)},2,0,1,{st['outline_px'] + 5},{st['shadow_px']},5,40,40,0,1
Style: Main,{font},{st['font_size']},{white},{white},{black},&H00000000&,0,0,0,0,{st.get('scale_x', 100)},{st.get('scale_y', 100)},2,0,1,3,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for i, c in enumerate(chunks):
        hook = c.get("hook", i == 0 and c.get("role") == "hook")
        size = c.get("size") or (st["hook_font_size"] if hook else st["font_size"])
        ccolors = {**colors, **c.get("colors", {})}
        dur_ms = int((c["end"] - c["start"]) * 1000)
        has_hl = any(col for ln in c["lines"] for _, col in highlight_spans(ln, c["terms"], ccolors, emph))
        kind = c.get("entrance_fixed") or ("pop" if (hook or has_hl) else ("slide" if c.get("sentence_start") else "fade"))
        c["entrance"] = kind
        ms = st["entrance_ms"]
        if kind == "pop":
            sx, sy = st.get("scale_x", 100), st.get("scale_y", 100)
            anim = f"\\fscx{sx * 0.55:.0f}\\fscy{sy * 0.55:.0f}\\t(0,{ms},\\fscx{sx}\\fscy{sy})"
            pos = f"\\pos(540,{cy})"
        elif kind == "slide":
            anim = f"\\fad({ms},0)"
            pos = f"\\move(470,{cy},540,{cy},0,{ms})"
        else:
            anim = f"\\fad({ms},0)"
            pos = f"\\pos(540,{cy})"
        back_txt, main_txt = [], []
        for ln in c["lines"]:
            spans = highlight_spans(ln, c["terms"], ccolors, emph)
            if hook or c.get("all_color"):
                spans = [(ln, c.get("all_color") or emph)]
            back_txt.append(ln)
            seg = ""
            for txt, col in spans:
                if col:
                    seg += f"{{\\c{_ass_color(col)}\\3c{white}\\bord{st['highlight_outline_px']}}}{txt}"
                else:
                    seg += f"{{\\c{white}\\3c{black}\\bord3}}{txt}"
            main_txt.append(seg)
        base = f"{{\\an5{pos}\\fs{size}{anim}}}"
        ev.append(f"Dialogue: 0,{_t(c['start'])},{_t(c['end'])},Back,,0,0,0,,{base}" + "\\N".join(back_txt))
        ev.append(f"Dialogue: 1,{_t(c['start'])},{_t(c['end'])},Main,,0,0,0,,{base}" + "\\N".join(main_txt))
        c["duration_ms"] = dur_ms
    job.ass.write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")


def build(job: Job, script: dict, timeline: dict) -> list[dict]:
    log = get_logger(job)
    st = style()["rules"]["subtitle"]
    W, H = 1080, 1920
    colors = st["person_colors"]
    emph = st["emphasis_color"]
    max_line = st["max_chars_per_line"]
    extra = script.get("readings", {})
    scene_by_id = {s["id"]: s for s in script["scenes"]}

    chunks = []
    for sc in timeline["scenes"]:
        terms = list(scene_by_id[sc["id"]].get("highlights", [])) + list(colors.keys())
        sents = sc["sentences"]
        for si, se in enumerate(sents):
            parts_list = pack_chunks(bunsetsu(se["text"]), max_line)
            mor = [mora_count(apply_readings("".join(p), extra)) for p in parts_list]
            total = sum(mor)
            # 文の終わり〜次の文の開始まで字幕を残す(間で画面が空にならない)
            nxt = sents[si + 1]["start"] if si + 1 < len(sents) else sc["end"]
            t = se["start"]
            span = se["end"] - se["start"]
            for k, (p, m) in enumerate(zip(parts_list, mor)):
                d = span * m / total
                end = t + d if k < len(parts_list) - 1 else nxt
                chunks.append({"scene": sc["id"], "role": sc.get("role"), "start": round(t, 3), "end": round(end, 3),
                               "lines": to_lines(p, max_line), "terms": terms,
                               "sentence_start": k == 0})
                t += d
    # 最短表示時間の確保(短すぎるチャンクは次と結合)
    min_d = st["min_chunk_sec"]
    merged = []
    for c in chunks:
        if merged and merged[-1]["end"] - merged[-1]["start"] < min_d and merged[-1]["scene"] == c["scene"] \
                and sum(len(x) for x in merged[-1]["lines"] + c["lines"]) <= 2 * max_line:
            joined = "".join(merged[-1]["lines"]) + "".join(c["lines"])
            merged[-1]["lines"] = to_lines([joined], max_line) if len(joined) <= max_line else [ "".join(merged[-1]["lines"]), "".join(c["lines"])]
            merged[-1]["end"] = c["end"]
        else:
            merged.append(c)
    chunks = merged
    if chunks:
        chunks[-1]["end"] = max(chunks[-1]["end"], timeline["duration"] - 0.05)

    write_ass(job, chunks)
    save_json(job.subs / "chunks.json", chunks)
    avg = sum(c["end"] - c["start"] for c in chunks) / max(1, len(chunks))
    log.info(f"字幕 {len(chunks)}チャンク (平均{avg:.2f}秒) → {job.ass}")
    job.mark("subtitles", True, chunks=len(chunks), avg_sec=round(avg, 2))
    return chunks


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    j = Job(a.job)
    build(j, load_json(j.script), load_json(j.timeline))
