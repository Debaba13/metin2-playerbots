// The words over a stall: the community's own market talk, by what the
// counter holds. Iwakura wrote the lists from 2010-2012 Polish server
// screenshots ("NAZWY SKLEPOW", 11 September 2026) - what people actually put
// over a counter, spelling and all - and asked for them to follow the goods:
// fish signs on a fish counter, book signs on a bookshop, and a keeper with a
// big refine still headlining that item. This file is the lists and the
// choice; playerbot_town.h decides what kind of counter it is opening.
//
// Player-visible, so ASCII-only Polish like every other bot string. A name
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
		"TANIEJ JUZ NIE BEDZIE",
		"TANIEJ NIZ OBOK >>>>>",
		"<<<<<< TANIEJ NIZ OBOK",
		"Koncze gre Koncze gre Koncze gre",
		"! ! Wybocilem to wszystko ! !",
		"Rozne smieci (KUP PLS)",
		"Da ktos cos na rozpoczecie gry?",
		"Wszystko i nic",
		"ZBANUJCIE TE BOTY!!!",
		"@@@@@ ZBIERAM NA SLUB @@@@@",
		"Sklep z roznosciami u %N",
		"do wyboru do koloru",
		"ZOBACZ SAM CO TU MAM",
		"Z A P R A S Z A M",
		"GG 52871243",
		"Itemy na miare twoich yangow",
		"! ! ITEMY SKYPE TOMEK NOWAK ! !",
		"TANIO :)",
		"tanioszka)))))))))))))))))))",
		"CUDA I NIEWIDY !!!!",
		"TANIOOOOOOOOOOOOOOOOOOO",
		"@ PIERWSZY    SKLEP @",
		"WSPOMOZ CHOREGO WOJTKA :(",
		"Zbieractwo to moja pasja",
		"Syf kila i mogila za yangi",
		"Zbierane na nielegalu",
		"Bot dzialal cala noc | zapraszam",
		"---> %N ZaPrAsZa :) <---",
		"WSZYSTKO CZEGO POTRZEBUJESZ :3",
		"Dobry Sklep",
		"! ! ! KUP SZYBKO ! ! !",
		".........ZAPRASZAM.........",
		"Zobacz kotku co mam w srodku",
		"Zaczynam gre, kup cos",
		"%N - najnizsze ceny",
		"Wszystko za grosze",
		"Tanio jak barszcz",
		"Czego szukasz, to mam",
		"Sprzedam, bez targow",
	};

	// Mostly skill books.
	static const char* const s_apszSignBooks[] = {
		"Makulatura po dziadku",
		"Ksiazeczki na dobranoc",
		"Wyprzedaz KU!!",
		"tylko ku",
		"Czytaj i wbijaj na G ;p",
		"Wszystkie KU taniej niz obok :)",
		"@@@@@@ KU Woj Sura Ninja @@@@@",
		"Ksiegarnia u Mirka :)",
		"Tylko dobre KU bez smieci!!!",
		"@@@@@@@ Hurtownia KU @@@@@@@",
		"Tajna wiedza z przeceny",
		"!!!Wyprzedaz z m2 same KU!!!",
		"Sell KU koncze gre!!",
		"@@@ Dla analfabetow @@@",
		"Nauka czytania dla opornych",
		"Czytelnia u Michala",
		"AURA MIECZA AURA MIECZA",
		"Ksiazki madrzejsze od Ciebie",
		"! >> Wiedza to potega << !",
		"Ksiegi umiejetnosci",
		"KU dla kazdej klasy",
	};

	// Mostly shellfish, pearls and fish.
	static const char* const s_apszSignFish[] = {
		"MALZE PERLY RYBKI",
		"Malze po %C sztuka!",
		"Smierdzi ryba ale tanio",
		"Perly Biala Niebieska Krwawa",
		"@@@@@@@@@@@@ RYBY! @@@@@@@@@@@@",
		"Sklep Rybny u Janusza ;]",
		"Sklep Rybny u Wiktori ;p",
		"@ @ @ Dary rzeki @ @ @",
		"<3 Rybak zaprasza na zakupy <3",
		"Zlow to sam albo kup tutaj!",
		"Drop z wedki +20 :O!!!",
		"RYBY | FARBY | MALZE",
		"Malze %C sztuka - taniocha!!",
		"RybieOsciKowalNieZrobiPoZlosci",
		"TANIE OWOCE MORZA",
		"@@@ RYBY TANIO KONCZE GRE @@@",
		"MALZE",
	};

	// Mostly weapons and armour worth a counter (PLAYERBOT_SHOP_MIN_GEAR_REFINE
	// and up); a single big refine still headlines under its own name.
	static const char* const s_apszSignGear[] = {
		"%I TANIO SPRAWDZ",
		"@@@@@@ KONIEC GRY SELL EQ @@@@@@",
		"Rzeczy ktore kowal oszczedzil",
		"EQ NAJTANIEJ w MIESCIE!",
		"Wyprzedaz szafy mojej szamanki",
		"@ @ Zbroje na chude klaty @ @",
		"W tym juz nikt cie nie wysmieje",
		"TARCZE ZBROJE BRONIE I INNE",
		"NIE MARZNIJ NA SOHAN",
		"@@@@ Kute w bolach u kowala @@@@",
		"! ! ! Sprzet po zmarlym kowalu",
		"$ Lepsze to niz bicie z piesci $",
		"Zestaw przetrwania na dzikie psy",
		"EKWIPUNEK +7/+8/+9 ! ! !",
		">>> EQ TANIEJ NIZ OBOK <<<",
		"%I i inne",
	};

	// Mostly refine materials.
	static const char* const s_apszSignMaterials[] = {
		"KAWALKI KLEJNOTU | ULEPY Z M2",
		"@@@@@@@@@ KSIEGI KLATW @@@@@@@@@",
		"Ulepki z m2 i doliny orkow",
		"Narzady zwierzat tanio oddam",
		"TANIE ULEPY KONCZE GRE!!!",
		"Kawalek klejnotu, zepsuta zbroja",
		"@@@ ZEBY ORKA @@@",
		"ZROB SOBIE EQ +9",
		"Pajecze sieci i oczy pajaka",
		"Matowe lody dla ochlody",
		"Oby Kowal Nie Palil",
		"Zolc i skora niedzwiedzia",
		"@@@ Shurikeny z plusem @@@",
		"Sklepik z ulepkami z m1/m2",
		"Wszystkie ulepszacze!!!",
		"ULEPSZACZE TANIEJ NIZ OBOK >>>>",
		"Materialy do kowala",
		"Skory, zeby i kly",
	};

	// One thing a counter can be full of and nothing else describes.
	static const char* const s_apszSignMedals[] = {
		"@@@@@@ MEDALE KONNE @@@@@@",
		"Medale konne, tanio",
		"MEDALE KONNE u %N",
	};
	static const char* const s_apszSignScrolls[] = {
		"ZWOJE BLOGOSLAWIENSTWA",
		"ZWOJE BLOGOSLAWIENSTWA TANIO!",
		"Zwoje blogoslawienstwa u %N",
	};
	static const char* const s_apszSignStones[] = {
		"Kamienie dla ukojenia duszy [*]",
		"KD +3/+4!!!",
		"@@@ KAMIENIE DUCHOW @@@",
		"KD taniej niz obok",
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
