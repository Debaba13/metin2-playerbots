# Auto Lowy: the player's auto-hunt.
#
# What the official system does (pl-wiki, "System - Auto Lowy"): attack the
# monsters round the character, cast the skills put in its slots on their own
# clocks, drink the potions put in its slots under a share of health or mana,
# use an item such as the cape on a clock, hit Metin stones when asked, keep
# going on a horse and stand up after dying. Here all of it is free and there is
# no premium half (Tieru, 15 September). What the official page does not
# describe and a player wants is a pick-up that leaves some things on the
# ground - "nie podnos broni, zbroi" (Tieru, 15 September) - so the pick-up
# goes by kind.
#
# The window is Colide's (19 September), a player who rebuilt it for himself and
# sent it in: twelve skills in two rows, a row of six potions each drunk under a
# share of its own - of mana when what lies in the slot restores mana
# (IsManaItem), of health otherwise - and a row of six items used on a clock in
# seconds (capes, dews), a switch for every part of the hunt, and a share of
# health to wait for after standing up, drinking and casting but neither
# walking nor fighting. Before him the first slot was health and the second
# mana whatever was put in them, so a player who swapped the two drank health
# potions for mana for as long as the hunt ran. His second version, the same
# evening, after his players had tried it: a second row of six items on a clock
# ("odpalow" there are many in this game, and six ran out), and the pick-up in a
# window of its own, "Auto Lowy - Lupy", beside the fight's - so each fits the
# game's smallest window, 800x600, and either closes on its own. The potions
# stay one row: a slot names a vnum, not a cell, so the next stack of the same
# potion anywhere in the bag is drunk when the first runs out.
#
# The client cannot list the monsters or the items round its character - the
# scripts that do this without the server scan a million VIDs a frame - so it
# asks the server (do_autohunt_target and do_autohunt_loot, playerbotify.py):
#   "/autohunt_target <range> <stones> <dx> <dy> [<skip>]" -> "AutoHuntTarget <vid>",
#   the nearest monster this character may hit within the range of the point
#   the hunt started from, what is already hitting it first - and with
#   <stones> a Metin stone before every monster; <skip> is a target this
#   hunt gave up on as out of its reach (STUCK_SKIP_SECONDS);
#   "/autohunt_loot <range> <kinds> <dx> <dy>" -> "AutoHuntLoot <vid> <dx> <dy>",
#   the nearest item on the ground it may take, of a kind the window keeps.
# Every place goes both ways as an offset from the character: this client
# counts positions from its map's corner and the server from the world's, and
# the world's coordinates put every item a map's base out of the pick-up's
# reach ("nie podnosi dropu", Tieru, 15 September).
# Every step, swing and pick-up goes through the client's own paths - the main
# instance's walk, the attack key, the pick-up packet - so the server sees a
# player walking, swinging and bending down, never a teleport.
#
# game.py registers the Hunter with its updateables (CreateUpdateables), K opens
# the window, and the window starts and stops the hunt. Python 2.7 as the client
# has it, and Python 3 for tests/uiautohunt_test.py. Player-visible strings are
# Polish, written as CP1250 escapes so that the file itself stays ASCII.

import app
import chat
import chr
import item
import math
import mouseModule
import net
import os
import player
import skill
import ui
import wndMgr

try:
    xrange
except NameError:
    xrange = range

SKILL_SLOTS = 12
USE_ITEM_SLOTS = 18
# The first six item slots are potions, each used under its own share of
# health or mana; the other twelve are items used on a clock, in seconds.
POTION_SLOTS = 6
ITEM_SLOT_KEYS = tuple('item%d_vnum' % i for i in xrange(USE_ITEM_SLOTS))
ITEM_EDIT_KEYS = tuple('item%d_val' % i for i in xrange(USE_ITEM_SLOTS))

RANGES = (1000, 2000, 3000, 4000)
# What the pick-up takes, as the server reads a kind (AutoHuntLootKind): the
# config key, the button's word and the bit. Yang is taken with every kind.
LOOT_KINDS = (
    ('loot_weapon',    'Bro\xf1',      1 << 0),
    ('loot_armour',    'Zbroje',       1 << 1),
    ('loot_jewellery', 'Ozdoby',       1 << 2),
    ('loot_potion',    'Mikstury',     1 << 3),
    ('loot_book',      'Ksi\xeagi',    1 << 4),
    ('loot_stone',     'Kamienie',     1 << 5),
    ('loot_other',     'Inne',         1 << 6),
)

# The server allows five commands in half a second (ENABLE_ANTI_CMD_FLOOD) and
# drops the rest without a word, so the two questions go a little under and a
# little over a second apart.
TARGET_REQUEST_INTERVAL = 0.8
LOOT_REQUEST_INTERVAL = 1.0
MOVE_INTERVAL = 0.35
RETURN_MOVE_INTERVAL = 1.0
FACE_INTERVAL = 0.5
POTION_INTERVAL = 1.0
# CHARACTER::PickupItem takes an item within 600 (DistanceValid) and one every
# half second; the pick-up is sent from well inside the first.
LOOT_PICK_DISTANCE = 450
# Between two fights an item this close is fetched before the next monster is
# chased: the next target is named in under a second, and walking to it at once
# left the drops of every fight where they fell ("autolowy nie podnosza
# itemkow", NerrVoVy, 15 September).
LOOT_FIRST_DISTANCE = 900
LOOT_PICK_INTERVAL = 0.6
LOOT_STUCK_SECONDS = 6.0
LOOT_STUCK_PAUSE = 10.0
REVIVE_RETRY = 5.0
# "/restart_here" is refused for the first ten seconds after death.
REVIVE_MIN_SECONDS = 10
SKILL_MIN_INTERVAL = 1.5
ITEM_MIN_INTERVAL = 1
STATUS_INTERVAL = 0.3
MELEE_REACH = 200
ARCHER_REACH = 800
# The walk aims this share of the reach short of the target, or it walks into it.
STOP_SHORT_SHARE = 0.6
# Idle further than this from where the hunt started, walk back.
ANCHOR_LEASH = 600
# A target not reached in this long is behind something the walk cannot pass.
STUCK_SECONDS = 8.0
STUCK_PAUSE = 2.0
# And it is named to the server this long afterwards, so the answer is another
# one: with stones first, the server would send the hunter straight back to
# the stone behind the same wall (blasty, 18 September).
STUCK_SKIP_SECONDS = 60.0

