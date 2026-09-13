# -*- coding: utf-8 -*-
"""Renderuje playerbot_price_tables.h z cennikow Iwakury.

Wejscie to jego wlasne pliki tekstowe plus dwie tabele swiata (item_proto,
mob_proto), zrzucone szesnastkowo, bo obie kolumny nazw sa w cp1250:

    docker exec <db> mariadb -uroot -p<haslo> -N -e \\
      "SELECT vnum, HEX(locale_name), type, subtype, COALESCE(limitvalue0,0) \\
       FROM player.item_proto ORDER BY vnum;" > item_proto_hex.tsv
    docker exec <db> mariadb -uroot -p<haslo> -N -e \\
      "SELECT vnum, HEX(locale_name), level FROM player.mob_proto ORDER BY vnum;" \\
      > mob_proto_hex.tsv

Uzycie:
    python linux-port/overlays/playerbot/tools/generate_iwakura_prices.py item_proto_hex.tsv mob_proto_hex.tsv \\
        linux-port/overlays/playerbot/data/iwakura_ceny_bronie_zbroje.txt linux-port/overlays/playerbot/data/iwakura_ceny_dodatkowe.txt \\
        linux-port/overlays/playerbot/src/game/src/playerbot_price_tables.h

Skrypt **przerywa z bledem**, gdy ktorejs nazwy nie da sie zwiazac z vnumem.
Cennik, ktory po cichu gubi polowe wierszy, jest gorszy niz jego brak: bot
wystawia wtedy stara cene i nikt nie wie dlaczego.
"""
import io
import re
import sys

# Nazwy, ktore Iwakura pisze w pelni, a gra skraca. Kazda sprawdzona recznie:
# w item_proto jest dokladnie jeden kandydat na kazda z nich.
GEAR_ALIASES = {
    'mnisia zbr. płytowa': 'mnisia zbr. płyt.',
    'żelazna zbr. płytowa': 'żelazna zbr. płyt.',
    'żałobna zbr. płytowa': 'żałobna zbr. płyt.',
    'burzowa zbroj. płytowa': 'burzowa zbroj. płyt.',
    'nieszczęsna zbr. płytowa': 'nieszczęsna zbr. płyt.',
    'upiorna zbroja płytowa': 'upiorna zbroja płyt.',
    'mistyczna zbroja płytowa': 'mistyczna zbroja płyt.',
    'mglista zbroja płytowa': 'mglista zbroja płyt.',
    'duchowa zbroja płytowa': 'duchowa zbroja płyt.',
    # Sekcja [DZWONY], wiec chodzi o dzwon - w grze pelna nazwa ma to slowo.
    'złoty robaczy': 'złoty robaczy dzwon',
}

# Potwory z listy wyjatkow do marmurow. Tak samo: gra skraca, on pisze w pelni.
MOB_ALIASES = {
    'ezoteryczny fanatyk': 'ezot. fanatyk',
    'podły śmier. truj. pająk': 'podły śm. truj. pająk',
    # "v2" to Loch Pajakow V2, na ktorym ten potwor stoi; w mob_proto jest
    # jeden "Maly Trujacy Pajak" i to jest ten.
    'mały trujący pająk v2': 'mały trujący pająk',
}

