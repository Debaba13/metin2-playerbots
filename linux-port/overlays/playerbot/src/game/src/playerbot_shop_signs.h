// The words over a stall: market talk, by what the counter holds. Iwakura
// wrote the original lists from 2010-2012 Polish server screenshots
// ("NAZWY SKLEPOW", 11 September 2026) - what people actually put over a
// counter - and asked for them to follow the goods: fish signs on a fish
// counter, book signs on a bookshop, and a keeper with a big refine still
// headlining that item. Fork-owned: the shapes and jokes are Iwakura's,
// the wording is this fork's Turkish, same as every other bot string (see
// playerbot_language.h). This file is the lists and the choice;
// playerbot_town.h decides what kind of counter it is opening.
//
// Player-visible, so ASCII-only Turkish like every other bot string. A name
// may carry three placeholders:
//   %N  the keeper's name
//   %C  the unit price of the counter's fish line (yang)
//   %I  the best gear line's name; the +N is part of the name
// A sign is SHOP_SIGN_MAX_LEN (32) characters. A name that does not fit once
// expanded is passed over for the next one in its list - a long nickname must
// never cut a sign mid-word - and a list with nothing that fits leaves the
// choice to the caller's older wording.
namespace
{
	enum EPlayerBotSignKind
	{
		SIGN_UNIVERSAL,
		SIGN_BOOKS,
		SIGN_FISH,
		SIGN_GEAR,
		SIGN_MATERIALS,
		SIGN_MEDALS,
		SIGN_SCROLLS,
		SIGN_STONES,
	};

	// A mixed counter, or one nothing else describes.
	static const char* const s_apszSignUniversal[] = {
		"DAHA UCUZU OLMAZ",
		"YANDAKINDEN UCUZ >>>>>",
		"<<<<<< YANDAKINDEN UCUZ",
		"Birakiyorum birakiyorum",
		"! ! Hepsini ben buldum ! !",
		"Cesitli esya (AL LUTFEN)",
		"Oyuna baslamam icin yardim?",
		"Her sey ve hicbir sey",
		"BU BOTLARI BANLAYIN!!!",
		"@@@@ DUGUNE BIRIKTIRIYORUM @@@@",
		"%N'in hirdavat dukkani",
		"Rengine gore sec begen",
		"GEL BAK NELERIM VAR",
		"B U Y R U N",
		"Mesaj atin, konusuruz",
		"Cebine gore esya",
		"! ! ESYA ICIN YAZIN ! !",
		"UCUZ :)",
		"ucuzcuk)))))))))))))))))))",
		"INANILMAZ SEYLER !!!!",
		"UCUZZZZZZZZZZZZZZZZZZZZ",
		"@ ILK    DUKKAN @",
		"HASTA MEHMET'E YARDIM :(",
		"Toplamak benim tutkum",
		"Ne varsa yanga satarim",
		"Botla toplandi",
		"Bot tum gece calisti | buyrun",
		"---> %N BUYURUN :) <---",
		"IHTIYACIN OLAN HER SEY :3",
		"Iyi Dukkan",
		"! ! ! HEMEN AL ! ! !",
		".........BUYRUN.........",
		"Bak bakalim icinde ne var",
		"Oyuna yeni basladim, al",
		"%N - en dusuk fiyatlar",
		"Her sey bedava gibi",
		"Sudan ucuz",
		"Ne ariyorsan bende var",
		"Satilik, pazarlik yok",
	};

	// Mostly skill books.
	static const char* const s_apszSignBooks[] = {
		"Dedemden kalma kitaplar",
		"Uyku oncesi kitaplar",
		"BK Indirimi!!",
		"sadece bk",
		"Oku ve YB'ye kas ;p",
		"Tum BK'lar yandan ucuz :)",
		"@@@@@@ BK Sav Sura Ninja @@@@@",
		"Ali'nin Kitabevi :)",
		"Sadece iyi BK, cop yok!!!",
		"@@@@@@@ BK Toptancisi @@@@@@@",
		"Indirimli gizli bilgi",
		"!!!M2'den sadece BK!!!",
		"BK satiyorum, birakiyorum!!",
		"@@@ Okuma bilmeyene @@@",
		"Zor ogrenene okuma dersi",
		"Ahmet'in Okuma Evi",
		"KILIC AURASI KILIC AURASI",
		"Kitaplar senden akilli",
		"! >> Bilgi guctur << !",
		"Yetenek kitaplari",
		"Her sinif icin BK",
	};