# What restores mana and not health, for a potion slot whose share is then one
# of mana: whatever the item's own table says so (IsManaItem) and these, whose
# table does not - the sugar cake works from a quest - and which Colide found in
# the locale.
MANA_ITEM_VNUMS = (
    27004, 27005, 27006, 27008,
    50815,
    27864, 27867, 27876,
    39012, 71019,
    50021,
)

DEFAULTS = [
    ('range', 2000), ('stones', 0), ('pickup', 1), ('revive', 1), ('revive_after', 15), ('return', 1),
    ('attack', 1), ('use_potions', 1), ('use_buffs', 1), ('use_skills', 1),
    ('revive_hp_percent', 60),
]
for _index in xrange(USE_ITEM_SLOTS):
    DEFAULTS.append(('item%d_vnum' % _index, 0))
    DEFAULTS.append(('item%d_val' % _index, 60 if _index < POTION_SLOTS else 30))
for _index in xrange(SKILL_SLOTS):
    DEFAULTS.append(('skill%d_slot' % _index, 0))
    DEFAULTS.append(('skill%d_interval' % _index, 0))
for _key, _label, _bit in LOOT_KINDS:
    DEFAULTS.append((_key, 1))
# 2: the window before Colide's (six skills, a health potion, a mana potion and
# three items); 3: Colide's own builds on his way to this one; 4: his window,
# with six items on a clock and then twelve - the second row only added keys,
# so a file saved with six reads here as it was and the new row starts empty.
# A file of 2 or older moves into the new slots (ConfigFromOldValues), one of 3
# starts from the defaults, as Colide's own window did with it.
CONFIG_VERSION = 4
DEFAULTS.append(('config_version', CONFIG_VERSION))
# Every character's settings in a folder of their own beside the client, not in
# the client's own; a file of the old name there is still read.
CONFIG_DIR = 'autohunt'


def DefaultConfig():
    return dict(DEFAULTS)


def ParseConfigText(text):
    """The "key=value" lines of a saved file as numbers, a bad line skipped."""
    values = {}
    for line in text.splitlines():
        key, _, value = line.partition('=')
        key = key.strip()
        if not key:
            continue
        try:
            values[key] = max(0, int(value.strip()))
        except ValueError:
            pass
    return values


def ApplyConfigText(config, text):
    """Reads "key=value" lines into ``config``; unknown keys and bad numbers are
    skipped, so a file from another version cannot break the window."""
    for key, value in ParseConfigText(text).items():
        if key in config:
            config[key] = value
    return config


def ConfigFromOldValues(values):
    """A file from the window before Colide's in this one's slots: the six
    skills where they were, the health and mana potions as the first two potion
    slots with their shares, the three items as the first three on a clock."""
    config = DefaultConfig()
    for key in ('range', 'stones', 'pickup', 'revive', 'revive_after', 'return'):
        if key in values:
            config[key] = values[key]
    for index in xrange(6):
        for key in ('skill%d_slot' % index, 'skill%d_interval' % index):
            if key in values:
                config[key] = values[key]
    for slot, (vnumKey, shareKey) in enumerate((('hp_vnum', 'hp_percent'), ('sp_vnum', 'sp_percent'))):
        config['item%d_vnum' % slot] = values.get(vnumKey, 0)
        if shareKey in values:
            config['item%d_val' % slot] = values[shareKey]
    for index in xrange(3):
        target = POTION_SLOTS + index
        config['item%d_vnum' % target] = values.get('item%d_vnum' % index, 0)
        if 'item%d_interval' % index in values:
            config['item%d_val' % target] = values['item%d_interval' % index]
    for key, label, bit in LOOT_KINDS:
        if key in values:
            config[key] = values[key]
    if 'config_version' not in values:
        # A file saved by the window that drew the pick-up's switches as toggle
        # buttons has no version: their pressed look read as "off", and one
        # click on Podnos turned the whole pick-up off (autohunt_Tieru.cfg,
        # 15 September). Such a file gets the pick-up back once.
        config['pickup'] = 1
        for key, label, bit in LOOT_KINDS:
            config[key] = 1
    return config


def ConfigFromText(text):
    values = ParseConfigText(text)
    version = values.get('config_version', 0)
    if version >= CONFIG_VERSION:
        config = ApplyConfigText(DefaultConfig(), text)
    elif version <= 2:
        config = ConfigFromOldValues(values)
    else:
        config = DefaultConfig()
    config['config_version'] = CONFIG_VERSION
    return config


def ConfigText(config):
    return ''.join('%s=%d\n' % (key, config[key]) for key, _ in DEFAULTS)


def SafeName(name):
    return ''.join(c if c.isalnum() else '_' for c in (name or 'postac'))


def ConfigPath(name):
    return os.path.join(CONFIG_DIR, '%s.cfg' % SafeName(name))


def OldConfigPath(name):
    return 'autohunt_%s.cfg' % SafeName(name)


def ParseTargetVid(value):
    try:
        vid = int(value)
    except (TypeError, ValueError):
        return 0
    return vid if 0 < vid <= 0xffffffff else 0


def ParseLoot(vid, x, y):
    """The server's "AutoHuntLoot <vid> <dx> <dy>" as (vid, dx, dy), or (0, 0, 0):
    the item's place as an offset from the character."""
    vid = ParseTargetVid(vid)
    if not vid:
        return (0, 0, 0)
    try:
        return (vid, int(x), int(y))
    except (TypeError, ValueError):
        return (0, 0, 0)


def LootMask(config):
    """The kinds the pick-up takes, as the server reads them; 0 when it is off."""
    if not config.get('pickup'):
        return 0
    mask = 0
    for key, label, bit in LOOT_KINDS:
        if config.get(key):
            mask |= bit
    return mask


def FacingDegree(fromX, fromY, toX, toY):
    """The rotation the client gives an instance that faces (toX, toY)."""
    dx = toX - fromX
    dy = toY - fromY
    distance = math.sqrt(dx * dx + dy * dy)
    if distance <= 0:
        return 0.0
    degree = 180.0 * math.acos(max(-1.0, min(1.0, dy / distance))) / math.pi + 180.0
    if fromX >= toX:
        degree = 360.0 - degree
    return degree


