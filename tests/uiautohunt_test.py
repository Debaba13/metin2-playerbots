# Auto Lowy without a client: the hunt's decisions against stub client modules.
#
#     python tests/uiautohunt_test.py
#
# Runs on Python 3 and on the client's Python 2.7
# (docker run --rm -v "$PWD":/w -w /w python:2.7 python tests/uiautohunt_test.py).
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_ROOT = os.path.normpath(os.path.join(HERE, '..', 'linux-port-mt2009', 'client-root'))

STATE = {}


def reset_state():
	STATE.clear()
	STATE.update({
		'now': 100.0, 'chat': [], 'commands': [], 'used': [], 'race': 0, 'group': 1,
		'status': {1: 100, 2: 100, 3: 100, 4: 100}, 'pos': (1000, 1000), 'distance': {},
		'where': {}, 'bag': {}, 'targets': [], 'attack': [], 'picked': [], 'skills': {},
		'cooling': set(), 'active': set(), 'cast': [], 'walks': [], 'rotations': [],
		'toggles': set(),
	})


def module(name, **attrs):
	mod = types.ModuleType(name)
	for key, value in attrs.items():
		setattr(mod, key, value)
	return mod


class StubBoard(object):
	pass


def install_stubs():
	sys.modules['app'] = module('app', GetTime=lambda: STATE['now'])
	sys.modules['chat'] = module('chat', CHAT_TYPE_INFO=1, AppendChat=lambda kind, text: STATE['chat'].append(text))
	sys.modules['net'] = module(
		'net',
		SendChatPacket=lambda text: STATE['commands'].append(text),
		SendItemUsePacket=lambda cell: STATE['used'].append(cell),
		SendItemPickUpPacket=lambda vid: STATE['picked'].append(vid),
		GetMainActorRace=lambda: STATE['race'],
		GetMainActorSkillGroup=lambda: STATE['group'])
	sys.modules['player'] = module(
		'player', HP=1, MAX_HP=2, SP=3, MAX_SP=4, INVENTORY_MAX_NUM=90, SLOT_TYPE_INVENTORY=1, SLOT_TYPE_SKILL=2,
		GetStatus=lambda point: STATE['status'][point],
		GetMainCharacterIndex=lambda: 7,
		GetMainCharacterName=lambda: 'Tester',
		GetMainCharacterPosition=lambda: (STATE['pos'][0], STATE['pos'][1], 0),
		GetCharacterDistance=lambda vid: STATE['distance'].get(vid, -1),
		GetItemIndex=lambda cell: STATE['bag'].get(cell, 0),
		SetTarget=lambda vid: STATE['targets'].append(vid),
		SetAttackKeyState=lambda on: STATE['attack'].append(on),
		GetSkillIndex=lambda slot: STATE['skills'].get(slot, 0),
		IsSkillCoolTime=lambda slot: slot in STATE['cooling'],
		IsSkillActive=lambda slot: slot in STATE['active'],
		ClickSkillSlot=lambda slot: STATE['cast'].append(slot))
	sys.modules['chr'] = module(
		'chr',
		GetPixelPosition=lambda vid: STATE['where'][vid],
		MoveToDestPosition=lambda vid, x, y: STATE['walks'].append((x, y)),
		SelectInstance=lambda vid: None,
		SetRotation=lambda degree: STATE['rotations'].append(degree),
		GetNameByVID=lambda vid: 'Wilk')
	sys.modules['skill'] = module('skill', IsToggleSkill=lambda index: index in STATE['toggles'])
	sys.modules['mouseModule'] = module('mouseModule')
	ui = module('ui', BoardWithTitleBar=StubBoard)
	setattr(ui, '__mem_func__', lambda func: func)
	sys.modules['ui'] = ui


reset_state()
install_stubs()
sys.path.insert(0, CLIENT_ROOT)
import uiautohunt  # noqa: E402


def step(hunter, seconds=0.0):
	STATE['now'] += seconds
	hunter.OnUpdate()


def commands(prefix):
	return [text for text in STATE['commands'] if text.startswith(prefix)]


