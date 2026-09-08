#ifndef __INC_METIN2_PLAYERBOT_STATUS_H__
#define __INC_METIN2_PLAYERBOT_STATUS_H__

// What a bot shows above its head, and the words for it.
//
// This is the only place a bot is described in a player's language rather than
// in the code's. Strings here are Polish and ASCII-only: the client renders
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
			case BOT_GOAL_SURVIVE: return PlayerBotText("regeneracja");
			case BOT_GOAL_CHOOSE_PROFESSION: return PlayerBotText("profesja");
			case BOT_GOAL_GET_EQUIPMENT: return PlayerBotText("ekwipunek");
			case BOT_GOAL_RESTOCK: return PlayerBotText("zapasy");
			case BOT_GOAL_REFINE: return PlayerBotText("ulepszanie");
			case BOT_GOAL_MASTER_SKILL: return PlayerBotText("rozwoj skilla");
			case BOT_GOAL_HUNT_METIN: return PlayerBotText("Metiny");
			case BOT_GOAL_PARTY_CHALLENGE: return PlayerBotText("silne moby PT");
			case BOT_GOAL_BIOLOGIST: return PlayerBotText("Biolog");
			case BOT_GOAL_HUNTING: return PlayerBotText("Polowanie");
			case BOT_GOAL_HORSE: return PlayerBotText("rozwoj konia");
			case BOT_GOAL_FISHING: return PlayerBotText("lowienie ryb");
			default: return PlayerBotText("poziom");
		}
	}

	// The map a player would name, not the one the code names. Used by the
	// travel line, which used to announce every journey as a hunt for
	// experience whatever the errand actually was.
	// Polish declines the destination, so the table carries the phrase that
	// follows "ide" rather than the bare name: "Ide na Dolina Orkow" is not a
	// sentence anybody would write.
	const char* GetPlayerBotMapDestinationPl(long mapIndex)
	{
		switch (mapIndex)
		{
			case PLAYERBOT_MAP_CHUNJO_M1: return "do Joan";
			case PLAYERBOT_MAP_CHUNJO_M2: return "do Bokjung";
			case PLAYERBOT_MAP_CHUNJO_M3: return "do Pyungmoo";
			case PLAYERBOT_MAP_MONKEY_EASY: return "do Lochu Malp";
			case PLAYERBOT_MAP_MONKEY_MEDIUM: return "do Lochu Malp II";
			case PLAYERBOT_MAP_MONKEY_HARD: return "do Lochu Malp III";
			case PLAYERBOT_MAP_DESERT: return "na Pustynie Yongbi";
			case PLAYERBOT_MAP_ORC_VALLEY: return "do Doliny Orkow";
			case PLAYERBOT_MAP_SOHAN: return "na Gore Sohan";
			case PLAYERBOT_MAP_SPIDER_V1: return "do Lochu Pajakow";
			case PLAYERBOT_MAP_HWANG: return "do Swiatyni Hwang";
			default: return "";
		}
	}

	const char* GetPlayerBotActionLabel(BYTE action)
	{
		switch (action)
		{
			case BOT_ACTION_TRAVEL: return PlayerBotText("ide");
			case BOT_ACTION_FIGHT: return PlayerBotText("walcze");
			case BOT_ACTION_LOOT: return PlayerBotText("zbieram");
			case BOT_ACTION_RECOVER: return PlayerBotText("odpoczywam");
			case BOT_ACTION_TRAIN: return PlayerBotText("wybieram profesje");
			case BOT_ACTION_SHOP: return PlayerBotText("handluje");
			case BOT_ACTION_REFINE: return PlayerBotText("ulepszam");
			case BOT_ACTION_READ_BOOK: return PlayerBotText("czytam KU");
			case BOT_ACTION_SOCKET_STONE: return PlayerBotText("wkladam KD");
			case BOT_ACTION_PARTY_ASSEMBLE: return PlayerBotText("zbieram PT");
			case BOT_ACTION_BIOLOGIST: return PlayerBotText("robie misje Biologa");
			case BOT_ACTION_STABLE: return PlayerBotText("odwiedzam Stajennego");
			case BOT_ACTION_STALL: return PlayerBotText("prowadze stragan");
			case BOT_ACTION_MARKET: return PlayerBotText("jestem na zakupach");
			case BOT_ACTION_LURE: return "podciagam moby dla PT";
			case BOT_ACTION_TOWN_REST: return "chodze po straganach";
			default: return PlayerBotText("mysle");
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
			case BOT_TOWN_PHASE_TRAINER: return PlayerBotText("Ide po profesje");
			case BOT_TOWN_PHASE_TRAINER_WAIT: return PlayerBotText("Wybieram profesje");
			case BOT_TOWN_PHASE_WEAPON_MERCHANT: return PlayerBotText("Ide do handlarza bronia");
			case BOT_TOWN_PHASE_WEAPON_WAIT: return PlayerBotText("Handluje bronia");
			case BOT_TOWN_PHASE_ARMOR_MERCHANT: return PlayerBotText("Ide do handlarza zbroja");
			case BOT_TOWN_PHASE_ARMOR_WAIT: return PlayerBotText("Handluje zbroja");
			case BOT_TOWN_PHASE_MISC_MERCHANT: return PlayerBotText("Ide do handlarki roznosci");
			case BOT_TOWN_PHASE_MISC_WAIT: return PlayerBotText("Kupuje potki i sprzedaje lup");
			case BOT_TOWN_PHASE_BLACKSMITH: return PlayerBotText("Ide do kowala");
			case BOT_TOWN_PHASE_BLACKSMITH_WAIT: return PlayerBotText("Ulepszam ekwipunek");
			case BOT_TOWN_PHASE_GATE_IN:
			case BOT_TOWN_PHASE_GATE_CROSS_IN: return PlayerBotText("Ide do miasta");
			case BOT_TOWN_PHASE_GATE_OUT:
			case BOT_TOWN_PHASE_GATE_CROSS_OUT: return PlayerBotText("Wracam na exp");
			default: return PlayerBotText("Zalatwiam sprawy w miescie");
		}
	}

	void BuildPlayerBotStatusText(LPCHARACTER ch, const TPlayerBotAIState& state,
			char* status, size_t statusSize)
	{
		if (!ch || !status || statusSize == 0)
			return;

		const char* prefix = ch->GetParty() ? "[PT] " : "";
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
				snprintf(status, statusSize, "%s%s - potki %u/%u", prefix,
						GetPlayerBotTownStatusLabel(state),
						(unsigned int)redCount, (unsigned int)blueCount);
				return;
			}
			snprintf(status, statusSize, "%s%s (cel: %s)", prefix,
					GetPlayerBotTownStatusLabel(state), goal);
			return;
		}

		if (state.bTacticalRetreat)
		{
			snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Uciekam - mam malo HP"));
			return;
		}
		// An errand the watchdog interrupted, and the map the bot still means to
		// leave for. The audit asked for exactly this pair - "Uzupelniam
		// mikstury; potem Sohan" - because an observer cannot otherwise tell a
		// bot that is stuck from one that is waiting.
		if (state.bServicePending)
		{
			const char* where = state.lDepartureMap != 0
					? GetPlayerBotMapDestinationPl(state.lDepartureMap) : "";
			if (where[0])
				snprintf(status, statusSize, "%sCzekam na trase do handlarza; potem %s",
						prefix, where);
			else
				snprintf(status, statusSize, "%sCzekam na trase do handlarza", prefix);
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
					snprintf(status, statusSize, "%sSzykuje lur dla druzyny", prefix);
					return;
				case LURE_STAGE_RETURN:
					snprintf(status, statusSize, "%sWracam do druzyny: prowadze %d mobow",
							prefix, state.iLureChasing);
					return;
				case LURE_STAGE_HANDOFF:
					snprintf(status, statusSize, "%sPrzekazuje moby: %d przyprowadzonych, %d nadal za mna",
							prefix, state.iLureDelivered, state.iLureChasing);
					return;
				case LURE_STAGE_RECOVER:
					snprintf(status, statusSize, "%sWstrzymuje lur: druzyna jeszcze walczy", prefix);
					return;
				default:
					snprintf(status, statusSize, "%sLuruje dla PT: %u/%u grupy, sciga mnie %d",
							prefix, (unsigned int)state.bLureGroupsTagged,
							(unsigned int)state.bLureGroupsPlanned, state.iLureChasing);
					return;
			}
		}
		if (state.bRecoveringAfterDeath)
		{
			snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Odpoczywam po smierci"));
			return;
		}

		LPCHARACTER target = state.dwTargetVID != 0
				? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		switch (state.bCurrentAction)
		{
			case BOT_ACTION_FIGHT:
				if (target && target->IsStone())
					FormatPlayerBotText(status, statusSize, prefix, "Rozbijam %s", target->GetName());
				else if (target && target->IsMonster())
				{
					int huntingRemaining = 0;
					const DWORD huntingMob = GetActivePlayerBotHuntingMobVnum(
							ch, &huntingRemaining);
					if (huntingMob != 0 && target->GetRaceNum() == huntingMob)
					{
						FormatPlayerBotText(status, statusSize, prefix, "Polowanie: %s (zostalo %d)",
								target->GetName(), huntingRemaining);
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
						snprintf(status, statusSize, "%sBronie sie przed %s", prefix,
								target->GetName());
					else if (state.bLastCombatReason ==
							(BYTE)playerbot_combat_value::ALLOW_PARTY_DEFENSE)
						snprintf(status, statusSize, "%sPomagam druzynie: %s", prefix,
								target->GetName());
					else if (state.bLastCombatReason ==
							(BYTE)playerbot_combat_value::ALLOW_MATERIAL)
						snprintf(status, statusSize, "%sZbieram material z %s", prefix,
								target->GetName());
					else if (distance > range)
						FormatPlayerBotText(status, statusSize, prefix, "Gonie %s", target->GetName());
					else
						FormatPlayerBotText(status, statusSize, prefix, "Walcze z %s", target->GetName());
				}
				else
						snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Szukam przeciwnika"));
				break;
			case BOT_ACTION_LOOT:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Podnosze lup"));
				break;
			case BOT_ACTION_RECOVER:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Regeneruje HP"));
				break;
			case BOT_ACTION_TRAIN:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Wybieram profesje"));
				break;
			case BOT_ACTION_SHOP:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Handluje"));
				break;
			case BOT_ACTION_REFINE:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Ulepszam ekwipunek"));
				break;
			case BOT_ACTION_READ_BOOK:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Czytam ksiege umiejetnosci"));
				break;
			case BOT_ACTION_SOCKET_STONE:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Wkladam kamien duszy"));
				break;
			case BOT_ACTION_PARTY_ASSEMBLE:
				snprintf(status, statusSize, "%s%s", prefix, PlayerBotText("Szukam celu dla grupy"));
				break;
			case BOT_ACTION_BIOLOGIST:
			{
				const TPlayerBotBiologistMission* mission =
						GetActivePlayerBotBiologistMission(ch);
				if (!mission)
					snprintf(status, statusSize, "%sWracam od Biologa", prefix);
				else if (state.bVisitingBiologist &&
						DISTANCE_APPROX(ch->GetX() - PLAYERBOT_BIOLOGIST_X,
								ch->GetY() - PLAYERBOT_BIOLOGIST_Y) > 850)
					snprintf(status, statusSize, "%sIde do Biologa z: %s", prefix, mission->itemLabel);
				else if (state.bVisitingBiologist)
					snprintf(status, statusSize, "%sOddaje Biologowi: %s", prefix, mission->itemLabel);
				else
					snprintf(status, statusSize, "%sZbieram dla Biologa: %s", prefix, mission->itemLabel);
				break;
			}
			case BOT_ACTION_STABLE:
				if (DISTANCE_APPROX(ch->GetX() - PLAYERBOT_STABLE_BOY_X,
						ch->GetY() - PLAYERBOT_STABLE_BOY_Y) > 850)
					snprintf(status, statusSize, "%sIde do Stajennego z medalem", prefix);
				else
					snprintf(status, statusSize, "%sOddaje medal konny (%u/21)", prefix,
							(unsigned int)ch->GetHorseLevel());
				break;
			case BOT_ACTION_FISHING:
				if (ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM) <
						PLAYERBOT_FISHING_BAIT_RESTOCK)
					snprintf(status, statusSize, "%sIde do Rybaka po przynete", prefix);
				else if (DISTANCE_APPROX(ch->GetX() - PLAYERBOT_FISHING_BANK_X,
						ch->GetY() - PLAYERBOT_FISHING_BANK_Y) >
						PLAYERBOT_FISHING_BANK_RADIUS)
					snprintf(status, statusSize, "%sIde nad rzeke lowic ryby", prefix);
				else if (state.bIsFishing)
					snprintf(status, statusSize, "%sLowie ryby - czekam na branie", prefix);
				else if (!IsPlayerBotHoldingRod(ch))
					// The old text here was a plain else, so an angler standing at
					// the water with no rod on its back announced that it was
					// baiting one - which is what got reported as "bots put bait
					// on weapons". Nothing was ever put on a weapon; the label
					// was simply wrong about what the bot was doing.
					snprintf(status, statusSize, "%sSzukam wedki", prefix);
				else
					snprintf(status, statusSize, "%sZakladam przynete na wedke", prefix);
				break;
			case BOT_ACTION_TOWN_REST:
				snprintf(status, statusSize, "%sOgladam stragany", prefix);
				break;
			case BOT_ACTION_MARKET:
				if (state.dwMarketStallVID != 0)
					snprintf(status, statusSize, "%sOgladam stragan", prefix);
				else
					snprintf(status, statusSize, "%sSzukam czegos na straganach", prefix);
				break;
			case BOT_ACTION_TRAVEL:
				if (ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M1 &&
						state.bLongTermGoal == BOT_GOAL_HORSE)
					snprintf(status, statusSize, "%sIde przez portal do M2 po Medal Konny", prefix);
				else if (ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M2 &&
						ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) == 0 &&
						state.bLongTermGoal == BOT_GOAL_HORSE)
					snprintf(status, statusSize, "%sIde do Lochu Malp po Medal Konny", prefix);
				else if (ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) > 0)
					snprintf(status, statusSize, "%sIde do najblizszego Stajennego z Medalem", prefix);
				else if (IsPlayerBotMonkeyMap(ch->GetMapIndex()))
					snprintf(status, statusSize, "%sWychodze z Lochu Malp", prefix);
				// "Szukam miejsca do expa (cel: zapasy)" was said over a bot
				// walking to a merchant, which is the audit's example of a
				// status that describes an action without its purpose. Say
				// where the bot is going, and when the errand is not experience,
				// say the errand instead.
				else if (state.bLongTermGoal == BOT_GOAL_RESTOCK)
					snprintf(status, statusSize, "%sIde do miasta po zapasy", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_REFINE)
					snprintf(status, statusSize, "%sIde do kowala ulepszyc ekwipunek", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_BIOLOGIST)
					snprintf(status, statusSize, "%sIde do Biologa", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_FISHING)
					snprintf(status, statusSize, "%sIde nad rzeke lowic ryby", prefix);
				else if (state.bLongTermGoal == BOT_GOAL_GET_EQUIPMENT)
					snprintf(status, statusSize, "%sIde do miasta po ekwipunek", prefix);
				else
				{
					const long wantMap = GetPlayerBotFrontierMapForLevel(ch);
					const char* where = wantMap != 0 && wantMap != ch->GetMapIndex()
							? GetPlayerBotMapDestinationPl(wantMap) : "";
					if (where[0])
						snprintf(status, statusSize, "%sIde %s (cel: %s)", prefix,
								where, goal);
					else
						snprintf(status, statusSize, "%sSzukam lepszego miejsca (cel: %s)",
								prefix, goal);
				}
				break;
			default:
				snprintf(status, statusSize, "%sPlanuje: %s", prefix, goal);
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
