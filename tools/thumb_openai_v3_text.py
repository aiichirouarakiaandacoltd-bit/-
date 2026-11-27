import sys, base64, requests, concurrent.futures as cf, time
import os; O=os.environ.get("THUMB_AI_OUT","work/v3/")
FLAT=" The background must be a perfectly flat, solid, uniform navy color #16243A with no texture, no gradient, no vignette, no frame, no decoration other than the text. Every Japanese character exactly as given, complete, crisp, nothing cropped, comfortable margin around the text. No people, no other text, no logos, no red."
J={
"xA":("1248x1440","A centered, stacked Japanese title lockup for a premium documentary thumbnail, filling the width. Line 1 (small, white, elegant Mincho, wide letter spacing): 雅子さま 63歳のお誕生日 . Line 2: a refined slim horizontal plaque with thin polished gold double border and darker navy fill, containing white Mincho text: 「あと20年で100年もの月日が」 . Line 3 (very large, bold Mincho, 3D polished metallic gold beveled with warm soft glow and dark drop shadow): 戦後80年 . A tiny gold art-deco ornament between line 2 and line 3."+FLAT),
"xB":("1280x1440","A left-aligned stacked Japanese title lockup for a premium documentary thumbnail, bold Mincho serif, filling the space. Line 1 (large, white with subtle dark shadow): 雅子さま . Line 2 (enormous, 3D polished metallic gold beveled with warm glow and dark drop shadow): 63歳 . A thin gold horizontal rule. Line 3 (white, medium): 戦後80年に . Line 4 (pale gold, medium): 心に刻まれた願い…"+FLAT),
"xS":("1088x960","A centered, stacked Japanese title lockup for a premium vertical cover, filling the width. Line 1 (white, elegant bold Mincho, wide letter spacing): 雅子さま 63歳のお誕生日 . Line 2: a refined horizontal plaque with thin polished gold double border and darker navy fill, containing white Mincho text: 「あと20年で100年もの月日が」 . Line 3 (huge, bold Mincho, 3D polished metallic gold beveled with warm soft glow and dark drop shadow): 戦後80年 ."+FLAT),
"xS2":("1632x544","One centered line of Japanese text, bold elegant Mincho serif, white with a thin gold outline and soft dark drop shadow, large, filling the width: その先に願われたこととは…"+FLAT),
"xCtop":("1920x640","One centered line of Japanese text for a punchy YouTube thumbnail, extra-bold rounded Japanese gothic, bright yellow fill with a very thick black outline and drop shadow, filling the width. The text MUST begin with the Japanese opening corner bracket 「 and end with the closing corner bracket 」, exactly: 「あと20年で100年もの月日が」"+FLAT),
"xCbot":("1920x768","Two stacked centered lines for a punchy YouTube thumbnail, extra-bold Japanese gothic, filling the width. Line 1: light cyan fill with a very thick black outline: 雅子さま 戦後80年のご感想 . Line 2: white extra-bold text on a glossy hot-pink (#EC4891) rounded pill-shaped band: その先に願われたこととは…"+FLAT),
}
def run(n):
    size,p=J[n]
    for t in range(3):
        r=requests.post("https://api.openai.com/v1/images/generations",json={"model":"gpt-image-2","prompt":p,"size":size,"quality":"high","n":1},headers={"Authorization":"Bearer dummy"},timeout=900)
        if r.status_code==200:
            open(O+n+".png","wb").write(base64.b64decode(r.json()["data"][0]["b64_json"])); return n,"ok"
        err=r.text[:200]; time.sleep(3)
    return n,"ERR "+err
names=sys.argv[1:] or list(J)
with cf.ThreadPoolExecutor(6) as ex:
    for n,s in ex.map(run,names): print(n,s,flush=True)
