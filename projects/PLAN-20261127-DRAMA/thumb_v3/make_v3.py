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
BLUE = (95, 211, 255); PINK = (255, 126, 182)   # 3段の時は3色(荒木指示 2026-11-28)。赤は使わない
# お顔・頭の範囲(書き出し後の座標。目視で登録し、余白30pxを足して検査する)
HEADS = {
 "L1": [(265, 60, 450, 305), (715, 90, 885, 285), (1120, 20, 1280, 245)],
 "L2": [(265, 224, 475, 439), (985, 229, 1195, 424)],
 "L3": [(235, 79, 435, 309), (735, 109, 955, 359)],
 "S":  [],  # ショートは写真の上に文字を置かない(帯の中だけ)
}
MARGIN = 30
BOXES = []
def T(im, xy, s, font, stroke=8, **kw):
    bb = text(im, xy, s, font, stroke=stroke, **kw)
    if bb: BOXES.append((s, (bb[0] - stroke, bb[1] - stroke, bb[2] + stroke, bb[3] + stroke)))
    return bb
def check(name):
    bad = []
    for s, (a, b, c, d) in BOXES:
        for (x0, y0, x1, y1) in HEADS[name]:
            if a < x1 + MARGIN and c > x0 - MARGIN and b < y1 + MARGIN and d > y0 - MARGIN: bad.append((s, (x0, y0, x1, y1)))
    BOXES.clear()
    assert not bad, f"{name}: 文字がお顔・頭に掛かる {bad}"
    print(name, "お顔・頭への重なり: なし")
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
    T(im, (640, 478), "「" + QUOTE + "」", fit("「" + QUOTE + "」", SERIF, 70, 1220), fill=WHITE, stroke=8, stroke_fill=BLK)
    T(im, (640, 600), "戦後80年の想い", F(SERIF, 140), fill=YEL, stroke=12, stroke_fill=BLK)
    credit(im, (1272, 714), ["写真:宮内庁 " + P["takkyu"][1] + "/" + P["aomori"][1], SRCQ], 13)
    check("L1"); return im

# ---- 長尺② 場面+3段の極太ゴシック型: 一場面を全面、上に黄色の「」、下に白と黄の2行 ----
EX = "/home/user/-/templates/fonts/extra/"
L2FONT = [SERIF]  # 長尺の型の決まり(Noto Serif CJK Black)にそろえる。荒木指示 2026-11-28「長尺②の書体がダサい」
def L2():
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
    im.paste(photo("shokuju", (0, 60, 920, 484), (1280, 590)), (0, 130))
    vgrad(im, 430, 720, color=(0, 0, 0), a1=235)
    T(im, (640, 66), "「" + QUOTE + "」", fit("「" + QUOTE + "」", L2FONT[0], 86, 1230), fill=WHITE, stroke=10, stroke_fill=BLK)
    T(im, (640, 548), "63歳 雅子さまのお誕生日", fit("63歳 雅子さまのお誕生日", L2FONT[0], 80, 1200), fill=BLUE, stroke=10, stroke_fill=BLK)
    T(im, (640, 650), "戦後80年に綴られた想いとは…", fit("戦後80年に綴られた想いとは…", L2FONT[0], 84, 1230), fill=PINK, stroke=10, stroke_fill=BLK)
    credit(im, (1272, 138), ["写真:宮内庁 " + P["shokuju"][1], SRCQ], 13, anchor="ra")
    check("L2"); return im

# ---- 長尺③ 一場面の大写し+短い一言: 両陛下を大きく、文字は右下に寄せて短く ----
def L3():
    im = photo("chakai", (90, 80, 1000, 600), (1280, 720))
    vgrad(im, 400, 720, color=(0, 0, 0), a1=225)
    T(im, (640, 462), "12月9日 63歳のお誕生日", F(SANS, 50), fill=BLUE, stroke=8, stroke_fill=BLK)
    T(im, (640, 545), "「" + QUOTE + "」", fit("「" + QUOTE + "」", SERIF, 62, 1100), fill=WHITE, stroke=8, stroke_fill=BLK)
    T(im, (640, 648), "雅子さまの願いとは…", F(SERIF, 104), fill=YEL, stroke=11, stroke_fill=BLK)
    credit(im, (1272, 714), ["写真:宮内庁 " + P["chakai"][1], SRCQ], 13)
    check("L3"); return im

# ---- ショート: 黒の帯の型(上に白の3行、中央に一場面、下に黄色の極太2行) ----
def S():
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
    im.paste(photo("tobe", (380, 0, 990, 666), (1080, 1180)), (0, 450))
    T(im, (540, 120), "63歳を迎える雅子さま", fit("63歳を迎える雅子さま", SANS, 96, 1020), fill=WHITE, stroke=0, shadow=False)
    T(im, (540, 255), "「あと20年で", F(SANS, 112), fill=YEL, stroke=0, shadow=False)
    T(im, (540, 380), "100年もの月日が」", fit("100年もの月日が」", SANS, 112, 1040), fill=YEL, stroke=0, shadow=False)
    T(im, (540, 1700), "戦後80年の", F(SANS, 140), fill=YEL, stroke=0, shadow=False)
    T(im, (540, 1840), "想いとは…", F(SANS, 130), fill=WHITE, stroke=0, shadow=False)
    credit(im, (1064, 1620), ["写真:宮内庁 " + P["tobe"][1], SRCQ], 22)
    BOXES.clear(); return im

if len(sys.argv) > 1 and sys.argv[1] == "l2fonts":
    for tag, fp in [("a_mincho_noto", SERIF), ("b_dela_gothic", EX + "DelaGothicOne.ttf"), ("c_zen_old_mincho", EX + "ZenOldMincho.ttf"), ("d_kaisei_tokumin", EX + "KaiseiTokumin.ttf")]:
        L2FONT[0] = fp; L2().convert("RGB").save(f"l2_font_{tag}.png"); print(tag)
    sys.exit()
for n, f in [("long_1_mincho", L1), ("long_2_scene3dan", L2), ("long_3_closeup", L3), ("short_blackband", S)]:
    f().convert("RGB").save(n + ".png"); print(n)
