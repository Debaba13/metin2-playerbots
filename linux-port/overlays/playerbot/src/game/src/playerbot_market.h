#ifndef __INC_METIN2_PLAYERBOT_MARKET_H__
#define __INC_METIN2_PLAYERBOT_MARKET_H__

// Buying from another bot's stall, and going out of one's way to do it.
//
// The stalls existed already; nobody ever bought from one, so a well-refined
// spare sat on a counter until its keeper packed up and eventually vendored it.
// This closes the loop: a bot with money in its pocket walks the market strip
// and buys what it actually needs - a refine material it is short of, a horse
// medal, or a piece of gear better than what it is wearing.
//
// The first version only bought from a counter that happened to be within
// twenty metres of wherever the bot was standing. That is not shopping, and it
// showed: twelve purchases in half an hour across seven hundred bots, all of
// them accidents of where a town errand had left somebody. So a bot that is
// short of something now walks to the ring, picks the nearest counter with that
// something on it, walks up to that counter, and buys there - which is also
// what a market is supposed to look like from the outside.
//
// It reads the offer from the seller's own AI state rather than from CShop,
// whose item list is private. That is not a workaround: we are the ones who put
// the items on the counter, in that order, so the recorded offer is exactly
// what is on it and its index is the index CShopManager::Buy expects.
//
// The purchase itself goes through the engine's ordinary path. Setting the shop
// owner is what a client does when a player clicks a stall, and everything
// after it - the price, the gold, the inventory space, moving the item - is the
// engine's own code, so a bot cannot buy anything a player could not.
//
// An implementation fragment in the sense playerbot_types.h describes: it
// defines objects, relies on the engine headers playerbot_manager.cpp includes
// above it, and reopens the same anonymous namespace. Include it exactly once,
// after playerbot_town.h - that file puts the goods on the counters and owns
// the walk into town this one borrows.

namespace
{
	// Defined with the chat trade, after this file: the bot that found the
	// market empty of what it came for asks the world channel.
	void AnnouncePlayerBotNeed(LPCHARACTER ch);

	class CCollectPlayerBotStalls
	{
		public:
			CCollectPlayerBotStalls(LPCHARACTER buyer, int maxDistance)
				: m_buyer(buyer), m_maxDistance(maxDistance)
			{
			}

			void operator()(LPENTITY entity)
			{
				if (!entity || !entity->IsType(ENTITY_CHARACTER) || !m_buyer)
					return;
				LPCHARACTER keeper = (LPCHARACTER)entity;
				if (keeper == m_buyer || !keeper->IsPC() || !keeper->GetMyShop())
					return;
				if (DISTANCE_APPROX(m_buyer->GetX() - keeper->GetX(),
						m_buyer->GetY() - keeper->GetY()) > m_maxDistance)
					return;
				m_stalls.push_back(keeper);
			}

			std::vector<LPCHARACTER> m_stalls;

		private:
			LPCHARACTER m_buyer;
			int m_maxDistance;
	};

	// Would this bot rather have the item than the money?
	bool WantsPlayerBotStallItem(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer)
			return false;

		// A material it is short of right now. This is the whole reason a bot
		// walks the market: the alternative is farming the same material for an
		// hour while a neighbour has spares on a counter three metres away.
		if (PlayerBotNeedsRefineMaterial(ch, offer->GetVnum()))
			return true;

