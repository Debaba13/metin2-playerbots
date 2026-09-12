#ifndef __INC_METIN2_PLAYERBOT_CONSUMABLES_H__
#define __INC_METIN2_PLAYERBOT_CONSUMABLES_H__

// The Moonlight Treasure Chest, and the boosters that come out of it.
//
// A chest is an ITEM_USE the engine opens itself - UseItem on 50011 draws one
// line of the chest's special item group into the bag - so opening one is a
// matter of noticing it is there. What it holds the bot already knows how to
// spend: the bonus scrolls go through playerbot_bonus.h, which takes a scroll
// from the bag before it buys one; the speed potions through UseUtilityPotions;
// the big potions through the ordinary potion lists. The two boosters, Hand of
// the Critic and Hand of Penetration, are new: a twenty-percent chance for ten
// minutes, worth drinking when a fight starts and pointless at an NPC.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_gear.h.

namespace
{
	// Boxes the engine will not open, by vnum and until when.
	//
	// "Skrzynia Eksperta III" and "Skrzynia Mistrza I" (50192, 50193) are
	// giftboxes a bot cannot use, and it asked anyway - close to six thousand
	// refusals a minute between them. Worse, a refusal ended the whole pass, so
	// every Moonlight chest sitting behind one of these in the bag was never
	// reached: that is how 587 bots came to be holding nine thousand of them.
	//
	// Keyed by bot AND vnum since 2.0.17. Keyed by vnum alone it was one map
	// for the whole population, and a refusal is mostly transient - the bag
	// had no room for the group at that moment - so the first bot in the tick
	// with a full bag switched the Moonlight chest off for everyone for ten
	// minutes, and with two thousand bots there always was one: a player's
	// table showed 165 663 unopened chests in the bots' bags (uxietoszef,
	// 12 September). What 50192 and 50193 actually were is a level limit
	// (Skrzynia Eksperta III at fifty, Skrzynia Mistrza I at sixty), and that
	// is asked before UseItem now, so no refusal has to be remembered for it.
	std::map<std::pair<DWORD, DWORD>, DWORD> s_mapPlayerBotChestRefused;

	// A box this bot has not grown into: the engine's own LIMIT_LEVEL on the
	// giftbox, which UseItem would refuse with a chat line nobody reads.
	bool IsPlayerBotChestLevelLocked(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && item->GetLevelLimit() > ch->GetLevel();
	}

