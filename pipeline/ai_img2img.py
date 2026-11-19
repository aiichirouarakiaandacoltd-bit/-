"""SD-Turbo(CPU)の img2img で、下絵(参考動画から復元した素材)を描き直す。
構図・人体の形は下絵に従うため、生成AI特有の崩れ(手足・重複・浮遊物)が出にくい。"""
from __future__ import annotations

import cv2
import numpy as np

_PIPE = None


def pipe():
    global _PIPE
    if _PIPE is None:
        import torch
        from diffusers import AutoPipelineForImage2Image
        torch.set_num_threads(4)
        _PIPE = AutoPipelineForImage2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
        _PIPE.set_progress_bar_config(disable=True)
    return _PIPE


def regenerate(bgr: np.ndarray, prompt: str, strength: float = 0.35, steps: int = 4, width: int = 576, seed: int = 0) -> np.ndarray:
    import torch
    from PIL import Image
    h, w = bgr.shape[:2]
    W = width
    H = int(round(h * W / w / 8)) * 8
    img = Image.fromarray(cv2.cvtColor(cv2.resize(bgr, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))
    g = torch.Generator().manual_seed(seed)
    out = pipe()(prompt=prompt, image=img, strength=strength, num_inference_steps=steps, guidance_scale=0.0, generator=g).images[0]
    res = cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)
    res = cv2.resize(res, (w, h), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(res, (0, 0), 1.4)
    return cv2.addWeighted(res, 1.5, blur, -0.5, 0)  # 拡大分の甘さを補う軽いシャープ
