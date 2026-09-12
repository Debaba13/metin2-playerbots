# -*- coding: utf-8 -*-
"""What the r40250 image adds to its share tree, for the mt2009 package.

Usage:  python shareify.py

Copies linux-port/docker/game/{mob_drop_item.m3.append.txt,
special_item_group.moonlight.txt} into linux-port-mt2009/docker/game/, writes
special_item_group.starter.txt beside them and puts the append step into the
runtime stage of docker/game/Dockerfile:

  * mob_drop_item.m3.append.txt - the level-30 weapon ladder's kill groups
    on the guild map's cursed wolves. 132/133/135/136 stand on map 24 in
    this package too (group_group 1101-1104, the same layout); the 127-130
    groups name mobs the package lacks and register on nothing.
  * special_item_group.moonlight.txt - the Moonlight chest (50011) the bots
    open, replacing the stock block: the reader keeps the first group it
    reads for a vnum, so the stock one is cut before ours goes on the end.
  * special_item_group.starter.txt - the starter chest chain (50187, 50212,
    50213 for the three job pairs, then 50188..50193 by level), as r40250's
    share defines it. The playerbot seed puts the lv1 chest in every bot's
    bag and this package has no group for any of them: 1500 chests refused
    fifty-five thousand times an hour. The lv30 and lv60 chests here lack
    r40250's 76016 and 76009 lines, items this package does not have; one
    missing item fails the whole file ("cannot load SpecialItemGroup").

Idempotent: re-run after editing an original.
"""
import io
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
R40250_GAME = os.path.normpath(os.path.join(HERE, '..', '..', 'linux-port', 'docker', 'game'))
GAME = os.path.normpath(os.path.join(HERE, '..', 'docker', 'game'))
WORLD_SQL = os.path.normpath(os.path.join(HERE, '..', 'docker', 'mariadb', 'initdb.d', 'dumps', 'world.sql'))


def dump_vnums(table):
    """The vnums the package's world dump inserts into a proto table."""
    text = io.open(WORLD_SQL, encoding='utf-8', errors='replace', newline='').read()
    m = re.search(r"INSERT INTO `%s` VALUES(.*?);\n" % table, text, re.S)
    if not m:
        raise SystemExit('shareify: no INSERT INTO `%s` in %s' % (table, WORLD_SQL))
    return set(int(v) for v in re.findall(r"[(]\s*(\d+)\s*,\s*'", m.group(1)))


def group_items(text):
    """Item vnums named by the lines of a special_item_group / mob_drop_item file."""
    return set(int(v) for v in re.findall(r"^\s*\d+\s+(\d+)\s", text, re.M))


def check_items(name, text, items):
    missing = sorted(group_items(text) - items)
    if missing:
        # One unknown item fails the whole special_item_group.txt at boot
        # ("cannot load SpecialItemGroup"), and with it every chest in the
        # world. Refuse here rather than find out in syserr.
        raise SystemExit('shareify: %s names items the package lacks: %s' % (name, missing))

STARTER = """\
# The starter chest chain, as r40250's special_item_group.txt defines it
# (rendered by linux-port-mt2009/port/shareify.py). The playerbot seed puts
# the lv1 chest in every bot's bag; the package has no group for it.
Group	lv1(sura_warrior)
{
	Vnum	50187
	Type	Pct
	1	50188	1	100
	2	10	1	100
	3	27051	20	100
	4	27052	10	100
	5	27053	5	100
	6	27054	5	100
}
Group	lv1(assassin)
{
	Vnum	50212
	Type	Pct
	1	50188	1	100
	2	1000	1	100
	3	27051	20	100
	4	27052	10	100
	5	27053	5	100
	6	27054	5	100
}
Group	lv1(shaman)
{
	Vnum	50213
	Type	Pct
	1	50188	1	100
	2	7000	1	100
	3	27051	20	100
	4	27052	10	100
	5	27053	5	100
	6	27054	5	100
}
Group	lv10
{
	Vnum	50188
	Type	Pct
	1	76012	3	100
	2	76017	3	100
	3	76021	1	100
	4	76008	3	100
	5	50189	1	100
}
Group	lv20
{
	Vnum	50189
	Type	Pct
	1	76012	3	100
	2	76017	3	100
	3	76004	1	100
	4	76006	1	100
	5	50190	1	100
	6	76023	3	100
	7	76024	3	100
}
Group	lv30
{
	Vnum	50190
	Type	Pct
	1	76012	3	100
	2	76017	3	100
	3	76011	1	100
	4	50191	1	100
}
Group	lv40
{
	Vnum	50191
	Type	Pct
	1	76012	3	100
	2	76018	3	100
	3	71153	1	100
	4	76011	1	100
	5	50192	1	100
}
Group	lv50
{
	Vnum	50192
	Type	Pct
	1	76003	3	100
	2	76018	3	100
	3	76007	20	100
	4	76019	5	100
	5	70058	1	100
	6	50193	1	100
}
Group	lv60
{
	Vnum	50193
	Type	Pct
	1	76003	3	100
	2	76018	3	100
	3	76000	5	100
	4	50194	1	100
}
"""

