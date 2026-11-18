"""ステージ4: ナレーション音声合成。

エンジン優先順: VOICEVOX(青山龍星, 速度1.0) → Open JTalk(pyopenjtalk, 速度1.0) フォールバック。
文ごとに合成して実測長を計測し、timeline.json(シーン・文の開始/終了時刻)を出力する。
読み補正: config/reading_dict.json + 台本の readings。
"""
from __future__ import annotations

import io
import re
import wave

import numpy as np
import requests

from .common import ROOT, Job, get_logger, load_json, save_json, settings

SR = 48000


def split_sentences(text: str) -> list[str]:
    parts = re.findall(r"[^。！？!?]+[。！？!?]?", text)
    return [p.strip() for p in parts if p.strip()]


def apply_readings(text: str, extra: dict | None = None) -> str:
    d = {k: v for k, v in (load_json(ROOT / "config" / "reading_dict.json", {}) or {}).items() if not k.startswith("_")}
    d.update(extra or {})
    for k in sorted(d, key=len, reverse=True):
        text = text.replace(k, d[k])
    # 字幕用の記号は読み上げない
    return re.sub(r"[「」『』【】〈〉《》]", "", text)


def mora_count(text: str) -> int:
    import pyopenjtalk
    kana = pyopenjtalk.g2p(text, kana=True) if text.strip() else ""
    kana = re.sub(r"[ャュョァィゥェォ’、。？！\s]", "", kana)
    return max(1, len(kana))


# ---------------- エンジン ----------------
class VoiceVox:
    name = "voicevox"

    def __init__(self, cfg):
        self.url = cfg["voicevox_url"].rstrip("/")
        self.cfg = cfg
        r = requests.get(self.url + "/speakers", timeout=3)
        r.raise_for_status()
        self.speaker = cfg["voicevox_speaker_id_fallback"]
        for sp in r.json():
            if sp["name"] == cfg["voicevox_speaker_name"]:
                for stl in sp["styles"]:
                    if stl["name"] == cfg["voicevox_style_name"]:
                        self.speaker = stl["id"]
        self.label = f"VOICEVOX:{cfg['voicevox_speaker_name']}({cfg['voicevox_style_name']}, id={self.speaker})"

    def synth(self, text: str) -> np.ndarray:
        q = requests.post(self.url + "/audio_query", params={"text": text, "speaker": self.speaker}, timeout=30).json()
        q["speedScale"] = self.cfg["speed"]
        q["volumeScale"] = self.cfg["volume"]
        q["prePhonemeLength"] = 0.05
        q["postPhonemeLength"] = 0.05
        q["outputSamplingRate"] = SR
        q["outputStereo"] = False
        r = requests.post(self.url + "/synthesis", params={"speaker": self.speaker}, json=q, timeout=120)
        r.raise_for_status()
        with wave.open(io.BytesIO(r.content)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return x


class OpenJTalk:
    name = "openjtalk"

    def __init__(self, cfg):
        import pyopenjtalk  # noqa
        self.cfg = cfg
        self.label = "OpenJTalk(pyopenjtalk 既定男性音声, 速度1.0) ※VOICEVOX未起動のため代替"

    def synth(self, text: str) -> np.ndarray:
        import pyopenjtalk
        x, sr = pyopenjtalk.tts(text, speed=self.cfg["speed"])
        x = x.astype(np.float32) / 32768
        if sr != SR:
            idx = np.linspace(0, len(x) - 1, int(len(x) * SR / sr))
            x = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
        return x


def get_engine(log, prefer: str | None = None):
    cfg = settings()["tts"]
    order = [prefer] if prefer else cfg["engine_order"]
    for name in order:
        try:
            eng = {"voicevox": VoiceVox, "openjtalk": OpenJTalk}[name](cfg)
            log.info(f"音声エンジン: {eng.label}")
            return eng
        except Exception as e:
            log.warning(f"音声エンジン {name} 使用不可: {e}")
    raise RuntimeError("使用可能な音声合成エンジンがありません")


def trim(x: np.ndarray, thr_db=-42, pad=0.03) -> np.ndarray:
    if len(x) == 0:
        return x
    win = int(SR * 0.01)
    n = len(x) // win
    e = 20 * np.log10(np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(1)) + 1e-9)
    idx = np.where(e > thr_db)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] * win - int(pad * SR))
    b = min(len(x), (idx[-1] + 1) * win + int(pad * SR))
    return x[a:b]


def write_wav(path, x: np.ndarray, sr=SR):
    y = np.clip(x * 32767, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())


def synthesize(job: Job, script: dict, engine_name: str | None = None) -> dict:
    log = get_logger(job)
    cfg = settings()["tts"]
    eng = get_engine(log, engine_name)
    extra = script.get("readings", {})
    pause = cfg["sentence_pause_sec"]
    lead = 0.15
    pieces = [np.zeros(int(SR * lead), np.float32)]
    t = lead
    scenes = []
    for sc in script["scenes"]:
        s0 = t
        sents = []
        for sent in split_sentences(sc["narration"]):
            tts_text = apply_readings(sent, extra)
            x = trim(eng.synth(tts_text))
            peak = np.abs(x).max() or 1
            x = x / peak * 0.89
            start = t
            pieces.append(x)
            t += len(x) / SR
            sents.append({"text": sent, "tts_text": tts_text, "start": round(start, 3), "end": round(t, 3),
                          "morae": mora_count(tts_text)})
            pieces.append(np.zeros(int(SR * pause), np.float32))
            t += pause
        # シーン間は少し長めの間(参考動画: 文末で約0.25〜0.3秒)
        extra_gap = 0.08
        pieces.append(np.zeros(int(SR * extra_gap), np.float32))
        t += extra_gap
        scenes.append({"id": sc["id"], "role": sc.get("role"), "start": round(s0, 3), "end": round(t, 3), "sentences": sents})
    pieces.append(np.zeros(int(SR * 0.35), np.float32))
    audio = np.concatenate(pieces)
    write_wav(job.narration, audio)
    dur = len(audio) / SR
    tl = {"engine": eng.name, "engine_label": eng.label, "speed": cfg["speed"], "sample_rate": SR,
          "duration": round(dur, 3), "scenes": scenes}
    save_json(job.timeline, tl)
    chars = sum(len(s["text"]) for sc in scenes for s in sc["sentences"])
    log.info(f"ナレーション {dur:.2f}秒 / {chars}字 ({chars / dur:.2f}字/秒) → {job.narration}")
    job.mark("tts", True, duration=dur, engine=eng.name)
    return tl


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--engine")
    a = ap.parse_args()
    j = Job(a.job)
    synthesize(j, load_json(j.script), a.engine)