def StopPoint(fromX, fromY, toX, toY, short):
    """The point ``short`` units before (toX, toY) on the way from (fromX, fromY)."""
    dx = fromX - toX
    dy = fromY - toY
    distance = math.sqrt(dx * dx + dy * dy)
    if distance <= short or distance <= 0:
        return (fromX, fromY)
    return (toX + dx * short / distance, toY + dy * short / distance)


def FindInventoryCell(vnum):
    if not vnum:
        return -1
    for cell in xrange(player.INVENTORY_MAX_NUM):
        if player.GetItemIndex(cell) == vnum:
            return cell
    return -1


_manaItems = {}


def IsManaItem(vnum):
    """Whether a potion slot holding ``vnum`` watches mana rather than health:
    a potion whose table restores mana and no health (value1 and value0 of
    USE_POTION and USE_POTION_NODELAY - the blue potions, the fish, Woda Bo,
    the sushi), a blessing that restores a share of mana and none of health
    (value4 and value3), or one of MANA_ITEM_VNUMS. Read once per vnum."""
    if vnum in _manaItems:
        return _manaItems[vnum]
    mana = vnum in MANA_ITEM_VNUMS
    if not mana and vnum:
        try:
            item.SelectItem(vnum)
            if item.GetItemType() == item.ITEM_TYPE_USE and item.GetItemSubType() in (item.USE_POTION, item.USE_POTION_NODELAY):
                mana = ((item.GetValue(1) > 0 and item.GetValue(0) <= 0) or
                        (item.GetValue(4) > 0 and item.GetValue(3) <= 0))
        except Exception:
            mana = False
    _manaItems[vnum] = mana
    return mana


def YesNo(value):
    return 'tak' if value else 'nie'


def WlWyl(value):
    return 'W\xa3' if value else 'WY\xa3'


