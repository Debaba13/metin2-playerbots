#ifndef __INC_METIN2_PLAYERBOT_ACTIVITIES_H__
#define __INC_METIN2_PLAYERBOT_ACTIVITIES_H__

// The things a bot does that are not fighting: raising a horse, and fishing.
//
// Both own the whole tick while they run - the rod sits in the weapon slot, and
// a bot walking to the stable is not hunting - which is why they read as
// separate activities rather than as steps inside the combat loop.
//
// An implementation fragment in the sense playerbot_types.h describes: it
// defines objects, relies on the engine headers playerbot_manager.cpp includes
// above it, and reopens the same anonymous namespace. Include it exactly once,
// after playerbot_movement.h (it walks) and playerbot_gear.h (it buys).

namespace
{
	BYTE GetPlayerBotNextHorseRequiredLevel(BYTE horseLevel)
	{
		if (horseLevel >= 21)
			return 255;
		if (horseLevel >= 20)
			return 50; // military horse milestone
		if (horseLevel >= 10)
			return 35; // combat horse milestone
		return PLAYERBOT_HORSE_REQUIRED_LEVEL;
	}

	bool CanPlayerBotAdvanceHorse(LPCHARACTER ch)
	{
		if (!ch || ch->GetHorseLevel() >= 21)
			return false;
		// A horse at exactly ten is what the battle horse trial asks for, and one
		// more medal makes it eleven - after which no medal, quest or NPC in this
		// world will ever put it back. So a bot that could still win the battle
		// horse keeps its medals until the stable keeper has handed the scroll
		// over, which sets the horse to eleven itself and starts the ladder again.
		//
		// This also stops it farming medals it must not spend: every other caller
		// of this function - the Monkey Dungeon expedition, buying a medal off a
		// stall, the goal that walks it to the stable - reads the same answer and
		// leaves it free to be out in the desert earning the thing instead.
		if (IsPlayerBotBattleHorseCandidate(ch))
			return false;
		return ch->GetLevel() >= GetPlayerBotNextHorseRequiredLevel(ch->GetHorseLevel());
	}

	void GetPlayerBotNpcApproach(DWORD playerID, long npcX, long npcY, DWORD salt,
			long& approachX, long& approachY);

	bool ManagePlayerBotHorse(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		// The stable keeper stands in all six villages, so the horse errand is a
		// local one wherever the bot lives.
		playerbot_empire_rules::TTownServices svc;
		if (!ch || !playerbot_empire_rules::GetTownServices(ch->GetMapIndex(), svc) ||
				state.bVisitingShop || state.bVisitingBiologist)
			return false;
		if (!state.bVisitingStable && dwNow < state.dwNextHorseCheckTime)
			return false;
		if (!state.bVisitingStable)
			state.dwNextHorseCheckTime = dwNow + 3000;

		const BYTE horseLevel = ch->GetHorseLevel();
		const bool bBattleHorseWaiting = IsPlayerBotBattleHorseEarned(ch) &&
				ch->GetGold() >= (int)PLAYERBOT_BATTLE_HORSE_FEE;
		if (!bBattleHorseWaiting && (!CanPlayerBotAdvanceHorse(ch) ||
				ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) <= 0))
		{
			state.bVisitingStable = false;
			state.dwNextHorseActionTime = 0;
			return false;
		}

		LPCHARACTER victim = state.dwTargetVID != 0
				? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		if (!state.bVisitingStable && victim && !victim->IsDead())
			return false;

