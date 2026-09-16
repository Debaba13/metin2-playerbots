// Rendered by linux-port/overlays/playerbot/tools/generate_iwakura_prices.py from Iwakura's price
// list (data/iwakura_ceny.txt, his v1.0). DO NOT EDIT; edit the list and re-run.
//
// Every number here is his, every vnum was resolved against this world's own
// item_proto and mob_proto, and every bonus row was checked against
// world.item_attr for the slot he put it under - the generator refuses to
// write this file if one name cannot be matched or one bonus cannot roll.
//
// Every price scales with the world's yang drop rate along the curve at the top
// of his sheet (PLAYERBOT_PRICE_RATE_POINTS, see ScalePlayerBotIwakuraPrice).
#ifndef __INC_METIN2_PLAYERBOT_PRICE_TABLES_H__
#define __INC_METIN2_PLAYERBOT_PRICE_TABLES_H__

namespace
{
	// The yang drop rate in percent and the multiplier it pays, in hundredths:
	// read straight through between his points and proportionally outside them.
	struct TPlayerBotPriceRatePoint { int iRate; int iPct; };
	const TPlayerBotPriceRatePoint PLAYERBOT_PRICE_RATE_POINTS[] = {
		{   100,   100 },
		{   200,   220 },
		{   500,   500 },
		{   900,   900 },
		{  1000,  1000 },
		{  1500,  1500 },
		{ 10000, 10000 },
	};

