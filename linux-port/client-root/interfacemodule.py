##
## Interface
##
import constInfo
import systemSetting
import wndMgr
import chat
import app
import player
import uiTaskBar
import uiCharacter
import uiInventory
import uiDragonSoul
import uiChat
import uiMessenger
import guild

import ui
import uiHelp
import uiWhisper
import uiPointReset
import uiShop
import uiExchange
import uiSystem
import uiRestart
import uiToolTip
import uiMiniMap
import uiParty
import uiSafebox
import net
import uiGuild
import uiQuest
import uiPrivateShopBuilder
import uiCommon
import uiRefine
import uiEquipmentDialog
import uiGameButton
import uiTip
import uiCube
import chr
import miniMap
# ACCESSORY_REFINE_ADD_METIN_STONE
import uiselectitem
# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE
import uiScriptLocale

import event
import localeInfo

# F9 GM panel (2026-09-09). Merged directly into interfacemodule.py rather
# than living in its own uiGMPanel.py: EPack32 on this project only refreshes
# files the packed root.epk already knows about, it does not auto-add brand
# new filenames, so a standalone module here never made it into the archive.
# interfacemodule.py is already tracked, so its content updates fine.
GM_PANEL_LOOKUP_FIELD_ORDER = [
	"lk_name", "lk_level", "lk_job", "lk_hp", "lk_mp", "lk_exp", "lk_gold",
	"lk_st", "lk_ht", "lk_dx", "lk_iq", "lk_statpt", "lk_skillpt",
	"lk_subskillpt", "lk_map", "lk_lastplay", "lk_horselvl", "lk_horsept",
	"lk_account", "lk_ip", "lk_playtime", "lk_range",
]

GM_PANEL_LOOKUP_LAYOUT = [
	("lk_name",		"Nick:"),
	("lk_level",	"Level:"),
	("lk_job",		"Klasa:"),
	("lk_hp",		"HP:"),
	("lk_mp",		"MP:"),
	("lk_exp",		"Exp:"),
	("lk_gold",		"Yang:"),
	("lk_st",		"Sil:"),
	("lk_ht",		"Wit:"),
	("lk_dx",		"ZR:"),
	("lk_iq",		"Int:"),
	("lk_statpt",	"Punkty statusu:"),
	("lk_skillpt",	"Punkty umiej.:"),
	("lk_subskillpt","Punkty umiej. (dod.):"),
	("lk_map",		"Mapa (index):"),
	("lk_lastplay",	"Ostatnio online:"),
	("lk_horselvl",	"Level konia:"),
	("lk_horsept",	"Punkty konne:"),
	("lk_account",	"Konto:"),
	("lk_ip",		"IP:"),
	("lk_playtime",	"Czas gry (min):"),
	("lk_range",	"Punkty range:"),
]

GM_PANEL_JOB_NAMES = {
	0 : "Wojownik (M)", 1 : "Wojowniczka (K)",
	2 : "Ninja (M)", 3 : "Ninja (K)",
	4 : "Sura (M)", 5 : "Sura (K)",
	6 : "Szaman (M)", 7 : "Szamanka (K)",
}

GM_PANEL_PAGE_NAMES = [
	"page_main", "page_addgm", "page_lookup", "page_createitem",
	"page_ban", "page_spawnbots", "page_spawnmobs",
	# Sub-pages of "Sprawdz Gracza"/"Spawn Mobow" opened by their action
	# buttons - not real tabs (no tab_* counterpart / no tab button), only
	# reachable via __SetPage from their parent tab and returning the same
	# way.
	"page_giveamount", "page_setvalue", "page_setstat", "page_skills",
	"page_gmcommands",
]
GM_PANEL_TAB_NAMES = [
	"tab_main", "tab_addgm", "tab_lookup", "tab_createitem",
	"tab_ban", "tab_spawnbots", "tab_spawnmobs",
]

GM_PANEL_TAB_LABELS = {
	"tab_main"			: "Glowny Panel",
	"tab_addgm"			: "Dodaj GM",
	"tab_lookup"		: "Sprawdz Gracza",
	"tab_createitem"	: "Utworz Przedmiot",
	"tab_ban"			: "Blokada Konta",
	"tab_spawnbots"		: "Spawn Botow",
	"tab_spawnmobs"		: "Spawn Mobow",
}

# Reference-only (client never sends this to the server) - the "Lista
# komend GM" button on Spawn Mobow just renders this scrollable list as-is,
# copied from the community command list the user provided. cmd_info[] in
# cmd.cpp has no description field to enumerate at runtime, so a curated
# static list is the only way to show what each command actually does.
GM_COMMANDS_LIST = [
	"/item - dodaje przedmiot",
	"/item - dodaje kilka sztuk przedmiotu",
	"/m - przywoluje potwora lub npc",
	"/p - zamiana w potwora lub npc",
	"/set align 200000 - ranga rycerski",
	"/weak - najpierw klikamy na potwora ppm, nastepnie wpisujemy komende i potwor ma 1hp",
	"/ski 121 - Dowodzenie",
	"/ski 131 - Przywolaj Konia",
	"/ski 124 - MPCictwo",
	"/ski 125 - Kowalstwo",
	"/xmas 0 - Dzien",
	"/xmas 1 - Noc",
	"/inv - niewidzialnosc",
	"/dc - wyrzuca kogos z serwera",
	"/warp - przenosi GM'a do gracza",
	"/transfer - przenosi gracza do GM'a",
	"/go x y - przenosi do wspolrzednych x y",
	"/go s - teleport na Gore Sohan",
	"/go t - teleport do Doliny Orkow",
	"/go m - teleport do Swiatynii Hwang",
	"/go f - teleport do Piekla",
	"/go tr - teleport do Lasu Duchow",
	"/go trent2 - teleport do Czerwonego Lasu",
	"/xmas_snow 0 - wylacz snieg",
	"/xmas_snow 1 - wlacz snieg",
	"/set max_hp - zwieksza punkty zycia",
	"/set max_sp - zwieksza punkty energii",
	"/n - Wiadomosc na gorze ekranu",
	"/block_chat - blokuje chat na jakis czas",
	"/block_chat_list - lista graczy z zablokowanym pisaniem",
	"/kill - zabija gracza",
	"/stun - omdlewa gracza",
	"/slow - spowalnia gracza",
	"/horse_level - podnosi poziom konia",
	"/reset - resetuje PZ i PE",
	"/go d - teleport na pustynie",
	"/go A - Shinsoo M1",
	"/go A3 - Shinsoo M2",
	"/go B - Chunjo M1",
	"/go B3 - Chunjo M2",
	"/go C - Jinno M1",
	"/go C3 - Jinno M2",
	"/purge - usuwa potwory, npc itp z okolicy",
	"/level - zmiana lvl'u postaci",
	"/go o - teleport do Areny OX",
	"/warp 400 600 - teleport do Areny GM'ow",
	"/warp 200 100 - Wyspa ze sniegiem (Siedliszcza GM'ow)",
	"/warp 7032 5225 - teleport do V2",
	"/resp all - jezeli usuniemy komenda /purge jakiegos NPC",
	"/ - powtarza poprzednia komende",
	"/gwlist - pokazuje wojny gildii",
	"/gwcancel - konczy wojne miedzy danymi gildiami",
	"/horse_ride - przywoluje konia",
	"/setsk 121 59 - Dowodzenie P",
	"/setsk 122 59 - Combo P",
	"/setsk 124 59 - MPCictwo P",
	"/setsk 125 59 - Kowalstwo P",
	"/setsk 126 59 - Jezyk Shinsoo P",
	"/setsk 127 59 - Jezyk Chunjo P",
	"/setsk 128 59 - Jezyk Jinno P",
	"/setsk 129 59 - Polimorfia P",
	"/setsk 130 30 - 30 lvl konia",
	"/setsk 131 10 - Przywolanie konia 100%",
	"/b - ogloszenie w ramce",
	"/x - dzien",
	"/h - informacja o koniu",
	"/o - Tryb obserwowania",
	"/f - ...nie wiem...",
	"/u - ilosc osob online",
	"/w - ilosc osob online",
	"/setsk 137 59 - Ciecie z Siodla P",
	"/setsk 138 59 - Stapniecie Konia P",
	"/setsk 139 59 - Fala Mocy P",
	"/setsk 140 59 - 4 skill militara",
	"/poly 0-3 - twoja postac",
	"/poly 4 - Wojownik",
	"/poly 5 - Ninja",
	"/poly 6 - Sura Kobieta",
	"/poly 7 - Szaman",
	"/priv_empire 0 1:item_drop - Zwieksza drop itemkow o dany procent na okreslony czas",
	"/priv_empire 0 2:gold_drop - Zwieksza drop Yang o dany procent na okreslony czas",
	"/priv_empire 0 3:gold10_drop - Zwieksza drop Yang o dany procent na okreslony czas i mnozy razy 10",
	"/priv_empire 0:4exp - Zwieksza exp o dany procent na okreslony czas",
	"-- Sura BM - skille P --",
	"/setsk 76 59",
	"/setsk 77 59",
	"/setsk 78 59",
	"/setsk 79 59",
	"/setsk 80 59",
	"/setsk 81 59",
	"-- Sura WP - skille P --",
	"/setsk 61 59",
	"/setsk 62 59",
	"/setsk 63 59",
	"/setsk 64 59",
	"/setsk 65 59",
	"/setsk 66 59",
	"-- Wojownik Body - skille P --",
	"/setsk 1 59",
	"/setsk 2 59",
	"/setsk 3 59",
	"/setsk 4 59",
	"/setsk 5 59",
	"-- Wojownik Mental - skille P --",
	"/setsk 16 59",
	"/setsk 17 59",
	"/setsk 18 59",
	"/setsk 19 59",
	"/setsk 20 59",
	"-- Szaman Smok - skille P --",
	"/setsk 91 59",
	"/setsk 92 59",
	"/setsk 93 59",
	"/setsk 94 59",
	"/setsk 95 59",
	"/setsk 96 59",
	"-- Szaman Healer - skille P --",
	"/setsk 106 59",
	"/setsk 107 59",
	"/setsk 108 59",
	"/setsk 109 59",
	"/setsk 110 59",
	"/setsk 111 59",
	"-- Ninja Dagger - skille P --",
	"/setsk 31 59",
	"/setsk 32 59",
	"/setsk 33 59",
	"/setsk 34 59",
	"/setsk 35 59",
	"-- Ninja Archer - skille P --",
	"/setsk 46 59",
	"/setsk 47 59",
	"/setsk 48 59",
	"/setsk 49 59",
	"/setsk 50 59",
	"/set exp - dostajemy dana ilosc expa",
	"/set gold - dostajemy dana ilosc Yang",
	"/pkmode 0 - Tryb PVP Pokojowy",
	"/pkmode 1 - Tryb PVP Agresywny",
	"/pkmode 2 - Tryb PVP Wolny",
	"/set skill - dodaje dana ilosc pkt umiejetnosci",
	"/setskillother 59 - dajemy komus dany skill na P",
	"/r - przywraca wszystkie pkt energii i zycia",
	"/a - dajemy komus dany lvl",
	"/xmas_song 1 - Wlacza sie piosenka swiateczna",
	"/xmas_song 0 - Wylacza sie piosenka",
	"/xmas_boom 1 - Noc",
	"/xmas_boom 0 - Dzien",
	"/xmas_tree 0 - swieta OFF",
	"/xmas_tree 1 - Pierwszy etap swiat.",
	"/xmas_tree 2 - Drugi etap swiat.",
	"/xmas_tree 3 - Trzeci etap swiat.",
	"/xmas_santa 1 - Santa Claus wlaczony",
	"/xmas_santa 0 - Santa Claus wylaczony",
	"/open - start eventu OX",
	"/mspd 0 - 1000 - szybkosc chodzenia",
	"/set_maxhp - doladowanie hp",
	"/set_maxsp - doladowanie pe",
	"/a level - Zmienia lvl gracza",
	"/polyitem - dodaje marmur polimorfii z danym potworem",
	"/setsk 151 7 - Krew Boga Smokow",
	"/setsk 152 7 - Blogoslawienstwo Boga Smokow",
	"/setsk 153 7 - Swieta Zbroja",
	"/setsk 154 7 - Akceleracja",
	"/setsk 155 7 - Furia Boga Smokow",
	"/setsk 156 7 - Smocze Zyczenie",
	"/setsk 157 7 - ...nie wiem...",
	"/set_state run - ...nie wiem...",
	"/set_state start - ...nie wiem...",
	"/set_state information - ...nie wiem...",
	"/e lotto_round - ...nie wiem...",
	"/e lotto-drop - ...nie wiem...",
	"/gete - ...nie wiem...",
	"/getq - ...nie wiem...",
	"/reload q - ...nie wiem...",
]

WINDOW_WIDTH = 680
WINDOW_HEIGHT = 620
TAB_Y = 44
TAB_HEIGHT = 22
CONTENT_Y = TAB_Y + TAB_HEIGHT + 8
CONTENT_HEIGHT = WINDOW_HEIGHT - CONTENT_Y - 10

# "Kategoria" dropdown on Utworz Przedmiot - codes match what
# do_gmpanel_itemlist (cmd_gm.cpp) understands.
GM_PANEL_CATEGORY_LIST = [
	("weapon",		"Bron"),
	("armor_body",	"Zbroja"),
	("armor_ear",	"Kolczyki"),
	("armor_wrist",	"Bransolety"),
	("armor_foots",	"Buty"),
	("armor_head",	"Helm"),
	("armor_shield","Tarcza"),
	("material",	"Ulepszacze"),
	("other",		"Inne przedmioty"),
]

# "Miejsce przyznania" dropdown - codes match do_gmpanel_createitem's
# location field (cmd_gm.cpp).
GM_PANEL_LOCATION_LIST = [
	("inv",		"Ekwipunek"),
	("safe",	"Magazyn"),
	("mall",	"Itemshop"),
]

# Bonus type dropdown source: (APPLY_* numeric id, enum suffix) pairs
# matching EApplyTypes in length.h exactly. Display labels are pulled at
# runtime from localeInfo.TOOLTIP_APPLY_<suffix> (locale_game.txt) instead
# of being hand-translated here, so they always match what item tooltips
# already show.
GM_PANEL_APPLY_SUFFIXES = [
	(1, "MAX_HP"), (2, "MAX_SP"), (3, "CON"), (4, "INT"), (5, "STR"), (6, "DEX"),
	(7, "ATT_SPEED"), (8, "MOV_SPEED"), (9, "CAST_SPEED"), (10, "HP_REGEN"),
	(11, "SP_REGEN"), (12, "POISON_PCT"), (13, "STUN_PCT"), (14, "SLOW_PCT"),
	(15, "CRITICAL_PCT"), (16, "PENETRATE_PCT"), (17, "ATTBONUS_HUMAN"),
	(18, "ATTBONUS_ANIMAL"), (19, "ATTBONUS_ORC"), (20, "ATTBONUS_MILGYO"),
	(21, "ATTBONUS_UNDEAD"), (22, "ATTBONUS_DEVIL"), (23, "STEAL_HP"),
	(24, "STEAL_SP"), (25, "MANA_BURN_PCT"), (26, "DAMAGE_SP_RECOVER"),
	(27, "BLOCK"), (28, "DODGE"), (29, "RESIST_SWORD"), (30, "RESIST_TWOHAND"),
	(31, "RESIST_DAGGER"), (32, "RESIST_BELL"), (33, "RESIST_FAN"),
	(34, "RESIST_BOW"), (35, "RESIST_FIRE"), (36, "RESIST_ELEC"),
	(37, "RESIST_MAGIC"), (38, "RESIST_WIND"), (39, "REFLECT_MELEE"),
	(40, "REFLECT_CURSE"), (41, "POISON_REDUCE"), (42, "KILL_SP_RECOVER"),
	(43, "EXP_DOUBLE_BONUS"), (44, "GOLD_DOUBLE_BONUS"), (45, "ITEM_DROP_BONUS"),
	(46, "POTION_BONUS"), (47, "KILL_HP_RECOVER"), (48, "IMMUNE_STUN"),
	(49, "IMMUNE_SLOW"), (50, "IMMUNE_FALL"), (51, "SKILL"), (52, "BOW_DISTANCE"),
	(53, "ATT_GRADE_BONUS"), (54, "DEF_GRADE_BONUS"), (55, "MAGIC_ATT_GRADE"),
	(56, "MAGIC_DEF_GRADE"), (57, "CURSE_PCT"), (58, "MAX_STAMINA"),
	(59, "ATTBONUS_WARRIOR"), (60, "ATTBONUS_ASSASSIN"), (61, "ATTBONUS_SURA"),
	(62, "ATTBONUS_SHAMAN"), (63, "ATTBONUS_MONSTER"), (64, "MALL_ATTBONUS"),
	(65, "MALL_DEFBONUS"), (66, "MALL_EXPBONUS"), (67, "MALL_ITEMBONUS"),
	(68, "MALL_GOLDBONUS"), (69, "MAX_HP_PCT"), (70, "MAX_SP_PCT"),
	(71, "SKILL_DAMAGE_BONUS"), (72, "NORMAL_HIT_DAMAGE_BONUS"),
	(73, "SKILL_DEFEND_BONUS"), (74, "NORMAL_HIT_DEFEND_BONUS"),
	(75, "PC_BANG_EXP_BONUS"), (76, "PC_BANG_DROP_BONUS"), (77, "EXTRACT_HP_PCT"),
	(78, "RESIST_WARRIOR"), (79, "RESIST_ASSASSIN"), (80, "RESIST_SURA"),
	(81, "RESIST_SHAMAN"), (82, "ENERGY"), (83, "DEF_GRADE"),
	(84, "COSTUME_ATTR_BONUS"), (85, "MAGIC_ATTBONUS_PER"),
	(86, "MELEE_MAGIC_ATTBONUS_PER"), (87, "RESIST_ICE"), (88, "RESIST_EARTH"),
	(89, "RESIST_DARK"), (90, "ANTI_CRITICAL_PCT"), (91, "ANTI_PENETRATE_PCT"),
]

# Plain ui.ComboBox with no way to hook "I'm opening now" - subclassed just
# to close every other combo/search-combo on the panel first, otherwise
# each one only knows how to close itself and clicking a different field
# leaves the previous dropdown stuck open on top of everything (this is
# what "tabele na siebie nachodza" turned out to be: Kategoria, Miejsce
# przyznania and a search-combo's results all left open at once).
class GMComboBox(ui.ComboBox):
	def __init__(self):
		ui.ComboBox.__init__(self)
		self.closeOthers = None

	def OnMouseLeftButtonUp(self):
		if not self.isListOpened and self.closeOthers:
			self.closeOthers(self)
		ui.ComboBox.OnMouseLeftButtonUp(self)

# Type-to-filter combo for lists too long for a plain ui.ComboBox (which has
# no scrolling - ComboBox.ArrangeItem sizes the popup to fit every item, so
# a 200+ entry weapon list rendered as one giant unclipped column covering
# the rest of the window). Always shows at most MAX_RESULTS matches, so the
# popup never needs to scroll. Typing filters live via OnUpdate polling -
# EditLine has no per-keystroke "changed" event in this engine, but OnUpdate
# is called every frame on any visible window (confirmed by ui.ComboBox's
# own use of it for hover state), so polling GetText() each frame is the
# supported way to detect this.
class GMSearchCombo(ui.Window):
	MAX_RESULTS = 10

	def __init__(self):
		ui.Window.__init__(self)
		self.items = []
		self.selectedValue = "0"
		self.onChange = None
		self.closeOthers = None
		self.openUpward = False
		self.lastText = None
		self.lastFocused = False
		self.edit = None
		self.slot = None
		self.listBox = None
		self.owner = None
		self.panelX = 0
		self.panelY = 0
		self._matches = []

	def __del__(self):
		ui.Window.__del__(self)

	# owner: the top-level GMPanelWindow. Its own popup gets parented
	# directly to it (not to this combo, which sits inside a page ui.Window
	# sized to CONTENT_HEIGHT) - a page clips its children to its own rect,
	# which is exactly why the popup was disappearing under the panel's
	# own board texture whenever it needed to extend past the page's
	# bounds. panelX/panelY is this combo's position in the PANEL's own
	# coordinate space (all pages sit at a fixed (10, CONTENT_Y) offset),
	# used to place the reparented popup directly under/above this combo.
	#
	# Split from __init__ like GMPanelWindow's pages: a child Show()n while
	# its parent is still hidden can end up permanently invisible even
	# after the parent is shown later in this engine, so the caller shows
	# this widget itself before calling Create().
	def Create(self, owner, panelX, panelY):
		self.owner = owner
		self.panelX = panelX
		self.panelY = panelY

		width = self.GetWidth()
		height = self.GetHeight()

		self.slot = ui.SlotBar()
		self.slot.SetParent(self)
		self.slot.SetSize(width, height)
		self.slot.SetPosition(0, 0)
		self.slot.AddFlag("not_pick")	# else it swallows clicks meant for self.edit below it
		self.slot.Show()

		self.edit = ui.EditLine()
		self.edit.SetParent(self)
		self.edit.SetPosition(3, 3)
		self.edit.SetSize(width - 6, height - 4)
		self.edit.SetMax(40)
		self.edit.Show()

		self.listBox = ui.ListBox()
		self.listBox.SetParent(owner)
		self.listBox.SetWidth(width)
		self.listBox.SetPickAlways()
		self.listBox.SetEvent(self.__OnSelectItem)
		self.listBox.Hide()

	def SetItems(self, items):
		self.items = items
		if items:
			self.__Select(items[0][0], items[0][1])
		else:
			self.__Select("0", "(brak)")

	def Close(self):
		if self.listBox:
			self.listBox.Hide()

	def __Select(self, value, label):
		self.selectedValue = value
		self.edit.SetText(label)
		self.lastText = label
		self.Close()

	def __OnSelectItem(self, index, name):
		if 0 <= index < len(self._matches):
			value, label = self._matches[index]
			self.__Select(value, label)
			if self.onChange:
				self.onChange(value)

	def OnUpdate(self):
		if not self.edit:
			return
		text = self.edit.GetText()
		focused = self.edit.IsFocus()
		if text == self.lastText and focused == self.lastFocused:
			return
		self.lastText = text
		self.lastFocused = focused
		if focused:
			self.__Refresh(text)
		else:
			self.Close()

	def __Refresh(self, text):
		query = text.strip().lower()
		self._matches = []
		# No query yet (box just clicked/focused) - show the first
		# MAX_RESULTS items as a starting point, same as a normal dropdown.
		for value, label in self.items:
			if not query or query in label.lower():
				self._matches.append((value, label))
				if len(self._matches) >= self.MAX_RESULTS:
					break

		self.listBox.ClearItem()
		if not self._matches:
			self.listBox.Hide()
			return

		if self.closeOthers:
			self.closeOthers(self)

		for i, (value, label) in enumerate(self._matches):
			self.listBox.InsertItem(i, label)
		self.listBox.ArrangeItem()
		popupHeight = self.listBox.GetHeight()
		if self.openUpward:
			self.listBox.SetPosition(self.panelX, self.panelY - popupHeight - 2)
		else:
			self.listBox.SetPosition(self.panelX, self.panelY + self.GetHeight() + 2)
		self.SetTop()
		self.listBox.Show()
		self.listBox.SetTop()

