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
            state.bFishingSession ||
            // A bot in a player's party does not warp off to its counter every
            // ten minutes; the stand keeps selling until the party ends.
            (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
            // Nor out of a Monkey Dungeon: a visit is half an hour in rooms
            // joined only by their doors, and a keeper warped out of it has the
            // whole way back in to walk. The service waits for the way out.
            IsPlayerBotMonkeyMap(ch->GetMapIndex());
    }
    // The wait before the next service visit: the long one for a dropper
    // (PLAYERBOT_DROPPER_SHOP_SERVICE_MIN_MS), ten to fifteen minutes for
    // everybody else.
    DWORD BotOfflineServiceGap(const TPlayerBotAIState& state) {
        if (IsPlayerBotDropper(state.bPersonality))
            return (DWORD)number((int)PLAYERBOT_DROPPER_SHOP_SERVICE_MIN_MS, (int)PLAYERBOT_DROPPER_SHOP_SERVICE_MAX_MS);
        return (DWORD)number(600000, 900000);
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
        o.nextService = now + BotOfflineServiceGap(state);
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
        sys_log(0, "PLAYERBOT_OFFLINE: create pid=%u sent=%d lines=%u map=%ld sign=\"%s\"",
            ch->GetPlayerID(), sent, unsigned(count), ch->GetMapIndex(), sign);
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
    // The first line this counter would not take today: gear under level thirty
    // below PLAYERBOT_SHOP_LOW_GEAR_MIN_REFINE, or past the
    // PLAYERBOT_SHOP_LOW_GEAR_MAX_LINES of it one counter carries. lowGear is
    // what stays of that gear, for the add that follows. An item the operator
    // put on "stall" is never second-guessed.
    DWORD BotOfflineUnwantedLine(NativeShop shop, int& lowGear) {
        lowGear = 0;
        DWORD unwanted = 0;
        if (!shop) return 0;
        // Moonlight chests stand on a counter in packs, and only on the counter
        // of a bot that sells them (IsPlayerBotSurplusChest): a line of eleven
        // to thirty never sold, and one a bot that opens its chests put up
        // before 2.0.53 comes home to be opened.
        const DWORD owner = shop->GetOwnerPID();
        const bool sellsChests = IsPlayerBotResourceTrader(owner) ||
            IsPlayerBotDropper(GetPlayerBotPersonalityByPID(owner));
        for (const auto& [id, line] : shop->GetItems()) {
            if (!line) continue;
            LPITEM preview = BotOfflinePreview(*line);
            if (!preview) continue;
            if (preview->GetVnum() == PLAYERBOT_MOONLIGHT_CHEST_VNUM &&
                    GetPlayerBotItemPolicy(preview) != PLAYERBOT_ITEM_POLICY_STALL &&
                    (!sellsChests || (int)preview->GetCount() > PLAYERBOT_CHEST_LINE_UNITS)) {
                if (!unwanted) unwanted = id;
                M2_DELETE(preview);
                continue;
            }
            // A scroll line of more than PLAYERBOT_SHOP_SCROLL_LINE_UNITS went
            // up as a whole stack before 2.0.55; it comes home to be cut.
            if (IsPlayerBotSafeRefineScroll(preview->GetVnum()) &&
                    (int)preview->GetCount() > PLAYERBOT_SHOP_SCROLL_LINE_UNITS &&
                    GetPlayerBotItemPolicy(preview) != PLAYERBOT_ITEM_POLICY_STALL) {
                if (!unwanted) unwanted = id;
                M2_DELETE(preview);
                continue;
            }
            if (IsPlayerBotLowLevelGear(preview) &&
                    GetPlayerBotItemPolicy(preview) != PLAYERBOT_ITEM_POLICY_STALL) {
                const bool capped = CountsAgainstPlayerBotLowGearCap(preview);
                if (preview->GetRefineLevel() < GetPlayerBotLowGearMinRefine(preview) ||
                        (capped && lowGear >= PLAYERBOT_SHOP_LOW_GEAR_MAX_LINES)) {
                    if (!unwanted) unwanted = id;
                } else if (capped) {
                    ++lowGear;
                }
            }
            M2_DELETE(preview);
        }
        return unwanted;
    }
    // One line back into the owner's bag, through the journal like every other
    // mutation. A bag with no room refuses it synchronously and the next visit
    // asks again. True when the request reached the DB core.
    bool BotOfflineTakeOff(LPCHARACTER ch, TPlayerBotAIState& state, DWORD itemid, int lowGear, DWORD now) {
        using namespace playerbot_offline;
        if (!Begin(ch->GetPlayerID(), Remove, itemid, now)) return false;
        ikashop::GetManager().RecvShopRemoveItemClientPacket(ch, itemid);
        if (!EndCall(ch->GetPlayerID())) return false;
        state.offlineShop.listed.erase(itemid);
        sys_log(0, "PLAYERBOT_OFFLINE: took off pid=%u name=%s item=%u low_gear_kept=%d",
            ch->GetPlayerID(), ch->GetName(), itemid, lowGear);
        return true;
    }
    // A piece on the owner's own counter it should be wearing: better, by the
    // equipment pass's own score, than what it has on and than anything in its
    // bag for the slot. Nothing asked the counter for gear - only for room to
    // add goods - so a warrior of 75 whose weapon burned at the anvil fought on
    // with a Gilotynowe Ostrze +7 of level ten while a Halabarda +6 and three
    // swords of level 55 stood on her own counter (CiosZKarpia, Tieru,
    // 15 September). A line taken back within six hours is not taken again:
    // a piece the equipment pass will not put on would otherwise go back on
    // the counter and come off it every visit.
    DWORD BotOfflineReclaimLine(LPCHARACTER ch, const TPlayerBotAIState& state, NativeShop shop,
            DWORD now, long long& gain) {
        gain = 0;
        DWORD best = 0;
        if (!ch || !shop) return 0;
        const auto& o = state.offlineShop;
        for (const auto& [id, line] : shop->GetItems()) {
            if (!line || !line->GetTable()) continue;
            const BYTE type = line->GetTable()->bType;
            if (type != ITEM_WEAPON && type != ITEM_ARMOR) continue;
            if (id == o.lastReclaimItem && !playerbot_offline::Due(now, o.lastReclaimAt + 21600000U)) continue;
            LPITEM preview = BotOfflinePreview(*line);
            if (!preview) continue;
            long long lineGain = 0;
            const int wearCell = IsPlayerBotEquipmentCandidate(ch, preview) &&
                    preview->GetLevelLimit() <= ch->GetLevel() ? preview->FindEquipCell(ch) : -1;
            if (wearCell >= 0 && wearCell < WEAR_MAX_NUM &&
                    (wearCell != WEAR_SHIELD || PlayerBotWantsShield(ch))) {
                LPITEM worn = ch->GetWear((BYTE)wearCell);
                if (!worn || !IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE)) {
                    // A rod or a pickaxe in the weapon slot is the session's tool,
                    // not the weapon to beat; that one waits in the bag.
                    long long baseline = worn && worn->GetType() == type ? GetPlayerBotEquipmentScore(worn, ch) : 0;
                    for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell) {
                        LPITEM held = ch->GetInventoryItem(cell);
                        if (!held || held->IsEquipped() || held->GetType() != type ||
                                !IsPlayerBotEquipmentCandidate(ch, held) ||
                                held->GetLevelLimit() > ch->GetLevel() || held->FindEquipCell(ch) != wearCell)
                            continue;
                        baseline = std::max(baseline, GetPlayerBotEquipmentScore(held, ch));
                    }
                    lineGain = GetPlayerBotEquipmentScore(preview, ch) - baseline;
                    // Worth a round trip and a line off the counter only by a margin.
                    if (baseline > 0 && lineGain * 100 < baseline * PLAYERBOT_OFFLINE_RECLAIM_MIN_GAIN_PERCENT)
                        lineGain = 0;
                }
            }
            M2_DELETE(preview);
            if (lineGain > gain) {
                gain = lineGain;
                best = id;
            }
        }
        return best;
    }
    // Back into the bag through the journal, for the equipment pass to put on.
    bool BotOfflineReclaim(LPCHARACTER ch, TPlayerBotAIState& state, DWORD itemid, long long gain, DWORD now) {
        using namespace playerbot_offline;
        if (!Begin(ch->GetPlayerID(), Remove, itemid, now)) return false;
        ikashop::GetManager().RecvShopRemoveItemClientPacket(ch, itemid);
        if (!EndCall(ch->GetPlayerID())) return false;
        state.offlineShop.listed.erase(itemid);
        state.offlineShop.lastReclaimItem = itemid;
        state.offlineShop.lastReclaimAt = now;
        sys_log(0, "PLAYERBOT_OFFLINE: took back to wear pid=%u name=%s item=%u gain=%lld",
            ch->GetPlayerID(), ch->GetName(), itemid, gain);
        return true;
    }
    // How many lines of this vnum the counter carries already.
    int BotOfflineLinesOf(NativeShop shop, DWORD vnum) {
        int lines = 0;
        if (shop)
            for (const auto& [id, line] : shop->GetItems())
                if (line && line->GetInfo().vnum == vnum) ++lines;
        return lines;
    }
    // The bag cell of the line to add. A hoard's pack of ten, a single key, a
    // pack of Moonlight chests (PLAYERBOT_CHEST_LINE_UNITS) or a line of
    // refine scrolls (PLAYERBOT_SHOP_SCROLL_LINE_UNITS)
    // is cut off its stack into a free cell (GetPlayerBotStallLineUnitsFor);
    // anything else goes up as the stack it is, as it always has - a stand
    // adds one line a visit. -1 when no line can be cut without the stack's
    // reserve or the bag's last free cells.
    int BotOfflinePrepareLine(LPCHARACTER ch, WORD cell) {
        LPITEM item = ch->GetInventoryItem(cell);
        if (!item) return -1;
        const int units = GetPlayerBotStallLineUnitsFor(ch, item);
        if (IsPlayerBotSafeRefineScroll(item->GetVnum())) {
            // A scroll line is what the bot holds over its own keep
            // (GetPlayerBotStallBaseKeep), up to the line: a stack of five
            // with a keep of three is a line of two, never the whole stack.
            // The keep is counted over every stack of the kind, so a line
            // already cut off (BotOfflinePrepareVisitLine) goes up whole while
            // the rest of the scrolls stay in the stack it came from.
            const int keep = GetPlayerBotStallBaseKeep(ch, item);
            const int spare = (int)ch->CountSpecifyItem(item->GetVnum()) - keep;
            const int take = std::min(units, std::min((int)item->GetCount(), spare));
            if (take <= 0) return -1;
            if (take >= (int)item->GetCount()) return cell;
            if (CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_SHOP_SPLIT_KEEP_FREE_CELLS) return -1;
            const int to = ch->GetEmptyInventory(item->GetSize());
            if (to < 0 || !ch->MoveItem(TItemPos(INVENTORY, cell), TItemPos(INVENTORY, (WORD)to), take))
                return -1;
            sys_log(0, "PLAYERBOT_OFFLINE: cut a line pid=%u name=%s vnum=%u units=%d left=%u keep=%d",
                ch->GetPlayerID(), ch->GetName(), item->GetVnum(), take, (unsigned int)item->GetCount(), keep);
            return to;
        }
        const bool cut = units == PLAYERBOT_SHOP_HOARD_PACK_UNITS ||
            (units == 1 && item->GetType() == ITEM_TREASURE_KEY) ||
            item->GetVnum() == PLAYERBOT_MOONLIGHT_CHEST_VNUM;
        if (!cut || (int)item->GetCount() <= units) return cell;
        if ((int)item->GetCount() - units < GetPlayerBotStallBaseKeep(ch, item) ||
                CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_SHOP_SPLIT_KEEP_FREE_CELLS)
            return -1;
        const int to = ch->GetEmptyInventory(item->GetSize());
        if (to < 0 || !ch->MoveItem(TItemPos(INVENTORY, cell), TItemPos(INVENTORY, (WORD)to), units))
            return -1;
        sys_log(0, "PLAYERBOT_OFFLINE: cut a line pid=%u name=%s vnum=%u units=%d left=%u",
            ch->GetPlayerID(), ch->GetName(), item->GetVnum(), units, (unsigned int)item->GetCount());
        return to;
    }
    // The line this visit will add, cut out of its stack while the bot can
    // still handle its bag. Once the board is open - looking at the shop, its
    // safebox, edit mode - IsBusy is true and MoveItem refuses through
    // CanHandleItem, so every cut in the add loop failed silently: not one
    // scroll, hoard pack or chest pack was ever cut on a service visit, and
    // the diag lines of 16 September read score 800, a slot, a keep of three
    // and lineCell=-1 for every scroll. Remembered by item id and cell for the
    // add of the same visit; a cut left behind by a visit that ended early is
    // an ordinary split stack, poured back by the merge pass.
    void BotOfflinePrepareVisitLine(LPCHARACTER ch, TPlayerBotAIState& state, NativeShop shop) {
        auto& o = state.offlineShop;
        o.preparedItem = 0;
        if (!ch || !shop || shop->GetDuration() == 0) return;
        int lowGear = 0;
        BotOfflineUnwantedLine(shop, lowGear);
        std::vector<std::pair<int, WORD> > scored;
        CollectPlayerBotShopItems(ch, scored, IsPlayerBotStallKeeper(state), lowGear);
        for (auto [score, cell] : scored) {
            LPITEM item = ch->GetInventoryItem(cell);
            if (!item || BotOfflineSlot(ch, shop, item) < 0) continue;
            if (IsPlayerBotHoardedMaterial(ch, item) &&
                    BotOfflineLinesOf(shop, item->GetVnum()) >= PLAYERBOT_SHOP_HOARD_LINES) continue;
            if (item->GetVnum() == PLAYERBOT_MOONLIGHT_CHEST_VNUM &&
                    BotOfflineLinesOf(shop, item->GetVnum()) >= PLAYERBOT_CHEST_COUNTER_LINES) continue;
            if (IsPlayerBotSafeRefineScroll(item->GetVnum()) &&
                    BotOfflineLinesOf(shop, item->GetVnum()) >= PLAYERBOT_SHOP_SCROLL_LINES) continue;
            const int lineCell = BotOfflinePrepareLine(ch, cell);
            if (lineCell < 0) continue;
            LPITEM line = ch->GetInventoryItem((WORD)lineCell);
            if (!line) continue;
            o.preparedItem = line->GetID();
            o.preparedCell = (uint32_t)lineCell;
            return;
        }
    }
    // A name for what the shop holds now, from previews of its own lines,
    // classified and named by this fork's own Turkish sign pool
    // (playerbot_shop_signs.h / playerbot_llm_shop.h) - the same system
    // playerbot_town.h uses for a live counter, rather than upstream's
    // pricing-aware, non-ASCII-Polish ChoosePlayerBotShopName. There is no
    // "poor keeper" concept offline, so the pid/poor prefix always reads
    // as if not poor; the draw is keyed to the pid alone since an offline
    // stand does not rotate pitches the way a live one does.
    bool BotOfflineNameForGoods(LPCHARACTER ch, NativeShop shop, char* out, size_t outSize, const char** how) {
        std::vector<LPITEM> goods;
        if (shop)
            for (const auto& [id, line] : shop->GetItems())
                if (line)
                    if (LPITEM preview = BotOfflinePreview(*line))
                        goods.push_back(preview);
        if (!ch || goods.empty()) {
            for (LPITEM preview : goods)
                M2_DELETE(preview);
            return false;
        }
        const char* pszBestName = NULL;
        const char* pszWeapon30 = NULL;
        const char* pszPrecious = NULL;
        BYTE bPreciousRefine = 0;
        const char* pszBook = NULL;
        int iBooks = 0;
        int iScrap = 0;
        int iFish = 0;
        int iGear = 0;
        int iMedals = 0;
        int iScrolls = 0;
        int iStones = 0;
        DWORD dwFishUnitPrice = 0;
        const char* pszGear = NULL;
        BYTE bGearRefine = 0;
        for (LPITEM item : goods) {
            const TItemTable* proto = item->GetProto();
            if (!proto) continue;
            const char* pszName = proto->szLocaleName;
            if (!pszBestName)
                pszBestName = pszName;
            if (IsPlayerBotSpecialLevel30Weapon(item))
                pszWeapon30 = pszWeapon30 ? pszWeapon30 : pszName;
            else if (item->GetRefineLevel() >= PLAYERBOT_PRECIOUS_REFINE) {
                if (!pszPrecious || item->GetRefineLevel() > bPreciousRefine) {
                    pszPrecious = pszName;
                    bPreciousRefine = item->GetRefineLevel();
                }
            }
            else if (item->GetType() == ITEM_FISH || item->GetVnum() == PLAYERBOT_SHELLFISH_VNUM ||
                    (item->GetVnum() >= 27992 && item->GetVnum() <= 27994)) // the three pearls
                ++iFish;
            else if (item->GetVnum() == PLAYERBOT_HORSE_MEDAL_VNUM)
                ++iMedals;
            else if (item->GetVnum() == PLAYERBOT_BLESSING_SCROLL_VNUM)
                ++iScrolls;
            else if (item->GetType() == ITEM_METIN)
                ++iStones;
            else if (item->GetType() == ITEM_SKILLBOOK) {
                pszBook = pszBook ? pszBook : pszName;
                ++iBooks;
            }
            else if ((item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) &&
                    item->GetRefineLevel() < PLAYERBOT_SHOP_MIN_GEAR_REFINE)
                ++iScrap;
            else if (item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) {
                if (!pszGear || item->GetRefineLevel() > bGearRefine) {
                    pszGear = pszName;
                    bGearRefine = item->GetRefineLevel();
                }
                ++iGear;
            }
        }
        const DWORD dwDraw = PlayerBotNavHash(ch->GetPlayerID() ^ 0x5349474eU);
        EPlayerBotSignKind signKind = SIGN_UNIVERSAL;
        const DWORD tableCount = (DWORD)goods.size();
        bool bSignByKind = tableCount > 0 && !pszWeapon30 && !pszPrecious;
        if (bSignByKind) {
            if (iFish > 0 && iFish * 2 >= (int)tableCount) signKind = SIGN_FISH;
            else if (iBooks > 0 && iBooks * 2 >= (int)tableCount) signKind = SIGN_BOOKS;
            else if (iGear > 0 && iGear * 2 >= (int)tableCount) signKind = SIGN_GEAR;
            else if (iMedals > 0 && iMedals * 2 >= (int)tableCount) signKind = SIGN_MEDALS;
            else if (iScrolls > 0 && iScrolls * 2 >= (int)tableCount) signKind = SIGN_SCROLLS;
            else if (iStones > 0 && iStones * 2 >= (int)tableCount) signKind = SIGN_STONES;
            else if (iScrap > 0 && iScrap >= (int)tableCount / 2) bSignByKind = false;
            else if (tableCount == 1) bSignByKind = false;
        }
        char signBody[SHOP_SIGN_MAX_LEN + 1];
        if (bSignByKind && PickPlayerBotShopSign(signBody, sizeof(signBody), signKind, dwDraw,
                ch->GetName(), dwFishUnitPrice, pszGear)) {
            ApplyPlayerBotShopSignPrefix(ch, false, signBody, out, outSize);
        }
        else {
            BuildPlayerBotTurkishShopSign(ch, false, tableCount, pszWeapon30, pszPrecious,
                    iFish, dwFishUnitPrice, iBooks, pszBook, 0, iGear, pszGear,
                    iMedals, iScrolls, iStones, iScrap, pszBestName, dwDraw,
                    out, outSize);
        }
        *how = "pool";
        for (LPITEM preview : goods)
            M2_DELETE(preview);
        return true;
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
        // A dropper's first visit is spread over its own long round: the ten
        // minutes pulled the medal droppers out of the second village 69 times
        // in the first fourteen minutes after a restart.
        if (o.nextService == 0)
            o.nextService = now + 30000 + PlayerBotNavHash(ch->GetPlayerID() ^ 0x4f534856U) %
                (IsPlayerBotDropper(state.bPersonality) ? PLAYERBOT_DROPPER_SHOP_SERVICE_MAX_MS : (DWORD)600000);
        if (BotOfflineBusy(ch, state) || !db_clientdesc || !db_clientdesc->IsPhase(PHASE_DBCLIENT)) {
            if (o.visiting) BotOfflineFinishVisit(ch, state, now);
            return false;
        }
        // An empty hand does not wait out the service interval when its own
        // counter holds something to wear (BotOfflineReclaimLine); probed once
        // a minute.
        if (!o.visiting && shop && !ch->GetWear(WEAR_WEAPON) && Due(now, o.nextReclaimProbe)) {
            o.nextReclaimProbe = now + 60000;
            long long gain = 0;
            if (BotOfflineReclaimLine(ch, state, shop, now, gain) != 0)
                o.nextService = now;
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
            o.nextService = now + BotOfflineServiceGap(state);
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
        BotOfflinePrepareVisitLine(ch, state, shop);
        ch->SetLookingShopOwner(true);
        manager.RecvShopSafeboxOpenClientPacket(ch);
        auto box = ch->GetIkarusShopSafebox();
        if (box && box->GetValutes().yang > 0) manager.RecvShopSafeboxGetValutesClientPacket(ch);
        manager.RecvShopSafeboxCloseClientPacket(ch);
        if (shop->GetDuration() == 0) {
            // An expired stand needs no edit mode to give a line back, and one
            // it would no longer take comes off before the stand is renewed.
            int lowGear = 0;
            const DWORD unwanted = BotOfflineUnwantedLine(shop, lowGear);
            if (unwanted && BotOfflineTakeOff(ch, state, unwanted, lowGear, now)) {
                BotOfflineFinishVisit(ch, state, now);
                return false;
            }
            // So does a piece the owner should be wearing.
            {
                long long gain = 0;
                const DWORD reclaim = BotOfflineReclaimLine(ch, state, shop, now, gain);
                if (reclaim && BotOfflineReclaim(ch, state, reclaim, gain, now)) {
                    BotOfflineFinishVisit(ch, state, now);
                    return false;
                }
            }
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
                // Renamed for what it holds now - eight hours of service visits
                // have added to it - by the same rules as a new stand. A name
                // from before those rules is not renewed either.
                char sign[SHOP_SIGN_MAX_LEN + 1];
                const char* how = "kept";
                if (!BotOfflineNameForGoods(ch, shop, sign, sizeof(sign), &how))
                    strlcpy(sign, shop->GetName(), sizeof(sign));
                manager.RecvShopReopenClientPacket(ch, sign, 1);
                if (EndCall(ch->GetPlayerID()))
                    sys_log(0, "PLAYERBOT_OFFLINE: reopen pid=%u name=%s lines=%u sign=\"%s\" how=%s",
                        ch->GetPlayerID(), ch->GetName(), unsigned(shop->GetItems().size()), sign, how);
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
        // A line the counter would not take today comes off before anything
        // goes on - that is the operation of this visit. The stands already up
        // when the rule arrived held 2 409 such lines between them; a bag with
        // no room for the piece refuses, and then the visit adds instead.
        int lowGearOnCounter = 0;
        {
            const DWORD unwanted = BotOfflineUnwantedLine(shop, lowGearOnCounter);
            if (unwanted && BotOfflineTakeOff(ch, state, unwanted, lowGearOnCounter, now)) {
                BotOfflineFinishVisit(ch, state, now);
                return false;
            }
        }
        // And a piece the owner should be wearing comes home before anything
        // goes on (BotOfflineReclaimLine).
        {
            long long gain = 0;
            const DWORD reclaim = BotOfflineReclaimLine(ch, state, shop, now, gain);
            if (reclaim && BotOfflineReclaim(ch, state, reclaim, gain, now)) {
                BotOfflineFinishVisit(ch, state, now);
                return false;
            }
        }
        std::vector<std::pair<int, WORD> > scored;
        CollectPlayerBotShopItems(ch, scored, IsPlayerBotStallKeeper(state), lowGearOnCounter);
        // The line cut before the board opened goes first, whatever it scores
        // now: it is exactly a line, so BotOfflinePrepareLine below hands it
        // back as it is. A stale cell (the item gone, or another in its
        // place) is simply not it.
        if (o.preparedItem) {
            LPITEM line = ch->GetInventoryItem((WORD)o.preparedCell);
            if (line && line->GetID() == o.preparedItem)
                scored.insert(scored.begin(), std::make_pair(1000000, (WORD)o.preparedCell));
            o.preparedItem = 0;
        }
        bool sent = false;
        for (auto [score, cell] : scored) {
            auto item = ch->GetInventoryItem(cell);
            int pos = BotOfflineSlot(ch, shop, item);
            if (pos < 0) continue;
            // A hoard carries PLAYERBOT_SHOP_HOARD_LINES of one kind on a
            // counter, each a pack cut here (BotOfflinePrepareLine).
            if (IsPlayerBotHoardedMaterial(ch, item) &&
                    BotOfflineLinesOf(shop, item->GetVnum()) >= PLAYERBOT_SHOP_HOARD_LINES) continue;
            if (item->GetVnum() == PLAYERBOT_MOONLIGHT_CHEST_VNUM &&
                    BotOfflineLinesOf(shop, item->GetVnum()) >= PLAYERBOT_CHEST_COUNTER_LINES) continue;
            if (IsPlayerBotSafeRefineScroll(item->GetVnum()) &&
                    BotOfflineLinesOf(shop, item->GetVnum()) >= PLAYERBOT_SHOP_SCROLL_LINES) continue;
            const int lineCell = BotOfflinePrepareLine(ch, cell);
            if (lineCell < 0) continue;
            const WORD at = (WORD)lineCell;
            item = ch->GetInventoryItem(at);
            if (!item || !BotOfflineValid(ch, item, pos)) continue;
            ikashop::TPriceInfo price{};
            price.yang = std::max(GetPlayerBotShopAskingPrice(item), GetPlayerBotRefineInvestment(item));
            if (price.yang <= 0 || price.yang >= GOLD_MAX ||
                    shop->GetTotalYangValue() >= GOLD_MAX - price.yang) continue;
            DWORD id = item->GetID();
            if (Begin(ch->GetPlayerID(), Add, id, now)) {
                manager.RecvShopAddItemClientPacket(ch, TItemPos(INVENTORY, at), price, pos);
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
            // The stamp carries the yang rate too (GetPlayerBotPriceGeneration).
            if (o.priceGeneration != GetPlayerBotPriceGeneration()) {
                if (wrapped) o.priceGeneration = GetPlayerBotPriceGeneration();
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
