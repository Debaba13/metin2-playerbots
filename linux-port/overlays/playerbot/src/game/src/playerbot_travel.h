#ifndef __INC_METIN2_PLAYERBOT_TRAVEL_H__
#define __INC_METIN2_PLAYERBOT_TRAVEL_H__

// Where a bot ought to be, and how it gets there across maps.
//
// Two things live here that look separate and are not. The first is what a bot
// still needs - potions, a weapon, a repair - because that is what decides
// whether it may leave for a hunting ground at all. The second is the crossing
// itself: which frontier suits its level, when a trip is worth making, and the
// difference between a warp and a walk to a portal.
//
// A server-side bot has no client to reconnect, so it cannot cross between game
// cores. Every route planned here has to stay on the cores that host its maps.
//
// An implementation fragment in the sense playerbot_types.h describes: it
// defines objects, relies on the engine headers playerbot_manager.cpp includes
// above it, and reopens the same anonymous namespace. Include it exactly once,
// after playerbot_movement.h - it decides the destination, that file walks to
// it - and after playerbot_economy.h, whose refine opportunities it consults.

namespace
{
	void CountPlayerBotPotions(LPCHARACTER ch, size_t& redCount, size_t& blueCount)
	{
		redCount = 0;
		blueCount = 0;
		if (!ch || !ch->IsItemLoaded())
			return;

		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item)
				continue;
			const DWORD vnum = item->GetVnum();
			if (vnum == 27001 || vnum == 27002 || vnum == 27003 || vnum == 27051)
				redCount += item->GetCount();
			else if (vnum == 27004 || vnum == 27005 || vnum == 27006 || vnum == 27052)
				blueCount += item->GetCount();
		}
	}

	bool NeedsPlayerBotPotions(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		size_t redCount = 0, blueCount = 0;
		CountPlayerBotPotions(ch, redCount, blueCount);
		const bool isMage = ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA;
		if (ch->GetLevel() <= 10)
			return (redCount < 30 && ch->GetGold() >= 300) ||
					(isMage && blueCount < 20 && ch->GetGold() >= 400);
		// Only a belt that is nearly out is worth crossing a map for. A bot with
		// half its potions left has no business walking away from a good spot -
		// it will fill up anyway the next time something else brings it to town.
		return (redCount < 150 && ch->GetGold() >= 1200) ||
				(blueCount < 100 && ch->GetGold() >= 1200);
	}

	bool NeedsPlayerBotEmergencyPotions(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		size_t redCount = 0, blueCount = 0;
		CountPlayerBotPotions(ch, redCount, blueCount);
		const bool isMage = ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA;
		// Normal restocking happens at 50/30 (or 10) units. Cross-map travel is
		// justified only by a genuinely short combat reserve, not by one consumed pot.
		//
		// Blue potions restore SP, so an empty belt is an emergency for a caster
		// and nothing at all for a warrior. Treating "no blue potions" as critical
		// for everybody put 210 of 442 warriors and ninjas into a permanent fake
		// emergency: they were always considered one step from being unable to
		// fight, so they abandoned every trip the moment their items finished
		// loading and shuttled straight back to town.
		return redCount < 10 || (isMage && blueCount < 8);
	}

	bool NeedsPlayerBotCriticalTownServices(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		// These problems can make continued combat impossible or waste most future
		// drops, so they justify an immediate cross-map return.
		if (ch->GetWear(WEAR_WEAPON) == NULL || ch->GetWear(WEAR_BODY) == NULL ||
				ch->GetWear(WEAR_SHIELD) == NULL || ch->GetWear(WEAR_HEAD) == NULL ||
				ch->GetWear(WEAR_FOOTS) == NULL || NeedsPlayerBotEmergencyPotions(ch) ||
				NeedsPlayerBotArrows(ch) ||
				ch->GetEmptyInventory(3) < 0)
			return true;

		size_t occupiedGridCells = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item)
				occupiedGridCells += std::max(1, (int)item->GetSize());
		}
		return occupiedGridCells * 100 >= INVENTORY_MAX_NUM * 45;
	}

	// A missing weapon or body armour, an empty potion belt, no arrows or a full
	// inventory really do stop a bot from playing, and must outrank travelling.
	// A missing helmet, boots or shield only make it a little weaker. Treating
	// those as equally critical trapped a bot for good whenever the town could
	// not sell it the missing piece: it always wanted to shop, so it was never
	// allowed to travel, and it kept farming level-3 wolves in Joan at level 27.
	bool BlocksPlayerBotTravel(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		return ch->GetWear(WEAR_WEAPON) == NULL || ch->GetWear(WEAR_BODY) == NULL ||
				NeedsPlayerBotEmergencyPotions(ch) || NeedsPlayerBotArrows(ch) ||
				ch->GetEmptyInventory(3) < 0;
	}

	bool NeedsPlayerBotM1OnlyServices(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		// Bokjung has no profession trainers or Biologist. Everything else can be
		// handled locally in M2, so only these two real activities justify M2 -> M1.
		if (ch->GetLevel() >= 5 && ch->GetSkillGroup() == 0 &&
				ch->GetJob() <= JOB_SHAMAN)
			return true;

		size_t missionIndex = 0;
		const TPlayerBotBiologistMission* mission =
				GetActivePlayerBotBiologistMission(ch, &missionIndex);
		if (!mission)
			return false;
		int required = mission->requiredCount;
		const DWORD wantedVnum = GetPlayerBotBiologistWantedItem(ch, missionIndex, &required);
		const int accepted = IsPlayerBotBiologistKeyPhase(ch, missionIndex) ? 0 : std::max(0, ch->GetQuestFlag(
				GetPlayerBotBiologistFlag(*mission, "collect_count")));
		const int remaining = std::max(0, required - accepted);
		return remaining > 0 && ch->CountSpecifyItem(wantedVnum) >= remaining;
	}

	// Above this level Bokjung has nothing left to offer, so nothing there is
	// worth keeping a bot for either.
	const BYTE PLAYERBOT_M2_COHORT_MAX_LEVEL = 35;

	bool IsPlayerBotPastM2Ceiling(LPCHARACTER ch)
	{
		return ch && ch->GetLevel() > PLAYERBOT_M2_COHORT_MAX_LEVEL;
	}

	bool IsPlayerBotM2LevelingCohort(LPCHARACTER ch)
	{
		if (!ch || ch->GetLevel() < 20 ||
				ch->GetLevel() > PLAYERBOT_M2_COHORT_MAX_LEVEL)
			return false;
		// Levels 20-21 still have a little useful M1 progression, so retain a small
		// stable minority there. At level 22 every ordinary leveler graduates to M2.
		return ch->GetLevel() >= 22 ||
				(PlayerBotNavHash(ch->GetPlayerID() ^ 0x4d325850U) % 10U) != 0;
	}

	bool ShouldPlayerBotLeaveRemoteMapForRefining(LPCHARACTER ch,
			TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!HasPlayerBotPriorityRefineOpportunity(ch))
			return false;
		if (state.dwNextRemoteRefineReturnTime == 0)
		{
			const DWORD spread = PlayerBotNavHash(ch->GetPlayerID() ^
					(dwNow / 60000U) ^ 0x52455455U) %
					(PLAYERBOT_REMOTE_REFINE_RETURN_MAX_DELAY -
					 PLAYERBOT_REMOTE_REFINE_RETURN_MIN_DELAY + 1);
			state.dwNextRemoteRefineReturnTime = dwNow +
					PLAYERBOT_REMOTE_REFINE_RETURN_MIN_DELAY + spread;
			return false;
		}
		return dwNow >= state.dwNextRemoteRefineReturnTime;
	}

	// Defined with the market-stall code in playerbot_town.h, which needs the
	// town and therefore comes later. Declared rather than included, the way
	// playerbot_gear.h declares GetPlayerBotNpcApproach.
	void ClosePlayerBotShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow,
			const char* reason);

	bool IsPlayerBotFrontierMap(long mapIndex)
	{
		return IsPlayerBotFrontierMapIndex(mapIndex);
	}

	// The map whose ordinary spawns still sit inside this bot's useful level
	// window, or 0 when Bokjung is still the right place for it.
	long GetPlayerBotFrontierMapForLevel(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		// A bot working on its battle horse hunts where the trial is, whatever
		// its level would otherwise say. By level 36 it would be off to Orc
		// Valley, and the Black Wind band it needs lives in the desert.
		if (IsPlayerBotOnBattleHorseTrial(ch))
			return PLAYERBOT_MAP_DESERT;

		const BYTE level = ch->GetLevel();
		const DWORD draw = PlayerBotNavHash(ch->GetPlayerID() ^ 0x45534f54U);
		// Forty-eight and up: the Spider Dungeon for half, Mount Sohan for the
		// other half, decided once per character so the answer does not change
		// under a bot halfway there. The valley is for those still short of it.
		if (level >= PLAYERBOT_SPIDER_MIN_LEVEL && level >= PLAYERBOT_SOHAN_MIN_LEVEL)
			return (draw & 1U) != 0 ? PLAYERBOT_MAP_SPIDER_V1 : PLAYERBOT_MAP_SOHAN;
		if (level >= PLAYERBOT_ORC_VALLEY_MIN_LEVEL && level <= PLAYERBOT_ORC_VALLEY_MAX_LEVEL)
			return PLAYERBOT_MAP_ORC_VALLEY;
		// Thirty to thirty-five: the Fanatic islands and the desert share the
		// population. Below thirty Bokjung keeps everyone.
		if (level >= PLAYERBOT_ORC_VALLEY_ESOTERIC_MIN_LEVEL && level < PLAYERBOT_ORC_VALLEY_MIN_LEVEL)
			return (draw & 1U) != 0 ? PLAYERBOT_MAP_ORC_VALLEY : PLAYERBOT_MAP_DESERT;
		return 0;
	}

	// How far from town a personality is willing to play, in eighths. Personality
	// used to decide only how far a bot would push a refine, so every character
	// hunted in the same places; this is what makes the trait visible in-world.
	BYTE GetPlayerBotFrontierAppetite(BYTE personality)
	{
		switch (personality)
		{
			case BOT_PERSONALITY_WANDERER:
				return 7; // explorer: almost always out on the far maps
			case BOT_PERSONALITY_METIN_BREAKER:
				return 6; // both frontier maps carry their own Metin spawns
			case BOT_PERSONALITY_GEAR_SPECIALIST:
				return 6; // Orc Valley is where the level-30 weapons drop
			case BOT_PERSONALITY_TEAM_COMPANION:
				return 4; // stays near the party pool at least half the time
			case BOT_PERSONALITY_CAREFUL_COLLECTOR:
				return 2; // protects what it has earned, keeps a town run short
			default:
				return 5; // steady adventurer
		}
	}

	// Due for a fishing trip: old enough for the rod, and its cooldown is up.
	bool WantsPlayerBotFishingTrip(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!IsPlayerBotAngler(ch, state))
			return false;
		return state.dwNextFishingCheckTime == 0 || dwNow >= state.dwNextFishingCheckTime;
	}

	bool ShouldPlayerBotLeaveForFrontier(LPCHARACTER ch)
	{
		if (!ch || GetPlayerBotFrontierMapForLevel(ch) == 0)
			return false;
		TPlayerBotAIStateMap::const_iterator it =
				s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		const BYTE personality = it != s_mapPlayerBotAIStates.end()
				? it->second.bPersonality : BOT_PERSONALITY_STEADY_ADVENTURER;
		// Above the Bokjung ceiling there is nothing there left to stay behind
		// for, so the reserve rule has nothing to protect and only strands bots.
		if (IsPlayerBotPastM2Ceiling(ch))
			return true;
		// Below it Bokjung must never empty out completely: even the keenest
		// explorer leaves one bot in eight behind for the town, its Bestials
		// and the local party pool.
		const DWORD appetite = GetPlayerBotFrontierAppetite(personality);
		return (PlayerBotNavHash(ch->GetPlayerID() ^ 0x46524f4eU) % 8U) < appetite;
	}

	// A wanderer settles in for a long session; a careful collector treats the
	// trip as an errand and heads back while it still has potions left.
	DWORD GetPlayerBotFrontierVisitTime(BYTE personality)
	{
		switch (personality)
		{
			case BOT_PERSONALITY_WANDERER:
				return PLAYERBOT_FRONTIER_MAX_VISIT_TIME * 2;
			case BOT_PERSONALITY_CAREFUL_COLLECTOR:
				return PLAYERBOT_FRONTIER_MAX_VISIT_TIME / 2;
			default:
				return PLAYERBOT_FRONTIER_MAX_VISIT_TIME;
		}
	}

	bool ShouldPlayerBotVisitM3(LPCHARACTER ch)
	{
		if (!ch || !HasPlayerBotM3ReadyEquipment(ch))
			return false;
		// The M3 dropper is there for the weapons it will sell, so owning one
		// changes nothing, and it stays as long as the map can still be hunted.
		if (GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_M3_DROPPER)
			return ch->GetLevel() <= 32;
		if (ch->GetLevel() > 24 || HasPlayerBotSpecialLevel30Weapon(ch, true))
			return false;
		// A stable third of the eligible population farms infected animals for
		// class-specific level-30 weapons. Other bots remain in M2 for Bestials.
		return (PlayerBotNavHash(ch->GetPlayerID() ^ 0x4d335850U) % 3U) == 0;
	}

	bool ShouldPlayerBotHuntM2Bestials(LPCHARACTER ch)
	{
		if (!ch || !HasPlayerBotM3ReadyEquipment(ch))
			return false;
		// The M2 dropper camps the two Bestials for the weapons it will sell,
		// owned weapon or not, for as long as they are worth its level.
		if (GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_M2_DROPPER)
			return ch->GetLevel() >= 25 && ch->GetLevel() <= 40;
		if (ch->GetLevel() < 25 || ch->GetLevel() > 35 ||
				HasPlayerBotSpecialLevel30Weapon(ch, true) ||
				ShouldPlayerBotVisitM3(ch))
			return false;
		// M3 already owns one third of the eligible weapon hunters. Half of the
		// remaining cohort searches the two rare Bestial spawns in M2, while the
		// rest keeps levelling normally instead of camping one pair of enemies.
		return (PlayerBotNavHash(ch->GetPlayerID() ^ 0x42455354U) % 2U) == 0;
	}

	bool ShouldPlayerBotPursueHorseExpedition(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return false;
		// The medal dropper goes for the medals themselves, whatever its own horse
		// needs, in whichever dungeon its level earns them.
		if (GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_MEDAL_DROPPER)
			return GetPlayerBotMonkeyMapForLevel(ch->GetLevel()) != 0;
		if (!CanPlayerBotAdvanceHorse(ch))
			return false;

		// There is a dungeon for every level from eighteen up - see
		// GetPlayerBotMonkeyMapForLevel for why the easy one alone gave a bot of
		// forty nothing - so the band no longer ends the errand: 439 bots past
		// forty stood on no horse at all, and 435 more on one below ten. This
		// gate also empties a dungeon: a bot inside re-evaluates the same call
		// every tick and walks out as soon as it is no longer chosen.
		if (GetPlayerBotMonkeyMapForLevel(ch->GetLevel()) == 0)
			return false;

		// A combat horse matters most to Warriors and weapon Suras, but it must be
		// one goal among several rather than a compulsory conveyor belt through the
		// dungeon.  The cohort rotates every 30 minutes and again after every earned
		// horse level.  Eventually every build gets opportunities while most bots
		// continue levelling in M2 at any given time.
		const bool hasCombatHorse = ch->GetHorseLevel() >= 11;
		BYTE chance = 10;
		switch (ch->GetJob())
		{
			case JOB_WARRIOR:
				chance = hasCombatHorse ? 4 : (ch->GetHorseLevel() == 0 ? 34 : 26);
				break;
			case JOB_SURA:
				// Skill group 1 is Weaponry (WP); group 2 is Black Magic.
				chance = ch->GetSkillGroup() == 1
						? (hasCombatHorse ? 4 : (ch->GetHorseLevel() == 0 ? 32 : 25))
						: (hasCombatHorse ? 2 : (ch->GetHorseLevel() == 0 ? 14 : 9));
				break;
			case JOB_ASSASSIN:
				chance = ch->GetSkillGroup() == 2
						? (hasCombatHorse ? 1 : (ch->GetHorseLevel() == 0 ? 6 : 4))
						: (hasCombatHorse ? 2 : (ch->GetHorseLevel() == 0 ? 18 : 14));
				break;
			case JOB_SHAMAN:
				chance = hasCombatHorse ? 2 : (ch->GetHorseLevel() == 0 ? 15 : 10);
				break;
		}
		TPlayerBotAIStateMap::const_iterator stateIt =
				s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (stateIt != s_mapPlayerBotAIStates.end() &&
				stateIt->second.bAmbition == BOT_AMBITION_HORSE && !hasCombatHorse)
			chance = std::min<BYTE>(55, chance + 15);

		const DWORD window = dwNow / (30U * 60U * 1000U);
		const DWORD seed = ch->GetPlayerID() ^ (window * 0x9e3779b9U) ^
				((DWORD)(ch->GetHorseLevel() + 1) * 0x85ebca6bU);
		// Through the weight, not past it. An operator who raises HORSE in the
		// panel is asking for exactly this - more bots in the dungeon - and until
		// now the slider moved the goal planner while the gate that actually
		// sends them ignored it, so nothing he did had any effect.
		return PlayerBotWeightedRoll(PlayerBotNavHash(seed ^ 0x484f5253U) % 100U,
				chance, PLAYERBOT_WEIGHT_HORSE);
	}

	int GetPlayerBotDesiredHorseMedalStock(LPCHARACTER ch)
	{
		if (!ch)
			return 1;
		// The high-priority builds occasionally prepare the next horse level in the
		// same visit. Other classes leave after one medal, freeing dungeon capacity
		// and returning to ordinary experience progression much sooner.
		const bool highPriority = ch->GetJob() == JOB_WARRIOR ||
				(ch->GetJob() == JOB_SURA && ch->GetSkillGroup() == 1);
		return highPriority
				? 1 + (PlayerBotNavHash(ch->GetPlayerID() ^ 0x4d454441U) % 2U)
				: 1;
	}

	// A warp that half worked, and the only kind of damage a bot cannot walk off.
	//
	// The frontier maps carry warp NPCs of their own and a bot that strays into
	// one's trigger radius is handed to whatever map it points at. When that map
	// belongs to the other core, the warp goes half way: the character's
	// coordinates are set to the destination and the placement into a sector
	// fails, so it stands in Orc Valley carrying a position in Milgyo. The
	// engine notices and says so - "SECTREE DIFFER: botsimon 56x111 was 56x112" -
	// and then the ordinary logout saves the coordinates it cannot use:
	//
	//     PlayerLoad: cannot find valid location 553600 x 144100 (name: botsimon)
	//
	// From then on the character is refused at every login. It is not stuck, or
	// idle, or lost - it is gone, and the only sign is that the world runs fewer
	// bots than it was asked for. Eighty-five had accumulated this way, 10% of
	// the population, all of them saved at one identical coordinate.
	//
	// The recovery branch at the end of ManagePlayerBotWorldTravel cannot help:
	// it reads GetMapIndex(), which still says Orc Valley, because the sector is
	// the half of the warp that failed. So the mismatch itself is what has to be
	// looked for, while the bot is still logged in and can still be moved.
	bool IsPlayerBotPositionOffItsMap(LPCHARACTER ch)
	{
		if (!ch || !ch->GetSectree())
			return false;
		const int byPosition = SECTREE_MANAGER::instance().GetMapIndex(
				ch->GetX(), ch->GetY());
		return byPosition > 0 && byPosition != (int)ch->GetMapIndex();
	}

	bool TransitionPlayerBotMap(LPCHARACTER ch, TPlayerBotAIState& state,
			long targetMap, long targetX, long targetY, DWORD dwNow, const char* reason)
	{
		if (!ch)
			return false;
		// V1 lies across the desert - see PLAYERBOT_DESERT_V1_GATE_X. A warp into
		// it from anywhere but the desert becomes a warp onto the desert with the
		// real destination remembered, and ManagePlayerBotWorldTravel walks the
		// bot to the gate; a warp out of it becomes the desert's far corner and
		// the walk back to the Bokjung gate. Both call back in here with the
		// desert as the target, which neither rule touches.
		if (targetMap == PLAYERBOT_MAP_SPIDER_V1 && ch->GetMapIndex() != PLAYERBOT_MAP_DESERT)
		{
			state.lDesertCrossingTo = targetMap;
			state.lDesertCrossingX = targetX;
			state.lDesertCrossingY = targetY;
			state.dwNextCrossingStoneCheck = 0;
			return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_DESERT,
					PLAYERBOT_DESERT_ARRIVAL_X, PLAYERBOT_DESERT_ARRIVAL_Y, dwNow, "desert_crossing_to_v1");
		}
		if (ch->GetMapIndex() == PLAYERBOT_MAP_SPIDER_V1 && targetMap != PLAYERBOT_MAP_DESERT)
		{
			state.lDesertCrossingTo = targetMap;
			state.lDesertCrossingX = targetX;
			state.lDesertCrossingY = targetY;
			state.dwNextCrossingStoneCheck = 0;
			return TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_DESERT,
					PLAYERBOT_DESERT_FROM_V1_X, PLAYERBOT_DESERT_FROM_V1_Y, dwNow, "desert_crossing_from_v1");
		}
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(targetMap);
		if (!navigation.Init(targetMap))
		{
			// Tagged by the reason, so a reason nobody has seen before still
			// speaks up inside the minute instead of hiding behind an old one.
			char szTag[64];
			snprintf(szTag, sizeof(szTag), "world_nav:%s", reason ? reason : "?");
			PlayerBotLogThrottled(szTag, dwNow,
					"PLAYERBOT_WORLD: target navigation unavailable pid=%u name=%s map=%ld reason=%s",
					ch->GetPlayerID(), ch->GetName(), targetMap, reason ? reason : "?");
			return false;
		}

		const long oldMap = ch->GetMapIndex();
		const bool wasRiding = ch->IsRiding();
		if (ch->GetParty())
			ch->GetParty()->Quit(ch->GetPlayerID());
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		// A PC mount and the separately summoned horse are two different server
		// entities. StopRiding() summons the latter on the old map, so explicitly
		// remove it before Show(). Otherwise a rider can leave behind an orphaned
		// horse at a dungeon portal (issue #4).
		if (wasRiding)
			ch->StopRiding();
		ch->HorseSummon(false);
		// And the stall, for the same reason and in the same place: the sign has
		// to be taken back on the map where it was put up. Closing it after the
		// warp broadcasts the clear to whoever happens to be standing in the
		// destination, while the people who actually saw it are still on the
		// market - which is how a bot ends up in the Monkey Dungeon wearing a
		// shop nobody can open.
		ClosePlayerBotShop(ch, state, dwNow, "map_transition");
		ClearPlayerBotRoute(state, true);
		state.bVisitingShop = false;
		state.bVisitingBiologist = false;
		state.bVisitingStable = false;
		if (!ch->Show(targetMap, targetX, targetY, 0))
		{
			if (wasRiding && !ch->IsRiding())
				ch->StartRiding();
			sys_err("PLAYERBOT_WORLD: transition failed pid=%u name=%s from=%ld to=%ld reason=%s",
					ch->GetPlayerID(), ch->GetName(), oldMap, targetMap, reason ? reason : "?");
			return false;
		}
		ch->Stop();
		ch->SendMovePacket(FUNC_MOVE, 0, targetX, targetY, 0, dwNow);
		if (wasRiding && ch->GetHorseHealth() > 0 && ch->GetHorseStamina() > 0)
			ch->StartRiding();
		ch->Save();
		state.dwNextWanderTime = dwNow + number(1500, 4500);
		state.dwNextHorseRideCheckTime = dwNow + 1000;
		state.dwDungeonEnteredTime = IsPlayerBotMonkeyMap(targetMap) ? dwNow : 0;
		state.dwM3EnteredTime = targetMap == PLAYERBOT_MAP_CHUNJO_M3 ? dwNow : 0;
		state.dwFrontierEnteredTime = IsPlayerBotFrontierMap(targetMap) ? dwNow : 0;
		// Landed anywhere but the desert: whatever crossing was under way is over.
		if (targetMap != PLAYERBOT_MAP_DESERT)
			state.lDesertCrossingTo = 0;
		// Everybody enters Orc Valley at the same point, so without this the
		// whole population lands on the doorstep and stays there - the rotation
		// that would move it on runs only on a tick with nothing to fight, and
		// that map has four thousand spawn points. Start the walk to this bot's
		// own hub on arrival instead of after the first camp timer expires.
		state.lCampX = targetX;
		state.lCampY = targetY;
		state.dwCampSince = dwNow;
		state.dwRelocateSince = IsPlayerBotFrontierMap(targetMap) ? dwNow : 0;
		if (targetMap == PLAYERBOT_MAP_CHUNJO_M3)
			state.dwNextRemoteRefineReturnTime = 0;
		sys_log(0, "PLAYERBOT_WORLD: transitioned pid=%u name=%s from=%ld to=%ld pos=(%ld,%ld) reason=%s",
				ch->GetPlayerID(), ch->GetName(), oldMap, targetMap, targetX, targetY,
				reason ? reason : "?");
		return true;
	}

	bool MovePlayerBotToWorldPortal(LPCHARACTER ch, TPlayerBotAIState& state,
			long portalX, long portalY, long targetMap, long targetX, long targetY,
			DWORD dwNow, const char* reason)
	{
		if (!ch)
			return false;
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		// Warp NPCs trigger at 300 units and hand the client to whichever core
		// hosts the target map, which is not a conversation a bot descriptor can
		// have - so the switch is made here, server-side, before the bot gets
		// that close. It used to happen at 900 units, nine metres short of the
		// portal, and a player watching one leave saw it vanish out of clear
		// ground. Patch 0008 makes warp_npc_event ignore bots outright, so the
		// margin only has to cover one tick of running now: the character walks
		// up to the portal and goes from there, the way a player does.
		const int distance = DISTANCE_APPROX(ch->GetX() - portalX, ch->GetY() - portalY);
		if (distance <= PLAYERBOT_PORTAL_SWITCH_DISTANCE)
		{
			state.dwPortalWalkSince = 0;
			state.iPortalWalkBest = 0;
			return TransitionPlayerBotMap(ch, state, targetMap, targetX, targetY, dwNow, reason);
		}

		// Walking to a portal has to be able to fail, and this is what it looked
		// like when it could not.
		//
		// The old body ignored what MovePlayerBot returned and ended in an
		// unconditional "return true", so a bot whose route could not be planned
		// reported a successful travel step - and travel claims the tick, so
		// nothing below it in the update ever ran again. Four of them were found
		// standing at the Bokjung teleporter: no route (route=0/0), no movement,
		// nothing in the log but their goal flipping between LEVEL_UP and BIOLOGIST
		// every six seconds as the planner and this branch overwrote each other.
		// The inactivity watchdog reset them 209 times in an evening and every
		// reset delivered them straight back into the same decision.
		//
		// Neither the map nor the route was at fault: 99.9% of Bokjung is one
		// walkable component and that portal is reachable from where they stood.
		// The navigation has several paths that stand still and report success - a
		// deferred plan when the per-tick planning budget is spent, and the
		// back-off window after a failure. Any of them, entered every tick, freezes
		// a bot for good once the caller treats them as progress.
		//
		// So progress is what is measured, not the return value. A bot that has not
		// moved for PLAYERBOT_PORTAL_WALK_TIMEOUT hands the tick back, and that is
		// all it takes: the update falls through to hunting and wandering, the bot
		// ends up somewhere else, and the next attempt plans from there.
		if (state.dwPortalWalkSince == 0 ||
				distance + PLAYERBOT_PORTAL_WALK_PROGRESS <= state.iPortalWalkBest ||
				distance >= state.iPortalWalkBest + PLAYERBOT_PORTAL_WALK_PROGRESS)
		{
			state.dwPortalWalkSince = dwNow;
			state.iPortalWalkBest = distance;
		}
		else if (dwNow - state.dwPortalWalkSince >= PLAYERBOT_PORTAL_WALK_TIMEOUT)
		{
			state.dwPortalWalkSince = 0;
			state.iPortalWalkBest = 0;
			PlayerBotLogThrottled("portal_stuck", dwNow,
					"PLAYERBOT_WORLD: portal walk stalled pid=%u name=%s map=%ld pos=(%ld,%ld) portal=(%ld,%ld) distance=%d reason=%s",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(),
					ch->GetX(), ch->GetY(), portalX, portalY, distance,
					reason ? reason : "?");
			return false;
		}

		// Mounted all the way up to it. A teleporter is scenery to a bot - the warp
		// happens server-side and nothing is said to anybody - so the dismount
		// MovePlayerBot performs on arrival at an ordinary destination buys nothing
		// here. It was 1362 of one evening's dismounts, each followed by a remount
		// on the far side three seconds later.
		MovePlayerBot(ch, portalX, portalY, dwNow, 24, true, true, false, true);
		return true;
	}

	// Being in a fight is not the same as having something selected. A bot is in
	// the fight when blows are being exchanged, when the monster is coming for
	// it, or when it already stands within reach. A mob picked out across the
	// field is none of those and must not postpone a decision to leave the map.
	bool IsPlayerBotEngagedWith(LPCHARACTER ch, LPCHARACTER victim,
			const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !victim)
			return false;
		if (victim->GetVictim() == ch)
			return true;
		if (state.dwLastCombatActionTime != 0 &&
				dwNow - state.dwLastCombatActionTime <= PLAYERBOT_TRAVEL_ENGAGED_WINDOW)
			return true;
		return DISTANCE_APPROX(ch->GetX() - victim->GetX(),
				ch->GetY() - victim->GetY()) <= PLAYERBOT_TRAVEL_ENGAGED_RANGE;
	}

	// The nearest stone within reach that is worth this bot's level. The
	// crossing fights nothing else, and this is looked for by hand because the
	// target scan does not run while a walk owns the tick.
	struct FPlayerBotFindStoneNearby
	{
		LPCHARACTER m_owner;
		LPCHARACTER m_found;
		int m_bestDistance;
		FPlayerBotFindStoneNearby(LPCHARACTER owner, int range)
			: m_owner(owner), m_found(NULL), m_bestDistance(range) {}
		void operator()(LPENTITY entity)
		{
			if (!entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER stone = static_cast<LPCHARACTER>(entity);
			if (!stone->IsStone() || stone->IsDead() ||
					!IsPlayerBotMetinWorthFighting(m_owner, stone))
				return;
			const int distance = DISTANCE_APPROX(stone->GetX() - m_owner->GetX(),
					stone->GetY() - m_owner->GetY());
			if (distance < m_bestDistance)
			{
				m_bestDistance = distance;
				m_found = stone;
			}
		}
	};

	LPCHARACTER FindPlayerBotStoneNearby(LPCHARACTER ch, int range)
	{
		if (!ch || !ch->GetSectree())
			return NULL;
		FPlayerBotFindStoneNearby finder(ch, range);
		ch->GetSectree()->ForEachAround(finder);
		return finder.m_found;
	}

	bool ManagePlayerBotWorldTravel(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || state.bVisitingShop || state.bVisitingBiologist ||
				state.bVisitingStable || state.bRecoveringAfterDeath || state.bTacticalRetreat)
			return false;

		const long mapIndex = ch->GetMapIndex();
		const bool hasMedal = ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) > 0;
		// A trader does not down tools to go and farm horse medals in the Monkey
		// Dungeon. That errand takes a bot right across the world for the better
		// part of an hour, and it is exactly the striving this personality exists
		// not to do.
		const bool pursuesHorseExpedition =
				state.bPersonality != BOT_PERSONALITY_MERCHANT &&
				ShouldPlayerBotPursueHorseExpedition(ch, dwNow);
		const bool needsHorseExpedition = pursuesHorseExpedition && !hasMedal;
		// GetWear answers NULL for every slot until the item cache has loaded,
		// which is exactly the state a character is in for the first seconds after
		// a map change. Trusting it there made a bot believe it had lost its
		// weapon the moment it arrived somewhere.
		const bool needsEssentialWeaponSupply = ch->IsItemLoaded() &&
				(ch->GetWear(WEAR_WEAPON) == NULL || NeedsPlayerBotArrows(ch));
		const bool m2LevelingCohort = IsPlayerBotM2LevelingCohort(ch);
		const bool wantsM3 = ShouldPlayerBotVisitM3(ch);
		const bool needsCriticalTownServices = NeedsPlayerBotCriticalTownServices(ch);
		const bool needsM1OnlyServices = NeedsPlayerBotM1OnlyServices(ch);
		// M2 has its own blacksmith. Only the remote M3 farm needs to schedule a
		// return to town for equipment progression.
		const bool scheduledRemoteRefine = mapIndex == PLAYERBOT_MAP_CHUNJO_M3 &&
				ShouldPlayerBotLeaveRemoteMapForRefining(ch, state, dwNow);

		// Leaving the Monkey Dungeon is a decision, not a pathfinding exercise.
		// Evaluate it before yielding to an existing victim: a monster near the
		// portal must not keep a finished, timed-out or unequipped bot here forever.
		if (IsPlayerBotMonkeyMap(mapIndex))
		{
			if (state.dwDungeonEnteredTime == 0)
				state.dwDungeonEnteredTime = dwNow;
			const bool visitExpired = dwNow - state.dwDungeonEnteredTime >=
					PLAYERBOT_MONKEY_MAX_VISIT_TIME;
			const int medalCount = ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM);
			playerbot_world_rules::TMonkeyVisitContext context;
			context.needsEssentialSupply = needsEssentialWeaponSupply;
			context.needsPotions = NeedsPlayerBotEmergencyPotions(ch);
			context.medalCount = medalCount;
			context.desiredMedalCount = GetPlayerBotDesiredHorseMedalStock(ch);
			context.visitExpired = visitExpired;
			// Re-evaluate the rotating cohort even inside the dungeon. Bots which are
			// no longer selected finish their current medal (if any) and leave instead
			// of occupying the dungeon until its absolute 30-minute timeout. A bot
			// that has levelled into the next dungeon's band leaves for the same
			// reason - the rooms here have stopped paying. The medal dropper farms
			// medals to sell, so its own horse does not gate it.
			const bool bMedalDropper = state.bPersonality == BOT_PERSONALITY_MEDAL_DROPPER;
			context.canAdvanceHorse = pursuesHorseExpedition &&
					(bMedalDropper || CanPlayerBotAdvanceHorse(ch)) &&
					GetPlayerBotMonkeyMapForLevel(ch->GetLevel()) == mapIndex;
			const playerbot_world_rules::EMonkeyExitDecision exitDecision =
					playerbot_world_rules::DecideMonkeyExit(context);
			if (exitDecision != playerbot_world_rules::MONKEY_STAY)
			{
				SetPlayerBotGoal(ch, state,
						exitDecision == playerbot_world_rules::MONKEY_EXIT_RESTOCK
						? BOT_GOAL_RESTOCK : BOT_GOAL_HORSE, dwNow);
				const char* reason = "monkey_horse_complete_direct";
				if (exitDecision == playerbot_world_rules::MONKEY_EXIT_RESTOCK)
					reason = "monkey_restock_direct";
				else if (exitDecision == playerbot_world_rules::MONKEY_EXIT_MEDAL_READY)
					reason = "monkey_medal_found_direct";
				else if (exitDecision == playerbot_world_rules::MONKEY_EXIT_TIMEOUT)
					reason = "monkey_timeout_direct";
				const bool transitioned = TransitionPlayerBotMap(ch, state,
						PLAYERBOT_MAP_CHUNJO_M2, PLAYERBOT_M2_MONKEY_RETURN_X,
						PLAYERBOT_M2_MONKEY_RETURN_Y, dwNow, reason);
				if (transitioned && medalCount == 0)
					state.dwNextWorldTravelTime = dwNow + number(300000, 900000);
				return transitioned;
			}
		}

		// M3 is a focused level-30 weapon farm, not a levelling map. A bot which
		// reaches level 25 graduates immediately, even if an old victim is still
		// alive, and resumes normal progression in M2.
		// ...unless it is there on purpose: the M3 dropper stays to 32, and
		// graduating it at 25 sent it back to Bokjung, where the same rule sent
		// it to M3 again - a hundred and fifty warps an hour per bot.
		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M3 && ch->GetLevel() > 24 &&
				!ShouldPlayerBotVisitM3(ch))
		{
			SetPlayerBotGoal(ch, state, BOT_GOAL_LEVEL_UP, dwNow);
			return MovePlayerBotToWorldPortal(ch, state,
					PLAYERBOT_M3_RETURN_PORTAL_X, PLAYERBOT_M3_RETURN_PORTAL_Y,
					PLAYERBOT_MAP_CHUNJO_M2, PLAYERBOT_M2_FROM_M3_X,
					PLAYERBOT_M2_FROM_M3_Y, dwNow, "m3_level_graduated");
		}

		// A bot should not walk away from a fight -- but "holds a target" was
		// standing in for "is fighting", and in a dense respawn those are not the
		// same thing at all. Something is always in range, so this check used to
		// return before the routing below had ever been consulted, and the
		// arrival areas of frontier maps quietly became one-way (issue #10).
		//
		// Three cases now. A Metin already under the hammer is always finished
		// first; ShouldPlayerBotAbandonStone releases a stalled one. A live fight
		// holds travel back, but only for a bounded grace period, so an endless
		// chain of packs can no longer outrank the decision to leave. A target
		// merely selected across the field does not delay anything.
		LPCHARACTER victim = state.dwTargetVID != 0
				? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		if (!victim || victim->IsDead())
			state.dwTravelBlockedSince = 0;
		else
		{
			if (state.dwTravelBlockedSince == 0)
				state.dwTravelBlockedSince = dwNow;
			const bool graceLeft = dwNow - state.dwTravelBlockedSince <
					PLAYERBOT_TRAVEL_FIGHT_GRACE;
			if (victim->IsStone() ||
					(graceLeft && IsPlayerBotEngagedWith(ch, victim, state, dwNow)))
				return false;
		}

		// Crossing the desert between its two gates: a walk that owns the tick,
		// so nothing on the way is fought - the target scan never runs - except
		// a stone worth the level, taken when one stands within reach, finished
		// (the victim rule above holds the walk for a stone) and then the walk
		// goes on. A player heading for V1 does exactly this.
		if (mapIndex == PLAYERBOT_MAP_DESERT && state.lDesertCrossingTo != 0)
		{
			if (dwNow >= state.dwNextCrossingStoneCheck)
			{
				state.dwNextCrossingStoneCheck = dwNow + PLAYERBOT_CROSSING_STONE_CHECK_INTERVAL;
				LPCHARACTER stone = FindPlayerBotStoneNearby(ch, PLAYERBOT_CROSSING_STONE_RANGE);
				if (stone)
				{
					RememberPlayerBotMetin(stone, dwNow);
					ReservePlayerBotMetin(ch, stone, dwNow);
					state.dwTargetVID = stone->GetVID();
					ch->SetVictim(stone);
					ClearPlayerBotRoute(state, true);
					sys_log(0, "PLAYERBOT_WORLD: crossing stone pid=%u name=%s stone_vid=%u level=%u pos=(%ld,%ld)",
							ch->GetPlayerID(), ch->GetName(), (unsigned int)stone->GetVID(),
							stone->GetLevel(), stone->GetX(), stone->GetY());
					return false;
				}
			}
			const bool toV1 = state.lDesertCrossingTo == PLAYERBOT_MAP_SPIDER_V1;
			SetPlayerBotGoal(ch, state, BOT_GOAL_LEVEL_UP, dwNow);
			return MovePlayerBotToWorldPortal(ch, state,
					toV1 ? PLAYERBOT_DESERT_V1_GATE_X : PLAYERBOT_DESERT_EXIT_X,
					toV1 ? PLAYERBOT_DESERT_V1_GATE_Y : PLAYERBOT_DESERT_EXIT_Y,
					state.lDesertCrossingTo, state.lDesertCrossingX, state.lDesertCrossingY,
					dwNow, toV1 ? "desert_gate_to_v1" : "desert_gate_to_bokjung");
		}

		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M1)
		{
			// Compact and sell an oversized potion reserve before the first trip to
			// M2. Once the bot is already outside M1, excess potions alone must not
			// drag it back across maps; it can keep levelling until a real restock or
			// inventory visit is needed.
			const bool townVisitRecentlyCompleted = state.dwNextShopCheckTime != 0 &&
					dwNow < state.dwNextShopCheckTime;
			const bool needsAnyRefine = HasPlayerBotRefineOpportunity(ch);
			const bool needsTownPreparation = NeedsPlayerBotPotions(ch) ||
					CountPlayerBotJunkItems(ch) >= 12 || needsAnyRefine;
			// The soft needs get one town visit to be met. If the bot has just
			// been shopping and still wants something, the town cannot supply it,
			// and standing here is worse than moving on.
			if (hasMedal || BlocksPlayerBotTravel(ch) || needsM1OnlyServices ||
					HasPlayerBotExcessPotions(ch) ||
					((needsTownPreparation || needsCriticalTownServices) &&
					 !townVisitRecentlyCompleted))
				return false;
			// The M2 cohort ends at 35, but the frontier maps begin at 30 and run
			// far past it. Testing only the cohort here meant a level 36+ bot fell
			// out of this gate on every tick and stayed in Joan for good, hunting
			// level-3 wolves - which is the "boty bija psy" the Discord keeps
			// reporting. Anything with somewhere better to be gets through.
			if (!needsHorseExpedition && !m2LevelingCohort && !wantsM3 &&
					GetPlayerBotFrontierMapForLevel(ch) == 0 &&
					!IsPlayerBotPastM2Ceiling(ch))
				return false;
			if (state.dwNextWorldTravelTime == 0)
			{
				const bool graduatedFromM1 = ch->GetLevel() >= 22 && !needsHorseExpedition;
				const DWORD minDelay = needsHorseExpedition ? PLAYERBOT_HORSE_TRAVEL_MIN_DELAY :
						(graduatedFromM1 ? PLAYERBOT_LEVEL22_TRAVEL_MIN_DELAY :
						 PLAYERBOT_WORLD_TRAVEL_MIN_DELAY);
				const DWORD maxDelay = needsHorseExpedition ? PLAYERBOT_HORSE_TRAVEL_MAX_DELAY :
						(graduatedFromM1 ? PLAYERBOT_LEVEL22_TRAVEL_MAX_DELAY :
						 PLAYERBOT_WORLD_TRAVEL_MAX_DELAY);
				const DWORD spread = PlayerBotNavHash(ch->GetPlayerID() ^ 0x54524156U) %
						(maxDelay - minDelay + 1);
				state.dwNextWorldTravelTime = dwNow + minDelay + spread;
				return false;
			}
			if (dwNow < state.dwNextWorldTravelTime)
				return false;

			// Joan has a Teleporter of its own, so a bot which has already outgrown
			// Bokjung can leave for the frontier directly. Routing it through M2
			// first would queue it behind every town errand in the village, which
			// is what left Orc Valley empty while the Desert filled up from the
			// bots that happened to already be in Bokjung.
			// Let it fish before it is handed the next hunting destination.
			if (WantsPlayerBotFishingTrip(ch, state, dwNow))
				return false;

			if (!needsHorseExpedition && !wantsM3)
			{
				const long directMap = ShouldPlayerBotLeaveForFrontier(ch)
						? GetPlayerBotFrontierMapForLevel(ch) : 0;
				if (directMap != 0)
				{
					long arriveX = 0, arriveY = 0;
					GetPlayerBotFrontierArrival(directMap, arriveX, arriveY);
					char reason[48];
					snprintf(reason, sizeof(reason), "m1_direct_to_%s", GetPlayerBotFrontierName(directMap));
					SetPlayerBotGoal(ch, state, BOT_GOAL_LEVEL_UP, dwNow);
					return MovePlayerBotToWorldPortal(ch, state,
							PLAYERBOT_M1_TELEPORTER_X, PLAYERBOT_M1_TELEPORTER_Y,
							directMap, arriveX, arriveY, dwNow, reason);
				}
			}

			SetPlayerBotGoal(ch, state, needsHorseExpedition ? BOT_GOAL_HORSE :
					(wantsM3 ? BOT_GOAL_GET_EQUIPMENT : BOT_GOAL_LEVEL_UP), dwNow);
			return MovePlayerBotToWorldPortal(ch, state,
					PLAYERBOT_M1_TO_M2_PORTAL_X, PLAYERBOT_M1_TO_M2_PORTAL_Y,
					PLAYERBOT_MAP_CHUNJO_M2, PLAYERBOT_M2_ARRIVAL_X, PLAYERBOT_M2_ARRIVAL_Y,
					dwNow, needsHorseExpedition ? "horse_to_m2" : "level_to_m2");
		}

		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M2)
		{
			// ManagePlayerBotHorse owns the medal on M2 and walks to the local Stable
			// Boy. Returning to M1 here was the source of the needless three-map trip.
			if (hasMedal)
				return false;

			// Profession trainers and the Biologist only exist in Joan. Routine gear,
			// potion, inventory and refine needs are served by the real Bokjung NPCs.
			if (needsM1OnlyServices)
			{
				SetPlayerBotGoal(ch, state, ch->GetSkillGroup() == 0
						? BOT_GOAL_CHOOSE_PROFESSION : BOT_GOAL_BIOLOGIST, dwNow);
				return MovePlayerBotToWorldPortal(ch, state,
						PLAYERBOT_M2_TO_M1_PORTAL_X, PLAYERBOT_M2_TO_M1_PORTAL_Y,
						PLAYERBOT_MAP_CHUNJO_M1, PLAYERBOT_M1_RETURN_X,
						PLAYERBOT_M1_RETURN_Y, dwNow, "m1_only_service");
			}
			// Same rule in Bokjung: its own shops own this need, but only until a
			// visit has actually happened. Otherwise a bot the town cannot equip
			// would never reach the frontier maps either.
			if (BlocksPlayerBotTravel(ch))
				return false;
			if (needsCriticalTownServices && (state.dwNextShopCheckTime == 0 ||
					dwNow < state.dwNextShopCheckTime))
				return false; // local M2 town visit owns this need

			if (needsHorseExpedition)
			{
				// Honour the rest period set by a failed/timed-out expedition and
				// stagger fresh M2 populations after a restart. Without this guard a
				// direct exit was followed by an immediate direct re-entry.
				if (state.dwNextWorldTravelTime == 0)
				{
					const DWORD spread = PlayerBotNavHash(ch->GetPlayerID() ^ 0x4d4f4e4bU) %
							(PLAYERBOT_HORSE_TRAVEL_MAX_DELAY -
							 PLAYERBOT_HORSE_TRAVEL_MIN_DELAY + 1);
					state.dwNextWorldTravelTime = dwNow +
							PLAYERBOT_HORSE_TRAVEL_MIN_DELAY + spread;
					return false;
				}
				if (playerbot_world_rules::IsTravelCooldownActive(
						dwNow, state.dwNextWorldTravelTime))
					return false;
				const long monkeyMap = GetPlayerBotMonkeyMapForLevel(ch->GetLevel());
				long monkeyX = 0, monkeyY = 0;
				GetPlayerBotMonkeyArrival(monkeyMap, monkeyX, monkeyY);
				char reason[48];
				snprintf(reason, sizeof(reason), "horse_to_monkey_%s", GetPlayerBotMonkeyName(monkeyMap));
				SetPlayerBotGoal(ch, state, BOT_GOAL_HORSE, dwNow);
				return MovePlayerBotToWorldPortal(ch, state,
						PLAYERBOT_M2_MONKEY_PORTAL_X, PLAYERBOT_M2_MONKEY_PORTAL_Y,
						monkeyMap, monkeyX, monkeyY, dwNow, reason);
			}

			if (wantsM3 && !needsCriticalTownServices)
			{
				SetPlayerBotGoal(ch, state, BOT_GOAL_GET_EQUIPMENT, dwNow);
				return MovePlayerBotToWorldPortal(ch, state,
						PLAYERBOT_M2_TO_M3_TELEPORTER_X, PLAYERBOT_M2_TO_M3_TELEPORTER_Y,
						PLAYERBOT_MAP_CHUNJO_M3, PLAYERBOT_M3_ARRIVAL_X,
						PLAYERBOT_M3_ARRIVAL_Y, dwNow, "level30_weapon_to_m3");
			}

			// The river is in Joan, and every bot old enough to hold a rod has long
			// since left it - so fishing only ever happens if the trip is a real
			// destination. Ranked above the frontier maps: a session is short, and
			// the pearls it brings back are worth more than the hunting it skips.
			if (WantsPlayerBotFishingTrip(ch, state, dwNow))
			{
				SetPlayerBotGoal(ch, state, BOT_GOAL_HUNTING, dwNow);
				return MovePlayerBotToWorldPortal(ch, state,
						PLAYERBOT_M2_TO_M1_PORTAL_X, PLAYERBOT_M2_TO_M1_PORTAL_Y,
						PLAYERBOT_MAP_CHUNJO_M1, PLAYERBOT_M1_RETURN_X,
						PLAYERBOT_M1_RETURN_Y, dwNow, "fishing_to_m1");
			}

			// Bokjung's own spawns stop paying long before the M2 band ends. Bots
			// which have outgrown them move on to Orc Valley and then the Desert
			// instead of grinding monsters they would rather walk past.
			const long frontierMap = ShouldPlayerBotLeaveForFrontier(ch)
					? GetPlayerBotFrontierMapForLevel(ch) : 0;
			if (frontierMap != 0)
			{
				long arriveX = 0, arriveY = 0;
				GetPlayerBotFrontierArrival(frontierMap, arriveX, arriveY);
				char reason[48];
				snprintf(reason, sizeof(reason), "level_to_%s", GetPlayerBotFrontierName(frontierMap));
				SetPlayerBotGoal(ch, state, BOT_GOAL_LEVEL_UP, dwNow);
				return MovePlayerBotToWorldPortal(ch, state,
						PLAYERBOT_M2_TO_M3_TELEPORTER_X, PLAYERBOT_M2_TO_M3_TELEPORTER_Y,
						frontierMap, arriveX, arriveY, dwNow, reason);
			}

			// Sending a bot back to Joan is only right when it has outgrown
			// nothing yet. Doing it above the ceiling produced an M1 <-> M2 loop:
			// Joan let it leave, Bokjung refused to keep it, and neither ever
			// hunted anything.
			if (!m2LevelingCohort && !IsPlayerBotPastM2Ceiling(ch))
			{
				SetPlayerBotGoal(ch, state, BOT_GOAL_LEVEL_UP, dwNow);
				const bool moving = MovePlayerBotToWorldPortal(ch, state,
						PLAYERBOT_M2_TO_M1_PORTAL_X, PLAYERBOT_M2_TO_M1_PORTAL_Y,
						PLAYERBOT_MAP_CHUNJO_M1, PLAYERBOT_M1_RETURN_X, PLAYERBOT_M1_RETURN_Y,
						dwNow, "m2_level_range_complete");
				if (ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M1)
					state.dwNextWorldTravelTime = dwNow + number(300000, 900000);
				return moving;
			}

			return false; // designated M2 leveler: hunt normally
		}

		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M3)
		{
			if (state.dwM3EnteredTime == 0)
				state.dwM3EnteredTime = dwNow;
			const bool visitExpired = dwNow - state.dwM3EnteredTime >= PLAYERBOT_M3_MAX_VISIT_TIME;
			if (!visitExpired && !needsCriticalTownServices && !needsM1OnlyServices &&
					!scheduledRemoteRefine &&
					!HasPlayerBotSpecialLevel30Weapon(ch, true))
				return false;

			SetPlayerBotGoal(ch, state,
					(needsCriticalTownServices || needsM1OnlyServices) ? BOT_GOAL_RESTOCK :
					(scheduledRemoteRefine ? BOT_GOAL_GET_EQUIPMENT : BOT_GOAL_LEVEL_UP), dwNow);
			const char* reason = "m3_weapon_found";
			if (needsCriticalTownServices || needsM1OnlyServices)
				reason = "m3_services_to_m2";
			else if (scheduledRemoteRefine)
				reason = "m3_scheduled_refine_to_m2";
			else if (visitExpired)
				reason = "m3_visit_complete";
			return MovePlayerBotToWorldPortal(ch, state,
					PLAYERBOT_M3_RETURN_PORTAL_X, PLAYERBOT_M3_RETURN_PORTAL_Y,
					PLAYERBOT_MAP_CHUNJO_M2, PLAYERBOT_M2_FROM_M3_X,
					PLAYERBOT_M2_FROM_M3_Y, dwNow, reason);
		}

		if (IsPlayerBotFrontierMap(mapIndex))
		{
			if (state.dwFrontierEnteredTime == 0)
				state.dwFrontierEnteredTime = dwNow;
			const DWORD stayed = dwNow - state.dwFrontierEnteredTime;
			const bool visitExpired = stayed >=
					GetPlayerBotFrontierVisitTime(state.bPersonality);
			// Two minutes of actually playing here before anything but a real
			// emergency may send the bot home again.
			const bool settledIn = stayed >= PLAYERBOT_FRONTIER_MIN_VISIT_TIME;
			// Outgrowing the map matters as much as running out of potions: neither
			// Orc Valley nor the Desert has a merchant, a blacksmith or a trainer.
			const bool outOfBand = GetPlayerBotFrontierMapForLevel(ch) != mapIndex;
			// Only a need that actually stops the bot playing is worth the trip
			// home. Sending it back for a helmet the town cannot sell turned the
			// journey into a shuttle: it arrived, saw the same unmet need, and
			// left again without ever fighting anything here.
			// A blocking need still wins immediately - a bot with no weapon left
			// cannot wait out a timer. Everything else waits until the bot has
			// been here long enough for the trip to have been worth making.
			const bool blocked = BlocksPlayerBotTravel(ch);
			const bool needsTown = blocked ||
					(settledIn && (needsM1OnlyServices || needsEssentialWeaponSupply));
			// The Monkey Dungeons are reached from Bokjung, and nothing here ever
			// went back for one: the roll that sends a bot for a medal was only
			// read in town, and a bot past forty lives out here - which is how
			// 439 of them came to have no horse. A party is not broken up for it;
			// the trip is taken alone, the party re-forms on the way back.
			const bool wantsMedal = settledIn && needsHorseExpedition &&
					ch->GetParty() == NULL;
			if (!visitExpired && !outOfBand && !needsTown && !wantsMedal)
				return false;

			SetPlayerBotGoal(ch, state, needsTown ? BOT_GOAL_RESTOCK :
					(wantsMedal ? BOT_GOAL_HORSE : BOT_GOAL_LEVEL_UP), dwNow);
			const char* reason = "frontier_visit_complete";
			if (needsTown)
				reason = "frontier_services_to_m2";
			else if (outOfBand)
				reason = "frontier_level_graduated";
			else if (wantsMedal)
				reason = "frontier_horse_to_m2";
			long exitX = 0, exitY = 0;
			GetPlayerBotFrontierExit(mapIndex, exitX, exitY);
			return MovePlayerBotToWorldPortal(ch, state, exitX, exitY,
					PLAYERBOT_MAP_CHUNJO_M2, PLAYERBOT_M2_FROM_M3_X, PLAYERBOT_M2_FROM_M3_Y,
					dwNow, reason);
		}

		if (IsPlayerBotMonkeyMap(mapIndex))
			return false; // stay and fight; departure was handled before victim yielding

		// Anything else means the bot was moved somewhere no branch above owns:
		// see IsPlayerBotPositionOffItsMap for the case where the move only half
		// happened and the map index still reads as the one the bot is standing
		// on. Both end here, and both are put back in Bokjung.
		// the frontier maps carry real warp NPCs of their own, and walking inside
		// one's trigger radius hands the character to a map the AI has no plan
		// for. Nothing would ever bring it back, so it would sit there for good.
		SetPlayerBotGoal(ch, state, BOT_GOAL_LEVEL_UP, dwNow);
		if (TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_CHUNJO_M2,
				PLAYERBOT_M2_FROM_M3_X, PLAYERBOT_M2_FROM_M3_Y, dwNow, "stranded_recovery"))
		{
			sys_log(0, "PLAYERBOT_WORLD: recovered pid=%u name=%s from unmanaged map=%ld",
					ch->GetPlayerID(), ch->GetName(), mapIndex);
			return true;
		}
		return false;
	}
}

#endif
