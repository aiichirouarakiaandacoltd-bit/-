"""VOICEVOX Core（0.15）で台本を1文ずつ音声にする補助スクリプト。
VOICEVOX専用の仮想環境のPythonから呼び出す（システムのPythonとはライブラリが衝突するため）。
使い方: python voicevox_synth.py <jobs.json>
jobs.json: {"dict_dir":..., "speaker":13, "speed_scale":0.9, "items":[{"text":..., "out":...}, ...]}
"""
import json
import sys

from voicevox_core import VoicevoxCore


def main():
    job = json.loads(open(sys.argv[1], encoding="utf-8").read())
    core = VoicevoxCore(open_jtalk_dict_dir=job["dict_dir"])
    sp = job["speaker"]
    core.load_model(sp)
    for it in job["items"]:
        aq = core.audio_query(it["text"], sp)
        aq.speed_scale = job["speed_scale"]
        aq.pitch_scale = job.get("pitch_scale", 0.0)
        aq.intonation_scale = job.get("intonation_scale", 1.0)
        aq.volume_scale = job.get("volume_scale", 1.0)
        aq.pre_phoneme_length = 0.05
        aq.post_phoneme_length = 0.05
        with open(it["out"], "wb") as f:
            f.write(core.synthesis(aq, sp))
        print(it["out"], "".join(m.text for ap in aq.accent_phrases for m in ap.moras), flush=True)


if __name__ == "__main__":
    main()
