"""Generate Akandel Website Builder preview thumbnails (wireframe SVGs)."""
import os
import sys

ROOT = sys.argv[1]
BUILDER = os.path.join(ROOT, 'static/src/img/builder')
SNIPPETS = os.path.join(ROOT, 'static/src/img/snippets_thumbs')
os.makedirs(BUILDER, exist_ok=True)
os.makedirs(SNIPPETS, exist_ok=True)

INK = '#17191B'
ACCENT = '#A9532F'
DEEP = '#1F3A37'
LINEN = '#F4EEE6'
WHITE = '#FFFFFF'
LINE = '#D9CFC3'
GREY = '#B9B2AA'
SAND = '#E6D9C9'


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def rect(self, x, y, w, h, fill, rx=0, stroke=None, op=None):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="1"'
        if op is not None:
            s += f' fill-opacity="{op}"'
        self.parts.append(s + '/>')
        return self

    def circle(self, cx, cy, r, fill, stroke=None):
        s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="1"'
        self.parts.append(s + '/>')
        return self

    def bars(self, x, y, n, w=12, gap=6, h=3, fill=GREY):
        for i in range(n):
            self.rect(x + i * (w + gap), y, w, h, fill, rx=1.5)
        return self

    def lines(self, x, y, n, w=24, gap=6, h=2.5, fill=GREY, shrink=0):
        for i in range(n):
            self.rect(x, y + i * gap, max(4, w - i * shrink), h, fill, rx=1.25)
        return self

    def logo(self, x, y, fill=INK, w=22):
        return self.rect(x, y, w, 6, fill, rx=1)

    def icons(self, x, y, n=3, fill=INK, gap=9):
        for i in range(n):
            self.circle(x + i * gap, y, 2.6, fill)
        return self

    def save(self, path):
        body = ''.join(self.parts)
        with open(path, 'w') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                    f'viewBox="0 0 {self.w} {self.h}">{body}</svg>\n')


# ---------------------------------------------------------------- headers
def header(name, draw):
    s = Svg(234, 60)
    s.rect(0.5, 4.5, 233, 51, WHITE, rx=3, stroke=LINE)
    draw(s)
    s.save(os.path.join(BUILDER, f'header_{name}.svg'))


header('essential', lambda s: (s.logo(12, 27), s.bars(78, 28.5, 5, w=11, gap=7), s.icons(196, 30)))
header('centered', lambda s: (s.rect(12, 18, 46, 8, LINEN, rx=4), s.logo(106, 19), s.icons(196, 22),
                               s.rect(0.5, 34, 233, 0.8, LINE), s.bars(64, 42, 5, w=14, gap=8)))
header('announce', lambda s: (s.rect(0.5, 4.5, 233, 13, INK, rx=3), s.rect(82, 10, 70, 2.5, WHITE, op=.8, rx=1),
                               s.logo(12, 31), s.bars(46, 32.5, 4, w=11, gap=7), s.icons(196, 34)))
header('category', lambda s: (s.logo(12, 17), s.rect(50, 14, 124, 12, LINEN, rx=6), s.rect(160, 14, 14, 12, ACCENT, rx=6),
                               s.icons(196, 20), s.rect(0.5, 36, 233, 19.5, DEEP), s.rect(10, 41, 30, 9, WHITE, op=.15),
                               s.bars(50, 44, 5, w=12, gap=8, fill=WHITE)))
header('promo', lambda s: (s.rect(0.5, 4.5, 233, 14, ACCENT, rx=3), s.rect(70, 10, 60, 3, WHITE, op=.9, rx=1),
                            s.rect(140, 8, 22, 7, WHITE, op=.0, rx=3.5), s.rect(140, 8, 22, 7, 'none', rx=3.5, stroke=WHITE),
                            s.bars(12, 35.5, 3, w=11, gap=6), s.logo(106, 34), s.icons(196, 37)))
