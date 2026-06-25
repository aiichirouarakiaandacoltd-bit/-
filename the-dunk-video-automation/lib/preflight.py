import json
import os
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_settings():
    path = os.path.join(BASE_DIR, "config", "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_python():
    import sys
    return {"name": "Python", "ok": True, "detail": f"{sys.version}"}

def check_ffmpeg():
    path = shutil.which("ffmpeg")
    if path:
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            ver = r.stdout.split("\n")[0] if r.stdout else "unknown"
            return {"name": "FFmpeg", "ok": True, "detail": ver}
        except Exception as e:
            return {"name": "FFmpeg", "ok": False, "detail": str(e)}
    return {"name": "FFmpeg", "ok": False, "detail": "ffmpegが見つかりません。インストールしてください。"}

def check_ffprobe():
    path = shutil.which("ffprobe")
    if path:
        return {"name": "ffprobe", "ok": True, "detail": path}
    return {"name": "ffprobe", "ok": False, "detail": "ffprobeが見つかりません。FFmpegと一緒にインストールされます。"}

def check_japanese_font():
    try:
        r = subprocess.run(["fc-list", ":lang=ja"], capture_output=True, text=True, timeout=5)
        fonts = [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
        if fonts:
            return {"name": "日本語フォント", "ok": True, "detail": f"{len(fonts)}個のフォント検出"}
        return {"name": "日本語フォント", "ok": False, "detail": "日本語フォントが見つかりません。"}
    except Exception:
        return {"name": "日本語フォント", "ok": False, "detail": "fc-listコマンドが利用できません。"}

def check_voicevox(settings):
    host = settings["voicevox"]["host"]
    try:
        import urllib.request
        req = urllib.request.Request(f"{host}/version", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            version = resp.read().decode("utf-8").strip().strip('"')
            return {"name": "VOICEVOX", "ok": True, "detail": f"バージョン {version}"}
    except Exception:
        return {"name": "VOICEVOX", "ok": False, "detail": f"VOICEVOX ({host}) に接続できません。起動してください。"}

def check_voicevox_speaker(settings):
    host = settings["voicevox"]["host"]
    speaker_name = settings["voicevox"]["speaker_name"]
    style_name = settings["voicevox"]["style_name"]
    try:
        import urllib.request
        req = urllib.request.Request(f"{host}/speakers", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            speakers = json.loads(resp.read().decode("utf-8"))
        for sp in speakers:
            if sp["name"] == speaker_name:
                for st in sp["styles"]:
                    if st["name"] == style_name:
                        return {"name": "VOICEVOX話者", "ok": True, "detail": f"{speaker_name} ({style_name}) ID={st['id']}"}
                styles_available = [s["name"] for s in sp["styles"]]
                return {"name": "VOICEVOX話者", "ok": False, "detail": f"話者 {speaker_name} のスタイル {style_name} が見つかりません。利用可能: {styles_available}"}
        return {"name": "VOICEVOX話者", "ok": False, "detail": f"話者 {speaker_name} が見つかりません。"}
    except Exception:
        return {"name": "VOICEVOX話者", "ok": False, "detail": "VOICEVOX未接続のため話者を確認できません。"}

def check_output_writable():
    out = os.path.join(BASE_DIR, "output")
    os.makedirs(out, exist_ok=True)
    try:
        test_path = os.path.join(out, ".write_test")
        with open(test_path, "w") as f:
            f.write("test")
        os.remove(test_path)
        return {"name": "出力先書き込み権限", "ok": True, "detail": out}
    except Exception as e:
        return {"name": "出力先書き込み権限", "ok": False, "detail": str(e)}

def check_input_materials():
    owned = os.path.join(BASE_DIR, "inputs", "owned_videos")
    licensed = os.path.join(BASE_DIR, "inputs", "licensed_videos")
    owned_files = []
    licensed_files = []
    if os.path.isdir(owned):
        owned_files = [f for f in os.listdir(owned) if not f.startswith(".")]
    if os.path.isdir(licensed):
        licensed_files = [f for f in os.listdir(licensed) if not f.startswith(".")]
    total = len(owned_files) + len(licensed_files)
    if total > 0:
        return {"name": "入力素材", "ok": True, "detail": f"owned: {len(owned_files)}, licensed: {len(licensed_files)}"}
    return {"name": "入力素材", "ok": False, "detail": "素材がありません。inputs/owned_videos/ にファイルを配置してください。"}

def check_disk_space():
    import shutil as sh
    stat = sh.disk_usage(BASE_DIR)
    free_gb = stat.free / (1024**3)
    ok = free_gb > 1.0
    return {"name": "空き容量", "ok": ok, "detail": f"{free_gb:.1f} GB"}

def run_preflight(mode="production"):
    settings = load_settings()
    checks = [
        check_python(),
        check_ffmpeg(),
        check_ffprobe(),
        check_japanese_font(),
        check_output_writable(),
        check_disk_space(),
        check_input_materials(),
    ]
    if mode == "production":
        checks.append(check_voicevox(settings))
        checks.append(check_voicevox_speaker(settings))

    passed = [c for c in checks if c["ok"]]
    failed = [c for c in checks if not c["ok"]]
    return {"passed": passed, "failed": failed, "all_ok": len(failed) == 0}

def print_preflight(result):
    print("\n=== preflight チェック ===\n")
    print("PASS:")
    for c in result["passed"]:
        print(f"  ✓ {c['name']}: {c['detail']}")
    if result["failed"]:
        print("\nFAIL:")
        for c in result["failed"]:
            print(f"  ✗ {c['name']}: {c['detail']}")
    print(f"\n結果: {'ALL PASS' if result['all_ok'] else 'FAIL あり'}")
    return result["all_ok"]
