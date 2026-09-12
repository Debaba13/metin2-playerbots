# -*- coding: utf-8 -*-
"""The playerbot migrator (mariadb/playerbot/apply.sh) for the mt2009 world.

Usage:  python migratorify.py

Copies linux-port/docker/mariadb/playerbot/{apply.sh,itemshop_schema.sql} into
linux-port-mt2009/docker/mariadb/playerbot/ and rewrites what the schema and
the map layout change:

  * the readiness probe: mt2009's log schema has hack_log, not speed_hack;
    player.item_proto is a view over world.item_proto (initdb creates it);
  * the list of maps a bot may be parked on: this stack's m2-render-config
    hosts the package's forty-six maps plus the guild villages and the high
    maps, so the list is that layout, not r40250's.

Idempotent: re-run after editing the r40250 original.
"""
import io
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'linux-port', 'docker', 'mariadb', 'playerbot'))
DST = os.path.normpath(os.path.join(HERE, '..', 'docker', 'mariadb', 'playerbot'))

# Everything m2-render-config's MAPS_first / MAPS_game1 / MAPS_game2 host.
HOSTED = ('1, 3, 4, 5, 6, 107, 81, 110, 111, 112, 113, 181, 182, 183, 200, 250, 302, 304,\n'
          '                               21, 23, 24, 25, 26, 61, 63, 64, 65, 69, 70, 71, 104, 108, 109, 79, 216, 217, 73,\n'
          '                               41, 43, 44, 45, 46, 62, 66, 67, 68, 72, 90, 208, 301, 303, 351')


def main():
    os.makedirs(DST, exist_ok=True)
    s = io.open(os.path.join(SRC, 'apply.sh'), encoding='utf-8', newline='').read()
    assert '\r' not in s

    n = s.count("table_name='speed_hack'")
    assert n == 1, n
    s = s.replace("table_name='speed_hack'", "table_name='hack_log'")

    pat = re.compile(r"\(1, 3, 4, 5, 21, 23, 24, 25, 41, 43, 44, 45,\s+108, 109, 61, 63, 64, 104, 65, 71\)")
    s, n = pat.subn('(' + HOSTED + ')', s)
    assert n == 2, n

    s = s.replace('echo "[playerbot-migrate] waiting for the complete r40250 schema"',
                  'echo "[playerbot-migrate] waiting for the complete mt2009 schema"')

    # A world initialised before initdb widened account.social_id gets the
    # same ALTER here, once; see 10-import-dumps.sh for why.
    anchor = 'itemshop_schema=/opt/playerbot/itemshop_schema.sql\n'
    assert s.count(anchor) == 1
    s = s.replace(anchor,
                  'social_len=$(db -e "\n'
                  '    SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.columns\n'
                  '     WHERE table_schema=\'account\' AND table_name=\'account\' AND column_name=\'social_id\';\n'
                  '")\n'
                  'if [ -n "$social_len" ] && [ "$social_len" -lt 18 ] 2>/dev/null; then\n'
                  '    echo "[playerbot-migrate] widening account.social_id from $social_len to 18 characters"\n'
                  '    db -e "ALTER TABLE account.account MODIFY social_id VARCHAR(18) NOT NULL DEFAULT \'\';"\n'
                  'fi\n'
                  '# The ItemShop reads mileage and jackpot off the account; this schema has\n'
                  '# cash alone. IF NOT EXISTS keeps it a no-op after the first time.\n'
                  'db -e "ALTER TABLE account.account ADD COLUMN IF NOT EXISTS mileage INT NOT NULL DEFAULT 0;"\n'
                  'db -e "ALTER TABLE account.account ADD COLUMN IF NOT EXISTS jackpot INT NOT NULL DEFAULT 0;"\n'
                  '# The log tables the engine writes and the package dump lacks (port/logschemify.py).\n'
                  'if [ -s /opt/playerbot/log_schema.sql ]; then\n'
                  '    if db < /opt/playerbot/log_schema.sql 2>/tmp/logschema.err; then\n'
                  '        echo "[playerbot-migrate] log schema checked"\n'
                  '    else\n'
                  '        echo "[playerbot-migrate] WARNING: log schema failed:" >&2\n'
                  '        head -3 /tmp/logschema.err >&2\n'
                  '    fi\n'
                  'fi\n'
                  '\n' + anchor)
    # The four game masters of the tester account (gm_characters.sql), before
    # the generic "grant the oldest character" step: on a world whose admin
    # account is still empty they are created with their gmlist rows, on a
    # world where somebody plays on admin the file does nothing and the
    # generic step grants that character.
    anchor = ('# ---------------------------------------------------------------------------\n'
              '# A game master for the tester account.\n')
    assert s.count(anchor) == 1
    s = s.replace(anchor,
                  '# The tester account\'s own game masters, mt2009 only (see the file).\n'
                  'if [ -s /opt/playerbot/gm_characters.sql ]; then\n'
                  '    if gm_out=$(db < /opt/playerbot/gm_characters.sql 2>&1); then\n'
                  '        echo "[playerbot-migrate] $gm_out"\n'
                  '    else\n'
                  '        echo "[playerbot-migrate] WARNING: gm_characters.sql failed:" >&2\n'
                  '        echo "$gm_out" | head -3 >&2\n'
                  '    fi\n'
                  'fi\n'
                  '\n' + anchor)
    head = ('#!/bin/sh\n'
            '# Rendered for the mt2009 world by linux-port-mt2009/port/migratorify.py from\n'
            '# linux-port/docker/mariadb/playerbot/apply.sh. DO NOT EDIT; edit the original.\n')
    assert s.startswith('#!/bin/sh\n'), s[:40]
    s = head + s[len('#!/bin/sh\n'):]
    io.open(os.path.join(DST, 'apply.sh'), 'w', encoding='utf-8', newline='').write(s)
    print('migratorify: apply.sh rendered')

    shutil.copyfile(os.path.join(SRC, 'itemshop_schema.sql'), os.path.join(DST, 'itemshop_schema.sql'))
    print('migratorify: itemshop_schema.sql copied')


if __name__ == '__main__':
    main()