class Hunter(object):
    """The hunt itself, driven by the game's updateables (CanUpdate, OnUpdate,
    Destroy) whether or not its windows are open."""

    def __init__(self):
        self.config = DefaultConfig()
        self.configName = None
        self.running = False
        self.mainWindow = None
        self.lootWindow = None
        self.ResetState()

    def ResetState(self):
        self.targetVid = 0
        self.skipVid = 0
        self.skipUntil = 0.0
        self.attacking = False
        self.anchor = (0, 0)
        self.nextRequest = 0.0
        self.nextMove = 0.0
        self.nextFace = 0.0
        self.nextPotion = 0.0
        self.nextRevive = 0.0
        self.deadSince = 0.0
        self.justRevived = False
        self.approachSince = 0.0
        self.skillNext = [0.0] * SKILL_SLOTS
        self.itemNext = [0.0] * USE_ITEM_SLOTS
        self.lootVid = 0
        self.lootPos = (0, 0)
        self.lootSince = 0.0
        self.lootPausedUntil = 0.0
        self.nextLootRequest = 0.0
        self.nextLootPick = 0.0

    # --- the game's updateable interface ---------------------------------
    def CanUpdate(self):
        return self.running

    def OnUpdate(self):
        now = app.GetTime()
        if player.GetStatus(player.HP) <= 0:
            self.WhileDead(now)
            return

        # Standing up - by the hunt's own "/restart_here" or by the player's
        # click - starts a wait for a share of health (revive_hp_percent):
        # potions and skills go on, the walk and the fight do not, or the
        # character is killed again where it fell.
        if self.deadSince > 0.0:
            self.justRevived = True
            self.deadSince = 0.0
        if self.justRevived:
            if not self.RevivedEnough():
                self.HandleItems(now)
                self.CastSkills(now)
                return
            self.justRevived = False

        self.HandleItems(now)
        self.CastSkills(now)
        self.AskForLoot(now)
        self.Chase(now)

    def Destroy(self):
        # The game window is closing (a warp or a logout) and the chat with it,
        # so this stop says nothing.
        self.Stop(quiet=True)
        if self.mainWindow:
            self.mainWindow.Destroy()
            self.mainWindow = None
        if self.lootWindow:
            self.lootWindow.Destroy()
            self.lootWindow = None

    # --- start and stop -------------------------------------------------
    def Start(self):
        if self.running:
            return
        self.ResetState()
        (x, y, z) = player.GetMainCharacterPosition()
        self.anchor = (int(x), int(y))
        self.running = True
        chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto \xa3owy: start, zasi\xeag %d.' % self.config['range'])
        if not LootMask(self.config):
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto \xa3owy: podnoszenie jest wy\xb3\xb9czone (Podnie\x9c: nie).')

    def Stop(self, quiet=False):
        if not self.running:
            return
        self.running = False
        self.ReleaseAttack()
        self.targetVid = 0
        self.lootVid = 0
        if not quiet:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto \xa3owy: stop.')

    def OnServerTarget(self, value):
        if not self.running or not self.config.get('attack', 1):
            return
        vid = ParseTargetVid(value)
        if vid != self.targetVid:
            self.ReleaseAttack()
            self.targetVid = vid
            self.approachSince = 0.0

    def OnServerLoot(self, vid, x, y):
        if not self.running or app.GetTime() < self.lootPausedUntil or not LootMask(self.config):
            return
        (vid, dx, dy) = ParseLoot(vid, x, y)
        if vid != self.lootVid:
            self.lootSince = 0.0
        self.lootVid = vid
        (px, py, pz) = player.GetMainCharacterPosition()
        self.lootPos = (int(px) + dx, int(py) + dy)

    # --- one pass -------------------------------------------------------
    def WhileDead(self, now):
        self.ReleaseAttack()
        self.targetVid = 0
        self.lootVid = 0
        if not self.deadSince:
            self.deadSince = now
            return
        wait = max(REVIVE_MIN_SECONDS, self.config['revive_after'])
        if self.config['revive'] and now - self.deadSince >= wait and now >= self.nextRevive:
            self.nextRevive = now + REVIVE_RETRY
            self.justRevived = True
            net.SendChatPacket('/restart_here')

    def RevivedShare(self):
        return min(100, self.config.get('revive_hp_percent', 60))

    def RevivedEnough(self):
        maxHP = player.GetStatus(player.MAX_HP)
        return maxHP <= 0 or player.GetStatus(player.HP) * 100 >= maxHP * self.RevivedShare()

    def HandleItems(self, now):
        if self.config['use_potions'] and now >= self.nextPotion:
            wanted = False
            for i in xrange(POTION_SLOTS):
                vnum = self.config['item%d_vnum' % i]
                share = self.config['item%d_val' % i]
                if not vnum or share <= 0:
                    continue
                if IsManaItem(vnum):
                    point = player.GetStatus(player.SP)
                    maxPoint = player.GetStatus(player.MAX_SP)
                else:
                    point = player.GetStatus(player.HP)
                    maxPoint = player.GetStatus(player.MAX_HP)
                if maxPoint <= 0 or point * 100 > maxPoint * share:
                    continue
                # A second before the next look whether or not the bag still
                # has one: the search walks every cell of four pages, and on
                # every frame it would cost the frame.
                wanted = True
                cell = FindInventoryCell(vnum)
                if cell >= 0:
                    net.SendItemUsePacket(cell)
            if wanted:
                self.nextPotion = now + POTION_INTERVAL

        if self.config['use_buffs']:
            for i in xrange(POTION_SLOTS, USE_ITEM_SLOTS):
                vnum = self.config['item%d_vnum' % i]
                interval = self.config['item%d_val' % i]
                if not vnum or interval <= 0 or now < self.itemNext[i]:
                    continue
                self.itemNext[i] = now + max(ITEM_MIN_INTERVAL, interval)
                cell = FindInventoryCell(vnum)
                if cell >= 0:
                    net.SendItemUsePacket(cell)

    def AskForLoot(self, now):
        mask = LootMask(self.config)
        if not mask:
            self.lootVid = 0
            return
        if now < self.nextLootRequest or now < self.lootPausedUntil:
            return
        self.nextLootRequest = now + LOOT_REQUEST_INTERVAL
        (dx, dy) = self.AnchorOffset()
        net.SendChatPacket('/autohunt_loot %d %d %d %d' % (self.config['range'], mask, dx, dy))

    def Chase(self, now):
        if self.config['attack']:
            if now >= self.nextRequest:
                self.nextRequest = now + TARGET_REQUEST_INTERVAL
                (dx, dy) = self.AnchorOffset()
                command = '/autohunt_target %d %d %d %d' % (
                    self.config['range'], 1 if self.config['stones'] else 0, dx, dy)
                if self.skipVid and now < self.skipUntil:
                    command += ' %d' % self.skipVid
                net.SendChatPacket(command)
        else:
            self.targetVid = 0

        # An item at the character's feet is taken whatever else is going on.
        self.PickNearLoot(now)

        vid = self.targetVid
        distance = player.GetCharacterDistance(vid) if vid else -1
        # The drops before a monster out of reach (LOOT_FIRST_DISTANCE); a fight
        # already in reach is finished first.
        if (self.lootVid and (distance < 0 or distance > self.Reach()) and
                self.LootDistance() <= LOOT_FIRST_DISTANCE and self.GoForLoot(now)):
            self.ReleaseAttack()
            return
        if distance < 0:
            # Nothing named, or the client no longer has it: it died and was
            # removed, or it walked out of sight. Pick up what lies about, or
            # walk back, and wait for the next answer.
            self.targetVid = 0
            self.ReleaseAttack()
            if not self.GoForLoot(now):
                self.ReturnToAnchor(now)
            return

        reach = self.Reach()
        if distance > reach:
            self.ReleaseAttack()
            if not self.approachSince:
                self.approachSince = now
            elif now - self.approachSince > STUCK_SECONDS:
                self.skipVid = vid
                self.skipUntil = now + STUCK_SKIP_SECONDS
                self.targetVid = 0
                self.approachSince = 0.0
                self.nextRequest = now + STUCK_PAUSE
                self.WalkTo(self.anchor[0], self.anchor[1])
                return
            if now >= self.nextMove:
                self.nextMove = now + MOVE_INTERVAL
                (px, py, pz) = player.GetMainCharacterPosition()
                (tx, ty, tz) = chr.GetPixelPosition(vid)
                (sx, sy) = StopPoint(px, py, tx, ty, reach * STOP_SHORT_SHARE)
                self.WalkTo(sx, sy)
            return

        self.approachSince = 0.0
        if now >= self.nextFace:
            self.nextFace = now + FACE_INTERVAL
            self.Face(vid)
        if not self.attacking:
            player.SetTarget(vid)
            player.SetAttackKeyState(True)
            self.attacking = True

    def CastSkills(self, now):
        # On their own clocks, fight or no fight (Colide): a buff stays up while
        # the player walks with the attack switched off - and then Wracaj
        # wants switching off too, or the walk back takes the character away.
        if not self.config['use_skills']:
            return
        for index in xrange(SKILL_SLOTS):
            slot = self.config['skill%d_slot' % index]
            if not slot or now < self.skillNext[index]:
                continue
            skillIndex = player.GetSkillIndex(slot)
            if not skillIndex or player.IsSkillCoolTime(slot):
                continue
            if skill.IsToggleSkill(skillIndex) and player.IsSkillActive(slot):
                continue
            player.ClickSkillSlot(slot)
            self.skillNext[index] = now + max(SKILL_MIN_INTERVAL, float(self.config['skill%d_interval' % index]))
            return

    def PickNearLoot(self, now):
        if not self.lootVid or now < self.nextLootPick:
            return False
        if self.LootDistance() > LOOT_PICK_DISTANCE:
            return False
        self.nextLootPick = now + LOOT_PICK_INTERVAL
        net.SendItemPickUpPacket(self.lootVid)
        self.lootVid = 0
        self.lootSince = 0.0
        # The next item is asked for straight away.
        self.nextLootRequest = min(self.nextLootRequest, now + 0.3)
        return True

    def GoForLoot(self, now):
        if not self.lootVid:
            return False
        if self.LootDistance() <= LOOT_PICK_DISTANCE:
            return True
        if not self.lootSince:
            self.lootSince = now
        elif now - self.lootSince > LOOT_STUCK_SECONDS:
            # Behind something the walk cannot pass: leave the pick-up alone for
            # a while, or the server would name the same item again.
            self.lootVid = 0
            self.lootSince = 0.0
            self.lootPausedUntil = now + LOOT_STUCK_PAUSE
            return False
        if now >= self.nextMove:
            self.nextMove = now + MOVE_INTERVAL
            self.WalkTo(self.lootPos[0], self.lootPos[1])
        return True

    # --- helpers --------------------------------------------------------
    def Reach(self):
        # An Archer (the assassin's second group) shoots from afar.
        if net.GetMainActorRace() % 4 == 1 and net.GetMainActorSkillGroup() == 2:
            return ARCHER_REACH
        return MELEE_REACH

    def AnchorOffset(self):
        # Where the hunt started, as an offset from where the character stands:
        # the server counts from the world's corner and this client from its map's.
        (px, py, pz) = player.GetMainCharacterPosition()
        return (self.anchor[0] - int(px), self.anchor[1] - int(py))

    def LootDistance(self):
        (px, py, pz) = player.GetMainCharacterPosition()
        (lx, ly) = self.lootPos
        return math.sqrt((px - lx) * (px - lx) + (py - ly) * (py - ly))

    def ReturnToAnchor(self, now):
        if not self.config['return'] or now < self.nextMove:
            return
        (px, py, pz) = player.GetMainCharacterPosition()
        (ax, ay) = self.anchor
        if (px - ax) * (px - ax) + (py - ay) * (py - ay) <= ANCHOR_LEASH * ANCHOR_LEASH:
            return
        self.nextMove = now + RETURN_MOVE_INTERVAL
        self.WalkTo(ax, ay)

    def WalkTo(self, x, y):
        chr.MoveToDestPosition(player.GetMainCharacterIndex(), int(x), int(y))

    def Face(self, vid):
        (px, py, pz) = player.GetMainCharacterPosition()
        (tx, ty, tz) = chr.GetPixelPosition(vid)
        chr.SelectInstance(player.GetMainCharacterIndex())
        chr.SetRotation(FacingDegree(px, py, tx, ty))

    def ReleaseAttack(self):
        if self.attacking:
            player.SetAttackKeyState(False)
            self.attacking = False

    # --- settings -------------------------------------------------------
    def LoadConfig(self):
        name = player.GetMainCharacterName()
        if name == self.configName:
            return
        self.configName = name
        self.config = DefaultConfig()
        path = ConfigPath(name)
        if not os.path.exists(path):
            oldPath = OldConfigPath(name)
            if os.path.exists(oldPath):
                path = oldPath
        try:
            with open(path, 'r') as handle:
                self.config = ConfigFromText(handle.read())
        except (IOError, OSError):
            pass

    def SaveConfig(self):
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
            except (IOError, OSError):
                pass
        try:
            with open(ConfigPath(self.configName), 'w') as handle:
                handle.write(ConfigText(self.config))
            return True
        except (IOError, OSError):
            return False

    def ToggleWindow(self):
        """K: both windows, side by side in the middle of the screen the first
        time; after that they stand where the player dragged them. K closes
        whichever of the two is open, and opens both when neither is."""
        self.LoadConfig()
        if self.mainWindow is None:
            self.mainWindow = AutoHuntWindow(self)
            self.lootWindow = AutoHuntLootWindow(self)
            width = self.mainWindow.WIDTH + 10 + self.lootWindow.WIDTH
            x = max(0, (wndMgr.GetScreenWidth() - width) // 2)
            y = max(0, (wndMgr.GetScreenHeight() - self.mainWindow.HEIGHT) // 2)
            self.mainWindow.SetPosition(int(x), int(y))
            self.lootWindow.SetPosition(int(x + self.mainWindow.WIDTH + 10), int(y))
        if self.mainWindow.IsShow() or self.lootWindow.IsShow():
            if self.mainWindow.IsShow():
                self.mainWindow.Close()
            if self.lootWindow.IsShow():
                self.lootWindow.Close()
        else:
            self.mainWindow.Refresh()
            self.lootWindow.Refresh()
            self.mainWindow.Show()
            self.lootWindow.Show()
            self.mainWindow.SetTop()
            self.lootWindow.SetTop()


class AutoHuntWindow(ui.BoardWithTitleBar):
    """The fight: skills, potions, items on a clock, the switches, and the
    buttons that save, start and stop."""
    WIDTH = 300
    HEIGHT = 555
    SLOT_STEP = 40
    SLOTS_PER_ROW = 6
    EDIT_W = 34
    EDIT_H = 18

    def __init__(self, hunter):
        ui.BoardWithTitleBar.__init__(self)
        self.hunter = hunter
        self.widgets = []
        self.edits = {}
        self.toggles = {}
        self.nextStatus = 0.0
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.SetTitleName('Auto \xa3owy - Walka')
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.Build()

    def Build(self):
        BL = 10
        BW = self.WIDTH - 2 * BL
        SL = 20
        SECTION_GAP = 5
        y = 32

        sk_r1_y = 22
        sk_e1_y = sk_r1_y + 34
        sk_r2_y = sk_e1_y + 18 + 4
        sk_e2_y = sk_r2_y + 34
        sk_h = sk_e2_y + 18 + 7

        skBoard = self._Board(BL, y, BW, sk_h)
        self._Label(skBoard, 14, 4, 'Umiej\xeatno\x9cci')

        self.skillSlots1 = self._Slots(skBoard, SL, sk_r1_y, self.SLOTS_PER_ROW)
        self.skillSlots1.SetSelectEmptySlotEvent(ui.__mem_func__(self._EvSkill1))
        self.skillSlots1.SetSelectItemSlotEvent(ui.__mem_func__(self._EvSkill1))
        self.skillSlots1.SetUnselectItemSlotEvent(ui.__mem_func__(self._EvClrSkill1))
        for i in xrange(self.SLOTS_PER_ROW):
            self._EditField(skBoard, SL + i * self.SLOT_STEP, sk_e1_y, self.EDIT_W, 'skill%d_interval' % i)

        self.skillSlots2 = self._Slots(skBoard, SL, sk_r2_y, self.SLOTS_PER_ROW)
        self.skillSlots2.SetSelectEmptySlotEvent(ui.__mem_func__(self._EvSkill2))
        self.skillSlots2.SetSelectItemSlotEvent(ui.__mem_func__(self._EvSkill2))
        self.skillSlots2.SetUnselectItemSlotEvent(ui.__mem_func__(self._EvClrSkill2))
        for i in xrange(self.SLOTS_PER_ROW):
            self._EditField(skBoard, SL + i * self.SLOT_STEP, sk_e2_y, self.EDIT_W, 'skill%d_interval' % (i + self.SLOTS_PER_ROW))

        y += sk_h + SECTION_GAP

        mk_r1_y = 22
        mk_e1_y = mk_r1_y + 34
        mk_h = mk_e1_y + 18 + 7

        mkBoard = self._Board(BL, y, BW, mk_h)
        self._Label(mkBoard, 14, 4, 'Mikstury (% HP / PE)')

        self.itemSlots1 = self._Slots(mkBoard, SL, mk_r1_y, self.SLOTS_PER_ROW)
        self.itemSlots1.SetSelectEmptySlotEvent(ui.__mem_func__(self._EvItem1))
        self.itemSlots1.SetSelectItemSlotEvent(ui.__mem_func__(self._EvItem1))
        self.itemSlots1.SetUnselectItemSlotEvent(ui.__mem_func__(self._EvClrItem1))
        for i in xrange(self.SLOTS_PER_ROW):
            self._EditField(mkBoard, SL + i * self.SLOT_STEP, mk_e1_y, self.EDIT_W, ITEM_EDIT_KEYS[i])

        y += mk_h + SECTION_GAP

        od_r1_y = 22
        od_e1_y = od_r1_y + 34
        od_r2_y = od_e1_y + 18 + 4
        od_e2_y = od_r2_y + 34
        od_h = od_e2_y + 18 + 7

        odBoard = self._Board(BL, y, BW, od_h)
        self._Label(odBoard, 14, 4, 'Odpa\xb3y (Sekundy)')

        self.itemSlots2 = self._Slots(odBoard, SL, od_r1_y, self.SLOTS_PER_ROW)
        self.itemSlots2.SetSelectEmptySlotEvent(ui.__mem_func__(self._EvItem2))
        self.itemSlots2.SetSelectItemSlotEvent(ui.__mem_func__(self._EvItem2))
        self.itemSlots2.SetUnselectItemSlotEvent(ui.__mem_func__(self._EvClrItem2))
        for i in xrange(self.SLOTS_PER_ROW):
            self._EditField(odBoard, SL + i * self.SLOT_STEP, od_e1_y, self.EDIT_W, ITEM_EDIT_KEYS[i + self.SLOTS_PER_ROW])

        self.itemSlots3 = self._Slots(odBoard, SL, od_r2_y, self.SLOTS_PER_ROW)
        self.itemSlots3.SetSelectEmptySlotEvent(ui.__mem_func__(self._EvItem3))
        self.itemSlots3.SetSelectItemSlotEvent(ui.__mem_func__(self._EvItem3))
        self.itemSlots3.SetUnselectItemSlotEvent(ui.__mem_func__(self._EvClrItem3))
        for i in xrange(self.SLOTS_PER_ROW):
            self._EditField(odBoard, SL + i * self.SLOT_STEP, od_e2_y, self.EDIT_W, ITEM_EDIT_KEYS[i + self.SLOTS_PER_ROW * 2])

        y += od_h + SECTION_GAP

        ROW_H = 19
        st_row_start = 22
        settings_rows = [
            ('Atak',                   'attack',            'toggle'),
            ('Umiej\xeatno\x9cci',     'use_skills',        'toggle'),
            ('Wskrzeszenie',           'revive',            'toggle'),
            ('HP po wskrz. %',         'revive_hp_percent', 'edit'),
            ('Mikstury',               'use_potions',       'toggle'),
            ('Odpa\xb3y',              'use_buffs',         'toggle'),
            ('Metiny',                 'stones',            'toggle'),
            ('Wracaj',                 'return',            'toggle'),
        ]
        st_h = st_row_start + 4 * ROW_H + 4
        stBoard = self._Board(BL, y, BW, st_h)
        self._Label(stBoard, 14, 4, 'Ustawienia')

        col_w = (BW - 8) // 2
        for idx, (lbl, key, kind) in enumerate(settings_rows):
            col = idx // 4
            row = idx % 4
            x = 4 + col * col_w
            ry = st_row_start + row * ROW_H
            if kind == 'toggle':
                self._SettingRow(stBoard, x, ry, col_w - 2, ROW_H - 1, lbl, key)
            else:
                self._EditSettingRow(stBoard, x, ry, col_w - 2, ROW_H - 1, lbl, key)

        y += st_h + 4

        bw = 88
        gap = 8
        total = 3 * bw + 2 * gap
        bx = (self.WIDTH - total) // 2

        self.statusText = self._Label(self, bx + 6, y, 'Wy\xb3\xb9czone')
        y += 18

        self._Btn(self, 'large', bx, y, 'Zapisz', self.OnSave)
        bx += bw + gap
        self.startButton = self._Btn(self, 'large', bx, y, 'Start', self.OnStart)
        bx += bw + gap
        self.stopButton = self._Btn(self, 'large', bx, y, 'Zatrzymaj', self.OnStop)

    def _Board(self, x, y, w, h):
        board = ui.ThinBoard()
        board.SetParent(self)
        board.SetPosition(x, y)
        board.SetSize(w, h)
        board.Show()
        self.widgets.append(board)
        return board

    def _Label(self, parent, x, y, text):
        line = ui.TextLine()
        line.SetParent(parent)
        line.SetPosition(x, y)
        line.SetText(text)
        line.Show()
        self.widgets.append(line)
        return line

    def _Btn(self, parent, size, x, y, text, event, *args):
        button = ui.Button()
        button.SetParent(parent)
        button.SetPosition(x, y)
        button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % size)
        button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % size)
        button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % size)
        button.SetText(text)
        button.SAFE_SetEvent(event, *args)
        button.Show()
        self.widgets.append(button)
        return button

    def _Slots(self, parent, x, y, count):
        slots = ui.SlotWindow()
        slots.SetParent(parent)
        slots.SetPosition(x, y)
        slots.SetSize(count * self.SLOT_STEP, 32)
        for i in xrange(count):
            slots.AppendSlot(i, i * self.SLOT_STEP, 0, 32, 32)
        slots.SetSlotBaseImage('d:/ymir work/ui/public/slot_base.sub', 1.0, 1.0, 1.0, 1.0)
        slots.Show()
        self.widgets.append(slots)
        return slots

    def _EditField(self, parent, x, y, w, key):
        bar = ui.SlotBar()
        bar.SetParent(parent)
        bar.SetPosition(x, y)
        bar.SetSize(w, self.EDIT_H)
        bar.Show()
        self.widgets.append(bar)

        edit = ui.EditLine()
        edit.SetParent(bar)
        edit.SetPosition(4, 1)
        edit.SetSize(w - 6, self.EDIT_H - 2)
        edit.SetMax(4)
        edit.SetNumberMode()
        edit.Show()
        self.widgets.append(edit)
        self.edits[key] = edit

    def _SettingRow(self, board, x, y, w, h, label, key):
        bar = ui.Bar()
        bar.SetParent(board)
        bar.SetPosition(x, y)
        bar.SetSize(w, h)
        bar.SetColor(0xC0000000)
        bar.Show()
        self.widgets.append(bar)

        btn_w = 50
        text_area = w - btn_w - 4

        tx = x + (text_area // 2)
        lbl_line = self._Label(board, tx, y + (h - 12) // 2, label)
        lbl_line.SetHorizontalAlignCenter()

        btn = ui.Button()
        btn.SetParent(board)
        btn.SetPosition(x + w - btn_w, y)
        btn.SetUpVisual('d:/ymir work/ui/public/small_button_01.sub')
        btn.SetOverVisual('d:/ymir work/ui/public/small_button_02.sub')
        btn.SetDownVisual('d:/ymir work/ui/public/small_button_03.sub')
        btn.SetText('WY\xa3')
        btn.SAFE_SetEvent(self.OnToggle, key)
        btn.Show()
        self.widgets.append(btn)
        self.toggles[key] = (btn, label, True)

    def _EditSettingRow(self, board, x, y, w, h, label, key):
        bar = ui.Bar()
        bar.SetParent(board)
        bar.SetPosition(x, y)
        bar.SetSize(w, h)
        bar.SetColor(0xC0000000)
        bar.Show()
        self.widgets.append(bar)

        edit_w = 34
        text_area = w - 50 - 4

        tx = x + (text_area // 2)
        lbl_line = self._Label(board, tx, y + (h - 12) // 2, label)
        lbl_line.SetHorizontalAlignCenter()

        slotbar = ui.SlotBar()
        slotbar.SetParent(board)
        slotbar.SetPosition(x + w - 46, y + 1)
        slotbar.SetSize(edit_w, h - 2)
        slotbar.Show()
        self.widgets.append(slotbar)

        edit = ui.EditLine()
        edit.SetParent(slotbar)
        edit.SetPosition(4, (h - 2 - 14) // 2)
        edit.SetSize(edit_w - 8, 14)
        edit.SetMax(3)
        edit.SetNumberMode()
        edit.Show()
        self.widgets.append(edit)
        self.edits[key] = edit

    def _EvSkill1(self, idx):
        self.OnSkillSlot(idx)

    def _EvClrSkill1(self, idx):
        self.OnClearSkillSlot(idx)

    def _EvSkill2(self, idx):
        self.OnSkillSlot(idx + self.SLOTS_PER_ROW)

    def _EvClrSkill2(self, idx):
        self.OnClearSkillSlot(idx + self.SLOTS_PER_ROW)

    def _EvItem1(self, idx):
        self.OnItemSlot(idx)

    def _EvClrItem1(self, idx):
        self.OnClearItemSlot(idx)

    def _EvItem2(self, idx):
        self.OnItemSlot(idx + self.SLOTS_PER_ROW)

    def _EvClrItem2(self, idx):
        self.OnClearItemSlot(idx + self.SLOTS_PER_ROW)

    def _EvItem3(self, idx):
        self.OnItemSlot(idx + self.SLOTS_PER_ROW * 2)

    def _EvClrItem3(self, idx):
        self.OnClearItemSlot(idx + self.SLOTS_PER_ROW * 2)

    # --- showing the settings -------------------------------------------
    def Refresh(self):
        config = self.hunter.config
        for key, (btn, label, wyl) in self.toggles.items():
            if wyl:
                btn.SetText(WlWyl(config[key]))
            else:
                btn.SetText('%s: %s' % (label, YesNo(config[key])))
        for key, edit in self.edits.items():
            edit.SetText(str(config[key]))
        self.RefreshSlots()
        self.RefreshStatus()

    def RefreshSlots(self):
        config = self.hunter.config
        for i in xrange(self.SLOTS_PER_ROW):
            slot = config['skill%d_slot' % i]
            si = player.GetSkillIndex(slot) if slot else 0
            if si:
                self.skillSlots1.SetSkillSlotNew(i, si, player.GetSkillGrade(slot), player.GetSkillLevel(slot))
            else:
                self.skillSlots1.ClearSlot(i)
        self.skillSlots1.RefreshSlot()

        for i in xrange(self.SLOTS_PER_ROW):
            gi = i + self.SLOTS_PER_ROW
            slot = config['skill%d_slot' % gi]
            si = player.GetSkillIndex(slot) if slot else 0
            if si:
                self.skillSlots2.SetSkillSlotNew(i, si, player.GetSkillGrade(slot), player.GetSkillLevel(slot))
            else:
                self.skillSlots2.ClearSlot(i)
        self.skillSlots2.RefreshSlot()

        for i in xrange(self.SLOTS_PER_ROW):
            vnum = config[ITEM_SLOT_KEYS[i]]
            if vnum:
                self.itemSlots1.SetItemSlot(i, vnum, 0)
            else:
                self.itemSlots1.ClearSlot(i)
        self.itemSlots1.RefreshSlot()

        for i in xrange(self.SLOTS_PER_ROW):
            vnum = config[ITEM_SLOT_KEYS[i + self.SLOTS_PER_ROW]]
            if vnum:
                self.itemSlots2.SetItemSlot(i, vnum, 0)
            else:
                self.itemSlots2.ClearSlot(i)
        self.itemSlots2.RefreshSlot()

        for i in xrange(self.SLOTS_PER_ROW):
            vnum = config[ITEM_SLOT_KEYS[i + self.SLOTS_PER_ROW * 2]]
            if vnum:
                self.itemSlots3.SetItemSlot(i, vnum, 0)
            else:
                self.itemSlots3.ClearSlot(i)
        self.itemSlots3.RefreshSlot()

    def RefreshStatus(self):
        hunter = self.hunter
        if not hunter.running:
            self.statusText.SetText('Wy\xb3\xb9czone')
            return
        if hunter.justRevived:
            self.statusText.SetText('Czekam na HP (%d%%)' % hunter.RevivedShare())
            return
        if hunter.targetVid:
            self.statusText.SetText('Cel: %s' % chr.GetNameByVID(hunter.targetVid))
        elif hunter.lootVid:
            self.statusText.SetText('Podnosz\xea przedmiot')
        else:
            self.statusText.SetText('Szukam potwor\xf3w')

    def ReadEdits(self):
        for key, edit in self.edits.items():
            try:
                self.hunter.config[key] = max(0, int(edit.GetText() or 0))
            except ValueError:
                pass

    # --- events ---------------------------------------------------------
    def OnUpdate(self):
        now = app.GetTime()
        if now < self.nextStatus:
            return
        self.nextStatus = now + STATUS_INTERVAL
        self.RefreshStatus()

    def OnStart(self):
        self.ReadEdits()
        if not self.hunter.running:
            self.hunter.Start()
        self.RefreshStatus()

    def OnStop(self):
        self.ReadEdits()
        if self.hunter.running:
            self.hunter.Stop()
        self.RefreshStatus()

    def OnToggle(self, key):
        self.ReadEdits()
        self.hunter.config[key] = 0 if self.hunter.config[key] else 1
        self.Refresh()

    def OnSave(self):
        self.ReadEdits()
        if self.hunter.SaveConfig():
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto \xa3owy: ustawienia zapisane.')
        else:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto \xa3owy: nie uda\xb3o si\xea zapisa\xe6 ustawie\xf1.')

    def OnSkillSlot(self, index):
        attached = self.TakeAttached()
        if attached and attached[0] == player.SLOT_TYPE_SKILL:
            self.hunter.config['skill%d_slot' % index] = attached[1]
            self.RefreshSlots()

    def OnClearSkillSlot(self, index):
        self.hunter.config['skill%d_slot' % index] = 0
        self.RefreshSlots()

    def OnItemSlot(self, index):
        attached = self.TakeAttached()
        if attached and attached[0] == player.SLOT_TYPE_INVENTORY:
            self.hunter.config[ITEM_SLOT_KEYS[index]] = attached[2]
            self.RefreshSlots()

    def OnClearItemSlot(self, index):
        self.hunter.config[ITEM_SLOT_KEYS[index]] = 0
        self.RefreshSlots()

    def TakeAttached(self):
        controller = mouseModule.mouseController
        if not controller.isAttached():
            return None
        attached = (
            controller.GetAttachedType(),
            controller.GetAttachedSlotNumber(),
            controller.GetAttachedItemIndex(),
        )
        controller.DeattachObject()
        return attached

    def Close(self):
        self.ReadEdits()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Hide()
        self.hunter = None
        self.widgets = []
        self.edits = {}
        self.toggles = {}


class AutoHuntLootWindow(ui.BoardWithTitleBar):
    """The pick-up: whether it runs, what kinds it takes and how far the hunt
    reaches. A window of its own (Colide): the fight's window fits an 800x600
    screen without it, and it has room to grow a filter of what drops."""
    WIDTH = 300
    HEIGHT = 136

    def __init__(self, hunter):
        ui.BoardWithTitleBar.__init__(self)
        self.hunter = hunter
        self.widgets = []
        self.toggles = {}
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.SetTitleName('Auto \xa3owy - \xa3upy')
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.Build()

    def Build(self):
        BL = 10
        BW = self.WIDTH - 2 * BL
        y = 32

        pd_btn_start = 24
        pd_h = pd_btn_start + 3 * 22 + 4
        pdBoard = self._Board(BL, y, BW, pd_h)
        self._Label(pdBoard, 14, 4, 'Podnoszenie')
        pdy = pd_btn_start
        self._FlagBtn(pdBoard, 4, pdy, 'Podnie\x9c', 'pickup')
        for idx, (key, label, bit) in enumerate(LOOT_KINDS):
            pos = idx + 1
            col = pos % 3
            row = pos // 3
            self._FlagBtn(pdBoard, 4 + col * 92, pdy + row * 22, label, key)
        self.rangeButton = self._Btn(pdBoard, 'large', 4 + 2 * 92, pdy + 2 * 22, '', self.OnRange)

    def _Board(self, x, y, w, h):
        board = ui.ThinBoard()
        board.SetParent(self)
        board.SetPosition(x, y)
        board.SetSize(w, h)
        board.Show()
        self.widgets.append(board)
        return board

    def _Label(self, parent, x, y, text):
        line = ui.TextLine()
        line.SetParent(parent)
        line.SetPosition(x, y)
        line.SetText(text)
        line.Show()
        self.widgets.append(line)
        return line

    def _Btn(self, parent, size, x, y, text, event, *args):
        button = ui.Button()
        button.SetParent(parent)
        button.SetPosition(x, y)
        button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % size)
        button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % size)
        button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % size)
        button.SetText(text)
        button.SAFE_SetEvent(event, *args)
        button.Show()
        self.widgets.append(button)
        return button

    def _FlagBtn(self, parent, x, y, label, key):
        # A switch says what it is set to: a toggle button's pressed look was
        # read as off.
        btn = self._Btn(parent, 'large', x, y, '', self.OnToggle, key)
        self.toggles[key] = (btn, label, False)
        return btn

    def Refresh(self):
        config = self.hunter.config
        self.rangeButton.SetText('Zasi\xeag %d' % config['range'])
        for key, (btn, label, wyl) in self.toggles.items():
            btn.SetText('%s: %s' % (label, YesNo(config[key])))

    def ReadFightEdits(self):
        # The fight's numbers typed but not yet read go into the settings
        # first, or this click would save them as they were.
        if self.hunter.mainWindow:
            self.hunter.mainWindow.ReadEdits()

    def OnRange(self):
        self.ReadFightEdits()
        config = self.hunter.config
        ranges = list(RANGES)
        pos = ranges.index(config['range']) if config['range'] in ranges else -1
        config['range'] = ranges[(pos + 1) % len(ranges)]
        self.Refresh()

    def OnToggle(self, key):
        self.ReadFightEdits()
        self.hunter.config[key] = 0 if self.hunter.config[key] else 1
        self.Refresh()

    def Close(self):
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Hide()
        self.hunter = None
        self.widgets = []
        self.toggles = {}


_hunter = None


def GetHunter():
    global _hunter
    if _hunter is None:
        _hunter = Hunter()
    return _hunter


def ToggleWindow():
    GetHunter().ToggleWindow()


def OnServerTarget(value):
    GetHunter().OnServerTarget(value)


def OnServerLoot(vid, x, y):
    GetHunter().OnServerLoot(vid, x, y)
