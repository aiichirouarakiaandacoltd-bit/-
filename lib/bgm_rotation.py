"""BGM6曲循環管理"""
import json
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BGM_TRACKS = [
    os.path.join(BASE_DIR, "inputs", "bgm", "bgm_01.mp3"),
    os.path.join(BASE_DIR, "inputs", "bgm", "bgm_02.mp3"),
    os.path.join(BASE_DIR, "inputs", "bgm", "bgm_03.mp3"),
    os.path.join(BASE_DIR, "inputs", "bgm", "bgm_04.mp3"),
    os.path.join(BASE_DIR, "inputs", "bgm", "bgm_05.mp3"),
    os.path.join(BASE_DIR, "inputs", "bgm", "bgm_06.mp3"),
]

STATE_PATH = os.path.join(BASE_DIR, "state", "bgm_rotation_state.json")


def _default_state():
    return {
        "rotation_version": 1,
        "last_completed_production_sequence": 0,
        "next_bgm_index": 0,
        "last_used_bgm": None,
        "updated_at": None,
        "completed_job_ids": [],
    }


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_state()


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_next_bgm(mode="production"):
    """次に使用するBGMパスとインデックスを返す。テストモードではNoneを返す。"""
    if mode == "test":
        return None, -1
    state = load_state()
    idx = state["next_bgm_index"] % len(BGM_TRACKS)
    path = BGM_TRACKS[idx]
    return path, idx


def validate_bgm_file(path):
    """BGMファイルの存在・0KB・読み込み可能・音声ストリームを検証"""
    if not path or not os.path.exists(path):
        return False, "ファイルが存在しません"
    if os.path.getsize(path) == 0:
        return False, "0KBファイルです"
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "stream=codec_type",
             "-of", "json", path],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(r.stdout)
        streams = data.get("streams", [])
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        if not has_audio:
            return False, "音声ストリームがありません"
        return True, "OK"
    except Exception as e:
        return False, f"ffprobe検証失敗: {e}"


def validate_all_bgm():
    """全6曲を検証し、結果を返す"""
    results = []
    for i, path in enumerate(BGM_TRACKS):
        ok, detail = validate_bgm_file(path)
        results.append({
            "index": i,
            "path": path,
            "name": os.path.basename(path),
            "valid": ok,
            "detail": detail,
        })
    return results


def mark_completed(job_id, bgm_index, bgm_path, timestamp=None):
    """本番動画が正常完成した場合のみ、BGM順を進める。重複防止あり。"""
    state = load_state()
    if job_id in state.get("completed_job_ids", []):
        return False
    state["last_completed_production_sequence"] += 1
    state["next_bgm_index"] = (bgm_index + 1) % len(BGM_TRACKS)
    state["last_used_bgm"] = os.path.basename(bgm_path)
    state["updated_at"] = timestamp
    state["completed_job_ids"].append(job_id)
    save_state(state)
    return True


def is_production_bgm(path):
    """パスが本番BGM6曲のいずれかであるか"""
    if not path:
        return False
    abs_path = os.path.abspath(path)
    return abs_path in [os.path.abspath(t) for t in BGM_TRACKS]