header('minimal', lambda s: (s.rect(12, 26, 10, 1.6, INK), s.rect(12, 29.5, 10, 1.6, INK), s.rect(12, 33, 10, 1.6, INK),
                              s.logo(106, 27), s.icons(196, 30)))
header('split', lambda s: (s.bars(14, 28.5, 3, w=12, gap=7), s.logo(106, 27), s.bars(146, 28.5, 2, w=12, gap=7),
                            s.icons(196, 30)))
header('floating', lambda s: (s.rect(8, 16, 218, 28, WHITE, rx=14, stroke=LINE), s.logo(22, 27),
                               s.bars(80, 28.5, 4, w=11, gap=7), s.icons(188, 30)))
header('search', lambda s: (s.logo(12, 18), s.rect(62, 14, 110, 14, WHITE, rx=7, stroke=LINE), s.icons(192, 21),
                             s.rect(0.5, 36, 233, 0.8, LINE), s.bars(12, 44, 5, w=12, gap=7), s.rect(180, 44, 40, 3, GREY, rx=1.5)))
header('luxe', lambda s: (s.rect(0.5, 4.5, 233, 11, LINEN, rx=3), s.bars(10, 8.5, 3, w=14, gap=6),
                           s.circle(16, 25, 2.6, INK), s.logo(97, 21, w=40), s.icons(196, 25), s.rect(0.5, 33, 233, 0.8, LINE),
                           s.bars(58, 42, 5, w=16, gap=8)))
header('bold', lambda s: (s.logo(12, 27, w=26), s.bars(50, 28, 4, w=14, gap=8, h=4, fill=INK),
                           s.rect(150, 23, 36, 14, LINEN, rx=7), s.icons(158, 30, 3, gap=10), s.rect(192, 23, 32, 14, ACCENT, rx=7)))
header('utility', lambda s: (s.rect(0.5, 4.5, 233, 12, LINEN, rx=3), s.rect(10, 9, 40, 2.5, GREY, rx=1), s.bars(140, 9, 3, w=18, gap=6),
                              s.logo(12, 31), s.bars(46, 32.5, 4, w=11, gap=6), s.rect(132, 29, 42, 9, LINEN, rx=4.5), s.icons(192, 33.5)))
header('stacked', lambda s: (s.logo(12, 16), s.rect(40, 14.5, 0.8, 10, LINE), s.lines(46, 16, 2, w=34, gap=4.5),
                              s.circle(176, 18, 2.6, INK), s.circle(192, 18, 2.6, INK), s.circle(208, 18, 2.6, INK),
                              s.bars(170, 24, 3, w=12, gap=4, h=2),
                              s.rect(0.5, 34, 233, 0.8, LINE), s.bars(12, 43, 5, w=13, gap=8), s.rect(12, 47.5, 13, 1.5, ACCENT)))


# ---------------------------------------------------------------- mobile
def mobile(name, draw):
    s = Svg(96, 64)
    s.rect(18, 2, 60, 60, LINEN, rx=8)
    s.rect(20.5, 4.5, 55, 55, WHITE, rx=6)
    draw(s)
    s.save(os.path.join(BUILDER, f'mobile_{name}.svg'))


def topbar(s, y=8, logo_x=25, burger_x=66, icons_x=None, fill=WHITE):
    s.rect(20.5, y - 3.5, 55, 11, fill, rx=0)
    s.logo(logo_x, y, w=14)
    if icons_x:
        s.circle(icons_x, y + 3, 1.8, INK)
    s.rect(burger_x, y + 1, 6, 1.2, INK)
    s.rect(burger_x, y + 3, 6, 1.2, INK)
    s.rect(burger_x, y + 5, 6, 1.2, INK)


def drawer(s, x=40, w=35.5, fill=WHITE, text=GREY, side='right'):
    s.rect(20.5, 15, 55, 44.5, INK, op=.25)
    s.rect(x, 15, w, 44.5, fill)
    s.lines(x + 4, 21, 5, w=w - 12, gap=6, fill=text)


