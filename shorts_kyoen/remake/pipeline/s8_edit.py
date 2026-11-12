"""工程⑧ 動画編集
カット動画をつなぎ、字幕を焼き込み、ナレーションとBGMを合わせて完成版を書き出す。
"""
import subprocess

import json

from common import BUILD, OUTPUT, ROOT, load_script


def main():
    sc = load_script()
    OUTPUT.mkdir(exist_ok=True)
    lst = BUILD / "clips.txt"
    lst.write_text("".join(f"file 'clips/cut_{c['id']:02d}.mp4'\n" for c in sc["cuts"]), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(BUILD / "video_nosub.mp4")], check=True)

    total = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))["total"]
    bg = sc["meta"].get("bgm", {})
    if bg.get("file"):
        # BGMを動画の長さで切り、音量を合わせ、最後をフェードアウト
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(ROOT / bg["file"]), "-t", f"{total:.3f}",
                        "-af", f"loudnorm=I={bg['loudness_lufs']}:TP=-6:LRA=11,"
                               f"afade=t=out:st={total - bg['fade_out_sec']:.3f}:d={bg['fade_out_sec']}",
                        "-ar", "48000", "-ac", "2", str(BUILD / "bgm.wav")], check=True)
        bgm_gain = "0dB"
    else:
        bgm_gain = "-26dB"

    ass = str(BUILD / "subtitles.ass").replace(":", r"\:")
    out = OUTPUT / "final.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-i", str(BUILD / "video_nosub.mp4"),
        "-i", str(BUILD / "narration.wav"),
        "-i", str(BUILD / "bgm.wav"),
        "-filter_complex",
        f"[0:v]ass='{ass}'[v];"
        # BGMはナレーションより約20dB小さく、ナレーション中はさらに下げる
        "[1:a]aformat=channel_layouts=stereo,asplit[n1][n2];"
        f"[2:a]volume={bgm_gain}[b];"
        "[b][n1]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[bd];"
        "[n2][bd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
        "-map", "[v]", "-map", "[a]", "-shortest",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
