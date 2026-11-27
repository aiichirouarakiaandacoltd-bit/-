"""表紙用のAI素材(背景・額縁・金の札・光)を gpt-image で作る。人物は作らない。
鍵は環境の Network secrets(api.openai.com)から自動で付く。ここの Bearer dummy は差し替え用の仮の値。"""
import sys, json, base64, requests, concurrent.futures as cf
import os; OUT=os.environ.get("THUMB_AI_OUT","work/ai/")
COMMON=(" Absolutely no text, no letters, no logos, no people, no faces, no flowers, no chrysanthemum,"
        " no crests or emblems, no buildings, no red color. Premium editorial design, photorealistic metallic gold, high detail.")
JOBS={
 "bg_A":("1920x1088","opaque","A luxurious deep navy blue (#16243A) background for a YouTube thumbnail. An elegant ornate gold frame border runs around all four edges, with refined thin double gold lines and delicate geometric Japanese-inspired corner ornaments (asanoha / seigaiha line patterns). Soft warm golden light glows from the top center, with faint light rays and tiny floating gold particles. The interior is mostly clean, dark navy with a subtle silk texture, leaving large empty areas on the left, right and center."+COMMON),
 "bg_B":("1920x1088","opaque","A cinematic deep navy and midnight blue background for a YouTube thumbnail. A large soft golden halo of light glows on the right half, like warm backlight, with elegant gold bokeh and fine floating gold dust. On the left side, a few thin flowing gold ribbon lines and a subtle seigaiha wave pattern in faint gold. Rich, dignified, calm atmosphere, plenty of empty dark space on the left."+COMMON),
 "bg_S":("1088x1920","opaque","A vertical luxurious deep navy blue (#16243A) background for a smartphone cover. Ornate gold frame along the edges with refined thin double gold lines and delicate geometric Japanese-inspired corner ornaments. A soft warm golden glow of light from the upper middle with gentle light rays and floating gold particles. Lower third slightly darker. Large clean empty areas."+COMMON),
 "plaque":("1536x1024","transparent","A single wide horizontal ornate gold plaque / cartouche, polished metallic gold with beveled edges and subtle engraved fine line border, slightly rounded ends, centered, the inside of the plaque is a smooth flat deep navy panel. Isolated on a fully transparent background."+COMMON),
}
def run(name):
    size,bg,prompt=JOBS[name]
    body={"model":("gpt-image-1.5" if bg=="transparent" else "gpt-image-2"),"prompt":prompt,"size":size,"quality":"high","n":1}
    if bg=="transparent": body["background"]="transparent"
    r=requests.post("https://api.openai.com/v1/images/generations",json=body,timeout=600,
        headers={"Authorization":"Bearer dummy"})
    if r.status_code!=200: return name, f"ERR {r.status_code} {r.text[:300]}"
    d=r.json()["data"][0]
    open(OUT+name+".png","wb").write(base64.b64decode(d["b64_json"]))
    return name,"ok"
names=sys.argv[1:] or list(JOBS)
with cf.ThreadPoolExecutor(4) as ex:
    for n,s in ex.map(run,names): print(n,s,flush=True)
