#ifndef __INC_METIN2_PLAYERBOT_ECONOMY_H__
#define __INC_METIN2_PLAYERBOT_ECONOMY_H__

// What a bot does with money and with the contents of its bag: deciding what is
// junk, selling it to the right merchant, upgrading gear at the blacksmith,
// rerolling bonus lines, and running a market stall of its own.
//
// The one rule worth knowing before changing anything here: IsPlayerBotJunkItem
// **defaults to true**. Anything worth keeping needs an explicit exemption, or
// bots vendor it on their next trip to town.
//
// An implementation fragment in the sense playerbot_types.h describes: it
// defines objects, relies on the engine headers playerbot_manager.cpp includes
// above it, and reopens the same anonymous namespace. Include it exactly once,
// after playerbot_gear.h - it prices and sells what that file decides to wear.

namespace
{
	// Demirci basarisi duyurusu (2010 TR Metin2 usulu bagirma)
	void BroadcastPlayerBotRefineSuccess(LPCHARACTER ch, LPITEM item, int newPlus)
	{
		if (!ch || !item || newPlus < 7)
			return;
		if (ch->GetMyShop())
			return;

		static DWORD s_dwLastShoutTime = 0;
		const DWORD dwNow = get_dword_time();
		if (s_dwLastShoutTime != 0 && dwNow < s_dwLastShoutTime + 180000)
			return;
		if (number(1, 100) > 45)
			return;

		static const char* kPlus7[] = {
			"%s +7 oldu sonunda, demirci bu sefer yakmadi",
			"hadi bakalim %s +7 gecti, fena durmadi",
			"%s tekte +7 gecti sansa bak",
			"demirci acimadi bugun: %s +7",
			"%s +7 oldu beyler gideri var mi",
			"+7 ye salladim gecti: %s"
		};
		static const char* kPlus8[] = {
			"%s +8 OLDU! elim ayagim titriyor valla",
			"yuregim agzima geldi ama %s +8 gecti!",
			"%s +8 oldu beyler, +9 denesem mi yakar mi",
			"helal be demirciye guvendik: %s +8!",
			"%s +8 temiz gecti, sirada ne var",
			"sans benden yana bugun, %s +8 hayirli olsun"
		};
		static const char* kPlus9[] = {
			"%s +9 BASILDI LAN OHA GECMEZ DIYODUM!!!",
			"%s +9 BEYLER TEKLIFLERI ALAYIM PM ATIN!",
			"ANANI AVRADINI %s +9 OLDU LAN WTT VAR MI?!",
			"koy agladi be %s +9 gecti, kurban olayim demirciye!",
			"%s +9 OLDU OYUNU BIRAKMIYORUM DEVAM!",
			"ALLAAAH %s +9! SERVERIN EN IYISI GEL PM",
			"%s +9 gecti ulan helal be, artik rahat uyurum!"
		};

		const char** pool = kPlus7;
		size_t poolSize = sizeof(kPlus7) / sizeof(kPlus7[0]);
		if (newPlus >= 9)
		{
			pool = kPlus9;
			poolSize = sizeof(kPlus9) / sizeof(kPlus9[0]);
		}
		else if (newPlus == 8)
		{
			pool = kPlus8;
			poolSize = sizeof(kPlus8) / sizeof(kPlus8[0]);
		}

		char msg[CHAT_MAX_LEN + 1];
		char body[CHAT_MAX_LEN + 1];
		snprintf(body, sizeof(body), pool[number(0, (int)poolSize - 1)], item->GetName());
		snprintf(msg, sizeof(msg), "%s : %s", ch->GetName(), body);

		s_dwLastShoutTime = dwNow;
		SendShout(msg, ch->GetEmpire());
		sys_log(0, "PLAYERBOT_SHOUT: pid=%u plus=%d text=%s",
				ch->GetPlayerID(), newPlus, msg);
	}

	PIXEL_POSITION GetPlayerBotGeneralStorePos(long mapIndex)
	{
		PIXEL_POSITION pos;
		pos.x = 0;
		pos.y = 0;
		pos.z = 0;

		if (mapIndex == 21 || mapIndex == 23) // Chunjo M1 / M3
		{
			pos.x = 59000;
			pos.y = 68900;
		}
		else if (mapIndex == 1 || mapIndex == 3) // Shinsoo M1 / M3
		{
			pos.x = 67800;
			pos.y = 56500;
		}
		else if (mapIndex == 41 || mapIndex == 43) // Jinno M1 / M3
		{
			pos.x = 38300;
			pos.y = 69300;
		}

		return pos;
	}

