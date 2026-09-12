#ifndef __INC_METIN2_PLAYERBOT_LLM_STATUS_H__
#define __INC_METIN2_PLAYERBOT_LLM_STATUS_H__

// What a bot shows above its head, and the words for it.
//
// This is the only place a bot is described in a player's language rather than
// in the code's. Strings here are Turkish and ASCII-only: the client renders
// them in a font that has no diacritics, so an accented character comes out as
// a box.
//
// The text is recomputed only when something it depends on actually changed -
// several hundred bots re-broadcasting an identical line every tick is a lot of
// packets for no new information.
//
// An implementation fragment in the sense playerbot_types.h describes: it
// defines objects, relies on the engine headers playerbot_manager.cpp includes
// above it, and reopens the same anonymous namespace. Include it exactly once.

namespace
{
	// Whether a real player is close enough for any of this to be seen. The
	// overhead text exists for them, so with nobody watching there is nothing
	// to broadcast.
	class CCheckNearbyHumanPlayer
	{
		public:
			CCheckNearbyHumanPlayer(LPCHARACTER owner, int maxDist) : m_owner(owner), m_maxDist(maxDist), m_bFound(false) {}
			bool operator () (LPENTITY entity)
			{
				if (!entity || !entity->IsType(ENTITY_CHARACTER))
					return true;
				LPCHARACTER ch = static_cast<LPCHARACTER>(entity);
				if (ch && ch->IsPC() && ch->GetDesc() != NULL && ch != m_owner)
				{
					if (DISTANCE_APPROX(m_owner->GetX() - ch->GetX(), m_owner->GetY() - ch->GetY()) <= m_maxDist)
					{
						m_bFound = true;
						return false; // Stop search
					}
				}
				return true;
			}
			LPCHARACTER m_owner;
			int m_maxDist;
			bool m_bFound;
	};

	const char* GetPlayerBotGoalLabel(BYTE goal)
	{
		switch (goal)
		{
			case BOT_GOAL_SURVIVE: return "can yenileme";
			case BOT_GOAL_CHOOSE_PROFESSION: return "meslek secimi";
			case BOT_GOAL_GET_EQUIPMENT: return "ekipman";
			case BOT_GOAL_RESTOCK: return "stok";
			case BOT_GOAL_REFINE: return "basma";
			case BOT_GOAL_MASTER_SKILL: return "skill gelistirme";
			case BOT_GOAL_HUNT_METIN: return "Metin avlama";
			case BOT_GOAL_PARTY_CHALLENGE: return "grup ile guclu mob";
			case BOT_GOAL_BIOLOGIST: return "Biyolog gorevi";
			case BOT_GOAL_HUNTING: return "avlanma";
			case BOT_GOAL_HORSE: return "at gelistirme";
			case BOT_GOAL_FISHING: return "balik tutma";
			default: return "seviye kasma";
		}
	}

	// The map a player would name, not the one the code names. Used by the
	// travel line, which used to announce every journey as a hunt for
	// experience whatever the errand actually was.
	const char* GetPlayerBotMapDestinationTurkish(long mapIndex)
	{
		switch (mapIndex)
		{
			// The names are the engine's own: new_quest_lv52 reads the first
			// villages out of { "Yongan", "Joan", "Pyongmoo" } by empire and
			// new_quest_lv7 names the second ones Jayang, Bokjung and Bakra.
			// Map 24 used to be labelled Pyungmoo here, which is Jinno's
			// capital and not Chunjo's guild ground.
			case 1: return "Yongan'a";
			case 3: return "Jayang'a";
			case PLAYERBOT_MAP_CHUNJO_M1: return "Joan'a";
			case PLAYERBOT_MAP_CHUNJO_M2: return "Bokjung'a";
			case 41: return "Pyongmoo'ya";
			case 43: return "Bakra'ya";
			case 4:
			case PLAYERBOT_MAP_CHUNJO_M3:
			case 44: return "Klan Topraklarina";
			case 5:
			case 45:
			case PLAYERBOT_MAP_MONKEY_EASY: return "Maymun Zindani";
			case PLAYERBOT_MAP_MONKEY_MEDIUM: return "Maymun Zindani II";
			case PLAYERBOT_MAP_MONKEY_HARD: return "Maymun Zindani III";
			case PLAYERBOT_MAP_DESERT: return "Yongbi Colu'ne";
			case PLAYERBOT_MAP_ORC_VALLEY: return "Orklar Vadisi'ne";
			case PLAYERBOT_MAP_SOHAN: return "Sohan Dagi'na";
			case PLAYERBOT_MAP_SPIDER_V1: return "Orumcek Zindani'na";
			case PLAYERBOT_MAP_SPIDER_V2: return "Orumcek Zindani'na 2";
			case PLAYERBOT_MAP_HWANG: return "Hwang Tapinagi'na";
			default: return "";
		}
	}