		if (!state.bVisitingStable)
		{
			int delivered = std::max(0, ch->GetQuestFlag(PLAYERBOT_HORSE_MEDALS_FLAG));
			if (delivered < horseLevel)
			{
				delivered = horseLevel;
				ch->SetQuestFlag(PLAYERBOT_HORSE_MEDALS_FLAG, delivered);
			}
			state.bVisitingStable = true;
			state.dwNextHorseActionTime = 0;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_HORSE: going to stable pid=%u name=%s medals=%d horse_level=%u delivered=%d",
					ch->GetPlayerID(), ch->GetName(),
					ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM), horseLevel, delivered);
		}

		SetPlayerBotGoal(ch, state, BOT_GOAL_HORSE, dwNow);
		SetPlayerBotAction(state, BOT_ACTION_STABLE, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		const bool inM2 = IsPlayerBotM2Map(ch->GetMapIndex());
		const long stableX = svc.stableKeeper.x;
		const long stableY = svc.stableKeeper.y;
		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), stableX, stableY,
				inM2 ? 0x4d324853U : 0x484f5253U, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > PLAYERBOT_STABLE_ARRIVE_DISTANCE)
		{
			if (!MovePlayerBot(ch, approachX, approachY, dwNow, PLAYERBOT_STABLE_SNAP_CELLS, true, true) &&
					state.bStuckCounter >= 6)
			{
				state.bVisitingStable = false;
				state.dwNextHorseCheckTime = dwNow + 30000;
				ClearPlayerBotRoute(state, true);
				sys_err("PLAYERBOT_HORSE: route failed pid=%u name=%s map=%ld from=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
				return false;
			}
			return true;
		}

		SetPlayerBotRidingForTravel(ch, state, false, dwNow, "stable_interaction");
		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (state.dwNextHorseActionTime == 0)
		{
			state.dwNextHorseActionTime = dwNow + number(5000, 15000);
			return true;
		}
		if (dwNow < state.dwNextHorseActionTime)
			return true;

		// The trial first: a bot that has earned the battle horse is here to
		// collect it, not to hand in a medal it does not have.
		if (CollectPlayerBotBattleHorse(ch))
		{
			state.bVisitingStable = false;
			state.dwNextHorseActionTime = 0;
			state.dwNextHorseCheckTime = dwNow + number(30000, 60000);
			ClearPlayerBotRoute(state, true);
			return false;
		}

		if (ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) <= 0)
		{
			state.bVisitingStable = false;
			state.dwNextHorseActionTime = 0;
			state.dwNextHorseCheckTime = dwNow + number(15000, 30000);
			ClearPlayerBotRoute(state, true);
			return false;
		}

		ch->RemoveSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM, 1);
		int delivered = std::max(0, ch->GetQuestFlag(PLAYERBOT_HORSE_MEDALS_FLAG));
		delivered = std::max(delivered, (int)ch->GetHorseLevel()) + 1;
		delivered = std::min(delivered, 21);
		ch->SetQuestFlag(PLAYERBOT_HORSE_MEDALS_FLAG, delivered);
		ch->SetQuestFlag(PLAYERBOT_HORSE_LAST_DELIVERY_TIME_FLAG, get_global_time());
		if (ch->GetHorseLevel() < delivered)
			ch->SetHorseLevel(delivered);
		ch->SetSkillLevel(131, 10);

		const char* stage = delivered >= 21 ? "military" :
				(delivered >= 11 ? "combat" : "normal");
		sys_log(0, "PLAYERBOT_HORSE: medal delivered pid=%u name=%s delivered=%d horse_level=%u stage=%s medals_left=%d",
				ch->GetPlayerID(), ch->GetName(), delivered, ch->GetHorseLevel(), stage,
				ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM));

		if (delivered >= 21 || !CanPlayerBotAdvanceHorse(ch) ||
				ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) <= 0)
		{
			state.bVisitingStable = false;
			state.dwNextHorseActionTime = 0;
			state.dwNextHorseCheckTime = dwNow + number(30000, 60000);
			ClearPlayerBotRoute(state, true);
			return false;
		}

		state.dwNextHorseActionTime = dwNow + number(5000, 10000);
		return true;
	}

	// A small, stable slice of the M1 population fishes. Careful collectors are the
	// natural anglers -- pearls are a collector's prize -- but a few other
	// personalities join them so the bank is never one archetype deep. The roll is
	// derived from the player id, so a bot keeps the same hobby across restarts.
	// The rod is a weapon and carries a level limit like any other. Asking the
	// item what it needs keeps this honest: the hand-picked level 10 was below
	// the rod's real requirement of 30, so a level-13 bot bought tackle it could
	// never equip and then retried the same failing step for good.
	bool CanPlayerBotUseFishingRod(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		TItemTable* proto = ITEM_MANAGER::instance().GetTable(PLAYERBOT_FISHING_ROD_VNUM);
		if (!proto)
			return false;
		return GetPlayerBotProtoLevelLimit(proto) <= (int)ch->GetLevel();
	}

	bool IsPlayerBotAngler(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!CanPlayerBotUseFishingRod(ch))
			return false;
		const DWORD roll = PlayerBotNavHash(ch->GetPlayerID() ^ 0x46495348U) % 100U;
		// Thirty collectors in a hundred and eight of everyone else, stretched or
		// shrunk by the FISHING weight.
		//
		// Raised from 20/2 because fishing is the one errand that takes a bot to
		// Joan and keeps it there: the bank, the Fisherman who sells the bait and
		// the market ring are all on map 21, so an angler is a customer, a
		// passer-by and a stall in one. Joan looked deserted with nineteen of
		// eight hundred live bots standing on its map, and half of those nineteen
		// were the anglers.
		const int chance = state.bPersonality == BOT_PERSONALITY_CAREFUL_COLLECTOR ? 30 : 8;
		return PlayerBotWeightedRoll(roll, chance, PLAYERBOT_WEIGHT_FISHING);
	}

	// Which angler stands where. A stand is claimed for the session and released
	// with it, because a hash cannot promise what the Discord asked for: fifty
	// anglers drawing from fifty slots collide by the birthday problem long
	// before they fill them, and what that looks like in game is a heap.
	//
	// The engine constrains none of this. CHARACTER::fishing() tests only the
	// cell the angler is standing on; it computes a point four hundred units in
	// front of the character and then never reads it. So the bank is chosen to
	// look right - standable ground with the river in front - and the spacing is
	// a metre because that is what was asked for.
	struct TPlayerBotFishingStand
	{
		DWORD dwPid;
		DWORD dwTouched;
	};
	std::map<int, TPlayerBotFishingStand> s_mapPlayerBotFishingStands;

	void ReleasePlayerBotFishingStand(DWORD playerID)
	{
		for (std::map<int, TPlayerBotFishingStand>::iterator it =
				s_mapPlayerBotFishingStands.begin();
				it != s_mapPlayerBotFishingStands.end(); ++it)
		{
			if (it->second.dwPid == playerID)
			{
				s_mapPlayerBotFishingStands.erase(it);
				return;
			}
		}
	}

	// Slot ids are per map: three banks numbering their stands from zero would
	// have an angler in Yongan holding Joan's stand seven.
	int PlayerBotFishingClaimKey(long mapIndex, int slot)
	{
		return (int)mapIndex * 1000 + slot;
	}

	void GetPlayerBotFishingStand(DWORD playerID, DWORD dwNow, long mapIndex,
			long& standX, long& standY)
	{
		const TPlayerBotFishingBank* bank = GetPlayerBotFishingBank(mapIndex);
		if (!bank)
			return;
		const int slots = (int)bank->standCount;
		int mine = -1;
		for (std::map<int, TPlayerBotFishingStand>::iterator it =
				s_mapPlayerBotFishingStands.begin();
				it != s_mapPlayerBotFishingStands.end(); ++it)
		{
			if (it->second.dwPid == playerID)
			{
				mine = it->first;
				it->second.dwTouched = dwNow;
				break;
			}
		}
		if (mine < 0)
		{
			// From its own place in the row, then along it: the same bot comes
			// back to the same stand session after session while the bank is
			// empty, and takes the next free one when it is not.
			const int start = (int)(PlayerBotNavHash(playerID ^ 0x42414e4bU) % (DWORD)slots);
			for (int step = 0; step < slots && mine < 0; ++step)
			{
				const int slot = PlayerBotFishingClaimKey(mapIndex, (start + step) % slots);
				std::map<int, TPlayerBotFishingStand>::const_iterator it =
						s_mapPlayerBotFishingStands.find(slot);
				if (it == s_mapPlayerBotFishingStands.end() ||
						dwNow - it->second.dwTouched >= PLAYERBOT_FISHING_STAND_CLAIM)
					mine = slot;
			}
			// More anglers than stands one day: share a stand rather than refuse
			// to fish.
			if (mine < 0)
				mine = PlayerBotFishingClaimKey(mapIndex, start);
			TPlayerBotFishingStand& claim = s_mapPlayerBotFishingStands[mine];
			claim.dwPid = playerID;
			claim.dwTouched = dwNow;
		}
		const int index = mine - PlayerBotFishingClaimKey(mapIndex, 0);
		if (index < 0 || index >= slots)
			return;
		standX = bank->stands[index].x;
		standY = bank->stands[index].y;
	}

	// The water this stand looks at. Due east was right for the one straight
	// stretch the first version knew about and wrong for every bend.
	void GetPlayerBotFishingFacing(DWORD playerID, long mapIndex,
			long& waterX, long& waterY)
	{
		const TPlayerBotFishingBank* bank = GetPlayerBotFishingBank(mapIndex);
		waterX = bank ? bank->centre.x : PLAYERBOT_FISHING_WATER_X;
		waterY = 0;
		if (!bank)
			return;
		for (std::map<int, TPlayerBotFishingStand>::const_iterator it =
				s_mapPlayerBotFishingStands.begin();
				it != s_mapPlayerBotFishingStands.end(); ++it)
		{
			if (it->second.dwPid != playerID)
				continue;
			const int index = it->first - PlayerBotFishingClaimKey(mapIndex, 0);
			if (index < 0 || index >= (int)bank->standCount)
				return;
			waterX = bank->stands[index].waterX;
			waterY = bank->stands[index].waterY;
			return;
		}
	}

	bool IsPlayerBotHoldingRod(LPCHARACTER ch)
	{
		LPITEM rod = ch ? ch->GetWear(WEAR_WEAPON) : NULL;
		return rod && rod->GetType() == ITEM_ROD;
	}

	// A bot stops walking at PLAYERBOT_NAV_ARRIVAL_DISTANCE from its goal, so an
	// arrival test tighter than that can never pass: the walk reports success,
	// the caller asks for another step, nothing moves, and the bot stands in the
	// gap with no failure recorded anywhere. Both files are included here, so
	// the rule can be checked rather than remembered.
	static_assert(PLAYERBOT_FISHING_ARRIVE >= PLAYERBOT_NAV_ARRIVAL_DISTANCE,
			"an arrival radius below the navigation's own strands the bot short of it");

	// Rods in the bag, whatever their grade. The engine refines a rod as it
	// is fished with (fishing.cpp: a roll per catch, and the rod becomes its
	// GetRefinedVnum, a new item), so a bot's Wedka+1 is a Wedka+2 after a
	// session and CountSpecifyItem(27400) says none: three of five anglers in
	// Joan had bought rods until the bag was full of them.
	int CountPlayerBotRods(LPCHARACTER ch)
	{
		int rods = 0;
		for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetType() == ITEM_ROD)
				++rods;
		}
		return rods;
	}

	bool EquipPlayerBotRod(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		if (IsPlayerBotHoldingRod(ch))
			return true;

		// The best rod in the bag: the grades are consecutive vnums, so the
		// highest vnum is the most refined one.
		LPITEM best = NULL;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetType() == ITEM_ROD && (!best || item->GetVnum() > best->GetVnum()))
				best = item;
		}
		if (!best)
			return false;
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		if (worn && !ch->UnequipItem(worn))
			return false;
		if (PlayerBotEquipItem(ch, best))
		{
			sys_log(0, "PLAYERBOT_FISHING: rod equipped pid=%u name=%s vnum=%u",
					ch->GetPlayerID(), ch->GetName(), best->GetVnum());
			return true;
		}
		return false;
	}

	// The rod is worthless in a fight, so a finished session always puts the real
	// weapon back before the bot rejoins the grind.
	void StowPlayerBotRod(LPCHARACTER ch)
	{
		if (!ch)
			return;
		LPITEM rod = ch->GetWear(WEAR_WEAPON);
		if (!rod || rod->GetType() != ITEM_ROD)
			return;
		if (!ch->UnequipItem(rod))
			return;
		EquipFirstAvailablePlayerBotWeapon(ch);
	}

	// Bait does not sit in the pouch while fishing: using it moves its value into
	// the rod's socket 2, which is what the engine actually checks before a cast.
	bool BaitPlayerBotRod(LPCHARACTER ch)
	{
		LPITEM rod = ch ? ch->GetWear(WEAR_WEAPON) : NULL;
		if (!rod || rod->GetType() != ITEM_ROD)
			return false;
		if (rod->GetSocket(2) != 0)
			return true;

		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetVnum() != PLAYERBOT_FISHING_BAIT_VNUM)
				continue;
			ch->UseItem(TItemPos(INVENTORY, cell));
			return rod->GetSocket(2) != 0;
		}
		return false;
	}

	// One item per pass. Gutting a fish and prying a shell open both run through
	// UseItem, which frees the very inventory slot being iterated over.
	// Defined in playerbot_economy.h, which this file precedes.
	bool PlayerBotNeedsRefineMaterial(LPCHARACTER ch, DWORD materialVnum);

	// What a thing is worth to sell: what the market has paid for it, else a
	// fifth of the shop price, which is what the merchant pays.
	long long GetPlayerBotVnumSaleValue(DWORD vnum, DWORD dwNow)
	{
		size_t samples = 0;
		const DWORD paid = GetPlayerBotSaleUnitPrice(vnum, 0, dwNow, &samples);
		if (paid != 0)
			return (long long)paid;
		TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto ? (long long)(proto->dwShopBuyPrice / 5) : 0;
	}

	// Prying a shell open is a bet, not a step: half the time a Stone Piece,
	// a third of the time nothing, a pearl the rest. Open it when what the bet
	// pays on average beats what the shell sells for whole; the careful
	// collector wants the bet to pay half again as much, the gear specialist
	// takes a slightly worse one for the pearls it is after.
	bool ShouldPlayerBotOpenShellfish(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return false;
		const long long expected =
				(long long)GetPlayerBotShellfishPermille(PLAYERBOT_SHELL_STONE, PLAYERBOT_SHELLFISH_STONE_PERMILLE) *
						GetPlayerBotVnumSaleValue(PLAYERBOT_STONE_PIECE_VNUM, dwNow) +
				(long long)GetPlayerBotShellfishPermille(PLAYERBOT_SHELL_WHITE, PLAYERBOT_SHELLFISH_WHITE_PERMILLE) *
						GetPlayerBotVnumSaleValue(PLAYERBOT_PEARL_FIRST_VNUM, dwNow) +
				(long long)GetPlayerBotShellfishPermille(PLAYERBOT_SHELL_BLUE, PLAYERBOT_SHELLFISH_BLUE_PERMILLE) *
						GetPlayerBotVnumSaleValue(PLAYERBOT_PEARL_FIRST_VNUM + 1, dwNow) +
				(long long)GetPlayerBotShellfishPermille(PLAYERBOT_SHELL_RED, PLAYERBOT_SHELLFISH_RED_PERMILLE) *
						GetPlayerBotVnumSaleValue(PLAYERBOT_PEARL_LAST_VNUM, dwNow);
		const long long whole = GetPlayerBotVnumSaleValue(PLAYERBOT_SHELLFISH_VNUM, dwNow) * 1000;
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		const BYTE personality = it != s_mapPlayerBotAIStates.end()
				? it->second.bPersonality : BOT_PERSONALITY_STEADY_ADVENTURER;
		const long long needed = personality == BOT_PERSONALITY_CAREFUL_COLLECTOR ? whole * 3 / 2
				: (personality == BOT_PERSONALITY_GEAR_SPECIALIST ? whole * 4 / 5 : whole);
		return expected >= needed;
	}

	// The campfire mob this bot lit, if it is still burning within reach.
	struct FPlayerBotFindCampfire
	{
		LPCHARACTER m_owner;
		LPCHARACTER m_found;
		int m_bestDistance;
		FPlayerBotFindCampfire(LPCHARACTER owner) : m_owner(owner), m_found(NULL), m_bestDistance(PLAYERBOT_BAKE_RANGE) {}
		void operator()(LPENTITY entity)
		{
			if (!entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER fire = static_cast<LPCHARACTER>(entity);
			if (fire->GetRaceNum() != PLAYERBOT_CAMPFIRE_MOB_VNUM)
				return;
			const int distance = DISTANCE_APPROX(fire->GetX() - m_owner->GetX(), fire->GetY() - m_owner->GetY());
			if (distance < m_bestDistance)
			{
				m_bestDistance = distance;
				m_found = fire;
			}
		}
	};

	int CountPlayerBotDeadFish(LPCHARACTER ch)
	{
		int count = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetType() == ITEM_FISH && item->GetSubType() == FISH_DEAD)
				count += item->GetCount();
		}
		return count;
	}

	// Light the fire at the end of a session with dead fish in the bag; the
	// engine does the rest once the fish are handed over. Returns whether a
	// fire was lit.
	bool LightPlayerBotCampfire(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || CountPlayerBotDeadFish(ch) == 0)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetVnum() != PLAYERBOT_CAMPFIRE_VNUM)
				continue;
			if (!ch->UseItem(TItemPos(INVENTORY, cell)))
				return false;
			state.dwBakeUntil = dwNow + PLAYERBOT_BAKE_WINDOW;
			sys_log(0, "PLAYERBOT_FISHING: campfire lit pid=%u name=%s dead_fish=%d",
					ch->GetPlayerID(), ch->GetName(), CountPlayerBotDeadFish(ch));
			return true;
		}
		return false;
	}

	// Hand the dead fish to the fire, one pass a tick, while it burns. Owns
	// the tick so the bot stands by its fire instead of walking off.
	bool BakePlayerBotFish(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || state.dwBakeUntil == 0)
			return false;
		if (dwNow >= state.dwBakeUntil || !ch->GetSectree())
		{
			state.dwBakeUntil = 0;
			return false;
		}
		FPlayerBotFindCampfire finder(ch);
		ch->GetSectree()->ForEachAround(finder);
		if (!finder.m_found)
			return true; // lit a moment ago, not in the sectree yet
		int baked = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetType() != ITEM_FISH || item->GetSubType() != FISH_DEAD)
				continue;
			const int count = item->GetCount();
			if (ch->GiveItem(finder.m_found, TItemPos(INVENTORY, cell)))
				baked += count;
		}
		if (CountPlayerBotDeadFish(ch) == 0)
		{
			sys_log(0, "PLAYERBOT_FISHING: baked pid=%u name=%s fish=%d", ch->GetPlayerID(), ch->GetName(), baked);
			state.dwBakeUntil = 0;
			return false;
		}
		return true;
	}

	bool ProcessPlayerBotCatch(LPCHARACTER ch)
	{
		if (!ch)
			return false;

		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item)
				continue;

			const DWORD vnum = item->GetVnum();
			const bool aliveFish = item->GetType() == ITEM_FISH &&
					item->GetSubType() == FISH_ALIVE;
			if (!aliveFish && vnum != PLAYERBOT_SHELLFISH_VNUM)
				continue;
			// A shellfish is two things: a shot at a pearl, and a refine material
			// in its own right - twenty-six recipes on this proto consume one as
			// it is. Prying open the one the bot's own anvil is about to ask for
			// trades a certain material for a chance at a different one.
			// A shell is worth something whole, so the first few are never
			// gambled with: they go to the anvil or onto the counter, and only
			// the surplus is pried open.
			if (vnum == PLAYERBOT_SHELLFISH_VNUM &&
					(ch->CountSpecifyItem(PLAYERBOT_SHELLFISH_VNUM) <= PLAYERBOT_SHELLFISH_KEEP ||
					 PlayerBotNeedsRefineMaterial(ch, vnum) ||
					 !ShouldPlayerBotOpenShellfish(ch, get_dword_time())))
				continue;
			const int stoneBefore = ch->CountSpecifyItem(PLAYERBOT_STONE_PIECE_VNUM);
			const int whiteBefore = ch->CountSpecifyItem(PLAYERBOT_PEARL_FIRST_VNUM);
			const int blueBefore = ch->CountSpecifyItem(PLAYERBOT_PEARL_FIRST_VNUM + 1);
			const int redBefore = ch->CountSpecifyItem(PLAYERBOT_PEARL_LAST_VNUM);
			if (!ch->UseItem(TItemPos(INVENTORY, cell)))
				continue;
			if (!aliveFish)
			{
				// What the shell held, counted whatever it was - the empty ones
				// are what keeps the population's estimate honest.
				int outcome = PLAYERBOT_SHELL_NOTHING;
				if (ch->CountSpecifyItem(PLAYERBOT_PEARL_LAST_VNUM) > redBefore)
					outcome = PLAYERBOT_SHELL_RED;
				else if (ch->CountSpecifyItem(PLAYERBOT_PEARL_FIRST_VNUM + 1) > blueBefore)
					outcome = PLAYERBOT_SHELL_BLUE;
				else if (ch->CountSpecifyItem(PLAYERBOT_PEARL_FIRST_VNUM) > whiteBefore)
					outcome = PLAYERBOT_SHELL_WHITE;
				else if (ch->CountSpecifyItem(PLAYERBOT_STONE_PIECE_VNUM) > stoneBefore)
					outcome = PLAYERBOT_SHELL_STONE;
				RememberPlayerBotShellfishOutcome(outcome);
			}

			sys_log(0, "PLAYERBOT_FISHING: processed catch pid=%u name=%s vnum=%u kind=%s",
					ch->GetPlayerID(), ch->GetName(), vnum,
					aliveFish ? "fish" : "shellfish");
			return true;
		}
		return false;
	}

	// One bot, one colour, for good.
	//
	// The dye is fished up and dropped often enough that bots were carrying it
	// about as scrap. The engine takes it straight from UseItem - SetPart on
	// PART_HAIR, no client involved - and the colour is permanent, which is
	// exactly why it is worth using: eight hundred characters that all look
	// alike stop looking like one character copied eight hundred times. Used
	// once and once only; everything after the first is goods, and the engine
	// would refuse a second one for three levels anyway.
	bool ManagePlayerBotHairDye(LPCHARACTER ch)
	{
		if (!ch || ch->GetPart(PART_HAIR) != 0)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item)
				continue;
			const DWORD vnum = item->GetVnum();
			// Only the range char_item.cpp answers for, and not the remover:
			// washing out a colour that was never applied consumes the item and
			// changes nothing.
			if (vnum <= PLAYERBOT_HAIR_DYE_FIRST_VNUM ||
					vnum > PLAYERBOT_HAIR_DYE_LAST_VNUM)
				continue;
			if (!ch->UseItem(TItemPos(INVENTORY, cell)))
				continue;
			sys_log(0, "PLAYERBOT_LOOK: hair dyed pid=%u name=%s vnum=%u part=%d",
					ch->GetPlayerID(), ch->GetName(), vnum, ch->GetPart(PART_HAIR));
			return true;
		}
		return false;
	}

	bool EndPlayerBotFishingSession(LPCHARACTER ch, TPlayerBotAIState& state,
			DWORD dwNow, const char* reason)
	{
		if (ch && ch->m_pkFishingEvent)
			ch->fishing_take();

		if (ch)
			ReleasePlayerBotFishingStand(ch->GetPlayerID());
		state.bFishingSession = false;
		state.bIsFishing = false;
		state.dwFishingCastTime = 0;
		state.dwFishingIdleSince = 0;
		state.dwFishingSessionEndTime = 0;
		state.dwNextFishingActionTime = 0;
		state.dwNextFishingCheckTime = dwNow +
				number(PLAYERBOT_FISHING_REST_MIN, PLAYERBOT_FISHING_REST_MAX);
		StowPlayerBotRod(ch);
		ClearPlayerBotRoute(state, true);
		// An angler that has just packed the rod away is the one bot reliably
		// standing in Joan with nothing left to do. Half of them wander over to
		// the market ring for a while instead of walking straight back out -
		// which is the whole of what makes that square look inhabited, since the
		// bank, the bait merchant and the stalls are all on this one map.
		if (RollPlayerBotTownRest(ch))
			state.dwTownLingerUntil = dwNow + number(
					(int)PLAYERBOT_TOWN_LINGER_MIN, (int)PLAYERBOT_TOWN_LINGER_MAX);
		if (ch)
			sys_log(0, "PLAYERBOT_FISHING: session over pid=%u name=%s pearls=%d/%d/%d reason=%s",
					ch->GetPlayerID(), ch->GetName(),
					ch->CountSpecifyItem(PLAYERBOT_PEARL_FIRST_VNUM),
					ch->CountSpecifyItem(PLAYERBOT_PEARL_FIRST_VNUM + 1),
					ch->CountSpecifyItem(PLAYERBOT_PEARL_LAST_VNUM),
					reason ? reason : "?");
		return false;
	}

	// Rod and bait both come from the Rybak, who stands on the bank the bots fish
	// from, so restocking and fishing share one walk.
	// Buying one thing from the Rybak, and saying out loud when it will not
	// happen. Three quite different failures used to leave by the same door and
	// arrive as "cannot_afford_tackle": an item this world does not price, a bot
	// that genuinely has no money, and a bot whose bag has no free cell. The
	// first is a serverfile question, the second fixes itself, the third is a
	// bag the merchant pass should have emptied - and no log told them apart.
	bool BuyPlayerBotTackleItem(LPCHARACTER ch, DWORD vnum, int count,
			const char* what, DWORD dwNow)
	{
		TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto)
		{
			PlayerBotLogThrottled("tackle_no_proto", dwNow,
					"PLAYERBOT_FISHING: %s has no item table pid=%u name=%s vnum=%u",
					what, ch->GetPlayerID(), ch->GetName(), vnum);
			return false;
		}
		long long price = GetPlayerBotNpcPurchasePrice(proto, count);
		if (price <= 0)
		{
			PlayerBotLogThrottled("tackle_no_price", dwNow,
					"PLAYERBOT_FISHING: %s has no price on this world pid=%u name=%s vnum=%u count=%d",
					what, ch->GetPlayerID(), ch->GetName(), vnum, count);
			return false;
		}
		if (ch->GetGold() < price)
			RaisePlayerBotEmergencyGold(ch, price, what);
		// Buy what the purse reaches rather than nothing at all. A bundle is
		// twenty worms for eight hundred yang and the bot was refusing the whole
		// purchase over the last few: caught on our own world with 556 yang in
		// hand, which is thirteen worms and a session's fishing, standing at the
		// Rybak buying none of them. Only for a stack - a rod is one item and
		// either affordable or not.
		if (ch->GetGold() < price && count > 1)
		{
			const long long unit = GetPlayerBotNpcPurchasePrice(proto, 1);
			const long long spendable = (long long)ch->GetGold() *
					PLAYERBOT_FISHING_TACKLE_SPEND_PERCENT / 100;
			const int affordable = unit > 0
					? (int)std::min<long long>(count, spendable / unit) : 0;
			if (affordable > 0)
			{
				count = affordable;
				price = GetPlayerBotNpcPurchasePrice(proto, count);
				PlayerBotLogThrottled("tackle_part_buy", dwNow,
						"PLAYERBOT_FISHING: buying what it can afford of %s pid=%u name=%s vnum=%u count=%d price=%lld gold=%d",
						what, ch->GetPlayerID(), ch->GetName(), vnum, count,
						price, ch->GetGold());
			}
		}
		if (price <= 0 || ch->GetGold() < price)
		{
			PlayerBotLogThrottled("tackle_no_gold", dwNow,
					"PLAYERBOT_FISHING: cannot afford %s pid=%u name=%s vnum=%u count=%d price=%lld gold=%d",
					what, ch->GetPlayerID(), ch->GetName(), vnum, count,
					price, ch->GetGold());
			return false;
		}
		// The bag has to have room BEFORE the purchase, because AutoGiveItem
		// does not refuse a full bag: char_item.cpp puts the item on the ground
		// at the character's feet (AddToGround + StartDestroyEvent) and hands
		// it back as a success. So the old "if (!AutoGiveItem)" below never
		// fired, the bot paid, the rod lay on the grass, the bot still had no
		// rod and bought another on the next pass - which is the photograph
		// from the Discord: a herd of summoned horses round the Rybak standing
		// in a carpet of "Wedka+1". The arrow purchase learned this first
		// (playerbot_gear.h) and says so in the same words; the tackle purchase
		// was written a day later without it. A stackable that already has a
		// stack merges into it and needs no cell - that is the bait case.
		const bool bMergesIntoStack = count > 1 && ch->CountSpecifyItem(vnum) > 0;
		if (!bMergesIntoStack && ch->GetEmptyInventory(1) < 0)
		{
			PlayerBotLogThrottled("tackle_no_room", dwNow,
					"PLAYERBOT_FISHING: no bag room for %s pid=%u name=%s vnum=%u count=%d gold=%d",
					what, ch->GetPlayerID(), ch->GetName(), vnum, count, ch->GetGold());
			return false;
		}
		if (!ch->AutoGiveItem(vnum, count, -1, false))
			return false;
		PlayerBotChangeGold(ch, -price);
		sys_log(0, "PLAYERBOT_FISHING: bought %s pid=%u name=%s vnum=%u count=%d price=%lld",
				what, ch->GetPlayerID(), ch->GetName(), vnum, count, price);
		return true;
	}

	bool RestockPlayerBotTackle(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return false;

		// "Nothing needed buying" and "buying failed" are not the same answer,
		// and returning the same false for both ended the session of every bot
		// that was already carrying what it came for.
		bool refused = false;
		if (!IsPlayerBotHoldingRod(ch) && CountPlayerBotRods(ch) <= 0)
		{
			if (!BuyPlayerBotTackleItem(ch, PLAYERBOT_FISHING_ROD_VNUM, 1, "fishing_rod", dwNow))
				refused = true;
		}

		if (!refused &&
				ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM) < PLAYERBOT_FISHING_BAIT_RESTOCK)
		{
			if (!BuyPlayerBotTackleItem(ch, PLAYERBOT_FISHING_BAIT_VNUM,
					PLAYERBOT_FISHING_BAIT_BUNDLE, "fishing_bait", dwNow))
				refused = true;
		}
		// And one piece of Dried Wood for the end of the session, from the same
		// counter: the dead fish get grilled instead of vendored. The wood costs
		// twenty thousand and one fire takes any number of fish, so it is bought
		// for a batch, not for the three fish of a short session.
		if (ch->CountSpecifyItem(PLAYERBOT_CAMPFIRE_VNUM) <= 0 &&
				CountPlayerBotDeadFish(ch) >= PLAYERBOT_BAKE_MIN_FISH)
		{
			TItemTable* proto = ITEM_MANAGER::instance().GetTable(PLAYERBOT_CAMPFIRE_VNUM);
			if (proto)
			{
				const long long price = GetPlayerBotNpcPurchasePrice(proto, 1);
				// Same trap as the rod: no cell means the wood lands on the grass.
				if (price > 0 && ch->GetGold() >= price &&
						ch->GetEmptyInventory(1) >= 0 &&
						ch->AutoGiveItem(PLAYERBOT_CAMPFIRE_VNUM, 1, -1, false))
				{
					PlayerBotChangeGold(ch, -price);
					sys_log(0, "PLAYERBOT_FISHING: bought campfire pid=%u name=%s price=%lld",
							ch->GetPlayerID(), ch->GetName(), price);
				}
			}
		}
		// The wood is a nicety and never a reason to end a session, so it does
		// not speak here. What matters is whether the two things the bot cannot
		// fish without were refused.
		return !refused;
	}

	bool ManagePlayerBotFishing(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (state.dwBakeUntil != 0 && BakePlayerBotFish(ch, state, dwNow))
			return true;
		if (!ch || ch->IsDead())
			return false;
		const TPlayerBotFishingBank* bank = GetPlayerBotFishingBank(ch->GetMapIndex());
		if (bank == NULL)
		{
			// The rod must not travel to a hunting map in the weapon slot.
			if (state.bFishingSession)
				EndPlayerBotFishingSession(ch, state, dwNow, "left_m1");
			return false;
		}
		if (state.bVisitingShop || state.bVisitingBiologist || state.bVisitingStable ||
				state.bRecoveringAfterDeath || state.bTacticalRetreat ||
				state.bMultiPullActive)
		{
			if (state.bFishingSession)
				EndPlayerBotFishingSession(ch, state, dwNow, "town_errand");
			return false;
		}

		if (!state.bFishingSession)
		{
			if (dwNow < state.dwNextFishingCheckTime || !IsPlayerBotAngler(ch, state))
				return false;
			// Never walk off mid-fight; finish the pack first.
			LPCHARACTER victim = state.dwTargetVID != 0
					? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
			if (victim && !victim->IsDead())
				return false;

			state.bFishingSession = true;
			state.bIsFishing = false;
			state.dwFishingCastTime = 0;
			state.dwNextFishingActionTime = 0;
			state.dwNextFishingProgressLogTime = 0;
			state.dwFishingSessionEndTime = dwNow +
					number(PLAYERBOT_FISHING_SESSION_MIN, PLAYERBOT_FISHING_SESSION_MAX);
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_FISHING: heading for the bank pid=%u name=%s level=%u personality=%u",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
					(unsigned int)state.bPersonality);
		}

		// A session only ends between casts, so a fish already on the hook is
		// still landed.
		if (dwNow >= state.dwFishingSessionEndTime && !state.bIsFishing)
		{
			LightPlayerBotCampfire(ch, state, dwNow);
			return EndPlayerBotFishingSession(ch, state, dwNow, "session_finished");
		}

		SetPlayerBotGoal(ch, state, BOT_GOAL_FISHING, dwNow);
		SetPlayerBotAction(state, BOT_ACTION_FISHING, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		// Rod first, then worms: both come from the Rybak, who stands a short walk
		// upstream of the bank. Running out of bait sends the bot back to him.
		const bool needsTackle =
				(!IsPlayerBotHoldingRod(ch) && CountPlayerBotRods(ch) <= 0) ||
				ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM) <
					PLAYERBOT_FISHING_BAIT_RESTOCK;

		long destX = 0, destY = 0;
		if (needsTackle)
		{
			GetPlayerBotNpcApproach(ch->GetPlayerID(), bank->fisherman.x,
					bank->fisherman.y, 0x46495348U, destX, destY);
		}
		else
		{
			GetPlayerBotFishingStand(ch->GetPlayerID(), dwNow, ch->GetMapIndex(),
					destX, destY);
			// A last check against the navigation's own grid, in case a stand
			// falls in a cell it refuses - but within two cells, not twelve.
			// Twelve is six hundred world units against an arrival radius of
			// twenty-five, which is the same mistake the portal walk made: two
			// stands a hundred and fifty apart could both be dragged onto one
			// cell, and two anglers were found eight units apart because of it.
			CPlayerBotNavigation& navigation =
					CPlayerBotNavigation::instance(ch->GetMapIndex());
			PIXEL_POSITION bank;
			if (navigation.Init(ch->GetMapIndex()) &&
					navigation.FindNearestWalkableWorld(destX, destY, 2, bank,
							ch->GetPlayerID()))
			{
				destX = bank.x;
				destY = bank.y;
			}
		}

		// bFishingSession exempts a bot from the inactivity watchdog - standing
		// still at the bank is the activity - which also means a session that goes
		// wrong is completely silent. One throttled line says where it actually is.
		if (dwNow >= state.dwNextFishingProgressLogTime)
		{
			state.dwNextFishingProgressLogTime = dwNow + PLAYERBOT_FISHING_PROGRESS_LOG;
			sys_log(0, "PLAYERBOT_FISHING: progress pid=%u name=%s pos=(%ld,%ld) dest=(%ld,%ld) dist=%ld tackle=%d rod=%d bait=%d casting=%d stuck=%u riding=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetX(), ch->GetY(),
					destX, destY,
					(long)DISTANCE_APPROX(ch->GetX() - destX, ch->GetY() - destY),
					needsTackle ? 1 : 0, IsPlayerBotHoldingRod(ch) ? 1 : 0,
					ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM),
					state.bIsFishing ? 1 : 0, (unsigned int)state.bStuckCounter,
					ch->IsRiding() ? 1 : 0);
		}

		// A session that never reaches the water is the worst of both worlds: the
		// bot has paid for tackle, stopped hunting, and walks the same failing
		// approach for as long as the server runs. Observed on a live world - a
		// level-34 bot stood at the Rybak with a rod in its bag and never cast.
		// Give up out loud instead, so the log says which leg failed.
		if (state.dwFishingSessionEndTime != 0 && !state.bIsFishing &&
				dwNow >= state.dwFishingSessionEndTime)
		{
			sys_err("PLAYERBOT_FISHING: never reached the water pid=%u name=%s pos=(%ld,%ld) dest=(%ld,%ld) tackle=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetX(), ch->GetY(),
					destX, destY, needsTackle ? 1 : 0);
			return EndPlayerBotFishingSession(ch, state, dwNow, "never_reached_water");
		}

		if (DISTANCE_APPROX(ch->GetX() - destX, ch->GetY() - destY) >
				PLAYERBOT_FISHING_ARRIVE)
		{
			// Riding there is fine; the line simply cannot go in from a saddle.
			if (MovePlayerBot(ch, destX, destY, dwNow, 16, true, true) ||
					state.bStuckCounter < PLAYERBOT_FISHING_STUCK_LIMIT)
				return true;

			// Out of route. The tackle leg cannot be skipped - only the Rybak sells
			// rods - but the bank can be: fishing() in r40250 asks for a
			// non-blocking tile, a rod of type ITEM_ROD and bait in socket 2, and
			// never looks for water at all (it computes a facing offset and then
			// discards it). Casting where the bot already stands is therefore a
			// real cast, and it beats spending the entire session walking at a
			// bank the navigation cannot reach.
			if (needsTackle ||
					IsPlayerBotPositionBlocked(ch->GetMapIndex(), ch->GetX(), ch->GetY()))
			{
				sys_err("PLAYERBOT_FISHING: route failed pid=%u name=%s from=(%ld,%ld) to=(%ld,%ld) tackle=%d",
						ch->GetPlayerID(), ch->GetName(), ch->GetX(), ch->GetY(),
						destX, destY, needsTackle ? 1 : 0);
				return EndPlayerBotFishingSession(ch, state, dwNow, "route_failed");
			}

			sys_log(0, "PLAYERBOT_FISHING: bank unreachable, casting in place pid=%u name=%s pos=(%ld,%ld) bank=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), ch->GetX(), ch->GetY(),
					destX, destY);
			state.bStuckCounter = 0;
			ClearPlayerBotRoute(state, true);
		}

		if (SetPlayerBotRidingForTravel(ch, state, false, dwNow, "fishing"))
			// StopRiding leaves the horse standing behind the angler for the
			// whole session ("wszystkie moje boty lowia z konmi obok"); it is
			// sent away like a player would, and summoned again for the ride.
			ch->HorseSummon(false);
		if (ch->IsStateMove())
			ch->Stop();
		ch->SetPosition(POS_STANDING);

		if (needsTackle)
		{
			if (!RestockPlayerBotTackle(ch, state, dwNow))
				return EndPlayerBotFishingSession(ch, state, dwNow, "cannot_afford_tackle");
			return true;
		}
		if (!EquipPlayerBotRod(ch))
			return EndPlayerBotFishingSession(ch, state, dwNow, "rod_not_equippable");

		if (dwNow < state.dwNextFishingActionTime)
			return true;

		// Ready to fish and not fishing. If that goes on long enough the session
		// is over: a rod that will not go on, a bait that will not seat, or
		// anything else nobody has thought of yet, all end the same way instead
		// of standing at the water for hours.
		if (state.bIsFishing)
			state.dwFishingIdleSince = 0;
		else
		{
			if (state.dwFishingIdleSince == 0)
				state.dwFishingIdleSince = dwNow;
			else if (dwNow - state.dwFishingIdleSince >= PLAYERBOT_FISHING_NO_CAST_GIVE_UP)
			{
				sys_log(0, "PLAYERBOT_FISHING: no cast pid=%u name=%s rod=%d bait=%d idle_ms=%u",
						ch->GetPlayerID(), ch->GetName(),
						IsPlayerBotHoldingRod(ch) ? 1 : 0,
						ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM),
						(unsigned int)(dwNow - state.dwFishingIdleSince));
				return EndPlayerBotFishingSession(ch, state, dwNow, "never_cast");
			}
		}

		LPITEM rod = ch->GetWear(WEAR_WEAPON);
		if (!state.bIsFishing && rod && rod->GetSocket(2) == 0 && !BaitPlayerBotRod(ch))
		{
			// The pouch ran dry between passes; the walk back to the Rybak is
			// picked up by the tackle check at the top of the next pass.
			state.dwNextFishingActionTime = dwNow + number(1000, 2000);
			return true;
		}

