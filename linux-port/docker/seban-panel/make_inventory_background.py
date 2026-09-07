# -*- coding: utf-8 -*-
"""Rysuje tlo okna ekwipunku dla profilu postaci.

player-profile.css odwoluje sie do /static/inventory-background.png, ale tego
pliku nie ma w zadnej paczce panelu - ani w 1.30.1, ani w 1.37.1. Na serwerze
autora plik istnieje lokalnie, u wszystkich pozostalych okno ekwipunku
wyswietla sie bez ramki: same ikony na plaskim tle.

Grafika klienta nie jest nasza i nie wolno jej rozprowadzac, wiec zamiast
wycinac ja z pakietow klienta rysujemy wlasna ramke w tej samej geometrii, co
CSS. Wspolrzedne ponizej sa przepisane z player-profile.css w procentach, wiec
kazde gniazdo lezy dokladnie tam, gdzie CSS umieszcza ikone.

Uruchomienie (wymaga Pillow):

    python make_inventory_background.py

Zapisuje static/inventory-background.png o rozmiarze 337x1140.
"""
import os
from PIL import Image, ImageDraw

W, H = 337, 1140

# Paleta w duchu okien klienta: ciemne drewno, mosiezna ramka, wglebione
# gniazda. Swiadomie wlasna - to ma pasowac do gry, a nie ja kopiowac.
PANEL_TOP = (46, 38, 29)
PANEL_BOTTOM = (28, 23, 18)
FRAME_OUTER = (18, 15, 11)
FRAME_LIGHT = (146, 116, 66)
FRAME_DARK = (74, 57, 32)
SLOT_FILL = (20, 17, 13)
SLOT_EDGE_DARK = (12, 10, 8)
SLOT_EDGE_LIGHT = (86, 69, 43)
DIVIDER = (96, 76, 45)

# Gniazda ekwipunku: (lewo, gora, szerokosc, wysokosc) w procentach.
EQUIP_SLOTS = [
    (6.23, 6.05, 18.99, 17.89),   # bron
    (28.19, 11.93, 20.48, 12.02),  # zbroja
    (28.19, 6.05, 20.18, 5.61),    # helm
    (28.19, 31.23, 20.77, 6.58),   # buty
    (50.15, 17.63, 21.66, 6.32),   # naramiennik
    (75.07, 17.63, 21.07, 6.32),   # naszyjnik
    (75.07, 11.93, 19.88, 5.53),   # kolczyki
    (5.93, 31.23, 21.66, 6.58),    # unikat 1
    (50.15, 31.23, 21.66, 6.58),   # unikat 2
    (75.07, 6.05, 19.88, 5.61),    # strzaly
    (50.15, 11.93, 21.66, 5.53),   # tarcza
    (28.19, 24.74, 20.48, 5.96),   # pas
]

# Siatka plecaka: obszar z .inventory-layer, 5 kolumn na 9 wierszy.
GRID_LEFT, GRID_TOP, GRID_RIGHT, GRID_BOTTOM = 4.15, 44.47, 0.89, 4.04
GRID_COLS, GRID_ROWS = 5, 9

# Pasek zakladek stron i pasek yang - zostawiamy im czyste miejsce.
TABS_TOP, TABS_HEIGHT = 38.95, 4.82
YANG_BOTTOM, YANG_HEIGHT = 1.50, 2.20


def px(value, total):
    return int(round(value * total / 100.0))


def recess(draw, x0, y0, x1, y1, radius=3):
    """Gniazdo: ciemne wglebienie z jasnym dolnym brzegiem."""
    draw.rounded_rectangle([x0, y0, x1, y1], radius, fill=SLOT_FILL,
                           outline=SLOT_EDGE_DARK)
    draw.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], fill=SLOT_EDGE_LIGHT)
    draw.line([(x1 - 1, y0 + 1), (x1 - 1, y1 - 1)], fill=SLOT_EDGE_LIGHT)


def build():
    img = Image.new('RGBA', (W, H), PANEL_TOP + (255,))
    draw = ImageDraw.Draw(img)

    # Tlo: pionowy gradient, zeby okno nie bylo plaska plama.
    for y in range(H):
        t = y / float(H - 1)
        draw.line([(0, y), (W, y)], fill=tuple(
            int(PANEL_TOP[i] + (PANEL_BOTTOM[i] - PANEL_TOP[i]) * t)
            for i in range(3)) + (255,))

    # Ramka okna.
    draw.rectangle([0, 0, W - 1, H - 1], outline=FRAME_OUTER, width=2)
    draw.rounded_rectangle([2, 2, W - 3, H - 3], 4, outline=FRAME_LIGHT, width=2)
    draw.rounded_rectangle([4, 4, W - 5, H - 5], 3, outline=FRAME_DARK)

    # Czesc z zalozonym ekwipunkiem.
    eq_top, eq_bottom = px(4.4, H), px(37.9, H)
    draw.rounded_rectangle([px(3.0, W), eq_top, W - px(3.0, W), eq_bottom], 4,
                           outline=FRAME_DARK)
    for left, top, width, height in EQUIP_SLOTS:
        recess(draw, px(left, W), px(top, H),
               px(left + width, W) - 1, px(top + height, H) - 1)

    # Kreska pod paskiem zakladek stron.
    tabs_bottom = px(TABS_TOP + TABS_HEIGHT, H)
    draw.line([(px(2.0, W), tabs_bottom), (W - px(2.0, W), tabs_bottom)],
              fill=DIVIDER)

    # Siatka plecaka.
    gx0, gy0 = px(GRID_LEFT, W), px(GRID_TOP, H)
    gx1, gy1 = W - px(GRID_RIGHT, W), H - px(GRID_BOTTOM, H)
    draw.rounded_rectangle([gx0 - 3, gy0 - 3, gx1 + 2, gy1 + 2], 4,
                           outline=FRAME_DARK)
    cell_w = (gx1 - gx0) / float(GRID_COLS)
    cell_h = (gy1 - gy0) / float(GRID_ROWS)
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x0 = int(round(gx0 + col * cell_w))
            y0 = int(round(gy0 + row * cell_h))
            x1 = int(round(gx0 + (col + 1) * cell_w)) - 1
            y1 = int(round(gy0 + (row + 1) * cell_h)) - 1
            recess(draw, x0, y0, x1, y1, 2)

    # Pasek na yang.
    yy1 = H - px(YANG_BOTTOM, H)
    yy0 = yy1 - px(YANG_HEIGHT, H) - 6
    draw.rounded_rectangle([px(10.0, W), yy0, W - px(4.0, W), yy1], 5,
                           fill=(14, 12, 9), outline=FRAME_DARK)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'static', 'inventory-background.png')
    img.save(out)
    print('zapisano %s (%dx%d)' % (out, W, H))


if __name__ == '__main__':
    build()
