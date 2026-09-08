#!/usr/bin/env python3
"""Rebuild the displayed names in files/items.json from the server's own files.

    python3 files/tools/rebuild_items.py --conf /path/to/serverfiles/share/conf

Why this exists: items.json used to be a file with no way back to where it came
from. The pack's ACTIVE name file is item_names.txt, which is English, while
item_names_de.txt contains the German names used by the admin operator.

What it does:

  * `n' (the name shown, and searched) comes from the selected display locale.
  * `k' (search keywords) keeps whatever was there and gains every other
    available locale name, whole. Matching is on substrings, so
    "vollmondschwert" and "vollmondschwert+9" both still find the item -- while
    splitting them on the plus would add "0" and "9" as keywords that match
    half the index.
  * `v' and `c' are not touched. The category comes from item_proto and there
    is nothing here that could improve on it.

Items whose vnum item_names.txt does not carry keep the name they had. There
are about 4300 of those and the server has no name for them either; they are
mostly fish, blend stones and other things no name file in the pack mentions.

Idempotent: running it twice changes nothing the second time.
"""
import argparse, io, json, os, sys

DEFAULT_CONF = "/opt/m2port/dockerctx/game/src/serverfiles/share/conf"


def read_names(conf, fname, encodings):
    """vnum -> name, from a two-column VNUM<TAB>LOCALE_NAME file.

    The files are not all in one encoding: the German one is latin-1 and the
    Turkish one is cp1254, so each is tried in turn rather than assumed.
    """
    path = os.path.join(conf, fname)
    if not os.path.exists(path):
        return {}
    raw = open(path, "rb").read()
    for enc in encodings:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin-1")

    out = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            out[int(parts[0])] = parts[1].strip()
        except ValueError:
            continue                      # the VNUM/LOCALE_NAME header line
    return out


def read_itemdesc(path):
    if not os.path.exists(path):
        return {}
    raw = open(path, "rb").read()
    for enc in ("cp1254", "latin-1", "utf-8"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin-1")
    out = {}
    for line in text.splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        try:
            vnum = int(parts[0])
        except ValueError:
            continue
        name = parts[1].strip()
        if name:
            out[vnum] = name
    return out


def translate_turkish_name(name):
    replacements = (
        ("Kardan Adam", "Snowman"), ("Kutup Ayısı", "Polar Bear"),
        ("Kutup", "Polar"), ("Kostümü", "Costume"), ("Maskesi", "Mask"),
        ("Şapkası", "Hat"), ("Kutusu", "Box"), ("Sandığı", "Chest"),
        ("Anahtarı", "Key"), ("Yıldızı", "Star"), ("Çiçeği", "Flower"),
        ("Efsun Nesnesi", "Enchant Item"), ("Yeşil Efsun", "Green Enchant"),
        ("Kırmızı", "Red"), ("Yeşil", "Green"), ("Mavi", "Blue"),
        ("Beyaz", "White"), ("Siyah", "Black"), ("Buz", "Ice"),
        ("Ejderha", "Dragon"), ("Ork", "Orc"), ("Yüzüğü", "Ring"),
        ("Zırh", "Armor"), ("Kılıç", "Sword"), ("Taş", "Stone"),
        ("Parçacık", "Fragment"), ("Bandaj", "Bandage"),
        ("Bilinmeyen", "Unknown"), ("Kutu", "Box"),
    )
    translated = name
    for source, target in replacements:
        translated = translated.replace(source, target)
    return translated


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conf", default=DEFAULT_CONF,
                    help="the serverfiles' share/conf directory (default: %(default)s)")
    ap.add_argument("--items", default=os.path.join(os.path.dirname(here), "items.json"),
                    help="the index to rewrite (default: %(default)s)")
    ap.add_argument("--display-locale", choices=("en", "de", "tr"), default="en",
                    help="locale used for the displayed name (default: %(default)s)")
    ap.add_argument("--missing-name", choices=("preserve", "generic"), default="preserve",
                    help="fallback for items missing all names (default: %(default)s)")
    ap.add_argument("--fallback-locale", choices=("en", "de", "tr"), default="",
                    help="locale used when the display locale has no name")
    ap.add_argument("--fallback-itemdesc", default="",
                    help="client itemdesc.txt used when the display locale has no name")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    if not os.path.isdir(args.conf):
        sys.exit("no such directory: %s\n"
                 "Point --conf at the serverfiles' share/conf." % args.conf)

    names = {
        "en": read_names(args.conf, "item_names.txt",    ("utf-8", "latin-1")),
        "de": read_names(args.conf, "item_names_de.txt", ("utf-8", "latin-1")),
        "tr": read_names(args.conf, "item_names_tr.txt", ("utf-8", "cp1254", "latin-1")),
    }
    display = names[args.display_locale]
    fallback = read_itemdesc(args.fallback_itemdesc)
    if not display:
        filename = "item_names.txt" if args.display_locale == "en" else \
                   "item_names_%s.txt" % args.display_locale
        sys.exit("%s/%s is missing or empty -- nothing to build from."
                 % (args.conf, filename))
    print("names read: EN %d, DE %d, TR %d" %
          (len(names["en"]), len(names["de"]), len(names["tr"])))

    items = json.load(open(args.items, encoding="utf-8"))
    renamed = untouched = 0

    for it in items:
        display_name = display.get(it["v"])
        if not display_name:
            untouched += 1
            if args.fallback_locale:
                display_name = names[args.fallback_locale].get(it["v"], "")
            display_name = fallback.get(it["v"], "") or display_name
            if display_name:
                display_name = translate_turkish_name(display_name)
            elif args.missing_name == "generic":
                display_name = "Unnamed item"
            if display_name:
                it["n"] = display_name
            continue

        words = []

        def add(w):
            w = w.strip().lower()
            if w and w not in words and w != display_name.lower():
                words.append(w)

        for w in str(it.get("k", "")).split():   # existing keywords are words
            add(w)
        for locale, locale_names in names.items():
            if locale != args.display_locale:
                add(locale_names.get(it["v"], ""))  # the other names go in whole

        if it["n"] != display_name:
            renamed += 1
        it["n"] = display_name
        it["k"] = " ".join(words)

    print("renamed: %d, left alone (no %s name): %d" %
          (renamed, args.display_locale.upper(), untouched))
    if args.dry_run:
        print("--dry-run: nothing written")
        return

    with io.open(args.items, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print("wrote %s (%d entries)" % (args.items, len(items)))


if __name__ == "__main__":
    main()
