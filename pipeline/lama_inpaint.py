"""LaMa(消した部分を周囲から自然に補完するAI, ONNX/CPU)で穴を埋める。
モデル: Carve/LaMa-ONNX (lama_fp32.onnx, 入力512x512)。"""
from __future__ import annotations

import cv2
import numpy as np

_SESS = None


def session():
    global _SESS
    if _SESS is None:
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        path = hf_hub_download("Carve/LaMa-ONNX", "lama_fp32.onnx")
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        _SESS = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
    return _SESS


def _run512(img_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    s = session()
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    x = rgb.transpose(2, 0, 1)[None]
    m = (mask > 127).astype(np.float32)[None, None]
    names = [i.name for i in s.get_inputs()]
    out = s.run(None, {names[0]: x, names[1]: m})[0][0]
    out = out.transpose(1, 2, 0)
    if out.max() <= 1.5:
        out = out * 255
    return cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)


def inpaint(img: np.ndarray, holes: np.ndarray, pad: int = 64) -> np.ndarray:
    """穴(holes>0)を含む領域ごとに正方形で切り出し、512に縮小してLaMaで補完し、穴の部分だけ戻す。"""
    out = img.copy()
    h, w = holes.shape
    n, lab, stats, _ = cv2.connectedComponentsWithStats((holes > 0).astype(np.uint8))
    boxes = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 30:
            continue
        boxes.append([x, y, x + bw, y + bh])
    # 近い箱はまとめる
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] - pad < b[2] and b[0] - pad < a[2] and a[1] - pad < b[3] and b[1] - pad < a[3]:
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    boxes.pop(j)
                    merged = True
                    break
            if merged:
                break
    for x0, y0, x1, y1 in boxes:
        side = max(x1 - x0, y1 - y0) + 2 * pad
        side = min(side, max(h, w))
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        X0 = int(min(max(cx - side // 2, 0), max(0, w - side)))
        Y0 = int(min(max(cy - side // 2, 0), max(0, h - side)))
        X1, Y1 = min(w, X0 + side), min(h, Y0 + side)
        crop = out[Y0:Y1, X0:X1]
        mc = holes[Y0:Y1, X0:X1]
        cs = cv2.resize(crop, (512, 512), interpolation=cv2.INTER_AREA)
        ms = cv2.resize(mc, (512, 512), interpolation=cv2.INTER_NEAREST)
        ms = cv2.dilate(ms, np.ones((5, 5), np.uint8))
        res = cv2.resize(_run512(cs, ms), (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_CUBIC)
        k = cv2.GaussianBlur(cv2.dilate(mc, np.ones((9, 9), np.uint8)).astype(np.float32) / 255, (0, 0), 3)[..., None]
        out[Y0:Y1, X0:X1] = (res * k + crop * (1 - k)).astype(np.uint8)
    return out