	// Weapons, armour, boots, bracelets, necklaces, earrings and shields by
	// family and refine. The index is the refine level, 0 to 9; a bit set in the
	// mask is a refine his sheet marks "do handlarki" - that piece is the
	// merchant's and its price is zero here. A family the table does not carry
	// keeps the old flat prices.
	struct TPlayerBotGearPrice { DWORD dwBaseVnum; WORD wMerchantMask; DWORD adwPrice[10]; };
	const TPlayerBotGearPrice PLAYERBOT_GEAR_PRICES[] = {
		{    10, 0x000, { 9000, 9000, 9000, 9000, 25000, 25000, 25000, 55000, 75000, 120000 } },	// Miecz
		{    20, 0x000, { 12500, 12500, 12500, 12500, 50000, 50000, 50000, 67000, 105000, 160000 } },	// Dlugi Miecz
		{    30, 0x000, { 18000, 18000, 18000, 18000, 30000, 30000, 30000, 79000, 140000, 205000 } },	// Sejmitar
		{    40, 0x000, { 25000, 25000, 25000, 25000, 50000, 50000, 50000, 90000, 220000, 395000 } },	// Stozkowy Miecz
		{    50, 0x000, { 32000, 32000, 32000, 32000, 89000, 89000, 89000, 155000, 270000, 420000 } },	// Szeroki Miecz
		{    60, 0x000, { 30000, 30000, 30000, 30000, 105000, 105000, 105000, 189000, 280000, 505000 } },	// Srebrny Miecz
		{    70, 0x000, { 60000, 60000, 60000, 60000, 120000, 120000, 120000, 240000, 380000, 550000 } },	// Miecz Storczykowy
		{    80, 0x000, { 72000, 72000, 72000, 72000, 135000, 135000, 135000, 290000, 450000, 650000 } },	// Miecz Poltorareczny
		{    90, 0x000, { 73000, 73000, 73000, 73000, 150000, 150000, 150000, 350000, 450000, 710000 } },	// Miecz Barbarzyncy
		{   100, 0x000, { 74000, 74000, 74000, 74000, 165000, 165000, 165000, 430000, 700000, 1150000 } },	// Krwawy Miecz
		{   110, 0x000, { 75000, 75000, 75000, 75000, 170000, 170000, 170000, 470000, 880000, 1250000 } },	// Wielki Miecz
		{   120, 0x000, { 77000, 77000, 77000, 77000, 180000, 180000, 180000, 640000, 950000, 1600000 } },	// Miecz Lat. Maga
		{   130, 0x000, { 78000, 78000, 78000, 78000, 190000, 190000, 190000, 780000, 1350000, 2250000 } },	// Pol-ksiezycowy Miecz
		{   140, 0x000, { 150000, 150000, 150000, 150000, 350000, 350000, 350000, 1200000, 2500000, 4500000 } },	// Miecz Bojowy
		{   150, 0x000, { 130000, 130000, 130000, 130000, 280000, 280000, 280000, 1000000, 2200000, 3500000 } },	// Miecz Szponu Ducha
		{   160, 0x000, { 140000, 140000, 140000, 140000, 320000, 320000, 320000, 1000000, 1900000, 3500000 } },	// Miecz Nimfy
		{   170, 0x000, { 110000, 110000, 110000, 110000, 280000, 280000, 280000, 1200000, 1800000, 2600000 } },	// Miecz Zadlo
		{   180, 0x000, { 1400000, 1400000, 1400000, 1400000, 2000000, 2500000, 3200000, 4600000, 8000000, 13000000 } },	// Zatruty miecz
		{   190, 0x000, { 800000, 800000, 800000, 800000, 1000000, 1350000, 1750000, 2400000, 3200000, 5500000 } },	// Lwi Miecz
		{   290, 0x000, { 370000, 370000, 370000, 370000, 420000, 550000, 660000, 880000, 1250000, 2050000 } },	// Miecz Pelni Ksiezyca
		{  1000, 0x000, { 6800, 6800, 6800, 6800, 19000, 19000, 19000, 40000, 58500, 90000 } },	// Sztylet
		{  1010, 0x000, { 9500, 9500, 9500, 9500, 39000, 39000, 39000, 50000, 81000, 118000 } },	// Sztylet Kobry
		{  1020, 0x000, { 13500, 13500, 13500, 13500, 23500, 23500, 23500, 57500, 105000, 155000 } },	// Sztylet Nozycowy
		{  1030, 0x000, { 18500, 18500, 18500, 18500, 40000, 40000, 40000, 69000, 165000, 300000 } },	// Noz Szczescia
		{  1040, 0x000, { 24000, 24000, 24000, 24000, 69000, 69000, 69000, 113000, 208000, 315000 } },	// Ukaszenie Kota
		{  1050, 0x000, { 23000, 23000, 23000, 23000, 83000, 83000, 83000, 140000, 210000, 394000 } },	// Twarz Diabla
		{  1060, 0x000, { 45000, 45000, 45000, 45000, 93500, 93500, 93500, 175000, 289000, 407000 } },	// Sztylet Piesci Diab.
		{  1070, 0x000, { 53000, 53000, 53000, 53000, 104000, 104000, 104000, 229000, 337500, 494000 } },	// Krwawy Sztylet
		{  1080, 0x000, { 55000, 55000, 55000, 55000, 114000, 114000, 114000, 259000, 351000, 532000 } },	// Zebrowy Noz
		{  1090, 0x000, { 57000, 57000, 57000, 57000, 122000, 122000, 122000, 322000, 553000, 874000 } },	// Chakram
		{  1100, 0x000, { 112000, 112000, 112000, 112000, 273000, 273000, 273000, 912000, 1850000, 3450000 } },	// Smoczy Noz
		{  1110, 0x000, { 104000, 104000, 104000, 104000, 240000, 240000, 240000, 780000, 1440000, 2550000 } },	// Noz Blyskawicy
		{  1120, 0x000, { 87000, 87000, 87000, 87000, 210000, 210000, 210000, 888000, 1380000, 1950000 } },	// Noz Siamese
		{  1130, 0x000, { 1050000, 1050000, 1050000, 1050000, 1560000, 1850000, 2430000, 3350000, 6160000, 9750000 } },	// Skrzydla Demona Chakr.
		{  1170, 0x000, { 227000, 227000, 227000, 227000, 340000, 432000, 636000, 764000, 942000, 1530000 } },	// Kozik Czar. Lis.
		{  2000, 0x000, { 7300, 7300, 7300, 7300, 21000, 21000, 21000, 45000, 59000, 99000 } },	// Luk
		{  2010, 0x000, { 10200, 10200, 10200, 10200, 41000, 41000, 41000, 54500, 85000, 130000 } },	// Dlugi Luk
		{  2020, 0x000, { 14800, 14800, 14800, 14800, 24500, 24500, 24500, 64000, 113000, 165000 } },	// Kompozytowy Luk
		{  2030, 0x000, { 20500, 20500, 20500, 20500, 41000, 41000, 41000, 73500, 178000, 320000 } },	// Bojowy Luk
		{  2040, 0x000, { 20000, 20000, 20000, 20000, 72000, 72000, 72000, 125000, 220000, 340000 } },	// Dlugi Luk Jezdzcy
		{  2050, 0x000, { 24500, 24500, 24500, 24500, 85000, 85000, 85000, 154000, 225000, 405000 } },	// Bojowy Luk Jezdzcy
		{  2060, 0x000, { 49000, 49000, 49000, 49000, 98000, 98000, 98000, 195000, 310000, 450000 } },	// Miedziany Luk
		{  2070, 0x000, { 57000, 57000, 57000, 57000, 110000, 110000, 110000, 235000, 365000, 525000 } },	// Luk Czarnych Ruin
		{  2080, 0x000, { 56000, 56000, 56000, 56000, 121000, 121000, 121000, 285000, 360000, 575000 } },	// Luk Czerwonego Oka
		{  2090, 0x000, { 58000, 58000, 58000, 58000, 135000, 135000, 135000, 350000, 565000, 935000 } },	// Luk Kolczastego Lis.
		{  2100, 0x000, { 61000, 61000, 61000, 61000, 138000, 138000, 138000, 380000, 715000, 1010000 } },	// Luk z rogu byka
		{  2110, 0x000, { 60000, 60000, 60000, 60000, 145000, 145000, 145000, 520000, 770000, 1300000 } },	// Luk Jednorozca
		{  2120, 0x000, { 63500, 63500, 63500, 63500, 154000, 154000, 154000, 635000, 1090000, 1820000 } },	// Olbrz. Skrzydl. Luk
		{  2130, 0x000, { 114000, 114000, 114000, 114000, 260000, 260000, 260000, 810000, 1540000, 2850000 } },	// Boski Luk Moreli
		{  2140, 0x000, { 122000, 122000, 122000, 122000, 285000, 285000, 285000, 970000, 2020000, 3650000 } },	// Olbrz. Luk Zolt. Smoka
		{  2150, 0x000, { 225000, 225000, 225000, 225000, 305000, 430000, 520000, 695000, 880000, 1430000 } },	// Luk Z Rogu Jelenia
		{  2160, 0x000, { 90000, 90000, 90000, 90000, 228000, 228000, 228000, 980000, 1460000, 2100000 } },	// Olbrz. Luk Diabla
		{  2170, 0x000, { 1140000, 1140000, 1140000, 1140000, 1620000, 2030000, 2600000, 3740000, 6480000, 10500000 } },	// Stalowy Luk Kruka
		{  2180, 0x000, { 650000, 650000, 650000, 650000, 810000, 1090000, 1420000, 1950000, 2600000, 4450000 } },	// Luk Niebieskiego Smoka
		{  3000, 0x000, { 8000, 8000, 8000, 8000, 22500, 22500, 22500, 50000, 67000, 108000 } },	// Glewia
		{  3010, 0x000, { 11000, 11000, 11000, 11000, 44000, 44000, 44000, 59000, 92000, 140000 } },	// Wlocznia
		{  3020, 0x000, { 16500, 16500, 16500, 16500, 27500, 27500, 27500, 72000, 128000, 188000 } },	// Gilotynowe Ostrze
		{  3030, 0x000, { 22000, 22000, 22000, 22000, 44500, 44500, 44500, 80000, 195000, 350000 } },	// Pajecza Wlocznia
		{  3040, 0x000, { 29000, 29000, 29000, 29000, 81000, 81000, 81000, 141000, 245000, 382000 } },	// Gizarma
		{  3050, 0x000, { 26000, 26000, 26000, 26000, 91000, 91000, 91000, 164000, 243000, 439000 } },	// Kosa Bojowa
		{  3060, 0x000, { 54000, 54000, 54000, 54000, 108000, 108000, 108000, 216000, 342000, 495000 } },	// Trojzab
		{  3070, 0x000, { 61000, 61000, 61000, 61000, 116000, 116000, 116000, 249000, 387000, 559000 } },	// Halabarda
		{  3080, 0x000, { 67000, 67000, 67000, 67000, 139000, 139000, 139000, 325000, 418000, 660000 } },	// Olbrz. Topor
		{  3090, 0x000, { 65000, 65000, 65000, 65000, 145000, 145000, 145000, 378000, 616000, 1012000 } },	// Lodowa Iglica
		{  3100, 0x000, { 68000, 68000, 68000, 68000, 154000, 154000, 154000, 427000, 800000, 1137000 } },	// Miecz Dwunastu Duchow
		{  3110, 0x000, { 68500, 68500, 68500, 68500, 160000, 160000, 160000, 569000, 845000, 1424000 } },	// Ostrze Zbawienia
		{  3120, 0x000, { 71000, 71000, 71000, 71000, 174000, 174000, 174000, 717000, 1242000, 2070000 } },	// Zabojca Lwow
		{  3130, 0x000, { 135000, 135000, 135000, 135000, 315000, 315000, 315000, 1080000, 2250000, 4050000 } },	// Partyzana
		{  3140, 0x000, { 114000, 114000, 114000, 114000, 246000, 246000, 246000, 880000, 1930000, 3080000 } },	// Magnetyczne Ostrze
		{  3150, 0x000, { 94000, 94000, 94000, 94000, 240000, 240000, 240000, 1030000, 1540000, 2230000 } },	// Zlodziej Dusz
		{  3160, 0x000, { 1300000, 1300000, 1300000, 1300000, 1860000, 2325000, 2970000, 4280000, 7440000, 12090000 } },	// Miecz Zalu
		{  3210, 0x000, { 280000, 280000, 280000, 280000, 358000, 430000, 574000, 782000, 995000, 1855000 } },	// Ostrze Z Czerw. Stali
		{  4000, 0x000, { 9500, 9500, 9500, 9500, 39000, 39000, 39000, 50500, 81000, 120000 } },	// Amija
		{  4010, 0x000, { 19000, 19000, 19000, 19000, 39000, 39000, 39000, 67500, 169000, 296000 } },	// Dziewiec Ostrzy
		{  4020, 0x000, { 22500, 22500, 22500, 22500, 80000, 80000, 80000, 142000, 210000, 379000 } },	// Krotki Noz
		{  5000, 0x000, { 6300, 6300, 6300, 6300, 17500, 17500, 17500, 38500, 52500, 84000 } },	// Miedziany Dzwon
		{  5010, 0x000, { 17500, 17500, 17500, 17500, 35000, 35000, 35000, 63000, 154000, 276500 } },	// Srebrny Dzwon
		{  5020, 0x000, { 22400, 22400, 22400, 22400, 62300, 62300, 62300, 108500, 189000, 294000 } },	// Zloty Dzwon
		{  5030, 0x000, { 21000, 21000, 21000, 21000, 73500, 73500, 73500, 132300, 196000, 353500 } },	// Jadeitowy Dzwon
		{  5040, 0x000, { 42000, 42000, 42000, 42000, 84000, 84000, 84000, 168000, 266000, 385000 } },	// Dzwon Fontanny
		{  5050, 0x000, { 50400, 50400, 50400, 50400, 94500, 94500, 94500, 203000, 315000, 455000 } },	// Morelowy Dzwon
		{  5060, 0x000, { 51100, 51100, 51100, 51100, 105000, 105000, 105000, 245000, 315000, 497000 } },	// Magiczny Dzwon
		{  5070, 0x000, { 51800, 51800, 51800, 51800, 115500, 115500, 115500, 301000, 490000, 805000 } },	// Zloty Robaczy
		{  5080, 0x000, { 52500, 52500, 52500, 52500, 119000, 119000, 119000, 329000, 616000, 875000 } },	// Stalowy Robaczy Dzwon
		{  5090, 0x000, { 53900, 53900, 53900, 53900, 126000, 126000, 126000, 448000, 665000, 1120000 } },	// Dzwon Burzowego Ptaka
		{  5100, 0x000, { 91000, 91000, 91000, 91000, 196000, 196000, 196000, 700000, 1540000, 2450000 } },	// Dzwon Nieba I Ziemi
		{  5110, 0x000, { 169000, 169000, 169000, 169000, 234000, 300000, 452000, 596000, 855000, 1475000 } },	// Antyczny Dzwon
		{  5120, 0x000, { 980000, 980000, 980000, 980000, 1400000, 1750000, 2240000, 3220000, 5600000, 9100000 } },	// Bambusowy Dzwon
		{  5130, 0x000, { 77000, 77000, 77000, 77000, 196000, 196000, 196000, 840000, 1260000, 1820000 } },	// Dzwon Smierci
		{  7000, 0x000, { 6300, 6300, 6300, 6300, 17500, 17500, 17500, 38500, 52500, 84000 } },	// Wachlarz
		{  7010, 0x000, { 8500, 8500, 8500, 8500, 34000, 34000, 34000, 45500, 71400, 109000 } },	// Zelazny Wachlarz
		{  7020, 0x000, { 13000, 13000, 13000, 13000, 21500, 21500, 21500, 57000, 101000, 148000 } },	// Wachlarz Czarn. Tygr.
		{  7030, 0x000, { 16000, 16000, 16000, 16000, 32500, 32500, 32500, 58500, 143000, 257000 } },	// Zurawi Wachlarz
		{  7040, 0x000, { 23500, 23500, 23500, 23500, 66000, 66000, 66000, 115000, 200000, 311000 } },	// Pawi Wachlarz
		{  7050, 0x000, { 20500, 20500, 20500, 20500, 72500, 72500, 72500, 130000, 193000, 348000 } },	// Wodny Wachlarz
		{  7060, 0x000, { 42500, 42500, 42500, 42500, 85000, 85000, 85000, 170000, 270000, 390000 } },	// Kamienny Wachlarz
		{  7070, 0x000, { 48000, 48000, 48000, 48000, 90500, 90500, 90500, 194000, 301000, 435000 } },	// Oceaniczny Wachlarz
		{  7080, 0x000, { 53000, 53000, 53000, 53000, 109000, 109000, 109000, 255000, 328000, 518000 } },	// Zadlowy Wachlarz
		{  7090, 0x000, { 49000, 49000, 49000, 49000, 109000, 109000, 109000, 284000, 462000, 759000 } },	// Wachlarz Feniksa
		{  7100, 0x000, { 52500, 52500, 52500, 52500, 119000, 119000, 119000, 329000, 616000, 875000 } },	// Potrojny Wachlarz
		{  7110, 0x000, { 53000, 53000, 53000, 53000, 124000, 124000, 124000, 442000, 655000, 1100000 } },	// Brwisty Wachlarz
		{  7120, 0x000, { 57500, 57500, 57500, 57500, 140000, 140000, 140000, 577000, 999000, 1665000 } },	// Czarny Slon. Wachlarz
		{  7130, 0x000, { 95000, 95000, 95000, 95000, 218000, 218000, 218000, 680000, 1290000, 2380000 } },	// Niebian. Ptasi Wachl.
		{  7140, 0x000, { 106500, 106500, 106500, 106500, 248500, 248500, 248500, 852000, 1775000, 3200000 } },	// Wachlarz Zbawienia
		{  7150, 0x000, { 79000, 79000, 79000, 79000, 202000, 202000, 202000, 864000, 1300000, 1870000 } },	// Ekstazyjny Wachlarz
		{  7160, 0x000, { 120000, 120000, 120000, 120000, 183000, 245000, 359000, 557000, 778000, 1260000 } },	// Wachlarz Jes. Wiatru
		{  7180, 0x000, { 952000, 952000, 952000, 952000, 1360000, 1700000, 2180000, 3130000, 5440000, 8840000 } },	// Wachlarz 8 Trigramow
		{ 11200, 0x000, { 10000, 10000, 10000, 10000, 28000, 28000, 28000, 60000, 125000, 485000 } },	// Mnisia Zbr. Plytowa
		{ 11210, 0x000, { 15000, 15000, 15000, 15000, 55000, 55000, 55000, 75000, 165000, 500000 } },	// Zelazna Zbr. Plytowa
		{ 11220, 0x000, { 22000, 22000, 22000, 22000, 70000, 70000, 70000, 120000, 380000, 750000 } },	// Zbr. Plyt. Tygrysa
		{ 11230, 0x000, { 35000, 35000, 35000, 35000, 95000, 95000, 95000, 370000, 570000, 1200000 } },	// Lwia Zbroja Plytowa
		{ 11240, 0x000, { 65000, 65000, 65000, 65000, 165000, 165000, 165000, 500000, 1200000, 2570000 } },	// Smiert. Zbroja Plytowa
		{ 11250, 0x000, { 85000, 85000, 85000, 85000, 195000, 195000, 195000, 600000, 1200000, 2570000 } },	// Smocza Zbroja Plytowa
		{ 11260, 0x000, { 90000, 90000, 90000, 90000, 220000, 220000, 220000, 700000, 1400000, 1900000 } },	// Zbroja Plytowa Z Lusek
		{ 11270, 0x000, { 95000, 95000, 95000, 95000, 240000, 240000, 240000, 920000, 1600000, 2800000 } },	// Zlota Zbroja Plytowa
		{ 11280, 0x000, { 250000, 250000, 250000, 250000, 350000, 550000, 1250000, 1700000, 3500000, 7200000 } },	// Zbroja Boga Smokow
		{ 11290, 0x000, { 900000, 900000, 900000, 900000, 1600000, 2200000, 3700000, 4900000, 8500000, 13000000 } },	// Zbroja Z Czarnej Stali
		{ 11400, 0x000, { 8500, 8500, 8500, 8500, 23500, 23500, 23500, 51500, 155500, 392000 } },	// Blekitne Ubranie
		{ 11410, 0x000, { 12500, 12500, 12500, 12500, 46000, 46000, 46000, 64000, 229000, 538000 } },	// Kremowe Ubranie
		{ 11420, 0x000, { 18500, 18500, 18500, 18500, 59500, 59500, 59500, 190000, 425000, 625000 } },	// Czerwone Ubranie
		{ 11430, 0x000, { 30000, 30000, 30000, 30000, 80000, 80000, 80000, 240000, 450000, 705000 } },	// Czer. Ubranie Mrowki
		{ 11440, 0x000, { 55000, 55000, 55000, 55000, 113000, 113000, 113000, 490000, 850000, 1490000 } },	// Ubranie Lwiej Mrowki
		{ 11450, 0x000, { 72500, 72500, 72500, 72500, 164000, 164000, 164000, 495000, 1105000, 1960000 } },	// Ubranie Zabojcy
		{ 11460, 0x000, { 76500, 76500, 76500, 76500, 185000, 185000, 185000, 600000, 1290000, 2500000 } },	// Ubranie Mlodego Smoka
		{ 11470, 0x000, { 81000, 81000, 81000, 81000, 200000, 200000, 200000, 780000, 1880000, 2980000 } },	// Ubranie Zaboj. Wiatru
		{ 11480, 0x000, { 212000, 212000, 212000, 212000, 294000, 465000, 1075000, 1410000, 2975000, 6050000 } },	// Ubranie Fuksyjne
		{ 11490, 0x000, { 865000, 865000, 865000, 865000, 1340000, 1870000, 3180000, 4070000, 7225000, 9240000 } },	// Ubranie Czarn. Wiatru
		{ 11600, 0x000, { 9000, 9000, 9000, 9000, 26000, 26000, 26000, 57000, 148000, 285000 } },	// Zalobna Zbr. Plytowa
		{ 11610, 0x000, { 14000, 14000, 14000, 14000, 51000, 51000, 51000, 69000, 188000, 385000 } },	// Burzowa Zbroj. Plytowa
		{ 11620, 0x000, { 20000, 20000, 20000, 20000, 64500, 64500, 64500, 114000, 227000, 455000 } },	// Nieszczesna Zbr. Plytowa
		{ 11630, 0x000, { 42500, 42500, 42500, 42500, 107500, 107500, 107500, 363000, 832000, 1012000 } },	// Upiorna Zbroja Plytowa
		{ 11640, 0x000, { 61000, 61000, 61000, 61000, 125000, 125000, 125000, 520000, 950000, 1620000 } },	// Zbroja Plyt. Yin-Yang
		{ 11650, 0x000, { 79000, 79000, 79000, 79000, 183000, 183000, 183000, 425000, 880000, 1560000 } },	// Mistyczna Zbroja Plytowa
		{ 11660, 0x000, { 82500, 82500, 82500, 82500, 209000, 209000, 209000, 650000, 1285000, 2085000 } },	// Mglista Zbroja Plytowa
		{ 11670, 0x000, { 88000, 88000, 88000, 88000, 225000, 225000, 225000, 874000, 1470000, 2600000 } },	// Zbroja Twarzy Ducha
		{ 11680, 0x000, { 235000, 235000, 235000, 235000, 322000, 500000, 1185000, 1580000, 3290000, 6620000 } },	// Duchowa Zbroja Plytowa
		{ 11690, 0x000, { 855000, 855000, 855000, 855000, 1500000, 2045000, 3400000, 4450000, 7990000, 10120000 } },	// Zbr. Plyt. Czar. Magii
		{ 11800, 0x000, { 8500, 8500, 8500, 8500, 23500, 23500, 23500, 51500, 72500, 112000 } },	// Blekitna Szata
		{ 11810, 0x000, { 13000, 13000, 13000, 13000, 55500, 55500, 55500, 74500, 126500, 238000 } },	// Turkusowa Szata
		{ 11820, 0x000, { 18500, 18500, 18500, 18500, 59500, 59500, 59500, 103000, 181000, 373000 } },	// Rozowa Szata
		{ 11830, 0x000, { 30000, 30000, 30000, 30000, 80000, 80000, 80000, 238000, 390000, 650000 } },	// Milosna Szata
		{ 11840, 0x000, { 55000, 55000, 55000, 55000, 115000, 115000, 115000, 485000, 950000, 1480000 } },	// Szata Zach. Nieba
		{ 11850, 0x000, { 72000, 72000, 72000, 72000, 168000, 168000, 168000, 330000, 720000, 1550000 } },	// Szata Slonca
		{ 11860, 0x000, { 76500, 76500, 76500, 76500, 189000, 189000, 189000, 595000, 1190000, 2570000 } },	// Szata Moralnosci
		{ 11870, 0x000, { 81500, 81500, 81500, 81500, 204000, 204000, 204000, 780000, 1440000, 2800000 } },	// Szata Pomaran. Kota
		{ 11880, 0x000, { 215000, 215000, 215000, 215000, 297000, 467000, 1050000, 1440000, 2970000, 6040000 } },	// Szata Baronow
		{ 11890, 0x000, { 765000, 765000, 765000, 765000, 1360000, 1870000, 3100000, 4160000, 6850000, 9350000 } },	// Czarna Szata
		{ 13000, 0x000, { 5000, 5000, 5000, 5000, 80000, 80000, 80000, 150000, 240000, 360000 } },	// Bojowa Tarcza
		{ 13020, 0x000, { 65000, 65000, 65000, 65000, 90000, 190000, 280000, 450000, 849000, 1950000 } },	// Pieciokatna Tarcza
		{ 13040, 0x000, { 90000, 90000, 90000, 90000, 125000, 210000, 390000, 574000, 1150000, 2945000 } },	// Czarna Okragla Tarcza
		{ 13060, 0x000, { 150000, 150000, 150000, 150000, 220000, 355000, 590000, 1800000, 3400000, 6000000 } },	// Sokola Tarcza
		{ 13080, 0x000, { 130000, 130000, 130000, 130000, 180000, 275000, 450000, 1500000, 2900000, 5200000 } },	// Tarcza Tygrysa
		{ 13100, 0x000, { 130000, 130000, 130000, 130000, 180000, 275000, 450000, 1500000, 2900000, 5200000 } },	// Lwia Tarcza
		{ 13120, 0x000, { 130000, 130000, 130000, 130000, 180000, 275000, 450000, 1500000, 2900000, 5200000 } },	// Tarcza Smoka
		{ 14000, 0x000, { 5000, 5000, 5000, 5000, 55000, 55000, 55000, 75000, 250000, 450000 } },	// Drewniana Bransoleta
		{ 14020, 0x000, { 15000, 15000, 15000, 15000, 81000, 81000, 81000, 94000, 280000, 480000 } },	// Miedziana Bransoleta
		{ 14040, 0x000, { 75000, 75000, 75000, 75000, 140000, 140000, 140000, 210000, 325000, 800000 } },	// Srebrna Bransoleta
		{ 14060, 0x000, { 25000, 25000, 25000, 25000, 75000, 75000, 75000, 124000, 240000, 350000 } },	// Zlota Bransoleta
		{ 14080, 0x000, { 25000, 25000, 25000, 25000, 65000, 65000, 65000, 84000, 180000, 380000 } },	// Jadeitowa Bransoleta
		{ 14100, 0x000, { 65000, 65000, 65000, 65000, 99000, 99000, 99000, 250000, 660000, 950000 } },	// Ebonitowa Bransoleta
		{ 14120, 0x000, { 19000, 19000, 19000, 19000, 70000, 70000, 70000, 94000, 150000, 350000 } },	// Perlowa Bransoleta
		{ 14140, 0x000, { 120000, 120000, 120000, 120000, 160000, 275000, 380000, 1500000, 2850000, 4200000 } },	// Bransol. Z Bial. Zlota
		{ 14160, 0x000, { 45000, 45000, 45000, 45000, 150000, 150000, 150000, 350000, 530000, 730000 } },	// Krysztalowa Bransoleta
		{ 14180, 0x000, { 46000, 46000, 46000, 46000, 120000, 120000, 120000, 210000, 340000, 660000 } },	// Ametystowa Bransoleta
		{ 14200, 0x000, { 150000, 150000, 150000, 150000, 190000, 275000, 450000, 3100000, 6500000, 9200000 } },	// Bransol. Z Niebian.Lez
		{ 15000, 0x000, { 5000, 5000, 5000, 5000, 40000, 40000, 40000, 75000, 250000, 510000 } },	// Skorzane Buty
		{ 15020, 0x000, { 12000, 12000, 12000, 12000, 50000, 50000, 50000, 84000, 280000, 570000 } },	// Bambusowe Buty
		{ 15040, 0x000, { 15000, 15000, 15000, 15000, 62000, 62000, 62000, 87000, 220000, 520000 } },	// Drewniane Buty
		{ 15060, 0x000, { 35000, 35000, 35000, 35000, 120000, 120000, 120000, 170000, 380000, 600000 } },	// Buty Wyszywane Zlotem
		{ 15080, 0x000, { 80000, 80000, 80000, 80000, 150000, 150000, 150000, 320000, 650000, 1200000 } },	// Skorzane Kozaki
		{ 15100, 0x000, { 30000, 30000, 30000, 30000, 75000, 75000, 75000, 280000, 360000, 790000 } },	// Zlote Buty
		{ 15120, 0x000, { 35000, 35000, 35000, 35000, 75000, 75000, 75000, 280000, 420000, 680000 } },	// Buty Z Brazu
		{ 15140, 0x000, { 65000, 65000, 65000, 65000, 120000, 120000, 120000, 320000, 580000, 880000 } },	// Jadeitowe Buty
		{ 15160, 0x000, { 21000, 21000, 21000, 21000, 85000, 85000, 85000, 87000, 220000, 520000 } },	// Ekstazyjne Buty
		{ 15180, 0x000, { 70000, 70000, 70000, 70000, 130000, 130000, 130000, 320000, 650000, 1200000 } },	// Deszczowe Buty
		{ 15200, 0x000, { 95000, 95000, 95000, 95000, 150000, 300000, 650000, 1600000, 2500000, 4000000 } },	// Buty Feniksa
		{ 15220, 0x000, { 90000, 90000, 90000, 90000, 130000, 280000, 560000, 1400000, 2100000, 3500000 } },	// Buty Ognistego Ptaka
		{ 16000, 0x000, { 5000, 5000, 5000, 5000, 40000, 40000, 40000, 75000, 125000, 240000 } },	// Drewniany Naszyjnik
		{ 16020, 0x000, { 12000, 12000, 12000, 12000, 55000, 55000, 55000, 82000, 165000, 255000 } },	// Miedziany Naszyjnik
		{ 16040, 0x000, { 20000, 20000, 20000, 20000, 67000, 67000, 67000, 92000, 226000, 365000 } },	// Srebrny Naszyjnik
		{ 16060, 0x000, { 25000, 25000, 25000, 25000, 92000, 92000, 92000, 170000, 316000, 445000 } },	// Zloty Naszyjnik
		{ 16080, 0x000, { 60000, 60000, 60000, 60000, 75000, 160000, 290000, 460000, 720000, 950000 } },	// Jadeitowy Naszyjnik
		{ 16100, 0x000, { 55000, 55000, 55000, 55000, 85000, 120000, 210000, 320000, 480000, 990000 } },	// Ebonitowy Naszyjnik
		{ 16120, 0x000, { 55000, 55000, 55000, 55000, 85000, 120000, 210000, 320000, 480000, 990000 } },	// Perlowy Naszyjnik
		{ 16140, 0x000, { 55000, 55000, 55000, 55000, 105000, 170000, 250000, 390000, 540000, 1100000 } },	// Naszyj. Z Bial. Zlota
		{ 16160, 0x000, { 55000, 55000, 55000, 55000, 85000, 120000, 210000, 320000, 480000, 990000 } },	// Krysztalowy Naszyjnik
		{ 16180, 0x000, { 80000, 80000, 80000, 80000, 120000, 190000, 350000, 1200000, 2100000, 4300000 } },	// Ametystowy Naszyjnik
		{ 16200, 0x000, { 90000, 90000, 90000, 90000, 140000, 290000, 570000, 1900000, 3200000, 5900000 } },	// Naszyj. Z Niebian.Lez
		{ 17000, 0x000, { 5000, 5000, 5000, 5000, 40000, 40000, 40000, 75000, 125000, 240000 } },	// Drewniane Kolczyki
		{ 17020, 0x000, { 45000, 45000, 45000, 45000, 80000, 80000, 80000, 110000, 220000, 370000 } },	// Miedziane Kolczyki
		{ 17040, 0x000, { 15000, 15000, 15000, 15000, 40000, 40000, 40000, 75000, 125000, 240000 } },	// Srebrne Kolczyki
		{ 17060, 0x000, { 45000, 45000, 45000, 45000, 80000, 80000, 80000, 120000, 210000, 350000 } },	// Zlote Kolczyki
		{ 17080, 0x000, { 60000, 60000, 60000, 60000, 90000, 150000, 310000, 480000, 950000, 1300000 } },	// Jadeitowe Kolczyki
		{ 17100, 0x000, { 95000, 95000, 95000, 95000, 130000, 225000, 320000, 510000, 1450000, 2500000 } },	// Ebonitowe Kolczyki
		{ 17120, 0x000, { 85000, 85000, 85000, 85000, 110000, 200000, 310000, 480000, 1150000, 2100000 } },	// Perlowe Kolczyki
		{ 17140, 0x000, { 55000, 55000, 55000, 55000, 85000, 140000, 280000, 390000, 750000, 1000000 } },	// Kolczyki Z Bial. Zlota
		{ 17160, 0x000, { 55000, 55000, 55000, 55000, 85000, 140000, 320000, 590000, 890000, 1500000 } },	// Krysztalowe Kolczyki
		{ 17180, 0x000, { 48000, 48000, 48000, 48000, 85000, 140000, 320000, 590000, 890000, 1500000 } },	// Ametystowe Kolczyki
		{ 17200, 0x000, { 125000, 125000, 125000, 125000, 180000, 420000, 600000, 1600000, 3800000, 5150000 } },	// Kolczyki Z Niebian.Lez
	};

