import json, os, sys
ROOT = sys.argv[1]
B = os.path.join(ROOT, 'static/src/img/builder'); SN = os.path.join(ROOT, 'static/src/img/snippets_thumbs')
INK, BLUE, GOLD, LIGHT, WHITE, LINE, GREY = '#142033', '#1570CC', '#C48A1C', '#F3F6FA', '#FFFFFF', '#D8DEE8', '#AEB6C4'

class Svg:
    def __init__(s, w, h): s.w, s.h, s.p = w, h, []
    def r(s, x, y, w, h, f, rx=0, st=None, op=None):
        a = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}"'
        if st: a += f' stroke="{st}"'
        if op is not None: a += f' fill-opacity="{op}"'
        s.p.append(a + '/>'); return s
    def c(s, x, y, rad, f, st=None):
        s.p.append(f'<circle cx="{x}" cy="{y}" r="{rad}" fill="{f}"' + (f' stroke="{st}"' if st else '') + '/>'); return s
    def bars(s, x, y, n, w=12, g=6, h=3, f=GREY):
        for i in range(n): s.r(x + i * (w + g), y, w, h, f, 1.5)
        return s
    def save(s, path):
        open(path, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h}" viewBox="0 0 {s.w} {s.h}">' + ''.join(s.p) + '</svg>\n')

def head(name, bg=WHITE, nav=GREY, icons=INK, extra=None, logo=INK):
    s = Svg(234, 60); s.r(.5, 4.5, 233, 51, bg, 3, LINE)
    if extra: extra(s)
    s.r(12, 27, 22, 6, logo, 1); s.bars(84, 28.5, 4, 12, 7, 3, nav)
    for i in range(3): s.c(192 + i * 10, 30, 2.6, icons)
    s.save(os.path.join(B, f'header_{name}.svg'))

head('pill', extra=lambda s: s.r(76, 22, 78, 16, LIGHT, 8))
head('transparent', bg='#9FB3C8', nav=WHITE, icons=WHITE, logo=WHITE)
head('dark', bg=INK, nav='#8A96AA', icons=WHITE, logo=WHITE)
head('brand', bg=BLUE, nav='#CFE1F5', icons=WHITE, logo=WHITE)
s = Svg(234, 60); s.r(.5, 4.5, 233, 51, WHITE, 3, LINE); s.r(12, 27, 22, 6, INK, 1); s.bars(44, 28.5, 4, 11, 6); s.r(128, 23, 50, 14, LIGHT, 7)
[s.c(192 + i * 10, 30, 2.6, INK) for i in range(3)]; s.save(os.path.join(B, 'header_searchpill.svg'))
head('contact', extra=lambda s: (s.r(.5, 4.5, 233, 11, LIGHT, 3), s.bars(10, 8.5, 3, 26, 8, 2.5)))
head('chips', extra=lambda s: (s.r(.5, 40, 233, .8, LINE), [s.r(12 + i * 30, 44, 26, 7, LIGHT, 3.5) for i in range(6)]))
head('boxed', extra=lambda s: s.r(6, 16, 222, 28, LIGHT, 8, LINE))
head('caps', extra=lambda s: s.r(.5, 52, 233, 3, BLUE))
s = Svg(234, 60); s.r(.5, 4.5, 233, 51, WHITE, 3, LINE); s.r(12, 27, 22, 6, INK, 1); s.bars(44, 28.5, 4, 11, 6)
s.r(150, 24, 26, 12, WHITE, 6, BLUE); s.r(180, 24, 26, 12, BLUE, 6); [s.c(214 + i * 8, 30, 2.2, INK) for i in range(2)]; s.save(os.path.join(B, 'header_duo.svg'))
s = Svg(234, 60); s.r(.5, 18, 233, 24, WHITE, 3, LINE); s.r(12, 27, 18, 5, INK, 1); s.bars(120, 28.5, 4, 10, 6); [s.c(196 + i * 9, 30, 2.2, INK) for i in range(3)]; s.save(os.path.join(B, 'header_slim.svg'))

