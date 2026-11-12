"""工程⑦ 動画収集（素材の切り出し）
script.json の src 区間を素材動画から切り出し、ナレーションの長さに合わせて
再生速度を調整し、レイアウト（全画面／上下帯つき）を組んだカット動画を作る。

※素材動画が字幕焼き込み済み（今回の練習用）の場合は、字幕のあった帯をぼかして消す。
  字幕なしの元素材に差し替える場合は、script.json の source_subtitle_mask を削除する。
"""
import subprocess

from common import BUILD, ROOT, load_script, load_timeline


def main():
    sc = load_script()
    m = sc["meta"]
    W, H, fps = m["width"], m["height"], m["fps"]
    sw, sh = m["source_size"]
    mask = m.get("source_subtitle_mask")
    tl = {c["id"]: c for c in load_timeline()["cuts"]}
    src = ROOT / m["source_video"]
    (BUILD / "clips").mkdir(parents=True, exist_ok=True)

    for c in sc["cuts"]:
        a, b = c["src"]
        dur = tl[c["id"]]["dur"]
        k = dur / (b - a)  # 1より大きい＝ゆっくり、小さい＝速く
        f = [f"[0:v]trim=start={a}:end={b},setpts=(PTS-STARTPTS)*{k:.5f},fps={fps},scale={sw}:{sh}[v0]"]
        last = "v0"
        if mask:
            y0, y1 = mask["y0"], mask["y1"]
            f.append(f"[{last}]split[m0][m1];[m1]crop={sw}:{y1 - y0}:0:{y0},boxblur=26:3,format=yuva420p[mb0];"
                     f"[MASK]format=gray,scale={sw}:{y1 - y0}[mk];[mb0][mk]alphamerge[mb];"
                     f"[m0][mb]overlay=0:{y0}[v1]")
            last = "v1"
        if c["layout"] == "full":
            f.append(f"[{last}]scale={W}:{H}:flags=lanczos,setsar=1[out]")
            inputs = []
        else:
            b0, b1 = c["band"]
            y = round(b0 * H / sh)
            f.append(f"[{last}]crop={sw}:{b1 - b0}:0:{b0},scale={W}:-2:flags=lanczos[band];"
                     f"[1:v]scale={W}:{H}[bg];[bg][band]overlay=0:{y}[lb]")
            last = "lb"
            inputs = ["-loop", "1", "-i", str(BUILD / "img" / f"bg_{c['bg']}.png")]
            if c.get("overlay"):
                inputs += ["-loop", "1", "-i", str(BUILD / "img" / f"{c['overlay']}.png")]
                f.append("[lb][2:v]overlay=0:0[ov]")
                last = "ov"
            f.append(f"[{last}]setsar=1[out]")
        if mask:
            # マスク画像を最後の入力として追加し、その番号でフィルタ内の[MASK]を置き換える
            n_in = 1 + inputs.count("-i")
            inputs += ["-loop", "1", "-i", str(BUILD / "img" / "mask.png")]
            f = [x.replace("[MASK]", f"[{n_in}:v]") for x in f]
        out = BUILD / "clips" / f"cut_{c['id']:02d}.mp4"
        csrc = ROOT / c["file"] if c.get("file") else src
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(csrc), *inputs,
               "-filter_complex", ";".join(f), "-map", "[out]", "-t", f"{dur:.3f}",
               "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-an", str(out)]
        subprocess.run(cmd, check=True)
        print(f"cut {c['id']:02d}: src {a:.2f}-{b:.2f}s x{k:.2f} -> {dur:.2f}s ({c['layout']})")


if __name__ == "__main__":
    main()