	// Upgrade materials ("ULEPSZACZE"), and then everything else he prices by
	// name - the Moonlight chest, the Blessing Scroll, the horse medal, herbs,
	// guild materials, ores and smelted ores - in the second table.
	struct TPlayerBotMaterialPrice { DWORD dwVnum; DWORD dwPrice; };
	const TPlayerBotMaterialPrice PLAYERBOT_MATERIAL_PRICES[] = {
		{ 27799,    76038 },	// Rybia Osc
		{ 27987,   183280 },	// Malz
		{ 27992,  1400900 },	// Biala Perla
		{ 27993,  1027280 },	// Niebieska Perla
		{ 27994,   750500 },	// Krwawa Perla
		{ 30003,    12670 },	// Nos Swini
		{ 30004,    15004 },	// Zab Dzika
		{ 30005,    38686 },	// Kawalek Zepsutej Zbroi
		{ 30006,   126730 },	// Zab Orka
		{ 30007,    60030 },	// Amulet Orka
		{ 30008,   113390 },	// Ezoteryczny Przewodnik
		{ 30009,    41354 },	// Nieznane Lekarstwo
		{ 30010,    36018 },	// Zolc Niedzwiedzia
		{ 30011,    12006 },	// Klab
		{ 30014,    46690 },	// Futro Yeti
		{ 30015,   100050 },	// Pamiatka Po Demonie
		{ 30016,    53360 },	// Klejnot Demona
		{ 30017,    18676 },	// Ozdobna Spinka Do Wlosow
		{ 30018,    66700 },	// Czerwona Wstega
		{ 30019,    60030 },	// Plonaca Grzywa
		{ 30021,    82708 },	// Kawalek Klejnotu
		{ 30022,    53360 },	// Ogon Weza
		{ 30023,    10672 },	// Futro Bialego Tygrysa
		{ 30025,    33350 },	// Worek Z Pajecza Trucizna
		{ 30027,    12668 },	// Futro Wilka
		{ 30028,    12670 },	// Szpon Wilka
		{ 30030,    21344 },	// Zardzewiale Ostrze
		{ 30031,    30682 },	// Ornament
		{ 30032,    60030 },	// Czarny Uniform
		{ 30033,    20010 },	// Stluczona Porcelana
		{ 30034,    33350 },	// Biala Wstega
		{ 30035,    17342 },	// Krem Do Twarzy
		{ 30037,    15338 },	// Szpon Tygrysa
		{ 30038,    12006 },	// Skora Tygrysa
		{ 30039,    24012 },	// Kawalek Plotna
		{ 30040,    13340 },	// Lisc
		{ 30041,    34684 },	// Shuriken
		{ 30042,    20010 },	// Pazur Tygrysa
		{ 30045,    26680 },	// Igla Skorpiona
		{ 30046,    33350 },	// Ogon Skorpiona
		{ 30047,   112056 },	// Ksiega Klatw
		{ 30048,    40010 },	// Kawalek Lodu
		{ 30049,    16008 },	// Lodowy Rog Wieloryba
		{ 30050,   120716 },	// Matowy Lod
		{ 30051,    58696 },	// Nieznany Talizman
		{ 30052,    29680 },	// Flaga
		{ 30053,    28014 },	// Niedzwiedzia Skora
		{ 30055,    92046 },	// Szpon Skorpiona
		{ 30056,    25346 },	// Pajecza Siec
		{ 30057,    54694 },	// Oczy Pajaka
		{ 30058,    48024 },	// Worek Z Pajeczymi Jajami
		{ 30059,    22678 },	// Nogi Pajaka
		{ 30060,    46690 },	// Jezyk Zaby
		{ 30061,    44022 },	// Zabie Udka
		{ 30067,    16008 },	// Skora Weza
		{ 30069,    12670 },	// Szpon Wilka +
		{ 30070,    12004 },	// Futro Wilka +
		{ 30071,    19008 },	// Zolc Niedzwiedzia +
		{ 30072,    18676 },	// Niedzwiedzia Skora +
		{ 30073,    56028 },	// Biala Wstega +
		{ 30074,    28680 },	// Czarny Uniform +
		{ 30075,   122728 },	// Shuriken +
		{ 30076,    33350 },	// Amulet Orka +
		{ 30077,    21344 },	// Zab Orka +
		{ 30078,    45352 },	// Ezoteryczny Przewodnik +
		{ 30079,    65366 },	// Nieznany Talizman +
		{ 30080,    24012 },	// Ksiega Klatw +
		{ 30081,    17342 },	// Ogon Skorpiona +
		{ 30082,    26680 },	// Ogon Weza +
		{ 30083,    46690 },	// Nieznane Lekarstwo +
		{ 30084,    65366 },	// Nieznany Talizman +
		{ 30085,    26680 },	// Kawalek Plotna +
		{ 30086,    40020 },	// Pamiatka Po Demonie +
		{ 30087,    24012 },	// Klejnot Demona +
		{ 30088,    46690 },	// Kawalek Lodu +
		{ 30089,    73370 },	// Futro Yeti +
		{ 30090,    20010 },	// Matowy Lod +
		{ 30091,    74704 },	// Symbol Wojownika
		{ 30092,    13340 },	// Zdobycz Dzikusa
		{ 30116,    44022 },	// Zabie Udka
		{ 30271,    18676 },	// Ozdobna Spinka Do Wlosow
		{ 30344,    75000 },	// Wysuszone Oczy
		{ 30347,    40000 },	// Gourou
		{ 30348,    95000 },	// Lodowata Maz
		{ 30349,    78000 },	// Zywe Drzewo
		{ 30350,    55000 },	// Pazury Malpy
		{ 30352,    50000 },	// Orkowe Jadra
		{ 30355,    45000 },	// Zgnile Mieso
		{ 30356,    32500 },	// Waleczna Dusza Zaprzys
		{ 30358,    54000 },	// Serce Wojownika
		{ 30367,    99000 },	// Luski Smoka
		{ 35002,    41354 },	// Nieznane Lekarstwo
	};
	const TPlayerBotMaterialPrice PLAYERBOT_EXTRA_MATERIAL_PRICES[] = {
		{ 25040,   170000 },	// Zwoj Blogoslawienstwa
		{ 50008,    90000 },	// Zloty klucz
		{ 50009,    72000 },	// Srebrny klucz
		{ 50011,    85000 },	// Szkat. Blasku Ksiezyca
		{ 50050,   180000 },	// Medal konny
		{ 50601,      900 },	// Diamentowy Kamien
		{ 50603,       82 },	// Skamienialy Pien
		{ 50604,       84 },	// Ruda Miedzi
		{ 50605,      328 },	// Ruda Srebra
		{ 50606,      123 },	// Ruda Zlota
		{ 50607,       82 },	// Ruda Jadeitu
		{ 50608,      656 },	// Ruda Ebonitu
		{ 50609,      340 },	// Kawalek Perly
		{ 50610,      620 },	// Ruda Bialego Zlota
		{ 50611,      287 },	// Ruda Krysztalu
		{ 50612,      295 },	// Ruda Ametystu
		{ 50613,      697 },	// Ruda Niebianskich Lez
		{ 50621,   200000 },	// Diament
		{ 50623,    45500 },	// Skamieniale Drewno
		{ 50624,    47000 },	// Miedz
		{ 50625,    68000 },	// Srebro
		{ 50626,    25600 },	// Zloto
		{ 50627,    44900 },	// Jadeit
		{ 50628,   180400 },	// Ebonit
		{ 50629,   110000 },	// Perla
		{ 50630,   138000 },	// Biale Zloto
		{ 50631,    95000 },	// Krysztal
		{ 50632,   105000 },	// Ametyst
		{ 50633,   188600 },	// Niebianskie Lzy
		{ 50701,     1000 },	// Kwiat Brzoskwini
		{ 50702,      500 },	// Pokrzywa
		{ 50703,      550 },	// Kwiat Kaki
		{ 50704,      350 },	// Korzen Gango
		{ 50705,      600 },	// Bez
		{ 50706,      500 },	// Grzyb Tue
		{ 50707,      950 },	// Roza Alpejska
		{ 50708,      900 },	// Morwa
		{ 50721,     1000 },	// Kwiat Brzoskwini
		{ 50722,      500 },	// Pokrzywa
		{ 50723,      550 },	// Kwiat Kaki
		{ 50724,      350 },	// Korzen Gango
		{ 50725,      600 },	// Bez
		{ 50726,      500 },	// Grzyb Tue
		{ 50727,      950 },	// Roza Alpejska
		{ 50728,      900 },	// Morwa
		{ 70201,    20000 },	// Wybielacz
		{ 70202,    25000 },	// Biala Farba Do Wlosow
		{ 70203,    12000 },	// Blond Farba Do Wlosow
		{ 70204,    25000 },	// Czerwona Farba Do Wlosow
		{ 70205,    11000 },	// Brazowa Farba Do Wlosow
		{ 70207,    20000 },	// Wybielacz
		{ 90010,     5000 },	// Kamien Wegielny
		{ 90011,     2000 },	// Pien
		{ 90012,    10000 },	// Dykta
	};

