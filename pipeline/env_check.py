"""制作ルール 第0-2章「作業前チェック」。毎回、制作の最初に実行する。

① ツール(Python3 / ffmpeg / ffprobe / requests / Pillow / gdown)— 不足は pip / apt で導入
② VOICEVOX エンジン(localhost:50021)— 未起動なら起動、未導入なら公式 GitHub リリースから導入。
   話者IDは /speakers から「青山龍星」「ノーマル」を取得、speedScale 0.90 で試験音声を生成
③ BGM(Googleドライブ ID 1NI_d0oPaY1N1QrG1F9MeKY0T7S29Rh9N)— gdown → 失敗時は同じファイルを
   drive.usercontent.google.com から取得(drive.google.com がネットワーク許可外の環境のため)
④ フォント Noto Sans JP(Regular/Bold/Black)— 未導入なら google/fonts から取得し固定版を作って導入
結果: projects/<制作番号>/env_check.md。準備できない項目があれば終了コード1(制作停止)。
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VV_URL = "http://127.0.0.1:50021"
VV_DIR = Path("/home/user/voicevox")
VV_VERSION = "0.26.2"
BGM_ID = "1NI_d0oPaY1N1QrG1F9MeKY0T7S29Rh9N"
BGM_DIR = ROOT / "assets" / "bgm"
FONT_DIR = Path("/usr/local/share/fonts/noto-sans-jp")
SPEED = 0.90


def sh(cmd, timeout=600):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)


def check_tools(rep):
    ok = True
    for name, cmd in (("Python 3", f"{sys.executable} --version"), ("ffmpeg", "ffmpeg -version | head -1"),
                      ("ffprobe", "ffprobe -version | head -1")):
        r = sh(cmd)
        if r.returncode and name != "Python 3":
            sh("apt-get update -qq && apt-get install -y -qq ffmpeg", 1200)
            r = sh(cmd)
        rep.append(f"- {name}: {'OK' if not r.returncode else 'NG'} `{(r.stdout or r.stderr).strip()[:80]}`")
        ok &= not r.returncode
    for mod, pkg in (("requests", "requests"), ("PIL", "Pillow"), ("gdown", "gdown")):
        r = sh(f"{sys.executable} -c 'import {mod};print({mod}.__version__)'")
        if r.returncode:
            sh(f"{sys.executable} -m pip install -q {pkg}", 900)
            r = sh(f"{sys.executable} -c 'import {mod};print({mod}.__version__)'")
        rep.append(f"- {pkg}: {'OK ' + r.stdout.strip() if not r.returncode else 'NG'}")
        ok &= not r.returncode
    return ok


def _vv_up():
    import requests
    try:
        return requests.get(VV_URL + "/version", timeout=2).json()
    except Exception:
        return None


def ensure_voicevox() -> bool:
    """エンジンが止まっていれば起動し直す(書き出しの直前に呼ぶ)。"""
    if _vv_up():
        return True
    check_voicevox([], Path("/tmp"))
    return bool(_vv_up())


def check_voicevox(rep, out_dir: Path):
    import requests
    ver = _vv_up()
    if not ver:
        run = VV_DIR / "linux-cpu-x64" / "run"
        if not run.exists():
            dl = VV_DIR / "engine_dl"
            dl.mkdir(parents=True, exist_ok=True)
            f = dl / f"voicevox_engine-linux-cpu-x64-{VV_VERSION}.7z.001"
            sh(f"curl -sL -o {f} https://github.com/VOICEVOX/voicevox_engine/releases/download/{VV_VERSION}/{f.name}", 3600)
            if not shutil.which("7z"):
                sh("apt-get update -qq && apt-get install -y -qq p7zip-full", 1200)
            sh(f"cd {VV_DIR} && 7z x -y {f} >/dev/null && rm -f {f}", 3600)
        if run.exists():
            # setsid で呼び出し元の終了から切り離す(作業の合間にエンジンが止まるのを防ぐ)
            subprocess.Popen(f"chmod +x {run} && setsid nohup {run} --host 127.0.0.1 --port 50021 > {VV_DIR}/engine.log 2>&1 < /dev/null &",
                             shell=True, start_new_session=True)
            for _ in range(60):
                time.sleep(3)
                ver = _vv_up()
                if ver:
                    break
    if not ver:
        rep.append("- VOICEVOX: **NG** 起動できない(公式配布元からの取得または起動に失敗)")
        return None
    sp = requests.get(VV_URL + "/speakers", timeout=10).json()
    sid = next((s["id"] for p in sp if p["name"] == "青山龍星" for s in p["styles"] if s["name"] == "ノーマル"), None)
    if sid is None:
        rep.append("- VOICEVOX: **NG** 話者「青山龍星」ノーマルが見つからない")
        return None
    q = requests.post(VV_URL + "/audio_query", params={"text": "日本が誇る皇室物語。試験音声です。", "speaker": sid}, timeout=30).json()
    q["speedScale"] = SPEED
    w = requests.post(VV_URL + "/synthesis", params={"speaker": sid}, json=q, timeout=120).content
    test = out_dir / "voicevox_test.wav"
    test.write_bytes(w)
    with wave.open(io.BytesIO(w)) as f:
        dur = f.getnframes() / f.getframerate()
    r = sh(f"ffmpeg -i {test} -af volumedetect -f null - 2>&1 | grep max_volume")
    rep.append(f"- VOICEVOX: OK エンジン {ver} / 青山龍星ノーマル id={sid} / speedScale {SPEED} / 試験音声 {dur:.2f}秒 "
               f"({r.stdout.strip().split(']')[-1].strip()})")
    return sid


def check_bgm(rep):
    BGM_DIR.mkdir(parents=True, exist_ok=True)
    have = [p for p in BGM_DIR.glob("*") if p.suffix.lower() in (".wav", ".mp3", ".m4a")]
    how = "既存ファイルを使用(再取得しない)"
    if not have:
        r = sh(f"cd {BGM_DIR} && {sys.executable} -m gdown {BGM_ID}", 600)
        have = [p for p in BGM_DIR.glob("*") if p.suffix.lower() in (".wav", ".mp3", ".m4a")]
        how = "gdown で取得"
        if not have:
            tmp = BGM_DIR / "download.bin"
            url = f"https://drive.usercontent.google.com/download?id={BGM_ID}&export=download&confirm=t"
            hdr = sh(f"curl -sSL -D - -o {tmp} '{url}'", 600).stdout
            name = "UNL1337.wav"
            for line in hdr.splitlines():
                if "filename=" in line.lower():
                    name = line.split("filename=")[-1].strip().strip('"')
            if tmp.exists() and tmp.stat().st_size > 100000:
                tmp.rename(BGM_DIR / name)
                have = [BGM_DIR / name]
                how = "gdown は drive.google.com がネットワーク許可外のため失敗 → 同じファイルを drive.usercontent.google.com から取得"
            else:
                tmp.unlink(missing_ok=True)
    if not have:
        rep.append("- BGM: **NG** 取得できない。Googleドライブの共有設定が「リンクを知っている全員」か確認が必要")
        return None
    f = have[0]
    r = sh(f"ffprobe -v error -show_entries format=duration,format_name -of compact=p=0 '{f}'")
    rep.append(f"- BGM: OK `{f.relative_to(ROOT)}` {how} / {r.stdout.strip()}")
    return f


def check_font(rep):
    def present():
        r = sh("fc-list | grep -i 'Noto Sans JP'")
        return "style=Bold" in r.stdout
    if not present():
        tmp = Path("/home/user/gfonts")
        if not (tmp / "ofl/notosansjp").exists():
            sh(f"rm -rf {tmp} && GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 --filter=blob:none --sparse "
               f"https://github.com/google/fonts {tmp} && cd {tmp} && git sparse-checkout set ofl/notosansjp", 1200)
        sh(f"{sys.executable} -m pip install -q fonttools", 600)
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        var = tmp / "ofl/notosansjp/NotoSansJP[wght].ttf"
        for w, s in ((400, "Regular"), (700, "Bold"), (900, "Black")):
            sh(f"{sys.executable} -m fontTools.varLib.instancer '{var}' wght={w} --update-name-table "
               f"-o {FONT_DIR}/NotoSansJP-{s}.ttf -q", 600)
        sh("fc-cache -f")
    ok = present()
    files = sorted(str(p) for p in FONT_DIR.glob("NotoSansJP-*.ttf"))
    rep.append(f"- フォント Noto Sans JP: {'OK' if ok else '**NG**'} {', '.join(Path(f).name for f in files)}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="制作番号")
    a = ap.parse_args()
    out = ROOT / "projects" / a.project
    out.mkdir(parents=True, exist_ok=True)
    rep = [f"# env_check — {a.project}", "", f"実行: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    rep.append("## ① ツール")
    t = check_tools(rep)
    rep += ["", "## ② VOICEVOX"]
    sid = check_voicevox(rep, out)
    rep += ["", "## ③ BGM"]
    bgm = check_bgm(rep)
    rep += ["", "## ④ フォント"]
    f = check_font(rep)
    ok = bool(t and sid is not None and bgm and f)
    rep += ["", f"## 判定: {'合格(制作を開始できる)' if ok else '不合格(制作を停止。上記NGの対応が必要)'}"]
    (out / "env_check.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    json.dump({"ok": ok, "speaker_id": sid, "bgm": str(bgm.relative_to(ROOT)) if bgm else None},
              open(out / "env_check.json", "w"), ensure_ascii=False)
    print("\n".join(rep))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