	const char* GetPlayerBotActionLabel(BYTE action)
	{
		switch (action)
		{
			case BOT_ACTION_TRAVEL: return "gidiyorum";
			case BOT_ACTION_FIGHT: return "savasiyorum";
			case BOT_ACTION_LOOT: return "topluyorum";
			case BOT_ACTION_RECOVER: return "dinleniyorum";
			case BOT_ACTION_TRAIN: return "meslek seciyorum";
			case BOT_ACTION_SHOP: return "ticaret yapiyorum";
			case BOT_ACTION_REFINE: return "esya basiyorum";
			case BOT_ACTION_READ_BOOK: return "BK okuyorum";
			case BOT_ACTION_SOCKET_STONE: return "KD takiyorum";
			case BOT_ACTION_PARTY_ASSEMBLE: return "grup topluyorum";
			case BOT_ACTION_BIOLOGIST: return "Biyolog gorevi yapiyorum";
			case BOT_ACTION_STABLE: return "Seyis'e gidiyorum";
			case BOT_ACTION_STALL: return "pazar kuruyorum";
			case BOT_ACTION_MARKET: return "pazarda alisveris yapiyorum";
			case BOT_ACTION_LURE: return "grup icin mob cekiyorum";
			case BOT_ACTION_TOWN_REST: return "sehirde dinleniyorum";
			default: return "takiliyorum";
		}
	}

	void SendPlayerBotOverheadChat(LPCHARACTER ch, const char* szText)
	{
		if (!ch || !szText || !szText[0] || !ch->GetSectree())
			return;

		char chatbuf[256];
		int len = snprintf(chatbuf, sizeof(chatbuf), "%s : %s", ch->GetName(), szText);
		if (len <= 0)
			return;
		if (len >= (int)sizeof(chatbuf))
			len = sizeof(chatbuf) - 1;
		// The regular talking packet contains its trailing NUL.  Keeping the packet
		// identical to a real player's chat is what makes every native/wasm client
		// render it as a text tail above the bot without a client fork.
		++len;

		TPacketGCChat pack_chat;
		pack_chat.header = HEADER_GC_CHAT;
		pack_chat.size = sizeof(TPacketGCChat) + len;
		pack_chat.type = CHAT_TYPE_TALKING;
		pack_chat.id = ch->GetVID();
		pack_chat.bEmpire = 0;

		TEMP_BUFFER buf;
		buf.write(&pack_chat, sizeof(TPacketGCChat));
		buf.write(chatbuf, len);
		ch->PacketAround(buf.read_peek(), buf.size());
	}