	// Skill books by the skill in socket 0, before the per-listing jitter.
	struct TPlayerBotBookPrice { DWORD dwSkill; DWORD dwPrice; };
	const TPlayerBotBookPrice PLAYERBOT_BOOK_PRICES[] = {
		{   1,   17199 },	// Trzystronne Ciecie
		{   2,   53235 },	// Wir Miecza
		{   3,   73710 },	// Berserk
		{   4,  180810 },	// Aura Miecza
		{   5,   22113 },	// Szarza
		{  16,   53235 },	// Duchowe Uderzenie
		{  17,   12285 },	// Tapniecie
		{  18,   12285 },	// Uderzenie Miecza
		{  19,   95130 },	// Silne Cialo
		{  20,   22932 },	// Walniecie
		{  31,   36855 },	// Zasadzka
		{  32,   13104 },	// Szybki Atak
		{  33,   36855 },	// Wirujacy Sztylet
		{  34,   20475 },	// Krycie Sie
		{  35,   13104 },	// Trujaca Chmura
		{  46,   13104 },	// Powtarzalny Strzal
		{  47,   10647 },	// Deszcz Strzal
		{  48,   45045 },	// Ognista Strzala
		{  49,    8190 },	// Bezszelestny Chod
		{  50,   36855 },	// Trujaca Strzala
		{  61,    7371 },	// Uderzenie Palcem
		{  62,   13104 },	// Smoczy Wir
		{  63,  119700 },	// Czarowane Ostrze
		{  64,   78120 },	// Strach
		{  65,   36855 },	// Czarowana Zbroja
		{  66,   20475 },	// Rozproszenie Magii
		{  76,   18018 },	// Mroczne Uderzenie
		{  77,   21294 },	// Ogniste Uderzenie
		{  78,   36855 },	// Ognisty Duch
		{  79,   32760 },	// Mroczna Ochrona
		{  80,    9828 },	// Duchowy Cios
		{  81,    8190 },	// Mroczny Kamien
		{  91,    7371 },	// Latajacy Talizman
		{  92,    9828 },	// Strzelajacy Smok
		{  93,   25389 },	// Smoczy Skowyt
		{  94,   57330 },	// Blogoslawienstwo
		{  95,   16380 },	// Odbicie
		{  96,   61425 },	// Pomoc Smoka
		{ 106,   12285 },	// Blyskawiczny Rzut
		{ 107,   20475 },	// Przywolanie Blyskawicy
		{ 108,   14742 },	// Szpon Blyskawicy
		{ 109,   36855 },	// Leczenie
		{ 110,   14742 },	// Zwinnosc
		{ 111,    9009 },	// Burza
	};