#if defined(PLAYERBOT_ENGINE_MT2009)
		// mt2009 fishing is a reaction test and then a minigame, both driven
		// from the client. The pre-event bites 17 s after the cast: the engine
		// stamps m_bPlayerFishReactTime and the take has to come 1.7-3.5 s later
		// (fishing::Take), or four seconds after the bite the cast is failed. A
		// take in the window rolls the rod's chance; on a hit the minigame
		// starts: a bar climbing 0..100 at 5-9 per half second, a fish sinking 2
		// per half second and rising 8 per take, and the fish has to stay inside
		// the bar until the bar's top reaches 100. The catch itself comes from
		// the fishing quest, so it is read off the bag exactly as before.
		const bool bPreCast = ch->m_pkPreFishingEvent != NULL;
		const bool bCastLive = bPreCast || ch->IsPlayingFishGame();
#else
		// The engine holds the whole cast in one event: step 0 is the line in the
		// water, step 1 means a fish is on and starts the 6 s window to pull.
		fishing::fishing_event_info* info = ch->m_pkFishingEvent
				? dynamic_cast<fishing::fishing_event_info*>(ch->m_pkFishingEvent->info)
				: NULL;
		const bool bCastLive = info != NULL;
#endif

		if (!state.bIsFishing || !bCastLive)
		{
			if (bCastLive)
			{
				// A cast survived from an earlier pass; adopt it rather than
				// stacking a second one.
				state.bIsFishing = true;
				state.dwFishingCastTime = dwNow;
				return true;
			}
			if (state.bIsFishing)
			{
				// The event ended on its own -- the bite window elapsed. The engine
				// already cleared the bait, so the next pass re-baits and recasts.
				state.bIsFishing = false;
				state.dwNextFishingActionTime = dwNow + number(2000, 4000);
				ProcessPlayerBotCatch(ch);
				return true;
			}

			// A catch goes through AutoGiveItem, and AutoGiveItem never refuses a
			// full bag: it puts the fish on the grass and reports success. That is
			// what "the anglers drop their catch and every bot runs for it" was
			// (bierzyn, 10 September, with the photograph). A session with no
			// cell left ends here; the planner sends the bot to empty the bag.
			if (ch->GetEmptyInventory(1) < 0)
				return EndPlayerBotFishingSession(ch, state, dwNow, "bag_full");

			// CHARACTER::fishing() dereferences the sectree map and the tile under
			// the bot without checking either, so never call it blind.
			if (!ch->GetSectree() ||
					!SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex()))
			{
				state.dwNextFishingActionTime = dwNow + number(4000, 8000);
				return true;
			}

			// Face straight across at the river rather than along the bank: the
			// water lies due east of this stretch.
			long waterX = 0, waterY = 0;
			GetPlayerBotFishingFacing(ch->GetPlayerID(), ch->GetMapIndex(),
					waterX, waterY);
			ch->SetRotationToXY(waterX, waterY != 0 ? waterY : ch->GetY());
