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
  * uitooltip.py  - the GM branch no longer kills every item tooltip, and the
                    speed potion's asks for no apply name this client lacks.
  * game.py       - the "PlayerBotStatus" server command, handed to
                    playerbot_status_tail.py (hand-written, beside serverinfo.py);
                    Auto Lowy: the "AutoHuntTarget" and "AutoHuntLoot" commands, the K key and the
                    hunt among the updateables (uiautohunt.py, hand-written).
  * uiinventory.py - the auto-stack button queues its moves for
                    autostackpump.py (hand-written) instead of sending them all
                    in one frame, which the server's flood limit closed on.
  * offlineshopmanage.py - a click on an empty slot of the shop's edit grid
                    removes nothing instead of raising KeyError.
  * uigameoption.py, uiscript/gameoptiondialog.py - the "Tytuly botow" row of
                    the game options: a bot's personality title or the classic
                    alignment title (playerbot_status_tail.py keeps the choice).

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
        # The speed potion's tooltip asked item for APPLY_ATT_SPEED and
        # APPLY_MOV_SPEED, which this client's item module does not export
        # (AttributeError in l0st3k's syserr, 15 September), so hovering one
        # broke the tooltip. On this line an apply is its point: 17 and 19,
        # what Zielona and Fioletowa Mikstura carry in value0.
        (b'\t\tif abilityType == item.APPLY_ATT_SPEED:\r\n',
         b'\t\tif abilityType == getattr(item, "APPLY_ATT_SPEED", 17):\r\n'),
        (b'\t\telif abilityType == item.APPLY_MOV_SPEED:\r\n',
         b'\t\telif abilityType == getattr(item, "APPLY_MOV_SPEED", 19):\r\n'),
    ],
    # A bot's status arrives as the command "PlayerBotStatus <vid> <hex>"
    # (SendPlayerBotOverheadChat) and is drawn as a text tail only: as talking
    # it also went into the chat history, and a town of bots filled the window.
    # Both edits take in the line after the insertion, so a second run on our
    # own output finds neither anchor and changes nothing.
    'game.py': [
        (b'\t\t\t"PlayerbotOverhead"\t\t\t\t: self.__PlayerbotAdmin_Overhead,\r\n'
         b'\t\t\t"Top1Badge"\t\t\t\t\t\t\t: self.__OnTop1Badge,\r\n',
         b'\t\t\t"PlayerbotOverhead"\t\t\t\t: self.__PlayerbotAdmin_Overhead,\r\n'
         b'\t\t\t"PlayerBotStatus"\t\t\t\t: self.__PlayerBotStatus,\r\n'
         b'\t\t\t"Top1Badge"\t\t\t\t\t\t\t: self.__OnTop1Badge,\r\n'),
        (b'\t\t\t\tself.interface.wndPlayerbotAdmin.OnOverheadTail(vid, wire)\r\n'
         b'\r\n'
         b'\t# Same transport as PlayerbotOverhead above (SendPlayerBotOverheadTail),\r\n',
         b'\t\t\t\tself.interface.wndPlayerbotAdmin.OnOverheadTail(vid, wire)\r\n'
         b'\r\n'
         b'\tdef __PlayerBotStatus(self, vid="0", encodedText="", *rest):\r\n'
         b'\t\t# A bot\'s status as a text tail and nothing in the chat history\r\n'
         b'\t\t# (playerbot_status_tail.py; SendPlayerBotOverheadChat on the server).\r\n'
         b'\t\timport playerbot_status_tail\r\n'
         b'\t\tplayerbot_status_tail.show(vid, encodedText)\r\n'
         b'\r\n'
         b'\t# Same transport as PlayerbotOverhead above (SendPlayerBotOverheadTail),\r\n'),
        # Auto Lowy (uiautohunt.py, hand-written beside serverinfo.py): the
        # server names the target with "AutoHuntTarget <vid>", K opens the
        # window, and the hunt runs as one of the game's updateables. Every
        # insertion splits its own anchor, so a re-run on our output finds the
        # new text and not the old, and none of them touches the two above.
        (b'\t\t\t"Top1Badge"\t\t\t\t\t\t\t: self.__OnTop1Badge,\r\n'
         b'\r\n'
         b'\t\t\t# fishing\r\n',
         b'\t\t\t"Top1Badge"\t\t\t\t\t\t\t: self.__OnTop1Badge,\r\n'
         b'\t\t\t"AutoHuntTarget"\t\t\t\t: self.__AutoHuntTarget,\r\n'
         b'\t\t\t"AutoHuntLoot"\t\t\t\t\t: self.__AutoHuntLoot,\r\n'
         b'\r\n'
         b'\t\t\t# fishing\r\n'),
        (b'\t\t#onPressKeyDict[app.DIK_K]\t\t\t= lambda : self.interface.OpenCubeWindow()\r\n'
         b'\t\t# CUBE_TEST_END\r\n',
         b'\t\t#onPressKeyDict[app.DIK_K]\t\t\t= lambda : self.interface.OpenCubeWindow()\r\n'
         b'\t\tonPressKeyDict[app.DIK_K]\t\t\t= lambda : self.__ToggleAutoHunt()\r\n'
         b'\t\t# CUBE_TEST_END\r\n'),
        (b'\t\tself.RegisterUpdatable(updateable.PickUpOnDownKey())\r\n'
         b'\r\n',
         b'\t\tself.RegisterUpdatable(updateable.PickUpOnDownKey())\r\n'
         b'\t\timport uiautohunt\r\n'
         b'\t\tself.RegisterUpdatable(uiautohunt.GetHunter())\r\n'
         b'\r\n'),
        (b'\t\tself.__PressQuickSlot(5)\r\n'
         b'\t\treturn\r\n'
         b'\r\n'
         b'\tdef __ToggleSprint(self):\r\n',
         b'\t\tself.__PressQuickSlot(5)\r\n'
         b'\t\treturn\r\n'
         b'\r\n'
         b'\tdef __ToggleAutoHunt(self):\r\n'
         b'\t\timport uiautohunt\r\n'
         b'\t\tuiautohunt.ToggleWindow()\r\n'
         b'\r\n'
         b'\tdef __AutoHuntTarget(self, vid="0", *rest):\r\n'
         b'\t\timport uiautohunt\r\n'
         b'\t\tuiautohunt.OnServerTarget(vid)\r\n'
         b'\r\n'
         b'\tdef __AutoHuntLoot(self, vid="0", x="0", y="0", *rest):\r\n'
         b'\t\timport uiautohunt\r\n'
         b'\t\tuiautohunt.OnServerLoot(vid, x, y)\r\n'
         b'\r\n'
         b'\tdef __ToggleSprint(self):\r\n'),
        # A bot's personality in the place of its alignment title: the server's
        # "PlayerBotTitle <vid> <personality>" (ManagePlayerBotPersonalityTitle)
        # goes to playerbot_status_tail.py, and the keeper that puts the title
        # back after an alignment refresh joins the updateables with the first
        # one. The entry sits before the admin window's block and the handler
        # before the achievements' end - places no other edit here touches, and
        # each insertion splits its own anchor.
        (b'\t\t\t"GMPanelSetAIWeightResult"\t: self.__GMPanelSetAIWeightResult,\r\n'
         b'\r\n'
         b'\t\t\t"OpenPlayerbotAdminWindow"\t\t\t: self.__PlayerbotAdmin_Open,\r\n',
         b'\t\t\t"GMPanelSetAIWeightResult"\t: self.__GMPanelSetAIWeightResult,\r\n'
         b'\r\n'
         b'\t\t\t"PlayerBotTitle"\t\t\t\t: self.__PlayerBotTitle,\r\n'
         b'\t\t\t"OpenPlayerbotAdminWindow"\t\t\t: self.__PlayerbotAdmin_Open,\r\n'),
        (b'\t\t\tself.interface.wndPlayerbotAdmin.OnAchievementRow(id, pid, name)\r\n'
         b'\r\n'
         b'\tdef __PlayerbotAdmin_AchievementsEnd(self):\r\n',
         b'\t\t\tself.interface.wndPlayerbotAdmin.OnAchievementRow(id, pid, name)\r\n'
         b'\r\n'
         b'\tdef __PlayerBotTitle(self, vid="0", personality="-1", *rest):\r\n'
         b'\t\t# A bot\'s personality where a player\'s alignment title stands\r\n'
         b'\t\t# (playerbot_status_tail.py; ManagePlayerBotPersonalityTitle on the server).\r\n'
         b'\t\timport playerbot_status_tail\r\n'
         b'\t\tif playerbot_status_tail.show_title(vid, personality) and not getattr(self, "playerbotTitleKeeper", None):\r\n'
         b'\t\t\tself.playerbotTitleKeeper = playerbot_status_tail.GetTitleKeeper()\r\n'
         b'\t\t\tself.RegisterUpdatable(self.playerbotTitleKeeper)\r\n'
         b'\r\n'
         b'\tdef __PlayerbotAdmin_AchievementsEnd(self):\r\n'),
    ],
    # The inventory's auto-stack button sent a move for every pair of stacks of
    # one item in a single frame - 300 moves for 25 stacks - and 300 packets in
    # a second is the server's flood limit (CInputMain::Analyze logs
    # FLOOD_HEADER_13 and closes the connection): "loga postac do ekranu
    # logowania" (l0st3k, 15 September). The same moves now leave a few at a
    # time through autostackpump.py (hand-written beside this file).
    'uiinventory.py': [
        (b'\tdef __OnAutoStackButton(self):\r\n'
         b'\t\tTOTAL_SLOTS = player.INVENTORY_MAX_NUM\r\n',
         b'\tdef __OnAutoStackButton(self):\r\n'
         b'\t\timport autostackpump\r\n'
         b'\t\tmoves = []\r\n'
         b'\t\tTOTAL_SLOTS = player.INVENTORY_MAX_NUM\r\n'),
        (b'\t\t\t\t\tif destItemVnum == srcItemVnum:\r\n'
         b'\t\t\t\t\t\tself.__SendMoveItemPacket(destSlot, sourceSlot, 0)\r\n'
         b'\r\n'
         b'\t\tchat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AUTOSTACK_INVENTORY)\r\n',
         b'\t\t\t\t\tif destItemVnum == srcItemVnum:\r\n'
         b'\t\t\t\t\t\tmoves.append((destSlot, sourceSlot))\r\n'
         b'\r\n'
         b'\t\tautostackpump.Queue(moves)\r\n'
         b'\t\tchat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AUTOSTACK_INVENTORY)\r\n'),
    ],
    # The offline shop's edit grid removes an item on a left click and never
    # asked whether the slot held one: a click on an empty slot was a KeyError
    # in syserr.txt (slots 44, 45, 55 and 57 in l0st3k's, 15 September). An
    # empty slot does nothing now.
    'offlineshopmanage.py': [
        (b'\tdef RemoveItem(self, slotIndex):\r\n'
         b'\t\tikashop.SendRemoveItem(constInfo.myshop_data["items"][slotIndex]["id"])\r\n',
         b'\tdef RemoveItem(self, slotIndex):\r\n'
         b'\t\titemData = constInfo.myshop_data["items"].get(slotIndex)\r\n'
         b'\t\tif not itemData:\r\n'
         b'\t\t\treturn\r\n'
         b'\t\tikashop.SendRemoveItem(itemData["id"])\r\n'),
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
    # The game options get a "Tytuly botow" row under the floating text one:
    # a bot's personality title (playerbot_status_tail.py, 2.0.53) or the
    # classic alignment title, the player's own choice ("dodac w opcjach gry
    # aby moc przelaczac pomiedzy klasycznymi i aktualnymi", NerrVoVy, 15
    # September). The two buttons follow the night mode's pattern: bound by
    # name, refreshed from the module, and the click writes the choice through
    # SetTitlesEnabled. The dialog's script grows by one row's height.
    'uigameoption.py': [
        (b'\t\tself.RefreshFloatingTextButtons()\r\n'
         b'\r\n'
         b'\tdef __del__(self):\r\n',
         b'\t\tself.RefreshFloatingTextButtons()\r\n'
         b'\t\tself.RefreshBotTitleButtons()\r\n'
         b'\r\n'
         b'\tdef __del__(self):\r\n'),
        (b'\t\tself.floatingTextButtonList = []\r\n'
         b'\t\tself.toolTip = None\r\n',
         b'\t\tself.floatingTextButtonList = []\r\n'
         b'\t\tself.botTitleButtonList = []\r\n'
         b'\t\tself.toolTip = None\r\n'),
        (b'\t\t\tself.floatingTextButtonList.append(GetObject("floating_text_off"))\r\n'
         b'\r\n'
         b'\t\texcept:\r\n',
         b'\t\t\tself.floatingTextButtonList.append(GetObject("floating_text_off"))\r\n'
         b'\r\n'
         b'\t\t\tself.botTitleButtonList.append(GetObject("bot_title_personality_button"))\r\n'
         b'\t\t\tself.botTitleButtonList.append(GetObject("bot_title_classic_button"))\r\n'
         b'\r\n'
         b'\t\texcept:\r\n'),
        (b'\t\tself.floatingTextButtonList[2].SAFE_SetEvent(self.__OnClickFloatingTextButton, 0)\r\n',
         b'\t\tself.floatingTextButtonList[2].SAFE_SetEvent(self.__OnClickFloatingTextButton, 0)\r\n'
         b'\r\n'
         b'\t\tself.botTitleButtonList[0].SAFE_SetEvent(self.__OnClickBotTitleButton, 1)\r\n'
         b'\t\tself.botTitleButtonList[1].SAFE_SetEvent(self.__OnClickBotTitleButton, 0)\r\n'),
        (b'\tdef __OnClickFloatingTextButton(self, state):\r\n'
         b'\t\tsystemSetting.SetShowFloatingText(state)\r\n'
         b'\t\tself.RefreshFloatingTextButtons()\r\n'
         b'\r\n',
         b'\tdef __OnClickFloatingTextButton(self, state):\r\n'
         b'\t\tsystemSetting.SetShowFloatingText(state)\r\n'
         b'\t\tself.RefreshFloatingTextButtons()\r\n'
         b'\r\n'
         b'\t# A bot\'s personality title or the classic alignment title (NerrVoVy):\r\n'
         b'\t# playerbot_status_tail.py keeps the choice in playerbot_titles.cfg.\r\n'
         b'\tdef __OnClickBotTitleButton(self, enabled):\r\n'
         b'\t\timport playerbot_status_tail\r\n'
         b'\t\tplayerbot_status_tail.SetTitlesEnabled(enabled)\r\n'
         b'\t\tself.RefreshBotTitleButtons()\r\n'
         b'\r\n'
         b'\tdef RefreshBotTitleButtons(self):\r\n'
         b'\t\timport playerbot_status_tail\r\n'
         b'\t\tfor btn in self.botTitleButtonList:\r\n'
         b'\t\t\tbtn.SetUp()\r\n'
         b'\t\tif playerbot_status_tail.TitlesEnabled():\r\n'
         b'\t\t\tself.botTitleButtonList[0].Down()\r\n'
         b'\t\telse:\r\n'
         b'\t\t\tself.botTitleButtonList[1].Down()\r\n'
         b'\r\n'),
    ],
    'uiscript/gameoptiondialog.py': [
        (b'\t"width" : 300,\r\n'
         b'\t"height" : 25*16+8,\r\n',
         b'\t"width" : 300,\r\n'
         b'\t"height" : 25*16+8+21,\r\n'),
        (b'\t\t\t"width" : 300,\r\n'
         b'\t\t\t"height" : 25*16+8,\r\n',
         b'\t\t\t"width" : 300,\r\n'
         b'\t\t\t"height" : 25*16+8+21,\r\n'),
        (b'\t\t\t\t\t"text" : uiScriptLocale.GAME_OPTIONS_FLOATING_TEXT_2,\r\n'
         b'\r\n'
         b'\t\t\t\t\t"default_image" : ROOT_PATH + "middle_button_01.sub",\r\n'
         b'\t\t\t\t\t"over_image" : ROOT_PATH + "middle_button_02.sub",\r\n'
         b'\t\t\t\t\t"down_image" : ROOT_PATH + "middle_button_03.sub",\r\n'
         b'\t\t\t\t},\r\n'
         b'\t\t\t],\r\n',
         b'\t\t\t\t\t"text" : uiScriptLocale.GAME_OPTIONS_FLOATING_TEXT_2,\r\n'
         b'\r\n'
         b'\t\t\t\t\t"default_image" : ROOT_PATH + "middle_button_01.sub",\r\n'
         b'\t\t\t\t\t"over_image" : ROOT_PATH + "middle_button_02.sub",\r\n'
         b'\t\t\t\t\t"down_image" : ROOT_PATH + "middle_button_03.sub",\r\n'
         b'\t\t\t\t},\r\n'
         b'\r\n'
         b'\t\t\t\t## BOT TITLES (playerbot_status_tail.py): the personality or the\r\n'
         b'\t\t\t\t## classic alignment title. The strings are CP1250 escapes so the\r\n'
         b'\t\t\t\t## file stays ASCII like the rest of the root.\r\n'
         b'\t\t\t\t{\r\n'
         b'\t\t\t\t\t"name" : "bot_title_text",\r\n'
         b'\t\t\t\t\t"type" : "text",\r\n'
         b'\r\n'
         b'\t\t\t\t\t"x" : LINE_LABEL_X,\r\n'
         b'\t\t\t\t\t"y" : 382+2,\r\n'
         b'\r\n'
         b'\t\t\t\t\t"text" : "Tytu\\xb3y bot\\xf3w",\r\n'
         b'\t\t\t\t},\r\n'
         b'\t\t\t\t{\r\n'
         b'\t\t\t\t\t"name" : "bot_title_personality_button",\r\n'
         b'\t\t\t\t\t"type" : "radio_button",\r\n'
         b'\r\n'
         b'\t\t\t\t\t"x" : LINE_DATA_X,\r\n'
         b'\t\t\t\t\t"y" : 382,\r\n'
         b'\r\n'
         b'\t\t\t\t\t"text" : "Osobowo\\x9c\\xe6",\r\n'
         b'\r\n'
         b'\t\t\t\t\t"default_image" : ROOT_PATH + "middle_button_01.sub",\r\n'
         b'\t\t\t\t\t"over_image" : ROOT_PATH + "middle_button_02.sub",\r\n'
         b'\t\t\t\t\t"down_image" : ROOT_PATH + "middle_button_03.sub",\r\n'
         b'\t\t\t\t},\r\n'
         b'\t\t\t\t{\r\n'
         b'\t\t\t\t\t"name" : "bot_title_classic_button",\r\n'
         b'\t\t\t\t\t"type" : "radio_button",\r\n'
         b'\r\n'
         b'\t\t\t\t\t"x" : LINE_DATA_X+MIDDLE_BUTTON_WIDTH,\r\n'
         b'\t\t\t\t\t"y" : 382,\r\n'
         b'\r\n'
         b'\t\t\t\t\t"text" : "Klasyczne",\r\n'
         b'\r\n'
         b'\t\t\t\t\t"default_image" : ROOT_PATH + "middle_button_01.sub",\r\n'
         b'\t\t\t\t\t"over_image" : ROOT_PATH + "middle_button_02.sub",\r\n'
         b'\t\t\t\t\t"down_image" : ROOT_PATH + "middle_button_03.sub",\r\n'
         b'\t\t\t\t},\r\n'
         b'\t\t\t],\r\n'),
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
        out = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(out), exist_ok=True)  # uiscript/...
        io.open(out, 'wb').write(data)
        print('clientrootify: client-root/%s (%d bytes)' % (name, len(data)))


if __name__ == '__main__':
    main()