	// Soul stones by kind and grade. The kinds are the last two digits of the
	// vnum (30-37 weapon, 38-43 armour) and the grade its hundreds digit.
	struct TPlayerBotSoulStonePrice { int iKind; int iGrade; DWORD dwPrice; };
	const TPlayerBotSoulStonePrice PLAYERBOT_SOUL_STONE_PRICES[] = {
		{ 30, 4,    65000 },
		{ 31, 3,    75000 },
		{ 31, 4,   250000 },
		{ 32, 4,    72000 },
		{ 33, 4,    70000 },
		{ 34, 4,    60000 },
		{ 35, 4,    68000 },
		{ 36, 4,    60000 },
		{ 37, 3,    80000 },
		{ 37, 4,   350000 },
		{ 38, 4,    70000 },
		{ 39, 4,    76000 },
		{ 40, 4,    50000 },
		{ 41, 4,    85000 },
		{ 42, 4,    61000 },
		{ 43, 2,    70000 },
		{ 43, 3,   100000 },
		{ 43, 4,   180000 },
	};
	// What a stone of that grade is worth when its kind is not named above.
	// Grade four has no general price in his table: every +4 is listed by name.
	const DWORD PLAYERBOT_SOUL_STONE_GRADE_PRICES[5] = { 12500, 21000, 29000, 45000, 0 };

