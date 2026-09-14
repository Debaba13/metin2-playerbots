#ifndef PLAYERBOT_OFFLINE_SHOP_H
#define PLAYERBOT_OFFLINE_SHOP_H
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
// Included once after playerbot_town.h. All transfers use native Ikarus.
namespace {
    using NativeShop = ikashop::CShopManager::SHOP_HANDLE;
    DWORD s_nextBotOfflineMutation = 0;

    bool BotOfflineBudget(DWORD now) {
        if (!playerbot_offline::Due(now, s_nextBotOfflineMutation)) return false;
        s_nextBotOfflineMutation = now + 1000;
        return true;
    }
    bool BotOfflineBusy(LPCHARACTER ch, const TPlayerBotAIState& state) {
        return !ch || !ch->IsItemLoaded() || ch->IsDead() || ch->IsStun() ||
            ch->GetExchange() || ch->GetShop() || ch->GetSafebox() || ch->IsBusy() ||
            (ch->GetVictim() && !ch->GetVictim()->IsDead()) ||
            state.bVisitingShop || state.bVisitingBiologist || state.bVisitingStable ||
            state.bRecoveringAfterDeath || state.bTacticalRetreat || state.bMultiPullActive ||
            state.bFishingSession;
    }
    void BotOfflineFinishVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        auto& o = state.offlineShop;
        if (o.visiting) {
            ikashop::GetManager().RecvCloseMyShopBoardClientPacket(ch);
            ikashop::GetManager().RecvShopSafeboxCloseClientPacket(ch);
            ClearPlayerBotRoute(state, true);
        }
        o.visiting = false;
        o.visitUntil = 0;
        o.nextService = now + number(600000, 900000);
    }
    bool BotOfflinePoll(LPCHARACTER ch, DWORD now) {
        auto it = playerbot_offline::requests.find(ch->GetPlayerID());
        if (it == playerbot_offline::requests.end()) return false;
        auto& r = it->second;
        if (r.done) {
            if (r.success && r.op == playerbot_offline::Buy && r.count && r.unitPrice)
                RememberPlayerBotSale(r.vnum, r.refine, r.unitPrice, now, r.skill);
            sys_log(0, "PLAYERBOT_OFFLINE: ack pid=%u op=%u item=%u ok=%d",
                ch->GetPlayerID(), unsigned(r.op), r.item, r.success);
            playerbot_offline::requests.erase(it);
            return false;
        }
        if (!r.warned && uint32_t(now - r.started) >= 30000) {
            r.warned = true;
            sys_err("PLAYERBOT_OFFLINE: unresolved pid=%u op=%u item=%u; commerce paused, gameplay continues; reconcile DB before retry",
                ch->GetPlayerID(), unsigned(r.op), r.item);
        }
        return true;
    }
    // Unregistered comparison object: no persistent ID allocation, save queue,
    // expiry events or item-manager insertion. Destroy with M2_DELETE below.
    LPITEM BotOfflinePreview(const ikashop::CShopItem& source) {
        const auto& i = source.GetInfo();
        auto proto = source.GetTable();
        if (!proto) return NULL;
        auto item = M2_NEW CItem(i.vnum);
        item->Initialize();
        item->SetProto(proto);
        item->SetSkipSave(true);
        item->SetCount(i.count);
        item->SetAttributes(i.aAttr);
        item->SetSockets(i.alSockets);
#ifdef ENABLE_CHANGELOOK_SYSTEM
        item->SetTransmutation(i.dwTransmutation);
#endif
        return item;
    }
    bool BotOfflineValid(LPCHARACTER ch, LPITEM item, int cell) {
        if (!item || item->GetOwner() != ch || item->IsEquipped() || item->isLocked()) return false;
#ifdef ENABLE_SOULBIND_SYSTEM
        if (item->IsSealed()) return false;
#endif
        return playerbot_offline::Fits(cell, item->GetSize(), SHOP_PLAYER_WIDTH,
                SHOP_PLAYER_HOST_ITEM_MAX_NUM) && ch->CanAddItemToShop(item, BYTE(cell));
    }
    int BotOfflineSlot(LPCHARACTER ch, NativeShop shop, LPITEM item) {
        bool used[SHOP_PLAYER_HOST_ITEM_MAX_NUM]{};
        if (shop) for (const auto& [id, line] : shop->GetItems()) {
            if (!line || !line->GetTable()) continue;
            int pos = line->GetInfo().pos, size = line->GetTable()->bSize;
            if (!playerbot_offline::Fits(pos, size, SHOP_PLAYER_WIDTH, SHOP_PLAYER_HOST_ITEM_MAX_NUM)) return -1;
            for (int y = 0; y < size; ++y) used[pos + y * SHOP_PLAYER_WIDTH] = true;
        }
        for (int pos = 0; pos < SHOP_PLAYER_HOST_ITEM_MAX_NUM; ++pos) {
            if (!BotOfflineValid(ch, item, pos)) continue;
            bool free = true;
            for (int y = 0; y < item->GetSize(); ++y) free &= !used[pos + y * SHOP_PLAYER_WIDTH];
            if (free) return pos;
        }
        return -1;
    }
    bool SubmitPlayerBotOfflineShop(LPCHARACTER ch, TPlayerBotAIState& state,
            DWORD now, const char* sign, TShopItemTable* table, BYTE count) {
        using namespace playerbot_offline;
        auto& manager = ikashop::GetManager();
        state.dwNextShopKeepTime = now + 120000;
        if (manager.GetShopByOwnerID(ch->GetPlayerID()) || requests.count(ch->GetPlayerID()) ||
                !db_clientdesc || !db_clientdesc->IsPhase(PHASE_DBCLIENT) || !count) return false;
        // Keep the existing prices and selection, but revalidate every line,
        // including vertical grid cells, before OpenMyShop removes anything.
        std::set<WORD> cells;
        bool grid[SHOP_PLAYER_HOST_ITEM_MAX_NUM]{};
        long long total = ch->GetGold();
        for (BYTE n = 0; n < count; ++n) {
            auto item = ch->GetItem(table[n].pos);
            int pos = table[n].display_pos;
            if (!BotOfflineValid(ch, item, pos) || !cells.insert(table[n].pos.cell).second ||
                    table[n].price <= 0 || table[n].price >= GOLD_MAX) return false;
            for (int y = 0; y < item->GetSize(); ++y) {
                int c = pos + y * SHOP_PLAYER_WIDTH;
                if (grid[c]) return false;
                grid[c] = true;
            }
            total += table[n].price;
            if (total >= GOLD_MAX) return false;
        }
        constexpr BYTE duration = 1; // constants.cpp: 8 hours, 6000 Yang
        // Not in the first two minutes after this bot spawned. The core loads
        // the shop list from the db core when it connects, long before any bot
        // spawns, but a keeper parked at its pitch by the last session rolls a
        // stall on its first tick; a create for an owner the engine already
        // has a shop for is an EXTEND (duration reset, lines added, 6000 yang
        // paid again), harmless to the goods but pointless - and this spreads
        // the reopenings after a restart instead of one a second.
        if (now - state.dwSpawnTime < 120000) return false;
        if (ch->GetGold() - aOfflineShopTime[duration].price < GetPlayerBotReservedGold(ch) ||
                !BotOfflineBudget(now) || !Begin(ch->GetPlayerID(), Create, 0, now)) return false;
        ch->OpenMyShop(sign, table, count, duration);
        bool sent = EndCall(ch->GetPlayerID());
        state.dwNextShopKeepTime = now + (sent ? 600000 : 120000);
        state.offlineShop.nextService = now + number(600000, 900000);
        ClearPlayerBotRoute(state, true);
        state.vecShopOffers.clear(); // native ownership, not the old inventory mirror
        sys_log(0, "PLAYERBOT_OFFLINE: create pid=%u sent=%d lines=%u map=%ld",
            ch->GetPlayerID(), sent, unsigned(count), ch->GetMapIndex());
        if (!sent) {
            // OpenMyShop refuses silently - a chat line to a descriptor nobody
            // reads - and refuses the whole shop over one condition, so name
            // the ones it tests (char_shop.cpp) the way the classic stall's
            // "refused" line did: a quest script running, the saddle, a
            // polymorph, a busy window, and the first item as the sample.
            quest::PC* pc = quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
            LPITEM first = ch->GetItem(table[0].pos);
            const TItemTable* rp = first ? first->GetProto() : NULL;
            sys_log(0, "PLAYERBOT_OFFLINE: refused pid=%u name=%s lines=%u quest=%d riding=%d poly=%d part=%d busy=%d "
                "myshop=%d ikashop=%d vnum=%u anti=%u equipped=%d locked=%d sign=%d gold=%d level=%d",
                ch->GetPlayerID(), ch->GetName(), unsigned(count),
                (pc && pc->IsRunning()) ? 1 : 0, ch->IsHorseRiding() ? 1 : 0,
                ch->IsPolymorphed() ? 1 : 0, (int)ch->GetPart(PART_MAIN), ch->IsBusy() ? 1 : 0,
                ch->GetMyShop() ? 1 : 0, ch->GetIkarusShop() ? 1 : 0,
                first ? first->GetVnum() : 0u, rp ? rp->dwAntiFlags : 0u,
                first && first->IsEquipped() ? 1 : 0, first && first->isLocked() ? 1 : 0,
                (int)strlen(sign), (int)(ch->GetGold() / 1000), (int)ch->GetLevel());
        }
        return false; // the independent entity owns the stall; AI resumes now
    }
    bool HasPlayerBotOfflineShop(LPCHARACTER ch) {
        return ch && (ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID()) ||
            playerbot_offline::requests.count(ch->GetPlayerID()));
    }
    // What sold while the owner was off hunting. The native manager records a
    // sale as it happens (playerbot_offline::NoteSold) because it is the only
    // side that knows: the goods belong to the shop entity, so the classic
    // stall's "one pass over my own bag" cannot see it, and that whole branch
    // of ManagePlayerBotShopLifetime is unreachable on this engine anyway.
    // Drained on the owner's own tick, so both the demand memory and the gear
    // history get what the classic stall used to give them.
    void BotOfflineDrainSales(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        auto it = playerbot_offline::sold.find(ch->GetPlayerID());
        if (it == playerbot_offline::sold.end()) return;
        auto& o = state.offlineShop;
        for (const auto& line : it->second) {
            auto known = o.listed.find(line.item);
            const bool haveListing = known != o.listed.end();
            const DWORD vnum = haveListing && known->second.vnum ? known->second.vnum : line.vnum;
            const BYTE refine = haveListing ? (BYTE)known->second.refine : (BYTE)0;
            const DWORD skill = haveListing ? (DWORD)known->second.skill : 0U;
            // A line that left within PLAYERBOT_MARKET_FAST_SALE_MS of going
            // up is Iwakura's "wysoki popyt": the next counter carrying this
            // thing asks more. A line whose listing time this core never saw -
            // it went up before the last restart - is sold, but not timed.
            if (haveListing && known->second.when != 0 &&
                    now - known->second.when < PLAYERBOT_MARKET_FAST_SALE_MS) {
                NotePlayerBotFastSale(vnum, refine, now, skill);
                sys_log(0, "PLAYERBOT_MARKET: fast sale pid=%u name=%s vnum=%u+%u skill=%u in=%u s",
                    ch->GetPlayerID(), ch->GetName(), vnum, (unsigned int)refine, skill,
                    (unsigned int)((now - known->second.when) / 1000));
            }
            char hint[64];
            snprintf(hint, sizeof(hint), "%u x%u za %lld", vnum,
                (unsigned int)line.count, (long long)line.price);
            LogManager::instance().ItemLog(ch, (int)line.item, (int)vnum,
                "PLAYERBOT_STALL_SOLD", hint);
            if (haveListing) o.listed.erase(known);
        }
        playerbot_offline::sold.erase(it);
    }
    bool ManagePlayerBotOfflineService(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        if (!ch) return false;
        BotOfflineDrainSales(ch, state, now);
        auto& o = state.offlineShop;
        auto& manager = ikashop::GetManager();
        auto shop = manager.GetShopByOwnerID(ch->GetPlayerID());
        ch->SetIkarusShop(shop); // boot/relog: native PID map is authoritative
        if (BotOfflinePoll(ch, now)) {
            // Never stand waiting for the DB, nor leave edit mode locking sales.
            if (o.visiting) BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        // The first visit after a spawn is spread over a whole service interval.
        // "pid % 60000" was meant to spread it over a minute, but every
        // registered pid is below 2504, so every keeper went thirty to thirty-
        // two seconds after a restart: 451 map changes in the first two minutes
        // of 14 September, each keeper pulled out of the dungeon or frontier it
        // had just been spawned on, and the same wave again ten to fifteen
        // minutes later because the whole population's clocks started together.
        // The thirty seconds stay: the shop list has to arrive from the DB first.
        if (o.nextService == 0)
            o.nextService = now + 30000 + PlayerBotNavHash(ch->GetPlayerID() ^ 0x4f534856U) % 600000;
        if (BotOfflineBusy(ch, state) || !db_clientdesc || !db_clientdesc->IsPhase(PHASE_DBCLIENT)) {
            if (o.visiting) BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        if (!Due(now, o.nextService)) return false;
        if (!shop) {
            // Proceeds even after sell-out deleted the empty shop.
            auto box = manager.GetShopSafeboxByOwnerID(ch->GetPlayerID());
            long x = 0, y = 0;
            if (box && GetPlayerBotShopCentre(ch->GetMapIndex(), x, y) &&
                    DISTANCE_APPROX(ch->GetX()-x, ch->GetY()-y) <= PLAYERBOT_SHOP_RING_RADIUS + 1000 &&
                    BotOfflineBudget(now)) {
                manager.RecvShopSafeboxOpenClientPacket(ch);
                if (box->GetValutes().yang > 0) manager.RecvShopSafeboxGetValutesClientPacket(ch);
                // Returned items use the DB-confirmed inventory-space check.
                if (!box->GetItems().empty()) {
                    auto itemid = box->GetItems().begin()->first;
                    if (Begin(ch->GetPlayerID(), WithdrawItem, itemid, now)) {
                        manager.RecvShopSafeboxGetItemClientPacket(ch, itemid);
                        EndCall(ch->GetPlayerID());
                    }
                }
                manager.RecvShopSafeboxCloseClientPacket(ch);
            }
            o.nextService = now + number(600000, 900000);
            return false;
        }
        const auto spawn = shop->GetSpawn();
        if (spawn.channel != g_bChannel ||
                playerbot_empire_rules::GetMapOwnerEmpire(spawn.map) != ch->GetEmpire() ||
                !IsPlayerBotMapHostedHere(spawn.map)) {
            BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        if (!o.visiting) {
            o.visiting = true;
            o.visitUntil = now + 90000; // absolute upper bound, including travel
            o.nextStep = 0;
        }
        if (Due(now, o.visitUntil)) {
            BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        SetPlayerBotAction(state, BOT_ACTION_TRAVEL, now);
        if (ch->GetMapIndex() != spawn.map) {
            // Reuses world-travel safety checks; never manufactures cross-core warps.
            TransitionPlayerBotMap(ch, state, spawn.map, spawn.x, spawn.y, now, "offline_shop_service");
            return true;
        }
        if (!MovePlayerBotTownLeg(ch, state, now, spawn.x, spawn.y, 800)) return true;
        if (!Due(now, o.nextStep)) return true;
        o.nextStep = now + 3000;
        if (!BotOfflineBudget(now)) return true;
        ch->SetLookingShopOwner(true);
        manager.RecvShopSafeboxOpenClientPacket(ch);
        auto box = ch->GetIkarusShopSafebox();
        if (box && box->GetValutes().yang > 0) manager.RecvShopSafeboxGetValutesClientPacket(ch);
        manager.RecvShopSafeboxCloseClientPacket(ch);
        if (shop->GetDuration() == 0) {
            // The operator moved the TRADE slider while this stand was up. An
            // eight-hour offline stand is not worth closing early - the fee is
            // paid and the goods are with the entity - but it is not renewed
            // under a weight that no longer wants it. The four exceptions
            // (Merchant, poor, full bag, dropper pressure) are not asked: the
            // slider never applied to them.
            const bool stillWanted = !IsPlayerBotShopReasonRolled(state.bShopOpenReason) ||
                    ShouldPlayerBotKeepShop(ch, state);
            if (stillWanted && !shop->GetItems().empty() &&
                    ch->GetGold() - aOfflineShopTime[1].price >= GetPlayerBotReservedGold(ch) &&
                    Begin(ch->GetPlayerID(), Create, 0, now)) {
                manager.RecvShopReopenClientPacket(ch, shop->GetName(), 1);
                EndCall(ch->GetPlayerID());
            }
            BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        // Everything on the counter this core did not watch go up - the lines
        // a restart inherited. Recorded without a time, so a sale is still
        // written to the gear history and only the "how fast" is left out
        // rather than guessed at. emplace keeps a real listing time where
        // there is one.
        for (const auto& [lineId, line] : shop->GetItems())
            if (line)
                o.listed.emplace(lineId,
                    playerbot_offline::ListedLine{ line->GetVnum(), 0u, 0u, 0 });
        // Edit is opened for one bounded operation only, never during hunting.
        if (!manager.RecvShopRequestEditClientPacket(ch, true)) {
            BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        std::vector<std::pair<int, WORD> > scored;
        CollectPlayerBotShopItems(ch, scored, IsPlayerBotStallKeeper(state));
        bool sent = false;
        for (auto [score, cell] : scored) {
            auto item = ch->GetInventoryItem(cell);
            int pos = BotOfflineSlot(ch, shop, item);
            if (pos < 0) continue;
            ikashop::TPriceInfo price{};
            price.yang = std::max(GetPlayerBotShopAskingPrice(item), GetPlayerBotRefineInvestment(item));
            if (price.yang <= 0 || price.yang >= GOLD_MAX ||
                    shop->GetTotalYangValue() >= GOLD_MAX - price.yang) continue;
            DWORD id = item->GetID();
            if (Begin(ch->GetPlayerID(), Add, id, now)) {
                manager.RecvShopAddItemClientPacket(ch, TItemPos(INVENTORY, cell), price, pos);
                sent = EndCall(ch->GetPlayerID());
                // Remembered while the item is still in hand: once it sells,
                // the only thing left is its id. The skill is socket 0 - every
                // ordinary book is vnum 50300 and one cheap sale of a spare
                // must not set the price of Aura Miecza.
                if (sent)
                    o.listed[id] = playerbot_offline::ListedLine{
                        item->GetVnum(),
                        item->GetType() == ITEM_SKILLBOOK ? (uint32_t)item->GetSocket(0) : 0u,
                        now, (uint8_t)item->GetRefineLevel() };
            }
            break; // at most one item per short service visit
        }
        if (!sent && Due(now, o.nextReprice)) {
            // Rotate by ID, one existing offer per visit; recompute from market
            // policy, not a repeated percentage markdown tending towards zero.
            auto it = shop->GetItems().upper_bound(o.repriceItem);
            bool wrapped = (it == shop->GetItems().end());
            if (wrapped) it = shop->GetItems().begin();
            if (it != shop->GetItems().end() && it->second) {
                o.repriceItem = it->first;
                auto preview = BotOfflinePreview(*it->second);
                if (preview) {
                    ikashop::TPriceInfo price{};
                    price.yang = std::max(GetPlayerBotShopAskingPrice(preview), GetPlayerBotRefineInvestment(preview));
                    M2_DELETE(preview);
                    if (price.yang > 0 && price.yang < GOLD_MAX && price.yang != it->second->GetPrice().yang &&
                            Begin(ch->GetPlayerID(), Edit, it->first, now)) {
                        manager.RecvShopEditItemClientPacket(ch, it->first, price);
                        EndCall(ch->GetPlayerID());
                    }
                }
            }
            // A counter priced against an older table is walked at the pace of the
            // service visit (10-15 min), not one line an hour; the stamp is set
            // only once the rotation has come round, so every line was seen.
            if (o.priceGeneration != PLAYERBOT_PRICE_TABLE_VERSION) {
                if (wrapped) o.priceGeneration = PLAYERBOT_PRICE_TABLE_VERSION;
                o.nextReprice = now;
            } else {
                o.nextReprice = now + 3600000;
            }
        }
        BotOfflineFinishVisit(ch, state, now);
        return false;
    }
}
#endif
#endif