mobile('refined', lambda s: (topbar(s, icons_x=58), drawer(s)))
mobile('centered', lambda s: (s.rect(25, 9, 6, 1.2, INK), s.rect(25, 11, 6, 1.2, INK), s.rect(25, 13, 6, 1.2, INK),
                              s.logo(41, 8, w=14), s.circle(64, 11, 1.8, INK), s.circle(70, 11, 1.8, INK),
                              s.rect(20.5, 18, 55, 41.5, LINEN, op=.6)))
mobile('drawer', lambda s: (topbar(s), s.rect(20.5, 15, 55, 44.5, INK, op=.25), s.rect(20.5, 15, 36, 44.5, WHITE),
                            s.lines(24, 20, 3, w=24, gap=5), s.rect(24, 37, 10, 2, ACCENT, rx=1),
                            s.bars(24, 42, 2, w=12, gap=4, h=6, fill=LINEN), s.bars(24, 50, 2, w=12, gap=4, h=6, fill=LINEN)))
mobile('fullscreen', lambda s: (s.rect(20.5, 4.5, 55, 55, WHITE, rx=6), s.lines(27, 16, 4, w=34, gap=9, h=4.5, fill=INK, shrink=4),
                                s.circle(68, 10, 2.5, 'none', stroke=INK)))
mobile('sheet', lambda s: (topbar(s), s.rect(20.5, 15, 55, 44.5, INK, op=.25), s.rect(20.5, 30, 55, 29.5, WHITE, rx=6),
                           s.rect(42, 33, 12, 1.6, GREY, rx=.8), s.lines(26, 39, 3, w=40, gap=6)))
mobile('tabbar', lambda s: (topbar(s), s.rect(20.5, 18, 55, 30, LINEN, op=.6), s.rect(20.5, 50, 55, 9.5, WHITE),
                            s.rect(20.5, 50, 55, .6, LINE), s.icons(27, 55, 5, fill=GREY, gap=10.5), s.circle(48, 55, 2.6, ACCENT)))
mobile('search', lambda s: (topbar(s), s.rect(24, 17, 48, 7, LINEN, rx=3.5), s.rect(20.5, 28, 55, 31.5, LINEN, op=.4)))
mobile('compact', lambda s: (s.logo(25, 7, w=10), s.circle(61, 9, 1.6, INK), s.rect(66, 8, 5, 1, INK), s.rect(66, 10, 5, 1, INK),
                             s.rect(20.5, 13, 55, .6, LINE), s.rect(20.5, 14, 55, 45.5, LINEN, op=.5)))
mobile('promo', lambda s: (s.rect(20.5, 4.5, 55, 7, ACCENT), s.rect(33, 7, 30, 1.6, WHITE, rx=.8), topbar(s, y=15),
                           s.rect(20.5, 25, 55, 34.5, LINEN, op=.5)))
mobile('dark', lambda s: (topbar(s), drawer(s, fill=INK, text='#5B5F63')))
mobile('floating', lambda s: (s.rect(20.5, 4.5, 55, 55, LINEN, rx=6), s.rect(24, 8, 48, 11, WHITE, rx=5, stroke=LINE),
                              s.logo(28, 11, w=12), s.circle(58, 13.5, 1.8, INK), s.rect(63, 12, 5, 1.1, INK),
                              s.rect(63, 14, 5, 1.1, INK)))
mobile('chips', lambda s: (topbar(s), s.rect(24, 18, 14, 6, WHITE, rx=3, stroke=LINE), s.rect(40, 18, 16, 6, WHITE, rx=3, stroke=LINE),
                           s.rect(58, 18, 16, 6, WHITE, rx=3, stroke=LINE), s.rect(20.5, 28, 55, 31.5, LINEN, op=.5)))