	// A stone seated in a weapon or armour raises what the piece is worth.
	// First by how many are in it, then by which ones (percent, 100 = x1.0).
	const int PLAYERBOT_SOCKET_COUNT_PERCENT[4] = { 100, 120, 130, 150 };
	struct TPlayerBotSocketStoneMultiplier { int iKind; int iGrade; int iPercent; };
	const TPlayerBotSocketStoneMultiplier PLAYERBOT_SOCKET_STONE_PERCENT[] = {
		{ 30, 4, 140 },
		{ 31, 3, 140 },
		{ 31, 4, 170 },
		{ 32, 4, 120 },
		{ 33, 4, 130 },
		{ 34, 4, 120 },
		{ 35, 4, 130 },
		{ 36, 4, 110 },
		{ 37, 3, 140 },
		{ 37, 4, 180 },
		{ 38, 4, 170 },
		{ 39, 4, 140 },
		{ 40, 4, 120 },
		{ 41, 4, 130 },
		{ 42, 4, 130 },
		{ 43, 3, 120 },
		{ 43, 4, 140 },
	};

	// Polymorph marbles, by the monster in socket 0. Anything not named here
	// is drawn from the band below, stable per marble.
	struct TPlayerBotMarblePrice { DWORD dwMob; DWORD dwPrice; };
	const TPlayerBotMarblePrice PLAYERBOT_MARBLE_PRICES[] = {
		{   502,   65000 },	// Dziki Sluga
		{   701,   50000 },	// Ezoteryczny Fanatyk
		{   731,   55000 },	// Elit. Ezot. Fanatyk
		{   751,   50000 },	// Wysoki Fanatyk
		{   771,   55000 },	// Best. Fanatyk
		{  1402,   40000 },	// Wojownik Z Toporem
		{  1403,   50000 },	// Tysieczny Wojownik
		{  1601,   45000 },	// Ogr Wojownik
		{  2001,   65000 },	// Mlody Pajak
		{  2002,   70000 },	// Trujacy Pajak
		{  2051,   65000 },	// Podly Mlody Truj. Pajak
		{  2052,   65000 },	// Podly Smier. Truj. Pajak
		{  2061,   75000 },	// Maly Trujacy Pajak v2
	};
	const DWORD PLAYERBOT_MARBLE_PRICE_MIN = 15000;
	const DWORD PLAYERBOT_MARBLE_PRICE_MAX = 35000;