	const char* GetPlayerBotTownStatusLabel(const TPlayerBotAIState& state)
	{
		switch (state.bTownVisitPhase)
		{
			case BOT_TOWN_PHASE_TRAINER: return "Meslekciye gidiyorum";
			case BOT_TOWN_PHASE_TRAINER_WAIT: return "Meslek seciyorum";
			case BOT_TOWN_PHASE_WEAPON_MERCHANT: return "Silahciya gidiyorum";
			case BOT_TOWN_PHASE_WEAPON_WAIT: return "Silahciyla is yapiyorum";
			case BOT_TOWN_PHASE_ARMOR_MERCHANT: return "Zirciciya gidiyorum";
			case BOT_TOWN_PHASE_ARMOR_WAIT: return "Zircidan alisveris yapiyorum";
			case BOT_TOWN_PHASE_MISC_MERCHANT: return "Genel saticiya gidiyorum";
			case BOT_TOWN_PHASE_MISC_WAIT: return "Iksir aliyor, ganimet satiyorum";
			case BOT_TOWN_PHASE_BLACKSMITH: return "Demirciye gidiyorum";
			case BOT_TOWN_PHASE_BLACKSMITH_WAIT: return "Esya basiyorum";
			case BOT_TOWN_PHASE_SAFEBOX: return "Depoya gidiyorum";
			case BOT_TOWN_PHASE_SAFEBOX_WAIT: return "Kitaplari depoya koyuyorum";
			case BOT_TOWN_PHASE_GATE_IN:
			case BOT_TOWN_PHASE_GATE_CROSS_IN: return "Sehre gidiyorum";
			case BOT_TOWN_PHASE_GATE_OUT:
			case BOT_TOWN_PHASE_GATE_CROSS_OUT: return "Exp yerine donuyorum";
			default: return "Kentte islerimi hallediyorum";
		}
	}