# Umiejetnosci po nazwie, jak pisze je Iwakura -> vnum ze skill_proto.
# Zrodlo: PLAYER_SKILLS w files/admin_panel.py (tam sa nazwy klienta).
SKILL_IDS = {
    'trzystronne cięcie': 1, 'wir miecza': 2, 'berserk': 3, 'aura miecza': 4, 'szarża': 5,
    'duchowe uderzenie': 16, 'tąpnięcie': 17, 'uderzenie miecza': 18, 'silne ciało': 19,
    'walnięcie': 20,
    'zasadzka': 31, 'szybki atak': 32, 'wirujący sztylet': 33, 'krycie się': 34,
    'trująca chmura': 35,
    'powtarzalny strzał': 46, 'deszcz strzał': 47, 'ognista strzała': 48,
    'bezszelestny chód': 49, 'trująca strzała': 50,
    'uderzenie palcem': 61, 'smoczy wir': 62, 'czarowane ostrze': 63, 'strach': 64,
    'czarowana zbroja': 65, 'rozproszenie magii': 66,
    'mroczne uderzenie': 76, 'ogniste uderzenie': 77, 'ognisty duch': 78,
    'mroczna ochrona': 79, 'duchowy cios': 80,
    # Klient nazywa 81 "Mroczna Sfera"; Iwakura pisze "Mroczny Kamien" - to ta
    # sama, ostatnia umiejetnosc czarnej magii.
    'mroczny kamień': 81, 'mroczna sfera': 81,
    'latający talizman': 91, 'strzelający smok': 92, 'smoczy skowyt': 93,
    'błogosławieństwo': 94, 'odbicie': 95, 'pomoc smoka': 96,
    'błyskawiczny rzut': 106, 'przywołanie błyskawicy': 107,
    # 108 to "Burzowy Szpon" w kliencie, u niego "Szpon Blyskawicy".
    'szpon błyskawicy': 108, 'burzowy szpon': 108,
    'leczenie': 109, 'zwinność': 110,
    # 111 to "Zwiekszenie Ataku"; zostaje jako jedyna nieobsadzona w jego
    # grupie uzdrawiania, gdzie pisze "Burza".
    'burza': 111, 'zwiększenie ataku': 111,
}

# Kamienie duszy: nazwa u Iwakury -> "kind", czyli dwie ostatnie cyfry vnumu.
# Bronowe 30-37, zbrojowe 38-43 (patrz IsPlayerBotWeaponSoulStoneKind).
SOUL_STONE_KINDS = {
    'penetracji': 30, 'śmierci': 31, 'powtórki': 32, 'wojownika': 33, 'ninja': 34,
    'sury': 35, 'szamana': 36, 'potwora': 37,
    'uchylenia': 38, 'uniku': 39, 'magii': 40, 'witalności': 41, 'obrony': 42,
    'przyspieszenia': 43,
}

BAND_RE = re.compile(r'^(?:od\s*)?\+(\d)\s*(?:do\s*\+(\d))?\s*[-–]\s*([\d ]+)$', re.I)
PRICE_RE = re.compile(r'^(.*?)\s*[-–]\s*([\d ]+)$')


def norm(text):
    return re.sub(r'\s+', ' ', text.replace(' ', ' ')).strip().lower()


# Overlay sources are ASCII by convention, and these names only ever appear in
# a trailing comment saying which row is which. Transliterate rather than drop
# them: "Zloty Robaczy Dzwon" still names the thing, "Z?oty" does not.
_ASCII = {
    0x104: 'A', 0x105: 'a', 0x106: 'C', 0x107: 'c', 0x118: 'E', 0x119: 'e',
    0x141: 'L', 0x142: 'l', 0x143: 'N', 0x144: 'n', 0xd3: 'O', 0xf3: 'o',
    0x15a: 'S', 0x15b: 's', 0x179: 'Z', 0x17a: 'z', 0x17b: 'Z', 0x17c: 'z',
}


def ascii_comment(text):
    return ''.join(_ASCII.get(ord(ch), ch if ord(ch) < 128 else '?') for ch in text)


def load_hex(path):
    out = []
    for line in io.open(path, encoding='latin-1'):
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 2:
            continue
        try:
            name = bytes.fromhex(parts[1]).decode('cp1250')
        except ValueError:
            continue
        out.append((int(parts[0]), name, parts[2:]))
    return out


class Resolver(object):
    """Nazwa -> vnum, z aliasami i lista tego, czego nie znalazl."""

    def __init__(self, items, mobs):
        self.items = {}
        for vnum, name, rest in items:
            self.items.setdefault(norm(name), vnum)
        self.mobs = {}
        for vnum, name, rest in mobs:
            self.mobs.setdefault(norm(name), vnum)
        self.missing = []

    def gear(self, family):
        key = GEAR_ALIASES.get(norm(family), norm(family))
        vnum = self.items.get(key + '+0')
        if vnum is None:
            self.missing.append('rodzina sprzetu: %s' % family)
        return vnum

    def item(self, name):
        vnum = self.items.get(norm(name))
        if vnum is None:
            self.missing.append('przedmiot: %s' % name)
        return vnum

    def mob(self, name):
        key = MOB_ALIASES.get(norm(name), norm(name))
        vnum = self.mobs.get(key)
        if vnum is None:
            self.missing.append('potwor: %s' % name)
        return vnum

    def skill(self, name):
        key = norm(re.sub(r'^oz\s+', '', name, flags=re.I))
        vnum = SKILL_IDS.get(key)
        if vnum is None:
            self.missing.append('umiejetnosc: %s' % name)
        return vnum