class HelpersTest(unittest.TestCase):
	def test_config_round_trip_ignores_what_it_does_not_know(self):
		config = uiautohunt.DefaultConfig()
		config['range'] = 3000
		config['skill5_slot'] = 5
		config['item2_vnum'] = 70038
		config['loot_armour'] = 0
		text = uiautohunt.ConfigText(config) + 'nonsense=1\nhp_percent=abc\nsp_percent=-7\n'
		loaded = uiautohunt.ApplyConfigText(uiautohunt.DefaultConfig(), text)
		self.assertEqual(loaded['range'], 3000)
		self.assertEqual(loaded['skill5_slot'], 5)
		self.assertEqual(loaded['item2_vnum'], 70038)
		self.assertEqual(loaded['loot_armour'], 0)
		self.assertEqual(loaded['hp_percent'], 60)
		self.assertEqual(loaded['sp_percent'], 0)
		self.assertNotIn('nonsense', loaded)

	def test_an_old_config_file_keeps_the_new_defaults(self):
		loaded = uiautohunt.ApplyConfigText(uiautohunt.DefaultConfig(), 'range=1000\npickup=1\n')
		self.assertEqual(loaded['range'], 1000)
		self.assertEqual(uiautohunt.LootMask(loaded), 127)

	def test_a_file_from_the_toggle_window_gets_the_pick_up_back(self):
		old = 'range=3000\npickup=0\nloot_weapon=0\nloot_other=0\n'
		loaded = uiautohunt.ConfigFromText(old)
		self.assertEqual(loaded['range'], 3000)
		self.assertEqual(loaded['pickup'], 1)
		self.assertEqual(uiautohunt.LootMask(loaded), 127)
		self.assertEqual(loaded['config_version'], uiautohunt.CONFIG_VERSION)

	def test_a_current_file_keeps_the_pick_up_off(self):
		config = uiautohunt.DefaultConfig()
		config['pickup'] = 0
		loaded = uiautohunt.ConfigFromText(uiautohunt.ConfigText(config))
		self.assertEqual(loaded['pickup'], 0)
		self.assertEqual(uiautohunt.LootMask(loaded), 0)

	def test_target_vid(self):
		self.assertEqual(uiautohunt.ParseTargetVid('123'), 123)
		self.assertEqual(uiautohunt.ParseTargetVid('0'), 0)
		self.assertEqual(uiautohunt.ParseTargetVid('-5'), 0)
		self.assertEqual(uiautohunt.ParseTargetVid('wilk'), 0)
		self.assertEqual(uiautohunt.ParseTargetVid(None), 0)

	def test_loot_answer(self):
		self.assertEqual(uiautohunt.ParseLoot('7', '100', '200'), (7, 100, 200))
		self.assertEqual(uiautohunt.ParseLoot('0', '100', '200'), (0, 0, 0))
		self.assertEqual(uiautohunt.ParseLoot('7', 'x', '200'), (0, 0, 0))

	def test_loot_mask_follows_the_toggles(self):
		config = uiautohunt.DefaultConfig()
		self.assertEqual(uiautohunt.LootMask(config), 127)
		config['loot_weapon'] = 0
		config['loot_armour'] = 0
		self.assertEqual(uiautohunt.LootMask(config), 124)
		config['pickup'] = 0
		self.assertEqual(uiautohunt.LootMask(config), 0)

	def test_stop_point_and_facing(self):
		self.assertEqual(uiautohunt.StopPoint(0, 0, 1000, 0, 120), (880.0, 0.0))
		self.assertEqual(uiautohunt.StopPoint(0, 0, 100, 0, 120), (0, 0))
		for target in ((0, 100), (100, 0), (-100, 0), (0, -100), (70, 70)):
			degree = uiautohunt.FacingDegree(0, 0, target[0], target[1])
			self.assertTrue(0.0 <= degree <= 360.0, (target, degree))

	def test_config_path_keeps_names_to_letters(self):
		self.assertEqual(uiautohunt.ConfigPath('Ab c/1'), 'autohunt_Ab_c_1.cfg')


