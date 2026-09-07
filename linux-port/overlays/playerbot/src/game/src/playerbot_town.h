#ifndef __INC_METIN2_PLAYERBOT_TOWN_H__
#define __INC_METIN2_PLAYERBOT_TOWN_H__

// A visit to town, from the gate to the last errand: which NPCs this trip is
// for and in what order, walking each leg, the Biologist, and setting up a
// market stall.
//
// A town visit is a small state machine because it has to survive being
// interrupted - a bot that is teleported, killed, or simply loses its route
// mid-errand must be able to pick the trip up rather than start it again. The
// phase in TPlayerBotAIState is that memory, and every branch here either
// advances it or ends the visit.
//
// The stall is engine state with an AI deadline, so releasing one runs at the
// very top of the tick, ahead of everything that could claim it - see
// ManagePlayerBotShopLifetime and the comment in CPlayerBotManager::Update.
//
// An implementation fragment in the sense playerbot_types.h describes: it
// defines objects, relies on the engine headers playerbot_manager.cpp includes
// above it, and reopens the same anonymous namespace. Include it exactly once,
// after playerbot_travel.h - that file decides a town trip is due, this one
// carries it out.

namespace
{
	BYTE GetPlayerBotFirstInteriorTownPhase(const TPlayerBotAIState& state)
	{
		if (state.bTownNeedMisc)
			return BOT_TOWN_PHASE_MISC_MERCHANT;
		if (state.bTownNeedBlacksmith)
			return BOT_TOWN_PHASE_BLACKSMITH;
		return BOT_TOWN_PHASE_NONE;
	}

	BYTE GetPlayerBotFirstExteriorTownPhase(const TPlayerBotAIState& state)
	{
		if (state.bTownNeedTrainer)
			return BOT_TOWN_PHASE_TRAINER;
		if (state.bTownNeedWeaponMerchant)
			return BOT_TOWN_PHASE_WEAPON_MERCHANT;
		if (state.bTownNeedArmorMerchant)
			return BOT_TOWN_PHASE_ARMOR_MERCHANT;
		return BOT_TOWN_PHASE_NONE;
	}

	BYTE GetPlayerBotFirstDirectTownPhase(const TPlayerBotAIState& state)
	{
		if (state.bTownNeedWeaponMerchant)
			return BOT_TOWN_PHASE_WEAPON_MERCHANT;
		if (state.bTownNeedArmorMerchant)
			return BOT_TOWN_PHASE_ARMOR_MERCHANT;
		if (state.bTownNeedMisc)
			return BOT_TOWN_PHASE_MISC_MERCHANT;
		if (state.bTownNeedBlacksmith)
			return BOT_TOWN_PHASE_BLACKSMITH;
		return BOT_TOWN_PHASE_NONE;
	}