	void BuildPlayerBotStatusText(LPCHARACTER ch, const TPlayerBotAIState& state,
			char* status, size_t statusSize)
	{
		if (!ch || !status || statusSize == 0)
			return;

		const char* prefix = ch->GetParty() ? "[GRUP] " : "";
		const char* goal = GetPlayerBotGoalLabel(state.bLongTermGoal);
		if (state.bVisitingShop)
		{
			// "Handluje bronia (cel: zapasy)" says what the bot is standing at
			// and nothing about what it came for. When the errand is potions,
			// the numbers are the whole story - and they are the one thing an
			// operator can check against the shelf.
			if (state.bLongTermGoal == BOT_GOAL_RESTOCK)
			{
				size_t redCount = 0, blueCount = 0;
				CountPlayerBotPotions(ch, redCount, blueCount);
				snprintf(status, statusSize, "%s%s - iksir %u/%u", prefix,
						GetPlayerBotTownStatusLabel(state),
						(unsigned int)redCount, (unsigned int)blueCount);
				return;
			}
			snprintf(status, statusSize, "%s%s (hedef: %s)", prefix,
					GetPlayerBotTownStatusLabel(state), goal);
			return;
		}

		if (state.bTacticalRetreat)
		{
			snprintf(status, statusSize, "%sKaciyorum - HP dusuk", prefix);
			return;
		}
		// An errand the watchdog interrupted, and the map the bot still means to
		// leave for. The audit asked for exactly this pair - "Uzupelniam
		// mikstury; potem Sohan" - because an observer cannot otherwise tell a
		// bot that is stuck from one that is waiting.
		if (state.bServicePending)
		{
			const char* where = state.lDepartureMap != 0
					? GetPlayerBotMapDestinationTurkish(state.lDepartureMap) : "";
			if (where[0])
				snprintf(status, statusSize, "%sSatici yolunu bekliyorum; sonra %s",
						prefix, where);
			else
				snprintf(status, statusSize, "%sSatici yolunu bekliyorum", prefix);
			return;
		}
		// The luring course says which stage it is in, because "walking away
		// from the party" and "bringing nine monsters back to it" look the same
		// from outside and are not the same thing at all.
		if (state.bLureStage != LURE_STAGE_NONE)
		{
			switch (state.bLureStage)
			{
				case LURE_STAGE_PLAN:
					snprintf(status, statusSize, "%sGrup icin lure hazirliyorum", prefix);
					return;
				case LURE_STAGE_RETURN:
					snprintf(status, statusSize, "%sGruba donuyorum: %d mob cekiyorum",
							prefix, state.iLureChasing);
					return;
				case LURE_STAGE_HANDOFF:
					snprintf(status, statusSize, "%sMoblari teslim ediyorum: %d getirildi, %d pesimde",
							prefix, state.iLureDelivered, state.iLureChasing);
					return;
				case LURE_STAGE_RECOVER:
					snprintf(status, statusSize, "%sLure ara: grup hala savasiyor", prefix);
					return;
				default:
					snprintf(status, statusSize, "%sGrup icin lure: %u/%u grup, pesimde %d",
							prefix, (unsigned int)state.bLureGroupsTagged,
							(unsigned int)state.bLureGroupsPlanned, state.iLureChasing);
					return;
			}
		}
		if (state.bRecoveringAfterDeath)
		{
			snprintf(status, statusSize, "%sOlumden sonra dinleniyorum", prefix);
			return;
		}

		LPCHARACTER target = state.dwTargetVID != 0
				? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		switch (state.bCurrentAction)
		{
			case BOT_ACTION_FIGHT:
				if (target && target->IsStone())
					snprintf(status, statusSize, "%s%s kiriyorum", prefix, target->GetName());
				else if (target && target->IsMonster())
				{
					int huntingRemaining = 0;
					const DWORD huntingMob = GetActivePlayerBotHuntingMobVnum(
							ch, &huntingRemaining);
					if (huntingMob != 0 && target->GetRaceNum() == huntingMob)
					{
						snprintf(status, statusSize, "%sAv: %s (kalan %d)",
								prefix, target->GetName(), huntingRemaining);
						break;
					}
					LPITEM weapon = ch->GetWear(WEAR_WEAPON);
					const bool bow = weapon && weapon->GetType() == ITEM_WEAPON &&
							weapon->GetSubType() == WEAPON_BOW;
					const int range = bow ? 800 : 280;
					const int distance = DISTANCE_APPROX(
							ch->GetX() - target->GetX(), ch->GetY() - target->GetY());
					// Action plus what for. "Walcze z X" is only half of what an
					// observer needs - the audit's complaint was that a status
					// never says why this monster and not another one. The
					// reason is the combat policy's own, recorded when it last
					// looked at this target.
					if (state.bLastCombatReason ==
							(BYTE)playerbot_combat_value::ALLOW_SELF_DEFENSE)
						snprintf(status, statusSize, "%s%s'ye karsi savunuyorum", prefix,
								target->GetName());
					else if (state.bLastCombatReason ==
							(BYTE)playerbot_combat_value::ALLOW_PARTY_DEFENSE)
						snprintf(status, statusSize, "%sGruba yardim ediyorum: %s", prefix,
								target->GetName());
					else if (state.bLastCombatReason ==
							(BYTE)playerbot_combat_value::ALLOW_MATERIAL)
						snprintf(status, statusSize, "%s%s malzemesini topluyorum", prefix,
								target->GetName());
					else if (distance > range)
						snprintf(status, statusSize, "%s%s'nin pesindeyim", prefix, target->GetName());
					else
						snprintf(status, statusSize, "%s%s ile savasiyorum", prefix, target->GetName());
				}
				else
					snprintf(status, statusSize, "%sRakip ariyorum", prefix);
				break;
			case BOT_ACTION_LOOT:
				snprintf(status, statusSize, "%sGanimet topluyorum", prefix);
				break;
			case BOT_ACTION_RECOVER:
				snprintf(status, statusSize, "%sCan dolduruyorum", prefix);
				break;
			case BOT_ACTION_TRAIN:
				if (state.bVisitingShop &&
						(state.bTownVisitPhase == BOT_TOWN_PHASE_SKILL_RESET ||
						 state.bTownVisitPhase == BOT_TOWN_PHASE_SKILL_RESET_WAIT))
					snprintf(status, statusSize, "%sYetenekleri sifirliyorum", prefix);
				else
					snprintf(status, statusSize, "%sMeslek seciyorum", prefix);
				break;
			case BOT_ACTION_SHOP:
				snprintf(status, statusSize, "%sTicaret yapiyorum", prefix);
				break;
			case BOT_ACTION_REFINE:
				snprintf(status, statusSize, "%sEkipman basiyorum", prefix);
				break;
			case BOT_ACTION_READ_BOOK:
				snprintf(status, statusSize, "%sBeceri kitabi okuyorum", prefix);
				break;
			case BOT_ACTION_SOCKET_STONE:
				snprintf(status, statusSize, "%sRuh Tasi takiyorum", prefix);
				break;
			case BOT_ACTION_PARTY_ASSEMBLE:
				snprintf(status, statusSize, "%sGrup icin hedef ariyorum", prefix);
				break;
			case BOT_ACTION_BIOLOGIST:
			{
				const TPlayerBotBiologistMission* mission =
						GetActivePlayerBotBiologistMission(ch);
				if (!mission)
					snprintf(status, statusSize, "%sBiologdan donuyorum", prefix);
				else if (state.bVisitingBiologist &&
						DISTANCE_APPROX(ch->GetX() - PLAYERBOT_BIOLOGIST_X,
								ch->GetY() - PLAYERBOT_BIOLOGIST_Y) > 850)
					snprintf(status, statusSize, "%sBiologa gidiyorum: %s", prefix, mission->itemLabel);
				else if (state.bVisitingBiologist)
					snprintf(status, statusSize, "%sBiyologa teslim ediyorum: %s", prefix, mission->itemLabel);
				else
					snprintf(status, statusSize, "%sBiyolog icin topluyorum: %s", prefix, mission->itemLabel);
				break;
			}
			case BOT_ACTION_STABLE:
			{
				// The stable keeper of the map the bot is on: measured against
				// Joan's alone, a bot handing its medal over in Bokjung was
				// "on its way" for the whole visit.
				playerbot_empire_rules::TTownServices svc;
				const bool haveStable = playerbot_empire_rules::GetTownServices(ch->GetMapIndex(), svc);
				const long stableX = haveStable ? svc.stableKeeper.x : ch->GetX();
				const long stableY = haveStable ? svc.stableKeeper.y : ch->GetY();
				const bool bFar = DISTANCE_APPROX(ch->GetX() - stableX, ch->GetY() - stableY) > 850;
				if (IsPlayerBotBattleHorseEarned(ch))
					snprintf(status, statusSize, bFar ? "%sSavas atina gidiyorum"
							: "%sSavas atini aliyorum", prefix);
				else if (bFar)
					snprintf(status, statusSize, "%sMadalyayla seyise gidiyorum", prefix);
				else
					snprintf(status, statusSize, "%sAt madalyasi veriyorum (%u/21)", prefix,
							(unsigned int)ch->GetHorseLevel());
				break;
			}
			case BOT_ACTION_FISHING:
				if (ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM) <
						PLAYERBOT_FISHING_BAIT_RESTOCK)
					snprintf(status, statusSize, "%sYem almak icin balikciya gidiyorum", prefix);
				else if (GetPlayerBotFishingBank(ch->GetMapIndex()) == NULL ||
						DISTANCE_APPROX(
							ch->GetX() - GetPlayerBotFishingBank(ch->GetMapIndex())->centre.x,
							ch->GetY() - GetPlayerBotFishingBank(ch->GetMapIndex())->centre.y) >
						GetPlayerBotFishingBank(ch->GetMapIndex())->radius)
					snprintf(status, statusSize, "%sNehirde balik tutmaya gidiyorum", prefix);
				else if (state.bIsFishing)
					snprintf(status, statusSize, "%sBalik tutuyorum - oltayi bekliyorum", prefix);
				else if (!IsPlayerBotHoldingRod(ch))
					// The old text here was a plain else, so an angler standing at
					// the water with no rod on its back announced that it was
					// baiting one - which is what got reported as "bots put bait
					// on weapons". Nothing was ever put on a weapon; the label
					// was simply wrong about what the bot was doing.
					snprintf(status, statusSize, "%sOlta ariyorum", prefix);
				else
					snprintf(status, statusSize, "%sYemi oltaya takiyorum", prefix);
				break;
			case BOT_ACTION_TOWN_REST:
				// The linger after a town errand. It reads as browsing only
				// where there are counters to browse; on a world too young
				// for a single stall it was "what stalls, there are none".
				if (GetPlayerBotStallsOnMap(ch->GetMapIndex()) > 0)
					snprintf(status, statusSize, "%sPazar tezgahlarini geziyorum", prefix);
				else
					snprintf(status, statusSize, "%sSehirde dinleniyorum", prefix);
				break;
			case BOT_ACTION_MARKET:
				if (state.dwMarketStallVID != 0)
					snprintf(status, statusSize, "%sPazari inceliyorum", prefix);
				else
					snprintf(status, statusSize, "%sPazarlarda bir sey ariyorum", prefix);
				break;
			case BOT_ACTION_TRAVEL:
				if (IsPlayerBotM1Map(ch->GetMapIndex()) &&
						state.bLongTermGoal == BOT_GOAL_HORSE)
					snprintf(status, statusSize, "%sM2'ye at madalyasi icin gidiyorum", prefix);
				else if (IsPlayerBotM2Map(ch->GetMapIndex()) &&
						ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) == 0 &&
						state.bLongTermGoal == BOT_GOAL_HORSE)
					snprintf(status, statusSize, "%sMaymun Zindani'na at madalyasi icin gidiyorum", prefix);
				else if (IsPlayerBotOnBattleHorseTrial(ch))
					snprintf(status, statusSize, "%sColde savas ati gorevini yapiyorum (%d/%d)", prefix,
							GetPlayerBotBattleHorseKills(ch), PLAYERBOT_BATTLE_HORSE_KILLS);
				// Only a medal the bot can hand in. A horse at ten waits for
				// level thirty-five, a medal dropper carries them for its
				// counter, and both used to announce the stable keeper on every
				// leg they rode - "idzie do stajennego przez godzine".
				else if (ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) > 0 &&
						CanPlayerBotAdvanceHorse(ch))
					snprintf(status, statusSize, "%sMadalyayla en yakin seyise gidiyorum", prefix);
				else if (IsPlayerBotMonkeyMap(ch->GetMapIndex()))
				{
					// Only when the bot has actually decided to go. This was a
					// plain else on a monkey map, so every bot moving inside the
					// dungeon announced that it was leaving - and moving is what
					// a bot in here does all the time: the maze is eleven
					// chambers joined only by GOTO NPCs, and crossing to the
					// next one is a walk like any other. Reported from the
					// Discord as "the bubble says they are leaving and they do
					// not leave". They were not leaving. Leaving is instant when
					// it happens at all - the exit is a direct map change, not a
					// walk - so a bot that is still here is doing something else.
					// Never "leaving" while the bot is still here, because
					// leaving is not something that takes time: the exit is a
					// direct map change made on the tick the decision is taken,
					// so a bot anybody can still see in the dungeon is by
					// definition not on its way out. Gating on the goal was not
					// enough - BOT_GOAL_HORSE is what a medal expedition carries
					// for its whole visit, so twenty-one of thirty bots still
					// announced an exit they were nowhere near. Say the true
					// thing instead: it is crossing the maze.
					snprintf(status, statusSize, "%sMaymun Zindani'nda yol ariyorum", prefix);
				}
				// "Szukam miejsca do expa (cel: zapasy)" was said over a bot
				// walking to a merchant, which is the audit's example of a
				// status that describes an action without its purpose. Say
				// where the bot is going, and when the errand is not experience,
				// say the errand instead.
				else if (state.bLongTermGoal == BOT_GOAL_RESTOCK)
					snprintf(status, statusSize, "%sSehre erzak icin gidiyorum", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_REFINE)
					snprintf(status, statusSize, "%sEsyalari basmak icin demirciye gidiyorum", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_BIOLOGIST)
					snprintf(status, statusSize, "%sBiologa gidiyorum", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_FISHING)
					snprintf(status, statusSize, "%sNehirde balik tutmaya gidiyorum", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_GET_EQUIPMENT)
					snprintf(status, statusSize, "%sEkipman icin sehre gidiyorum", prefix);
				else
				{
					const long wantMap = GetPlayerBotFrontierMapForLevel(ch);
					const char* where = wantMap != 0 && wantMap != ch->GetMapIndex()
							? GetPlayerBotMapDestinationTurkish(wantMap) : "";
					// The frontier is reached from Bokjung through the
					// Teleporter, at his price; a bot that cannot pay is not
					// going anywhere, and a plain travel line over a bot that
					// has stood in Bokjung for an hour is what an operator
					// reads as a bot that cannot find the portal.
					if (where[0] && IsPlayerBotM2Map(ch->GetMapIndex()) &&
							ch->GetGold() < GetPlayerBotTeleporterFee(ch))
						snprintf(status, statusSize, "%sTeleporter icin yang biriktiriyorum %s (%d/%d)",
								prefix, where, ch->GetGold(), GetPlayerBotTeleporterFee(ch));
					else if (where[0])
						snprintf(status, statusSize, "%s%s gidiyorum (hedef: %s)", prefix,
								where, goal);
					else
						snprintf(status, statusSize, "%sDaha iyi bir yer ariyorum (hedef: %s)",
								prefix, goal);
				}
				break;
			case BOT_ACTION_STALL:
				// The head carries the sign in the world; the panel read
				// "Planuje: poziom" for a keeper at its counter and an operator
				// counted thirty-nine idle bots in the Joan square.
				snprintf(status, statusSize, "%sPazar kuruyorum", prefix);
				break;
			default:
				snprintf(status, statusSize, "%sPlanliyorum: %s", prefix, goal);
				break;
		}
	}

	void ManagePlayerBotStatusOverhead(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		// A keeper's head already carries its shop sign. Writing the status line
		// over it replaces the one label a passing player actually needs - the
		// name of the stall they are deciding whether to open.
		if (ch && ch->GetMyShop())
			return;
		// The operator's switch in the panel. The status text still goes to the
		// panel's snapshot; only the line over the head is silenced.
		if (!IsPlayerBotOverheadChatEnabled())
			return;
		if (!ch)
			return;

		const BYTE inParty = ch->GetParty() ? 1 : 0;
		const DWORD relevantTargetVID = state.bCurrentAction == BOT_ACTION_FIGHT
				? state.dwTargetVID : 0;
		const BYTE relevantTownPhase = state.bVisitingShop
				? state.bTownVisitPhase : BOT_TOWN_PHASE_NONE;
		const bool changed =
				state.bLastStatusAction != state.bCurrentAction ||
				state.bLastStatusGoal != state.bLongTermGoal ||
				state.bLastStatusTownPhase != relevantTownPhase ||
				state.bLastStatusParty != inParty ||
				state.dwLastStatusTargetVID != relevantTargetVID;
		const bool keepAliveDue = dwNow >= state.dwNextChatTime;
		if (!changed && !keepAliveDue)
			return;
		if (dwNow < state.dwNextStatusProbeTime)
			return;
		if (state.dwLastStatusChatTime != 0 &&
				dwNow - state.dwLastStatusChatTime < 2500)
		{
			state.dwNextStatusProbeTime = state.dwLastStatusChatTime + 2500;
			return;
		}

		// Do not make 350 bots fill the chat window or spend time formatting text
		// nobody can see. A player entering the area gets the current state within
		// three seconds; state changes are otherwise published immediately.
		CCheckNearbyHumanPlayer humanChecker(ch, 2500);
		if (ch->GetSectree())
			ch->GetSectree()->ForEachAround(humanChecker);
		if (!humanChecker.m_bFound)
		{
			state.dwNextStatusProbeTime = dwNow + 3000;
			return;
		}

		char szStatus[160];
		BuildPlayerBotStatusText(ch, state, szStatus, sizeof(szStatus));
		SendPlayerBotOverheadChat(ch, szStatus);
		state.dwLastStatusChatTime = dwNow;
		state.dwNextStatusProbeTime = dwNow + 2500;
		state.dwNextChatTime = dwNow + number(9000, 14000);
		state.bLastStatusAction = state.bCurrentAction;
		state.bLastStatusGoal = state.bLongTermGoal;
		state.bLastStatusTownPhase = relevantTownPhase;
		state.bLastStatusParty = inParty;
		state.dwLastStatusTargetVID = relevantTargetVID;
	}
}

#endif