def parse_gear(path):
    """[(rodzina, {plus: cena}), ...] - wpis to nazwa, pod nia linie pasm."""
    entries, current = [], None
    skip = ('[', 'Skalowanie', 'W przypadku', 'Dla dropu', '...', 'Mnożnik',
            'Później', 'Wszystkie KD', 'Kamień Duszy', 'Pęknięte KD',
            'Jedno włożone', 'Dwa włożone', 'Trzy włożone')
    for raw in io.open(path, encoding='utf-8'):
        line = raw.strip()
        if not line or line.startswith(skip):
            continue
        band = BAND_RE.match(line)
        if band and current is not None:
            lo = int(band.group(1))
            hi = int(band.group(2)) if band.group(2) else lo
            price = int(band.group(3).replace(' ', ''))
            for plus in range(lo, hi + 1):
                current[1][plus] = price
            continue
        if PRICE_RE.match(line):
            continue
        current = (line, {})
        entries.append(current)
    return [e for e in entries if e[1]]


def parse_socket_multipliers(path):
    """Mnozniki z sekcji [MNOZNIK KAMIENI DUSZY ...]: (kind, grade, procent)."""
    out, count_mult = [], {}
    for raw in io.open(path, encoding='utf-8'):
        line = raw.strip()
        m = re.match(r'^(.*?)\s*[-–]\s*([\d.,]+)\s*$', line)
        if not m:
            continue
        name, value = m.group(1).strip(), m.group(2).replace(',', '.')
        try:
            factor = float(value)
        except ValueError:
            continue
        if factor > 3.0:  # to juz cena, nie mnoznik
            continue
        low = norm(name)
        if low.startswith('pęknięte kd'):
            count_mult[0] = factor
        elif low.startswith('jedno włożone'):
            count_mult[1] = factor
        elif low.startswith('dwa włożone'):
            count_mult[2] = factor
        elif low.startswith('trzy włożone'):
            count_mult[3] = factor
        elif low.startswith('kamień duszy'):
            m2 = re.match(r'^kamień duszy\s+(.*?)\s*\+(\d)$', low)
            if m2 and m2.group(1) in SOUL_STONE_KINDS:
                out.append((SOUL_STONE_KINDS[m2.group(1)], int(m2.group(2)), factor))
    return out, count_mult


def section(text, title, all_titles):
    start = text.find('[' + title + ']')
    if start < 0:
        return ''
    end = len(text)
    for stop in all_titles:
        pos = text.find('[' + stop + ']', start + 1)
        if 0 <= pos < end:
            end = pos
    return text[start:end]


