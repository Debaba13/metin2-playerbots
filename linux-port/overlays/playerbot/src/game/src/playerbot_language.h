#ifndef __INC_METIN2_PLAYERBOT_LANGUAGE_H__
#define __INC_METIN2_PLAYERBOT_LANGUAGE_H__

// Fork-owned player-facing bot wording. The upstream source has no equivalent
// language engine, so prepare-context.sh reapplies this overlay after every
// source refresh; keep new player-visible bot text behind this function.
// Keep strings ASCII: the server's legacy chat path and stock data are CP1250.
namespace
{
        const char* PlayerBotText(const char* key)
        {
                if (!key)
                        return "";
                if (strcmp(key, "regeneracja") == 0) return "can basiyorum";
                if (strcmp(key, "profesja") == 0) return "meslek";
                if (strcmp(key, "ekwipunek") == 0) return "esya";
                if (strcmp(key, "zapasy") == 0) return "stok";
                if (strcmp(key, "ulepszanie") == 0) return "basma";
                if (strcmp(key, "rozwoj skilla") == 0) return "skill kasiyorum";
                if (strcmp(key, "Metiny") == 0) return "Metin kesiyorum";
                if (strcmp(key, "silne moby PT") == 0) return "Grup ile guclu mob kesiyorum";
                if (strcmp(key, "Biolog") == 0) return "Biyolog";
                if (strcmp(key, "Polowanie") == 0) return "avlaniyorum";
                if (strcmp(key, "rozwoj konia") == 0) return "at gelistiriyorum";
                if (strcmp(key, "lowienie ryb") == 0) return "balik tutuyorum";
                if (strcmp(key, "poziom") == 0) return "level kasiyorum";

                if (strcmp(key, "ide") == 0) return "gidiyorum";
                if (strcmp(key, "walcze") == 0) return "savasiyorum";
                if (strcmp(key, "zbieram") == 0) return "topluyorum";
                if (strcmp(key, "odpoczywam") == 0) return "dinleniyorum";
                if (strcmp(key, "wybieram profesje") == 0) return "meslek seciyorum";
                if (strcmp(key, "handluje") == 0) return "ticaret yapiyorum";
                if (strcmp(key, "ulepszam") == 0) return "esya basiyorum";
                if (strcmp(key, "czytam KU") == 0) return "BK okuyorum";
                if (strcmp(key, "wkladam KD") == 0) return "Ruh Tasi takiyorum";
                if (strcmp(key, "zbieram PT") == 0) return "Grup topluyorum";
                if (strcmp(key, "robie misje Biologa") == 0) return "Biyolog gorevi yapiyorum";
                if (strcmp(key, "odwiedzam Stajennego") == 0) return "Seyis'e gidiyorum";
                if (strcmp(key, "prowadze stragan") == 0) return "pazar kuruyorum";
                if (strcmp(key, "jestem na zakupach") == 0) return "pazarda alisveris yapiyorum";
                if (strcmp(key, "mysle") == 0) return "takiliyorum";

                if (strcmp(key, "Ide po profesje") == 0) return "Meslekciye gidiyorum";
                if (strcmp(key, "Wybieram profesje") == 0) return "Meslek seciyorum";
                if (strcmp(key, "Ide do handlarza bronia") == 0) return "silahciya gidiyorum";
                if (strcmp(key, "Handluje bronia") == 0) return "silahciyla is yapiyorum";
                if (strcmp(key, "Ide do handlarza zbroja") == 0) return "zirciciya gidiyorum";
                if (strcmp(key, "Handluje zbroja") == 0) return "zircidan alisveris yapiyorum";
                if (strcmp(key, "Ide do handlarki roznosci") == 0) return "marketciye gidiyorum";
                if (strcmp(key, "Kupuje potki i sprzedaje lup") == 0) return "pot basiyor, droplari satiyorum";
                if (strcmp(key, "Ide do kowala") == 0) return "demirciye gidiyorum";
                if (strcmp(key, "Ulepszam ekwipunek") == 0) return "esya basiyorum";
                if (strcmp(key, "Ide do miasta") == 0) return "kente gidiyorum";
                if (strcmp(key, "Wracam na exp") == 0) return "exp yerine donuyorum";
                if (strcmp(key, "Zalatwiam sprawy w miescie") == 0) return "kentte isimi hallediyorum";

                if (strcmp(key, "Nieprzytomny - czekam na wstanie") == 0) return "Bayildim - kalkmayi bekliyorum";
                if (strcmp(key, "Uciekam - mam malo HP") == 0) return "Kaciyorum - can az";
                if (strcmp(key, "Odpoczywam po smierci") == 0) return "Oldum - yeniden dirilmeyi bekliyorum";
                if (strcmp(key, "Rozbijam %s") == 0) return "%s kesiyorum";
                if (strcmp(key, "Polowanie: %s (zostalo %d)") == 0) return "Av: %s (kalan %d)";
                if (strcmp(key, "Gonie %s") == 0) return "%s'nin pesindeyim";
                if (strcmp(key, "Walcze z %s") == 0) return "%s ile savasiyorum";
                if (strcmp(key, "Szukam przeciwnika") == 0) return "rakip ariyorum";
                if (strcmp(key, "Podnosze lup") == 0) return "drop topluyorum";
                if (strcmp(key, "Regeneruje HP") == 0) return "can dolduruyorum";
                if (strcmp(key, "Wybieram profesje") == 0) return "meslek seciyorum";
                if (strcmp(key, "Handluje") == 0) return "ticaret yapiyorum";
                if (strcmp(key, "Czytam ksiege umiejetnosci") == 0) return "BK okuyorum";
                if (strcmp(key, "Wkladam kamien duszy") == 0) return "Ruh Tasi takiyorum";
                if (strcmp(key, "Szukam celu dla grupy") == 0) return "Grup icin hedef ariyorum";
                if (strcmp(key, "Wracam od Biologa") == 0) return "Biyologdan donuyorum";
                if (strcmp(key, "Ide do Biologa z: %s") == 0) return "Biyologa gidiyorum: %s";
                if (strcmp(key, "Oddaje Biologowi: %s") == 0) return "Biyologa teslim ediyorum: %s";
                if (strcmp(key, "Zbieram dla Biologa: %s") == 0) return "Biyolog icin topluyorum: %s";
                if (strcmp(key, "Ide do Stajennego z medalem") == 0) return "Madalyayla Seyis'e gidiyorum";
                if (strcmp(key, "Oddaje medal konny (%u/21)") == 0) return "At madalyasi veriyorum (%u/21)";
                if (strcmp(key, "Ide do Rybaka po przynete") == 0) return "Yem icin balikciya gidiyorum";
                if (strcmp(key, "Ide nad rzeke lowic ryby") == 0) return "Nehirde balik tutmaya gidiyorum";
                if (strcmp(key, "Lowie ryby - czekam na branie") == 0) return "Balik tutuyorum - oltayi bekliyorum";
                if (strcmp(key, "Zakladam przynete na wedke") == 0) return "Yemi oltaya takiyorum";
                if (strcmp(key, "Ogladam stragan") == 0) return "pazar geziyorum";
                if (strcmp(key, "Szukam czegos na straganach") == 0) return "pazarda esya ariyorum";
                if (strcmp(key, "Ide przez portal do M2 po Medal Konny") == 0) return "At Madalyasi icin M2'ye gidiyorum";
                if (strcmp(key, "Ide do Lochu Malp po Medal Konny") == 0) return "At Madalyasi icin Maymun Zindani'na gidiyorum";
                if (strcmp(key, "Ide do najblizszego Stajennego z Medalem") == 0) return "Madalyayla en yakin Seyis'e gidiyorum";
                if (strcmp(key, "Wychodze z Lochu Malp") == 0) return "Maymun Zindani'ndan cikiyorum";
                if (strcmp(key, "Szukam miejsca do expa (cel: %s)") == 0) return "Exp yeri ariyorum (hedef: %s)";
                if (strcmp(key, "Planuje: %s") == 0) return "Plan: %s";

                if (strcmp(key, "Sprzedam %s - stragan w %s") == 0) return "%s satilik - pazar %s'te";
                if (strcmp(key, "Kupie %s - kto ma, niech wystawi w %s") == 0) return "%s ariyorum - %s'te pazara koyun";
                if (strcmp(key, "Mam %s x%u na straganie w %s, %u yang za calosc") == 0) return "Pazarda %s x%u var, yer: %s, toplam %u yang";
                if (strcmp(key, "Mam %s na straganie w %s, %u yang") == 0) return "Pazarda %s var, yer: %s, %u yang";
                if (strcmp(key, "Kupie KU %s - wystaw na straganie w Joan albo Bokjung, boty tam kupuja") == 0) return "BK %s ariyorum - Joan veya Bokjung'da pazara koyun, botlar alir";
                if (strcmp(key, "Kupie %s - wystaw na straganie w Joan albo Bokjung, boty tam kupuja") == 0) return "%s ariyorum - Joan veya Bokjung'da pazara koyun, botlar alir";
                if (strcmp(key, "Stoje ze straganem w %s, mam: %s") == 0) return "%s'te pazarim acik, elimde: %s";
                if (strcmp(key, "Wlasnie ide na targ w %s") == 0) return "%s'te pazara gidiyorum";
                if (strcmp(key, "Nie handluje teraz, poluje. Zajrzyj na stragany w Joan i Bokjung") == 0) return "Su an ticaret yok, kasiyorum. Joan ve Bokjung pazarlarina bak";
                if (strcmp(key, "nic juz") == 0) return "bosta";
                if (strcmp(key, "miescie") == 0) return "kent";
                if (strcmp(key, "Tanio: ") == 0) return "Ucuza: ";
                if (strcmp(key, "Okazja: ") == 0) return "Firsat: ";
                if (strcmp(key, "Sprzedam ") == 0) return "Satilik ";
                if (strcmp(key, "Bron 30: %s") == 0) return "30'luk silah: %s";
                if (strcmp(key, "Ksiegi: %s i inne") == 0) return "SK: %s ve digerleri";
                if (strcmp(key, "Ksiega: %s") == 0) return "SK: %s";
                if (strcmp(key, "Zlom do palenia +0..+3") == 0) return "+0..+3 yakmalik esyalar";
                if (strcmp(key, "%s i inne") == 0) return "%s ve digerleri";

                if (strcmp(key, "%s - potki %u/%u") == 0) return "%s - iksir %u/%u";
                if (strcmp(key, "%s (cel: %s)") == 0) return "%s (hedef: %s)";
                if (strcmp(key, "Uciekam - mam malo HP") == 0) return "Kaciyorum - can az";
                if (strcmp(key, "Czekam na trase do handlarza; potem %s") == 0) return "Saticiya giden yolu bekliyorum; sonra %s";
                if (strcmp(key, "Czekam na trase do handlarza") == 0) return "Saticiya giden yolu bekliyorum";
                if (strcmp(key, "Szykuje lur dla druzyny") == 0) return "Grup icin lure hazirliyorum";
                if (strcmp(key, "Wracam do druzyny: prowadze %d mobow") == 0) return "Gruba donuyorum: %d mob getiriyorum";
                if (strcmp(key, "Przekazuje moby: %d przyprowadzonych, %d nadal za mna") == 0) return "Moblar teslim ediliyor: %d getirildi, %d hala pesimde";
                if (strcmp(key, "Wstrzymuje lur: druzyna jeszcze walczy") == 0) return "Lure ara verildi: grup hala savasiyor";
                if (strcmp(key, "Luruje dla PT: %u/%u grupy, sciga mnie %d") == 0) return "Grup icin lure: %u/%u grup, pesimde %d";
                if (strcmp(key, "Odpoczywam po smierci") == 0) return "Olumden sonra dinleniyorum";
                if (strcmp(key, "Rozbijam %s") == 0) return "%s kiriyorum";
                if (strcmp(key, "Polowanie: %s (zostalo %d)") == 0) return "Av: %s (kalan %d)";
                if (strcmp(key, "Bronie sie przed %s") == 0) return "%s'e karsi savunuyorum";
                if (strcmp(key, "Pomagam druzynie: %s") == 0) return "Gruba yardim ediyorum: %s";
                if (strcmp(key, "Zbieram material z %s") == 0) return "%s malzemesini topluyorum";
                if (strcmp(key, "Gonie %s") == 0) return "%s'nin pesindeyim";
                if (strcmp(key, "Walcze z %s") == 0) return "%s ile savasiyorum";
                if (strcmp(key, "Szukam przeciwnika") == 0) return "Rakip ariyorum";
                if (strcmp(key, "Podnosze lup") == 0) return "Ganimet topluyorum";
                if (strcmp(key, "Regeneruje HP") == 0) return "Can dolduruyorum";
                if (strcmp(key, "Czytam ksiege umiejetnosci") == 0) return "Yetenek kitabi okuyorum";
                if (strcmp(key, "Wkladam kamien duszy") == 0) return "Ruh Tasi takiyorum";
                if (strcmp(key, "Szukam celu dla grupy") == 0) return "Grup icin hedef ariyorum";
                if (strcmp(key, "Wracam od Biologa") == 0) return "Biyologdan donuyorum";
                if (strcmp(key, "Ide do Biologa z: %s") == 0) return "Biyologa gidiyorum: %s";
                if (strcmp(key, "Oddaje Biologowi: %s") == 0) return "Biyologa teslim ediyorum: %s";
                if (strcmp(key, "Zbieram dla Biologa: %s") == 0) return "Biyolog icin topluyorum: %s";
                if (strcmp(key, "Ide do Stajennego z medalem") == 0) return "Madalyayla Seyis'e gidiyorum";
                if (strcmp(key, "Oddaje medal konny (%u/21)") == 0) return "At madalyasi veriyorum (%u/21)";
                if (strcmp(key, "Ide do Rybaka po przynete") == 0) return "Yem icin balikciya gidiyorum";
                if (strcmp(key, "Ide nad rzeke lowic ryby") == 0) return "Nehirde balik tutmaya gidiyorum";
                if (strcmp(key, "Lowie ryby - czekam na branie") == 0) return "Balik tutuyorum - oltayi bekliyorum";
                if (strcmp(key, "Szukam wedki") == 0) return "Olta ariyorum";
                if (strcmp(key, "Zakladam przynete na wedke") == 0) return "Yemi oltaya takiyorum";
                if (strcmp(key, "Ogladam stragany") == 0) return "Pazar tezgahlarini geziyorum";
                if (strcmp(key, "Ogladam stragan") == 0) return "Pazari inceliyorum";
                if (strcmp(key, "Szukam czegos na straganach") == 0) return "Pazarlarda bir sey ariyorum";
                if (strcmp(key, "Ide przez portal do M2 po Medal Konny") == 0) return "At Madalyasi icin portaldan M2'ye gidiyorum";
                if (strcmp(key, "Ide do Lochu Malp po Medal Konny") == 0) return "At Madalyasi icin Maymun Zindani'na gidiyorum";
                if (strcmp(key, "Ide do najblizszego Stajennego z Medalem") == 0) return "Madalyayla en yakin Seyis'e gidiyorum";
                if (strcmp(key, "Wychodze z Lochu Malp") == 0) return "Maymun Zindani'ndan cikiyorum";
                if (strcmp(key, "Ide do miasta po zapasy") == 0) return "Stok icin sehre gidiyorum";
                if (strcmp(key, "Ide do kowala ulepszyc ekwipunek") == 0) return "Esya gelistirmek icin demirciye gidiyorum";
                if (strcmp(key, "Ide do Biologa") == 0) return "Biyologa gidiyorum";
                if (strcmp(key, "Ide nad rzeke lowic ryby") == 0) return "Nehirde balik tutmaya gidiyorum";
                if (strcmp(key, "Ide do miasta po ekwipunek") == 0) return "Ekipman icin sehre gidiyorum";
                if (strcmp(key, "Szukam lepszego miejsca (cel: %s)") == 0) return "Daha iyi bir yer ariyorum (hedef: %s)";
                if (strcmp(key, "Planuje: %s") == 0) return "Planliyorum: %s";
                if (strcmp(key, "Mam %s x%u na straganie w %s, %u yang za calosc") == 0) return "Pazarda %s x%u var, yer: %s, toplam %u yang";
                if (strcmp(key, "Stoje ze straganem w %s, mam: %s") == 0) return "%s'te pazarim acik, elimde: %s";
                if (strcmp(key, "Wlasnie ide na targ w %s") == 0) return "%s'te pazara gidiyorum";
                if (strcmp(key, "Nie handluje teraz, poluje. Zajrzyj na stragany w Joan i Bokjung") == 0) return "Su an ticaret yok, avlaniyorum. Joan ve Bokjung pazarlarina bak";
                if (strcmp(key, "%s stoi! Zbieramy sie na niego.") == 0) return "%s burada! Ona saldiriyoruz.";
                if (strcmp(key, "do Joan") == 0) return "Joan'a";
                if (strcmp(key, "do Bokjung") == 0) return "Bokjung'a";
                if (strcmp(key, "do Pyungmoo") == 0) return "Pyungmoo'ya";
                if (strcmp(key, "do Lochu Malp") == 0) return "Maymun Zindani'na";
                if (strcmp(key, "do Lochu Malp II") == 0) return "Maymun Zindani II'ye";
                if (strcmp(key, "do Lochu Malp III") == 0) return "Maymun Zindani III'e";
                if (strcmp(key, "na Pustynie Yongbi") == 0) return "Yongbi Colu'na";
                if (strcmp(key, "do Doliny Orkow") == 0) return "Ork Vadisi'ne";
                if (strcmp(key, "na Gore Sohan") == 0) return "Sohan Dagi'na";
                if (strcmp(key, "do Lochu Pajakow") == 0) return "Orumcek Zindani'na";
                if (strcmp(key, "do Swiatyni Hwang") == 0) return "Hwang Tapinagi'na";
                if (strcmp(key, "Ide po profesje") == 0) return "Meslek secmeye gidiyorum";
                if (strcmp(key, "Ide do handlarza bronia") == 0) return "Silah saticisina gidiyorum";
                if (strcmp(key, "Handluje bronia") == 0) return "Silah saticisiyla ticaret yapiyorum";
                if (strcmp(key, "Ide do handlarza zbroja") == 0) return "Zirh saticisina gidiyorum";
                if (strcmp(key, "Handluje zbroja") == 0) return "Zirh saticisiyla ticaret yapiyorum";
                if (strcmp(key, "Ide do handlarki roznosci") == 0) return "Genel saticiya gidiyorum";
                if (strcmp(key, "Kupuje potki i sprzedaje lup") == 0) return "Iksir aliyor, ganimet satiyorum";
                if (strcmp(key, "Ide do kowala") == 0) return "Demirciye gidiyorum";
                if (strcmp(key, "Ide do miasta") == 0) return "Sehre gidiyorum";
                if (strcmp(key, "Wracam na exp") == 0) return "Exp yerine donuyorum";
                if (strcmp(key, "Zalatwiam sprawy w miescie") == 0) return "Sehirde islerimi hallediyorum";
                if (strcmp(key, "%s poszedl na +7, kowal dzis laskawy") == 0) return "%s +7 oldu, demirci bugun sansli";
                if (strcmp(key, "no i mam +7 na %s, moglo byc gorzej") == 0) return "%s +7 oldu, daha kotusu olabilirdi";
                if (strcmp(key, "+7 na %s siadlo za pierwszym razem") == 0) return "%s +7 ilk denemede basildi";
                if (strcmp(key, "udalo sie, %s na +7") == 0) return "Basardim, %s +7 oldu";
                if (strcmp(key, "%s na +8! rece mi sie trzesly") == 0) return "%s +8! Ellerim titredi";
                if (strcmp(key, "jest +8 na %s, teraz sie zastanawiam czy pchac dalej") == 0) return "%s +8 oldu, daha ileri basayim mi diye dusunuyorum";
                if (strcmp(key, "+8 na %s, chyba mam dzis szczescie") == 0) return "%s +8 oldu, galiba bugun sansliyim";
                if (strcmp(key, "weszlo na +8, %s gotowy do roboty") == 0) return "+8 oldu, %s goreve hazir";
                if (strcmp(key, "%s NA +9!!! nie wierze") == 0) return "%s +9!!! Inanamiyorum";
                if (strcmp(key, "+9 na %s, kto by pomyslal") == 0) return "%s +9 oldu, kim dusunurdu";
                if (strcmp(key, "dziewiatka na %s, dzis stawiam :D") == 0) return "%s +9 oldu, bugun benden :D";
                if (strcmp(key, "%s +9, chyba wystarczy tych probek na dzis") == 0) return "%s +9, galiba bugunluk yeter";
                return key;
        }

        const char* GetPlayerBotTownNameTurkish(long mapIndex)
        {
                if (mapIndex == PLAYERBOT_MAP_CHUNJO_M1)
                        return "Joan";
                if (mapIndex == PLAYERBOT_MAP_CHUNJO_M2)
                        return "Bokjung";
                return "kent";
        }

        void FormatPlayerBotText(char* out, size_t size, const char* prefix,
                        const char* key, ...)
        {
                if (!out || size == 0)
                        return;
                char body[512];
                va_list args;
                va_start(args, key);
                vsnprintf(body, sizeof(body), PlayerBotText(key), args);
                va_end(args);
                snprintf(out, size, "%s%s", prefix ? prefix : "", body);
        }
}

#endif