	// Mostly shellfish, pearls and fish.
	static const char* const s_apszSignFish[] = {
		"MIDYE INCI BALIK",
		"Midye %C'den!",
		"Balik kokuyor ama ucuz",
		"Inci Beyaz Mavi Kirmizi",
		"@@@@@@@@@@@@ BALIK! @@@@@@@@@@@@",
		"Ali'nin Balikcisi ;]",
		"Ayse'nin Balikcisi ;p",
		"@ @ @ Nehrin Hediyeleri @ @ @",
		"<3 Balikci alisverise cagirir <3",
		"Kendin tut ya da buradan al!",
		"Oltadan +20 drop :O!!!",
		"BALIK | INCI | MIDYE",
		"Midye %C'den - ucuzluk!!",
		"KilcikDemirciyeInatDayanir",
		"UCUZ DENIZ URUNLERI",
		"@@@ BALIK UCUZ, BIRAKIYORUM @@@",
		"MIDYE",
	};

	// Mostly weapons and armour worth a counter (PLAYERBOT_SHOP_MIN_GEAR_REFINE
	// and up); a single big refine still headlines under its own name.
	static const char* const s_apszSignGear[] = {
		"%I UCUZA BAK",
		"@@@@@ BIRAKIYORUM EKIPMAN @@@@@",
		"Demircinin kiymadigi esyalar",
		"SEHRIN EN UCUZ EKIPMANI!",
		"Samanimin dolabi bosaliyor",
		"@ @ Zayif govdeye zirh @ @",
		"Bununla kimse gulmez sana",
		"KALKAN ZIRH SILAH VE DIGER",
		"SOHAN'DA USUME",
		"@@@@ Aci cekerek dovuldu @@@@",
		"! ! ! Olen demircinin esyasi",
		"$ Yumruktan iyidir $",
		"Yabani kopeklere karsi set",
		"EKIPMAN +7/+8/+9 ! ! !",
		">>> EKIPMAN YANDAN UCUZ <<<",
		"%I ve digerleri",
	};

	// Mostly refine materials.
	static const char* const s_apszSignMaterials[] = {
		"MUCEVHER PARCASI | M2 ULEP",
		"@@@@@@@ LANET KITAPLARI @@@@@@@",
		"M2 ve Ork Vadisi'nden ulepler",
		"Hayvan organlarini ucuza veririm",
		"UCUZ ULEPLER, BIRAKIYORUM!!!",
		"Mucevher parcasi, bozuk zirh",
		"@@@ ORK DISLERI @@@",
		"KENDINE +9 EKIPMAN YAP",
		"Orumcek agi ve gozu",
		"Serinlemek icin buz parcasi",
		"Insallah Demirci Yakmaz",
		"Ayi safrasi ve derisi",
		"@@@ Artili Shurikenler @@@",
		"M1/M2 Ulep Dukkani",
		"Tum gelistiriciler!!!",
		"GELISTIRICI YANDAN UCUZ >>>>",
		"Demirci malzemeleri",
		"Deriler, disler, azi disi",
	};

	// One thing a counter can be full of and nothing else describes.
	static const char* const s_apszSignMedals[] = {
		"@@@@@@ AT MADALYALARI @@@@@@",
		"At madalyalari, ucuz",
		"%N'de At Madalyalari",
	};
	static const char* const s_apszSignScrolls[] = {
		"KUTSAMA TOMARLARI",
		"KUTSAMA TOMARLARI UCUZ!",
		"%N'de Kutsama Tomarlari",
	};
	static const char* const s_apszSignStones[] = {
		"Ruhu dindiren taslar [*]",
		"RT +3/+4!!!",
		"@@@ RUH TASLARI @@@",
		"RT yandan ucuz",
	};

