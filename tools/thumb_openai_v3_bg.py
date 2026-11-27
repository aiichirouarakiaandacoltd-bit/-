import sys, base64, requests, concurrent.futures as cf, time
import os; O=os.environ.get("THUMB_AI_OUT","work/v3/")
NO=" No people, no faces, no human figures, no buildings, no flowers, no chrysanthemum, no crests or emblems, no red, no logos."
BG=" Absolutely no text or letters."
TX=" Fully transparent background, only the typography and its own effects (shadow, glow, plaque). Every Japanese character must be exactly as given, complete and crisp. No other text."
J={
"bgA":("gpt-image-2","1280x720","opaque","Premium YouTube thumbnail background, deep navy blue with luxurious textured real gold-leaf (kinpaku) brush strokes sweeping in from the bottom-left and top-right corners, a thin elegant gold art-deco double-line frame around the edges with small geometric corner ornaments, two warm soft golden glows (backlight) on the left third and right third, the center slightly darker and calm, fine gold dust, cinematic."+BG+NO),
"bgB":("gpt-image-2","1280x720","opaque","Premium YouTube thumbnail background, deep midnight navy, rich textured real gold-leaf brush strokes on the far left edge and top-left, a few elegant flowing thin gold lines across the lower left, a big warm golden halo of backlight on the right half, fine gold bokeh and dust, cinematic depth, calm and dignified."+BG+NO),
"bgS":("gpt-image-2","1088x1920","opaque","Premium vertical smartphone cover background, deep navy blue with luxurious textured gold-leaf brush strokes at the top-left and bottom-right corners, a thin elegant gold art-deco double-line frame along the edges with small geometric corner ornaments, a warm soft golden glow behind the lower-middle area, fine gold dust, cinematic."+BG+NO),
"tA":("gpt-image-1.5","1024x1024","transparent","A centered, stacked Japanese title lockup for a premium documentary thumbnail, elegant bold Mincho serif. Line 1 (small, white, wide letter spacing): 雅子さま 63歳のお誕生日 . Line 2: a refined slim horizontal plaque with thin gold double border and deep navy fill, containing white text: 「あと20年で100年もの月日が」 . Line 3 (very large, 3D polished metallic gold beveled with soft warm glow and dark drop shadow): 戦後80年 . A small gold art-deco ornament divider above line 3."+TX),
"tB":("gpt-image-1.5","1024x1536","transparent","A left-aligned stacked Japanese title lockup for a premium documentary thumbnail, bold Mincho serif. Line 1 (large, white with subtle dark shadow): 雅子さま . Line 2 (enormous, 3D polished metallic gold beveled with warm glow and dark drop shadow): 63歳 . A thin gold horizontal rule. Line 3 (white): 戦後80年に . Line 4 (white): 心に刻まれた願い…"+TX),
"tS2":("gpt-image-1.5","1536x1024","transparent","A single line of Japanese text, bold elegant Mincho serif, white with a thin gold outline and dark soft drop shadow, centered: その先に願われたこととは…"+TX),
"tCtop":("gpt-image-1.5","1536x1024","transparent","A single line of Japanese text for a punchy YouTube thumbnail, extra-bold rounded Japanese gothic, bright yellow fill with a very thick black outline and drop shadow, centered, as wide as possible: 「あと20年で100年もの月日が」"+TX),
"tCbot":("gpt-image-1.5","1536x1024","transparent","Two stacked centered lines for a punchy YouTube thumbnail, extra-bold Japanese gothic. Line 1: light cyan fill with a very thick dark navy outline: 雅子さま 戦後80年のご感想 . Line 2: white extra-bold text on a glossy hot-pink (#EC4891) rounded pill-shaped band with subtle highlight: その先に願われたこととは…"+TX),
}
def run(n):
    m,size,bg,p=J[n]
    for t in range(3):
        b={"model":m,"prompt":p,"size":size,"quality":"high","n":1}
        if bg=="transparent": b["background"]="transparent"
        r=requests.post("https://api.openai.com/v1/images/generations",json=b,headers={"Authorization":"Bearer dummy"},timeout=900)
        if r.status_code==200:
            open(O+n+".png","wb").write(base64.b64decode(r.json()["data"][0]["b64_json"])); return n,"ok"
        err=r.text[:160]; time.sleep(3)
    return n,"ERR "+err
names=sys.argv[1:] or list(J)
with cf.ThreadPoolExecutor(8) as ex:
    for n,s in ex.map(run,names): print(n,s,flush=True)
