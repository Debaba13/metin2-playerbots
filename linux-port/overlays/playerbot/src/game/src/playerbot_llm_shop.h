#ifndef __INC_METIN2_PLAYERBOT_LLM_SHOP_H__
#define __INC_METIN2_PLAYERBOT_LLM_SHOP_H__

namespace
{
	void BuildPlayerBotTurkishShopSign(LPCHARACTER ch, bool bPoor, DWORD tableCount,
			const char* pszWeapon30, const char* pszPrecious, int iBooks,
			const char* pszBook, int iMaterials, int iScrap, const char* pszBestName,
			char* sign, size_t signSize)
	{
		const DWORD draw = PlayerBotNavHash(ch->GetPlayerID() ^ 0x5349474eU);
		static const char* const s_apszPrefixes[] =
				{ "", "Ucuza: ", "Firsat: ", "Satilik: " };
		static const char* const s_apszBookShops[] = {
			"Skill kitaplari", "Her sinif icin BK", "Skill kitapligi",
			"Kitaplar: %s ve digerleri" };
		static const char* const s_apszMaterialShops[] = {
			"%s malzemeleri", "Demirci malzemeleri", "Deriler ve disler",
			"Gelistirme malzemeleri" };
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
		else if (iBooks > 0 && iBooks * 2 >= (int)tableCount)
		{
			pszTemplate = s_apszBookShops[draw % 4U];
			pszArg = pszBook ? pszBook : "";
		}
		else if (iMaterials > 0 && iMaterials * 2 >= (int)tableCount)
		{
			pszTemplate = s_apszMaterialShops[draw % 4U];
			pszArg = ch->GetMapIndex() == PLAYERBOT_MAP_CHUNJO_M1 ? "M1" : "M2";
		}
		else if (iScrap > 0 && iScrap >= (int)tableCount / 2)
			snprintf(body, sizeof(body), "Satilik dusuk ekipman +0..+3");
		else if (pszBestName && tableCount > 1 && (draw & 8U) != 0)
			snprintf(body, sizeof(body), "%s ve digerleri", pszBestName);
		else if (tableCount > 1)
		{
			pszTemplate = s_apszMarketCries[draw % 8U];
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
		if (strlen(pszPrefix) + strlen(body) <= SHOP_SIGN_MAX_LEN)
			snprintf(sign, signSize, "%s%s", pszPrefix, body);
		else
			snprintf(sign, signSize, "%s", body);
	}
}

#endif