# ---------------------------------------------------------------- footers
def footer(name, draw, bg=LINEN):
    s = Svg(234, 60)
    s.rect(0.5, 4.5, 233, 51, bg, rx=3, stroke=LINE)
    draw(s)
    s.save(os.path.join(BUILDER, f'footer_{name}.svg'))


def columns(s, x, y, n, gap=34, fill=GREY, head=INK):
    for i in range(n):
        s.rect(x + i * gap, y, 16, 2.5, head, rx=1)
        s.lines(x + i * gap, y + 7, 3, w=20, gap=5, fill=fill)


footer('columns', lambda s: (s.logo(12, 14), s.lines(12, 24, 3, w=40, gap=5), s.icons(14, 44, 3, gap=8),
                             columns(s, 72, 14, 2), s.rect(150, 14, 30, 2.5, INK, rx=1), s.rect(150, 22, 72, 10, WHITE, rx=5),
                             s.rect(198, 23.5, 22, 7, ACCENT, rx=3.5)))
footer('newsletter', lambda s: (s.rect(0.5, 4.5, 233, 22, ACCENT, rx=3), s.rect(12, 11, 60, 3.5, WHITE, rx=1),
                                s.rect(130, 9.5, 92, 11, WHITE, rx=5.5), s.rect(196, 11, 24, 8, INK, rx=4),
                                columns(s, 12, 32, 4, gap=56)))
footer('centered', lambda s: (s.logo(102, 14, w=30), s.rect(87, 24, 60, 2.5, GREY, rx=1), s.bars(70, 33, 5, w=14, gap=6),
                              s.icons(105, 44, 4, gap=8)))
footer('minimal', lambda s: (s.logo(12, 27), s.bars(78, 28.5, 4, w=14, gap=8), s.icons(196, 30, 3, gap=9)))
footer('mega', lambda s: (s.logo(10, 12), s.lines(10, 22, 2, w=36, gap=5), s.rect(10, 38, 16, 7, INK, rx=2), s.rect(29, 38, 16, 7, INK, rx=2),
                          columns(s, 62, 12, 5, gap=34)))
footer('trust', lambda s: ([(s.circle(20 + i * 56, 15, 4, 'none', stroke=ACCENT), s.lines(28 + i * 56, 13, 2, w=24, gap=4))
                            for i in range(4)], s.rect(0.5, 26, 233, .8, LINE), s.logo(12, 34), columns(s, 120, 34, 3, gap=36)))
footer('statement', lambda s: (s.rect(14, 13, 140, 7, WHITE, rx=1.5), s.rect(14, 24, 96, 7, ACCENT, rx=1.5),
                               s.rect(14, 40, 70, 9, WHITE, op=.2, rx=4.5), s.bars(140, 43, 4, w=14, gap=6, fill='#6B6F73')), )
footer('contact', lambda s: (columns(s, 14, 14, 3, gap=76), s.circle(176, 44, 2.5, INK), s.circle(185, 44, 2.5, INK)))
footer('split', lambda s: (s.rect(0.5, 4.5, 90, 51, ACCENT, rx=3), s.logo(10, 14, fill=WHITE, w=28), s.lines(10, 25, 2, w=60, gap=5, fill=WHITE),
                           s.rect(10, 38, 68, 9, WHITE, rx=4.5), columns(s, 104, 14, 3, gap=42)))
footer('payments', lambda s: (s.logo(12, 12), s.lines(12, 22, 2, w=44, gap=5), columns(s, 110, 12, 3, gap=40),
                              s.rect(0.5, 40, 233, .8, LINE), s.rect(12, 46, 40, 2.5, GREY, rx=1),
                              [s.rect(150 + i * 15, 44, 12, 7, INK if i % 2 else DEEP, rx=1.5) for i in range(5)]))
footer('gallery', lambda s: ([s.rect(10 + i * 36, 10, 33, 24, SAND if i % 2 else GREY, rx=2) for i in range(6)],
                             s.logo(12, 42), s.bars(110, 43.5, 5, w=14, gap=6)))