	DWORD GetPlayerBotSkillBookSkillVnum(LPITEM item)
	{
		if (!item || item->GetType() != ITEM_SKILLBOOK)
			return 0;
		return item->GetVnum() == 50300 ? (DWORD)item->GetSocket(0) : (DWORD)item->GetValue(0);
	}

	bool IsPlayerBotOwnSkill(LPCHARACTER ch, DWORD skillVnum)
	{
		if (!ch || skillVnum == 0 || ch->GetSkillGroup() == 0)
			return false;
		const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
		for (BYTE i = 0; i < build.bSkillCount; ++i)
			if (build.dwSkills[i] == skillVnum)
				return true;
		return false;
	}

	bool PlayerBotIsShortOfRefineMaterial(LPCHARACTER ch, DWORD materialVnum)
	{
		if (!ch)
			return false;

		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};
		std::vector<LPITEM> gear;
		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]); ++i)
			if (ch->GetWear(wearSlots[i]))
				gear.push_back(ch->GetWear(wearSlots[i]));
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM candidate = ch->GetInventoryItem(cell);
			if (IsPlayerBotEquipmentCandidate(ch, candidate))
				gear.push_back(candidate);
		}

		for (size_t i = 0; i < gear.size(); ++i)
		{
			LPITEM item = gear[i];
			if (!item || item->GetRefinedVnum() == 0 ||
					item->GetRefineLevel() >= GetPlayerBotRefineTarget(ch, item))
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(item->GetRefineSet());
			if (!recipe)
				continue;
			for (int m = 0; m < recipe->material_count; ++m)
			{
				const DWORD vnum = recipe->materials[m].vnum;
				if (vnum == 0 || recipe->materials[m].count == 0)
					continue;
				if (materialVnum != 0 && vnum != materialVnum)
					continue;
				if (ch->CountSpecifyItem(vnum) < recipe->materials[m].count * 2)
					return true;
			}
		}
		return false;
	}

	bool PlayerBotNeedsRefineMaterial(LPCHARACTER ch, DWORD materialVnum)
	{
		return materialVnum != 0 &&
				PlayerBotIsShortOfRefineMaterial(ch, materialVnum);
	}

	bool PlayerBotNeedsAnyRefineMaterial(LPCHARACTER ch)
	{
		return PlayerBotIsShortOfRefineMaterial(ch, 0);
	}

	void CollectPlayerBotWantedMaterials(LPCHARACTER ch, std::set<DWORD>& out)
	{
		out.clear();
		if (!ch || !ch->IsItemLoaded())
			return;
		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};
		std::vector<LPITEM> gear;
		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]); ++i)
			if (ch->GetWear(wearSlots[i]))
				gear.push_back(ch->GetWear(wearSlots[i]));
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM candidate = ch->GetInventoryItem(cell);
			if (IsPlayerBotEquipmentCandidate(ch, candidate))
				gear.push_back(candidate);
		}
		for (size_t i = 0; i < gear.size(); ++i)
		{
			LPITEM item = gear[i];
			if (!item || item->GetRefinedVnum() == 0 ||
					item->GetRefineLevel() >= GetPlayerBotRefineTarget(ch, item))
				continue;
			const TRefineTable* recipe =
					CRefineManager::instance().GetRefineRecipe(item->GetRefineSet());
			if (!recipe)
				continue;
			for (int m = 0; m < recipe->material_count; ++m)
			{
				const DWORD vnum = recipe->materials[m].vnum;
				if (vnum == 0 || recipe->materials[m].count == 0)
					continue;
				if (ch->CountSpecifyItem(vnum) < recipe->materials[m].count * 2)
					out.insert(vnum);
			}
		}
	}

	const std::set<DWORD>& GetPlayerBotRefineMaterialVnums()
	{
		static std::set<DWORD> s_materials;
		static bool s_loaded = false;
		if (!s_loaded)
		{
			s_loaded = true;
			for (DWORD id = 1; id <= PLAYERBOT_REFINE_RECIPE_MAX_ID; ++id)
			{
				const TRefineTable* recipe =
						CRefineManager::instance().GetRefineRecipe(id);
				if (!recipe)
					continue;
				for (int m = 0; m < recipe->material_count; ++m)
					if (recipe->materials[m].vnum != 0)
						s_materials.insert(recipe->materials[m].vnum);
			}
			sys_log(0, "PLAYERBOT_ECONOMY: %u refine materials are worth a counter slot",
					(unsigned int)s_materials.size());
		}
		return s_materials;
	}

	bool IsPlayerBotFishingKeepsake(DWORD vnum)
	{
		return vnum == PLAYERBOT_SHELLFISH_VNUM ||
				(vnum >= PLAYERBOT_PEARL_FIRST_VNUM && vnum <= PLAYERBOT_PEARL_LAST_VNUM);
	}

	bool IsPlayerBotTradeableMaterial(LPITEM item)
	{
		if (!item)
			return false;
		const std::set<DWORD>& materials = GetPlayerBotRefineMaterialVnums();
		return materials.find(item->GetVnum()) != materials.end();
	}

	bool IsPlayerBotSurplusMaterial(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotTradeableMaterial(item))
			return true;

		size_t ahead = 0;
		const WORD ownCell = item->GetCell();
		for (WORD cell = 0; cell < ownCell && cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other != item && IsPlayerBotTradeableMaterial(other) &&
					!IsPlayerBotFishingKeepsake(other->GetVnum()) &&
					++ahead >= PLAYERBOT_MATERIAL_STOCK_SLOTS)
				return true;
		}
		return false;
	}

	int CountPlayerBotFreeInventoryCells(LPCHARACTER ch)
	{
		int free = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
			if (!ch->GetInventoryItem(cell))
				++free;
		return free;
	}

	int CountPlayerBotSkillBooksAhead(LPCHARACTER ch, LPITEM item, DWORD skillVnum)
	{
		int ahead = 0;
		const WORD ownCell = item->GetCell();
		for (WORD cell = 0; cell < ownCell && cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other != item && other->GetType() == ITEM_SKILLBOOK &&
					GetPlayerBotSkillBookSkillVnum(other) == skillVnum)
				++ahead;
		}
		return ahead;
	}

	bool PlayerBotHasTreasureKeyFor(LPCHARACTER ch, LPITEM box)
	{
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM key = ch->GetInventoryItem(cell);
			if (key && key->GetType() == ITEM_TREASURE_KEY && key->GetValue(0) == box->GetValue(0))
				return true;
		}
		return false;
	}

	bool IsPlayerBotJunkItem(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->IsEquipped() || item->isLocked())
			return false;

		if (IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_SELL))
			return false;

		const DWORD vnum = item->GetVnum();

		if (IsPlayerBotSpecialLevel30Weapon(item))
			return false;

		if (item->GetRefineLevel() >= PLAYERBOT_PRECIOUS_REFINE)
			return false;

		if ((item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) &&
				IsPlayerBotScrapKeeper(ch->GetPlayerID()) &&
				CountPlayerBotFreeInventoryCells(ch) > PLAYERBOT_SCRAP_KEEP_FREE_CELLS)
			return false;

		if (vnum == PLAYERBOT_HORSE_MEDAL_VNUM ||
				vnum == PLAYERBOT_BATTLE_HORSE_BOOK_VNUM ||
				(vnum >= 50701 && vnum <= 50706) ||
				vnum == PLAYERBOT_ORC_TOOTH_VNUM || vnum == PLAYERBOT_JINUNGGYI_STONE_VNUM)
			return false;

		if (vnum == PLAYERBOT_MOONLIGHT_CHEST_VNUM)
			return false;

		if (item->GetType() == ITEM_TREASURE_BOX)
			return CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_BAG_PRESSURE_FREE_CELLS &&
					!PlayerBotHasTreasureKeyFor(ch, item);
		if (item->GetType() == ITEM_TREASURE_KEY ||
				item->GetType() == ITEM_GIFTBOX || vnum == PLAYERBOT_SKILL_FORGET_SCROLL_VNUM)
			return false;

		if (item->GetType() == ITEM_METIN)
			return false;

		if (item->GetType() == ITEM_ROD || vnum == PLAYERBOT_FISHING_BAIT_VNUM ||
				vnum == PLAYERBOT_SHELLFISH_VNUM || vnum == PLAYERBOT_CAMPFIRE_VNUM ||
				(vnum >= PLAYERBOT_PEARL_FIRST_VNUM && vnum <= PLAYERBOT_PEARL_LAST_VNUM))
			return false;
		// Hair dye. The merchant pays nothing for it and a player will: it is
		// the only way to change a character's colour for good, and the anglers
		// pull it out of the water by the handful.
		if (IsPlayerBotHairDye(vnum))
			return false;
		// A dead fish waits for the campfire at the end of the next session, as
		// long as the bot has the wood for one; a grilled fish is a potion.
		if (item->GetType() == ITEM_FISH && item->GetSubType() == FISH_DEAD &&
				ch->CountSpecifyItem(PLAYERBOT_CAMPFIRE_VNUM) > 0)
			return false;
		if (vnum >= PLAYERBOT_GRILLED_FISH_FIRST_VNUM && vnum <= PLAYERBOT_GRILLED_FISH_LAST_VNUM)
			return false;

		if (item->GetType() == ITEM_WEAPON && item->GetSubType() == WEAPON_ARROW)
		{
			const bool isOrWillBeArcher = ch->GetJob() == JOB_ASSASSIN &&
					(ch->GetSkillGroup() == 2 ||
					 (ch->GetSkillGroup() == 0 && (ch->GetPlayerID() % 2) != 0));
			return !isOrWillBeArcher;
		}

		if (item->GetType() == ITEM_SKILLBOOK)
		{
			if (GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_METIN_DROPPER)
				return false;
			if (ch->GetSkillGroup() == 0)
				return false;
			const DWORD skillVnum = GetPlayerBotSkillBookSkillVnum(item);
			if (!IsPlayerBotOwnSkill(ch, skillVnum))
				return true;
			return CountPlayerBotSkillBooksAhead(ch, item, skillVnum) >= PLAYERBOT_BOOK_KEEP_PER_SKILL;
		}

		if (vnum == 27051 || vnum == 27001 || vnum == 27002 || vnum == 27003 ||
			vnum == 27052 || vnum == 27004 || vnum == 27005 || vnum == 27006 ||
			(vnum >= 27100 && vnum <= 27105) || vnum == 27053 || vnum == 27054)
			return false;

		if (vnum == GetStarterChestVnum(ch->GetJob()) ||
				(vnum >= 50187 && vnum <= 50196))
			return false;

		if (IsPlayerBotTradeableMaterial(item))
			return !PlayerBotNeedsRefineMaterial(ch, vnum) &&
					IsPlayerBotSurplusMaterial(ch, item);
		if (vnum >= 30000 && vnum <= 30200)
			return !PlayerBotNeedsRefineMaterial(ch, vnum);
		if (vnum >= 70038 && vnum <= 70060)
			return false;

		if (IsPlayerBotEquipmentCandidate(ch, item))
		{
			const int wearCell = item->FindEquipCell(ch);
			if (wearCell >= 0 && wearCell < WEAR_MAX_NUM)
			{
				if (item->GetLevelLimit() > ch->GetLevel())
					return true;

				LPITEM oldItem = ch->GetWear(wearCell);
				const long long itemScore = GetPlayerBotEquipmentScore(item, ch);
				const long long oldScore = oldItem ? GetPlayerBotEquipmentScore(oldItem, ch) : 0;
				if (!oldItem || itemScore > oldScore)
				{
					for (WORD otherCell = 0; otherCell < INVENTORY_MAX_NUM; ++otherCell)
					{
						LPITEM other = ch->GetInventoryItem(otherCell);
						if (!other || other == item || !IsPlayerBotEquipmentCandidate(ch, other) ||
								other->GetLevelLimit() > ch->GetLevel() ||
								other->FindEquipCell(ch) != wearCell)
							continue;

						const long long otherScore = GetPlayerBotEquipmentScore(other, ch);
						if (otherScore > itemScore ||
								(otherScore == itemScore && other->GetID() < item->GetID()))
							return true;
					}
					return false;
				}

				if (item->GetRefineLevel() >= PLAYERBOT_RESERVE_GEAR_MIN_REFINE)
				{
					for (WORD otherCell = 0; otherCell < INVENTORY_MAX_NUM; ++otherCell)
					{
						LPITEM other = ch->GetInventoryItem(otherCell);
						if (!other || other == item ||
								other->GetRefineLevel() < PLAYERBOT_RESERVE_GEAR_MIN_REFINE ||
								!IsPlayerBotEquipmentCandidate(ch, other) ||
								other->GetLevelLimit() > ch->GetLevel() ||
								other->FindEquipCell(ch) != wearCell)
							continue;

						const long long otherScore = GetPlayerBotEquipmentScore(other, ch);
						if (otherScore > itemScore ||
								(otherScore == itemScore && other->GetID() < item->GetID()))
							return true;
					}
					return false;
				}
			}
		}

		return true;
	}

	EPlayerBotMerchantCategory GetPlayerBotJunkMerchant(LPITEM item)
	{
		if (!item)
			return BOT_MERCHANT_MISC;

		if (item->GetType() == ITEM_WEAPON)
			return BOT_MERCHANT_WEAPON;
		if (item->GetType() == ITEM_ARMOR || item->GetType() == ITEM_UNIQUE ||
				item->GetType() == ITEM_RING || item->GetType() == ITEM_BELT)
			return BOT_MERCHANT_ARMOR;
		return BOT_MERCHANT_MISC;
	}

	bool HasPlayerBotJunkForMerchant(LPCHARACTER ch, EPlayerBotMerchantCategory category)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;

		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotJunkItem(ch, item) &&
					GetPlayerBotJunkMerchant(item) == category)
				return true;
		}
		return false;
	}

	size_t CountPlayerBotJunkItems(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return 0;
		size_t count = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
			if (IsPlayerBotJunkItem(ch, ch->GetInventoryItem(cell)))
				++count;
		return count;
	}

	bool SellPlayerBotJunkAtMerchant(LPCHARACTER ch, EPlayerBotMerchantCategory category,
			const char* merchantName)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;

		size_t soldCount = 0;
		long long totalSoldGold = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || !IsPlayerBotJunkItem(ch, item) ||
					GetPlayerBotJunkMerchant(item) != category)
				continue;

			DWORD price = item->GetShopBuyPrice();
			if (price == 0)
				price = item->GetProto() ? item->GetProto()->dwGold : 100;
			price = std::max<DWORD>(10, price / 5);
			totalSoldGold += price;
			ch->PointChange(POINT_GOLD, price);
			ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_SHOP_SELL");
			++soldCount;
		}

		if (soldCount > 0)
		{
			sys_log(0, "PLAYERBOT_AI: sold %u items at %s pid=%u name=%s gold_gained=%lld total_gold=%lld",
					(unsigned int)soldCount, merchantName ? merchantName : "merchant",
					ch->GetPlayerID(), ch->GetName(), totalSoldGold, (long long)ch->GetGold());
		}
		return soldCount > 0;
	}

	bool HasPlayerBotBackupGear(LPCHARACTER ch, BYTE wearCell)
	{
		if (!ch)
			return false;

		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!IsPlayerBotEquipmentCandidate(ch, item))
				continue;
			if (item->FindEquipCell(ch) == wearCell)
				return true;
		}

		return false;
	}

	bool ManagePlayerBotRefining(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || dwNow < state.dwNextRefineCheckTime)
			return false;

		state.dwNextRefineCheckTime = dwNow + PLAYERBOT_REFINE_INTERVAL;

		struct TRefineCandidate
		{
			BYTE wearCell;
			LPITEM item;
			BYTE plusLevel;
			BYTE priority;
		};

		std::vector<TRefineCandidate> candidates;
		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};

		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]); ++i)
		{
			LPITEM item = ch->GetWear(wearSlots[i]);
			if (!item || item->GetRefinedVnum() == 0)
				continue;

			const BYTE plusLevel = item->GetRefineLevel();
			const bool coreProgression = IsPlayerBotCoreProgressionItem(ch, item);
			if (plusLevel >= GetPlayerBotRefineTarget(ch, item))
				continue;

			TRefineCandidate cand;
			cand.wearCell = wearSlots[i];
			cand.item = item;
			cand.plusLevel = plusLevel;
			cand.priority = coreProgression ? 0 : 2;
			candidates.push_back(cand);
		}

		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetRefinedVnum() == 0 || !IsPlayerBotEquipmentCandidate(ch, item))
				continue;

			const BYTE plusLevel = item->GetRefineLevel();
			if (plusLevel >= GetPlayerBotRefineTarget(ch, item))
				continue;

			TRefineCandidate cand;
			cand.wearCell = 255;
			cand.item = item;
			cand.plusLevel = plusLevel;
			const bool coreProgression = IsPlayerBotCoreProgressionItem(ch, item);
			cand.priority = coreProgression ? 0 : 2;
			candidates.push_back(cand);
		}

		if (candidates.empty())
			return false;

		for (size_t i = 0; i < candidates.size(); ++i)
		{
			for (size_t j = i + 1; j < candidates.size(); ++j)
			{
				if (candidates[j].priority < candidates[i].priority ||
						(candidates[j].priority == candidates[i].priority &&
						 candidates[j].plusLevel < candidates[i].plusLevel))
				{
					TRefineCandidate tmp = candidates[i];
					candidates[i] = candidates[j];
					candidates[j] = tmp;
				}
			}
		}

		int refinedCount = 0;
		for (size_t i = 0; i < candidates.size() && refinedCount < 2; ++i)
		{
			LPITEM item = candidates[i].item;
			if (!item || item->GetRefinedVnum() == 0)
				continue;

			const DWORD oldVnum = item->GetVnum();
			const DWORD nextVnum = item->GetRefinedVnum();
			const BYTE plusLevel = candidates[i].plusLevel;

			if (!IsPlayerBotWearableAtLevel(ch, nextVnum))
			{
				PlayerBotLogThrottled("refine_outgrows", dwNow,
						"PLAYERBOT_AI: refine would outgrow the bot pid=%u name=%s level=%u vnum=%u next=%u plus=%u",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
						oldVnum, nextVnum, (unsigned int)plusLevel + 1);
				continue;
			}
			const BYTE wearCell = candidates[i].wearCell;
			const bool hasBackup = (wearCell != 255) ? HasPlayerBotBackupGear(ch, wearCell) : true;

			if (wearCell == WEAR_WEAPON && !hasBackup && plusLevel >= 4 && ch->GetGold() < 5000)
				continue;

			if (plusLevel >= 5 && !hasBackup && ch->GetGold() < 15000)
				continue;

			if (plusLevel == 4 && !hasBackup && number(1, 100) > 75)
				continue;

			if (item->IsEquipped())
			{
				int emptyCell = ch->GetEmptyInventory(item->GetSize());
				if (emptyCell < 0)
					continue;
				if (!ch->UnequipItem(item) || item->IsEquipped())
					continue;
			}

			const int resultCountBefore = ch->CountSpecifyItem(nextVnum);
			int scrollCell = -1;
			if (plusLevel >= PLAYERBOT_SCROLL_REFINE_MIN_PLUS)
			{
				for (WORD cell = 0; cell < INVENTORY_MAX_NUM && scrollCell < 0; ++cell)
				{
					LPITEM scroll = ch->GetInventoryItem(cell);
					if (scroll && scroll->GetVnum() == PLAYERBOT_BLESSING_SCROLL_VNUM)
						scrollCell = cell;
				}
			}
			bool attempted = false;
			if (scrollCell >= 0)
			{
				ch->SetRefineMode(scrollCell);
				attempted = ch->DoRefineWithScroll(item);
				ch->ClearRefineMode();
			}
			else
				attempted = ch->DoRefine(item, false);
			if (attempted)
			{
				const bool success = ch->CountSpecifyItem(nextVnum) > resultCountBefore;
				if (success)
					BroadcastPlayerBotRefineSuccess(ch, item, (int)plusLevel + 1);
				sys_log(0, "PLAYERBOT_AI: refine %s pid=%u name=%s old_vnum=%u new_vnum=%u plus=%u scroll=%d",
						success ? "SUCCESS" : (scrollCell >= 0 ? "FAILED_DOWNGRADED" : "FAILED_BURNED"),
						ch->GetPlayerID(), ch->GetName(), oldVnum, nextVnum, plusLevel + 1, scrollCell >= 0 ? 1 : 0);
				++refinedCount;
			}
			else
			{
				sys_log(0, "PLAYERBOT_AI: refine SKIPPED pid=%u name=%s vnum=%u plus=%u (requirements/state)",
						ch->GetPlayerID(), ch->GetName(), oldVnum, plusLevel);
			}
		}

		return refinedCount > 0;
	}

	bool ManagePlayerBotScrollRefine(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || dwNow < state.dwNextScrollRefineTime)
			return false;
		if (state.bCurrentAction == BOT_ACTION_FIGHT || state.bVisitingShop ||
				state.bRecoveringAfterDeath || state.bTacticalRetreat || ch->IsDead())
			return false;
		state.dwNextScrollRefineTime = dwNow + PLAYERBOT_SCROLL_REFINE_INTERVAL;

		int scrollCell = -1;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM && scrollCell < 0; ++cell)
		{
			LPITEM scroll = ch->GetInventoryItem(cell);
			if (scroll && scroll->GetVnum() == PLAYERBOT_BLESSING_SCROLL_VNUM)
				scrollCell = cell;
		}
		if (scrollCell < 0)
			return false;

		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_HEAD, WEAR_SHIELD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};
		LPITEM best = NULL;
		BYTE bestWear = 0;
		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]); ++i)
		{
			LPITEM item = ch->GetWear(wearSlots[i]);
			if (!item || item->GetRefinedVnum() == 0 || item->isLocked() || item->IsExchanging())
				continue;
			const BYTE plus = item->GetRefineLevel();
			if (plus < PLAYERBOT_SCROLL_REFINE_MIN_PLUS || plus >= GetPlayerBotRefineTarget(ch, item))
				continue;
			if (!IsPlayerBotWearableAtLevel(ch, item->GetRefinedVnum()))
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(item->GetRefineSet());
			if (!recipe)
				continue;
			if (ch->GetGold() - GetPlayerBotReservedGold(ch) < (int)recipe->cost)
				continue;
			bool materials = true;
			for (int m = 0; m < recipe->material_count && materials; ++m)
				if (recipe->materials[m].vnum != 0 &&
						ch->CountSpecifyItem(recipe->materials[m].vnum) < recipe->materials[m].count)
					materials = false;
			if (!materials)
				continue;
			if (!best || plus < best->GetRefineLevel())
			{
				best = item;
				bestWear = wearSlots[i];
			}
		}
		if (!best)
			return false;

		if (ch->GetEmptyInventory(best->GetSize()) < 0)
			return false;
		const DWORD oldVnum = best->GetVnum();
		const DWORD nextVnum = best->GetRefinedVnum();
		const BYTE plus = best->GetRefineLevel();
		if (!ch->UnequipItem(best) || best->IsEquipped())
			return false;
		const WORD cell = best->GetCell();
		const int before = ch->CountSpecifyItem(nextVnum);
		ch->SetRefineMode(scrollCell);
		const bool attempted = ch->DoRefineWithScroll(best);
		ch->ClearRefineMode();
		LPITEM after = ch->GetInventoryItem(cell);
		if (after)
			ch->EquipItem(after);
		if (attempted)
		{
			const bool success = ch->CountSpecifyItem(nextVnum) > before;
			if (success)
				BroadcastPlayerBotRefineSuccess(ch, after ? after : best, (int)plus + 1);
			sys_log(0, "PLAYERBOT_AI: refine %s pid=%u name=%s old_vnum=%u new_vnum=%u plus=%u scroll=1 place=field wear=%u",
					success ? "SUCCESS" : "FAILED_DOWNGRADED", ch->GetPlayerID(), ch->GetName(),
					oldVnum, nextVnum, (unsigned int)plus + 1, (unsigned int)bestWear);
		}
		return attempted;
	}

	bool ManagePlayerBotMiscMerchant(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;

		CompactPlayerBotPotionStacks(ch);
		SellPlayerBotExcessPotions(ch);

		size_t redCount = 0;
		size_t blueCount = 0;
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

		SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_MISC, "misc_merchant");

		const bool isMage = (ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA);
		const BYTE botLvl = ch->GetLevel();

		if (botLvl <= 10)
		{
			if (redCount < 30 && ch->GetGold() >= 300)
			{
				ch->PointChange(POINT_GOLD, -240);
				ch->AutoGiveItem(27001, 30);
			}
			if (isMage && blueCount < 20 && ch->GetGold() >= 400)
			{
				ch->PointChange(POINT_GOLD, -360);
				ch->AutoGiveItem(27004, 15);
			}
		}
		else
		{
			const DWORD RED_TARGET = 800;
			const DWORD BLUE_TARGET = 600;
			const DWORD RED_UNIT = 20;
			const DWORD BLUE_UNIT = 32;

			if (redCount < RED_TARGET && ch->GetGold() >= 1200)
			{
				const DWORD want = (DWORD)(RED_TARGET - redCount);
				const DWORD affordable = (DWORD)(ch->GetGold() / 2 / RED_UNIT);
				const DWORD buy = want < affordable ? want : affordable;
				if (buy > 0)
				{
					ch->PointChange(POINT_GOLD, -(int)(buy * RED_UNIT));
					ch->AutoGiveItem(27002, buy);
				}
			}
			if (blueCount < BLUE_TARGET && ch->GetGold() >= 1200)
			{
				const DWORD want = (DWORD)(BLUE_TARGET - blueCount);
				const DWORD affordable = (DWORD)(ch->GetGold() / 2 / BLUE_UNIT);
				const DWORD buy = want < affordable ? want : affordable;
				if (buy > 0)
				{
					ch->PointChange(POINT_GOLD, -(int)(buy * BLUE_UNIT));
					ch->AutoGiveItem(27005, buy);
				}
			}
		}

		if (NeedsPlayerBotProgressionBoots(ch))
			BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionBootsVnum(ch), "boots");

		return true;
	}

	bool ManagePlayerBotWeaponMerchant(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		const bool sold = SellPlayerBotJunkAtMerchant(
				ch, BOT_MERCHANT_WEAPON, "weapon_merchant");
		bool bought = false;
		const bool isArcher = ch->GetJob() == JOB_ASSASSIN && ch->GetSkillGroup() == 2;
		if (!ch->GetWear(WEAR_WEAPON))
			bought = BuyPlayerBotEmergencyWeapon(ch) || bought;
		if (isArcher)
			bought = BuyPlayerBotArrowsAtMerchant(ch) || bought;
		if (NeedsPlayerBotProgressionWeapon(ch) &&
				(!isArcher || CountPlayerBotArrows(ch) >= PLAYERBOT_ARROW_RESTOCK_THRESHOLD))
			bought = BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionWeaponVnum(ch), "weapon") || bought;
		return sold || bought;
	}

	bool ManagePlayerBotArmorMerchant(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		const bool sold = SellPlayerBotJunkAtMerchant(
				ch, BOT_MERCHANT_ARMOR, "armor_merchant");
		bool bought = NeedsPlayerBotProgressionArmor(ch) &&
				BuyPlayerBotProgressionGear(ch,
						GetPlayerBotProgressionArmorVnum(ch), "armor");
		if (NeedsPlayerBotProgressionShield(ch))
			bought = BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionShieldVnum(ch), "shield") || bought;
		if (NeedsPlayerBotProgressionHelmet(ch))
			bought = BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionHelmetVnum(ch), "helmet") || bought;
		if (NeedsPlayerBotProgressionWrist(ch))
			bought = BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionWristVnum(ch), "wrist") || bought;
		if (NeedsPlayerBotProgressionNecklace(ch))
			bought = BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionNecklaceVnum(ch), "necklace") || bought;
		if (NeedsPlayerBotProgressionEarring(ch))
			bought = BuyPlayerBotProgressionGear(ch,
					GetPlayerBotProgressionEarringVnum(ch), "earring") || bought;
		return sold || bought;
	}

	bool CanPlayerBotAttemptRefineItem(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetRefinedVnum() == 0 ||
				item->GetRefineLevel() >= GetPlayerBotRefineTarget(ch, item))
			return false;

		const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(
				item->GetRefineSet());
		if (!recipe || ch->GetGold() - GetPlayerBotReservedGold(ch) <
				ch->ComputeRefineFee(recipe->cost))
			return false;

		for (int i = 0; i < recipe->material_count; ++i)
		{
			if (ch->CountSpecifyItem(recipe->materials[i].vnum) < recipe->materials[i].count)
				return false;
		}
		return true;
	}

	bool HasPlayerBotRefineOpportunity(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;

		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};
		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]); ++i)
		{
			LPITEM item = ch->GetWear(wearSlots[i]);
			if (CanPlayerBotAttemptRefineItem(ch, item))
				return true;
		}

		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (IsPlayerBotEquipmentCandidate(ch, item) &&
					CanPlayerBotAttemptRefineItem(ch, item))
				return true;
		}
		return false;
	}

	bool HasPlayerBotPriorityRefineOpportunity(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;

		const BYTE coreWearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD, WEAR_FOOTS
		};
		for (size_t i = 0; i < sizeof(coreWearSlots) / sizeof(coreWearSlots[0]); ++i)
		{
			LPITEM item = ch->GetWear(coreWearSlots[i]);
			if (item && CanPlayerBotAttemptRefineItem(ch, item))
				return true;
		}
		return false;
	}
}

#endif