def parse_extras(path, resolver):
    text = io.open(path, encoding='utf-8').read()
    titles = ['Marmury Polimorfi', 'Inne', 'Zielarstwo', 'Kamienie duszy',
              'Opaski zapomnienia']

    materials = []          # (vnum, cena) - ziola i "inne"
    for title in ('Inne', 'Zielarstwo'):
        for line in section(text, title, titles).splitlines()[1:]:
            line = line.strip()
            if not line or line.startswith('/'):
                continue
            m = PRICE_RE.match(line)
            if not m:
                continue
            vnum = resolver.item(m.group(1).strip())
            if vnum:
                materials.append((vnum, int(m.group(2).replace(' ', '')), m.group(1).strip()))

    stones = []             # (kind, grade, cena)
    grade_default = {}
    for line in section(text, 'Kamienie duszy', titles).splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith('/'):
            continue
        m = PRICE_RE.match(line)
        if not m:
            continue
        name, price = norm(m.group(1)), int(m.group(2).replace(' ', ''))
        price_all = re.match(r'^kamienie duszy \+(\d) \(wszystkie\)$', name)
        if price_all:
            grade_default[int(price_all.group(1))] = price
            continue
        one = re.match(r'^kamień duszy\s+(.*?)\s*\+(\d)$', name)
        if one and one.group(1) in SOUL_STONE_KINDS:
            stones.append((SOUL_STONE_KINDS[one.group(1)], int(one.group(2)), price))
        elif one:
            resolver.missing.append('kamien duszy: %s' % m.group(1).strip())

    marbles = []            # (mob, cena)
    body = section(text, 'Marmury Polimorfi', titles)
    band = re.search(r'od\s*(\d+)\s*[-–]\s*(\d+)', body)
    marble_min = int(band.group(1)) if band else 15000
    marble_max = int(band.group(2)) if band else 35000
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith('/') or line.startswith('Wszystkie') or line.startswith('('):
            continue
        m = re.match(r'^(.*?)\s*[-–]\s*(\d+)$', line)
        if not m or 'losowo' in line:
            continue
        mob = resolver.mob(m.group(1).strip())
        if mob:
            marbles.append((mob, int(m.group(2)), m.group(1).strip()))

    scrolls = []            # (skill, cena)  albo cena 0 = "do handlarki"
    for line in section(text, 'Opaski zapomnienia', titles).splitlines()[1:]:
        line = line.strip()
        if not line.lower().startswith('oz '):
            continue
        m = PRICE_RE.match(line)
        if m:
            skill = resolver.skill(m.group(1))
            if skill:
                scrolls.append((skill, int(m.group(2).replace(' ', '')), m.group(1).strip()))
        elif 'handlar' in line.lower():
            skill = resolver.skill(re.split(r'[-–]', line)[0])
            if skill:
                scrolls.append((skill, 0, re.split(r'[-–]', line)[0].strip()))
    return materials, stones, grade_default, marbles, marble_min, marble_max, scrolls


HEADER = u'''// Rendered by linux-port/overlays/playerbot/tools/generate_iwakura_prices.py from Iwakura's own price
// lists. DO NOT EDIT; edit the lists and re-run.
//
// Every number here is his, and every vnum was resolved against this world's
// own item_proto and mob_proto rather than guessed - the generator refuses to
// write this file if one name cannot be matched.
//
// All of it scales with the yang drop rate the same way his sheets say: the
// base price times rate/100, so a world at 100%% pays the table and one at
// 500%% pays five times it. See GetPlayerBotMaterialAskingBase.
#ifndef __INC_METIN2_PLAYERBOT_PRICE_TABLES_H__
#define __INC_METIN2_PLAYERBOT_PRICE_TABLES_H__

namespace
{
\t// Weapons and armour by family and refine. The index is the refine level,
\t// 0 to 9; a family the table does not carry keeps the old flat prices.
\tstruct TPlayerBotGearPrice { DWORD dwBaseVnum; DWORD adwPrice[10]; };
\tconst TPlayerBotGearPrice PLAYERBOT_GEAR_PRICES[] = {
%(gear)s\t};

\t// Soul stones by kind and grade. The kinds are the last two digits of the
\t// vnum (30-37 weapon, 38-43 armour) and the grade its hundreds digit.
\tstruct TPlayerBotSoulStonePrice { int iKind; int iGrade; DWORD dwPrice; };
\tconst TPlayerBotSoulStonePrice PLAYERBOT_SOUL_STONE_PRICES[] = {
%(stones)s\t};
\t// What a stone of that grade is worth when its kind is not named above.
\t// Grade four has no general price in his table: every +4 is listed by name.
\tconst DWORD PLAYERBOT_SOUL_STONE_GRADE_PRICES[5] = { %(grades)s };

\t// A stone seated in a weapon or armour raises what the piece is worth.
\t// First by how many are in it, then by which ones (percent, 100 = x1.0).
\tconst int PLAYERBOT_SOCKET_COUNT_PERCENT[4] = { %(counts)s };
\tstruct TPlayerBotSocketStoneMultiplier { int iKind; int iGrade; int iPercent; };
\tconst TPlayerBotSocketStoneMultiplier PLAYERBOT_SOCKET_STONE_PERCENT[] = {
%(mults)s\t};

\t// Polymorph marbles, by the monster in socket 0. Anything not named here
\t// is drawn from the band below, stable per marble.
\tstruct TPlayerBotMarblePrice { DWORD dwMob; DWORD dwPrice; };
\tconst TPlayerBotMarblePrice PLAYERBOT_MARBLE_PRICES[] = {
%(marbles)s\t};
\tconst DWORD PLAYERBOT_MARBLE_PRICE_MIN = %(marble_min)d;
\tconst DWORD PLAYERBOT_MARBLE_PRICE_MAX = %(marble_max)d;

\t// Forgetting Scrolls by the skill in the socket. A price of zero is his
\t// "do sprzedazy u handlarki": that one is the merchant's, not a counter's.
\tstruct TPlayerBotForgetScrollPrice { DWORD dwSkill; DWORD dwPrice; };
\tconst TPlayerBotForgetScrollPrice PLAYERBOT_FORGET_SCROLL_PRICES[] = {
%(scrolls)s\t};

\t// Herbs and the few oddments his "Inne" section prices. Read by
\t// GetPlayerBotMaterialAskingBase beside PLAYERBOT_MATERIAL_PRICES.
\tconst TPlayerBotMaterialPrice PLAYERBOT_EXTRA_MATERIAL_PRICES[] = {
%(materials)s\t};
}

#endif
'''