footer('cards', lambda s: ([(s.rect(10 + i * 72, 10, 68, 30, WHITE, rx=4, stroke=LINE), s.circle(18 + i * 72, 18, 3, ACCENT),
                             s.lines(16 + i * 72, 26, 2, w=44, gap=5)) for i in range(3)], s.logo(12, 46), s.icons(196, 49)))

# Dark variant background for the statement footer
s = Svg(234, 60)
s.rect(0.5, 4.5, 233, 51, INK, rx=3)
s.rect(14, 13, 140, 7, WHITE, rx=1.5)
s.rect(14, 24, 96, 7, ACCENT, rx=1.5)
s.rect(14, 40, 70, 9, WHITE, op=.2, rx=4.5)
s.bars(140, 43, 4, w=14, gap=6, fill='#6B6F73')
s.save(os.path.join(BUILDER, 'footer_statement.svg'))


# ---------------------------------------------------------------- snippets
def snip(name, draw, bg=WHITE):
    s = Svg(140, 60)
    s.rect(0, 0, 140, 60, bg)
    draw(s)
    s.save(os.path.join(SNIPPETS, f'{name}.svg'))


snip('s_ak_hero_split', lambda s: (s.rect(10, 14, 22, 2, ACCENT), s.rect(10, 20, 52, 6, INK, rx=1), s.rect(10, 29, 40, 6, INK, rx=1),
                                   s.lines(10, 40, 2, w=50, gap=4), s.rect(10, 49, 22, 6, ACCENT, rx=3), s.rect(35, 49, 20, 6, 'none', rx=3, stroke=INK),
                                   s.rect(78, 6, 52, 48, SAND, rx=4), s.rect(82, 42, 26, 8, WHITE, rx=2)), bg=LINEN)
snip('s_ak_hero_cover', lambda s: (s.rect(0, 0, 140, 60, DEEP), s.rect(0, 30, 140, 30, INK, op=.4), s.rect(56, 14, 28, 2, WHITE, op=.7),
                                   s.rect(30, 20, 80, 7, WHITE, rx=1), s.rect(45, 32, 50, 2.5, WHITE, op=.7), s.rect(56, 42, 28, 7, WHITE, rx=3.5)))
snip('s_ak_hero_editorial', lambda s: (s.rect(8, 6, 70, 7, INK, rx=1), s.rect(8, 15, 50, 7, INK, rx=1), s.lines(92, 8, 3, w=40, gap=4),
                                       s.rect(8, 28, 62, 28, SAND, rx=3), s.rect(73, 28, 29, 28, GREY, rx=3), s.rect(105, 28, 27, 28, LINEN, rx=3)))
snip('s_ak_hero_framed', lambda s: (s.rect(6, 6, 128, 48, ACCENT, op=.55, rx=4), s.rect(14, 24, 52, 24, WHITE, rx=3),
                                    s.rect(18, 29, 36, 4, INK, rx=1), s.lines(18, 36, 2, w=40, gap=4), s.rect(18, 42, 16, 4, ACCENT, rx=2)))
snip('s_ak_campaign_banner', lambda s: (s.rect(0, 0, 140, 60, INK), s.rect(70, 0, 70, 60, SAND, op=.35), s.rect(12, 16, 20, 2, WHITE, op=.7),
                                        s.rect(12, 22, 58, 7, WHITE, rx=1), s.rect(12, 33, 44, 2.5, WHITE, op=.6),
                                        s.rect(12, 42, 22, 7, WHITE, rx=3.5), s.rect(37, 42, 22, 7, 'none', rx=3.5, stroke=WHITE)))
snip('s_ak_promo_strip', lambda s: (s.rect(0, 20, 140, 20, ACCENT), s.rect(30, 28.5, 54, 3, WHITE, rx=1.5),
                                    s.rect(88, 26, 22, 8, 'none', rx=2, stroke=WHITE)))