	// Opens one chest per pass. UseItem refuses when the bag has no room, and
	// says so in the engine's own log; the bot's next town visit makes room.
	// A box that belongs on a counter rather than in the bot's own hands.
	//
	// Two kinds qualify. One this bot cannot open - a level-locked giftbox, or
	// one the engine refused it - which is goods to whoever holds it. And the
	// surplus of a stack big enough that selling it costs the bot nothing: the
	// chest pass keeps eating the stack meanwhile, so most of what drops is
	// still opened and only what piles up is sold. A stack goes up whole
	// because a private shop line is a whole stack; splitting one is its own
	// change and not this one.
	bool IsPlayerBotSurplusChest(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || (item->GetVnum() != PLAYERBOT_MOONLIGHT_CHEST_VNUM &&
				item->GetType() != ITEM_GIFTBOX))
			return false;
		if (IsPlayerBotChestLevelLocked(ch, item))
			return true;
		// A box the engine refused this bot stays goods; the retry clock is not
		// consulted here - it exists to stop the asking, not to make the box
		// valuable again.
		if (s_mapPlayerBotChestRefused.find(std::make_pair(ch->GetPlayerID(), item->GetVnum())) !=
				s_mapPlayerBotChestRefused.end())
			return true;
		return item->GetCount() >= PLAYERBOT_CHEST_STALL_MIN_STACK;
	}

	// Ile pol plecaka jest naprawde puste.
	//
	// GetEmptyInventory(height) odpowiada na inne pytanie - "gdzie zmiesci sie
	// jeden przedmiot tej wysokosci" - i nie da sie z niego zbudowac rezerwacji
	// na kilka nagrod naraz.
	int CountPlayerBotFreeInventoryCells(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		int free = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			if (!ch->GetInventoryItem(cell))
				++free;
		return free;
	}

	bool ManagePlayerBotChests(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || dwNow < state.dwNextChestTime)
			return false;
		state.dwNextChestTime = dwNow + PLAYERBOT_CHEST_INTERVAL;
		// A treasure chest (the silver and gold ones) opens with a key, not by
		// itself: the engine's path is "use the key on the chest", which removes
		// both and hands out the chest's group. Any key whose lock value matches.
		for (WORD boxCell = 0; boxCell < PLAYERBOT_BAG_CELLS; ++boxCell)
		{
			LPITEM box = ch->GetInventoryItem(boxCell);
			if (!box || box->GetType() != ITEM_TREASURE_BOX)
				continue;
			for (WORD keyCell = 0; keyCell < PLAYERBOT_BAG_CELLS; ++keyCell)
			{
				LPITEM key = ch->GetInventoryItem(keyCell);
				if (!key || key->GetType() != ITEM_TREASURE_KEY || key->GetValue(0) != box->GetValue(0))
					continue;
				// Miejsce na caly zestaw, a nie na jeden przedmiot: patrz
				// PLAYERBOT_CHEST_FREE_CELLS. Wysokie przedmioty potrzebuja
				// dodatkowo ciaglych trzech pol w jednej kolumnie, o co
				// GetEmptyInventory(3) pyta wprost.
				// The whole set or nothing (PlayerBotBagTakesGroup, playerbot_gear.h):
				// the key's use hands out the box's own group.
				int cellsNeeded = 0;
				if (!PlayerBotBagTakesGroup(ch, box->GetVnum(), cellsNeeded))
					return false;
				const DWORD boxVnum = box->GetVnum(), keyVnum = key->GetVnum();
				const int before = ch->GetEmptyInventory(1);
				if (ch->UseItem(TItemPos(INVENTORY, keyCell), TItemPos(INVENTORY, boxCell)))
				{
					sys_log(0, "PLAYERBOT_CHEST: treasure pid=%u name=%s box=%u key=%u free_before=%d free_after=%d",
							ch->GetPlayerID(), ch->GetName(), boxVnum, keyVnum, before, ch->GetEmptyInventory(1));
					return true;
				}
				break;
			}
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			// The Moonlight chest, and every boss casket (ITEM_GIFTBOX: the Orc
			// Chief's, the Spider Queen's) - the engine opens both the same way.
			if (!item || (item->GetVnum() != PLAYERBOT_MOONLIGHT_CHEST_VNUM &&
					item->GetType() != ITEM_GIFTBOX))
				continue;
			// A box already on this bot's own counter. UseItem refuses a locked
			// item, and that refusal is remembered by vnum for every bot in the
			// world - so opening one that is for sale would stop the whole
			// population opening that kind of box for the next few minutes.
			if (item->isLocked())
				continue;
			// A box above the bot's level is not asked for: the engine would
			// refuse it, and remembering that refusal is what used to switch the
			// chest off for everybody.
			if (IsPlayerBotChestLevelLocked(ch, item))
				continue;
			const std::pair<DWORD, DWORD> refuseKey(ch->GetPlayerID(), item->GetVnum());
			std::map<std::pair<DWORD, DWORD>, DWORD>::const_iterator refused =
					s_mapPlayerBotChestRefused.find(refuseKey);
			if (refused != s_mapPlayerBotChestRefused.end() && dwNow < refused->second)
				continue;
			// The same test as for the treasure box: room for the whole set the
			// group can hand out, placed the way the engine places it.
			int cellsNeeded = 0;
			if (!PlayerBotBagTakesGroup(ch, item->GetVnum(), cellsNeeded))
				return false;
			const int before = ch->GetEmptyInventory(1);
			const DWORD chestVnum = item->GetVnum();
			const DWORD chestCount = item->GetCount();
			if (ch->UseItem(TItemPos(INVENTORY, cell)))
			{
				sys_log(0, "PLAYERBOT_CHEST: opened pid=%u name=%s level=%u map=%ld free_before=%d free_after=%d",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(),
						before, ch->GetEmptyInventory(1));
				return true;
			}
			// Not the end of the pass: the next box in the bag may well open,
			// and giving up here is what kept the Moonlight chests behind these
			// two out of reach. The refusal is remembered - for this bot and
			// this box - so the bot stops asking every eight seconds.
			s_mapPlayerBotChestRefused[refuseKey] = dwNow + PLAYERBOT_CHEST_REFUSED_RETRY;
			PlayerBotLogThrottled("chest_refused", dwNow,
					"PLAYERBOT_CHEST: refused pid=%u name=%s vnum=%u count=%u free=%d",
					ch->GetPlayerID(), ch->GetName(), chestVnum,
					(unsigned int)chestCount, ch->GetEmptyInventory(1));
			continue;
		}
		return false;
	}

	// A booster at the start of a fight. The engine keeps one of each running
	// at a time and refuses a second, so a failed use is the usual case and
	// nothing to log; a minute between attempts is enough.
	bool UsePlayerBotBoosters(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || dwNow < state.dwNextBoosterTime)
			return false;
		if (state.bCurrentAction != BOT_ACTION_FIGHT || state.bVisitingShop ||
				state.bRecoveringAfterDeath || state.bTacticalRetreat)
			return false;
		state.dwNextBoosterTime = dwNow + PLAYERBOT_BOOSTER_INTERVAL;
		bool used = false;
		for (size_t b = 0; b < sizeof(PLAYERBOT_BOOSTER_VNUMS) / sizeof(PLAYERBOT_BOOSTER_VNUMS[0]); ++b)
		{
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetVnum() != PLAYERBOT_BOOSTER_VNUMS[b])
					continue;
				const DWORD vnum = item->GetVnum();
				if (ch->UseItem(TItemPos(INVENTORY, cell)))
				{
					sys_log(0, "PLAYERBOT_CHEST: booster pid=%u name=%s vnum=%u",
							ch->GetPlayerID(), ch->GetName(), vnum);
					used = true;
				}
				break;
			}
		}
		return used;
	}
}

#endif
