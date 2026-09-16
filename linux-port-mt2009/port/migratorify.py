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
                  '# Fishing from thirty, which is what the wiki says and what the operator\n'
                  '# asked for. This line shipped fifty in three places and moving two was not\n'
                  '# enough: CHARACTER::fishing() (playerbotify.py lowers it), the AI gate, and\n'
                  '# the rod LIMIT_LEVEL - the one that refuses the equip, so a bot of thirty\n'
                  '# could neither wear a rod nor be drawn as an angler. item_proto is read out\n'
                  '# of world.item_proto here (PROTO_FROM_DB = 1), which is why this sticks;\n'
                  '# idempotent, and it touches only rods still carrying the old fifty.\n'
                  'db -e "UPDATE world.item_proto SET limitvalue0 = 30 WHERE type = 13 AND limittype0 = 1 AND limitvalue0 = 50;"\n'
                  '# Maska Sabaha left the world with the Hwang curse (playerbotify\n'
                  '# apply_hwang_curse_removed, the share step of the game Dockerfile): the shop\n'
                  '# that sold one sells it no more. The db core reads the shops at boot, so this\n'
                  '# is live on the next start; idempotent.\n'
                  'db -e "DELETE FROM world.shop_item WHERE item_vnum IN (72731, 72735);"\n'
                  '# And nobody keeps one: every Maska Sabaha still in a bag, on a character, in a\n'
                  '# safebox or on a counter is removed (Tieru, 15 September, "usun" to the masks\n'
                  '# players already held). On every start, so a mask an old core still held while\n'
                  '# an update ran this beside it goes on the next one.\n'
                  'masks=$(db -e "DELETE FROM player.item WHERE vnum IN (72731, 72735); SELECT ROW_COUNT();" || echo x)\n'
                  'masks=$(printf \'%s\' "$masks" | tr -d \'[:space:]\')\n'
                  'if [ "$masks" = "x" ]; then\n'
                  '    echo "[playerbot-migrate] WARNING: could not remove the Maska Sabaha items" >&2\n'
                  'elif [ -n "$masks" ] && [ "$masks" != "0" ]; then\n'
                  '    echo "[playerbot-migrate] removed $masks Maska Sabaha item(s)"\n'
                  'fi\n'
                  '# The market of Shinsoo\'s and Jinno\'s villages moved onto the kingdom\'s guard\n'
                  '# in 2.0.52 (GetTownPitch, playerbot_empire_rules.h), and nothing would ever\n'
                  '# have moved the shops standing round the old pitch: an offline shop stands\n'
                  '# where its keeper stood when it was opened (OpenOfflineShop takes the\n'
                  '# character\'s position, a reopen included) and a keeper walks to its shop to\n'
                  '# serve it. So each bot\'s shop of the old ring is carried across by the\n'
                  '# distance between the two pitches, which keeps the ring\'s shape and spacing,\n'
                  '# and pulled in to 1650 of the guard where it stood further out - the ring of\n'
                  '# 400 to 1700 round each guard is open ground inside the safe zone on\n'
                  '# server_attr. A shop already inside the new ring and outside the old one\n'
                  '# belongs to the new pitch and stays. Once, marked in\n'
                  '# player.playerbot_migrations in the same transaction as the move; on every\n'
                  '# start after that only a bot\'s shop still within 2000 of an old pitch and more\n'
                  '# than 2000 from the new one moves - a keeper that reopened on the old spot\n'
                  '# while an update ran this beside the old game container (update.sh does not\n'
                  '# stop the game first). The db core writes a position only when a shop is\n'
                  '# opened or moved, so an old core cannot write the moved ones back. A player\'s\n'
                  '# own shop is left where its owner put it. Before the game container starts,\n'
                  '# because the db core reads the shops at boot.\n'
                  'db -e "CREATE TABLE IF NOT EXISTS player.playerbot_migrations (name VARCHAR(64) NOT NULL PRIMARY KEY, done_at DATETIME NOT NULL) ENGINE=InnoDB;"\n'
                  'pitch_done=$(db -e "SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = \'pitch_on_guard_2052\';" 2>/dev/null || echo x)\n'
                  'case "$pitch_done" in\n'
                  '    0) pitch_near=1700; pitch_far=1700 ;;\n'
                  '    1) pitch_near=-1; pitch_far=2000 ;;\n'
                  '    *) pitch_near= ;;\n'
                  'esac\n'
                  'if [ -n "$pitch_near" ]; then\n'
                  '    if pitch_moved=$(db -e "\n'
                  '        CREATE TEMPORARY TABLE player.tmp_pitch_moves AS\n'
                  '        SELECT d.owner,\n'
                  '               d.nx + ROUND(d.dx * LEAST(1, 1650 / GREATEST(1, d.d_old))) AS tx,\n'
                  '               d.ny + ROUND(d.dy * LEAST(1, 1650 / GREATEST(1, d.d_old))) AS ty\n'
                  '          FROM (SELECT s.owner, m.nx, m.ny,\n'
                  '                       CAST(s.x AS SIGNED) - m.ox AS dx,\n'
                  '                       CAST(s.y AS SIGNED) - m.oy AS dy,\n'
                  '                       SQRT(POW(CAST(s.x AS SIGNED) - m.ox, 2) + POW(CAST(s.y AS SIGNED) - m.oy, 2)) AS d_old,\n'
                  '                       SQRT(POW(CAST(s.x AS SIGNED) - m.nx, 2) + POW(CAST(s.y AS SIGNED) - m.ny, 2)) AS d_new\n'
                  '                  FROM player.ikashop_offlineshop AS s\n'
                  '                  JOIN player.player AS p ON p.id = s.owner\n'
                  '                  JOIN account.account AS a ON a.id = p.account_id\n'
                  '                  JOIN (SELECT 1 AS map, 473625 AS ox, 954925 AS oy, 474325 AS nx, 954225 AS ny\n'
                  '                        UNION ALL SELECT 3, 353987, 880012, 353025, 882325\n'
                  '                        UNION ALL SELECT 41, 961212, 270162, 959925, 268825\n'
                  '                        UNION ALL SELECT 43, 865500, 244975, 863425, 246025) AS m ON m.map = s.map\n'
                  '                 WHERE a.login LIKE \'playerbot%\') AS d\n'
                  '         WHERE d.d_old <= 2000 AND (d.d_old <= $pitch_near OR d.d_new > $pitch_far);\n'
                  '        START TRANSACTION;\n'
                  '        UPDATE player.ikashop_offlineshop AS s\n'
                  '          JOIN player.tmp_pitch_moves AS t ON t.owner = s.owner\n'
                  '           SET s.x = t.tx, s.y = t.ty;\n'
                  '        SELECT ROW_COUNT();\n'
                  '        INSERT IGNORE INTO player.playerbot_migrations (name, done_at) VALUES (\'pitch_on_guard_2052\', NOW());\n'
                  '        COMMIT;\n'
                  '        DROP TEMPORARY TABLE player.tmp_pitch_moves;\n'
                  '    "); then\n'
                  '        pitch_moved=$(printf \'%s\' "$pitch_moved" | tr -d \'[:space:]\')\n'
                  '        if [ "${pitch_moved:-0}" != "0" ]; then\n'
                  '            echo "[playerbot-migrate] $pitch_moved bot offline shop(s) in Yongan, Jayang, Pyongmoo and Bakra carried onto the guard\'s square"\n'
                  '        fi\n'
                  '    else\n'
                  '        echo "[playerbot-migrate] WARNING: could not move the bots\' offline shops onto the new pitches" >&2\n'
                  '    fi\n'
                  'fi\n'
                  '# fish_log came from r40250\'s dump and has that engine\'s eight columns,\n'
                  '# while this one writes six - so every catch failed with errno 1136 and the\n'
                  '# table is empty on every 2.x world that ever ran. CREATE IF NOT EXISTS\n'
                  '# cannot repair a table that already exists with the wrong shape, so the\n'
                  '# old one is dropped here, before log_schema.sql below recreates it.\n'
                  '# Recognised by a column this engine never writes; a table already in the\n'
                  '# right shape, and whatever history it holds, is left alone.\n'
                  'fish_old=$(db -e "\n'
                  '    SELECT COUNT(*) FROM information_schema.columns\n'
                  '     WHERE table_schema=\'log\' AND table_name=\'fish_log\' AND column_name=\'map_index\';\n'
                  '" 2>/dev/null || echo 0)\n'
                  'if [ "$fish_old" = "1" ]; then\n'
                  '    echo "[playerbot-migrate] fish_log has the r40250 shape and cannot be written; rebuilding it"\n'
                  '    db -e "DROP TABLE IF EXISTS log.fish_log;"\n'
                  'fi\n'
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
