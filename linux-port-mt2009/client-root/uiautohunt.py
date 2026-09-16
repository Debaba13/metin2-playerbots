# Auto Lowy: the player's auto-hunt.
#
# What the official system does (pl-wiki, "System - Auto Lowy"): attack the
# monsters round the character, cast the skills put in its slots on their own
# clocks, drink the potions put in its slots under a share of health or mana,
# use an item such as the cape on a clock, hit Metin stones when asked, keep
# going on a horse and stand up after dying. Here all of it is free and there is
# no premium half (Tieru, 15 September), so the premium's extra slots are
# everybody's: six skills, two potions and three items. What the official page
# does not describe and a player wants is a pick-up that leaves some things on
# the ground - "nie podnos broni, zbroi" (Tieru, 15 September) - so the pick-up
# goes by kind.
#
# The client cannot list the monsters or the items round its character - the
# scripts that do this without the server scan a million VIDs a frame - so it
# asks the server (do_autohunt_target and do_autohunt_loot, playerbotify.py):
#   "/autohunt_target <range> <stones> <dx> <dy>" -> "AutoHuntTarget <vid>",
#   the nearest monster this character may hit within the range of the point
#   the hunt started from, what is already hitting it first;
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
# ASCII.

import app
import chat
import chr
import mouseModule
import net
import player
import skill
import ui

import math

try:
	xrange
except NameError:
	xrange = range

