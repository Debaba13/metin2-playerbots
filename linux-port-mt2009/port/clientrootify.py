# -*- coding: utf-8 -*-
"""The client's root scripts this line changes, rendered from the stock ones.

Usage:  python clientrootify.py --root <directory the stock root pack was extracted to>

    python tools/eterpack.py --profile mt2009 extract <Klient>/pack/root <dir>

Writes into client-root/ (beside serverinfo.py, which is hand-written):

  * gamerules.py  - RULES_VERSION bumped, so a client that accepted the public
                    server's terms is shown ours once (client-locale-src/rules.pl.txt);
  * intrologin.py - the three buttons of the login window: the home page is
                    the project's GitHub, the Discord is ours, and the Facebook
                    button - there is no Facebook - opens the buycoffee page;
                    also drops the gatekeeper ping to the original commercial
                    site's server on every launch, whose result nothing reads;
  * uiitemshop.py, itemshop_subscriptionwindow.py - "Doladuj SM!" and the
                    subscription button open the buycoffee page, not mt2009.pl;
  * uisystem.py   - the system menu's support button opens our Discord.
  * uitooltip.py  - the GM branch no longer kills every item tooltip.

Exact-string edits on the stock CP1250/CRLF files, byte for byte otherwise.
Idempotent; re-run after a new client package.
"""
import argparse
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'client-root'))

EDITS = {
    'gamerules.py': [
        (b'RULES_VERSION = 3\r\n', b'RULES_VERSION = 4\r\n'),
    ],
    # The ItemShop's "Doladuj SM!" and the subscription window's button both
    # opened the public server's site, and the system menu's support button
    # its account page. Nothing on this server sells coins; the two shop
    # buttons open the buycoffee page (the players' own suggestion) and
    # support is the Discord.
    'uiitemshop.py': [
        (b'\t\t\t"type" : "open_url",\r\n\t\t\t"value" : "https://mt2009.pl/"\r\n',
         b'\t\t\t"type" : "open_url",\r\n\t\t\t"value" : "https://buycoffee.to/metin2-playerbots"\r\n'),
    ],
    'itemshop_subscriptionwindow.py': [
        (b'\t\tutils.open_url("https://mt2009.pl/")\r\n',
         b'\t\tutils.open_url("https://buycoffee.to/metin2-playerbots")\r\n'),
    ],
    # A game master saw no item tooltip at all: the GM branch of the item
    # tooltip iterates self.auxiliaryDict.items(), and auxiliaryDict is the
    # empty string (its assignment from player.GetAuxiliaryString is
    # commented out), so every tooltip died in AttributeError before
    # ShowToolTip ("Nie widac nazw itemow" - "tylko gdy jestes GM").
    'uitooltip.py': [
        (b'\t\t\tself.AppendTextLine("Auxs: ")\r\n'
         b'\t\t\tfor _, val in self.auxiliaryDict.items():\r\n'
         b'\t\t\t\tself.AppendTextLine("Key: [{}] Value: [{}]".format(_, val))\r\n',
         b'\t\t\tif isinstance(self.auxiliaryDict, dict) and self.auxiliaryDict:\r\n'
         b'\t\t\t\tself.AppendTextLine("Auxs: ")\r\n'
         b'\t\t\t\tfor _, val in self.auxiliaryDict.items():\r\n'
         b'\t\t\t\t\tself.AppendTextLine("Key: [{}] Value: [{}]".format(_, val))\r\n'),
    ],
    'uisystem.py': [
        (b'\t\tutils.open_url("https://mt2009.pl/Identity/Account/Manage/Support")\r\n',
         b'\t\tutils.open_url("https://discord.gg/pt5tvnrN6")\r\n'),
    ],
    'intrologin.py': [
        (b'\t\tself.homePageButton.SAFE_SetEvent(self.OpenURL, "https://mt2009.pl/")\r\n',
         b'\t\tself.homePageButton.SAFE_SetEvent(self.OpenURL, "https://github.com/Debaba13/metin2-playerbots")\r\n'),
        (b'\t\tself.facebookButton.SAFE_SetEvent(self.OpenURL, "https://www.facebook.com/Metin2009PL")\r\n',
         b'\t\tself.facebookButton.SAFE_SetEvent(self.OpenURL, "https://buycoffee.to/metin2-playerbots")\r\n'),
        (b'\t\tself.discordButton.SAFE_SetEvent(self.OpenURL, "https://discord.gg/RhUaGRYZG7")\r\n',
         b'\t\tself.discordButton.SAFE_SetEvent(self.OpenURL, "https://discord.gg/pt5tvnrN6")\r\n'),
        # A ping to the original commercial site on every client launch, gated
        # only on the release-build flags so it fires for every player, and a
        # synchronous one - a firewalled or offline single-player machine
        # would stall the login window waiting on it. The result is never
        # read (only "success!" printed to a console nobody sees), so nothing
        # depends on this beyond the network call itself.
        (b'\t\tif not app.DEBUG_BUILD and not app.INTERNAL_BUILD:\r\n'
         b'\t\t\tif not constInfo.GATEKEEPER_CHECK and app.RestPOSTRequest("logon.mt2009.pl", "80", "/gatekeeper.php"):\r\n'
         b'\t\t\t\tprint "success!"\r\n'
         b'\r\n'
         b'\t\t\tconstInfo.GATEKEEPER_CHECK = True\r\n'
         b'\r\n',
         b''),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, help='directory holding the extracted stock root')
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for name, edits in EDITS.items():
        src = os.path.join(args.root, name)
        if not os.path.isfile(src):
            raise SystemExit('clientrootify: no %s in %s' % (name, args.root))
        data = io.open(src, 'rb').read()
        for old, new in edits:
            if data.count(old) != 1:
                if data.count(new) == 1:
                    continue  # already ours (re-run on our own output)
                raise SystemExit('clientrootify: %s: expected exactly one %r, found %d' % (name, old[:50], data.count(old)))
            data = data.replace(old, new)
        io.open(os.path.join(OUT, name), 'wb').write(data)
        print('clientrootify: client-root/%s (%d bytes)' % (name, len(data)))


if __name__ == '__main__':
    main()