	// Forgetting Scrolls by the skill in the socket. A price of zero is his
	// "do sprzedazy u handlarki": that one is the merchant's, not a counter's.
	struct TPlayerBotForgetScrollPrice { DWORD dwSkill; DWORD dwPrice; };
	const TPlayerBotForgetScrollPrice PLAYERBOT_FORGET_SCROLL_PRICES[] = {
		{   1,   52500 },	// OZ Trzystronne Ciecie
		{   2,   62250 },	// OZ Wir Miecza
		{   3,  136550 },	// OZ Berserk
		{   4,       0 },	// OZ Aura Miecza
		{   5,   58500 },	// OZ Szarza
		{  16,   79750 },	// OZ Duchowe Uderzenie
		{  17,   52250 },	// OZ Tapniecie
		{  18,   45500 },	// OZ Uderzenie Miecza
		{  19,       0 },	// OZ Silne Cialo
		{  20,   58200 },	// OZ Walniecie
		{  31,   60400 },	// OZ Zasadzka
		{  32,   59250 },	// OZ Szybki Atak
		{  33,   60400 },	// OZ Wirujacy Sztylet
		{  34,   56250 },	// OZ Krycie Sie
		{  35,   79250 },	// OZ Trujaca Chmura
		{  46,   40400 },	// OZ Powtarzalny Strzal
		{  47,   39250 },	// OZ Deszcz Strzal
		{  48,       0 },	// OZ Ognista Strzala
		{  49,   35750 },	// OZ Bezszelestny Chod
		{  50,   42450 },	// OZ Trujaca Strzala
		{  61,   65000 },	// OZ Uderzenie Palcem
		{  62,   52000 },	// OZ Smoczy Wir
		{  63,       0 },	// OZ Czarowane Ostrze
		{  64,  105000 },	// OZ Strach
		{  65,   66250 },	// OZ Czarowana Zbroja
		{  66,   59250 },	// OZ Rozproszenie Magii
		{  76,   46900 },	// OZ Mroczne Uderzenie
		{  77,   44300 },	// OZ Ogniste Uderzenie
		{  78,       0 },	// OZ Ognisty Duch
		{  79,   76800 },	// OZ Mroczna Ochrona
		{  80,   36000 },	// OZ Duchowy Cios
		{  81,   49250 },	// OZ Mroczny Kamien
		{  91,   48750 },	// OZ Latajacy Talizman
		{  92,   45500 },	// OZ Strzelajacy Smok
		{  93,   35000 },	// OZ Smoczy Skowyt
		{  94,   92800 },	// OZ Blogoslawienstwo
		{  95,   70150 },	// OZ Odbicie
		{  96,       0 },	// OZ Pomoc Smoka
		{ 106,   35150 },	// OZ Blyskawiczny Rzut
		{ 107,   41700 },	// OZ Przywolanie Blyskawicy
		{ 108,   49250 },	// OZ Szpon Blyskawicy
		{ 109,       0 },	// OZ Leczenie
		{ 110,   56250 },	// OZ Zwinnosc
		{ 111,   31750 },	// OZ Burza
	};

