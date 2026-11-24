import sys,cv2,numpy as np
sys.path.insert(0,'/home/user/-')
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pipeline.rules_render import faces
FB=str(next(__import__('pathlib').Path('/usr/local/share/fonts').rglob('NotoSansJP-Bold.ttf')))
NAVY=(22,36,58);GOLD=(216,188,114);WHITE=(255,255,255);BAND=(12,22,38)
S='/tmp/claude-0/-home-user--/43a7a50c-dc00-57d9-956c-aa12a4cfeb48/scratchpad/sample/'
A='/home/user/-/assets/KB-20261123-06/'
def F(n): return ImageFont.truetype(FB,n)
def fit_text(d,txt,maxw,size):
    while d.textlength(txt,font=F(size))>maxw and size>30: size-=2
    return size
def ctext(d,y,txt,size,fill,stroke,maxw=1220):
    size=fit_text(d,txt,maxw,size); f=F(size); w=d.textlength(txt,font=f)
    d.text(((1280-w)/2,y),txt,font=f,fill=fill,stroke_width=stroke,stroke_fill=(0,0,0))
    return size
def face_crop(path,w,h,zoom=2.6):
    img=cv2.imread(path); ih,iw=img.shape[:2]; fs=faces(img)
    x,y,fw,fh=max(fs,key=lambda f:f[2]*f[3]); cx,cy=x+fw/2,y+fh/2
    ch=min(ih,fh*4.2); cw=ch*w/h
    if cw>iw: cw=iw; ch=cw*h/w
    l=min(max(cx-cw/2,0),iw-cw); t=min(max(cy-0.42*ch,0),ih-ch)
    c=img[int(t):int(t+ch),int(l):int(l+cw)]
    return Image.fromarray(cv2.cvtColor(cv2.resize(c,(w,h),interpolation=cv2.INTER_LANCZOS4),cv2.COLOR_BGR2RGB))
def cover(path,w,h,cx=0.5,cy=0.5):
    im=Image.open(path).convert('RGB'); iw,ih=im.size; s=max(w/iw,h/ih)
    im=im.resize((int(iw*s)+1,int(ih*s)+1),Image.LANCZOS); iw,ih=im.size
    l=min(max(int(cx*iw-w/2),0),iw-w); t=min(max(int(cy*ih-h/2),0),ih-h)
    return im.crop((l,t,l+w,t+h))
def make(out,quote,left,lcap,right,bottom1,bottom2):
    im=Image.new('RGB',(1280,720),NAVY); d=ImageDraw.Draw(im)
    d.text((22,10),'日本が誇る皇室物語',font=F(24),fill=GOLD)
    ctext(d,34,quote,88,WHITE,8,maxw=1230)
    # 中段 y150-520
    lw,lh=380,370; im.paste(left,(40,150)); d.rectangle((40,150,40+lw,150+lh),outline=GOLD,width=4)
    d.text((44,150+lh+4),lcap,font=F(16),fill=(225,225,225))
    # 金の矢印
    d.polygon([(440,300),(490,300),(490,280),(530,335),(490,390),(490,370),(440,370)],fill=GOLD)
    x=550; n=len(right); gap=12; rw=(1240-x-gap*(n-1))//n
    for k,(path,cap,cx,cy) in enumerate(right):
        ph=cover(path,rw,lh,cx,cy); im.paste(ph,(x,150)); d.rectangle((x,150,x+rw,150+lh),outline=GOLD,width=4)
        d.text((x+4,150+lh+4),cap,font=F(16),fill=(225,225,225)); x+=rw+gap
    d.rectangle((0,550,1280,720),fill=BAND); d.line((0,550,1280,550),fill=GOLD,width=4)
    ctext(d,556,bottom1,68,WHITE,6,maxw=1240)
    ctext(d,638,bottom2,58,GOLD,6,maxw=1240)
    im.save(out); print(out)
O='/home/user/-/samples/long_aiko_2countries/'
make(O+'thumb_A.png','「改めて深く感謝いたします」',face_crop(A+'A115.jpg',380,370),'愛子さま（令和7年12月1日公表）',
     [(S+'lao_601_3.jpeg','2025.11.18 ラオス 晩餐会のおことば',0.5,0.4),(S+'lao_600_1.jpeg','2025.11.18 ラオス バーシーセレモニー',0.5,0.4)],
     '2つの国で込められた感謝とは？','ラオスとシンガポールのおことばから')
make(O+'thumb_B.png','「東日本大震災などの大きな試練」',face_crop(A+'A116.jpg',380,370),'愛子さま（令和7年12月1日公表）',
     [(S+'lao_599_1.jpeg','2025.11.18 ラオス 国家主席表敬',0.45,0.4),(S+'lao_609_1.jpeg','2025.11.20 ラオス 午餐会のおことば',0.5,0.35)],
     '1年で2回、おことばに出てきた言葉','令和7年ラオス・令和8年シンガポール')
make(O+'thumb_C.png','「私の祖父母である上皇上皇后両陛下」',face_crop(A+'A020.jpg',380,370),'愛子さま 2026.6.22 ©Naoya Ikegami/SUNTORY HALL',
     [(S+'jg.jpg','イメージ：ジュロン地区の日本庭園（写真 FN-082 / CC BY-SA 4.0）',0.5,0.55)],
     '56年前に祖父母が植えられた木とは？','シンガポールでのおことばから')
