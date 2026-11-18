"""SD-Turbo(CPU)で一般的な場面の画像を生成する。実在人物の生成には使わない。"""
import sys, json, time
import torch
from diffusers import AutoPipelineForText2Image
jobs = json.load(open(sys.argv[1]))
out = sys.argv[2]
torch.set_num_threads(4)
pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
for j in jobs:
    for k in range(j.get("n", 1)):
        t = time.time()
        g = torch.Generator().manual_seed(j.get("seed", 0) + k)
        im = pipe(prompt=j["prompt"], negative_prompt=None, num_inference_steps=j.get("steps", 4), guidance_scale=0.0,
                  width=j.get("w", 576), height=j.get("h", 1024), generator=g).images[0]
        p = f"{out}/{j['name']}_{k}.png"; im.save(p); print(p, round(time.time() - t, 1), "s", flush=True)
