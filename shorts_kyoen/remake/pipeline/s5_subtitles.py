"""工程⑤ 字幕作成
タイムラインに合わせて、色分け付きの字幕（ASS）と確認用のSRTを書き出す。
"""
from common import BUILD, load_script, load_timeline, plain, spans


def ass_color(hex_rgb):
    h = hex_rgb.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}&"


def ts_ass(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ts_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    sc = load_script()
    meta, st = sc["meta"], sc["meta"]["subtitle"]
    colors = meta["colors"]
    tl = {c["id"]: c for c in load_timeline()["cuts"]}

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {meta['width']}
PlayResY: {meta['height']}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{st['font']},{st['size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,{st['outline']},{st['shadow']},5,20,20,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events, srt = [], []
    for n, cut in enumerate(sc["cuts"], 1):
        t = tl[cut["id"]]
        start = t["start"]
        end = t["start"] + t["speech"] + 0.12
        lines = []
        for line in cut["text"]:
            parts = []
            for text, col, edge in spans(line):
                if col is None:
                    parts.append(text)
                else:
                    tag = f"{{\\c{ass_color(colors[col])}"
                    if edge == "white":
                        tag += "\\3c&H00FFFFFF&"
                    parts.append(tag + "}" + text + "{\\c&H00FFFFFF&\\3c&H00000000&}")
            lines.append("".join(parts))
        body = "\\N".join(lines)
        events.append(f"Dialogue: 0,{ts_ass(start)},{ts_ass(end)},Main,,0,0,0,,"
                      f"{{\\an5\\pos({meta['width']//2},{st['pos_y']})\\fad({st['fade_in_ms']},0)}}{body}")
        srt.append(f"{n}\n{ts_srt(start)} --> {ts_srt(end)}\n" + "\n".join(plain(l) for l in cut["text"]) + "\n")

    (BUILD / "subtitles.ass").write_text(head + "\n".join(events) + "\n", encoding="utf-8")
    (BUILD / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"{len(events)} subtitles -> build/subtitles.ass, build/subtitles.srt")


if __name__ == "__main__":
    main()