	// His bonus multipliers: per slot, per line, one multiplier for the maximum
	// roll and one for any other value, the races split at level 33; a weapon's
	// two damage lines by tiers of their value. They compound into the asking
	// price (GetPlayerBotBonusPricePercent). "Maximum" is the engine's own:
	// g_map_itemAttr's top value for the apply on the item's attribute set.
	// Lines his sheet does not name, or names at x1.0, multiply by nothing. The
	// percent points are hundredths: 250 is x2.5.
	enum EPlayerBotPriceSlot
	{
		PRICE_SLOT_HEAD = 1, PRICE_SLOT_BODY = 2, PRICE_SLOT_SHIELD = 4, PRICE_SLOT_FOOTS = 8,
		PRICE_SLOT_WRIST = 16, PRICE_SLOT_NECK = 32, PRICE_SLOT_EAR = 64, PRICE_SLOT_WEAPON = 128
	};
	struct TPlayerBotBonusPriceRow
	{
		BYTE bSlots;      // EPlayerBotPriceSlot mask
		BYTE bApply;      // APPLY_*
		WORD wMaxPct;     // the maximum roll, hundredths
		WORD wOtherPct;   // any other value, hundredths
		BYTE bMinLevel;   // the item's level limit band, inclusive
		BYTE bMaxLevel;
	};
	const TPlayerBotBonusPriceRow PLAYERBOT_BONUS_PRICE_ROWS[] = {
		{ PRICE_SLOT_HEAD, APPLY_ATTBONUS_ANIMAL, 230, 130, 0, 32 },	// silny przeciwko zwierzetom
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_ANIMAL, 250, 130, 0, 32 },	// silny przeciwko zwierzetom
		{ PRICE_SLOT_HEAD | PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_ANIMAL, 150, 115, 33, 255 },	// silny przeciwko zwierzetom
		{ PRICE_SLOT_HEAD, APPLY_ATTBONUS_DEVIL, 230, 150, 0, 255 },	// silny przeciwko diablom
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_DEVIL, 240, 150, 0, 255 },	// silny przeciwko diablom
		{ PRICE_SLOT_HEAD, APPLY_ATTBONUS_HUMAN, 230, 115, 0, 255 },	// silny przeciwko ludziom
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR, APPLY_ATTBONUS_HUMAN, 250, 140, 0, 255 },	// silny przeciwko ludziom
		{ PRICE_SLOT_WEAPON, APPLY_ATTBONUS_HUMAN, 180, 130, 0, 255 },	// silny przeciwko ludziom
		{ PRICE_SLOT_HEAD | PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_MILGYO, 150, 110, 0, 255 },	// silny przeciwko mistykom
		{ PRICE_SLOT_HEAD | PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR, APPLY_ATTBONUS_ORC, 180, 110, 0, 32 },	// silny przeciwko orkom
		{ PRICE_SLOT_WEAPON, APPLY_ATTBONUS_ORC, 150, 110, 0, 32 },	// silny przeciwko orkom
		{ PRICE_SLOT_HEAD | PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_ORC, 220, 130, 33, 255 },	// silny przeciwko orkom
		{ PRICE_SLOT_HEAD | PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_UNDEAD, 200, 110, 0, 32 },	// silny przeciwko nieumarlym
		{ PRICE_SLOT_HEAD, APPLY_ATTBONUS_UNDEAD, 230, 150, 33, 255 },	// silny przeciwko nieumarlym
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WRIST | PRICE_SLOT_EAR | PRICE_SLOT_WEAPON, APPLY_ATTBONUS_UNDEAD, 250, 150, 33, 255 },	// silny przeciwko nieumarlym
		{ PRICE_SLOT_BODY, APPLY_ATT_GRADE_BONUS, 210, 170, 0, 255 },	// wartosc ataku
		{ PRICE_SLOT_HEAD, APPLY_ATT_SPEED, 200, 120, 0, 255 },	// szybkosc ataku
		{ PRICE_SLOT_FOOTS, APPLY_ATT_SPEED, 170, 130, 0, 255 },	// szbykosc ataku
		{ PRICE_SLOT_SHIELD, APPLY_BLOCK, 250, 150, 0, 255 },	// szansa na blok ciosu
		{ PRICE_SLOT_BODY, APPLY_CAST_SPEED, 160, 115, 0, 255 },	// szybkosc zaklecia
		{ PRICE_SLOT_WEAPON, APPLY_CAST_SPEED, 130, 105, 0, 255 },	// szybkosc zaklecia
		{ PRICE_SLOT_SHIELD, APPLY_CON, 200, 140, 0, 255 },	// witalnosc
		{ PRICE_SLOT_WEAPON, APPLY_CON, 150, 110, 0, 255 },	// witalnosc
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_WEAPON, APPLY_CRITICAL_PCT, 200, 160, 0, 255 },	// szansa na cios krytyczny
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WEAPON, APPLY_DEX, 200, 140, 0, 255 },	// zrecznosc
		{ PRICE_SLOT_HEAD, APPLY_DODGE, 200, 140, 0, 255 },	// szansa na unik. strzaly
		{ PRICE_SLOT_FOOTS, APPLY_DODGE, 160, 120, 0, 255 },	// szansa na unik. strzaly
		{ PRICE_SLOT_SHIELD, APPLY_GOLD_DOUBLE_BONUS, 250, 170, 0, 255 },	// szansa na podwojna ilosc yang
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK, APPLY_GOLD_DOUBLE_BONUS, 250, 150, 0, 255 },	// szansa na podwojna ilosc yang
		{ PRICE_SLOT_HEAD | PRICE_SLOT_NECK, APPLY_HP_REGEN, 130, 110, 0, 255 },	// regeneracja mistur pz
		{ PRICE_SLOT_SHIELD, APPLY_IMMUNE_SLOW, 120, 120, 0, 255 },	// niewrazliwy na spowolnienie
		{ PRICE_SLOT_SHIELD, APPLY_IMMUNE_STUN, 300, 300, 0, 255 },	// niewrazliwy na omdlenie
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WEAPON, APPLY_INT, 200, 140, 0, 255 },	// inteligencja
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK, APPLY_MALL_EXPBONUS, 160, 125, 0, 255 },	// punkty doswiadczenia +%
		{ PRICE_SLOT_WRIST | PRICE_SLOT_EAR, APPLY_MANA_BURN_PCT, 120, 100, 0, 255 },	// szansa na kradziez pe
		{ PRICE_SLOT_BODY, APPLY_MAX_HP, 210, 170, 0, 255 },	// maks. pz
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_WRIST | PRICE_SLOT_NECK, APPLY_MAX_HP, 250, 180, 0, 255 },	// maks. pz
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_WRIST | PRICE_SLOT_NECK, APPLY_MAX_SP, 130, 110, 0, 255 },	// maks. pe
		{ PRICE_SLOT_HEAD, APPLY_MAX_STAMINA, 140, 110, 0, 255 },	// maks. stamina
		{ PRICE_SLOT_BODY, APPLY_MAX_STAMINA, 130, 110, 0, 255 },	// maks. stamina
		{ PRICE_SLOT_EAR, APPLY_MOV_SPEED, 250, 160, 0, 255 },	// szybkosc ruchu
		{ PRICE_SLOT_WRIST | PRICE_SLOT_NECK, APPLY_PENETRATE_PCT, 170, 130, 0, 255 },	// szansa na przeszywajace uderzenie
		{ PRICE_SLOT_WEAPON, APPLY_PENETRATE_PCT, 140, 115, 0, 255 },	// szansa na przeszywajace uderzenie
		{ PRICE_SLOT_HEAD, APPLY_POISON_PCT, 220, 150, 0, 255 },	// szansa na otrucie
		{ PRICE_SLOT_WEAPON, APPLY_POISON_PCT, 140, 120, 0, 255 },	// szansa na otrucie
		{ PRICE_SLOT_EAR, APPLY_POISON_REDUCE, 110, 100, 0, 255 },	// odpornosc na trucizny
		{ PRICE_SLOT_BODY, APPLY_REFLECT_MELEE, 130, 115, 0, 255 },	// szansa na dobicie ciosu
		{ PRICE_SLOT_SHIELD, APPLY_REFLECT_MELEE, 160, 110, 0, 255 },	// szansa na odbicie ciosu
		{ PRICE_SLOT_BODY | PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_EAR, APPLY_RESIST_BELL, 150, 105, 0, 255 },	// odpornosc na dzwony
		{ PRICE_SLOT_BODY | PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_EAR, APPLY_RESIST_BOW, 240, 130, 0, 255 },	// odpornosc na strzaly
		{ PRICE_SLOT_BODY, APPLY_RESIST_DAGGER, 160, 120, 0, 255 },	// odpornosc na sztylety
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_EAR, APPLY_RESIST_DAGGER, 180, 120, 0, 255 },	// odpornosc na sztylety
		{ PRICE_SLOT_BODY | PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_EAR, APPLY_RESIST_FAN, 150, 105, 0, 255 },	// odpornosc na wahlarze
		{ PRICE_SLOT_HEAD, APPLY_RESIST_MAGIC, 170, 115, 0, 255 },	// odpornosc na magie
		{ PRICE_SLOT_BODY, APPLY_RESIST_MAGIC, 150, 120, 0, 255 },	// odpornosc na magie
		{ PRICE_SLOT_WRIST, APPLY_RESIST_MAGIC, 180, 120, 0, 255 },	// odpornosc na magie
		{ PRICE_SLOT_BODY, APPLY_RESIST_SWORD, 160, 120, 0, 255 },	// odpornosc na miecze
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_EAR, APPLY_RESIST_SWORD, 180, 120, 0, 255 },	// odpornosc na miecze
		{ PRICE_SLOT_BODY, APPLY_RESIST_TWOHAND, 160, 120, 0, 255 },	// odrponosc na bron dwureczna
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK | PRICE_SLOT_EAR, APPLY_RESIST_TWOHAND, 180, 120, 0, 255 },	// odrponosc na bron dwureczna
		{ PRICE_SLOT_BODY, APPLY_STEAL_HP, 170, 160, 0, 255 },	// x% obrazen dodanych do pz
		{ PRICE_SLOT_WRIST, APPLY_STEAL_HP, 200, 160, 0, 255 },	// x% obrazen dodanych do pz
		{ PRICE_SLOT_BODY, APPLY_STEAL_SP, 120, 105, 0, 255 },	// x% obrazen dodanych do pe
		{ PRICE_SLOT_SHIELD | PRICE_SLOT_WEAPON, APPLY_STR, 200, 140, 0, 255 },	// sila
		{ PRICE_SLOT_FOOTS | PRICE_SLOT_NECK, APPLY_STUN_PCT, 180, 150, 0, 255 },	// szansa na omdlenie
		{ PRICE_SLOT_WEAPON, APPLY_STUN_PCT, 200, 150, 0, 255 },	// szansa na omdlenie
#if defined(PLAYERBOT_ENGINE_MT2009)
		{ PRICE_SLOT_WRIST | PRICE_SLOT_EAR, APPLY_REFLECT_ARROW, 140, 110, 0, 255 },	// szansa na odbicie pocisku
		{ PRICE_SLOT_HEAD | PRICE_SLOT_BODY | PRICE_SLOT_WRIST, APPLY_SKILL_DURATION, 130, 110, 0, 255 },	// czas trwania umiejetnosci
		{ PRICE_SLOT_HEAD | PRICE_SLOT_BODY | PRICE_SLOT_WRIST, APPLY_ST_REGEN, 130, 110, 0, 255 },	// regeneracja st (staminy)
#endif
	};
	// A weapon's average and skill damage, by tier of the value.
	struct TPlayerBotDamageTier { BYTE bFrom; WORD wPct; };
	const TPlayerBotDamageTier PLAYERBOT_AVERAGE_DAMAGE_TIERS[] = {
		{ 0, 100 }, { 10, 120 }, { 20, 150 }, { 30, 250 }, { 40, 600 }, { 46, 900 }, { 51, 1400 }, { 56, 2800 }, { 60, 7000 }
	};
	const TPlayerBotDamageTier PLAYERBOT_SKILL_DAMAGE_TIERS[] = {
		{ 1, 120 }, { 11, 200 }, { 20, 400 }, { 25, 1400 }, { 30, 4000 }
	};
}

#endif
