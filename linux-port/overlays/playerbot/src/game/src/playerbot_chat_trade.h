#ifndef __INC_METIN2_PLAYERBOT_CHAT_TRADE_H__
#define __INC_METIN2_PLAYERBOT_CHAT_TRADE_H__

// Trading over the chat: what a bot shouts about its counter and its wants,
// and what it whispers back when a player shouts "Kupie ..." or "Sprzedam ...".
//
// The market already exists - counters in Joan and Bokjung, a ledger of who
// is short of what - but a player only found out by walking the ring. A
// player on a real server finds out from the shout channel, and answers a
// shout with a whisper, and that is the shape copied here: a bot that opens
// a counter with something worth crossing town for says so once, a bot that
// walked the market for a material and found none asks for it once, and a
// player's own shout is read for the two words that matter and answered by
// the one bot best placed to answer - the nearest counter that has the
// thing, or a bot that is short of it.
//
// The engine side of this is patch 0007: CInputMain::Chat hands a player's
// shout to CPlayerBotManager::OnPlayerShout after it has gone out, and
// CInputMain::Whisper hands a whisper addressed to a bot to OnPlayerWhisper
// instead of writing it to a descriptor with no client behind it. Both are
// one call each; everything they call is here.
//
// Text is CP1250, which is what the Polish client sends and what the item
// names in the proto are written in. Matching folds both sides to lowercase
// ASCII so "Kupię Kość Niedźwiedzia" finds "Kość Niedźwiedzia" whether or not
// the player bothered with the diacritics. What a bot says is ASCII, as
// everywhere else; the item names it quotes are the proto's own.
//
// An implementation fragment in the sense playerbot_types.h describes:
// include it exactly once, after playerbot_market.h - it reads the counters
// the way a shopping bot does, and the market's own helpers for what a bot
// wants.

namespace
{
	// One trade shout on the world channel this often, whoever it is from,
	// and one from any single bot this often. The refine announcements run at
	// one every three minutes; with these the channel carries a line a minute
	// at the most, which reads as a market and not as a wall.
	const DWORD PLAYERBOT_TRADE_SHOUT_INTERVAL = 90000;
	const DWORD PLAYERBOT_TRADE_SHOUT_BOT_INTERVAL = 1200000;
	// A player gets one whispered answer this often, so a shout repeated
	// twice does not bring two bots to the same door.
	const DWORD PLAYERBOT_TRADE_REPLY_INTERVAL = 8000;
	// get_dword_time() is expressed in milliseconds.
	const DWORD PLAYERBOT_PLAYER_MESSAGE_HOLD_TIME = 15000;
	// World coordinates use roughly 10 units per metre; keep a contacted bot
	// within about ten metres before it stops for the conversation hold.
	const int PLAYERBOT_PLAYER_MESSAGE_APPROACH_DISTANCE = 100;
	// Fewer letters than this after the verb is not a thing anybody meant.
	const size_t PLAYERBOT_TRADE_QUERY_MIN = 3;
	// The skill books the proto names one skill each - "Instr. Aura Miecza",
	// value 0 the skill - which is the only place the server has a skill's
	// Polish name. skill_proto holds the Korean ones.
	const DWORD PLAYERBOT_TRADE_SKILL_BOOK_FIRST = 50401;
	const DWORD PLAYERBOT_TRADE_SKILL_BOOK_LAST = 50511;

	DWORD s_dwPlayerBotTradeShoutTime = 0;
	std::map<DWORD, DWORD> s_mapPlayerBotTradeShoutTime;
	std::map<DWORD, DWORD> s_mapPlayerBotConversationHoldUntil;
	std::map<DWORD, LPCHARACTER> s_mapPlayerBotConversationPlayer;

	void HoldPlayerBotForPlayerMessage(LPCHARACTER bot, LPCHARACTER player = NULL)
	{
		if (!bot)
			return;
		s_mapPlayerBotConversationHoldUntil[bot->GetPlayerID()] =
				get_dword_time() + PLAYERBOT_PLAYER_MESSAGE_HOLD_TIME;
		if (player)
			s_mapPlayerBotConversationPlayer[bot->GetPlayerID()] = player;
	}

	bool IsPlayerBotConversationHeld(DWORD playerID, DWORD dwNow)
	{
		std::map<DWORD, DWORD>::const_iterator it =
				s_mapPlayerBotConversationHoldUntil.find(playerID);
		return it != s_mapPlayerBotConversationHoldUntil.end() && it->second > dwNow;
	}

	LPCHARACTER GetPlayerBotConversationPlayer(DWORD playerID)
	{
		std::map<DWORD, LPCHARACTER>::const_iterator it =
				s_mapPlayerBotConversationPlayer.find(playerID);
		return it != s_mapPlayerBotConversationPlayer.end() ? it->second : NULL;
	}
	std::map<DWORD, DWORD> s_mapPlayerBotTradeReplyTime;
	struct TPlayerBotDeferredPriceQuestion
	{
		LPCHARACTER player;
		LPCHARACTER bot;
		char text[CHAT_MAX_LEN + 1];
		TPlayerBotDeferredPriceQuestion() : player(NULL), bot(NULL)
		{
			text[0] = 0;
		}
	};
	std::map<DWORD, TPlayerBotDeferredPriceQuestion> s_mapPlayerBotDeferredPriceQuestions;
	struct TPlayerBotPendingTrade
	{
		LPCHARACTER bot;
		WORD cell;
		DWORD price;
		DWORD expires;
		bool botBuys;
		bool confirmed;
		TPlayerBotPendingTrade()
			: bot(NULL), cell(0), price(0), expires(0), botBuys(false), confirmed(false) {}
	};
	std::map<DWORD, TPlayerBotPendingTrade> s_mapPlayerBotPendingTrades;
	std::string DescribePlayerBotItem(LPITEM item);

	std::string FormatPlayerBotYang(DWORD yang)
	{
		char formatted[64];
		if (yang >= 1000000)
		{
			const DWORD millions = yang / 1000000;
			const DWORD thousands = (yang % 1000000) / 1000;
			if (thousands > 0)
				snprintf(formatted, sizeof(formatted), "%uM %uk", millions, thousands);
			else
				snprintf(formatted, sizeof(formatted), "%uM", millions);
		}
		else if (yang >= 1000)
		{
			snprintf(formatted, sizeof(formatted), "%uk", yang / 1000);
		}
		else
		{
			snprintf(formatted, sizeof(formatted), "%u", yang);
		}
		return formatted;
	}

	void RememberPlayerBotPendingBuy(LPCHARACTER player, LPCHARACTER bot, DWORD price)
	{
		if (!player || !bot)
			return;
		TPlayerBotPendingTrade pending;
		pending.bot = bot;
		pending.price = price;
		pending.expires = get_dword_time() + 120000;
		pending.botBuys = true;
		s_mapPlayerBotPendingTrades[player->GetPlayerID()] = pending;
	}