	struct TPlayerBotSignList
	{
		const char* const* names;
		size_t count;
	};

	TPlayerBotSignList GetPlayerBotSignList(EPlayerBotSignKind kind)
	{
		TPlayerBotSignList list = { s_apszSignUniversal, sizeof(s_apszSignUniversal) / sizeof(s_apszSignUniversal[0]) };
		switch (kind)
		{
			case SIGN_BOOKS:     list.names = s_apszSignBooks;     list.count = sizeof(s_apszSignBooks) / sizeof(s_apszSignBooks[0]); break;
			case SIGN_FISH:      list.names = s_apszSignFish;      list.count = sizeof(s_apszSignFish) / sizeof(s_apszSignFish[0]); break;
			case SIGN_GEAR:      list.names = s_apszSignGear;      list.count = sizeof(s_apszSignGear) / sizeof(s_apszSignGear[0]); break;
			case SIGN_MATERIALS: list.names = s_apszSignMaterials; list.count = sizeof(s_apszSignMaterials) / sizeof(s_apszSignMaterials[0]); break;
			case SIGN_MEDALS:    list.names = s_apszSignMedals;    list.count = sizeof(s_apszSignMedals) / sizeof(s_apszSignMedals[0]); break;
			case SIGN_SCROLLS:   list.names = s_apszSignScrolls;   list.count = sizeof(s_apszSignScrolls) / sizeof(s_apszSignScrolls[0]); break;
			case SIGN_STONES:    list.names = s_apszSignStones;    list.count = sizeof(s_apszSignStones) / sizeof(s_apszSignStones[0]); break;
			default: break;
		}
		return list;
	}

	// One name with its placeholders filled. False when the result would not
	// fit a sign, or when the name wants something the counter has not got
	// (%I with no gear line, %C with no fish line).
	bool ExpandPlayerBotShopSign(char* out, size_t outSize, const char* pszName,
			const char* pszNick, DWORD dwFishUnitPrice, const char* pszGearName)
	{
		size_t len = 0;
		for (const char* p = pszName; *p; ++p)
		{
			const char* piece = NULL;
			char number[16];
			if (*p == '%' && p[1] != '\0')
			{
				++p;
				if (*p == 'N')
					piece = pszNick ? pszNick : "";
				else if (*p == 'I')
				{
					if (!pszGearName || !*pszGearName)
						return false;
					piece = pszGearName;
				}
				else if (*p == 'C')
				{
					if (dwFishUnitPrice == 0)
						return false;
					snprintf(number, sizeof(number), "%u", dwFishUnitPrice);
					piece = number;
				}
				else
				{
					number[0] = '%'; number[1] = *p; number[2] = '\0';
					piece = number;
				}
			}
			if (piece)
			{
				const size_t n = strlen(piece);
				if (len + n > SHOP_SIGN_MAX_LEN || len + n + 1 > outSize)
					return false;
				memcpy(out + len, piece, n);
				len += n;
				continue;
			}
			if (len + 1 > SHOP_SIGN_MAX_LEN || len + 2 > outSize)
				return false;
			out[len++] = *p;
		}
		out[len] = '\0';
		return len > 0;
	}

	// The list's name for this keeper: the draw picks where to start, and the
	// first name that fits from there wins, so two neighbours with different
	// draws read differently and a draw that lands on a long name still gets
	// a sign. False when nothing in the list fits.
	bool PickPlayerBotShopSign(char* out, size_t outSize, EPlayerBotSignKind kind, DWORD dwDraw,
			const char* pszNick, DWORD dwFishUnitPrice, const char* pszGearName)
	{
		const TPlayerBotSignList list = GetPlayerBotSignList(kind);
		if (list.count == 0)
			return false;
		for (size_t i = 0; i < list.count; ++i)
		{
			const char* pszName = list.names[(dwDraw + i) % list.count];
			if (ExpandPlayerBotShopSign(out, outSize, pszName, pszNick, dwFishUnitPrice, pszGearName))
				return true;
		}
		return false;
	}
}