class HuntTest(unittest.TestCase):
	def setUp(self):
		reset_state()
		self.hunter = uiautohunt.Hunter()
		self.hunter.Start()

	def test_asks_the_server_from_the_start_point(self):
		step(self.hunter)
		self.assertEqual(commands('/autohunt_target'), ['/autohunt_target 2000 0 0 0'])
		self.assertEqual(commands('/autohunt_loot'), ['/autohunt_loot 2000 127 0 0'])
		step(self.hunter, 0.5)
		self.assertEqual(len(commands('/autohunt_target')), 1)
		step(self.hunter, 0.4)
		self.assertEqual(len(commands('/autohunt_target')), 2)
		self.assertEqual(len(commands('/autohunt_loot')), 1)
		step(self.hunter, 0.2)
		self.assertEqual(len(commands('/autohunt_loot')), 2)

	def test_no_loot_question_when_the_pick_up_is_off(self):
		self.hunter.config['pickup'] = 0
		step(self.hunter)
		self.assertEqual(commands('/autohunt_loot'), [])
		self.hunter.OnServerLoot('77', '50', '0')
		step(self.hunter, 1.0)
		self.assertEqual(STATE['picked'], [])

	def test_walks_to_the_target_then_swings_and_casts_once(self):
		self.hunter.config['skill0_slot'] = 1
		STATE['skills'][1] = 3
		self.hunter.OnServerTarget('55')
		STATE['where'][55] = (1500, 1000, 0)
		STATE['distance'][55] = 500
		step(self.hunter)
		self.assertEqual(STATE['walks'], [(1380, 1000)])
		self.assertEqual(STATE['attack'], [])
		STATE['distance'][55] = 150
		step(self.hunter, 0.1)
		self.assertEqual(STATE['targets'], [55])
		self.assertEqual(STATE['attack'], [True])
		self.assertEqual(len(STATE['rotations']), 1)
		self.assertEqual(STATE['cast'], [1])
		step(self.hunter, 1.0)
		self.assertEqual(STATE['cast'], [1])
		step(self.hunter, 0.6)
		self.assertEqual(STATE['cast'], [1, 1])

	def test_casts_the_sixth_skill_slot(self):
		self.hunter.config['skill5_slot'] = 9
		STATE['skills'][9] = 4
		STATE['where'][55] = (1100, 1000, 0)
		STATE['distance'][55] = 100
		self.hunter.OnServerTarget('55')
		step(self.hunter)
		self.assertEqual(STATE['cast'], [9])

	def test_a_new_target_releases_the_attack_key(self):
		STATE['where'][55] = (1100, 1000, 0)
		STATE['distance'][55] = 100
		self.hunter.OnServerTarget('55')
		step(self.hunter)
		self.assertEqual(STATE['attack'], [True])
		self.hunter.OnServerTarget('0')
		self.assertEqual(STATE['attack'], [True, False])
		self.assertEqual(self.hunter.targetVid, 0)

	def test_walks_to_loot_and_picks_it_up(self):
		self.hunter.OnServerLoot('77', '600', '0')
		step(self.hunter)
		self.assertEqual(STATE['walks'][-1], (1600, 1000))
		self.assertEqual(STATE['picked'], [])
		STATE['pos'] = (1500, 1000)
		step(self.hunter, 0.4)
		self.assertEqual(STATE['picked'], [77])
		self.assertEqual(self.hunter.lootVid, 0)

	def test_takes_loot_at_its_feet_during_a_fight(self):
		STATE['where'][55] = (1100, 1000, 0)
		STATE['distance'][55] = 100
		self.hunter.OnServerTarget('55')
		self.hunter.OnServerLoot('77', '50', '0')
		step(self.hunter)
		self.assertEqual(STATE['attack'], [True])
		self.assertEqual(STATE['picked'], [77])

	def test_leaves_loot_it_cannot_reach_alone_for_a_while(self):
		self.hunter.OnServerLoot('77', '2000', '0')
		step(self.hunter)
		step(self.hunter, 6.5)
		self.assertEqual(self.hunter.lootVid, 0)
		self.hunter.OnServerLoot('77', '2000', '0')
		self.assertEqual(self.hunter.lootVid, 0)
		asked = len(commands('/autohunt_loot'))
		step(self.hunter, 2.0)
		self.assertEqual(len(commands('/autohunt_loot')), asked)

	def test_uses_the_third_item_on_its_clock(self):
		self.hunter.config['item2_vnum'] = 70038
		self.hunter.config['item2_interval'] = 5
		STATE['bag'][3] = 70038
		step(self.hunter)
		self.assertEqual(STATE['used'], [3])
		step(self.hunter, 4.0)
		self.assertEqual(STATE['used'], [3])
		step(self.hunter, 1.5)
		self.assertEqual(STATE['used'], [3, 3])

	def test_drinks_below_the_share_and_not_twice_a_second(self):
		self.hunter.config['hp_vnum'] = 27001
		STATE['bag'][5] = 27001
		STATE['status'][1] = 30
		step(self.hunter)
		self.assertEqual(STATE['used'], [5])
		step(self.hunter, 0.5)
		self.assertEqual(STATE['used'], [5])
		step(self.hunter, 0.6)
		self.assertEqual(STATE['used'], [5, 5])

	def test_stands_up_after_the_wait(self):
		STATE['status'][1] = 0
		step(self.hunter)
		step(self.hunter, 14.0)
		self.assertNotIn('/restart_here', STATE['commands'])
		step(self.hunter, 1.5)
		self.assertIn('/restart_here', STATE['commands'])

	def test_gives_up_on_a_target_it_cannot_reach(self):
		STATE['where'][55] = (2000, 1000, 0)
		STATE['distance'][55] = 900
		self.hunter.OnServerTarget('55')
		step(self.hunter)
		step(self.hunter, 8.5)
		self.assertEqual(self.hunter.targetVid, 0)
		self.assertEqual(STATE['walks'][-1], (1000, 1000))

	def test_names_the_target_it_gave_up_on_for_a_minute(self):
		self.hunter.config['stones'] = 1
		STATE['where'][55] = (2000, 1000, 0)
		STATE['distance'][55] = 900
		self.hunter.OnServerTarget('55')
		step(self.hunter)
		self.assertEqual(commands('/autohunt_target'), ['/autohunt_target 2000 1 0 0'])
		step(self.hunter, 8.5)
		self.assertEqual(self.hunter.targetVid, 0)
		del STATE['commands'][:]
		step(self.hunter, 2.5)
		self.assertEqual(commands('/autohunt_target'), ['/autohunt_target 2000 1 0 0 55'])
		del STATE['commands'][:]
		step(self.hunter, 60.0)
		self.assertEqual(commands('/autohunt_target'), ['/autohunt_target 2000 1 0 0'])

	def test_an_archer_shoots_from_afar(self):
		STATE['race'] = 5
		STATE['group'] = 2
		STATE['where'][55] = (1700, 1000, 0)
		STATE['distance'][55] = 700
		self.hunter.OnServerTarget('55')
		step(self.hunter)
		self.assertEqual(STATE['attack'], [True])
		self.assertEqual(STATE['walks'], [])

	def test_walks_back_when_idle_far_from_the_start(self):
		STATE['pos'] = (2000, 1000)
		step(self.hunter)
		self.assertEqual(STATE['walks'], [(1000, 1000)])

	def test_fetches_drops_before_a_far_target(self):
		STATE['where'][55] = (1500, 1000, 0)
		STATE['distance'][55] = 500
		self.hunter.OnServerTarget('55')
		self.hunter.OnServerLoot('77', '700', '0')
		step(self.hunter)
		self.assertEqual(STATE['walks'][-1], (1700, 1000))
		self.assertEqual(STATE['attack'], [])

	def test_a_fight_in_reach_comes_before_drops(self):
		STATE['where'][55] = (1100, 1000, 0)
		STATE['distance'][55] = 100
		self.hunter.OnServerTarget('55')
		self.hunter.OnServerLoot('77', '700', '0')
		step(self.hunter)
		self.assertEqual(STATE['attack'], [True])
		self.assertEqual(STATE['walks'], [])

	def test_picks_up_from_four_hundred_and_fifty(self):
		self.hunter.OnServerLoot('77', '440', '0')
		step(self.hunter)
		self.assertEqual(STATE['picked'], [77])

	def test_the_start_point_goes_as_an_offset(self):
		STATE['pos'] = (1500, 800)
		step(self.hunter)
		self.assertEqual(commands('/autohunt_target'), ['/autohunt_target 2000 0 -500 200'])
		self.assertEqual(commands('/autohunt_loot'), ['/autohunt_loot 2000 127 -500 200'])

	def test_the_loot_answer_is_an_offset_from_the_character(self):
		STATE['pos'] = (5000, 7000)
		self.hunter.OnServerLoot('77', '-300', '400')
		self.assertEqual(self.hunter.lootPos, (4700, 7400))

	def test_destroy_stops_without_a_word(self):
		messages = len(STATE['chat'])
		self.hunter.Destroy()
		self.assertFalse(self.hunter.running)
		self.assertEqual(len(STATE['chat']), messages)


if __name__ == '__main__':
	unittest.main()