def mob(name, bar=WHITE, drawer=None, side='right', icons=INK, extra=None):
    s = Svg(96, 64); s.r(18, 2, 60, 60, LIGHT, 8); s.r(20.5, 4.5, 55, 55, WHITE, 6)
    s.r(20.5, 4.5, 55, 11, bar, 0); s.r(25, 8, 14, 5, icons, 1); s.c(60, 10, 1.8, icons); s.r(65, 8, 6, 1.2, icons); s.r(65, 10.2, 6, 1.2, icons); s.r(65, 12.4, 6, 1.2, icons)
    if drawer:
        s.r(20.5, 15.5, 55, 44, INK, op=.25); x = 20.5 if side == 'left' else 40
        if side == 'bottom': s.r(20.5, 32, 55, 27.5, drawer, 6); [s.r(26, 38 + i * 6, 40, 2.5, GREY, 1) for i in range(3)]
        else: s.r(x, 15.5, 35.5, 44, drawer); [s.r(x + 4, 21 + i * 6, 24, 2.5, GREY, 1) for i in range(5)]
    if extra: extra(s)
    s.save(os.path.join(B, f'mobile_{name}.svg'))

mob('brand', bar=BLUE, icons=WHITE); mob('darkbar', bar=INK, icons=WHITE); mob('glass', bar='#E7EDF5')
mob('bordered', extra=lambda s: s.r(20.5, 15.5, 55, 1.5, BLUE)); mob('gold', extra=lambda s: s.r(20.5, 15.5, 55, 1.2, GOLD))
mob('rounded', drawer=WHITE, extra=lambda s: s.r(42, 17, 32, 40, WHITE, 5, LINE)); mob('bigtype', drawer=WHITE, extra=lambda s: [s.r(44, 20 + i * 9, 26, 5, INK, 1) for i in range(4)])
mob('iconpills', extra=lambda s: (s.c(54, 10, 3.5, LIGHT), s.c(60, 10, 1.8, INK))); mob('leftdark', drawer=INK, side='left')
mob('sheetdark', drawer=INK, side='bottom'); mob('cards', drawer=WHITE, extra=lambda s: [s.r(43, 19 + i * 9, 30, 7, LIGHT, 2, LINE) for i in range(4)]); mob('clean')

def foot(name, draw, bg=INK):
    s = Svg(234, 60); s.r(.5, 4.5, 233, 51, bg, 3, LINE); draw(s); s.save(os.path.join(B, f'footer_{name}.svg'))

def cols(s, x, y, n, g=36, f='#6C7891', h=WHITE):
    for i in range(n): s.r(x + i * g, y, 16, 2.5, h, 1); [s.r(x + i * g, y + 7 + k * 5, 20, 2, f, 1) for k in range(3)]