def main(item_path, mob_path, gear_path, extra_path, out_path):
    resolver = Resolver(load_hex(item_path), load_hex(mob_path))

    gear_rows = []
    for family, bands in parse_gear(gear_path):
        vnum = resolver.gear(family)
        if vnum is None:
            continue
        prices = [bands.get(plus, 0) for plus in range(10)]
        # Pasmo, ktorego nie napisal, bierze najblizsza nizsza cene - jego
        # tabele zawsze ida w gore, wiec dziura znaczy "tyle samo co nizej".
        last = 0
        for i in range(10):
            if prices[i] == 0:
                prices[i] = last
            last = prices[i]
        gear_rows.append('\t\t{ %5d, { %s } },\t// %s\n'
                         % (vnum, ', '.join('%d' % p for p in prices),
                            ascii_comment(family)))

    (materials, stones, grade_default, marbles,
     marble_min, marble_max, scrolls) = parse_extras(extra_path, resolver)
    mults, count_mult = parse_socket_multipliers(gear_path)

    if resolver.missing:
        sys.stderr.write('generate_iwakura_prices: nie rozpoznano %d nazw:\n'
                         % len(resolver.missing))
        for item in resolver.missing:
            sys.stderr.write('  %s\n' % item)
        raise SystemExit(1)

    body = HEADER % {
        'gear': ''.join(gear_rows),
        'stones': ''.join('\t\t{ %2d, %d, %8d },\n' % (k, g, p) for k, g, p in sorted(stones)),
        'grades': ', '.join('%d' % grade_default.get(g, 0) for g in range(5)),
        'counts': ', '.join('%d' % int(round(count_mult.get(i, 1.0) * 100)) for i in range(4)),
        'mults': ''.join('\t\t{ %2d, %d, %3d },\n' % (k, g, int(round(f * 100)))
                         for k, g, f in sorted(mults)),
        'marbles': ''.join('\t\t{ %5d, %7d },\t// %s\n' % (v, p, ascii_comment(n))
                           for v, p, n in sorted(marbles)),
        'marble_min': marble_min,
        'marble_max': marble_max,
        'scrolls': ''.join('\t\t{ %3d, %7d },\t// %s\n' % (s, p, ascii_comment(n))
                           for s, p, n in sorted(scrolls)),
        'materials': ''.join('\t\t{ %5d, %7d },\t// %s\n' % (v, p, ascii_comment(n))
                             for v, p, n in sorted(materials)),
    }
    body.encode('ascii')  # the overlay is ASCII; fail here rather than in the build
    with io.open(out_path, 'w', encoding='ascii', newline='\n') as handle:
        handle.write(body)
    print('zapisano %s' % out_path)
    print('  rodzin sprzetu: %d' % len(gear_rows))
    print('  kamieni duszy (wyjatki): %d, mnoznikow socketow: %d' % (len(stones), len(mults)))
    print('  marmurow (wyjatki): %d, opasek: %d, materialow: %d'
          % (len(marbles), len(scrolls), len(materials)))


if __name__ == '__main__':
    main(*sys.argv[1:6])