	const char* GetPlayerBotTownName(long mapIndex)
	{
		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M1)
			return "Joan";
		if (mapIndex == PLAYERBOT_MAP_CHUNJO_M2)
			return "Bokjung";
		return PlayerBotText("miescie");
	}

	// Lowercase ASCII from CP1250: the Polish letters go to their base, the
	// rest of the high half to '?', so a name compares the same however it
	// was typed.
	void FoldPlayerBotChatText(const char* in, char* out, size_t size)
	{
		size_t o = 0;
		for (const unsigned char* p = (const unsigned char*)(in ? in : ""); *p && o + 1 < size; ++p)
		{
			unsigned char c = *p;
			if (p[0] == 0xC3 && p[1] != 0)
			{
				switch (p[1])
				{
					case 0x87: case 0xA7: c = 'c'; ++p; break;
					case 0x96: case 0xB6: c = 'o'; ++p; break;
					case 0x9C: case 0xBC: c = 'u'; ++p; break;
					default: break;
				}
			}
			else if (p[0] == 0xC4 && p[1] != 0)
			{
				switch (p[1])
				{
					case 0x9E: case 0x9F: c = 'g'; ++p; break;
					case 0xB0: case 0xB1: c = 'i'; ++p; break;
					default: break;
				}
			}
			else if (p[0] == 0xC5 && p[1] != 0 &&
					(p[1] == 0x9E || p[1] == 0x9F))
			{
				c = 's';
				++p;
			}
			switch (c)
			{
				case 0xC7: case 0xE7: case 0xA7: c = 'c'; break;
				case 0xD0: case 0xF0: c = 'g'; break;
				case 0xDD: case 0xFD: c = 'i'; break;
				case 0xD6: case 0xF6: c = 'o'; break;
				case 0xDE: case 0xFE: c = 's'; break;
				case 0xDC: case 0xFC: c = 'u'; break;
				case 0xA5: case 0xB9: c = 'a'; break;
				case 0xC6: case 0xE6: c = 'c'; break;
				case 0xCA: case 0xEA: c = 'e'; break;
				case 0xA3: case 0xB3: c = 'l'; break;
				case 0xD1: case 0xF1: c = 'n'; break;
				case 0xD3: case 0xF3: c = 'o'; break;
				case 0x8C: case 0x9C: c = 's'; break;
				case 0x8F: case 0x9F: case 0xAF: case 0xBF: c = 'z'; break;
				default:
					if (c >= 'A' && c <= 'Z')
						c = (unsigned char)(c - 'A' + 'a');
					else if (c >= 0x80)
						c = '?';
					break;
			}
			out[o++] = (char)c;
		}
		out[o] = 0;
	}

	bool IsPlayerBotChatSeparator(char c)
	{
		return c == ' ' || c == '\t' || c == ':' || c == ',' || c == '.' || c == '!' ||
				c == '?' || c == '-' || c == '"' || c == '\'';
	}

	// The whisper the client shows as one from the bot: the same packet
	// CInputMain::Whisper builds for a player, with the bot's name as sender.
	void SendPlayerBotWhisper(LPCHARACTER bot, LPCHARACTER to, const char* text)
	{
		if (!bot || !to || !to->GetDesc() || !text || !*text)
			return;
		HoldPlayerBotForPlayerMessage(bot, to);
		const size_t len = std::min<size_t>(strlen(text), CHAT_MAX_LEN);
		TPacketGCWhisper pack;
		pack.bHeader = HEADER_GC_WHISPER;
		pack.bType = WHISPER_TYPE_NORMAL;
		pack.wSize = (WORD)(sizeof(TPacketGCWhisper) + len);
		strlcpy(pack.szNameFrom, bot->GetName(), sizeof(pack.szNameFrom));
		TEMP_BUFFER tmpbuf;
		tmpbuf.write(&pack, sizeof(pack));
		tmpbuf.write(text, (int)len);
		to->GetDesc()->Packet(tmpbuf.read_peek(), tmpbuf.size());
		sys_log(0, "PLAYERBOT_TRADE: whisper pid=%u name=%s to=%s text=\"%s\"",
				bot->GetPlayerID(), bot->GetName(), to->GetName(), text);
	}

	// A line on the world channel in the bot's name, within the two throttles.
	bool ShoutPlayerBotTrade(LPCHARACTER bot, const char* text, DWORD dwNow)
	{
		if (!bot || !text || !*text)
			return false;
		if (s_dwPlayerBotTradeShoutTime != 0 &&
				dwNow - s_dwPlayerBotTradeShoutTime < PLAYERBOT_TRADE_SHOUT_INTERVAL)
			return false;
		DWORD& last = s_mapPlayerBotTradeShoutTime[bot->GetPlayerID()];
		if (last != 0 && dwNow - last < PLAYERBOT_TRADE_SHOUT_BOT_INTERVAL)
			return false;
		s_dwPlayerBotTradeShoutTime = last = dwNow;
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "%s : %s", bot->GetName(), text);
		SendShout(msg, bot->GetEmpire());
		sys_log(0, "PLAYERBOT_TRADE: shout pid=%u name=%s text=\"%s\"",
				bot->GetPlayerID(), bot->GetName(), text);
		return true;
	}

	// The counter just opened with something worth crossing town for; the
	// keeper says so. Called from the stall code with the headline item.
	void AnnouncePlayerBotStall(LPCHARACTER ch, const char* pszItemName)
	{
		if (!ch || !pszItemName || !*pszItemName)
			return;
		char text[CHAT_MAX_LEN + 1];
		FormatPlayerBotText(text, sizeof(text), "",
				"Satilik %s - %s'te pazar", pszItemName,
				GetPlayerBotTownName(ch->GetMapIndex()));
		ShoutPlayerBotTrade(ch, text, get_dword_time());
	}

	// The bot walked the market for a material and found none: it asks. Called
	// from the market code when a trip ends with nothing on offer.
	void AnnouncePlayerBotNeed(LPCHARACTER ch)
	{
		if (!ch)
			return;
		std::set<DWORD> wanted;
		CollectPlayerBotWantedMaterials(ch, wanted);
		if (wanted.empty())
			return;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(*wanted.begin());
		if (!proto)
			return;
		char text[CHAT_MAX_LEN + 1];
		FormatPlayerBotText(text, sizeof(text), "",
				"%s ariyorum - kimde varsa %s'te pazara koysun", proto->szLocaleName,
				GetPlayerBotTownName(ch->GetMapIndex()));
		ShoutPlayerBotTrade(ch, text, get_dword_time());
	}

	// The skill a folded name means, from the per-skill books' names.
	DWORD FindPlayerBotSkillByName(const char* foldedQuery)
	{
		if (!foldedQuery || strlen(foldedQuery) < PLAYERBOT_TRADE_QUERY_MIN)
			return 0;
		for (DWORD vnum = PLAYERBOT_TRADE_SKILL_BOOK_FIRST; vnum <= PLAYERBOT_TRADE_SKILL_BOOK_LAST; ++vnum)
		{
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
			if (!proto || proto->bType != ITEM_SKILLBOOK)
				continue;
			char name[64];
			FoldPlayerBotChatText(proto->szLocaleName, name, sizeof(name));
			const char* p = name;
			if (strncmp(p, "instr. ", 7) == 0)
				p += 7;
			if (strstr(p, foldedQuery) || strstr(foldedQuery, p))
				return (DWORD)proto->alValues[0];
		}
		return 0;
	}

	// The Polish name of a skill, for a bot's own line about it.
	const char* GetPlayerBotSkillName(DWORD skillVnum)
	{
		for (DWORD vnum = PLAYERBOT_TRADE_SKILL_BOOK_FIRST; vnum <= PLAYERBOT_TRADE_SKILL_BOOK_LAST; ++vnum)
		{
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
			if (proto && proto->bType == ITEM_SKILLBOOK && (DWORD)proto->alValues[0] == skillVnum)
				return strncmp(proto->szLocaleName, "Instr. ", 7) == 0
						? proto->szLocaleName + 7 : proto->szLocaleName;
		}
		return "?";
	}

	bool PlayerBotItemNameMatches(LPITEM item, const char* foldedQuery)
	{
		if (!item || !item->GetProto())
			return false;
		char name[64];
		FoldPlayerBotChatText(item->GetProto()->szLocaleName, name, sizeof(name));
		if (item->GetType() == ITEM_SKILLBOOK &&
				(!strcmp(foldedQuery, "bk") || !strcmp(foldedQuery, "ku") ||
				 !strcmp(foldedQuery, "beceri kitabi") ||
				 !strcmp(foldedQuery, "skill kitabi") ||
				 !strcmp(foldedQuery, "skill book")))
			return true;
		struct TTurkishMarketAlias
		{
			const char* alias;
			const char* names[5];
		};
		static const TTurkishMarketAlias aliases[] = {
			{ "kdp", { "kirmizi demir pala", "red iron blade",
				"czerwone ostrze", "czerwony miecz", NULL } },
			{ "gby", { "geyik boynuzu yay", "horn bow",
				"luk z jeleniego rogu", "rog jelenia", NULL } },
			{ "syh", { "siyah yaprak hanceri", "black leaf dagger",
				"czarny sztylet", "czarny lisc", NULL } },
			{ "kutsama", { "kutsama kagidi", "blessing paper",
				"papier egzorcyzmu", "papier blogoslawienstwa", NULL } },
			{ "kagit", { "kutsama kagidi", "exorcism scroll",
				"blessing paper", "papier egzorcyzmu", NULL } },
			{ "dolu", { "dolunay", "dolunay kilici", "full moon sword",
				"miecz pelni ksiezyca", NULL } },
			{ "dolunay", { "dolunay", "dolunay kilici", "full moon sword",
				"miecz pelni ksiezyca", NULL } }
		};
		for (size_t i = 0; i < sizeof(aliases) / sizeof(aliases[0]); ++i)
		{
			if (strcmp(foldedQuery, aliases[i].alias) != 0)
				continue;
			for (size_t k = 0; k < sizeof(aliases[i].names) / sizeof(aliases[i].names[0]); ++k)
				if (aliases[i].names[k] && strstr(name, aliases[i].names[k]))
					return true;
		}
		if (strstr(name, foldedQuery) != NULL)
			return true;
		char acronym[32];
		size_t acronymSize = 0;
		bool atWordStart = true;
		for (const char* p = name; *p && acronymSize + 1 < sizeof(acronym); ++p)
		{
			if (IsPlayerBotChatSeparator(*p))
			{
				atWordStart = true;
				continue;
			}
			if (atWordStart)
			{
				acronym[acronymSize++] = *p;
				atWordStart = false;
			}
		}
		acronym[acronymSize] = 0;
		return strcmp(acronym, foldedQuery) == 0;
	}

	enum EPlayerBotTradeVerb
	{
		PLAYERBOT_TRADE_NONE,
		PLAYERBOT_TRADE_BUY,
		PLAYERBOT_TRADE_SELL
	};

	// "Kupię KU Aura", "sprzedam kosc niedzwiedzia", "Szukam Amuletu Orka":
	// the verb, whether a skill book is meant, and the rest folded.
	EPlayerBotTradeVerb ParsePlayerBotTradeText(const char* text, char* outQuery,
			size_t size, bool& outBook)
	{
		outQuery[0] = 0;
		outBook = false;
		char folded[CHAT_MAX_LEN + 1];
		FoldPlayerBotChatText(text, folded, sizeof(folded));
		char* suffixVerb = NULL;
		EPlayerBotTradeVerb suffixType = PLAYERBOT_TRADE_NONE;
		static const struct { const char* word; EPlayerBotTradeVerb verb; } kSuffixes[] = {
			{ " alinir", PLAYERBOT_TRADE_BUY }, { " alin", PLAYERBOT_TRADE_BUY },
			{ " alirim", PLAYERBOT_TRADE_BUY }, { " aranir", PLAYERBOT_TRADE_BUY },
			{ " satilir", PLAYERBOT_TRADE_SELL }
		};
		for (size_t i = 0; i < sizeof(kSuffixes) / sizeof(kSuffixes[0]); ++i)
		{
			char* found = strstr(folded, kSuffixes[i].word);
			if (found && (!suffixVerb || found > suffixVerb))
			{
				suffixVerb = found;
				suffixType = kSuffixes[i].verb;
			}
		}
		if (suffixVerb)
		{
			*suffixVerb = 0;
			while (suffixVerb > folded && IsPlayerBotChatSeparator(suffixVerb[-1]))
				*--suffixVerb = 0;
		}
		const char* p = folded;
		while (*p && IsPlayerBotChatSeparator(*p))
			++p;
		static const struct { const char* word; EPlayerBotTradeVerb verb; } kVerbs[] = {
			{ "kupie", PLAYERBOT_TRADE_BUY }, { "kupuje", PLAYERBOT_TRADE_BUY },
			{ "szukam", PLAYERBOT_TRADE_BUY }, { "potrzebuje", PLAYERBOT_TRADE_BUY },
			{ "alinir", PLAYERBOT_TRADE_BUY }, { "alin", PLAYERBOT_TRADE_BUY },
			{ "alirim", PLAYERBOT_TRADE_BUY }, { "aranir", PLAYERBOT_TRADE_BUY },
			{ "sprzedam", PLAYERBOT_TRADE_SELL }, { "sprzedaje", PLAYERBOT_TRADE_SELL },
			{ "satilir", PLAYERBOT_TRADE_SELL },
			{ "oddam", PLAYERBOT_TRADE_SELL }, { "s>", PLAYERBOT_TRADE_SELL },
			{ "k>", PLAYERBOT_TRADE_BUY },
		};
		EPlayerBotTradeVerb verb = suffixVerb ? suffixType : PLAYERBOT_TRADE_NONE;
		for (size_t i = 0; i < sizeof(kVerbs) / sizeof(kVerbs[0]); ++i)
		{
			const size_t len = strlen(kVerbs[i].word);
			if (strncmp(p, kVerbs[i].word, len) == 0 &&
					(p[len] == 0 || IsPlayerBotChatSeparator(p[len])))
			{
				verb = kVerbs[i].verb;
				p += len;
				break;
			}
		}
		if (verb == PLAYERBOT_TRADE_NONE)
			return verb;
		while (*p && IsPlayerBotChatSeparator(*p))
			++p;
		if (strncmp(p, "ku ", 3) == 0 || strncmp(p, "bk ", 3) == 0 ||
				strncmp(p, "beceri kitabi ", 14) == 0 ||
				strncmp(p, "skill kitabi ", 13) == 0 ||
				strncmp(p, "skill book ", 12) == 0)
		{
			outBook = true;
			if (strncmp(p, "beceri kitabi ", 14) == 0)
				p += 14;
			else if (strncmp(p, "skill kitabi ", 13) == 0)
				p += 13;
			else if (strncmp(p, "skill book ", 12) == 0)
				p += 12;
			else
				p += 3;
		}
		else if (strncmp(p, "ksiege ", 7) == 0 || strncmp(p, "ksiega ", 7) == 0 ||
				strncmp(p, "ksiegi ", 7) == 0)
		{
			outBook = true;
			p += 7;
		}
		while (*p && IsPlayerBotChatSeparator(*p))
			++p;
		strlcpy(outQuery, p, size);
		size_t n = strlen(outQuery);
		while (n > 0 && IsPlayerBotChatSeparator(outQuery[n - 1]))
			outQuery[--n] = 0;
		// "kdp alinir" and "kdp satilir" can contain the verb twice.
		const char* trailingVerbs[] = {
			" alinir", " alin", " alirim", " aranir", " satilir"
		};
		for (size_t i = 0; i < sizeof(trailingVerbs) / sizeof(trailingVerbs[0]); ++i)
		{
			char* trailing = strstr(outQuery, trailingVerbs[i]);
			if (trailing)
			{
				*trailing = 0;
				n = strlen(outQuery);
				while (n > 0 && IsPlayerBotChatSeparator(outQuery[n - 1]))
					outQuery[--n] = 0;
				break;
			}
		}
		return n >= PLAYERBOT_TRADE_QUERY_MIN ? verb : PLAYERBOT_TRADE_NONE;
	}

	DWORD ParsePlayerBotChatPrice(const char* text)
	{
		char folded[CHAT_MAX_LEN + 1];
		FoldPlayerBotChatText(text, folded, sizeof(folded));
		DWORD parsed = 0;
		const char* p = folded;
		while (*p)
		{
			while (*p && !isdigit((unsigned char)*p))
				++p;
			if (!*p)
				break;
			char* end = NULL;
			unsigned long value = strtoul(p, &end, 10);
			if (end == p || value == 0)
			{
				++p;
				continue;
			}
			unsigned long multiplier = 1;
			if (*end == 'k') multiplier = 1000;
			else if (*end == 'm') multiplier = 1000000;
			else if (*end == 'b') multiplier = 1000000000UL;
			if (*end == 'k' || *end == 'm' || *end == 'b')
				++end;
			if (multiplier != 1 || end == p + strlen(p) || *end == ' ' || IsPlayerBotChatSeparator(*end))
			{
				const unsigned long total = value * multiplier;
				if (total <= 2000000000UL)
					parsed = (DWORD)total;
			}
			p = end;
		}
		return parsed;
	}

	// "Kupie X": the nearest open counter with X on it answers with where and
	// how much. The player's own map first, then any.
	bool AnswerPlayerBotOwnedItemBuyShout(LPCHARACTER player, const char* query,
			bool book, DWORD skillVnum)
	{
		LPCHARACTER bestSeller = NULL;
		LPITEM bestItem = NULL;
		bool bestEquipped = false;
		WORD bestCell = 0;
		long long bestDistance = -1;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!bot || !bot->IsItemLoaded() || bot->GetMyShop() ||
					bot->GetMapIndex() != player->GetMapIndex())
				continue;
			for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
			{
				LPITEM item = bot->GetInventoryItem(cell);
				if (!item)
					continue;
				const bool match = book
						? (item->GetType() == ITEM_SKILLBOOK &&
							GetPlayerBotSkillBookSkillVnum(item) == skillVnum)
						: PlayerBotItemNameMatches(item, query);
				if (!match)
					continue;
				const long long distance = bot->GetMapIndex() == player->GetMapIndex()
						? (long long)DISTANCE_APPROX(player->GetX() - bot->GetX(),
								player->GetY() - bot->GetY())
						: 1000000LL + (long long)bot->GetMapIndex();
				if (bestDistance < 0 || distance < bestDistance)
				{
					bestDistance = distance;
					bestSeller = bot;
					bestItem = item;
					bestEquipped = item->IsEquipped();
					bestCell = cell;
				}
			}
		}
		if (!bestSeller || !bestItem || !bestItem->GetProto())
			return false;

		if (bestEquipped)
		{
			char reply[CHAT_MAX_LEN + 1];
			FormatPlayerBotText(reply, sizeof(reply), "",
					"%s bende var ama ustumde, satmiyorum",
					bestItem->GetProto()->szLocaleName);
			SendPlayerBotWhisper(bestSeller, player, reply);
			return true;
		}
		const DWORD unitPrice = std::max<DWORD>(1, GetPlayerBotShopAskingPrice(bestItem));
		const unsigned long long totalPrice =
				std::min<unsigned long long>(2000000000ULL,
					std::max<unsigned long long>(1ULL,
						(unsigned long long)unitPrice * 110ULL / 100ULL));
		TPlayerBotPendingTrade pending;
		pending.bot = bestSeller;
		pending.cell = bestCell;
		pending.price = (DWORD)totalPrice;
		pending.expires = get_dword_time() + 120000;
		pending.botBuys = false;
		s_mapPlayerBotPendingTrades[player->GetPlayerID()] = pending;
		char reply[CHAT_MAX_LEN + 1];
		const std::string itemDetails = DescribePlayerBotItem(bestItem);
		const std::string priceText = FormatPlayerBotYang(pending.price);
		FormatPlayerBotText(reply, sizeof(reply), "",
				"Selam kanka, bende %s var. %s yang, istersen trade acalim",
				itemDetails.c_str(), priceText.c_str());
		SendPlayerBotWhisper(bestSeller, player, reply);
		return true;
	}

	bool AnswerPlayerBotBuyShout(LPCHARACTER player, const char* query, bool book,
			DWORD skillVnum)
	{
		if (AnswerPlayerBotOwnedItemBuyShout(player, query, book, skillVnum))
			return true;

		LPCHARACTER bestKeeper = NULL;
		const TPlayerBotShopOffer* bestOffer = NULL;
		LPITEM bestItem = NULL;
		long long bestDistance = -1;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			if (it->second.vecShopOffers.empty())
				continue;
			LPCHARACTER keeper = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!keeper || !keeper->GetMyShop())
				continue;
			for (size_t k = 0; k < it->second.vecShopOffers.size(); ++k)
			{
				const TPlayerBotShopOffer& offer = it->second.vecShopOffers[k];
				LPITEM item = FindPlayerBotOfferItem(keeper, offer);
				if (!item)
					continue;
				const bool match = book
						? (item->GetType() == ITEM_SKILLBOOK &&
							GetPlayerBotSkillBookSkillVnum(item) == skillVnum)
						: PlayerBotItemNameMatches(item, query);
				if (!match)
					continue;
				const long long distance = keeper->GetMapIndex() == player->GetMapIndex()
						? (long long)DISTANCE_APPROX(player->GetX() - keeper->GetX(),
								player->GetY() - keeper->GetY())
						: 1000000LL + (long long)keeper->GetMapIndex();
				if (bestDistance < 0 || distance < bestDistance)
				{
					bestDistance = distance;
					bestKeeper = keeper;
					bestOffer = &offer;
					bestItem = item;
				}
				break;
			}
		}
		if (!bestKeeper || !bestOffer || !bestItem)
			return false;
		WORD inventoryCell = 0;
		bool foundInventoryCell = false;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			if (bestKeeper->GetInventoryItem(cell) == bestItem)
			{
				inventoryCell = cell;
				foundInventoryCell = true;
				break;
			}
		}
		if (!foundInventoryCell)
			return false;
		TPlayerBotPendingTrade pending;
		pending.bot = bestKeeper;
		pending.cell = inventoryCell;
		pending.price = std::max<DWORD>(1, bestOffer->dwPrice);
		pending.expires = get_dword_time() + 120000;
		pending.botBuys = false;
		s_mapPlayerBotPendingTrades[player->GetPlayerID()] = pending;
		char reply[CHAT_MAX_LEN + 1];
		if (bestOffer->wCount > 1)
		{
			const std::string priceText = FormatPlayerBotYang(bestOffer->dwPrice);
			FormatPlayerBotText(reply, sizeof(reply), "",
					"Pazarda %s x%u var, %s'te. Hepsi %s yang",
					bestItem->GetProto()->szLocaleName, (unsigned int)bestOffer->wCount,
					GetPlayerBotTownName(bestKeeper->GetMapIndex()), priceText.c_str());
		}
		else
		{
			const std::string priceText = FormatPlayerBotYang(bestOffer->dwPrice);
			FormatPlayerBotText(reply, sizeof(reply), "",
					"Pazarda %s var, %s'te. Fiyati %s yang",
					bestItem->GetProto()->szLocaleName,
					GetPlayerBotTownName(bestKeeper->GetMapIndex()), priceText.c_str());
		}
		SendPlayerBotWhisper(bestKeeper, player, reply);
		return true;
	}

	// The anti-flag that keeps a class off an item, for a weapon offered by
	// name: the proto says who may not carry it.
	DWORD GetPlayerBotJobAntiFlag(BYTE bJob)
	{
		switch (bJob)
		{
			case JOB_WARRIOR: return ITEM_ANTIFLAG_WARRIOR;
			case JOB_ASSASSIN: return ITEM_ANTIFLAG_ASSASSIN;
			case JOB_SURA: return ITEM_ANTIFLAG_SURA;
			case JOB_SHAMAN: return ITEM_ANTIFLAG_SHAMAN;
			default: return 0;
		}
	}

	BYTE GetPlayerBotTradeInterestChance(BYTE personality)
	{
		switch (personality)
		{
			case BOT_PERSONALITY_MERCHANT: return 5;
			case BOT_PERSONALITY_GEAR_SPECIALIST: return 4;
			case BOT_PERSONALITY_CAREFUL_COLLECTOR: return 3;
			case BOT_PERSONALITY_METIN_DROPPER:
			case BOT_PERSONALITY_M3_DROPPER:
			case BOT_PERSONALITY_M2_DROPPER:
			case BOT_PERSONALITY_MEDAL_DROPPER: return 2;
			default: return 1;
		}
	}

	// "Sprzedam X": a bot that is short of X says it will buy, and where. The
	// bot can: playerbot_market.h reads a player's counter like any other. A
	// world shout is an opportunity, not a broadcast storm: interested bots
	// roll their personality chance and at most three make an offer.
	bool AnswerPlayerBotSellShout(LPCHARACTER player, const char* text, const char* query,
			bool book, DWORD skillVnum)
	{
		DWORD wantedVnum = 0;
		const char* pszName = NULL;
		if (!book)
		{
			// A refine material, or a level-30 weapon: the two things a bot
			// reliably wants from anybody.
			const std::set<DWORD>& materials = GetPlayerBotRefineMaterialVnums();
			for (std::set<DWORD>::const_iterator m = materials.begin();
					m != materials.end() && wantedVnum == 0; ++m)
			{
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(*m);
				if (!proto)
					continue;
				char name[64];
				FoldPlayerBotChatText(proto->szLocaleName, name, sizeof(name));
				if (strstr(name, query))
				{
					wantedVnum = *m;
					pszName = proto->szLocaleName;
				}
			}
			for (DWORD vnum = 290; vnum <= 7169 && wantedVnum == 0; ++vnum)
			{
				if (!IsPlayerBotSpecialLevel30WeaponVnum(vnum))
					continue;
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
				if (!proto)
					continue;
				char name[64];
				FoldPlayerBotChatText(proto->szLocaleName, name, sizeof(name));
				if (strstr(name, query))
				{
					wantedVnum = vnum;
					pszName = proto->szLocaleName;
				}
			}
			if (wantedVnum == 0)
			{
				// Player shouts may offer ordinary weapons and armor too, not
				// only the market's preferred materials and level-30 weapons.
				for (DWORD vnum = 1; vnum <= 7169 && wantedVnum == 0; ++vnum)
				{
					const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
					if (!proto)
						continue;
					char name[64];
					FoldPlayerBotChatText(proto->szLocaleName, name, sizeof(name));
					if (strstr(name, query))
					{
						wantedVnum = vnum;
						pszName = proto->szLocaleName;
					}
				}
			}
			if (wantedVnum == 0)
				return false;
		}
		{
			for (DWORD vnum = PLAYERBOT_TRADE_SKILL_BOOK_FIRST;
					vnum <= PLAYERBOT_TRADE_SKILL_BOOK_LAST && wantedVnum == 0; ++vnum)
			{
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
				if (proto && proto->bType == ITEM_SKILLBOOK &&
						(DWORD)proto->alValues[0] == skillVnum)
				{
					wantedVnum = vnum;
					pszName = proto->szLocaleName;
				}
			}
			if (wantedVnum == 0)
				return false;
		}

		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(wantedVnum);
		if (!proto)
			return false;
		const DWORD dwNow = get_dword_time();
		const DWORD basePrice = (DWORD)std::max<long long>(1,
				GetPlayerBotVnumSaleValue(wantedVnum, dwNow));
		const DWORD marketOffer = std::max<DWORD>(1, basePrice * 80 / 100);
		const DWORD playerPrice = ParsePlayerBotChatPrice(text);
		const DWORD offerPrice = playerPrice != 0 && playerPrice < marketOffer
				? playerPrice : marketOffer;
		int offersSent = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end() && offersSent < 3; ++it)
		{
			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!bot || !bot->IsItemLoaded() || bot->GetMyShop() ||
					bot->GetMapIndex() != player->GetMapIndex() ||
					DISTANCE_APPROX(player->GetX() - bot->GetX(),
							player->GetY() - bot->GetY()) >= EXCHANGE_MAX_DISTANCE ||
					!CanPlayerBotAffordMarket(bot))
				continue;
			const BYTE interestChance = wantedVnum != 0
					? 100
					: GetPlayerBotTradeInterestChance(
							GetPlayerBotPersonalityByPID(bot->GetPlayerID()));
			if (number(1, 100) > interestChance)
				continue;
			if (bot->GetGold() - (int)offerPrice < (int)PLAYERBOT_SHOPPING_GOLD_FLOOR)
				continue;
			if (book)
			{
				if (IsPlayerBotOwnSkill(bot, skillVnum) &&
						bot->GetSkillMasterType(skillVnum) == SKILL_MASTER &&
						bot->GetSkillLevel(skillVnum) >= 20 && bot->GetSkillLevel(skillVnum) < 30)
				{
					char reply[CHAT_MAX_LEN + 1];
					RememberPlayerBotPendingBuy(player, bot, offerPrice);
					const std::string priceText = FormatPlayerBotYang(offerPrice);
					FormatPlayerBotText(reply, sizeof(reply), "",
							"%s icin %s yang veririm, musaitsen trade ac",
							pszName ? pszName : query, priceText.c_str());
					SendPlayerBotWhisper(bot, player, reply);
					++offersSent;
				}
			}
			else if (IsPlayerBotSpecialLevel30WeaponVnum(wantedVnum))
			{
				if (bot->GetLevel() >= 30 && !HasPlayerBotSpecialLevel30Weapon(bot, false) &&
						!IS_SET(proto->dwAntiFlags, GetPlayerBotJobAntiFlag(bot->GetJob())))
				{
					char reply[CHAT_MAX_LEN + 1];
					RememberPlayerBotPendingBuy(player, bot, offerPrice);
					const std::string priceText = FormatPlayerBotYang(offerPrice);
					FormatPlayerBotText(reply, sizeof(reply), "",
							"%s lazim, %s yang veririm. Trade acabiliriz",
							pszName ? pszName : query, priceText.c_str());
					SendPlayerBotWhisper(bot, player, reply);
					++offersSent;
				}
			}
			else if (PlayerBotNeedsRefineMaterial(bot, wantedVnum) ||
					!book)
			{
				char reply[CHAT_MAX_LEN + 1];
				RememberPlayerBotPendingBuy(player, bot, offerPrice);
				const std::string priceText = FormatPlayerBotYang(offerPrice);
				FormatPlayerBotText(reply, sizeof(reply), "",
						"%s lazim, %s yang veririm. Trade acabiliriz",
						pszName ? pszName : query, priceText.c_str());
				SendPlayerBotWhisper(bot, player, reply);
				++offersSent;
			}
		}
		return offersSent > 0;
	}

	bool PlayerBotTradeReplyAllowed(LPCHARACTER player, DWORD dwNow)
	{
		DWORD& last = s_mapPlayerBotTradeReplyTime[player->GetPlayerID()];
		if (last != 0 && dwNow - last < PLAYERBOT_TRADE_REPLY_INTERVAL)
			return false;
		last = dwNow;
		return true;
	}

	bool IsPlayerBotInventoryQuestion(const char* text)
	{
		char folded[CHAT_MAX_LEN + 1];
		FoldPlayerBotChatText(text, folded, sizeof(folded));
		return strstr(folded, "elinde") || strstr(folded, "ustunde") ||
				strstr(folded, "uzerinde") ||
				strstr(folded, "envanter") || strstr(folded, "silah") ||
				strstr(folded, "zirh") || strstr(folded, "itemlerin") ||
				strstr(folded, "ozellik") || strstr(folded, "bonus") ||
				strstr(folded, "kalkan") || strstr(folded, "yay") ||
				strstr(folded, "hancer") || strstr(folded, "kilic") ||
				strstr(folded, "kitap") || strstr(folded, "kutsama");
	}

	const char* GetPlayerBotApplyLabel(BYTE type)
	{
		switch (type)
		{
			case APPLY_MAX_HP: return "can";
			case APPLY_MAX_SP: return "zeka";
			case APPLY_ATT_GRADE_BONUS: return "saldiri";
			case APPLY_DEF_GRADE_BONUS: return "savunma";
			case APPLY_ATT_SPEED: return "saldiri hizi";
			case APPLY_MOV_SPEED: return "hareket hizi";
			case APPLY_CAST_SPEED: return "buyu hizi";
			case APPLY_CRITICAL_PCT: return "kritik";
			case APPLY_PENETRATE_PCT: return "delici";
			case APPLY_ATTBONUS_MONSTER: return "canavarlara karsi";
			case APPLY_NORMAL_HIT_DAMAGE_BONUS: return "ortalama";
			case APPLY_SKILL_DAMAGE_BONUS: return "beceri";
			case APPLY_RESIST_SWORD: return "kilic direnci";
			case APPLY_RESIST_TWOHAND: return "cift el direnci";
			case APPLY_RESIST_DAGGER: return "hancer direnci";
			case APPLY_RESIST_BELL: return "zil direnci";
			case APPLY_RESIST_FAN: return "yelpaze direnci";
			case APPLY_RESIST_BOW: return "yay direnci";
			case APPLY_IMMUNE_STUN: return "sersemletme bagisikligi";
			default: return "bonus";
		}
	}

	std::string DescribePlayerBotItemName(LPITEM item)
	{
		if (!item || !item->GetProto())
			return "yok";
		char part[96];
		std::string result = item->GetProto()->szLocaleName;
		const int refine = item->GetRefineLevel();
		if (refine > 0)
		{
			snprintf(part, sizeof(part), " +%d", refine);
			result += part;
		}
		if (item->GetCount() > 1)
		{
			snprintf(part, sizeof(part), " x%u", (unsigned int)item->GetCount());
			result += part;
		}
		return result;
	}

	std::string DescribePlayerBotItem(LPITEM item)
	{
		std::string result = DescribePlayerBotItemName(item);
		if (!item || !item->GetProto())
			return result;
		char part[96];
		int listed = 0;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const BYTE type = item->GetAttributeType(i);
			const long value = item->GetAttributeValue(i);
			if (!type || value == 0)
				continue;
			snprintf(part, sizeof(part), "%s%s %ld", listed == 0 ? " (" : ", ",
					GetPlayerBotApplyLabel(type), value);
			result += part;
			++listed;
		}
		if (listed > 0)
			result += ")";
		return result;
	}

	bool AnswerPlayerBotInventoryQuestion(LPCHARACTER bot, LPCHARACTER player)
	{
		if (!bot || !player || !bot->IsItemLoaded())
			return false;
		std::string equipped;
		std::string carried;
		const BYTE wearSlots[] = {
			WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD,
			WEAR_FOOTS, WEAR_WRIST, WEAR_NECK, WEAR_EAR
		};
		for (size_t i = 0; i < sizeof(wearSlots) / sizeof(wearSlots[0]); ++i)
		{
			LPITEM item = bot->GetWear(wearSlots[i]);
			if (item && item->GetProto())
			{
				if (!equipped.empty())
					equipped += ", ";
				equipped += DescribePlayerBotItemName(item);
			}
		}
		int listed = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM && listed < 8; ++cell)
		{
			LPITEM item = bot->GetInventoryItem(cell);
			if (!item || item->IsEquipped() || !item->GetProto())
				continue;
			if (!carried.empty())
				carried += ", ";
			carried += DescribePlayerBotItemName(item);
			++listed;
		}
		char reply[CHAT_MAX_LEN + 1];
		FormatPlayerBotText(reply, sizeof(reply), "",
				"Ustumde: %s. Cantada: %s",
				equipped.empty() ? "yok" : equipped.c_str(),
				carried.empty() ? "yok" : carried.c_str());
		SendPlayerBotWhisper(bot, player, reply);
		return true;
	}

	bool IsPlayerBotPriceQuestion(const char* text)
	{
		char folded[CHAT_MAX_LEN + 1];
		FoldPlayerBotChatText(text, folded, sizeof(folded));
		return strstr(folded, "fiyat") || strstr(folded, "fiyati") ||
				strstr(folded, "ne kadar") || strstr(folded, "kac para") ||
				strstr(folded, "kac yang") || strstr(folded, "buna ne verirsin");
	}

	bool IsPlayerBotTradeConfirmation(const char* text)
	{
		char folded[CHAT_MAX_LEN + 1];
		FoldPlayerBotChatText(text, folded, sizeof(folded));
		return strstr(folded, "tamam") || strstr(folded, "olur") ||
				strstr(folded, "trade ac") || strcmp(folded, "al") == 0 ||
				strcmp(folded, "aliyorum") == 0;
	}

	bool AnswerPlayerBotItemPriceQuestion(LPCHARACTER player, LPCHARACTER targetBot,
			const char* text)
	{
		if (!player || !targetBot || !text)
			return false;
		if (targetBot->GetMapIndex() != player->GetMapIndex() ||
				DISTANCE_APPROX(player->GetX() - targetBot->GetX(),
						player->GetY() - targetBot->GetY()) >= EXCHANGE_MAX_DISTANCE)
		{
			HoldPlayerBotForPlayerMessage(targetBot, player);
			TPlayerBotDeferredPriceQuestion deferred;
			deferred.player = player;
			deferred.bot = targetBot;
			strlcpy(deferred.text, text, sizeof(deferred.text));
			s_mapPlayerBotDeferredPriceQuestions[targetBot->GetPlayerID()] = deferred;
			char reply[CHAT_MAX_LEN + 1];
			FormatPlayerBotText(reply, sizeof(reply), "",
					"Yanina geliyorum, sonra %s icin fiyat soyleyeyim",
					text);
			SendPlayerBotWhisper(targetBot, player, reply);
			return true;
		}
		char folded[CHAT_MAX_LEN + 1];
		FoldPlayerBotChatText(text, folded, sizeof(folded));
		const char* markers[] = {
			" ne kadar", " fiyat", " fiyati", " kac para", " kac yang",
			" buna ne verirsin"
		};
		for (size_t i = 0; i < sizeof(markers) / sizeof(markers[0]); ++i)
		{
			char* marker = strstr(folded, markers[i]);
			if (marker)
			{
				*marker = 0;
				break;
			}
		}
		while (*folded && IsPlayerBotChatSeparator(folded[0]))
			memmove(folded, folded + 1, strlen(folded));
		if (strlen(folded) < PLAYERBOT_TRADE_QUERY_MIN)
			return false;

		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!bot || bot != targetBot || !bot->IsItemLoaded() || bot->GetMyShop())
				continue;
			for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
			{
				LPITEM item = bot->GetInventoryItem(cell);
				if (!item || item->IsEquipped() || !PlayerBotItemNameMatches(item, folded))
					continue;
				const DWORD basePrice = std::max<DWORD>(1,
						GetPlayerBotShopAskingPrice(item));
				const unsigned long long totalPrice =
						std::min<unsigned long long>(2000000000ULL,
							std::max<unsigned long long>(1ULL,
								(unsigned long long)basePrice * 110ULL / 100ULL));
				TPlayerBotPendingTrade pending;
				pending.bot = bot;
				pending.cell = cell;
				pending.price = (DWORD)totalPrice;
				pending.expires = get_dword_time() + 120000;
				pending.botBuys = false;
				s_mapPlayerBotPendingTrades[player->GetPlayerID()] = pending;
				char reply[CHAT_MAX_LEN + 1];
				const std::string itemDetails = DescribePlayerBotItem(item);
				const std::string priceText = FormatPlayerBotYang(pending.price);
				FormatPlayerBotText(reply, sizeof(reply), "",
						"%s icin %s yang. Uygunsa tamam yaz, trade acayim",
						itemDetails.c_str(), priceText.c_str());
				SendPlayerBotWhisper(bot, player, reply);
				return true;
			}
		}
		return false;
	}

	bool CompletePlayerBotDeferredPriceQuestion(LPCHARACTER bot)
	{
		if (!bot)
			return false;
		std::map<DWORD, TPlayerBotDeferredPriceQuestion>::iterator it =
				s_mapPlayerBotDeferredPriceQuestions.find(bot->GetPlayerID());
		if (it == s_mapPlayerBotDeferredPriceQuestions.end())
			return false;
		TPlayerBotDeferredPriceQuestion deferred = it->second;
		s_mapPlayerBotDeferredPriceQuestions.erase(it);
		if (!deferred.player || !deferred.player->GetDesc() ||
				deferred.player->IsDead() || deferred.player->GetMapIndex() != bot->GetMapIndex())
			return false;
		if (DISTANCE_APPROX(deferred.player->GetX() - bot->GetX(),
				deferred.player->GetY() - bot->GetY()) >= EXCHANGE_MAX_DISTANCE)
		{
			s_mapPlayerBotDeferredPriceQuestions[bot->GetPlayerID()] = deferred;
			return false;
		}
		return AnswerPlayerBotItemPriceQuestion(deferred.player, bot, deferred.text);
	}

	bool OpenPlayerBotPendingTrade(LPCHARACTER player);

	bool CompletePlayerBotDeferredTradeConfirmation(LPCHARACTER bot)
	{
		if (!bot)
			return false;
		for (std::map<DWORD, TPlayerBotPendingTrade>::iterator it =
				s_mapPlayerBotPendingTrades.begin();
				it != s_mapPlayerBotPendingTrades.end(); ++it)
		{
			TPlayerBotPendingTrade& pending = it->second;
			if (!pending.confirmed || pending.bot != bot)
				continue;
			LPCHARACTER player = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!player || !player->GetDesc() || player->IsDead() ||
					player->GetMapIndex() != bot->GetMapIndex())
				continue;
			if (DISTANCE_APPROX(player->GetX() - bot->GetX(),
					player->GetY() - bot->GetY()) < EXCHANGE_MAX_DISTANCE)
				return OpenPlayerBotPendingTrade(player);
		}
		return false;
	}

	bool OpenPlayerBotPendingTrade(LPCHARACTER player)
	{
		if (!player)
			return false;
		std::map<DWORD, TPlayerBotPendingTrade>::iterator it =
				s_mapPlayerBotPendingTrades.find(player->GetPlayerID());
		if (it == s_mapPlayerBotPendingTrades.end() ||
				it->second.expires < get_dword_time())
		{
			sys_log(0, "PLAYERBOT_TRADE: confirmation without pending player=%s",
					player->GetName());
			return false;
		}
		TPlayerBotPendingTrade pending = it->second;
		if (!pending.bot)
		{
			sys_log(0, "PLAYERBOT_TRADE: exchange start failed player=%s bot=? botBuys=%d",
					player->GetName(), pending.botBuys ? 1 : 0);
			return false;
		}
		if (pending.bot->GetMyShop())
		{
			TPlayerBotAIStateMap::iterator stateIt =
					s_mapPlayerBotAIStates.find(pending.bot->GetPlayerID());
			if (stateIt != s_mapPlayerBotAIStates.end())
				ClosePlayerBotShop(pending.bot, stateIt->second, get_dword_time(),
						"player_trade");
			else
				pending.bot->CloseMyShop();
		}
		if (DISTANCE_APPROX(player->GetX() - pending.bot->GetX(),
				player->GetY() - pending.bot->GetY()) >= EXCHANGE_MAX_DISTANCE)
		{
			pending.confirmed = true;
			it->second = pending;
			HoldPlayerBotForPlayerMessage(pending.bot, player);
			char reply[CHAT_MAX_LEN + 1];
			FormatPlayerBotText(reply, sizeof(reply), "",
					"Yanina geliyorum, yaklasinca trade acilacak");
			SendPlayerBotWhisper(pending.bot, player, reply);
			return true;
		}
		if ((!pending.botBuys &&
				(pending.bot->GetInventoryItem(pending.cell) == NULL ||
				pending.bot->GetInventoryItem(pending.cell)->IsEquipped())) ||
				!pending.bot->ExchangeStart(player))
		{
			sys_log(0, "PLAYERBOT_TRADE: exchange start failed player=%s bot=%s botBuys=%d",
					player->GetName(), pending.bot ? pending.bot->GetName() : "?",
					pending.botBuys ? 1 : 0);
			return false;
		}
		const bool itemAdded = pending.botBuys ||
				pending.bot->GetExchange()->AddItem(TItemPos(INVENTORY, pending.cell), 0);
		const bool goldAdded = pending.botBuys
				? pending.bot->GetExchange()->AddGold(pending.price)
				: itemAdded && player->GetExchange()->AddGold(pending.price);
		if (!itemAdded || !goldAdded)
		{
			sys_log(0, "PLAYERBOT_TRADE: exchange offer failed player=%s bot=%s item=%d gold=%d",
					player->GetName(), pending.bot->GetName(),
					itemAdded ? 1 : 0, goldAdded ? 1 : 0);
			if (pending.bot->GetExchange())
				pending.bot->GetExchange()->Cancel();
			return false;
		}
		if (!pending.bot->GetExchange()->Accept(true))
		{
			sys_log(0, "PLAYERBOT_TRADE: bot accept failed player=%s bot=%s",
					player->GetName(), pending.bot->GetName());
			if (pending.bot->GetExchange())
				pending.bot->GetExchange()->Cancel();
			return false;
		}
		char reply[CHAT_MAX_LEN + 1];
		const std::string priceText = FormatPlayerBotYang(pending.price);
		FormatPlayerBotText(reply, sizeof(reply), "",
				"Trade acildi, item ve %s yang hazir. Son onay sende",
				priceText.c_str());
		SendPlayerBotWhisper(pending.bot, player, reply);
		s_mapPlayerBotPendingTrades.erase(it);
		return true;
	}

	// A player's shout, after it has gone out on the channel.
	void HandlePlayerShoutForTrade(LPCHARACTER player, const char* text)
	{
		if (!player || !text)
			return;
		sys_log(0, "PLAYERBOT_INPUT: player shout from=%s text=\"%s\"",
				player->GetName(), text);
		char query[128];
		bool book = false;
		const EPlayerBotTradeVerb verb = ParsePlayerBotTradeText(text, query, sizeof(query), book);
		if (verb == PLAYERBOT_TRADE_NONE)
			return;
		const DWORD skillVnum = book ? FindPlayerBotSkillByName(query) : 0;
		if (book && skillVnum == 0)
			return;
		const DWORD dwNow = get_dword_time();
		if (!PlayerBotTradeReplyAllowed(player, dwNow))
			return;
		const bool answered = verb == PLAYERBOT_TRADE_BUY
				? AnswerPlayerBotBuyShout(player, query, book, skillVnum)
				: AnswerPlayerBotSellShout(player, text, query, book, skillVnum);
		sys_log(0, "PLAYERBOT_TRADE: shout from=%s verb=%s book=%d query=\"%s\" answered=%d",
				player->GetName(), verb == PLAYERBOT_TRADE_BUY ? "buy" : "sell",
				book ? 1 : 0, query, answered ? 1 : 0);
	}

	// Forward declaration of LLM bridge dispatch defined in playerbot_llm_bridge.h
	static bool DispatchPlayerBotLLMWhisper(LPCHARACTER player, LPCHARACTER bot, const char* text);

	// A player's whisper to a bot. A trade line is answered like a shout, by
	// whichever bot is best placed; anything else gets the bot's own state -
	// what its counter holds, or that it is out hunting.
	void HandlePlayerWhisperToBot(LPCHARACTER player, LPCHARACTER bot, const char* text)
	{
		if (!player || !bot || !text)
			return;
		HoldPlayerBotForPlayerMessage(bot, player);
		sys_log(0, "PLAYERBOT_INPUT: player whisper from=%s to=%s text=\"%s\"",
				player->GetName(), bot->GetName(), text);
		const DWORD dwNow = get_dword_time();
		if (IsPlayerBotTradeConfirmation(text) && OpenPlayerBotPendingTrade(player))
			return;
		if (IsPlayerBotPriceQuestion(text) &&
				AnswerPlayerBotItemPriceQuestion(player, bot, text))
			return;
		if (IsPlayerBotInventoryQuestion(text) &&
				AnswerPlayerBotInventoryQuestion(bot, player))
			return;
		char query[128];
		bool book = false;
		const EPlayerBotTradeVerb verb = ParsePlayerBotTradeText(text, query, sizeof(query), book);
		// Trade broadcasts are handled only by the real shout hook. A private
		// whisper must never fan out to every bot in the world.
		(void)verb;
		(void)query;
		(void)book;
		// Non-trade conversation is owned by the cognitive bridge. Queue it
		// before market/status replies so those handlers cannot answer first.
		if (DispatchPlayerBotLLMWhisper(player, bot, text))
			return;
		if (!PlayerBotTradeReplyAllowed(player, dwNow))
			return;
		char reply[CHAT_MAX_LEN + 1];
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.find(bot->GetPlayerID());
		if (bot->GetMyShop() && it != s_mapPlayerBotAIStates.end() && !it->second.vecShopOffers.empty())
		{
			std::string goods;
			int listed = 0;
			for (size_t k = 0; k < it->second.vecShopOffers.size() && listed < 3; ++k)
			{
				LPITEM item = FindPlayerBotOfferItem(bot, it->second.vecShopOffers[k]);
				if (!item || !item->GetProto())
					continue;
				if (!goods.empty())
					goods += ", ";
				goods += item->GetProto()->szLocaleName;
				++listed;
			}
			FormatPlayerBotText(reply, sizeof(reply), "",
					"%s'te pazarim acik, elimde: %s",
					GetPlayerBotTownName(bot->GetMapIndex()),
					goods.empty() ? PlayerBotText("nic juz") : goods.c_str());
			SendPlayerBotWhisper(bot, player, reply);
		}
		else if (it != s_mapPlayerBotAIStates.end() && it->second.bMarketTrip)
		{
			FormatPlayerBotText(reply, sizeof(reply), "",
					"%s'te pazara gidiyorum",
					GetPlayerBotTownName(bot->GetMapIndex()));
			SendPlayerBotWhisper(bot, player, reply);
		}
		else
		{
			// Fallback if bridge is not available
			FormatPlayerBotText(reply, sizeof(reply), "",
					"Su an ticaret yapmiyorum, avlaniyorum. Joan ve Bokjung pazarlarina bak");
			SendPlayerBotWhisper(bot, player, reply);
		}
	}
}

#endif