snip('s_ak_promo_marquee', lambda s: (s.rect(0, 20, 140, 20, INK), [s.rect(6 + i * 34, 28.5, 22, 3, WHITE, rx=1.5) for i in range(4)],
                                      [s.circle(31 + i * 34, 30, 1.5, ACCENT) for i in range(4)]))
snip('s_ak_promo_tiles', lambda s: ([(s.rect(6 + i * 44, 12, 40, 36, c, rx=4), s.rect(11 + i * 44, 22, 22, 7, WHITE if c != LINEN else INK, rx=1),
                                      s.rect(11 + i * 44, 36, 18, 2.5, WHITE if c != LINEN else INK, op=.7))
                                     for i, c in enumerate([ACCENT, LINEN, INK])]))
snip('s_ak_categories_grid', lambda s: (s.rect(8, 8, 40, 4, INK, rx=1), [(s.rect(8 + i * 32, 18, 28, 34, SAND, rx=3),
                                         s.rect(11 + i * 32, 44, 16, 5, WHITE, rx=2.5)) for i in range(4)]))
snip('s_ak_categories_bento', lambda s: (s.rect(8, 6, 60, 48, GREY, rx=3), s.rect(72, 6, 60, 22, SAND, rx=3), s.rect(72, 32, 28, 22, LINEN, rx=3),
                                         s.rect(104, 32, 28, 22, SAND, rx=3), s.rect(12, 44, 30, 4, WHITE, rx=1)), bg=LINEN)
snip('s_ak_categories_circles', lambda s: (s.rect(50, 8, 40, 4, INK, rx=1), [(s.circle(16 + i * 22, 32, 9, SAND if i % 2 else GREY),
                                           s.rect(10 + i * 22, 45, 12, 2.5, INK, rx=1)) for i in range(6)]))


def products(s, design):
    s.rect(8, 6, 16, 2, ACCENT)
    s.rect(8, 11, 44, 5, INK, rx=1)
    s.rect(112, 12, 20, 2.5, INK, rx=1)
    for i in range(4):
        x = 8 + i * 32
        if design == 'cards':
            s.rect(x, 22, 29, 34, WHITE, rx=3, stroke=LINE)
            s.rect(x + 2, 24, 25, 18, SAND, rx=2)
        else:
            s.rect(x, 22, 29, 22, SAND if i % 2 else LINEN, rx=3)
        s.rect(x, 46 if design != 'cards' else 45, 20, 2.5, INK, rx=1)
        s.rect(x, 51 if design != 'cards' else 50, 12, 2.5, ACCENT, rx=1)


snip('s_ak_products_new', lambda s: products(s, 'thumbs'))
snip('s_ak_products_best', lambda s: products(s, 'cards'), bg=LINEN)
snip('s_ak_products_viewed', lambda s: products(s, 'condensed'))
snip('s_ak_product_spotlight', lambda s: (s.rect(8, 6, 56, 48, SAND, rx=4), s.rect(76, 10, 18, 2, ACCENT), s.rect(76, 16, 50, 6, INK, rx=1),
                                          [s.circle(78 + i * 5, 27, 1.6, '#E0A526') for i in range(5)], s.lines(76, 33, 3, w=50, gap=4),
                                          s.rect(76, 47, 22, 6, ACCENT, rx=3), s.rect(102, 48.5, 16, 3, INK, rx=1)), bg=LINEN)
snip('s_ak_collection_duo', lambda s: ([(s.rect(6 + i * 66, 8, 62, 44, SAND if i else GREY, rx=4), s.rect(12 + i * 66, 34, 30, 5, WHITE, rx=1),
                                         s.rect(12 + i * 66, 42, 20, 2.5, WHITE, op=.8)) for i in range(2)]))