	void StartPlayerBotTownVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || state.bVisitingShop ||
				(ch->GetMapIndex() != PLAYERBOT_MAP_CHUNJO_M1 &&
				 ch->GetMapIndex() != PLAYERBOT_MAP_CHUNJO_M2))
			return;
		const bool inM2 = ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M2;

		state.bTownNeedTrainer = !inM2 && ch->GetLevel() >= 5 && ch->GetSkillGroup() == 0 &&
				ch->GetJob() <= JOB_SHAMAN;
		state.bTownNeedMisc = HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_MISC) ||
				NeedsPlayerBotPotions(ch) || HasPlayerBotExcessPotions(ch) ||
				NeedsPlayerBotProgressionBoots(ch);
		state.bTownNeedWeaponMerchant = HasPlayerBotJunkForMerchant(
				ch, BOT_MERCHANT_WEAPON) || ch->GetWear(WEAR_WEAPON) == NULL ||
				NeedsPlayerBotProgressionWeapon(ch) || NeedsPlayerBotArrows(ch);
		state.bTownNeedArmorMerchant = HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_ARMOR) ||
				NeedsPlayerBotProgressionArmor(ch) || NeedsPlayerBotProgressionShield(ch) ||
				NeedsPlayerBotProgressionHelmet(ch);
		state.bTownNeedBlacksmith = HasPlayerBotRefineOpportunity(ch);
		if (!state.bTownNeedTrainer && !state.bTownNeedMisc && !state.bTownNeedWeaponMerchant &&
				!state.bTownNeedArmorMerchant && !state.bTownNeedBlacksmith)
		{
			state.dwNextShopCheckTime = dwNow + number(60000, 120000);
			return;
		}

		state.bVisitingShop = true;
		if (inM2)
		{
			state.bTownVisitPhase = GetPlayerBotFirstDirectTownPhase(state);
		}
		else
		{
			const bool alreadyInsideTown = ch->GetX() >= 57000 && ch->GetX() <= 63000 &&
					ch->GetY() >= 170000 && ch->GetY() <= 174000;
			if (alreadyInsideTown)
			{
				state.bTownVisitPhase = GetPlayerBotFirstInteriorTownPhase(state);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					state.bTownVisitPhase = BOT_TOWN_PHASE_GATE_OUT;
			}
			else
			{
				state.bTownVisitPhase = GetPlayerBotFirstExteriorTownPhase(state);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					state.bTownVisitPhase = BOT_TOWN_PHASE_GATE_IN;
			}
		}
		state.dwTownWaitUntil = 0;
		state.dwNextShopCheckTime = dwNow + 60000;
		state.dwTargetVID = 0;
		state.bStuckCounter = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		ClearPlayerBotRoute(state, true);
	}

	void GetPlayerBotNpcApproach(DWORD playerID, long npcX, long npcY, DWORD salt,
			long& approachX, long& approachY)
	{
		const DWORD hash = PlayerBotNavHash(playerID ^ salt);
		const int lane = (int)(hash % 11U) - 5;
		const int row = (int)((hash / 11U) % 6U);
		approachX = npcX + lane * 90;
		approachY = npcY - 240 - row * 80;
	}

	void GivePlayerBotBiologistReward(LPCHARACTER ch,
			const TPlayerBotBiologistMission& mission)
	{
		if (!ch)
			return;

		DWORD rewardItem = 0;
		switch (mission.requiredLevel)
		{
			case 4:
				rewardItem = ch->GetJob() == JOB_SHAMAN ? 7003 : 13;
				break;
			case 7:
			{
				const DWORD armorRewards[4] = { 11203, 11403, 11603, 11803 };
				if (ch->GetJob() <= JOB_SHAMAN)
					rewardItem = armorRewards[ch->GetJob()];
				break;
			}
			case 10: rewardItem = 16023; break;
			case 15: rewardItem = 17023; break;
			case 20: rewardItem = 14023; break;
			case 25:
			{
				const DWORD helmetRewards[4] = { 12222, 12362, 12502, 12642 };
				if (ch->GetJob() <= JOB_SHAMAN)
					rewardItem = helmetRewards[ch->GetJob()];
				break;
			}
		}

		if (rewardItem != 0)
			ch->AutoGiveItem(rewardItem, 1, -1, false);
		if (mission.rewardGold > 0)
			ch->PointChange(POINT_GOLD, mission.rewardGold);
		if (mission.rewardExp > 0)
			ch->PointChange(POINT_EXP, mission.rewardExp, true);
	}

	bool CompletePlayerBotBiologistMission(LPCHARACTER ch, size_t missionIndex)
	{
		if (!ch || missionIndex >= PLAYERBOT_BIOLOGIST_MISSION_COUNT)
			return false;
		const TPlayerBotBiologistMission& mission = PLAYERBOT_BIOLOGIST_MISSIONS[missionIndex];
		const int completeState = GetPlayerBotBiologistStateIndex(missionIndex, "__complete");
		quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
		if (!pc || completeState < 0)
			return false;

		GivePlayerBotBiologistReward(ch, mission);
		ch->SetQuestFlag(GetPlayerBotBiologistFlag(mission, "collect_count"), 0);
		ch->SetQuestFlag(GetPlayerBotBiologistFlag(mission, "drink_drug"), 0);
		pc->SetQuestState(mission.questName, completeState);
		sys_log(0, "PLAYERBOT_BIOLOGIST: mission complete pid=%u name=%s quest=%s level=%u gold=%u exp=%u",
				ch->GetPlayerID(), ch->GetName(), mission.questName, mission.requiredLevel,
				mission.rewardGold, mission.rewardExp);
		return true;
	}

	bool ManagePlayerBotBiologist(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || state.bVisitingShop)
			return false;
		if (!state.bVisitingBiologist && dwNow < state.dwNextBiologistCheckTime)
			return false;
		if (!state.bVisitingBiologist)
			state.dwNextBiologistCheckTime = dwNow + 2000;

		size_t missionIndex = 0;
		const TPlayerBotBiologistMission* mission =
				GetActivePlayerBotBiologistMission(ch, &missionIndex);
		if (!mission)
		{
			state.bVisitingBiologist = false;
			return false;
		}

		if (!EnsurePlayerBotBiologistMissionStarted(ch, missionIndex))
			return false;
		if (ch->GetMapIndex() != 21)
		{
			state.bVisitingBiologist = false;
			return false;
		}

		const bool keyPhase = IsPlayerBotBiologistKeyPhase(ch, missionIndex);
		int required = mission->requiredCount;
		const DWORD wantedVnum = GetPlayerBotBiologistWantedItem(ch, missionIndex, &required);
		const int accepted = keyPhase ? 0 : std::max(0, ch->GetQuestFlag(
				GetPlayerBotBiologistFlag(*mission, "collect_count")));
		const int remaining = std::max(0, required - accepted);
		const int carried = ch->CountSpecifyItem(wantedVnum);
		if (!state.bVisitingBiologist && carried < remaining)
			return false;

		if (!state.bVisitingBiologist)
		{
			state.bVisitingBiologist = true;
			state.dwNextBiologistActionTime = 0;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_BIOLOGIST: going to NPC pid=%u name=%s quest=%s carried=%d accepted=%d/%u",
					ch->GetPlayerID(), ch->GetName(), mission->questName,
					carried, accepted, mission->requiredCount);
		}

		SetPlayerBotAction(state, BOT_ACTION_BIOLOGIST, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), PLAYERBOT_BIOLOGIST_X,
				PLAYERBOT_BIOLOGIST_Y, 0x42494f4cU, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > 650)
		{
			if (!MovePlayerBot(ch, approachX, approachY, dwNow, 20, true, true) &&
					state.bStuckCounter >= 6)
			{
				state.bVisitingBiologist = false;
				state.dwNextBiologistCheckTime = dwNow + 30000;
				ClearPlayerBotRoute(state, true);
				sys_err("PLAYERBOT_BIOLOGIST: route failed pid=%u name=%s from=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), ch->GetX(), ch->GetY());
				return false;
			}
			return true;
		}

		SetPlayerBotRidingForTravel(ch, state, false, dwNow, "biologist_interaction");
		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (state.dwNextBiologistActionTime == 0)
		{
			state.dwNextBiologistActionTime = dwNow + number(3000, 8000);
			return true;
		}
		if (dwNow < state.dwNextBiologistActionTime)
			return true;

		if (ch->CountSpecifyItem(wantedVnum) <= 0)
		{
			state.bVisitingBiologist = false;
			state.dwNextBiologistActionTime = 0;
			state.dwNextBiologistCheckTime = dwNow + number(5000, 12000);
			ClearPlayerBotRoute(state, true);
			return false;
		}

		if (keyPhase)
		{
			ch->RemoveSpecifyItem(wantedVnum, 1);
			ch->AddAffect(AFFECT_COLLECT, POINT_MOV_SPEED, PLAYERBOT_ORC_TOOTH_REWARD_MOV_SPEED,
					0, 60L * 60L * 24L * 365L * 60L, 0, false);
			ch->AutoGiveItem(PLAYERBOT_ORC_TOOTH_REWARD_BOX_VNUM, 1, -1, false);
			sys_log(0, "PLAYERBOT_BIOLOGIST: soul stone handed in pid=%u name=%s quest=%s mov_speed=+%d",
					ch->GetPlayerID(), ch->GetName(), mission->questName, PLAYERBOT_ORC_TOOTH_REWARD_MOV_SPEED);
			CompletePlayerBotBiologistMission(ch, missionIndex);
			state.bVisitingBiologist = false;
			state.dwNextBiologistActionTime = 0;
			state.dwNextBiologistCheckTime = dwNow + number(10000, 25000);
			ClearPlayerBotRoute(state, true);
			return false;
		}

		ch->RemoveSpecifyItem(mission->itemVnum, 1);
		const bool acceptedNow = number(1, 100) <= mission->acceptPercent;
		int newAccepted = accepted;
		if (acceptedNow)
		{
			newAccepted = accepted + 1;
			ch->SetQuestFlag(GetPlayerBotBiologistFlag(*mission, "collect_count"), newAccepted);
		}
		sys_log(0, "PLAYERBOT_BIOLOGIST: submitted pid=%u name=%s quest=%s accepted_now=%d progress=%d/%u carried_left=%d",
				ch->GetPlayerID(), ch->GetName(), mission->questName, acceptedNow ? 1 : 0,
				newAccepted, mission->requiredCount, ch->CountSpecifyItem(mission->itemVnum));

		if (newAccepted >= mission->requiredCount && missionIndex == PLAYERBOT_BIOLOGIST_ORC_TOOTH_INDEX)
		{
			const int keyState = GetPlayerBotBiologistStateIndex(missionIndex, "key_item");
			quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
			if (pc && keyState >= 0)
			{
				pc->SetQuestState(mission->questName, keyState);
				sys_log(0, "PLAYERBOT_BIOLOGIST: teeth accepted, waiting for the soul stone pid=%u name=%s",
						ch->GetPlayerID(), ch->GetName());
			}
			state.bVisitingBiologist = false;
			state.dwNextBiologistActionTime = 0;
			state.dwNextBiologistCheckTime = dwNow + number(10000, 25000);
			ClearPlayerBotRoute(state, true);
			return false;
		}
		if (newAccepted >= mission->requiredCount &&
				CompletePlayerBotBiologistMission(ch, missionIndex))
		{
			state.bVisitingBiologist = false;
			state.dwNextBiologistActionTime = 0;
			state.dwNextBiologistCheckTime = dwNow + number(10000, 25000);
			ClearPlayerBotRoute(state, true);
			return false;
		}

		state.dwNextBiologistActionTime = dwNow + number(2500, 5000);
		return true;
	}

	void FinishPlayerBotTownVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow,
			bool completed)
	{
		state.bVisitingShop = false;
		state.bTownNeedMisc = false;
		state.bTownNeedWeaponMerchant = false;
		state.bTownNeedArmorMerchant = false;
		state.bTownNeedBlacksmith = false;
		state.bTownNeedTrainer = false;
		state.bTownVisitPhase = BOT_TOWN_PHASE_NONE;
		state.dwTownWaitUntil = 0;
		state.dwNextShopCheckTime = dwNow +
			(completed ? number(300000, 600000) : number(60000, 120000));
		state.dwNextShoppingTime = dwNow;
		state.dwTargetVID = 0;
		state.bStuckCounter = 0;
		if (ch)
		{
			ch->SetVictim(NULL);
			ch->Stop();
			ch->SetPosition(POS_STANDING);
		}
		ClearPlayerBotRoute(state, true);
	}

	bool MovePlayerBotTownLeg(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow,
			long goalX, long goalY, int arrivalDistance);

	void AnnouncePlayerBotStall(LPCHARACTER ch, const char* pszItemName);

	bool GetPlayerBotShopCentre(long mapIndex, long& pitchX, long& pitchY)
	{
		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M1)
		{
			pitchX = PLAYERBOT_M1_GUARD_X;
			pitchY = PLAYERBOT_M1_GUARD_Y;
			return true;
		}
		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M2)
		{
			pitchX = PLAYERBOT_M2_MARKET_X;
			pitchY = PLAYERBOT_M2_MARKET_Y;
			return true;
		}
		return false;
	}

	bool IsPlayerBotMerchant(const TPlayerBotAIState& state)
	{
		return state.bPersonality == BOT_PERSONALITY_MERCHANT;
	}

	bool IsPlayerBotStallKeeper(const TPlayerBotAIState& state)
	{
		return IsPlayerBotMerchant(state) || IsPlayerBotDropper(state.bPersonality);
	}

	bool ShouldPlayerBotKeepShop(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_SHOP_MIN_LEVEL)
			return false;
		if (IsPlayerBotMerchant(state))
			return true;
		if (IsPlayerBotDropper(state.bPersonality))
			return PlayerBotWeightedRoll(
					PlayerBotNavHash(ch->GetPlayerID() ^ 0x44524f50U) % 1000U,
					PLAYERBOT_DROPPER_SHOP_ROLL, PLAYERBOT_WEIGHT_TRADE);
		return PlayerBotWeightedRoll(
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x53484f50U) % 1000U,
				IsPlayerBotFullyEquipped(ch) ? PLAYERBOT_FULL_GEAR_SHOP_ROLL : 100,
				PLAYERBOT_WEIGHT_TRADE);
	}

	DWORD ApplyPlayerBotBonusPremium(DWORD price, int bonusPercent)
	{
		if (bonusPercent <= 0)
			return price;
		return std::max<DWORD>(1, (DWORD)((unsigned long long)price *
				(unsigned long long)(100 + bonusPercent) / 100ULL));
	}

	DWORD GetPlayerBotShopAskingPrice(LPITEM item)
	{
		if (!item)
			return 1;
		const int bonusPercent = GetPlayerBotBonusPricePercent(item);
		const BYTE refine = item->GetRefineLevel();
		if (refine >= 9)
			return ApplyPlayerBotBonusPremium(PLAYERBOT_SHOP_PRICE_PLUS9, bonusPercent);
		if (refine == 8)
			return ApplyPlayerBotBonusPremium(PLAYERBOT_SHOP_PRICE_PLUS8, bonusPercent);
		if (refine == 7)
			return ApplyPlayerBotBonusPremium(PLAYERBOT_SHOP_PRICE_PLUS7, bonusPercent);
		const DWORD npcUnit = GetPlayerBotNpcSellUnitPrice(item);
		if ((item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) &&
				refine < PLAYERBOT_SHOP_MIN_GEAR_REFINE)
			return ApplyPlayerBotBonusPremium(
					std::max<DWORD>(1, npcUnit * PLAYERBOT_SCRAP_PRICE_MULT), bonusPercent);
		DWORD unit = npcUnit * PLAYERBOT_SHOP_MATERIAL_MARKUP;
		if (item->GetType() == ITEM_METIN)
			unit = PLAYERBOT_SHOP_PRICE_SOUL_STONE[std::min(4, GetPlayerBotSoulStoneGrade(item->GetVnum()))];

		const DWORD wallet = GetPlayerBotMarketMedianWallet();
		if (wallet > 0 && item->GetType() != ITEM_METIN)
		{
			DWORD permille = PLAYERBOT_MARKET_OTHER_WALLET_PERMILLE;
			if (IsPlayerBotTradeableMaterial(item))
				permille = PLAYERBOT_MARKET_MATERIAL_WALLET_PERMILLE;
			else if ((item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) && refine > 2)
				permille = PLAYERBOT_MARKET_GEAR_WALLET_PERMILLE_PER_REFINE * (refine - 2);
			const unsigned long long count = std::max<DWORD>(1, item->GetCount());
			const DWORD walletUnit = (DWORD)((unsigned long long)wallet * permille / 1000);
			const DWORD stackCap = (DWORD)((unsigned long long)wallet *
					PLAYERBOT_MARKET_STACK_WALLET_PERCENT / 100 / count);
			unit = std::max(unit, std::max<DWORD>(1, std::min(walletUnit, stackCap)));
		}
		const DWORD prior = unit;
		const DWORD dwNow = get_dword_time();

		size_t samples = 0;
		const DWORD paid = GetPlayerBotSaleUnitPrice(item->GetVnum(), refine, dwNow, &samples);
		if (paid != 0)
		{
			const DWORD floor = std::max<DWORD>(std::max<DWORD>(1, npcUnit),
					prior / PLAYERBOT_SALE_PRICE_CAP_MULT);
			const DWORD cap = prior == 0 ? PLAYERBOT_SALE_PRICE_CAP_FLAT
					: prior * PLAYERBOT_SALE_PRICE_CAP_MULT;
			const DWORD market = std::min(std::max(paid, floor), std::max(floor, cap));
			if (prior == 0)
				unit = market;
			else
			{
				const double w = (double)samples /
						(double)(samples + PLAYERBOT_MARKET_ANCHOR_N0);
				unit = (DWORD)(exp((1.0 - w) * log((double)prior) +
						w * log((double)market)) + 0.5);
			}
		}

		if (unit > 0 && IsPlayerBotTradeableMaterial(item))
		{
			const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(item->GetVnum());
			if (entry && (entry->dwDemandBots > 0 || entry->dwSupplyUnits > 0))
			{
				const double ratio =
						(double)(entry->dwDemandBots + PLAYERBOT_MARKET_REGULATOR_Q0) /
						(double)(entry->dwSupplyUnits + PLAYERBOT_MARKET_REGULATOR_Q0);
				const double mult = std::max(PLAYERBOT_MARKET_REGULATOR_MIN,
						std::min(PLAYERBOT_MARKET_REGULATOR_MAX,
							pow(ratio, PLAYERBOT_MARKET_REGULATOR_EXPONENT)));
				unit = std::max<DWORD>(1, (DWORD)(unit * mult + 0.5));
			}
		}

		unit = LimitPlayerBotAskStep(item->GetVnum(), refine, std::max<DWORD>(1, unit), dwNow);
		unit = ApplyPlayerBotBonusPremium(unit, bonusPercent);
		const DWORD price = unit * (DWORD)item->GetCount();
		return price == 0 ? 1U : price;
	}

	bool HasPlayerBotValuableBonus(LPITEM item)
	{
		if (!item)
			return false;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const BYTE type = item->GetAttributeType(i);
			const long value = item->GetAttributeValue(i);
			if (value <= 0)
				continue;
			if (type == APPLY_MAX_HP && value >= PLAYERBOT_VALUABLE_HP_BONUS)
				return true;
			if (item->GetType() == ITEM_ARMOR &&
					item->GetSubType() == ARMOR_SHIELD &&
					type == APPLY_IMMUNE_STUN)
				return true;
		}
		return false;
	}

	bool IsPlayerBotTopSlotLowLevelGear(LPITEM item)
	{
		if (!item || item->GetType() != ITEM_ARMOR)
			return false;
		const BYTE sub = item->GetSubType();
		if (sub != ARMOR_SHIELD && sub != ARMOR_HEAD)
			return false;
		return item->GetLevelLimit() >= PLAYERBOT_SHOP_TOP_SLOT_GEAR_LEVEL;
	}

	bool CanPlayerBotSellHorseMedals(LPCHARACTER ch, bool merchant)
	{
		if (merchant)
			return true;
		if (ch && GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_MEDAL_DROPPER)
			return true;
		return ch && ch->GetHorseLevel() >= 10 &&
				ch->GetLevel() < GetPlayerBotNextHorseRequiredLevel(ch->GetHorseLevel());
	}

	int DecidePlayerBotMaterialListing(LPCHARACTER ch, LPITEM item, bool report)
	{
		const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(item->GetVnum());
		const DWORD supply = entry ? entry->dwSupplyUnits : 0;
		const DWORD demand = entry ? entry->dwDemandBots : 0;
		int decision;
		if (demand == 0)
			decision = supply == 0 ? PLAYERBOT_LIST_PROBE : PLAYERBOT_LIST_NO_DEMAND;
		else
		{
			const DWORD target = demand * PLAYERBOT_MARKET_SUPPLY_PER_BUYER *
					PLAYERBOT_MARKET_SUPPLY_MARGIN_PERCENT / 100;
			decision = supply < target ? PLAYERBOT_LIST_LIST : PLAYERBOT_LIST_OVERSTOCK;
		}
		if (!report)
			return decision;
		++s_auMarketDecisions[decision];
		if (decision == PLAYERBOT_LIST_NO_DEMAND || decision == PLAYERBOT_LIST_OVERSTOCK)
			PlayerBotLogThrottled("PLAYERBOT_MARKET_HELD", get_dword_time(),
					"PLAYERBOT_MARKET: held pid=%u name=%s vnum=%u count=%u reason=%s supply=%u demand=%u",
					ch->GetPlayerID(), ch->GetName(), item->GetVnum(),
					(unsigned int)item->GetCount(), s_apszMarketDecisionNames[decision],
					supply, demand);
		return decision;
	}

	int ScorePlayerBotShopStock(LPCHARACTER ch, LPITEM item, bool merchant, bool report)
	{
		if (!item)
			return -1;
		if (IsPlayerBotSpecialLevel30Weapon(item))
			return 2000;
		if (HasPlayerBotValuableBonus(item))
			return 1500;
		if (item->GetRefineLevel() >= PLAYERBOT_PRECIOUS_REFINE)
			return 1000 + item->GetRefineLevel();
		if (PlayerBotNeedsRefineMaterial(ch, item->GetVnum()))
			return -1;
		if (item->GetVnum() == PLAYERBOT_HORSE_MEDAL_VNUM)
			return CanPlayerBotSellHorseMedals(ch, merchant) ? 900 : -1;
		if (IsPlayerBotTradeableMaterial(item))
		{
			const int decision = DecidePlayerBotMaterialListing(ch, item, report);
			if (decision == PLAYERBOT_LIST_LIST)
				return 500;
			if (decision == PLAYERBOT_LIST_PROBE)
				return 450;
			return -1;
		}
		if (item->GetVnum() == PLAYERBOT_SKILL_FORGET_SCROLL_VNUM)
			return GetPlayerBotStuckSkill(ch) != 0 ? -1 : 800;
		if (item->GetRefinedVnum() == 0 && item->GetType() == ITEM_MATERIAL)
			return -1;
		if (item->GetType() == ITEM_METIN)
			return WantsPlayerBotSoulStone(ch, item->GetVnum(), (DWORD)item->GetValue(5))
					? -1 : 700 + GetPlayerBotSoulStoneGrade(item->GetVnum()) * 100;
		if (item->GetType() == ITEM_SKILLBOOK)
		{
			const DWORD skillVnum = GetPlayerBotSkillBookSkillVnum(item);
			if (ch->GetSkillGroup() != 0 && IsPlayerBotOwnSkill(ch, skillVnum) &&
					CountPlayerBotSkillBooksAhead(ch, item, skillVnum) < PLAYERBOT_BOOK_KEEP_PER_SKILL)
				return -1;
			return GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_METIN_DROPPER
					? 1800 : 400;
		}

		const BYTE type = item->GetType();
		if (type == ITEM_WEAPON || type == ITEM_ARMOR)
		{
			if (IsPlayerBotScrapKeeper(ch->GetPlayerID()) &&
					item->GetRefineLevel() < PLAYERBOT_SHOP_MIN_GEAR_REFINE)
				return 100 + item->GetRefineLevel();
			if (item->GetRefineLevel() < PLAYERBOT_SHOP_MIN_GEAR_REFINE)
				return -1;
			if (item->GetLevelLimit() < PLAYERBOT_SHOP_MIN_GEAR_LEVEL &&
					!IsPlayerBotTopSlotLowLevelGear(item))
				return -1;
			return 100;
		}

		return -1;
	}

	bool IsPlayerBotStallWorthOpening(size_t lines, int bestScore)
	{
		if (lines == 0)
			return false;
		return lines >= PLAYERBOT_SHOP_MIN_ITEMS ||
				bestScore >= PLAYERBOT_SHOP_PRIZE_SCORE;
	}

	void CollectPlayerBotShopItems(LPCHARACTER ch,
			std::vector<std::pair<int, WORD> >& outScored, bool merchant)
	{
		outScored.clear();
		if (!ch || !ch->IsItemLoaded())
			return;
		const bool report = ShouldReportPlayerBotMarketDecisions(
				ch->GetPlayerID(), get_dword_time());
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->IsEquipped() || item->isLocked())
				continue;
			const TItemTable* proto = item->GetProto();
			if (!proto || IS_SET(proto->dwAntiFlags,
					ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP))
				continue;
			const DWORD vnum = item->GetVnum();
			if (vnum == 27001 || vnum == 27002 || vnum == 27003 || vnum == 27051 ||
					vnum == 27004 || vnum == 27005 || vnum == 27006 || vnum == 27052)
				continue;
			if ((vnum >= 50701 && vnum <= 50706) || vnum == PLAYERBOT_ORC_TOOTH_VNUM ||
					vnum == PLAYERBOT_JINUNGGYI_STONE_VNUM)
				continue;
			const BYTE type = item->GetType();
			if (type == ITEM_WEAPON || type == ITEM_ARMOR)
			{
				const int wearCell = item->FindEquipCell(ch);
				if (wearCell < 0 || ch->GetWear((BYTE)wearCell) == NULL)
					continue;
			}
			const int score = ScorePlayerBotShopStock(ch, item, merchant, report);
			if (score > 0)
				outScored.push_back(std::make_pair(score, cell));
		}
		std::sort(outScored.begin(), outScored.end(),
				std::greater<std::pair<int, WORD> >());
		const size_t limit = merchant
				? (size_t)PLAYERBOT_SHOP_MERCHANT_ITEMS
				: (size_t)PLAYERBOT_SHOP_MAX_ITEMS;

		const size_t reserved = limit / 2;
		std::vector<std::pair<int, WORD> > materials;
		std::vector<std::pair<int, WORD> > rest;
		for (size_t i = 0; i < outScored.size(); ++i)
		{
			LPITEM item = ch->GetInventoryItem(outScored[i].second);
			const bool isMaterial = IsPlayerBotTradeableMaterial(item);
			if (isMaterial && materials.size() < reserved)
				materials.push_back(outScored[i]);
			else
				rest.push_back(outScored[i]);
		}
		outScored = materials;
		for (size_t i = 0; i < rest.size() && outScored.size() < limit; ++i)
			outScored.push_back(rest[i]);
		std::sort(outScored.begin(), outScored.end(),
				std::greater<std::pair<int, WORD> >());
	}

	void GetPlayerBotHomePoint(long mapIndex, long& outMap, long& outX, long& outY)
	{
		outMap = PLAYERBOT_MAP_CHUNJO_M2;
		outX = PLAYERBOT_M2_FROM_M3_X;
		outY = PLAYERBOT_M2_FROM_M3_Y;
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_CHUNJO_M1:
				outMap = mapIndex; outX = PLAYERBOT_M1_RETURN_X; outY = PLAYERBOT_M1_RETURN_Y; break;
			case PLAYERBOT_MAP_CHUNJO_M2:
				outMap = mapIndex; outX = PLAYERBOT_M2_ARRIVAL_X; outY = PLAYERBOT_M2_ARRIVAL_Y; break;
			case PLAYERBOT_MAP_CHUNJO_M3:
				outMap = mapIndex; outX = PLAYERBOT_M3_ARRIVAL_X; outY = PLAYERBOT_M3_ARRIVAL_Y; break;
			case PLAYERBOT_MAP_MONKEY_EASY:
			case PLAYERBOT_MAP_MONKEY_MEDIUM:
			case PLAYERBOT_MAP_MONKEY_HARD:
				if (GetPlayerBotMonkeyArrival(mapIndex, outX, outY))
					outMap = mapIndex;
				break;
			default:
				if (GetPlayerBotFrontierArrival(mapIndex, outX, outY))
					outMap = mapIndex;
				break;
		}
	}

	bool RescuePlayerBotWithoutSectree(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return false;
		const long mapIndex = ch->GetMapIndex();
		if (ch->GetSectree() && SECTREE_MANAGER::instance().GetMap(mapIndex) != NULL)
			return false;
		if (state.dwNextSectreeRescueTime != 0 && dwNow < state.dwNextSectreeRescueTime)
			return true;
		state.dwNextSectreeRescueTime = dwNow + 30000;

		long homeMap = 0, homeX = 0, homeY = 0;
		GetPlayerBotHomePoint(mapIndex, homeMap, homeX, homeY);
		if (TransitionPlayerBotMap(ch, state, homeMap, homeX, homeY, dwNow, "sectree_rescue"))
		{
			sys_log(0, "PLAYERBOT_RESCUE: pid=%u name=%s had no sectree on map=%ld, moved to map=%ld (%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), mapIndex, homeMap, homeX, homeY);
		}
		return true;
	}

	void ClearPlayerBotShopSign(LPCHARACTER ch)
	{
		if (!ch)
			return;
		TPacketGCShopSign p;
		p.bHeader = HEADER_GC_SHOP_SIGN;
		p.dwVID = ch->GetVID();
		p.szSign[0] = '\0';
		ch->PacketAround(&p, sizeof(TPacketGCShopSign));
	}

	void ClosePlayerBotShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow,
			const char* reason)
	{
		if (!ch)
			return;
		const bool bHadShop = ch->GetMyShop() != NULL;
		if (bHadShop)
			ch->CloseMyShop();
		state.dwShopOpenedTime = 0;
		state.dwShopCloseTime = 0;
		state.vecShopOffers.clear();
		state.dwNextShopKeepTime = dwNow +
				number(PLAYERBOT_SHOP_REST_MIN, PLAYERBOT_SHOP_REST_MAX);
		if (bHadShop)
		{
			state.dwShopSignClearUntil = dwNow + PLAYERBOT_SHOP_SIGN_CLEAR_WINDOW;
			state.dwNextShopSignClearTime = dwNow;
			sys_log(0, "PLAYERBOT_SHOP: closed pid=%u name=%s reason=%s",
					ch->GetPlayerID(), ch->GetName(), reason);
		}
	}

	int FindPlayerBotShopSlot(const bool* grid, int height)
	{
		for (int row = 0; row + height <= PLAYERBOT_SHOP_GRID_ROWS; ++row)
			for (int col = 0; col < PLAYERBOT_SHOP_GRID_COLUMNS; ++col)
			{
				bool empty = true;
				for (int h = 0; h < height && empty; ++h)
					empty = !grid[(row + h) * PLAYERBOT_SHOP_GRID_COLUMNS + col];
				if (empty)
					return row * PLAYERBOT_SHOP_GRID_COLUMNS + col;
			}
		return -1;
	}

	void PutPlayerBotShopSlot(bool* grid, int slot, int height)
	{
		for (int h = 0; h < height; ++h)
			grid[slot + h * PLAYERBOT_SHOP_GRID_COLUMNS] = true;
	}

	LPITEM FindPlayerBotOfferItem(LPCHARACTER keeper, const TPlayerBotShopOffer& offer)
	{
		if (!keeper || offer.dwItemID == 0)
			return NULL;
		LPITEM item = ITEM_MANAGER::instance().Find(offer.dwItemID);
		if (!item || item->GetOwner() != keeper)
			return NULL;
		return item;
	}

	bool ManagePlayerBotShopLifetime(LPCHARACTER ch, TPlayerBotAIState& state,
			DWORD dwNow)
	{
		if (!ch || !ch->GetMyShop())
		{
			if (ch && !state.vecShopOffers.empty())
			{
				state.vecShopOffers.clear();
				state.dwShopSignClearUntil = dwNow + PLAYERBOT_SHOP_SIGN_CLEAR_WINDOW;
				state.dwNextShopSignClearTime = dwNow;
			}
			if (state.dwShopSignClearUntil != 0)
			{
				if (dwNow >= state.dwShopSignClearUntil)
				{
					state.dwShopSignClearUntil = 0;
					state.dwNextShopSignClearTime = 0;
				}
				else if (dwNow >= state.dwNextShopSignClearTime)
				{
					state.dwNextShopSignClearTime =
							dwNow + PLAYERBOT_SHOP_SIGN_CLEAR_INTERVAL;
					ClearPlayerBotShopSign(ch);
				}
			}
			return false;
		}

		if (state.dwShopCloseTime == 0)
			state.dwShopCloseTime =
					(state.dwShopOpenedTime != 0 ? state.dwShopOpenedTime : dwNow) +
					PLAYERBOT_SHOP_MIN_DURATION;

		bool bSoldOut = !state.vecShopOffers.empty() && ch->IsItemLoaded();
		if (bSoldOut)
		{
			for (size_t i = 0; i < state.vecShopOffers.size() && bSoldOut; ++i)
				if (FindPlayerBotOfferItem(ch, state.vecShopOffers[i]))
					bSoldOut = false;
		}

		long pitchX = 0, pitchY = 0;
		const bool onShopMap = GetPlayerBotShopCentre(ch->GetMapIndex(), pitchX, pitchY);
		const bool bOffPitch = ch->IsDead() || !onShopMap ||
				DISTANCE_APPROX(ch->GetX() - pitchX, ch->GetY() - pitchY) >
					PLAYERBOT_SHOP_RING_RADIUS + PLAYERBOT_MARKET_ARRIVE * 2;

		if (bSoldOut)
		{
			ClosePlayerBotShop(ch, state, dwNow, "sold_out");
			return false;
		}

		if (dwNow < state.dwShopCloseTime && !bOffPitch)
		{
			state.dwLastMeaningfulActivityTime = dwNow;
			state.lLastX = ch->GetX();
			state.lLastY = ch->GetY();
			SetPlayerBotAction(state, BOT_ACTION_STALL, dwNow);
			return true;
		}

		ClosePlayerBotShop(ch, state, dwNow, bOffPitch ? "off_pitch" : "expired");
		return false;
	}

	bool ManagePlayerBotPrivateShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;

		if (ch->GetMyShop())
			return true;

		if (!ShouldPlayerBotKeepShop(ch, state))
			return false;

		if (state.bVisitingShop || state.bVisitingBiologist || state.bVisitingStable)
			return false;
		if (state.dwNextShopKeepTime != 0 && dwNow < state.dwNextShopKeepTime)
			return false;

		const bool justFinishedInTown = state.dwNextShopCheckTime != 0 &&
				dwNow < state.dwNextShopCheckTime;

		long pitchX = 0, pitchY = 0;
		const long wantedMap = (number(1, 100) <= (int)PLAYERBOT_SHOP_M1_SHARE)
				? PLAYERBOT_MAP_CHUNJO_M1 : PLAYERBOT_MAP_CHUNJO_M2;
		if (ch->GetMapIndex() != wantedMap ||
				!GetPlayerBotShopCentre(ch->GetMapIndex(), pitchX, pitchY))
			return false;

		const bool alreadyAtPitch =
				DISTANCE_APPROX(ch->GetX() - pitchX, ch->GetY() - pitchY) <=
					PLAYERBOT_SHOP_RING_RADIUS + PLAYERBOT_MARKET_ARRIVE;
		if (!justFinishedInTown && !alreadyAtPitch)
			return false;

		std::vector<std::pair<int, WORD> > scored;
		CollectPlayerBotShopItems(ch, scored, IsPlayerBotStallKeeper(state));
		if (!IsPlayerBotStallWorthOpening(scored.size(),
				scored.empty() ? 0 : scored[0].first))
		{
			state.dwNextShopKeepTime = dwNow + (scored.empty()
					? number(300000, 600000) : number(120000, 240000));
			sys_log(0, "PLAYERBOT_SHOP: nothing to sell pid=%u name=%s lines=%u best=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)scored.size(),
					scored.empty() ? 0 : scored[0].first);
			return false;
		}

		long offsetX = 0, offsetY = 0;
		GetPlayerBotStableOffset(ch->GetPlayerID(), 0x4d4b5450U,
				PLAYERBOT_SHOP_RING_MIN, PLAYERBOT_SHOP_RING_RADIUS,
				offsetX, offsetY);
		const long stallX = pitchX + offsetX;
		const long stallY = pitchY + offsetY;

		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		if (!MovePlayerBotTownLeg(ch, state, dwNow, stallX, stallY,
				PLAYERBOT_MARKET_ARRIVE))
			return true;

		if (ch->IsRiding())
			ch->StopRiding();
		ch->HorseSummon(false);
		ch->SetVictim(NULL);
		ch->Stop();

		TShopItemTable table[PLAYERBOT_SHOP_MERCHANT_ITEMS];
		memset(table, 0, sizeof(table));
		std::vector<TPlayerBotShopOffer> offers;
		const BYTE tableLimit = IsPlayerBotStallKeeper(state)
				? PLAYERBOT_SHOP_MERCHANT_ITEMS : PLAYERBOT_SHOP_MAX_ITEMS;
		BYTE tableCount = 0;
		int bestScore = 0;
		const char* pszBestName = NULL;
		const char* pszWeapon30 = NULL;
		const char* pszPrecious = NULL;
		BYTE bPreciousRefine = 0;
		const char* apszMaterials[2] = { NULL, NULL };
		int iMaterials = 0;
		const char* pszBook = NULL;
		int iBooks = 0;
		int iScrap = 0;
		bool grid[PLAYERBOT_SHOP_GRID_CELLS];
		memset(grid, 0, sizeof(grid));
		for (size_t i = 0; i < scored.size() && tableCount < tableLimit; ++i)
		{
			const WORD cell = scored[i].second;
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->IsEquipped() || item->isLocked())
				continue;
			const TItemTable* proto = item->GetProto();
			if (!proto || IS_SET(proto->dwAntiFlags,
					ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP))
				continue;
			const int height = std::max<int>(1, std::min<int>(PLAYERBOT_SHOP_GRID_ROWS, item->GetSize()));
			const int slot = FindPlayerBotShopSlot(grid, height);
			if (slot < 0)
				continue;
			PutPlayerBotShopSlot(grid, slot, height);
			const DWORD price = GetPlayerBotShopAskingPrice(item);
			table[tableCount].vnum = item->GetVnum();
			table[tableCount].count = item->GetCount();
			table[tableCount].pos = TItemPos(INVENTORY, cell);
			table[tableCount].price = price;
			table[tableCount].display_pos = (BYTE)slot;

			TPlayerBotShopOffer offer;
			offer.dwVnum = item->GetVnum();
			offer.dwPrice = price;
			offer.bRefine = item->GetRefineLevel();
			offer.wCount = item->GetCount();
			offer.dwItemID = item->GetID();
			offer.bSlot = (BYTE)slot;
			offers.push_back(offer);
			if (scored[i].first > bestScore)
				bestScore = scored[i].first;
			++tableCount;

			const char* pszName = proto->szLocaleName;
			if (!pszBestName)
				pszBestName = pszName;
			if (IsPlayerBotSpecialLevel30Weapon(item))
				pszWeapon30 = pszWeapon30 ? pszWeapon30 : pszName;
			else if (item->GetRefineLevel() >= PLAYERBOT_PRECIOUS_REFINE)
			{
				if (!pszPrecious || item->GetRefineLevel() > bPreciousRefine)
				{
					pszPrecious = pszName;
					bPreciousRefine = item->GetRefineLevel();
				}
			}
			else if (IsPlayerBotTradeableMaterial(item))
			{
				if (iMaterials < 2)
					apszMaterials[iMaterials] = pszName;
				++iMaterials;
			}
			else if (item->GetType() == ITEM_SKILLBOOK)
			{
				pszBook = pszBook ? pszBook : pszName;
				++iBooks;
			}
			else if ((item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) &&
					item->GetRefineLevel() < PLAYERBOT_SHOP_MIN_GEAR_REFINE)
				++iScrap;
		}

		if (!IsPlayerBotStallWorthOpening(tableCount, bestScore))
		{
			state.dwNextShopKeepTime = dwNow + (tableCount == 0
					? number(300000, 600000) : number(120000, 240000));
			return false;
		}

		char sign[SHOP_SIGN_MAX_LEN + 1];
		{
			static const char* const s_apszPrefixes[] = {
				"", "ACIL YANG: ", "GEL BAK: ", "KAPATIOZ: ", "COZULMEDIK: ", "EN UCUZ: ", "SATIYORUM: "
			};
			const size_t prefixCount = sizeof(s_apszPrefixes) / sizeof(s_apszPrefixes[0]);
			const char* pszPrefix = s_apszPrefixes[(ch->GetPlayerID() * 2654435761U >> 8) % prefixCount];
			char body[SHOP_SIGN_MAX_LEN * 2 + 1];
			if (pszWeapon30)
				snprintf(body, sizeof(body), "30Lvl Silah: %s", pszWeapon30);
			else if (pszPrecious)
				snprintf(body, sizeof(body), "%s", pszPrecious);
			else if (iMaterials >= 2)
				snprintf(body, sizeof(body), "%s, %s ucuz", apszMaterials[0], apszMaterials[1]);
			else if (iBooks > 1 && iBooks >= tableCount / 2)
				snprintf(body, sizeof(body), "BKlar: %s ve digerleri", pszBook);
			else if (iBooks == 1 && tableCount == 1)
				snprintf(body, sizeof(body), "BK: %s gel cek", pszBook);
			else if (iScrap > 0 && iScrap >= tableCount / 2)
				snprintf(body, sizeof(body), "Yakmalik Item +0..+3");
			else if (pszBestName && tableCount > 1)
				snprintf(body, sizeof(body), "%s ve karisik", pszBestName);
			else
				snprintf(body, sizeof(body), "%s", pszBestName ? pszBestName : ch->GetName());

			if (strlen(pszPrefix) + strlen(body) <= SHOP_SIGN_MAX_LEN)
				snprintf(sign, sizeof(sign), "%s%s", pszPrefix, body);
			else
				snprintf(sign, sizeof(sign), "%s", body);
		}

		if (ch->CountSpecifyItem(71049) > 0)
			return false;
		if (ch->CountSpecifyItem(50200) == 0)
		{
			if (ch->GetEmptyInventory(1) < 0)
			{
				sys_log(0, "PLAYERBOT_SHOP: no room for bundle pid=%u name=%s lines=%u",
						ch->GetPlayerID(), ch->GetName(), (unsigned int)tableCount);
				return false;
			}
			if (ch->GetGold() >= PLAYERBOT_SHOP_BUNDLE_PRICE)
				ch->PointChange(POINT_GOLD, -(int)PLAYERBOT_SHOP_BUNDLE_PRICE);
			ch->AutoGiveItem(50200, 1);
		}

		ch->OpenMyShop(sign, table, tableCount);
		if (!ch->GetMyShop())
		{
			quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
			LPITEM first = ch->GetItem(table[0].pos);
			const TItemTable* rp = first ? first->GetProto() : NULL;
			sys_log(0, "PLAYERBOT_SHOP: refused pid=%u items=%u poly=%d quest=%d vnum=%u anti=%u equipped=%d locked=%d viaPos=%d sign=%d gold=%d",
					ch->GetPlayerID(), (unsigned int)tableCount,
					ch->IsPolymorphed() ? 1 : 0,
					(pc && pc->IsRunning()) ? 1 : 0, table[0].vnum,
					rp ? rp->dwAntiFlags : 0, first && first->IsEquipped() ? 1 : 0,
					first && first->isLocked() ? 1 : 0, first ? 1 : 0,
					(int)strlen(sign), (int)(ch->GetGold() / 1000));
			ClearPlayerBotShopSign(ch);
			state.dwNextShopKeepTime = dwNow + number(60000, 180000);
			return false;
		}

		ch->RemoveGoodAffect();

		state.dwShopOpenedTime = dwNow;
		state.dwShopCloseTime = dwNow + (IsPlayerBotMerchant(state)
				? number(PLAYERBOT_SHOP_MERCHANT_MIN_DURATION,
						PLAYERBOT_SHOP_MERCHANT_MAX_DURATION)
				: number(PLAYERBOT_SHOP_MIN_DURATION, PLAYERBOT_SHOP_MAX_DURATION));
		state.vecShopOffers = offers;
		for (size_t i = 0; i < offers.size(); ++i)
			AddPlayerBotMarketSupply(offers[i].dwVnum, offers[i].wCount);
		sys_log(0, "PLAYERBOT_SHOP: opened pid=%u name=%s items=%u first_vnum=%u first_price=%u pos=(%ld,%ld) sign=\"%s\"",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)tableCount,
				offers[0].dwVnum, offers[0].dwPrice, ch->GetX(), ch->GetY(), sign);

		if (bestScore >= PLAYERBOT_SHOP_PRIZE_SCORE && pszBestName)
			AnnouncePlayerBotStall(ch, pszBestName);
		return true;
	}

	bool MovePlayerBotTownLeg(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow,
			long goalX, long goalY, int arrivalDistance)
	{
		if (DISTANCE_APPROX(ch->GetX() - goalX, ch->GetY() - goalY) <= arrivalDistance)
		{
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "town_interaction");
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			ClearPlayerBotRoute(state, true);
			return true;
		}

		const int snapCells = std::max(2, std::min(16, arrivalDistance / 100));
		const bool moveAccepted = MovePlayerBot(ch, goalX, goalY, dwNow,
				snapCells, true, true);
		if (!moveAccepted && state.bStuckCounter >= 6)
		{
			sys_err("PLAYERBOT_TOWN: route failed pid=%u name=%s phase=%u from=(%ld,%ld) to=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)state.bTownVisitPhase,
					ch->GetX(), ch->GetY(), goalX, goalY);

			CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
			PIXEL_POSITION safe;
			if (navigation.Init(ch->GetMapIndex()) &&
					navigation.FindNearestWalkableWorld(goalX, goalY, 16, safe,
							ch->GetPlayerID() ^ (DWORD)state.bTownVisitPhase))
			{
				ClearPlayerBotRoute(state, true);
				state.bStuckCounter = 0;
				ch->Show(ch->GetMapIndex(), safe.x, safe.y, 0);
				ch->Stop();
				ch->SendMovePacket(FUNC_MOVE, 0, safe.x, safe.y, 0, dwNow);
				sys_err("PLAYERBOT_TOWN: service rescue pid=%u name=%s phase=%u to=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), (unsigned int)state.bTownVisitPhase,
						safe.x, safe.y);
			}
			else
				FinishPlayerBotTownVisit(ch, state, dwNow, false);
		}
		return false;
	}

	bool MovePlayerBotAcrossTownGate(LPCHARACTER ch, TPlayerBotAIState& state,
			DWORD dwNow, long goalY)
	{
		if (!ch)
			return false;
		const int distance = DISTANCE_APPROX(
				ch->GetX() - PLAYERBOT_TOWN_GATE_X, ch->GetY() - goalY);
		if (distance <= 450)
		{
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			ClearPlayerBotRoute(state, true);
			return true;
		}

		if (distance <= 1200)
		{
			ClearPlayerBotRoute(state, true);
			ch->SetRotationToXY(PLAYERBOT_TOWN_GATE_X, goalY);
			if (ch->Goto(PLAYERBOT_TOWN_GATE_X, goalY))
			{
				ch->SendMovePacket(FUNC_MOVE, 0, PLAYERBOT_TOWN_GATE_X, goalY,
						ch->GetCurrentMoveDuration(), dwNow);
				return false;
			}
		}

		return MovePlayerBotTownLeg(ch, state, dwNow,
				PLAYERBOT_TOWN_GATE_X, goalY, 450);
	}

	bool HandlePlayerBotTownVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !state.bVisitingShop ||
				(ch->GetMapIndex() != PLAYERBOT_MAP_CHUNJO_M1 &&
				 ch->GetMapIndex() != PLAYERBOT_MAP_CHUNJO_M2))
			return false;
		const bool inM2 = ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M2;
		const long weaponNpcX = inM2 ? PLAYERBOT_M2_WEAPON_MERCHANT_X : PLAYERBOT_WEAPON_MERCHANT_X;
		const long weaponNpcY = inM2 ? PLAYERBOT_M2_WEAPON_MERCHANT_Y : PLAYERBOT_WEAPON_MERCHANT_Y;
		const long armorNpcX = inM2 ? PLAYERBOT_M2_ARMOR_MERCHANT_X : PLAYERBOT_ARMOR_MERCHANT_X;
		const long armorNpcY = inM2 ? PLAYERBOT_M2_ARMOR_MERCHANT_Y : PLAYERBOT_ARMOR_MERCHANT_Y;
		const long miscNpcX = inM2 ? PLAYERBOT_M2_MISC_MERCHANT_X : PLAYERBOT_MISC_MERCHANT_X;
		const long miscNpcY = inM2 ? PLAYERBOT_M2_MISC_MERCHANT_Y : PLAYERBOT_MISC_MERCHANT_Y;
		const long blacksmithNpcX = inM2 ? PLAYERBOT_M2_BLACKSMITH_X : PLAYERBOT_BLACKSMITH_X;
		const long blacksmithNpcY = inM2 ? PLAYERBOT_M2_BLACKSMITH_Y : PLAYERBOT_BLACKSMITH_Y;

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_TRAINER ||
				state.bTownVisitPhase == BOT_TOWN_PHASE_TRAINER_WAIT)
			SetPlayerBotAction(state, BOT_ACTION_TRAIN, dwNow);
		else if (state.bTownVisitPhase == BOT_TOWN_PHASE_BLACKSMITH ||
				state.bTownVisitPhase == BOT_TOWN_PHASE_BLACKSMITH_WAIT)
			SetPlayerBotAction(state, BOT_ACTION_REFINE, dwNow);
		else if (state.bTownVisitPhase == BOT_TOWN_PHASE_WEAPON_WAIT ||
				state.bTownVisitPhase == BOT_TOWN_PHASE_ARMOR_WAIT ||
				state.bTownVisitPhase == BOT_TOWN_PHASE_MISC_WAIT)
			SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		else
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);

		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
		{
			state.bTownVisitPhase = inM2
					? GetPlayerBotFirstDirectTownPhase(state)
					: GetPlayerBotFirstExteriorTownPhase(state);
			if (!inM2 && state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
				state.bTownVisitPhase = BOT_TOWN_PHASE_GATE_IN;
			if (inM2 && state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
			{
				FinishPlayerBotTownVisit(ch, state, dwNow, true);
				return true;
			}
		}

		const BYTE wantedGroup = (ch->GetPlayerID() % 2 == 0) ? 1 : 2;
		const long trainerGroup1X[4] = { 62300, 63100, 64500, 65300 };
		const long trainerGroup2X[4] = { 62700, 63500, 64900, 65700 };
		const BYTE trainerJob = std::min<BYTE>(ch->GetJob(), JOB_SHAMAN);
		const long trainerNpcX = wantedGroup == 1
				? trainerGroup1X[trainerJob] : trainerGroup2X[trainerJob];
		const long trainerNpcY = ch->GetJob() <= JOB_WARRIOR ? 161800 : 161900;
		long trainerX = 0, trainerY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), trainerNpcX, trainerNpcY,
				0x54524149U, trainerX, trainerY);

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_TRAINER)
		{
			SetPlayerBotAction(state, BOT_ACTION_TRAIN, dwNow);
			if (MovePlayerBotTownLeg(ch, state, dwNow, trainerX, trainerY, 550))
			{
				if (ChoosePlayerBotSkillGroup(ch))
					state.bTownNeedTrainer = false;
				state.dwTownWaitUntil = dwNow + number(
						PLAYERBOT_TRAINER_WAIT_MIN, PLAYERBOT_TRAINER_WAIT_MAX);
				state.bTownVisitPhase = BOT_TOWN_PHASE_TRAINER_WAIT;
				sys_log(0, "PLAYERBOT_TOWN: trainer visit pid=%u name=%s job=%u group=%u wait_ms=%u pos=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), ch->GetJob(), ch->GetSkillGroup(),
						state.dwTownWaitUntil - dwNow, ch->GetX(), ch->GetY());
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_TRAINER_WAIT)
		{
			SetPlayerBotAction(state, BOT_ACTION_TRAIN, dwNow);
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			if (dwNow >= state.dwTownWaitUntil)
			{
				state.bTownVisitPhase = state.bTownNeedWeaponMerchant
						? BOT_TOWN_PHASE_WEAPON_MERCHANT
						: (state.bTownNeedArmorMerchant ? BOT_TOWN_PHASE_ARMOR_MERCHANT
							: ((state.bTownNeedMisc || state.bTownNeedBlacksmith)
								? BOT_TOWN_PHASE_GATE_IN : BOT_TOWN_PHASE_NONE));
				state.dwTownWaitUntil = 0;
				ClearPlayerBotRoute(state, true);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					FinishPlayerBotTownVisit(ch, state, dwNow, true);
			}
			return true;
		}

		long weaponMerchantX = 0, weaponMerchantY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), weaponNpcX,
				weaponNpcY, 0x57454150U, weaponMerchantX, weaponMerchantY);
		if (state.bTownVisitPhase == BOT_TOWN_PHASE_WEAPON_MERCHANT)
		{
			if (MovePlayerBotTownLeg(ch, state, dwNow,
					weaponMerchantX, weaponMerchantY, 850))
			{
				ManagePlayerBotWeaponMerchant(ch);
				ManagePlayerBotEquipment(ch, state, dwNow);
				if (!ch->GetWear(WEAR_WEAPON))
				{
					state.dwEmergencyScavengeUntil = dwNow + 120000;
					sys_log(0, "PLAYERBOT_GEAR: emergency scavenging armed pid=%u name=%s until=%u gold=%lld",
							ch->GetPlayerID(), ch->GetName(), state.dwEmergencyScavengeUntil,
							(long long)ch->GetGold());
				}
				state.bTownNeedBlacksmith = state.bTownNeedBlacksmith ||
						HasPlayerBotRefineOpportunity(ch);
				state.bTownNeedWeaponMerchant = false;
				state.dwTownWaitUntil = dwNow + number(
						PLAYERBOT_MERCHANT_WAIT_MIN, PLAYERBOT_MERCHANT_WAIT_MAX);
				state.bTownVisitPhase = BOT_TOWN_PHASE_WEAPON_WAIT;
				sys_log(0, "PLAYERBOT_TOWN: weapon merchant visit pid=%u name=%s wait_ms=%u pos=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), state.dwTownWaitUntil - dwNow,
						ch->GetX(), ch->GetY());
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_WEAPON_WAIT)
		{
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			if (dwNow >= state.dwTownWaitUntil)
			{
				state.bTownVisitPhase = state.bTownNeedArmorMerchant
						? BOT_TOWN_PHASE_ARMOR_MERCHANT
						: (inM2 ? GetPlayerBotFirstDirectTownPhase(state)
							: ((state.bTownNeedMisc || state.bTownNeedBlacksmith)
								? BOT_TOWN_PHASE_GATE_IN : BOT_TOWN_PHASE_NONE));
				state.dwTownWaitUntil = 0;
				ClearPlayerBotRoute(state, true);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					FinishPlayerBotTownVisit(ch, state, dwNow, true);
			}
			return true;
		}

		long armorMerchantX = 0, armorMerchantY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), armorNpcX,
				armorNpcY, 0x41524d52U, armorMerchantX, armorMerchantY);
		if (state.bTownVisitPhase == BOT_TOWN_PHASE_ARMOR_MERCHANT)
		{
			if (MovePlayerBotTownLeg(ch, state, dwNow,
					armorMerchantX, armorMerchantY, 850))
			{
				ManagePlayerBotArmorMerchant(ch);
				ManagePlayerBotEquipment(ch, state, dwNow);
				state.bTownNeedBlacksmith = state.bTownNeedBlacksmith ||
						HasPlayerBotRefineOpportunity(ch);
				state.bTownNeedArmorMerchant = false;
				state.dwTownWaitUntil = dwNow + number(
						PLAYERBOT_MERCHANT_WAIT_MIN, PLAYERBOT_MERCHANT_WAIT_MAX);
				state.bTownVisitPhase = BOT_TOWN_PHASE_ARMOR_WAIT;
				sys_log(0, "PLAYERBOT_TOWN: armor merchant visit pid=%u name=%s wait_ms=%u pos=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), state.dwTownWaitUntil - dwNow,
						ch->GetX(), ch->GetY());
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_ARMOR_WAIT)
		{
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			if (dwNow >= state.dwTownWaitUntil)
			{
				state.bTownVisitPhase = inM2
						? GetPlayerBotFirstDirectTownPhase(state)
						: ((state.bTownNeedMisc || state.bTownNeedBlacksmith)
							? BOT_TOWN_PHASE_GATE_IN : BOT_TOWN_PHASE_NONE);
				state.dwTownWaitUntil = 0;
				ClearPlayerBotRoute(state, true);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					FinishPlayerBotTownVisit(ch, state, dwNow, true);
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_GATE_IN)
		{
			if (inM2)
			{
				FinishPlayerBotTownVisit(ch, state, dwNow, false);
				return true;
			}
			if (MovePlayerBotTownLeg(ch, state, dwNow,
					PLAYERBOT_TOWN_GATE_X, PLAYERBOT_TOWN_GATE_OUTSIDE_Y, 1000))
				state.bTownVisitPhase = BOT_TOWN_PHASE_GATE_CROSS_IN;
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_GATE_CROSS_IN)
		{
			if (MovePlayerBotAcrossTownGate(ch, state, dwNow,
					PLAYERBOT_TOWN_GATE_INSIDE_Y))
			{
				state.bTownVisitPhase = GetPlayerBotFirstInteriorTownPhase(state);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					state.bTownVisitPhase = BOT_TOWN_PHASE_GATE_OUT;
			}
			return true;
		}

		long merchantX = 0, merchantY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), miscNpcX,
				miscNpcY, 0x4d495343U, merchantX, merchantY);
		if (state.bTownVisitPhase == BOT_TOWN_PHASE_MISC_MERCHANT)
		{
			if (MovePlayerBotTownLeg(ch, state, dwNow, merchantX, merchantY, 650))
			{
				ManagePlayerBotMiscMerchant(ch);
				state.bTownNeedMisc = false;
				state.dwTownWaitUntil = dwNow + number(
						PLAYERBOT_MERCHANT_WAIT_MIN, PLAYERBOT_MERCHANT_WAIT_MAX);
				state.bTownVisitPhase = BOT_TOWN_PHASE_MISC_WAIT;
				sys_log(0, "PLAYERBOT_TOWN: misc merchant visit pid=%u name=%s wait_ms=%u pos=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), state.dwTownWaitUntil - dwNow,
						ch->GetX(), ch->GetY());
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_MISC_WAIT)
		{
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			if (dwNow >= state.dwTownWaitUntil)
			{
				state.bTownVisitPhase = state.bTownNeedBlacksmith
						? BOT_TOWN_PHASE_BLACKSMITH
						: (inM2 ? BOT_TOWN_PHASE_NONE : BOT_TOWN_PHASE_GATE_OUT);
				state.dwTownWaitUntil = 0;
				ClearPlayerBotRoute(state, true);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					FinishPlayerBotTownVisit(ch, state, dwNow, true);
			}
			return true;
		}

		long blacksmithX = 0, blacksmithY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), blacksmithNpcX,
				blacksmithNpcY, 0x4b4f574cU, blacksmithX, blacksmithY);
		blacksmithX = blacksmithNpcX + (blacksmithX - blacksmithNpcX) / 2;
		blacksmithY = blacksmithNpcY + (blacksmithY - blacksmithNpcY) / 2;
		if (state.bTownVisitPhase == BOT_TOWN_PHASE_BLACKSMITH)
		{
			if (MovePlayerBotTownLeg(ch, state, dwNow, blacksmithX, blacksmithY, 500))
			{
				ManagePlayerBotRefining(ch, state, dwNow);
				ManagePlayerBotBonusReroll(ch, state, dwNow);
				if (!HasPlayerBotRefineOpportunity(ch))
					RestorePlayerBotEquipmentAfterRefining(ch, state, dwNow);
				state.bTownNeedBlacksmith = false;
				state.dwTownWaitUntil = dwNow + number(
						PLAYERBOT_BLACKSMITH_WAIT_MIN, PLAYERBOT_BLACKSMITH_WAIT_MAX);
				state.bTownVisitPhase = BOT_TOWN_PHASE_BLACKSMITH_WAIT;
				sys_log(0, "PLAYERBOT_TOWN: blacksmith visit pid=%u name=%s wait_ms=%u pos=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), state.dwTownWaitUntil - dwNow,
						ch->GetX(), ch->GetY());
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_BLACKSMITH_WAIT)
		{
			ch->Stop();
			ch->SetPosition(POS_STANDING);
			ManagePlayerBotRefining(ch, state, dwNow);
			ManagePlayerBotBonusReroll(ch, state, dwNow);
			if (!HasPlayerBotRefineOpportunity(ch))
				RestorePlayerBotEquipmentAfterRefining(ch, state, dwNow);
			if (dwNow >= state.dwTownWaitUntil)
			{
				RestorePlayerBotEquipmentAfterRefining(ch, state, dwNow);
				state.bTownVisitPhase = inM2
						? BOT_TOWN_PHASE_NONE : BOT_TOWN_PHASE_GATE_OUT;
				state.dwTownWaitUntil = 0;
				ClearPlayerBotRoute(state, true);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					FinishPlayerBotTownVisit(ch, state, dwNow, true);
			}
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_GATE_OUT)
		{
			if (inM2)
			{
				FinishPlayerBotTownVisit(ch, state, dwNow, false);
				return true;
			}
			if (MovePlayerBotTownLeg(ch, state, dwNow,
					PLAYERBOT_TOWN_GATE_X, PLAYERBOT_TOWN_GATE_INSIDE_Y, 1000))
				state.bTownVisitPhase = BOT_TOWN_PHASE_GATE_CROSS_OUT;
			return true;
		}

		if (state.bTownVisitPhase == BOT_TOWN_PHASE_GATE_CROSS_OUT)
		{
			if (MovePlayerBotAcrossTownGate(ch, state, dwNow,
					PLAYERBOT_TOWN_GATE_OUTSIDE_Y))
			{
				state.bTownVisitPhase = GetPlayerBotFirstExteriorTownPhase(state);
				ClearPlayerBotRoute(state, true);
				if (state.bTownVisitPhase == BOT_TOWN_PHASE_NONE)
					FinishPlayerBotTownVisit(ch, state, dwNow, true);
			}
			return true;
		}

		FinishPlayerBotTownVisit(ch, state, dwNow, false);
		return true;
	}
}

#endif