# Built entirely from ui.py widget classes in Python (no uiscript file to
# execfile()/pack) - see the comment above GM_PANEL_LOOKUP_FIELD_ORDER for why.
class GMPanelWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.pages = {}
		self.tabs = {}
		self.lookupValues = {}
		# Widgets built by pure Python code (no uiscript "children" tree)
		# have no other Python reference once the local variable that
		# created them goes out of scope - without this, refcounting GC
		# destroys the native widget (via __del__) right after Show(),
		# which is why the panel rendered its tabs but no page content.
		self._widgets = []
		# Every GMComboBox/GMSearchCombo on the panel, so opening one can
		# close all the others (see GMComboBox above).
		self._allCombos = []
		# Shared by every "..." picker field across every tab (Utworz
		# Przedmiot, Blokada Konta, Dodaj GM, ...) - this must exist before
		# ANY of those pages build their fields. It used to be initialized
		# inside __BuildCreateItemPage itself, which happened to work only
		# because that page was built before the others that also use
		# __MakePickerField - adding Dodaj GM ahead of it in the page-build
		# order (page_addgm comes before page_createitem) turned that
		# ordering assumption into a hard crash for every single login,
		# GM or not, since wndGMPanel is built unconditionally for everyone.
		self.pickerFields = {}

		# do_gmpanel_itemlist (cmd_gm.cpp) answers over several chat packets
		# (CHAT_MAX_LEN=512 caps one message) - these serialize requests so
		# two in-flight fetches never interleave their chunks.
		self._itemListQueue = []
		self._itemListBusy = False
		self._itemListTarget = None
		self._itemListBuffer = ""
		# If a response never arrives (dropped packet, server-side error
		# with no reply, etc.) _itemListBusy would otherwise stay stuck
		# forever and silently swallow every later fetch put behind it in
		# the queue - which is exactly what "czasem sie nie pobiera" turned
		# out to be. OnUpdate below counts frames spent busy and force-
		# advances the queue past whatever never answered.
		self._itemListBusyFrames = 0

		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.SetPosition(200, 100)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName("Panel GM by OskarPWA")
		self.SetCloseEvent(self.Hide)

		x = 10
		for tabName in GM_PANEL_TAB_NAMES:
			width = 110 if tabName in ("tab_spawnbots", "tab_spawnmobs") else 82
			button = ui.Button()
			button.SetParent(self)
			button.SetPosition(x, TAB_Y)
			button.SetSize(width, TAB_HEIGHT)
			button.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
			button.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
			button.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
			button.SetText(GM_PANEL_TAB_LABELS[tabName])
			button.SetEvent(self.__MakeSetPageHandler(tabName[len("tab_"):]))
			button.Show()
			self.tabs[tabName] = button
			x += width + 2

		for pageName in GM_PANEL_PAGE_NAMES:
			page = ui.Window()
			page.SetParent(self)
			page.SetPosition(10, CONTENT_Y)
			page.SetSize(WINDOW_WIDTH - 20, CONTENT_HEIGHT)
			# Show before adding children - children added while a parent is
			# still hidden can end up permanently invisible even after the
			# parent is shown later, in this engine.
			page.Show()
			self.pages[pageName] = page

		self.__BuildMainPage(self.pages["page_main"])
		self.__BuildAddGMPage(self.pages["page_addgm"])
		self.__BuildLookupPage(self.pages["page_lookup"])
		self.__BuildCreateItemPage(self.pages["page_createitem"])
		self.__BuildBanPage(self.pages["page_ban"])
		self.__BuildSpawnBotsPage(self.pages["page_spawnbots"])
		self.__BuildSpawnMobsPage(self.pages["page_spawnmobs"])
		self.__BuildGiveAmountPage(self.pages["page_giveamount"])
		self.__BuildSetValuePage(self.pages["page_setvalue"])
		self.__BuildSetStatPage(self.pages["page_setstat"])
		self.__BuildSkillsPage(self.pages["page_skills"])
		self.__BuildGMCommandsPage(self.pages["page_gmcommands"])

		# Full-page item/stone/bonus picker, not one of the 6 tabs - opened
		# on top of page_createitem by a field's "..." button and closed
		# back to it. Floating dropdown popups (ui.ComboBox and the earlier
		# GMSearchCombo attempt) kept rendering underneath this panel's own
		# board texture no matter what layer/z-order trick was tried, since
		# this panel is a "float" window; showing/hiding a normal sibling
		# page instead reuses the one part of this UI already proven to
		# render correctly (the tab pages themselves).
		pickerPage = ui.Window()
		pickerPage.SetParent(self)
		pickerPage.SetPosition(10, CONTENT_Y)
		pickerPage.SetSize(WINDOW_WIDTH - 20, CONTENT_HEIGHT)
		pickerPage.Show()
		self.pages["page_picker"] = pickerPage
		self.__BuildPickerPage(pickerPage)
		pickerPage.Hide()

		self.__SetPage("page_main")

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	# Polls the picker page's search box the same way GMSearchCombo did -
	# EditLine has no per-keystroke event in this engine, but OnUpdate is
	# called every frame on any visible window.
	def OnUpdate(self):
		if self._itemListBusy:
			self._itemListBusyFrames += 1
			if self._itemListBusyFrames > 180:
				self._itemListBusy = False
				self._itemListTarget = None
				self._itemListBuffer = ""
				self._itemListBusyFrames = 0
				self.__ProcessItemListQueue()
		else:
			self._itemListBusyFrames = 0

		picker = self.pages.get("page_picker")
		if not picker or not picker.IsShow():
			return
		text = self.pickerSearchEdit.GetText()
		if text != self._pickerLastQuery:
			self._pickerLastQuery = text
			self._pickerPageOffset = 0
			self.__RefreshPickerRows(text)

	def __MakeText(self, parent, x, y, text=""):
		textLine = ui.TextLine()
		textLine.SetParent(parent)
		textLine.SetPosition(x, y)
		textLine.SetText(text)
		textLine.Show()
		self._widgets.append(textLine)
		return textLine

	def __MakeEdit(self, parent, x, y, width, maxlen=8):
		slot = ui.SlotBar()
		slot.SetParent(parent)
		slot.SetSize(width, 20)
		slot.SetPosition(x, y)
		slot.Show()
		self._widgets.append(slot)

		editLine = ui.EditLine()
		editLine.SetParent(slot)
		editLine.SetPosition(3, 3)
		editLine.SetSize(width - 6, 17)
		editLine.SetMax(maxlen)
		editLine.Show()
		self._widgets.append(editLine)
		return editLine

	def __MakeCombo(self, parent, x, y, width, height=20):
		combo = GMComboBox()
		combo.SetParent(parent)
		combo.SetPosition(x, y)
		combo.SetSize(width, height)
		combo.Show()
		combo.closeOthers = self.__CloseOtherCombos
		self._widgets.append(combo)
		self._allCombos.append(combo)
		return combo

	# For lists too long for a plain ComboBox (see GMSearchCombo above) -
	# vnum/stone/bonus-type pickers all use this instead. y is this widget's
	# position within its page, used to decide whether its results popup
	# needs to open upward to stay inside the page (see GMSearchCombo).
	def __MakeSearchCombo(self, parent, x, y, width, items=None, onChange=None):
		combo = GMSearchCombo()
		combo.SetParent(parent)
		combo.SetPosition(x, y)
		combo.SetSize(width, 20)
		combo.Show()
		# All pages sit at a fixed (10, CONTENT_Y) inside this panel - see
		# GMSearchCombo.Create for why the popup needs panel-relative coords.
		combo.Create(self, 10 + x, CONTENT_Y + y)
		combo.onChange = onChange
		combo.closeOthers = self.__CloseOtherCombos
		combo.openUpward = y > CONTENT_HEIGHT - 210
		combo.SetItems(items or [])
		self._widgets.append(combo)
		self._allCombos.append(combo)
		return combo

	def __CloseOtherCombos(self, keep):
		for combo in self._allCombos:
			if combo is keep:
				continue
			if hasattr(combo, "CloseListBox"):
				combo.CloseListBox()
			else:
				combo.Close()

	# items: list of (value, label). Stored on the combo itself (_gmItems)
	# so the SetEvent callback - which only ever receives an index - can
	# resolve back to both the value and the label to display.
	def __FillCombo(self, combo, items):
		combo.ClearItem()
		combo._gmItems = items
		for i, (value, label) in enumerate(items):
			combo.InsertItem(i, label)
		if items:
			combo.SetCurrentItem(items[0][1])
			combo._gmSelected = items[0][0]
		else:
			combo.SetCurrentItem("(brak)")
			combo._gmSelected = "0"

	def __MakeComboSelectHandler(self, combo, onChange=None):
		def handler(index):
			items = getattr(combo, "_gmItems", [])
			if 0 <= index < len(items):
				value, label = items[index]
				combo._gmSelected = value
				combo.SetCurrentItem(label)
				if onChange:
					onChange(value)
		return handler

	def __ApplyLabel(self, suffix):
		# Basic stats (STR/DEX/CON/INT/MAX_HP/MAX_SP/speeds/regen/SKILL) are
		# localized as plain TOOLTIP_<name> in this client, not
		# TOOLTIP_APPLY_<name> - only the less common apply types use the
		# _APPLY_ form. Without this most bonus types fell back to their
		# raw English enum name instead of a Polish label.
		for prefix in ("TOOLTIP_APPLY_", "TOOLTIP_"):
			getter = getattr(localeInfo, prefix + suffix, None)
			if getter is None:
				continue
			try:
				return getter(0)
			except:
				pass
		return suffix

	# do_gmpanel_itemlist (cmd_gm.cpp) answers in several CHAT_MAX_LEN-capped
	# chat packets ("GMPanelItemListChunk <isLast>|<data>") - queued so two
	# fetches (e.g. category change + stone list) never interleave.
	def __FetchItemList(self, category, target):
		if target == "botlist":
			command = "gmpanel_botlist"
		elif target == "availbots":
			command = "gmpanel_available_bots"
		elif target == "moblist":
			command = "gmpanel_moblist"
		elif target == "metinlist":
			command = "gmpanel_metinlist"
		else:
			command = "gmpanel_itemlist"
		self._itemListQueue.append((command, category, target))
		self.__ProcessItemListQueue()

	def __ProcessItemListQueue(self):
		if self._itemListBusy or not self._itemListQueue:
			return
		command, category, target = self._itemListQueue.pop(0)
		self._itemListBusy = True
		self._itemListTarget = target
		self._itemListBuffer = ""
		net.SendChatPacket("/%s %s" % (command, category))

	# Called from game.py's server-command dispatcher with each
	# "GMPanelItemListChunk <isLast>|<data>" payload.
	def SetItemListChunk(self, data):
		parts = data.split("|", 1)
		if len(parts) != 2:
			return
		isLast, chunk = parts
		self._itemListBuffer += chunk

		if isLast != "1":
			return

		raw = self._itemListBuffer
		self._itemListBuffer = ""
		target = self._itemListTarget
		self._itemListTarget = None
		self._itemListBusy = False

		items = []
		for entry in raw.split(";"):
			if not entry:
				continue
			bits = entry.split(":", 1)
			if len(bits) != 2:
				continue
			vnum, name = bits
			items.append((vnum, name.replace("_", " ")))

		if target == "botlist":
			# Already ordered by the server (level descending) - keep it,
			# and don't alphabetize the way item lists are below.
			self._botListItems = items
			if self._pickerKey == "__botlist__" and self.pages["page_picker"].IsShow():
				self.__RefreshPickerRows(self.pickerSearchEdit.GetText())
			self.__ProcessItemListQueue()
			return

		if target == "availbots":
			# Already ordered by the server (PID ascending) - keep it.
			self._availBotsItems = items
			if self._pickerKey == "__availbots__" and self.pages["page_picker"].IsShow():
				self.__RefreshPickerRows(self.pickerSearchEdit.GetText())
			self.__ProcessItemListQueue()
			return

		if target == "moblist":
			# Already ordered by the server (vnum ascending, ORDER BY vnum
			# in do_gmpanel_moblist) - keep it, don't alphabetize like the
			# vnum/stone item lists below (user asked for smallest-to-
			# largest ID order, not alphabetical).
			self._mobListItems = items
			if self._pickerKey == "mob_picker" and self.pages["page_picker"].IsShow():
				self.__RefreshPickerRows(self.pickerSearchEdit.GetText())
			self.__ProcessItemListQueue()
			return

		if target == "metinlist":
			self._metinListItems = items
			if self._pickerKey == "metin_picker" and self.pages["page_picker"].IsShow():
				self.__RefreshPickerRows(self.pickerSearchEdit.GetText())
			self.__ProcessItemListQueue()
			return

		items.sort(key=lambda pair: pair[1])

		if target == "vnum":
			self._vnumItems = items
		elif target == "stone":
			self._stoneItems = [("0", "(puste)")] + items

		self.__ProcessItemListQueue()

	def __OnCategoryChanged(self, catCode):
		self.__FetchItemList(catCode, "vnum")

	def __BuildMainPage(self, page):
		self.__MakeText(page, 10, 10, "Panel Administracyjny GM")
		self.__MakeText(page, 10, 32, "Wybierz zakladke powyzej. Kazda akcja jest")
		self.__MakeText(page, 10, 46, "dodatkowo zweryfikowana po stronie serwera.")
		self.__MakeText(page, 10, 62, "Panel jest w wersji BETA. Jak zauwazysz bugi")
		self.__MakeText(page, 10, 76, "napisz na Discord do OskarPWA.")

		# m2sp_logo.tga: pack\ETC\ymir work\ui\public\ - a loose folder that
		# mirrors the ETC.epk archive (the "d:/ymir work/..." namespace
		# every stock .tga in this client loads from), separate from the
		# root/locale_pl script packs this session has otherwise worked in.
		# 512x256 image: "GM Panel" + the real M2Singleplayer logo +
		# "www.m2singleplayer.pl" composited into one graphic (baked-in
		# text, not engine TextLine widgets - matches the reference mockup).
		# No logo. The original loaded d:/ymir work/ui/public/m2sp_logo.tga, a
		# loose file of one client that no pack we ship carries; and a failed
		# LoadImage in this engine does not raise where it is called - it leaves
		# the error set and the interpreter throws it at the next builtin call,
		# a for loop forty lines further on, past any try/except. The whole
		# interface then stayed unbuilt and the game hung on the loading screen.

	def __BuildPlaceholderPage(self, page):
		self.__MakeText(page, 10, 10, "W przygotowaniu.")

	def __BuildLookupPage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")

		slot = ui.SlotBar()
		slot.SetParent(page)
		slot.SetSize(140, 20)
		slot.SetPosition(55, 2)
		slot.Show()
		self._widgets.append(slot)

		editLine = ui.EditLine()
		editLine.SetParent(slot)
		editLine.SetPosition(3, 3)
		editLine.SetSize(134, 17)
		editLine.SetMax(24)
		editLine.Show()
		self.lookupNickEdit = editLine

		searchButton = ui.Button()
		searchButton.SetParent(page)
		searchButton.SetPosition(210, 2)
		searchButton.SetSize(80, 20)
		searchButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		searchButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		searchButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		searchButton.SetText("Sprawdz")
		searchButton.SetEvent(self.__OnClickSearch)
		searchButton.Show()
		self._widgets.append(searchButton)

		self.lookupStatus = self.__MakeText(page, 300, 6, "")

		colX = [10, 300]
		rowH = 18
		for i, (fieldName, label) in enumerate(GM_PANEL_LOOKUP_LAYOUT):
			col = i % 2
			row = i // 2
			x = colX[col]
			y = 30 + row * rowH
			self.__MakeText(page, x, y, label)
			self.lookupValues[fieldName] = self.__MakeText(page, x + 130, y, "-")

		# Skill summary (read-only - "Zmien skille" below opens the actual
		# editor, page_skills) - names/levels only for skills the character
		# actually has (GetSkillLevel(vnum) > 0), online-only (see
		# do_gmpanel_skilllist comment: no trusted way to read skill_level's
		# raw BLOB for an offline character).
		skillsY = 30 + 11 * rowH + 10
		self.__MakeText(page, 10, skillsY, "Umiejetnosci:")
		self.lookupSkillLines = []
		for i in range(8):
			line = self.__MakeText(page, 10, skillsY + 18 + i * 14, "")
			self.lookupSkillLines.append(line)

		# Akcje GM na sprawdzanej postaci - dwa rzedy po 3 przyciski, pod
		# lista umiejetnosci. Kazdy zapamietuje self._lookupNick (ustawiane
		# w __OnClickSearch) i przechodzi na wlasciwa pod-strone.
		actionsY = skillsY + 18 + 8 * 14 + 10
		actionW = 175
		actionGap = 5
		actions = [
			("Daj Yang", lambda: self.__OpenGiveAmount("gold")),
			("Daj Smocze Monety", lambda: self.__OpenGiveAmount("cash")),
			("Zmien poziom konia", lambda: self.__OpenSetValue("horse")),
			("Zmien range", lambda: self.__OpenSetValue("range")),
			("Dodaj statystyki", self.__OpenSetStat),
			("Zmien skille", self.__OpenSkills),
		]
		for i, (label, handler) in enumerate(actions):
			col = i % 3
			row = i // 3
			btn = ui.Button()
			btn.SetParent(page)
			btn.SetPosition(10 + col * (actionW + actionGap), actionsY + row * 26)
			btn.SetSize(actionW, 22)
			btn.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
			btn.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
			btn.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
			btn.SetText(label)
			btn.SetEvent(handler)
			btn.Show()
			self._widgets.append(btn)

		self._lookupNick = ""
		self._skillListBuffer = ""
		self._lookupSkills = []

	# One field on page_createitem: a read-only display + a "..." button
	# that opens the shared full-page picker (see __BuildPickerPage). kind
	# says which item list the picker should search: "static" uses the
	# items passed in here directly, "vnum"/"stone"/"apply" pull from the
	# matching self._xxxItems list that SetItemListChunk/__init__ fill in.
	def __MakePickerField(self, page, x, y, width, key, kind,
			staticItems=None, defaultValue="0", defaultLabel="(wybierz)"):
		button = ui.Button()
		button.SetParent(page)
		button.SetPosition(x, y)
		button.SetSize(width, 20)
		button.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		button.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		button.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		button.SetText(defaultLabel)
		button.SetEvent(self.__MakeOpenPickerHandler(key))
		button.Show()
		self._widgets.append(button)

		self.pickerFields[key] = {
			"kind": kind, "value": defaultValue, "widget": button, "items": staticItems,
		}

	def __MakeOpenPickerHandler(self, key):
		return lambda: self.__OpenPicker(key)

	def __GetPickerSourceItems(self, key):
		field = self.pickerFields[key]
		if field["kind"] == "static":
			return field["items"]
		if field["kind"] == "vnum":
			return self._vnumItems
		if field["kind"] == "stone":
			return self._stoneItems
		if field["kind"] == "apply":
			return self._applyItems
		if field["kind"] == "botlist":
			return self._botListItems
		if field["kind"] == "availbots":
			return self._availBotsItems
		if field["kind"] == "moblist":
			return self._mobListItems
		if field["kind"] == "metinlist":
			return self._metinListItems
		return []

	def __SetPickerFieldValue(self, key, value, label):
		field = self.pickerFields[key]
		field["value"] = value
		# The bot list "field" is read-only display, not a real form field -
		# it has no widget of its own to write the picked label into.
		if field["widget"] is not None:
			field["widget"].SetText(label)
		if key == "category":
			self.__FetchItemList(value, "vnum")
		# The name-only picker button shows the picked mob/metin's name (no
		# ID, per "Dodaj same nazwy w zakladce bez ID") - the actual vnum
		# used to Spawn still has to land somewhere typable, so it's mirrored
		# into the plain "ID" edit line next to it. Typing an ID directly
		# there works exactly the same way, without ever touching the picker.
		elif key == "mob_picker":
			self.spawnMobIdEdit.SetText(value)
		elif key == "metin_picker":
			self.spawnMetinIdEdit.SetText(value)

	def __OpenPicker(self, key):
		self._pickerKey = key
		# Whichever tab page was actually open when the "..." field was
		# clicked - hardcoding "page_createitem" here hid the WRONG page
		# whenever a field on a different tab (e.g. Blokada Konta) opened
		# a picker, leaving that tab's own content visible underneath.
		self._pickerReturnPage = self._currentPageName
		self.pickerSearchEdit.SetText("")
		self._pickerLastQuery = ""
		self._pickerPageOffset = 0
		if key == "mob_picker" and not self._mobListItems:
			self.__FetchItemList("0", "moblist")
		elif key == "metin_picker" and not self._metinListItems:
			self.__FetchItemList("0", "metinlist")
		self.__RefreshPickerRows("")
		self.pages[self._pickerReturnPage].Hide()
		self.pages["page_picker"].Show()

	def __ClosePicker(self):
		self.pages["page_picker"].Hide()
		self.pages[self._pickerReturnPage].Show()

	# Strips anything outside plain ASCII instead of trying to match exact
	# bytes - the typed search text and the item names (round-tripped
	# through the server) aren't guaranteed to use the same encoding for
	# Polish letters, so comparing "kamie" against "kamie" (both stripped
	# of a/e/l/etc-with-diacritics) matches reliably where comparing the
	# raw accented bytes against each other did not.
	def __SearchKey(self, text):
		return "".join(ch for ch in text.lower() if ord(ch) < 128)

	def __RefreshPickerRows(self, text):
		items = self.__GetPickerSourceItems(self._pickerKey)
		query = self.__SearchKey(text.strip())
		filtered = [(value, label) for value, label in items
				if not query or query in self.__SearchKey(label)]

		pageSize = len(self.pickerRows)
		offset = self._pickerPageOffset
		matches = filtered[offset:offset + pageSize]
		self._pickerMatches = matches
		for i, button in enumerate(self.pickerRows):
			if i < len(matches):
				button.SetText(matches[i][1])
				button.Show()
			else:
				button.Hide()

		# "Dalej" only makes sense once a list is actually longer than one
		# page (e.g. "Lista botow gotowych do spawnu" easily has more PIDs
		# than the 42-row grid fits) - hidden otherwise, same as "Wroc" is
		# always shown regardless.
		self.pickerNextButton.Show() if offset + len(matches) < len(filtered) else self.pickerNextButton.Hide()

	def __MakePickerRowHandler(self, index):
		return lambda: self.__OnPickerRowClick(index)

	def __OnClickPickerNextPage(self):
		self._pickerPageOffset += len(self.pickerRows)
		self.__RefreshPickerRows(self.pickerSearchEdit.GetText())

	def __OnPickerRowClick(self, index):
		if index >= len(self._pickerMatches):
			return
		value, label = self._pickerMatches[index]
		self.__SetPickerFieldValue(self._pickerKey, value, label)
		self.__ClosePicker()

	def __BuildPickerPage(self, page):
		slot = ui.SlotBar()
		slot.SetParent(page)
		slot.SetSize(300, 20)
		slot.SetPosition(10, 6)
		slot.AddFlag("not_pick")
		slot.Show()
		self._widgets.append(slot)

		self.pickerSearchEdit = ui.EditLine()
		self.pickerSearchEdit.SetParent(page)
		self.pickerSearchEdit.SetPosition(13, 9)
		self.pickerSearchEdit.SetSize(294, 17)
		self.pickerSearchEdit.SetMax(40)
		self.pickerSearchEdit.Show()
		self._widgets.append(self.pickerSearchEdit)
		self._pickerLastQuery = ""
		self._pickerMatches = []
		self._pickerKey = None
		self._pickerPageOffset = 0

		# Grid instead of a single column - a single column only ever showed
		# 14 of a possibly much longer list at a time while leaving most of
		# the page empty.
		COLS = 3
		ROWS = 14
		colWidth = 175
		colGap = 5
		rowHeight = 20
		gridTop = 34

		self.pickerRows = []
		for i in range(COLS * ROWS):
			col = i % COLS
			row = i // COLS
			rowButton = ui.Button()
			rowButton.SetParent(page)
			rowButton.SetPosition(10 + col * (colWidth + colGap), gridTop + row * rowHeight)
			rowButton.SetSize(colWidth, 19)
			rowButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
			rowButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
			rowButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
			rowButton.SetEvent(self.__MakePickerRowHandler(i))
			rowButton.Hide()
			self._widgets.append(rowButton)
			self.pickerRows.append(rowButton)

		backButton = ui.Button()
		backButton.SetParent(page)
		backButton.SetPosition(10, gridTop + ROWS * rowHeight + 4)
		backButton.SetSize(80, 22)
		backButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		backButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		backButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		backButton.SetText("Wroc")
		backButton.SetEvent(self.__ClosePicker)
		backButton.Show()
		self._widgets.append(backButton)

		nextButton = ui.Button()
		nextButton.SetParent(page)
		nextButton.SetPosition(95, gridTop + ROWS * rowHeight + 4)
		nextButton.SetSize(80, 22)
		nextButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		nextButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		nextButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		nextButton.SetText("Dalej")
		nextButton.SetEvent(self.__OnClickPickerNextPage)
		nextButton.Hide()
		self._widgets.append(nextButton)
		self.pickerNextButton = nextButton

	def __BuildCreateItemPage(self, page):
		self._vnumItems = []
		self._stoneItems = [("0", "(puste)")]
		self._applyItems = [("0", "(brak)")]
		for typeId, suffix in GM_PANEL_APPLY_SUFFIXES:
			self._applyItems.append((str(typeId), self.__ApplyLabel(suffix)))

		self.__MakeText(page, 10, 6, "Wlasciciel:")
		self.createOwnerEdit = self.__MakeEdit(page, 90, 2, 140, 24)

		self.__MakeText(page, 10, 30, "Kategoria:")
		self.__MakePickerField(page, 90, 26, 130, "category", "static",
				staticItems=GM_PANEL_CATEGORY_LIST,
				defaultValue=GM_PANEL_CATEGORY_LIST[0][0], defaultLabel=GM_PANEL_CATEGORY_LIST[0][1])

		self.__MakeText(page, 230, 30, "Przedmiot:")
		self.__MakePickerField(page, 300, 26, 140, "vnum", "vnum")

		self.__MakeText(page, 450, 30, "Ilosc:")
		self.createCountEdit = self.__MakeEdit(page, 485, 26, 50, 5)

		self.__MakeText(page, 10, 54, "Miejsce przyznania:")
		self.__MakePickerField(page, 140, 50, 150, "location", "static",
				staticItems=GM_PANEL_LOCATION_LIST,
				defaultValue=GM_PANEL_LOCATION_LIST[0][0], defaultLabel=GM_PANEL_LOCATION_LIST[0][1])

		self.__MakeText(page, 10, 80, "Kamienie Duszy (0 = puste):")
		sx = 10
		for i in range(6):
			self.__MakePickerField(page, sx, 98, 84, "socket%d" % i, "stone",
					defaultValue="0", defaultLabel="(puste)")
			sx += 87

		self.__MakeText(page, 10, 124, "Bonusy (typ 0 = puste):")
		self.createAttrValueEdits = []
		ay = 142
		for i in range(7):
			self.__MakeText(page, 10, ay + 3, "Bonus %d:" % (i + 1))
			self.__MakePickerField(page, 90, ay, 200, "attr%d" % i, "apply",
					defaultValue="0", defaultLabel="(brak)")
			self.__MakeText(page, 300, ay + 3, "Wartosc:")
			valueEdit = self.__MakeEdit(page, 360, ay, 60, 6)
			self.createAttrValueEdits.append(valueEdit)
			ay += 22

		createButton = ui.Button()
		createButton.SetParent(page)
		createButton.SetPosition(10, ay + 8)
		createButton.SetSize(120, 24)
		createButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		createButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		createButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		createButton.SetText("Utworz")
		createButton.SetEvent(self.__OnClickCreateItem)
		createButton.Show()
		self._widgets.append(createButton)

		self.createItemStatus = self.__MakeText(page, 140, ay + 14, "")

		# Item lists are NOT fetched here - wndGMPanel is built for every
		# login regardless of GM status (F9 just gates showing it), so
		# firing gmpanel_itemlist automatically at construction time meant
		# a burst of a dozen+ chat-command response packets landing right
		# as every character enters the game world. That's exactly the kind
		# of "too early / too much at once" traffic that broke the login
		# handshake before (see the SetGMFlag comment in char.cpp) - lazy
		# load these the first time the tab is actually opened instead
		# (see __SetPage below).
		self._createItemListsLoaded = False

	def __OnClickCreateItem(self):
		owner = self.createOwnerEdit.GetText().strip()
		vnum = self.pickerFields["vnum"]["value"]
		count = self.createCountEdit.GetText().strip() or "1"
		location = self.pickerFields["location"]["value"]

		if not owner or not vnum or vnum == "0":
			self.createItemStatus.SetText("Podaj wlasciciela i wybierz przedmiot.")
			return

		fields = [owner, vnum, count, location]
		for i in range(6):
			fields.append(self.pickerFields["socket%d" % i]["value"])
		for i in range(7):
			fields.append(self.pickerFields["attr%d" % i]["value"])
			fields.append(self.createAttrValueEdits[i].GetText().strip() or "0")

		# "|" is our own field delimiter and a space would get the whole
		# chat command line split apart by the client<->server parser (see
		# the comment on gmpanel_createitem, cmd_gm.cpp) - refuse both.
		for value in fields:
			if "|" in value or " " in value:
				self.createItemStatus.SetText("Niedozwolony znak w polu.")
				return

		self.createItemStatus.SetText("Tworze...")
		net.SendChatPacket("/gmpanel_createitem %s" % "|".join(fields))

	# Called from game.py's server-command dispatcher with the raw payload
	# do_gmpanel_createitem (cmd_gm.cpp) sent back.
	def SetCreateItemResult(self, data):
		if data == "OK":
			self.createItemStatus.SetText("Przedmiot utworzony.")
		elif data == "ERR_OWNER_OFFLINE":
			self.createItemStatus.SetText("Gracz nie jest online.")
		elif data == "ERR_BADVNUM":
			self.createItemStatus.SetText("Zly vnum przedmiotu.")
		elif data == "ERR_NOSPACE":
			self.createItemStatus.SetText("Brak miejsca docelowego.")
		elif data == "ERR_SAFEBOX_CLOSED":
			self.createItemStatus.SetText("Gracz nie otwieral Magazynu w tej sesji.")
		elif data == "ERR_MALL_CLOSED":
			self.createItemStatus.SetText("Gracz nie otwieral Itemshopu w tej sesji.")
		elif data == "ERR_BADDATA":
			self.createItemStatus.SetText("Blad danych.")
		else:
			self.createItemStatus.SetText("Blad: %s" % data)

	def __BuildBanPage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")
		self.banAccountEdit = self.__MakeEdit(page, 90, 2, 160, 24)

		self.__MakeText(page, 10, 30, "Akcja:")
		banActionItems = [
			("check",	"Sprawdz status"),
			("temp",	"Blokada tymczasowa"),
			("perm",	"Blokada permanentna"),
			("unlock",	"Odblokuj"),
		]
		self.__MakePickerField(page, 90, 26, 190, "ban_action", "static",
				staticItems=banActionItems, defaultValue="check", defaultLabel="Sprawdz status")

		self.__MakeText(page, 10, 54, "Dni (tylko blokada tymczasowa):")
		self.banDaysEdit = self.__MakeEdit(page, 210, 50, 60, 4)

		execButton = ui.Button()
		execButton.SetParent(page)
		execButton.SetPosition(10, 82)
		execButton.SetSize(120, 24)
		execButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		execButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		execButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		execButton.SetText("Wykonaj")
		execButton.SetEvent(self.__OnClickBanAccount)
		execButton.Show()
		self._widgets.append(execButton)

		kickButton = ui.Button()
		kickButton.SetParent(page)
		kickButton.SetPosition(140, 82)
		kickButton.SetSize(150, 24)
		kickButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		kickButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		kickButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		kickButton.SetText("Wyrzuc z serwera")
		kickButton.SetEvent(self.__OnClickKickAccount)
		kickButton.Show()
		self._widgets.append(kickButton)

		self.banStatus = self.__MakeText(page, 10, 112, "")

		self.__MakeText(page, 10, 132,
				"Blokada dziala od NASTEPNEGO logowania na to konto - nie")
		self.__MakeText(page, 10, 146,
				"wylogowuje juz zalogowanej sesji. Wyrzuc z serwera dziala")
		self.__MakeText(page, 10, 160,
				"tylko gdy gracz jest AKTUALNIE online.")

	def __OnClickKickAccount(self):
		nick = self.banAccountEdit.GetText().strip()
		if not nick or " " in nick or "|" in nick:
			self.banStatus.SetText("Podaj nick.")
			return
		self.banStatus.SetText("Wyrzucam...")
		net.SendChatPacket("/gmpanel_account %s" % "|".join([nick, "kick", "1", "-"]))

	def __OnClickBanAccount(self):
		nick = self.banAccountEdit.GetText().strip()
		action = self.pickerFields["ban_action"]["value"]
		days = self.banDaysEdit.GetText().strip() or "1"

		if not nick:
			self.banStatus.SetText("Podaj nick.")
			return

		for value in (nick, days):
			if "|" in value or " " in value:
				self.banStatus.SetText("Niedozwolony znak w polu.")
				return

		self.banStatus.SetText("Wysylam...")
		net.SendChatPacket("/gmpanel_account %s" % "|".join([nick, action, days, "-"]))

	# Called from game.py's server-command dispatcher with the raw payload
	# do_gmpanel_account (cmd_gm.cpp) sent back.
	def SetAccountResult(self, data):
		if data.startswith("STATUS|"):
			parts = data.split("|")
			if len(parts) == 3:
				self.banStatus.SetText("Status konta: %s, dostep: %s" % (parts[1], parts[2]))
			else:
				self.banStatus.SetText("Blad odpowiedzi serwera.")
		elif data == "OK":
			self.banStatus.SetText("Wykonano.")
		elif data == "ERR_NOTFOUND":
			self.banStatus.SetText("Gracz nie istnieje.")
		elif data == "ERR_BADNAME":
			self.banStatus.SetText("Niedozwolony znak w nazwie konta.")
		elif data == "ERR_BADDATA":
			self.banStatus.SetText("Blad danych.")
		elif data == "ERR_QUERY":
			self.banStatus.SetText("Blad zapytania do bazy.")
		elif data == "ERR_NOTONLINE":
			self.banStatus.SetText("Gracz nie jest online.")
		elif data == "ERR_SELF":
			self.banStatus.SetText("Nie mozesz wyrzucic samego siebie.")
		else:
			self.banStatus.SetText("Blad: %s" % data)

	def __BuildAddGMPage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")
		self.addGmNickEdit = self.__MakeEdit(page, 90, 2, 160, 24)

		self.__MakeText(page, 10, 30, "Ranga:")
		gmRankItems = [
			("HIGH_WIZARD",	"High Wizard (GM)"),
			("GOD",			"God (Admin)"),
			("LOW_WIZARD",	"Low Wizard (Moderator)"),
			("IMPLEMENTOR",	"Implementor (Wlasciciel)"),
		]
		self.__MakePickerField(page, 90, 26, 200, "gm_rank", "static",
				staticItems=gmRankItems, defaultValue="HIGH_WIZARD", defaultLabel="High Wizard (GM)")

		addButton = ui.Button()
		addButton.SetParent(page)
		addButton.SetPosition(10, 54)
		addButton.SetSize(120, 24)
		addButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		addButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		addButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		addButton.SetText("Dodaj GM")
		addButton.SetEvent(self.__OnClickAddGM)
		addButton.Show()
		self._widgets.append(addButton)

		removeButton = ui.Button()
		removeButton.SetParent(page)
		removeButton.SetPosition(140, 54)
		removeButton.SetSize(120, 24)
		removeButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		removeButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		removeButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		removeButton.SetText("Usun GM")
		removeButton.SetEvent(self.__OnClickRemoveGM)
		removeButton.Show()
		self._widgets.append(removeButton)

		self.addGmStatus = self.__MakeText(page, 10, 84, "")

		self.__MakeText(page, 10, 106,
				"Dziala natychmiast (bez restartu serwera) - odswieza liste GM")
		self.__MakeText(page, 10, 120,
				"na wszystkich juz zalogowanych postaciach.")

	def __SendAddGM(self, action):
		nick = self.addGmNickEdit.GetText().strip()
		rank = self.pickerFields["gm_rank"]["value"]

		if not nick:
			self.addGmStatus.SetText("Podaj nick.")
			return
		if "|" in nick or " " in nick:
			self.addGmStatus.SetText("Niedozwolony znak w nicku.")
			return

		self.addGmStatus.SetText("Wysylam...")
		net.SendChatPacket("/gmpanel_addgm %s" % "|".join([nick, rank, action]))

	def __OnClickAddGM(self):
		self.__SendAddGM("add")

	def __OnClickRemoveGM(self):
		self.__SendAddGM("remove")

	# Called from game.py's server-command dispatcher with the raw payload
	# do_gmpanel_addgm (cmd_gm.cpp) sent back.
	def SetAddGMResult(self, data):
		if data == "OK":
			self.addGmStatus.SetText("Wykonano.")
		elif data == "ERR_NOTFOUND":
			self.addGmStatus.SetText("Gracz nie istnieje.")
		elif data == "ERR_BADNAME":
			self.addGmStatus.SetText("Niedozwolony znak w nicku.")
		elif data == "ERR_BADRANK":
			self.addGmStatus.SetText("Niepoprawna ranga.")
		elif data == "ERR_BADDATA":
			self.addGmStatus.SetText("Blad danych.")
		elif data == "ERR_QUERY":
			self.addGmStatus.SetText("Blad zapytania do bazy.")
		else:
			self.addGmStatus.SetText("Blad: %s" % data)

	def __BuildSpawnBotsPage(self, page):
		self.__MakeText(page, 10, 6, "ID Bota:")
		self.spawnPidEdit = self.__MakeEdit(page, 100, 2, 80, 6)

		self.__MakeText(page, 200, 6, "Ilosc:")
		self.spawnCountEdit = self.__MakeEdit(page, 250, 2, 60, 4)

		self.__MakeText(page, 10, 30, "Imperium:")
		empireItems = [
			("1", "1 - Shinsoo"),
			("2", "2 - Chunjo"),
			("3", "3 - Jinno"),
		]
		self.__MakePickerField(page, 100, 26, 150, "spawn_empire", "static",
				staticItems=empireItems, defaultValue="1", defaultLabel="1 - Shinsoo")

		spawnButton = ui.Button()
		spawnButton.SetParent(page)
		spawnButton.SetPosition(10, 54)
		spawnButton.SetSize(100, 24)
		spawnButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		spawnButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		spawnButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		spawnButton.SetText("Spawn")
		spawnButton.SetEvent(self.__OnClickSpawnBots)
		spawnButton.Show()
		self._widgets.append(spawnButton)

		despawnButton = ui.Button()
		despawnButton.SetParent(page)
		despawnButton.SetPosition(120, 54)
		despawnButton.SetSize(100, 24)
		despawnButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		despawnButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		despawnButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		despawnButton.SetText("Despawn")
		despawnButton.SetEvent(self.__OnClickDespawnBots)
		despawnButton.Show()
		self._widgets.append(despawnButton)

		self.spawnStatus = self.__MakeText(page, 10, 84, "")

		refreshButton = ui.Button()
		refreshButton.SetParent(page)
		refreshButton.SetPosition(10, 104)
		refreshButton.SetSize(180, 22)
		refreshButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		refreshButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		refreshButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		refreshButton.SetText("Odswiez liste aktywnych")
		refreshButton.SetEvent(self.__OnClickRefreshBotList)
		refreshButton.Show()
		self._widgets.append(refreshButton)

		availButton = ui.Button()
		availButton.SetParent(page)
		availButton.SetPosition(200, 104)
		availButton.SetSize(220, 22)
		availButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		availButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		availButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		availButton.SetText("Lista botow gotowych do spawnu")
		availButton.SetEvent(self.__OnClickShowAvailableBots)
		availButton.Show()
		self._widgets.append(availButton)

		# Read-only "field" for the bot list - no widget of its own, it just
		# reuses the same full-page picker every other list already uses
		# instead of a small on-page list (which is also what made this
		# reliably visible - see the comment on GMSearchCombo/page_picker).
		self.pickerFields["__botlist__"] = {"kind": "botlist", "value": "0", "widget": None, "items": None}
		self._botListItems = []

		# Available-to-spawn list DOES have a widget: spawnPidEdit itself -
		# clicking a PID in the picker fills it in directly, ready to press
		# "Spawn" (same generic __SetPickerFieldValue path every other
		# picker field already uses, just pointed at this edit line).
		self.pickerFields["__availbots__"] = {"kind": "availbots", "value": "0", "widget": self.spawnPidEdit, "items": None}
		self._availBotsItems = []

	def __OnClickSpawnBots(self):
		self.__SendSpawn("spawn")

	def __OnClickDespawnBots(self):
		self.__SendSpawn("despawn")

	def __SendSpawn(self, action):
		pid = self.spawnPidEdit.GetText().strip()
		count = self.spawnCountEdit.GetText().strip()
		empire = self.pickerFields["spawn_empire"]["value"]

		if not pid or not count:
			self.spawnStatus.SetText("Podaj PID i ilosc.")
			return

		self.spawnStatus.SetText("Wysylam...")
		net.SendChatPacket("/gmpanel_spawn %s" % "|".join([pid, count, empire, action]))

	def __OnClickRefreshBotList(self):
		self._botListItems = []
		self.__OpenPicker("__botlist__")
		self.__FetchItemList("-", "botlist")

	def __OnClickShowAvailableBots(self):
		self._availBotsItems = []
		self.__OpenPicker("__availbots__")
		self.__FetchItemList("-", "availbots")

	# Called from game.py's server-command dispatcher with the raw payload
	# do_gmpanel_spawn (cmd_gm.cpp) sent back.
	def SetSpawnResult(self, data):
		if data.startswith("OK|"):
			parts = data.split("|")
			if len(parts) == 4:
				self.spawnStatus.SetText("Wykonano %s/%s. Aktywnych ogolem: %s" % (parts[1], parts[2], parts[3]))
			else:
				self.spawnStatus.SetText("Blad odpowiedzi serwera.")
		elif data == "ERR_BADDATA":
			self.spawnStatus.SetText("Blad danych - sprawdz PID i ilosc.")
		elif data == "ERR_BADEMPIRE":
			self.spawnStatus.SetText("Niepoprawne imperium.")
		else:
			self.spawnStatus.SetText("Blad: %s" % data)

	def __MakeSetPageHandler(self, shortName):
		return lambda: self.__SetPage("page_" + shortName)

	# Called from Interface.OpenGMLookupFor (interfacemodule.py), itself
	# called from uitarget.TargetBoard's new "Sprawdz" button - the target
	# menu already knows the clicked player's name, so this jumps straight
	# to the lookup tab pre-filled and already searching instead of making
	# the GM retype a nick they just clicked on.
	def OpenLookupFor(self, name):
		self.__SetPage("page_lookup")
		self.lookupNickEdit.SetText(name)
		self.__OnClickSearch()

	def Destroy(self):
		self.ClearDictionary()
		self.pages = {}
		self.tabs = {}
		self.lookupValues = {}
		self._widgets = []
		self._allCombos = []

	def OnPressEscapeKey(self):
		self.Hide()
		return True

	def __SetPage(self, pageName):
		self._currentPageName = pageName
		for name, page in self.pages.items():
			if name == pageName:
				page.Show()
			else:
				page.Hide()
		for name, tab in self.tabs.items():
			pageOfTab = "page_" + name[len("tab_"):]
			if pageOfTab == pageName:
				tab.Down()
			else:
				tab.SetUp()

		if pageName == "page_createitem" and not self._createItemListsLoaded:
			self._createItemListsLoaded = True
			self.__FetchItemList(GM_PANEL_CATEGORY_LIST[0][0], "vnum")
			self.__FetchItemList("stone", "stone")

	def __OnClickSearch(self):
		nick = self.lookupNickEdit.GetText().strip()
		if not nick:
			self.lookupStatus.SetText("Podaj nick.")
			return
		self._lookupNick = nick
		self.lookupStatus.SetText("Szukam...")
		for line in self.lookupSkillLines:
			line.SetText("")
		net.SendChatPacket("/gmpanel_lookup %s" % nick)
		net.SendChatPacket("/gmpanel_skilllist %s" % nick)

	# Called from game.py's server-command dispatcher (BINARY_ServerCommand_Run
	# -> "GMPanelLookupResult" -> here) with the raw pipe-delimited payload
	# do_gmpanel_lookup (cmd_gm.cpp) sent back.
	def SetLookupResult(self, data):
		if data.startswith("ERR_NOTFOUND"):
			self.lookupStatus.SetText("Nie znaleziono gracza.")
			for fieldName in GM_PANEL_LOOKUP_FIELD_ORDER:
				self.lookupValues[fieldName].SetText("-")
			return
		if data.startswith("ERR_BADNAME"):
			self.lookupStatus.SetText("Niedozwolony znak w nicku.")
			return

		parts = data.split("|")
		if len(parts) != len(GM_PANEL_LOOKUP_FIELD_ORDER):
			self.lookupStatus.SetText("Blad odpowiedzi serwera.")
			return

		values = dict(zip(GM_PANEL_LOOKUP_FIELD_ORDER, parts))
		try:
			values["lk_job"] = GM_PANEL_JOB_NAMES.get(int(values["lk_job"]), values["lk_job"])
		except ValueError:
			pass

		for fieldName in GM_PANEL_LOOKUP_FIELD_ORDER:
			self.lookupValues[fieldName].SetText(values.get(fieldName, "-"))

		self.lookupStatus.SetText("OK")

	# Called from game.py's dispatcher with each "GMPanelSkillListResult
	# <isLast>|<data>" payload from do_gmpanel_skilllist (cmd_gm.cpp) -
	# entries are "<vnum>:<name>:<level>:<maxlevel>;". Same chunk-buffer
	# idea as SetItemListChunk, but its own small buffer - this fetch runs
	# alongside (not through) the picker-oriented item-list queue.
	def SetSkillListResult(self, data):
		if data in ("ERR_OFFLINE", "ERR_BADDATA"):
			self._skillListBuffer = ""
			self._lookupSkills = []
			for i, line in enumerate(self.lookupSkillLines):
				if i == 0 and data == "ERR_OFFLINE":
					line.SetText("(postac offline - brak podgladu skilli)")
				else:
					line.SetText("")
			return

		parts = data.split("|", 1)
		if len(parts) != 2:
			return
		isLast, chunk = parts
		self._skillListBuffer += chunk

		if isLast != "1":
			return

		raw = self._skillListBuffer
		self._skillListBuffer = ""

		skills = []
		for entry in raw.split(";"):
			if not entry:
				continue
			bits = entry.split(":")
			if len(bits) != 4:
				continue
			vnum, name, level, maxLevel = bits
			skills.append((vnum, name.replace("_", " "), level, maxLevel))

		self._lookupSkills = skills
		for i, line in enumerate(self.lookupSkillLines):
			if i < len(skills):
				vnum, name, level, maxLevel = skills[i]
				line.SetText("%s: %s/%s" % (name, level, maxLevel))
			else:
				line.SetText("")

	######################################################################
	## "Spawn Mobow" - mob i metin spawn are the same layout twice over: a
	## name-only picker (do_gmpanel_moblist/metinlist, filtered server-side
	## by mob_proto.type so metins can never show up in the mob list or vice
	## versa - see CHAR_TYPE_STONE=2 in common/length.h) next to a plain
	## "ID" edit line that either one fills in with the vnum (see
	## __SetPickerFieldValue's mob_picker/metin_picker branch), or that can
	## just be typed into directly - both end up calling the exact same
	## do_gmpanel_spawnmob. "Lista komend GM" opens a separate scrollable
	## text page (page_gmcommands), not the click-to-pick grid every other
	## picker uses, since its entries are full sentences that don't fit the
	## picker's 175px-wide row buttons.
	######################################################################

	def __BuildSpawnMobsPage(self, page):
		self._mobListItems = []
		self._metinListItems = []

		self.__MakeText(page, 10, 6, "Moby:")
		self.__MakePickerField(page, 60, 2, 180, "mob_picker", "moblist",
				defaultValue="0", defaultLabel="(wybierz z listy)")

		self.__MakeText(page, 260, 6, "ID:")
		self.spawnMobIdEdit = self.__MakeEdit(page, 280, 2, 70, 6)

		self.__MakeText(page, 360, 6, "Ilosc:")
		self.spawnMobCountEdit = self.__MakeEdit(page, 410, 2, 60, 4)

		mobSpawnButton = ui.Button()
		mobSpawnButton.SetParent(page)
		mobSpawnButton.SetPosition(480, 2)
		mobSpawnButton.SetSize(90, 20)
		mobSpawnButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		mobSpawnButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		mobSpawnButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		mobSpawnButton.SetText("Spawn")
		mobSpawnButton.SetEvent(self.__OnClickSpawnMob)
		mobSpawnButton.Show()
		self._widgets.append(mobSpawnButton)

		self.spawnMobStatus = self.__MakeText(page, 10, 30, "")

		self.__MakeText(page, 10, 70, "Metiny:")
		self.__MakePickerField(page, 60, 66, 180, "metin_picker", "metinlist",
				defaultValue="0", defaultLabel="(wybierz z listy)")

		self.__MakeText(page, 260, 70, "ID:")
		self.spawnMetinIdEdit = self.__MakeEdit(page, 280, 66, 70, 6)

		self.__MakeText(page, 360, 70, "Ilosc:")
		self.spawnMetinCountEdit = self.__MakeEdit(page, 410, 66, 60, 4)

		metinSpawnButton = ui.Button()
		metinSpawnButton.SetParent(page)
		metinSpawnButton.SetPosition(480, 66)
		metinSpawnButton.SetSize(90, 20)
		metinSpawnButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		metinSpawnButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		metinSpawnButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		metinSpawnButton.SetText("Spawn")
		metinSpawnButton.SetEvent(self.__OnClickSpawnMetin)
		metinSpawnButton.Show()
		self._widgets.append(metinSpawnButton)

		self.spawnMetinStatus = self.__MakeText(page, 10, 94, "")

		gmCmdButton = ui.Button()
		gmCmdButton.SetParent(page)
		gmCmdButton.SetPosition(10, 130)
		gmCmdButton.SetSize(170, 24)
		gmCmdButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		gmCmdButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		gmCmdButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		gmCmdButton.SetText("Lista komend GM")
		gmCmdButton.SetEvent(self.__OnClickShowGMCommands)
		gmCmdButton.Show()
		self._widgets.append(gmCmdButton)

	def __OnClickSpawnMob(self):
		self.__SendSpawnMob(self.spawnMobIdEdit, self.spawnMobCountEdit, self.spawnMobStatus, "mob")

	def __OnClickSpawnMetin(self):
		self.__SendSpawnMob(self.spawnMetinIdEdit, self.spawnMetinCountEdit, self.spawnMetinStatus, "metin")

	def __SendSpawnMob(self, idEdit, countEdit, statusText, kind):
		vnum = idEdit.GetText().strip()
		count = countEdit.GetText().strip()

		if not vnum or not count:
			statusText.SetText("Podaj ID i ilosc.")
			return

		statusText.SetText("Wysylam...")
		net.SendChatPacket("/gmpanel_spawnmob %s" % "|".join([vnum, count, kind]))

	# Called from game.py's server-command dispatcher with do_gmpanel_spawnmob's
	# response - "<kind>|OK|<done>|<count>" or "<kind>|ERR_<reason>".
	def SetSpawnMobResult(self, data):
		parts = data.split("|")
		if len(parts) < 2:
			return
		kind = parts[0]
		statusText = self.spawnMobStatus if kind == "mob" else self.spawnMetinStatus

		if parts[1] == "OK" and len(parts) == 4:
			statusText.SetText("Zespawnowano %s/%s." % (parts[2], parts[3]))
		elif parts[1] == "ERR_BADDATA":
			statusText.SetText("Blad danych - sprawdz ID i ilosc.")
		elif parts[1] == "ERR_NOTFOUND":
			statusText.SetText("Nie znaleziono moba/metina o takim ID.")
		else:
			statusText.SetText("Blad: %s" % parts[1])

	def __OnClickShowGMCommands(self):
		self.__SetPage("page_gmcommands")

	def __OnClickBackFromGMCommands(self):
		self.__SetPage("page_spawnmobs")

	# Plain scrollable text list, not the click-to-pick grid every other
	# picker uses - GM_COMMANDS_LIST entries are full sentences (command +
	# description), which don't fit the picker's 175px-wide row buttons.
	# Same scrollbar-over-a-slot-board approach as PlayerbotAdminWindow's bot
	# list (__PBAMakeScrollBar/__PBARebuildBotListUI below) - a real
	# up/down slider, matching "tabelka z suwakiem gora/dol" literally,
	# since this list is informational only and never needs search/paging.
	def __BuildGMCommandsPage(self, page):
		self.__MakeText(page, 10, 6, "Lista komend GM:")

		listWidth = WINDOW_WIDTH - 20 - 30
		listHeight = CONTENT_HEIGHT - 60

		listBoard = ui.Window()
		listBoard.SetParent(page)
		listBoard.SetPosition(10, 28)
		listBoard.SetSize(listWidth + 20, listHeight)
		listBoard.Show()
		self._widgets.append(listBoard)

		self.gmCommandsScrollBar = ui.ScrollBar()
		self.gmCommandsScrollBar.SetParent(listBoard)
		self.gmCommandsScrollBar.SetPosition(listWidth, 0)
		self.gmCommandsScrollBar.SetScrollBarSize(listHeight)
		self.gmCommandsScrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScrollGMCommands))
		self.gmCommandsScrollBar.Show()
		self._widgets.append(self.gmCommandsScrollBar)

		self.gmCommandsSlotBoard = ui.Window()
		self.gmCommandsSlotBoard.SetParent(listBoard)
		self.gmCommandsSlotBoard.SetPosition(0, 0)
		self.gmCommandsSlotBoard.SetSize(listWidth, listHeight)
		self.gmCommandsSlotBoard.Show()
		self._widgets.append(self.gmCommandsSlotBoard)

		self._gmCommandsRowHeight = 14
		self._gmCommandsStartLine = 0
		self._gmCommandsVisibleRows = max(1, listHeight // self._gmCommandsRowHeight)
		self._gmCommandsLines = []
		for text in GM_COMMANDS_LIST:
			line = ui.TextLine()
			line.SetParent(self.gmCommandsSlotBoard)
			line.SetPosition(2, 0)
			line.SetText(text)
			line.Hide()
			self._widgets.append(line)
			self._gmCommandsLines.append(line)

		rowCount = len(self._gmCommandsLines)
		if rowCount <= self._gmCommandsVisibleRows:
			self.gmCommandsScrollBar.Hide()
		else:
			self.gmCommandsScrollBar.SetMiddleBarSize(float(self._gmCommandsVisibleRows) / float(rowCount))
			self.gmCommandsScrollBar.Show()

		backButton = ui.Button()
		backButton.SetParent(page)
		backButton.SetPosition(10, listHeight + 34)
		backButton.SetSize(80, 22)
		backButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		backButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		backButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		backButton.SetText("Wroc")
		backButton.SetEvent(self.__OnClickBackFromGMCommands)
		backButton.Show()
		self._widgets.append(backButton)

		self.__LayoutGMCommandsRows()

	def __LayoutGMCommandsRows(self):
		yPos = 0
		for i, line in enumerate(self._gmCommandsLines):
			if i < self._gmCommandsStartLine or i >= self._gmCommandsStartLine + self._gmCommandsVisibleRows:
				line.Hide()
				continue
			line.SetPosition(2, yPos)
			line.Show()
			yPos += self._gmCommandsRowHeight

	def __OnScrollGMCommands(self):
		rowCount = len(self._gmCommandsLines)
		scrollableRows = max(0, rowCount - self._gmCommandsVisibleRows)
		startLine = int(scrollableRows * self.gmCommandsScrollBar.GetPos())
		if startLine != self._gmCommandsStartLine:
			self._gmCommandsStartLine = startLine
			self.__LayoutGMCommandsRows()

	######################################################################
	## "Sprawdz Gracza" - akcje GM (Daj Yang/Smocze Monety, Zmien punkty
	## konne/range, Dodaj statystyki, Zmien skille). Wspolny wzorzec: kazdy
	## przycisk na page_lookup zapamietuje tryb (self._giveAmountMode /
	## self._setValueMode) i przechodzi na jedna z dwoch reuzywanych
	## pod-stron (page_giveamount, page_setvalue) zamiast budowac 4 prawie
	## identyczne strony osobno.
	######################################################################

	def __BuildGiveAmountPage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")
		self.giveAmountNickText = self.__MakeText(page, 60, 6, "-")

		self.giveAmountTitleText = self.__MakeText(page, 10, 34, "Kwota:")
		self.giveAmountEdit = self.__MakeEdit(page, 110, 30, 120, 10)

		giveButton = ui.Button()
		giveButton.SetParent(page)
		giveButton.SetPosition(240, 28)
		giveButton.SetSize(80, 22)
		giveButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		giveButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		giveButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		giveButton.SetText("Daj")
		giveButton.SetEvent(self.__OnClickGiveAmount)
		giveButton.Show()
		self._widgets.append(giveButton)

		cancelButton = ui.Button()
		cancelButton.SetParent(page)
		cancelButton.SetPosition(330, 28)
		cancelButton.SetSize(80, 22)
		cancelButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		cancelButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		cancelButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		cancelButton.SetText("Anuluj")
		cancelButton.SetEvent(lambda: self.__SetPage("page_lookup"))
		cancelButton.Show()
		self._widgets.append(cancelButton)

		self.giveAmountStatus = self.__MakeText(page, 10, 64, "")
		self._giveAmountMode = "gold"

	def __OpenGiveAmount(self, mode):
		if not self._lookupNick:
			return
		self._giveAmountMode = mode
		self.giveAmountNickText.SetText(self._lookupNick)
		self.giveAmountTitleText.SetText("Kwota Yang:" if mode == "gold" else "Kwota SM:")
		self.giveAmountEdit.SetText("")
		self.giveAmountStatus.SetText("")
		self.__SetPage("page_giveamount")

	def __OnClickGiveAmount(self):
		amount = self.giveAmountEdit.GetText().strip()
		if not self._lookupNick or not amount:
			self.giveAmountStatus.SetText("Podaj kwote.")
			return
		self.giveAmountStatus.SetText("Wysylam...")
		cmd = "gmpanel_give_gold" if self._giveAmountMode == "gold" else "gmpanel_give_cash"
		net.SendChatPacket("/%s %s" % (cmd, "|".join([self._lookupNick, amount])))

	# Called from game.py's dispatcher with do_gmpanel_give_gold's response.
	def SetGiveGoldResult(self, data):
		if data.startswith("OK_OFFLINE"):
			self.giveAmountStatus.SetText("OK (gracz offline, zapisano w bazie).")
		elif data.startswith("OK|"):
			newGold = data.split("|")[1]
			self.giveAmountStatus.SetText("OK. Nowy stan Yang: %s" % newGold)
			if self.lookupValues["lk_name"].GetText() == self._lookupNick:
				self.lookupValues["lk_gold"].SetText(newGold)
		elif data == "ERR_BADDATA":
			self.giveAmountStatus.SetText("Blad danych - sprawdz kwote.")
		elif data == "ERR_NOTFOUND":
			self.giveAmountStatus.SetText("Nie znaleziono gracza.")
		else:
			self.giveAmountStatus.SetText("Blad: %s" % data)

	# Called from game.py's dispatcher with do_gmpanel_give_cash's response.
	def SetGiveCashResult(self, data):
		if data == "OK":
			self.giveAmountStatus.SetText("OK. Smocze Monety dodane.")
		elif data == "ERR_BADDATA":
			self.giveAmountStatus.SetText("Blad danych - sprawdz kwote.")
		elif data == "ERR_NOTFOUND":
			self.giveAmountStatus.SetText("Nie znaleziono gracza.")
		else:
			self.giveAmountStatus.SetText("Blad: %s" % data)

	def __BuildSetValuePage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")
		self.setValueNickText = self.__MakeText(page, 60, 6, "-")

		self.setValueTitleText = self.__MakeText(page, 10, 34, "Nowa wartosc:")
		self.setValueEdit = self.__MakeEdit(page, 130, 30, 100, 10)

		saveButton = ui.Button()
		saveButton.SetParent(page)
		saveButton.SetPosition(240, 28)
		saveButton.SetSize(80, 22)
		saveButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		saveButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		saveButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		saveButton.SetText("Zapisz")
		saveButton.SetEvent(self.__OnClickSetValue)
		saveButton.Show()
		self._widgets.append(saveButton)

		cancelButton = ui.Button()
		cancelButton.SetParent(page)
		cancelButton.SetPosition(330, 28)
		cancelButton.SetSize(80, 22)
		cancelButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		cancelButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		cancelButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		cancelButton.SetText("Anuluj")
		cancelButton.SetEvent(lambda: self.__SetPage("page_lookup"))
		cancelButton.Show()
		self._widgets.append(cancelButton)

		self.setValueStatus = self.__MakeText(page, 10, 64, "")
		self._setValueMode = "horse"

	def __OpenSetValue(self, mode):
		if not self._lookupNick:
			return
		self._setValueMode = mode
		self.setValueNickText.SetText(self._lookupNick)
		if mode == "horse":
			self.setValueTitleText.SetText("Nowy poziom konia (0-30):")
			current = self.lookupValues["lk_horselvl"].GetText()
		else:
			self.setValueTitleText.SetText("Nowe punkty range:")
			current = self.lookupValues["lk_range"].GetText()
		self.setValueEdit.SetText(current if current != "-" else "")
		self.setValueStatus.SetText("")
		self.__SetPage("page_setvalue")

	def __OnClickSetValue(self):
		value = self.setValueEdit.GetText().strip()
		if not self._lookupNick or not value:
			self.setValueStatus.SetText("Podaj wartosc.")
			return
		self.setValueStatus.SetText("Wysylam...")
		cmd = "gmpanel_set_horse_points" if self._setValueMode == "horse" else "gmpanel_set_range"
		net.SendChatPacket("/%s %s" % (cmd, "|".join([self._lookupNick, value])))

	# Called from game.py's dispatcher with do_gmpanel_set_horse_points's response.
	def SetHorsePointsResult(self, data):
		if data.startswith("OK_OFFLINE|") or data.startswith("OK|"):
			value = data.split("|")[1]
			self.setValueStatus.SetText("OK. Poziom konia: %s" % value)
			if self.lookupValues["lk_name"].GetText() == self._lookupNick:
				self.lookupValues["lk_horselvl"].SetText(value)
		elif data == "ERR_BADDATA":
			self.setValueStatus.SetText("Blad danych - sprawdz wartosc.")
		elif data == "ERR_NOTFOUND":
			self.setValueStatus.SetText("Nie znaleziono gracza.")
		else:
			self.setValueStatus.SetText("Blad: %s" % data)

	# Called from game.py's dispatcher with do_gmpanel_set_range's response.
	def SetRangeResult(self, data):
		if data.startswith("OK_OFFLINE|") or data.startswith("OK|"):
			value = data.split("|")[1]
			self.setValueStatus.SetText("OK. Punkty range: %s" % value)
			if self.lookupValues["lk_name"].GetText() == self._lookupNick:
				self.lookupValues["lk_range"].SetText(value)
		elif data == "ERR_BADDATA":
			self.setValueStatus.SetText("Blad danych - sprawdz wartosc.")
		elif data == "ERR_NOTFOUND":
			self.setValueStatus.SetText("Nie znaleziono gracza.")
		else:
			self.setValueStatus.SetText("Blad: %s" % data)

	def __BuildSetStatPage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")
		self.setStatNickText = self.__MakeText(page, 60, 6, "-")

		self.__MakeText(page, 10, 34, "Statystyka:")
		statItems = [
			("st", "Sila"),
			("ht", "Wytrzymalosc"),
			("dx", "Zrecznosc"),
			("iq", "Inteligencja"),
		]
		self.__MakePickerField(page, 130, 30, 150, "setstat_stat", "static",
				staticItems=statItems, defaultValue="st", defaultLabel="Sila")

		self.__MakeText(page, 10, 62, "Nowa wartosc:")
		self.setStatEdit = self.__MakeEdit(page, 130, 58, 100, 6)
		self.__MakeText(page, 240, 62, "(Max 30.000)")

		saveButton = ui.Button()
		saveButton.SetParent(page)
		saveButton.SetPosition(10, 90)
		saveButton.SetSize(100, 22)
		saveButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		saveButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		saveButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		saveButton.SetText("Zapisz")
		saveButton.SetEvent(self.__OnClickSetStat)
		saveButton.Show()
		self._widgets.append(saveButton)

		cancelButton = ui.Button()
		cancelButton.SetParent(page)
		cancelButton.SetPosition(120, 90)
		cancelButton.SetSize(100, 22)
		cancelButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		cancelButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		cancelButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		cancelButton.SetText("Anuluj")
		cancelButton.SetEvent(lambda: self.__SetPage("page_lookup"))
		cancelButton.Show()
		self._widgets.append(cancelButton)

		self.setStatStatus = self.__MakeText(page, 10, 120, "")

	def __OpenSetStat(self):
		if not self._lookupNick:
			return
		self.setStatNickText.SetText(self._lookupNick)
		self.setStatEdit.SetText("")
		self.setStatStatus.SetText("")
		self.__SetPage("page_setstat")

	def __OnClickSetStat(self):
		stat = self.pickerFields["setstat_stat"]["value"]
		value = self.setStatEdit.GetText().strip()
		if not self._lookupNick or not value:
			self.setStatStatus.SetText("Podaj wartosc.")
			return
		self.setStatStatus.SetText("Wysylam...")
		net.SendChatPacket("/gmpanel_set_stat %s" % "|".join([self._lookupNick, stat, value]))

	# Called from game.py's dispatcher with do_gmpanel_set_stat's response.
	def SetStatResult(self, data):
		if data.startswith("OK_OFFLINE|") or data.startswith("OK|"):
			parts = data.split("|")
			stat, value = parts[1], parts[2]
			self.setStatStatus.SetText("OK. %s = %s" % (stat, value))
			fieldName = {"st": "lk_st", "ht": "lk_ht", "dx": "lk_dx", "iq": "lk_iq"}.get(stat)
			if fieldName and self.lookupValues["lk_name"].GetText() == self._lookupNick:
				self.lookupValues[fieldName].SetText(value)
		elif data == "ERR_BADSTAT":
			self.setStatStatus.SetText("Nieznana statystyka.")
		elif data == "ERR_BADDATA":
			self.setStatStatus.SetText("Blad danych - sprawdz wartosc.")
		elif data == "ERR_NOTFOUND":
			self.setStatStatus.SetText("Nie znaleziono gracza.")
		else:
			self.setStatStatus.SetText("Blad: %s" % data)

	def __BuildSkillsPage(self, page):
		self.__MakeText(page, 10, 6, "Nick:")
		self.skillsNickText = self.__MakeText(page, 60, 6, "-")

		backButton = ui.Button()
		backButton.SetParent(page)
		backButton.SetPosition(WINDOW_WIDTH - 20 - 100, 2)
		backButton.SetSize(100, 20)
		backButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		backButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		backButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		backButton.SetText("Powrot")
		backButton.SetEvent(lambda: self.__SetPage("page_lookup"))
		backButton.Show()
		self._widgets.append(backButton)

		self.skillRows = []
		rowY0 = 34
		rowH = 26
		for i in range(10):
			y = rowY0 + i * rowH
			nameText = self.__MakeText(page, 10, y, "")
			editLine = self.__MakeEdit(page, 300, y - 3, 60, 3)

			saveBtn = ui.Button()
			saveBtn.SetParent(page)
			saveBtn.SetPosition(370, y - 4)
			saveBtn.SetSize(70, 20)
			saveBtn.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
			saveBtn.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
			saveBtn.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
			saveBtn.SetText("Zapisz")
			saveBtn.SetEvent(self.__MakeSaveSkillHandler(i))
			saveBtn.Hide()
			self._widgets.append(saveBtn)

			rowStatus = self.__MakeText(page, 445, y, "")

			self.skillRows.append({
				"vnum": None, "nameText": nameText, "edit": editLine,
				"button": saveBtn, "status": rowStatus,
			})

		self.skillsStatus = self.__MakeText(page, 10, rowY0 + 10 * rowH + 6, "")

	def __MakeSaveSkillHandler(self, index):
		return lambda: self.__OnClickSaveSkill(index)

	def __OpenSkills(self):
		if not self._lookupNick:
			return
		self.skillsNickText.SetText(self._lookupNick)
		self.__PopulateSkillRows()
		self.__SetPage("page_skills")

	# Poziom skilla <-> notacja: 1-19 zwykle liczby, 20-29 = M1-M10 (n=level-19),
	# 30-39 = G1-G10 (n=level-29), 40 = P. Podane wprost przez uzytkownika
	# (M5=24, G1=30, P=40) - nie zgadywane.
	def __LevelToGrade(self, level):
		try:
			level = int(level)
		except (TypeError, ValueError):
			return str(level)
		if level <= 19:
			return str(level)
		if level <= 29:
			return "M%d" % (level - 19)
		if level <= 39:
			return "G%d" % (level - 29)
		if level == 40:
			return "P"
		return str(level)

	def __GradeToLevel(self, text):
		text = text.strip().upper()
		if not text:
			return None
		if text == "P":
			return 40
		if text[0] in ("M", "G") and text[1:].isdigit():
			n = int(text[1:])
			if 1 <= n <= 10:
				return (19 if text[0] == "M" else 29) + n
			return None
		if text.isdigit():
			return int(text)
		return None

	def __PopulateSkillRows(self):
		skills = self._lookupSkills
		for i, row in enumerate(self.skillRows):
			if i < len(skills):
				vnum, name, level, maxLevel = skills[i]
				row["vnum"] = vnum
				row["nameText"].SetText("%s (obecnie %s/%s):" % (
						name, self.__LevelToGrade(level), self.__LevelToGrade(maxLevel)))
				row["edit"].SetText(self.__LevelToGrade(level))
				row["status"].SetText("")
				row["button"].Show()
			else:
				row["vnum"] = None
				row["nameText"].SetText("")
				row["edit"].SetText("")
				row["status"].SetText("")
				row["button"].Hide()
		self.skillsStatus.SetText("")

	def __OnClickSaveSkill(self, index):
		row = self.skillRows[index]
		if row["vnum"] is None or not self._lookupNick:
			return
		text = row["edit"].GetText().strip()
		if not text:
			row["status"].SetText("Podaj poziom.")
			return
		level = self.__GradeToLevel(text)
		if level is None:
			row["status"].SetText("Zly format (np. 18, M5, G1, P).")
			return
		row["status"].SetText("Wysylam...")
		self.skillsStatus.SetText("")
		net.SendChatPacket("/gmpanel_setskill %s" % "|".join([self._lookupNick, row["vnum"], str(level)]))

	# Called from game.py's dispatcher with do_gmpanel_setskill's response.
	def SetSetSkillResult(self, data):
		if data.startswith("OK|"):
			parts = data.split("|")
			vnum, level = parts[1], parts[2]
			for row in self.skillRows:
				if row["vnum"] == vnum:
					row["status"].SetText("OK (%s)" % self.__LevelToGrade(level))
					row["edit"].SetText(self.__LevelToGrade(level))
					break
			self.skillsStatus.SetText("Zapisano.")
		elif data == "ERR_OFFLINE":
			self.skillsStatus.SetText("Gracz musi byc online.")
		elif data == "ERR_BADSKILL":
			self.skillsStatus.SetText("Nieznany skill.")
		elif data == "ERR_BADDATA":
			self.skillsStatus.SetText("Blad danych.")
		else:
			self.skillsStatus.SetText("Blad: %s" % data)

## ============================================================================
## PlayerbotAdminWindow / BotOverheadTail - dawniej osobny plik
## root/uiPlayerbotAdmin.py, teraz scalone bezposrednio tutaj z tego samego
## powodu co GMPanelWindow nigdy nie uzywa pliku uiscript: EPack32 "Add file"
## na uiscript.epk (dodanie playerbotadminwindow.py) nadpisalo cale archiwum
## PUSTYM, kasujac wszystkie inne pliki (PopupDialog.py i reszta) - klient nie
## startowal w ogole. Po przywroceniu uiscript.epk z backupu i przepisaniu
## PlayerbotAdminWindow na czysty Python (bez uiscript), okazalo sie ze sam
## NOWY plik root/uiPlayerbotAdmin.py tez nigdy nie trafil do root.epk (EPack32
## "Save" odswieza tylko already-tracked pliki, nigdy nie dodaje nowych same z
## siebie) - "ImportError: No module named uiPlayerbotAdmin" przy wyborze
## postaci. Scalajac ten kod do interfacemodule.py (ktory JUZ jest w root.epk
## i regularnie edytowany caly ten sesje) znika potrzeba jakiegokolwiek "Add
## file" - zwykly Save wystarczy, tak jak GMPanelWindow od poczatku.
##
## Stale ponizej maja prefiks PBA_ zeby nie kolidowaly z WINDOW_WIDTH/TAB_Y/
## CONTENT_Y/CONTENT_HEIGHT itp. juz zdefiniowanymi wyzej dla GMPanelWindow
## (inny rozmiar okna - 940x680 zamiast 560x460).
## ============================================================================

PBA_WINDOW_WIDTH = 940
PBA_WINDOW_HEIGHT = 680

PBA_TAB_Y = 40
PBA_TAB_HEIGHT = 20
PBA_CONTENT_X = 15
PBA_CONTENT_Y = 75
PBA_CONTENT_HEIGHT = PBA_WINDOW_HEIGHT - PBA_CONTENT_Y - 45

PBA_LIST_WIDTH = 230
PBA_RIGHT_X = PBA_CONTENT_X + PBA_LIST_WIDTH + 15
PBA_RIGHT_WIDTH = PBA_WINDOW_WIDTH - PBA_RIGHT_X - 15

PBA_ROW_HEIGHT = 20
PBA_LOG_LINE_HEIGHT = 16
PBA_LIST_ROW_WIDTH = 190
PBA_LIST_ROW_HEIGHT = 18
PBA_LIST_ROW_NAME_MAXLEN = 11

# "Czat ogolny" nie renderuje tekstu w silniku gry w ogole - laduje prawdziwa
# strone panelu w ten sam wbudowany silnik przegladarki co Item Mall
# (app.ShowWebPage, patrz root/uiweb.py). 127.0.0.1 dziala bo to serwer
# singleplayer, klient i panel siedza na tej samej maszynie.
PBA_BOTCHAT_URL = "http://127.0.0.1:7788/botchat"

PBA_GLOBAL_CHAT_RECT_X = PBA_CONTENT_X
PBA_GLOBAL_CHAT_RECT_Y = PBA_CONTENT_Y
PBA_GLOBAL_CHAT_RECT_WIDTH = PBA_WINDOW_WIDTH - PBA_CONTENT_X * 2 - 35
PBA_GLOBAL_CHAT_RECT_HEIGHT = PBA_CONTENT_HEIGHT - 45

PBA_LIVE_LOG_BOARD_HEIGHT = PBA_CONTENT_HEIGHT - 80

# Etykiety osiagniec PO POLSKU - musza miec te same id co
# s_playerBotAchievementDefs w playerbot_manager.cpp. Nazwy NIGDY nie leca
# przez siec (prosty parser komend klienta nie znosi spacji w argumentach),
# stad ta tablica zamiast czytania nazwy z pakietu.
PBA_ACHIEVEMENT_LABELS = {
	1 : "Pierwszy 30 poziom",
	2 : "Pierwszy 60 poziom",
	3 : "Pierwszy 90 poziom",
}
PBA_ACHIEVEMENT_ORDER = [1, 2, 3]

# Ile klatek bez aktualizacji zanim uznajemy ze bot zniknal/wyszedl z zasiegu
# i chowamy jego dymek na stale - patrz BotOverheadTail.OnUpdate.
PBA_OVERHEAD_TIMEOUT_TICKS = 400

# Wysokosc (w jednostkach swiata, nad stopami postaci) na ktorej
# chr.GetProjectPosition rzutuje punkt na ekran - 220 to ta sama wartosc co
# juz uzywa uiprivateshopbuilder.py (PrivateShopAdvertisementBoard) dla szyldu
# straganu nad glowa DOWOLNEGO gracza.
PBA_OVERHEAD_HEAD_HEIGHT = 220


class BotOverheadTail(ui.ThinBoard):
	"""Maly panel nad glowa bota (do 5 linii), pozycjonowany co klatke przez
	chr.GetProjectPosition(vid, PBA_OVERHEAD_HEAD_HEIGHT) - ten sam mechanizm
	i baza klasy (ui.ThinBoard) co PrivateShopAdvertisementBoard w
	uiprivateshopbuilder.py, ktora robi dokladnie to samo (szyld nad glowa
	DOWOLNEGO gracza z otwartym straganem)."""

	MAX_LINES = 5
	LINE_HEIGHT = 14

	def __init__(self):
		ui.ThinBoard.__init__(self, "UI_BOTTOM")
		self.vid = None
		self.aliveTicks = 0
		self.textLines = []
		for i in xrange(BotOverheadTail.MAX_LINES):
			line = ui.TextLine()
			line.SetParent(self)
			line.SetHorizontalAlignLeft()
			line.SetPosition(6, 4 + i * BotOverheadTail.LINE_HEIGHT)
			self.textLines.append(line)

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def Open(self, vid, lines):
		self.vid = vid
		self.SetLines(lines)
		self.Show()

	def SetLines(self, lines):
		count = min(len(lines), BotOverheadTail.MAX_LINES)
		maxLen = 1
		for i in xrange(BotOverheadTail.MAX_LINES):
			if i < count:
				self.textLines[i].SetText(lines[i])
				self.textLines[i].Show()
				maxLen = max(maxLen, len(lines[i]))
			else:
				self.textLines[i].Hide()
		self.SetSize(maxLen * 6 + 20, 8 + count * BotOverheadTail.LINE_HEIGHT)
		self.aliveTicks = 0

	def OnUpdate(self):
		if self.vid is None:
			return
		self.aliveTicks += 1
		if self.aliveTicks > PBA_OVERHEAD_TIMEOUT_TICKS:
			self.vid = None
			self.Hide()
			return
		try:
			x, y = chr.GetProjectPosition(self.vid, PBA_OVERHEAD_HEAD_HEIGHT)
		except:
			self.vid = None
			self.Hide()
			return
		self.SetPosition(int(x - self.GetWidth() / 2), int(y - self.GetHeight()))

	def Destroy(self):
		self.vid = None
		self.Hide()


class PlayerbotAdminWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)

		self.activeTab = "general"
		self.selectedPid = 0
		self.selectedEmpire = 0

		# Widgets built by pure Python code have no other Python reference
		# once the local variable that created them goes out of scope -
		# without this, refcounting GC destroys the native widget right
		# after Show() (see the same comment on GMPanelWindow._widgets above).
		self._widgets = []

		self.botRows = []          # [(pid, level, empire, x, y, name), ...]
		self.botRowButtons = []    # ui.Button widgets, jeden na wiersz listy
		self.botListStartLine = 0

		self.logPid = 0
		self.logLines = []
		self.logTextLines = []     # ui.TextLine widgets
		self.logStartLine = 0
		self.logScrollableCount = 0

		self.globalChatWebOpen = False
		self.globalChatWebLastPos = None

		self.overheadBoards = {}  # vid -> BotOverheadTail

		self.achievementRows = {}  # id -> (pid, name)
		self.achievementTextLines = []

		# LoadWindow() is called explicitly by __MakePlayerbotAdminWindow
		# right after construction - NOT called here too, or every widget
		# below would be built twice.

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	######################################################################
	## Budowa okna - w calosci w Pythonie (patrz komentarz nad ta sekcja).
	######################################################################

	def __PBAMakeBoard(self, parent, x, y, w, h):
		board = ui.Window()
		board.SetParent(parent)
		board.SetPosition(x, y)
		board.SetSize(w, h)
		board.Show()
		self._widgets.append(board)
		return board

	def __PBAMakeText(self, parent, x, y, text=""):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		self._widgets.append(line)
		return line

	def __PBAMakeButton(self, parent, x, y, w, h, text, size="middle"):
		prefix = "middle_button" if size == "middle" else "small_button"
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetSize(w, h)
		button.SetUpVisual("d:/ymir work/ui/public/%s_01.sub" % prefix)
		button.SetOverVisual("d:/ymir work/ui/public/%s_02.sub" % prefix)
		button.SetDownVisual("d:/ymir work/ui/public/%s_03.sub" % prefix)
		button.SetText(text)
		button.Show()
		self._widgets.append(button)
		return button

	def __PBAMakeEdit(self, parent, x, y, width, maxlen=8):
		slot = ui.SlotBar()
		slot.SetParent(parent)
		slot.SetSize(width, 20)
		slot.SetPosition(x, y)
		slot.Show()
		self._widgets.append(slot)

		editLine = ui.EditLine()
		editLine.SetParent(slot)
		editLine.SetPosition(3, 3)
		editLine.SetSize(width - 6, 17)
		editLine.SetMax(maxlen)
		editLine.Show()
		self._widgets.append(editLine)
		return editLine

	def __PBAMakeScrollBar(self, parent, x, y, height):
		scrollBar = ui.ScrollBar()
		scrollBar.SetParent(parent)
		scrollBar.SetPosition(x, y)
		scrollBar.SetScrollBarSize(height)
		scrollBar.Show()
		self._widgets.append(scrollBar)
		return scrollBar

	def LoadWindow(self):
		self.SetSize(PBA_WINDOW_WIDTH, PBA_WINDOW_HEIGHT)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName("Zarzadzanie Botami [GM]")
		self.SetCloseEvent(self.Close)

		tabDefs = (
			("general",       15,  110, "Ogolne"),
			("globalchat",    130, 125, "Czat ogolny"),
			("live",          260, 125, "Akcje botow"),
			("manage",        390, 125, "Zarzadzanie"),
			("achievements",  520, 110, "Osiagniecia"),
		)
		tabButtons = {}
		for tabName, x, w, text in tabDefs:
			button = self.__PBAMakeButton(self, x, PBA_TAB_Y, w, PBA_TAB_HEIGHT, text)
			button.SetEvent(ui.__mem_func__(self.OnClickTab), tabName)
			tabButtons[tabName] = button
		self.tabGeneral = tabButtons["general"]
		self.tabGlobalChat = tabButtons["globalchat"]
		self.tabLive = tabButtons["live"]
		self.tabManage = tabButtons["manage"]
		self.tabAchievements = tabButtons["achievements"]

		## Lista botow (wspolna dla zakladek "Akcje na zywo" i "Zarzadzanie")
		self.botListPanel = self.__PBAMakeBoard(self, PBA_CONTENT_X, PBA_CONTENT_Y, PBA_LIST_WIDTH, PBA_CONTENT_HEIGHT)
		self.__PBAMakeText(self.botListPanel, 5, 5, "Aktywne boty")
		self.botListScrollBar = self.__PBAMakeScrollBar(self.botListPanel, PBA_LIST_WIDTH - 25, 25, PBA_CONTENT_HEIGHT - 30)
		self.botListScrollBar.SetScrollEvent(ui.__mem_func__(self.OnScrollBotList))
		self.botListSlotBoard = self.__PBAMakeBoard(self.botListPanel, 5, 25, PBA_LIST_WIDTH - 30, PBA_CONTENT_HEIGHT - 30)

		## Zakladka: Ogolne
		self.generalPage = self.__PBAMakeBoard(self, PBA_CONTENT_X, PBA_CONTENT_Y, PBA_WINDOW_WIDTH - PBA_CONTENT_X * 2, PBA_CONTENT_HEIGHT)
		self.generalTotalText = self.__PBAMakeText(self.generalPage, 10, 15, "Aktywne boty: -")
		self.generalInPartyText = self.__PBAMakeText(self.generalPage, 10, 40, "W party: -")
		self.generalStallsText = self.__PBAMakeText(self.generalPage, 10, 65, "Prowadza stragan: -")
		self.generalRefreshButton = self.__PBAMakeButton(self.generalPage, 10, 100, 90, 20, "Odswiez", "small")
		self.generalRefreshButton.SetEvent(ui.__mem_func__(self.RequestStats))

		## Zakladka: Czat ogolny (polaczony strumien wszystkich botow, pelna szerokosc)
		self.globalChatPage = self.__PBAMakeBoard(self, PBA_CONTENT_X, PBA_CONTENT_Y, PBA_WINDOW_WIDTH - PBA_CONTENT_X * 2, PBA_CONTENT_HEIGHT)
		self.globalChatScrollBar = self.__PBAMakeScrollBar(self.globalChatPage, PBA_WINDOW_WIDTH - PBA_CONTENT_X * 2 - 20, 0, PBA_CONTENT_HEIGHT - 45)
		## Prawdziwa strona ma wlasne przewijanie - ten pasek jest tu tylko
		## dlatego, ze bylo prosciej zostawic go zbudowany niz go stad wywalac.
		## Nigdy pokazywany.
		self.globalChatScrollBar.Hide()
		self.globalChatRefreshButton = self.__PBAMakeButton(self.globalChatPage, 10, PBA_CONTENT_HEIGHT - 35, 90, 20, "Odswiez", "small")
		## Strona i tak odswieza sie sama co 2s (patrz BOTCHAT_TEMPLATE w
		## admin_panel.py) - ten przycisk po prostu wymusza to natychmiast.
		self.globalChatRefreshButton.SetEvent(ui.__mem_func__(self.__PBAOpenGlobalChatWeb))

		## Zakladka: Akcje na zywo (prawa kolumna)
		self.liveRightPanel = self.__PBAMakeBoard(self, PBA_RIGHT_X, PBA_CONTENT_Y, PBA_RIGHT_WIDTH, PBA_CONTENT_HEIGHT)
		self.liveSelectedBotText = self.__PBAMakeText(self.liveRightPanel, 10, 10, "Wybierz bota z listy po lewej")
		self.liveLogScrollBar = self.__PBAMakeScrollBar(self.liveRightPanel, PBA_RIGHT_WIDTH - 25, 35, PBA_CONTENT_HEIGHT - 80)
		self.liveLogScrollBar.SetScrollEvent(ui.__mem_func__(self.OnScrollLiveLog))
		self.liveLogBoard = self.__PBAMakeBoard(self.liveRightPanel, 10, 35, PBA_RIGHT_WIDTH - 45, PBA_CONTENT_HEIGHT - 80)
		self.liveRefreshButton = self.__PBAMakeButton(self.liveRightPanel, 10, PBA_CONTENT_HEIGHT - 35, 90, 20, "Odswiez log", "small")
		self.liveRefreshButton.SetEvent(ui.__mem_func__(self.RequestBotLog))

		## Zakladka: Zarzadzanie (prawa kolumna)
		self.manageRightPanel = self.__PBAMakeBoard(self, PBA_RIGHT_X, PBA_CONTENT_Y, PBA_RIGHT_WIDTH, PBA_CONTENT_HEIGHT)
		self.manageSelectedBotText = self.__PBAMakeText(self.manageRightPanel, 10, 10, "Wybierz bota z listy po lewej")

		self.manageKickButton = self.__PBAMakeButton(self.manageRightPanel, 10, 45, 130, 20, "Wyrzuc bota")
		self.manageKickButton.SetEvent(ui.__mem_func__(self.OnClickKick))
		self.manageRespawnButton = self.__PBAMakeButton(self.manageRightPanel, 145, 45, 130, 20, "Zrespawnuj")
		self.manageRespawnButton.SetEvent(ui.__mem_func__(self.OnClickRespawn))

		self.__PBAMakeText(self.manageRightPanel, 10, 90, "Daj przedmiot (vnum / ilosc):")
		self.manageVnumEdit = self.__PBAMakeEdit(self.manageRightPanel, 10, 110, 80, 6)
		self.manageCountEdit = self.__PBAMakeEdit(self.manageRightPanel, 100, 110, 60, 4)
		self.manageGiveButton = self.__PBAMakeButton(self.manageRightPanel, 195, 108, 70, 20, "Wyslij", "small")
		self.manageGiveButton.SetEvent(ui.__mem_func__(self.OnClickGive))

		self.manageRefreshButton = self.__PBAMakeButton(self.manageRightPanel, 10, PBA_CONTENT_HEIGHT - 35, 100, 20, "Odswiez liste", "small")
		self.manageRefreshButton.SetEvent(ui.__mem_func__(self.RequestBotList))

		## Zakladka: Osiagniecia
		self.achievementsPage = self.__PBAMakeBoard(self, PBA_CONTENT_X, PBA_CONTENT_Y, PBA_WINDOW_WIDTH - PBA_CONTENT_X * 2, PBA_CONTENT_HEIGHT)
		self.achievementsBoard = self.__PBAMakeBoard(self.achievementsPage, 0, 0, PBA_WINDOW_WIDTH - PBA_CONTENT_X * 2, PBA_CONTENT_HEIGHT - 45)
		self.achievementsRefreshButton = self.__PBAMakeButton(self.achievementsPage, 10, PBA_CONTENT_HEIGHT - 35, 90, 20, "Odswiez", "small")
		self.achievementsRefreshButton.SetEvent(ui.__mem_func__(self.RequestAchievements))

		self.__PBAShowTab("general")

	def Destroy(self):
		self.__PBACloseGlobalChatWeb()
		self.__ClearOverheadBoards()
		self.__ClearBotListUI()
		self.__ClearLogUI()
		self.__ClearAchievementsUI()
		self._widgets = []
		self.Hide()

	def Open(self):
		self.__PBAShowTab("general")
		self.Show()
		self.SetCenterPosition()
		self.RequestStats()
		self.RequestBotList()
		self.RequestAchievements()

	def Close(self):
		self.__PBACloseGlobalChatWeb()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		## Wolane co klatke przez silnik (ten sam mechanizm co uiweb.WebWindow),
		## dopoki to okno jest widoczne.
		if self.globalChatWebOpen:
			newPos = self.GetGlobalPosition()
			if newPos != self.globalChatWebLastPos:
				self.globalChatWebLastPos = newPos
				app.MoveWebPage(self.__PBAGlobalChatRect())

	######################################################################
	## Dymki nad glowami botow - BotOverheadTail (na gorze pliku), pozycja
	## z chr.GetProjectPosition(vid, ...), ten sam sprawdzony mechanizm co
	## szyld "stragan" w uiprivateshopbuilder.py. Dzialaja SAME, bez pomocy
	## z zewnatrz - ui.ThinBoard dostaje OnUpdate() co klatke od silnika
	## niezaleznie od stanu jakiegokolwiek innego okna - stad brak potrzeby
	## wolania czegokolwiek z game.py poza samym dostarczeniem danych.
	######################################################################

	def OnOverheadTail(self, vid, wire):
		vid = int(vid)
		lines = [l.replace("~", " ") for l in wire.split("|") if l]
		if not lines:
			return

		board = self.overheadBoards.get(vid)
		if board is None:
			board = BotOverheadTail()
			self.overheadBoards[vid] = board
			board.Open(vid, lines)
		else:
			board.SetLines(lines)

	def __ClearOverheadBoards(self):
		for board in self.overheadBoards.values():
			board.Destroy()
		self.overheadBoards = {}

	######################################################################
	## Zakladki
	######################################################################

	def OnClickTab(self, tabName):
		self.__PBAShowTab(tabName)

	def __PBAShowTab(self, tabName):
		self.activeTab = tabName

		if tabName != "globalchat":
			self.__PBACloseGlobalChatWeb()

		self.generalPage.Hide()
		self.globalChatPage.Hide()
		self.liveRightPanel.Hide()
		self.manageRightPanel.Hide()
		self.achievementsPage.Hide()
		self.botListPanel.Hide()

		if tabName == "general":
			self.generalPage.Show()
		elif tabName == "globalchat":
			self.globalChatPage.Show()
			self.__PBAOpenGlobalChatWeb()
		elif tabName == "live":
			self.botListPanel.Show()
			self.liveRightPanel.Show()
			if self.selectedPid:
				self.RequestBotLog()
		elif tabName == "manage":
			self.botListPanel.Show()
			self.manageRightPanel.Show()
		elif tabName == "achievements":
			self.achievementsPage.Show()

	######################################################################
	## Zakladka: Ogolne
	######################################################################

	def RequestStats(self):
		net.SendChatPacket("/botadmin_stats")

	def OnStats(self, total, inParty, stalls):
		self.generalTotalText.SetText("Aktywne boty: %s" % total)
		self.generalInPartyText.SetText("W party: %s" % inParty)
		self.generalStallsText.SetText("Prowadza stragan: %s" % stalls)

	######################################################################
	## Przewijalna lista tekstu - wspolne dla "Czat ogolny" i "Akcje botow".
	## WSZYSTKIE linie dostaja swoj TextLine raz, scroll tylko chowa/pokazuje
	## i przesuwa - nic sie nie tworzy/niszczy w trakcie przeciagania paska.
	######################################################################

	def __PBABuildLineWidgets(self, board, lines):
		widgets = []
		for text in lines:
			line = ui.MakeTextLine(board)
			line.SetText(text)
			widgets.append(line)
		return widgets

	def __PBASetupLineScrollBar(self, scrollBar, panelHeight, itemCount):
		visibleCount = max(1, panelHeight / PBA_LOG_LINE_HEIGHT)
		if itemCount <= visibleCount:
			scrollBar.Hide()
			return 0
		scrollBar.SetScrollBarSize(panelHeight)
		scrollBar.SetMiddleBarSize(float(visibleCount) / float(itemCount))
		scrollBar.Show()
		return itemCount - visibleCount

	def __PBALocateLineWidgets(self, widgets, startLine, panelHeight):
		yPos = 0
		for i in xrange(len(widgets)):
			widget = widgets[i]
			if i < startLine or yPos + PBA_LOG_LINE_HEIGHT > panelHeight:
				widget.Hide()
				continue
			widget.SetPosition(0, yPos)
			widget.Show()
			yPos += PBA_LOG_LINE_HEIGHT

	######################################################################
	## Zakladka: Czat ogolny - prawdziwa strona panelu w wbudowanej
	## przegladarce, nie tekst renderowany przez silnik gry. Patrz
	## PBA_BOTCHAT_URL wyzej i /botchat w admin_panel.py.
	######################################################################

	def __PBAGlobalChatRect(self):
		wx, wy = self.GetGlobalPosition()
		sx = wx + PBA_GLOBAL_CHAT_RECT_X
		sy = wy + PBA_GLOBAL_CHAT_RECT_Y
		return (sx, sy, sx + PBA_GLOBAL_CHAT_RECT_WIDTH, sy + PBA_GLOBAL_CHAT_RECT_HEIGHT)

	def __PBAOpenGlobalChatWeb(self):
		self.globalChatWebLastPos = self.GetGlobalPosition()
		app.ShowWebPage(PBA_BOTCHAT_URL, self.__PBAGlobalChatRect())
		self.globalChatWebOpen = True

	def __PBACloseGlobalChatWeb(self):
		if not self.globalChatWebOpen:
			return
		self.globalChatWebOpen = False
		app.HideWebPage()

	######################################################################
	## Lista botow (wspolna: Akcje na zywo + Zarzadzanie)
	######################################################################

	def RequestBotList(self):
		net.SendChatPacket("/botadmin_list")

	def OnBotRow(self, pid, level, empire, x, y, name):
		self.botRows.append((int(pid), int(level), int(empire), int(x), int(y), name))

	def OnBotListEnd(self):
		self.__PBARebuildBotListUI()

	def __ClearBotListUI(self):
		for btn in self.botRowButtons:
			btn.Hide()
		self.botRowButtons = []

	def __PBARebuildBotListUI(self):
		self.__ClearBotListUI()

		pageSize = self.botListPanel.GetHeight() - 30
		self.botListScrollBar.SetScrollBarSize(pageSize)

		rowCount = len(self.botRows)
		if rowCount <= pageSize / PBA_ROW_HEIGHT:
			self.botListScrollBar.Hide()
			self.botListStartLine = 0
		else:
			self.botListScrollBar.SetMiddleBarSize(float(pageSize / PBA_ROW_HEIGHT) / float(rowCount))
			self.botListScrollBar.Show()

		for pid, level, empire, x, y, name in self.botRows:
			shortName = name[:PBA_LIST_ROW_NAME_MAXLEN]
			button = ui.MakeButton(self.botListSlotBoard, 0, 0, "Lv%d %s" % (level, shortName),
					"d:/ymir work/ui/public/", "small_button_01.sub", "small_button_02.sub", "small_button_03.sub")
			## Bez tego przycisk przyjmuje natywny rozmiar grafiki .sub, ktory
			## bywa wiekszy/inny niz miejsce w liscie i wychodzi poza okno.
			button.SetSize(PBA_LIST_ROW_WIDTH, PBA_LIST_ROW_HEIGHT)
			button.SetEvent(ui.__mem_func__(self.OnSelectBot), pid)
			self.botRowButtons.append(button)

		self.__PBALocateBotListRows()

	def OnScrollBotList(self):
		pageSize = self.botListPanel.GetHeight() - 30
		visibleRows = max(1, pageSize / PBA_ROW_HEIGHT)
		scrollableRows = max(0, len(self.botRows) - visibleRows)
		startLine = int(scrollableRows * self.botListScrollBar.GetPos())

		if startLine != self.botListStartLine:
			self.botListStartLine = startLine
			self.__PBALocateBotListRows()

	def __PBALocateBotListRows(self):
		yPos = 0
		for i in xrange(len(self.botRowButtons)):
			button = self.botRowButtons[i]
			if i < self.botListStartLine:
				button.Hide()
				continue
			button.SetPosition(0, yPos)
			button.Show()
			yPos += PBA_ROW_HEIGHT

	def OnSelectBot(self, pid):
		self.selectedPid = int(pid)

		row = None
		for r in self.botRows:
			if r[0] == self.selectedPid:
				row = r
				break

		if row:
			pid, level, empire, x, y, name = row
			self.selectedEmpire = empire
			self.liveSelectedBotText.SetText("%s (Lv %d) - pid %d" % (name, level, pid))
			self.manageSelectedBotText.SetText("%s (Lv %d) - pid %d, poz (%d, %d), cesarstwo %d" %
					(name, level, pid, x, y, empire))

		if self.activeTab == "live":
			self.RequestBotLog()

	######################################################################
	## Zakladka: Akcje na zywo
	######################################################################

	def RequestBotLog(self):
		if not self.selectedPid:
			return
		self.logPid = self.selectedPid
		self.logLines = []
		net.SendChatPacket("/botadmin_botlog %d" % self.selectedPid)

	def OnBotLogLine(self, pid, text):
		if int(pid) != self.logPid:
			return
		self.logLines.append(text.replace("~", " "))

	def OnBotLogEnd(self, pid):
		if int(pid) != self.logPid:
			return
		self.__PBARebuildLogUI()

	def __ClearLogUI(self):
		for line in self.logTextLines:
			line.Hide()
		self.logTextLines = []

	def __PBARebuildLogUI(self):
		self.__ClearLogUI()
		self.logStartLine = 0

		## Najnowsze na gorze.
		if self.logLines:
			displayLines = list(reversed(self.logLines))
		else:
			displayLines = ["(ten bot nic jeszcze nie powiedzial)"]
		self.logTextLines = self.__PBABuildLineWidgets(self.liveLogBoard, displayLines)

		self.logScrollableCount = self.__PBASetupLineScrollBar(
				self.liveLogScrollBar, PBA_LIVE_LOG_BOARD_HEIGHT, len(self.logTextLines))
		self.__PBALocateLineWidgets(self.logTextLines, self.logStartLine, PBA_LIVE_LOG_BOARD_HEIGHT)

	def OnScrollLiveLog(self):
		startLine = int(self.logScrollableCount * self.liveLogScrollBar.GetPos())
		if startLine != self.logStartLine:
			self.logStartLine = startLine
			self.__PBALocateLineWidgets(self.logTextLines, self.logStartLine, PBA_LIVE_LOG_BOARD_HEIGHT)

	######################################################################
	## Zakladka: Zarzadzanie
	######################################################################

	def OnClickKick(self):
		if not self.selectedPid:
			return
		net.SendChatPacket("/bot_despawn %d" % self.selectedPid)
		self.selectedPid = 0
		self.RequestBotList()

	def OnClickRespawn(self):
		if not self.selectedPid or not self.selectedEmpire:
			return
		net.SendChatPacket("/bot_spawn %d %d" % (self.selectedPid, self.selectedEmpire))
		self.RequestBotList()

	def OnClickGive(self):
		if not self.selectedPid:
			return

		vnumText = self.manageVnumEdit.GetText()
		countText = self.manageCountEdit.GetText()

		if not vnumText:
			return
		if not countText:
			countText = "1"

		net.SendChatPacket("/botadmin_give %d %s %s" % (self.selectedPid, vnumText, countText))

	######################################################################
	## Zakladka: Osiagniecia
	######################################################################

	def RequestAchievements(self):
		self.achievementRows = {}
		net.SendChatPacket("/botadmin_achievements")

	def OnAchievementRow(self, id, pid, name):
		self.achievementRows[int(id)] = (int(pid), name)

	def OnAchievementsEnd(self):
		self.__PBARebuildAchievementsUI()

	def __ClearAchievementsUI(self):
		for line in self.achievementTextLines:
			line.Hide()
		self.achievementTextLines = []

	def __PBARebuildAchievementsUI(self):
		self.__ClearAchievementsUI()

		yPos = 0
		for achievementId in PBA_ACHIEVEMENT_ORDER:
			label = PBA_ACHIEVEMENT_LABELS.get(achievementId, "Osiagniecie #%d" % achievementId)
			pid, name = self.achievementRows.get(achievementId, (0, "-"))

			nameLine = ui.MakeTextLine(self.achievementsBoard)
			nameLine.SetPosition(0, yPos)
			nameLine.SetText(label)
			self.achievementTextLines.append(nameLine)

			winnerLine = ui.MakeTextLine(self.achievementsBoard)
			winnerLine.SetPosition(320, yPos)
			if pid:
				winnerLine.SetText("Zdobyl: %s" % name)
			else:
				winnerLine.SetText("Jeszcze nikt")
			self.achievementTextLines.append(winnerLine)

			yPos += PBA_ROW_HEIGHT