snip('s_ak_collection_trio', lambda s: (s.rect(50, 4, 40, 4, INK, rx=1), [(s.rect(10 + i * 42, 12, 36, 34, SAND if i % 2 else GREY, rx=3),
                                         s.rect(10 + i * 42, 49, 24, 3, INK, rx=1), s.rect(10 + i * 42, 54, 30, 2, GREY)) for i in range(3)]), bg=LINEN)
snip('s_ak_shop_the_look', lambda s: (s.rect(8, 6, 66, 48, SAND, rx=4), [s.circle(x, y, 3, WHITE) for x, y in ((30, 30), (52, 22), (62, 44))],
                                      [s.circle(x, y, 1.3, ACCENT) for x, y in ((30, 30), (52, 22), (62, 44))],
                                      s.rect(82, 10, 40, 5, INK, rx=1), [s.rect(82, 22 + i * 7, 48, .7, LINE) for i in range(4)],
                                      s.lines(82, 18, 4, w=30, gap=7), s.rect(82, 48, 26, 6, ACCENT, rx=3)), bg=LINEN)
snip('s_ak_story_split', lambda s: (s.rect(8, 6, 44, 48, SAND, rx=4), s.rect(62, 8, 16, 2, ACCENT), s.rect(62, 14, 66, 5, INK, rx=1),
                                    s.rect(62, 21, 50, 5, INK, rx=1), s.lines(62, 31, 2, w=66, gap=4),
                                    [s.rect(62 + i * 24, 44, 14, 5, ACCENT, rx=1) for i in range(3)]))
snip('s_ak_story_values', lambda s: (s.rect(8, 8, 50, 6, INK, rx=1), [(s.rect(8 + i * 32, 24, 28, .8, LINE), s.rect(8 + i * 32, 28, 8, 3, ACCENT, rx=1),
                                     s.rect(8 + i * 32, 35, 22, 3, INK, rx=1), s.lines(8 + i * 32, 41, 2, w=26, gap=4)) for i in range(4)]), bg=LINEN)
snip('s_ak_benefits_bar', lambda s: (s.rect(0, 18, 140, .8, LINE), s.rect(0, 42, 140, .8, LINE),
                                     [(s.circle(14 + i * 34, 30, 5, SAND), s.rect(22 + i * 34, 27, 14, 2.5, INK, rx=1),
                                       s.rect(22 + i * 34, 32, 10, 2, GREY)) for i in range(4)]))
snip('s_ak_benefits_cards', lambda s: (s.rect(50, 4, 40, 4, INK, rx=1), [(s.rect(6 + i * 33, 14, 30, 40, WHITE, rx=3, stroke=LINE),
                                       s.circle(14 + i * 33, 22, 4, SAND), s.rect(10 + i * 33, 32, 18, 2.5, INK, rx=1),
                                       s.lines(10 + i * 33, 38, 3, w=22, gap=4)) for i in range(4)]), bg=LINEN)
snip('s_ak_press', lambda s: (s.rect(55, 14, 30, 2, ACCENT), [s.rect(8 + i * 26, 28, 20, 5, GREY, rx=1) for i in range(5)]))
snip('s_ak_testimonials_grid', lambda s: (s.rect(8, 6, 50, 5, INK, rx=1), [(s.rect(8 + i * 42, 16, 38, 38, WHITE, rx=3, stroke=LINE),
                                          [s.circle(13 + i * 42 + j * 4, 22, 1.4, '#E0A526') for j in range(5)],
                                          s.lines(12 + i * 42, 28, 3, w=30, gap=4), s.circle(15 + i * 42, 47, 3, ACCENT),
                                          s.rect(21 + i * 42, 46, 14, 2.5, INK, rx=1)) for i in range(3)]), bg=LINEN)