# Goes right after the share COPYs of the runtime stage. The package's file
# is UTF-8 with CRLF; the appended text is given the same endings so the
# file stays one thing. The awk keeps every Group..} block that does not
# name one of the vnums ours define.
DOCKERFILE_ANCHOR = 'COPY src/serverfiles/share/package /opt/metin2/share/package\n'
DOCKERFILE_STEP = r'''
# What the r40250 image adds to its share, for the poland locale here
# (port/shareify.py renders the three files and this step):
#  * mob_drop_item.m3.append.txt - the level-30 weapon ladder's kill groups on
#    the guild map's cursed wolves;
#  * special_item_group.moonlight.txt - the Moonlight chest (50011) the bots
#    open, replacing the stock block (the reader keeps the first group per
#    vnum, so the stock one is cut out first);
#  * special_item_group.starter.txt - the starter chest chain the playerbot
#    seed hands out and the package has no group for.
COPY mob_drop_item.m3.append.txt special_item_group.moonlight.txt special_item_group.starter.txt /tmp/share-add/
RUN set -eu; L=/opt/metin2/share/locale/poland \
 && for f in /tmp/share-add/*.txt; do sed -i 's/\r$//; s/$/\r/' "$f"; done \
 && cat /tmp/share-add/mob_drop_item.m3.append.txt >> "$L/mob_drop_item.txt" \
 && f="$L/special_item_group.txt" \
 && awk 'BEGIN{keep=1} /^Group/{blk=""; keep=1} {blk=blk $0 "\n"} /Vnum[ \t]+(50011|50187|50212|50213|50188|50189|50190|50191|50192|50193)([^0-9]|$)/{keep=0} /^}/{ if (keep) printf "%s", blk; blk=""; keep=1 }' "$f" > "$f.new" \
 && cat /tmp/share-add/special_item_group.moonlight.txt /tmp/share-add/special_item_group.starter.txt >> "$f.new" \
 && mv "$f.new" "$f" \
 && rm -rf /tmp/share-add \
 && echo "share: moonlight + starter chests, M3 drops appended"
'''


def main():
    items = dump_vnums('item_proto')
    mobs = dump_vnums('mob_proto')
    print('shareify: package has %d items, %d mobs' % (len(items), len(mobs)))
    for name in ('mob_drop_item.m3.append.txt', 'special_item_group.moonlight.txt'):
        text = io.open(os.path.join(R40250_GAME, name), encoding='latin-1', newline='').read()
        check_items(name, text, items)
        shutil.copyfile(os.path.join(R40250_GAME, name), os.path.join(GAME, name))
        print('shareify: %s copied' % name)
    m3 = io.open(os.path.join(GAME, 'mob_drop_item.m3.append.txt'), encoding='latin-1', newline='').read()
    absent = sorted(set(int(v) for v in re.findall(r"^\s*Mob\s+(\d+)", m3, re.M)) - mobs)
    if absent:
        # The reader registers a kill group under any vnum; a mob that never
        # spawns simply never drops. Said once so nobody measures it.
        print('shareify: note: M3 drop groups for mobs the package lacks (never spawn): %s' % absent)
    check_items('special_item_group.starter.txt', STARTER, items)
    with io.open(os.path.join(GAME, 'special_item_group.starter.txt'), 'w', encoding='ascii', newline='\n') as f:
        f.write(STARTER)
    print('shareify: special_item_group.starter.txt written')

    dockerfile = os.path.join(GAME, 'Dockerfile')
    s = io.open(dockerfile, encoding='utf-8', newline='').read()
    assert '\r' not in s
    if 'special_item_group.starter.txt /tmp/share-add/' in s:
        print('shareify: Dockerfile already carries the step')
        return
    assert s.count(DOCKERFILE_ANCHOR) == 1, s.count(DOCKERFILE_ANCHOR)
    s = s.replace(DOCKERFILE_ANCHOR, DOCKERFILE_ANCHOR + DOCKERFILE_STEP)
    io.open(dockerfile, 'w', encoding='utf-8', newline='').write(s)
    print('shareify: Dockerfile step added')


if __name__ == '__main__':
    main()