foot('app', lambda s: (s.r(8, 9, 218, 18, '#22324D', 4), s.r(14, 15, 70, 4, WHITE, 1), s.r(170, 13, 22, 8, WHITE, 2), s.r(196, 13, 22, 8, WHITE, 2), cols(s, 14, 34, 4, 52)))
foot('darkcols', lambda s: (s.r(12, 14, 30, 5, WHITE, 1), cols(s, 80, 14, 2), s.r(156, 14, 30, 2.5, WHITE, 1), s.r(156, 22, 66, 9, WHITE, 4.5), s.r(200, 23.5, 20, 6, BLUE, 3)))
foot('bigbrand', lambda s: (s.bars(70, 12, 5, 14, 6, 2.5, '#6C7891'), s.r(20, 28, 194, 20, '#22324D', 2)))
foot('twotone', lambda s: (s.r(.5, 4.5, 233, 20, LIGHT, 3), s.r(10, 12, 70, 5, INK, 1), s.r(170, 10, 26, 8, BLUE, 4), s.r(200, 10, 26, 8, WHITE, 4, BLUE), cols(s, 12, 32, 4, 52)))
foot('support', lambda s: ([(s.r(10 + i * 72, 10, 68, 20, '#22324D', 4), s.c(20 + i * 72, 20, 5, BLUE)) for i in range(3)], s.r(12, 42, 26, 4, WHITE, 1), s.bars(90, 43, 4, 14, 6, 2.5, '#6C7891')))
foot('newsleft', lambda s: (s.r(12, 12, 50, 5, WHITE, 1), s.r(12, 24, 76, 10, WHITE, 5), s.r(66, 25.5, 20, 7, BLUE, 3.5), cols(s, 112, 12, 3, 38)))
foot('wave', lambda s: (s.p.append('<path d="M0.5 4.5 Q117 26 233.5 4.5 Z" fill="#FFFFFF"/>'), s.r(12, 26, 30, 5, WHITE, 1), cols(s, 100, 26, 3, 40)))
foot('linkgrid', lambda s: cols(s, 10, 14, 6, 37))
foot('socialband', lambda s: (s.r(80, 10, 74, 5, WHITE, 1), [s.c(87 + i * 15, 26, 5, '#22324D', '#6C7891') for i in range(5)], s.r(.5, 36, 233, .8, '#2E3E5A'), s.r(12, 44, 26, 4, WHITE, 1), s.bars(150, 45, 3, 14, 6, 2.5, '#6C7891')))
foot('categories', lambda s: (s.r(12, 12, 30, 5, WHITE, 1), s.r(12, 24, 66, 9, WHITE, 4.5), [s.r(110 + (i % 2) * 40, 12 + (i // 2) * 7, 30, 2.5, '#6C7891', 1) for i in range(8)], cols(s, 196, 12, 1)))
foot('compactdark', lambda s: (s.r(12, 28, 28, 5, WHITE, 1), s.bars(80, 29, 4, 14, 7, 2.5, '#6C7891'), [s.c(190 + i * 10, 30, 3, '#22324D', '#6C7891') for i in range(3)]))
foot('brandcta', lambda s: (s.r(10, 9, 214, 18, BLUE, 5), s.r(18, 15, 70, 5, WHITE, 1), s.r(186, 13, 30, 9, WHITE, 4.5), cols(s, 14, 34, 4, 52)))

def snip(name, draw, w=140, h=60, bg=WHITE):
    s = Svg(w, h); s.r(0, 0, w, h, bg); draw(s); s.save(os.path.join(SN, name))

snip('group_ak_hero.svg', lambda s: (s.r(10, 14, 20, 2, GOLD), s.r(10, 20, 54, 6, INK, 1), s.r(10, 29, 40, 6, GOLD, 1), s.r(10, 42, 24, 7, BLUE, 3.5), s.r(76, 8, 54, 44, '#DCE6F2', 6), s.c(66, 54, 1.6, BLUE), s.c(71, 54, 1.6, GREY), s.c(76, 54, 1.6, GREY)), bg=LIGHT)
snip('group_ak_categories.svg', lambda s: [ (s.c(18 + i * 21, 26, 8, '#F1E4CB' if i % 2 else '#DCE6F2'), s.r(11 + i * 21, 40, 14, 2.5, INK, 1)) for i in range(6)])
snip('group_ak_products.svg', lambda s: [(s.r(8 + i * 32, 8, 28, 44, WHITE, 3, LINE), s.r(11 + i * 32, 11, 22, 18, LIGHT, 2), s.r(11 + i * 32, 33, 18, 2.5, INK, 1), s.r(11 + i * 32, 38, 12, 2.5, BLUE, 1), s.r(11 + i * 32, 44, 22, 5, BLUE, 2.5)) for i in range(4)])
snip('group_ak_offers.svg', lambda s: [(s.r(8 + i * 43, 6, 39, 48, WHITE, 3, LINE), s.r(11 + i * 43, 9, 33, 26, '#DCE6F2' if i != 1 else '#F1E4CB', 2), s.r(15 + i * 43, 39, 25, 4, INK, 1), s.r(19 + i * 43, 47, 17, 2.5, BLUE, 1)) for i in range(3)])
snip('group_ak_gallery.svg', lambda s: (s.r(8, 6, 58, 48, '#DCE6F2', 3), s.r(70, 6, 28, 22, '#F1E4CB', 3), s.r(102, 6, 30, 22, '#E3E8EF', 3), s.r(70, 32, 62, 22, '#DCE6F2', 3)))

m = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'sections_manifest.json')))
for num, key, kit in m['products']:
    s = Svg(140, 60); s.r(0, 0, 140, 60, LIGHT)
    if kit in ('vertical', 'overlay'):
        dark = key == 'dark'
        for i in range(3):
            x = 8 + i * 43; s.r(x, 5, 39, 50, INK if dark else WHITE, 4, None if dark else LINE)
            s.r(x + 3, 8, 33, 24, '#22324D' if dark else LIGHT, 3 if key != 'round' else 12)
            s.r(x + 4, 36, 24, 3, WHITE if dark else INK, 1); s.r(x + 4, 41, 14, 3, GOLD if key in ('gold', 'dark') else BLUE, 1)
            if key not in ('minimal', 'quickadd', 'float', 'centered', 'reveal', 'pricetag'): s.r(x + 4, 47, 31, 5, GOLD if key in ('gold', 'dark') else BLUE, 2.5)
            if key in ('quickadd', 'float', 'minimal'): s.c(x + 32, 28, 4, BLUE)
            if key == 'sale': s.r(x + 5, 10, 10, 4, '#C2410C', 2)
    elif kit in ('horizontal', 'feature'):
        n = 1 if key in ('duo', 'deal') else 2
        for i in range(2 if n == 1 else 4):
            x = 8 + (i % 2) * 64; y = 6 + (i // 2) * 25 if n == 2 else 8
            hh = 22 if n == 2 else 44
            s.r(x, y, 60, hh, WHITE, 4, LINE); s.r(x + 3, y + 3, 18 if n == 2 else 24, hh - 6, LIGHT, 2)
            s.r(x + 25 if n == 2 else x + 31, y + 5, 24, 2.5, INK, 1); s.r(x + 25 if n == 2 else x + 31, y + 11, 12, 2.5, BLUE, 1)
            s.r(x + 46 if n == 2 else x + 31, y + hh - 9, 11 if n == 2 else 22, 5, BLUE, 2.5)
    else:
        for i in range(6):
            x = 8 + (i % 2) * 64; y = 6 + (i // 2) * 17
            s.r(x, y, 60, 14, WHITE, 3, LINE); s.r(x + 2, y + 2, 10, 10, LIGHT, 2); s.r(x + 15, y + 3, 26, 2.5, INK, 1); s.r(x + 15, y + 8, 12, 2.5, BLUE, 1); s.c(x + 53, y + 7, 3.5, BLUE)
    s.save(os.path.join(SN, f'pc_{num}.svg'))

for num, key, kit in m['categories']:
    s = Svg(140, 60); s.r(0, 0, 140, 60, WHITE)
    tint = ['#DCE6F2', '#F1E4CB', '#E3E8EF', '#DCEBE3']
    if key in ('circle', 'soft', 'ring', 'hexagon', 'arch', 'stagger'):
        for i in range(5):
            x = 14 + i * 26; f = tint[i % 4]
            if key == 'soft': s.r(x - 10, 12, 20, 20, f, 6)
            elif key == 'arch': s.r(x - 9, 10, 18, 26, f, 9)
            else: s.c(x, 22 + (6 if key == 'stagger' and i % 2 else 0), 10, f, GOLD if key == 'ring' else None)
            s.r(x - 8, 40, 16, 2.5, INK, 1)
    elif kit == 'inline':
        for i in range(4 if key != 'pill' else 6):
            if key == 'pill': x = 8 + (i % 3) * 43; y = 14 + (i // 3) * 18; s.r(x, y, 40, 13, WHITE, 6.5, LINE); s.c(x + 6.5, y + 6.5, 4.5, tint[i % 4]); s.r(x + 14, y + 5, 20, 2.5, INK, 1)
            else: y = 8 + i * 12; s.r(10, y + 10, 120, .7, LINE); s.r(10, y + 2, 6, 3, GOLD, 1); s.r(20, y, 8, 8, tint[i % 4], 2); s.r(32, y + 2, 40, 3, INK, 1)
    elif key in ('bento', 'masonry'):
        s.r(8, 6, 60, 48, tint[0], 3); s.r(72, 6, 28, 22, tint[1], 3); s.r(104, 6, 28, 22, tint[2], 3); s.r(72, 32, 28, 22, tint[3], 3); s.r(104, 32, 28, 22, tint[0], 3)
    elif key in ('large', 'banner'):
        for i in range(2): s.r(8 + i * 64, 10 if key == 'large' else 18, 60, 40 if key == 'large' else 24, tint[i], 3); s.r(13 + i * 64, 38 if key == 'large' else 28, 24, 4, WHITE, 1)
    else:
        for i in range(4):
            x = 8 + i * 32; f = tint[i % 4]
            s.r(x, 8, 28, 36 if kit != 'card' else 26, f, 3)
            if kit == 'over': s.r(x + 3, 36, 18, 3, WHITE, 1)
            else: s.r(x + 3, 37 if kit == 'card' else 48, 18, 3, INK, 1); kit == 'card' and s.r(x + 3, 43, 12, 2.5, BLUE, 1)
    s.save(os.path.join(SN, f'cc_{num}.svg'))
print(len(os.listdir(B)), len(os.listdir(SN)))
