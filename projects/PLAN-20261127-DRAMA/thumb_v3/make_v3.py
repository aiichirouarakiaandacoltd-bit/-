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
 "L2": [(177, 181, 464, 474), (921, 181, 1208, 448)],
 "L3": [(235, 23, 435, 253), (735, 53, 955, 303)],
 "S":  [],  # ショートは写真の上に文字を置かない(帯の中だけ)
}
MARGIN = 30
BOXES = []
def T(im, xy, s, font, stroke=8, **kw):
    bb = text(im, xy, s, font, stroke=stroke, **kw)
    if bb: BOXES.append((s, (bb[0] - stroke, bb[1] - stroke, bb[2] + stroke, bb[3] + stroke)))
    return bb
def check(name):
    bad = []; global BOXES_LAST; BOXES_LAST = list(BOXES)
    for s, (a, b, c, d) in BOXES:
        for (x0, y0, x1, y1) in HEADS[name]:
            if a < x1 + MARGIN and c > x0 - MARGIN and b < y1 + MARGIN and d > y0 - MARGIN: bad.append((s, (x0, y0, x1, y1)))
    # 文字どうしの重なりも検査する(荒木指示 2026-11-28「中段と下段の文字が重なっている」)
    for i in range(len(BOXES)):
        for j in range(i + 1, len(BOXES)):
            (s1, (a, b, c, d)), (s2, (e, f, g, h)) = BOXES[i], BOXES[j]
            if a < g and c > e and b < h and d > f: bad.append(("文字どうし", s1, s2))
    BOXES.clear()
    assert not bad, f"{name}: 文字がお顔・頭に掛かる {bad} 文字の範囲={BOXES_LAST}"
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
def ctext(im, center, s, path, fill, glyph_h, maxw, condense=0.76, stroke=10, bold=2, bottom=None):
    """競合の表紙(荒木さん指定の見本)に合わせた極太ゴシック: 文字の高さで大きさを決め、横を少し詰める(長体)。
    幅が足りなければ小さくする。黒の太い縁取り+影。戻り値は縁取りを含む範囲(お顔の検査用)。"""
    from PIL import ImageFont, ImageFilter
    size = int(glyph_h * 1.18)
    while True:
        f = ImageFont.truetype(path, size)
        l, t, r, bt = f.getbbox(s, stroke_width=stroke)
        w = (r - l) * condense
        if w <= maxw or size < 20: break
        size -= 2
    lay = Image.new("RGBA", (r - l + 20, bt - t + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((10 - l, 10 - t), s, font=f, fill=BLK, stroke_width=stroke, stroke_fill=BLK)
    d.text((10 - l, 10 - t), s, font=f, fill=fill, stroke_width=bold, stroke_fill=fill)  # 少し太らせて見本の極太に近づける
    lay = lay.resize((int(lay.width * condense), lay.height), Image.LANCZOS)
    x = int(center[0] - lay.width / 2); y = int(center[1] - lay.height / 2)
    if bottom is not None:  # 縁取りを含めた文字の下端を bottom にそろえる
        y = bottom - lay.split()[-1].getbbox()[3]
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.putalpha(lay.split()[-1].point(lambda v: int(v * 0.7)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (x + 4, y + 6)); im.alpha_composite(lay, (x, y))
    bb = lay.split()[-1].getbbox()
    BOXES.append((s, (x + bb[0], y + bb[1], x + bb[2], y + bb[3])))
    return (x + bb[0], y + bb[1], x + bb[2], y + bb[3])


def stack(im, items, top, bottom=714, maxw=1256, gap=4, stroke=10, cmin=0.72, path=None, bold=1):
    """荒木指示 2026-11-28「出来る限り大きく」: 決められた範囲(top〜bottom)に、各段を重ねずに入る最大の大きさで置く。
    各段は横幅いっぱい(maxw)まで使い、足りなければ横を詰める(長体、最小 cmin)。見本(JAPANマインドの表紙)の型。"""
    from PIL import ImageFont
    path = path or SANS
    for size in range(200, 20, -2):
        f = ImageFont.truetype(path, size); hs = []; cs = []; ok = True
        for t, _ in items:
            l, tp, r, bt = f.getbbox(t, stroke_width=stroke)
            c = min(1.0, maxw / (r - l + 20))
            if c < cmin: ok = False; break
            hs.append(bt - tp); cs.append(c)
        if ok and sum(hs) + gap * (len(items) - 1) <= bottom - top: break
    y = bottom; boxes = []
    for (t, col), c in reversed(list(zip(items, cs))):
        b = ctext(im, (640, 0), t, path, col, size / 1.18, 99999, condense=c, stroke=stroke, bold=bold, bottom=y)
        boxes.append(b); y = b[1] - gap
    return size

def L2():
    # 荒木指示 2026-11-28: 見本(JAPANマインドの表紙)の書体と文字の大きさに合わせる。上段は白。3段3色(白・水色・ピンク)
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
    # 荒木指示 2026-11-28: お顔を見本(画面の高さの約4割)まで大きく → 陛下と雅子さまを左右2枚に分けて約2倍に
    im.paste(photo("shokuju", (97, 117, 434, 412), (640, 560)), (0, 160))
    im.paste(photo("shokuju", (560, 120, 897, 415), (640, 560)), (640, 160))
    ImageDraw.Draw(im).line((640, 160, 640, 720), fill=WHITE, width=4)
    vgrad(im, 480, 720, color=(0, 0, 0), a1=235)
    ctext(im, (640, 80), "「" + QUOTE + "」", SANS, WHITE, 112, 1265, condense=0.68, bold=1)
    # 中段と下段は重ねない: 下段の下端を712に置き、中段は下段の上端から16px空けて置く(荒木指示 2026-11-28)
    # 中段と下段: お顔の下(お顔の枠+30px)から下端までに、重ねずに入る最大の大きさ
    stack(im, [("63歳 雅子さまのお誕生日", BLUE), ("戦後80年に綴られた想いとは…", PINK)], top=max(b[3] for b in HEADS["L2"]) + MARGIN + 1)
    cr = ["写真:宮内庁", "令和8年5月17日 全国植樹祭", "「」:宮内庁 令和7年", "皇后陛下お誕生日のご感想より"]
    credit(im, (650, 168), cr, 12, anchor="la")
    BOXES.append(("出典", (650, 168, 650 + 12 * 15, 168 + 4 * 16)))
    check("L2"); return im

# ---- 長尺③ 一場面の大写し+短い一言: 両陛下を大きく、文字は右下に寄せて短く ----
def L3():
    # 荒木指示 2026-11-28: 文字を出来る限り大きく(見本の極太ゴシック)。3段3色(水色・白・黄)
    im = photo("chakai", (90, 120, 1000, 640), (1280, 720))
    top = max(b[3] for b in HEADS["L3"]) + MARGIN + 1
    vgrad(im, top - 60, 720, color=(0, 0, 0), a1=235)
    stack(im, [("12月9日 63歳のお誕生日", BLUE), ("「" + QUOTE + "」", WHITE), ("雅子さまの願いとは…", YEL)], top=top)
    cr = ["写真:宮内庁", "令和8年11月4日 茶会(宮殿)", "「」:宮内庁 令和7年", "皇后陛下お誕生日のご感想より"]
    credit(im, (1272, 8), cr, 12, anchor="ra")
    BOXES.append(("出典", (1272 - 12 * 15, 8, 1272, 8 + 4 * 16)))
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
