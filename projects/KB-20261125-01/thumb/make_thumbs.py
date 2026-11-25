"""KB-20261125-01 の長尺の表紙 3パターン(第5-2章・第5-3章5・templates/thumb_long_template.md の型D)。
python3 projects/KB-20261125-01/thumb/make_thumbs.py で thumb_A.png・thumb_B.png・thumb_C.png(1280×720)を書き出す。
写真は宮内庁(ledger の確認方法が「キャプション」または「目視確認済(当てっこ係)」のものだけ)。切り抜き・拡大縮小のみ。

型D(左右2枚・お顔はパネル中央 x320・y305・高さ約175px)の決まりはそのままにして、第5-3章5
「表紙の文字は2か所・合計20字前後・最大の文字は2〜5字の語」に合わせ、文字を
  ① 上の帯(白・かぎかっこは宮内庁原文の一節を一字一句。帯の右に小さく出典)
  ② 下の一言(白の短い語＋金のグラデーションの大きな2〜5字の語を1行に)
の2か所にした(金の帯は文字が3か所目になるため使わない)。
  A = 左 雅子さま A025(令和7年 皇后陛下お誕生日のご近影)/右 愛子さま A057(令和7年 愛子内親王殿下お誕生日のご近影)
  B = 令和7年 新年のご一家のご近影 A073 から、左に雅子さま・右に愛子さま(お二人が同じ1枚に写る写真)
  C = 左 雅子さま A021(令和6年 皇后陛下お誕生日のご近影)/右 令和4年3月17日 ご成年の記者会見の愛子さま A061
2026-11-25 直し係(rules_check.md 12. G6 の指摘): B の帯右を出典の形にし、陛下のお召し物が出ない切り抜きに。C の左を A065(338px)から A021(1000px)に。クレジットの右余白を 24px に。
2026-11-25 直し係(荒木指示「3枚の構図が全部一緒。ABテストが出来るように」・第5-2章4): 3枚で素材・構図・配置・タイトルの位置を変えた。
  A = 型D(左右2枚・上の帯＋下の金の一言)のまま: 左 雅子さま A025/右 愛子さま A057
  B = 型R系(文字 左4.5割・写真 右5.5割): 右に愛子さまお一人 A059(令和7年 お誕生日のご近影の別カット・左向き)。
      左に横書き2行「18歳から/24歳まで」＋金「7回」のご感想。左下に年の違う愛子さまの小さな写真4枚(A037・A043・A142・A152)
  C = 写真1枚いっぱい(左寄せ・お顔は左1/3): 雅子さまお一人 A021。右に縦書き「生まれてきて/ありがとう」(白と金)。上の帯なし
  そろえているのは 明朝の極太・金の文字・配色(赤なし・下部の濃紺グラデーションなし)・クレジットの置き方だけ。
  書き出しの最後に、3枚を縮小して並べた一覧 thumb/abc_overview.jpg も作る(ひと目で別の表紙に見えるかの確認用)
2026-11-25 直し係(荒木の指摘「文字の意味が分からない・誰の言葉か分からない」。構図・写真は変えず文字だけ直した):
  A = 下の一言を「7回のご感想のうち/6回」から「母がつづった/娘への思い(金)」に。帯の右の出典の上に小さく「雅子さま」
  B = 左上に主語の表示「愛子さま」を足した(台詞ではないのでかぎかっこなし)。「18歳から/24歳まで」＋金「7回」のご感想 はそのまま
  C = 縦書きの引用の上に「雅子さま」。出典を「平成14年 愛子さまご誕生の会見より」に。
      かぎかっこ内は原文の一部「生まれてきてありがとう」のまま(呼びかけ「愛子、」などは足さない＝原文にないため)
2026-11-25 直し係(rules_check.md 15. 表紙 文字直しの採点。構図・写真は変えず小さな直しだけ):
  A = 下の一言を「母がつづった」→「母がつづられた」(本編の語りと敬語をそろえる)。1字増えたので 84→78px・金 136→128px
  B = 「7回のご感想」の下に小さな出典「雅子さまのお誕生日のご感想より」(金・小さく。出典なので文字の数に入れない)。
      入れるために見出しを少し上に詰め、小さな写真の高さを 140→124px に(年ラベルの位置は同じ)
  C = 出典を「愛子さまご誕生の会見より(平成14年4月)」に(年月が会見にかかる形。ご誕生は平成13年12月1日)。
      縦書きのかぎかっこは縦書き用の字形(﹁ ﹂)のまま、文字と離して置き直した(前は「生」「う」に食い込んで横書きの形に見えた)
2026-11-25 直し係(荒木指示 2026-11-25。表紙B の文字だけ。A・C は触らない):
  B = 左上の主語の表示「愛子さま」→「愛子さまが」。ほかの文字・出典・写真・構図はそのまま
2026-11-25 直し係(追加の荒木指示 2026-11-25。表紙C の小さな文字だけ。A は触らない):
  C = 小さな「雅子さま」→「雅子さまから愛子さまへの思い」(横書き1行・36px・右寄せ)。縦書きの引用・出典・写真・構図はそのまま
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline import thumb_long as T
from pipeline.thumb_long import place, text, grad, credit, check_faces, F, W, H, NAVY

A = str(ROOT / "assets/KB-20261125-01") + "/"
O = str(Path(__file__).resolve().parent) + "/"
BAND = 104          # 上の帯の高さ
BASE = 668          # 下の一言のベースライン
SRC_GOLD = (232, 200, 110)
CREDIT_RIGHT = 24   # クレジットの右の余白(G6 の指摘で 20px以上に)


def panel(path, focus, fh=175, extra=(), target=(320, 305)):
    """型Dの決まった位置(パネル中央 x320・y305)に、お顔の高さ fh で置く。extra=同じ写真に写る主役の方のお顔(元の写真のpx)"""
    p = place(path, 640, H, target, fh, focus)
    faces = [place.last_face]
    if extra:
        import cv2
        ih, iw = cv2.imread(path).shape[:2]
        cx, cy, s = focus[0] * iw, focus[1] * ih, fh / (focus[2] * ih)
        faces += [(target[0] + (x - cx) * s, target[1] + (y - cy) * s, w * s, h * s) for (x, y, w, h) in extra]
    return p, faces


def d2(out, left, right, quote, src, parts, cap, who=None):
    im = Image.new("RGB", (W, H), NAVY)
    p1, f1 = panel(*left); p2, f2 = panel(*right)
    im.paste(p1, (0, 0)); im.paste(p2, (640, 0))
    ImageDraw.Draw(im).line((640, BAND, 640, H), fill=(10, 20, 45), width=6)
    faces = f1 + [(x + 640, y, w, h) for (x, y, w, h) in f2]
    # ① 上の帯: 白の一節(左寄せ)＋右に小さく出典
    im.paste(grad(W, BAND, [(0, (6, 14, 36)), (1, (16, 32, 68))]), (0, 0))
    d = ImageDraw.Draw(im)
    sw_src = max(d.textlength(src, font=F(28)), d.textlength(who, font=F(40)) if who else 0)
    qx1 = W - 24 - sw_src - 24
    qs = text(im, (24, BAND // 2), quote, 78, anchor="lm", maxw=qx1 - 24, shadow=False)
    if who:   # 誰の言葉か(小さな名前の札)。出典の上に置く。文字の数には入れない
        text(im, (W - 24, 32), who, 40, sw=3, shadow=False, anchor="rm")
        text(im, (W - 24, 78), src, 28, fill=SRC_GOLD, sw=3, shadow=False, anchor="rm")
    else:
        text(im, (W - 24, BAND // 2 + 4), src, 28, fill=SRC_GOLD, sw=3, shadow=False, anchor="rm")
    # ② 下の一言: [(文字, 大きさ, "white"/"gold"), ...] を1行に(中央寄せ・同じベースライン)
    ws = [d.textlength(s, font=F(n)) for s, n, _ in parts]
    x = (W - sum(ws)) / 2; boxes = []
    for (s, n, fill), w in zip(parts, ws):
        text(im, (x, BASE), s, n, fill=fill, sw=9 if fill == "gold" else 8, anchor="ls")
        boxes.append(ImageDraw.Draw(im).textbbox((x, BASE), s, font=F(n), anchor="ls", stroke_width=9)); x += w
    bottom = (int(min(b[0] for b in boxes)), int(min(b[1] for b in boxes)), int(max(b[2] for b in boxes)), int(max(b[3] for b in boxes)))
    credit(im, cap, [bottom, (0, 0, W, BAND)], right=CREDIT_RIGHT)
    im.save(out)
    print(out, "帯の文字", qs, "px / 下の一言の枠", bottom)
    if not check_faces(out, faces, [(0, 0, W, BAND), bottom]):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


# A 実際のお言葉×疑問(題名A): 左 雅子さま(令和7年お誕生日のご近影 A025)/右 愛子さま(令和7年お誕生日のご近影 A057)
#   帯 =「あの幼かった愛子が」(令和3年 皇后陛下お誕生日のご感想の原文の一部)。帯の右に小さく「雅子さま」と出典
#   下 = 母がつづられた＋金「娘への思い」(かぎかっこなし＝当チャンネルの見出し。ご感想は文書なので「つづった」。facts F4)。2か所・20字
d2(O + "thumb_A.png", (A + "A025.jpg", None), (A + "A057.jpg", None),
   "「あの幼かった愛子が」", "令和3年のご感想より",
   [("母がつづられた", 78, "white"), ("娘への思い", 128, "gold")],
   "写真: 宮内庁 令和7年 皇后陛下お誕生日のご近影(御所)/令和7年 愛子内親王殿下お誕生日のご近影", who="雅子さま")


def bbox(im, xy, s, n, anchor, sw=9):
    return ImageDraw.Draw(im).textbbox(xy, s, font=F(n), anchor=anchor, stroke_width=sw)


def union(bs):
    return (int(min(b[0] for b in bs)), int(min(b[1] for b in bs)), int(max(b[2] for b in bs)), int(max(b[3] for b in bs)))


def head_box(f):
    """check_faces と同じ「髪から顎までの頭の範囲」"""
    x, y, w, h = f
    return (x - w * 0.25, y - h * 0.55, x + w * 1.25, y + h * 1.15)


def r1(out, hero, hero_focus, hero_fh, hero_xy, lines, parts, strip, cap, src=None):
    """B 型R系: 右 約5.5割に人物1名の大きい写真、左 約4.5割に横書きの文字(白2行＋金の大きな語)。左下に年の違う小さな写真の帯"""
    PX = 440                                    # 写真パネルの左端(ここから右へ。左側は濃紺へなじませる)
    im = Image.new("RGB", (W, H), NAVY)
    ph = place(hero, W - PX, H, (hero_xy[0] - PX, hero_xy[1]), hero_fh, hero_focus); im.paste(ph, (PX, 0))
    fx, fy, fw, fh = place.last_face; faces = [(fx + PX, fy, fw, fh)]
    fade = grad(W, H, [(0, (255,) * 3), (0.40, (255,) * 3), (0.50, (0,) * 3), (1, (0,) * 3)], horizontal=True).convert("L")
    im = Image.composite(grad(W, H, [(0, (6, 16, 40)), (1, (20, 40, 80))]), im, fade)
    # ① 左上: 白の2行(横書き・左寄せ)
    boxes1 = []
    for (s, n, y) in lines:
        text(im, (28, y), s, n, sw=8, anchor="ls"); boxes1.append(bbox(im, (28, y), s, n, "ls", 8))
    if lines[0][0].startswith("愛子さま"):   # 主語の表示の下に細い金の線(次の2行と分ける)
        b0 = boxes1[0]; ImageDraw.Draw(im).rectangle((30, b0[3] + 2, b0[2] - 8, b0[3] + 6), fill=SRC_GOLD)
    # ② その下: 金の大きな語＋白の短い語(同じベースライン)
    d = ImageDraw.Draw(im); x = 28; boxes2 = []
    for (s, n, fill, y) in parts:
        text(im, (x, y), s, n, fill=fill, sw=9 if fill == "gold" else 8, anchor="ls")
        boxes2.append(bbox(im, (x, y), s, n, "ls")); x += d.textlength(s, font=F(n)) + 6
    tboxes = [union(boxes1), union(boxes2)]
    if src:   # 小さな出典(誰のご感想か)。(文字, 大きさ, 中心y)。金・小さく。文字の数には入れない
        ss, sn, sy = src
        text(im, (30, sy), ss, sn, fill=SRC_GOLD, sw=3, shadow=False, anchor="lm")
        srcb = bbox(im, (30, sy), ss, sn, "lm", 3)
        if srcb[1] < tboxes[1][3]:
            raise SystemExit(f"{out}: 出典が見出しと重なっています {srcb} {tboxes[1]}")
        tboxes.append(tuple(int(v) for v in srcb))
    # 左下: 年の違う小さな写真(年は掲載ページで確認できたものだけ)。下に小さく年(写真の説明。文字の数には入れない)
    TW, TH, GAP, TY = 124, 124, 12, 524
    tile_boxes = []
    for k, (path, focus, label) in enumerate(strip):
        tx = 28 + k * (TW + GAP)
        t = place(path, TW, TH, (TW // 2, 60), 56, focus); f = place.last_face
        hb = head_box(f)
        if hb[0] < 0 or hb[1] < 0 or hb[2] > TW or hb[3] > TH:
            raise SystemExit(f"{path}: 小さな写真の中でお顔(頭の範囲)が見切れています {hb}")
        im.paste(t, (tx, TY))
        ImageDraw.Draw(im).rectangle((tx - 2, TY - 2, tx + TW + 1, TY + TH + 1), outline=(232, 200, 110), width=2)
        text(im, (tx + TW // 2, TY + TH + 20), label, 22, fill=SRC_GOLD, sw=2, shadow=False, anchor="mm")
        faces.append((f[0] + tx, f[1] + TY, f[2], f[3])); tile_boxes.append((tx - 2, TY - 2, tx + TW + 2, TY + TH + 36))
    strip_box = union(tile_boxes)
    for tb in tboxes:
        if tb[3] > strip_box[1] or tb[2] > W * 0.48:
            raise SystemExit(f"{out}: 文字が小さな写真の帯か写真側にはみ出しています {tb}")
    credit(im, cap, tboxes + [strip_box], right=CREDIT_RIGHT)
    im.save(out)
    print(out, "文字の枠", tboxes, "/ 小さな写真の帯", strip_box)
    if not check_faces(out, faces, tboxes):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


def v1(out, path, focus, fh, xy, col_w, col_g, src, cap, who=None):
    """C 写真1枚いっぱい(左寄せ・お顔は左1/3)。右に縦書き2行(右の行=白・左の行=金)。上の帯なし"""
    import cv2, numpy as np
    img = cv2.imread(path); ih, iw = img.shape[:2]
    # 下地: 同じ写真のぼかし(画面いっぱい)。右の文字の所だけ横方向に濃紺を重ねる(下部のグラデーションは敷かない)
    cs = max(W / iw, H / ih)
    bg = cv2.GaussianBlur(cv2.resize(img, (int(iw * cs) + 2, int(ih * cs) + 2)), (0, 0), 26)
    y0 = (bg.shape[0] - H) // 3
    im = Image.fromarray(cv2.cvtColor(bg[y0:y0 + H, :W], cv2.COLOR_BGR2RGB))
    # 写真(切り抜き・拡大縮小のみ)。右端はぼかしの下地へなじませる
    PW = 870
    ph = place(path, PW, H, xy, fh, focus); faces = [place.last_face]
    m = grad(PW, H, [(0, (255,) * 3), (0.90, (255,) * 3), (1, (0,) * 3)], horizontal=True).convert("L")
    im.paste(ph, (0, 0), m)
    shade = grad(W, H, [(0, (0,) * 3), (0.61, (0,) * 3), (0.69, (232,) * 3), (1, (240,) * 3)], horizontal=True).convert("L")
    im = Image.composite(grad(W, H, [(0, (6, 16, 40)), (1, (20, 40, 80))]), im, shade)
    # 縦書き: 1字ずつ行の中心に置く。かぎかっこは縦書き用の字形(﹁ ﹂)
    boxes = []
    KG = 12   # かぎかっこと文字の間(px)
    def ink(ch, n):
        """字形の線が実際にある上下の位置(中心からのpx)。縦書き用のかぎかっこは升目の端に寄っているため測って置く"""
        m = Image.new("L", (n * 3, n * 3), 0); ImageDraw.Draw(m).text((n * 1.5, n * 1.5), ch, font=F(n), fill=255, anchor="mm")
        bb = m.getbbox(); return bb[1] - n * 1.5, bb[3] - n * 1.5
    def column(cx, top, s, n, fill, opening=None, closing=None):
        y = top
        if opening:   # 字形の実際の線の位置を測り、線の上端を top+8 に、線の下端から KG 空けて1字目を始める
            t0, b0 = ink(opening, n); oy = y + 8 - t0
            text(im, (cx, oy), opening, n, fill=fill, sw=8, anchor="mm"); boxes.append((cx - n // 2 - 8, int(oy + t0 - 8), cx + n // 2 + 8, int(oy + b0 + 8))); y = oy + b0 + KG
        for ch in s:
            text(im, (cx, y + n / 2), ch, n, fill=fill, sw=9 if fill == "gold" else 8, anchor="mm")
            boxes.append(bbox(im, (cx, y + n / 2), ch, n, "mm")); y += n * 1.0
        if closing:
            t0, b0 = ink(closing, n); oy = y + KG + 6 - t0
            text(im, (cx, oy), closing, n, fill=fill, sw=8, anchor="mm"); boxes.append((cx - n // 2 - 8, int(oy + t0 - 8), cx + n // 2 + 8, int(oy + b0 + 8))); y = oy + b0 + 8
        return y
    column(*col_w); yb = column(*col_g)
    if who:   # 誰の言葉か: 金の行の上(横書き・小さめ)。(文字, 大きさ, 中心y)。下に細い金の線
        ws, wn, wy = who[:3]
        wx, wa = (who[3], "rm") if len(who) > 3 else (col_g[0], "mm")   # 4つ目があれば右端の x(右寄せ)。長い一言を白い行の左に収める
        text(im, (wx, wy), ws, wn, sw=6, anchor=wa); wb = bbox(im, (wx, wy), ws, wn, wa, 6); wbox = tuple(int(v) for v in wb)
        ImageDraw.Draw(im).rectangle((wb[0] + 8, wb[3] + 1, wb[2] - 8, wb[3] + 4), fill=SRC_GOLD)
    # 出典(小さく・金の行の下)。文字の数には入れない
    sx = col_g[0] + col_g[3] // 2 + 6
    sb = bbox(im, (sx, yb + 30), src, 28, "rm", 3)
    sb = (sb[0] - 12, sb[1] - 5, sb[2] + 10, sb[3] + 5)   # 出典が写真(白いお召し物)にかかるので、濃紺の札を敷いて読めるようにする
    ImageDraw.Draw(im).rounded_rectangle(sb, radius=6, fill=(8, 20, 48))
    text(im, (sx, yb + 30), src, 28, fill=SRC_GOLD, sw=3, shadow=False, anchor="rm")
    tbox = union(boxes + [sb] + ([wbox] if who else []))
    if tbox[3] > H - 24 or tbox[2] > W - 8 or tbox[1] < 4:
        raise SystemExit(f"{out}: 縦書きの文字が画面からはみ出しています {tbox}")
    credit(im, cap, [tbox], right=CREDIT_RIGHT)
    im.save(out)
    # お顔との重なりは、縦書き(名前を含む)の枠と出典の札を別々の枠で確かめる(まとめた1つの枠だと、文字のない所までお顔と重なる扱いになるため)
    cbox = union(boxes); sbox = tuple(int(v) for v in sb)
    if who and any(wbox[0] < b[2] and wbox[2] > b[0] and wbox[1] < b[3] and wbox[3] + 4 > b[1] for b in boxes):
        raise SystemExit(f"{out}: 上の一言が縦書きの文字と重なっています {wbox}")
    print(out, "縦書きの枠", cbox, "/ 上の一言", wbox if who else None, "/ 出典の札", sbox, "/ 全体", tbox, "/ お顔", [tuple(int(v) for v in head_box(f)) for f in faces])
    if not check_faces(out, faces, [cbox, sbox] + ([wbox] if who else [])):
        raise SystemExit(f"{out}: お顔が文字と重なるか見切れています")


# B 数字・事実型(題名B): 型R系。右に 令和7年 愛子内親王殿下お誕生日のご近影の別カット A059(長辺1000px・左向き＝文字の側)
#   表紙A の A057 とは別の写真。お顔は検出器が横顔を拾わないため手で指定(元の写真で 中心 x385・y425・高さ約150px)
#   「7回のご感想」の下に小さな出典「雅子さまのお誕生日のご感想より」(7回のご感想は雅子さまのご感想。facts F4。数に入れない)
#   文字は2か所・21字: ①主語の表示「愛子さまが」(台詞ではない・かぎかっこなし。荒木指示 2026-11-25 で「愛子さま」→「愛子さまが」)＋「18歳から/24歳まで」(白・横書き) ②金「7回」＋のご感想
#   左下の小さな写真は、年が掲載ページで確認できる4枚(小さく表示するため長辺400pxでよい):
#     A037 令和元年12月のご近影(18歳)/A043 令和3年12月のご近影(成年)/A142 令和4年3月17日 ご成年の記者会見/A152 令和6年3月20日 学習院大学卒業式
r1(O + "thumb_B.png", A + "A059.jpg", (385 / 666, 425 / 1000, 150 / 1000), 205, (905, 300),
   [("愛子さまが", 76, 84), ("18歳から", 106, 192), ("24歳まで", 106, 302)],
   [("7回", 160, "gold", 458), ("のご感想", 64, "white", 452)],
   [(A + "A037.jpg", None, "令和元年"), (A + "A043.jpg", None, "令和3年"), (A + "A142.jpg", None, "令和4年"), (A + "A152.jpg", None, "令和6年")],
   "写真: 宮内庁 令和7年 お誕生日のご近影/左下: 令和元年・3年のご近影、令和4年 ご成年の記者会見、令和6年 大学卒業式",
   src=("雅子さまのお誕生日のご感想より", 27, 498))

# C 人物の物語型(題名C): 雅子さまお一人の写真 A021(令和6年 皇后陛下お誕生日のご近影・長辺1000px)を1枚・左寄せ(お顔は左1/3)。
#   右に縦書きで「生まれてきて/ありがとう」(平成14年4月2日 御誕生につき記者会見の原文の一部を一字一句)。右の行=白・左の行=金
#   文字は縦書き2行・11字＋かぎかっこ＋上の小さい一言「雅子さまから愛子さまへの思い」(横書き・かぎかっこなし＝当チャンネルの見出し。
#   荒木指示 2026-11-25 で「雅子さま」から替えた。金の行の上・白い行の左に右寄せ)＋小さい出典。上の帯は使わない
#   かぎかっこ内は原文の一部のまま。呼びかけ(「愛子、」など)は原文にないので足さない
#   言葉は平成14年・写真は令和6年なので、出典「愛子さまご誕生の会見より(平成14年4月)」とクレジット「令和6年」で年を分けて示す(年月は会見の日付。ご誕生は平成13年12月1日)
v1(O + "thumb_C.png", A + "A021.jpg", None, 245, (425, 305),
   (1196, 12, "生まれてきて", 98, "white", "﹁", None),
   (1044, 96, "ありがとう", 96, "gold", None, "﹂"),
   "愛子さまご誕生の会見より(平成14年4月)",
   "写真: 宮内庁 令和6年 皇后陛下お誕生日に際してのご近影(御所)", who=("雅子さまから愛子さまへの思い", 36, 44, 1126))

# 3枚を縮小して並べた一覧(ひと目で別の表紙に見えるかの確認用)
sheet = Image.new("RGB", (3 * 440 + 40, 248 + 20), (30, 30, 30))
for k, n in enumerate("ABC"):
    sheet.paste(Image.open(O + f"thumb_{n}.png").resize((440, 248), Image.LANCZOS), (10 + k * 450, 10))
sheet.save(O + "abc_overview.jpg", quality=90)
print(O + "abc_overview.jpg")