#if defined(PLAYERBOT_ENGINE_MT2009)
			// The onboarding quest's flag is what fishing() checks; a bot never
			// talks to the fisherman, so it is set here once.
			if (ch->GetQuestFlag("fishing_onboarding.completed") < 1)
				ch->SetQuestFlag("fishing_onboarding.completed", 1);
			ch->fishing();
			if (!ch->m_pkPreFishingEvent)
#else
			ch->fishing();
			if (!ch->m_pkFishingEvent)
#endif
			{
				// Blocked tile or missing bait; step away and try again shortly.
				state.dwNextFishingActionTime = dwNow + number(4000, 8000);
				return true;
			}
			state.bIsFishing = true;
			state.dwFishingCastTime = dwNow;
			return true;
		}

#if defined(PLAYERBOT_ENGINE_MT2009)
		if (bPreCast)
		{
			const DWORD react = ch->m_bPlayerFishReactTime;
			if (react >= state.dwFishingCastTime && react <= dwNow &&
					dwNow - react >= PLAYERBOT_MT2009_FISHING_REACT_MIN &&
					dwNow - react <= PLAYERBOT_MT2009_FISHING_REACT_MAX)
			{
				ch->fishing_take();
				state.dwLastMeaningfulActivityTime = dwNow;
				return true;
			}
			if (dwNow - state.dwFishingCastTime > PLAYERBOT_FISHING_CAST_TIMEOUT)
			{
				// A take outside the window cancels both events.
				ch->fishing_take();
				state.bIsFishing = false;
				state.dwNextFishingActionTime = dwNow + number(2000, 4000);
				sys_log(0, "PLAYERBOT_FISHING: cast timed out pid=%u name=%s",
						ch->GetPlayerID(), ch->GetName());
			}
			return true;
		}

		// The minigame. This pass runs every quarter second and the bar moves at
		// most 13 per half second, so a fish put just under the top of the bar
		// on each pass is still inside it on the next.
		fishing::fishing_event_info* game = ch->m_pkFishingEvent
				? dynamic_cast<fishing::fishing_event_info*>(ch->m_pkFishingEvent->info)
				: NULL;
		if (game && ch->m_biFishGameState >= PLAYERBOT_MT2009_FISHING_GAME_IN_PROGRESS)
		{
			const int top = (int)game->bar_position + (int)game->bar_height;
			for (int presses = 0; presses < 16 && ch->m_iFish_position + 8 <= top + 2; ++presses)
				fishing::Take(game, ch);
		}
		state.dwLastMeaningfulActivityTime = dwNow;
		return true;