		// A skill book for a skill this bot is actually raising.
		//
		// There was no branch for these at all, so no bot ever bought one off a
		// counter: books piled up on stalls, and the only way to a skill was to
		// find the book yourself. What a bot wants is a small working stock of
		// its own build's skills - two or three, not every book to Grand Master
		// - and only while the skill can still be read up.
		// A Forgetting Scroll on somebody's counter is what a bot past the old
		// woman's thirty with a skill stuck at seventeen came to market for.
		if (offer->GetVnum() == PLAYERBOT_SKILL_FORGET_SCROLL_VNUM)
			return GetPlayerBotStuckSkill(ch) != 0 &&
					ch->GetLevel() > PLAYERBOT_SKILL_RESET_MAX_LEVEL &&
					ch->CountSpecifyItem(PLAYERBOT_SKILL_FORGET_SCROLL_VNUM) == 0;
		if (offer->GetType() == ITEM_SKILLBOOK)
		{
			const DWORD skillVnum = GetPlayerBotSkillBookSkillVnum(offer);
			if (skillVnum == 0 || ch->GetSkillGroup() == 0 ||
					!IsPlayerBotOwnSkill(ch, skillVnum))
				return false;
			// Already at the grade a book stops helping, or already holding the
			// working stock: somebody else needs it more. The limit is the
			// bag's own (GetPlayerBotBookKeepLimit) - a few for a skill not yet
			// readable, the full stock once it is.
			return CountPlayerBotSkillBooksAhead(ch, offer, skillVnum) <
					GetPlayerBotBookKeepLimit(ch, skillVnum);
		}

		// A horse medal, if this bot still has a horse to raise. Buying one is
		// hours of the Monkey Dungeon it does not have to run.
		if (offer->GetVnum() == PLAYERBOT_HORSE_MEDAL_VNUM)
			return CanPlayerBotAdvanceHorse(ch);

		// A Forgetting Scroll, while a skill stands at seventeen unmastered.
		if (offer->GetVnum() == PLAYERBOT_SKILL_FORGET_SCROLL_VNUM)
			return GetPlayerBotStuckSkill(ch) != 0;

		// A soul stone of its set, at a grade its piece deserves, for a socket
		// it has open.
		if (offer->GetType() == ITEM_METIN)
			return WantsPlayerBotSoulStone(ch, offer->GetVnum(), (DWORD)offer->GetValue(5));

		// A level-30 weapon of its own class, when it has none. This is the item
		// bots cross the world to farm; buying one off a counter is the whole
		// point of there being a market.
		if (IsPlayerBotSpecialLevel30Weapon(offer) && IsPlayerBotWeapon(ch, offer) &&
				offer->GetLevelLimit() <= ch->GetLevel() &&
				!HasPlayerBotSpecialLevel30Weapon(ch, false))
			return true;

