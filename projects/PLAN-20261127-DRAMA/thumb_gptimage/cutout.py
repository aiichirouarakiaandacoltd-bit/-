# 切り抜き: Canvaの背景除去(小さい見本)を元写真の輪郭に合わせて拡大する(カラーガイデッドフィルタ)。
# 顔や体の画素は一切変えない。透明度(どこを残すか)だけを計算する。
import numpy as np, sys
from PIL import Image, ImageFilter
ROOT = "/home/user/-/assets/KB-20261124-01/"
def box(x, r):
    c = np.cumsum(np.cumsum(np.pad(x, ((r+1, r), (r+1, r)), mode="edge"), 0), 1)
    return (c[2*r+1:, 2*r+1:] - c[:-2*r-1, 2*r+1:] - c[2*r+1:, :-2*r-1] + c[:-2*r-1, :-2*r-1]) / (2*r+1)**2
def gf_color(I, p, r, eps):
    mI = [box(I[..., k], r) for k in range(3)]; mp = box(p, r)
    cov = [box(I[..., k]*p, r) - mI[k]*mp for k in range(3)]
    S = np.empty(p.shape + (3, 3))
    for i in range(3):
        for j in range(3):
            S[..., i, j] = box(I[..., i]*I[..., j], r) - mI[i]*mI[j] + (eps if i == j else 0)
    a = np.linalg.solve(S, np.stack(cov, -1)[..., None])[..., 0]
    b = mp - sum(a[..., k]*mI[k] for k in range(3))
    ma = [box(a[..., k], r) for k in range(3)]; mb = box(b, r)
    return sum(ma[k]*I[..., k] for k in range(3)) + mb
def cut(name):
    im = Image.open(ROOT + name + ".jpg").convert("RGB")
    m = Image.open(f"src_mask/{name}_canva_mask.png").split()[-1].resize(im.size, Image.BICUBIC)
    I = np.asarray(im, np.float64) / 255; p = np.asarray(m, np.float64) / 255
    a = gf_color(I, p, max(4, im.width // 120), 2e-4)
    a = np.clip((a - 0.25) / 0.5, 0, 1)
    al = Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.copy(); out.putalpha(al); out.save(f"cut/{name}_cut.png"); return out
for n in sys.argv[1:]:
    o = cut(n); bg = Image.new("RGB", o.size, (20, 40, 90)); bg.paste(o, (0, 0), o); bg.save(f"/tmp/claude-0/-home-user--/805ab223-7c39-5a4d-ab05-a74a1e8125b5/scratchpad/prev_{n}.jpg")
