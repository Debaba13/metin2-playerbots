#ifndef __INC_METIN2_PLAYERBOT_LLM_SHOP_H__
#define __INC_METIN2_PLAYERBOT_LLM_SHOP_H__

namespace
{
	// Turkish counterpart of upstream's community sign pool
	// (playerbot_shop_signs.h): that file's lists are Iwakura's own Polish
	// market slang, screenshotted off 2010-2012 servers, and are kept as
	// authentic flavor rather than translated - every string a bot actually
	// shows a player goes through this function instead, in Turkish, the same
	// way playerbot_llm_status.h and playerbot_llm_chat_trade.h stand in for
	// their upstream counterparts. The category set (fish/books/materials/
	// gear/medals/scrolls/stones) mirrors upstream's EPlayerBotSignKind so a
	// counter is still named for its majority content.
	void BuildPlayerBotTurkishShopSign(LPCHARACTER ch, bool bPoor, DWORD tableCount,
			const char* pszWeapon30, const char* pszPrecious,
			int iFish, DWORD dwFishUnitPrice, int iBooks, const char* pszBook,
			int iMaterials, int iGear, const char* pszGear,
			int iMedals, int iScrolls, int iStones,
			int iScrap, const char* pszBestName, DWORD dwDraw,
			char* sign, size_t signSize)
	{
		static const char* const s_apszPrefixes[] =
				{ "", "Ucuza: ", "Firsat: ", "Satilik: " };
		static const char* const s_apszBookShops[] = {
			"Skill kitaplari", "Her sinif icin BK", "Skill kitapligi",
			"Kitaplar: %s ve digerleri" };
		static const char* const s_apszMaterialShops[] = {
			"%s malzemeleri", "Demirci malzemeleri", "Deriler ve disler",
			"Gelistirme malzemeleri" };
		static const char* const s_apszFishShops[] = {
			"Balik ve deniz urunleri", "Taze balik burada", "Inci ve midye",
			"Balikci tezgahi" };
		static const char* const s_apszGearShops[] = {
			"Silah ve zirh", "Ekipman firsatlari", "%s ve digerleri",
			"Kaliteli ekipman" };
		static const char* const s_apszMedalShops[] = {
			"At madalyalari", "Madalya burada", "Seyis icin madalyalar" };
		static const char* const s_apszScrollShops[] = {
			"Kutsama tomarlari", "Tomar satisi", "Sansli tomarlar" };
		static const char* const s_apszStoneShops[] = {
			"Ruh taslari", "KD satisi", "Tas burada" };
		static const char* const s_apszMarketCries[] = {
			"Ne ararsan bende var", "Oyuna basladim, bir sey al",
			"%s - en dusuk fiyatlar", "Her sey hesapli", "Uygun fiyatlar",
			"Cesit cesit urunler, beklerim", "Aradigin bende var",
			"Satilik, pazarlik yok" };
		const char* pszPrefix = bPoor ? "Indirim: "
				: s_apszPrefixes[(ch->GetPlayerID() * 2654435761U >> 8) % 4U];
		char body[SHOP_SIGN_MAX_LEN * 2 + 1];
		const char* pszTemplate = NULL;
		const char* pszArg = "";
		if (pszWeapon30)
			snprintf(body, sizeof(body), "30 seviye silah: %s", pszWeapon30);
		else if (pszPrecious)
			snprintf(body, sizeof(body), "%s", pszPrecious);
		else if (iFish > 0 && iFish * 2 >= (int)tableCount)
			pszTemplate = s_apszFishShops[dwDraw % 4U];
		else if (iBooks > 0 && iBooks * 2 >= (int)tableCount)
		{
			pszTemplate = s_apszBookShops[dwDraw % 4U];
			pszArg = pszBook ? pszBook : "";
		}
		else if (iMaterials > 0 && iMaterials * 2 >= (int)tableCount)
		{
			pszTemplate = s_apszMaterialShops[dwDraw % 4U];
			pszArg = IsPlayerBotM1Map(ch->GetMapIndex()) ? "M1" : "M2";
		}
		else if (iGear > 0 && iGear * 2 >= (int)tableCount)
		{
			pszTemplate = s_apszGearShops[dwDraw % 4U];
			pszArg = pszGear ? pszGear : "";
		}
		else if (iMedals > 0 && iMedals * 2 >= (int)tableCount)
			pszTemplate = s_apszMedalShops[dwDraw % 3U];
		else if (iScrolls > 0 && iScrolls * 2 >= (int)tableCount)
			pszTemplate = s_apszScrollShops[dwDraw % 3U];
		else if (iStones > 0 && iStones * 2 >= (int)tableCount)
			pszTemplate = s_apszStoneShops[dwDraw % 3U];
		else if (iScrap > 0 && iScrap >= (int)tableCount / 2)
			snprintf(body, sizeof(body), "Satilik dusuk ekipman +0..+3");
		else if (pszBestName && tableCount > 1 && (dwDraw & 8U) != 0)
			snprintf(body, sizeof(body), "%s ve digerleri", pszBestName);
		else if (tableCount > 1)
		{
			pszTemplate = s_apszMarketCries[dwDraw % 8U];
			pszArg = ch->GetName();
		}
		else
			snprintf(body, sizeof(body), "%s", pszBestName ? pszBestName : ch->GetName());
		if (pszTemplate)
		{
			if (strstr(pszTemplate, "%s"))
				snprintf(body, sizeof(body), pszTemplate, pszArg);
			else
				snprintf(body, sizeof(body), "%s", pszTemplate);
		}
		// dwFishUnitPrice is not read by any branch above: kept as a parameter
		// so the call site's shape matches upstream's scan (and so a future
		// fish sign can quote it, the way s_apszSignFish's "%C" does), not
		// because this function needs it today.
		(void)dwFishUnitPrice;
		if (strlen(pszPrefix) + strlen(body) <= SHOP_SIGN_MAX_LEN)
			snprintf(sign, signSize, "%s%s", pszPrefix, body);
		else
			snprintf(sign, signSize, "%s", body);
	}
}

#endif
