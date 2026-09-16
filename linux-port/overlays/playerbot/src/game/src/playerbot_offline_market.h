#ifndef PLAYERBOT_OFFLINE_MARKET_H
#define PLAYERBOT_OFFLINE_MARKET_H
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
// Included after playerbot_market.h so the existing demand/gear rules are used.
namespace {
    bool ManagePlayerBotOfflineShopping(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now) {
        using namespace playerbot_offline;
        auto& o = state.offlineShop;
        auto& manager = ikashop::GetManager();
        if (BotOfflineBusy(ch, state) || requests.count(ch->GetPlayerID()) || o.visiting || state.bMarketTrip) {
            o.buyOwner = 0;
            return false;
        }
        long pitchX = 0, pitchY = 0;
        if (!GetPlayerBotShopCentre(ch->GetMapIndex(), pitchX, pitchY)) return false;
        if (!o.buyOwner) {
            if (!Due(now, o.nextBrowse)) return false;
            o.nextBrowse = now + number(120000, 240000);
            const long long budget = Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR);
            if (budget <= 0) return false;
            std::vector<std::pair<int, NativeShop> > shops;
            for (const auto& [pid, shop] : manager.GetPlayerBotOfflineShops()) {
                if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode()) continue;
                const auto spawn = shop->GetSpawn();
                if (spawn.map != ch->GetMapIndex() || spawn.channel != g_bChannel) continue;
                const int distance = DISTANCE_APPROX(spawn.x-ch->GetX(), spawn.y-ch->GetY());
                if (distance <= PLAYERBOT_MARKET_TRIP_RANGE) shops.emplace_back(distance, shop);
            }
            std::sort(shops.begin(), shops.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
            // Bound expensive item previews and rotate the starting shop.
            unsigned checked = 0;
            const size_t start = shops.empty() ? 0 : (ch->GetPlayerID() + now / 120000) % shops.size();
            for (size_t n = 0; n < shops.size() && checked < 64 && !o.buyOwner; ++n) {
                auto shop = shops[(start+n) % shops.size()].second;
                for (const auto& [id, line] : shop->GetItems()) {
                    if (++checked > 64) break;
                    if (!line) continue;
                    const auto price = line->GetPrice().GetTotalYangAmount();
                    // A level-30 weapon, a medal or a scroll is saved up for: the
                    // bot's own budget caps it, not the median wallet.
                    const long long strategicCap = budget * PLAYERBOT_STRATEGIC_BUDGET_PERCENT / 100;
                    const bool strategic = IsPlayerBotStrategicPurchase(line->GetInfo().vnum);
                    const long long cap = strategic ? strategicCap
                            : (long long)GetPlayerBotMarketMedianWallet() * PLAYERBOT_MARKET_STACK_WALLET_PERCENT / 100;
                    // A weapon far better than the one in the hand is saved for
                    // the same way (IsPlayerBotStrategicWeaponOffer): over the
                    // wallet cap it is still looked at, against the bot's budget.
                    const bool overCap = cap > 0 && price > cap;
                    const bool weaponLine = line->GetTable() && line->GetTable()->bType == ITEM_WEAPON;
                    if (price <= 0 || price > budget ||
                            (overCap && (strategic || !weaponLine || price > strategicCap))) continue;
                    auto preview = BotOfflinePreview(*line);
                    if (!preview) continue;
                    bool want = WantsPlayerBotStallItem(ch, preview) && ch->GetEmptyInventory(preview->GetSize()) >= 0 &&
                            (!overCap || IsPlayerBotStrategicWeaponOffer(ch, preview));
                    M2_DELETE(preview);
                    if (!want) continue;
                    o.buyOwner = shop->GetOwnerPID();
                    o.buyItem = id;
                    o.buyUntil = now + 45000;
                    break;
                }
            }
        }
        if (!o.buyOwner) return false;
        auto shop = manager.GetShopByOwnerID(o.buyOwner);
        if (!shop || shop->GetDuration() == 0 || shop->IsEditMode() || Due(now, o.buyUntil) ||
                shop->GetSpawn().map != ch->GetMapIndex() || shop->GetSpawn().channel != g_bChannel) {
            o.buyOwner = 0;
            ClearPlayerBotRoute(state, true);
            return false;
        }
        auto line = shop->GetItem(o.buyItem);
        if (!line) { o.buyOwner = 0; return false; }
        SetPlayerBotAction(state, BOT_ACTION_TRAVEL, now);
        if (!MovePlayerBotTownLeg(ch, state, now, shop->GetSpawn().x, shop->GetSpawn().y, 600)) return true;
        auto price = line->GetPrice().GetTotalYangAmount();
        if (price > Affordable(ch->GetGold(), GetPlayerBotReservedGold(ch), PLAYERBOT_SHOPPING_GOLD_FLOOR)) {
            o.buyOwner = 0;
            return false;
        }
        if (!BotOfflineBudget(now)) return true;
        // Read before the request: the log line below must not touch the shop
        // line once the purchase is in the engine's hands.
        const DWORD boughtVnum = line->GetInfo().vnum;
        if (boughtVnum == PLAYERBOT_MOONLIGHT_CHEST_VNUM)
            NotePlayerBotChestBought(ch->GetPlayerID(), now);
        if (Begin(ch->GetPlayerID(), Buy, o.buyItem, now)) {
            auto& request = requests.at(ch->GetPlayerID());
            request.vnum = line->GetInfo().vnum;
            request.count = line->GetInfo().count;
            request.unitPrice = uint32_t(price / std::max<uint32_t>(1, request.count));
            if (auto preview = BotOfflinePreview(*line)) {
                request.refine = preview->GetRefineLevel();
                request.skill = preview->GetType() == ITEM_SKILLBOOK ? GetPlayerBotSkillBookSkillVnum(preview) : 0;
                M2_DELETE(preview);
            }
            manager.RecvShopOpenClientPacket(ch, o.buyOwner);
            manager.RecvShopBuyItemClientPacket(ch, o.buyOwner, o.buyItem, false, price);
            const bool sent = EndCall(ch->GetPlayerID());
            manager.RecvCloseShopGuestClientPacket(ch);
            sys_log(0, "PLAYERBOT_OFFLINE: purchase_requested buyer=%u owner=%u item=%u vnum=%u price=%lld sent=%d",
                ch->GetPlayerID(), o.buyOwner, o.buyItem, (unsigned int)boughtVnum, (long long)price, sent);
        }
        o.buyOwner = 0;
        ClearPlayerBotRoute(state, true);
        return false; // DB completion owns delivery; never synthesize money/items
    }
    void AddPlayerBotOfflineLedger(DWORD& stalls, DWORD& lines) {
        for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops()) {
            if (!shop || shop->GetDuration() == 0 || shop->GetSpawn().channel != g_bChannel) continue;
            ++stalls;
            ++s_mapPlayerBotStallsByMap[shop->GetSpawn().map];
            if (IsPlayerBotM2Map(shop->GetSpawn().map)) ++s_iPlayerBotStallsInM2;
            for (const auto& [id, item] : shop->GetItems()) {
                if (!item) continue;
                AddPlayerBotMarketSupply(item->GetVnum(), item->GetInfo().count);
                ++lines;
            }
        }
    }
}
#endif
#endif