SKILL_SLOTS = 6
USE_ITEM_SLOTS = 3
# Health potion, mana potion, and the items used on a clock (the cape).
ITEM_SLOT_KEYS = ('hp_vnum', 'sp_vnum') + tuple('item%d_vnum' % i for i in xrange(USE_ITEM_SLOTS))
ITEM_EDIT_KEYS = ('hp_percent', 'sp_percent') + tuple('item%d_interval' % i for i in xrange(USE_ITEM_SLOTS))
RANGES = (1000, 2000, 3000, 4000)
# What the pick-up takes, as the server reads a kind (AutoHuntLootKind): the
# config key, the button's word and the bit. Yang is taken with every kind.
LOOT_KINDS = (
	('loot_weapon', 'Bron', 1 << 0),
	('loot_armour', 'Zbroje', 1 << 1),
	('loot_jewellery', 'Ozdoby', 1 << 2),
	('loot_potion', 'Mikstury', 1 << 3),
	('loot_book', 'Ksiegi', 1 << 4),
	('loot_stone', 'Kamienie', 1 << 5),
	('loot_other', 'Inne', 1 << 6),
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

DEFAULTS = [
	('range', 2000), ('stones', 0), ('pickup', 1), ('revive', 1), ('revive_after', 15), ('return', 1),
	('hp_vnum', 0), ('hp_percent', 60), ('sp_vnum', 0), ('sp_percent', 40),
]
for _index in xrange(USE_ITEM_SLOTS):
	DEFAULTS.append(('item%d_vnum' % _index, 0))
	DEFAULTS.append(('item%d_interval' % _index, 30))
for _index in xrange(SKILL_SLOTS):
	DEFAULTS.append(('skill%d_slot' % _index, 0))
	DEFAULTS.append(('skill%d_interval' % _index, 0))
for _key, _label, _bit in LOOT_KINDS:
	DEFAULTS.append((_key, 1))
# A file saved by the window that drew these switches as toggle buttons has
# no version: their pressed look read as "off", and one click on Podnos
# turned the whole pick-up off (autohunt_Tieru.cfg, 15 September: pickup=0
# and every kind 0, and "postac nic nie podnosi"). Such a file gets the
# pick-up back once (ConfigFromText).
CONFIG_VERSION = 2
DEFAULTS.append(('config_version', CONFIG_VERSION))


def DefaultConfig():
	return dict(DEFAULTS)


def ApplyConfigText(config, text):
	"""Reads "key=value" lines into ``config``; unknown keys and bad numbers are
	skipped, so a file from another version cannot break the window."""
	for line in text.splitlines():
		key, _, value = line.partition('=')
		key = key.strip()
		if key not in config:
			continue
		try:
			config[key] = max(0, int(value.strip()))
		except ValueError:
			pass
	return config


def ConfigFromText(text):
	"""A saved file read into the defaults, the pick-up switched back on for a
	file older than CONFIG_VERSION."""
	config = ApplyConfigText(DefaultConfig(), text)
	if 'config_version=' not in text:
		config['pickup'] = 1
		for key, label, bit in LOOT_KINDS:
			config[key] = 1
	config['config_version'] = CONFIG_VERSION
	return config


def ConfigText(config):
	return ''.join('%s=%d\n' % (key, config[key]) for key, _ in DEFAULTS)


def ConfigPath(name):
	safe = ''.join(c if c.isalnum() else '_' for c in (name or 'postac'))
	return 'autohunt_%s.cfg' % safe


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


def YesNo(value):
	return 'tak' if value else 'nie'


class Hunter(object):
	"""The hunt itself, driven by the game's updateables (CanUpdate, OnUpdate,
	Destroy) whether or not the window is open."""

	def __init__(self):
		self.config = DefaultConfig()
		self.configName = None
		self.running = False
		self.window = None
		self.ResetState()

	def ResetState(self):
		self.targetVid = 0
		self.attacking = False
		self.anchor = (0, 0)
		self.nextRequest = 0.0
		self.nextMove = 0.0
		self.nextFace = 0.0
		self.nextPotion = 0.0
		self.nextRevive = 0.0
		self.deadSince = 0.0
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
		self.deadSince = 0.0
		self.DrinkPotions(now)
		self.UseItems(now)
		self.AskForLoot(now)
		self.Chase(now)
		self.CastSkills(now)

	def Destroy(self):
		# The game window is closing (a warp or a logout) and the chat with it,
		# so this stop says nothing.
		self.Stop(quiet=True)
		if self.window:
			self.window.Destroy()
			self.window = None

	# --- start and stop -------------------------------------------------
	def Start(self):
		if self.running:
			return
		self.ResetState()
		(x, y, z) = player.GetMainCharacterPosition()
		self.anchor = (int(x), int(y))
		self.running = True
		chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto Lowy: start, zasieg %d.' % self.config['range'])
		if not LootMask(self.config):
			chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto Lowy: podnoszenie jest wylaczone (Podnos: nie).')

	def Stop(self, quiet=False):
		if not self.running:
			return
		self.running = False
		self.ReleaseAttack()
		self.targetVid = 0
		self.lootVid = 0
		if not quiet:
			chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto Lowy: stop.')

	def OnServerTarget(self, value):
		if not self.running:
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
			net.SendChatPacket('/restart_here')

	def DrinkPotions(self, now):
		if now < self.nextPotion:
			return
		for (vnumKey, percentKey, point, maxPoint) in (
				('hp_vnum', 'hp_percent', player.HP, player.MAX_HP),
				('sp_vnum', 'sp_percent', player.SP, player.MAX_SP)):
			vnum = self.config[vnumKey]
			maxValue = player.GetStatus(maxPoint)
			if not vnum or maxValue <= 0:
				continue
			if player.GetStatus(point) * 100 >= maxValue * self.config[percentKey]:
				continue
			cell = FindInventoryCell(vnum)
			if cell >= 0:
				net.SendItemUsePacket(cell)
				self.nextPotion = now + POTION_INTERVAL
				return

	def UseItems(self, now):
		for index in xrange(USE_ITEM_SLOTS):
			vnum = self.config['item%d_vnum' % index]
			interval = self.config['item%d_interval' % index]
			if not vnum or interval <= 0 or now < self.itemNext[index]:
				continue
			self.itemNext[index] = now + max(ITEM_MIN_INTERVAL, interval)
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
		if now >= self.nextRequest:
			self.nextRequest = now + TARGET_REQUEST_INTERVAL
			(dx, dy) = self.AnchorOffset()
			net.SendChatPacket('/autohunt_target %d %d %d %d' % (
				self.config['range'], 1 if self.config['stones'] else 0, dx, dy))

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
		# In a fight only: an attack skill needs its target in reach, and a buff
		# is worth casting when there is something to fight.
		if not self.attacking:
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
		try:
			with open(ConfigPath(name), 'r') as handle:
				self.config = ConfigFromText(handle.read())
		except (IOError, OSError):
			pass

	def SaveConfig(self):
		try:
			with open(ConfigPath(self.configName), 'w') as handle:
				handle.write(ConfigText(self.config))
			return True
		except (IOError, OSError):
			return False

	def ToggleWindow(self):
		self.LoadConfig()
		if self.window is None:
			self.window = AutoHuntWindow(self)
		if self.window.IsShow():
			self.window.Close()
		else:
			self.window.Refresh()
			self.window.Show()
			self.window.SetTop()


class AutoHuntWindow(ui.BoardWithTitleBar):
	WIDTH = 332
	HEIGHT = 402
	SLOT_STEP = 45
	BUTTON_STEP = 78

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
		self.SetTitleName('Auto Lowy')
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.Build()
		self.SetCenterPosition()

	def Build(self):
		step = self.BUTTON_STEP
		self.startButton = self.MakeButton('large', 15, 35, 'Start', self.OnStartStop)
		self.statusText = self.MakeText(115, 40, 'Wylaczone')
		self.rangeButton = self.MakeButton('middle', 15, 66, '', self.OnRange)
		self.stonesButton = self.MakeButton('middle', 15 + step, 66, '', self.OnToggle, 'stones')
		self.reviveButton = self.MakeButton('middle', 15 + 2 * step, 66, '', self.OnToggle, 'revive')
		self.returnButton = self.MakeButton('middle', 15 + 3 * step, 66, '', self.OnToggle, 'return')
		self.MakeText(15, 96, 'Wstawaj po sekundach:')
		self.MakeEdit('revive_after', 145, 94, 32, 3)

		self.MakeText(15, 120, 'Podnoszenie (kliknij, aby zmienic):')
		self.MakeFlagButton(15, 138, 'Podnos', 'pickup')
		for index, (key, label, bit) in enumerate(LOOT_KINDS):
			column = (index + 1) % 4
			row = (index + 1) // 4
			self.MakeFlagButton(15 + column * step, 138 + row * 24, label, key)

		self.MakeText(15, 192, 'Umiejetnosci z okna V, co ile sekund (PPM usuwa):')
		self.skillSlots = self.MakeSlots(15, 210, SKILL_SLOTS, self.OnSkillSlot, self.OnClearSkillSlot)
		for index in xrange(SKILL_SLOTS):
			self.MakeEdit('skill%d_interval' % index, 15 + index * self.SLOT_STEP, 246, 32, 3)

		self.MakeText(15, 274, 'Mikstury PZ i PE (%), przedmioty co ile sekund:')
		self.itemSlots = self.MakeSlots(15, 292, len(ITEM_SLOT_KEYS), self.OnItemSlot, self.OnClearItemSlot)
		for index, key in enumerate(ITEM_EDIT_KEYS):
			self.MakeEdit(key, 15 + index * self.SLOT_STEP, 328, 32, 4)

		self.MakeButton('middle', 15, 362, 'Zapisz', self.OnSave)
		self.MakeButton('middle', 15 + step, 362, 'Zamknij', self.Close)

	def MakeText(self, x, y, text):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		self.widgets.append(line)
		return line

	def MakeButton(self, size, x, y, text, event, *args):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % size)
		button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % size)
		button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % size)
		button.SetText(text)
		button.SAFE_SetEvent(event, *args)
		button.Show()
		self.widgets.append(button)
		return button

	def MakeFlagButton(self, x, y, label, key):
		# A switch says what it is set to, like Metiny/Wstawaj/Wracaj: a toggle
		# button's pressed look was read as off.
		button = self.MakeButton('middle', x, y, '', self.OnToggle, key)
		self.toggles[key] = (button, label)
		return button

	def MakeSlots(self, x, y, count, onSelect, onUnselect):
		slots = ui.SlotWindow()
		slots.SetParent(self)
		slots.SetPosition(x, y)
		slots.SetSize(count * self.SLOT_STEP, 32)
		for index in xrange(count):
			slots.AppendSlot(index, index * self.SLOT_STEP, 0, 32, 32)
		slots.SetSlotBaseImage('d:/ymir work/ui/public/slot_base.sub', 1.0, 1.0, 1.0, 1.0)
		slots.SetSelectEmptySlotEvent(ui.__mem_func__(onSelect))
		slots.SetSelectItemSlotEvent(ui.__mem_func__(onSelect))
		slots.SetUnselectItemSlotEvent(ui.__mem_func__(onUnselect))
		slots.Show()
		self.widgets.append(slots)
		return slots

	def MakeEdit(self, key, x, y, width, length):
		bar = ui.SlotBar()
		bar.SetParent(self)
		bar.SetPosition(x, y)
		bar.SetSize(width, 16)
		bar.Show()
		edit = ui.EditLine()
		edit.SetParent(bar)
		edit.SetPosition(4, 1)
		edit.SetSize(width - 6, 14)
		edit.SetMax(length)
		edit.SetNumberMode()
		edit.Show()
		self.widgets.append(bar)
		self.widgets.append(edit)
		self.edits[key] = edit

	# --- showing the settings -------------------------------------------
	def Refresh(self):
		config = self.hunter.config
		self.rangeButton.SetText('Zasieg %d' % config['range'])
		self.stonesButton.SetText('Metiny: %s' % YesNo(config['stones']))
		self.reviveButton.SetText('Wstawaj: %s' % YesNo(config['revive']))
		self.returnButton.SetText('Wracaj: %s' % YesNo(config['return']))
		for key, (button, label) in self.toggles.items():
			button.SetText('%s: %s' % (label, YesNo(config[key])))
		for key, edit in self.edits.items():
			edit.SetText(str(config[key]))
		self.RefreshSlots()
		self.RefreshStatus()

	def RefreshSlots(self):
		config = self.hunter.config
		for index in xrange(SKILL_SLOTS):
			slot = config['skill%d_slot' % index]
			skillIndex = player.GetSkillIndex(slot) if slot else 0
			if skillIndex:
				self.skillSlots.SetSkillSlotNew(index, skillIndex, player.GetSkillGrade(slot), player.GetSkillLevel(slot))
			else:
				self.skillSlots.ClearSlot(index)
		self.skillSlots.RefreshSlot()
		for index, key in enumerate(ITEM_SLOT_KEYS):
			if config[key]:
				self.itemSlots.SetItemSlot(index, config[key], 0)
			else:
				self.itemSlots.ClearSlot(index)
		self.itemSlots.RefreshSlot()

	def RefreshStatus(self):
		hunter = self.hunter
		if not hunter.running:
			self.startButton.SetText('Start')
			self.statusText.SetText('Wylaczone')
			return
		self.startButton.SetText('Stop')
		if hunter.targetVid:
			self.statusText.SetText('Cel: %s' % chr.GetNameByVID(hunter.targetVid))
		elif hunter.lootVid:
			self.statusText.SetText('Podnosze przedmiot')
		else:
			self.statusText.SetText('Szukam potworow')

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

	def OnStartStop(self):
		self.ReadEdits()
		if self.hunter.running:
			self.hunter.Stop()
		else:
			self.hunter.Start()
		self.RefreshStatus()

	def OnRange(self):
		self.ReadEdits()
		config = self.hunter.config
		ranges = list(RANGES)
		position = ranges.index(config['range']) if config['range'] in ranges else -1
		config['range'] = ranges[(position + 1) % len(ranges)]
		self.Refresh()

	def OnToggle(self, key):
		self.ReadEdits()
		self.hunter.config[key] = 0 if self.hunter.config[key] else 1
		self.Refresh()

	def OnSave(self):
		self.ReadEdits()
		if self.hunter.SaveConfig():
			chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto Lowy: ustawienia zapisane.')
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, 'Auto Lowy: nie udalo sie zapisac ustawien.')

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
		attached = (controller.GetAttachedType(), controller.GetAttachedSlotNumber(), controller.GetAttachedItemIndex())
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
