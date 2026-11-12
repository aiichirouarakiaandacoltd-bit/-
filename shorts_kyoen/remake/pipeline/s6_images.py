"""工程⑥ 画像収集（自作素材の生成）
上下の帯に使う背景グラデーション（金・ピンク）、冒頭の赤丸と矢印、
BGM（自作の静かなパッド音）を作る。外部素材は使わない。
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.io import wavfile

from common import BUILD, load_script


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(w, h, top, bottom):
    a, b = np.array(hex2rgb(top), float), np.array(hex2rgb(bottom), float)
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(-1, 1, w)[None, :]
    # 縦グラデーション＋中央をやや明るくして、光が差すような質感にする
    glow = np.clip(1 - (x ** 2) * 0.6, 0, 1)[..., None] * 0.12
    img = a[None, None, :] * (1 - y[..., None]) + b[None, None, :] * y[..., None]
    img = img + 255 * glow * (1 - img / 255)
    noise = np.random.default_rng(1).normal(0, 1.2, img.shape)
    return Image.fromarray(np.clip(img + noise, 0, 255).astype(np.uint8))


def circle_arrow(w, h, sx):
    """冒頭の赤丸と矢印（元動画の位置を、406×720基準の座標で指定）。"""
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = sx * 2
    red = (232, 32, 42, 255)
    cx, cy, rx, ry = 178 * s, 283 * s, 122 * s, 95 * s
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=red, width=int(5 * s))
    # 矢印（右上から丸へ向かう）
    x0, y0, x1, y1 = 318 * s, 118 * s, 272 * s, 192 * s
    d.line([x0, y0, x1, y1], fill=red, width=int(6 * s))
    ang = math.atan2(y1 - y0, x1 - x0)
    L = 26 * s
    for da in (math.radians(150), math.radians(-150)):
        d.line([x1, y1, x1 + L * math.cos(ang + da), y1 + L * math.sin(ang + da)], fill=red, width=int(6 * s))
    return im.resize((w, h), Image.LANCZOS)


def bgm(total, sr=48000):
    """静かなパッド（Cmaj7→Am7→Fmaj7→G6、各4秒）。著作権の問題がない自作音源。"""
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0],
              [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 329.6]]
    n = int(total * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    seg = 4.0
    for i in range(int(math.ceil(total / seg)) + 1):
        ch = chords[i % 4]
        t0 = i * seg
        env = np.clip((t - t0 + 0.8) / 1.6, 0, 1) * np.clip((t0 + seg + 0.8 - t) / 1.6, 0, 1)
        for f in ch:
            out += env * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)) / 4
    out *= 0.25 * np.clip(t / 1.0, 0, 1) * np.clip((total - t) / 1.5, 0, 1)
    wavfile.write(BUILD / "bgm.wav", sr, np.stack([out, out], 1).astype(np.float32))


def main():
    sc = load_script()
    m = sc["meta"]
    W, H = m["width"], m["height"]
    (BUILD / "img").mkdir(parents=True, exist_ok=True)
    for name, g in m["backgrounds"].items():
        gradient(W, H, g["top"], g["bottom"]).filter(ImageFilter.GaussianBlur(1)).save(BUILD / "img" / f"bg_{name}.png")
    circle_arrow(W, H, W / m["source_size"][0]).save(BUILD / "img" / "circle_arrow.png")
    mk = m.get("source_subtitle_mask")
    if mk:
        # 焼き込み字幕を消すぼかし帯の不透明度マスク（上下の境目をなめらかにする）
        h, fe = mk["y1"] - mk["y0"], mk.get("feather", 0)
        a = np.ones(h)
        if fe:
            ramp = np.linspace(0, 1, fe)
            a[:fe], a[-fe:] = ramp, ramp[::-1]
        Image.fromarray((np.tile(a[:, None], (1, m["source_size"][0])) * 255).astype(np.uint8), "L").save(BUILD / "img" / "mask.png")
    bgm(m["tts"]["target_total_sec"] + 2)
    print("backgrounds, circle_arrow, bgm -> build/img, build/bgm.wav")


if __name__ == "__main__":
    main()