snip('s_ak_testimonial_feature', lambda s: (s.rect(0, 0, 140, 60, INK), s.rect(10, 10, 6, 5, ACCENT, rx=1), s.rect(10, 20, 74, 5, WHITE, rx=1),
                                            s.rect(10, 28, 64, 5, WHITE, rx=1), s.rect(10, 40, 30, 2.5, WHITE, op=.6),
                                            s.rect(98, 8, 32, 44, SAND, rx=4)))
snip('s_ak_newsletter_band', lambda s: (s.rect(0, 0, 140, 60, ACCENT), s.rect(52, 10, 36, 2, WHITE, op=.7), s.rect(32, 16, 76, 6, WHITE, rx=1),
                                        s.rect(40, 26, 60, 2.5, WHITE, op=.7), s.rect(34, 35, 72, 11, WHITE, rx=5.5), s.rect(82, 37, 22, 7, INK, rx=3.5)))
snip('s_ak_newsletter_split', lambda s: (s.rect(0, 0, 70, 60, SAND), s.rect(80, 14, 20, 2, ACCENT), s.rect(80, 20, 50, 5, INK, rx=1),
                                         s.lines(80, 30, 2, w=48, gap=4), s.rect(80, 42, 52, 9, WHITE, rx=4.5, stroke=LINE),
                                         s.rect(114, 43.5, 16, 6, ACCENT, rx=3)), bg=LINEN)
snip('s_ak_lookbook', lambda s: (s.rect(8, 6, 46, 4, INK, rx=1), s.rect(8, 14, 50, 42, GREY, rx=3), s.rect(62, 14, 70, 20, SAND, rx=3),
                                 s.rect(62, 37, 34, 19, LINEN, rx=3), s.rect(99, 37, 33, 19, SAND, rx=3), s.rect(12, 49, 22, 4, WHITE, rx=2)))
snip('s_ak_journal', lambda s: (s.rect(8, 4, 40, 4, INK, rx=1), [(s.rect(8 + i * 43, 12, 38, 24, SAND if i % 2 else GREY, rx=3),
                                 s.rect(8 + i * 43, 39, 16, 2, ACCENT), s.lines(8 + i * 43, 44, 2, w=34, gap=4, fill=INK),
                                 s.rect(8 + i * 43, 53, 26, 2, GREY)) for i in range(3)]))
snip('s_ak_delivery_info', lambda s: (s.rect(8, 10, 16, 2, ACCENT), s.rect(8, 16, 34, 5, INK, rx=1), s.lines(8, 26, 2, w=36, gap=4),
                                      s.rect(8, 38, 26, 7, 'none', rx=3.5, stroke=ACCENT),
                                      [(s.rect(56, 10 + i * 11, 76, .8, LINE), s.rect(56, 14 + i * 11, 44, 3, INK, rx=1),
                                        s.rect(127, 14 + i * 11, 4, 3, ACCENT, rx=1)) for i in range(4)]))

# Snippet group thumbnails
snip('group_ak_intro', lambda s: (s.rect(0, 0, 140, 60, LINEN), s.rect(10, 14, 50, 6, INK, rx=1), s.rect(10, 24, 36, 6, INK, rx=1),
                                  s.rect(10, 38, 22, 7, ACCENT, rx=3.5), s.rect(76, 6, 56, 48, SAND, rx=4)))
snip('group_ak_shop', lambda s: products(s, 'thumbs'))
snip('group_ak_story', lambda s: (s.rect(8, 6, 44, 48, SAND, rx=4), [s.circle(66 + i * 5, 14, 1.6, '#E0A526') for i in range(5)],
                                  s.rect(62, 20, 66, 5, INK, rx=1), s.rect(62, 27, 50, 5, INK, rx=1), s.lines(62, 37, 2, w=66, gap=4),
                                  s.circle(66, 50, 3, ACCENT), s.rect(72, 49, 20, 2.5, INK, rx=1)), bg=LINEN)

print(len(os.listdir(BUILDER)), 'builder thumbs;', len(os.listdir(SNIPPETS)), 'snippet thumbs')
