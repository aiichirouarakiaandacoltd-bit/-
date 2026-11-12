"""工程⑧ 動画編集
カット動画をつなぎ、字幕を焼き込み、ナレーションとBGMを合わせて完成版を書き出す。
"""
import subprocess

from common import BUILD, OUTPUT, load_script


def main():
    sc = load_script()
    OUTPUT.mkdir(exist_ok=True)
    lst = BUILD / "clips.txt"
    lst.write_text("".join(f"file 'clips/cut_{c['id']:02d}.mp4'\n" for c in sc["cuts"]), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(BUILD / "video_nosub.mp4")], check=True)

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
        "[2:a]volume=-26dB[b];[b][n1]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[bd];"
        "[n2][bd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
        "-map", "[v]", "-map", "[a]", "-shortest",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
