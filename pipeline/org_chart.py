"""組織図と自動化の状況を docs/org_chart.png に描く。python -m pipeline.org_chart"""
from PIL import Image, ImageDraw, ImageFont

from .common import ROOT

F = '/usr/local/share/fonts/noto-sans-jp/NotoSansJP-'
fb = lambda s: ImageFont.truetype(F + 'Bold.ttf', s)
fr = lambda s: ImageFont.truetype(F + 'Regular.ttf', s)
NAVY, GOLD, WHITE, GRAY, LGRAY, CREAM, MID = (22, 36, 58), (216, 188, 114), (255, 255, 255), (150, 156, 168), (232, 234, 238), (250, 244, 226), (52, 70, 98)
STYLE = {'tool': (NAVY, WHITE, None), 'agent': (WHITE, NAVY, NAVY), 'plan': (CREAM, NAVY, GOLD), 'idle': (LGRAY, GRAY, GRAY),
         'human': (MID, WHITE, None), 'dept': (NAVY, WHITE, None), 'deptnew': (GOLD, NAVY, None), 'ext': (WHITE, NAVY, GRAY)}
DEPTS = [
    ('企画部', 'dept', [('棚調べ係', 'R1 ニュース収集（自動）', 'tool'), ('企画係', 'R1 最新の皇室の動向', 'agent'), ('企画係', 'R2 競合の伸びている動画', 'agent'), ('企画係', 'G0 題材確定・タイトル・概要', 'agent')]),
    ('制作部（まとめ：制作係）', 'dept', [('事実確認係', 'G1 facts.md', 'agent'), ('制作係', 'G2 写真収集：ページ選びを自動化', 'plan'),
                               ('台本係', 'G3 台本・場面設計（承認なし）', 'agent'), ('書き出し係', 'G4 音声・字幕・映像（自動）', 'tool'),
                               ('直し係', '検査の指摘を修正', 'agent'), ('画面割り係', '旧方式', 'idle'), ('デザイナー(通常)', '旧方式', 'idle')]),
    ('採点の係', 'dept', [('決まりの確認係', '本書で採点', 'agent'), ('当てっこ係', 'コマ点検＋主役位置の登録', 'plan'),
                      ('確認係', 'G5・G6 自動検査（自動）', 'tool'), ('通りすがり係', 'タイトル候補の順位', 'agent'), ('動画の確認係', '旧方式', 'idle')]),
    ('発信部', 'deptnew', [('タイトル係', 'G6① 承認済みタイトル／② 表紙3段', 'agent'), ('デザイナー(重要)', '表紙：Canva操作を手順化', 'plan'),
                        ('説明文係', 'G6③ 本文＋組立（自動）', 'agent'), ('ショート係', '旧方式', 'idle')]),
    ('分析部', 'dept', [('分析係', '公開後のCTR実測（vidIQ）', 'plan'), ('型の分析係', 'タイトル・表紙の型の見直し', 'agent')]),
]
EXT = [('VOICEVOX（青山龍星）', '自動で導入・起動 ✓', 'ext'), ('BGM UNL1337', '自動で取得 ✓', 'ext'), ('宮内庁サイト', '写真・記録 ✓', 'ext'),
       ('Canva', '表紙の作成 ✓', 'ext'), ('報道写真サイト・YouTube', '許可ドメイン未設定 ×', 'plan'), ('vidIQ', '残高0（11/22 8:55に補充）', 'plan')]
FLOW = [('R1 最新動向', 'agent'), ('R2 競合調査', 'agent'), ('G0 承認★', 'human'), ('G1 事実', 'agent'), ('G2 素材', 'plan'), ('G3 台本', 'agent'),
        ('G4 生成', 'tool'), ('G5 検査', 'tool'), ('G6 表紙・説明文', 'agent')]


def draw(path=ROOT / 'docs' / 'org_chart.png', date='2026-11-21'):
    W, H = 2600, 1760
    im = Image.new('RGB', (W, H), WHITE)
    d = ImageDraw.Draw(im)

    def box(x, y, w, h, title, sub=None, style='agent'):
        fill, fg, ol = STYLE[style]
        d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=fill, outline=ol, width=4 if ol else 0)
        f = fb(26 if style not in ('dept', 'deptnew', 'human') else 30)
        ty = y + (h - (40 if sub else 0)) / 2 - 19
        d.text((x + (w - d.textlength(title, font=f)) / 2, ty), title, fill=fg, font=f)
        if sub:
            f2 = fr(21)
            col = fg if style in ('tool', 'human') else (GRAY if style == 'idle' else (90, 100, 118))
            d.text((x + (w - d.textlength(sub, font=f2)) / 2, ty + 40), sub, fill=col, font=f2)

    d.text((60, 36), f'組織図と自動化の状況（{date} 時点）', fill=NAVY, font=fb(48))
    d.text((60, 104), '「全て自動」に向けて、各係が今どこまで自動で動くかを色で示しています', fill=GRAY, font=fr(26))
    lx = 60
    for st, label in [('tool', '道具で自動（完成）'), ('agent', 'Claudeの係が判断して実行'), ('plan', '改善予定（全自動化の残り）'),
                      ('human', '荒木さんの判断（G0承認・公開）'), ('idle', '現行の流れでは未使用')]:
        box(lx, 160, 60, 40, '', style=st)
        d.text((lx + 72, 164), label, fill=NAVY, font=fr(24))
        lx += 72 + d.textlength(label, font=fr(24)) + 50
    box(1000, 240, 600, 100, '荒木さん', '承認はG0（タイトルと概要）の1回だけ／公開の判断', style='human')
    box(1050, 375, 500, 80, 'メイン（/kabu 指揮）', style='dept')
    d.line([1300, 340, 1300, 375], fill=NAVY, width=4)
    n, colw, y0 = len(DEPTS), 460, 520
    gap = (W - 120 - colw * n) / (n - 1)
    d.line([60 + colw / 2, 490, W - 60 - colw / 2, 490], fill=NAVY, width=4)
    d.line([1300, 455, 1300, 490], fill=NAVY, width=4)
    for i, (name, st, members) in enumerate(DEPTS):
        x = 60 + i * (colw + gap)
        d.line([x + colw / 2, 490, x + colw / 2, y0], fill=NAVY, width=4)
        box(x, y0, colw, 76, name, style=st)
        y = y0 + 96
        for m, sub, ms in members:
            box(x + 18, y, colw - 36, 84, m, sub, style=ms)
            y += 100
    ey = 1400
    d.text((60, ey - 50), '外部とのつながり', fill=NAVY, font=fb(30))
    ex = 60
    for t, s, st in EXT:
        box(ex, ey, 400, 84, t, s, style=st)
        ex += 420
    fy = 1580
    d.text((60, fy - 50), '工程の流れ（★G0＝荒木さんがタイトルと概要を承認。以後は承認を求めず完成まで自動）', fill=NAVY, font=fb(30))
    sx, sw = 60, 250
    for k, (s, st) in enumerate(FLOW):
        box(sx, fy, sw, 80, s, style=st)
        if k < len(FLOW) - 1:
            d.polygon([(sx + sw + 8, fy + 30), (sx + sw + 26, fy + 40), (sx + sw + 8, fy + 50)], fill=NAVY)
        sx += sw + 33
    d.text((60, 1690), '全自動の判定条件：/kabu を1回実行し、★G0の承認1回以外に人やメインが手を入れずに完成まで流れること（通し試験）',
           fill=NAVY, font=fb(26))
    im.save(path)
    return path


if __name__ == '__main__':
    print(draw())
