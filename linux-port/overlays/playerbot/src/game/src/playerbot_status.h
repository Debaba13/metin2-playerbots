#ifndef __INC_METIN2_PLAYERBOT_STATUS_H__
#define __INC_METIN2_PLAYERBOT_STATUS_H__

// What a bot shows above its head, and the words for it.
//
// 2010 Turkish Metin2 Style overhead messages and status texts (Pure ASCII).

namespace
{
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
						return false;
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
			case BOT_GOAL_SURVIVE: return "hayatta kalma";
			case BOT_GOAL_CHOOSE_PROFESSION: return "beceri secimi";
			case BOT_GOAL_GET_EQUIPMENT: return "ekipman dizme";
			case BOT_GOAL_RESTOCK: return "pot stogu";
			case BOT_GOAL_REFINE: return "arti basma";
			case BOT_GOAL_MASTER_SKILL: return "bk okuma";
			case BOT_GOAL_HUNT_METIN: return "metin kesme";
			case BOT_GOAL_PARTY_CHALLENGE: return "grup ile kasilma";
			case BOT_GOAL_BIOLOGIST: return "biyolog gorevi";
			case BOT_GOAL_HUNTING: return "av gorevi";
			case BOT_GOAL_HORSE: return "at gelistirme";
			case BOT_GOAL_FISHING: return "balik tutma";
			default: return "level kasma";
		}
	}

	const char* GetPlayerBotActionLabel(BYTE action)
	{
		switch (action)
		{
			case BOT_ACTION_TRAVEL: return "yuruyor";
			case BOT_ACTION_FIGHT: return "dovusuyor";
			case BOT_ACTION_LOOT: return "topluyor";
			case BOT_ACTION_RECOVER: return "dinleniyor";
			case BOT_ACTION_TRAIN: return "egitim aliyor";
			case BOT_ACTION_SHOP: return "ticaret yapiyor";
			case BOT_ACTION_REFINE: return "arti basiyor";
			case BOT_ACTION_READ_BOOK: return "bk okuyor";
			case BOT_ACTION_SOCKET_STONE: return "tas basiyor";
			case BOT_ACTION_PARTY_ASSEMBLE: return "pt topluyor";
			case BOT_ACTION_BIOLOGIST: return "biyolog teslim ediyor";
			case BOT_ACTION_STABLE: return "seyise gidiyor";
			case BOT_ACTION_STALL: return "pazar tutuyor";
			case BOT_ACTION_MARKET: return "pazarlari geziyor";
			default: return "bekliyor";
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
			case BOT_TOWN_PHASE_TRAINER: return "Skilleri almaya gidiyom";
			case BOT_TOWN_PHASE_TRAINER_WAIT: return "Beceri seciyom bekle";
			case BOT_TOWN_PHASE_WEAPON_MERCHANT: return "Silahciya gidiyom";
			case BOT_TOWN_PHASE_WEAPON_WAIT: return "Silahciya bakiyom";
			case BOT_TOWN_PHASE_ARMOR_MERCHANT: return "Zirhciya gidiyom";
			case BOT_TOWN_PHASE_ARMOR_WAIT: return "Zirh bakiyom";
			case BOT_TOWN_PHASE_MISC_MERCHANT: return "Saticiya gidiyom";
			case BOT_TOWN_PHASE_MISC_WAIT: return "Kirmizi pot aliyom copleri satiyom";
			case BOT_TOWN_PHASE_BLACKSMITH: return "Demirciye gidiyom dua edin";
			case BOT_TOWN_PHASE_BLACKSMITH_WAIT: return "Demircide arti basiyom";
			case BOT_TOWN_PHASE_GATE_IN:
			case BOT_TOWN_PHASE_GATE_CROSS_IN: return "Koye giriyom";
			case BOT_TOWN_PHASE_GATE_OUT:
			case BOT_TOWN_PHASE_GATE_CROSS_OUT: return "Kasilmaya geri donuyom";
			default: return "Koyde islerimi hallediyom";
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
			snprintf(status, statusSize, "%s%s (Hedef: %s)", prefix,
					GetPlayerBotTownStatusLabel(state), goal);
			return;
		}

		if (state.bTacticalRetreat)
		{
			snprintf(status, statusSize, "%sKaciyom can cok azaldi", prefix);
			return;
		}
		if (state.bRecoveringAfterDeath)
		{
			snprintf(status, statusSize, "%sYerdeyiz yine kalkiyom bekle", prefix);
			return;
		}

		LPCHARACTER target = state.dwTargetVID != 0
				? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		switch (state.bCurrentAction)
		{
			case BOT_ACTION_FIGHT:
				if (target && target->IsStone())
					snprintf(status, statusSize, "%s%s kesiyom ks atmayin", prefix, target->GetName());
				else if (target && target->IsMonster())
				{
					int huntingRemaining = 0;
					const DWORD huntingMob = GetActivePlayerBotHuntingMobVnum(
							ch, &huntingRemaining);
					if (huntingMob != 0 && target->GetRaceNum() == huntingMob)
					{
						snprintf(status, statusSize, "%sAv gorevi: %s (kalan %d)",
								prefix, target->GetName(), huntingRemaining);
						break;
					}
					LPITEM weapon = ch->GetWear(WEAR_WEAPON);
					const bool bow = weapon && weapon->GetType() == ITEM_WEAPON &&
							weapon->GetSubType() == WEAPON_BOW;
					const int range = bow ? 800 : 280;
					const int distance = DISTANCE_APPROX(
							ch->GetX() - target->GetX(), ch->GetY() - target->GetY());
					if (distance > range)
						snprintf(status, statusSize, "%sKacma gel buraya %s", prefix, target->GetName());
					else
						snprintf(status, statusSize, "%sDaliyorum: %s", prefix, target->GetName());
				}
				else
					snprintf(status, statusSize, "%sTemiz slot ariyorum", prefix);
				break;
			case BOT_ACTION_LOOT:
				snprintf(status, statusSize, "%sYere duseni topluyom", prefix);
				break;
			case BOT_ACTION_RECOVER:
				snprintf(status, statusSize, "%sPot basiyom can dolsun", prefix);
				break;
			case BOT_ACTION_TRAIN:
				snprintf(status, statusSize, "%sHocalardan skil seciyom", prefix);
				break;
			case BOT_ACTION_SHOP:
				snprintf(status, statusSize, "%sPazarlik yapiyom", prefix);
				break;
			case BOT_ACTION_REFINE:
				snprintf(status, statusSize, "%sDemircide item basiyom", prefix);
				break;
			case BOT_ACTION_READ_BOOK:
				snprintf(status, statusSize, "%sBK okuyom ins gecer", prefix);
				break;
			case BOT_ACTION_SOCKET_STONE:
				snprintf(status, statusSize, "%sTas basiyom kirilmaz ins", prefix);
				break;
			case BOT_ACTION_PARTY_ASSEMBLE:
				snprintf(status, statusSize, "%sPartiye adam ariyorum", prefix);
				break;
			case BOT_ACTION_BIOLOGIST:
			{
				const TPlayerBotBiologistMission* mission =
						GetActivePlayerBotBiologistMission(ch);
				if (!mission)
					snprintf(status, statusSize, "%sBiyologdan donuyom", prefix);
				else if (state.bVisitingBiologist &&
						DISTANCE_APPROX(ch->GetX() - PLAYERBOT_BIOLOGIST_X,
								ch->GetY() - PLAYERBOT_BIOLOGIST_Y) > 850)
					snprintf(status, statusSize, "%sBiyologa goturuyom: %s", prefix, mission->itemLabel);
				else if (state.bVisitingBiologist)
					snprintf(status, statusSize, "%sBiyologa teslim ediom: %s", prefix, mission->itemLabel);
				else
					snprintf(status, statusSize, "%sBiyolog icin %s topluyom", prefix, mission->itemLabel);
				break;
			}
			case BOT_ACTION_STABLE:
				if (DISTANCE_APPROX(ch->GetX() - PLAYERBOT_STABLE_BOY_X,
						ch->GetY() - PLAYERBOT_STABLE_BOY_Y) > 850)
					snprintf(status, statusSize, "%sSeyise gidiyom madalyon vermeye", prefix);
				else
					snprintf(status, statusSize, "%sMadalyon teslim ediom (%u/21)", prefix,
							(unsigned int)ch->GetHorseLevel());
				break;
			case BOT_ACTION_FISHING:
				if (ch->CountSpecifyItem(PLAYERBOT_FISHING_BAIT_VNUM) <
						PLAYERBOT_FISHING_BAIT_RESTOCK)
					snprintf(status, statusSize, "%sBalikciya solucan almaya gidiyom", prefix);
				else if (DISTANCE_APPROX(ch->GetX() - PLAYERBOT_FISHING_BANK_X,
						ch->GetY() - PLAYERBOT_FISHING_BANK_Y) > 850)
					snprintf(status, statusSize, "%sKiyiya balik tutmaya gidiyom", prefix);
				else if (state.bIsFishing)
					snprintf(status, statusSize, "%sOltayi attim balik bekliyom", prefix);
				else
					snprintf(status, statusSize, "%sOltaya yem takiyom", prefix);
				break;
			case BOT_ACTION_MARKET:
				if (state.dwMarketStallVID != 0)
					snprintf(status, statusSize, "%sPazara bakiyom ne var ne yok", prefix);
				else
					snprintf(status, statusSize, "%sPazarlari geziyom ucuz item var mi", prefix);
				break;
			case BOT_ACTION_TRAVEL:
				if (ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M1 &&
						state.bLongTermGoal == BOT_GOAL_HORSE)
					snprintf(status, statusSize, "%sM2 ye geciyom madalyon lazim", prefix);
				else if (ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M2 &&
						ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) == 0 &&
						state.bLongTermGoal == BOT_GOAL_HORSE)
					snprintf(status, statusSize, "%sMaymun Zindanina gidiyom madalyon kasmaya", prefix);
				else if (ch->CountSpecifyItem(PLAYERBOT_HORSE_MEDAL_VNUM) > 0)
					snprintf(status, statusSize, "%sMadalyon dustu seyise goturuyom", prefix);
				else if (IsPlayerBotMonkeyMap(ch->GetMapIndex()))
					snprintf(status, statusSize, "%sZindandan cikiyom artik", prefix);
				else
					snprintf(status, statusSize, "%sSlotluk yer ariyorum (hedef: %s)", prefix, goal);
				break;
			default:
				snprintf(status, statusSize, "%sPlan: %s", prefix, goal);
				break;
		}
	}

	void ManagePlayerBotStatusOverhead(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (ch && ch->GetMyShop())
			return;
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