#else
		if (info->step < 1)
		{
			// Still waiting for a bite. The engine takes 10-40 s; anything past a
			// minute means the event is wedged.
			if (dwNow - state.dwFishingCastTime > PLAYERBOT_FISHING_CAST_TIMEOUT)
			{
				ch->fishing_take();
				state.bIsFishing = false;
				state.dwNextFishingActionTime = dwNow + number(2000, 4000);
				sys_log(0, "PLAYERBOT_FISHING: cast timed out pid=%u name=%s",
						ch->GetPlayerID(), ch->GetName());
			}
			return true;
		}

		// A fish is on. fishing::Compute() peaks around 3 s after the bite, so wait
		// out that band before pulling instead of yanking the rod instantly.
		const DWORD hooked = get_dword_time() - info->hang_time;
		const DWORD pullAt = PLAYERBOT_FISHING_PULL_MIN_DELAY +
				PlayerBotNavHash(ch->GetPlayerID() ^ info->hang_time) %
				(PLAYERBOT_FISHING_PULL_MAX_DELAY - PLAYERBOT_FISHING_PULL_MIN_DELAY + 1U);
		if (hooked < pullAt)
			return true;

		ch->fishing_take();
		state.bIsFishing = false;
		state.dwNextFishingActionTime = dwNow + number(2000, 4000);
		state.dwLastMeaningfulActivityTime = dwNow;
		ProcessPlayerBotCatch(ch);
		sys_log(0, "PLAYERBOT_FISHING: pulled pid=%u name=%s hooked_ms=%u fish=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)hooked, info->fish_id);
		return true;
#endif
	}
}

#endif
