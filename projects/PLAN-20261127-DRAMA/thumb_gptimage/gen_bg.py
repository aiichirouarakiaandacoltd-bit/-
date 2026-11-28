# ChatGPT(gpt-image)で背景・額縁・金の飾り・光だけを作る。人物・実在の建物・紋章は描かせない。
import base64, json, os, sys, urllib.request, concurrent.futures as cf
COMMON = (" Absolutely no people, no faces, no human figures, no buildings, no palace, no architecture, "
          "no chrysanthemum crest, no emblems, no logos, no text, no letters, no red color. "
          "Professional luxury graphic design background, ultra clean, high detail, 8k.")
JOBS = {
 "A1_frame_navy": ("1920x1088",
   "Elegant deep navy blue (#0E1A33) background with a refined ornate gold filigree frame border around the edges, "
   "subtle traditional Japanese seigaiha wave pattern embossed faintly in the navy, soft warm golden light glow in the center, "
   "fine gold dust particles, the center area is mostly empty and dark for placing photos and text. Symmetrical, regal, formal."),
 "A2_goldscreen": ("1920x1088",
   "Luxurious background: midnight navy blue gradient, with flowing stylized gold leaf clouds (kasumi mist bands) in the style of a "
   "Japanese gold folding screen at the top and bottom edges, gentle diagonal rays of soft golden light from the upper center, "
   "glittering gold particles, large calm empty navy space in the middle. Sophisticated, celebratory, dignified."),
 "B_light": ("1920x1088",
   "Abstract soft bokeh light overlay on dark charcoal navy background: warm golden and soft white bokeh circles and gentle light leaks "
   "concentrated near the top and bottom edges, very subtle, cinematic, the middle is darker. Minimal and stylish."),
 "S_frame_portrait": ("1088x1920",
   "Vertical elegant deep navy blue background with an ornate thin gold filigree frame border along the edges, "
   "faint traditional Japanese seigaiha wave pattern, flowing gold leaf kasumi mist bands near the bottom, soft golden light glow "
   "from the upper center, fine gold sparkles, large empty dark area in the middle. Regal, celebratory, formal."),
}
def gen(name):
    size, p = JOBS[name]
    body = json.dumps({"model": "gpt-image-2", "prompt": p + COMMON, "size": size, "quality": "high", "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": "Bearer sk-dummy", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=600))
    open(f"bg/{name}.png", "wb").write(base64.b64decode(r["data"][0]["b64_json"]))
    return name
names = sys.argv[1:] or list(JOBS)
with cf.ThreadPoolExecutor(4) as ex:
    for f in cf.as_completed([ex.submit(gen, n) for n in names]):
        try: print("ok", f.result())
        except Exception as e: print("ERR", e, getattr(e, "read", lambda: b"")()[:400])
