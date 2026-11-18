"""VOICEVOX CORE(Python版)を直接使う音声合成。エンジンのサーバー起動不要。

配置: /home/user/voicevox/{15.vvm, ort/...}(青山龍星は 15.vvm, style_id=13)
クレジット表記: 「VOICEVOX:青山龍星」
"""
from __future__ import annotations

import io
import os
import wave

import numpy as np

VV_DIR = os.environ.get("VOICEVOX_DIR", "/home/user/voicevox")
ORT = f"{VV_DIR}/ort/voicevox_onnxruntime-linux-x64-1.17.3/lib/libvoicevox_onnxruntime.so"
VVM = f"{VV_DIR}/15.vvm"
STYLE_AOYAMA_NORMAL = 13
_SYN = None


def synthesizer():
    global _SYN
    if _SYN is None:
        import pyopenjtalk
        from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
        ort = Onnxruntime.load_once(filename=ORT)
        dic = os.path.join(os.path.dirname(pyopenjtalk.__file__), "dictionary")
        _SYN = Synthesizer(ort, OpenJtalk(dic))
        with VoiceModelFile.open(VVM) as m:
            _SYN.load_voice_model(m)
    return _SYN


def synth(text: str, style: int = STYLE_AOYAMA_NORMAL, speed: float = 1.0, sr: int = 24000,
          pre: float = 0.0, post: float = 0.0, pitch: float = 0.0, intonation: float = 1.0) -> np.ndarray:
    syn = synthesizer()
    q = syn.create_audio_query(text, style)
    q.speed_scale = speed
    q.pitch_scale = pitch
    q.intonation_scale = intonation
    q.pre_phoneme_length = pre
    q.post_phoneme_length = post
    q.output_sampling_rate = sr
    q.output_stereo = False
    wav = syn.synthesis(q, style)
    with wave.open(io.BytesIO(wav)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