IsQBHide = 0
class Interface(object):
	CHARACTER_STATUS_TAB = 1
	CHARACTER_SKILL_TAB = 2
	
	def __init__(self):
		systemSetting.SetInterfaceHandler(self)
		self.windowOpenPosition = 0
		self.dlgWhisperWithoutTarget = None
		self.inputDialog = None
		self.tipBoard = None
		self.bigBoard = None

		# ITEM_MALL
		self.mallPageDlg = None
		# END_OF_ITEM_MALL

		self.wndWeb = None
		self.wndTaskBar = None
		self.wndCharacter = None
		self.wndInventory = None
		self.wndGMPanel = None
		self.wndPlayerbotAdmin = None
		self.wndExpandedTaskBar = None
		self.wndDragonSoul = None
		self.wndDragonSoulRefine = None
		self.wndChat = None
		self.wndMessenger = None
		self.wndMiniMap = None
		self.wndGuild = None
		self.wndGuildBuilding = None

		self.listGMName = {}
		self.wndQuestWindow = {}
		self.wndQuestWindowNewKey = 0
		self.privateShopAdvertisementBoardDict = {}
		self.guildScoreBoardDict = {}
		self.equipmentDialogDict = {}
		# GM-only "EQ" on the target menu (uitarget.py) - feeds the SAME
		# EquipmentDialog above, just from a safe text response
		# (do_gmpanel_view_equip, "GMEquipChunk") instead of the native
		# /view_equip binary packet, which crashes this client build
		# (confirmed via server syslog: DISCONNECT immediately follows it,
		# 3/3 times - almost certainly a WEAR_MAX_NUM/struct-size mismatch
		# in TPacketViewEquip). vid -> accumulated chunk buffer.
		self._gmEquipBuffers = {}
		event.SetInterfaceWindow(self)

	def __del__(self):
		systemSetting.DestroyInterfaceHandler()
		event.SetInterfaceWindow(None)

	################################
	## Make Windows & Dialogs
	def __MakeUICurtain(self):
		wndUICurtain = ui.Bar("TOP_MOST")
		wndUICurtain.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		wndUICurtain.SetColor(0x77000000)
		wndUICurtain.Hide()
		self.wndUICurtain = wndUICurtain

	def __MakeMessengerWindow(self):
		self.wndMessenger = uiMessenger.MessengerWindow()

		from _weakref import proxy
		self.wndMessenger.SetWhisperButtonEvent(lambda n,i=proxy(self):i.OpenWhisperDialog(n))
		self.wndMessenger.SetGuildButtonEvent(ui.__mem_func__(self.ToggleGuildWindow))

	def __MakeGuildWindow(self):
		self.wndGuild = uiGuild.GuildWindow()

	def __MakeChatWindow(self):
		
		wndChat = uiChat.ChatWindow()
		
		wndChat.SetSize(wndChat.CHAT_WINDOW_WIDTH, 0)
		wndChat.SetPosition(wndMgr.GetScreenWidth()/2 - wndChat.CHAT_WINDOW_WIDTH/2, wndMgr.GetScreenHeight() - wndChat.EDIT_LINE_HEIGHT - 37)
		wndChat.SetHeight(200)
		wndChat.Refresh()
		wndChat.Show()

		self.wndChat = wndChat
		self.wndChat.BindInterface(self)
		self.wndChat.SetSendWhisperEvent(ui.__mem_func__(self.OpenWhisperDialogWithoutTarget))
		self.wndChat.SetOpenChatLogEvent(ui.__mem_func__(self.ToggleChatLogWindow))

	def __MakeTaskBar(self):
		wndTaskBar = uiTaskBar.TaskBar()
		wndTaskBar.LoadWindow()
		self.wndTaskBar = wndTaskBar
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_CHARACTER, ui.__mem_func__(self.ToggleCharacterWindowStatusPage))
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_INVENTORY, ui.__mem_func__(self.ToggleInventoryWindow))
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_MESSENGER, ui.__mem_func__(self.ToggleMessenger))
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_SYSTEM, ui.__mem_func__(self.ToggleSystemDialog))
		if uiTaskBar.TaskBar.IS_EXPANDED:
			self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_EXPAND, ui.__mem_func__(self.ToggleExpandedButton))
			self.wndExpandedTaskBar = uiTaskBar.ExpandedTaskBar()
			self.wndExpandedTaskBar.LoadWindow()
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_DRAGON_SOUL, ui.__mem_func__(self.ToggleDragonSoulWindow))

		else:
			self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_CHAT, ui.__mem_func__(self.ToggleChat))
		
		self.wndEnergyBar = None
		import app
		if app.ENABLE_ENERGY_SYSTEM:
			wndEnergyBar = uiTaskBar.EnergyBar()
			wndEnergyBar.LoadWindow()
			self.wndEnergyBar = wndEnergyBar	

	def __MakeParty(self):
		wndParty = uiParty.PartyWindow()
		wndParty.Hide()
		self.wndParty = wndParty

	def __MakeGameButtonWindow(self):
		wndGameButton = uiGameButton.GameButtonWindow()
		wndGameButton.SetTop()
		wndGameButton.Show()
		wndGameButton.SetButtonEvent("STATUS", ui.__mem_func__(self.__OnClickStatusPlusButton))
		wndGameButton.SetButtonEvent("SKILL", ui.__mem_func__(self.__OnClickSkillPlusButton))
		wndGameButton.SetButtonEvent("QUEST", ui.__mem_func__(self.__OnClickQuestButton))
		wndGameButton.SetButtonEvent("HELP", ui.__mem_func__(self.__OnClickHelpButton))
		wndGameButton.SetButtonEvent("BUILD", ui.__mem_func__(self.__OnClickBuildButton))

		self.wndGameButton = wndGameButton

	def __IsChatOpen(self):
		return True
		
	def __MakeWindows(self):
		wndCharacter = uiCharacter.CharacterWindow()
		wndInventory = uiInventory.InventoryWindow()
		wndInventory.BindInterfaceClass(self)
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			wndDragonSoul = uiDragonSoul.DragonSoulWindow()	
			wndDragonSoulRefine = uiDragonSoul.DragonSoulRefineWindow()
		else:
			wndDragonSoul = None
			wndDragonSoulRefine = None
 
		wndMiniMap = uiMiniMap.MiniMap()
		wndSafebox = uiSafebox.SafeboxWindow()
		
		# ITEM_MALL
		wndMall = uiSafebox.MallWindow()
		self.wndMall = wndMall
		# END_OF_ITEM_MALL

		wndChatLog = uiChat.ChatLogWindow()
		wndChatLog.BindInterface(self)

		wndGMPanel = GMPanelWindow()
		wndGMPanel.Hide()
		self.wndGMPanel = wndGMPanel

		self.wndCharacter = wndCharacter
		self.wndInventory = wndInventory
		self.wndDragonSoul = wndDragonSoul
		self.wndDragonSoulRefine = wndDragonSoulRefine
		self.wndMiniMap = wndMiniMap
		self.wndSafebox = wndSafebox
		self.wndChatLog = wndChatLog
		
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.SetDragonSoulRefineWindow(self.wndDragonSoulRefine)
			self.wndDragonSoulRefine.SetInventoryWindows(self.wndInventory, self.wndDragonSoul)
			self.wndInventory.SetDragonSoulRefineWindow(self.wndDragonSoulRefine)

	def __MakeDialogs(self):
		self.dlgExchange = uiExchange.ExchangeDialog()
		self.dlgExchange.LoadDialog()
		self.dlgExchange.SetCenterPosition()
		self.dlgExchange.Hide()

		self.dlgPointReset = uiPointReset.PointResetDialog()
		self.dlgPointReset.LoadDialog()
		self.dlgPointReset.Hide()

		self.dlgShop = uiShop.ShopDialog()
		self.dlgShop.LoadDialog()
		self.dlgShop.Hide()

		self.dlgRestart = uiRestart.RestartDialog()
		self.dlgRestart.LoadDialog()
		self.dlgRestart.Hide()

		self.dlgSystem = uiSystem.SystemDialog()
		self.dlgSystem.LoadDialog()
		self.dlgSystem.SetOpenHelpWindowEvent(ui.__mem_func__(self.OpenHelpWindow))

		self.dlgSystem.Hide()

		self.dlgPassword = uiSafebox.PasswordDialog()
		self.dlgPassword.Hide()

		self.hyperlinkItemTooltip = uiToolTip.HyperlinkItemToolTip()
		self.hyperlinkItemTooltip.Hide()

		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.Hide()

		self.tooltipSkill = uiToolTip.SkillToolTip()
		self.tooltipSkill.Hide()

		self.privateShopBuilder = uiPrivateShopBuilder.PrivateShopBuilder()
		self.privateShopBuilder.Hide()

		self.dlgRefineNew = uiRefine.RefineDialogNew()
		self.dlgRefineNew.Hide()

	def __MakeHelpWindow(self):
		self.wndHelp = uiHelp.HelpWindow()
		self.wndHelp.LoadDialog()
		self.wndHelp.SetCloseEvent(ui.__mem_func__(self.CloseHelpWindow))
		self.wndHelp.Hide()

	def __MakeTipBoard(self):
		self.tipBoard = uiTip.TipBoard()
		self.tipBoard.Hide()

		self.bigBoard = uiTip.BigBoard()
		self.bigBoard.Hide()

	def __MakeWebWindow(self):
		if constInfo.IN_GAME_SHOP_ENABLE:
			import uiWeb
			self.wndWeb = uiWeb.WebWindow()
			self.wndWeb.LoadWindow()
			self.wndWeb.Hide()

	def __MakeCubeWindow(self):
		self.wndCube = uiCube.CubeWindow()
		self.wndCube.LoadWindow()
		self.wndCube.Hide()

	def __MakeCubeResultWindow(self):
		self.wndCubeResult = uiCube.CubeResultWindow()
		self.wndCubeResult.LoadWindow()
		self.wndCubeResult.Hide()

	# ACCESSORY_REFINE_ADD_METIN_STONE
	def __MakeItemSelectWindow(self):
		self.wndItemSelect = uiselectitem.SelectItemWindow()
		self.wndItemSelect.Hide()
	# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

	def __MakePlayerbotAdminWindow(self):
		self.wndPlayerbotAdmin = PlayerbotAdminWindow()
		self.wndPlayerbotAdmin.LoadWindow()
		self.wndPlayerbotAdmin.Hide()
				
	def MakeInterface(self):
		self.__MakeMessengerWindow()
		self.__MakeGuildWindow()
		self.__MakeChatWindow()
		self.__MakeParty()
		self.__MakeWindows()
		self.__MakeDialogs()

		self.__MakeUICurtain()
		self.__MakeTaskBar()
		self.__MakeGameButtonWindow()
		self.__MakeHelpWindow()
		self.__MakeTipBoard()
		self.__MakeWebWindow()
		self.__MakeCubeWindow()
		self.__MakeCubeResultWindow()
		
		
		# ACCESSORY_REFINE_ADD_METIN_STONE
		self.__MakeItemSelectWindow()
		# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

		self.__MakePlayerbotAdminWindow()

		self.questButtonList = []
		self.whisperButtonList = []
		self.whisperDialogDict = {}
		self.privateShopAdvertisementBoardDict = {}

		self.wndInventory.SetItemToolTip(self.tooltipItem)
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.SetItemToolTip(self.tooltipItem)
			self.wndDragonSoulRefine.SetItemToolTip(self.tooltipItem)
		self.wndSafebox.SetItemToolTip(self.tooltipItem)
		self.wndCube.SetItemToolTip(self.tooltipItem)
		self.wndCubeResult.SetItemToolTip(self.tooltipItem)

		# ITEM_MALL
		self.wndMall.SetItemToolTip(self.tooltipItem)
		# END_OF_ITEM_MALL

		self.wndCharacter.SetSkillToolTip(self.tooltipSkill)
		self.wndTaskBar.SetItemToolTip(self.tooltipItem)
		self.wndTaskBar.SetSkillToolTip(self.tooltipSkill)
		self.wndGuild.SetSkillToolTip(self.tooltipSkill)

		# ACCESSORY_REFINE_ADD_METIN_STONE
		self.wndItemSelect.SetItemToolTip(self.tooltipItem)
		# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

		self.dlgShop.SetItemToolTip(self.tooltipItem)
		self.dlgExchange.SetItemToolTip(self.tooltipItem)
		self.privateShopBuilder.SetItemToolTip(self.tooltipItem)

		self.__InitWhisper()
		self.DRAGON_SOUL_IS_QUALIFIED = False

	def MakeHyperlinkTooltip(self, hyperlink):
		tokens = hyperlink.split(":")
		if tokens and len(tokens):
			type = tokens[0]
			if "item" == type:
				self.hyperlinkItemTooltip.SetHyperlinkItem(tokens)

	## Make Windows & Dialogs
	################################

	def Close(self):
		if self.dlgWhisperWithoutTarget:
			self.dlgWhisperWithoutTarget.Destroy()
			del self.dlgWhisperWithoutTarget

		if uiQuest.QuestDialog.__dict__.has_key("QuestCurtain"):
			uiQuest.QuestDialog.QuestCurtain.Close()

		if self.wndQuestWindow:
			for key, eachQuestWindow in self.wndQuestWindow.items():
				eachQuestWindow.nextCurtainMode = -1
				eachQuestWindow.CloseSelf()
				eachQuestWindow = None
		self.wndQuestWindow = {}

		if self.wndChat:
			self.wndChat.Destroy()

		if self.wndTaskBar:
			self.wndTaskBar.Destroy()
		
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Destroy()
			
		if self.wndEnergyBar:
			self.wndEnergyBar.Destroy()

		if self.wndCharacter:
			self.wndCharacter.Destroy()

		if self.wndInventory:
			self.wndInventory.Destroy()
			
		if self.wndDragonSoul:
			self.wndDragonSoul.Destroy()

		if self.wndDragonSoulRefine:
			self.wndDragonSoulRefine.Destroy()

		if self.dlgExchange:
			self.dlgExchange.Destroy()

		if self.dlgPointReset:
			self.dlgPointReset.Destroy()

		if self.dlgShop:
			self.dlgShop.Destroy()

		if self.dlgRestart:
			self.dlgRestart.Destroy()

		if self.dlgSystem:
			self.dlgSystem.Destroy()

		if self.dlgPassword:
			self.dlgPassword.Destroy()

		if self.wndMiniMap:
			self.wndMiniMap.Destroy()

		if self.wndSafebox:
			self.wndSafebox.Destroy()

		if self.wndWeb:
			self.wndWeb.Destroy()
			self.wndWeb = None

		if self.wndMall:
			self.wndMall.Destroy()

		if self.wndParty:
			self.wndParty.Destroy()

		if self.wndHelp:
			self.wndHelp.Destroy()

		if self.wndCube:
			self.wndCube.Destroy()
			
		if self.wndCubeResult:
			self.wndCubeResult.Destroy()

		if self.wndPlayerbotAdmin:
			self.wndPlayerbotAdmin.Destroy()

		if self.wndMessenger:
			self.wndMessenger.Destroy()

		if self.wndGuild:
			self.wndGuild.Destroy()

		if self.privateShopBuilder:
			self.privateShopBuilder.Destroy()

		if self.dlgRefineNew:
			self.dlgRefineNew.Destroy()

		if self.wndGuildBuilding:
			self.wndGuildBuilding.Destroy()

		if self.wndGameButton:
			self.wndGameButton.Destroy()

		# ITEM_MALL
		if self.mallPageDlg:
			self.mallPageDlg.Destroy()
		# END_OF_ITEM_MALL

		# ACCESSORY_REFINE_ADD_METIN_STONE
		if self.wndItemSelect:
			self.wndItemSelect.Destroy()
		# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

		self.wndChatLog.Destroy()
		for btn in self.questButtonList:
			btn.SetEvent(0)
		for btn in self.whisperButtonList:
			btn.SetEvent(0)
		for dlg in self.whisperDialogDict.itervalues():
			dlg.Destroy()
		for brd in self.guildScoreBoardDict.itervalues():
			brd.Destroy()
		for dlg in self.equipmentDialogDict.itervalues():
			dlg.Destroy()

		# ITEM_MALL
		del self.mallPageDlg
		# END_OF_ITEM_MALL

		del self.wndGuild
		del self.wndMessenger
		del self.wndUICurtain
		del self.wndChat
		del self.wndTaskBar
		if self.wndExpandedTaskBar:
			del self.wndExpandedTaskBar
		del self.wndEnergyBar
		del self.wndCharacter
		del self.wndInventory
		if self.wndDragonSoul:
			del self.wndDragonSoul
		if self.wndDragonSoulRefine:
			del self.wndDragonSoulRefine
		del self.dlgExchange
		del self.dlgPointReset
		del self.dlgShop
		del self.dlgRestart
		del self.dlgSystem
		del self.dlgPassword
		del self.hyperlinkItemTooltip
		del self.tooltipItem
		del self.tooltipSkill
		del self.wndMiniMap
		del self.wndSafebox
		del self.wndMall
		del self.wndParty
		del self.wndHelp
		del self.wndCube
		del self.wndCubeResult
		del self.wndPlayerbotAdmin
		del self.privateShopBuilder
		del self.inputDialog
		del self.wndChatLog
		del self.dlgRefineNew
		del self.wndGuildBuilding
		del self.wndGameButton
		del self.tipBoard
		del self.bigBoard
		del self.wndItemSelect

		self.questButtonList = []
		self.whisperButtonList = []
		self.whisperDialogDict = {}
		self.privateShopAdvertisementBoardDict = {}
		self.guildScoreBoardDict = {}
		self.equipmentDialogDict = {}

		uiChat.DestroyChatInputSetWindow()

	## Skill
	def OnUseSkill(self, slotIndex, coolTime):
		self.wndCharacter.OnUseSkill(slotIndex, coolTime)
		self.wndTaskBar.OnUseSkill(slotIndex, coolTime)
		self.wndGuild.OnUseSkill(slotIndex, coolTime)

	def OnActivateSkill(self, slotIndex):
		self.wndCharacter.OnActivateSkill(slotIndex)
		self.wndTaskBar.OnActivateSkill(slotIndex)

	def OnDeactivateSkill(self, slotIndex):
		self.wndCharacter.OnDeactivateSkill(slotIndex)
		self.wndTaskBar.OnDeactivateSkill(slotIndex)

	def OnChangeCurrentSkill(self, skillSlotNumber):
		self.wndTaskBar.OnChangeCurrentSkill(skillSlotNumber)

	def SelectMouseButtonEvent(self, dir, event):
		self.wndTaskBar.SelectMouseButtonEvent(dir, event)

	## Refresh
	def RefreshAlignment(self):
		self.wndCharacter.RefreshAlignment()

	def RefreshStatus(self):
		self.wndTaskBar.RefreshStatus()
		self.wndCharacter.RefreshStatus()
		self.wndInventory.RefreshStatus()
		if self.wndEnergyBar:
			self.wndEnergyBar.RefreshStatus()
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.RefreshStatus()

	def RefreshStamina(self):
		self.wndTaskBar.RefreshStamina()

	def RefreshSkill(self):
		self.wndCharacter.RefreshSkill()
		self.wndTaskBar.RefreshSkill()

	def RefreshInventory(self):
		self.wndTaskBar.RefreshQuickSlot()
		self.wndInventory.RefreshItemSlot()
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.RefreshItemSlot()

	def RefreshCharacter(self): ## Character �������� ��, Inventory �������� ���� �׸� ���� Refresh
		self.wndCharacter.RefreshCharacter()
		self.wndTaskBar.RefreshQuickSlot()

	def RefreshQuest(self):
		self.wndCharacter.RefreshQuest()

	def RefreshSafebox(self):
		self.wndSafebox.RefreshSafebox()

	# ITEM_MALL
	def RefreshMall(self):
		self.wndMall.RefreshMall()

	def OpenItemMall(self):
		if not self.mallPageDlg:
			self.mallPageDlg = uiShop.MallPageDialog()

		self.mallPageDlg.Open()
	# END_OF_ITEM_MALL

	def RefreshMessenger(self):
		self.wndMessenger.RefreshMessenger()

	def RefreshGuildInfoPage(self):
		self.wndGuild.RefreshGuildInfoPage()

	def RefreshGuildBoardPage(self):
		self.wndGuild.RefreshGuildBoardPage()

	def RefreshGuildMemberPage(self):
		self.wndGuild.RefreshGuildMemberPage()

	def RefreshGuildMemberPageGradeComboBox(self):
		self.wndGuild.RefreshGuildMemberPageGradeComboBox()

	def RefreshGuildSkillPage(self):
		self.wndGuild.RefreshGuildSkillPage()

	def RefreshGuildGradePage(self):
		self.wndGuild.RefreshGuildGradePage()

	def DeleteGuild(self):
		self.wndMessenger.ClearGuildMember()
		self.wndGuild.DeleteGuild()

	def RefreshMobile(self):
		self.dlgSystem.RefreshMobile()

	def OnMobileAuthority(self):
		self.dlgSystem.OnMobileAuthority()

	def OnBlockMode(self, mode):
		self.dlgSystem.OnBlockMode(mode)

	## Calling Functions
	# PointReset
	def OpenPointResetDialog(self):
		self.dlgPointReset.Show()
		self.dlgPointReset.SetTop()

	def ClosePointResetDialog(self):
		self.dlgPointReset.Close()

	# Shop
	def OpenShopDialog(self, vid):
		self.wndInventory.Show()
		self.wndInventory.SetTop()
		self.dlgShop.Open(vid)
		self.dlgShop.SetTop()

	def CloseShopDialog(self):
		self.dlgShop.Close()

	def RefreshShopDialog(self):
		self.dlgShop.Refresh()

	## Quest
	def OpenCharacterWindowQuestPage(self):
		self.wndCharacter.Show()
		self.wndCharacter.SetState("QUEST")

	def OpenQuestWindow(self, skin, idx):

		wnds = ()

		q = uiQuest.QuestDialog(skin, idx)
		q.SetWindowName("QuestWindow" + str(idx))
		q.Show()
		if skin:
			q.Lock()
			wnds = self.__HideWindows()

			# UNKNOWN_UPDATE
			q.AddOnDoneEvent(lambda tmp_self, args=wnds: self.__ShowWindows(args))
			# END_OF_UNKNOWN_UPDATE

		if skin:
			q.AddOnCloseEvent(q.Unlock)
		q.AddOnCloseEvent(lambda key = self.wndQuestWindowNewKey:ui.__mem_func__(self.RemoveQuestDialog)(key))
		self.wndQuestWindow[self.wndQuestWindowNewKey] = q

		self.wndQuestWindowNewKey = self.wndQuestWindowNewKey + 1

		# END_OF_UNKNOWN_UPDATE
		
	def RemoveQuestDialog(self, key):
		del self.wndQuestWindow[key]

	## Exchange
	def StartExchange(self):
		self.dlgExchange.OpenDialog()
		self.dlgExchange.Refresh()

	def EndExchange(self):
		self.dlgExchange.CloseDialog()

	def RefreshExchange(self):
		self.dlgExchange.Refresh()

	## Party
	def AddPartyMember(self, pid, name):
		self.wndParty.AddPartyMember(pid, name)

		self.__ArrangeQuestButton()

	def UpdatePartyMemberInfo(self, pid):
		self.wndParty.UpdatePartyMemberInfo(pid)

	def RemovePartyMember(self, pid):
		self.wndParty.RemovePartyMember(pid)

		##!! 20061026.levites.����Ʈ_��ġ_����
		self.__ArrangeQuestButton()

	def LinkPartyMember(self, pid, vid):
		self.wndParty.LinkPartyMember(pid, vid)

	def UnlinkPartyMember(self, pid):
		self.wndParty.UnlinkPartyMember(pid)

	def UnlinkAllPartyMember(self):
		self.wndParty.UnlinkAllPartyMember()

	def ExitParty(self):
		self.wndParty.ExitParty()

		##!! 20061026.levites.����Ʈ_��ġ_����
		self.__ArrangeQuestButton()

	def PartyHealReady(self):
		self.wndParty.PartyHealReady()

	def ChangePartyParameter(self, distributionMode):
		self.wndParty.ChangePartyParameter(distributionMode)

	## Safebox
	def AskSafeboxPassword(self):
		if self.wndSafebox.IsShow():
			return

		# SAFEBOX_PASSWORD
		self.dlgPassword.SetTitle(localeInfo.PASSWORD_TITLE)
		self.dlgPassword.SetSendMessage("/safebox_password ")
		# END_OF_SAFEBOX_PASSWORD

		self.dlgPassword.ShowDialog()

	def OpenSafeboxWindow(self, size):
		self.dlgPassword.CloseDialog()
		self.wndSafebox.ShowWindow(size)

	def RefreshSafeboxMoney(self):
		self.wndSafebox.RefreshSafeboxMoney()

	def CommandCloseSafebox(self):
		self.wndSafebox.CommandCloseSafebox()

	# ITEM_MALL
	def AskMallPassword(self):
		if self.wndMall.IsShow():
			return
		self.dlgPassword.SetTitle(localeInfo.MALL_PASSWORD_TITLE)
		self.dlgPassword.SetSendMessage("/mall_password ")
		self.dlgPassword.ShowDialog()

	def OpenMallWindow(self, size):
		self.dlgPassword.CloseDialog()
		self.wndMall.ShowWindow(size)

	def CommandCloseMall(self):
		self.wndMall.CommandCloseMall()
	# END_OF_ITEM_MALL

	## Guild
	def OnStartGuildWar(self, guildSelf, guildOpp):
		self.wndGuild.OnStartGuildWar(guildSelf, guildOpp)

		guildWarScoreBoard = uiGuild.GuildWarScoreBoard()
		guildWarScoreBoard.Open(guildSelf, guildOpp)
		guildWarScoreBoard.Show()
		self.guildScoreBoardDict[uiGuild.GetGVGKey(guildSelf, guildOpp)] = guildWarScoreBoard

	def OnEndGuildWar(self, guildSelf, guildOpp):
		self.wndGuild.OnEndGuildWar(guildSelf, guildOpp)

		key = uiGuild.GetGVGKey(guildSelf, guildOpp)

		if not self.guildScoreBoardDict.has_key(key):
			return

		self.guildScoreBoardDict[key].Destroy()
		del self.guildScoreBoardDict[key]

	# GUILDWAR_MEMBER_COUNT
	def UpdateMemberCount(self, gulidID1, memberCount1, guildID2, memberCount2):
		key = uiGuild.GetGVGKey(gulidID1, guildID2)

		if not self.guildScoreBoardDict.has_key(key):
			return

		self.guildScoreBoardDict[key].UpdateMemberCount(gulidID1, memberCount1, guildID2, memberCount2)
	# END_OF_GUILDWAR_MEMBER_COUNT

	def OnRecvGuildWarPoint(self, gainGuildID, opponentGuildID, point):
		key = uiGuild.GetGVGKey(gainGuildID, opponentGuildID)
		if not self.guildScoreBoardDict.has_key(key):
			return

		guildBoard = self.guildScoreBoardDict[key]
		guildBoard.SetScore(gainGuildID, opponentGuildID, point)

	## PK Mode
	def OnChangePKMode(self):
		self.wndCharacter.RefreshAlignment()
		self.dlgSystem.OnChangePKMode()

	## Refine
	def OpenRefineDialog(self, targetItemPos, nextGradeItemVnum, cost, prob, type):
		self.dlgRefineNew.Open(targetItemPos, nextGradeItemVnum, cost, prob, type)

	def AppendMaterialToRefineDialog(self, vnum, count):
		self.dlgRefineNew.AppendMaterial(vnum, count)

	## Show & Hide
	def ShowDefaultWindows(self):
		self.wndTaskBar.Show()
		self.wndMiniMap.Show()
		self.wndMiniMap.ShowMiniMap()
		if self.wndEnergyBar:
			self.wndEnergyBar.Show()

	def ShowAllWindows(self):
		self.wndTaskBar.Show()
		self.wndCharacter.Show()
		self.wndInventory.Show()
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.Show()
			self.wndDragonSoulRefine.Show()
		self.wndChat.Show()
		self.wndMiniMap.Show()
		if self.wndEnergyBar:
			self.wndEnergyBar.Show()
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Show()
			self.wndExpandedTaskBar.SetTop()

	def HideAllWindows(self):
		if self.wndTaskBar:
			self.wndTaskBar.Hide()
		
		if self.wndEnergyBar:
			self.wndEnergyBar.Hide()

		if self.wndCharacter:
			self.wndCharacter.Hide()

		if self.wndInventory:
			self.wndInventory.Hide()
			
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.Hide()
			self.wndDragonSoulRefine.Hide()

		if self.wndChat:
			self.wndChat.Hide()

		if self.wndMiniMap:
			self.wndMiniMap.Hide()

		if self.wndMessenger:
			self.wndMessenger.Hide()

		if self.wndGuild:
			self.wndGuild.Hide()
			
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Hide()
 

	def ShowMouseImage(self):
		self.wndTaskBar.ShowMouseImage()

	def HideMouseImage(self):
		self.wndTaskBar.HideMouseImage()

	def ToggleChat(self):
		if True == self.wndChat.IsEditMode():
			self.wndChat.CloseChat()
		else:
			# ���������� ���������� ä�� �Է��� �ȵ�
			if self.wndWeb and self.wndWeb.IsShow():
				pass
			else:
				self.wndChat.OpenChat()

	def IsOpenChat(self):
		return self.wndChat.IsEditMode()

	def SetChatFocus(self):
		self.wndChat.SetChatFocus()

	def OpenRestartDialog(self):
		self.dlgRestart.OpenDialog()
		self.dlgRestart.SetTop()

	def CloseRestartDialog(self):
		self.dlgRestart.Close()

	def ToggleSystemDialog(self):
		if False == self.dlgSystem.IsShow():
			self.dlgSystem.OpenDialog()
			self.dlgSystem.SetTop()
		else:
			self.dlgSystem.Close()

	def OpenSystemDialog(self):
		self.dlgSystem.OpenDialog()
		self.dlgSystem.SetTop()

	def ToggleMessenger(self):
		if self.wndMessenger.IsShow():
			self.wndMessenger.Hide()
		else:
			self.wndMessenger.SetTop()
			self.wndMessenger.Show()

	def ToggleMiniMap(self):
		if app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT):
			if False == self.wndMiniMap.isShowMiniMap():
				self.wndMiniMap.ShowMiniMap()
				self.wndMiniMap.SetTop()
			else:
				self.wndMiniMap.HideMiniMap()

		else:
			self.wndMiniMap.ToggleAtlasWindow()

	def PressMKey(self):
		if app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT):
			self.ToggleMessenger()

		else:
			self.ToggleMiniMap()

	def SetMapName(self, mapName):
		self.wndMiniMap.SetMapName(mapName)

	def MiniMapScaleUp(self):
		self.wndMiniMap.ScaleUp()

	def MiniMapScaleDown(self):
		self.wndMiniMap.ScaleDown()

	def ToggleCharacterWindow(self, state):
		if False == player.IsObserverMode():
			if False == self.wndCharacter.IsShow():
				self.OpenCharacterWindowWithState(state)
			else:
				if state == self.wndCharacter.GetState():
					self.wndCharacter.OverOutItem()
					self.wndCharacter.Hide()
				else:
					self.wndCharacter.SetState(state)

	def OpenCharacterWindowWithState(self, state):
		if False == player.IsObserverMode():
			self.wndCharacter.SetState(state)
			self.wndCharacter.Show()
			self.wndCharacter.SetTop()

	def ToggleCharacterWindowStatusPage(self):
		self.ToggleCharacterWindow("STATUS")

	def ToggleInventoryWindow(self):
		if False == player.IsObserverMode():
			if False == self.wndInventory.IsShow():
				self.wndInventory.Show()
				self.wndInventory.SetTop()
			else:
				self.wndInventory.OverOutItem()
				self.wndInventory.Close()

	def ToggleGMPanelWindow(self):
		# Wolane WYLACZNIE po odpowiedzi serwera na /gmpanel_open (patrz
		# game.py __GMPanel_Open) - dokladnie ten sam wzorzec co F10/
		# PlayerbotAdminWindow. Serwer sprawdza gm_level (cmd.cpp) na nowo
		# przy kazdym nacisnieciu F9, wiec nie ma tu juz zadnej bramki
		# client-side do sprawdzenia - ta linia w ogole nie wykona sie dla
		# zwyklego gracza, bo "OpenGMPanelWindow" nigdy do niego nie dotrze.
		if False == self.wndGMPanel.IsShow():
			self.wndGMPanel.Show()
			self.wndGMPanel.SetTop()
		else:
			self.wndGMPanel.Hide()

	def OpenPlayerbotAdminWindow(self):
		self.wndPlayerbotAdmin.Open()

	# Called from game.py, wired to uitarget.TargetBoard's "Sprawdz" button
	# (GM-only, next to Zapr. Grupy - see uitarget.py RefreshButton).
	def OpenGMLookupFor(self, name):
		self.wndGMPanel.Show()
		self.wndGMPanel.SetTop()
		self.wndGMPanel.OpenLookupFor(name)

	# Called from game.py, wired to uitarget.TargetBoard's "EQ" button.
	# Opens the SAME native-look EquipmentDialog the vanilla /view_equip
	# would (OpenEquipmentDialog, already existing/working code below) but
	# fills it from do_gmpanel_view_equip's safe text response instead of
	# that crashing native packet - see the comment on _gmEquipBuffers.
	def OpenGMEquipFor(self, vid, name):
		vid = int(vid)
		self.OpenEquipmentDialog(vid)
		self._gmEquipBuffers[vid] = ""
		net.SendChatPacket("/gmpanel_view_equip %d" % vid)

	# Called from game.py's server-command dispatcher with each
	# "GMEquipChunk <vid> <isLast> <data>" payload from do_gmpanel_view_equip
	# (cmd_gm.cpp) - entries are
	# "<slot>:<vnum>:<count>:<s0>:<s1>:<s2>:<t0>:<v0>:...:<t6>:<v6>;"
	# (3 sockets, 7 attribute type/value pairs - ITEM_SOCKET_MAX_NUM /
	# ITEM_ATTRIBUTE_MAX_NUM server-side). SetEquipmentDialogItem must run
	# BEFORE the socket/attr calls for the same slot - it resets
	# itemDataDict[slotIndex] to empty sockets/attrs as a side effect.
	def SetGMEquipChunk(self, vid, isLast, data):
		vid = int(vid)
		if vid not in self._gmEquipBuffers:
			return
		self._gmEquipBuffers[vid] += data

		if isLast != "1":
			return

		raw = self._gmEquipBuffers.pop(vid)
		for entry in raw.split(";"):
			if not entry:
				continue
			bits = entry.split(":")
			if len(bits) != 20:
				continue
			try:
				nums = [int(b) for b in bits]
			except ValueError:
				continue

			slotIndex, vnum, count = nums[0], nums[1], nums[2]
			sockets = nums[3:6]
			attrPairs = nums[6:20]

			self.SetEquipmentDialogItem(vid, slotIndex, vnum, count)
			for socketIndex, value in enumerate(sockets):
				self.SetEquipmentDialogSocket(vid, slotIndex, socketIndex, value)
			for attrIndex in range(7):
				aType = attrPairs[attrIndex * 2]
				aValue = attrPairs[attrIndex * 2 + 1]
				self.SetEquipmentDialogAttr(vid, slotIndex, attrIndex, aType, aValue)

	def ToggleExpandedButton(self):
		if False == player.IsObserverMode():
			if False == self.wndExpandedTaskBar.IsShow():
				self.wndExpandedTaskBar.Show()
				self.wndExpandedTaskBar.SetTop()
			else:
				self.wndExpandedTaskBar.Close()
	
	# ��ȥ��
	def DragonSoulActivate(self, deck):
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.ActivateDragonSoulByExtern(deck)

	def DragonSoulDeactivate(self):
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.DeactivateDragonSoul()
		
	def Highligt_Item(self, inven_type, inven_pos):
		if player.DRAGON_SOUL_INVENTORY == inven_type:
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				self.wndDragonSoul.HighlightSlot(inven_pos)
			
	def DragonSoulGiveQuilification(self):
		self.DRAGON_SOUL_IS_QUALIFIED = True
		self.wndExpandedTaskBar.SetToolTipText(uiTaskBar.ExpandedTaskBar.BUTTON_DRAGON_SOUL, uiScriptLocale.TASKBAR_DRAGON_SOUL)

	def ToggleDragonSoulWindow(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if False == self.wndDragonSoul.IsShow():
					if self.DRAGON_SOUL_IS_QUALIFIED:
						self.wndDragonSoul.Show()
					else:
						try:
							self.wndPopupDialog.SetText(localeInfo.DRAGON_SOUL_UNQUALIFIED)
							self.wndPopupDialog.Open()
						except:
							self.wndPopupDialog = uiCommon.PopupDialog()
							self.wndPopupDialog.SetText(localeInfo.DRAGON_SOUL_UNQUALIFIED)
							self.wndPopupDialog.Open()
				else:
					self.wndDragonSoul.Close()
		
	def ToggleDragonSoulWindowWithNoInfo(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if False == self.wndDragonSoul.IsShow():
					if self.DRAGON_SOUL_IS_QUALIFIED:
						self.wndDragonSoul.Show()
				else:
					self.wndDragonSoul.Close()
				
	def FailDragonSoulRefine(self, reason, inven_type, inven_pos):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if True == self.wndDragonSoulRefine.IsShow():
					self.wndDragonSoulRefine.RefineFail(reason, inven_type, inven_pos)
 
	def SucceedDragonSoulRefine(self, inven_type, inven_pos):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if True == self.wndDragonSoulRefine.IsShow():
					self.wndDragonSoulRefine.RefineSucceed(inven_type, inven_pos)
 
	def OpenDragonSoulRefineWindow(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if False == self.wndDragonSoulRefine.IsShow():
					self.wndDragonSoulRefine.Show()
					if None != self.wndDragonSoul:
						if False == self.wndDragonSoul.IsShow():
							self.wndDragonSoul.Show()

	def CloseDragonSoulRefineWindow(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if True == self.wndDragonSoulRefine.IsShow():
					self.wndDragonSoulRefine.Close()

	# ��ȥ�� ��
	
	def ToggleGuildWindow(self):
		if not self.wndGuild.IsShow():
			if self.wndGuild.CanOpen():
				self.wndGuild.Open()
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GUILD_YOU_DO_NOT_JOIN)
		else:
			self.wndGuild.OverOutItem()
			self.wndGuild.Hide()

	def ToggleChatLogWindow(self):
		if self.wndChatLog.IsShow():
			self.wndChatLog.Hide()
		else:
			self.wndChatLog.Show()

	def CheckGameButton(self):
		if self.wndGameButton:
			self.wndGameButton.CheckGameButton()

	def __OnClickStatusPlusButton(self):
		self.ToggleCharacterWindow("STATUS")

	def __OnClickSkillPlusButton(self):
		self.ToggleCharacterWindow("SKILL")

	def __OnClickQuestButton(self):
		self.ToggleCharacterWindow("QUEST")

	def __OnClickHelpButton(self):
		player.SetPlayTime(1)
		self.CheckGameButton()
		self.OpenHelpWindow()

	def __OnClickBuildButton(self):
		self.BUILD_OpenWindow()

	def OpenHelpWindow(self):
		self.wndUICurtain.Show()
		self.wndHelp.Open()

	def CloseHelpWindow(self):
		self.wndUICurtain.Hide()
		self.wndHelp.Close()

	def OpenWebWindow(self, url):
		self.wndWeb.Open(url)

		# ���������� ���� ä���� �ݴ´�
		self.wndChat.CloseChat()

	# show GIFT
	def ShowGift(self):
		self.wndTaskBar.ShowGift()
	    	
	def CloseWbWindow(self):
		self.wndWeb.Close()

	def OpenCubeWindow(self):
		self.wndCube.Open()

		if FALSE == self.wndInventory.IsShow():
			self.wndInventory.Show()

	def UpdateCubeInfo(self, gold, itemVnum, count):
		self.wndCube.UpdateInfo(gold, itemVnum, count)

	def CloseCubeWindow(self):
		self.wndCube.Close()

	def FailedCubeWork(self):
		self.wndCube.Refresh()

	def SucceedCubeWork(self, itemVnum, count):
		self.wndCube.Clear()
		
		print "ť�� ���� ����! [%d:%d]" % (itemVnum, count)

		if 0: # ��� �޽��� ����� ���� �Ѵ�
			self.wndCubeResult.SetPosition(*self.wndCube.GetGlobalPosition())
			self.wndCubeResult.SetCubeResultItem(itemVnum, count)
			self.wndCubeResult.Open()
			self.wndCubeResult.SetTop()

	def __HideWindows(self):
		hideWindows = self.wndTaskBar,\
						self.wndCharacter,\
						self.wndInventory,\
						self.wndMiniMap,\
						self.wndGuild,\
						self.wndMessenger,\
						self.wndChat,\
						self.wndParty,\
						self.wndGameButton,

		if self.wndEnergyBar:
			hideWindows += self.wndEnergyBar,
 			
		if self.wndExpandedTaskBar:
			hideWindows += self.wndExpandedTaskBar,
 			
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			hideWindows += self.wndDragonSoul,\
						self.wndDragonSoulRefine,

		hideWindows = filter(lambda x:x.IsShow(), hideWindows)
		map(lambda x:x.Hide(), hideWindows)
		import sys

		self.HideAllQuestButton()
		self.HideAllWhisperButton()

		if self.wndChat.IsEditMode():
			self.wndChat.CloseChat()

		return hideWindows

	def __ShowWindows(self, wnds):
		import sys
		map(lambda x:x.Show(), wnds)
		global IsQBHide
		if not IsQBHide:
			self.ShowAllQuestButton()
		else:
			self.HideAllQuestButton()

		self.ShowAllWhisperButton()

	def BINARY_OpenAtlasWindow(self):
		if self.wndMiniMap:
			self.wndMiniMap.ShowAtlas()

	def BINARY_SetObserverMode(self, flag):
		self.wndGameButton.SetObserverMode(flag)

	# ACCESSORY_REFINE_ADD_METIN_STONE
	def BINARY_OpenSelectItemWindow(self):
		self.wndItemSelect.Open()
	# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

	#####################################################################################
	### Private Shop ###

	def OpenPrivateShopInputNameDialog(self):
		#if player.IsInSafeArea():
		#	chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_OPEN_PRIVATE_SHOP_IN_SAFE_AREA)
		#	return

		inputDialog = uiCommon.InputDialog()
		inputDialog.SetTitle(localeInfo.PRIVATE_SHOP_INPUT_NAME_DIALOG_TITLE)
		inputDialog.SetMaxLength(32)
		inputDialog.SetAcceptEvent(ui.__mem_func__(self.OpenPrivateShopBuilder))
		inputDialog.SetCancelEvent(ui.__mem_func__(self.ClosePrivateShopInputNameDialog))
		inputDialog.Open()
		self.inputDialog = inputDialog

	def ClosePrivateShopInputNameDialog(self):
		self.inputDialog = None
		return True

	def OpenPrivateShopBuilder(self):

		if not self.inputDialog:
			return True

		if not len(self.inputDialog.GetText()):
			return True

		self.privateShopBuilder.Open(self.inputDialog.GetText())
		self.ClosePrivateShopInputNameDialog()
		return True

	def AppearPrivateShop(self, vid, text):

		board = uiPrivateShopBuilder.PrivateShopAdvertisementBoard()
		board.Open(vid, text)

		self.privateShopAdvertisementBoardDict[vid] = board

	def DisappearPrivateShop(self, vid):

		if not self.privateShopAdvertisementBoardDict.has_key(vid):
			return

		del self.privateShopAdvertisementBoardDict[vid]
		uiPrivateShopBuilder.DeleteADBoard(vid)

	#####################################################################################
	### Equipment ###

	def OpenEquipmentDialog(self, vid):
		dlg = uiEquipmentDialog.EquipmentDialog()
		dlg.SetItemToolTip(self.tooltipItem)
		dlg.SetCloseEvent(ui.__mem_func__(self.CloseEquipmentDialog))
		dlg.Open(vid)

		self.equipmentDialogDict[vid] = dlg

	def SetEquipmentDialogItem(self, vid, slotIndex, vnum, count):
		if not vid in self.equipmentDialogDict:
			return
		self.equipmentDialogDict[vid].SetEquipmentDialogItem(slotIndex, vnum, count)

	def SetEquipmentDialogSocket(self, vid, slotIndex, socketIndex, value):
		if not vid in self.equipmentDialogDict:
			return
		self.equipmentDialogDict[vid].SetEquipmentDialogSocket(slotIndex, socketIndex, value)

	def SetEquipmentDialogAttr(self, vid, slotIndex, attrIndex, type, value):
		if not vid in self.equipmentDialogDict:
			return
		self.equipmentDialogDict[vid].SetEquipmentDialogAttr(slotIndex, attrIndex, type, value)

	def CloseEquipmentDialog(self, vid):
		if not vid in self.equipmentDialogDict:
			return
		del self.equipmentDialogDict[vid]

	#####################################################################################

	#####################################################################################
	### Quest ###	
	def BINARY_ClearQuest(self, index):
		btn = self.__FindQuestButton(index)
		if 0 != btn:
			self.__DestroyQuestButton(btn)		
	
	def RecvQuest(self, index, name):
		# QUEST_LETTER_IMAGE
		self.BINARY_RecvQuest(index, name, "file", localeInfo.GetLetterImageName())
		# END_OF_QUEST_LETTER_IMAGE

	def BINARY_RecvQuest(self, index, name, iconType, iconName):

		btn = self.__FindQuestButton(index)
		if 0 != btn:
			self.__DestroyQuestButton(btn)

		btn = uiWhisper.WhisperButton()

		# QUEST_LETTER_IMAGE
		##!! 20061026.levites.����Ʈ_�̹���_��ü
		import item
		if "item"==iconType:
			item.SelectItem(int(iconName))
			buttonImageFileName=item.GetIconImageFileName()
		else:
			buttonImageFileName=iconName

		if localeInfo.IsEUROPE():
			if "highlight" == iconType:
				btn.SetUpVisual("locale/ymir_ui/highlighted_quest.tga")
				btn.SetOverVisual("locale/ymir_ui/highlighted_quest_r.tga")
				btn.SetDownVisual("locale/ymir_ui/highlighted_quest_r.tga")
			else:
				btn.SetUpVisual(localeInfo.GetLetterCloseImageName())
				btn.SetOverVisual(localeInfo.GetLetterOpenImageName())
				btn.SetDownVisual(localeInfo.GetLetterOpenImageName())				
		else:
			btn.SetUpVisual(buttonImageFileName)
			btn.SetOverVisual(buttonImageFileName)
			btn.SetDownVisual(buttonImageFileName)
			btn.Flash()
		# END_OF_QUEST_LETTER_IMAGE

		if localeInfo.IsARABIC():
			btn.SetToolTipText(name, 0, 35)
			btn.ToolTipText.SetHorizontalAlignCenter()
		else:
			btn.SetToolTipText(name, -20, 35)
			btn.ToolTipText.SetHorizontalAlignLeft()
			
		btn.SetEvent(ui.__mem_func__(self.__StartQuest), btn)
		btn.Show()

		btn.index = index
		btn.name = name

		self.questButtonList.insert(0, btn)
		self.__ArrangeQuestButton()

		#chat.AppendChat(chat.CHAT_TYPE_NOTICE, localeInfo.QUEST_APPEND)

	def __ArrangeQuestButton(self):

		screenWidth = wndMgr.GetScreenWidth()
		screenHeight = wndMgr.GetScreenHeight()

		##!! 20061026.levites.����Ʈ_��ġ_����
		if self.wndParty.IsShow():
			xPos = 100 + 30
		else:
			xPos = 20

		if localeInfo.IsARABIC():
			xPos = xPos + 15

		yPos = 170 * screenHeight / 600
		yCount = (screenHeight - 330) / 63

		count = 0
		for btn in self.questButtonList:

			btn.SetPosition(xPos + (int(count/yCount) * 100), yPos + (count%yCount * 63))
			count += 1
			global IsQBHide
			if IsQBHide:
				btn.Hide()
			else:
				btn.Show()

	def __StartQuest(self, btn):
		event.QuestButtonClick(btn.index)
		self.__DestroyQuestButton(btn)

	def __FindQuestButton(self, index):
		for btn in self.questButtonList:
			if btn.index == index:
				return btn

		return 0

	def __DestroyQuestButton(self, btn):
		btn.SetEvent(0)
		self.questButtonList.remove(btn)
		self.__ArrangeQuestButton()

	def HideAllQuestButton(self):
		for btn in self.questButtonList:
			btn.Hide()

	def ShowAllQuestButton(self):
		for btn in self.questButtonList:
			btn.Show()
	#####################################################################################

	#####################################################################################
	### Whisper ###

	def __InitWhisper(self):
		chat.InitWhisper(self)

	## ä��â�� "�޽��� ������"�� �������� �̸� ���� ��ȭâ�� ���� �Լ�
	## �̸��� ���� ������ ������ WhisperDialogDict �� ������ �����ȴ�.
	def OpenWhisperDialogWithoutTarget(self):
		if not self.dlgWhisperWithoutTarget:
			dlgWhisper = uiWhisper.WhisperDialog(self.MinimizeWhisperDialog, self.CloseWhisperDialog)
			dlgWhisper.BindInterface(self)
			dlgWhisper.LoadDialog()
			dlgWhisper.OpenWithoutTarget(self.RegisterTemporaryWhisperDialog)
			dlgWhisper.SetPosition(self.windowOpenPosition*30,self.windowOpenPosition*30)
			dlgWhisper.Show()
			self.dlgWhisperWithoutTarget = dlgWhisper

			self.windowOpenPosition = (self.windowOpenPosition+1) % 5

		else:
			self.dlgWhisperWithoutTarget.SetTop()
			self.dlgWhisperWithoutTarget.OpenWithoutTarget(self.RegisterTemporaryWhisperDialog)

	## �̸� ���� ��ȭâ���� �̸��� ���������� WhisperDialogDict�� â�� �־��ִ� �Լ�
	def RegisterTemporaryWhisperDialog(self, name):
		if not self.dlgWhisperWithoutTarget:
			return

		btn = self.__FindWhisperButton(name)
		if 0 != btn:
			self.__DestroyWhisperButton(btn)

		elif self.whisperDialogDict.has_key(name):
			oldDialog = self.whisperDialogDict[name]
			oldDialog.Destroy()
			del self.whisperDialogDict[name]

		self.whisperDialogDict[name] = self.dlgWhisperWithoutTarget
		self.dlgWhisperWithoutTarget.OpenWithTarget(name)
		self.dlgWhisperWithoutTarget = None
		self.__CheckGameMaster(name)

	## ĳ���� �޴��� 1:1 ��ȭ �ϱ⸦ �������� �̸��� ������ �ٷ� â�� ���� �Լ�
	def OpenWhisperDialog(self, name):
		if not self.whisperDialogDict.has_key(name):
			dlg = self.__MakeWhisperDialog(name)
			dlg.OpenWithTarget(name)
			dlg.chatLine.SetFocus()
			dlg.Show()

			self.__CheckGameMaster(name)
			btn = self.__FindWhisperButton(name)
			if 0 != btn:
				self.__DestroyWhisperButton(btn)

	## �ٸ� ĳ���ͷκ��� �޼����� �޾����� �ϴ� ��ư�� ��� �δ� �Լ�
	def RecvWhisper(self, name):
		if not self.whisperDialogDict.has_key(name):
			btn = self.__FindWhisperButton(name)
			if 0 == btn:
				btn = self.__MakeWhisperButton(name)
				btn.Flash()

				chat.AppendChat(chat.CHAT_TYPE_NOTICE, localeInfo.RECEIVE_MESSAGE % (name))

			else:
				btn.Flash()
		elif self.IsGameMasterName(name):
			dlg = self.whisperDialogDict[name]
			dlg.SetGameMasterLook()

	def MakeWhisperButton(self, name):
		self.__MakeWhisperButton(name)

	## ��ư�� �������� â�� ���� �Լ�
	def ShowWhisperDialog(self, btn):
		try:
			self.__MakeWhisperDialog(btn.name)
			dlgWhisper = self.whisperDialogDict[btn.name]
			dlgWhisper.OpenWithTarget(btn.name)
			dlgWhisper.Show()
			self.__CheckGameMaster(btn.name)
		except:
			import dbg
			dbg.TraceError("interface.ShowWhisperDialog - Failed to find key")

		## ��ư �ʱ�ȭ
		self.__DestroyWhisperButton(btn)

	## WhisperDialog â���� �ּ�ȭ ������ ���������� ȣ��Ǵ� �Լ�
	## â�� �ּ�ȭ �մϴ�.
	def MinimizeWhisperDialog(self, name):

		if 0 != name:
			self.__MakeWhisperButton(name)

		self.CloseWhisperDialog(name)

	## WhisperDialog â���� �ݱ� ������ ���������� ȣ��Ǵ� �Լ�
	## â�� ����ϴ�.
	def CloseWhisperDialog(self, name):

		if 0 == name:

			if self.dlgWhisperWithoutTarget:
				self.dlgWhisperWithoutTarget.Destroy()
				self.dlgWhisperWithoutTarget = None

			return

		try:
			dlgWhisper = self.whisperDialogDict[name]
			dlgWhisper.Destroy()
			del self.whisperDialogDict[name]
		except:
			import dbg
			dbg.TraceError("interface.CloseWhisperDialog - Failed to find key")

	## ��ư�� ������ �ٲ������ ��ư�� ������ �ϴ� �Լ�
	def __ArrangeWhisperButton(self):

		screenWidth = wndMgr.GetScreenWidth()
		screenHeight = wndMgr.GetScreenHeight()

		xPos = screenWidth - 70
		yPos = 170 * screenHeight / 600
		yCount = (screenHeight - 330) / 63
		#yCount = (screenHeight - 285) / 63

		count = 0
		for button in self.whisperButtonList:

			button.SetPosition(xPos + (int(count/yCount) * -50), yPos + (count%yCount * 63))
			count += 1

	## �̸����� Whisper ��ư�� ã�� ������ �ִ� �Լ�
	## ��ư�� ��ųʸ��� ���� �ʴ� ���� ���� �Ǿ� ���� ������ ���� ���� ������
	## �̷� ���� ToolTip���� �ٸ� ��ư�鿡 ���� �������� �����̴�.
	def __FindWhisperButton(self, name):
		for button in self.whisperButtonList:
			if button.name == name:
				return button

		return 0

	## â�� ����ϴ�.
	def __MakeWhisperDialog(self, name):
		dlgWhisper = uiWhisper.WhisperDialog(self.MinimizeWhisperDialog, self.CloseWhisperDialog)
		dlgWhisper.BindInterface(self)
		dlgWhisper.LoadDialog()
		dlgWhisper.SetPosition(self.windowOpenPosition*30,self.windowOpenPosition*30)
		self.whisperDialogDict[name] = dlgWhisper

		self.windowOpenPosition = (self.windowOpenPosition+1) % 5

		return dlgWhisper

	## ��ư�� ����ϴ�.
	def __MakeWhisperButton(self, name):
		whisperButton = uiWhisper.WhisperButton()
		whisperButton.SetUpVisual("d:/ymir work/ui/game/windows/btn_mail_up.sub")
		whisperButton.SetOverVisual("d:/ymir work/ui/game/windows/btn_mail_up.sub")
		whisperButton.SetDownVisual("d:/ymir work/ui/game/windows/btn_mail_up.sub")
		if self.IsGameMasterName(name):
			whisperButton.SetToolTipTextWithColor(name, 0xffffa200)
		else:
			whisperButton.SetToolTipText(name)
		whisperButton.ToolTipText.SetHorizontalAlignCenter()
		whisperButton.SetEvent(ui.__mem_func__(self.ShowWhisperDialog), whisperButton)
		whisperButton.Show()
		whisperButton.name = name

		self.whisperButtonList.insert(0, whisperButton)
		self.__ArrangeWhisperButton()

		return whisperButton

	def __DestroyWhisperButton(self, button):
		button.SetEvent(0)
		self.whisperButtonList.remove(button)
		self.__ArrangeWhisperButton()

	def HideAllWhisperButton(self):
		for btn in self.whisperButtonList:
			btn.Hide()

	def ShowAllWhisperButton(self):
		for btn in self.whisperButtonList:
			btn.Show()

	def __CheckGameMaster(self, name):
		if not self.listGMName.has_key(name):
			return
		if self.whisperDialogDict.has_key(name):
			dlg = self.whisperDialogDict[name]
			dlg.SetGameMasterLook()

	def RegisterGameMasterName(self, name):
		if self.listGMName.has_key(name):
			return
		self.listGMName[name] = "GM"

	def IsGameMasterName(self, name):
		if self.listGMName.has_key(name):
			return True
		else:
			return False

	#####################################################################################

	#####################################################################################
	### Guild Building ###

	def BUILD_OpenWindow(self):
		self.wndGuildBuilding = uiGuild.BuildGuildBuildingWindow()
		self.wndGuildBuilding.Open()
		self.wndGuildBuilding.wnds = self.__HideWindows()
		self.wndGuildBuilding.SetCloseEvent(ui.__mem_func__(self.BUILD_CloseWindow))

	def BUILD_CloseWindow(self):
		self.__ShowWindows(self.wndGuildBuilding.wnds)
		self.wndGuildBuilding = None

	def BUILD_OnUpdate(self):
		if not self.wndGuildBuilding:
			return

		if self.wndGuildBuilding.IsPositioningMode():
			import background
			x, y, z = background.GetPickingPoint()
			self.wndGuildBuilding.SetBuildingPosition(x, y, z)

	def BUILD_OnMouseLeftButtonDown(self):
		if not self.wndGuildBuilding:
			return

		# GUILD_BUILDING
		if self.wndGuildBuilding.IsPositioningMode():
			self.wndGuildBuilding.SettleCurrentPosition()
			return True
		elif self.wndGuildBuilding.IsPreviewMode():
			pass
		else:
			return True
		# END_OF_GUILD_BUILDING
		return False

	def BUILD_OnMouseLeftButtonUp(self):
		if not self.wndGuildBuilding:
			return

		if not self.wndGuildBuilding.IsPreviewMode():
			return True

		return False

	def BULID_EnterGuildArea(self, areaID):
		# GUILD_BUILDING
		mainCharacterName = player.GetMainCharacterName()
		masterName = guild.GetGuildMasterName()

		if mainCharacterName != masterName:
			return

		if areaID != player.GetGuildID():
			return
		# END_OF_GUILD_BUILDING

		self.wndGameButton.ShowBuildButton()

	def BULID_ExitGuildArea(self, areaID):
		self.wndGameButton.HideBuildButton()

	#####################################################################################

	def IsEditLineFocus(self):
		if self.ChatWindow.chatLine.IsFocus():
			return 1

		if self.ChatWindow.chatToLine.IsFocus():
			return 1

		return 0

	def EmptyFunction(self):
		pass

if __name__ == "__main__":

	import app
	import wndMgr
	import systemSetting
	import mouseModule
	import grp
	import ui
	import localeInfo

	app.SetMouseHandler(mouseModule.mouseController)
	app.SetHairColorEnable(True)
	wndMgr.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetScreenSize(systemSetting.GetWidth(), systemSetting.GetHeight())
	app.Create(localeInfo.APP_TITLE, systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
	mouseModule.mouseController.Create()

	class TestGame(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)

			localeInfo.LoadLocaleData()
			player.SetItemData(0, 27001, 10)
			player.SetItemData(1, 27004, 10)

			self.interface = Interface()
			self.interface.MakeInterface()
			self.interface.ShowDefaultWindows()
			self.interface.RefreshInventory()
			#self.interface.OpenCubeWindow()

		def __del__(self):
			ui.Window.__del__(self)

		def OnUpdate(self):
			app.UpdateGame()

		def OnRender(self):
			app.RenderGame()
			grp.PopState()
			grp.SetInterfaceRenderState()

	game = TestGame()
	game.SetSize(systemSetting.GetWidth(), systemSetting.GetHeight())
	game.Show()

	app.Loop()
