import json, sys
from PIL import Image, ImageDraw, ImageFont
F=ImageFont.truetype("/home/user/-/templates/fonts/NotoSansJP-Bold.ttf",15)
def sheet(items, out, folder, tw=480, th=270, cols=4, vertical=False):
    if vertical: tw, th, cols = 270, 480, 6
    rows=(len(items)+cols-1)//cols; W=cols*(tw+8)+8; H=rows*(th+52)+8
    c=Image.new("RGB",(W,H),(30,30,30)); d=ImageDraw.Draw(c)
    for i,r in enumerate(items):
        x=8+(i%cols)*(tw+8); y=8+(i//cols)*(th+52)
        try:
            im=Image.open(f"{folder}/{r['id']}.jpg").convert("RGB")
            s=max(tw/im.width,th/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1)); l=(im.width-tw)//2; t=(im.height-th)//2
            c.paste(im.crop((l,t,l+tw,t+th)),(x,y))
        except Exception: pass
        d.text((x,y+th+3),f"#{i+1} {r['x']:.0f}倍 {r['v']/10000:.0f}万回 {r['channel'][:10]}",font=F,fill=(255,220,120))
        d.text((x,y+th+24),r['title'][:30 if not vertical else 16],font=F,fill=(230,230,230))
    c.save(out,quality=88)
if __name__=="__main__":
    P=json.load(open("long_pick.json"))
    sheet(P['good'][:12],"sheets/long_good_01-12.jpg","long_thumbs")
    sheet(P['good'][12:24],"sheets/long_good_13-24.jpg","long_thumbs")
    sheet(P['ng'],"sheets/long_ng.jpg","long_thumbs")
    sheet(P['low'],"sheets/long_low.jpg","long_thumbs")