		// Gear only when it is genuinely better than what is worn. A bot that
		// buys sideways upgrades spends its yang on nothing.
		if (!IsPlayerBotEquipmentCandidate(ch, offer))
			return false;
		if (offer->GetLevelLimit() > ch->GetLevel())
			return false;
		const int wearCell = offer->FindEquipCell(ch);
		if (wearCell < 0)
			return false;
		// Not when the bag already holds one at least as good for the same
		// slot. The comparison below is against what is worn, and what is
		// worn does not change until the gear pass runs - so a bot standing at
		// the ring bought the same +6 armour three times over, two seconds
		// apart, each one better than what it had on and none of them on yet.
		const long long offerScore = GetPlayerBotEquipmentScore(offer, ch);
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM spare = ch->GetInventoryItem(cell);
			if (!spare || spare->IsEquipped() || !IsPlayerBotEquipmentCandidate(ch, spare) ||
					spare->FindEquipCell(ch) != wearCell)
				continue;
			if (GetPlayerBotEquipmentScore(spare, ch) * (100 + PLAYERBOT_MARKET_GEAR_MARGIN_PERCENT) / 100 >= offerScore)
				return false;
		}
		LPITEM worn = ch->GetWear((BYTE)wearCell);
		if (!worn)
			return true;
		// A big bonus line is worth having even when the base item scores level
		// with what is worn - a thousand health does not show up in the equipment
		// score, and it is exactly what a player would buy the piece for.
		if (HasPlayerBotValuableBonus(offer) && !HasPlayerBotValuableBonus(worn))
			return true;
		return offerScore >
				GetPlayerBotEquipmentScore(worn, ch) * (100 + PLAYERBOT_MARKET_GEAR_MARGIN_PERCENT) / 100;
	}

	// Is there anything at all a market could sell this bot? Asked before the
	// walk, so it has to be answerable without reading a single counter: these
	// are the three things a bot is reliably short of and a stall reliably has.
	bool PlayerBotWantsAnythingFromMarket(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		// A refine material for something it is carrying below its target. This
		// is the common case by a long way - half the counters in this world are
		// materials, because half of what a bot needs is.
		if (PlayerBotNeedsAnyRefineMaterial(ch))
			return true;
		// A horse medal, while there is still a horse to raise.
		if (CanPlayerBotAdvanceHorse(ch))
			return true;
		// A Forgetting Scroll for a skill stuck at seventeen.
		if (GetPlayerBotStuckSkill(ch) != 0)
			return true;
		// A socket open on a piece it keeps.
		if (PlayerBotHasOpenSoulStoneSocket(ch))
			return true;
		// And a piece of gear for a slot that is empty or behind the ladder.
		//
		// This branch was missing, and it is the whole of why "I put +8 battle
		// shields on a stall for one yang and the bots would not buy them"
		// happens: WantsPlayerBotStallItem has always known how to compare an
		// offered piece against what is worn, but nothing ever walked a bot to
		// a counter to look. Gear was reachable only by accident, on a trip the
		// bot made for a refine material. The question has to be answerable
		// without reading a counter, and these predicates are exactly that -
		// the same ones the tick uses to decide a merchant trip is due.
		if (NeedsPlayerBotProgressionWeapon(ch) || NeedsPlayerBotProgressionArmor(ch) ||
				NeedsPlayerBotProgressionShield(ch) || NeedsPlayerBotProgressionHelmet(ch) ||
				NeedsPlayerBotProgressionBoots(ch) || NeedsPlayerBotProgressionWrist(ch) ||
				NeedsPlayerBotProgressionNecklace(ch) || NeedsPlayerBotProgressionEarring(ch))
			return true;
		// And the level-30 weapon it would otherwise cross the world to farm.
		return ch->GetLevel() >= 30 && !HasPlayerBotSpecialLevel30Weapon(ch, false);
	}

	// One line of one counter: what a buyer decided it wants, where it is, and
	// which slot number CShopManager::Buy will need.
	struct TPlayerBotStallPick
	{
		LPCHARACTER keeper;
		DWORD dwVnum;
		DWORD dwPrice;
		// Which skill, for a skill book. The purchase is recorded against the
		// book's own market, not against every book that shares vnum 50300.
		DWORD dwSkillVnum;
		BYTE bSlot;
		BYTE bRefine;
		WORD wCount;

		TPlayerBotStallPick()
			: keeper(NULL), dwVnum(0), dwPrice(0), dwSkillVnum(0), bSlot(0),
			  bRefine(0), wCount(0)
		{
		}
	};

	// The nearest counter in reach with something on it this bot would rather
	// have than its money. Nearest rather than best: the counters are all within
	// the same ring, so walking past three of them to reach a fourth buys nothing
	// extra, and a bot that goes to the closest one gets there before the keeper
	// packs up.
	bool FindPlayerBotStallPick(LPCHARACTER ch, TPlayerBotStallPick& outPick)
	{
		if (!ch || !ch->GetSectree())
			return false;

		CCollectPlayerBotStalls collector(ch, PLAYERBOT_SHOPPING_RANGE);
		ch->GetSectree()->ForEachAround(collector);

		int bestDistance = -1;
		for (size_t i = 0; i < collector.m_stalls.size(); ++i)
		{
			LPCHARACTER keeper = collector.m_stalls[i];
			if (!keeper || !keeper->GetMyShop())
				continue;
			TPlayerBotAIStateMap::const_iterator it =
					s_mapPlayerBotAIStates.find(keeper->GetPlayerID());
			// A player's counter is read from the engine's own shop through the
			// accessor patch 0007 adds - the offer list only exists for bots. A
			// line a player asks more than a share of the median wallet for is
			// passed over: the bots are customers, not a way to print yang.
			std::vector<TPlayerBotShopOffer> playerOffers;
			if (it == s_mapPlayerBotAIStates.end())
			{
				if (keeper->GetDesc() && keeper->GetDesc()->IsBot())
					continue;
				const std::vector<CShop::SHOP_ITEM>& lines = keeper->GetMyShop()->GetItemVector();
				const DWORD cap = (DWORD)((unsigned long long)GetPlayerBotMarketMedianWallet() *
						PLAYERBOT_MARKET_STACK_WALLET_PERCENT / 100);
				for (size_t k = 0; k < lines.size(); ++k)
				{
					const CShop::SHOP_ITEM& line = lines[k];
					if (!line.pkItem || line.vnum == 0 || line.price <= 0 ||
							(cap != 0 && (DWORD)line.price > cap))
						continue;
					TPlayerBotShopOffer offer;
					offer.dwVnum = line.vnum;
					offer.dwPrice = (DWORD)line.price;
					offer.bRefine = line.pkItem->GetRefineLevel();
					offer.wCount = line.count;
					offer.dwItemID = (DWORD)line.itemid;
					offer.bSlot = (BYTE)k;
					playerOffers.push_back(offer);
				}
			}
			const std::vector<TPlayerBotShopOffer>& offers =
					it != s_mapPlayerBotAIStates.end() ? it->second.vecShopOffers : playerOffers;
			if (offers.empty())
				continue;

			const int distance = DISTANCE_APPROX(ch->GetX() - keeper->GetX(),
					ch->GetY() - keeper->GetY());
			if (bestDistance >= 0 && distance >= bestDistance)
				continue; // a nearer counter has already offered something

			// A counter holds several things. Walk it and take the first line the
			// buyer actually wants; the offer carries the engine's slot for it.
			for (size_t k = 0; k < offers.size(); ++k)
			{
				const TPlayerBotShopOffer& candidate = offers[k];
				// Never spend down to nothing: potions and the next weapon first.
				if (candidate.dwPrice == 0 ||
						ch->GetGold() - (int)candidate.dwPrice <
							(int)PLAYERBOT_SHOPPING_GOLD_FLOOR)
					continue;
				// The real item, with its sockets and bonus lines, is still in
				// the keeper's bag to be looked at - or it is sold, and it is not.
				LPITEM candidateItem = FindPlayerBotOfferItem(keeper, candidate);
				if (!WantsPlayerBotStallItem(ch, candidateItem))
					continue;
				// Room for this particular thing, not room in general. The engine
				// refuses the whole purchase when the item does not fit, and a
				// weapon is three cells against the two the trip checked for -
				// so a bot with a two-cell gap would ask for a sword, be refused,
				// and ask again.
				if (ch->GetEmptyInventory(candidateItem->GetSize()) < 0)
					continue;
				outPick.keeper = keeper;
				outPick.dwVnum = candidate.dwVnum;
				outPick.dwPrice = candidate.dwPrice;
				outPick.bSlot = candidate.bSlot;
				outPick.bRefine = candidate.bRefine;
				outPick.wCount = candidate.wCount;
				outPick.dwSkillVnum = candidateItem->GetType() == ITEM_SKILLBOOK
						? GetPlayerBotSkillBookSkillVnum(candidateItem) : 0;
				bestDistance = distance;
				break;
			}
		}
		return bestDistance >= 0;
	}

	// Exactly what a client does when a player clicks a stall, in the same order.
	// Both halves are required and neither is optional: CShopManager::Buy returns
	// immediately unless the buyer is registered as a guest of the shop (AddGuest
	// is what sets ch->GetShop()) *and* has the shop owner set. Setting only the
	// owner, which is the obvious half, silently bought nothing at all.
	bool BuyFromPlayerBotStall(LPCHARACTER ch, const TPlayerBotStallPick& pick)
	{
		if (!ch || !pick.keeper)
			return false;
		LPSHOP shop = pick.keeper->GetMyShop();
		if (!shop || ch->GetShop() || ch->GetExchange())
			return false;
		if (!shop->AddGuest(ch, pick.keeper->GetVID(), false))
			return false;

		const int goldBefore = ch->GetGold();
		ch->SetShopOwner(pick.keeper);
		CShopManager::instance().Buy(ch, pick.bSlot);
		// Leaving either of these set would point this bot at a character it is no
		// longer standing next to.
		ch->SetShopOwner(NULL);
		shop->RemoveGuest(ch);

		if (ch->GetGold() >= goldBefore)
			return false;

		const int paid = goldBefore - ch->GetGold();
		// A sale is the one measurement of demand there is. The asking price on
		// a counter is what a seller hoped for; this is what a buyer did.
		// With the skill, so a book sale lands on its own market.
		RememberPlayerBotSale(pick.dwVnum, pick.bRefine,
				(DWORD)paid / std::max<DWORD>(1, pick.wCount), get_dword_time(),
				pick.dwSkillVnum);
		sys_log(0, "PLAYERBOT_MARKET: bought pid=%u name=%s from=%s slot=%u vnum=%u refine=%u count=%u asked=%u paid=%d gold=%d",
				ch->GetPlayerID(), ch->GetName(), pick.keeper->GetName(),
				(unsigned int)pick.bSlot, pick.dwVnum, (unsigned int)pick.bRefine,
				(unsigned int)pick.wCount, pick.dwPrice, paid, ch->GetGold());
		return true;
	}

	// Ending a trip says why, the way closing a stall does. Without it the only
	// measurable thing about shopping was the purchases, and a market with no
	// purchases could equally mean nobody set off, nobody arrived, or nobody
	// found anything - three different faults with three different fixes.
	void EndPlayerBotMarketTrip(LPCHARACTER ch, TPlayerBotAIState& state,
			const char* reason)
	{
		if (ch && state.bMarketTrip)
			sys_log(0, "PLAYERBOT_MARKET: trip over pid=%u name=%s reason=%s pos=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), reason, ch->GetX(), ch->GetY());
		// Joan was looked at and had nothing this bot wanted, so Bokjung is
		// worth a walk for a while. Without this a shopper would cross to the
		// quiet market for ever and never see the busy one.
		if (ch && ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M1 && state.bMarketTrip)
			state.dwMarketM2AllowedUntil = get_dword_time() +
					PLAYERBOT_MARKET_M2_FALLBACK;
		state.bMarketTrip = false;
		state.dwMarketTripUntil = 0;
		state.dwMarketBrowseTime = 0;
		state.dwMarketStallVID = 0;
	}

	// Money it may actually spend, and somewhere to put what it buys. Both are
	// re-asked every tick of a trip: a bot whose bag filled up on the way has
	// nothing left to go to the market for.
	bool CanPlayerBotAffordMarket(LPCHARACTER ch)
	{
		return ch && ch->GetGold() - GetPlayerBotReservedGold(ch) >
					(int)PLAYERBOT_SHOPPING_GOLD_FLOOR &&
				ch->GetEmptyInventory(2) >= 0;
	}

	// One tick of a shopping trip: read the counters now and then, walk to the
	// one that has something, and buy when standing at it. Claims the tick for as
	// long as the trip lasts, which is what keeps the bot walking instead of
	// planning a hunt halfway across the market.
	bool ContinuePlayerBotMarketTrip(LPCHARACTER ch, TPlayerBotAIState& state,
			DWORD dwNow, long pitchX, long pitchY)
	{
		if (dwNow >= state.dwMarketTripUntil || !CanPlayerBotAffordMarket(ch))
		{
			EndPlayerBotMarketTrip(ch, state,
					dwNow >= state.dwMarketTripUntil ? "timeout" : "broke");
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_MARKET, dwNow);

		// The counters change while their customer is walking over - a keeper
		// packs up, another opens - so what the bot is heading for is re-decided
		// every couple of seconds rather than once at the start of the trip.
		TPlayerBotStallPick pick;
		bool havePick = false;
		if (dwNow >= state.dwMarketBrowseTime)
		{
			state.dwMarketBrowseTime = dwNow + PLAYERBOT_MARKET_BROWSE_INTERVAL;
			havePick = FindPlayerBotStallPick(ch, pick);
			state.dwMarketStallVID = havePick ? pick.keeper->GetVID() : 0;
			if (!havePick &&
					DISTANCE_APPROX(ch->GetX() - pitchX, ch->GetY() - pitchY) <=
						PLAYERBOT_SHOP_RING_RADIUS)
			{
				// Standing in the ring with nothing on it worth buying. The trip
				// is over rather than a bot loitering for another minute - and
				// the world channel hears what it came for.
				EndPlayerBotMarketTrip(ch, state, "nothing_on_offer");
				AnnouncePlayerBotNeed(ch);
				return false;
			}
		}

		// A keeper that has packed up since the last look stops being a
		// destination, and the bot falls back on the middle of the ring.
		LPCHARACTER keeper = state.dwMarketStallVID != 0
				? CHARACTER_MANAGER::instance().Find(state.dwMarketStallVID) : NULL;
		if (keeper && !keeper->GetMyShop())
		{
			keeper = NULL;
			state.dwMarketStallVID = 0;
		}

		if (!MovePlayerBotTownLeg(ch, state, dwNow,
				keeper ? keeper->GetX() : pitchX,
				keeper ? keeper->GetY() : pitchY,
				keeper ? PLAYERBOT_MARKET_STALL_APPROACH : PLAYERBOT_MARKET_ARRIVE))
			return true; // still walking

		// Standing at the counter. The line is read again now, whatever the
		// browse clock says: what was on it two seconds ago is what the bot
		// walked over for, what is on it this tick is what it can buy. Gone,
		// and the bot heads for the next counter that has it, or the ring.
		if (keeper && !havePick)
		{
			havePick = FindPlayerBotStallPick(ch, pick);
			state.dwMarketBrowseTime = dwNow + PLAYERBOT_MARKET_BROWSE_INTERVAL;
			state.dwMarketStallVID = havePick ? pick.keeper->GetVID() : 0;
			if (!havePick || pick.keeper != keeper)
				return true;
		}
		if (keeper && havePick && pick.keeper == keeper)
		{
			if (!BuyFromPlayerBotStall(ch, pick))
			{
				// The engine said no - no room for that size, not enough gold,
				// the line sold to somebody else while this bot walked over - and
				// it says so at a log level nobody runs with. Whatever it was, it
				// will be just as true on the next tick, so asking again only
				// produces one Shop::Buy per second until the trip times out.
				// Which is precisely what an operator photographed.
				EndPlayerBotMarketTrip(ch, state, "refused");
				return false;
			}
			// Bought. A bot that came for two things gets the second without
			// walking off, but through the ordinary browse interval rather than
			// on this same tick - and the gear pass runs first, so a bought piece
			// is worn before the next counter is read.
			state.dwNextEquipmentCheckTime = dwNow;
			state.dwMarketStallVID = 0;
			state.dwMarketBrowseTime = dwNow + PLAYERBOT_MARKET_BROWSE_INTERVAL;
		}
		return true;
	}

	bool ManagePlayerBotShopping(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead())
			return false;
		// A keeper minding its own counter is not also a customer.
		if (ch->GetMyShop() || state.bVisitingBiologist || state.bVisitingStable ||
				state.bRecoveringAfterDeath || state.bTacticalRetreat ||
				state.bMultiPullActive || state.bFishingSession)
		{
			EndPlayerBotMarketTrip(ch, state, "busy");
			return false;
		}
		// Stalls stand in both towns - most of them in Joan, round the village
		// guard - and nowhere else, so the pitch is both the test for "is there a
		// market here" and the place a shopping trip walks to.
		long pitchX = 0, pitchY = 0;
		if (!GetPlayerBotShopCentre(ch->GetMapIndex(), pitchX, pitchY) ||
				!ch->GetSectree())
		{
			EndPlayerBotMarketTrip(ch, state, "left_town");
			return false;
		}

		if (state.bMarketTrip)
			return ContinuePlayerBotMarketTrip(ch, state, dwNow, pitchX, pitchY);

		if (dwNow < state.dwNextShoppingTime)
			return false;
		state.dwNextShoppingTime = dwNow + number(
				PLAYERBOT_SHOPPING_INTERVAL_MIN, PLAYERBOT_SHOPPING_INTERVAL_MAX);
		if (!CanPlayerBotAffordMarket(ch))
			return false;

		// bVisitingShop does not stop a bot buying from a counter it is already
		// standing beside - a bot anywhere near the market is on a town errand
		// almost by definition, and excluding them left the market with no
		// customers at all. It does stop it walking off across town: the errand
		// owns the bot's feet until it is finished.
		TPlayerBotStallPick pick;
		const bool haveStallInReach = FindPlayerBotStallPick(ch, pick);
		if (state.bVisitingShop)
			return haveStallInReach && BuyFromPlayerBotStall(ch, pick);

		// Something in reach, or a reason to go and look: either way it is a trip,
		// so the bot walks up to the counter instead of buying from twenty metres
		// off. That is the difference between a market and a vending machine.
		if (!haveStallInReach && !PlayerBotWantsAnythingFromMarket(ch))
			return false;
		// Joan first. A shopper standing in Bokjung crosses to the quieter market
		// before browsing the one under its nose: that is what gives the Joan
		// counters customers, and it is also what stops five hundred bots
		// circling the same seven stalls. Bokjung opens up again for a while
		// once Joan has been looked at and had nothing.
		if (!haveStallInReach && ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M2 &&
				dwNow >= state.dwMarketM2AllowedUntil)
		{
			PlayerBotLogThrottled("market_to_m1", dwNow,
					"PLAYERBOT_MARKET: looking in Joan first pid=%u name=%s",
					ch->GetPlayerID(), ch->GetName());
			return MovePlayerBotToWorldPortal(ch, state,
					PLAYERBOT_M2_TO_M1_PORTAL_X, PLAYERBOT_M2_TO_M1_PORTAL_Y,
					PLAYERBOT_MAP_CHUNJO_M1, PLAYERBOT_M1_GUARD_X,
					PLAYERBOT_M1_GUARD_Y, dwNow, "market_to_m1");
		}
		if (!haveStallInReach &&
				DISTANCE_APPROX(ch->GetX() - pitchX, ch->GetY() - pitchY) >
					PLAYERBOT_MARKET_TRIP_RANGE)
			return false; // wants something, but the market is a hunt away

		state.bMarketTrip = true;
		state.dwMarketTripUntil = dwNow + PLAYERBOT_MARKET_TRIP_TIMEOUT;
		state.dwMarketBrowseTime = dwNow + PLAYERBOT_MARKET_BROWSE_INTERVAL;
		state.dwMarketStallVID = haveStallInReach ? pick.keeper->GetVID() : 0;
		sys_log(0, "PLAYERBOT_MARKET: trip pid=%u name=%s map=%ld stall=%u pos=(%ld,%ld)",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(),
				(unsigned int)state.dwMarketStallVID, ch->GetX(), ch->GetY());
		return ContinuePlayerBotMarketTrip(ch, state, dwNow, pitchX, pitchY);
	}

	// Once a minute, the ledger playerbot_world_memory.h keeps: every open
	// counter's lines, and every bot short of a material with the money and
	// the bag room to go and buy it. Walked here rather than kept up to date
	// by the sites that change it, because those sites are a purchase, a
	// stall closing, a refine consuming a material, a drop landing in a bag
	// and a bot outgrowing a piece - and one walk a minute is cheaper than
	// getting all five right. Eight hundred bags once a minute is what one
	// target scan costs, and a target scan happens hundreds of times a minute.
	//
	// Every ten minutes it is written down: the counters, the shortages, and
	// what the listing decisions said in between. Read the top of that list
	// against the drops: a material with thirty bots short and nothing on any
	// counter is not being held back by the ledger, it is not being found.
	void RefreshPlayerBotMarketLedger(DWORD dwNow)
	{
		if (s_dwMarketLedgerTime != 0 &&
				dwNow - s_dwMarketLedgerTime < PLAYERBOT_MARKET_LEDGER_INTERVAL)
			return;
		s_dwMarketLedgerTime = dwNow;
		s_mapMarketLedger.clear();

		DWORD stalls = 0, lines = 0, demandBots = 0;
		s_iPlayerBotStallsInM2 = 0;
		std::set<DWORD> wanted;
		std::vector<DWORD> wallets;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded())
				continue;
			const TPlayerBotAIState& state = it->second;
			if (ch->GetMyShop() && !state.vecShopOffers.empty())
			{
				++stalls;
				if (ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M2)
					++s_iPlayerBotStallsInM2;
				for (size_t k = 0; k < state.vecShopOffers.size(); ++k)
				{
					const TPlayerBotShopOffer& offer = state.vecShopOffers[k];
					// A line that has been bought stays in the offer list; the
					// item does not stay in the bag.
					if (!FindPlayerBotOfferItem(ch, offer))
						continue;
					AddPlayerBotMarketSupply(offer.dwVnum, offer.wCount);
					++lines;
				}
			}
			// A keeper counts as a buyer too: its counter closes within the
			// half hour and its own anvil is still waiting.
			if (!CanPlayerBotAffordMarket(ch))
				continue;
			wallets.push_back((DWORD)std::max(0, ch->GetGold() - GetPlayerBotReservedGold(ch)));
			CollectPlayerBotWantedMaterials(ch, wanted);
			if (wanted.empty())
				continue;
			++demandBots;
			for (std::set<DWORD>::const_iterator w = wanted.begin(); w != wanted.end(); ++w)
				++s_mapMarketLedger[*w].dwDemandBots;
		}

		if (!wallets.empty())
		{
			std::sort(wallets.begin(), wallets.end());
			s_dwMarketMedianWallet = wallets[wallets.size() / 2];
		}

		if (s_dwMarketReportTime != 0 &&
				dwNow - s_dwMarketReportTime < PLAYERBOT_MARKET_REPORT_INTERVAL)
			return;
		s_dwMarketReportTime = dwNow;

		std::vector<std::pair<DWORD, DWORD> > ranked; // demand, vnum
		for (TPlayerBotMarketLedger::const_iterator e = s_mapMarketLedger.begin();
				e != s_mapMarketLedger.end(); ++e)
			ranked.push_back(std::make_pair(e->second.dwDemandBots, e->first));
		std::sort(ranked.rbegin(), ranked.rend());
		std::string top;
		for (size_t i = 0; i < ranked.size() && i < 8; ++i)
		{
			const TPlayerBotMarketLedgerEntry& entry = s_mapMarketLedger[ranked[i].second];
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(ranked[i].second);
			char buf[128];
			snprintf(buf, sizeof(buf), " %s(%u) D=%u S=%u/%u ask=%u",
					proto ? proto->szLocaleName : "?", ranked[i].second,
					entry.dwDemandBots, entry.dwSupplyUnits, entry.dwSupplyStalls,
					GetPlayerBotLastAsk(ranked[i].second, 0, dwNow));
			top += buf;
		}
		sys_log(0, "PLAYERBOT_MARKET: ledger stalls=%u lines=%u vnums=%u demand_bots=%u wallet=%u decisions list=%u probe=%u no_demand=%u overstock=%u top:%s",
				stalls, lines, (unsigned int)s_mapMarketLedger.size(), demandBots,
				s_dwMarketMedianWallet,
				s_auMarketDecisions[PLAYERBOT_LIST_LIST], s_auMarketDecisions[PLAYERBOT_LIST_PROBE],
				s_auMarketDecisions[PLAYERBOT_LIST_NO_DEMAND], s_auMarketDecisions[PLAYERBOT_LIST_OVERSTOCK],
				top.c_str());
		for (int d = 0; d < PLAYERBOT_LIST_DECISIONS; ++d)
			s_auMarketDecisions[d] = 0;
	}
}

#endif
