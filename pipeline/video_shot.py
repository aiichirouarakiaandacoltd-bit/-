"""動きのあるカット(人物が動く映像)を1コマずつ再現する。
各コマの字幕部分を、①近いコマの同じ場所(位置合わせ済み) ②直前に仕上げたコマ ③LaMa の順で埋める。
静止画+カメラワークでは動きが止まってしまうカット用。"""
from __future__ import annotations

import cv2
import numpy as np

from .rebuild_reference import estimate_motion, _sane
from .trace_reference import full_mask


def _warp(img, M, size, interp=cv2.INTER_LINEAR):
    return cv2.warpAffine(img, M, size, flags=interp, borderMode=cv2.BORDER_CONSTANT)


def rebuild_frames(frames, ass_masks, t0, fps, search=30, log=None):
    """frames: 参考動画のコマ列。ass_masks: [(start,end,mask)]。戻り値: 字幕を消したコマ列。"""
    from .lama_inpaint import inpaint as lama
    n = len(frames)
    h, w = frames[0].shape[:2]
    masks = []
    for j, f in enumerate(frames):
        t = t0 + j / fps
        m = full_mask(f)
        for (cs, ce, am) in ass_masks:
            if cs - 0.1 <= t < ce + 0.1:
                m = m | am
                if t - cs < 0.7:  # 滑り込み中・拡大中の字幕の位置(左側・外側)も覆う
                    for dx in range(60, 481, 60):
                        sh = np.zeros_like(am)
                        sh[:, :-dx] = am[:, dx:]
                        m = m | sh
                    m = m | cv2.dilate(am, np.ones((61, 61), np.uint8))
        masks.append(cv2.dilate(m, np.ones((27, 27), np.uint8)))
    out = []
    prev = None
    for j in range(n):
        f = frames[j].copy()
        hole = masks[j] > 0
        if hole.any():
            order = sorted([k for k in range(max(0, j - search), min(n, j + search + 1)) if k != j], key=lambda k: abs(k - j))
            for k in order:
                if not hole.any():
                    break
                cand = (~(masks[k] > 0)).astype(np.uint8) * 255
                # 埋める先に字幕が無いコマだけ使う
                if not ((cand > 0) & hole).any():
                    continue
                M = estimate_motion(frames[k], frames[j])
                if not _sane(M):
                    continue
                wk = _warp(frames[k], M, (w, h))
                wv = _warp(cand, M, (w, h), cv2.INTER_NEAREST) > 0
                take = hole & wv
                # 周辺(穴の外側の帯)で位置が合っているか確認(動く被写体の二重写しを防ぐ)
                ring = (cv2.dilate(take.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0) & ~hole & wv
                if ring.sum() > 200 and np.abs(wk.astype(np.float32) - f.astype(np.float32))[ring].mean() > 8:
                    continue
                f[take] = wk[take]
                hole &= ~take
            if hole.any():
                f = lama(f, hole.astype(np.uint8) * 255)
        out.append(f)
        prev = f
        if log and j % 30 == 0:
            log(f"    {j}/{n} コマ")
    return out
