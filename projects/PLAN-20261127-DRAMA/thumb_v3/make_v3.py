# 表紙 第3版(2026-11-28): 伸びている競合の型(写真+極太文字だけ。飾り・AI背景なし)
# 写真は宮内庁の行事写真(切り抜き・拡大縮小のみ。お顔の加工なし)。皇族方以外が写る部分は切り落とす。
import sys
sys.path.insert(0, "/home/user/-/projects/PLAN-20261127-DRAMA/thumb_gptimage")
from compose import text, F, SERIF, SANS, SANSB, vgrad, credit, fit
from PIL import Image, ImageDraw
A = "/home/user/-/assets/"
P = {  # 台帳の写真と撮影情報
 "tobe":   (A + "KB-20261127-01/A006.jpg", "令和8年5月17日 ご視察(愛媛県砥部町)"),
 "takkyu": (A + "KB-20261122-01/A008.jpg", "令和8年10月11日 卓球競技ご覧(青森市)"),
 "aomori": (A + "KB-20261122-01/A011.jpg", "令和8年10月11日 ご視察(青森市)"),
 "shokuju":(A + "KB-20261127-01/A009.jpg", "令和8年5月17日 全国植樹祭(愛媛県)"),
 "chakai": (A + "KB-20261122-02/A012.jpg", "令和8年11月4日 茶会(宮殿)"),
}
QUOTE = "あと20年で100年もの月日が"
assert QUOTE in open("/home/user/-/projects/PLAN-20261127-DRAMA/raw/empress2025.txt").read()
YEL = (255, 222, 0); BLK = (0, 0, 0); WHITE = (255, 255, 255)
SRCQ = "「」:宮内庁 令和7年 皇后陛下お誕生日のご感想より"

def photo(key, box, size):  # box = 元写真の切り出し範囲(人物以外を外す)
    im = Image.open(P[key][0]).convert("RGB").crop(box)
    W, H = size; s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((l, t, l + W, t + H)).convert("RGBA")

# ---- 長尺① 人物史の明朝型: 写真2枚を横に並べ、下半分に白と黄の極太明朝 ----
def L1():
    im = Image.new("RGBA", (1280, 720))
    im.paste(photo("takkyu", (50, 60, 520, 588), (640, 720)), (0, 0))
    im.paste(photo("aomori", (180, 0, 940, 560), (640, 720)), (640, 0))
    ImageDraw.Draw(im).line((640, 0, 640, 720), fill=WHITE, width=4)
    vgrad(im, 380, 720, color=(0, 0, 0), a1=235)
    text(im, (640, 478), "「" + QUOTE + "」", fit("「" + QUOTE + "」", SERIF, 70, 1220), fill=WHITE, stroke=8, stroke_fill=BLK)
    text(im, (640, 600), "戦後80年の想い", F(SERIF, 140), fill=YEL, stroke=12, stroke_fill=BLK)
    credit(im, (1272, 714), ["写真:宮内庁 " + P["takkyu"][1] + "/" + P["aomori"][1], SRCQ], 13)
    return im

# ---- 長尺② 場面+3段の極太ゴシック型: 一場面を全面、上に黄色の「」、下に白と黄の2行 ----
def L2():
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
    im.paste(photo("shokuju", (0, 20, 920, 444), (1280, 590)), (0, 130))
    vgrad(im, 430, 720, color=(0, 0, 0), a1=235)
    text(im, (640, 66), "「" + QUOTE + "」", fit("「" + QUOTE + "」", SANS, 86, 1230), fill=YEL, stroke=10, stroke_fill=BLK)
    text(im, (640, 548), "63歳 雅子さまのお誕生日", fit("63歳 雅子さまのお誕生日", SANS, 80, 1200), fill=WHITE, stroke=10, stroke_fill=BLK)
    text(im, (640, 650), "戦後80年に綴られた想いとは…", fit("戦後80年に綴られた想いとは…", SANS, 84, 1230), fill=YEL, stroke=10, stroke_fill=BLK)
    credit(im, (1272, 138), ["写真:宮内庁 " + P["shokuju"][1], SRCQ], 13, anchor="ra")
    return im

# ---- 長尺③ 一場面の大写し+短い一言: 両陛下を大きく、文字は右下に寄せて短く ----
def L3():
    im = photo("chakai", (90, 40, 1000, 560), (1280, 720))
    vgrad(im, 400, 720, color=(0, 0, 0), a1=225)
    text(im, (50, 110), "12月9日", F(SANS, 60), fill=YEL, stroke=8, stroke_fill=BLK, anchor="lm")
    text(im, (50, 195), "63歳の", F(SANS, 60), fill=WHITE, stroke=8, stroke_fill=BLK, anchor="lm")
    text(im, (50, 280), "お誕生日", F(SANS, 60), fill=WHITE, stroke=8, stroke_fill=BLK, anchor="lm")
    text(im, (640, 520), "「" + QUOTE + "」", fit("「" + QUOTE + "」", SERIF, 64, 1100), fill=WHITE, stroke=8, stroke_fill=BLK)
    text(im, (640, 635), "雅子さまの願いとは…", F(SERIF, 112), fill=YEL, stroke=11, stroke_fill=BLK)
    credit(im, (1272, 714), ["写真:宮内庁 " + P["chakai"][1], SRCQ], 13)
    return im

# ---- ショート: 黒の帯の型(上に白の3行、中央に一場面、下に黄色の極太2行) ----
def S():
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
    im.paste(photo("tobe", (380, 0, 990, 666), (1080, 1180)), (0, 450))
    text(im, (540, 120), "63歳を迎える雅子さま", fit("63歳を迎える雅子さま", SANS, 96, 1020), fill=WHITE, stroke=0, shadow=False)
    text(im, (540, 255), "「あと20年で", F(SANS, 112), fill=YEL, stroke=0, shadow=False)
    text(im, (540, 380), "100年もの月日が」", fit("100年もの月日が」", SANS, 112, 1040), fill=YEL, stroke=0, shadow=False)
    text(im, (540, 1700), "戦後80年の", F(SANS, 140), fill=YEL, stroke=0, shadow=False)
    text(im, (540, 1840), "想いとは…", F(SANS, 130), fill=WHITE, stroke=0, shadow=False)
    credit(im, (1064, 1620), ["写真:宮内庁 " + P["tobe"][1], SRCQ], 22)
    return im

for n, f in [("long_1_mincho", L1), ("long_2_scene3dan", L2), ("long_3_closeup", L3), ("short_blackband", S)]:
    f().convert("RGB").save(n + ".png"); print(n)
