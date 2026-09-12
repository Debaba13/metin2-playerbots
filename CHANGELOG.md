# Changelog

Every release of this project, newest first. The admin panel reads this file to
show you what an update would bring before you install it.

Versions are `MAJOR.MINOR.PATCH`:

- **PATCH** — a fix. Nothing you do changes.
- **MINOR** — something new, or something behaves better than it did. Safe to
  take; nothing you have set up stops working.
- **MAJOR** — something you have to act on. A setting that has to move, a
  command that no longer exists, a manual step during the update. These say so
  at the top, in full, before anything else.

Updating never touches your database. Characters, accounts and settings survive
every version here.

---

## 2.0.14 — 2026-09-12

Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Panel klasyczny: polskie znaki w nazwach przedmiotów

W 2.0.13 panel czyta nazwy z `item_proto` tego świata, ale kolumna jest w
CP1250, a połączenie panelu z bazą w latin1 — serwer bazy konwertował
nazwy po drodze i każda litera, której latin1 nie ma („ł, ś, ż, ę, ń”),
przychodziła jako „?”: „Skrzyd?a Demona Chakr.”, „Zw?j B?ogos?awie?stwa”.
Panel prosi teraz o surowe bajty i dekoduje je sam. Sprawdzone na 6001
nazwach: ani jednego znaku zapytania.

### Panel klasyczny: bazowe statystyki przedmiotu w dymku

Dymek przedmiotu pokazywał linie bonusów i sloty, a wartość ataku, obronę,
stałe bonusy przedmiotu i wymagany poziom brał ze statycznej tabeli linii
1.x — dla przedmiotu, który ma tam ten sam numer, były to liczby drugiego
silnika, dla reszty nic. Na mt2009 te pola też idą z `item_proto` tego
świata i dymek liczy je jak klient: Lwi Miecz +9 to „Wartość Ataku 226–251”,
„Wartość Magicznego Ataku 163–209”, „Szybkość Ataku +26%” i „Wymagany
Poziom 75”, dokładnie jak w grze.

## 2.0.13 — 2026-09-12

Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Profil wyposażenia czterech GM na koncie admin

Konto `admin` ma cztery postacie GM — Admin (wojownik), AdminNinja,
AdminSura i postać operatora — i dotąd tylko generator `gm_characters.sql`
je wyposażał: raz, przy tworzeniu, bez umiejętności, bez konia w siodle i
bez eliksirów; postać założoną ręcznie przed dodaniem generatora (Tieru,
szamanka na poziomie 1 z wachlarzem +0) omijał w całości, a stosy 50 zwojów
i 50 medali w jednym rekordzie były stosami, których silnik nie utrzymuje
(proto: 20). Nowy quest `gm_profile` uruchamia się przy każdym logowaniu
postaci GM z konta `admin` i, gdy wersja profilu postaci jest starsza,
doprowadza ją do profilu przez własne ścieżki silnika: poziom 90, 500 mln
yang, grupa umiejętności 1 i umiejętności profesji na P (40), wspólne na
własnych sufitach (jazda 21, przywołanie konia 10, języki i konne 20),
koń 21, komplet +9 klasy z bonusami z audytu (`docs/codex-audits/admin-gm-
mt2009-20260912`) założony na postać, druga broń, 1000 strzał dla ninja,
plecak (księga wojskowego konia 50053, po 200 dużych eliksirów, zwoje po 20,
pierścień teleportacji, pełne automatyczne eliksiry 72726/72730 po dwie
sztuki), a kilka sekund po zalogowaniu włącza po jednym eliksirze każdego
rodzaju — przez tę samą ścieżkę użycia, którą idzie kliknięcie w kliencie,
bo tylko ona zakłada efekt regeneracji. Każdy krok pyta najpierw, co postać
już ma: przedmiot noszony lub leżący w plecaku nie jest dawany drugi raz,
stosy są dopełniane do minimum, a przy ponownym logowaniu i po restarcie
nic się nie dubluje (flaga wersji zapisywana na końcu). Starterowy złom —
broń +0 klasy i małe mikstury — schodzi dopiero, gdy broń profilu jest
założona; questy startowe dostają znacznik „wydano”, żeby nie nadały go
ponownie. Dobre przedmioty zostają. Do tego dwie poprawki silnika:
fabryka przedmiotów tworzyła każdy automatyczny eliksir jako zużyty (gniazdo
„zużyte” równe pojemności — świeży eliksir z NPC lub z panelu mówił
„pusty”), a questy dostały `item.use()` (przez `UseItemEx`, bo `UseItem`
odmawia wszystkiego, gdy działa skrypt questa). Silnik dopuszcza pięć
założeń na pół sekundy, a logowanie potrafi je zużyć, więc to, czego
logowanie nie założyło, ubiera timer kilka sekund później.
`gm_characters.sql` wpisuje stosy zgodne z proto i nie daje medali konnych.
Sprawdzone na stosie testowym na wszystkich czterech postaciach (w tym
Tieru z poziomu 1 i ninja z łukiem w ręku): komplet założony, eliksiry
włączone przez quest, po dwa–trzy logowania i restart rdzenia z tą samą
liczbą przedmiotów.

### Gildie botów z nazwami od Iwakury

Boty zakładały gildie pod dwiema nazwami na królestwo — sześć gildii na
świat, a każdy kolejny założyciel zastawał obie nazwy zajęte. Pula to teraz
sto nazw z listy Iwakury (`data/guild_names_iwakura.txt`, „Shire”,
„UrzadPracy”, „TotalneBoty”…): założyciel zaczyna od miejsca wyliczonego z
własnego pid, bierze pierwszą nazwę, której żadna gildia na świecie nie
nosi, i pomija te dłuższe niż limit silnika (14 znaków na mt2009). Sam
system — założenie przez bota od 40 poziomu z 200 tys. yang, zaproszenia
dla botów tego samego królestwa w pobliżu, wspólne polowania na bossa przez
czat gildii — bez zmian; w tej wersji sprawdzony na żywo na stosie
testowym: stu botom Chunjo podniesiono poziom do 41, siedem gildii
powstało w trzy sekundy od startu (Biedronka, TotalneBoty, Vitality,
BlackWolfs, Zawodowcy, ZakonBigosu, Anarchia), 24 członków po trzech
minutach, tabele `guild` i `guild_member` wypełnione.

### Linux: aktualizacja z paczki, nie z gita

Na serwerze bez launchera (Debian/VPS) jedyną drogą aktualizacji był
aktualizator linii 1.x: `installer/install.sh` i kontener `updater`, które
odświeżają checkout repozytorium i nakładają drzewo `linux-port/` — linii 1.x.
Na serwerze 2.x kończyło się to wersją 1.33.3 w `VERSION`, stawkami
zawieszonymi w `state=running` (skrypt stawek 1.x nie zna flag zdarzeń
mt2009), panelem, który nie rozmawia z grą, i aktualizacją z panelu stojącą
na 40% (l0st3k, 12 września: „checkout z main melduje 1.33.3”). Nowy
`linux-port/tools/update.sh` robi na Linuksie to, co launcher na Windows:
czyta `update-manifest-mt2009.json`, pobiera paczkę tej linii, sprawdza sumę
SHA-256, rozpakowuje ją na folder serwera (`.env` zostaje) i uruchamia
`docker compose up -d --build`. Kontener `updater` z profilu `update`
uruchamia ten skrypt w trybie `watch` (te same pliki `request` i
`update.status`, które pisze i czyta panel), a przycisk w panelu klasycznym
pokazuje polecenie dla tej linii. `PACZKA_INFO.txt` ma sekcję dla Linuksa.
Sprawdzone w kontenerze `python:3-alpine`: pobranie, suma, 6454 plików
rozpakowanych na miejsce, `.env` nietknięty, tryb `watch` odpowiada na
żądanie panelu.

### Skrzynie nie wysypują się na ziemię

„Postać nadal źle sprawdza zajętość ekwipunku: otwierając skrzynię, wypada
to na ziemię” (sizowski, zrzut z Zieloną Siłą i Skrzynią Eksperta I na
trawie). Na mt2009 stała `INVENTORY_MAX_NUM` to 135 komórek: dwie strony
plecaka plus strona ekwipunku konia, do której silnik nie wkłada niczego,
dopóki postać jej nie odblokuje — bot nigdy tego nie robi. Każde liczenie
wolnych komórek w botach szło po 135, widziało 45 komórek‑duchów i skrzynia
„mieściła się” w plecaku, którego nie było; to samo przekłamanie siedziało
w regułach pełnego plecaka, nacisku na plecak i straganu. Boty liczą teraz
po `INVENTORY_DEFAULT_MAX_NUM` (90) — 84 miejsca w kodzie, jedna stała
`PLAYERBOT_BAG_CELLS`.

### Wyszukiwarka przedmiotów widzi stragany botów

„Wyszukiwarka pokazuje 0 sklepów, mimo że przedmioty na pewno są na
straganach” (sizowski). Wyszukiwarka z tych plików przeszukiwała tylko
sklepy offline (system ikarus); stragan bota to zwykły sklep prywatny, więc
plac z trzystoma straganami odpowiadał „Znaleziono 0 sklepów”. Ten sam
przełącznik kategorii pyta teraz także lady każdego bota z otwartym
straganem na tej mapie w zasięgu wyszukiwarki i oznacza je na mapie jak
sklepy offline (`ikarus_shop_manager.cpp`, plik w paczce).

### Panel klasyczny: nazwy, dane i rozmiary przedmiotów z tego świata

„Pomieszane nazwy angielskie/polskie, brak danych przedmiotu, miecz na dwa
sloty widoczny w jednym” (Tieru). Panel czytał nazwy i rozmiary z plików
linii 1.x (`items.json`, `item_names_pl.txt`) i tłumaczył resztę słowo po
słowie — stąd „Leather Buty”, „Azure Suit”, „Przedmiot #30347”. Na mt2009
panel czyta teraz `player.item_proto` tego świata (rdzeń db odświeża ją z
`item_names.txt` paczki przy każdym starcie): polskie nazwy, typ i rozmiar
w komórkach; siatka ekwipunku rysuje przedmiot na tyle komórek, ile ma.
Tabela ładuje się przy pierwszym użyciu i odświeża co godzinę.

### Panel klasyczny bez hasła na serwerze tylko lokalnym

„Nie wiem, gdzie mam hasło admina — może niech każdy będzie automatycznie
zalogowany, skoro to singleplayer” (Tieru). Panel ma od dawna tryb bez
hasła, ale włączał go tylko instalator linii 1.x; paczka 2.x nie ma
instalatora. Panel dostaje teraz adres, na którym go opublikowano
(`M2_HOST_BIND_ADDRESS`, w paczce 127.0.0.1): na adresie lokalnym nikt poza
tym komputerem go nie otworzy, więc nie pyta o hasło. Serwer za proxy
(nginx) też wiąże panel na 127.0.0.1 i jest publiczny — tam operator
ustawia `M2_PANEL_LOCAL_ONLY=0` w `.env` (nowy klucz, opisany w
`.env.example`); instalator 1.x z nginx nadal wymusza hasło sam.

### Teleport do bota z panelu klasycznego

„Nie działa teleportowanie do bota” (Tieru). Przycisk wybierał postać
gracza po najnowszym `last_play`, a ten zapis powstaje przy zapisie
postaci, minuty po zalogowaniu — wybierał więc postać, która grała
poprzednio, kolejkował teleport dla kogoś, kto nie jest w grze, odpowiadał
„timeout” i zostawiał wiersz w kolejce, żeby teleportować tamtą postać przy
jej następnym logowaniu. Odtworzone na stosie testowym: w grze Tieru, panel
kolejkował dla AdminSura. Panel pyta teraz wszystkie postacie graczy z
ostatniego tygodnia naraz, bierze pierwszą odpowiedź (tylko postać online
ją da) i wycofuje resztę. Sprawdzone: `WarpSet Tieru … target map 1`,
ponowne logowanie na rdzeniu docelowym w 3 sekundy, kolejka pusta.

### Paczka logów zbiera też linie skrzyń i walk

`PLAYERBOT_CHEST`, `PLAYERBOT_COMBAT` i `PLAYERBOT_STOCK` w filtrze
sysloga — zgłoszenie o skrzyni na ziemi nie miało w paczce ani jednej
linii o skrzyniach.

### Dwie tabele logów, których brakowało

„Unknown column 'hwid' in loginlog2” przy każdym logowaniu na świecie
założonym przed dodaniem tej kolumny (`CREATE TABLE IF NOT EXISTS` nigdy nie
dokłada kolumny) i „Table 'log.itemshop_dragon_scroll' doesn't exist” przy
zakupie w ItemShopie (quest paczki pisze do tabeli, której żaden zrzut nie
definiuje). Migrator dokłada kolumnę i tabelę przy każdym starcie;
sprawdzone dwukrotnym uruchomieniem na bazie testowej.

## 2.0.12 — 2026-09-12

Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Logowanie nie wisi przy dużej liczbie botów

„Po aktualizacji 2.0.11 ciągle wisi na ekranie logowania”, „po zmniejszeniu
botów do 1500 działa” (sizowski). Odtworzone na stosie testowym z 2482
botami: rdzeń db odpowiadał na logowanie po 14–28 sekundach, klient dawał
sobie spokój wcześniej, a w logu rdzenia kanału zostawało
`LoginSuccess - cannot find handle [admin]`. Powód: tabele gry są na tej
linii InnoDB, a MariaDB domyślnie czeka na fsync przy każdym zapisie — na
dysku Docker Desktop to około 70 zapisów na sekundę, a 2482 boty zapisują
około stu (flagi statystyk, flagi questów, przedmioty). Kolejka zapytań
rdzenia db rosła do ~1900, a SELECT logowania stał na jej końcu.
`innodb_flush_log_at_trx_commit = 2` w `99-metin2.cnf`: log InnoDB jest
zrzucany co sekundę zamiast przy każdym zapisie. Przy awarii zasilania
przepada najwyżej sekunda zapisów; dla świata jednego gracza to właściwa
proporcja. Ustawienie wchodzi przy restarcie kontenera bazy (launcher robi
to przy aktualizacji). Zmierzone po zmianie, ten sam świat i 2482 boty:
kolejka rdzenia db 0, odpowiedź na logowanie po sekundzie, logowanie z
klienta przechodzi do wyboru postaci. To samo stało za „teleport na GM-ie
wywala mnie i nie mogę się zalogować ponownie” (marcol_): teleport między
rdzeniami to ponowne logowanie kluczem, które czekało w tej samej kolejce.

### Boty na mt2009 wystawiają stragany

„2500 botów — 0 sklepów” (sizowski), „u mnie nie ma sklepów” (namiot_,
pasywnezarabianie, mlodszygie). Dwie przyczyny, obie po stronie tego silnika:

- Siatka prywatnego sklepu ma tu dziesięć kolumn (`SHOP_PLAYER_WIDTH`), a
  prawa połowa to sloty zablokowane albo premium. Boty układały linie na
  pięciu kolumnach jak na r40250 i każdą linię powyżej piątej wysyłały w
  zablokowaną połowę — silnik odrzucał cały stragan (w logu
  `PLAYERBOT_SHOP: refused`). Linia trafia teraz w ten sam wiersz i kolumnę
  siatki silnika.
- Ten silnik daje prawo do sklepu od 15 poziomu i 800 zabitych potworów
  (`CanOpenShop`). Reguła dla ludzi; bot po każdym restarcie świata zaczynał
  liczyć od nowa, więc przez wiele godzin żaden nie handlował. Bot jest z niej
  zwolniony (zmiana w `char_shop.cpp`, plik w paczce).

Zmierzone na stosie testowym z 2482 botami: przed zmianą 0 straganów w
godzinę, po zmianie 113 otwartych w pięć minut od startu (13 Yongan, 66
Joan, 34 Pyongmoo), dwie odmowy silnika na 116 prób.

### Księgi i medale bez czekania

„Księgi co 24 h” (namiot_), prośba operatora: bez limitu czasu na kolejną
Księgę Umiejętności i na kolejny medal konia. `SKILLBOOK_LEARN_DELAY` (21 h
w paczce mt2009) jest zerem — dla gracza i dla bota. Stajenny nie każe już
czekać 18 godzin na kolejny medal: `pony_levelup.quest` z paczki jedzie w
naszym katalogu questów z wyłączoną bramką `next_time` i jest kompilowany
przy budowie obrazu na miejsce oryginału.

### M2_PLAYERBOT_KINGDOMS=0 wyłącza Shinsoo i Jinno także po zasiewie

„Ustawiłem KINGDOMS=0, a boty i tak pojawiają się w Jinno i Shinsoo”
(adijhos). Przełącznik działał tylko na zasiew: świat, który raz ruszył z 1,
miał tożsamości obu królestw w bazie i każdy rdzeń je startował. Rdzeń czyta
teraz ten sam przełącznik ze środowiska usługi `game` (linia w logu
`PLAYERBOT: M2_PLAYERBOT_KINGDOMS=0 …`) i przy 0 nie daje Shinsoo ani Jinno
żadnego przydziału. Boty zostają w bazie; 1 uruchamia je z powrotem.

### Panel klasyczny sprawdza wersję swojej linii

„Sprawdź najnowszą wersję” mówiło 2.0.5, że jest najnowsza (archded,
l0st3k). Panel czytał `VERSION` z korzenia repozytorium, czyli wersję linii
1.x (1.33.3), i porównywał ją ze swoją 2.x. Panel mt2009 czyta
`linux-port-mt2009/VERSION`; panel 1.x dostaje dodatkowo zdanie, że istnieje
linia 2.x i że to osobna paczka z Discorda, nie aktualizacja.

### Paczka logów: naprawiony grep, logowanie i rdzeń auth

`game-supervise.txt` w 2.0.11 zawierał tylko błąd PowerShella (brak `grep`
w Windows). Filtr robi teraz PowerShell. Do paczki wchodzą też linie
logowania z każdego rdzenia kanału (`login-<rdzeń>.txt`), rdzenia auth
(`login-auth.txt`, `syserr-auth.txt`) i rdzenia db (`login-db.txt`) — bez
nich zgłoszenie „wisi na logowaniu” nie miało w paczce ani jednego wiersza.

### Bot w wiosce poluje na potwory swojego poziomu

„Biegają z 16 levelami po 11 h” (l0st3k), „boty biją na 9/10 lvlach nadal
psy”. Zmierzone na stosie testowym (350 botów, mnożnik expa 100%): jedna
trzecia walk w pierwszych wioskach toczyła się z potworem o sześć i więcej
poziomów niższym od bota, poziom w okolicach 8–9 zajmował 40 minut, a 13–15
około dwóch godzin. Winne było pasmo hubu: bot brał każdy hub, którego
potwory są do siedmiu poziomów niżej od niego, więc bot na 9 poziomie szedł
według pid równie chętnie do psów (Dziki Pies, 15 expa) co do wilków swojego
poziomu (Nieb. Alfa Wilk, 111 expa). Tabela kar za różnicę poziomów w tym
silniku tego nie ogranicza — sześć poziomów niżej to wciąż 90% — niska jest
sama baza. Hub jest teraz brany od dwóch poziomów nad botem do trzech pod
nim, a gdy w wiosce nie ma hubu w tym paśmie, bot bierze huby najbliższego
pasma zamiast dowolnego (bot na 16 poziomie w Yongan szedł dotąd gdziekolwiek,
także do tygrysów na 25, których nie pokona, i do psów). Obozy grup wybierane
są tą samą regułą.

Samo pasmo podwoiło awanse i nie ruszyło nikogo z miejsca: zasięg szukania celu
to 6000 jednostek, tyle co komórka hubu, więc bot stojący przy wilkach swojego
poziomu dalej widział psy sześć kilometrów dalej, a wędrówka do hubu — która
dostaje tick tylko wtedy, gdy nie ma czego bić — nigdy go nie dostawała: 96 ze
115 botów w Joan stało dalej niż 2500 jednostek od jakiegokolwiek hubu. Druga
połowa zmiany: w pierwszej wiosce potwór o sześć i więcej poziomów niższy od
bota i dalej niż 800 jednostek nie jest celem („outgrown_prey” w logu), więc
bot idzie do swojego hubu, a po drodze bije to, co ma pod nogami. Obrona,
zadanie, materiał i polowanie na broń mają pierwszeństwo, jak dotąd.

Zmierzone na tym samym świecie w oknach po 10 minut, awanse na królestwo
(117 botów): Shinsoo 30 → 47, Chunjo 5 → 38, Jinno 37 → 57 — przy rosnących
poziomach, więc każdy kolejny awans kosztuje więcej expa. Walki z potworem
o sześć i więcej poziomów niżej: z 36–40% do 9–18% (reszta to obrona i to,
co stało w zasięgu 800). Tick, liczba szukań celu i resety watchdoga bez
zmian; odmów „outgrown_prey” 5–40 na minutę na rdzeń.

## 2.0.11 — 2026-09-12

Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Boty Shinsoo i Jinno nie stoją już na 5 poziomie

„W królestwie czerwonym i niebieskim boty na 5 lv się bugują”, „stoją przy
kowalu i handlarzach”, „2500 botów — 0 sklepów” (greess, martynka19cm,
mrgixon, sizowski). Od 2.0.8 Yongan i Pyongmoo idą do NPC „wprost”, jak
Bokjung — ale lista faz „wprost” była listą Bokjung, gdzie nie ma trenera ani
Starszej Pani. Bot na 5 poziomie potrzebuje trenera (wybór grupy
umiejętności), zaczynał więc wizytę z pustą listą, kończył ją w tym samym
ticku i zaczynał od nowa w następnym: stał na placu z celem „wybór profesji”,
resetowany przez watchdoga co 90 sekund, i nigdy nie wyszedł poza 5 poziom.
W paczce logów sizowskiego: 500 takich botów na rdzeń. Lista „wprost” ma
teraz trenera i Starszą Panią na początku, jak lista Joan, a wizyta, której
lista nie ma czym obsłużyć, w ogóle się nie zaczyna (z linią w logu). Bokjung
tego nie dotyczy — w drugiej wiosce potrzeba trenera nigdy nie jest ustawiana.

### Jedna Księga Umiejętności z kamienia Metin, nie trzy

„Graczowi lvl 46 lecą 3 KU ze wszystkich metinów w M1” (cyfrowy_mat). Od
1.29 każdy kamień dawał trzy księgi, obojętnie od poziomu kamienia. Teraz
kamień dopełnia do jednej: jeśli tabela dropu nic nie wylosowała, jedna
księga i tak wypada, jeśli wylosowała, zostaje to, co wylosowała. Dotyczy obu
silników (łatka 0006 i port mt2009).

### Bot przemianowany ręcznie zachowuje nazwę

„Dałem botowi ADAM miecz +9, rano nie było już bota o tym nicku” (gregoszky):
2.0.10 przemianowało wszystkie boty na nową listę, także te, którym operator
sam zmienił nazwę w bazie. Nazwa, która nie jest ani z puli, ani z zasiewu,
jest czyimś wyborem: taki bot nie jest już przemianowywany (przez żadną
kolejną wersję listy), a jego nazwa nie trafia do nikogo innego. Migrator
liczy je osobno („N bot(s) renamed by hand keep their names”).

### Paczka logów zbiera wszystkie trzy rdzenie i ślady padów

ZBIERZ / WYŚLIJ LOGI zbierało syslog i status tylko z rdzenia Chunjo
(`game1`); zgłoszenie o botach Shinsoo i Jinno nie miało ani jednej linii z
rdzeni, na których stały. Teraz paczka ma osobno syslog, syserr, status i
pliki `crash-*.txt` (ślad stosu po padzie, od 2.0.8) dla `first`, `game1` i
`game2`, syserr rdzenia bazy oraz osobny, dłuższy log kontenera gry — wspólne
800 linii logów compose mieściło 50 sekund, bo zalewały je resety watchdoga i
komunikaty MariaDB o zerwanych połączeniach, a linia „CORE DIED” ze śladem
stosu wypadała z okna, zanim paczka powstała.

## 2.0.10 — 2026-09-12

Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Bonusy przedmiotów w panelach mają nazwy, nie numery

„Zamiast nazwy bonusu jest numer #139” (djariczek): silnik mt2009 ma 31
linii bonusów, których stary silnik nie znał — od 138 do 168 w `length.h`
(regeneracja wytrzymałości, czas trwania umiejętności, silny przeciw
Metinom/bossom, pochłanianie obrażeń, przełamania odporności…) — i nie mają
one numeru APPLY, przez który oba panele nazywają linie. Panel klasyczny i
panel Sebana dostały etykiety dla wszystkich 31 (po polsku i po angielsku,
z właściwą jednostką); 139 to „Regeneracja wytrzymałości”, 147 „Czas
trwania umiejętności”. Sprawdzone: tabela etykiet parsuje się (118 wpisów),
oba panele kompilują się.

### Nowa lista nicków Iwakury, po królestwach, bez duplikatów

Iwakura dopisała listę do 1500 nicków (po 500 na królestwo, w tym nicki
wspierających; „te generowane przez AI są okropne”, więc wszystko ręcznie)
i podała zasadę: nicki brane z listy w losowej kolejności, po równo na
królestwo, a dopiero gdy królestwo ma więcej botów niż nicków, do jego
nicków dopisywane „2”, „v2”, „3” lub „v3”. Do tej pory pula szła po kolei od
Chunjo, które brało pierwszy tysiąc nazw, a Shinsoo i Jinno dostawały kopie
z v2/v3. Teraz lista (1475 poprawnych nazw; odrzucone: same cyfry, „GM…”,
dwa wulgarne) jest tasowana raz, dzielona na trzy równe udziały po 491, i
tylko Chunjo — 1500 zasianych postaci — dostaje dalej swoje nazwy z „2”/„v2”,
potem „3”/„v3”. Każdy bot zostanie przemianowany przy pierwszym starcie po
aktualizacji (nowa wersja puli); `M2_PLAYERBOT_HUMAN_NAMES=0` zostawia nazwy,
`restore` przywraca zasiane.

Przy okazji naprawiony błąd, który dotyczy każdego świata po 2.0.8:
**dosiane boty Shinsoo i Jinno dostały te same nicki co boty Chunjo**. SQL
numerował czekające boty od jedynki i dawał im nazwy od początku listy, nie
patrząc, czy inny bot już je nosi — na świecie testowym 999 nazw było
zdublowanych (np. 000Achtung000 na dwóch postaciach). Nazwa noszona przez
bota, który nie czeka na nową, nie jest już wolna. Sprawdzone na tym
świecie: 2499 botów przemianowanych, zero duplikatów, postać gracza na koncie
admin nietknięta, drugi start nic nie zmienia, trzy boty pozbawione nicku
dostają wolne nazwy bez kolizji.

## 2.0.9 — 2026-09-12

Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Panel Sebana: zakładanie kont znów działa na 2.x

„Nie utworzono konta: Unknown column 'empire' in 'INSERT INTO'” na każdym
z trzech królestw (NieBijOddam). Tabela kont w plikach mt2009 nie ma kolumny
`empire` (królestwo konta trzyma `player_index`, a pierwsza postać gracza
dostaje je od gry), a formularz wstawiał ją zawsze. Na 2.x konto powstaje
bez tej kolumny; postać GM zakładana z panelu dostaje królestwo w
`player_index` jak dotąd. Do tego login ma na mt2009 najwyżej 16 znaków
(tyle mieści kolumna) — formularz mówi to od razu zamiast błędu „Data too
long” z bazy.

### Suwak „Odpoczynek w mieście”, a poniżej 18 poziomu nikt nie odpoczywa

W obu panelach (Zachowanie botów) jest nowy suwak `REST`, 0–100%, domyślnie
100: udział botów, które po załatwieniu spraw w pierwszej wiosce zostają na
rynku około trzech minut i spacerują między straganami. Kto ustawi 0, ma boty
cały czas na expie — do miasta przychodzą tylko w sprawach (mikstury, kowal,
handlarz, stragan) i od razu wracają. Suwak działa na żywo: bot, który już
odpoczywa, kończy odpoczynek przy najbliższym ticku po zmianie na 0.
Niezależnie od suwaka dwie nowe reguły: **bot poniżej 18 poziomu nie
odpoczywa nigdy** (ma poziomy do zdobycia i nic do oglądania), a **bez
wystawionego straganu na mapie nikt nie „ogląda straganów”** — do tej pory
bot spacerował między pustymi stanowiskami pod napisem „Odpoczywam w
mieście”, co na młodym świecie wyglądało jak bezczynność (`MayPlayerBotRestInTown`
w `playerbot_config.h` jest całą regułą; licznik straganów pochodzi z księgi
rynku, odświeżanej co minutę). Sprawdzone na stosie testowym po przebudowie:
przy 353 botach poniżej 18 poziomu żaden nie odpoczywa, a rdzeń przy zmianie
suwaka pisze `PLAYERBOT_CONFIG: town rest N%`.

### Cztery postacie GM także na koncie, na którym już ktoś gra

„Na moim koncie admin nie ma postaci GM, tylko moja Tieru” — skrypt z 2.0.4
tworzył Admin, AdminNinja, AdminSura i AdminSzaman tylko wtedy, gdy konto
`admin` nie miało **żadnej** postaci, więc kto założył sobie postać wcześniej,
nie dostawał ich nigdy. Teraz skrypt dosiewa brakujące klasy do wolnych
miejsc (konto ma cztery), pomija klasę, którą ktoś na koncie już gra, i nie
rusza tego, co na koncie jest; ekran wyboru postaci pokazuje stare postacie
na swoich miejscach, a nowe za nimi. Nowe postacie stoją w pierwszej wiosce
swojego królestwa (Joan, Yongan albo Pyongmoo), bo konto ma jedno królestwo.
Sprawdzone na świecie testowym z jedną szamanką na koncie: powstały Admin,
AdminNinja i AdminSura, drugi start nic już nie zmienia. Dzieje się przy
najbliższym starcie serwera po aktualizacji.

### Launcher: trzy wiersze wersji na dole

Stopka launchera pokazuje osobno serwer, launcher i klienta — zainstalowaną
i najnowszą wersję każdego z nich (launcher jest częścią paczki serwera, więc
jego „najnowsza” to wersja serwera; po aktualizacji w tej samej sesji stopka
mówi, że na dysku jest nowsza i trzeba uruchomić launcher ponownie). Do tego
zabezpieczenie: gdy launcher nie wystartuje albo któryś przycisk wyrzuci
wyjątek, treść błędu trafia do `launcher-logs` i do okna z komunikatem — po
restarcie z 2.0.8 jeden z graczy zobaczył okno błędu, którego log nie
zawierał, bo urywał się na „Uruchamiam launcher ponownie”. Odtworzenie tej
ścieżki (prawdziwa aktualizacja serwera → Tak → restart) przeszło bez błędu;
następny raport będzie miał treść.

### Sprawdzanie wersji bez pięciominutowego opóźnienia

Launcher czyta manifest aktualizacji najpierw przez API GitHuba (świeże w
minutę), a dopiero potem z raw.githubusercontent.com, którego CDN trzyma
stary plik przez pięć minut — stąd „Masz już najnowszą wersję (2.0.7)” w
pięć minut po wydaniu 2.0.8.

## 2.0.8 — 2026-09-11

### Boty Shinsoo i Jinno wreszcie chodzą do kowala i handlarki różności

„Tylko boty z Chunjo ulepszają ekwipunek, do kowala nie podbiega żaden z
innych królestw” (nerrvous_s, potwierdzone na 2.0.6). Odtworzone na stosie
testowym z trzema królestwami: w osiem minut rdzeń Chunjo miał 131 wizyt u
kowala i 3918 ulepszeń, rdzenie Shinsoo i Jinno zero — przy wizytach u
handlarzy broni i zbroi u wszystkich. Przyczyna: wizyta w pierwszej wiosce
ma osobną nogę „brama” do wnętrza Joan (handlarka różności i kowal stoją za
murem), a jej współrzędne są Joan (60300, 169400) — na mapach 1 i 41 to
nigdzie, więc noga kończyła się „unreachable” i faz wnętrza nigdy nie było.
Zmierzone na `server_attr` mt2009: w Yongan i Pyongmoo kowal i handlarka
różności stoją w tym samym spójnym obszarze co handlarz broni, bez muru,
więc te wioski idą wprost do każdego NPC, jak druga wioska
(`IsPlayerBotGatedVillage` — brama zostaje tylko dla Joan). Zmierzone po poprawce na tym samym stosie, dziewięć minut od startu:
Shinsoo 308 wizyt u kowala i 4792 ulepszenia, Jinno 329 i 5475, Chunjo 134
i 3920 — a handlarka różności odpowiednio 297, 309 i 169 wizyt.

### Trzy królestwa domyślnie u każdego, boty dzielone po równo

Do 2.0.7 `M2_PLAYERBOT_KINGDOMS=0` był domyślny, więc każdy świat 2.x miał
boty tylko w Chunjo (paczka logów procedera: `shinsoo=0 chunjo=1500
jinno=0`). Teraz domyślnie 1: migrator dosiewa kohorty Shinsoo i Jinno (po
500, raz, także na istniejącym świecie — chwilę dłuższy start), a każdy
rdzeń uruchamia swoje królestwo; liczba botów z suwaka dzieli się po równo
(zmierzone: 970 → 324/323/323). Plik `.env` gracza jest pisany raz i nigdy
nadpisywany, więc launcher przełącza stare `0` na `1` dokładnie raz i
zapisuje to w `M2_PLAYERBOT_KINGDOMS_DEFAULTED`; kto potem ustawi 0, zostaje
przy 0. „Żółci mają przewagę” (sosen94) bierze się z liczby powyżej 1500:
Shinsoo i Jinno mają po 500 postaci, reszta idzie do Chunjo — do 1500 botów
podział jest równy. Ściana poziomów Shinsoo/Jinno (36 lvl) bez zmian.

### Padający rdzeń zapisuje własny backtrace

„Wywala co 2 minuty” (proceder): rdzeń `ch1-game1` padał z sygnałem 11
83–86 s po każdym starcie, a w paczce logów było tylko „Segmentation fault
(core dumped)” — Docker Desktop kieruje zrzuty pamięci do WSL
(`/wsl-capture-crash`), a limit rdzenia w kontenerze to 0, więc nie ma
czego oglądać. Od teraz `libthecore` przechwytuje SIGSEGV/SIGBUS/SIGFPE/
SIGILL/SIGABRT, zapisuje ślad stosu (`backtrace()`) do `crash.txt` w katalogu
rdzenia i na stderr, po czym oddaje sygnał domyślnej obsłudze; rdzenie są
linkowane z `-rdynamic`, więc ramki niosą nazwy funkcji (zmanglowane —
`c++filt`). `m2-supervise` po „CORE DIED” drukuje ślad do logu kontenera
(trafia do paczki logów) i odkłada go jako `crash-<data>.txt` obok syserr.
Przyczyna padu u procedera nie jest jeszcze znana — następna paczka logów ją
pokaże.

### Launcher: „The property 'Count' cannot be found on this object”

Start, URUCHOM DOCKER i paczka logów kończyły się tym błędem u co najmniej
dwóch graczy (sykesal420). Wszystkie trzy uruchamiają sprawdzenie Dockera,
które pyta Windows o zarezerwowane zakresy portów; funkcja zwracająca
dokładnie jeden zakres (albo żadnego) oddaje pojedynczy obiekt (albo nic)
zamiast tablicy, a moduł działa w trybie strict, w którym `.Count` na takim
obiekcie to ten właśnie błąd. Wynik jest teraz zawsze tablicą. Osobna sprawa
u drugiego gracza — „The Compose app is no longer running” — to uszkodzony
Docker Desktop, nie launcher.

### Dane do Navicat i inne drobiazgi

Bez zmian w danych; patrz 2.0.7.

---

## 2.0.7 — 2026-09-11

### Risk mode naprawdę znika (2.0.6 tylko usunęło plik)

Sizowski po 2.0.6: „risk mode nadal jest”. Aktualizacja nigdy nie kasuje
plików, więc każde drzewo z 2.0.0–2.0.5 wciąż ma `quest/high_risk.quest`, a
pętla kompilacji w obrazie gry nadal miała `high_risk` na liście — 2.0.6
zdjęło plik z repozytorium i nic więcej, więc u graczy quest kompilował się
dalej. Bramką jest lista w Dockerfile, nie katalog: `high_risk` zniknęło z
listy, a plik zostawiony w drzewie gracza jest ignorowany. Po tej aktualizacji
nowe konto nie dostaje już wyboru High Risk / No Risk.

### Launcher sam pyta o aktualizację przy starcie

Po otwarciu okna launcher czyta kanał aktualizacji (jak dotąd, raz na sesję)
i gdy serwer w kanale jest nowszy niż zainstalowany, pyta od razu: „Znaleziono
nowszą wersję serwera X — czy chcesz dokonać aktualizacji teraz? Tak / Nie”.
TAK uruchamia tę samą aktualizację, co przycisk AKTUALIZUJ; NIE odkłada
pytanie do następnej wersji (zapamiętane w `.m2launcher-offers.json`), a
przycisk działa zawsze. To samo dla klienta na linii 2.x: po aktualizacji
serwera (albo od razu, gdy serwer jest aktualny) pyta o nowszą wersję
klienta i podmienia packi przyciskiem AKTUALIZUJ KLIENTA. Świeża instalacja z
pełnej paczki wie, jaki klient dostała: plik `CLIENT_VERSION` obok `VERSION`
(dotąd launcher mówił „nieznana” i pytałby o klienta, który już jest);
instalacje z 2.0.0–2.0.6 nie mają tego pliku, więc pytanie o klienta 2.0.3
pojawi się u nich raz — TAK jest nieszkodliwe (podmienia te same packi),
NIE zapamiętuje.

### Dane do Navicat sprawdzone i uzupełnione

Sprawdzone na plikach 2.x: host 127.0.0.1, port z `M2_DB_PUBLISH_PORT`
(domyślnie 3306), konto root z `M2_DB_ROOT_PASSWORD`, konto gry (`M2_DB_USER`,
domyślnie `metin2`) z `M2_DB_PASSWORD` — wszystko czytane z `.env` tej
instalacji, więc zgadza się z tym, na czym stoi baza. Dopisana uwaga, której
brakowało osobom edytującym bazę ręcznie: na 2.x przedmioty i potwory
(`item_proto`, `mob_proto`) są w bazie `world`, a `player.item_proto` i
`player.mob_proto` to tylko widoki; zmiany w `world` zostają po restarcie
(inaczej niż na 1.33, gdzie tabele były nadpisywane z plików txt).

### Suwak „Stragany” ma jawną umowę i dosięga stojących straganów (audyt D11)

„Minimalny suwak, a 180 z 280 botów handluje”: stragan, który już stał, nigdy
nie był pytany ponownie, a cztery wyjątki od suwaka nie były nigdzie
opisane. Teraz stragan pamięta powód otwarcia — Handlarz, brak yang na
mikstury, pełny plecak, dropper pod presją plecaka (te cztery suwak omija,
bo lada to jedyny sposób opróżnienia plecaka), nadmiar ksiąg, los droppera,
„jeden na dziesięciu” (te trzy suwak rusza). Status bota mówi „Prowadze
stragan (los)” zamiast samego „Prowadze stragan”, log otwarcia niesie powód,
a co dziesięć minut rdzeń pisze spis `PLAYERBOT_SHOP: census` z liczbą
straganów według powodu i obowiązującą wagą. Po zmianie suwaka każdy
stojący stragan z losowanego powodu jest sądzony ponownie pod nową wagą
(los jest po PID, więc odpowiedź jest ta sama, jaką dostałby nowy stragan)
i ten, który przegrał, zwija się w ciągu pięciu minut, rozłożonych po PID,
zamiast wszystkie w jednej sekundzie. Opis suwaka w obu panelach mówi to
samo, co kod.

### Martwy zapas ma koniec: magazyn, nie handlarz (audyt D14)

„Szaman trzyma stal wojownika +9, sura przedmioty innych klas”: ekwipunek
powyżej +4, którego handlarz nigdy nie bierze, po czterech stoiskach bez
kupca miał już pełny rabat i żadnej dalszej drogi — jechał w plecaku po
kamieniach do końca życia bota. Teraz każdy wiersz lady ma zapisany czas
pierwszego wystawienia (`mapStockFirstListed`), a przedmiot niesprzedany
przez osiem stoisk (`PLAYERBOT_SHOP_UNSOLD_SAFEBOX_STANDS`) idzie pod
presją plecaka do magazynu razem z nadwyżką ksiąg — zachowany, nigdy
złomowany, poza plecakiem; log `PLAYERBOT_STOCK: to safebox` mówi ile
stoisk i minut za sobą miał. Przedmiot, który bot powinien nosić, nigdy nie
trafia do magazynu. Linia otwarcia straganu mówi też, co się nie zmieściło
i dlaczego (`left_behind no_line= no_slot= antiflag=`), czyli rejestr
powodów niewystawienia z audytu. Skompilowane na obu silnikach; na
serwerach testowych z młodymi botami (poziom 2–4, brak straganów) nie
zaobserwowane w ruchu.

### Masowe nadawanie nie zatrzymuje się na botach offline (audyt D02)

Zmierzone na 1500 zarejestrowanych botach, z których 349 było w świecie:
paczka dla wszystkich doszła do 350 nadanych w dwie minuty i stanęła na
`queued=10` na stałe. Dziesięć miejsc kolejki gry (`MAX_PENDING`) zajmowały
postacie offline — każda czeka 30 s na sweep questa, 60 s na wycofanie przez
workera i wraca po dwóch minutach — więc dziesięć nieobecnych nazwisk
blokowało każdego obecnego za nimi. To „zatrzymanie po 333” z audytu: nie
stan końcowy, tylko kolejka z głową offline. Worker czyta pięciominutową
migawkę kolektora (kto jest w świecie), obecnych wysyła pierwszych, a sondy
dla nieobecnych zajmują najwyżej cztery z dziesięciu miejsc, po dwie na tick.
Zmierzone po zmianie: 40 obecnych botów nadanych w 15 s przy 1146
nieobecnych w ogonie, `pending` w kolejce gry nie przekracza czterech.

Strona nadawania pokazuje stan workera: bicie serca co tick (kontener
`seban-item-grants` stoi → wprost, z poleceniem uruchomienia), ostatni błąd,
liczby i wiek najstarszego zlecenia w każdym stanie, oraz ostrzeżenie, gdy
zlecenie w kolejce gry leży ponad 45 s bez odbioru (pomocnik w grze budzi się
przy pierwszym logowaniu po starcie).

---

## 2.0.6 — 2026-09-11

### Panel klasyczny: przedmioty, teleport, szybkość, poziom znów działają na 2.x

Każde polecenie z panelu klasycznego (nadanie przedmiotu, yang, poziom,
teleport, szybkość biegu) kończyło się na 2.0.x komunikatem „Nic w grze nie
odpowiedziało” (czerwcuu, u4nt). Quest `web_admin` czyta kolejkę panelu przez
`mysql_direct_query()`, a ta funkcja nie jest jedna na obu silnikach: na
r40250 (nasza łatka) zwraca wiersze jako tabelę, na mt2009 zwraca NAJPIERW
liczbę zmienionych wierszy, a wiersze jako drugą wartość. Quest brał pierwszą
wartość za tabelę i nigdy nie widział polecenia. Wspólna owijka bierze tę z
dwóch wartości, która jest tabelą. To samo naprawia masowe nadawanie z panelu
zaawansowanego, bo idzie tą samą kolejką.

### Mnożniki EXP, dropu i yang naprawdę działają na 2.x

Strona mnożników obu paneli mówiła na zielono „Zapisano! Serwer właśnie się
restartuje”, a na serwerze nic się nie zmieniało (wątek z 11 września: „panel
www niby na zielono informuje o zmianie różnych parametrów, a one się nie
zmieniają”). Na r40250 mnożnik to przepisanie `mob_proto.txt` i tabel dropu
przez `m2-rates` w kontenerze gry — obraz mt2009 nie miał tego programu, więc
zlecenie panelu leżało w kolejce i nikt go nie czytał. Silnik mt2009 ma
mnożniki własne: flagi zdarzeń `mob_exp`, `mob_item`, `mob_gold` (i bliźniacze
`_buyer` dla kont premium), przez które `CHARACTER_MANAGER` mnoży
doświadczenie, szansę dropu i ilość yang. Flaga to wiersz `player.quest` z
`dwPID = 0`, wczytywany przez rdzeń bazy przy starcie i rozsyłany do rdzeni
gry. Panel klasyczny zapisuje sześć wierszy, a potem prosi pomocnika w grze
(`web_admin`, polecenie `RATES` na timerze serwera, `game.set_event_flag`) o
ustawienie ich na żywo — zmierzone 2–3 s, bez restartu, we wszystkich trzech
rdzeniach naraz. Gdy nikt nie jest zalogowany i pomocnik nie odpowie, panel
zleca restart jak dotąd, a obraz mt2009 dostał własny `m2-rates`, który nic
nie przepisuje, tylko restartuje rdzenie i raportuje wynik (zmierzone 35 s od
zlecenia do „wszystkie rdzenie działają”, flagi wczytane z bazy). Panel
zaawansowany zapisuje te same wiersze i idzie ścieżką restartu; oba panele
pokazują te same liczby. Wartości 100% oznaczają grę bez zmian.

### Nadanie rangi GM na 2.x mówi prawdę

Silnik mt2009 nie ma gniazda administracyjnego, więc `m2-gm` (przeładowanie
listy GM na żywo) nie istnieje w tym obrazie, a panel i tak pisał „Działa od
razu, w grze”. Listę odczytuje na nowo `/reload a` — polecenie, które pomocnik
w grze może wykonać tylko jako zalogowany IMPLEMENTOR. Panel próbuje tego
przez kolejkę (`GM_RELOAD`), a gdy żaden IMPLEMENTOR nie jest w grze, mówi:
uprawnienia wczytają się przy najbliższym restarcie albo po `/reload a`
wpisanym przez zalogowanego GM.

### Tryb ryzyka (Risk mode) zdjęty z linii 2.x

Quest `high_risk` z plików 1.33 (wybór „High Risk / No Risk” przy logowaniu)
przyszedł do obrazu mt2009 razem z resztą i nie powinien tu być. Nie jest już
kompilowany; kto wybrał tryb wcześniej, ma go zwyczajnie wyłączonego.

### Zamiar wyjazdu gaśnie po dotarciu (audyt D12)

`lDepartureMap` — „ten bot ma wyjechać na mapę X, gdy skończy sprawunki” —
był ustawiany raz i nigdy zerowany. Bot raz wstrzymany w Bokjung nosił go do
końca życia: po powrocie do miasta po zapasy odmawiał każdego polowania na
materiał i każdej wyprawy do Joan, a nad głową miał cel wyjazdu, na który
już dawno dotarł. Zamiar gaśnie po przejściu na docelową mapę (albo na
dowolne pogranicze, gdy pasmo poziomu przesunęło cel w międzyczasie), a
wstrzymany dłużej niż dziesięć minut jest raportowany raz na dziesięć minut
(`PLAYERBOT_DEPARTURE: overdue`) z tym, co go trzyma: broń, zbroja,
mikstury, strzały, miejsce w plecaku, wizyta w mieście, złoto.

### Skrzynia otwiera się tylko wtedy, gdy zmieści się cała paczka (audyt D01)

Silnik wydaje nagrody ze skrzyni po jednej przez `AutoGiveItem`, a to, co się
nie mieści, kładzie na ziemi i zgłasza sukces. Bot pytał przed skrzynią o
pięć wolnych kratek i jedno miejsce na trzy pola — dla paczki z sześciu
przedmiotów to za mało („boty mając pełne EQ otwierają skrzynie ucznia i
wszystko wylatuje na glebę”). Teraz przed każdą skrzynią — ucznia, Moonlight,
skrzynką bossa i skrzynią na klucz — bot układa całą paczkę grupy na kopii
swojej siatki tak, jak robi to silnik: przedmiot potrzebuje swojej wysokości
w jednej kolumnie jednej strony, stos dokłada się do stosu tego samego vnumu,
każda nagroda zajmuje miejsce przed sprawdzeniem następnej. Dla grupy typu
Pct (skrzynie ucznia) liczą się wszystkie linie naraz, dla pozostałych jedna,
największa. Gdy się nie mieści, skrzynia czeka (raz na minutę
`PLAYERBOT_GEAR: chest waits for room`), a plecak opróżnia wizyta w mieście.
Na mt2009 typ grupy odsłania jednolinijkowy getter dodawany przez
`playerbotify.py`; na r40250 liczone są wszystkie linie.

### Launcher mówi, ile trwała każda faza

Skarga „aktualizacja i start trwają bardzo długo” nie miała do tej pory
liczby, którą dałoby się sprawdzić: log launchera znał tylko początek i koniec
akcji. Launcher pisze teraz linie `[faza] … (+N s od początku akcji)` po
sprawdzeniu Dockera, po przygotowaniu kontekstu budowania, przy starcie i
końcu `docker compose up --build`, po pobraniu pakietu (rozmiar i czas) i po
podmianie plików; `start-server.ps1` podaje czas samego `docker compose up`,
czyli od bazy przez migrator do zdrowej gry. Okno launchera pokazuje bieżącą
fazę w pasku stanu. Zmierzone na maszynie deweloperskiej dla 2.0.5: start
zatrzymanego serwera 52 s, aktualizacja z zbudowanymi obrazami około minuty,
pełna budowa obrazu gry od zera (bez cache kompilatora) 5 min 9 s, z czego
2 min to pakiety Ubuntu i biblioteki zewnętrzne, 94 s rdzeń gry, 31 s apt
obrazu docelowego. Na czterordzeniowym laptopie należy się spodziewać trzech,
czterech razy tyle; to czas pierwszego uruchomienia, aktualizacja kompiluje
tylko zmienione pliki botów przez ccache.

---

## 2.0.5 — 2026-09-11

### Postacie GM w zestawie, który klient umie pokazać

Zbroja 90 poziomu i broń 87 poziomu z 2.0.4 istnieją w `item_proto` serwera,
ale nie w kliencie: jego `pc2/*.msm` znają kształty zbroi 0–12, 14–22 i 24
(Pancerz Diabelskiego Rogu to 13, Zbroja z Niebieskiej Stali to 26), a
pakiet `item` ma modele broni tylko do zestawu 75 poziomu. Postać w takiej
zbroi była niewidzialna i nie mogła się ruszać (Iwakura). Czwórka GM nosi
teraz zbroję 66 poziomu +9 swojej klasy (Zbroja z Czarnej Stali, Ubranie
Czarnego Wiatru, Zbroja Płytowa Czarnej Magii, Czarna Szata) i broń 75
poziomu +9 (Zatruty Miecz, Skrzydła Demona Chakram, Lwi Miecz, Bambusowy
Dzwon; w plecaku Miecz Żalu, Stalowy Łuk Kruka, Wachlarz Ośmiu Trigramów),
a do tego Olejek Wygnania do zmiany królestwa. Świat, który dostał czwórkę w
2.0.4, ma podmieniane te same sloty przy najbliższym starcie — bonusy
zostają, zmienia się tylko vnum.

### Panel: ikony przedmiotów u każdego, historia ekwipunku działa

Panel klasyczny pokazywał u każdego gracza przekreślony obrazek zamiast
ikony przedmiotu: 1572 ikony generował na 1.33 instalator na maszynie
operatora i nigdy nie były w repozytorium ani w paczce, a linia 2.x nie
generowała ich nigdzie. Ikony są teraz robione z pakietu `icon` klienta
mt2009 (`port/iconify.py`: 1557 ikon per-item z klienta plus 253 ze starego
zestawu dla przedmiotów, których klient trzyma tylko w atlasach — mikstury
startowe, księga umiejętności, skrzynie ucznia) i jadą w `files/static/icons`
(8,6 MB w każdej aktualizacji serwera). Przedmiot bez ikony (741 z 6001
vnumów świata, prawie żaden w obiegu) dostaje szare pole zamiast
przekreślonego obrazka.

„Historia ekwipunku” pokazywała `startswith first arg must be bytes…`: na
mt2009 kolumny `how`, `hint` i `type` w `log.log` są `varbinary` i przychodzą
jako bajty. Oba panele dekodują je teraz (CP1250) przed użyciem.

### Pełny plecak: bot nie udaje, że podnosi, i robi miejsce

Bot z zerem wolnych kratek podchodził do każdego dropu, pokazywał „Podnosze
lup”, dostawał odmowę od silnika i próbował następnego — a między tym
polował dalej („bot dropi, itemki pod nim leżą, mówi że podnosi łup, ale nie
robi nic, bo nie ma miejsca” — JaroszV2). Zbieracz łupu pomija teraz
przedmioty, które nie zmieszczą się w plecaku (zostaje tylko to, co dołoży
się do istniejącego stosu), a raz na minutę pisze do logu
`PLAYERBOT_LOOT: bag full pid= name= drops_in_reach= can_open_shop=`.

Handlarz może dostać ekwipunek tylko do +4 — także z reguły „niesprzedane
przez sześć straganów” (dotąd do +6). +5 i wyżej nigdy nie idzie do NPC: to
towar na stragan, a co bot nosi sam, kowal podnosi dalej. Gdy plecak jest
pod presją (8 wolnych kratek lub mniej) i bot nie może otworzyć straganu (na
mt2009 przed 15 poziomem i 800 zabiciami), ekwipunek do +4, którego sam by
nie założył, i nadwyżka materiałów idą do handlarza — wcześniej „towar na
ladę” bez lady był plecakiem na zawsze.

---

## 2.0.4 — 2026-09-11

Czwarta poprawka pierwszego dnia: cztery wyposażone postacie GM i skrzynia
startowa dla gracza. Tylko serwer (ZAINSTALUJ AKTUALIZACJE); klient bez zmian.

### Cztery postacie GM z pełnym wyposażeniem

Zamiast jednej postaci Admin konto `admin` ma cztery, po jednej na klasę:
**Admin** (wojownik), **AdminNinja**, **AdminSura** i **AdminSzaman**, każda
90 poziomu z uprawnieniami IMPLEMENTOR. Każda nosi najlepszy zestaw +9, jaki
ma ta paczka dla jej klasy (broń 87 poziomu, zbroja 90, hełm 80, Tarcza
Tytanów, granatowa biżuteria, buty 65) z mocnymi bonusami — w tym linią
średnich obrażeń 45% i obrażeń umiejętności 20% na broni — a w plecaku drugą
broń (dwuręczna, łuk ze strzałami, wachlarz), po 200 mikstur XL, zwoje
błogosławieństwa, Boga Smoków i teleportu, medale konne, 500 milionów yang,
konia 21 poziomu i Księgę Wojskowego Konia do jego przywołania. Postacie
powstają na świeżym świecie, a na istniejącym przy najbliższym starcie, o ile
konto `admin` nie ma jeszcze żadnej postaci; konto, na którym ktoś już gra,
zostaje jak było (jego pierwsza postać dostała GM w 2.0.2). PID-y 9001–9004,
poza zakresem seeda botów.

### Nowa postać gracza dostaje Skrzynię Ucznia

Boty zaczynają ze Skrzynią Ucznia I w plecaku, gracz zaczynał z niczym
(„gracz jest gorszy niż bot” — sizowski). Quest `starter_chest` daje ją przy
pierwszym wejściu do gry postaci do 5 poziomu, według klasy (wojownik i sura
50187, ninja 50212, szaman 50213) — dalsze skrzynie łańcucha otwierają się jak
u botów, od 10 poziomu. Bot do 5 poziomu też dostanie jedną przy najbliższym
logowaniu; quest nie odróżnia bota od gracza, a to garść skrzyń więcej.

---

## 2.0.3 — 2026-09-11

Trzecia poprawka pierwszego dnia: konto premium dla botów i tooltipy dla
GM-a. Serwer: ZAINSTALUJ AKTUALIZACJE; klient: AKTUALIZUJ KLIENTA (pakiet
`root`).

### Każdy bot ma konto premium

Ten silnik ma abonament premium (50% więcej doświadczenia, podwójna szansa
na drop przedmiotów i yang, automatyczne podnoszenie yang, dodatkowa strona
magazynu, więcej miejsc w sklepie, lepsze wyławianie ryb). Bot nie loguje się
przez serwer auth, więc nigdy go nie miał. Od tej wersji każdy bot — obecny
i każdy nowy — dostaje abonament przy wejściu do gry, bez wpisów w bazie:
premium siedzi w tabeli konta deskryptora, z której silnik czyta je przy
ładowaniu postaci (`SetPlayerProto`), i stamtąd odpowiadają wszystkie
sprawdzenia `GetPremiumRemainSeconds`. Ważne pięć lat od każdego startu.

### GM widzi tooltipy przedmiotów

Postać z uprawnieniami GM nie widziała nazwy ani statystyk żadnego
przedmiotu po najechaniu („Nie widać nazw itemów” — davids998; „tylko gdy
jesteś GM” — sizowski). Gałąź GM w tooltipie klienta iteruje po
`auxiliaryDict.items()`, a `auxiliaryDict` jest w tym roocie pustym napisem
(jego przypisanie jest wykomentowane), więc każdy tooltip umierał na
`AttributeError`, zanim został pokazany. Gałąź jest teraz strzeżona; GM
widzi zwykły tooltip plus linie VNUM/TYPE/SOCKET. Zmiana w kliencie:
AKTUALIZUJ KLIENTA.

---

## 2.0.2 — 2026-09-11

Druga poprawka z pierwszego dnia: zgłoszenia z Discorda po południu, nowa
pula nicków i aktualizacja klienta (przycisk „AKTUALIZUJ KLIENTA” w
launcherze — dwa pliki pakietu `root`).

### Konto admin ma postać GM

Paczka mt2009 przychodzi z pustą listą GM i bez żadnej postaci na koncie
`admin`, więc kto zalogował się na konto testowe, dostawał zwykłego gracza
(archded: „loguję się admin admin, a tam nie ma postaci GM”). Świeży świat
tworzy teraz na tym koncie postać **Admin** (wojownik 90 poziomu, stoi w
Joan) z uprawnieniami IMPLEMENTOR. Świat założony na 2.0.0 lub 2.0.1 dostaje
to przy najbliższym starcie: pierwsza postać konta `admin` zostaje GM (jeśli
na koncie nie ma jeszcze postaci — pierwsza, którą utworzysz, po kolejnym
starcie). Nadanie jest jednorazowe i tylko na pustej liście; świat, który
kiedykolwiek miał własnego GM, zostaje jak był.

### „Doładuj SM!” prowadzi na buycoffee, nie na mt2009.pl

Przycisk „Doładuj SM!” w sklepie z przedmiotami i przycisk w oknie
abonamentu otwierały stronę publicznego serwera mt2009 (sizowski, matthaeu;
„powinno przenosić na buycoffee” — kuszaa). Oba prowadzą teraz na
https://buycoffee.to/metin2-playerbots, a „Wsparcie” w menu systemowym na nasz
Discord. To zmiana w kliencie: w launcherze kliknij „AKTUALIZUJ KLIENTA”.
Smoczych Monet na tym serwerze nikt nie sprzedaje — dopisujesz je sobie w
bazie (`account.account.cash`).

### Boty nie oglądają straganów, których nie ma

Po załatwieniu spraw w mieście bot chwilę zostaje na placu, a nad głową
miał „Ogladam stragany” — także na świecie, na którym żaden bot nie dorósł
jeszcze do otwarcia sklepu („jakie stragany oglądają jak żadnego nie ma” —
.christoff). Bez lady na mapie mówi teraz „Odpoczywam w miescie”. To samo z
zakupami: wyprawa na targ („Szukam czegos na straganach”) rusza tylko wtedy,
gdy na tej mapie albo w pierwszej wiosce królestwa stoi jakiś stragan;
wcześniej bot szedł na pusty pitch i przeglądał powietrze.

### Panel: ranking nie wisi na „Ładowanie…”

Lista rankingu w panelu klasycznym zmieniała się tylko po udanej odpowiedzi
API, a pierwsze pobranie ruszało dopiero po pozycjach botów — na świecie,
który jeszcze nie miał botów w grze, albo po błędzie API napis „Ładowanie…”
zostawał na zawsze (davids998). Odmowa API jest teraz wypisywana w miejscu
listy, a ranking pobiera się od razu.

### Nicki botów: lista Iwakury, w całości i tylko ona

Iwakura spisał 1000 nicków z polskich serwerów z lat 2010–2012 („tu jest
postaranie”). Ta lista jest teraz jedyną pulą: znika poprzednia (lista
jaksiezabica, pierwsza lista Iwakury i nicki składane z ich słów) i znika
dopasowanie do klasy i płci — nazwy idą po kolei według PID, jak zostały
napisane. Każdy bot, który nosił nick ze starej puli, dostaje nowy przy
najbliższym starcie serwera (pula ma wersję; historia w
`common.playerbot_name_history` pamięta nazwę z seeda, więc „restore” dalej
działa). Gdy botów jest więcej niż nazw, lista idzie drugi raz z „v2” na
końcu, potem „v3”; Iwakura dopisze kolejne nicki w tygodniu. Odrzucone: dwa
wulgarne, dwa udające GM i pięć złożonych z samych cyfr. Podkreślniki są
wycinane, bo klient ich nie przyjmuje.

---

## 2.0.1 — 2026-09-11

Pierwsza poprawka linii 2.x, z pierwszego dnia instalacji u graczy.

### Budowa nie stoi już na `deps 7/7`

Pierwsza budowa pobiera pakiety Ubuntu, a archive.ubuntu.com serwowało dziś z
Polski kilka kilobajtów na sekundę: 10 MB szło kilkanaście minut, budowa
„wisiała” na `deps 7/7` po 20–40 minut (jaksiezabic, drip9660, matthaeu,
u4nt). Wpisanie w `.env` polskiego mirrora skracało to do dwóch minut
(piotrekf3). Ten mirror (`http://ubuntu.task.gda.pl/ubuntu/`) jest teraz
domyślny: pusty `M2_APT_MIRROR` w istniejącym `.env` też go dostaje, więc
nikt nie musi niczego edytować. Inny kraj wpisuje bliższy mirror w
`M2_APT_MIRROR`.

### Nazwy straganów od społeczności

Iwakura spisał nazwy sklepów z polskich serwerów z lat 2010–2012, z podziałem
na kategorie. Stragan botów ma teraz szyld według tego, co przeważa na ladzie:
ryby i małże („Sklep Rybny u Janusza ;]”, „Malze po 3000 sztuka!”), księgi
umiejętności („Makulatura po dziadku”), ulepszacze („Zolc i skora
niedzwiedzia”), ekwipunek („Zbroje na chude klaty”), medale konne, zwoje
błogosławieństwa, kamienie duchów — a stragan mieszany bierze jedną z
kilkudziesięciu uniwersalnych („TANIEJ NIZ OBOK >>>>>”, „ZBANUJCIE TE
BOTY!!!”). Broń 30 poziomu i duży ulepszony przedmiot dalej idą na szyld pod
własną nazwą. Szyld zmienia się z każdym kolejnym straganem tego samego bota.

### Stragan dopiero od 15 poziomu i 800 zabitych potworów

Ten silnik pozwala otworzyć sklep dopiero od 15 poziomu i 800 zabić
(`CanOpenShop`); młodszy bot dostawał od silnika odmowę przy każdej próbie —
39 z rzędu w młodym świecie. Bot pyta o to przed wyjściem na pitch i wraca po
dziesięciu minutach.

---

## 2.0.0 — 2026-09-11

**Nowa linia serwera: pliki serwerowe mt2009 (Martysama r41023) zamiast r40250.**
To osobna, pełna paczka — klient i serwer razem — i osobny kanał aktualizacji.
Instalacja 1.33.x niczego z tej wersji nie dostanie i nie powinna: stary
launcher i stary klient nie pasują do nowych plików. Pełną paczkę pobierasz z
Discorda (discord.gg/pt5tvnrN6), a od tej chwili aktualizacje serwera i klienta
przychodzą już przez launcher, jak dotąd.

### Podziękowania

To wydanie powstało dzięki ostatnim wpłatom. Bez nich nie byłoby czasu ani
środków na to, co się tu wydarzyło: dziesiątki tysięcy linii kodu, zmiana
architektury serwera i zbudowanie jej od nowa na innym silniku — przy
zachowaniu wszystkiego, co boty i panele potrafiły do tej pory. Dziękuję.
Wsparcie projektu: buycoffee.to/metin2-playerbots.

### Serwer

- Silnik mt2009 przeniesiony na Linuksa i budowany w Dockerze tak jak
  dotąd: cztery etapy obrazu, protosy w bazie (`PROTO_FROM_DB`), sześć baz na
  MariaDB 11.8, te same porty, ten sam launcher.
- Port jest zapisany jako skrypty, nie jako ręczne poprawki: każdy plik
  silnika, bazy, compose i share, który różni się od paczki, jest renderowany
  z oryginału r40250 albo z pakietu i da się odtworzyć jedną komendą.
- Świat startuje otwarty. Pakiet uruchamiał każdy serwer w „przerwie
  technicznej” do czasu, aż GM wpisze `/maintenance 0`; zwykłe konto widziało
  na ostatnim kroku logowania „Obecnie trwa przerwa techniczna”.
- Schemat logów uzupełniony o 23 tabele, które silnik zapisuje, a których
  pakiet nie miał; `account.social_id` poszerzony do 18 znaków (identyfikatory
  botów były ucinane); kolumny `mileage`/`jackpot` dla ItemShopu.
- Skrzynie startowe botów, skrzynia księżycowa i drop broni 30 poziomu na
  mapie gildii dopisane do plików pakietu; brakujący przedmiot w takiej
  grupie wywraca cały plik przy starcie, więc render sprawdza vnumy względem
  zrzutu świata.

### Playerbots

- Cała logika botów bez zmian w zachowaniu. Różnice silnika są zamknięte w
  jednym nagłówku (`playerbot_engine_compat.h`): numeracja bonusów
  (`POINT_*` zamiast `APPLY_*`), nazwy afektów, złoto (`ChangeGold` zamiast
  `PointChange`, który tu jest odrzucany), zakładanie przedmiotów, flagi
  specjalne postaci, wędkowanie.
- Zakładanie ekwipunku: mt2009 odpowiada na `CanEquipNow` sześć razy na pół
  sekundy na postać, a przebieg ekwipunku pytał o każdy przedmiot w torbie —
  63 tysiące odrzuconych ulepszeń na godzinę. Zegar jest zerowany przed
  każdym pytaniem; po poprawce 6940 założeń i 213 odmów w tym samym czasie.
- Flagi specjalne postaci (statystyki `stat_*`) ładują się dla botów: pakiet
  ładowania bota niesie id konta, bez którego rdzeń db odpowiadał flagami
  wszystkich botów naraz i gra je odrzucała.
- Panele klasyczny, Sebana i ItemShop działają na obu silnikach z jednym
  przełącznikiem (`M2PANEL_ENGINE` / `PLAYERBOTS_ENGINE`); ranking broni
  liczy właściwe linie obrażeń.

### Klient

- Klient w paczce jest gotowy do gry na tym komputerze (127.0.0.1); launcher
  znajduje go sam w folderze `Klient` obok `Serwer` i nie pyta o plik EXE.
- Własny regulamin w oknie logowania: co to za projekt, zasady, wsparcie na
  buycoffee, Discord, prywatność. Przyciski okna logowania prowadzą do
  GitHuba projektu, buycoffee i naszego Discorda.
- Narzędzie do packów klienta rozumie układ PackMakerLite: ten klient
  sprawdza CRC32 każdego pliku typu 2 i root spakowany po staremu nie
  uruchamiał gry (`RunMain Error`).

### Launcher i paczka

- Jeden zip na hosting (`Metin2-Singleplayer-2.0.0.zip`): `Klient\`,
  `Serwer\` i `CZYTAJ.txt`. Bez haseł, tożsamości instalacji, logów i kopii —
  launcher tworzy je przy pierwszym starcie.
- Launcher rozpoznaje silnik po pliku `linux-port\docker\ENGINE`: własny
  kanał aktualizacji (`update-manifest-mt2009.json`), lista zrzutów, brak
  łatek r40250, lista modułów kontekstu budowania.
- Adopcja istniejącej instalacji Dockera tylko tego samego silnika: kto
  przechodzi z r40250, ma na dysku jedną instalację — starą — i launcher
  podpiąłby nowy serwer pod jej bazę. Teraz stara instalacja zostaje obok,
  nietknięta, a nowa dostaje własną.
- Przycisk „PANEL GM F9” na tej linii to zwykłe „AKTUALIZUJ KLIENTA”.

### Czego jeszcze nie ma

- Panel GM F9 (część serwerowa i kliencka) — celowo pominięty, żeby nie
  kolidować z klientem; wróci osobno.
- Misje poziomowe botów: ten pakiet nie ma questa `levelup`, boty pomijają
  ten etap rozwoju.
- Wędkowanie: silnik wymaga 50 poziomu i przepustki wędkarskiej; boty na razie
  nie łowią.

---

## 1.33.3 — 2026-09-11

Poranek po nocy zgłoszeń: siedem poprawek, każda sprawdzona na żywym serwerze
testowym. Tym razem **zmienia się też klient** — paczka klienta 1.33.3.

### Panel GM nie może już zatrzymać ładowania gry

Po zainstalowaniu panelu GM u części graczy pasek ładowania stawał na 100% i
gra nie wchodziła (Dixdros, jaroszv2, .unright, ligivanestrea). Okno panelu
było budowane bezwarunkowo w środku budowy całego interfejsu, więc jakikolwiek
wyjątek w nim — kontrolka, której nie ma w innej wersji klienta, klucz, którego
nie ma w innym pakiecie językowym — przerywał budowę wszystkiego. Stockowy root
wchodził na tych samych maszynach.

Teraz panel buduje się w osobnym bloku: jeśli się nie zbuduje, gra wchodzi bez
niego, a powód trafia do `syserr.txt` w folderze klienta. F9 mówi wtedy na
czacie, że panelu nie ma i gdzie szukać przyczyny. **Sama przyczyna jest wciąż
nieznana** — nikt jeszcze nie przysłał `syserr.txt`. To zabezpieczenie zamienia
„gra nie wchodzi" w zgłoszenie, które niesie odpowiedź.

### Pełny kanał przy 2500 botach

Lista kanałów pokazywała FULL, a klient odmawiał wejścia, gdy botów było więcej
niż 1200 — silnik liczył boty jak graczy, i przy statusie kanału, i przy limicie
logowania. Boty nie są graczami w tej rachubie: liczone są tylko postacie ludzi,
także te zalogowane na innych rdzeniach. Rdzeń wypisuje co pięć minut
`CHANNEL_STATUS: players=… status=…`, więc następny zrzut ekranu będzie miał
liczbę.

### Boty przestały grzęznąć w M3

Po wejściu na mapę gildii bot lądował w punkcie (179500, 1000) — to komórka
(3, 10) mapy, nieprzechodni północno-zachodni róg. Nie miał trasy do niczego,
watchdog resetował go co półtorej minuty w tym samym miejscu i nic nie mogło go
ruszyć; teleport z panelu też nie, bo bot nie ma klienta, który mógłby przeżyć
zmianę mapy po stronie klienta. Zgłoszone z logiem przez greessa, potwierdzone
przez dwie kolejne osoby.

Ten punkt pochodził z tabeli questu Teleportera; stała w kodzie miała już od
dawna właściwy, z `Town.txt` mapy. Tabela dla trzech królestw przywróciła stary
numer. Wszystkie trzy mapy gildii lądują teraz na własnym punkcie z `Town.txt`
i test jednostkowy to przypina. Sprawdzone: ten sam bot, który rano utknął w
rogu, po poprawce wylądował na (221900, 9200), zaatakował i dosiadł konia.

### Koreański tekst zamiast „nie straciłeś doświadczenia"

Jeden plik silnika trafił do paczki przekodowany na UTF-8. Gra szuka
komunikatów po ich koreańskim kluczu, bajt w bajt, a pliki tłumaczeń są w
kodowaniu koreańskim — więc trzynaście komunikatów z tego pliku nie trafiało w
tłumaczenie i wracało po koreańsku, a każda śmierć z błogosławieństwem Boga
Smoków zostawiała błąd w logu (276 w jednym zgłoszeniu). Od 1.31.6. Plik wrócił
do właściwego kodowania; po restarcie zero takich błędów.

### Wędkarze nie rozrzucają ryb po trawie

Złowiona ryba idzie do plecaka funkcją, która pełnego plecaka nie odmawia —
kładzie rybę na ziemi i zgłasza sukces. Stąd zdjęcie od bierzyna: wędkarze
„upuszczają drop", a potem wszystkie boty biegną po niego. Sesja wędkowania
kończy się teraz, gdy w plecaku nie ma wolnego pola, i bot idzie go opróżnić.

### Nicki botów: 1000 od Iwakury, klasa i płeć się zgadzają

Iwakura przysłał tysiąc nicków z prośbą, żeby były „bardziej różne". Po
odsianiu duplikatów i tego, czego silnik nie przyjmie, 747 nowych trafiło do
puli. Reszta puli jest składana ze słów wyjętych z obu list i w ich kształtach —
poprzednia wersja składała wszystko w jednej gramatyce z czterdziestu słów.

Nick, który mówi o klasie — Włócznia, Szaman, Sura, Woj, Fms, Ninja — trafia do
bota tej klasy, a nick wyraźnie kobiecy — Szamanka, Królowa, Marysia — do postaci
kobiecej. „Ninja szamanka, ale to sura" było prawdziwym zrzutem ekranu. Zmierzone
na 2500 botach: wojownicy dostali wojownicze nicki w 80%, nicki kobiece trafiły
wyłącznie na postacie kobiece. Boty, które nick już mają, zachowują go.

### Martwy towar w końcu idzie do handlarza

Reguła „czego nikt nie kupił przez sześć stoisk, to złom" stała pod regułą „+4
i wyżej nigdy do NPC", więc nigdy nie dotyczyła tego, co stragan naprawdę
trzyma. Plecak pełen +5, których nikt nie kupuje, był plecakiem na zawsze — i to
jest bot, który „siedzi w M1, ogląda stragany i od wczoraj nie wbił poziomu".
Reguła działa teraz do +6; +7 i wyżej nadal nigdy nie idzie do NPC.

### ItemShop: moneta i zdrowie kontenera

Adres sklepu z gry miał na końcu losowy bajt zamiast kodu kraju, bo zmienna nie
była zainicjalizowana dla locale spoza listy silnika — Apache odpowiadał 400,
zanim PHP w ogóle wystartowało (archded, z logiem). Ma teraz wartość domyślną.
Do tego błąd PHP zwraca 500 zamiast 200 z treścią błędu, więc healthcheck
przestaje nazywać zepsuty sklep zdrowym, a wbudowana przeglądarka klienta nie
zapamiętuje strony błędu na stałe.

---

## 1.33.2 — 2026-09-11

Trzy zgłoszenia z Discorda z jednego wieczoru. Wszystkie sprawdzone odtworzonym
błędem, nie z lektury kodu. Klient bez zmian — aktualizuje się tylko serwer.

### Suwak liczby botów wreszcie znaczy to, co pokazuje

Suwak w launcherze sięga 2500 i tak jest podpisany, a rdzeń gry ścinał tę liczbę
do 1000. Kto ustawił więcej, dostawał dokładnie tysiąc botów i nigdzie nie było
powiedziane dlaczego — ani w logu, ani w panelu.

Sufit w rdzeniu to teraz też 2500, a gdy liczba z `.env` jest większa, rdzeń
wypisuje, co uciął. Prawdziwym ograniczeniem nigdy nie był ten sufit, tylko liczba
tożsamości botów w bazie: prośba o 3000 daje na naszym świecie 2012 botów
(shinsoo 500, chunjo 1012, jinno 500) i tak ma być.

**Zmiana suwaka działa dopiero po restarcie serwera** — rdzeń czyta tę liczbę raz,
przy starcie. To było prawdą od zawsze, ale nigdzie nie napisane.

Zmierzone przy pełnej kohorcie: 2004 boty w świecie, 33 sekundy rdzenia na minutę
dla całego kontenera gry — niecałe 0,6 jednego rdzenia. Rozdzielenie botów między
trzy królestwa jest tym, co czyni to tanim: królestwo z mapami współdzielonymi
kosztuje czterokrotnie tyle, co królestwo wioskowe.

### Launcher mówi, dlaczego nie mógł zapisać pliku klienta

„Odmowa dostępu do ścieżki" to zdanie, którym Windows opisuje co najmniej cztery
różne problemy, a launcher przepisywał je bez zmian. Gracz, który próbował
zainstalować panel GM dziewięć razy w ciągu dnia, dziewięć razy dostawał to samo
zdanie i nie miał z czym pójść dalej.

Teraz launcher sprawdza i nazywa przyczynę: proces trzymający plik, atrybut
tylko-do-odczytu (zdejmowany automatycznie), Ochrona folderów w Windows
Defenderze, albo uprawnienia NTFS — z rozróżnieniem, czy nie da się pisać do
całego folderu, czy tylko do jednego pliku.

Przy okazji wyszło coś gorszego: wycofywanie nieudanej aktualizacji przywracało
kopię zapasową na ten sam plik, którego przed chwilą nie dało się zapisać,
dostawało tę samą odmowę — i to jej komunikat wychodził na wierzch, kasując
właściwą diagnozę. Wycofywane jest teraz wyłącznie to, co naprawdę zapisano,
a żadne przywracanie nie może już przesłonić przyczyny.

**Uwaga dla graczy z panelem GM na F9:** przycisk PANEL GM to po prostu
aktualizacja klienta. Jeśli wyskakuje odmowa dostępu, to nie panel jest zepsuty,
tylko launcher nie może podmienić dwóch plików w folderze gry.

### Zaawansowany panel mówi, że tabela jest uszkodzona

Panel odpowiadał samym „Internal Server Error", bez żadnej wskazówki. Pod spodem
były uszkodzone tabele bazy `log` — silnik gry używa MyISAM, a te nie przeżywają
nagłego zatrzymania: wystarczy zamknięcie Dockera w trakcie zapisu albo zanik
zasilania.

Stąd bardzo mylący objaw: **zwykły panel działa, a zaawansowany nie** — ten drugi
czyta tabelę logów na samej stronie głównej, do rankingu wędkarzy. I stąd druga
myląca rzecz: **aktualizacja tego nie naprawia**, bo uszkodzenie jest w danych na
dysku, a nie w programie.

Panel pokazuje teraz stronę, która nazywa uszkodzoną tabelę, podaje gotową
komendę naprawy, mówi wprost, że aktualizacja nie pomoże, i wskazuje opróżnienie
tabel `log` jako ostateczność — to wyłącznie historia, gra jej nie czyta i żadna
postać ani przedmiot od niej nie zależą. Inne błędy bazy przechodzą dalej bez
zmian, żeby ta strona nie zasłaniała prawdziwych awarii.

---

## 1.33.1 — 2026-09-10

Poprawki z audytu zgłoszeń z Discorda. Wszystkie sprawdzone na żywym serwerze
testowym, nie tylko skompilowane.

### Masowe nadawanie przedmiotów gubiło sztuki i mówiło, że się udało

Panel przyjmował do 65535 sztuk, a silnik czyta tę liczbę jako jeden bajt:
300 stawało się 44, 256 stawało się zerem, 65535 stawało się 255. Nikt się o tym
nie dowiadywał, bo paczka kończyła się statusem „Nadano”.

Prawdziwy sufit jednego wydania to 200 sztuk — pełny stos, i tyle silnik potrafi
dodać za jednym razem. Powyżej tej liczby panel odmawia teraz wprost, a po
wydaniu porównuje zawartość plecaka przed i po, bo samo „silnik coś zwrócił” nie
dowodzi dostarczenia: przy braku miejsca ten sam kod kładzie przedmiot na ziemi
i też zgłasza sukces.

**Do wiadomości operatorów:** kto dotąd wpisywał 300, dostawał 44 i widział
„Nadano”. Teraz zobaczy czytelną odmowę. Limit 200 na jedno żądanie jest nowy.

### Nagrody ze skrzyń przestają lądować na ziemi

Bot sprawdzał miejsce w plecaku dwoma pytaniami o to samo pole — silnikowa
funkcja zwraca *pozycję* wolnego miejsca, a nie ich liczbę, więc dwa wywołania
obok siebie mogą wskazać tę samą kratkę i nie rezerwują niczego. Skrzynia wydaje
nagrody po kolei, a to, co się nie mieści, spada na trawę. Teraz liczone są
rzeczywiste wolne pola i skrzynia otwiera się dopiero, gdy jest ich pięć.

To zabezpieczenie, nie pełne rozwiązanie: docelowo zestaw nagród trzeba wylosować
raz, sprawdzić miejsce na całość i dopiero potem zużyć skrzynię, a to zmiana
w silniku, która musi dostać własny tryb „do plecaka albo wcale”, żeby nie ruszyć
nagród graczy.

### Bot przestał chodzić do kowala po nic

Planer i wykonawca oceniały zawartość plecaka inaczej: planer przyjmował wszystko,
co bot potrafi założyć, a wykonawca odrzucał to, co reguła złomu przeznaczyła dla
handlarza. Rozpoczęta wizyta w mieście jest zobowiązaniem, którego planer nie
cofnie, więc bot szedł przez pół mapy i wracał z niczym — zgłoszone jako „mam
wszystko +9 założone, a bot dalej lezie do kowala”. Obie strony pytają teraz
jednej funkcji.

### Świeża instalacja bazy nie zbuduje się już w połowie

Skrypt startowy bazy sprawdzał istnienie plików z danymi świata, a potem próbował
je przeczytać kontem `mysql` przez katalog wpięty z dysku hosta. Paczka
rozpakowana pod ścisłą maską uprawnień na Linuksie dawała prawa, których to konto
nie miało — import przerywał się w połowie, już po utworzeniu baz i użytkownika,
a katalog danych przestawał być pusty. Ten krok wykonuje się raz na wolumen
i nigdy więcej, więc świat zostawał na stałe w połowie zbudowany, za zdrowym
healthcheckiem.

Każdy z pięciu plików jest teraz czytany na jeden bajt, zanim powstanie
cokolwiek trwałego, a komunikat nazywa po imieniu plik brakujący, nieczytelny
i pusty. Instalator Linuksa przy okazji normalizuje uprawnienia całego kontekstu
budowy, żeby ta sytuacja nie powstała.

### Sklep z przedmiotami odpowiadał 403

`COPY` w obrazie zachowuje uprawnienia źródła, więc pliki sklepu skopiowane
z katalogu o ścisłych prawach były nieczytelne dla serwera WWW w środku
kontenera. Uprawnienia są teraz normalizowane w obrazie.

### Migrator bazy przestał czekać pół godziny na złe hasło

Błędne hasło do bazy jest odpowiedzią ostateczną, a nie chwilową niedostępnością
— migrator ponawiał je przez trzydzieści minut i kończył komunikatem o czasie
oczekiwania, który niczego nie tłumaczył. Po pięciu odmowach uwierzytelnienia
z rzędu kończy teraz pracę i pisze, co jest nie tak. Zmierzone: 9 sekund zamiast
pół godziny.

### Rankingi w panelach pokazywały nie to, co obiecywały

Trzy osobne błędy w tej samej okolicy:

- **Obrażenia od umiejętności i średnie były zamienione miejscami.** Numery 71
  i 72 stały odwrotnie w obu panelach, w panelu zaawansowanym w trzech miejscach
  naraz — w tym w nazwach kolumn, po których sortuje baza, więc pierwsza setka
  wyników była wybierana według niewłaściwej wartości.
- **Ranking +9 nie widział tarcz ani biżuterii.** Filtr odcinał wszystko powyżej
  pewnego numeru przedmiotu, co miało wykluczyć materiały, a wykluczało również
  tarcze. Panel pyta teraz bazę, co jest wyposażeniem: 17 przedmiotów zamiast 9.
- **Ranking umiejętności brał pod uwagę tylko czterystu najwyższych poziomem.**
  Bot trzydziestego poziomu z mistrzowską umiejętnością nie miał szans się
  pojawić. Liczony jest cały zbiór.

Do tego dwie osobowości botów były podpisane nawzajem: handlarz jako wędrowiec
i odwrotnie.

### Czego to wydanie nie naprawia

- **Nazwy przedmiotów w historii ekwipunku.** Tabela logów jest zadeklarowana
  w chińskim kodowaniu, a gra pisze do niej po polsku. 128 573 z 279 242 wpisów
  spoza ASCII ma w tym miejscu nieodwracalny znak zapytania — zmiana deklaracji
  naprawi to, co zostanie zapisane dalej, i nie odzyska niczego. Tabela ma
  22 miliony wierszy i 1,75 GB, więc każda zmiana to minuty przerwy w działaniu.
  To zaplanowana migracja z kopią zapasową, a nie poprawka przy okazji. Dotyczy
  wyłącznie historii — nic w grze tej kolumny nie czyta.
- **Cztery zgłoszenia czekają na powtórzenie:** wyjątki suwaka straganów, bot
  krążący po pierwszej wiosce mimo celu na pustyni, boty zamarzające lub
  znikające, oraz cenne przedmioty innych klas zapychające plecak. Każde z nich
  wymaga najpierw diagnostyki, nie ślepej poprawki.

---

## 1.33.0 — 2026-09-10

### Gra znowu jest po polsku po każdej aktualizacji

Przełącznik języka podmienia cztery pliki w `share/`: nazwy przedmiotów, nazwy
potworów i dwa pliki tłumaczeń. `share/` jest wpieczone w obraz gry, a każda
aktualizacja ten obraz przebudowuje — więc angielskie oryginały wracały na
miejsce, podczas gdy zapamiętany wybór, strona języka w panelu i status dalej
mówiły „polski". Świat był nazwany po połowie w każdym języku: nasze polskie
napisy obok „Skill Book" na szyldzie straganu, misje i potwory po angielsku.

Kontener nakłada teraz zapamiętany język przy każdym starcie. Jedno uruchomienie
naprawia instalację, która dziś jest po angielsku — nie trzeba niczego migrować.

### Hasło do panelu przestało być tajemnicą przed właścicielem serwera

`M2_PANEL_PASSWORD` bywało puste — plik `.env` przepisany z przykładu, przerwana
instalacja, serwer odpalony samym `docker compose`. Panel wymyślał wtedy
dwudziestoznakowe hasło, zapisywał sam jego skrót i wypisywał je raz do logu
kontenera, którego nikt nie czyta. Od tej chwili panel miał hasło, które nie
istniało nigdzie.

Launcher wypełnia teraz tę lukę, zanim Docker ją zobaczy, i pokazuje hasło.
A przycisk OTWÓRZ PANEL WWW ma trzecią pozycję — „Nie mogę się zalogować" —
która pokazuje hasło z `.env` i proponuje reset, gdy panel pamięta starsze.
Baza, świat, postacie i boty nie są tym ruszane.

### Strona panelu domyślnie po polsku

Panel pytał najpierw przeglądarkę i spadał na angielski, więc Polak na
angielskim Windowsie dostawał angielski. To, co widział, było gorsze od obu
języków osobno: ten panel jest przetłumaczony w połowie, więc angielska strona
to polska strona z dziurami. Teraz domyślny jest polski, a wybór z przełącznika
w nagłówku jest pamiętany przez rok.

### Boty noszą ludzkie nicki

Trzy tysiące sześćset nicków: 1491 napisanych przez jaksiezabica dla tego
serwera, reszta złożona z tego samego słownictwa. Bot utworzony minutę wcześniej
dostaje nick na tym samym starcie. `M2_PLAYERBOT_HUMAN_NAMES`: 1 nadaje
(domyślnie), 0 nie rusza niczego, „restore" przywraca stare nazwy — stara nazwa
jest zapamiętana, więc to odwracalne.

Nazwa jest jedyną częścią tożsamości bota, od której nic nie zależy: rdzeń
dopasowuje postać po loginie konta, a oba panele robią to samo. Nasiona wymagały
poprawki w pięciu miejscach, żeby przemianowany bot nadal był ich botem.

### Bonusy wyceniane według map i slotów

Linia „silny przeciwko orkom" mnoży cały atak przeciwko każdemu potworowi tej
rasy. Pas ekwipunku wyceniał ją wysoko, a pas mixowania na jeden punkt — bot
kupował tarczę dla tej linii i zrzucał ją u pierwszego kowala. Teraz obie strony
pytają o to samo i skalują udziałem rasy w mapie, zmierzonym po wszystkich
punktach odrodzenia: Dolina Orków to 63% orków, każda druga wioska 100% ludzi,
Lochy Małp 100% zwierząt, Sohan 46% nieumarłych. Na Pustyni i w obu Lochach
Pająków żadna taka linia nie działa i bot już o tym wie.

Druga rzecz: reguła „przedmiot skończony" pytała hełm o życie i wartość ataku, a
kolczyki o życie i krytyczne — żadna z tych linii nie może wypaść na tych
slotach, więc hełm, kolczyk i bransoleta były mixowane bez końca. Każdy slot ma
teraz warunek z linii, które na nim faktycznie wypadają.

### Flaga królestwa przy nicku bota

W obu panelach. Przy okazji wyszło, że konta botów Shinsoo i Jinno twierdziły,
że są z Chunjo — nasiona wpisywały tam dosłownie 2 dla całej kohorty. Naprawione
także dla kont już założonych.

### Kopia świata w launcherze

Przycisk KOPIA ŚWIATA: zapisz, przywróć, zacznij od zera. Kopia to pięć zrzutów
SQL, plik z datą i liczbą postaci oraz jeden zip w folderze `backups`.
Przywracanie zapisuje najpierw obecny świat do własnej kopii. Reset odmawia,
dopóki pliki, z których powstaje nowa baza, nie leżą na dysku.

Przy okazji: obietnica z okna importu — „kopia trafi do folderu backups" — nie
była prawdziwa. Sonda sprawdzająca istnienie bazy miała cudzysłów w miejscu, w
którym PowerShell go nie przepuszcza, więc folder z kopią był pusty przy każdym
imporcie, jaki ktokolwiek wykonał.

### Panel GM (F9): osiem nowych komend

Nowa wersja panelu OskarPWA dostała stronę serwera: losowe bossy i metiny (pula
metinów budowana z plików serwera, nie z zaszytej listy), marmur przemiany,
siedemnaście suwaków AI zapisywanych do tego samego pliku co panel webowy, trzy
raty i restart. Klientowa połowa jedzie w paczce klienta tej wersji.

---

## 1.32.5 — 2026-09-10

### Suwak straganiarzy znowu coś znaczy

Bot z sześcioma nadmiarowymi książkami umiejętności otwierał stragan
bezwarunkowo, z pominięciem suwaka handlu — i było to w kodzie zapisane jako
zamierzone. Rzecz w tym, że książki po kilku godzinach polowania na metiny ma
praktycznie każdy świat, więc ta jedna reguła decydowała o udziale straganiarzy,
a suwak nie ruszał niczego. Zgłosił Shenyo: 180 straganów na 288 botów przy
suwaku ustawionym na minimum.

Zmierzone u nas: 238 botów z 970 ma sześć lub więcej nadmiarowych książek, czyli
czwarta część populacji kwalifikowała się bez względu na ustawienie. Teraz i ta
reguła pyta o wagę handlu. Przy ustawieniu domyślnym zachowanie jest takie jak
dotąd — sprawdzone po wdrożeniu — a przy minimum stragany faktycznie przestają
powstawać.

### Panel nie każe instalować czegoś, czego tu nie ma

Konsola ustawień w panelu zaawansowanym pokazywała ostrzeżenie „Zainstaluj
integrację `m2-server-settings` i `m2-supervise`". Ta wersja serwera takiej
integracji nie zawiera i nie potrzebuje: restart serwera oraz zmiana rat działają
bez niej i zawsze działały. Niedostępna jest wyłącznie zmiana respawnów map, i
tylko to komunikat mówi teraz.

---

## 1.32.4 — 2026-09-10

### Boty oddają wreszcie okazy Biologowi

Bot z dwoma Zębami Orka w plecaku przechodził obok Biologa i je zatrzymywał.
Próg czterech sztuk, który miał sens jako powód do wyprawy z frontu do M1,
stosował się też do bota, który już stoi w swojej wiosce — a quest przyjmuje
jedną sztukę na raz, więc nie było na co czekać.

Zmierzone przed poprawką: 656 botów od trzydziestego poziomu nie oddało ani
jednej sztuki, niosąc między sobą 577 zębów. Po niej, w dziesięć minut: 1766
przyjętych okazów i 778 wizyt u Biologa.

Przy okazji Shinsoo i Jinno dostały swoich Biologów. Warunek sprawdzający mapę
Chunjo przetrwał w tym miejscu przenosiny na katalog królestw i odcinał oba nowe
królestwa od ich własnego NPC.

### Ulepszanie broni ruszyło z miejsca

Cenny przedmiot był wstrzymywany, gdy szansa powodzenia wynosiła mniej niż sto
procent, czyli na każdym kroku tabeli ulepszeń, a zwoju szukano dopiero od +6.
Poniżej +6 przedmiot nie mógł więc być ani ryzykowany, ani chroniony i nie
ruszał się wcale (zgłosił sekuras).

Zmierzone: 451 z 959 botów posiadających zwój nosiło broń dokładnie na +4, a 230
na +0, przy 1287 Zwojach Boga Smoków i 1002 Zwojach Błogosławieństwa w
plecakach. Teraz zwoju wolno szukać przy każdym poziomie ulepszenia, a
wstrzymanie zostaje tylko tam, gdzie porażka naprawdę kosztuje. Po wdrożeniu:
6361 prób ulepszenia w pięć minut wobec praktycznego zastoju wcześniej.

Uczciwie o drugiej połowie tego zgłoszenia: pomiar pokazał, że większość botów
stojących na +4 nie ma po prostu materiału. Krok z +4 na +5 wymaga dwóch sztuk
Nieznanego Lekarstwa+, a w całym świecie jest ich 586 na około 360 takich botów.
Tego kod nie naprawi, to kwestia dropu i rynku.

### Skrzynie nie wysypują się już na ziemię

Przed otwarciem skrzyni sprawdzane było miejsce na jeden mały przedmiot, a
skrzynia wydaje kilka — sama broń zajmuje trzy komórki. Silnik nie odmawia przy
pełnym plecaku, tylko rzuca resztę na ziemię i zgłasza sukces, więc zawartość
lądowała pod nogami bota na oczach wszystkich (zgłosił archonek2137). Teraz bot
pyta o miejsce na broń, zanim otworzy.

### Boty kupują tylko to, co handlarz naprawdę ma

Bot nie kupował drogich broni — on je tworzył. Zakup przedmiotu z drabinki
rozwoju wywoływał silnikowe „daj przedmiot" i liczył cenę z tabeli
przedmiotów, nie zaglądając wcale do asortymentu NPC. Stąd bot w Masce Strachu
na sześćdziesiąty poziom kupionej za 20 000 yang u handlarza zbrojami, choć
żaden sklep w tym świecie jej nie ma (zgłosił jaksiezabic, z linią logu na
dowód).

Teraz bot kupuje wyłącznie to, co stoi na ladzie u handlarza bronią, zbrojami
albo różności, i po cenie sklepu. Warto wiedzieć, co to znaczy: te trzy sklepy
mają razem 64 pozycje, broń do 36 poziomu, zbroje do 26, hełmy tylko startowe.
Wszystko powyżej ma pochodzić z dropu, straganów i kowala — dokładnie tak, jak
u gracza.

---

## 1.32.3 — 2026-09-10

### Trzy królestwa dało się włączyć tylko na świeżej instalacji

Plik `.env` powstaje raz i nigdy nie jest przepisywany, bo trzyma Wasze hasła,
których nikt inny nie ma. Skutkiem ubocznym było to, że każdy przełącznik
dodany do wzorca po Waszej instalacji po prostu u Was nie istniał, a rada
„ustaw `M2_PLAYERBOT_KINGDOMS=1`" dotyczyła linii, której w pliku nie ma
(zgłosił jaksiezabic). Nic nie wywalało błędu, bo Docker ma własną wartość
domyślną. Po prostu nie było czym włączyć królestw.

Launcher dopisuje teraz do `.env` wyłącznie ustawienia, których w nim nie ma, i
zawsze z wartością domyślną z pliku wzorcowego. Nie rusza żadnej istniejącej
linii i nigdy nie tyka haseł ani kluczy. Sprawdzone na prawdziwym `.env`
starszej instalacji: dopisało siedem ustawień, które narosły przez ostatnie
wydania, i nie zmieniło ani jednej linii, która już tam była.

### Panel zaawansowany po nieczystym zatrzymaniu serwera

Siedemdziesiąt trzy z siedemdziesięciu pięciu tabel tej gry to MyISAM, a jedno
nieczyste zatrzymanie wystarczy, żeby oznaczyć tabelę jako uszkodzoną. Od tej
chwili każdy, kto z niej czyta, dostaje błąd, więc klasyczny panel działa
normalnie (czyta pliki), a zaawansowany wywala się na „Internal Server Error"
(czyta wyłącznie bazę). Zgłosił archonek2137, z wklejonym błędem — co skróciło
szukanie do minuty.

Automatyczna naprawa w konfiguracji obejmuje tylko tabele otwierane po tym, jak
ustawienie weszło w życie, więc baza, która już chodziła w chwili aktualizacji,
zostawała na starym zachowaniu aż do restartu. Teraz przy każdym starcie serwera
idzie przebieg naprawczy, który ogląda wyłącznie tabele niezamknięte poprawnie i
naprawia uszkodzone, zanim cokolwiek z nich przeczyta. Na zdrowym świecie
kosztuje 417 milisekund przy tabeli `log` wielkości 1130 MB i 21,7 miliona
wierszy, więc startu nie opóźnia, a błąd nigdy nie zatrzymuje uruchamiania.

### ItemShop odpowiadał błędem 400

Rdzeń składa link, który otwiera klient, jako `http://` plus zawartość
`M2_MALL_URL`. Adres wpisany razem ze schematem dawał więc
`http://http://127.0.0.1:7791/ishop?...`, a wbudowana przeglądarka klienta
odpowiadała gołym HTTP 400, o którym w logach serwera nie ma ani słowa (zgłosił
jaroszv2). Napisanie `http://` przed adresem jest odruchem, więc adres jest
teraz przyjmowany w każdej postaci, a schemat i końcowy ukośnik są zdejmowane
przy starcie.

Przy okazji: `M2_MALL_URL` występował w pliku wzorcowym dwa razy. Docker bierze
ostatnie wystąpienie, więc kto przeczytał opis przy pierwszym i tam wpisał swój
adres, nie dostawał z tego nic. Został jeden wpis, ten z opisem.

---

## 1.32.2 — 2026-09-10

### Suwak liczby botów sięga teraz 2500

Przy włączonych trzech królestwach dosiew tworzy 2500 botów, a suwak w
launcherze kończył się na 1500. Tysiąca dosianych botów nie dało się w ogóle
poprosić z poziomu okienka. Zgłosił xewi zaraz po 1.32.0.

Limit siedział w dwóch miejscach i podniesienie samego suwaka nic by nie dało:
funkcja zapisująca liczbę do `.env` zaciskała ją z powrotem do 1500, więc
widzielibyście 2500, a do pliku poszłoby 1500. Poprawione są oba miejsca, a
także tryb konsolowy i pozycja w menu.

Dla samego Chunjo, czyli przy domyślnych ustawieniach, sufitem dalej jest 1500,
bo tyle tożsamości tworzy ziarno. Proszenie o więcej, niż świat ma, było i jest
bezpieczne: rdzeń uruchamia tyle botów, ile ma w rejestrze, i wypisuje w logu
ile poproszono, ile jest zarejestrowanych i ile wystartowało.

### Masowe dawanie przedmiotów botom

Nic tu nie zmieniamy w kodzie, ale warto wiedzieć, skąd się brało „nie działa"
(zgłosili zombian. i archded). Panel zleca nadanie przez wiersz w bazie, a
podejmuje go pomocniczy quest w grze. Quest jest kompilowany przy budowaniu
obrazu gry, nigdy przy starcie kontenera, więc serwer, którego obraz zbudowano
przed 7 września, ma starszego questa i na każde zlecenie odpowiada „Quest
wymaga aktualizacji". Wystarczy zaktualizować i kliknąć GRAJ, czekając aż
przejdzie budowanie obrazu.

Sprawdzone po przebudowaniu: zlecenie kończy się statusem „Nadano" w trzy
sekundy, a log gry pokazuje utworzenie przedmiotu na koncie bota.

---

## 1.32.1 — 2026-09-10

### Sprawdzanie aktualizacji mówi prawdę

Przez dwadzieścia minut po wydaniu 1.32.0 launcher pokazywał wszystkim naraz
dwa sprzeczne komunikaty: w stopce „Najnowsza wersja: nie udało się sprawdzić",
a w okienku „Kanał aktualizacji nie ma obecnie nowej wersji serwera". Żaden z
nich nie był prawdziwy. Nowa wersja była, tylko launcher nie potrafił odczytać
pliku, w którym o niej pisze. Zgłosili to kiciamol i jaksiezabic, jeden był o
krok od skasowania instalacji i postawienia jej od zera.

Winny był plik manifestu, który poszedł ze znacznikiem BOM na początku —
żaden wcześniejszy go nie miał. Sam manifest został poprawiony od razu i
naprawa nie wymagała żadnej aktualizacji po Waszej stronie. To wydanie
naprawia drugą połowę problemu, czyli to, że launcher w ogóle mógł tak
skłamać:

- **Manifest jest teraz czytany i rozbierany u nas, a nie przez
  `Invoke-RestMethod`.** Ta komenda nie zgłasza błędu, gdy odpowiedź nie jest
  poprawnym JSON-em: po cichu oddaje surowy tekst zamiast obiektu. Launcher
  pytał wtedy taki tekst o wersję serwera, nie znajdował jej i uznawał, że
  aktualizacji nie ma.
- **Znacznik BOM jest zdejmowany przed odczytem**, więc ta sama pomyłka nie
  zablokuje już nikomu aktualizacji.
- **Pusta odpowiedź, strona HTML podstawiona przez proxy albo firmową sieć i
  każdy inny plik, który nie jest manifestem, kończą się teraz czytelnym
  błędem**, który wprost mówi, że problem jest po stronie kanału aktualizacji,
  a nie Waszej instalacji.
- Komunikat o braku wersji mówi „kanał nie podał wersji serwera" zamiast
  twierdzić, że nowej wersji nie ma.

Sprawdzone w tym samym Windows PowerShellu 5.1, w którym chodzi launcher:
poprawny plik i żywy adres dają wersję, plik z BOM przechodzi, a strona HTML i
pusta odpowiedź dają nazwany błąd.

---

## 1.32.0 — 2026-09-10

### Trzy królestwa

Dotąd cały świat botów był jednym królestwem: Chunjo, jego dwie wioski i jego
mapy. Shinsoo i Jinno stały puste. Od tego wydania boty mogą żyć we wszystkich
trzech królestwach naraz, każde w swoich wioskach, u swoich kupców i na swoich
łowiskach.

**Domyślnie nic się nie zmienia.** Przełącznik `M2_PLAYERBOT_KINGDOMS` w
`.env` jest ustawiony na `0`, więc świat, który masz, zostaje dokładnie taki,
jaki był: 1500 botów Chunjo, te same postacie, te same poziomy, ten sam
ekwipunek. Żeby dołożyć dwa nowe królestwa, ustaw `M2_PLAYERBOT_KINGDOMS=1` i
uruchom serwer ponownie. Dosiewane jest wtedy 500 botów Shinsoo i 500 Jinno
obok istniejących; nic z tego, co już masz, nie jest ruszane ani przepisywane.

Co dostaje każde królestwo:

- **Własne wioski.** Yongan i Jayang dla Shinsoo, Joan i Bokjung dla Chunjo,
  Pyongmoo i Bakra dla Jinno. Nazwy są te, których używają questy silnika, a
  nie zgadywane.
- **Własne usługi.** Handlarz bronią, handlarz zbrojami, handlarka różności,
  dozorca, kowal, stajenny, starsza pani i Teleporter tej wioski, w której bot
  stoi. Wcześniej bot Shinsoo pisał nad głową „Ide do kowala" i szedł do kowala
  osiemdziesiąt kilometrów dalej, bo w kodzie były wpisane współrzędne Chunjo.
- **Własnych trenerów zawodu.** Ośmiu w każdej pierwszej wiosce. Drugie wioski
  nie mają żadnego i nigdy nie miały, i właśnie dlatego bot bez grupy
  umiejętności wraca do M1.
- **Własnego Biologa**, własny rynek ze straganami i własne łowisko z Rybakiem.
- **Własne tereny łowieckie.** Huby, pasma poziomów, punkty metinów i Bestialni
  bossowie każdej drugiej wioski, zmierzone z plików mapy tego królestwa.
- **Własne bramy.** Każdy przeskok między mapami królestwa czyta bramę i punkt
  lądowania z nazwy samego NPC, tak jak robi to silnik. Sprawdzone: wszystkie
  osiemnaście bram prowadzi tam, gdzie ma prowadzić, i wypuszcza postać na
  gruncie, po którym da się chodzić.

Chunjo nie został ruszony. Pomiar odtwarza jego stare, ręcznie wpisane
współrzędne co do jednostki — łącznie z trzema bossami Bokjung i ośmioma
trenerami Joan — i test pilnuje, żeby tak zostało.

### Panele widzą cały świat

- **Klasyczny panel** dostał granice i mapy terenu ośmiu nowych map, nazwy
  wiosek w filtrze i w rankingu. Do tej pory boty Shinsoo i Jinno były żywe i
  niewidoczne.
- **Panel zaawansowany** dostał te same granice, więc jego żywa mapa i lista
  śledzonych map obejmują nowe królestwa, a konsola respawnu ziemie klanowe.
- Mapa 24 była podpisana „Pyungmoo" i „Waryong". Pyongmoo to stolica Jinno, nie
  ziemia klanowa Chunjo; obie nazwy poprawione.

### Czego nowe królestwa jeszcze nie mają

Wspólne mapy świata — Dolina Orków, Pustynia Yongbi, Góra Sohan, oba Lochy
Pająków, Świątynia Hwang i dwa trudniejsze Lochy Małp — są hostowane przez ten
sam rdzeń co Chunjo, a bot nie może przejść na mapę, której jego rdzeń nie
hostuje (przeniesienie postaci między rdzeniami wymaga ponownego połączenia
klienta, a bot klienta nie ma). Dlatego Shinsoo i Jinno mają na razie własne
cztery mapy, które niosą je mniej więcej do trzydziestego szóstego poziomu.

Żeby to nie kończyło się botami stojącymi bezczynnie: bot nie jest wysyłany na
mapę spoza swojego rdzenia, a królestwo bez frontu może polować w swojej drugiej
wiosce także powyżej trzydziestego piątego poziomu. Rozwiązanie docelowe to
decyzja o tym, jak ma być poukładany serwer, i czeka na Ciebie.

### Drobne

- **Raport rejestru mówił nieprawdę.** Liczył tożsamość jako odrzuconą, gdy jej
  królestwo nie było Chunjo, więc wypisywał „wrong_empire=1000" obok modułu,
  który przed chwilą przyjął wszystkie tysiąc. Teraz odrzuceniem jest tylko
  królestwo spoza zakresu 1-3.

### Pomiar

Na serwerze testowym, 970 botów w trzech królestwach naraz:

| co | ile |
|---|---|
| procesor | 12,59 s rdzenia na 65 s ściany, czyli 19,4% jednego rdzenia |
| tick, rdzeń Shinsoo | 1,45 s z 60 |
| tick, rdzeń Chunjo | 2,16 s z 60 |
| tick, rdzeń Jinno | 1,41 s z 60 |
| resety watchdoga | 0, 1, 0 |

Budżet, którego pilnujemy, to 40% rdzenia przy 850 botach. W cztery minuty nowe
królestwa zrobiły po ponad 600 wizyt u własnych kupców i po ponad 300 u własnych
trenerów.

---

## 1.31.8 — 2026-09-10

### Boss z pustyni w Bokjung

- **Boss nie skacze już za ofiarą na inną mapę** (zgłosił Pasywny: komuś
  przeteleportował się Olbrzymi Żółw z Pustyni Yongbi do M2). Błąd jest w
  samym silniku, w `char_state.cpp`: żółw (rasa 2191) co jakiś czas
  przeskakuje pod swoją ofiarę przez `Show(victim->GetMapIndex(), ...)`,
  a więc bierze mapę **ofiary**, nie swoją. Gdy ofiara w tym czasie przeszła
  przez bramę albo zapłaciła Teleporterowi, boss szedł za nią i lądował w
  mieście. Łatka 0011 pozwala bossowi gonić i przeskakiwać tylko do ofiary
  na tej samej mapie; ta sama poprawka usuwa bezsensowną pogoń za
  współrzędnymi z mapy, której ofiara już nie ma. Dotyczy też graczy, nie
  tylko botów. Plik `char_state.cpp` jedzie w aktualizacji jak `char.cpp`.

### Aktualizacja na Linuksie i VPS

- **Aktualizacja nie zatrzymuje się już na łatce 0009** (zgłosił archded, wraz
  z trafną diagnozą). `prepare-context.sh` sprawdzał każdą łatkę osobno, na
  nietkniętym drzewie — a to inne pytanie niż to, o które chodzi: pierwszy
  hunk łatki 0009 ma w kontekście `#include "playerbot_manager.h"`, który
  dokłada łatka 0001. Osobno nie przechodzi, po kolei przechodzi bez zarzutu.
  Każda instalacja na Linuksie i VPS stawała w tym miejscu („Hunk #1 FAILED at
  37") i nie dało się zaktualizować; Windows tego nie widział, bo tam launcher
  wykłada pliki już połatane. Teraz próba jest kumulacyjna: pliki, których
  dotyka seria, lądują w katalogu roboczym poza kontekstem budowy i cała seria
  jest tam nakładana naprawdę. Prawdziwe drzewo zostaje ruszone dopiero wtedy,
  gdy próba przejdzie do końca — zasada „albo wszystkie, albo żadna" zostaje.

### Baza danych

- **Uszkodzona tabela naprawia się sama** (zgłosił cyckiseusmaz: „Błąd: (144,
  Table './player/quest' is marked as crashed and last (automatic?) repair
  failed")). Siedemdziesiąt trzy z siedemdziesięciu pięciu tabel gry to MyISAM,
  który nie znosi nagłego zatrzymania — wyciągnięta wtyczka, ubity kontener
  albo pełny dysk zostawiają tabelę oznaczoną jako uszkodzona i od tej chwili
  wszystko, co ją czyta, pada. Domyślne `BACKUP,QUICK` naprawia tylko plik
  indeksu, więc gdy uszkodzony jest plik danych, automat się poddaje — i to
  właśnie mówi ten komunikat. Ustawiamy `BACKUP,FORCE`: pełna naprawa przy
  otwarciu, z kopią uszkodzonego pliku obok, żeby nic nie znikło po cichu.
  **Kto ma ten błąd teraz**, naprawi go jednym poleceniem, zanim zaktualizuje:
  `docker compose exec mariadb mysqlcheck -uroot -p"$M2_DB_ROOT_PASSWORD" --auto-repair --check --all-databases`

### Boty i ulepszacze

- **Bot nie sprzedaje już zwojów ulepszeń handlarzowi** (zgłosił jaroszv2).
  Reguła złomu nie miała dla nich żadnej gałęzi, a handlarz płaci grosze za
  jedyną rzecz, bez której nie da się ulepszać powyżej +6: u nas przez dobę
  poszło tak 471 Zwojów Błogosławieństwa, podczas gdy bronie na nie czekały.
  Objęte są wszystkie zwoje, które zna silnik: Błogosławieństwa, Magiczny
  Kamień, Podręcznik Kowala, Zwój Boga Wojny i Zwój Boga Smoków. Na straganie
  nadal mogą stać — inny bot też ich potrzebuje.

### Miasta

- **Zdjęte limity straganów i zwiedzających.** Bokjung miał limit straganów
  (8 promili żywych botów), a straganiarz, który zastał pełny rynek, szedł
  z towarem do Joan. Jedno i drugie zniknęło: miasto ma się zaludniać, a
  odprawiony straganiarz to bot bez zajęcia. Joan bierze stragany od botów,
  które w Joan stoją.
- **Bot odsyła konia, gdy zsiada w strefie bezpiecznej.** `StopRiding`
  zostawia konia jako towarzysza, więc każde zsiadanie w mieście dokładało
  wierzchowca do tłumu na placu (u nas 295 zsiadań na M1 w kwadrans).
  Sprawdzone w `server_attr`: oba rynki, w Joan i w Bokjung, mają flagę
  strefy bezpiecznej, więc koń znika dokładnie tam, gdzie stoi tłum. Na
  mapach łowieckich koń zostaje, bo bot zaraz znów go dosiądzie.

---

## 1.31.7 — 2026-09-10

### Boty w grze (sosen, „Ulepszanie broni na 30 lvl oraz zmiany w umiejętnościach”)

- **Punkty skilli przenoszone Księgą Zapomnienia.** Po wprowadzeniu
  priorytetów bot z szesnastoma punktami w Tąpnięciu wkładał nowe punkty w
  Duchowe, a stare zostawały. Teraz bot bez wolnych punktów zdejmuje jeden
  punkt Księgą Zapomnienia z najniżej stojącego skilla, który ma ich więcej
  niż jeden, i wkłada go w najwyżej stojący jeszcze bez Mistrza — jeden punkt
  na 30 s, księga za 20 000 yang, od piątego poziomu. Skille już na Mistrzu
  zostają, bo silnik ich nie obniża.
- **Każda broń ze średnią ≥ 20% jest gotowa i nie jest przelosowywana.**
  Reguła „gotowa broń” działała tylko dla rodziny broni 30 lv, więc np. łuk
  45 lv ze średnią 40% był losowany Zaczarowaniem, aż dobił wynik punktowy,
  a średnia znikała. To były te „zmiksowane średnie 35+”.
- **Broń 30 lv od +6 w górę tylko na zwoju.** Bez Zwoju Błogosławieństwa
  (albo lepszego) bot nie niesie jej do kowala, tylko czeka — dotąd czekała
  tylko broń z nagrodowymi liniami.

---

## 1.31.6 — 2026-09-10

### Yang prosto do sakiewki, dla każdego

- **Yang z zabójstwa trafia prosto do sakiewki każdemu — graczom i botom —
  bez Trzeciej Ręki** (Invisible: „czy da się dodać status trzeciej ręki bez
  zajmowania slota w eq?”; Tieru: „na większości serwerów tak jest
  domyślnie”). Łatka silnika 0010 w `CHARACTER::RewardGold` uznaje każdego
  zabójcę za wyposażonego w automatyczne zbieranie; Trzecia Ręka i premium
  nadal są honorowane, ale niepotrzebne. Plik `char_battle.cpp` jedzie w
  aktualizacji jak `char.cpp`.
- **Boty zdejmują i oddają Trzecią Rękę** (72016–72018): pass, który do tej
  pory ją tworzył, zakładał i nakręcał, teraz ją usuwa, żeby nie zajmowała
  slota. Gracze swoje egzemplarze zachowują.

---

## 1.31.5 — 2026-09-10

### Boty w grze

- **Bot znów zbiera cudzy drop, gdy ma okazję** (decyzja Tieru). Blokada z
  1.31.4 („przedmiot bez właściciela podnosi tylko bot, który widział go,
  gdy był jego”) cofnięta: po dziesięciu sekundach drop przestaje mieć
  właściciela i bot bierze go jak każdy gracz, który stoi obok. Reszta
  1.31.4 bez zmian.

---

## 1.31.4 — 2026-09-10

### Aktualizacja, która się nie budowała

- **Obraz ItemShopu bez `apt-get`** (Marcol, paczka z 23:43: „target itemshop:
  failed to solve … Splitting of clearsigned file failed”). Obraz `php:8.2-apache`
  przeszedł na Debiana trixie, którego `apt` weryfikuje repozytorium przez
  sequoia i na niektórych Docker Desktopach pada; jedna nieudana warstwa
  anulowała całą budowę i serwer zostawał na starej wersji. ItemShop jest
  teraz przypięty do bookworm i nie stawia żadnej paczki Debiana (healthcheck
  pyta samo PHP), a panel klasyczny też jest przypięty do bookworm. Jeśli u
  kogoś strona ItemShopu „się nie ładuje” (sosen), to najpewniej ten sam
  powód: kontener sklepu nigdy nie powstał.

### Boty w grze

- **NPC z siodła** (Tieru). Bot nie zsiada już z konia przy sklepie, kowalu,
  dozorcy, Biologu ani przy portalu — silnik obsługuje jeźdźca przy każdej
  ladzie, odmawia tylko czytania księgi (tu bot zsiada) i stroju. Zsiadanie
  przy każdym NPC i wsiadanie zaraz potem było najbardziej widoczną częścią
  wizyty w mieście.
- **Koń odwołany na czas łowienia** (cyfrowy_mat: „wszystkie moje boty łowią
  z końmi obok”). Zsiadając przy wodzie bot odsyła konia, jak gracz, i
  przywołuje go do jazdy.
- **Bot nie zbiera cudzego dropu** (Kuszaa: „bije metina w M1, podchodzi
  jakiś koks i zbiera mój złom”). Silnik po dziesięciu sekundach zdejmuje
  własność z przedmiotu i od tej chwili każdemu odpowiada „twój”; pass lootu
  brał to dosłownie. Teraz przedmiot bez właściciela podnosi tylko bot, który
  widział go, gdy jeszcze był jego.
- **Martwy towar na straganie** (sekuras, cyfrowy_mat, jaksiezabic). Linia,
  która wróciła z lady niesprzedana, jest na następnym stoisku o 10% tańsza
  (do 40% po czterech), a broń albo zbroja poniżej +4, której nikt nie chciał
  przez sześć stoisk, idzie do handlarza. Od +4 w górę nic się nie zmienia —
  tego handlarz od bota nie dostaje.

- **Priorytety wbijania skilli według listy sosena** (wątek „Priorytety
  wbijania skilli przez botów”). Każdy build ma teraz kolejność punktów:
  Wojownik Body: Aura, potem Berek/Wir (losowo), potem Szarża/Trójstronne;
  Mental: Silne Ciało, Duchowe/Walnięcie, Tąpnięcie, Uderzenie Miecza; Sura
  WP: Czarowane Ostrze, potem cztery losowo, Rozproszenie na końcu; Sura BM:
  Ognisty Duch, Mroczna Ochrona, potem cztery losowo; Szaman Smok: Pomoc
  Smoka, Błogosławieństwo/Skowyt, Talizman/Strzelający Smok, Odbicie;
  Healer: Leczenie, Zwinność/Błyskawica/Szpon, Piorun/Zwiększenie Ataku;
  Ninja Dagger: Chmura/Zasadzka, Sztylet/Szybki Atak, Krycie; Archer: Ognista,
  Trująca, potem trzy losowo. „Losowo” to stały los per bot, więc dwa boty
  jednego buildu różnią się, a jeden bot jutro chce tego samego. Pierwszy
  skill z listy idzie do Mistrza przed drugim punktem w czymkolwiek innym.

### ItemShop

- **Księga Zapomnienia (70037) w ItemShopie** (sosen): cofa punkt wybranej
  umiejętności, dla skilla, który utknął na 17 po trzydziestym poziomie.
  Trafia też do sklepów już założonych, raz, pod kolejnym wolnym numerem.

---

## 1.31.3 — 2026-09-09

### Łucznik kontra Metin

- **Łucznik bije kamienie Metin sztyletem albo mieczem, nie łukiem** (Kuszaa,
  „Archer vs metin”: łucznik przewracał się przy kamieniu kilka razy i
  odpuszczał). Kamień nie rusza się z miejsca, strzały się kończą, a strzał z
  łuku to ułamek uderzenia wręcz. Łucznik trzyma teraz w torbie jedną broń na
  kamienie — sztylet przed mieczem, bo jest szybszy i tańszy; miecz tylko
  gdy sztyletu brak — dobiera ją, gdy celem jest Metin, i wraca do łuku,
  gdy kamień pęknie. Bez łuku w ręce nie
  rzuca umiejętności (silnik liczy je ze strzały: bez łuku dają 0), tylko
  zwykłe ciosy. Kupiec broni sprzedaje mu sztylet na jego poziom, gdy w
  torbie nie ma żadnego; ani stragan, ani sprzedawca tej broni nie zabierają.
  Panel klasyczny: pod znacznikami `PLAYERBOT_GEAR: archer draws the stone
  weapon` / `takes the bow back` w logu.

### Boty przy bramie do Joan w Bokjung

- **Boty nie kotłują się już przy bramie do Joan** (Kuszaa, nagranie z
  1.31.1: boty ze statusem „Ide na Gore Sohan”, „Ide do Lochu Malp”, „Ide do
  kowala” dojeżdżają do bramy, zsiadają z konia, po chwili wsiadają i
  odjeżdżają, a po kilku minutach wracają). Diagnostyka na naszym serwerze:
  152 ze 160 marszów pod tę bramę w dziesięć minut to targ — bot bez
  straganu w zasięgu miał „najpierw zajrzeć do Joan”, ale pass targu prosił
  o portal raz na dwie–pięć minut, więc trasę do bramy dokańczały zwykłe
  passy ruchu, a przy samej bramie nikt już o przejście nie prosił; bot
  oddawał tick wędrówce i odjeżdżał, a po następnym pytaniu targu wracał.
  Teraz marsz na targ w Joan jest zobowiązaniem: bot prosi o portal co tick,
  aż zmieni mapę, a bot, którego miejsce jest na pograniczu (albo którego
  wyjazd wstrzymał sprawunek), w ogóle tam nie idzie — kupuje w zasięgu w
  Bokjung. Do tego passy, które tylko kontynuują trasę do portalu, nie
  zsiadają już z konia kilometr przed bramą.

### Bot bez yangów na Teleporter

- **Bot, którego nie stać na Teleporter, poluje w Bokjung na opłatę, zamiast
  pytać Teleportera co tick.** Pomiar u nas: 268 z 362 botów 40+ w Bokjung
  miało mniej yangów niż jedna opłata (najbiedniejszy 79), a Teleporter
  odpowiadał odmową 26 000 razy na minutę — bo odczekanie z 1.30.42 ustawiało
  zegar, którego gałąź wyjazdu na pogranicze nigdy nie czytała, a powyżej
  pułapu Bokjung bot nie miał prawa polować, więc nie miał z czego zapłacić.
  Teraz: (1) po odmowie bot naprawdę czeka pięć minut; (2) bot bez opłaty
  nie idzie do Teleportera, tylko poluje w Bokjung, aż uzbiera trzy opłaty
  (status „Zbieram yang na Teleporter”); (3) kowal, zmiana bonusów, targ,
  reset umiejętności i Zwój Zapomnienia zostawiają w sakiewce trzy opłaty
  dla bota, którego łowisko leży za Teleporterem — to wydawanie wszystkiego u
  kowala po powrocie z pogranicza robiło z botów nędzarzy.

---

## 1.31.2 — 2026-09-09

### Panel zaawansowany

- **Panel Sebana 1.40.0** (z 1.38.5): zwijany poradnik aktualizatora na
  VPS w Zarządzaniu, motywy dziedziczone przez tabele i kafelki, ikony
  przedmiotów w bazie, flagi i nazwy królestw, portrety klas w profilach,
  listach i rankingach, kreator GM z wyborem płci. Nasze poprawki nałożone
  na nowo: Świątynia Hwang i Loch Pająków V2 w nazwach, granicach i
  respawnach, przełącznik „Noc na serwerze”, ranking broni z właściwymi
  kolumnami średnich i umiejętności (71/72), restart bez helpera Sebana,
  panel startowy bez błędu w pierwszych minutach świeżej bazy.

- **Opis „Szybkie czytanie ksiąg” mówi to, co robi kod** (Kenny: „na stronie
  jest co pół godziny, w kodzie czyta od razu”). Od 1.30.30 bot czyta księgę
  od razu, gdy ją ma; jedyny hamulec to sama gra — 20 000 doświadczenia i
  rzut przy każdej lekturze. Opis w obu panelach poprawiony.

---

## 1.31.1 — 2026-09-09

> **Ta aktualizacja jest mocno eksperymentalna.** ItemShop i panel GM to
> nowe, obce nam systemy (autor: OskarPWA) spięte z naszym stosem w jeden
> wieczór. ItemShop jedzie do każdego w zwykłej aktualizacji serwera (bez
> zmian w kliencie). Panel GM na F9 wymaga podmiany plików klienta i jest
> **opcjonalny**: instaluje go osobny przycisk launchera „PANEL GM F9
> (TEST)”, po ostrzeżeniu, z kopią zapasową poprzednich plików. Zwykła
> aktualizacja („SPRAWDŹ AKTUALIZACJE”) nie dotyka klienta.

### Panel GM (F9) i klient

- **Panel GM na F9 oraz przyciski EQ/Sprawdź w menu postaci** (autor:
  OskarPWA). Serwer: 21 komend `gmpanel_*` scalonych z naszym rdzeniem
  (`cmd_gm.cpp`, `cmd.cpp`, łatka 0009 dla instalacji linuksowych), każda
  sprawdza poziom GM po stronie serwera; „Spawn Botów” korzysta z naszego
  `CPlayerBotManager` (nowa metoda `GetAvailableBots`). Klient: cztery pliki
  (`game.py`, `interfacemodule.py`, `uitarget.py`, `constinfo.py`) w
  `pack/root.epk` — przepakowane narzędziem `tools/eterpack.py` (własny
  czytnik i zapis archiwów `.eix/.epk`, klucze stockowe r40250, weryfikacja
  obiegu: 90 plików, różnią się dokładnie 4 podmienione). Aktualizacja
  klienta jedzie jako składnik `client` manifestu i launcher nakłada ją na
  folder klienta. Panel otwiera się klawiszem F9 tylko postacią GM.

### Loch Małp i medale

- **Więcej wypraw po Medal Konny** (na rynku jest ich za mało). Bot z koniem
  bojowym miał 1–4% szansy na wyprawę w każdym półgodzinnym oknie, a to
  właśnie boty 46+ z takim koniem chodzą do trudnego lochu, gdzie medal
  wypada im z pełną szansą. Szansa po koniu bojowym potrojona (wojownik i
  sura broni 12%, sura magii, ninja sztylet i szaman 6%, łucznik 3%);
  przed koniem bez zmian. Pasma bez zmian: łatwy do 32, średni 33–45,
  trudny od 46.

### Naprawy z paczek graczy

- **Koń nie jest dosiadany i zsiadany co sekundę przy Metinie** (Kuszaa,
  botgrom2 w Lochu Pająków: „mounted_combat” i „near_destination” na zmianę,
  sto par na minutę). Przejście celowania dosiada konia bojowego do walki, a
  marsz, który przyprowadził bota pod kamień, zsiadał, bo koniec trasy był
  blisko. Marsz nie zsiada, gdy bot ma cel, z którym może walczyć z siodła.

- **Straganiarz z pogranicza nie jedzie z towarem do Joan** i spacer z
  towarem ma własny status „Ide z towarem na targ w Joan” (Kuszaa: botgrom2
  ze statusem „Ide na Gore Sohan” jechał do bramy M1). Bot, którego miejsce
  jest na pograniczu, przy pełnym Bokjung czeka zamiast iść do Joan.

- **Launcher GUI nie wysypuje się przy „Zainstaluj/Przygotuj”** (Uxie:
  „The property 'Count' cannot be found on this object”). Przy niekompletnej
  paczce lista brakujących plików była pojedynczym tekstem, a tryb ścisły
  PowerShella nie zna `.Count` na tekście. Teraz pokazuje komunikat
  o niekompletnej paczce, tak jak miał.

### Ulepszanie

- **Od +7 bot używa Zwoju Boga Smoków, gdy go ma**, zamiast Zwoju
  Błogosławieństwa (oba działają bez kowala — przejście ze zwojem chodzi
  tam, gdzie bot stoi). Uwaga do faktów silnika (`char_item.cpp`): Zwój
  Boga Smoków ma tu 25% przy +7→+8 i 20% przy +8→+9, Zwój Błogosławieństwa
  40% i 30% (jak u kowala), oba przy porażce cofają o poziom; Podręcznik
  Kowala 30% i 20%. Wybór zgodnie z prośbą, liczby do wiadomości.

---

## 1.31.0 — 2026-09-09

### ItemShop

- **ItemShop w grze** (autor: OskarPWA; wdrożenie jako usługa w naszym
  stosie). Kliknięcie monety na pasku otwiera w wbudowanej przeglądarce
  klienta sklep za Smocze Monety (`account.cash`) i Smocze Znaki
  (`account.mileage`): kategorie Ulepszanie, Bonusy, Koń i pomoc, Za Smocze
  Znaki (17 pozycji na start, do urządzenia przez operatora w bazie
  `itemshop`) oraz koło szczęścia za 10 SM. Zakup trafia do
  `player.item_award`, a rdzeń db dostarcza przedmiot przy najbliższym
  logowaniu. Rdzeń r40250 i klient miały już potrzebne części (komenda
  `in_game_mall` z podpisem, `WebWindow`, mapowanie „mall”) — dochodzi tylko
  usługa `itemshop` (PHP, port `M2_ITEMSHOP_PUBLIC_PORT`, domyślnie 7791) i
  schemat nakładany przez `playerbot-migrate` przy każdym starcie
  (idempotentnie; zasiew tylko do pustego sklepu). Hasło bazy i sekret
  podpisu idą ze środowiska, nie z plików. Adres sklepu (`MALL_URL`) rdzeń
  dostaje z `M2_MALL_URL`, a gdy pusty — z `M2_PUBLIC_ADDRESS` i portu.
  Sprawdzone u nas: podpisany link loguje automatycznie, zły podpis odsyła
  do logowania. Nie ma jeszcze: panelu GM na F9 i przycisków EQ/Sprawdź z
  paczki Oskara (wymagają przepakowania `root.epk` w kliencie), dropu
  Smoczych Monet z metinów i bossów dla botów i graczy, zakupów botów w
  sklepie — to następne kroki.

---

## 1.30.42 — 2026-09-09

### Loch Pająków 2

- **Boty od 54 poziomu chodzą do Lochu Pająków 2** (mapa 71,
  `metin2_map_spiderdungeon_02`). Z wiki i plików serwera: trujące pająki
  60–68 poziomu, które nie atakują pierwsze, bez metinów, na końcu warp do
  V3 i Elitarna Królowa Pająków (97 lvl, 2,6 mln HP — bez hubu, za silna).
  Do lochu wchodzi się u Chuk-Sala na końcu V1 za Przepustkę; boty na razie
  wchodzą bez przepustki, tą samą drogą co do V1: przez pustynię do bramy
  Kuahlo Dong i dalej po stronie serwera. Losowanie pogranicza od 54 poziomu:
  V2, Sohan albo Świątynia Hwang (łowca metinów zamiast V2 idzie na Sohan,
  bo w lochach nie ma kamieni). 11 hubów na prawdziwych punktach spawnu z
  `regen.txt` (668 punktów przez `group.txt` i `group_group.txt`), punkty
  przybycia (384,273) i wyjścia sprawdzone na `server_attr` (81/81 wolnych
  komórek, cała mapa to jeden spójny obszar). Mapa 71 przeniesiona na rdzeń
  game1, dodana do listy dozwolonych w `apply.sh`, do obu paneli (nazwa,
  granice, kafelek terenu).

### Ekonomia

- **Bot nie ulepsza tego, co za chwilę sprzeda handlarzowi** (jaksiezabic:
  Ametystowy Naszyjnik+0 → +1 o 17:58, sprzedany handlarzowi o 18:19; u nas
  w 6 godzin 12 534 przedmioty ulepszone w plecaku i potem sprzedane).
  Przejście ulepszania brało z plecaka każdy przedmiot, który bot może
  założyć, a reguła złomu sprzedawała każdy, który nie jest lepszy od
  noszonego i ma mniej niż +6. Teraz z plecaka ulepszane jest tylko to, co
  bot zatrzyma: ulepszenie noszonego, przedmiot wyższego poziomu niż noszony
  w tym slocie (nowa reguła — najlepszy taki zapas na slot zostaje w
  plecaku, żeby kowal mógł go doprowadzić do stanu lepszego od noszonego),
  rezerwa od +6.

- **Przedmiot od +4 nie idzie do handlarza** — to towar na stragan (stragan
  wystawia od +4), a handlarz brał każdy +4 i +5 (gregory: Szata Zach.
  Nieba+4, Złote Buty+4 sprzedane zaraz po ulepszeniu).

- **Materiał, na który jest popyt, nie idzie do handlarza** (gregory: Ogon
  Skorpiona, Worek z Pajęczymi Jajami, Igła Skorpiona sprzedane handlarzowi,
  podczas gdy boty kupują Ogon Skorpiona na straganach po 58 894). Reguła
  złomu pyta ledger rynku: materiał z popytem to towar na stragan; do
  handlarza idzie tylko taki, którego nikt nie potrzebuje, i tylko pod
  presją plecaka.

### Panel

- **Ranking botów pokazuje do 1000 pozycji** (Iwakura: „poproszę żeby mogło
  pokazywać więcej niż 100”). Selektor ma 200/500/1000, a API przestało
  ucinać do 100.

### Podróże

- **30% botów wraca z pogranicza po usługi do Joan, nie do Bokjung**
  (jaksiezabic: „M1 przy 1000 botów wygląda jak Balmora, a M2 jak Baerim”).
  Dotąd każdy powrót po zapasy, do kowala czy handlarza szedł do Bokjung.
  Udział wybierany raz na bota (po pid); Joan ma wszystkie usługi, kosztem
  jest powrót przez Bokjung do Teleportera. Medal, polowanie na broń i
  wyrośnięcie z mapy nadal prowadzą do Bokjung. W logu:
  `frontier_services_to_m1`.

---

## 1.30.41 — 2026-09-09

### Stragany i podróże

- **Limit straganów na Bokjung rośnie z liczbą botów.** Poprawka z 1.30.40
  trzymała tylko pierwszą serię: po restarcie wszyscy straganiarze otwierali
  w tym samym ticku (licznik odświeża się co minutę), a potem każde ponowne
  otwarcie odbijało się o limit 7 straganów na Bokjung — 229 odmów na minutę
  — i bot szedł z towarem do Joan, gdzie planista wysyłał go po zakupy
  zamiast na plac. Z 90 straganów po półtorej godziny zostało 28 (6 na
  Bokjung, 21 w Joan). Limit to teraz 8% żywych botów, nigdy mniej niż 7:
  80 dla tysiąca, 28 dla 350.

- **Bot bez yangów na Teleporter nie pyta go co tick.** Bot 58 poziomu z 799
  yang wobec opłaty 11 000 był odrzucany 24 000 razy na minutę, a jego status
  brzmiał „Ide na Gore Sohan” (Kuszaa: boty, które chcą na Sohan, kręcą się
  po Bokjung). Po odmowie podróż czeka 5 minut, w tym czasie działa wizyta w
  mieście i stragan, które zarabiają opłatę; status mówi „Zbieram yang na
  Teleporter na Gore Sohan (799/11000)”.

### Launcher

- **`playerbot-syslog.txt` w paczce diagnostycznej nie jest już pusty** (Kuszaa,
  1.30.40). Windows PowerShell 5.1 owija argument natywnego polecenia w
  cudzysłowy, nie escapując tych, które już w nim są — pierwszy cudzysłów
  wewnątrz polecenia `sh -c` kończył argument i wycinek wychodził pusty.
  Polecenie nie ma już żadnego cudzysłowu w środku (wzorce przez `grep -e`).
  Sprawdzone u nas: 60 000 linii, ~6 MB.

---

## 1.30.40 — 2026-09-09

### Stragany

- **Stragany nie znikają godzinę po restarcie** (jaksiezabic: „na 1000 botów
  11 sklepów 1 h po restarcie, 5 min po restarcie 50–100”; Oskar: liczba
  sklepów co jakiś czas spada do zera). Odtworzone u nas: 94 straganiarzy
  10 minut po restarcie, 33 po 25 minutach, bez żadnego restartu. Mechanizm:
  stragan stał 10–25 minut, po zamknięciu bot dostawał 30–90 minut przerwy,
  a ponownie otwierał dopiero po zakończeniu następnej wizyty w mieście —
  więc po restarcie (każdy straganiarz stoi tam, gdzie miał stragan) otwierali
  wszyscy naraz, a potem wygasali szybciej, niż wracali. Teraz stragan, który
  wygasł, otwiera się ponownie na tym samym miejscu (nowa wycena, nowy szyld,
  towar z plecaka), do 3 stanowisk z rzędu; dwa stanowiska z rzędu bez żadnej
  sprzedaży kończą serię wcześniej. Dopiero po serii bot bierze 30–90 minut
  przerwy i idzie grać. W logu: `PLAYERBOT_SHOP: another stand`.

### Launcher

- **Paczka diagnostyczna niesie log podróży botów.** Do kontenera trafia
  tylko syserr, więc paczka wysłana o „boty idą do złego portalu” (Kuszaa)
  nie miała ani jednej linii o tym, dokąd bot chciał iść. DIAGNOSTYKA dokłada
  teraz `playerbot-syslog.txt` (przejścia między mapami, portale, nawigacja,
  watchdog, cele, stragany, miasto, koń, Loch Małp — tylko linie botów, bez
  czatu graczy) i `playerbot-status.tsv` (aktualny status każdego bota).

---

## 1.30.39 — 2026-09-09

### Broń

- **Pomiar broni per klasa: procenty średnich i umiejętności mnożą obrażenia
  broni** (Iwakura: bot z Łukiem z Rogu Jelenia+8 151–244 i +47% średnich w
  plecaku nosił Miedziany Łuk+4 90–156). Dotąd linia procentowa była
  płaską sumą kilku tysięcy obok miliona za obrażenia. Teraz obrażenia broni
  (fizyczne dla wojownika/ninji/sury broni, magiczne dla szamana i sury
  czarnej magii; sztylet i łuk ×2 jak w silniku) są mnożone przez
  `100 + średnie·waga + umiejętności·waga`: build zwykłych ciosów czuje
  100% linii średnich i 35% umiejętności, build umiejętności odwrotnie.
  Ujemne linie (np. −17% umiejętności) liczą się tak samo. Broń na 30 i 75
  poziom z liniami nagrody wygrywa z „miedzianym” bez nich o tyle, o ile
  naprawdę bije mocniej.

- **Lepsza broń w plecaku jest zakładana także w ciągłej walce.** Silnik
  odmawia założenia w 1,5 s po ataku lub czarze, a bot, który nie przestaje
  atakować, nigdy nie miał okna — na teście 247 z 970 botów nosiło broń o
  ⅓ słabszą od tej w plecaku. Dotąd pauza w walce była tylko dla pustego
  slotu; teraz dla każdego lepszego przedmiotu (do 5 s, najwyżej raz na
  minutę, gdy okno nie przyszło). Drugi powód: przejście ekwipunku siedziało
  na końcu ticku, za straganem, lootem, koniem, wędkowaniem, podróżą i
  wędrówką, z których każde przejmuje tick — bot ciągle czymś zajęty nie
  zaglądał do plecaka wcale (wojownik 28 lvl bił Mieczem+6 z 1 poziomu mając
  Długi Miecz+4 w plecaku). Przejście uruchamia się teraz na początku ticku,
  poza otwartym straganem, wizytą w mieście, wędkowaniem i stajnią.

- **Broń z linią nagrody nie idzie na kowadło bez Zwoju Błogosławieństwa**
  (Oskar: „51% i spalił u kowala”). W tym silniku każde nieudane ulepszenie
  niszczy przedmiot (nie ma progu +3), a szanse od +5 to 80/60/50/40/30%.
  Broń ze średnimi ≥ 20% albo umiejętnościami ≥ 15% bot ulepsza tylko pod
  zwojem (nieudane = poziom niżej, nie strata), a bez zwoju czeka. To samo
  dotyczy każdego przedmiotu, który ma już 5 linii bonusów.

- **Wzmocnienie Przedmiotu i Zaczarowanie dopiero od +4.** Bot nie wydaje
  kamieni na przedmiot poniżej +4 — najpierw ulepszenie (i ryzyko spalenia),
  potem bony.

### Panel i launcher

- **Panel klasyczny (7788) pokazuje wersję, którą naprawdę ma** (azzyl5021:
  „Masz uruchomioną 1.29.0. Dostępna jest 1.30.38”, mimo aktualizacji i
  przebudowy panelu). Plik VERSION i CHANGELOG do obrazu panelu kopiował tylko
  `start-server.ps1` — za wczesnym `return` gałęzi `-IdentityOnly`, którą
  wywołuje launcher przed własnym `docker compose up --build`. Kliknięcie
  GRAJ/AKTUALIZUJ nigdy tam nie docierało, więc obraz panelu był budowany ze
  starym VERSION i przebudowa nic nie zmieniała. Launcher kopiuje teraz
  VERSION, CHANGELOG, `admin_panel.py`, `items.json`, schemat i questy panelu
  do kontekstu budowy w tym samym miejscu, w którym kopiuje źródła botów.

- **Panel zaawansowany (7790) pokazuje wersję z pliku VERSION.** Dotąd brał
  ją z `M2_PLAYERBOTS_VERSION` w `.env` (którego nikt nie ustawia) albo z
  domyślnej w `docker-compose.yml`, która stanęła na 1.30.29. Launcher i
  `start-server.ps1` przekazują ją z VERSION przez środowisko procesu (compose
  czyta je przed `.env`; sam `.env` nie jest dotykany), a domyślna w compose
  podniesiona do 1.30.39.

- **Logi na żywo bota pokazują tylko tego bota** (szubartov: przy „botgrom”
  były też linie botgrom2…botgrom6). Filtr dopasowywał nazwę jako fragment
  linii; teraz dopasowuje całe słowo — nazwa w logu silnika jest ograniczona
  spacją, `=`, `:` albo końcem linii, nigdy własną cyfrą.

---

## 1.30.38 — 2026-09-09

### Z kanału propozycji

- **Historia ekwipunku bota w panelu klasycznym** (Iwakura: „czemu moja top1
  sura nagle nie ma FMS-a +8, tylko lata z useless bronią”). Na stronie
  postaci, nad dziennikiem na żywo, sekcja „Historia ekwipunku” czytana z
  `log.log`: ulepszenia udane i nieudane, spalone przedmioty, założenia (co
  i zamiast czego), prezenty dla innych botów i od nich, sprzedaż na
  straganie (ile i za ile), zakupy na straganach, sprzedaż handlarzowi,
  kamienie zużyte na przemianę bonusów, depozyty do magazynu, Szkatułki
  Blasku. Domyślnie 60 ostatnich wpisów, przycisk „Pokaż starsze” — 400.
  Rdzeń dopisuje do `log.log` to, czego silnik sam nie zapisywał: założenie
  (`PLAYERBOT_EQUIP`), obie strony prezentu (`PLAYERBOT_GIFT_OUT/IN`),
  sprzedaż na straganie po stronie sprzedawcy (`PLAYERBOT_STALL_SOLD`) i
  depozyt u Dozorcy (`SAFEBOX PUT`, jak silnik dla gracza).

---

## 1.30.37 — 2026-09-09

### Zmienione

- **Plecak zapełniony w 80% to sprawa do załatwienia, nie stan do polowania**
  (Iwakura: „eq pełne od dawna, a on napierdala 2 godziny małpy po medal,
  który nie mieści się do eq”). Od 72 z 90 pól: żadna wyprawa po drop nie
  rusza — ani do Lochu Małp po medal (bot już w środku kończy medal i
  wychodzi; dropek medali też), ani do M3 po broń — a w mieście bot ma co
  robić: otwiera stragan niezależnie od osobowości (nawet z jedną linią, bez
  wyprzedażowej zniżki), księgi ponad zapas niesie do Dozorcy, złom do
  handlarza, materiały zużywa u kowala. Zbieracz ekwipunku, który nie odda
  zapasowych +8 handlarzowi, wystawia je na ladę.

- **Bramy brane z mapy, Teleporter za opłatą** (Kuszaa, nadal na 1.30.36:
  bot dojeżdża pod portal M1, zawraca i krąży). Punkt bramy nie jest już
  stałą z `npc.txt`: bot szuka na swojej mapie żywego NPC-warpa, którego
  cel (z nazwy NPC, tak jak czyta ją silnik) leży na docelowej mapie, i
  idzie do niego — więc gdy paczka serwera stawia bramę gdzie indziej, bot
  trafia tam, gdzie brama stoi. Do M3 prowadzi teraz brama Waryong, nie
  Teleporter. Teleporter (9012) działa jak dla gracza: od 11 poziomu, za
  `floor(poziom/5)·1000` yang (min. 1000) — bot bez pieniędzy nie
  teleportuje się. Zawieszony marsz do portalu trafia też do `syserr`, więc
  będzie w paczce diagnostycznej.

- **Stragan bez pola na pakiet scala stosy zamiast się poddawać.** Bot z
  plecakiem 90/90 nosił 12 małży w 12 polach: skan straganu pociął je na
  pojedyncze linie, stragan nie otworzył się z braku pola na pakiet, a
  scalanie czekało na zamknięcie, które nigdy nie nastąpiło.

---

## 1.30.36 — 2026-09-09

### Instalator i launcher (raport Sykesa)

- **Brak zrzutów SQL po przygotowaniu paczki kończył się „database not ready
  after 30 minutes”.** Instalator sprawdzał tylko, czy katalog
  `mariadb/initdb.d/dumps` istnieje, launcher nie sprawdzał go wcale; MariaDB
  startowała pusta i zgłaszała „healthy”, a `playerbot-migrate` czekał 30
  minut na schemat, którego nie było — prawdziwy błąd leżał w logu MariaDB.
  Teraz pięć plików (`account`, `common`, `player`, `log`, `hotbackup.sql`,
  cztery pierwsze niepuste) sprawdza **przed** `docker compose up`:
  instalator (`Test-ContextComplete`, z listą brakujących), `start-server.ps1`
  i ścieżka GRAJ w launcherze (obie — bo to dwie różne drogi do builda), oraz
  przycisk przygotowania paczki w GUI. Instalacja z już zainicjalizowaną bazą
  nie jest wstrzymywana (zrzuty czyta się tylko przy pierwszym starcie).
  Komunikat mówi, skąd wziąć zrzuty (`Server\metin2_mysql_dump.zip` z paczki
  r40250, `$env:M2_SRC_ARCHIVE` dla instalatora).

- **`playerbot-migrate` rozróżnia trzy czekania.** Zamiast jednego „still
  waiting for the database”: „MariaDB odpowiada, ale nie ma ŻADNEJ z tabel
  r40250 — baza zainicjalizowała się bez zrzutów, czekanie tego nie naprawi”,
  „import pierwszego startu w toku: X/8 tabel” albo „baza jeszcze nie
  odpowiada — duży świat odzyskuje się dłużej”.

---

## 1.30.35 — 2026-09-09

### Naprawione

- **„Bot, który chce iść na Sohan, kieruje się do portalu M1, zawraca i
  robi kółko wokół M2” (Kuszaa), „boty do łatwego lochu małp też jadą
  najpierw do portalu M1”.** Skutek 1.30.34: straganiarzem stał się każdy
  bot z ≥6 nadmiarowymi księgami, a pas straganu — który biegnie w ticku
  przed podróżą między mapami — gdy ring w Bokjung jest pełny (7 straganów),
  prowadził każdego straganiarza z towarem do portalu M1, „żeby otworzyć
  stragan w Joan”. Na serwerze z pełnymi plecakami ring jest pełny zawsze,
  więc setki botów z celem na pograniczu były co tick zawracane do portalu
  M1. Do Joan z towarem idzie teraz tylko kupiec albo dropek z osobowości,
  i tylko bez zaplanowanego wyjazdu; reszta czeka 10 minut na wolne miejsce
  na ringu i podróżuje tam, gdzie chciała.

- **„Boty nie wychodzą z lochu małp — zatrzymują się tuż przed portalem i
  zawracają” (Sekuras).** Bot stojący dokładnie na środku pola, z którego
  następny odcinek trasy „ociera się” o róg ściany: planer (siatka
  statyczna) ten odcinek zaplanował, test na żywo (supercover) go odrzuca —
  i odrzuci identycznie przy każdym ponownym planowaniu. Do 1.30.33 bot
  stał tam po cichu (reset watchdoga co 90 s); od 1.30.34 zjadał punkt pod
  nogami i przez gałąź „odcinek zasłonięty” planował w kółko, aż marsz do
  portalu poddawał się i bot zawracał. Trzeci ratunek: gdy oba końce są już
  środkami pól, a rogu nie da się ominąć, bot idzie tym odcinkiem — serwer
  prowadzi bota po prostej bez kolizji, więc najwyżej otrze się ramieniem o
  dekoracyjny róg. W logu `PLAYERBOT_NAV: forced through a grazed corner`,
  w linii watchdoga `nav_out=12`.

- **„Boty kupują więcej niż jedną wędkę — tyle, ile mają miejsca w eq”
  (FanFar).** Silnik ulepsza wędkę w trakcie łowienia (rzut przy każdym
  połowie, Wędka+1 staje się nowym przedmiotem Wędka+2 itd.), a warunek
  „mam wędkę” liczył wyłącznie vnum Wędki+1 — po pierwszym ulepszeniu bot
  kupował nową co sesję. Liczy się teraz każda wędka w plecaku, do ręki idzie
  najlepsza, a wędki zapasowe (słabsze lub równe innej) bot sprzedaje
  handlarzowi przy najbliższej wizycie.

---

## 1.30.34 — 2026-09-09

### Zmienione

- **Księga umiejętności nigdy nie trafia do handlarza.** Zapas własnych ksiąg
  zostaje w plecaku, nadmiar — cudze klasy i własne ponad zapas — jest towarem
  na stragan, a to, czego plecak pod presją nie mieści ponad 12 ksiąg towaru
  (dropek metinów: 20), bot zanosi do **Dozorcy** i wkłada do magazynu
  (jedna strona, 45 pól) — każdy bot do własnego, na koncie `playerbot_NNN`
  (deskryptor bota dostał wreszcie id konta; dotąd miał 0). Jak gracz: za
  pierwszym razem płaci Dozorcy 500 yang za stronę, otwiera magazyn tylko
  stojąc przy nim; PIN-u nie ustawia, bo silnik przyjmuje domyślne „000000”
  dla konta bez hasła. Nowy etap wizyty w mieście, w Joan
  i w Bokjung; status „Ide do magazynu z ksiegami” / „Oddaje ksiegi do
  magazynu”. Pełny magazyn zostawia resztę w plecaku jako towar — do
  handlarza nie idzie nic. Reguła z 1.30.33 („nadmiar ponad 20 ksiąg do
  handlarza”) wycofana.

- **Skill, który nie wszedł na M — Księga Zapomnienia powyżej 30 poziomu.**
  Bot nie wkłada punktów ponad 17 od 1.30.2x; do 30 poziomu resetuje skille
  u Starszej Pani, a powyżej miał używać Księgi Zapomnienia z rynku — której
  nikt w tym świecie nie sprzedaje ani nie dropi, więc skill stał na 17 do
  końca życia (81 botów nosiło 18–19 sprzed ograniczenia). Bot powyżej 30 lv
  kupuje księgę jak w sklepie itemowym (200 000 yang prosto do plecaka, przy
  zapasie 300 000), sparowaną ze skillem, i od razu ją czyta: jeden punkt
  z powrotem, kolejny rzut na M przy 17. Księga wystawiona na czyimś
  straganie też jest kupowana. Poniżej 30 lv Starsza Pani jak dotąd.

- **Stragany: kto ma nadmiar ksiąg, ten handluje; materiały w pakietach;
  scalanie zaraz po zamknięciu** (Oskar, jaksiezabic: „21 sklepów na 1000
  botów, na nich kilka KU, a boty latają po metinach z pełnym eq”). Los
  osobowości wybierał jednego bota na dziesięciu, a księgi leżały u
  pozostałych dziewięciu. Teraz każdy bot z co najmniej 6 nadmiarowymi
  księgami (cudzych klas albo własnych ponad zapas do czytania) otwiera
  stragan niezależnie od losu — bez czekania na pełny plecak, bo na świecie
  pełnych plecaków każdy by się kwalifikował, a na świecie półpustych nikt.
  Materiały (ości, skóry, talizmany…) idą na ladę w pakietach po 2, do 8
  linii jednego rodzaju — 16 ości to osiem linii po 2, nie jedna po 16;
  perły i małż pojedynczo, mikstury/zwoje/kamienie jak dotąd po 1. Po
  zamknięciu straganu bot scala stosy po 5 s, nie po 5 minutach, i wraca po
  kolejną porcję, dopóki jest co scalać. Cena małża (ok. 100 tys.) to
  celowo dziesiąta część oczekiwanej wartości pereł w środku — nie zmieniam.

### Naprawione

- **Marsz do Handlarki Różności w Bokjung „nieosiągalny” — 260 ratunków
  serwisowych dziennie.** Punkt podejścia do handlarki (141300, 240400) leży
  na pasku gruntu odciętym od placu w `server_attr`; planer odpowiadał
  „unreachable” trzy razy, a szósta porażka przenosiła bota. Etap wizyty
  sprawdza teraz osiągalność celu i, gdy cel leży na cudzym terenie, idzie
  do najbliższego pola własnego terenu w promieniu przybycia — tam, gdzie
  ratunek i tak by go postawił, bez sześciu nieudanych planów.

- **Bot stojący na własnym pierwszym punkcie trasy stał w nieskończoność.**
  16 z 18 resetów watchdoga po południu to `nav_out=11` (Goto odrzucone)
  przy `route=0/2` na środku pola: bot stał dokładnie na punkcie 0, następny
  odcinek był zasłonięty z jego dokładnej pozycji, pętla zjadania punktów nie
  zjadała punktu 0 („najpierw dojdź do środka pola” — a już tam był), Goto
  odmawiało ruchu w to samo miejsce, a marsz meldował „idę”. Jeden bot stał
  tak 20 minut przy kowalu w Joan. Punkt, na którym bot stoi, jest zjadany;
  zasłonięty odcinek idzie przez gałąź z ratunkami i licznikiem utknięcia.

### Świątynia Hwang

- Pomiar całego `regen.txt` (407 spawnów przez `group_group`): trzy komórki
  po 800–1200 spawnów bez huba w promieniu 19 km — południowo-wschodni róg,
  ziemia na wschód od środka i polana żab na północ od wejścia. Cztery nowe
  huby (każdy sprawdzony w `server_attr`), więc boty obiegają całą
  świątynię, nie tylko zachodnie i wschodnie pasmo.
- **Boss: Zjawa Żółtego Tygrysa** (1304, 75 lv, 178 040 HP, co 2 h z
  `boss.txt`, przy (575000, 93200) z dwoma Ropuszymi Generałami i dwoma
  Drzewnymi Żabimi Przywoływaczami) ma hub bossa jak Królowa Pająków i
  Dziewięć Ogonów: wyprawa grupy od 55 lv, pełna grupa może wyzwać 75,
  a po trzech wyruszających boss wyprzedza żaby wokół niego. Wejście do
  Wieży Demonów (Strażnik przy (590800, 110800)) stoi na ziemi bez spawnów,
  więc huba tam nie ma — boty przechodzą obok, idąc do środkowego huba.

---

## 1.30.33 — 2026-09-09

### Naprawione

- **Łucznicy zamarzali na punktach przybycia — na pustyni, w M3, w Dolinie
  Orków — na dwadzieścia minut i dłużej.** Znalezione w obserwacji po 1.30.32:
  dwanaście botów resetowanych przez watchdoga co 90 s, wszystkie łuczniczki.
  Każda miała w plecaku wyłącznie strzały ponad swój poziom (skrzynia
  postępu daje 8003 na 40 poziom botowi na 34, 8004 na 45 botowi na 41) i
  nic w slocie strzał. Licznik strzał liczył je jako zapas („sto strzał, nie
  trzeba kupować”), a łuk nie miał czym strzelać: przygotowanie broni
  zawodziło co tick i tick wychodził przez wizytę w mieście, której na mapie
  bez handlarza nie da się zacząć. Strzały ponad poziom nie liczą się do
  zapasu; bot bez strzał na mapie bez handlarza rusza do miasta przez zwykłą
  podróż między mapami, a gdy ta nie ma nic do powiedzenia — przynajmniej
  wędruje. Linia watchdoga mówi teraz, na czym tick stanął
  (`equip_pending`, `service`, `riding`, `nav_out`, `wander_in`).

- **Slot tarczy nie jest „brakującym slotem” dla łuku ani broni dwuręcznej.**
  Ta sama obserwacja: każdy łucznik był na stałe „w krytycznej potrzebie
  usług miasta”, więc z M3 wychodził w chwili przyjścia, a polowanie na broń
  30 odsyłało go z powrotem — piętnaście sekund na okrążenie. Do tego pauza
  „czekam na okno ekwipunku” dostała limit 5 s zamiast nieskończoności.

- **„Dropek metinów” z plecakiem pełnym ksiąg nie sprzedaje ich i nic nie
  podnosi (Sekuras).** Osobowość trzyma każdą księgę dla swojego straganu, a
  gdy los na stragan nie wypadł, trzymała je w nieskończoność: 80 ksiąg, brak
  miejsca na łup, bot dalej rozbija metiny. Pod presją plecaka dropek otwiera
  stragan niezależnie od losu, a to, co i tak nie mieści się ponad dwadzieścia
  ksiąg, sprzedaje handlarzowi. Księgi cudzych klas u każdego bota pod presją
  plecaka też idą do handlarza zamiast blokować łup.

- **„Bot z koniem na 10 poziomie krzyczy »idę do stajennego« i jeździ w kółko
  godzinę” (CarloMontana).** Bot nie jechał do stajennego — napis kłamał.
  Każdy bot w podróży z medalem w plecaku ogłaszał stajennego, a medal, którego
  nie da się oddać, zostaje w plecaku na długo: koń na 10 czeka na 35 poziom
  postaci, dropek medali nosi je na stragan. Napis mówi teraz o stajennym tylko
  wtedy, gdy bot naprawdę może oddać medal; bot w próbie konia bojowego pisze
  „Zdobywam konia bojowego na pustyni (x/100)”, a odbiór konia bojowego ma
  własne linie. Status u stajennego w Bokjung mierzył odległość do stajennego
  w Joan, więc oddawanie medalu w Bokjung wyglądało jak marsz. Przy okazji
  marsz do stajennego dostał przyciąganie celu w promieniu przybycia (6 pól
  zamiast 20), tak jak wcześniej wizyta w mieście i marsz do portalu.

### Z kanału propozycji

- **Noc na serwerze (Oskar).** Rdzeń między 22:00 a 05:59 czasu serwera
  (`M2_TZ` z `.env`) podnosi flagę `xmas_snow` — tę samą, którą GM ustawia
  komendą `/xmas_snow 1` — i rano ją opuszcza; klient pokazuje wtedy nocne
  niebo i, bo to flaga świąteczna, śnieg. Flaga idzie przez rdzeń bazy i wraca
  rozgłoszona do wszystkich klientów, sprawdzana raz na minutę. Przełącznik
  „Noc na serwerze” jest w obu panelach (Boty → Zachowanie na żywo; domyślnie
  włączony); po wyłączeniu w środku nocy rdzeń opuszcza flagę sam. Ręczne
  `/xmas_snow` GM-a działa jak dotąd, gdy przełącznik jest wyłączony.

### Obserwacja po 1.30.32 (serwer testowy, 970 botów)

Portale: 0 zablokowanych marszów, 0 nieudanych przejść, 1 400 przejść między
mapami w 36 minut. Cel bez migotania, tick 7–11 s z każdych 60. Jedyny
problem to zamrożeni łucznicy wyżej.

---

## 1.30.32 — 2026-09-09

### Z kanału propozycji

- **Przejrzyste nazwy sklepów (Xewi, Mat).** Szyld mówi, jaki to sklep,
  zamiast wypisywać nazwę pierwszego przedmiotu. Stragan, na którym
  większość to księgi, nazywa się np. „Ksiegi umiejetnosci”, „KU dla kazdej
  klasy”, „Biblioteka - ksiegi”; z przewagą materiałów — „Ulepki z M1/M2”,
  „Materialy do kowala”, „Skory, zeby i kly”; mieszany — jeden z ośmiu
  okrzyków targowych losowanych po bocie: „Zobacz kotku co mam w srodku”,
  „Zaczynam gre, kup cos”, „<nazwa> - najnizsze ceny”, „Wszystko za grosze”,
  „Tanio jak barszcz”… Szyldy z nazwą przedmiotu zostają tam, gdzie po ten
  przedmiot idzie się przez cały rynek: broń na 30 poziom, wysokie ulepszenie.

- **Nadmiar okazów biologa na stragan (Xewi, Oskar).** Okaz, którego
  zadanie bot już oddał, przestaje być „postępem zadania” i staje się
  towarem — kwiaty, korzenie, bez, grzyby idą na ladę. Zęby orka to także
  materiał do ulepszania, więc — jak zauważył Oskar — trafiają na rynek
  przez zwykłą regułę materiałów i księgę popytu, a nie pod biologa.
  Kamień duszy nigdy nie jest nadmiarem (klucz do drugiej połowy zadania).

- **Wyprzedaż biednego bota (Oskar, dziewięć głosów).** Bot od 20 poziomu,
  którego nie stać na wyprawę po mikstury (300 czerwonych i 200
  niebieskich po cenach handlarki — ok. 12 tys. yang, od 40 lv ok. 25 tys.),
  otwiera stragan niezależnie od losu osobowości, nawet z jedną linią, po
  70% ceny wywoławczej, pod szyldem „Wyprzedaz: …”. W danej godzinie robi
  to jedna czwarta takich botów (losowanie po bocie), więc rynek nie
  zamienia się w tłum biedaków — pierwsza wersja z progiem 30 tys. yang
  postawiła 36 botów 16–19 lv na ringu w Joan w pierwszej minucie.
  Zniżka jest nakładana po wycenie, więc pamięć sprzedaży dalej uczy się
  cen rynku, nie wyprzedaży.

### Naprawione

- **„Za dużo botów kręci się w strefie bezpiecznej” (Dixdros).** Stragan
  w panelu opisywał się „Planuje: poziom” — dla operatora to wyglądało jak
  bezczynny tłum na placu; w świecie bot i tak nosi szyld. Status mówi
  teraz „Prowadze stragan”. Reszta tłumu w Joan to wędkarze, zakupy,
  biolog — z celem, nie bez.

- **„Boty na 9–10 lv biją psy, na 19–20 wilki” (DavidS).** 32 huby
  łowieckie Joan były losowane po numerze bota, bez patrzenia na poziom:
  bot na dziesiątce trafiał do tygrysów na południowym wschodzie, a bot
  na dwudziestce do psów na wschodzie. Zmierzono medianę poziomu potworów
  w promieniu 2500 j. od każdego huba (regen.txt przez group.txt i
  group_group.txt, poziomy z mob_proto — od 1 do 21) i bot wybiera hub,
  którego pasmo (mediana −2 … +7) mieści jego poziom; numer bota dalej
  rozrzuca populację po hubach z pasma. To samo dla ośmiu obozów grup.

### Nie w tym wydaniu

- **Noc na serwerze 22–5:59 (Oskar).** To ustawienie klienta (środowisko
  mapy), nie serwera ani botów — Oskar wprowadził je u siebie po stronie
  klienta. Serwer nie ma czego przełączyć; paczka klienta to osobny temat.
- Suwak respawnów spotów/metinów/bossów (U4NT) — wymaga helpera
  gry z integracji Sebana; grupy z botami, PvP, królestwa (dixdros,
  Remigiusz) — zanotowane na później.

---

## 1.30.31 — 2026-09-09

### Naprawione

- **Boty na mapach frontowych zmieniały cel co pięć sekund: „zapasy” ↔
  „poziom”.** Zgłaszane jako „boty w M2 / na pustyni nie wiedzą, co robić”.
  Dziewięć miejsc w kodzie podróży (przejście przez pustynię, wyjścia z M3
  i z frontu, wyjścia na front, powrót do Joan, wyjścia po biologa, konia,
  sprzęt i polowanie) wpisywało cel w każdym ticku, a planer pięć sekund
  później przywracał swój — zmierzone: **350 botów, 12 000 z
  20 000 linii zmiany celu** w oknie pomiaru, status „Ide do miasta po
  zapasy” i „Ide do Lochu Pajakow” na zmianę u tego samego bota. Podróż nie
  dotyka już celu; decyduje planer. Po poprawce, w takim samym
  oknie na serwerze testowym (970 botów): par „zapasy↔poziom” **0** (było
  5 828), wszystkich linii zmiany celu 1 988 (było 13 766); zostało tylko
  naturalne „przeżyć↔zapasy” przy niskim PŻ.

- **„Boty 30+ zrobiły wymarsz na M3” — 60% serwera na jednej mapie.**
  Zgłoszone ze zrzutem mapy. Reguła z 1.30.29 („każdy powyżej 35 bez broni
  na 30 idzie ją wyfarmić”) była dobra dla świata, którego boty mają
  głównie 50 lv, i katastrofalna dla świata z botami 36–40. M3 przyjmuje
  najwyżej **15% żywej populacji** (nie mniej niż 30), a bot, który już tam
  jest, zostaje, dopóki tłum nie przekroczy półtorakrotności tego progu —
  drzwi nie migają.

- **Bot wracający do Bokjung po sprzęt krążył po spotach za materiałem.**
  Zgłoszone z logiem (Kuszaa): metinowiec 61 lv po zakupach w M2 przez
  siedem minut gonił Jak-To Czarnego Wiatru po materiał do ulepszania,
  zbierając przy okazji przedmioty po innych botach, zanim poszedł do
  teleportera. Wyprawa po materiał nie startuje na mapie, na której bot nie
  ma prawa grindować, ani gdy ma już zaplanowane wyjście.

- **Wędkarze: „zapasy” ↔ „wędkowanie” co pięć sekund.** Ta sama choroba
  w innym miejscu: sesja wędkarska wpisywała cel co tick, planer „zapasy”
  co pięć sekund — 43 wędkarzy, 6 000 linii w 12 minut. Planer respektuje
  trwającą sesję wędkarską. Podobnie wyjście z frontu po zakupy przestało
  wpisywać „poziom”.

- **Bonowanie broni na 30 poziom: aż do średnich ≥ 20%.** Zgłoszone z
  Discorda („boty za rzadko bonują”, „broń 30 z ŚR niżej 20% niech mixują
  aż się uda”). Próg „skończona” dla broni 30 spadł z 30% do 20% średnich,
  a bot przebija ją dopóki tego nie osiągnie — niezależnie od sumy
  pozostałych linii, która wcześniej mówiła „wystarczy” przy 12% średnich.
  Bronie 30 w plecaku (towar na stragan) też są bonowane do tego progu —
  kamień kosztuje czterdziestą część ceny gotowej sztuki. Zwoje z plecaka
  idą pierwsze, dokupywane są dopiero, gdy ich nie ma. Zmierzone przed:
  580 zmian i 123 dodania w 3 godziny na 970 botów.

- **Panel zaawansowany, ranking „Broń 30 lv”: ŚR i UM.** Zgłoszone
  dwukrotnie. Sprawdzone na surowych wierszach bazy: typ 72 niesie średnie
  (do +46), typ 71 obrażenia umiejętności (broń 30 ma je w parze, ujemne —
  stąd „−5%” na zrzutach). Zapytanie nazywa kolumny wprost, bez zamiany po
  fakcie, a sortowanie „według średnich” sortuje według średnich.

### Sprawdzone i nie jest błędem

- **„Wojownicy nie kupują mikstur”.** Zmierzone na 970 botach: wojownicy
  kupują **najwięcej** czerwonych ze wszystkich klas (529 zakupów, 345 tys.
  sztuk, ~650 na wizytę, przychodzą do handlarki ze średnio 130) — i wypijają
  18,8 tys. dziennie. Mają ich mało w plecaku, bo je zużywają, nie dlatego,
  że nie kupują. Sury trzymają 650–740, bo prawie ich nie piją.
- **Pętla konia w M2 i na pustyni (1.30.29)** — to regresja naprawiona w
  1.30.30; logi Kordyla i Kuszaa pochodzą sprzed tej wersji.

---

## 1.30.30 — 2026-09-09

### Naprawione

- **Boty na mapach łowieckich wsiadały i zsiadały z konia co sekundę i nie
  robiły ani kroku na długiej trasie.** Regresja z 1.30.28 („koń biegnie za
  botem"): wędrówka na końcu ticku wsadzała bota na konia na długą nogę, a
  początek następnego ticku zdejmował go bezwarunkowo „do walki" — i każdy z
  tych kroków kasował trasę. Zmierzone na 970 botach: **133 000 wsiadań i
  zsiadań w 28 minut u 261 botów, 6 sekund z każdych 60 sekund ticku** i ani
  jednej przejścia między hubami. To dlatego rajd na Królową Pająków nigdy
  nie dochodził do skutku: 27 decyzji „idę na bossa" i zero botów w promieniu
  trzech kilometrów od niej. Koń transportowy schodzi teraz tylko wtedy, gdy
  jest z kim walczyć (cel albo napastnik), sekcja celu zsiada w ticku, w
  którym cel wybrała, a bufy i wieloprzyciąganie nie ruszają z siodła (silnik
  odmawia umiejętności z konia bez umiejętności konnych). Po poprawce:
  z 4 732 wsiadań na minutę do ~200, tick z 12,1 s na 6–7 s z każdych 60.

- **Boss szukany był w dziewięciu sektorach wokół punktu z tabeli — a Królowa
  Pająków łazi za tymi, którzy ją biją.** Znaleziona 5 km od huba, trzy minuty
  później „powalona" bez żadnego BOSS_KILL w logu, po chwili znów stojąca
  11 km dalej — i każdy rajd był odsyłany do pracy, gdy ona stała. Boss jest
  teraz szukany na całej mapie (jedna migawka bytów mapy, wynik pamiętany
  30 s). Uczciwie: rajd wciąż jej nie zabija — ma 193 408 PŻ i 60 poziom, a
  bierze się za nią 8–10 botów z 48–56 poziomem, które giną lub uciekają
  (59 śmierci od potworów na tej mapie w godzinę). Do przemyślenia liczba
  rajdowiczów; mechanika chodzenia i szukania jest już poprawna.

- **Bot z celem „Metiny" szedł do Lochu Pająków, gdzie kamieni nie ma.**
  Zgłoszone z Discorda ze zrzutem („Ide do Lochu Pajakow (cel: Metiny)").
  Loch Pająków i trzy Lochy Małp nie mają `stone.txt`. Metinowiec z roli
  losuje zamiast Lochu Pająków Górę Sohan, a wyprawa metinowa nie startuje z
  mapy bez kamieni ani w jej stronę (los za godzinę, z miejsca, gdzie bot stoi).

- **Księgi umiejętności zalegały w plecakach.** Zgłoszone z Discorda
  („głównie są to KU, cały dzień nic z nimi nie robią"). Bot trzymał
  dwanaście ksiąg każdej własnej umiejętności — także tej, której czytać
  jeszcze nie może, bo nie ma jej na M. Zmierzone: **2 636 ksiąg w 929
  plecakach, 5 przeczytanych w 3 godziny, 4 sprzedane.** Dwanaście zostaje
  tylko dla umiejętności na M1–M9 (czytelnych teraz), trzy na zapas dla
  reszty, zero dla umiejętności na G; nadwyżka idzie na stragan jak księgi
  cudzych klas, a do handlarza dopiero pod presją plecaka.

- **Stosy w plecaku i pojedyncze sztuki na straganie.** Zgłoszone z
  Discorda: dwa stosy tego samego przedmiotu, których nie da się złączyć.
  Reguła silnika jest jedna — ten sam numer przedmiotu i identyczne gniazda,
  do 200 sztuk — i tylko przeciągnięcie ręką ją uruchamia, którego bot nie
  ma. Bot co pięć minut zlewa swoje rozdzielone stosy (po częściowym zakupie,
  sprzedaży czy podniesieniu do pełnego stosu), a na straganie robi odwrotnie:
  ze zwojów i kamieni duszy odłącza do czterech pojedynczych sztuk na osobne
  linie, bo prywatny sklep sprzedaje linię w całości — dwadzieścia zwojów na
  jednej linii to dwadzieścia albo nic. Materiały zostają w stosach, bo boty,
  które je kupują, kupują stos. U gracza dwóch stosów o różnych gniazdach
  silnik nie złączy nigdy — to nie jest coś, co można naprawić po stronie
  botów.

- **Panel „Loch Pająków" pokazywał 0 widocznych postaci przy 150 botach na
  mapie.** Lista pozycji brała tylko boty z zapisanym `map_index` z listy
  starych map. Filtr mapy w zapytaniu obejmuje teraz każdą mapę z granicami
  (Loch Pająków, oba nowe Lochy Małp, Sohan, Hwang): 846 pozycji zamiast 587.

- **Mikstury: 300 czerwonych i 200 niebieskich na wyprawę, duże od 40
  poziomu.** Pytanie z Discorda „czemu tak mało potek". Handlarka sprzedaje
  duże mikstury (27003/27006) i od czterdziestki bot kupuje właśnie je; zakup
  liczony do pojemności plecaka, nie do zamierzonej liczby.

- **Małże po 7 000 na straganie.** Cena wywoławcza małża ma próg 100 000 —
  jak perły — zamiast trzykrotności ceny handlarza.

- **Ubijanie kamienia.** Bot nie odpuszcza metina poniżej 15% jego PŻ, dopóki
  sam ma powyżej 10%: kamień nie goni, a wracał do pełnego zdrowia.

### Panel zaawansowany 1.38.5 (Seban)

Scalone z tym wydaniem: konto GM z gotową postacią (klasa, punkt startowy),
nazwy przedmiotów w kanale zdarzeń, sezon tygodniowy z właściwych wpisów
logu (`REFINE SUCCESS`, `BOSS_KILL`), przycisk aktualizacji przez nasz
`updater` (profil `update`; panel dostaje wolumen `update-spool` w compose),
ciasteczko sesji osobne od panelu klasycznego. Zachowane nasze poprawki:
Świątynia Hwang (nazwa, granice, kafelek), poprawne ŚR/UM w tablicy bonusów,
odporność na brak migawki systemu na świeżej instalacji. Restart i zapis rat
z konsoli restartu działają bez helpera z `integration/` (którego ten obraz
nie zawiera) — odmawiana jest tylko zmiana respawnów, i panel mówi dlaczego.

### Launcher

- **Dane do bazy (Navicat, HeidiSQL, DBeaver).** Zgłoszone z Discorda
  („1045 - Access denied for user 'root'@'172.18.0.1'"). Nowy przycisk
  **DANE DO BAZY (NAVICAT)** w GUI (akcja `DbAccess`, pozycja 16 w menu
  konsolowym) pokazuje host, port i oba konta z hasłami z `.env` — w polach
  do skopiowania, nie w logu, bo log trafia do paczek diagnostycznych.
  **NAPRAW DOSTĘP DO BAZY** ustawia teraz oprócz konta `metin2` także
  `root@'%'` na hasło z `.env`, więc po nim dane z tego przycisku zawsze
  działają. Opis w README i `docs/INSTALL.md`.

### Spawn

- Kolejność spawnu: najpierw boty grane w ostatnim tygodniu, potem świeże
  (poziom ≤4), potem reszta — suwak podniesiony o 120 daje 120 nowych
  postaci od pierwszego poziomu (zweryfikowane: `registered_started=970`,
  120 botów na 1–10 poziomie po kwadransie).

### Weryfikacja

Cztery pełne przebiegi na serwerze testowym (970 botów): koń, rajd, księgi,
stosy, panel Sebana, akcja DbAccess. Zmierzone przed i po; liczby wyżej.
Paczka aktualizacji sprawdzona pod kątem kompletności (`check-update-covers-build`)
i przeskanowana Defenderem przed publikacją.

---

## 1.30.29 — 2026-09-08

### Naprawione

- **Wędki leżały na ziemi, a wokół stało stado koni.** Zgłoszone z Discorda ze
  zdjęciem i słusznie: to był nasz błąd z 1.30.26. Silnik przy pełnym plecaku
  **kładzie kupiony przedmiot na ziemi i zgłasza sukces** — `AutoGiveItem` nie
  zwraca błędu, tylko `AddToGround`. Nowy zakup wędki tego nie sprawdzał: bot
  płacił, wędka lądowała na trawie, bot nadal jej nie miał i kupował następną.
  Konie wokół to towarzysze wezwani przy zsiadaniu. Kod strzał znał tę pułapkę od
  dawna („rynek wyłożony drewnianymi strzałami") — zakup wędki powstał dzień
  później bez tej wiedzy. Sprzęt wędkarski, drewno na ognisko i mikstury sprawdzają
  teraz miejsce w plecaku **przed** zapłatą; mikstury kupowane są najwyżej do
  pojemności, a nie do zamierzonej liczby.

- **Bot na czterdziestym poziomie „zbierał Korzeń Gango 0/5" do końca świata.**
  Zgłoszone czterokrotnie z Discorda i jako pytanie od operatora. Dwa osobne błędy,
  oba potwierdzone liczbowo.

  W rdzeniu: przejście „noszę okazy" wygrywało z każdym innym i liczyło **jeden**
  okaz. Bot na czterdziestce z jednym Korzeniem Gango z wyprawy wędkarskiej do Joan
  był przypięty do wiersza z piętnastego poziomu na zawsze: wiersz przerośnięty,
  więc nie poluje na tego potwora, więc nigdy nie zbierze pięciu, więc nigdy nie
  odda. Zmierzone: **38 botów na 26+ trzyma korzenie, 36 z nich po jednym do
  czterech sztuk.** Przerośnięty wiersz liczy się teraz tylko wtedy, gdy plecak
  trzyma już całe oddanie; wiersz własnego pasma działa jak dotąd.

  W panelu klasycznym: „Etap Biologa" pokazywał **pierwszy nieukończony** wiersz,
  bez związku z tym, co rdzeń naprawdę robi — stąd „w panelu bota jedno, w rankingu
  drugie". Panel liczy teraz tą samą regułą co rdzeń, z odczytem plecaka.
  Sprawdzone na trzech przypiętych botach: dwa na 33 i 34 poziomie pokazują Grzyb
  Tue, jeden na 49 — Ząb Orka, czyli najwyższy otwarty wiersz, gdy wszystkie są
  przerośnięte.

- **Przycisk „ZAINSTALUJ / PRZYGOTUJ" w launcherze mówił „Paczka jest gotowa"
  paczce bez źródeł gry.** Zgłoszone z Discorda po 1.30.27: „ponowne uruchomienie
  instalatora przez Install in GUI nie odtworzyło źródeł". Nie mogło — ten
  przycisk **nigdy nie był instalatorem**. Sprawdza Dockera, tworzy skrót na
  pulpicie i zakłada, że źródła już są na dysku; nie ma w nim ani jednego
  odwołania do `installer\install.ps1`. Teraz wykrywa brak źródeł i mówi po
  polsku, czego brakuje, że żaden przycisk ani aktualizacja tego nie pobierze, i
  podaje dokładne polecenie z `M2_SRC_ARCHIVE`.

### Zmienione

- **Broń z trzydziestego poziomu: boty jej szukają dłużej, wracają po nią z
  rubieży i wyceniają ją jak nagrodę.** Trzy zgłoszenia z Discorda naraz.

  Pułap polowania wynosił 24 (Loch M3) i 35 (Bestiale w Bokjungu) — broń była
  czymś, co bot albo zdobył młodo, albo nigdy. Zmierzone: **205 z 393** botów na
  36+ z ponad milionem yang nie miało jej nigdzie — „latają na 37 z sześcioma
  milionami i stożkowym mieczem +6 po dolinie". Farmą teraz do czterdziestki
  (krzywa dropu trzyma siedemdziesiąt procent dziesięć poziomów nad potworem), a
  rubież **oddaje** bezbronnego bota do M2, skąd idzie na M3. Trzy minuty po
  wdrożeniu: trzy powroty z rubieży, siedem wyjść na M3 i **sześć znalezionych
  broni**.

  Cena: nieulepszona broń 30 wpadała do gałęzi „szrot" (cena handlarza razy dwa,
  29 032 na naszej ladzie), podczas gdy Futro Tygrysa obok stało po kilkaset
  tysięcy z podłogi materiałowej. Propozycja z Discorda — piętnaście do dwudziestu
  razy drożej — ma rację co do rzędu wielkości: podłoga 250 000, między +7 a +8
  zwykłego sprzętu. Na ladach po zmianie: **312 500, 375 000, 512 500.** Do tego
  osobny, stromy schodek (+300%) za linię **średniej 24%+ albo umiejętności
  15%+** — progi dobrane do realnych zakresów tego świata (46 i 18), tylko na
  tym zestawie broni.

- **Dwie rzeczy z tej samej listy zgłoszeń celowo bez zmiany.** Bransoleta,
  naszyjnik i kolczyk **są kupowane** u handlarza zbroi, a zwoje błogosławieństwa
  **są używane** przy ulepszaniu — oba mechanizmy istniały wcześniej i działają;
  ogranicza je 30 poziom i trzy zwoje na wizytę.

---

## 1.30.28 — 2026-09-08

### Naprawione

- **Ostrzeżenie o brakujących źródłach było w połowie kodu, której „GRAJ" nie
  uruchamia.** Zgłoszone z Discorda **drugi raz**, przeciwko wersji, która miała
  to naprawić — i było to słuszne zgłoszenie. 1.30.27 dodała sprawdzenie
  kompletności kontekstu budowy do `start-server.ps1`. Tyle że launcher woła ten
  skrypt z przełącznikiem `-IdentityOnly`, który kończy się zaraz po zapisaniu
  `.env` — **w linii 557, a sprawdzenie stało w 713** — po czym launcher buduje
  sam, wywołując `docker compose up --build` bezpośrednio. Gracz klikający GRAJ
  nigdy tego sprawdzenia nie widział i dostawał piętnaście linii
  `failed to calculate checksum ... not found`, tak samo jak przedtem.

  Sprawdzenie stoi teraz tam, gdzie budowa naprawdę zachodzi. Zamiast piętnastu
  błędów Dockera pada jedno zdanie: czego brakuje, że to **nie jest** błąd
  Dockera, WSL ani aktualizacji, że te pliki pochodzą z własnej paczki serwera
  r40250 i żadna aktualizacja ich nie przywróci — oraz że ratunkiem jest ponowne
  uruchomienie instalatora, przy nietkniętej bazie, postaciach i ustawieniach.

- **Boty w Lochu Małp ogłaszały wyjście, którego nie było.** Zgłoszone z Discorda:
  „mimo chmurki, że wychodzą z lochu, one nie wychodzą". Napis „Wychodzę z Lochu
  Małp" był zwykłym „w przeciwnym razie" — mówił go **każdy** bot, który na mapie
  lochu się przemieszczał. A w lochu przemieszczanie się to stan normalny:
  jedenaście komnat połączonych wyłącznie NPC-ami GOTO, więc przejście do
  następnej to zwykły marsz. Złapany bot z tą chmurką miał cel **polowanie na
  metiny**.

  Rzecz, która czyniła to szczególnie mylącym: **wyjście z lochu jest
  natychmiastowe** — to bezpośrednia zmiana mapy w tym samym ticku, nie marsz do
  portalu. Bot, którego widać w lochu, z definicji nie wychodzi. Napis brzmi teraz
  „Szukam drogi przez Loch Małp" i słowo „wychodzę" nie pada tam w ogóle.

  Trzeba dodać, czego pomiar **nie** potwierdził: zarzutu o zepsute poruszanie się
  i teleporty. Przez półtorej minuty obserwacji **jeden bot na trzydzieści** nie
  drgnął, i ten najpewniej walczył. Geometria wczytuje się kompletna na wszystkich
  trzech mapach, przejścia między komnatami zachodzą, wejść i wyjść jest tyle
  samo. Problemem była sama chmurka.

### Zmienione

- **Bonusy ważone według klasy, a nie jednakowo dla wszystkich.** Mechanika
  działała od dawna — zmierzone **2155 użyć** zwojów, a bot nie dokupuje zwoju,
  gdy jakiś ma. Zły był wybór tego, co warto zatrzymać.

  Zmierzone na każdym atrybucie każdego przedmiotu w tym świecie: **średnie
  obrażenia losują się do 46, a obrażenia umiejętności tylko do 18**. Przy wagach
  dwanaście i dziesięć — tych samych dla wszystkich — najlepsze możliwe średnie
  obrażenia dawały 460 punktów, a najlepsze obrażenia umiejętności 216. Czyli
  **szaman, który wylosował najlepszą linię w grze dla swojego buildu, wyrzucał ją
  na następnym przebiegu**, choć jego obrażenia to niemal wyłącznie umiejętności.
  Wagi są teraz dobrane wprost do tych dwóch sufitów: dla maga najlepszy skill
  bije najlepsze średnie, dla reszty kolejność zostaje bez zmian.

  I rzecz, którą trzeba powiedzieć wprost, bo zmienia oczekiwania: **„Silny
  przeciwko Potworom" w tym świecie nie występuje ani razu.** Poradniki słusznie
  stawiają go bardzo wysoko — podnosi obrażenia wobec wszystkich potworów i
  kamieni metinu, czyli wobec wszystkiego, z czym bot kiedykolwiek walczy — ale
  żadna zmianka go tu nie wylosuje. Jego waga została podniesiona dla przedmiotów,
  które mają go wbudowanego, i to wszystko, co da się z nim zrobić.

  Uczciwie o stanie pomiaru: nowe wagi są policzone z realnych zakresów i
  wdrożone, ale w oknie obserwacji zdążyły zajść dopiero dwa przebiegi — za mało,
  by pokazać zmianę w liczbach. Sama zmiana dotyczy wyłącznie tego, którą linię
  bot uznaje za lepszą.

---

## 1.30.27 — 2026-09-08

### Naprawione

- **Instalacja, która straciła źródła gry, nie mówiła o tym ani słowa.**
  Zgłoszone z Discorda po 1.30.26: budowa kończy się piętnastoma liniami
  `failed to calculate checksum ... not found`, wymieniającymi `src/server/common`,
  `libgame`, `extern`, `serverfiles/share/...` — a Docker i WSL działają poprawnie.

  Liczba, która to rozstrzygnęła: kontekst budowy miał **1,61 MB**, a pełny liczy
  się w setkach megabajtów. Paczka aktualizacji wkłada pod `game/src` dokładnie
  **trzydzieści osiem plików** — sam `src/server/game`, bo tam należą źródła botów.
  Cała reszta drzewa pochodzi z **własnej paczki serwera r40250** operatora i jest
  rozpakowywana raz, przy instalacji; aktualizacja jej nie przywraca, bo nie wolno
  nam jej rozpowszechniać. Na maszynie, która to drzewo straciła, aktualizacja
  **wytwarza** wiarygodnie wyglądający `src/server/game` — i budowa dochodzi dalej
  tylko po to, by paść na wszystkim obok.

  A dlaczego drzewo znikało: `prepare-context.sh` kasował kontekst budowy, **zanim**
  sprawdził, czy ma z czego go odtworzyć. Kontrola na górze pliku patrzyła tylko,
  czy katalog `server/` istnieje — nie czy zawiera dziewięć modułów. Niepełne
  drzewo przechodziło tę kontrolę, po czym skrypt **niszczył działającą
  instalację i dopiero potem umierał**. Teraz sprawdza wszystkie dziewięć modułów
  i cztery katalogi `share/` przed skasowaniem czegokolwiek, a gdy źródeł brakuje,
  zostawia istniejący kontekst w spokoju.

  Drugie zabezpieczenie jest po stronie gracza: launcher sprawdza kompletność
  kontekstu **przed** uruchomieniem budowy i mówi jednym zdaniem po polsku, czego
  brakuje, że to nie jest błąd Dockera ani aktualizacji, i że ratunkiem jest
  ponowne uruchomienie instalatora — baza, postacie i ustawienia zostają nietknięte.

- **Boty przemierzały pół mapy pieszo, a koń biegł za nimi.** Zgłoszone z Discorda
  dokładnie taką obserwacją — i tak właśnie było. Silnik przy zsiadaniu
  **przywołuje konia jako towarzysza**, a nic nie sadzało jeźdźca z powrotem:
  każde przejście wędrowne prosiło o trasę z końmi **wyłączonymi**, choć miejsce
  polowania wybierane jest nawet dwadzieścia kilometrów dalej. Koń wraca na trasy
  wędrowne, do znanego metina, na wyprawę na bossa i na powrót po śmierci; krótkie
  przebieżki są nietknięte, bo dosiad i tak nie zachodzi bliżej niż 1800 jednostek.

  Zmierzone po wdrożeniu: **304 dosiady na długą trasę w pięć minut** — wobec
  **siedmiu w dwadzieścia pięć minut** przed poprawką.

- **Bot odchodził od metina, któremu został ułamek życia.** Zgłoszone przez dwie
  osoby. To nie był odwrót taktyczny — kamień jest w silniku `CHAR_TYPE_STONE`, a
  nie `CHAR_TYPE_MONSTER`, więc odwrót go nie dotyczy. Winna była **awaryjna
  regeneracja przy dwudziestu procentach życia**, która porzuca cel bez względu na
  to, czym on jest. Dla potwora to słuszne: goni i zabije. Kamień **nikogo nie
  goni**, a odejście od niego wyrzuca całą walkę — bot wraca do kamienia w pełni
  sił albo nie zastaje go wcale. Teraz dobija kamień poniżej piętnastu procent
  jego wytrzymałości i tylko dopóki sam jest powyżej dziesięciu. Śmierć kosztuje
  doświadczenie i to nie jest przyzwolenie na stanie w fali uderzeniowej.

- **Przynęta kupowana za tyle, ile bot ma — ale nie do ostatniego yanga.**
  Poprawka z 1.30.26 zadziałała aż za dobrze: ten sam bot przeszedł z 556 przez
  601 do **jednego yanga**, wydając ostatni grosz na robaki i nie zostawiając nic
  na miksturkę. Rezerwa kwotowa nie da się tu zastosować — każda dość duża, by
  miała sens, jest większa niż majątek botów, którym ta poprawka pomaga, więc
  odmówiłaby dokładnie tego zakupu, dla którego powstała. Jest udziałem: bot
  wydaje najwyżej dziewięćdziesiąt procent sakiewki.

### Nowe

- **Boty resetują umiejętności u staruszki, gdy nie mają już czym próbować.**
  Zaproponowane na Discordzie. Sprawdzone w plikach serwerowych i zrobione
  dokładnie tak, jak robi to gracz: **NPC 9006** na południe od Joan, koszt
  `10000 + poziom × 2000`, odmowa poniżej piątego i **powyżej trzydziestego**
  poziomu — wszystko wprost z `skill_reset2.quest`.

  Bot idzie tam tylko wtedy, gdy naprawdę utknął: umiejętność stoi na siedemnastu
  bez mistrza **i** nie został mu ani jeden punkt umiejętności. Reset kasuje
  wszystkie poziomy umiejętności, więc bot z punktami w ręce ma je najpierw wydać
  i rzucać dalej za darmo. Do tego pół godziny odstępu i zapas w sakiewce, żeby
  reset nie zostawił go bez pieniędzy na mikstury.

  Zmierzone na żywo, od zapłaty po powrót do pracy:

      19:36:44  reset u staruszki  poziom=27 grupa=2 zablokowana=48 koszt=64000 punkty=26
      19:36:49  cel: wybór profesji
      19:37:10  wybrał grupę u trenera  punkty=26
      19:37:14  wrócił do roboty

  Koszt 64 000 to dokładnie `10000 + 27 × 2000`, a 26 punktów to dokładnie tyle,
  ile zwraca silnik przy czyszczeniu umiejętności. **Dwadzieścia sześć sekund
  po zapłacie bot stał u trenera** — bo grupa wyzerowana to dokładnie ten stan,
  który od zawsze odsyłał bota do trenera, więc druga połowa sprawy nie
  potrzebowała żadnej nowej mechaniki.

### Zmienione

- **Trzy pozycje robią stragan.** Zgłoszone z Discorda: „bez sensu, że boty mają
  dużo yang i miejsce w ekwipunku, a wystawiają na siłę sklep z jedną Niedźwiedzią
  Skórą czy innym ornamentem". Zasada obok tego progu od zawsze mówiła „trzy",
  podczas gdy liczba mówiła „dwa" — a dwa tanie materiały to ta sama skarga jedną
  linię dalej. Prawdziwy łup otwiera stragan sam jak dotąd: broń z trzydziestego
  poziomu, cokolwiek na +6, duży bonus, medal konny. Materiał nigdy nie zbliża
  się do tego progu.

---

## 1.30.26 — 2026-09-08

### Naprawione

- **Bot, którego nie stać na całą paczkę przynęty, nie kupował jej wcale.**
  Zgłoszone z Discorda jako „stoją pod Rybakiem, a przynęty nie kupują", i
  w 1.30.25 nie umieliśmy tego rozstrzygnąć — zakup mógł się nie udać na trzy
  różne sposoby, a wszystkie wychodziły jednymi drzwiami. Kiedy każda odmowa
  zaczęła mówić własnym zdaniem, przyczyna znalazła się **na naszym własnym
  serwerze w dwie minuty**:

      cannot afford fishing_bait vnum=27801 count=20 price=800 gold=556

  Paczka to dwadzieścia robaków za osiemset yang. Bot miał pięćset
  pięćdziesiąt sześć — czyli trzynaście robaków i całą sesję łowienia — i nie
  kupował żadnego, bo kupno było „cała paczka albo nic". Teraz bierze tyle, na
  ile go stać. Dotyczy to rzeczy kupowanych na sztuki: wędka jest jedna i albo
  na nią stać, albo nie.

  Trzeba powiedzieć uczciwie, czego **nie** widać w pomiarze: przez pół godziny
  po wdrożeniu ta gałąź nie miała okazji się odpalić — osiemdziesiąt trzy
  zakupy przynęty i żadnej odmowy, bo nasze boty są zamożne. Zmiana jest
  bezpieczna z konstrukcji: po zmniejszeniu ilości cena jest przeliczana i
  sprawdzana ponownie, więc w najgorszym razie kończy się tą samą odmową co
  dotąd.

### Potwierdzone po 1.30.25

- **Portale trzymają przy pełnej obsadzie.** Szesnaście minut pomiaru przy
  850 botach: **1455 przejść portalami i zero zacięć**. Przed poprawką było
  dziewięćdziesiąt do stu zacięć na minutę.

- **Świat rozkłada się na dziewięć map.** To było pytanie z Discorda —
  „nie wiem jak jest z górą Sohan, jest tam mało botów" — i odpowiedź okazała
  się inna, niż wyglądała. Sohan nie był pusty z powodu Sohanu: boty nie mogły
  wyjść z miasta. Po naprawie portali Bokjung spadł z 465 botów na 107, a
  reszta rozeszła się po świecie:

  | mapa | boty |
  |---|---|
  | Pustynia Yongbi | 239 |
  | Joan | 201 |
  | Mount Sohan | **108** |
  | Bokjung | 107 |
  | Dolina Orków | 105 |
  | Loch Pająków V1 | 36 |
  | Loch Małp trudny | 20 |
  | Świątynia Hwang | 18 |
  | Loch Małp średni | 12 |

- **Drużyny na rubieżach.** 354 boty z 846 polują w drużynie.

---

## 1.30.25 — 2026-09-08

### Naprawione

- **Świeża instalacja nie budowała się — i nie chodziło o jeden plik.**
  Zgłoszone z Discorda: budowa zatrzymywała się na
  `failed to compute cache key ... "/rates": not found`, a katalogu `rates/`
  nie było ani w instalacji, ani w żadnej kopii aktualizacji.
  Sprawdziliśmy **wszystkie 33 instrukcje `COPY`** we wszystkich Dockerfile'ach
  i brakowało **sześciu** rzeczy: `game/rates/`, `client-builder/pack/`,
  `client-builder/bin/`, `updater/bin/` i `wsbridge/bin/`.

  Wniosek, który trzeba zapisać wprost, bo to już trzeci raz ta sama pomyłka:
  **bycie w repozytorium to nie to samo co bycie dostarczonym.** Instalacja
  złożona z paczki ma dokładnie to, co wymienia lista plików —
  `panel/bin/apply_rates.sh` był w repozytorium i mimo to go tam nie było.
  Doszło `tools/check-update-covers-build.py`, które czyta każdy `COPY`
  każdego Dockerfile'a i odmawia, gdy cokolwiek, czego budowa dotyka, nie
  jechałoby w aktualizacji. Paczka tego wydania została nim sprawdzona:
  1878 plików, nakładka i kopia sceniczna zgodne co do pliku.

- **Boty nie potrafiły wejść w portal — w żaden portal.** Zgłoszone z Discorda dla
  Lochu Małp („cały czas pisze nad ich głowami «Ide do lochu po medal konny»
  i tak stoją na koniach"), potwierdzone dla M3, a zmierzone u nas na
  **pięciu portalach na czterech mapach naraz**.

  Przyczyna nie była ani w terenie, ani w trasie. **Planer i marsz mierzyły co
  innego.** Planer prostuje trasę po środkach komórek swojej siatki; marsz
  sprawdza rzeczywisty odcinek z dokładnej pozycji postaci, przejściem, które
  liczy komórkę muśniętą o milimetr rogu. Cel portalu to surowa współrzędna
  ze stałej — na granicy komórki, nie w jej środku. Te dwa testy różnią się
  właśnie tam, a różnica jest **trwała**: ten sam plan wraca za każdym razem.

  Bot odrzucał więc własny jedyny punkt trasy **czterdzieści dwa razy w
  dwadzieścia sekund**, i robił to **w zupełnej ciszy**: gałąź, która wyrzuca
  trasę, nie logowała niczego, a sąsiednia odzywa się tylko przy pierwszej i
  trzeciej porażce, po czym milknie na zawsze. Dlatego nie było tego widać w
  żadnym logu i dlatego trzeba było to najpierw oprzyrządować.

  Marsz do portalu celuje teraz w środek komórki, na której planer liczył — to
  najwyżej trzydzieści pięć jednostek różnicy przy progu przejścia dwustu — a
  odrzucony odcinek ma dwie próby ratunku, zanim trasa pójdzie do kosza. Sama
  gałąź przestała być cicha, a linia zacięcia niesie teraz komplet: ile razy
  marsz naprawdę pytano, jaka była trasa i która dokładnie odmowa zapadła.

  Zmierzone u nas, ta sama wersja co u graczy:

  | | przed | po |
  |---|---|---|
  | zacięcia portali | ~90–100 na minutę | **0** |
  | przejścia portalami | — | **569** w ośmiu minutach |
  | boty w Lochach Małp | 1 i 1 | **10 i 5** |
  | `tick_ms` | 9558–9939 | **4389** |
  | trasy planowane na minutę | 4108 | **623** |

- **Marsz uznawany za zacięty, gdy bot legalnie obchodził budynek.** Postęp
  mierzono wyłącznie skracaniem się linii prostej do portalu, a portal
  praktycznie zawsze stoi przy zabudowie — więc obejście było regułą, nie
  wyjątkiem. Złapany na żywo bot miał trasę w punkcie piątym z siedmiu,
  licznik zacięć na zerze i był wyrzucany ze swojej trasy co dwadzieścia
  sekund. Zaliczony punkt trasy jest teraz postępem na równi ze skróceniem
  odległości.

- **Zegar zacięcia liczył czas ścienny, nie próby marszu.** Zegar biegł także
  wtedy, gdy bot robił coś zupełnie innego — walczył, zbierał, stał u kupca —
  więc pierwszy tick podróży po zajętych dwudziestu sekundach ogłaszał
  zacięcie bota, który dostał dokładnie jedną szansę, żeby zrobić krok.
  Złapany na gorącym uczynku: jeden przebieg, pełna trasa i osiemdziesiąt
  osiem kilometrów do celu.

- **Sprzęt nie był powodem, by pójść na stragany.** Zgłoszone z Discorda:
  „wystawiłem bojowe tarcze +8 za 1 yang i boty nie kupują, mimo że mają
  tylko +4". Porównywanie oferty z tym, co bot nosi, działało od dawna — ale
  brama, która decyduje, czy w ogóle wybrać się pod ladę, znała tylko
  materiały do ulepszeń, medal konny, zwój zapomnienia, wolne gniazdo na
  kamień duszy i broń z trzydziestego poziomu. Sprzęt był osiągalny wyłącznie
  przypadkiem, przy okazji wyprawy po coś innego.

- **Odmowa zakupu przynęty w końcu mówi, dlaczego odmawia.** Zgłoszone
  z Discorda: „stoją pod Rybakiem, a przynęty nie kupują". Trzeba powiedzieć
  wprost: **tego jeszcze nie rozstrzygnęliśmy** — u nas ta ścieżka działa,
  w godzinie pomiaru zanotowaliśmy 69 zakupów po dwadzieścia robaków za 800
  yang. Powodem, dla którego nie da się tego orzec ze zgłoszenia, jest sam log:
  zakup mógł się nie udać na **trzy zupełnie różne sposoby** — przedmiot bez
  ceny w serverfiles, bot bez pieniędzy, plecak bez miejsca — a wszystkie trzy
  wychodziły jednymi drzwiami jako „cannot_afford_tackle". Teraz każdy mówi
  własnym zdaniem, z ceną, stanem sakiewki i numerem przedmiotu.
  Przy okazji naprawiona prawdziwa wada: funkcja zwracała „czy cokolwiek
  kupiono", więc „nie było czego kupować" i „kupno się nie udało" dawały tę samą
  odpowiedź. Sprawdzone też w silniku, żeby nie zgadywać: `AutoGiveItem`
  dokłada do istniejącego stosu, zanim poszuka wolnej komórki — pełny plecak
  blokuje więc przynętę tylko temu botowi, który nie ma jej wcale.

  Drugie zgłoszenie z tego samego wątku — bot z napisem „Zakladam przynete na
  wedke", który nie ma wędki na plecach — zostało poprawione w **1.30.23**
  i ten zrzut pochodzi ze starszej wersji.

### Zmienione

- **Na rubieżach częściej w drużynie, i częściej z szamanem.** Szaman już
  wcześniej rzucał na całą drużynę — Błogosławieństwo, Pomoc Smoka,
  Chyżość, Wzmocnienie Ataku i leczenie — tyle że polował samotnie, więc
  rzucał to na nikogo. Przy doborze partnera na mapach rubieży para
  z **dokładnie jednym** szamanem ma teraz wyraźną przewagę (drugi szaman nic
  nie dodaje, bo buffy i tak obejmują drużynę), drużyna z szamanem ma
  pierwszeństwo przed drużyną bez niego, a skłonność do samotnego polowania
  spada tam z dwudziestu pięciu procent do dziesięciu.

---

## 1.30.24 — 2026-09-08

### Naprawione

- **Wędkarze stali w miejscu zamiast łowić — i był to nasz błąd z 1.30.22.**
  Żeby trzymali metr odstępu, promień „dotarłem" został tam zawężony z dwustu
  jednostek do dwudziestu pięciu. Tyle że marsz zatrzymuje się przy stu — to
  `PLAYERBOT_NAV_ARRIVAL_DISTANCE`, próg, przy którym nawigacja uznaje cel za
  osiągnięty i przestaje iść. Między dwudziestoma pięcioma a stoma powstała
  martwa strefa: nawigacja melduje sukces i staje, pas wędkowania prosi o
  kolejny krok, nic się nie rusza, licznik zacięć pokazuje zero i w żadnym logu
  nie ma śladu porażki. Dwa boty złapane na żywo stały siedemdziesiąt jeden i
  siedemdziesiąt sześć jednostek od celu, którego żaden nigdy nie osiągnął.

  Promień wrócił do stu — nigdy poniżej progu, przy którym marsz staje — a sama
  zasada jest teraz **sprawdzana przy kompilacji**, nie zapisana w komentarzu:

      static_assert(PLAYERBOT_FISHING_ARRIVE >= PLAYERBOT_NAV_ARRIVAL_DISTANCE,
              "an arrival radius below the navigation's own strands the bot short of it");

  Zmierzone po wdrożeniu: wędkarzy nad wodą 43 → **53**, z tego łowiących
  11 → **53**. Nikt już nie chodzi do Rybaka w kółko ani nie szuka wędki.
  Odstępy na brzegu: najmniejszy **60** jednostek zamiast dwunastu, średnio
  **198** do najbliższego sąsiada.

  Trzeba powiedzieć wprost, czego to nie daje: **metr odstępu nie jest
  gwarantowany.** Przy stanowiskach co sto pięćdziesiąt jednostek i stu
  jednostkach tolerancji na każdym końcu dwaj sąsiedzi mogą się zejść bliżej i
  czasem schodzą. Żeby zagwarantować metr, stanowiska musiałyby stać co trzysta,
  a wtedy na tym odcinku rzeki zmieści się około czterdziestu przy pięćdziesięciu
  sześciu wędkarzach — więc na razie zostaje ta ziarnistość, opisana zamiast
  obiecywanej.

  Przy okazji sprawdzone: drugi i ostatni promień przybycia w kodzie,
  `PLAYERBOT_MARKET_ARRIVE`, wynosi 450 i leży bezpiecznie powyżej progu.

- **Panel podstawowy zaniżał liczbę botów.** Zgłoszone z Discorda ze zrzutami obu
  paneli obok siebie: zaawansowany pokazywał **999 botów w grze**, podstawowy
  **399**. Boty były — mylił się licznik. Odczyt migawki stanu miał `int()`
  wewnątrz `try`, które obejmowało **całą pętlę po pliku**, więc jedna nieczytelna
  linia — wystarczy rozdarty odczyt w chwili, gdy rdzeń przepisuje plik —
  wyrzucała wszystkie pozostałe wiersze tego pliku. Stąd dokładnie taka liczba:
  parsowanie urwane w połowie. Teraz zła linia kosztuje jedną linię, a panel
  zapisuje w swoim logu, ile wierszy pominął. Sprawdzone na próbie: plik z 999
  wierszami i jednym uszkodzonym daje 998 odczytanych i jeden pominięty.

---

## 1.30.23 — 2026-09-08

### Naprawione

- **Botów ubywało i nic ich nie przywracało.** Zgłoszone z Discorda: „z tysiąca
  po godzinie mam trzysta pięćdziesiąt". Kolejka odrodzeń była napełniana
  **raz**, przy starcie, i opróżniana przez minutę — potem nikt już nigdy nie
  liczył. Bot, któremu nie powiodło się wejście do świata, albo który z niego
  wypadł, był stracony aż do restartu serwera.
  Teraz raz na minutę rdzeń przelicza, ilu z zamówionych naprawdę jest w
  świecie, i dosyła brakujących tą samą rozłożoną w czasie kolejką. Ograniczone
  do tego, co zamówiono, więc odbudowuje obsadę i nigdy jej nie powiększa.
  Zmierzone na naszym własnym, zdrowym serwerze zaraz po wdrożeniu: **jedenastu
  botów nie było** po pierwszym napełnieniu — i przed tą zmianą zostaliby poza
  światem do końca dnia.

- **Nie dało się dowiedzieć, dlaczego botów jest mniej, niż się zamówiło.**
  Rdzeń przyjmuje tożsamość tylko wtedy, gdy przejdzie sześć warunków naraz —
  jeden wielki AND — a wiersz, który poległ, znikał bez słowa. Operator prosił o
  tysiąc, dostawał sześćset pięćdziesiąt i nie miał się czego chwycić.
  Teraz przy starcie idzie jedna linia z rozbiciem. U nas wygląda tak:
  `registry rows=1182 usable=1012 rejected: login=170 social_id=101
  other_characters=62` — czyli sufitu nie wyznacza suwak w launcherze, tylko
  konta, których login albo social_id nie pasuje do wzorca generatora.

- **Skrypt, który jedzie tylko w instalatorze, to skrypt nie do naprawienia.**
  Zgłoszone z Discorda: instalacja bez `panel/bin/apply_rates.sh` nie miała skąd
  go wziąć. Sprawdziliśmy całość i było gorzej: **z dziewięciu skryptów
  kontenera gry aktualizacja wysyłała jeden.** `m2-rates`, `m2-supervise`,
  `m2-gm`, `m2-lang`, `entrypoint.sh` — czyli wszystko, czym ten kontener jest
  sterowany — nie jechało nigdy. Teraz idzie całe `bin/` obu kontenerów.

- **Panel zaawansowany zamieniał miejscami dwa bonusy.** Zgłoszone z Discorda ze
  zrzutem: w rankingu „ŚR" i „UM" pokazywały się na odwrót względem opisu
  przedmiotu w grze. Kanoniczna tabela mówi `71 = Obrażenie Umiejętności`,
  `72 = Średnie Obrażenia`, a zapytanie panelu miało te dwa numery zamienione.

- **Wędkarz stał nad wodą godzinami i twierdził, że zakłada przynętę.** Zgłoszone
  z Discorda jako „boty zakładają przynętę na bronie" — i tu trzeba powiedzieć
  wprost: **na broń nic nie było zakładane.** Kod przynęty sprawdza, czy w ręce
  jest wędka, i odmawia. Kłamał napis: był zwykłym „w przeciwnym razie", więc
  każdy wędkarz nad wodą, który akurat nie zarzucił, ogłaszał zakładanie
  przynęty — również taki, który wędki nie miał na sobie w ogóle. Teraz w tym
  przypadku pisze „Szukam wędki".
  Prawdziwy był drugi zarzut: **nic nie ograniczało tego stania.** Zegar
  pilnował zarzutu, który nie bierze, ale kroku wcześniej — bota gotowego do
  łowienia, który nie zarzuca ani razu — nie pilnowało nic. Sesja bez jednego
  zarzutu kończy się po dwóch minutach i zostawia w logu powód razem ze stanem
  wędki i przynęty.

### Zmienione

- **Pustynia przestaje być korytarzem.** To najbogatsza mapa tego świata —
  **14 026 punktów odrodzenia** przeciwko 8122 w Dolinie Orków — a polowało na
  niej wyłącznie pasmo 30–35. Wszyscy od 36 wzwyż szli do Doliny, więc mapa, na
  której sam Król Skorpion stoi w 2234 miejscach, służyła za przejście do Lochu
  Pająków. Pasmo 36–47 dzieli się teraz między Dolinę i pustynię, tak jak 30–35
  już się dzieliło.
  Zmierzone: Dolina Orków z 308–388 botów na **141**, pustynia z 97–123 na
  **232**. Przy okazji spadło obciążenie — rozłożenie ludzi na więcej map ścięło
  pracę nawigacji do jednej trzeciej: `tick_ms` z trzynastu–dziewiętnastu tysięcy
  na **5244**, odrzuconych tras z kilkuset na **jedną**.

- **Droper medali nie czeka już na swoją ambicję.** Zdobywanie medali to całość
  tego, po co ta osobowość istnieje, a ambicja się rotuje: siedemdziesiąt trzy
  boty z ośmiuset trzydziestu ośmiu miały ją w danej chwili, więc trzynastu
  droperów siedziało bezczynnie dziewięć razy na dziesięć i wszystkie trzy Lochy
  Małp stały niemal puste. Reszta botów nadal potrzebuje ambicji, więc loch nie
  zamienia się w taśmociąg.

---

## 1.30.22 — 2026-09-08

### Naprawione

- **Instalacje na Linuksie i VPS-ach nie dawały się zaktualizować.** Zgłoszone z
  Discorda z dokładną diagnozą, za którą dziękujemy: łatka silnika
  `0008-warp-npc-ignores-playerbots.patch` jest ucięta. Jej nagłówek deklaruje
  `@@ -6447,7 +6447,19 @@`, a treść niesie sześć starych i osiemnaście nowych
  linii — brakuje ostatniej linii kontekstu z zamykającą klamrą. `patch` odrzuca
  taki plik, `prepare-context.sh` przerywa i aktualizacja staje w pół drogi.
  Dotyczyło to wydań od 1.30.13 do 1.30.20; w 1.30.12 tej łatki jeszcze nie ma.
  Brakująca linia jest dopisana, a łatka przechodzi teraz próbę na sucho z
  `--fuzz=0` przeciwko czystemu drzewu portu.
  Dlaczego nikt tego u nas nie złapał: **na Windowsie ta łatka w ogóle się nie
  uruchamia** — launcher wgrywa gotowy, już załatany `char.cpp`, a
  `prepare-context.sh` odpala się tylko tam, gdzie serwer buduje się ze źródeł.
  Cały nasz tor testowy jest windowsowy, więc trafiło to wyłącznie w instalacje,
  których nie testujemy. To się zmienia: próba na sucho z `--fuzz=0` wchodzi na
  stałe do sprawdzania łatek.

- **Jeden uszkodzony plik potrafił zatrzymać cały serwer i żadna aktualizacja go
  nie naprawiała.** Zgłoszone z Discorda: „nie mogę aktualizować ani grać".
  W logu widać `linux-port/docker/panel/Dockerfile` o rozmiarze **dwóch bajtów**
  (u nas ma prawie pięć kilobajtów). `docker compose up` buduje trzy obrazy
  jednym przebiegiem, więc panel wywalał się na pierwszym kroku, a gra i panel
  zaawansowany szły z nim (`CANCELED`) — nie wstawało nic. Rada z komunikatu,
  żeby kliknąć GRAJ ponownie, nie miała jak pomóc, bo nic tego pliku nie
  zastępowało: **z siedmiu Dockerfile'ów, które budują się na maszynie gracza,
  aktualizacja wysyłała tylko ten od gry.** Teraz jadą wszystkie, razem z plikami
  `.dockerignore`, więc następna aktualizacja odbudowuje uszkodzony plik sama.

- **Dwóch wędkarzy stawało na jednym stanowisku.** Dwie przyczyny, obie po
  naszej stronie. Po pierwsze, po wyborze miejsca kod dociągał je do
  „najbliższej chodzalnej komórki" w promieniu **dwunastu komórek, czyli
  sześciuset jednostek**, przy promieniu przybycia równym dwudziestu pięciu —
  więc dwa stanowiska odległe o sto pięćdziesiąt mogły trafić na jedno miejsce.
  To ten sam błąd, który w tym samym wydaniu naprawiliśmy w marszu do portalu.
  Po drugie, i głębiej: **nawigacja ocenia komórkę, próbkując jej środek**
  (`podstawa + n*50 + 25`), a stanowiska były generowane na wielokrotnościach
  pięćdziesięciu, czyli na rogach komórek. Sprawdzaliśmy jeden punkt, a silnik
  sądził po sąsiednim. Cała tablica jest przeliczona na środki komórek.

### Nowe

- **Świątynia Hwang.** Mapa 65 wchodzi jako szósty teren dla botów, dla postaci
  od 52 poziomu, obok Sohanu i Lochu Pająków. Wszystko wzięte z plików samego
  serwera, nie z opisu: 5088 punktów odrodzenia, potwory od 52 do 61, mediana
  56. Zachodnia połowa to Elit. Ezoterycy 52–55 i tam się na mapę wchodzi,
  wschodnia to Drzewne Żółwie i Straszydła 55–58 — i tak samo dzieli się
  dziewięć miejsc łowieckich, policzonych z gęstości odrodzeń i sprawdzonych co
  do jednego, czy da się na nich stanąć.
  Metinów tam nie ma; to, co u innych map jest plikiem kamieni, tutaj jest
  szesnastoma żyłami rudy. Nie ma też miejsca zbiórki na bossa: dwa punkty
  losują wśród trzech ras, a jedna z nich to Zjawa Żółtego Tygrysa na
  siedemdziesiątym piątym poziomie — nie ma po co wysyłać tam pięćdziesiątki.
  **Prawdziwym powodem jest jednak drop.** Język Żaby, Żabie Udka, Liść,
  Nieznany Talizman+ i Księga Klątw+ występują w osiemnastu recepturach
  ulepszania i nie wypadały na żadnej mapie, po której chodziły boty — rejestr
  rynku prosił o pierwszy z nich przy podaży dokładnie zero. Botom nie trzeba
  było o nich mówić ani słowa: kod czyta tabelę receptur samego silnika, więc
  stały się towarem w tej samej chwili, w której bot mógł stanąć tam, gdzie
  wypadają.

### Zmienione

- **Koniec ze staniem w mieście — boty chodzą po straganach.** Poproszone na
  Discordzie. Postój po załatwionych sprawach skrócony z czterech–dziesięciu
  minut do około trzech, a zamiast stać w jednym punkcie rynku bot co
  sześć–czternaście sekund wybiera inną ladę i tam idzie; nad głową pisze
  „Oglądam stragany". Lada, do której nie potrafi dojść, jest porzucana po
  dwudziestu sekundach — bez tego jeden bot ze zniszczoną trasą stałby przez
  cały postój, czyli dokładnie tak, jak przedtem.
  Zmierzone: cztery boty z napisem 'Ogladam stragany', wszystkie w ruchu — zaden nie trafil na liste stojacych.

- **Wędkarze stoją wzdłuż rzeki, nie na trawie.** Poprzednie wydanie rozstawiło
  ich na prostokącie, a ta rzeka się wije — brzeg biegnie od x 69 900 na północy
  przez 67 200 w środku do 67 800 na południu — więc prostokąt dość szeroki, by
  pomieścić pięćdziesiąt osób, sięgał tam, gdzie wody nie ma wcale.
  Stanowiska są teraz tablicą, tak jak miejsca łowieckie są tablicą: każda
  chodzalna komórka wzdłuż rzeki, posortowana po odległości do wody i przyjęta
  tylko wtedy, gdy żadne przyjęte wcześniej nie leży bliżej niż sto pięćdziesiąt
  jednostek. **162 miejsca**, każde najwyżej trzysta pięćdziesiąt jednostek od
  wody. Każde niesie też własny punkt wody, bo obracanie się na wschód jest
  poprawne dla jednego prostego odcinka i błędne wszędzie tam, gdzie rzeka
  skręca. Zmierzone: trzydziestu wedkarzy rozlozonych wzdluz rzeki, najblizsza para dwanascie jednostek od siebie. To wciaz mniej niz zalozone poltora metra i nie jest to jeszcze wyjasnione — osobno tloczy sie tez kolejka dwudziestu dziewieciu botow po przynete u Rybaka, ktora rozstawia zupelnie inny kod.

---

## 1.30.21 — 2026-09-08

### Naprawione

- **Bot sprzedawał prezent zamiast go założyć.** Zgłoszone z Discorda trzy razy
  jednego popołudnia przez ludzi, którzy właśnie dali botowi coś dobrego: buty
  +9 z trzema bonusami i 1500 HP wylądowały na ladzie zamiast na nogach.
  To nie była ocena przedmiotu, tylko wyścig w takcie. Stragan uznaje za „zapas"
  każdą broń i zbroję, której slot jest już zajęty — a prezent nie zajmuje
  pustego slotu, tylko bije zajęty. Pas straganu stoi w takcie kilkaset linii
  przed pasem ekwipunku, więc lada dostawała rzecz pierwsza, i to na sam szczyt:
  „zapas +6 lub lepszy" to najwyżej punktowany towar, jaki stragan może nieść.
  Teraz przed uznaniem czegoś za zapas pada pytanie, czy bot powinien to na
  sobie mieć — silnikowe `CanEquipNow` plus ta sama punktacja, której używa pas
  ekwipunku, więc liczą się linie bonusów i HP. Granica jest przy „może założyć
  **teraz**": miecz na trzydziesty poziom w plecaku bota z piątego zostaje
  towarem. Do handlarza NPC nic takiego nigdy nie trafiało — tam +6 i wyżej jest
  wykluczone; jedyną drogą utraty prezentu była lada.

- **Setki botów stały w miejscu, twierdząc, że idą.** Zgłoszone z Discorda przez
  dwie osoby: „nie chcą iść tam, gdzie piszą, że idą" i „500 na 750 botów stoi
  w kółku". U nas stało 148 z 838, z czego 53 w podróży, która nigdzie nie
  prowadziła. Złożyły się na to trzy rzeczy.

  Po pierwsze, **budżet planowania tras liczył sztuki**. Na minutę przy 839
  botach: 7440 planów, z tego 7086 to skoki do sąsiedniego potwora kosztujące
  **41 milisekund razem**, a całe jedenaście z dwunastu sekund zjadało 148
  długich tras. Skok za sześć mikrosekund zajmował dokładnie ten sam slot co
  przejście przez Dolinę Orków — i to długie trasy były wypychane z kolejki.
  Połowa wszystkich żądań odrzucana, jedno z nich czekało **trzynaście minut**.
  Plan kosztuje teraz wedle dystansu, a budżet mikrosekundowy dalej ogranicza
  cały takt.

  Po drugie, **żądanie odrzucone dwadzieścia razy przestaje stać w kolejce** za
  licznikiem. Dalej podlega budżetowi czasu i limitowi dalekich tras — to nie
  otwiera dziury, tylko przestaje trzymać jednego bota na końcu kolejki na
  zawsze.

  Po trzecie, **zsiadanie z konia zjadało takt ucieczki**. Zatrzymany marsz do
  portalu oddaje takt właśnie po to, żeby bot poszedł gdzie indziej i zaplanował
  od nowa; pas „koń transportowy nie walczy" ten takt zabierał, bot wsiadał z
  powrotem i stał kolejne dwadzieścia sekund. Czterdzieści sześć botów robiło to
  na wyjściu z Sohanu, wsiadając i zsiadając co dwadzieścia sekund bez jednego
  kroku. Teraz marsz sam zsiada, zanim odda takt.

  Zmierzone po wdrożeniu: odroczeń 3738 → 264 na minutę, zagłodzonych żądań
  170 → 0, botów stojących w podróży 53 → 13.

- **Marsz do portalu celował o kilometr obok.** Promień dociągania celu wynosił
  24 komórki nawigacji, czyli 1200 jednostek świata, a przejście przez portal
  testuje 200. Trasa mogła się legalnie skończyć kilometr od bramy: bot stawał
  na jej końcu, po dwudziestu sekundach marsz się poddawał, a następny takt
  planował to samo. To ta sama pułapka, którą zastawił kiedyś marsz do NPC w
  mieście, i ta sama zasada ją zamyka — dociągnięty cel musi zmieścić się w
  promieniu, który testuje przybycie.

### Zmienione

- **Wędkarze stoją metr od siebie.** Zgłoszone z Discorda ze zdjęciem: kilkadziesiąt
  tabliczek z imionami w jednym stosie i jeden widoczny bot pod spodem. Wszyscy
  szli na tę samą łatkę dwa na cztery metry, a gniazd było pięćdziesiąt co pół
  metra i rozdawał je sam hash — przy pięćdziesięciu wędkarzach i pięćdziesięciu
  gniazdach kolizje są regułą.
  Brzeg został zmierzony z `server_attr` mapy Joan: stojący grunt z otwartą wodą
  na wschód biegnie przez 2250 jednostek. Na nim leży **dziewięćdziesiąt
  stanowisk, sześć kolumn na piętnaście rzędów co 150 jednostek**, każde
  sprawdzone. Stanowisko jest zajmowane na czas sesji i zwalniane razem z nią,
  jak miejsce przy ladzie; zajęcie, którego nikt nie dotknął przez dwie minuty,
  wygasa, żeby bot wylogowany w połowie zarzutu nie trzymał miejsca na zawsze.
  Promień „dotarłem" zszedł z 200 na 25 jednostek — to on decyduje, jak blisko
  siebie kończą dwaj sąsiedzi, i przy dwustu można było stanąć na cudzym
  miejscu.
  Silnik niczego tu nie narzuca: `CHARACTER::fishing()` liczy punkt czterysta
  jednostek przed postacią i nigdy go nie odczytuje, a jedyny teren, jaki
  sprawdza, to kafelek pod nogami.

### Dla budujących z repozytorium

- **Szybki build kopiuje teraz skrypty kontenera.** Do tej pory podmieniał
  wyłącznie skompilowany rdzeń i brał całą resztę z warstwy bazowej, czyli z
  tego, co zostawił ostatni pełny build. Serwer testowy cicho odjeżdżał od tego,
  co dostają gracze: jego warstwa bazowa nosiła przydział map sprzed
  przeniesienia Lochu Pająków V1 i Trudnego Lochu Małp na rdzeń botów, więc
  `m2-render-config` pisał `MAP_ALLOW` bez nich, każdy bot dochodzący do którejś
  z tych bram był odprawiany z kwitkiem **ponad dziesięć tysięcy razy na
  minutę**, a cały dzień pomiarów mówił, że te mapy są puste z powodów, które
  nigdy nie były prawdziwe. Wydania tego nie dotyczyło — `m2-render-config`
  jedzie w paczce aktualizacji od zawsze i u gracza, który się zaktualizował,
  przydział był poprawny.
  Po naprawie narzędzia i przebudowie: V1 z 0 na 55 botów, Trudny Loch Małp z 0
  na 18, Średni z 6 na 14, a korek tranzytowy na pustyni ze 123 na 77.

---

## 1.30.20 — 2026-09-08

### Naprawione

- **Jeden yang za medal konny.** Zgłoszone z Discorda: boty dostały medale konne
  i zaczęły je wystawiać po jednym yangu. `item_proto` daje medalowi (50050) cenę
  zero, więc wycena mnożyła zero przez marżę handlarza i wychodziło z niej
  `max(1, 0)`. Dokładnie tak samo stały wszystkie skrzynki i szkatułki — 50011,
  50192 i 50193 też mają tam zero. Gorzej: taka cena zostawała na zawsze.
  Ogranicznik kroku pozwala ruszyć kotwicą o pięć procent na dziesięć minut, a
  pięć procent z jednego yanga to w liczbach całkowitych zero — więc kotwica
  poniżej czterech yangów nie mogła się już nigdy ruszyć, a każdy stragan
  wystawiający ten przedmiot odświeżał jej zegar, zanim zdążyła się zestarzeć.
  Teraz przedmiot, którego handlarz nie kupi, dostaje własną cenę wyjściową
  (medal konny 400 tys., reszta 30 tys.), kotwica poniżej stu yangów jest
  traktowana jak pomyłka i liczona od nowa, a krok ceny przesuwa ją o co najmniej
  jednego yanga. Zmierzone po wdrożeniu: 39 otwartych straganów i ani
  jednej linii poniżej stu yangów, przy medianie 150 000 yang.

- **Stragan bez zawiniątka kręcił bota w kółko.** Zgłoszone z Discorda razem ze
  zrzutem logu: osiem identycznych linii `no room for bundle` na sekundę dla
  jednego bota, który chodził w tę i z powrotem wzdłuż jednej linii. Gdy plecak
  jest pełny, nie ma gdzie położyć kupionego zawiniątka — a kod nie ustawiał
  wtedy żadnego zegara, więc pytał ponownie na każdym takcie i sam sobie odbierał
  kolejkę, w której handlarz opróżniłby plecak. Teraz odczekuje od minuty do
  trzech, a linia w logu jest dławiona jak każda inna.

- **Biolog stawał na Korzeniu Gango.** Zgłoszone z Discorda: Sura czterdziestego
  drugiego poziomu z celem „Etap Biologa: Korzeń Gango 0/5", bijąca orki. Wybór
  misji szedł trzema przebiegami — co bot niesie, co stoi na jego mapie, pierwsza
  niezrobiona — i ten trzeci wręczał postaci z Doliny Orków zbiórkę z poziomu
  piętnastego, której potwór stoi w Joan. Bot tam nie chodzi, więc łańcuch stawał
  na tym wierszu i nie ruszał się dalej. Siedem etapów Biologa to siedem osobnych
  zadań, nie jeden łańcuch, więc wiersz wyrośnięty o dziesięć poziomów jest teraz
  pomijany zamiast blokować wszystko za sobą, a gdy wyrośnięte są już wszystkie,
  bot bierze najwyższy, jaki mu został — czyli Ząb Orka, po który i tak chodzi.

- **Konsola restartu w panelu zaawansowanym nikogo o restart nie prosiła.**
  Zgłoszone z Discorda: „Zleć restart" nic nie robi, a konsola stoi na „Ostatni
  ukończony restart: brak zarejestrowanych danych". Panel publikował własny plik
  `server-settings.request`, którego po stronie gry nie czyta nikt — kontener
  pilnuje pliku `request` i tylko jego. Nikt tego pliku również nie kasował, więc
  po pierwszym kliknięciu każde następne było odrzucane jako „poprzednie zlecenie
  nadal trwa", i to na stałe. Teraz oba przyciski zlecają restart tą samą drogą,
  którą od zawsze działa strona mnożników, a blokada podwójnego kliknięcia wygasa
  po dziesięciu minutach, żeby milczący kontener nie zablokował konsoli na dobre.
  To jest ta droga, którą wchodzą zmiany wprowadzone ręcznie w bazie: rdzenie
  czytają `item_proto` tylko przy starcie.

### Zmienione

- **Nieotwarte skrzynki trafiają na lady.** Zaproponowane na Discordzie, żeby boty
  wystawiały blaski i szkatułki zamiast otwierać wszystko. Większość i tak się
  otwiera — stamtąd biorą mikstury i wzmocnienia — ale dwa rodzaje idą na ladę:
  te, których silnik na tym serwerze nie otworzy w ogóle (50192 i 50193, w tej
  chwili blisko osiemset sztuk zajmujących po jednej komórce w plecakach), oraz nadwyżka stosu
  od pięciu sztuk w górę. Nieotwarte pudełko to jedyna rzecz na tym rynku, na
  którą gracz może zagrać w ciemno, a dotąd nie było ani jednego. Bot nie próbuje
  otworzyć pudełka, które sam wystawił: silnik odmawia na zablokowanym
  przedmiocie, a taka odmowa jest zapamiętywana dla całego świata i uciszyłaby
  otwieranie u wszystkich. Kupującym jest tu gracz, nie bot: żaden bot nie ma w
  sobie powodu, żeby kupić pudełko, i to się nie zmienia. Zmierzone: cztery
  odmowy silnika zapisane w ciągu pół godziny, czyli warunek wystawienia jest
  spełniony — sama lada nie jest w logu widoczna poza najlepszą linią, więc
  pudełko na straganie zobaczycie w grze, nie w pomiarze.

### Czego w tym wydaniu nie ma

- Respawn ustawiany z panelu zaawansowanego nadal nie działa — po stronie gry nie
  ma modułu, który zapisywałby pliki `regen.txt`. Panel przestał przynajmniej
  twierdzić, że zadziałał.
- Stackowanie odłamków: `Odłamek Smoczego Kamienia` (30270) nie ma w `item_proto`
  flagi stosu, więc każda sztuka zajmuje osobną komórkę. To zmiana w danych
  serwera i klienta naraz, nie w kodzie botów.
- Zakładki w składzie i misja na powiększenie plecaka — to funkcje silnika, nie AI.

---

## 1.30.19 — 2026-09-08

### Nowe

- **Launcher po angielsku.** Na dole okna jest przycisk „JĘZYK / LANGUAGE" —
  przełącza całe okno między polskim a angielskim i zapamiętuje wybór w
  `.m2launcher.json`, więc następne uruchomienie startuje w wybranym języku.
  Przetłumaczony jest interfejs launchera: przyciski, nagłówki, okna wyboru
  botów, panelu i importu bazy. **Panele WWW zostają po polsku** — to dwie
  osobne aplikacje z ponad tysiącem własnych napisów każda i ich tłumaczenie to
  oddzielna robota, nie dopisek do tego wydania.

### Naprawione

- **Boty wreszcie chodzą do Biologa.** Ząb Orka stał na 0/10 dla całego świata,
  a 700 botów nosiło 2219 zębów w plecakach — po trzy na głowę. Powód: wyprawa
  do Biologa zaczynała się dopiero, gdy bot miał **cały** brakujący komplet
  naraz, czyli dziesięć sztuk. Miało to dziesięć osób w całym świecie.
  Tymczasem samo oddawanie zawsze działało po jednej sztuce, z sześćdziesięciu-
  procentową szansą przyjęcia — więc na komplet nie było na co czekać. Teraz
  wystarczą cztery sztuki, żeby wyprawa się opłacała, i ten sam próg otwiera
  drogę z Bokjung do Joan. Zmierzone przez pierwsze minuty po wdrożeniu:
  1742 oddanych okazów.
- **Szanse w małżu były cztery razy zawyżone.** Kod AI zakładał 10% białej
  perły, 7% niebieskiej i 3% krwawej. Silnik ma dwie tabele wybierane flagą
  `g_iUseLocale`, a `common.locale` tego świata to **english**, co ustawia tę
  flagę — czyli obowiązuje druga tabela: 50% kamień, 45% nic, **2% / 2% / 1%**
  na perły. Każda decyzja „otworzyć czy sprzedać" liczyła się więc z wartości
  cztery razy za wysokiej. Stałe poprawione na te, które silnik naprawdę
  stosuje.
- **Aura Miecza przestaje kosztować tyle co byle księga.** Rynek pamiętał ceny
  po numerze przedmiotu, a każda zwykła księga to ten sam numer 50300 — skill
  siedzi w gnieździe. Sprzedaż czyjejś zbędnej księgi ustawiała więc cenę Aury,
  a sprzedaż Aury cenę wszystkich pozostałych. Klucz rynku zawiera teraz
  umiejętność: każda księga ma własną historię cen, własny limit kroku ceny i
  własną cenę startową (Aura 250 tys., Czarowane Ostrze 220 tys., Silne Ciało
  180 tys., zwykłe od 45 tys.). Perły dostały to samo — 2 / 3 / 6 mln.
- **Boty kupują wreszcie księgi umiejętności.** W kodzie kupującego nie było
  dla nich żadnej gałęzi, więc żaden bot nigdy nie kupił księgi ze straganu —
  same wisiały. Teraz bot bierze księgę swojej profesji i swojego skilla,
  dopóki nie ma jeszcze roboczego zapasu i dopóki skill da się jeszcze
  podnieść. Bez kupujących samo podniesienie ceny zrobiłoby tylko drogie,
  niesprzedające się sklepy.
- **Księga obcej profesji nie idzie już do handlarza za grosze.** Aura
  znaleziona przez ninję była złomem — teraz trafia na stragan, gdzie stoi po
  nią wojownik.
- **Cena mogła skoczyć przy każdym wywołaniu.** Ogranicznik liczył
  `1 + czas/interwał`, więc nawet przy zerowym czasie dawał jeden pełny krok, a
  każdy krok zerował zegar. Czterdzieści straganów otwartych w tej samej minucie
  przesuwało wspólną kotwicę czterdzieści razy, mimo komentarza o pięciu
  procentach na dziesięć minut. Teraz liczą się wyłącznie pełne interwały.

### Zmienione

- **W Bokjung stoi najwyżej siedem straganów.** Ósmy kupiec zabiera towar do
  Joan zamiast dokładać ladę, której i tak nikt nie zobaczy. A kupujący
  zaglądają **najpierw do Joan** — dopiero gdy tam niczego nie znajdą, przez
  dziesięć minut wolno im szukać w Bokjung. To jest to, co ożywia drugie
  miasto: nie sam stragan, tylko klienci, którzy do niego przychodzą.
  Zmierzone: 20 straganow w Joan przeciwko dokladnie siedmiu w Bokjung straganów przeniesionych do Joan i 300 żywych
  botów na jej mapie zamiast dziewiętnastu z rana.

---

## 1.30.18 — 2026-09-08

### Naprawione

- **Niedokończona sprawa w mieście przestaje trafiać do przypadkowej walki.**
  To była pętla opisana w audycie z 8 września i widać ją w logu jak na dłoni:
  bot potrzebuje handlarza → trasa zostaje odroczona przez budżet planowania →
  po dziewięćdziesięciu sekundach bezruchu budzi go watchdog → wizyta zostaje
  skasowana → sekundę później bot rzuca umiejętność w pierwszego moba obok, a
  potrzeba, po którą przyszedł, dalej jest niezaspokojona. I tak w kółko, z
  zapasami topniejącymi po drodze.
  Watchdog nadal robi to, do czego służy — kasuje martwą trasę i odblokowuje
  postać — ale **sprawa zostaje przy bocie**. Dostaje własny termin ponowienia
  (15–40 s), a do tego czasu bot jest klientem, nie myśliwym: zwykłe walki są
  dla niego zamknięte, obrona nie. Sprawa, której nie da się załatwić przez
  piętnaście minut, jest jawnie porzucana z powodem w logu, żeby nic nie mogło
  utknąć na zawsze.
- **Bokjung przestaje być expowiskiem dla tych, którzy z niego wyrośli.**
  Filtr opłacalności odcinał skrajnie słabe cele, ale nie zabraniał grindu na
  mapie, z której bot już wyrósł — a to dwie różne reguły i audyt słusznie się
  tego czepił. Powyżej progu kohorty (35) Bokjung jest miejscem, gdzie można
  kupować, przechodzić, handlować i **dokończyć konkretne zadanie** — z nazwanym
  potworem albo z materiałem, którego naprawdę brakuje i który realnie z niego
  wypada. Samo „mam ambicję Metiny" albo „mam ambicję konia" nie jest zgodą na
  polowanie.
  Reguła obowiązuje wszystkie drogi do walki, nie tylko wybór nowego celu:
  wspólny cel drużyny, cel już trzymany, przeciwnik zaangażowany, podciąganie
  grup i lur łucznika. Ratowanie życia jest poza nią — bot bije się z tym, co
  bije jego, gdziekolwiek stoi.
- **Zamiar wyjazdu przeżywa wizytę i watchdog.** Bot, który wrócił do miasta po
  zapasy, pamięta teraz, dokąd zmierzał. Zakupy odraczają wyjazd, ale go nie
  kasują, a po załatwieniu sprawy nie trzeba czekać na kolejne losowanie
  ambicji. W logu widać to jako `PLAYERBOT_DEPARTURE: held`.

### Dla ciekawych

- **Odroczenie trasy mówi wreszcie, które ograniczenie ją wstrzymało.** Trzy
  różne budżety — plany na takt, czas planowania na takt i dalekie trasy na
  minutę — zwracały jedną i tę samą odpowiedź, więc „odroczono" bywało czytane
  jako „nie ma drogi". Log podaje teraz powód i to, jak długo bot czeka — i od
  razu się to opłaciło: przez 26 minut **108 odroczających to limit planów na
  takt, 10 to budżet czasu, a limit dalekich tras nie zatrzymał ani jednej**.
  Audyt ostrzegał, żeby nie zakładać, że chodzi o dalekie trasy, i miał rację.
- **Każdy bot 40+ w Bokjung ma odczytywalny powód i następny krok.** Rdzeń pisze
  `PLAYERBOT_M2: why` dla rotacyjnej garstki botów na minutę: poziom, cel, czy
  wolno mu tu polować, stan sprawy i jej wiek, mapa docelowa wyjazdu, stan
  mikstur, aktualny cel walki wraz z powodem, w którym miejscu jest trasa i jak
  długo czeka na planowanie. To odpowiedź na zarzut audytu, że po samym opisie
  akcji nie da się orzec, czy bot działa sensownie.
  Zmierzone przez 26 minut po wdrożeniu: 2870 odmów walki z powodu
  reguły mapy, 422 zapamiętanych zamiarów wyjazdu, 9 (z czego 4 zakonczone zakupem, zero porzuconych)
  spraw przejętych przez naprawę po watchdogu.
- Czego **nie** zrobiłem z tego audytu: sprawiedliwej kolejki planowania tras z
  wiekiem zlecenia i rezerwacją części budżetu dla usług krytycznych. To
  przebudowa gorącej ścieżki wydajnościowej i chcę ją mierzyć osobno, a nie
  doklejać do wydania naprawiającego pętlę usług. Odroczenia są na razie tylko
  opisane w logu.

---

## 1.30.17 — 2026-09-08

### Zmienione

- **Bot mówi nad głową, co robi i po co.** Do tej pory opis mówił o czynności i
  milczał o jej celu — a czasem obie części sobie przeczyły: „Szukam miejsca do
  expa (cel: zapasy)" wisiało nad postacią idącą do handlarza. Teraz:
  - podróż nazywa miejsce i powód — „Idę do Doliny Orków (cel: poziom)",
    „Idę do miasta po zapasy", „Idę do kowala ulepszyć ekwipunek", „Idę do
    Biologa", „Idę nad rzekę łowić ryby";
  - wizyta po zapasy pokazuje stan mikstur, czyli jedyną rzecz, którą da się
    sprawdzić w ekwipunku — „Kupuje potki i sprzedaje lup - potki 143/86";
  - walka mówi, **dlaczego ta walka** — „Bronię się przed …", „Pomagam
    drużynie: …", „Zbieram materiał z …" zamiast samego „Walczę z …". Powód
    bierze się z tego samego modułu, który decyduje, czy walka ma sens, a nie
    ze zgadywania po tekście.
- **Joan ma po co żyć.** Bot, który załatwi sprawę albo skończy łowienie w Joan,
  zostaje teraz na cztery do dziesięciu minut na rynku zamiast wychodzić w pole w
  tej samej sekundzie —
  a wędkarzy jest więcej (8 na stu zamiast 2, a wśród rozważnych zbieraczy 30
  zamiast 20). Łowienie to jedyna czynność, która sama z siebie prowadzi bota do
  Joan: brzeg, Rybak sprzedający przynętę i pierścień straganów leżą na tej
  samej mapie, więc wędkarz jest przy okazji klientem i sprzedawcą.
  Bokjung świadomie pominięty — tam tłok jest problemem, nie brakiem.

### Dla ciekawych

- Poprzednia wersja opierała się na złym pomiarze i trzeba to sprostować:
  kolumna `map_index` w bazie to **ostatnia zapisana pozycja każdego
  zarejestrowanego bota**, także tych niewłączonych. Mówiła o 400 botach na
  mapie Joan, podczas gdy plik statusów — a ten zawiera wyłącznie żywe postacie
  — mówił o 19 na 837. Stąd pusty rynek: nie brakowało straganów,
  brakowało ludzi, bo prawie cała żyjąca populacja to poziom 40+, a ci dawno
  wyjechali na pogranicze. Po zmianie w Joan stoi 52 botów — prawie
  trzy razy więcej, i to zasługa samych wędkarzy.
- Odpoczynek na rynku jest w tej wersji **niepotwierdzony w grze**. Kod jest
  wdrożony i sprawdzony kompilatorem, ale jego wyzwalacze — załatwiona sprawa w
  Joan albo skończona sesja wędkarska — zdarzają się rzadko, a sesja trwa od
  piętnastu do czterdziestu minut, więc każde przebudowanie serwera zerowało
  licznik, zanim cokolwiek zdążyło się wydarzyć. Zobaczymy to dopiero po
  dłuższej pracy bez restartu.

---

## 1.30.16 — 2026-09-08

### Naprawione

- **Aura, szał i zaklęcia wchodzą od razu, a nie po kolei co pięć sekund.**
  Rzucenie buffa zajmuje całą turę bota, a kolejnej próby nie było przez pięć
  sekund — więc wojownik potrzebował dziesięciu sekund na aurę i szał, a sura
  broni piętnastu na trzy zaklęcia. Aura Miecza trwa od trzydziestu sekund i ma
  trzydziestosekundowy cooldown, więc bot spędzał na jej odnawianiu tyle czasu,
  ile trwała, i przez większość walk stał bez niej. Po rzuceniu jednego buffa
  bot wraca po następny po 1,2 sekundy; pełny zestaw staje w trzy sekundy
  zamiast piętnastu, a zwykłe pięć sekund wraca, gdy niczego nie brakuje.
- **Trująca chmura i trująca strzała nie lecą już w kamień Metin.** Rotacja
  bierze pierwszą umiejętność, która zeszła z cooldownu, a kamień trwa
  wystarczająco długo, żeby zdjąć z listy te dobre — więc w kamień szła ta
  obszarowa, czyli akurat najsłabsza na jeden cel. Trująca Chmura to
  `-(lv*2 + (atk + str*3 + dex*18)*k)` przy `-(atk + (1,6*atk + …))` Szybkiego
  Ataku: jedna wartość ataku wobec dwóch i pół, za te same 1,4 sekundy blokady
  animacji. Kamień nigdy nie jest tłumem, więc bot pomija obszarówki i wraca do
  zwykłych ciosów, które w tym czasie zadają więcej. Silnik jest pytany o flagę
  `SPLASH`, więc serwer z inną tablicą umiejętności też dostanie dobrą odpowiedź.
- **Perła kosztuje jak perła, a nie jak małż.** Ceny na straganach mają podłogę
  liczoną z zasobności kupujących — i ta podłoga była jedna dla wszystkiego. Przy
  medianie portfela 2,6 mln wypadała na ~38 tysiącach, więc małż, którego
  handlarz wycenia na 3 000, i biała perła za 12 000 stały na ladzie w tej samej
  cenie, a krwawa perła ledwie wyżej. Podłoga jest teraz skalowana tym, ile
  handlarz płaci za tę konkretną rzecz — i **tylko w górę**, więc nic nie
  tanieje: biała perła idzie do ok. 150 tys., krwawa do ok. 300 tys., a małż
  zostaje tam, gdzie był.
  Do tego niedobór wreszcie coś znaczy: dopłata za brak towaru mogła podnieść
  cenę najwyżej o jedną trzecią, co przy pięciuset botach szukających materiału,
  którego nie ma na żadnym straganie, nie jest odpowiedzią rynku. Teraz sięga
  dwukrotności.
- **Stragany stają w Joan.** Bot losował miasto dla każdego straganu — dziewięć
  razy na dziesięć Joan — a potem odmawiał otwarcia, jeśli akurat tam nie stał.
  Ponieważ boty z towarem stoją w Bokjung, dziewięć losowań na dziesięć szło do
  kosza i w Joan nie było ani jednego straganu, czyli dokładnie odwrotnie, niż
  to losowanie miało robić. Kupiec handluje teraz w mieście, w którym stoi.
  Na mapie 21 jest 399 botów, a przy jej rynku stało pięciu —
  przeglądanie straganów i tak zawsze czytało pierścień tej mapy, na której jest
  bot, więc stragan w Joan ma od razu swoich klientów.

---

## 1.30.15 — 2026-09-08

### Nowe

- **Ninja łucznik podciąga potwory dla drużyny.** W drużynie pięciu i więcej
  jeden łucznik dostaje rolę lurera: wybiega, budzi paczkę jednym zwykłym
  strzałem, sprawdza, czy faktycznie za nim ruszyła, i prowadzi ją z powrotem
  do towarzyszy, którzy ją przejmują normalną walką.
  Zastępuje to dawne okazjonalne strzelanie w bok, które nie było
  podciąganiem: łucznik pukał w jednego potwora, dopisywał sobie obrażenia,
  gdy prawdziwe wyszły za niskie, i wracał do swojego celu — nikt na to nie
  czekał i nic z tego nie wynikało.
  Kurs ma swoje granice i każda z nich broni przed konkretną wpadką: dwanaście
  sekund na zbieranie, smycz 4500 jednostek od miejsca zbiórki, przerwanie
  przy spadku HP, jeden lurer na drużynę i limit potworów, który drużyna
  podnosi dopiero po kilku udanych kursach. Odbiorca musi żyć i stać na
  miejscu — a to, że sam ninja się oddala, nie unieważnia jego własnej misji.
  Liczy się to, co wróciło, nie to, ile razy strzelono: potwór zabity strzałem
  albo taki, który nie zareagował, nie jest dostarczony. Nad głową widać etap:
  „Luruje dla PT", „Wracam do druzyny: prowadze 9 mobow", „Przekazuje moby".
  Agresja potworów nie jest przy tym nigdzie podmieniana — drużyna przejmuje
  je tak, jak przejmuje wszystko inne, i przejęcie bywa częściowe.

### Naprawione

- **Bot broni się tak długo, jak jest bity.** W 1.30.14 ograniczyliśmy epizod
  obrony do dziesięciu sekund, żeby „ono zaatakowało pierwsze" nie było
  wymówką do grindu. Skutek uboczny był dotkliwy: po dziesięciu sekundach
  potwór, który wciąż zabijał bota, przestawał być dopuszczalnym celem —
  postać stała bezczynnie albo uciekała i ginęła. Przy silnym potworze
  dochodziło do tego drugie zabezpieczenie, które porzucało cel dziesięć
  poziomów wyżej nawet wtedy, gdy ten cel właśnie bił.
  Obronę własną ogranicza teraz **smycz, nie zegar**: bot odpowiada temu, co
  go bije, tak długo, jak go bije, ale nie daje się przy tym wywlec z miejsca,
  w którym walka się zaczęła. Od zrywania przegranej walki jest ucieczka i ona
  dalej ma pierwszeństwo. Pomoc towarzyszowi z drużyny zostaje ograniczona
  także czasem — bronić siebie trzeba, pomagać można.
- **Gildia jedzie na bossa dopiero wtedy, gdy ktoś go widzi.** Raz wybrany
  punkt polowania trzymał się cztery minuty **bez ponownego pytania, czy boss
  jeszcze stoi**. Boss padał, a boty dalej szły na współrzędne z tabeli i tam
  stały — stąd te kolumny postaci w szczerym polu. Teraz punkt bossa jest
  sprawdzany na bieżąco i gdy bossa nie ma, boty wracają do swojej roboty.
  Do tego boss przestał być wart tyle, że opłacał się każdemu: **kto go
  zobaczy, woła swoją gildię**, i to ta gildia ma pierwszeństwo do dwunastu
  miejsc, a reszta świata do sześciu. Na żywo: sto czterdzieści pięć postaci
  ruszających na jednego potwora spadło do trzynastu, a w logu pojawiły się
  wołania w rodzaju „Wodz Orkow stoi! Zbieramy sie na niego."
- **Śmierć wygląda jak śmierć gracza.** Ciało leży dziesięć sekund i dopiero
  potem postać wstaje — ale wstawała niewidzialna na dziesięć sekund, dwa razy
  dłużej niż człowiek po `restart_here`. Teraz to te same pięć sekund, które
  silnik daje graczowi.
- **Wędkarz nie tonie we własnym połowie.** Ryby otwierały się tylko między
  zarzuceniami, więc bot, który odszedł od brzegu, nosił je ze sobą — a żywa
  ryba się nie stackuje, więc trzydzieści ryb to trzydzieści pól i plecak bez
  miejsca na cokolwiek innego. Połów jest teraz opracowywany wszędzie, przy
  okazji zwykłego utrzymania. W plecakach świata nie została ani jedna
  nieotwarta ryba.
- **Panel: wróciła ramka okna ekwipunku.** Style panelu odwołują się do
  `inventory-background.png`, którego nie ma w żadnej paczce autora — ani w
  1.37.1, ani w 1.30.1 — więc u wszystkich poza nim okno ekwipunku było płaskim
  tłem z ikonami. Grafika z klienta nie jest nasza do rozprowadzania, więc
  narysowaliśmy własną ramkę w dokładnie tej geometrii, której oczekują style:
  wnęki na dwanaście gniazd ekwipunku, siatka pięć na dziewięć i pasek na yang.
- **Launcher mówi, który plik zablokował antywirus.** Gdy Windows przerywa
  aktualizację komunikatem „plik zawiera wirusa lub potencjalnie niechciane
  oprogramowanie", w logu zostawało samo to zdanie — bez nazwy pliku, czyli bez
  niczego, co dałoby się sprawdzić. Teraz launcher rozpoznaje ten błąd przy
  pobieraniu, przy rozpakowywaniu każdego pliku z osobna i przy wgrywaniu na
  miejsce, podaje ścieżkę, przypomina, że nic nie zostało zainstalowane i że
  poprzednia wersja działa dalej, oraz podpowiada wykluczenie w Zabezpieczeniach
  Windows.

### Zmienione

- **Małże są towarem, nie losem na loterii.** Pierwsze cztery bot trzyma
  zawsze — dwadzieścia sześć receptur zużywa małża takiego, jaki jest, i tyle
  właśnie za niego płacą. Otwiera dopiero nadmiar, i tylko wtedy, gdy
  oczekiwana wartość perły bije cenę całej sztuki.
- **Farba do włosów trafia na stragany, a raz w życiu na głowę bota.** Silnik
  przyjmuje ją wprost, kolor jest trwały, więc bot, który ją znajdzie, farbuje
  się raz — a reszta idzie do sprzedaży zamiast do handlarza jako złom. Osiemset
  postaci przestaje wyglądać jak jedna skopiowana osiemset razy.

---

## 1.30.14 — 2026-09-07

### Zmienione

- **Bot bije to, z czego cokolwiek ma.** Wysokopoziomowe boty koczowały w
  Bokjung i tłukły potwory dwadzieścia poziomów niżej. Silnik mnoży przez
  `aiPercentByDeltaLev` zarówno doświadczenie, jak i drop: piętnaście poziomów
  nad potworem to jeden procent jednego i drugiego, więc z takiego grindu nie
  było nic poza zajętą mapą i zatrzymanym rozwojem postaci.
  Decyzję „czy ta walka ma sens" podejmuje teraz jeden wspólny moduł i
  podejmuje ją tak samo w każdym miejscu, które pyta: przy wyborze nowego
  celu, przy podciąganiu grup i — co trzy sekundy — dla potwora, którego bot
  już bije. Wcześniej filtr działał tylko przy wyborze, więc przeciwnik wzięty
  chwilę przed zmianą zadania był bity do końca.
  Powody, dla których wolno walczyć, są policzalne: realne doświadczenie,
  potwór z aktualnego zadania, brakujący materiał do ulepszenia, kamień Metin
  i ograniczona obrona. Nic więcej.
- **Obrona ma koniec, także kiedy zmienia się napastnik.** Wyjątek „ono
  zaatakowało pierwsze" musi być ograniczony, bo inaczej jest pozwoleniem na
  dowolny grind. W pierwszej wersji epizod obrony był liczony osobno dla
  każdego napastnika — dwa potwory na zmianę utrzymywały go więc bez końca.
  Teraz epizod należy do bota: dopóki trwa, odpiera każdego napastnika w
  swoim czasie i w swoim promieniu, a nowy zaczyna się dopiero wtedy, gdy
  walka faktycznie ustała na kilkanaście sekund. Obrona towarzysza z drużyny
  mieści się w tym samym epizodzie, więc jest ograniczona nie tylko
  odległością, ale i czasem.
- **Potrzeba materiału nie usprawiedliwia polowania na coś, co go nie da.**
  Wyjątek materiałowy sprawdzał, czy botowi rzeczywiście brakuje surowca do
  receptury — i tylko to. Drop podlega jednak temu samemu przelicznikowi
  poziomów co doświadczenie, więc „potrzebuję" potrafiło wysłać postać na
  potwora, z którego ten materiał praktycznie nie wypada. Teraz wyjątek
  wymaga jeszcze realnej szansy dropu.
- **Panel seban latino w wersji 1.37.1, tym razem w całości.** Poprzednie
  wdrożenie było zlepkiem starszej wersji z naszymi poprawkami: brakowało
  grafik, styli i oryginalnego layoutu. Teraz jest pełny pakiet autora —
  szablony, style i 1599 plików statycznych — z zachowanymi dwiema naszymi
  poprawkami: pierwsza migawka kolektora robi się od razu zamiast po pięciu
  minutach, a pulpit nie wywraca się na świeżej bazie, w której nie ma
  jeszcze tabeli migawek. Panel zna też wreszcie wersję serwera, na który
  patrzy, zamiast pokazywać „nieustawiona".
- **„OTWÓRZ PANEL WWW" pyta, który panel.** Panele są dwa, działają
  jednocześnie i żaden nie zastępuje drugiego, więc przycisk nie decyduje za
  nikogo: pokazuje wybór między **oryginalnym panelem** (mapa i sterowanie) a
  **zaawansowanym panelem seban latino** (profile, rankingi, gospodarka,
  obciążenie). Porty odczytuje z `.env` tej instalacji, więc świat, który je
  przesunął, otwiera się pod właściwym adresem.

### Dla ciekawych

- Rdzeń pisze teraz raz na minutę linię `PLAYERBOT_M2: census` — ilu botów od
  czterdziestego poziomu stoi w Bokjung i z jakiego powodu (zadanie,
  materiały, wizyta, podróż, obrona, brak planu) — oraz `PLAYERBOT_M2: left
  after errand` z czasem, jaki bot potrzebował na opuszczenie mapy po
  załatwieniu swojej sprawy. Sama liczba postaci w mieście nigdy nie
  odpowiadała na pytanie, czy coś jest zepsute; te dwie linie odpowiadają.
  Zmierzone na żywo: przez dziesięć minut w Bokjung stało od 45 do 60 botów od czterdziestego poziomu wzwyż i każdy z konkretnego powodu — 297 razy zadanie, 197 razy wizyta u handlarza, 11 razy obrona, ani razu „brak planu"; 222 wyjścia z mapy po załatwionej sprawie, mediana 21 sekund, 182 z nich poniżej pół minuty; 1872 odmowy walki, wszystkie z powodu zerowego doświadczenia.

---

## 1.30.13 — 2026-09-07

### Zmienione

- **Boty dochodzą do portalu, zamiast znikać dziewięć metrów przed nim.**
  Zmiana mapy nigdy nie mogła iść przez silnikowy portal: `WarpSet` każe
  klientowi połączyć się z rdzeniem, który obsługuje mapę docelową, a bot nie
  ma klienta, który by odpowiedział — zostałby po prostu porzucony przy
  portalu. Dlatego przejście robiliśmy po stronie serwera z bezpiecznym
  zapasem 900 jednostek, i to ten zapas widać było w grze: postać biegła do
  wyjścia i znikała w szczerym polu.
  Nowa łatka silnika **0008** każe `warp_npc_event` pomijać boty, więc zapas
  nie musi już chronić przed niczym — przejście robi się 200 jednostek od
  portalu, czyli bot dochodzi pod sam NPC i znika tam, gdzie znika gracz.
  Portale wewnątrz mapy (te w Lochu Małp) działają jak dotąd: to lokalne
  przeniesienie, nie zmiana rdzenia, i łatka ich nie dotyka.
  Sprawdzone na żywo: 398 przejść między mapami w dziewięć minut, w tym
  dwanaście wejść i dwanaście wyjść z Lochu Pająków, i ani jeden zgubiony bot.
- **Poprawka prywatnych straganów dociera wreszcie do graczy.** Łatka 0004
  zamieniła w `OpenMyShop` test `GetPart(PART_MAIN) > 2` na `IsPolymorphed()`
  — bez tego silnik odmawia otwarcia straganu każdemu, kto ma na sobie zbroję,
  również żywemu graczowi. Łatki silnika trafiają do gracza wyłącznie jako
  gotowy plik z listy aktualizacji, a `char.cpp` na tej liście nie było, więc
  ta poprawka od początku działała tylko na maszynie deweloperskiej. Teraz
  plik jest wysyłany razem z resztą.

- **Bot z celem „zapasy" nie zaczynał po nie iść.** Planista i wykonawca
  zadawali dwa różne pytania o mikstury. `NeedsPlayerBotPotions` liczy sztuki i
  mówi „trzeba" przy czerwonych poniżej 150 albo niebieskich poniżej 100 — i na
  tym stawia cel RESTOCK. Wyzwalacz wizyty liczył natomiast **stosy**, patrzył
  wyłącznie na cztery czerwone numery przedmiotów, niebieskich nie widział
  wcale, i odpalał się dopiero przy zerze mikstur w co najmniej w połowie pełnym
  plecaku. Bot z jednym stosem 32 czerwonych i 56 niebieskich nosił więc cel
  „zapasy", którego wizyta nigdy nie zaczynała, i stał w Bokjung bijąc, co
  akurat przeszło obok — 116 botów poziomu 40 i wyżej siedziało tak na M2.
  Wyzwalacz pyta teraz o dokładnie to samo, co planista. Pomiar po zmianie, w
  trzynaście minut: 944 rozpoczęte wizyty u handlarzy (w tym 333 u handlarki
  różności, gdzie kupuje się mikstury), 311 wyjazdów z M2 na mapy dalsze i
  spadek populacji 40+ w mieście do 93. Pętli zakupowych to nie tworzy: wizyty
  nadal bramkuje pięcio-dziesięciominutowy odstęp, a warunek wymaga pieniędzy
  na wyjazd.

  Ustalenie z audytu przekazanego przez Tieru; sprawdzone w kodzie, który
  właśnie zmieniałem, a nie w starszej kopii z buildera.

Zgłoszenie: Tieru.

---

## 1.30.12 — 2026-09-07

### Naprawione

- **Boty siedziały na tysiącach nieotwartych Szkatułek Blasku.** Przebieg
  otwierania kończył się na pierwszej skrzynce, której silnik nie otwiera —
  Skrzynia Eksperta III (50192) i Skrzynia Mistrza I (50193), razem blisko
  sześć tysięcy odmów na minutę — i przez to nigdy nie docierał do szkatułek
  leżących za nimi w plecaku. Do tego stał na samym końcu taktu, za walką,
  łupem, podróżą, miastem i wędrówką, z których każde przejmuje turę.
  Zmierzone przed zmianą: **9723 szkatułki u 587 botów**, największy stos 106,
  a otwieranych 190 na godzinę; plecaki miały średnio 29 zajętych kratek z 90,
  więc miejsce nie było przeszkodą. Po zmianie zaległość zeszła do **887 sztuk
  u 44 botów w osiem minut**, w szczycie 380 otwarć na minutę. Odmowa pomija
  teraz jedną skrzynkę zamiast kończyć przebieg i jest zapamiętywana na
  dziesięć minut, żeby bot nie pytał o to samo co osiem sekund.
- **Stragany wyceniały bonusy na zero.** Wszystko, co ustalało cenę — tabela
  sprzedawcy, pamięć sprzedaży, ogranicznik kroku — jest kluczowane numerem
  przedmiotu i poziomem ulepszenia, czyli dokładnie tą parą, która nie
  odróżnia butów +7 z pięcioma liniami bonusów od butów +7 bez żadnej. Obie
  szły po 150 000. Teraz do ceny dochodzi 25% za każdą linię, dodatkowe 100%
  od czwartej linii wzwyż i 80% za każdą rolkę, na której gracz się zatrzymuje
  (2000 PŻ, 10% krytyku, 10% przebicia, odporność na ogłuszenie), przy suficie
  600%. Premia obejmuje także ceny płaskie za +7, +8 i +9 oraz złom — one
  wychodziły z wyceny wcześniej i to je właśnie widać było na straganach.
- **Diagnostyka launchera meldowała „OK", gdy silnik Dockera odmawiał.**
  `docker info` kończy się kodem 0, choć zamiast wersji wypisuje odmowę demona,
  więc w logu gracza stało „OK: Docker Engine odpowiada (wersja Error response
  from daemon: Docker Desktop is unable to start)" i werdykt „można uruchomić
  serwer" — sześć razy z rzędu. Ostrzeżenie o zepsutym WSL, jedyne, które mówi
  co naprawić, podnosimy tylko gdy silnik jest znany jako wyłączony, więc przy
  fałszywym „OK" nie pojawiało się wcale. Za wersję uznajemy teraz wyłącznie to,
  co wygląda jak wersja; przy każdej innej odpowiedzi diagnostyka pokazuje
  dosłowną treść odmowy demona.

Zgłoszenie: Tieru, OskarPWA, BibiSiu.

---

## 1.30.11 — 2026-09-07

### Zmienione

- **Bot nie czeka już między księgami umiejętności.** Silnik trzyma od
  osiemnastu do trzydziestu godzin przerwy między dwoma czytaniami tej samej
  umiejętności; przełącznik KSIĘGI w panelu i tak ją zdejmował, ale bot
  narzucał sobie w zamian własne pół godziny. Tego półgodzinnego oczekiwania
  już nie ma: bot czyta wtedy, kiedy ma co czytać.
  Nie zmieniło się nic z tego, co decyduje, jak daleko umiejętność zajdzie, bo
  to reguły silnika: 20 000 punktów doświadczenia pobieranych za każde
  czytanie, losowanie o powodzenie i liczba udanych czytań potrzebnych na
  kolejny poziom mistrzowski, aż do G.

  Pomiar na 638 botach pokazał przy okazji, gdzie naprawdę jest wąskie gardło:
  480 botów ma umiejętność na Mistrzu, 326 z nich nosi jakieś księgi, ale tylko
  **44 mają księgę tej właśnie umiejętności**. Czytań przybyło (z jednego na
  dziewięć minut do jednego na dwie i pół minuty na całą populację), lecz
  tempo rozwoju umiejętności ogranicza teraz podaż właściwych ksiąg, a nie
  żaden zegar.

Zgłoszenie: Tieru.

---

## 1.30.10 — 2026-09-07

### Nowe

- **Każdy bot nosi Trzecią Rękę.** Z nią silnik dopisuje yang z zabitego
  potwora prosto do sakiewki zabójcy, zamiast rozsypywać kupki monet po ziemi
  (`CHARACTER::RewardGold` pyta o `UNIQUE_GROUP_AUTOLOOT`). Dla bota to nie
  wygoda, tylko czas: dojście do każdej kupki kosztuje wyliczenie trasy, a te,
  do których nie zdąży, i tak znikają — teraz bot zamiast biegać po monetach
  bije dalej, a na terenach łowieckich przestaje zalegać yang, którego nikt nie
  podnosi. Boty nie mają sklepu z przedmiotami, więc przedmiot jest im nadawany,
  a jego zegar zużycia nakręcany — tak samo jak `ManagePlayerBotSkillBooks`
  kasuje osiemnastogodzinną przerwę między czytaniem tej samej księgi.

Zgłoszenie: OskarPWA.

---

## 1.30.9 — 2026-09-07

### Naprawione

- **Boty tłoczyły się w jednym korytarzu Lochu Małp i nie korzystały z reszty.**
  Labirynt nie jest jedną przestrzenią. `server_attr` dzieli go na jedenaście
  osobnych komnat — dziewięć pokoi z regenu i dwie sale bossów — a łączą je
  wyłącznie NPC-e przenoszące, które teleportują każdego, kto podejdzie na trzy
  metry (silnik sprawdza to dwa razy na sekundę, nic się nie klika). Wybór
  pokoju pytał nawigację, czy da się tam dojść po ziemi, a ta odpowiada tylko za
  komnatę, w której bot stoi — więc każdy bot znajdował jeden pokój z ośmiu w
  tablicy, ten swój, i szedł na ten sam punkt spawnu co wszyscy, którzy weszli
  przez wejście. W godzinie logów: 130 wypraw do lochu i ani jedno zaplanowane
  przejście portalem, a w raporcie gęstości ze wszystkich trzech lochów były
  wyłącznie komórki komnaty wejściowej. Trzy komnaty — w tym największa, z
  dziewiętnastoma punktami spawnu, i obie sale bossów — nie miały nawet wpisu.
  Teraz bot patroluje punkty spawnu komnaty, w której stoi, a po czterech
  minutach idzie do przejścia prowadzącego do sąsiedniej i nie wraca tym samym,
  dopóki jest inne. Tablica obejmuje wszystkie jedenaście komnat i 148
  rzeczywistych punktów spawnu z `regen.txt`.
- **Przejścia czytane z samych NPC-ów, nie z tablicy.** Trzy Lochy Małp stoją na
  jednym `server_attr` i mają NPC-e przenoszące w tych samych komórkach, ale
  **każdy loch jest inaczej okablowany**: przejście przy komórce (80,308)
  prowadzi w łatwym lochu do (106,547), a w średnim do (520,352); średni i
  trudny mają dodatkowo dwa przejścia, których łatwy nie ma w ogóle, i przez nie
  jedenastą komnatę. Cel przejścia jest teraz odczytywany z nazwy NPC-a, tak jak
  robi to silnik, więc każdy loch chodzi po swoim własnym układzie.
- **Przekroczenie przejścia rozpoznawane co takt.** Teleport przenosi bota, nie
  ruszając jego trasy: przy następnym planowaniu nawigacja uznaje stary cel za
  nieosiągalny, szuka przejścia do niego i znajduje to, którym bot właśnie
  przyszedł. Bot dropiony między agresywne małpy walczy, a nie wędruje, więc
  zanim kolejna decyzja wędrówki doszła do słowa, mijał dwa albo trzy przejścia.
  Teraz komnata jest ustalana raz na takt, zanim cokolwiek zdąży przejąć turę.
- **Boty stojące bez ruchu w mieście.** Przystanek miejski pozwalał planerowi
  przyciągnąć cel do najbliższej kratki, na której da się stanąć, nawet o
  osiemset jednostek — a potem sprawdzał dojście promieniem od 350 do 850. Gdy
  sprzedawca stoi za ladą albo filarem, bot szedł do przyciągniętej kratki,
  wciąż był poza promieniem, czyścił trasę i planował tę samą. Zaliczenie punktu
  trasy zeruje licznik zacięć, więc ratunek serwisowy — ten po sześciu
  nieudanych próbach — nigdy się nie uruchamiał: jeden bot stał u nauczyciela
  umiejętności w Joan trzy dni, budzony przez watchdoga co dziewięćdziesiąt
  sekund i ani razu nie ruszył się z miejsca. Przyciąganie celu mieści się teraz
  w promieniu dojścia, a cel naprawdę nieosiągalny trafia w istniejący ratunek.

Zgłoszenie: Tieru, Remigiusz.

---

## 1.30.8 — 2026-09-07

### Naprawione

- **Tobołki straganów leżące na ziemi.** Przed otwarciem straganu bot
  kupuje tobołek (przedmiot 50200 „Tobół”) przez `AutoGiveItem`, a ten
  przy pełnym plecaku — a plecak tuż przed sprzedażą bywa właśnie pełny —
  kładzie go na ziemi. Stragan odmawiał (brak tobołka), następna próba
  kupowała kolejny i plac zapełniał się tobołkami z etykietą „botjade2's”
  (okno ochrony dropu), a boty biegały między nimi. Ta sama wada co
  strzały w 1.30.7: teraz tobołek kupowany jest tylko do wolnej kratki,
  bez niej stragan czeka na następną wizytę (`PLAYERBOT_SHOP: no room for
  bundle` w logu).

Zgłoszenie: Renagaruu.

---

## 1.30.7 — 2026-09-07

### Nowe

- **Średni i trudny Loch Małp.** Medal Konny to grupa dropu „kill”
  (jeden na 550 żołnierzy, 500 wojowników, 200 generałów), a silnik skaluje
  każdy taki rzut różnicą poziomów: piętnaście poziomów nad potworem
  zostaje 1 % szansy. Bot 45 poziomu w łatwym lochu (małpy 22–29)
  potrzebował więc ok. 50 tysięcy zabójstw na medal — 140 wypraw na godzinę
  przynosiło jeden. Teraz loch dobiera poziom: łatwy (25) do 32, średni
  (108, małpy 35–42) 33–45, trudny (109, małpy 45–54) od 46. Trzy lochy to
  ten sam labirynt (jeden `server_attr`, te same portale), więc nawigacja,
  pokoje i wyjście działają wszędzie; mapa 109 przeniesiona na rdzeń
  game1. Bot, który przerośnie swój loch, wychodzi i wraca do właściwego.
- **Po medal także z map granicznych.** Losowanie wyprawy po medal
  czytano tylko w mieście, a bot po czterdziestce mieszka na Dolinie,
  Pustyni, Sohan i w V1 — stąd 439 botów 40+ bez konia i 435 na koniu
  poniżej dziesiątki. Teraz wylosowany bot bez drużyny schodzi z mapy
  granicznej do Bokjung, idzie do swojego lochu i wraca; drużyn nie
  rozbija. Zniesiony też podział „po 26 poziomie tylko trzecia część
  szansy” i blokada dla konia ≥ 10: koń bojowy (11–19) dalej potrzebuje
  medali do dwudziestki.
- **Medal-dropper jest sklepikarzem medalowym.** Zbiera medale w lochu
  swojego poziomu (dotąd tylko do 32) i zawsze wystawia je na straganie —
  wcześniej trzymał je, dopóki jego własny koń mógł ich użyć, a dropper na
  koniu 10 (kandydat do bojowego, nie wolno mu wydać medalu) nie mógł ich
  ani użyć, ani sprzedać.
- **Pełne eq chętniej otwiera stragan.** Bot z każdym slotem zajętym i bez
  niczego do kupienia na drabince postępu trzyma stragan w trzech
  przypadkach na dziesięć zamiast jednego (ten sam rzut, więc dotychczasowi
  handlarze zostają).

### Naprawione

- **Łucznicy wysypywali strzały na ziemię.** `AutoGiveItem` oddaje przedmiot
  także wtedy, gdy nie miał go gdzie położyć — przy pełnym plecaku paczka
  strzał lądowała na ziemi, bot płacił, wciąż „potrzebował strzał” i
  kupował znowu (dwadzieścia razy na godzinę). Teraz przed zakupem sprawdza
  wolną kratkę, a bez niej czeka na następną wizytę.
- **Panel seban (port 7790): „Internal Server Error” zaraz po starcie.**
  Pulpit czyta tabelę zrzutów, którą kolektor zakłada przy pierwszym
  zrzucie — a kolektor startuje razem z bazą, która na świeżej lub właśnie
  zaktualizowanej instalacji jeszcze nie odpowiada; po nieudanej próbie
  czekał pięć minut i przez ten czas każdy, kto otworzył panel, widział
  błąd 500. Teraz do pierwszego udanego zrzutu kolektor ponawia co 15 s,
  a pulpit bez tabeli pokazuje pustą sekcję obciążenia zamiast błędu.

Zgłoszenie: OskarPWA, ŁOŚTEK, Remigiusz, stylowy26.

---

## 1.30.6 — 2026-09-07

### Naprawione

- **Świeża instalacja z archiwum repozytorium nie budowała panelu.** Launcher
  kopiuje przy starcie `files/web_admin_schema.sql` do
  `linux-port/docker/panel/schema/`, ale gdy tego katalogu nie było (Git go
  ignoruje, więc archiwum „metin2-playerbots-main” go nie zawiera), pomijał
  kopię — i budowa panelu padała na `COPY schema/` przy każdym Starcie, po
  aktualizacji też. Launcher tworzy teraz brakujący katalog. Obejście dla
  zainstalowanych: utworzyć ręcznie folder `linux-port\docker\panel\schema`
  i kliknąć Start.

---

## 1.30.5 — 2026-09-07

### Nowe

- **Dwa nowe bossy do wypadów.** Dziewięć Ogonów na Górze Sohan (1901,
  poziom 72, 166 tys. PZ, dwa lodowe golemy i yeti u boku, odrodzenie co
  2 godziny w promieniu 150×200 pól) — wypad drużyny co najmniej
  trzyosobowej, jak na Królową. Bestialski Kapitan w Bokjung (591, poziom
  42, 19 tys. PZ, co godzinę) — każdy bot od 35 poziomu skręca do niego,
  póki stoi, jak Dolina do Wodza.
- **Drużyny na wszystkich mapach granicznych.** Drużyny tworzyły się tylko
  na Dolinie Orków, a przejście mapy rozwiązuje drużynę, więc w V1 i na
  Sohan nie było ani jednej (16 botów w V1, wszystkie solo) i nikt nie mógł
  ruszyć na Królową ani Dziewięć Ogonów. Teraz drużyna zawiązuje się od 40
  poziomu na każdej mapie granicznej (Dolina, Pustynia, Sohan, V1), do
  ośmiu osób.
- **Koń bojowy = częstsze Metiny, i ciosy w rytmie konia.** Jeździec z
  koniem bojowym losuje wyprawę na Metiny dwa razy częściej. Kombo w siodle
  ma trzy ciosy, nie cztery, i własne czasy z danych klienta
  (`horse_<broń>/combo_NN.msa`); dotąd jeździec bijący kamień używał tabeli
  pieszej, wysyłał czwarty cios, którego koń nie ma, i kolejny za wcześnie,
  więc kombo nigdy nie grało do końca.

Zgłoszenie: Tieru.

---

## 1.30.4 — 2026-09-07

### Naprawione

- **Tarcza przy broni dwuręcznej.** W 1.30.3 bot odmawiał kupna tarczy,
  gdy nosił broń dwuręczną — a w Metin2 tarcza ma własny slot niezależny od
  broni (nosi ją każda postać, także z łukiem). Reguła usunięta; zostają
  te właściwe: nie kupuj, gdy w plecaku leży co najmniej równie dobry
  zamiennik, i wymagaj 15 % przewagi nad noszonym.

Zgłoszenie: Tieru.

---

## 1.30.3 — 2026-09-07

### Naprawione

- **Boty kupowały po trzy te same zbroje i tarcze, których nie noszą.**
  Ocena „czy chcę ten przedmiot ze straganu” porównywała go tylko z tym, co
  bot ma na sobie, a założenie kupionej rzeczy czekało na przegląd
  ekwipunku — więc bot stojący przy ladzie kupował tę samą zbroję +6 trzy
  razy co dwie sekundy, każda lepsza od noszonej i żadna jeszcze nie
  założona. Teraz bot nie kupuje, gdy w plecaku leży co najmniej równie
  dobry zamiennik na ten sam slot, a rzecz ze straganu musi być o 15 %
  lepsza od noszonej i od zapasu (dwie zbroje +6 różnią się tylko rzutem
  bonusów), nie kupuje tarczy przy broni dwuręcznej, a po zakupie przegląd
  ekwipunku rusza natychmiast.
- **Pętla Bokjung ↔ M3 M3-droppera.** Dropper z M3 ma tam zostać do 32
  poziomu, ale reguła „powyżej 24 opuść M3” wyrzucała go natychmiast, a w
  Bokjung ta sama logika słała go z powrotem: 148 przejść w kwartę u jednego
  bota, kolejka do teleportera w Bokjung i boty 25+ „expiące w M2” między
  skokami. Dropper zostaje na M3, dopóki chce tam być.

Zgłoszenie: OskarPWA.

---

## 1.30.2 — 2026-09-07

### Naprawione

- **Do V1 przez pustynię, jak w grze.** Bot przenosił się z teleportera w
  Bokjung wprost do Lochu Pająków i wprost z powrotem, czego żaden gracz nie
  może zrobić. Teraz wejście to dwa etapy: teleporter → Pustynia Yongbi
  (lewy górny róg) → marsz przez całą pustynię do bramy „Kuahlo Dong” w
  prawym dolnym rogu (NPC 10016) → V1; powrót: wyjście z V1 na pustynię w
  prawym dolnym rogu → marsz do bramy Bokjung w lewym górnym rogu → miasto.
  W drodze bot nie bije mobów (marsz zajmuje tick, wybór celu nie działa), a
  jedynie Metin w zasięgu 25 metrów, jeśli jest wart jego poziomu (ta sama
  reguła dropu co przy polowaniu: kamień nie niżej niż 10 i nie wyżej niż 9
  poziomów od bota); po rozbiciu idzie dalej. Log: `PLAYERBOT_WORLD:
  transitioned ... reason=desert_crossing_to_v1 / desert_gate_to_v1 /
  desert_crossing_from_v1 / desert_gate_to_bokjung` oraz `crossing stone`.
- **Wypady na bossa naprawdę się zdarzają.** Huby Wodza Orków (Dolina) i
  Królowej Pająków (V1) były oceniane jak każdy obóz — po gęstości potworów
  z pamięci spotów — a jeden boss co pół godziny to gęstość zero, więc w
  dobie logów ani jeden bot ich nie wybrał; Królowa nie zginęła ani razu.
  Teraz hub bossa pyta sektor, czy boss stoi (odpowiedź trzymana 30 s), i
  gdy stoi, wygrywa z każdym obozem: na Wodza (25 tys. PZ, co 30 minut)
  rzuca się każdy bot z pasma 45+, także bez drużyny; na Królową (193 tys.
  PZ, poziom 60, co ok. 4 godziny) idzie tylko lider drużyny co najmniej
  trzyosobowej, a członkowie za nim. Log: `PLAYERBOT_RAID: boss ...
  standing/down` i `heading for boss`.

Zgłoszenie: Tieru.

---

## 1.30.1 — 2026-09-07

### Nowe

- **Wyprawa na Metiny.** Dotąd kamienie biła tylko rola łowcy Metinów
  (co czwarty bot), a reszta rozbijała Metin wyłącznie wtedy, gdy stanął
  jej na drodze — nie tak gra człowiek, który umawia się na wieczór
  Metinów i przeczesuje mapę. Teraz każdy pozostały bot od 15 poziomu raz
  na godzinę losuje (25 % szansy, skalowane suwakiem „Metiny” w panelu)
  półgodzinną wyprawę: przez ten czas planuje, celuje i wędruje jak łowca —
  Metin znany z rejestru (widziany przez dowolnego bota na mapie) idzie
  przed hubem, kamień jest celem ważniejszym niż moby, a na mapach polowań
  bot zmienia hub co półtorej minuty zamiast co cztery, bo kamień znajduje
  się pokrywając teren. W każdej chwili około jeden bot na osiem spoza roli
  łowcy jest na wyprawie. Log: `PLAYERBOT_METIN: expedition start/over`.
- **Łowcy Metinów poza Joan szukają znanych kamieni.** Na Dolinie Orków,
  Pustyni, Sohan i w V1 łowca szedł do hubów jak każdy inny i bił kamień
  tylko z zasięgu skanu; teraz Metin z rejestru mapy jest jego celem
  wędrówki tak samo, jak na mapie startowej.

Zgłoszenie: OskarPWA.

---

## 1.30.0 — 2026-09-07

### Nowe

- **Metin2 Singleplayer Panel autorstwa seban latino — drugi panel w
  instalacji.** Startuje razem z serwerem pod `http://127.0.0.1:7790`
  (klasyczny panel zostaje pod 7788; 7789 należy do mostu przeglądarkowego).
  Mapa świata botów odświeżana na żywo z pozycjami, poziomami, grupami i
  botami przy Metinach; profile postaci z ekwipunkiem, magazynem, Yangami i
  tooltipami przedmiotów w stylu klienta (bonusy, kamienie duszy); rankingi
  poziomu, Yangów, broni 30 lv, konia, gildii; historia gospodarki (stan
  przedmiotów, obieg Yangów, wykresy per przedmiot); telemetria CPU, RAM i
  dysku; sterowanie zachowaniem botów, mnożnikami i bezpiecznym restartem;
  masowe nadawanie przedmiotów według poziomu, klasy, konia i czasu gry;
  przybornik GM, trzy motywy, opcjonalne hasło. Przy pierwszym wejściu
  kreator `/setup`.
- **Jak to jest wpięte.** Trzy kontenery z jednego obrazu w naszym compose
  (`seban-panel`, `seban-collector`, `seban-item-grants`) na tej samej bazie,
  plikach statusu i spoolu co klasyczny panel; hasła z naszego `.env`,
  wersja z pliku `VERSION`. Nowe, opcjonalne klucze `.env`:
  `M2_SEBAN_PANEL_PORT` (7790), `M2_SEBAN_SESSION_SECRET` (pusty = sekret
  strony admina), `M2_SEBAN_TIERU_PANEL_URL`. Quest `web_admin.quest`
  rozszerzony o polecenia nadań (`BULK_ITEM`, `BULK_MISSING`, `RIDER_ITEM`).
  Paczka aktualizacji rośnie o ikony przedmiotów (ok. 20 MB); pierwszy start
  po aktualizacji buduje nowy obraz panelu i grę z nowym questem.

Źródło: seban latino, Metin2 Singleplayer Panel 1.30.1, przygotowany pod
Playerbots 1.29.10 i tu dostosowany (wersja z pliku, jeden `COPY` kontekstu).

---

## 1.29.17 — 2026-09-07

### Nowe

- **Handel na czacie.** Bot, który otwiera stragan z czymś wartym przejścia
  przez miasto (broń 30 lv, +7 i wyżej, dobry bonus), woła raz na świecie:
  „Sprzedam Kozik Czar. Liś.+0 - stragan w Joan”; bot, który przyszedł na
  targ po materiał i nic nie zastał, woła „Kupie Amulet Orka - kto ma, niech
  wystawi w Joan”. Najwyżej jedno takie wołanie na 90 s na całym świecie i
  jedno na bota na 20 minut. Wołanie gracza „Kupię X” / „Szukam X” dostaje
  szept od najbliższego straganiarza, który ma X (z ceną i miastem);
  „Sprzedam X” — szept od bota, któremu X brakuje. „KU Aura” rozumiane
  (nazwy umiejętności z protos ksiąg). Szept do bota zwraca jego stan
  (co ma na straganie, albo że poluje). Dopasowanie nazw nie zważa na
  polskie znaki ani wielkość liter.
- **Boty kupują też na straganach graczy.** Prywatny sklep gracza jest
  czytany przez boty tak jak stragan bota; linia droższa niż 30 % mediany
  portfela botów jest pomijana, żeby nikt nie drukował yangów na botach.
  Gracz może więc odpowiedzieć na „Kupie X” bota, wystawić X w Joan lub
  Bokjung i sprzedać.
- **Łatka silnika 0007** (`input_main.cpp`, `shop.h`): wołanie i szept gracza
  trafiają do botów, a lada sklepu jest czytelna. Pliki są w paczce jak przy
  0006; pierwszy start po aktualizacji kompiluje grę na nowo.

### Wydajność

- **Dalekie plany tras.** Cache tras: 16 tras na cel zamiast 6, pół godziny
  zamiast dziesięciu minut, dołączenie z 2400 zamiast 1600 jednostek;
  długi korytarz szukany zachłanniej (waga 3); najwyżej 80 dalekich planów
  na minutę, reszta odroczona o sekundę-dwie. Pomiar na 837 botach: tick
  21–31 s → 8–17 s, planowanie 17–28 s z każdych 60 → 4–14 s, dalekie
  plany 100–120/min po 221 ms → 30–82/min po 120 ms, trafienia cache
  143–180 → 196–264/min.

---

## 1.29.16 — 2026-09-07

### Nowe

- **Księgi bez dobowej przerwy (przełącznik w panelu, zakładka AI).** Gra każe
  czekać 18–30 godzin między dwoma czytaniami tej samej umiejętności, więc
  bot potrzebował miesiąca ksiąg, by przejść z M1 na G1, a księgi zalegały w
  plecaku. Domyślnie włączone: bot czyta ponownie po pół godzinie — to, co
  gracz robi Zwojami Egzorcyzmu. Wyłączenie przywraca tempo gry. Klucz
  `BOOKS` w pliku wag, jak `CHAT` i `SCRAP`.
- **Limit ksiąg własnych.** Bot trzyma najwyżej 12 ksiąg jednej swojej
  umiejętności (dziesięć udanych czytań to M1→G1 z zapasem); nadmiar idzie na
  ladę lub do handlarza. Stragan nie wystawia już księgi, na którą jej
  właściciel czeka.
- **Skrzynki bez klucza pod presją plecaka.** Srebrne i złote szkatułki bez
  pasującego klucza są trzymane, dopóki jest miejsce; gdy w plecaku zostaje
  8 lub mniej wolnych pól, idą do handlarza, żeby loot i Szkatułki Blasku
  (które otwierają się same, ale tylko do wolnego pola) miały gdzie
  wylądować.

### Naprawione

- **Bot wolał smoczą zbroję +3 od zbroi z +1500 PZ.** Kara za przerośnięty
  o 20 poziomów pancerz była płaskimi 1500 punktami za poziom i zjadała
  linie bonusów: zbroja płytowa na 18 lv z 1500 PZ przegrywała na 50 lv ze
  zbroją o 7 punktów obrony więcej. Kara jest teraz procentem samej obrony
  (5 % za poziom), a punkt maksymalnego PZ liczy się 15 zamiast 10.
- **Panel: wyszukiwarka postaci na liście graczy.** Lista brała 200
  ostatnio grających postaci, a przy 1500 botach nie mieściła w niej żadnej
  postaci gracza — filtr w przeglądarce nic nie znajdował. Ludzie są teraz
  na liście zawsze, boty dopełniają ją do 200.

Łuk: log potwierdza, że łucznicy ciągną po 3–4 cele i strzelają obszarowymi
Strzałą Ognia i Strzałą Trucizny (do 12 trafień w promieniu 300); zwykły
strzał z łuku jest jednocelowy z natury silnika — bez zmian.

---

## 1.29.15 — 2026-09-06

### Naprawione

- **Koniec fałszywych odmów zakupu.** W godzinie 22–23 było 2158 odmów na
  501 zakupów, każda z wpisem silnika „this user seems to be a hacker”.
  Przyczyna: prywatny sklep w silniku to siatka 5 kolumn × 8 wierszy, broń
  zajmuje 3 pola w kolumnie, zbroja 2, a bot numerował linie 0, 1, 2…, więc
  każdą linię od drugiego rzędu pod bronią lub zbroją silnik po cichu
  pomijał („not empty position” w syserr, 280 razy na godzinę) i kupujący
  trafiali w pusty slot. Linie są teraz układane na siatce tak jak robi to
  silnik, oferta pamięta swój slot, a do tego jest identyfikowana po id
  przedmiotu, którego właścicielem wciąż jest straganiarz (ten sam test,
  który robi silnik), bo sprzedany stos bywa zastąpiony drugim takim samym
  z plecaka. Po dojściu do stoiska bot czyta ofertę jeszcze raz i kupuje
  to, co naprawdę tam leży, albo idzie do następnej lady. Wyprzedany
  stragan zamyka się po id, nie po vnum.

### Nowe

- **Ceny skalowane do portfeli kupujących.** Cena bazowa była trzykrotnością
  ceny u handlarza, a handlarz płaci grosze: materiał, którego brakowało
  czterystu botom, stał za 600 yang na rynku, gdzie klienci mają po milion.
  Co minutę liczona jest mediana wolnego złota botów, które chodzą po
  zakupy (`wallet=` w raporcie `PLAYERBOT_MARKET: ledger`), i sztuka na
  ladzie prosi o udział w niej: materiał 1,5 %, zapasowy sprzęt +4/+5/+6
  odpowiednio 3/4,5/6 %, reszta 1 %, a cały stos najwyżej 30 % — żeby bot z
  medianą portfela mógł go kupić. Marża handlarza zostaje tam, gdzie jest
  wyższa; kamienie duszy trzymają tabelę po stopniu; +7/+8/+9 bez zmian.
- **Pasmo rynku względem ceny bazowej.** Mediana transakcji koryguje cenę w
  przedziale od ćwierci do czterokrotności ceny bazowej (dotąd: do
  dwunastokrotności ceny u handlarza), więc jedna przepłata nie wywinduje
  materiału, a stare tanie sprzedaże nie ściągną go z powrotem do groszy.

---

## 1.29.14 — 2026-09-06

### Nowe

- **Księga rynku.** Co minutę serwer liczy, ile sztuk każdego materiału
  stoi na otwartych straganach i ilu botów brakuje go do własnej receptury
  (i ma za co kupić). Dotąd stragan wystawiał każdy zapasowy materiał, więc
  czterdzieści straganów pokazywało te same rzeczy, których nikt nie
  potrzebował.
- **Limit podaży z kodami powodów.** Materiał trafia na ladę tylko wtedy,
  gdy na straganach jest go mniej niż 1,5 × 5 sztuk na każdego
  potrzebującego bota (`LIST`). Gdy nikt go nie potrzebuje, jeden stos może
  stać jako sonda (`PROBE`); kolejne zostają w plecaku (`NO_DEMAND`), a przy
  pokrytym popycie — `OVERSTOCK`. Odmowy z liczbami idą do logu raz na
  minutę (`PLAYERBOT_MARKET: held`), a co 10 minut raport
  `PLAYERBOT_MARKET: ledger` pokazuje osiem najbardziej poszukiwanych
  materiałów (D = boty, S = sztuki/stragany, ask = ostatnia cena).
- **Wycena z kotwicą i regulatorem.** Cena bazowa (3× cena u handlarza, dla
  kamieni tabela po stopniu) łączy się z medianą prawdziwych transakcji
  wagą n/(n+4) w skali logarytmicznej: dwie sprzedaże przesuwają cenę o
  jedną trzecią, pełna pamięć ośmiu o dwie trzecie. Dotąd dwie sprzedaże
  zastępowały cenę bazową w całości. Dla materiałów dochodzi regulator
  popyt/podaż ((D+5)/(S+5))^0,2 w granicach 0,75–1,35, a cena rynkowa
  przedmiotu może przesunąć się najwyżej o 5 % na 10 minut (do 30 % naraz
  po godzinie bez ofert).
- **Materiał bez receptury nie jest towarem.** Przedmiot typu MATERIAL,
  którego żadna receptura nie zużywa, nie trafia już na ladę tylko dlatego,
  że ma taki typ.

Ograniczenie: zakupy graczy na straganach botów przechodzą przez silnik bez
śladu w tej pamięci — księga i mediana widzą wyłącznie handel bot–bot.

Z dokumentu o handlu i wycenie (etapy A, B i C).

---

## 1.29.13 — 2026-09-06

### Naprawione

- **Stopień Kamienia Duszy był czytany z niewłaściwej cyfry.** Vnum kamienia
  to 28[stopień][rodzaj] (28037 Potwora+0, 28437 Potwora+4); kod brał
  ostatnią cyfrę, więc każdy kamień liczył się jako +0, reguła „+3 i +4
  tylko na sprzęt +6” nigdy nie działała, a +4 Potwora szedł w byle co.
- **Kamienie Duszy nie idą już do handlarza.** Reguła śmieci uznawała je za
  złom — kamień, którego bot nie mógł od razu osadzić, sprzedawał NPC za
  jednego yanga.

### Nowe

- **Zestawy Kamieni Duszy według stylu walki.** Jedna wspólna ocena
  rodzaju kamienia dla kowala, lady i rynku: Potwora dla każdego, potem
  Śmierci; Penetracji dla szkół bijących, Powtórki dla skillowych; kamienie
  klasowe (Wojownika, Sury, Ninja, Szamana) są warte zero w świecie
  potworów. Na zbroi: Witalności, potem Uchylenia dla tych, co stoją w
  hordzie, Przyspieszenia dla dystansowych (łucznik, BM, szaman), potem
  Obrony i Uniku; Magii tylko dla skillowych. Silnik odmawia drugiego
  kamienia tego samego rodzaju, więc zestaw układa się sam.
- **Gniazdo warte czekania.** Osadzenie to 30% szansy, a 70% to pęknięty
  kamień wspawany w gniazdo na zawsze. Na sprzęcie +6 bot osadza tylko +3 i
  +4, na +8 tylko +4; +0..+2 idą na sprzęt tymczasowy, +3/+4 nigdy poniżej
  +6.
- **Kamienie na targowisku.** Straganiarz wystawia kamienie, których nie
  osadzi (zły rodzaj, brak gniazda, zły stopień na jego sprzęt), z ceną po
  stopniu (30–500 tys.) do czasu, aż targowisko wyceni je transakcjami; bot
  z wolnym gniazdem na sprzęcie +6 idzie na targ i kupuje kamień ze swojego
  zestawu.

Z audytu wiedzy o grze (sekcja 9).

---

## 1.29.12 — 2026-09-06

### Nowe

- **Pamięć dropu materiałów per spot, z zerami.** Każdy podniesiony materiał
  (typ `ITEM_MATERIAL`) jest liczony w komórce spotu, w której leżał. Bot,
  któremu brakuje materiału do własnej receptury, wybiera hub, gdzie ten
  materiał już wypadał (warto o połowę więcej), a komórka z długim
  rejestrem walk i bez tego dropu nie dostaje premii — zera są obserwacją
  tak samo jak trafienia. Dotąd wybór szedł wyłącznie z tabel dropu.
- **Bonus rasowy według tego, co bot naprawdę bije.** Ocena ekwipunku
  (Silny przeciw Orkom, Nieumarłym…) brała rasę dominującą całej mapy.
  Teraz każdy bot prowadzi własny histogram ras z ostatnich walk (połowiony
  co 10 minut) i po 20 walkach to on decyduje; mapa jest zapasem. Pustynia
  ma skorpiony obok nieumarłych, Dolina orków obok mistyków — liczy się
  konkretny cel.
- **Wojownik mentalny rozdaje statystyki jak tank.** 2 WIT : 1 SIŁ do 90,
  potem ZR; Body bez zmian (2 SIŁ : 1 WIT). Reszta klas była już zgodna z
  audytem (sura i szaman INT:WIT, ninja ZR:WIT).

Z audytu wiedzy o grze (sekcje 3, 8 i 11).

---

## 1.29.11 — 2026-09-06

### Naprawione

- **Launcher rozpoznaje „read-only file system” Dockera.** Gdy dysk maszyny
  WSL Docker Desktop przejdzie w tryb tylko do odczytu albo się zapełni,
  budowa obrazu pada na `desktop-containerd/.../meta.db`, a launcher
  odsyłał do logów. Teraz mówi, co zrobić: zamknąć Docker Desktop,
  `wsl --shutdown`, sprawdzić miejsce w `%LOCALAPPDATA%\Docker\wsl`,
  uruchomić Dockera i GRAJ — i czego nie robić („Clean / Purge data”
  kasuje bazę z postaciami). Zgłoszenie z serwera (Ciapek).

### Nowe

- **Ryby pieczone na ognisku.** Martwa ryba szła dotąd do handlarza. Rybak
  kupuje Wysuszone Drzewo (20 000 yang, więc dopiero gdy ma co najmniej 30
  martwych ryb), na koniec sesji rozpala ognisko (silnik stawia je na 40 s)
  i podaje mu martwe ryby; pieczone
  wracają do plecaka i są używane jak mikstury: Karaś, Duży Karaś i Tenchi
  jako czerwone, Ryba Mandaryna i Sum jako niebieskie, Pieczony Karp
  (+20 ruchu) i Krasnopiórka (+10 zręczności) jak boostery na początku
  walki. Wszystko przez natywną ścieżkę silnika (podanie przedmiotu
  ognisku, `Grill`).
- **Otwarcie małża to decyzja, nie odruch.** Silnik daje z małża w połowie
  Kawałek Kamienia, w 30% nic, w 10/7/3% białą, niebieską i krwawą perłę.
  Bot otwiera małża tylko wtedy, gdy oczekiwana wartość zawartości (ceny z
  transakcji na targowisku, a bez nich cena u NPC) przebija wartość całego
  małża; ostrożny kolekcjoner chce półtora raza tyle, specjalista od sprzętu
  zadowala się mniej. Małż potrzebny własnej recepturze nadal zostaje.
  Populacja pamięta wyniki wszystkich otwarć — także puste — i po 50
  otwarciach liczy szansę z własnych danych; raport `PLAYERBOT_SHELLFISH:`
  co 10 minut. Z audytu wiedzy o grze (sekcje 7 i 12).

---

## 1.29.10 — 2026-09-06

### Naprawione

- **„Nie znaleziono programu Docker Desktop” po STOP albo po aktualizacji.**
  Launcher szukał `Docker Desktop.exe` tylko w trzech standardowych
  katalogach; kto miał Dockera na innym dysku, ten po zatrzymaniu serwera
  (które zatrzymuje też Docker Desktop) nie mógł go już uruchomić z
  launchera, a aktualizacja, która trafiła w międzyczasie, dostawała winę.
  Launcher szuka teraz też obok `docker.exe` z PATH i w rejestrze (wpis
  odinstalowania, `InstallLocation`). Do tego czasu: uruchomić Docker
  Desktop ręcznie i kliknąć GRAJ.
- **Dalekie plany w Dolinie liczone raz, nie dla każdego bota z osobna.**
  Daleki plan trasy (ponad 12 km) kosztował 150–250 ms rdzenia, a w Dolinie
  szło ich 60–120 na minutę — 10–25 s z każdej minuty — i prawie wszystkie
  były tą samą drogą: wejście na mapę do huba, hub do wyjścia, hub do huba,
  proszone przez kolejne boty z tego samego kilkuset metrów. Rdzeń trzyma
  teraz policzone trasy (start i cel zaokrąglone do 1,2 km, dołączenie tylko
  przy czystym pierwszym odcinku, ważność 10 minut, do 400 tras na mapę) i
  bot idący tam, gdzie ktoś już szedł, dostaje gotową trasę bez liczenia.
  Linia `PLAYERBOT_LOAD` ma `cached=`, a każdy daleki plan ma wpis z celem,
  wynikiem i kosztem. Pomiar przy 843 botach: 107–176 gotowych tras
  na minutę, dalekie plany ze 100–170 na 38–93, rdzeń z 45–56% na 35–40%.

- **Boty po 40 nosiły Bojową Tarczę+6 z pierwszego poziomu.** Silnik liczy
  obronę jako `value1 + 2·value5`, więc Bojowa Tarcza+6 (39) wygrywała z
  Czarną Okrągłą Tarczą+3 (37) i bot nosił ją „uczciwie” — 61 botów po
  czterdziestce miało tarczę z 1 poziomu na grzbiecie, a 41-tarczę w
  plecaku. Element zbroi przerośnięty o ponad 20 poziomów traci punkty za
  każdy dalszy poziom, więc bot zakłada tarczę, zbroję, hełm i buty z
  właściwego progu i dopiero je ulepsza (cel ulepszania to nadal +6 i wyżej);
  41-tarcza od +4 wygrywa z 21-tarczą+6. Zgłoszenie z serwera.

### Nowe

- **Suwaki Szkatułek Księżycowych w panelu.** Zakładka zachowania botów ma
  dwa suwaki: szansa na szkatułkę z zabitego potwora (‰) i z rozbitego
  Metina (‰). Rdzeń przepisuje je do silnika w pięć sekund, bez restartu i
  bez edycji `.env`; dopóki nikt ich nie zapisze, obowiązuje `.env`.
- **Szyld straganu mówi, co jest na ladzie.** Dotąd szyld to była nazwa
  konta bota, więc targowisko z czterdziestoma straganami czytało się jak
  ściana identycznych napisów. Szyld powstaje z zawartości lady: „Bron 30:
  Miecz Zabojcy”, „Zbroja Smoka+7”, „Futro Wilka, Skora Niedzwiedzia”,
  „Ksiegi: Aura Miecza i inne”, „Zlom do palenia +0..+3” albo „Zolc
  Niedzwiedzia i inne”; krótki przedrostek zależny od bota (Tanio, Okazja,
  Sprzedam) tylko, gdy mieści się w 32 znakach. Szyld jest też w logu
  otwarcia straganu. Pomysł z Discorda (Renagaruu).

---

## 1.29.9 — 2026-09-06

### Nowe

- **Boty złomiarze (suwak w panelu, domyślnie wyłączone).** Zakładka
  zachowania botów ma suwak „Boty złomiarze” 0–100%: taki udział
  straganiarzy wystawia na ladę swoje słabe ulepszenia (+0 do +3) za
  dwukrotność ceny NPC zamiast sprzedawać je handlarzowi — złom do palenia
  u kowala, jak na serwerach hard. Złomiarz trzyma złom, dopóki ma ponad
  20 wolnych komórek w plecaku. Pomysł z Discorda (Remigiusz).
- **Łucznik ciągnie 3–4 cele naraz.** Multi-pull, dotąd tylko dla
  tarczowników i wojowników mentalnych, działa też dla łucznika: jedna
  grupa, limit czterech atakujących zamiast czternastu. Pomysł z Discorda
  (Archded).
- **Wypad po drop z Metina.** Przez 20 sekund od rozbicia kamienia bot idzie
  po swoje przedmioty w promieniu 15 m mimo trwającej walki z przywołaną
  hordą — jak gracz, który skacze po drop, zanim zabiorą go inni. Dotąd w
  walce podnosił tylko to, co leżało w zasięgu ręki (300 jednostek, tyle
  pozwala silnik). Pomysł z Discorda (Kordyl13).
- **Wypady na bossów.** Wódz Orków (Dolina, poziom 50, co 30 minut) i
  Królowa Pająków (koniec Lochu V1, poziom 60, co ~4 godziny) są hubami dla
  drużyn: przywódca z drużyną (najpierw współgildianie) może je wybrać jak
  obozy Czarnych Orków. Szkatułki bossów (Szkatułka Wodza Orków, Królowej
  Pająków i pozostałe) boty otwierają tak jak Szkatułkę Księżycową i nie
  sprzedają ich.

---

## 1.29.8 — 2026-09-06

### Nowe

- **Srebrne i złote skrzynie otwierane kluczem.** Bot, który ma skrzynię
  skarbów i pasujący klucz, używa klucza na skrzyni tak jak gracz: silnik
  zabiera oboje i wydaje zawartość. Skrzynie i klucze nie idą do handlarza.
- **Siedemnaście punktów i Zwój Zapomnienia.** Silnik losuje Mistrza przy
  każdym punkcie od siedemnastego; bot wbijał do dwudziestu i tracił punkty.
  Teraz zatrzymuje się na 17, a gdy Mistrz nie wszedł, szuka na targowisku
  Zwoju Zapomnienia (70037, wypada z potworów): zwój cofa umiejętność o jeden
  i oddaje punkt, bot wbija siedemnasty ponownie i losuje jeszcze raz. Bot
  ze zwojem, któremu nie jest potrzebny, wystawia go na ladę; zwój nie jest
  śmieciem.
- **Boty od 48 idą tylko do Lochu Pająków i na Sohan**, po połowie. Dolina
  zostaje dla 36–47, więc na obu wysokich mapach widać kogoś, mimo że
  populacja sięga dopiero 50 poziomu.
- **Przełącznik w panelu: czy boty piszą nad głową, co robią.** Zakładka
  zachowania botów ma pole „Boty piszą nad głową, co robią”; wyłączone
  ucisza napisy nad głowami (poluje, idzie do kowala, łowi) dla graczy,
  którym to przeszkadza. Rdzeń odczytuje to w pięć sekund, bez restartu.
  Wołanie na czacie świata o ulepszeniu na +7/+8/+9 zostaje niezależnie.

### Naprawione

- **Panel: Biolog liczył 6 misji, boty mają 7.** Ząb Orka dodany do listy
  panelu (ranking, karta bota, etap), licznik 0/7.

---

## 1.29.7 — 2026-09-06

### Naprawione

- **„Góra Sohan” botów była drugą wioską Jinno.** Od 1.29.0 boty 26–39
  szły na mapę 43 (`metin2_map_c3`, żołnierze 26–36) pod nazwą Sohan.
  Prawdziwa Góra Sohan to mapa 61 (`map_n_snowm_01`): Zarażeni 49–58 na
  południu, lodowe stwory i Yeti 62–66 na północy. Boty od 48 dzielą się
  teraz na trzy: Loch Pająków, Sohan i Dolinę; 30–35 na pół między wyspy
  Fanatyków i pustynię; poniżej 30 zostają w Bokjung. Czternaście hubów
  Sohan z regen tej mapy (osiem wśród Zarażonych od 48, sześć w lodzie od
  58), wejście ze spawnu miasta. Misje polowań na Zarażonych (wiersze od
  41) są wykonalne, bo ich potwory mają teraz mapę. Mapa 43 wraca na rdzeń
  Jinno, a boty, które na niej stały, migrator odsyła do Bokjung przy
  pierwszym starcie po aktualizacji. Panel ma granice i kafelek mapy 61;
  lista map, na których bot może stać, zna też 61 i 104 (dotąd boty z Lochu
  Pająków wracały do Bokjung po każdym restarcie).
- **Migrator nie ściąga już botów na środkową wyspę Doliny.** Krok z czasów,
  gdy nawigacja nie znała mostów, przy każdym starcie przenosił każdego bota
  spoza środkowej wyspy z powrotem na nią — 207 botów z wysp Fanatyków i
  obozów Czarnych Orków na każdy restart. Usunięty.

---

## 1.29.6 — 2026-09-06

### Naprawione

- **Panel odpowiadał „Access denied” do bazy, choć gra działała.** Panel
  czyta hasło bazy ze swojego pliku `m2panel.conf`, zapisywanego raz przy
  pierwszym uruchomieniu i trzymanego w wolumenie `panel-conf`. Instalacja
  przejęta z poprzedniej wersji miała tam stare hasło, a `.env` (i gra)
  nowe — pulpit panelu i statystyki padały na 1045, migrator i rdzeń
  działały normalnie. Przy starcie panelu adres, użytkownik i hasło bazy są
  teraz odświeżane z `.env`; hasło panelu, sól i sekret sesji zostają bez
  zmian. Plik startowy panelu jedzie w paczce aktualizacji, a aktualizacja
  przebudowuje obraz panelu.

---

## 1.29.5 — 2026-09-06

### Naprawione

- **Przejęcie starszej instalacji padało na „Cannot bind argument to parameter
  'Value' because it is an empty string”.** Gdy launcher znajdował istniejący
  serwer z poprzedniej wersji (kontenery `metin2-db` bez pliku tożsamości
  `.m2install.json`), przepisywał jego `.env` do nowego — a każdy prawdziwy
  `.env` ma puste wartości (`M2_BRAND=`, `M2_CLIENT_URL=`…), których funkcja
  zapisu nie przyjmowała. GRAJ i aktualizacja kończyły się tym błędem w
  kółko. Puste wartości są pomijane (nie nadpisują niczego), hasła i adresy
  ze starego pliku przechodzą. Test przejęcia starej instalacji ma teraz
  puste wartości w `.env`.

---

## 1.29.4 — 2026-09-06

### Naprawione

- **Wojownik mentalny brał iglicę +4 zamiast miecza +6 z 30% na potwory.**
  Premia +200000 punktów za broń dwuręczną biła każdą różnicę w ulepszeniu i
  bonusach. Premia działa teraz dopiero od 11 poziomu konia (koń bojowy) —
  wtedy dwuręczna ma sens, bo bot bije nią Metiny z siodła. Zgłoszenie od
  gracza z Discorda.
- **Zaparkowana trasa faktycznie wznawiana.** W 1.29.3 każdy krok do potwora
  w trakcie walki (inny cel niż hub) kasował zaparkowaną trasę, więc wznowień
  było 5–18 na minutę przy ~100 dalekich planach. Inny cel już jej nie
  kasuje, robi to tylko zmiana mapy. Po poprawce: 200–360 wznowień na
  minutę, dalekie plany spadły ze 100–170 do 46–94 na minutę, rdzeń z 56% na
  35% przy 843 botach.
- **Aktualizacja na świeżym silniku Dockera zgłaszała błąd, choć obrazy się
  zbudowały.** `up --build` ścigał się z własnym pobieraniem i padał na
  „No such image: mariadb:10.11”; druga próba przechodziła. Launcher pobiera
  teraz obrazy obce przed budową.

---

## 1.29.3 — 2026-09-06

### Naprawione

- **Świeża instalacja na Linuksie (`installer/install.sh`) padała na patchu
  szkatułek.** Hunk patcha 0006 zakładał, że w `item_manager.cpp` jest już
  `#include "high_risk.h"`, a tę linię wstawia dopiero krok High Risk, który
  w `prepare-context.sh` idzie po overlayu botów. Na czystym drzewie r40250
  `patch --fuzz=0` odrzucał hunk; na maszynie, gdzie w cache było już drzewo
  z High Risk, nakładał się przypadkiem. Kontekst hunku nie zależy już od tej
  linii. Zgłoszenie z dokładną diagnozą przyszło od gracza.
- **Paczka rozpakowana ręcznie (bez instalatora) nie miała pliku `.env` i nic
  nie działało.** GRAJ kończył się na „Missing Docker environment file”, a po
  aktualizacji dokańczanie budowy uruchamiało compose bez haseł bazy
  (`M2_DB_PASSWORD is missing a value`) — i tak w kółko, bo budowa szła
  przed krokiem, który plik tworzy. `start-server.ps1` tworzy teraz `.env`
  z `.env.example`, nowymi hasłami i adresami 127.0.0.1, wypisując hasło
  panelu; dokańczanie budowy najpierw przygotowuje `.env`. Gdy jest już
  baza z tej instalacji, a `.env` zniknął, launcher mówi wprost, że hasła
  trzeba przywrócić z kopii, zamiast wymyślać nowe, których baza nie przyjmie.
- **Zbieranie logów padało bez pliku `.env`** („WriteAllLines: wartość nie
  może być zerowa”) — akurat u gracza, któremu logi były najbardziej
  potrzebne. Pusta lista zmiennych zapisuje się jako „(brak pliku .env)”.
- **Przerwany marsz jest parkowany, nie kasowany.** Bot idący przez Dolinę do
  odległego huba zatrzymywał się na każdą walkę, trasa szła do kosza, a po
  walce rdzeń liczył ją od zera (200 ms za każdym razem, 100–170 dalekich
  planów na minutę). Trasa przerwana walką jest teraz zachowywana i
  podejmowana od najbliższego punktu, na który bot może wejść prosto.
  W pierwszej obserwacji wznowień jest jeszcze niewiele (7–18 na minutę);
  linia `PLAYERBOT_LOAD` mówi `resumed=`, a każdy daleki plan ma wpis
  `PLAYERBOT_NAV: far plan` z celem — dalsze strojenie w następnym wydaniu.

### Nowe

- **Misje polowań do 55 poziomu.** Tabela kończyła się na 25, a w praktyce
  prawie każdy bot stał od tygodni na misji z 14–17 poziomu: przyjął ją w
  Joan, wyrósł z jej potwora i nigdy po niego nie wrócił. Tabela sięga teraz
  55 (ostatni wiersz wykonalny na hostowanych mapach). Bot wybiera tę z dwóch
  opcji, której potwór stoi na jego mapie, a gdy żadna — tę, która stoi
  gdziekolwiek. Misja o ponad dziesięć poziomów niższa od bota, misja bez
  potwora na żadnej mapie, misja z potworem na innej mapie niż ta, na której
  bot osiadł, i misja wisząca dwie godziny są oddawane jako pominięte, bez
  nagrody, żeby nie blokowały następnych. Nagroda z
  doświadczenia zwęża się jak w questlib: 2–5% od 31, 1–4% od 51. Panel zna
  nazwy potworów nowych wierszy.
- **Ząb Orka u Biologa.** Siódma misja Biologa: dziesięć Zębów Orka z Orków w
  Dolinie, oddawane po jednym, 60% szansy na przyjęcie i spalony ząb przy
  porażce — jak u gracza bez eliksiru, tylko bez 22 godzin czekania między
  oddaniami. Po dziesiątym zębie quest czeka na Kamień Duszy Jinunggyi
  (1/500 z Elitarnych Orków, przez własny hook questu), bot poluje wtedy na
  Elitarne Orki, a Kamień oddaje Biologowi: +10 szybkości ruchu na 60 lat i
  skrzynka, jak w skrypcie. Ząb i Kamień nie idą do handlarza ani na ladę.
- **Misję Biologa bot bierze tam, gdzie stoi.** Dotąd przyjmował ją tylko na
  M1, a okazy spadają dopiero po przyjęciu — bot, który minął 25 poziom poza
  Joan, nie zbierał nic (663 z 876 botów miało Grzyb Tue nietknięty). Teraz
  przyjmuje ją gdziekolwiek, a do Biologa idzie dopiero z kompletem. Z
  zaległych misji wybiera tę, której okazy już niesie, potem tę, której potwór
  stoi na jego mapie — bot z Doliny zbiera zęby zamiast wracać po grzyby.

---

## 1.29.2 — 2026-09-06

### Naprawione

- **Aktualizacja do 1.29.1 padała przy budowaniu obrazu.** Nowy plik obrazu
  kopiuje tabelę szkatułki z kontekstu, a aktualizacja buduje obraz od razu
  po wgraniu plików, zanim `start-server.ps1` zdąży ją tam podstawić:
  „special_item_group.moonlight.txt: not found”. Paczka wkłada teraz ten plik
  (i tabelę dropu M3) prosto do kontekstu, a launcher podstawia je także przy
  aktualizacji. Kto już ma ten błąd: kliknięcie GRAJ dokańcza budowanie.

---

## 1.29.1 — 2026-09-06

### Naprawione

- **Szkatułki i trzy księgi z Metina nie docierały do graczy.** Zmiana w
  silniku z 1.29.0 była patchem, a na Windows launcher nie nakłada patchy —
  robi to tylko skrypt, który działa u autora. Do tego plik obrazu z podmianą
  zawartości szkatułki nie jechał w paczce. Efekt: po aktualizacji 30 Metinów
  nie dało ani jednej szkatułki i jedną księgę. Paczka wiezie teraz oba
  spatchowane pliki silnika tak samo jak źródła botów, plik obrazu i tabelę
  szkatułki; obraz zbudowany ścieżką gracza zawiera i tokeny, i tabelę.
- **Kowal ze Zwojem Błogosławieństwa.** Bez zwoju porażka ulepszania niszczy
  przedmiot — 1584 spalonych w jedno popołudnie. Ze zwojem z szkatułki bot
  ulepsza od +6 wzwyż ścieżką silnika ze zwojem: porażka to spadek o poziom,
  nie strata. Robi to z plecaka, w polu, bez kowala — jak gracz. W pierwsze
  trzy minuty: 10 sukcesów, 13 spadków o poziom, zero spalonych.

### Nowe

- **Góra Sohan i Loch Pająków V1 dla botów.** Sohan (Żołnierze Czarnego
  Wiatru i Dzicy, 26–36, trzy rodzaje Metinów) przyjmuje boty od 26: połowa
  26–29 idzie tam zamiast czekać w Bokjung, a 30–35 dzieli się na trzy
  między wyspy Fanatyków, pustynię i Sohan. Loch Pająków V1 (pająki 50–58)
  bierze połowę botów od 48 zamiast Doliny. Dziesięć hubów Sohan i osiem
  Lochu ze spawnów, wejścia z Town.txt, wyjścia przy NPC obok wejścia. Obie
  mapy przeniesione na rdzeń, na którym działają boty. Panel zna obie mapy i
  ma ich kafelki.

---

## 1.29.0 — 2026-09-06

### Nowe

- **Dolina Orków po poziomach, obozy Czarnych Orków dla grup po osiem.** Pięć
  wysp Fanatyków (35) i Arahanów (38) dla botów 30–39, szesnaście hubów
  gęstości dla 36+, trzy obozy Czarnych Orków (46) — (601,625), (774,923),
  (933,639) — dla grupy 40+, a wyspa środkowa z Dręczycielami (49), którzy
  noszą Księgę Klątw, dla grupy 45+. Boty 30–35 idą na wyspy Fanatyków albo
  na pustynię, po parzystości pidu. Grupa w Dolinie ma do ośmiu osób; każdy
  bot poziomu obozu może do niej wejść, nie tylko dziesięcioprocentowa
  kohorta; współgildianin liczy się w doborze za dwóch przyjaciół, a lider
  z gildią wybiera obóz po numerze gildii, więc jedna gildia zbiera się na
  jednym obozie. Marudera za liderem w drodze do nowego obozu grupa nie
  wyrzuca — 57 z 59 rozpadów pierwszej godziny to była właśnie ta droga.
- **Wspólna pamięć populacji: gdzie stoi najwięcej potworów.** Każde szukanie
  celu zapisuje w komórce 6400 jednostek, ile potworów było w zasięgu, jakiego
  poziomu i ile walk tam zaczęto; wpisy maleją o połowę co dziesięć minut.
  Hub wybiera się po udziale (potwory w zasięgu podzielone przez boty, które
  już tam są), o połowę taniej na 20 km, i trzyma cztery minuty. Obóz pełen
  potworów, których bot nie tknie sam, jest dla niego pusty. Raz na dziesięć
  minut `PLAYERBOT_SPOT:` wypisuje najbogatsze komórki każdej mapy — komórka
  bez huba, która wciąż wychodzi na wierzch, to hub, którego brakuje tabeli.
- **Szkatułka Blasku Księżyca jako event.** Szansa na tysiąc na zabity potwór
  (`M2_MOONLIGHT_CHEST_PERMILLE`, domyślnie 10) i osobno na kamień Metin
  (`M2_MOONLIGHT_CHEST_STONE_PERMILLE`, domyślnie 300), z CONFIG, bez
  przebudowy; 0 wyłącza. W środku, po wadze: Zaczarowanie i Wzmocnienie
  Przedmiotu, Zielona i Fioletowa Mikstura po pięć, Dłoń Krytyka i Dłoń
  Przebicia po trzy, Błogosławieństwo Życia i Smoka, Zwój Błogosławieństwa,
  Księga Umiejętności. Bot otwiera szkatułkę w ciągu sekund, zwoje bonusów
  idą przez istniejący dobór bonusów (własny zwój przed kupnem), mikstury
  szybkości przez istniejące picie, wzmocnienia pije na początku walki, a
  Błogosławieństwa są ostatnią miksturą w zapasie. W pierwsze pół godziny:
  315 otwartych szkatułek, 876 wypitych wzmocnień.
- **Trzy Księgi Umiejętności z każdego Metina.** Tabela dawała jedną z szansą
  od ćwierci do całości; teraz liczba ksiąg z kamienia jest dopełniana do
  trzech, każda z losową umiejętnością tak jak dotąd.
- **Cztery osobowości „Dropek”.** Dropek Metinów (co trzeci łowca Metinów)
  zbiera Księgi Umiejętności — także te, których nie przeczyta — i stawia je
  na straganie obok broni 30 lv. Dropek z M3 siedzi na Waryong po bronie 30
  lv do 32 poziomu, niezależnie od tego, czy ma własną. Dropek z M2 obozuje
  u Bestii w Bokjung po ich bronie do 40 poziomu. Dropek medali chodzi do
  Łatwego Lochu Małp po medale do 32 poziomu, nie tylko póki jego koń ich
  potrzebuje, i sprzedaje nadwyżkę. Co ósmy zwykły poszukiwacz jest jednym
  z trzech ostatnich. Dropek otwiera stragan na co trzeciej wizycie w mieście
  i dostaje stół handlarza. Panel zna ich nazwy.
- **Panel po polsku.** 305 wpisów słownika interfejsu miało tylko angielski,
  niemiecki i turecki, więc polska przeglądarka dostawała angielski; strona
  konta miała teksty wpisane na sztywno. Wszystko przetłumaczone.

### Naprawione

- **Launcher rozpoznaje port zarezerwowany przez Windows.** Po restarcie
  Hyper-V/WSL rezerwuje losowe zakresy portów; gdy 11000 albo 13000 w nie
  trafi, `docker compose` pada sekundę po zbudowaniu obrazów z „ports are
  not available … zabroniony przez uprawnienia”, a launcher pokazywał to jako
  nieznany błąd. Jeden gracz przeszedł tak pięć identycznych prób
  aktualizacji. Teraz diagnostyka sprawdza `netsh interface ipv4 show
  excludedportrange` przed startem, a po błędzie launcher wypisuje, co zrobić:
  `net stop winnat`, GRAJ, `net start winnat`.
- **Wybór huba nie goni najlepszego spotu przez całą mapę.** Pierwsza wersja
  pamięci spotów przełączała hub przy każdej decyzji: 160–334 dalekich planów
  na minutę, osiem tysięcy odroczeń, tick 57 s z 60. Waga odległości i
  przyklejenie do wyboru na cztery minuty sprowadziły to do 33–65 planów i
  ticku 10–18 s.

---

## 1.28.0 — 2026-09-06

### Nowe

- **Boty logują się stopniowo przez minutę po starcie serwera.** Do tej pory
  cała populacja wchodziła do świata w jednej sekundzie: 848 postaci, każda w
  pierwszym ticku prosiła o trasę, a budżet nawigacji to 32 plany na tick.
  Kto nie dostał trasy, stał; strażnik bezczynności go resetował; reset prosił
  znowu — 4075 resetów w pierwsze dziewięć minut i rdzeń na 99,9%. Teraz
  logowanie idzie partiami po 15 na sekundę, a pierwsze ciężkie przebiegi bota
  (ulepszanie, dobór sprzętu, zakupy, kamienie) są rozłożone po pidzie na tę
  samą minutę. Populacja 850 botów jest w świecie po 66 sekundach.
- **Raz na minutę serwer pisze, ile kosztowała populacja.** Linia
  `PLAYERBOT_LOAD:` w syslogu: czas ticku, liczba i czas planów tras w czterech
  koszykach odległości, odroczenia, szukanie celu, migawka panelu, skany mapy,
  zapisy, resety strażnika. Bez tej linii pierwsza wersja wędrówki po materiał
  została zdiagnozowana z samego CPU — i wszystkie skany populacji wpadły w
  jedną sekundę.

### Naprawione

- **Zużycie CPU przy 850 botach spadło z 63–68% do 26% rdzenia.** Planer tras
  pytał silnik o atrybut sektora na żywo dla każdego sąsiada każdego węzła A* —
  do 24 razy na węzeł — choć siatka nawigacji ma ten sam bit spróbkowany w tym
  samym punkcie. Tysiąc planów na minutę spędzało na tym 31 s z każdych 60.
  Teraz planer czyta siatkę; tylko chód (segment przed botem, raz na tick)
  pyta silnik, żeby wciąż zatrzymać bota przed czymś postawionym po zbudowaniu
  siatki. Plan przez całą Dolinę Orków: 513 ms → 50–80 ms; plan na 256–1024
  komórek: 35 ms → 5–10 ms.
- **Jeden tick nie zatrzymuje już świata na pół sekundy.** Budżet planów na
  tick liczył sztuki, a plan może kosztować 0,2 ms albo 80 ms. Obok liczby
  jest teraz czas: po 50 ms planowania reszta próśb w tym ticku idzie
  ścieżką odroczenia i wraca w ciągu dwóch sekund. Wiąże tylko w minucie po
  starcie.
- **Zapis postaci bota co 120 s zamiast co 30 s.** Silnik i tak zapisuje każdą
  postać co 120 s, a awans poziomu wymusza zapis natychmiast; boty dokładały
  cztery zbędne zapisy na jeden zapis silnika — blisko trzydzieści na sekundę.
- **Launcher mówi, czego brakuje, zamiast „exit 1".** Kontener
  `playerbot-migrate` kończy się w pierwszej sekundzie, gdy brak lub pusty jest
  plik `playerbots_seed.sql`; launcher kopiował go tylko wtedy, gdy źródło
  istniało, i milczał, gdy nie. Teraz brak źródła daje ostrzeżenie z pełną
  ścieżką, brak pliku w paczce zatrzymuje start przed `docker compose` z
  instrukcją co zrobić, a gdy `compose up` się nie uda, w logu launchera lądują
  ostatnie 40 linii z `playerbot-migrate`, `mariadb`, `game` i `panel`.

---

## 1.27.0 — 2026-09-06

### Nowe

- **Bot, któremu brakuje ulepszacza, idzie po niego do potwora, który go nosi.**
  Do tej pory brak materiału kończył się na targu — a jeśli lada była pusta,
  bot polował gdziekolwiek. Teraz przy wyborze celu potwór, którego przedmiot
  z tabeli dropu jest na liście braków, wygrywa z sąsiadami; a gdy w zasięgu
  nie ma żadnego, bot przeszukuje całą mapę i rusza do najbliższego. W pierwsze
  24 minuty 385 botów wyruszyło 1845 razy, z czego 500 po Amulet Orka.
- **Cena na straganie bierze się z zakończonych sprzedaży, nie ze stałego
  mnożnika.** Świat pamięta ostatnie ceny jednostkowe każdego przedmiotu.
  Przy dwóch sprzedażach lada wystawia medianę: 15% drożej, gdy ostatnia
  sprzedaż była w ciągu dziesięciu minut, 15% taniej, gdy nikt nie kupił od
  godziny — w klamrze między ceną u kupca a jej dwunastokrotnością. Cena
  wystawiona to nadzieja sprzedawcy; cena zapłacona to jedyny pomiar popytu.
- **Bot porównuje broń po tym, jak jego szkoła zadaje obrażenia.** Miecz sury
  Czarnej Magii i dzwon szamana mają w proto dwie pary wartości — fizyczną i
  magiczną — a wycena czytała tylko fizyczną. Szkoły czarujące (Czarna Magia,
  obie szkoły szamana) liczą teraz magię z połową fizyki; reszta fizykę z
  ćwiartką magii. Tak samo bonusy: średnie obrażenia są warte więcej szkołom
  ciosów, obrażenia umiejętności — szkołom skilli; wcześniej te drugie wpadały
  do domyślnego koszyka wartego dziesięć razy mniej.
- **Rybia Ość, Małż, perły i Zwój Błogosławieństwa są ulepszaczami.** Ośmiu z
  84 materiałów receptur nie ma typu „materiał"; Rybia Ość (13 receptur) szła
  do kupca jako „kieszonkowe wędkarza". Teraz o tym, co jest ulepszaczem,
  decyduje tabela receptur, nie typ przedmiotu.
- **Małż potrzebny do receptury nie jest otwierany.** 26 receptur zużywa go
  jako jest; otwieranie tego, po który bot i tak idzie do kowala, zamieniało
  pewny materiał na szansę na inny.
- **Kamień Duszy dobierany pod szkołę.** Kamień Potwora pierwszy dla każdego,
  Śmierci i Penetracji dla szkół ciosów, Powtórki dla szkół skilli, klasowe
  na końcu — w świecie potworów. Zbroja: Witalności, potem Uchylenia, Obrony.

### Naprawione

- **Bot wkładał Kamień Duszy z gwarancją sukcesu i za darmo.** Kamień był
  wpisywany wprost do gniazda i kasowany; gracz ma 30% szans, a przy porażce
  pęknięty kamień na stałe w gnieździe. Na żywym świecie stało 261 obsadzonych
  gniazd i zero pękniętych. Teraz kamień idzie tą samą ścieżką co u gracza —
  zdjęcie sprzętu, próba, odczyt gniazda, założenie. Pierwszego wieczoru:
  sześć pęknięć, jeden sukces.
- **Kamień Potwora był po stronie zbroi.** Podział rodzajów kamieni na
  broń/zbroję miał granicę o jeden za nisko; proto mówi jasno, że 28037 to
  broń. Poprzedni sposób wkładania nie zauważał różnicy.
- **Bot mógł przekuć broń w stopień, którego nie założy.** Silnik sprawdza
  poziom wyniku ulepszania tylko w wersji koreańskiej; ten serwer ma locale,
  więc kontrola była wyłączona. Pięć rodzin w zasięgu botów podnosi wymagany
  poziom z każdym plusem — Upiorna Kusza z 38 na 56, trzy dzwony z 52 na 60.
  Bot pyta teraz o poziom wyniku przed próbą.
- **Skan mapy po materiał spadał całym stadem naraz.** Po restarcie każdy bot
  robił go w tej samej sekundzie, i znowu co 90 s — rdzeń szedł na 100%.
  Pierwszy skan jest rozłożony po pidzie, a na jeden tick przypada ich
  najwyżej sześć. W stanie ustalonym rdzeń pracuje na 14%.

### Sprostowanie

Wcześniejsza analiza tego projektu twierdziła, że na hostowanych mapach da
się zdobyć 28 z 84 materiałów. To wynik błędnego odczytu `group_group.txt`.
Poprawnie: **64 z 84**, plus Rybia Ość z wędkowania. Skóra Niedźwiedzia,
której czekały 943 sztuki sprzętu na +6, wypada z niedźwiedzi na mapach 21
i 24 — nie brakowało dropu, brakowało kogoś, kto go zbierze.

---

## 1.26.0 — 2026-09-05

### Nowe

- **Boty wchodzą do Doliny Orków bramą Chunjo i rozchodzą się po wyspach.**
  Mapa ma cztery teleportery — po jednym na królestwo i jeden na środku,
  niczyj. Boty lądowały przy tym środkowym, więc cała populacja pojawiała się
  na wyspie centralnej. Teraz wychodzą tam, gdzie wychodzi postać z Chunjo.
- **Bot, który przez pięć minut nie ruszył się dalej niż o szerokość huba,
  idzie do następnego** — nawet jeśli akurat ma tu co bić. Rotacja po miejscach
  polowania działała wyłącznie w turze, w której nie było żadnego celu, a przy
  4041 punktach odrodzenia w Dolinie taka tura nie przychodziła nigdy. Razem
  z bramą Chunjo dało to jedną wyspę z dwudziestu trzech — a Amulet Orka
  i Ezoteryczny Przewodnik nie mają tam ani jednego punktu odrodzenia.
- **Ulepszacze krążą między botami.** Materiał, którego znalazca sam nie
  potrzebował, był złomem i szedł do kupca ogólnego przy najbliższej wizycie
  w mieście — niszczony w tempie, w jakim wypadał. Teraz zostaje jako towar na
  własny stragan, do ośmiu komórek (materiały się stackują). Na ladę trafiają
  wyłącznie te 84 materiały, których faktycznie żąda jakaś receptura, a nie
  wszystkie 240 przedmiotów typu materiał.
- **Boty nie zsiadają z konia przy teleporterze.** Zsiadanie ma sens przed
  rozmową z NPC; z teleporterem bot nie rozmawia, bo przejście jest serwerowe.
  W jeden wieczór było to 1362 zsiadania, każde z ponownym wsiadaniem trzy
  sekundy później po drugiej stronie.
- **Bot porównuje broń po obrażeniach w czasie, a nie po rodzinie.** Broń
  z zestawu na 30 poziom dostawała płaski bonus tak duży, że żaden bot nigdy
  jej nie wymieniał — FMS +4 wygrywał z mieczem na 36 poziom +7, który jest
  lepszy. Do tego silnik skraca o połowę odstęp między ciosami sztyletu
  i podwaja obrażenia łuku, więc na tych dwóch te same liczby są warte dwa
  razy tyle: sztylet na 30 poziom z 40-44 bije mocniej niż miecz z 57-73.
- **Mapy w panelu są dwa razy dokładniejsze.** Kafle 1024 zamiast 512, więc
  na mapie królestwa piksel to dwie komórki terenu, a nie cztery — mury,
  budynki i drogi przestały się rozmazywać. Jasne, piaskowe podłoże zamiast
  ciemnozielonego, bo nakładki cieplne są ciepłe i na ciemnym tle z nim
  konkurowały. Siatka mapy cieplnej z 44 na 72, więc ognisko wypada na
  budynku, a nie na dzielnicy. Doszła trzecia warstwa: **awanse umiejętności**.

### Naprawione

- **Boty potrafiły zamarznąć przy teleporterze na dobre.** Marsz do portalu
  ignorował to, czy udało się wyznaczyć trasę, i zawsze meldował sukces —
  a podróż zajmuje całą turę, więc nic poniżej już się nie wykonywało. Bot stał
  bez trasy, przeskakując cel co sześć sekund, a strażnik bezczynności resetował
  go w kółko prosto z powrotem w tę samą decyzję. Teraz mierzony jest postęp:
  bez ruchu przez dwadzieścia sekund bot oddaje turę i wraca do polowania.
- **Bot i potwór potrafili leczyć się nawzajem w nieskończoność.** Reguła
  „ta walka do niczego nie prowadzi" istniała tylko dla kamieni metin. Zwykły
  potwór był porzucany wyłącznie wtedy, gdy bot nie potrafił do niego dojść,
  więc walka z Czarnym Orkiem, który regenerował się szybciej, niż bot zdejmował
  mu życie, nie miała końca. Teraz obowiązuje ten sam test co przy kamieniach.
- **Boty przestały bić potwory dużo poniżej swojego poziomu.** Zwykły cel
  wybierany był po samej odległości, więc bot z 19 poziomu tłukł psy z 1
  poziomu pod murami Joan. Tabela doświadczenia silnika płaci za takiego
  potwora jedną setną — potwór niżej niż o dziewięć poziomów jest teraz
  pomijany, dopóki w zasięgu jest cokolwiek lepszego.
- **Postacie botów przepadały bezpowrotnie po przejściu na mapę drugiego
  rdzenia.** Takie przejście udaje się połowicznie: współrzędne się zmieniają,
  wstawienie do sektora nie — a zwykłe wylogowanie utrwala pozycję, której
  żaden start już nie wczyta. Bot nie był zablokowany ani bezczynny; był
  odrzucany przy każdym uruchomieniu i po prostu nie istniał. Teraz rozjazd
  między mapą a pozycją jest wykrywany i bot wraca do Bokjung.

  Postaci, które zdążyły utknąć wcześniej, poprawka nie odzyska — trzeba je
  przestawić raz w bazie:

  ```sql
  UPDATE player.player SET map_index = 21, x = 55700, y = 157900
  WHERE name LIKE 'bot%'
    AND map_index NOT IN (21,23,24,25,26,61,63,64,69,70,73,108,216,217);
  ```

- **Znak straganu znikał tylko tym, którzy akurat patrzyli.** Odwołanie szyldu
  leci do klientów będących w zasięgu w tej jednej chwili, więc kto podszedł
  sekundę później, widział bota z szyldem sklepu, którego nie da się otworzyć.
  Zamknięty stragan odbiera swój znak przez sześć sekund.
- **Szybka przebudowa serwera potrafiła po cichu wydać starą binarkę.** Dotyczy
  tylko osób budujących lokalnie przez `tools/fast-game-build`: ścieżka
  kontenera była przepisywana przez Git Bash, plik nie dostawał świeżego
  znacznika czasu i `make` uznawał go za aktualny. Teraz brak odświeżenia
  przerywa budowę zamiast wydać stary plik.

---

## 1.25.8 — 2026-09-05

### Nowe

- **Boty kupują wreszcie bransolety, naszyjniki i kolczyki.** Drabinę sprzętu
  miało pięć slotów; te trzy nie miały żadnej, więc bot nosił ozdobę tylko
  wtedy, gdy jakaś mu wypadła. Większość chodziła z trzema pustymi polami na
  karcie postaci przez całe życie.
- **Ozdoba jest dobierana do klasy, nie do poziomu.** Kolczyki rotują
  statystyką w miarę wzrostu — zwinność, siła, kondycja, inteligencja — więc
  najwyższy nie jest najlepszy dla każdego. Szaman na 62 poziomie bierze teraz
  kolczyk z 54 poziomu, bo ten ma inteligencję, a ten nowszy dałby mu siłę.
  Wojownik i sura walczący bronią biorą kolczyk z siłą, ninja ze zwinnością,
  szaman i sura magiczny z inteligencją.
- **Cała wycena sprzętu rozróżnia teraz klasy.** Siła, zwinność i inteligencja
  były warte po tyle samo, kimkolwiek byłeś. Statystyka, którą klasa walczy,
  jest teraz warta dwa razy tyle, a te nieużywane jedną piątą. Dotyczy to nie
  tylko zakupów, ale i porównywania tego, co wypadło z potwora.

### Naprawione

- **Do Lochu Małp praktycznie nikt nie chodził, a suwak konia w panelu nic nie
  robił.** Dwie osobne przyczyny. Warunek wyprawy wymaga poziomu 25, żeby koń
  mógł wejść z zera na jedynkę, a pasmo lochu kończyło się na 26 — razem dawało
  to okno **dokładnie dwa poziomy szerokie**, po którym drzwi zamykały się na
  zawsze. Na testowym świecie 446 botów było powyżej pasma i 435 z nich miało
  konia poniżej dziesiątki: odcięte od jedynego źródła medali, a przez to od
  konia bojowego. Teraz powyżej pasma bot nadal przychodzi po medal, dopóki ma
  konia do podniesienia, z trzykrotnie mniejszą szansą — i wychodzi, gdy tylko
  medal ma. Druga przyczyna: waga HORSE była czytana wyłącznie przez planer
  celów, a bramka, która faktycznie wysyła bota do lochu, nigdy o niej nie
  słyszała. Teraz suwak działa.
- **Boty kupowały najgorszą bransoletę w grze.** Wytrzymałość nie miała własnej
  wagi i wpadała do domyślnego kosza, więc dziesięć jej punktów ze startowej
  bransolety było warte więcej niż cokolwiek, co ta linia oferuje poniżej 46
  poziomu. Wytrzymałość to pasek biegu — jest teraz warta tyle co punkty many.

## 1.25.7 — 2026-09-05

### Naprawione

- **Bot sprzedawał konia bojowego kupcowi trzy minuty po tym, jak go zdobył.**
  Reguła złomowania mówi „to szrot", dopóki ktoś jej wyraźnie nie zaprzeczy.
  Medal konny taki wyjątek miał od dawna, z komentarzem o tym, że postęp w
  zadaniu musi przeżyć wizytę u kupca — nagroda, do której medal prowadzi, już
  nie. Pierwszy bot w historii, który ukończył próbę (dwadzieścia jeden medali,
  sto Czarnych Wichrów i 500 000 yang u stajennego), poszedł do miasta i sprzedał
  zwój przyzwania za swoją część z 1020 sztuk złota. W całym świecie nie został
  ani jeden.
- **Bot powyżej 36 poziomu przestawał ulepszać broń — na zawsze.** Drabina
  sprzętu sprawdzała tylko osiem stopni, a ósmy to w czterech z pięciu rodzin
  broń na 36 poziom. Bot uznawał, że jest już uzbrojony, i nigdy nie sięgał
  wyżej. Zgłoszony przypadek bota na 49 poziomie z bronią +0 nie był wyjątkiem,
  tylko regułą. Po zmianie drabina sięga tam, dokąd sięga rodzina:

  | broń | było | jest |
  |---|---|---|
  | miecz | 36 | **80** |
  | dwuręczny | 36 | **87** |
  | łuk | 36 | **80** |
  | dzwonek | 36 | **80** |
  | sztylet | 50 | **75** |

  Zbroja dostała dwa brakujące stopnie i sięga teraz 66 zamiast 54. Tarcze i
  buty już wcześniej dochodziły do końca swojej rodziny i nie były ruszane.
  Hełmy poszły w drugą stronę — o jeden stopień w dół, bo ósmy sięgał po hełm
  innej klasy; nic na tym nie tracimy, każda klasa dochodzi do swojego
  najlepszego hełmu w czwartym stopniu.
- **Boty z przemianowanym nickiem były niewidoczne na stronie.** Osiemnaście
  zapytań panelu pytało, czy nick zaczyna się od „bot" — więc mapa na żywo,
  wszystkie jedenaście rankingów, statystyki świata i strona sezonu przestawały
  je liczyć, gdy ktoś zmienił im nazwy. Panel pyta teraz o to samo co silnik: o
  konto `playerbot_NNN`, którego zmiana nicku nie dotyka. Stary test po nicku
  został jako drugie ramię, żeby ręcznie zrobiony bot na zwykłym koncie nadal
  był widoczny.

### Warto wiedzieć

- Wyższe stopnie broni (45 i dalej) oraz dwa nowe stopnie zbroi są na razie
  potwierdzone tylko z danych — żaden bot nie ma jeszcze poziomu, żeby po nie
  sięgnąć. Potwierdzone na żywym świecie zostały zakupy broni na 40 poziom,
  stopnia, który wcześniej dla bota nie istniał.

## 1.25.6 — 2026-09-05

### Naprawione

- **Bot w kółko próbował kupić to samo z tego samego straganu.** Regresja z
  1.25.5. Kiedy silnik odrzucał zakup, bot pytał o dokładnie to samo w następnym
  ticku — czyli raz na sekundę, aż wyprawa wygasła po półtorej minuty, po czym
  zaczynał od nowa. W dzienniku wyglądało to jak `Shop::Buy pos 0` bez końca.
  Silnik odmawia po cichu: „pełny plecak" i „za mało pieniędzy" zapisuje na
  poziomie logowania, którego nikt nie włącza, więc z zewnątrz widać było tylko
  powtarzane żądanie. Teraz odmowa kończy wyprawę, a bot z góry pomija pozycję,
  która mu się nie zmieści — **broń zajmuje trzy komórki plecaka, a wcześniej
  sprawdzane były dwie**.
- **Próba o konia bojowego liczyła mniej więcej co drugie zabicie.** Bot bije w
  dwóch miejscach: w pełnym cyklu decyzyjnym i w tańszym, pośrednim — a ten
  drugi nie zaliczał niczego. Pełny cykl nie mógł tego nadrobić, bo zabity cel
  jest podmieniany na żywego, zanim kod dojdzie do zaliczania. Do tego przepadały
  wszystkie zabicia dobite przez towarzyszy z grupy, więc bot polujący w drużynie
  potrafił nie ruszyć licznika ani razu. Zmierzone na żywym świecie: **2,6 → 7,7
  zabicia na minutę**.
- **Bot z medalem w plecaku tracił konia bojowego bezpowrotnie.** Próba wymaga
  konia dokładnie na dziesiątym poziomie, a nic nie powstrzymywało bota przed
  oddaniem kolejnego medalu i awansem na jedenastkę — po którym żaden medal,
  quest ani NPC już nie cofnie. Drabina zatrzymuje się teraz na dziesiątce,
  dopóki bojowiec jest do zdobycia. To nie jest zakleszczenie: odbiór sam ustawia
  konia na jedenaście i drabina rusza dalej. Przy okazji bot przestaje zbierać i
  kupować medale, których i tak nie może wydać.

### Warto wiedzieć

- Cały łańcuch konia bojowego przeszedł na żywym świecie **pierwszy raz**:
  medale u stajennego, dziesiąty poziom konia, wyjazd na pustynię, sto zabić
  Czarnych Wichrów, powrót, opłata 500 000 yang i zwój przyzwania w plecaku.
  Wcześniej zatrzymywał się na liczniku zabić i nikt nigdy nie dotarł do końca.

## 1.25.5 — 2026-09-05

### Naprawione

- **Boty w Dolinie Orków stały tylko na środku mapy.** Dolina to dwadzieścia trzy
  wyspy w delcie rzeki, połączone dwudziestoma dwoma mostami. W danych mapy rzeka
  ma znacznik blokady i znacznik wody, a **pomost nad tą rzeką ma samą wodę, bez
  blokady** — i właśnie tak mapa mówi „tędy można przejść". Nawigacja bota
  odrzucała każdą wodę, więc odrzucała też wszystkie mosty. Z punktu wejścia bot
  miał dostęp do 17,6% chodliwego terenu i 161 z 532 grup potworów, a mapa
  rozpadała mu się na dziewiętnaście osobnych kawałków. Teraz jest **jednym
  kawałkiem**. Woda jest przechodnia, ale kosztowna, więc bot wchodzi na most, bo
  innej drogi z wyspy nie ma, a płycizn na pustyni nie brodzi, kiedy obok jest
  suchy ląd.
- **Miejsca łowieckie Doliny obejmowały jedną wyspę.** Lista dwunastu punktów
  została kiedyś przycięta do tego, co bot potrafił osiągnąć przy zepsutej
  nawigacji — mieściła się w prostokącie 37×35 km na mapie, której potwory
  rozstawione są na 133×131 km, i obejmowała 128 z 532 grup. Nowe szesnaście
  punktów wyliczono z danych respawnu mapy: każdy to prawdziwe miejsce potworów,
  sprawdzone jako chodliwe i osiągalne z wejścia, rozstawione co najmniej 12 000
  jednostek od siebie. Obejmują 250 grup.
- **Na straganach leżał szrot.** Sprzęt na poziom 29 i niższy przy +4 albo +5 nie
  trafia już na ladę — z 487 takich sztuk w plecakach botów 272 były na poziom 29
  lub niżej, czyli o klasę za stare dla właściciela i bez wartości dla kogokolwiek
  innego. Wyjątki zostają: dobre bonusy, wszystko od +6, broń na 30. poziom,
  a także **tarcze i hełmy od 21. poziomu**, bo w tych dwóch slotach nie ma nic
  między sprzętem startowym a 41. poziomem.
- **Stragany z jedną sztuką.** Osiemnaście z trzydziestu czterech straganów
  otwartych w ciągu kwadransa niosło dokładnie jeden przedmiot. Lada wymaga teraz
  co najmniej dwóch pozycji — chyba że ta jedna jest tego warta sama w sobie:
  broń na 30. poziom, medal konny, mocny bonus albo ulepszenie od +6.

### Nowe

- **Boty chodzą na zakupy.** Wcześniej kupowały tylko z lady, która akurat stała
  dwadzieścia metrów od nich — stąd dwanaście zakupów na pół godziny przy siedmiu
  setkach botów. Bot, któremu brakuje składnika do ulepszenia, może rozwinąć konia
  albo nie ma broni na 30. poziom, idzie teraz na rynek, wybiera najbliższą ladę
  z tą rzeczą, **podchodzi pod nią** i tam kupuje; jeśli przyszedł po dwie rzeczy,
  zostaje po drugą. Wyprawa ma dziewięćdziesiąt sekund i kończy się w chwili, gdy
  bot stoi wśród straganów i nic go nie interesuje.
- **Mapa świata w panelu pokazuje przeprawy.** Tło mapy malowało każdą wodę jako
  rzekę, więc Dolina Orków wyglądała na deltę bez jednego przejścia — dokładnie
  tak, jak widziały ją boty. Mosty i brody mają teraz własny kolor, a kafle mają
  512 pikseli zamiast 256 i próbkują każdą komórkę pod pikselem, bo most ma 600
  jednostek szerokości i przy próbkowaniu samego środka połowa z nich znikała.

### Warto wiedzieć

- Jeśli u Ciebie Dolina Orków była pusta mimo botów na 36. poziomie i wyżej, to
  mogła być jeszcze jedna, osobna przyczyna: serwer dzieli mapy na trzy procesy,
  a bot nie ma klienta, który mógłby przelogować się między nimi, więc Dolina musi
  być na tym samym procesie co miasta. W kodzie jest tak od 1.22.0 i aktualizacja
  launcherem przebudowuje obrazy, więc nic nie musisz robić — ale jeśli obraz
  serwera jest starszy, boty będą stały pod teleporterem zamiast wejść na mapę.

## 1.25.4 — 2026-09-05

### Naprawione

- **Bot z szyldem sklepu biegający po lochu.** Przenosiny między mapami zwalniały
  wszystko, czego bot nie może zabrać ze sobą — wypisywały z grupy, kasowały cel,
  zsiadały z konia i odwoływały go, żeby nie został przy portalu — ale **sklepu
  nie ruszały**. Bot przeniesiony z otwartą ladą zabierał ją ze sobą, a sklep
  zamykał się dopiero na nowej mapie. Silnik rozsyła wtedy pusty szyld tylko do
  tych, którzy są w zasięgu wzroku **w tamtej chwili** — czyli do przypadkowych
  osób w miejscu docelowym. Ludzie, którzy ten szyld naprawdę widzieli, zostawali
  na rynku i nie dostawali niczego, więc szyld zostawał u nich przyklejony do
  postaci. Stragan jest teraz zamykany tam, gdzie został postawiony.
- **Aktualizacje trwały cztery minuty zamiast kilkunastu sekund.** Paczka 1.25.3
  niosła 4952 pliki zamiast ~200, bo wzorzec obejmujący zawartość `/static`
  zaciągał 4768 wygenerowanych ikon z kontekstu obrazu — a każdy z nich jest
  jeszcze kopiowany do kopii zapasowej. Wysyłane jest teraz samo źródło.
- **Dziennik launchera był częściowo nieczytelny.** Skrypt akcji działa ukryty, z
  wyjściem przekierowanym do pliku, więc pisał stroną kodową konsoli, a launcher
  czytał ten plik jako UTF-8. Dlatego w jednym logu stały obok siebie linie
  poprawne i rozsypane. Obie strony mówią teraz tym samym kodowaniem, a to, co
  trafia do pliku, jest dodatkowo zapisywane bez polskich znaków — bo ten plik
  ląduje w Notatniku i we wklejkach, gdzie ogonki i tak nie przechodzą. Okno
  launchera zostaje z ogonkami, tam wyświetlają się poprawnie.

---

## 1.25.3 — 2026-09-05

> Jeśli po aktualizacji panel nadal pokazuje starą wersję albo brakuje w nim
> nowych zakładek — **to jest ta poprawka**. Przebudowa obrazu, nawet z
> `--no-cache`, nie mogła tego naprawić.

### Naprawione

- **Panel raportował wersję sprzed wielu aktualizacji.** Panel czyta numer z
  `linux-port/docker/panel/app/VERSION`, który stawia tam `prepare-context.sh` —
  skrypt, jak dokumentuje sam `start-server.ps1`, **nigdy nieuruchamiany na
  maszynie gracza**. Plik zostawał więc na wartości z instalatora niezależnie od
  liczby aktualizacji: u jednego z operatorów panel po trzech wydaniach dalej
  mówił 1.15.6, a `docker compose build --no-cache panel` niczego nie zmieniał,
  bo budował ze starego pliku.
- **Dziewięć innych plików miało ten sam problem.** Przejrzeliśmy wszystko, co
  `prepare-context.sh` przygotowuje, i porównaliśmy z tym, co paczka wysyła.
  Zamrożone od instalacji były: `panel/app/VERSION`, `panel/app/CHANGELOG.md`
  (dziennik zmian w panelu), `items.json`, `favicon.png`, cała zawartość
  `/static`, `panel/schema/web_admin_schema.sql` (schemat bazy dla funkcji
  panelu), `game/quest/web_admin.quest` (pomocnik teleportacji z panelu),
  `high_risk.quest` oraz `mob_drop_item.m3.append.txt`. Skrypt startowy
  synchronizuje teraz wszystkie, a paczka niesie ich źródła.
- **Wzorzec `katalog/*` w liście aktualizacji schodzi w podkatalogi.** Dotąd
  łapał wyłącznie pliki bezpośrednio w katalogu, więc `files/static/*` nie
  pasował do niczego. Dodanie drugiego zestawu ikon nie wymaga już edycji listy.

---

## 1.25.2 — 2026-09-05

### Naprawione

- **Panel po aktualizacji zostawał stary.** Panel istnieje w dwóch kopiach:
  `files/admin_panel.py` jest źródłem, a `linux-port/docker/panel/app/admin_panel.py`
  jest tym, z czego powstaje obraz. Przepisuje jedną na drugą `prepare-context.sh`,
  który — jak `start-server.ps1` sam odnotowuje w trzech miejscach — **nigdy nie
  uruchamia się u gracza**. Skrypt startowy nadrabiał to dla źródeł botów, dla
  Makefile i dla seeda SQL, a o panelu zapomniano. Efekt: aktualizacje 1.25.0 i
  1.25.1 przynosiły poprawny panel w `files/`, a obraz i tak budował się ze
  starej kopii — więc suwaki zachowania botów i strona sezonu **nie pojawiały
  się mimo zainstalowanej nowej wersji**. Skrypt startowy synchronizuje teraz
  panel tak samo jak resztę, a obie kopie w paczce są zgodne.

---

## 1.25.1 — 2026-09-05

> Dalej **wydanie eksperymentalne**, na tych samych zasadach co 1.25.0: baza nie
> jest ruszana, powrót do poprzedniej wersji nic nie psuje.

### Naprawione

- **Stragany przestały wystawiać szrot.** W wycenie towaru siedziała łapanka
  `return 1` na wszystko, co nie wpadło do żadnej sensownej kategorii — więc bot
  z ośmioma spadami po +1 wystawiał całą ósemkę. W plecakach botów na
  testowanym świecie leżało **1902 sztuki sprzętu +0…+3** wobec 219 sztuk od +4
  wzwyż, czyli ta jedna linia decydowała o wyglądzie całego targu. Zwykły sprzęt
  wchodzi teraz na ladę **od +4**, a co nie jest ani sprzętem, ani nazwaną
  kategorią (broń na 30 lv, duży bonus, +6, medal konny, ulepszacz, księga) — nie
  jest towarem w ogóle. Lady mają 1–8 pozycji zamiast ośmiu napchanych.
- **Szyld sklepu, którego nie dało się otworzyć.** Silnik rozsyła szyld do
  wszystkich w pobliżu **jedną linijkę przed** utworzeniem sklepu, a gdy tworzenie
  się nie uda, nikt tego szyldu nie cofa: `CloseMyShop` kasuje go tylko wtedy, gdy
  jest co zamykać. Postać odchodziła ze sklepem, którego nie da się kliknąć.
  Teraz szyld jest zdejmowany zawsze, gdy sklep nie powstał albo zniknął bez
  naszego udziału.
- **Bot prowadzący stragan zdejmuje swoje buffy.** Nic nie rzucał — hak straganu
  przerywa pętlę decyzji przed umiejętnościami — ale aura rzucona przed
  siadnięciem do lady dopalała się jeszcze kilkanaście minut i wyglądała, jakby
  postać grała, stojąc w sklepie.

### Nowe

- **Boty zdobywają konia bojowego.** Wzorem jest quest stajennego i większość
  została: 35. poziom postaci, koń już na dziesiątce, sto zabitych potworów na
  pustyni, 500 000 yang na koniec, wydana Księga Opancerzonego Konia i zabrane
  Zdjęcie Konia. Trzech rzeczy nie dało się zachować i każda z nich to fakt o
  tym świecie, a nie decyzja: potwory z questa (2105 i 2107) **nie są nigdzie
  spawnowane**, więc próba liczy bandę Czarnego Wiatru z tej samej pustyni;
  limitu pół godziny nie ma, bo bot poluje godzinami i nie ma komu przegrać; a
  ośmiu do szesnastu godzin oczekiwania też nie, bo populacja, która nigdy się
  nie wylogowuje, przeczekałaby je w logu.
- **Bot, który zdobył konia, przestaje przepalać yang.** Pierwsza obserwacja na
  żywo pokazała bota, który skończył próbę z 432 000 yang i w dwadzieścia minut
  zszedł do 149 000 u kowala i na kamieniach bonusowych — konia nie odebrałby
  nigdy. Kowal, kamienie i zakupy na targu omijają teraz odłożoną opłatę.

---

## 1.25.0 — 2026-09-05

> **Wydanie eksperymentalne.** Wchodzi naraz kilka nowych systemów, które
> dotykają tego, jak boty planują cały swój czas, a nie pojedynczej funkcji.
> Baza danych nie jest ruszana i cofnięcie się do 1.24.9 nic nie psuje, ale
> spodziewaj się, że coś będzie wymagało dostrojenia. Zgłoszenia są mile
> widziane — szczególnie takie z opisem, co bot robił i gdzie.

### Nowe

- **Zachowanie botów regulujesz suwakami w panelu, na żywo.** Nowa strona
  **🧠 Zachowanie botów** daje jedenaście wag: kupowanie mikstur, kowal, księgi
  umiejętności, koń, Biolog, metiny, grupy, misje polowania, zwykłe bicie
  potworów, wędkowanie i stragany. 100 to dokładnie tak, jak serwer był
  zbudowany; 25 znaczy cztery razy rzadziej, 250 — dwa i pół raza częściej.
  Zapis działa w ciągu pięciu sekund, **bez restartu i bez rozłączania kogokolwiek**.
  Ucieczka z przegranej walki, wybór profesji i zdobycie broni nie podlegają
  suwakom — to nie są preferencje.
- **Sezon tygodniowy i rekordy serwera** pod adresem `/season`, dostępne bez
  logowania. Metiny, bossy i ulepszenia, które weszły na +7 lub wyżej, z
  ostatnich siedmiu dni, oraz kafle z rekordami od początku istnienia świata.
  Statystyki liczą się **wstecz przez całą historię serwera**, bo silnik i tak
  zapisywał te zdarzenia od pierwszego dnia — nie trzeba było niczego doliczać.
- **Boty zakładają gildie.** Na 40. poziomie i za 200 000 yang, dokładnie jak
  gracz u Strażnika Wsi. Mistrz gildii przyjmuje potem stojące obok boty tego
  samego królestwa. Herbów jeszcze nie ma.
- **Boty pamiętają, z kim polowały.** Wspólna grupa buduje znajomość, a przy
  szukaniu drużyny bot wybiera teraz tego, z kim już mu się układało, zamiast
  pierwszego napotkanego.

### Naprawione

- **Koń bojowy wreszcie może walczyć.** W pętli decyzji siedziało bezwarunkowe
  zsiadanie wykonywane przed wyborem celu — napisane, zanim walka z siodła w
  ogóle powstała. Bot dojeżdżał do metina konno i natychmiast lądował na ziemi.
  Teraz zsiadają tylko te boty, które i tak nie mogą bić z konia, a decyzja
  zapada tam, gdzie cel jest już znany — więc bot, który podszedł pieszo, potrafi
  też **wsiąść** przed walką.
- **Odporność na omdlenie (NNO) przestała być wyrzucana.** W wycenie bonusów nie
  miała własnego przypadku i wpadała do gałęzi domyślnej, a wartość linii
  immunitetu wynosi 1 — czyli najcenniejszy roll na tarczy w całej grze był dla
  bota wart mniej niż punkt szybkości ruchu i szedł do przerzucenia. Doszły też
  warunki zatrzymania: tarcza z NNO, broń na 30. poziom ze średnimi obrażeniami
  od 30%, pancerz i biżuteria z 1500 PŻ **nie są już nigdy przerzucane**, choć
  nadal mogą dostać kolejną linię.
- **Piąta linia bonusów.** Silnik pozwala na pięć, a pętla kończyła na czterech —
  każdy bot na świecie chodził o jedną linię uboższy. Na uruchomionym świecie
  przedmiotów z pięcioma liniami przybyło z 7 do 108 w ciągu godziny.
- **Boty przestają pilnować jednego respawnu.** Po dojściu na miejsce, na którym
  nie ma już czego bić, planer przesuwał je o siedemset jednostek i czekał
  kolejne 8–12 sekund, w kółko. Teraz idą do następnego miejsca, do którego da
  się dojść. Dotyczy Doliny Orków i Pustyni Yongbi.
- **Logi przestały zagłuszać serwer.** Katalog logów jednego rdzenia miał 4,5 GB
  przy 126 MB pozostałych i rósł o 155–278 MB na godzinę, przy 43 wpisach SYSERR
  na sekundę — a **żaden z nich nie sygnalizował usterki**. Cztery komunikaty
  pisane z pętli przez każdego bota na mapie: dwa nasze, dwa silnika, wszystkie
  na poziomie zapisywanym zawsze. Nasze mają teraz licznik i jedną linię na
  minutę, komunikaty silnika zeszły na poziom diagnostyczny. Po zmianie: **50 MB
  na godzinę i jeden wpis SYSERR na pięć sekund**.
  Efektem ubocznym okazał się wyraźny wzrost tempa gry — przy niezmienionej
  liczbie botów liczba zabić w oknie piętnastu minut wzrosła z ~265 do ~4100.
  Zapisywanie tych logów kosztowało serwer więcej, niż ktokolwiek podejrzewał.

### Zmienione

- Kod botów rozbity na kolejne moduły: planowanie celów, wagi z panelu, bonusy,
  gildie i wyciszanie logów mieszkają teraz w osobnych plikach.
- Łatki silnika są wyszukiwane po wzorcu, a nie wymieniane z nazwy. Jedna z list
  zdążyła się już rozjechać — łatka straganów była nakładana, ale nie wchodziła
  do sumy kontrolnej budowania, więc jej zmiana nie unieważniała gotowego obrazu.

---

## 1.24.9 — 2026-09-05

### Zmienione

- **Stragany wystawiają to, co gracz faktycznie chce kupić**, w tej kolejności:
  - **Broń na 30. poziom** — przy dowolnym ulepszeniu, także bez żadnego. To przedmiot, po który boty jeżdżą przez pół świata.
  - **Przedmioty z dużym bonusem** — od +1000 PŻ wzwyż, oraz tarcze z blokiem lub odbiciem ciosu, bo tarczę kupuje się dla tego, a nie dla liczby obrony.
  - **Zapasowy sprzęt od +6** zamiast dotychczasowego +7. To jednocześnie nowa granica, poniżej której nic nie trafia do handlarza NPC za jedną piątą wartości.
  - **Ulepszacze** — mają zarezerwowaną **połowę lady**, bo sama wycena je z niej wypychała.
  - **Księgi umiejętności** — żaden bot ich nie czyta, więc to czysty towar.
- **Medale konne trafiają na sprzedaż** u handlarzy oraz u botów, których koń i tak czeka na wyższy poziom postaci. Wcześniej były wykluczone całkowicie, więc **nikt nie mógł ich kupić**.
- **Kupujący chcą tego samego.** Medalu, jeśli mają jeszcze konia do wychowania — to godziny lochu, których nie muszą biegać. Broni lv 30 swojej klasy, gdy żadnej nie mają. Oraz przedmiotu z dużym bonusem nawet wtedy, gdy baza wypada na równi z noszonym, bo tysiąc życia nie wchodzi do wyceny sprzętu.

### Naprawione

- **Plac handlowy zwężony do zasięgu, w którym gra pozwala kupować.** `shop_manager.cpp` odrzuca zakup powyżej 2000 jednostek, czyli 20 metrów. Rozstawienie lad na 40 metrów sprawiło, że rynek wyglądał przestronnie i przestał działać: przy dziesięciu straganach i 89 zamożnych botach w mieście nie doszło do **ani jednej** transakcji przez piętnaście minut. Rozrzut wynosi teraz 4–17 metrów — nadal siedem razy więcej niż na początku, ale każda lada jest osiągalna. Tego sufitu nie da się podnieść po naszej stronie.

---

## 1.24.8 — 2026-09-05

### Naprawione

- **Stragany wreszcie powstają w Joan.** Losowanie 90/10 działało poprawnie i było bez znaczenia, bo w ścieżce straganu został twardy warunek z czasów, gdy rynek istniał tylko w Bokjung — i stał **przed** losowaniem. Bot stojący w Joan odpadał, zanim zdążył wybrać miasto. Sprawdzone na uruchomionym świecie: stragany stają teraz w obu miastach, bez ani jednej odmowy.

### Zmienione

- **Plac w Joan przeniesiony pod Strażnika Wsi** na komórkę (634, 639), a stragany rozstawiają się w promieniu **8–40 metrów** zamiast dotychczasowych dwóch i pół. Między ladami da się przejść, a każdy bot ma stały własny punkt, więc rynek nie przestawia się przy każdym otwarciu.
- **Nowa osobowość: Handlarz.** Mniej więcej co szósty bot bez innego powołania. Handlarz trzyma stragan zawsze, gdy może, a nie raz na dziesięć razy; wystawia **20 pozycji** zamiast ośmiu; pracuje na zmianę 10–20 minut; i **nie przerywa handlu, żeby biec po medale konne** — ta wyprawa zabiera pół świata i godzinę, czyli dokładnie to gonienie za czymś, czego ta osobowość ma nie robić. W panelu widnieje jako **Handlarz** z ambicją **Handel**.

### Warto wiedzieć

- **Ambicja bota jest wyłącznie etykietą.** Trafia do pliku statusu i na stronę, ale żaden kod nigdy się na niej nie rozgałęział — dotyczy to także ambicji, które istniały wcześniej. Zachowanie Handlarza wynika z osobowości, nie z ambicji.

---

## 1.24.7 — 2026-09-05

### Naprawione

- **Boty kończą uderzenia.** Rytm ataku był odmierzany płaskimi 480 ms, skalowanymi tylko szybkością ataku. Klient przyjmuje kolejne uderzenie combo dopiero od `DirectInputTime`, a ta wartość jest **późniejsza niż 480 ms dla każdej broni w grze**: 533 ms miecz jednoręczny, 732 szable, 932 dwuręczny, cała sekunda łuk. Trwająca animacja była więc za każdym razem ucinana.
  - **Ostatnie uderzenie było ucinane najmocniej.** Krok combo, który ma `DirectInputTime` równe zero, w ogóle się nie łączy — kończy sekwencję i klient odgrywa go w całości. Czwarte combo dzwonka jest właśnie takie i potrzebuje 1333 ms, a dostawało niecałe 400.
  - Czasy pochodzą z danych animacji, które serwer i tak wozi w `share/data/pc`, i są generowane przez `tools/generate_swing_timing.py` — 4 klasy × 6 rodzajów broni × 4 kroki combo. Dla łuku, który nie ma łańcucha combo, brana jest pełna długość animacji.
  - **Boty przez to zwolniły, celowo.** Biły mniej więcej dwa razy szybciej, niż pozwala animacja, a obrażenia idą razem z pakietem — więc tempo zdobywania poziomów spadnie proporcjonalnie. To do wyrównania osobnym mnożnikiem, nie oszukiwaniem animacji.
- **Ranking umiejętności pokazuje najwyższą rangę, nie sumę poziomów.** Sumowanie premiowało rozłożenie punktów po całym drzewku. Teraz widać to, co powiedziałby gracz: `M10 Silne Ciało`, `G1 Przywołanie Błyskawicy`, `P Berserk` — i po tym idzie sortowanie.

### Zmienione

- **Stragany mają wreszcie towar.** Bot wystawiał dokładnie jeden przedmiot; teraz na ladzie stoi do **ośmiu**, najlepsze na przedzie, więc ulepszacze i zapasowy ulepszony sprzęt idą pierwsze. Kupujący przechodzi całą ladę i bierze pozycję, która go interesuje, a nie zawsze pierwszą.
- **Stragan można wystawić od 1. poziomu.** Wymóg 20. poziomu był nasz, nie gry — tobołek (przedmiot 50200) ma w tabelach `LIMIT_NONE`. To dlatego w Joan nie było żadnego straganu: z pięciuset botów stojących tam pięć miało dwudziestkę, podczas gdy w Bokjung było ich sto dwadzieścia.
- **Wyprzedany stragan się zwija** i bot wraca do gry, zamiast stać przy pustej ladzie do końca licznika.

---

## 1.24.6 — 2026-09-04

### Naprawione

- **Boty przestały rzucać buffy bojowe poza walką.** Wersja 1.24.2 zdjęła wymóg posiadania celu, bo boty wchodziły do każdej walki bez niczego — ale poszła za daleko w drugą stronę: stały w mieście, rzucając aurę, silne ciało czy czarowane ostrze, które i tak wygasały, zanim dotarły do potworów kilometr dalej. Teraz buff bojowy wchodzi tylko wtedy, gdy bot jest w walce albo był w niej na tyle niedawno, że zaraz będzie w następnej (okno 60 sekund — dłuższe niż przerwa na dobiegnięcie do kolejnego potwora i podniesienie łupu, krótsze niż droga do miasta).
- **Umiejętności przydatne w drodze działają bez zmian, wszędzie.** To **Bezszelestny Chód** ninja i **Zwinność** szamana — obie przyspieszają ruch, a chodzenie jest tym, co bot robi najczęściej.
- **Leczenie szamana też zostało poza tą blokadą.** To nie buff, tylko leczenie zależne od własnego zdrowia, a ranny bot wracający do miasta ma więcej powodów, żeby je rzucić, niż ten w walce.

---

## 1.24.5 — 2026-09-04

### Dodane

- **Trzy nowe zakładki w rankingach na stronie**, obok Konia i Biologa:
  - **Otwarte sklepy** — kto właśnie prowadzi stragan i w którym mieście.
  - **Umiejętności** — suma wyuczonych poziomów umiejętności.
  - **Przedmiot +9** — boty posiadające dowolny sprzęt na +9, z ikoną i oznaczeniem, czy nosi go na sobie, czy trzyma w plecaku.
- **Boty raportują osobną akcję „Prowadzi stragan".** Dotąd sklepikarz zgłaszał tę samą akcję co bot w drodze, więc z zewnątrz nie dało się odróżnić handlującego od przechodzącego — a otwarty stragan istnieje wyłącznie w pamięci silnika i baza nic o nim nie wie. Panel czyta teraz tę akcję z pliku statusu i na niej opiera zakładkę.

### Uwagi

- Zakładka **Przedmiot +9** będzie pusta, dopóki któryś bot nie dobije do +9. W chwili wydania wszystkie przedmioty +9 w świecie należały do postaci gracza, nie do botów; botom udało się dojść do +8.

---

## 1.24.4 — 2026-09-04

### Zmienione

- **Stragany stoją teraz w kole.** W Joan wokół **Strażnika Wsi**, w Bokjung na dotychczasowym placu targowym. Każdy bot ma stały kąt na okręgu i wraca zawsze na to samo miejsce, więc krąg nie rozłazi się przy kolejnych otwarciach.
  - Pozycja strażnika nie jest zgadnięta: to NPC 11002 z komórki (633,640) mapy `metin2_map_b1`, której `BasePosition` wynosi (0,102400) — czyli świat (63300,166400). Ten sam rachunek daje istniejącej stałej `PLAYERBOT_M1_TELEPORTER` jej (51900,153600) z komórki (519,512), więc jest sprawdzony. Wokół strażnika nie stoi żaden inny NPC w promieniu czterdziestu komórek.
- **Przy każdym wystawieniu bot losuje miasto: 90% szans na Joan, 10% na Bokjung.** Losowanie jest za każdym razem od nowa, nie przypisane botowi na stałe. Nic nie jest zapamiętywane — bot, który wylosuje miasto, w którym akurat nie stoi, po prostu tym razem nie wystawia i losuje ponownie przy następnej próbie, więc nikt nie utknie w oczekiwaniu na miasto, do którego rzadko zagląda.
- **Kupujący szukają straganów w obu miastach.** Wcześniej przeglądali wyłącznie Bokjung — po przeniesieniu większości sklepów do Joan dziewięć straganów na dziesięć zostałoby bez klientów.

---

## 1.24.3 — 2026-09-04

### Naprawione

- **Prywatne stragany wreszcie działają — botów i graczy.** Silnik zaczyna `OpenMyShop` od warunku `GetPart(PART_MAIN) > 2`, a `PART_MAIN` przechowuje vnum **założonej zbroi**. Niezałatany silnik odmawiał więc straganu każdemu, kto ma na sobie zbroję — również żywemu graczowi, który próbował wystawić sklep sam.
  - Łatka `0004-private-shop-guard.patch`, która zamienia ten warunek na `IsPolymorphed()`, istnieje od dawna, jest w paczce aktualizacji i leży w każdej instalacji — ale nakłada ją `prepare-context.sh`, którego ścieżka przebudowy w launcherze **nigdy nie uruchamiała**. Łatka była dowożona i nigdy nakładana.
  - Launcher nakłada teraz łatki silnika przy każdej przebudowie, **odkrywając** katalog zamiast trzymać listę nazw. To trzeci błąd tej samej klasy po seedzie i wildcardzie w Makefile.
  - O tym, czy łatka już jest, decyduje **odczyt plików docelowych**, a nie kod wyjścia `patch`. Podczas pracy nad tym `patch -N` z busyboxa nałożył 18-kilobajtową łatkę integracji na drzewo, które już ją miało, i zdublował w niej wszystkie deklaracje. Porównywany jest cały blok hunka wraz z kontekstem — pojedyncza dodana linia nie wystarcza, bo `if (IsPolymorphed())` występuje w `char.cpp` w trzech innych miejscach.
  - Gdy nałożenie się nie powiedzie, launcher **mówi o tym wprost** zamiast po cichu zgłosić sukces.
- **Boty ze straganem nie rzucają już buffów.** Rzucanie skilla nie zamyka prywatnego sklepu — silnik zamyka go tylko przy ogłuszeniu, śmierci i wyjściu ze świata — ale sklepikarz machający aurą przy ladzie marnował manę i wyglądał niepoważnie.
- **Rynek w Bokjung jest wyłączony ze strefy buffowania.** Ten warunek obejmował dotąd wyłącznie mapę 21, a rynek jest na mapie 23.

---

## 1.24.2 — 2026-09-04

### Podziękowania

- **OskarPWA** udostępnił swoją wersję panelu i zgodził się, żeby wziąć z niej dwie rzeczy: **okno magazynu bota** oraz **ikony przy umiejętnościach**. Jedno i drugie jest w tym wydaniu. Dzięki!

### Dodane

- **Magazyn bota na stronie.** Obok ekwipunku doszła ikona magazynu. Okno jest niezależne od karty bota: można je przeciągać po stronie i zostaje otwarte, gdy zamkniesz i otworzysz kartę. Siatka 5×9 jest tą samą, którą rysuje ekwipunek.
  - **Uwaga na teraz:** boty jeszcze nie korzystają z magazynu — w kodzie AI nie ma ani jednego odwołania do skrytki — więc okno będzie pokazywać „Magazyn jest pusty", dopóki nie dołożymy botom samego zachowania. Sam widok działa.
- **Ikony przy umiejętnościach.** Każda umiejętność na karcie bota ma teraz swoją ikonę, z osobnym wariantem dla mistrzowskich (M/G/P). Gdy ikony nie ma w danej instalacji, nazwa wyświetla się sama, bez zepsutego obrazka.

- **Nazwy bonusów na przedmiotach są teraz takie jak w grze.** Panel miał własną, ręcznie pisaną listę; teraz opisy pochodzą wprost z klienta — numery z enuma serwera, przypisanie z `AFFECT_DICT` klienta, brzmienie z jego polskiego `locale_game.txt`. Nic nie jest tłumaczone na piechotę.
  - **`71` i `72` były zamienione miejscami.** `71` to Obrażenie Umiejętności, `72` to Średnie Obrażenia — istotne przy FMS/RIB.
  - **Brakowało bonusów `87`–`91`**, więc odporność na lód, ziemię i mrok oraz odporności na cios krytyczny i przeszywający pokazywały się jako „Bonus #89" i podobne.
  - **`42` i `47`** (szansa na odzyskanie PE/PŻ po zabiciu) były pokazywane jako zwykłe liczby zamiast procentów, a **`48`–`50`** dostawały doklejone „+1%", choć w grze to same nazwy bez wartości.
  - **`51` i `77` zniknęły z opisów.** `51` to spakowana liczba (numer umiejętności plus wartość), a nie bonus do pokazania; `77` nie występuje w tym kliencie.
  - Wartość ujemna nie da już zapisu `+-10`.

### Naprawione

- **Aktualizacja przestała kończyć się błędem Dockera.** Zatrzymanie serwera wyłącza także Docker Desktop, a aktualizacja szła prosto do budowania i trafiała na martwy silnik — już po podmianie plików. Rozsądna kolejność (zatrzymaj, potem zaktualizuj) zawodziła zawsze. Teraz silnik jest podnoszony przed budowaniem. To samo dotyczyło przycisku GRAJ, który dokańczał zaległe budowanie, zanim cokolwiek zdążyło uruchomić Dockera.
- **Launcher przestał zgłaszać wersję, której nie ma.** Numer zapisywał się dopiero po udanym budowaniu, więc po nieudanym launcher w kolejnych uruchomieniach wciąż podawał poprzednią wersję, proponował tę samą aktualizację i pobierał ją od nowa — za każdym razem z nowym katalogiem w `backups`.
- **Teleportacja do bota działa dla każdego.** Przycisk wysyłał na sztywno wpisaną nazwę postaci, więc na każdej instalacji przenosił tę jedną postać, a wszystkim pozostałym po cichu nie robił nic.
- **Boty mają włączone swoje najważniejsze umiejętności.** Buffy rzucały się wyłącznie wtedy, gdy bot miał już cel — czyli bot wchodził do każdej walki bez nich, tracił pierwsze sekundy na rzucanie, a po walce znów stał goły. Teraz utrzymuje je także poza walką.
  - **Sura WP zdejmowała sobie Czarowane Ostrze.** Na liście buffów było 66, czyli Rozproszenie Magii — a to nie buff, tylko atak z flagą `REMOVE_GOOD_AFFECT`, rzucany sam na siebie. Czarowana Zbroja (65) nie była buffowana w ogóle.
  - **Wojownik nigdy nie rzucał Berserku, a szaman jednego z dwóch buffów.** Numery umiejętności były skrzyżowane z flagami efektów, przez co włączony jeden buff raportował drugi jako już aktywny. Sprawdzone w `skill_proto`.

---

## 1.24.1 — 2026-09-04

### Fixed

- **Boty faktycznie kupują na rynku.** Wersja 1.24.0 wystawiała towar i nikt go nie brał, bo zakup wymaga **dwóch** rzeczy naraz, a ustawiona była jedna: `CShopManager::Buy` odrzuca kupującego, który nie jest zarejestrowany jako **gość straganu** (to `AddGuest` ustawia `ch->GetShop()`), nawet gdy właściciel sklepu jest ustawiony poprawnie. Bez tego funkcja wychodziła w pierwszej linii, po cichu.
  - Przy okazji filtr wykluczał boty z `bVisitingShop` — czyli akurat te, które są w mieście i stoją przy rynku. Rynek nie miał w ogóle klientów.
  - **Sprawdzone na serwerze:** transakcje bot–bot z przepływem yanga w obie strony.

---

## 1.24.0 — 2026-09-04

### Changed

- **Bot pilnujący straganu milczy.** Nad głową ma już szyld sklepu, a linia statusu zamazywała jedyną etykietę, której przechodzący gracz naprawdę potrzebuje — nazwę straganu, który właśnie rozważa otworzyć. Ta sama zasada wycisza okrzyk o udanym ulepszeniu.
- **Yang podnoszony pierwszy i niemal natychmiast.** Kolejka łupu sortowała się wyłącznie po odległości, więc bot mijał trzy kupki monet w drodze do skóry, a potem wracał po każdą z osobna — czas schodził na chodzenie po wyczyszczonym polu. Yang idzie teraz przed przedmiotami, a jego opóźnienie spada z 1000–1800 ms na **150–350 ms**. To zresztą yang płaci za mikstury, które pozwalają dalej zabijać.
- **Łatwy Loch Małp dostał własne pasmo poziomów: 18–26.** Wyprawa zależała dotąd tylko od poziomu konia i klasy, nigdy od poziomu postaci — na żywym świecie siedziało tam **48 botów na poziomach 25–35**, tracąc półgodzinne wizyty na medale warte grosze wobec tego, co ten sam czas daje na granicy.
  - Warunek sprawdzany jest w jednym miejscu i działa w obie strony: bot już w środku przelicza go co takt, więc ten, który wyrośnie z pasma, kończy, co robi, i wychodzi, zamiast czekać na trzydziestominutowy limit.
  - **Sprawdzone na serwerze:** po przebudowie **wszystkie** działające boty powyżej pasma opuściły loch (82 wyjścia z powodem `monkey_horse_complete_direct`).

### Added

- **Mapa w panelu ma prawdziwy teren pod spodem.** Rysowany z tego samego `server_attr`, po którym nawigują boty, a nie zrzucony z klienta: ląd, woda i blokady w trzech kolorach, 256×256, **20 KB na wszystkie sześć map**.
  - Pokrywa się ze znacznikami co do piksela, bo jedno i drugie liczone jest z tych samych granic mapy. Dzięki temu jest to tyle samo tło, co narzędzie diagnostyczne: jezioro na obrazku to jezioro, którego znaczniki nigdy nie przekroczą.
  - `tools/render_map_tiles.py` odtwarza kafle, gdy dojdzie nowa mapa.
- **Pasma filtra poziomów dopasowane do świata.** 1-5/6-10/11-15/16+ wrzucało prawie każdego bota do ostatniego kubełka, odkąd populacja sięga 37 poziomu. Teraz **1-15 / 16-25 / 26-35 / 36+**, gdzie 36+ to obsada Doliny Orków.

---

Pomysły gracza z `m2singleplayer.pl` (EXP, miejsce przebywania, umiejętności) panel ma już od dawna — jego strona to wersja 1.15.6. Jedyną rzeczą, której faktycznie brakowało, było tło mapy, i to zostało dodane.

---

## 1.23.10 — 2026-09-04

### Fixed

- **Dwa z dwunastu punktów łowieckich Doliny Orków leżały za wodą i nie dało się do nich dojść.** Zastąpione punktami wewnątrz obszaru, po którym boty faktycznie chodzą — wybranymi tak samo jak pozostałe: najgęstsze skupiska spawnów, przyciągnięte do prawdziwej współrzędnej z `regen.txt`.

### Mosty: boty ich nie przechodzą i nie powinny próbować

Dolina Orków to wysokie wyspy nad przepaściami z wodą na dnie, połączone mostami. Pytanie, czy boty przez nie przechodzą, było więc zasadne — i odpowiedź brzmi **nie**, ale konsekwencja jest odwrotna, niż mogłoby się wydawać.

Przeszukałem całą mapę pod kątem chodliwych pasm z wodą po obu stronach, czyli tego, jak most wygląda w `server_attr`. Na 3,16 mln chodliwych komórek znalazły się **dwa pasma po 16 komórek**, oba poza terenem botów. **Mosty tej mapy nie istnieją w danych kolizji serwera** — dno przepaści jest oznaczone jako woda, a pokład mostu nad nim nie został z niej wycięty.

Dlatego poluzowanie blokady wody **nie pomogłoby, tylko zaszkodziło**: bot nie wszedłby na most, tylko przeszedłby przez wodę na dnie przepaści. Blokada zostaje.

Co z tego wynika w praktyce:

- **Cały teren łowiecki botów to jeden lity ląd.** Sprawdzone wprost: wewnątrz tego obszaru nie ma ani jednej komórki o profilu mostu, więc **żadna trasa między punktami łowieckimi nie prowadzi przez most**.
- Odcinki wody odcinające resztę mapy mają **4 600–6 750 jednostek** — to przepaście, nie strumyki do przeskoczenia.
- **Mapa nigdy nic nie stawia na wodzie:** ani jeden z 532 punktów spawnu, ani jeden z 16 NPC.
- Silnik r40250 **w ogóle nie blokuje wody** — czyta `ATTR_WATER` tylko dla łowienia. Blokada jest naszą decyzją.

**Ograniczenie, wprost:** boty korzystają z około 30% Doliny Orków. Reszta leży za wodą, której nie przejdą, dopóki mosty nie zostaną opisane w danych kolizji.

---

## 1.23.9 — 2026-09-04

### Fixed

- **Dolina Orków była mapą, na którą bot mógł wejść, ale nie mógł na niej grać.** Boty lądowały w punkcie startowym imperium, a `map_n_threeway` to mapa graniczna trzech imperiów — **każdy róg jest odgrodzony murem**. Z tego miejsca bot sięgał **17 z 532 grup spawnu** i ani jednego z dwunastu punktów łowieckich.
  - Trzynaście botów siedziało tam na dokładnie wejściowym poziomie i nie awansowało, planując w kółko trasy, które nie mogły istnieć: **7812 z 8259** wpisów „unreachable" w jednej sesji pochodziło z tej jednej mapy.
  - Wejście i wyjście są teraz w największym spójnym obszarze mapy — **161 grup spawnu** i wszystkie punkty łowieckie. Oba to współrzędne z `regen.txt`, więc są chodliwe, i oba w tym samym obszarze: **do wyjścia bot idzie pieszo**, więc wyjście za murem zablokowałoby każdego, kto tam wszedł.
  - Migracja przenosi boty zostawione w starym rogu do terenu łowieckiego, zanim rdzeń gry je wczyta.
- **Wędrówka pyta, czy punkt jest osiągalny, zanim do niego pójdzie** — na mapach granicznych i w Małpiej Świątyni. Kosztuje to sprawdzenie spójnego obszaru, a oszczędza przeszukiwanie trasy, które i tak musi się nie udać. Bot po złej stronie muru poluje tam, gdzie stoi, zamiast cyklicznie próbować dwunastu niemożliwych celów.

### Added

- **`tools/analyse_map_reach.py`** — narzędzie, którym to zmierzono. Dekoduje `server_attr`, stosuje tę samą regułę blokowania co nawigacja botów, rozlewa się od zadanego punktu i mówi, jaka część tablicy spawnów jest po tej samej stronie murów. Pustynia dostaje z wejścia **1170 z 1172** — dlatego ta mapa zawsze działała, a tamta nigdy.

---

**Zmierzone na uruchomionym serwerze:** trasy nieosiągalne do Doliny Orków **7812 → 0**, w całym ostatnim oknie logu zostały **4 awarie od 2 botów**. Bot obecny na mapie stoi wewnątrz głównego terenu łowieckiego.

**Zamknięte zgłoszenia:** [#5](https://github.com/TieruYT/metin2-playerbots/issues/5) i [#7](https://github.com/TieruYT/metin2-playerbots/issues/7).

## 1.23.8 — 2026-09-04

### Changed

- **Podział kodu botów dokończony — wydanie bez zmian w zachowaniu.** `playerbot_manager.cpp` miał rano **12 527 linii**; ma **1 521**. Wszystko to przeniesienia, nic nie zostało przepisane.
  - Wydzielone w tym kroku: `playerbot_targeting.h` (wybór celu i rezerwowanie go przed setką innych botów), `playerbot_loot.h`, `playerbot_survival.h`, `playerbot_wandering.h`, `playerbot_status.h`.
  - Rdzeń celowania został **jednym plikiem**, choć ma 1266 linii: rezerwacja celu, licznik atakujących metin i decyzja o multi-pullu muszą widzieć ten sam obraz tego, kto z czym walczy. Rozbicie ich dałoby trzy pliki czytające trzy różne prawdy.
  - Sprawdzenie „czy gracz jest blisko" trafiło do statusu — to ono decyduje, że przy nikim nie ma po co nic nadawać.
  - W menedżerze została **rola menedżera**: kim bot jest, jego drużyna, drobne przeglądy, watchdog i sam takt. Takt zostaje tam celowo — jako jedyny musi widzieć wszystkie podsystemy.

---

**Weryfikacja:** kontrola `-m32` w gcc:13 po każdym cięciu — zero błędów, te same dwanaście ostrzeżeń przez cały czas, test jednostkowy przechodzi. Obraz zbudowany i uruchomiony: rejestr 1012 tożsamości, boty piją mikstury, ulepszają, zakładają sprzęt, rozdają punkty, wycofują się taktycznie i wspierają drużynę.

## 1.23.7 — 2026-09-04

### Changed

- **Kod botów podzielony na podsystemy — wydanie bez zmian w zachowaniu.** `playerbot_manager.cpp` miał rano **12 527 linii**; ma **4 001**. Nic nie zostało przepisane, wszystko to przeniesienia.

  | Plik | Co |
  |---|---|
  | `playerbot_navigation.h` | Gdzie bot może stanąć i czy dwa punkty się łączą |
  | `playerbot_world_memory.h` | Czego populacja nauczyła się o świecie |
  | `playerbot_movement.h` | Jazda trasą: koń, waypointy, portale, rejestr metinów |
  | `playerbot_gear.h` | Co bot nosi i dźwiga |
  | `playerbot_activities.h` | Koń i łowienie |
  | `playerbot_missions.h` | Biolog i polowanie na poziom, bez okna zadania |
  | `playerbot_skills.h` | Karta postaci: punkty, kolejność umiejętności, bufy |
  | `playerbot_combat.h` | Sama walka: pakiety ciosu i zaklęcia, umiejętności ataku |
  | `playerbot_economy.h` | Pieniądze i plecak: śmieci, handlarze, kowal, bonusy, stragany |
  | `playerbot_travel.h` | Gdzie bot powinien być i jak przechodzi między mapami |
  | `playerbot_town.h` | Wizyta w mieście od bramy do ostatniej sprawy |

  Lista `#include` na górze menedżera jest teraz **kolejnością zależności całego systemu**, czytaną z góry na dół. W jednej jednostce kompilacji i jednej anonimowej przestrzeni nazw kolejność definicji *jest* kolejnością zależności, więc plik, który idzie pierwszy, to ten, który nie woła niczego.

  W menedżerze została pętla walki (wybór celu, rezerwacja go przed innymi botami, atak, multi-pull, łup, drużyna, wędrówka), tekst statusu i sam takt.

---

**Weryfikacja:** kontrola `-m32` w gcc:13 po każdym cięciu — zero błędów, te same dwanaście ostrzeżeń przez cały czas, test jednostkowy przechodzi. Na koniec obraz zbudowany i uruchomiony: rejestr 1012 tożsamości, boty piją mikstury, ulepszają, kupują sprzęt, chodzą do kowala i handlarza, rozdają punkty.

## 1.23.6 — 2026-09-04

### Fixed

- **Rejestr po cichu odrzucał każdego bota od PID 1003 w górę.** `LPAD` w MySQL nie dopełnia, tylko **skraca**, gdy wartość jest dłuższa niż podana szerokość — więc `LPAD(1001,3,'0')` to `100`, czyli login zupełnie innego bota. Zapytanie rejestru porównywało z tym konto każdej postaci, przez co każdy bot powyżej PID 1002 nie przechodził warunku, którego nie mógł przejść. Bez żadnego błędu w logu.
  - Obsada nie mogła urosnąć powyżej tysiąca, **niezależnie od tego, ile postaci utworzyło ziarno**.
  - Zmierzone na żywym świecie z 1500 zasianymi botami: zapytanie zwracało **511**, po poprawce zwraca **1012**.

### Changed

- **Kanoniczna obsada powiększona do 1500** (PID 4..1503), a limit w launcherze razem z nią. Świat, który nosi boty ze starszego rozruchu, zachowuje je — ale zajmują one PID-y, których rejestr nigdy nie przyjmie, więc jedyny sposób, by dać takiemu światu więcej grających botów, to poszerzyć zakres kanoniczny poza nie.
- **Wydzielony `playerbot_movement.h`** (720 linii): trasy, wsiadanie na konia, przechodzenie waypointów, portale Małpiej Świątyni. Rejestr znanych metinów trafił tam razem z nimi — o tym, czy kamień warto zapamiętać, decyduje to, czy ktoś może do niego dojść, więc rozdzielenie ich znaczyłoby przekazywanie osiągalności z powrotem.
  - `playerbot_manager.cpp`: **8 388 linii** zamiast 12 527 z dzisiejszego rana.

---

**Zmierzone na działającym serwerze, krok po kroku:**

| | boty w grze |
|---|---|
| przed 1.23.5 | 180 |
| po 1.23.5 (ziarno wreszcie dociera) | 511 |
| po 1.23.6 (poprawka rejestru + obsada 1500) | **750** |

## 1.23.5 — 2026-09-04

### Fixed

- **Powiększona obsada botów nigdy do nikogo nie dotarła.** Kontener migracji montuje `linux-port/docker/mariadb/playerbot`, więc SQL, który faktycznie wykonuje, to **kopia** ziarna z overlaya — umieszczana tam przez `prepare-context.sh`, który wymaga czystego drzewa silnika i u gracza nie uruchamia się nigdy. Kopia, którą stosowały wszystkie instalacje, była **z 23 sierpnia**. Rejestr 1000 postaci z 1.23.2 i dzisiejsze dokładanie kont jechały w każdej paczce i nie zmieniały niczego.
  - Synchronizacja overlaya odświeża teraz również tę kopię — na tej samej zasadzie co kontekst budowania: overlay jest źródłem prawdy, a każda jego kopia musi być aktualna, zanim wystartuje to, co ją czyta.
  - **Sprawdzone na żywym świecie z 668 botami**: 668 zachowanych bez zmian, 332 utworzone, 1000 obecnych, a te 667, które miały postęp, nadal go mają. Druga migracja nie tworzy nic i nie zgłasza nic.
- **Nowy plik źródłowy silnika nie skompilowałby się u gracza.** `Makefile` w kontekście budowania jest łatany przez `prepare-context.sh`, więc zmiana na `$(wildcard playerbot_*.cpp)` naprawiła ścieżkę deweloperską i ominęła tę, która ma znaczenie. Naprawiane jest teraz to jedno miejsce przy synchronizacji — bez nadpisywania graczom całego `Makefile`.
- **Migracja przestała ostrzegać sama przed sobą.** PID zwykle wpada w kilka reguł pomijania naraz, a klucz główny zamieniał każde powtórzenie w ostrzeżenie o duplikacie — dwa tysiące linii przed operatorem, zasłaniających te dwie, które mówią, co migracja zrobiła.

### Changed

- **Kod botów podzielony na moduły.** `playerbot_manager.cpp` miał 12 527 linii, bo dodanie funkcji nic nie kosztowało, a dodanie **pliku** kosztowało pięć edycji w `prepare-context.sh` plus edycję łatki. Ta asymetria zniknęła: nic już nie wymienia tych plików z nazwy — skrypt odkrywa katalog, `Makefile` bierze wildcard, pakowarka rozwija wzorzec.
  - Usunięte **483 linie martwego kodu** — stara nawigacja (`CPlayerBotNavGrid`, `MovePlayerBotLegacy`) była osiągalna wyłącznie z siebie nawzajem.
  - Wydzielone `playerbot_navigation.h`, `playerbot_world_memory.h` i `playerbot_gear.h`. Menedżer ma **9 085 linii** zamiast 12 527.
  - To były czyste przeniesienia. **Sprawdzone na żywo**: 1000 botów chodzi, walczy, kupuje, ulepsza, handluje i łowi.

---

## 1.23.4 — 2026-09-04

### Added

- **Boty poprawiają bonusy na swoim sprzęcie.** Ekwipunek to tylko połowa siły postaci — druga połowa to cztery linie bonusów, a do tej pory nikt na nie nie patrzył. Bot na 30+ poziomie, stojąc u kowala, dokłada brakującą linię (`Wzmocnienie Przedmiotu`) albo przelosowuje słabe (`Zaczarowanie Przedmiotu`).
  - Oba przedmioty sprawdzone w `item_proto`, nie wzięte z notatek: **71084** to `USE_CHANGE_ATTRIBUTE`, **71085** to `USE_ADD_ATTRIBUTE`.
  - Silnik **odmawia** zmiany bonusów w założonym przedmiocie (`if (item2->IsEquipped()) return false`), więc bot zdejmuje część, losuje i zakłada z powrotem — dokładnie jak gracz.
  - Punktacja jest celowo zgrubna: ma odróżnić „warto zachować" od „losuj jeszcze raz", a nie odwzorować wzór na obrażenia. Broń ceni obrażenia od umiejętności, krytyki i przebicia; reszta sprzętu punkty życia i obronę.
  - Bot nie tknie ostatnich **120 tysięcy** yang — mikstury i sprzęt są ważniejsze — i wydaje najwyżej trzy kamienie na wizytę.

### Fixed

- **Bot potrafił przestać łowić na dobre.** Sesja wędkarska zwalnia bota z watchdoga bezczynności (stanie przy brzegu **jest** czynnością), więc bot, który nie mógł dojść nad wodę, stał w miejscu w całkowitej ciszy. Teraz:
  - punkt na brzegu jest **przyciągany do zweryfikowanej chodliwej komórki**, tak samo jak punkty usług w mieście;
  - gdy brzeg i tak jest nieosiągalny, bot **zarzuca tam, gdzie stoi** — `fishing()` w r40250 wymaga tylko niezablokowanego pola, wędki i przynęty, a wody nie sprawdza w ogóle (wylicza kierunek i go odrzuca);
  - co 15 sekund trafia do dziennika jedna linia `PLAYERBOT_FISHING: progress` z pozycją, celem, odległością i stanem sprzętu, więc następne zgłoszenie będzie można rozstrzygnąć jedną linią.
- **Panel nazywał co trzeci bonus „Bonus #63".** Tablica nazw pokrywała typy 1–25 i garść innych; brakowało między innymi odbicia ataku, odporności na omdlenie, magicznej wartości ataku i całej rodziny „silny przeciwko…". Dodane **31 brakujących** nazw, po polsku i angielsku.
- **Panel pokazywał cztery podstawowe statystyki jako procenty.** Siła, Zręczność, Inteligencja i Energia Życiowa to liczby, nie procenty — podobnie jak magiczna wartość ataku i obrony czy wytrzymałość. Rozróżnienie ma teraz własną listę zamiast testu na cztery typy.

---

## 1.23.3 — 2026-09-04

### Fixed

- **Serwer nie budował się po aktualizacji — to naprawiamy w pierwszej kolejności.** Zgłosili to `Archded` (build kończył się na `playerbot_types.h: No such file or directory`) i `Nagash` (`class 'CPlayerBotManager' does not have any field named 'm_bRegistryLoaded'`). Obie awarie miały **jedną przyczynę**: aktualizacja wysyłała nowy plik bota do kontekstu budowania, ale **bez jego własnych nagłówków**. Kompilator widział wtedy nowy kod obok nagłówka z poprzedniego wydania — albo bez nagłówka w ogóle.
  - Winne było założenie, że kontekst budowania utrzymuje `prepare-context.sh`. Ten skrypt wymaga czystego drzewa silnika, którego paczka **celowo nie zawiera**, więc u gracza nie uruchamiał się nigdy.
  - Teraz launcher i `start-server.ps1` **kopiują cały katalog źródeł bota** do kontekstu przed każdym budowaniem, więc kolejny nowy plik nie może się już zgubić. Dodatkowo pakowarka aktualizacji **odmawia zbudowania paczki**, w której źródło i jego kopia się rozjeżdżają.
  - `Nagash` podejrzewał, że zepsuła to jego zmiana nazw botów. Tak nie było — nazwy nie miały z tym nic wspólnego.
- **Sklepy botów nie były zamykane; nazwa stragana zostawała nad głową.** Zgłosił `Nagash`. Straganem zarządza silnik, a termin jego zamknięcia — kod bota, i zamykanie wykonywało się **za** watchdogiem bezczynności oraz ratunkami nawigacji. Każdy z nich przerywa takt, więc handlujący bot potrafił nigdy nie dojść do własnego kodu zamykania — a ratunek nawigacji mógł go **przenieść z rynku razem z wywieszonym szyldem**. Zamykanie stragana wykonuje się teraz **przed wszystkim innym**, a dodatkowo:
  - straganowi bez terminu zamknięcia termin jest **dopisywany**, więc żadna ścieżka nie zostawi go otwartego na zawsze;
  - bot, który zginął albo znalazł się poza rynkiem, zamyka stragan natychmiast;
  - stanie przy straganie **liczy się jako aktywność**, więc watchdog nie zgłasza już błędu co 90 sekund dla każdego handlarza.
- **Stragany stały zbyt długo, by ktokolwiek zobaczył ich zamknięcie.** Czas otwarcia zmieniony z 20–60 minut na **10–25 minut**.
- **Świeża instalacja z obsadą 1000 botów przerwałaby się na ziarnie.** Końcowa asercja porównywała wynik z liczbą **350** wpisaną na sztywno — przy rejestrze 1000 pozycji zgłaszała błąd przy **każdym** udanym zasianiu. Teraz porównuje z rzeczywistym rozmiarem rejestru.
- **Czytelny komunikat o limicie GitHuba.** Kilka kliknięć „Sprawdź aktualizacje" pod rząd wyczerpuje anonimowy limit zapytań, a launcher pokazywał wtedy tylko „Operacja nie powiodła się". Teraz mówi wprost, że to limit po stronie GitHuba, że instalacja jest sprawna i że wystarczy poczekać.

### Changed

- **Baza sama dokłada brakujące postacie botów.** Poprosił o to `Gacek`. Do tej pory **jedna** zmieniona nazwa bota unieważniała całe ziarno: świat zostawał na tylu botach, ile akurat miał, a suwak w launcherze obiecywał więcej, niż baza mogła dostarczyć. Teraz postać, która nie należy do ziarna, jest po prostu **pomijana** — a brakujące PID-y powstają normalnie.
  - **Żaden istniejący wiersz nie jest zmieniany ani usuwany.** Twoje postacie, przezwiska i postęp zostają nietknięte; dokładane są wyłącznie te, których w bazie nie ma.
  - Migracja wypisuje teraz, ile postaci zachowała i ile utworzyła.
- **Launcher pokazuje wersje na dole okna:** `Aktualna wersja` i `Najnowsza wersja`. Zielono, gdy masz najnowszą. Manifest czytany jest **raz na sesję**, żeby nie zużywać limitu GitHuba.

---

## 1.23.2 — 2026-09-04

### Changed

- **Suwak liczby botów sięga teraz 1000, a nie 668 — i ta liczba wreszcie coś znaczy.** Sedno problemu nie było w suwaku: spawnować mogą się **wyłącznie boty z rejestru nasion**, a ten miał **350 pozycji**. Dlatego gracz przesuwał suwak wyżej i dostawał 350. Rejestr obejmuje teraz 1000 postaci (PID 4..1003).
  - **Uwaga: istniejący świat zachowuje swoją obsadę.** Migracja celowo nie nadpisuje świata, który ma już własne boty — wypisuje ostrzeżenie i pomija nasiona. Nowy limit dostaną **świeże instalacje**; przeniesienie istniejącego świata na większą obsadę to osobna, świadoma operacja na bazie.

### Fixed

- **Bot wysyłał się na ryby, mimo że nie mógł unieść wędki.** Wędkarzem mógł zostać bot od 10 poziomu, a wędka wymaga 30 — więc bot kupował sprzęt, którego nigdy nie założy, i próbował w kółko. Zgłosił to `OskarPWA`, widząc bota na 13 poziomie zablokowanego przy Rybaku. Teraz o tym, kto może łowić, decyduje **wymagany poziom samej wędki**, odczytany z danych przedmiotu — więc zmiana wędki nie rozjedzie się z kodem.
- **Łowienie w ogóle nie mogło się odbyć.** Rzeka jest w Joan, a każdy bot dość wysoki, by unieść wędkę, dawno stamtąd wyszedł — więc warunek „łowimy tylko w M1" nie mógł być nigdy spełniony. Wyprawa na ryby jest teraz **prawdziwym celem podróży**: bot wraca do Joan, łowi i dopiero potem wraca do polowania.
- **Sesja łowienia ma twardy limit czasu.** Bot, który nie dotrze nad wodę, kończy sesję z wpisem w dzienniku, zamiast w nieskończoność chodzić tą samą nieudaną trasą.

---

## 1.23.1 — 2026-09-03

### Fixed

- **Boty, które utknęły bez sektora, wracają do gry.** Postać bez sektora nie może się ruszyć **w ogóle**, a kod tylko zapisywał błąd i próbował ponownie w następnym takcie. W logach z jednego dnia dało to **35 tysięcy takich wpisów od 45 botów**, które nie zrobiły już ani kroku, plus 7900 bezskutecznych resetów watchdoga. Teraz taki bot jest przenoszony na punkt wejścia swojej mapy.
- **Boty zapisane na mapie, której serwer nie prowadzi, nigdy się nie pojawiały.** Wczytanie postaci pytało o pozycję, nie dostawało odpowiedzi i się poddawało — te same dwa boty przepadały przy każdym z 17 startów w ciągu dnia, bez możliwości odzyskania, bo pętla AI widzi tylko boty, które się pojawiły. Migracja przy starcie przenosi je teraz do Bokjung. **U mnie odzyskała 4 boty.**
- **Koniec zalewania dziennika przy starcie.** Zabezpieczenie przed przejęciem cudzego konta zapisywało błąd dla każdego niezarejestrowanego numeru — 170 linii przy każdym uruchomieniu za coś, co działa dokładnie tak, jak ma działać. Teraz jest to jedna zbiorcza linia.
- **Paczka diagnostyczna zbierana przy wyłączonym Dockerze** była oznaczana jako udana, choć zamiast logów kontenerów zawierała same błędy połączenia. Teraz na górze pliku jest wyraźne **PACZKA NIEPEŁNA** z informacją, co zrobić.

---

## 1.23.0 — 2026-09-03

### Added

- **Boty prowadzą stragany w Bokjung.** Stała dziesiąta część botów po załatwieniu spraw w mieście idzie na rynek, zsiada z konia i wystawia jeden przedmiot na 20–60 minut: materiał albo naprawdę zbędną broń czy zbroję, w cenie liczonej z kursu NPC. Zapasy, noszony sprzęt i rzeczy, których gra zabrania sprzedawać, nie trafiają nigdy. **Możesz u nich normalnie kupować.**
- **Walka z siodła.** Koń bojowy (11+ poziom) jedzie teraz do walki, zamiast zostawać na podejściu. Metiny bije z siodła każdy, kto takiego konia ma; wojownicy i sury tłuką konno także zwykłe spoty. Łucznicy i zwykłe konie nadal walczą pieszo. Blokadą nie był dystans zsiadania, tylko podejście do walki wołające ruch bez zgody na konia — bot zsiadał za każdym razem.
- **Wędkowanie.** Część botów w M1 kupuje wędkę u Rybaka i łowi na brzegu poniżej niego. Zrobione pod to, co silnik faktycznie robi, a nie pod opis: przynęta siedzi w gnieździe 2 wędki, branie przychodzi po 10–40 s i daje 6 sekund okna, a szczyt wypada około 3 s po braniu — więc bot czeka na właściwy moment, zamiast szarpać. Połów jest patroszony, a małże otwierane, co wprowadza do gospodarki **perły**. Pas brzegu i kierunek odczytane z `server_attr` mapy, nie zgadnięte.
- **Ogłoszenia u kowala na Wołaj.** Udane ulepszenie na +7 i wyżej ma szansę trafić na czat, najwyżej raz na trzy minuty w skali świata. **Przy zaatakowaniu, w PvP i po zabiciu boty milczą.**
- **Pamięć ras map.** Populacja zapamiętuje, z czego składa się każda mapa, i waży tym bonusy rasowe — „silny przeciw orkom" liczy się bardziej tam, gdzie orki naprawdę są. Mapa musi mieć 200 obserwacji i wyraźną większość, zanim cokolwiek zostanie uznane za jej rasę.

### Fixed

- **Prywatnego sklepu nie mógł otworzyć nikt w zbroi — także Ty.** `OpenMyShop` zaczynał się od `GetPart(PART_MAIN) > 2`, a silnik trzyma w `PART_MAIN` numer noszonej zbroi, więc warunek odrzucał każdą ubraną postać. Miał chronić przed otwieraniem sklepu w transformacji i teraz pyta o to wprost. Zmiana idzie jako osobna łatka rdzenia.
- **Bot trzymający cel nie sprawdzał już podróży** ([#10](https://github.com/TieruYT/metin2-playerbots/issues/10)), przez co gęste spoty potrafiły go uwięzić.
- **Loch Małp nie pytał o mikstury** ([#11](https://github.com/TieruYT/metin2-playerbots/issues/11)) — bot bez mikstur zostawał i ginął w kółko. Zgłoszone razem z poprawką przez `sentydeploy`.
- **Paczka aktualizacji nie zawierała trzech plików**, bez których przebudowa u gracza kończy się błędem kompilacji: `playerbot_world_rules.h` (zyskał nowe pole), nowy `playerbot_types.h` oraz `prepare-context.sh`, który jako jedyny kopiuje pliki overlaya do budowania.

---

## 1.22.4 — 2026-09-03

### Changed

- **Boty idą po mikstury dopiero wtedy, gdy są na wykończeniu.** Poprzednia wersja wysyłała je do handlarki już przy połowie pasa, co kosztowało dobry spot za zakup, którego nie potrzebowały. Wyprawa po zakupy to teraz próg **150 czerwonych / 100 niebieskich**. Uzupełnianie **do pełna** (800/600) zostaje bez zmian, ale dzieje się przy okazji — gdy bot i tak stoi u handlarki, dokupienie nic nie kosztuje.

---

## 1.22.3 — 2026-09-03

### Fixed

- **Boty powyżej 35 poziomu nie mogły wyjść z Joan i biły tam wilki.** Zgłoszone przez `sentydeploy` w [#9](https://github.com/TieruYT/metin2-playerbots/issues/9) razem z pomiarem na 350 botach: **z 276 postaci powyżej 35 poziomu aż 243 tkwiły w Joan**, goniąc Dzikie Psy i Niebieskie Wilki. Bramka wyjścia z miasta sprawdzała tylko przynależność do grupy expiącej w Bokjung, która kończy się na 35 poziomie — więc bot 36+ odbijał się od niej przy każdym takcie i nigdy nie docierał do trasy na nowe mapy. To właśnie te „boty biją psy na 30 poziomie", które wracały na Discordzie. Przechodzi teraz każdy, kto ma dokąd pójść.
- **Pętla Joan ↔ Bokjung powyżej sufitu.** Bot, którego Joan wypuściła, docierał do Bokjung, a tam odsyłano go z powrotem, bo nie należał do tamtejszej grupy. Powyżej 35 poziomu nie ma już powodu wracać.

### Changed

- **Boty noszą znacznie większy zapas mikstur: 800 czerwonych i 600 niebieskich**, jeśli mają na to yang (wcześniej 300 i 80). Uzupełniają je po zejściu poniżej połowy, a nie dopiero przy pustym pasie, i nigdy nie wydają więcej niż połowy portfela. Limit odsprzedaży nadmiaru podniesiony razem z zakupem — inaczej boty od razu sprzedałyby to, co kupiły.

---

## 1.22.2 — 2026-09-02

### Fixed

- **Boty kupowały hełm innej klasy i nie mogły go założyć.** Zgłoszone przez `sentydeploy` w [#8](https://github.com/TieruYT/metin2-playerbots/issues/8) — bardzo dobra diagnoza. Rodziny hełmów dzieli 140 numerów, a pętla wyboru sięgała dokładnie `baza + 140`, czyli startowego hełmu sąsiedniej klasy. Ponieważ wygrywało „ostatnie trafienie", a startowy hełm wymaga 0 poziomu, zawsze nadpisywał poprawny wybór. Wojownik kupował hełm Ninji, Sura hełm Szamana — i gra odmawiała założenia. Widać to było w danych: Szaman, którego rodzina jest ostatnia w łańcuchu, miał hełm w 100% przypadków, pozostałe klasy poniżej 50%. Wybór idzie teraz według **najwyższego wymaganego poziomu**, więc przedmiot startowy obcej klasy nigdy nie przebije właściwego. Ta sama poprawka objęła wszystkie pięć list progresji (broń, zbroja, tarcza, hełm, buty).

- **Przerwana aktualizacja nie zostawia już serwera w martwym punkcie.** Gdy Docker nie dokończył budowania, nowe pliki (w tym `VERSION`) były już na dysku, więc launcher mówił „masz najnowszą wersję" i nigdy nie ponawiał budowania — a „GRAJ" startowało stare obrazy. **Właśnie dlatego część graczy nie widziała nowych map na stronie mimo aktualizacji.** Launcher zapisuje teraz znacznik nieukończonej przebudowy: dopóki istnieje, wersja liczy się jako nieznana, a kliknięcie **GRAJ** samo dokańcza budowanie. Nic nie trzeba robić ręcznie.

### Changed

- **Nowe pasma poziomów dla map.** Bokjung do 29, **Pustynia Yongbi 30–35**, **Dolina Orków od 36**. Zwykłe moby w Dolinie mają 18–25 poziom, ale jej **metiny mają 45, 48 i 50** — a metina opłaca się rozbijać dopiero od `poziom_metina − 9`. Dolina zaczyna się więc realnie opłacać dopiero od 36 poziomu i tam trafiła, mimo słabych mobów.
- **Większy zapas niebieskich mikstur dla klas walczących wręcz.** Wojownik i Ninja uzupełniają je teraz do 20 sztuk zamiast 10 — umiejętności zużywają SP bez przerwy. Brak niebieskich nadal nie blokuje podróży, bo to właśnie zamykało boty w mieście.

---

## 1.22.1 — 2026-09-02

### Fixed

- **Aktualizacja z launchera nie wywala już serwera przy dużym świecie.** Migracja bazy czekała na nią 5 minut i się poddawała, a Docker traktuje to jako nieudany start całego serwera — stąd „Docker nie zbudował serwera", mimo że uruchomienie ręczne minutę później działało. Świat, który nie został czysto zamknięty, potrafi odtwarzać się dłużej niż 5 minut, więc limit to teraz 30 minut, a skrypt na bieżąco pisze, że czeka. **To samo naprawia panel www, który u części graczy nie pokazywał nowych map** — przerwana aktualizacja nie zdążyła przebudować strony.
- **Migracja pokazuje wreszcie błąd bazy, zamiast go połykać.** Odrzucone logowanie wyglądało dokładnie tak samo jak wolny import. Teraz wypisuje powód, a przy „Access denied" wprost odsyła do przycisku „NAPRAW DOSTĘP DO BAZY".
- **Boty przestały odbijać się od nowych map.** Przyjeżdżały i wracały po kilku sekundach — 271 przyjazdów na Pustynię dawało 269 powrotów, więc obie mapy wyglądały na puste, bo każdy bot był akurat w drodze. Złożyły się na to trzy rzeczy: brak niebieskich mikstur uznawany za sytuację awaryjną **także u wojownika i ninja** (dotyczyło 210 z 442 postaci, które ich nie używają), sprawdzanie ekwipunku zanim zdążył się wczytać po zmianie mapy, oraz brak minimalnego czasu pobytu. Bot zostaje teraz co najmniej 2 minuty, chyba że naprawdę nie może walczyć.
- **Bot, który trafi na nieobsługiwaną mapę, wraca do Bokjung.** Na nowych mapach stoją prawdziwe NPC teleportujące; wejście w ich zasięg przenosiło postać tam, gdzie AI nie ma żadnego planu, i bot zostawał tam na zawsze.

### Changed

- Ostrzeżenie Dockera o wolumenie `db-data` nie pojawia się już w oknie launchera. Jest nieszkodliwe, ale słowo „warning" obok bazy skłaniało graczy do `down -v` — jedynej komendy, która naprawdę kasuje świat. W dzienniku sesji zostaje.

---

## 1.22.0 — 2026-09-02

### Added

- **Boty wychodzą wreszcie poza Bokjung — na Dolinę Orków i Pustynię Yongbi.** Progresja kończyła się na M2, którego moby przestają się opłacać koło 27 poziomu, więc bot, który je przerósł, był odsyłany do Joan bić wilki na 3 poziomie. Dolina Orków (moby 18–25) obsługuje poziomy 20–27, Pustynia (moby 26–30) poziomy 28–33. Boty podróżują przez Teleportera, którego każda wioska ma naprawdę, i wracają bramką kilka kroków od miejsca, w którym się pojawiły.
- **Obie mapy na stronie.** Selektor na `/map` ma teraz sześć pozycji, więc widać boty także na nowych mapach. Teleport do bota działa tam bez zmian.
- **Mapy cieplne.** Nowy przełącznik pokazuje, **gdzie boty giną** i **gdzie rozbijają metiny** — na podstawie zdarzeń, które serwer i tak zapisuje. Wielkość plamy skaluje się pierwiastkiem z liczby zdarzeń, więc jedno gorące miejsce nie zalewa całej mapy.

### Fixed

- **Brakujący hełm nie przykuwa już bota do jednej mapy.** Brak dowolnej części EQ liczył się jako krytyczna potrzeba miasta, a ta blokowała podróż bezterminowo. Bot zawsze chciał na zakupy, więc nigdy nie wolno mu było wyjść — i bił wilki na 3 poziomie mając 27 poziom i ponad milion yang. Teraz blokują tylko braki, które faktycznie uniemożliwiają grę (broń, zbroja, mikstury, strzały, pełny plecak); reszta dostaje jedną wizytę w mieście i jeśli miasto nie ma czym pomóc, bot rusza dalej.
- **Poprawione przyciski teleportacji w panelu.** „Pustynia" i „Ognista Ziemia" wskazywały współrzędne spoza świata gry, więc nigdy nie działały. Wszystkie miejsca celują teraz w punkt odrodzenia Chunjo danej mapy; doszły też Bokjung, Dolina Orków, Pustynia i Góra Sohan.

### Changed

- **Osobowość bota wpływa teraz na to, gdzie gra**, a nie tylko na to, jak ryzykownie ulepsza. Wędrowiec wyrusza na dalekie mapy 7 razy na 8 i zostaje tam dwa razy dłużej, ostrożny kolekcjoner 2 na 8 i wraca szybciej. Około 38% każdego pasma zostaje w Bokjung, żeby miasto, bestie i pula na drużyny nie pustoszały.
- Mapa 64 przeniesiona na rdzeń `game1`. Bot serwerowy nie ma klienta, który przełączyłby się między rdzeniami, więc cała jego trasa musi być na jednym — mapa 303 poszła w drugą stronę dla zachowania balansu.

---

## 1.21.2 — 2026-09-02

### Fixed

- **Launcher prosi o ponowne uruchomienie po aktualizacji.** Aktualizacja podmienia pliki samego launchera, ale okno, które masz otwarte, wczytało stary kod przy starcie — więc nowe przyciski się nie pojawiały i wyglądało to, jakby aktualizacja nie weszła (choć na dysku była). Teraz launcher wykrywa, że podmienił własne pliki, i pyta: „Uruchomić ponownie teraz?".
- **„IMPORTUJ BAZĘ" przy wyłączonym Dockerze nie kłamie już, że nie ma czego importować.** Wcześniej lista baz wychodziła pusta i komunikat brzmiał jak utrata danych. Teraz launcher sprawdza silnik i mówi wprost: uruchom Docker i spróbuj ponownie — dane są całe. To samo dotyczy „NAPRAW DOSTĘP DO BAZY".

### Added

- **Data utworzenia przy każdej bazie na liście importu.** Nazwy instalacji to nieczytelne skróty (`m2pb-34c3e45f`), więc lista pokazuje teraz `m2pb-34c3e45f   (utworzona 2026-08-31 23:51)` — widać, która jest która. Działa tak samo w launcherze graficznym i tekstowym.

---

## 1.21.1 — 2026-09-02

### Added

- **„ZBIERZ / WYŚLIJ LOGI" wysyła paczkę prosto na Discorda projektu.** Gdy kanał zgłoszeń jest włączony, jeden klik pakuje logi i wrzuca je na serwer autora — bez szukania folderu i przeciągania pliku. Paczka nadal ma wycięte hasła, a wiadomość nie może nikogo oznaczyć (żadnych `@everyone`).
- Gdy kanał jest wyłączony albo nie ma internetu, launcher robi to co dotąd: zapisuje ZIP, otwiera jego folder — a teraz dodatkowo otwiera zaproszenie na Discorda, żeby było wiadomo, gdzie go wrzucić.

### Changed

- **Adres kanału zgłoszeń jest pobierany z manifestu aktualizacji**, a nie wbudowany w launcher. Dzięki temu można go włączyć, zmienić albo unieważnić edycją jednego pliku na GitHubie — bez wydawania nowej wersji i bez ponownej instalacji u graczy. Własne ustawienie w `.m2launcher.json` nadal ma pierwszeństwo.
- Launcher rozpoznaje pomyłkę „zaproszenie zamiast webhooka" (`discord.gg/...`) i mówi wprost, jak wygląda poprawny adres, zamiast zgłaszać błąd HTTP.
- Paczka większa niż 10 MB jest odrzucana **przed** wysyłką, z informacją ile waży — wcześniej Discord odrzucał ją dopiero po przesłaniu całości.

---

## 1.21.0 — 2026-09-02

### Fixed

- **Import nie potrafi już zniszczyć bazy.** Jeśli baza tej instalacji jeszcze nie istniała, import montował nieistniejący wolumen — Docker tworzył go pustego, a MariaDB inicjalizowała bazę **bez hasła i bez schematów gry**. Ponieważ wolumen przestawał być pusty, właściwa inicjalizacja nigdy się już nie uruchamiała i instalacja zostawała trwale zepsuta (trzeba było kasować wolumeny). Teraz launcher odmawia i mówi wprost: najpierw uruchom serwer („GRAJ"), dopiero potem importuj.
- **Czytelna podpowiedź przy błędzie startu.** Gdy `playerbot-migrate` nie może zalogować się do bazy, launcher pokazuje konkretną instrukcję: kliknij „NAPRAW DOSTĘP DO BAZY", zamiast surowego błędu Dockera.

### Added

- **Suwak liczby botów (0–668).** Zamiast wpisywania liczby — suwak z podglądem wartości. Efektywny limit to liczba botów w Twoim świecie (kanoniczna paczka ma 350).
- **Widoczny postęp podczas uruchamiania.** Log w launcherze pokazuje teraz przebieg **na żywo**, a pasek postępu i status podają upływający czas oraz etap budowy (np. `game deps 4/6 (67%)`). Koniec z ciszą przez kilka minut i pytaniem „czy to się zawiesiło?". Przy pierwszym budowaniu launcher wprost uprzedza, że potrwa to kilkanaście–kilkadziesiąt minut.

### Changed

- **Jeden przycisk aktualizacji.** Zamiast osobnych „SPRAWDŹ" i „ZAINSTALUJ" jest teraz samo **SPRAWDŹ AKTUALIZACJE**: launcher sprawdza kanał i — jeśli faktycznie jest nowsza wersja — pyta „Znaleziono nową wersję. Zainstalować teraz?" (TAK/NIE). Gdy nic nowego nie ma, mówi to wprost, zamiast cokolwiek instalować.
- **Szybsze zgłaszanie problemów.** Przycisk „ZBIERZ / WYŚLIJ LOGI" potrafi od razu wysłać paczkę logów do autora, jeśli w konfiguracji ustawiono kanał pomocy; w przeciwnym razie zapisuje ZIP i otwiera folder do załączenia na Discordzie. Hasła są z logów usuwane.

## 1.20.0 — 2026-09-02

### Fixed

- **Import świata już nie blokuje startu serwera.** Po „IMPORTUJ BAZĘ" migrator botów potrafił nie uwierzytelnić się w bazie (`playerbot-migrate` kończył się błędem), przez co gra i panel nie wstawały. Import zamyka teraz bazę pomocniczą łagodnie (bez wymuszania odzysku InnoDB) i po podmianie świata odtwarza techniczne konto bazy wraz z uprawnieniami. Postacie, przedmioty i boty pozostają nietknięte.
- **Nowy przycisk „NAPRAW DOSTĘP DO BAZY".** Jednym kliknięciem odtwarza techniczne konto bazy dla osób, które zaimportowały świat wcześniejszą wersją i zostały z serwerem, który nie startuje. Nie zmienia postaci ani botów.

## 1.19.0 — 2026-09-01

### Added

- **Dostęp do bazy z Navicat / HeidiSQL / DBeaver.** Baza jest wystawiona na `127.0.0.1:3306` (tylko lokalnie). Loguj się jako `root` / `local-playerbots-root` albo `metin2` / `local-playerbots-game`, aby edytować itemy, NPC i questy.
- **Ustawianie liczby grających botów (0–350)** w launcherze — przycisk „LICZBA BOTÓW".
- **Import świata z innej instalacji** („IMPORTUJ BAZĘ") — kopiuje postacie/poziomy/ekwipunek z innego wolumenu Docker na tym komputerze, z kopią zapasową i bez ruszania źródła. Pokazuje datę utworzenia świata i ostatniej gry.

### Fixed

- **Koniec fałszywego „Błąd: Start (kod )".** Launcher nie myli już postępu Dockera na stderr (ani nieodczytanego kodu wyjścia w GUI) z awarią — udany start pokazuje „Gotowe".
- **Mapa botów po zmianie nazwy.** Panel rozpoznaje boty po koncie `playerbot_`, więc bot ze zmienioną nazwą znów jest widoczny na mapie.
- **Bezpieczeństwo.** Zwykła postać gracza nie może już zostać przejęta jako bot.
- Poprawne wykrywanie i przejmowanie istniejących instalacji Docker przy pierwszym uruchomieniu z nowego folderu.

## 1.17.0 — 2026-08-25

### Added

- **Autonomous Chunjo multi-map progression.** Bots now travel between Joan (M1), Bokjung (M2), Waryong (M3) and the Easy Monkey Dungeon through the real portals and local dungeon teleports. M1 remains the natural early zone, most level 20–35 characters move into M2, and a suitably equipped cohort visits M3.
- **A real Horse Medal journey.** Eligible bots enter the Easy Monkey Dungeon, navigate its disconnected rooms through the native GOTO portal graph, pick up actual Medal drops and deliver them to a Stable Boy. The M2 Stable Boy is used after a dungeon trip, avoiding the old M2 → M1 detour. Different bots deliberately farm a stock of one to three medals before leaving, with a bounded visit time.
- **Mounted travel.** Bots with a horse mount for long journeys to merchants, the Blacksmith, the Biologist and world portals, then dismount near the destination and before ordinary combat. Combat-horse fighting remains a later milestone.
- **M3 equipment progression.** Infected animals can drop the class-specific level-30 weapon families and the level-21 Pentagon Shield through an additive serverfiles overlay. Bots value positive average-damage weapons especially highly.
- **Operational safety tools.** Added a verified compressed MariaDB backup helper and a read-only horse-journey diagnostic report.
- **A bilingual live world panel.** `/map` now supports Polish and English throughout, filters M1/M2/M3/Monkey Dungeon positions, and localises classes, professions, skills, hunting missions, Biologist stages and item names from the stock Polish locale table.

### Changed

- Loot remains visible for 1.0–1.8 seconds and is picked up one stack at a time instead of disappearing in the kill tick. Bots finish an active pull before starting the loot sweep.
- Combat target selection now prioritises the remaining monsters already attacking the bot or its party, so a character does not abandon a half-finished group for a fresh target.
- Playerbot combat ignores both attackers and targets inside `ATTR_BANPK` safe zones, preventing endless attacks against invulnerable monsters near teleporters.
- Shields are now treated as core progression gear: bots buy a Battle Shield when missing one, equip better shields and include them in Blacksmith refinement decisions.
- Skill development is no longer identical within a class. Mental Warriors rotate between Strong Body, Bash, Spirit Strike and Stump priorities; Dragon Shamans alternate Dragon's Aid and Dragon Roar openings. Dagger Ninjas learn Stealth but do not waste PvE actions casting it.
- Long-distance navigation can retain its mounted state across incremental route updates. Monkey Dungeon routing blocks immediate reverse-portal loops.
- The Playerbot autospawn safety ceiling was raised from 350 to 1000 while the reproducible bundled seed remains 350 bots.
- Docker-published auth, game and panel ports accept the explicit `M2_HOST_BIND_ADDRESS` setting.

### Fixed

- Corrected the Waryong arrival point to the walkable `Town.txt` location. The previous generic teleporter coordinates landed at the unwalkable north-west border without a sectree.
- Bots carrying a Horse Medal in M2 no longer return to M1 before looking for a Stable Boy.
- Bots no longer instantly clear freshly spawned Metin loot or leave it behind because town-service logic ran first.
- Horse travel no longer repeatedly dismounts and remounts when a lightweight AI update continues an existing route.

### Verification

- Rebuilt the full r40250 game image and the panel image successfully.
- Verified 51 live bots moving on valid Waryong coordinates after deployment, with no recurrence of the old arrival coordinate or missing-sectree error.
- Verified both Polish and English panel views, map filters and localised equipment/skill details against a live 668-bot development world.

---

## 1.16.0 — 2026-08-24

### Changed

- **The project is now installable independently of the retired upstream repository.** Installer, updater, panel metadata, and image labels point at `TieruYT/metin2-playerbots`.
- **Native-client-only installation.** The withdrawn upstream WebClient is not fetched, published, or started. Legacy WebClient flags remain accepted only so old saved commands do not fail.
- **Bring your own files (BYOF).** No third-party r40250 server/client mirror is built in. Supply a local server archive/reference directory and, optionally, a native client archive you are authorised to use. Windows adds `-ClientArchive` and `-NoClient`.
- Added an explicit provenance and attribution document, retained upstream Git history, and clarified the licensing boundary for all game files.

### Fixed

- Corrected Docker Compose host/container port interpolation so a fresh local install can bind the panel and game ports without producing an invalid four-part port mapping.
- Verified the complete local archive path against `Reference_Server.zip`: checksum, r40250 baseline, extraction, 30 patched files, and staging all pass without fuzz or rejects.

---

## 1.15.6 — 2026-08-14

### Fixed

- **Fixed Issue with Admin Panel**

---

---

## 1.15.5 — 2026-08-14

### Added

- **The panel points at the community's Discord.** A quiet line in the footer of every page, and a proper card for anyone signed in to their game account, saying what is actually there: what changed in the last update, when the server is down for maintenance, and people who answer a question faster than you can search for it — and that a bug reported there is the quickest way to get it fixed. In all three languages the panel speaks.

- The address is **part of the software, not a setting.** It is written into the code rather than read from a config file, deliberately: it is where this project posts its news, so an install cannot quietly drift to a different address and leave its players pointed at nothing. An operator running their own community changes that one line, which is a change to the software and looks like one.

---

## 1.15.4 — 2026-08-14

### Fixed

- **Updating a server could leave it unable to start.** The scripts that start and supervise the game cores are installed into the images with `chmod +x`, and that cannot repair the one thing that was wrong with them. A file staged as "executable by everyone but readable only by its owner" already has the execute bit for everybody, so `+x` changes nothing — and the server does not run as the owner. A compiled program would still have run; a shell script cannot, because the shell has to *read* it. The result was a game container restarting in a loop, once a minute, on `Permission denied`, with every other container healthy and the cause nowhere near the message. The four images that install scripts now set an absolute mode instead, the way the bridge image always did — which is exactly why the bridge was the one part that never broke.

- **The updater could not apply any change to the game's own code.** Every customisation this project makes to the server — the Custom Experience, High Risk mode, the storeroom pages — is a Python script, and the updater image did not contain Python. So an update that carried one of them stopped with `FATAL: python3 is needed`, refused to go further, and left the server on its old version. It never showed up during a first install, because that runs on the host, where Python is present. The updater image now carries it.

### Note for anyone running a server

Both of these are in the images, so they take effect the next time the images are rebuilt — which is what an update does anyway. If your server is currently in the restart loop described above, the update that fixes it is the same update that was failing; rebuild the images once and it clears.

---

## 1.15.3 — 2026-08-14

### Added

- **The storeroom at the Storekeeper has three pages.** It opened with one page — 45 slots — and the only way the game ever gave you more was a premium account or an item-mall chest expander, neither of which exists on a server that sells nothing, so the second and third pages were unreachable by design. Every account now gets all three, 135 slots, the moment the cores are rebuilt. Nothing is stored per account and nothing has to be bought, claimed or unlocked. Three is also the most this game can hold: the chest is exactly 135 slots wide internally, and the build refuses to go past it rather than quietly corrupting itself. Nothing you have stored moves and nothing is lost — the extra pages are added after the slots you already have, and every client already draws as many page tabs as the server tells it to, so there is no client update to install.

- **The bonus drops off metins and bosses can be dropped, handed to another player and put in a private shop.** Every item in that drop group — Blessing Scroll, Bravery Cape, Exorcism Scroll, Concentrated Reading, the two bonus scrolls, the Experience Ring and the Thief's Gloves — shipped locked to the character who found it: no dropping it, no handing it over, no shop. All three locks are now off. Selling them to an NPC is still refused, deliberately: it is the one mistake you cannot undo.

- **Exorcism Scrolls and Concentrated Reading stack.** Both rows already claimed to be stackable and were vetoed by a second flag on the same row, so a handful of them took a handful of inventory slots. Using one out of a stack spends one — the branch that consumes them already counted down instead of deleting the item.

- **Experience Rings and Thief's Gloves stack, and only while they are unused.** A ring you have worn never merges back into the fresh pile, so you can never lose the time left on one by stacking it: a unique item keeps its remaining time in a socket, the countdown only runs while it is on, and all three places the server merges items already compare every socket before combining anything. Putting one on takes **one** out of the pile — the server moved the whole stacked item into the slot, which was harmless while these could not stack and would have destroyed the entire pile when the hour ran out, so the two changes are made together and neither is applied without the other. If your bags are completely full the ring is not put on at all, rather than the rest of the pile being thrown away to make room. Quivers are untouched.

### Fixed

- **The bonus items dropped by metin stones were the wrong ones.** They were the pair that re-rolls the two *rare* bonus slots — the fifth and sixth, which almost nothing in this game ever fills and no ordinary item shows. Players were being handed items that appeared to do nothing on everything they owned. They are now the pair that works on bonuses one to four, which is what a player actually reads off a weapon or a piece of armour.

- **Ordinary monsters dropped boss loot.** The drop table was attached to 130 monsters it was never meant to include — everything at the rank just below a boss, the stone apes among them. That rank is a common monster in this distribution, not a boss, so the metin and boss reward was falling off things that die by the dozen. The table now covers exactly what it says: 68 metin stones and 108 bosses.

### Note for anyone running a server

Two of these changes are in the game's C++ and not in a data file — the three storeroom pages and the split that takes a single ring out of a stack. **The cores have to be rebuilt** for this release to do anything; re-running the installer is enough. Your database is not touched, and characters, accounts and stored items all survive.

---

## 1.15.2 — 2026-08-13

### Fixed

- **Killing another High Risk player never costs reputation.** It was already meant to be free, and mostly was — but only as a side effect of the killer mark the mode keeps lit, and that mark blinks: it is cleared the moment its wearer dies and only comes back a few seconds later, and there is a gap right after someone opts in before it is lit at all. A kill landing in either gap quietly took 20,000 reputation off the killer for something the mode promises is free. The rule now asks whether the victim is in High Risk instead of watching for the mark.

- **Updating with `--domain` forgot the e-mail address your certificate is registered with.** It was only ever read back from your server's settings inside the branch that runs when you *don't* name a domain — and naming it is exactly what the panel's own update command does. Passing `--domain` therefore skipped it and handed the certificate tool an empty address. It is now read back first, whichever way you run it.

## 1.15.0 — 2026-08-13

### Fixed

- **High Risk did nothing at all, on every server built from this repository.** The mode was offered at level 15, the player chose it, the choice was saved — and then nothing happened: they were not attackable, not marked, dropped nothing extra on death and got none of the bonuses. Only the *quest* half was ever staged into a build. The half that gives the choice meaning is a change to the game core, and that change existed only on the machine where it had been applied by hand; the server tree is re-staged from the pristine archive on every build, so it was never in anyone else's server. It is now applied during the build, every time, and the build refuses to start if it is missing rather than quietly producing a server where the mode is decorative.
- If you have High Risk switched on, this is the update that makes it real. Nobody has to re-choose anything: the choice was being recorded correctly the whole time and takes effect the moment the cores are rebuilt.

### Changed

- **High Risk sets your combat mode for you.** Choosing the mode put you in reach of everyone else in it without letting you fight back: whether *you* may hit someone is decided by your own combat mode, and that is Peace until you change it by hand. It is now set to Free for as long as High Risk is on, and kept there — the game quietly resets it in a few places, such as when a duel ends, and it comes straight back. Game masters and characters below the protection level are left alone, exactly as the rest of the game leaves them alone.
- **High Risk is now a pool, not a licence.** It only ever pairs you with other players who also chose it. Someone in No Risk can no longer kill a High Risk player and take what they drop, and a High Risk player can no longer hunt someone who never opted in — neither direction works, inside an empire or across empires. Both of you chose, or there is no fight. Guild wars, castle sieges, duels and the arena are settled before this rule and keep working between the two modes, because those are consensual on their own terms.
- **A High Risk death costs more.** Dying with the mode on now drops something from your bags **one time in two** (was one in ten) and something you are wearing **one time in ten** (was one in five). Quantities are unchanged — eight items from the bags, one worn item — and so is everything about which items can be lost at all. Characters who are simply Cruel are not affected: they still drop on exactly the odds the game shipped with, which is what the mode borrowed before and no longer does.

### Added

- **Skill books stack, and only with books of the same skill.** Part of the Custom Experience. Books for one skill now merge into a single slot instead of taking a fresh one each, whether you pick them up, drag them together or store them in the chest. Books for *different* skills never merge, and this is not a promise the change had to make good on itself: the generic Skill Book is one and the same item number for every skill it can teach — it carries the skill in a socket rather than in its number — and all three places the server merges items already compare every socket before they combine anything. Two books that teach different things differ there and are refused.
- Reading one book out of a stack now spends one book. The core deleted the *item* when a book was read, which was the same thing while books could not stack and would have thrown away the whole pile once they could, so the two changes are made together and neither is applied without the other.
- Off unless the Custom Experience is on. Unlike the Blessing Scroll, there is nothing in the shipped files that contradicts itself here — all 45 skill books agree that they do not stack — so this is a deliberate change rather than a fix, and it sits with the other deliberate ones.

## 1.13.1 — 2026-08-13

### Fixed

- **Nothing could be picked up.** Neither items nor Yang, by key or by clicking — the character walked to the drop and left it lying there. Removing a diagnostic line before the release took the body of an `if` with it, so the branch adopted the next statement and the pick-up was nested inside a condition that could never be true at the same time. It compiled without a warning. Browser client 1.11.6; the game data is unchanged, so this is a 17 MB update rather than 1.7 GB.

## 1.13.0 — 2026-08-13

### Added

- **Enable Custom Experience? — one question, and everything behind it.** The installer now asks once, before it downloads anything, whether your server should play the way the original files do or the friendlier way this project has been using. It is **off** by default and nothing changes for anyone who says no. Say yes and you get: items and Yang picked up from twice as far away, a horse that always comes when you call it, no waiting until tomorrow between the Horse Medal steps, bonus drops on 283 metin stones and bosses, Musk Oil stocked in the General Store, High Risk offered to your players, and everyone 20% faster on foot. Rates are untouched and so are your existing characters.
- **It is written down, and it is replayable.** The answer is kept as `M2_CUSTOM_EXPERIENCE` in your server's `.env`, so every later update rebuilds the server you have instead of the one the defaults would produce, and the update command the panel shows you names it. For an unattended install, `--custom-experience` / `--no-custom-experience` on Linux, `-CustomExperience` / `-NoCustomExperience` on Windows, or `M2_CUSTOM_EXPERIENCE=1` in the environment. `--yes` takes the default and leaves it off. Everything behind the switch now lives in `files/custom/` and is applied to the server tree at every build, so it survives updates instead of being quietly reverted by the next one — which is exactly what used to happen to changes made by hand.
- Turning it on also turns High Risk on and sets the movement-speed bonus to 20%, as starting points rather than as locks: `M2_HIGH_RISK=0` and a movement-speed bonus you have chosen yourself both still win, and both are carried forward untouched by later updates.
- **High Risk — a mode your players choose, at level 15.** They are asked once, shortly after they reach it: live dangerously, or carry on as before. High Risk means anyone may attack and kill them, anywhere, their own empire included, and nobody is punished for doing it. In exchange they earn 50% more experience and find 50% more drops — and when they die they drop items the way the cruellest characters do, out of their bags and off their bodies, using the game's own Cruel rules rather than a new one. No Risk changes nothing at all.
- **It is never a trap.** A character in High Risk is drawn the way a player-killer is drawn, to themselves and to everyone around them, so nobody is in it without knowing and nobody attacks one by accident. There is a line in the chat window at every login while it is on, and the choice can be reversed as often as they like at any Guardian or City Guard.
- Town safe zones still protect everyone, High Risk included — killing inside one would break every shop standing in it. Characters below level 15 and game masters are outside the mode entirely.
- To run a server without it, delete `files/high_risk.quest` before assembling, or set `M2_HIGH_RISK=0`. The rest of the change does nothing on its own: without that file no character can enter the mode and every check falls back to the ordinary rules.
- **The browser client keeps what it downloads.** It used to fetch half a gigabyte of game data in the background and lose it again by the next visit — not because the server said so, but because a browser's ordinary cache is one shared pool that the game's own reading pushes things out of. It now keeps that data in storage of its own. Measured: 144 downloads on a first visit, **one** on the second.
- **If it crashes, it offers to say so.** A dialog appears with what went wrong, a box to describe what you were doing, and a button to send it. Nothing leaves the browser unless that button is pressed, and the complete report can be read first. Account name and password are not in it — they are not reachable from the page at all.
- **Playing in the browser fills the window.** The game followed a fixed 1024×768 and let the browser stretch it. It now follows the window, including full screen, and remembers if you pin a resolution instead.

### Fixed

- **The Drachenhort quest paid out its own fee.** Handing in the items credited 150,000 Yang instead of charging it, and it could be repeated. Anyone who found it had unlimited money. This one is not behind the Custom Experience switch and never will be: it is a hole in the shipped files, it is open on every server running them untouched, and every server gets it closed.
- **A character with a friend, or in a guild of more than one, could not play in the browser.** The screen stayed grey at login and never finished loading. One line of the interface used a variable name that Python 3 no longer allows there, and it ran on every friend and every guild member.
- **A script error no longer takes the whole browser client down with it.** It is written to the console and the game carries on — which is how the bug above was found in seconds after days of guessing.
- Skills and emoticons can be dragged onto the quick slots again, and from one slot to another.
- Selling something no longer quotes a price with decimals in it. The price charged was always correct; only the confirmation was wrong.
- A weapon no longer stays in your hands after you take it off, and a metin's aura stays on the metin instead of occasionally landing on the player.
- Items and Yang are picked up from 600 units away on foot and 800 on a mount, instead of 300. With the Custom Experience on.
- Blessing Scrolls and Bravery Capes stack, along with eight more items that claimed to and never did — including Blessing Marbles and Scrolls of Correction. Every server gets this: the rows say they stack and then do not, which is a mistake in the table rather than a decision.
- The Horse Medal quests no longer make you wait between steps, and characters already waiting are released instead of serving out the rest. With the Custom Experience on.
- The Musk Oil quest points at the General Store, where the oil is actually sold, instead of an Item Shop this server does not have. With the Custom Experience on, which is also what puts the oil on the counter — the two go together, or the quest would send players to an empty shelf.
- Seven quests handed out rewards that did not match what they promised — among them one that skipped its Yang, experience and level-up entirely. Every server gets these: in each case the quest contradicts its own text, and the pack itself says which side was meant.

## 1.12.2 — 2026-08-12

### Fixed

- **The installer survives being run from a directory that was deleted.** Uninstall, then reinstall from the same terminal, and the installer used to stop three minutes in with `fatal: Unable to read current working directory` — which reads like a network problem and is not one. It now says what actually happened and carries on. The same protection covers the installer's own doing: it refreshes its checkout by deleting it, which pulled the rug out from under anyone who happened to be standing in it.
- [UNINSTALL.md](UNINSTALL.md) now says to leave the directory before deleting it, and shows that error so it can be recognised.

## 1.12.1 — 2026-08-12

- **[UNINSTALL.md](UNINSTALL.md)** — how to remove an installation completely and put a fresh one in its place. It says which of the five places an installation lives in can be thrown away freely, which one holds every character on your server, and how to save that one first. It also lists the three cheaper things to try before wiping anything.

## 1.12.0 — 2026-08-12

### Added

- **A second place to download from.** When MEGA answers `509 over quota` — the share's daily allowance, spent by other people, nothing to do with your machine — the installer now moves straight on to another copy of the same archive instead of stopping. It is the identical file and it is checked against the same checksum, so an install that used to mean coming back in a few hours carries on within seconds. This covers the three big downloads: the browser client's data, the desktop client, and the server files.
- Nothing to set up. The links travel in `artifacts.json` and an update picks them up. A link you supplied yourself is still tried first, and a fallback is only ever reached after the one before it has already failed.

## 1.11.13 — 2026-08-12

### Fixed

- The installer no longer tells you to copy the browser client onto the panel's volume by hand. It printed `docker compose cp ./browser panel:…` whenever playing in the browser was switched on — a leftover from before 1.11.0, when that really was the only way. Since then the installer fetches and installs the client itself, and the command it printed can only fail: there is no `./browser` directory in an install, so it answers `lstat …/browser: no such file or directory`. Reported by an operator who did exactly what the installer told him to.
- The same instruction is corrected in the Docker README, where it also pointed one directory too high — a client copied there is invisible to both the panel and nginx, which serve `browser/current`.

## 1.11.12 — 2026-08-12

### Added

- **A server-wide movement-speed bonus.** Set `M2_MOVE_SPEED_BONUS` in `.env` to a percentage and every character gets it at login — no item, no button, nothing for players to know about. `0` is off, which is what a server that says nothing gets. Changing the number takes effect at each character's next login; nothing has to be cleaned up.

## 1.11.11 — 2026-08-12

- The "What is this?" box on the front page says you can play in the browser — on servers that offer it — and no longer explains the panel to people who are looking for the game.

## 1.11.10 — 2026-08-12

- The front page puts the game account first, then the ways to play in one frame: **JETZT IM BROWSER SPIELEN**, a line saying **ODER**, and the download with its steps.
- The account card says what an account is for and that the same one works in the browser and in the download.

## 1.11.9 — 2026-08-12

- After registering, a player is shown the ways into the game this server really offers — the browser, the download, or both side by side with **ODER** between them.
- The browser card stands out and its button opens the game in a **new tab**, so the panel stays open behind it.

## 1.11.8 — 2026-08-12

- You are asked which clients you want **before** anything large is downloaded, instead of after.
- The Windows installer downloads only the server too, about 220 MB instead of 1.6 GB.
- The release notes below are written in plain language.

## 1.11.7 — 2026-08-12

- The Windows installer no longer stops at the question about which clients to install.
- A new install downloads only the server, about 220 MB instead of 1.6 GB.
- The desktop client is fetched from its own download.

## 1.11.6 — 2026-08-12

- The admin panel starts again on servers that use a domain name.

## 1.11.5 — 2026-08-12

- **Play in Browser** hands out a link that works on servers with HTTPS.
- The client download is fast again and no longer blocks the panel while it runs.

## 1.11.4 — 2026-08-12

- Updating now really does update the browser client.
- The installer writes its web-server settings again.

## 1.11.3 — 2026-08-12

- The browser client starts instead of stopping at "starting…".
- The browser client reaches servers that use a domain name.
- **Play in Browser** works on servers with HTTPS.
- The game stutters far less in the browser.
- A file that was briefly missing is no longer remembered as missing for a year.

## 1.11.2 — 2026-08-12

- The **Play in Browser** card appears in the panel again.

## 1.11.1 — 2026-08-12

- A server that chose the browser client now actually gets one.

## 1.11.0 — 2026-08-11

# 🌍 Play in the browser — no download

## Your players click a link and they are in the game. No client to download, no installation, nothing to set up on their side.

The installer asks which clients you want to offer — browser, desktop, or both
— and fetches only what you chose. Servers installed before this keep working
exactly as they are; the browser client is simply offered on your next update.

### Added

- Play in the browser: a link is all a player needs.
- The installer asks which clients you want and downloads only those.
- The browser client is installed for you, checked, and kept up to date.
- An update to the browser client is a small download, not the whole game again.
- Updating it cannot leave a player with half a client, and it can be undone.
- **Play in Browser** appears on the panel's front page once everything is ready.

## 1.10.0 — 2026-08-11

- The item search works on a local install and in older browsers, and says so when it cannot reach the server.
- Setting a level above what your server allows now tells you, instead of quietly doing nothing.
- The highest character level is 120 by default. Change `M2_MAX_LEVEL` in `.env` to raise it.
- **Game language** and **Admin passphrase** moved to the bottom of the admin page, under their own heading.

---

## 1.9.0 — 2026-08-11

### Added

- **Game language** on the admin page. The server files carry fifteen
  languages; pick one and the game speaks it — quest text, system messages,
  item and monster names. The game restarts for well under a minute.
- The download page says which language the game is in.
- After a switch, the panel shows players who already downloaded the game how
  to change their copy: one file to rename, nothing to download again.
- The client the panel hands out is built in the server's language.

### Fixed

- The patch log button had two translations, of which only the second was ever
  used.

---

## 1.8.0 — 2026-08-10

### Added

- **Admin passphrase** on the admin page, just under the introduction. Pick
  your own instead of the generated one; it takes effect straight away and you
  stay logged in.

### Changed

- The installer shows the admin passphrase every time it runs, including one
  you chose yourself in the panel, and never changes it behind your back.
- The introduction no longer says teleport and running speed are missing from
  a normal install. They are there; they need the player to be logged in.

---

## 1.7.0 — 2026-08-10

### Fixed

- The item search shows the names your game actually uses. The index had been
  built from the German name file while the server and the client use the
  English one, so nothing you saw in game matched what the panel offered.
- Searching for several words now needs all of them. "Full Moon Sword" no
  longer offers Half Moon Sword as well.
- Item numbers work in the search box, with or without the `#`. Typing `299`
  or `#299` finds that item, and `29` offers everything starting with it.

### Added

- **Show more** at the bottom of the item list, which used to stop at forty
  without saying so.
- German and Turkish item names are search keywords, so an item can be found
  by whichever of the three names you know.

---

## 1.6.0 — 2026-08-10

### Added

- Game master ranks on the player page. Pick a rank to give somebody the
  in-game admin commands, or set them back to a normal player. Granting takes
  effect immediately, even mid-game; taking a rank away applies at the player's
  next login.

### Fixed

- The game cores' admin interface had no password, which made an empty one
  correct. It now gets a generated password, like the others.
- The tutorial no longer claims that teleport and running speed do not work.

---

## 1.5.0 — 2026-08-10

### Changed

- Updating no longer asks for the address players connect to, or for your
  domain name. Both are kept from your settings. The address is only asked
  about when this machine has moved to a different one.

### Added

- `--no-domain`, to drop the domain a server was set up with and go back to
  plain HTTP on its address.

---

## 1.4.1 — 2026-08-10

### Fixed

- Running speed can be changed back. "Normal (reset)" resets it, a slower
  setting is slower than a faster one, and characters that were sped up before
  this version are put right the next time you set their speed.

---

## 1.4.0 — 2026-08-10

### Added

- The panel's in-game actions work. Items, yang and levels reach a character
  who is logged in straight away instead of at their next login, and teleport
  and running speed work at all.

Set `M2_INGAME_HELPER=0` in `.env` to leave the helper out.

---

## 1.3.4 — 2026-08-10

### Fixed

- The in-game helper no longer crashes the channel it runs on. It is still not
  installed by default — nobody has played on the fix yet.

---

## 1.3.3 — 2026-08-10

### Fixed

- The item search works in English and Turkish. It matched the whole box
  against German names, so "Full Moon Sword" found nothing while
  "Vollmondschwert" worked. It now matches word by word, translates the common
  ones, and ranks by how many words fit.

---

## 1.3.2 — 2026-08-10

### Fixed

- The in-game helper introduced in 1.3.0 disconnects the character it acts on.
  It is no longer installed. Items, yang and levels work as they did before
  1.3.0 — written to the account, visible at the next login — and teleport and
  running speed refuse instead of dropping the player.

**If you are on 1.3.0 or 1.3.1, update.** Until you do, avoid the buttons on a
character's page while somebody is playing on them.

---

## 1.3.1 — 2026-08-10

### Fixed

- Updating a server never picked up changes to the game itself. The source was
  staged once and reused, so the rebuild produced the same binaries and every
  C++ change since the install was dropped. If you updated to 1.3.0 and teleport
  still does not work, update again.

---

## 1.3.0 — 2026-08-10

### Added

- Teleport and running speed work. The helper that carries them out is now
  built and installed with the server.
- Items, yang and levels reach a character who is logged in straight away,
  instead of at their next login.

### Fixed

- On a Linux host the game could start with no quests loaded at all, and still
  report itself healthy. Staged quest files could carry permissions the server
  account could not read.

### Security

- The database function the helper uses accepts only statements against the
  panel's own queue table.

---

## 1.2.3 — 2026-08-10

### Fixed

- The update command shown in the panel now includes the options the server was
  installed with, such as `--domain` and `--email`. It previously showed the
  bare one-liner, which on the next update would have dropped the certificate.

---

## 1.2.2 — 2026-08-10

### Fixed

- Giving an item, yang or a level to a character who is logged in no longer
  claims they were not in game. It says the change was written to the account
  and appears at their next login.
- Teleport and running speed now say that nothing in the game answered and
  that nothing was changed, instead of suggesting the game server might be
  down.

---

## 1.2.1 — 2026-08-10

### Changed

- Removed the paragraph about the deleted `admin` and `test` accounts from the
  panel's introduction.

---

## 1.2.0 — 2026-08-10

### Changed

- The patch log splits the changelog at the version you are running: "What an
  update would bring" lists only the releases you do not have yet, and "What
  you are running" the rest. No release appears in both.

---

## 1.1.9 — 2026-08-10

### Changed

- The patch log shows the changelog once. When an update was available it was
  printed twice, under two headings, with the same releases in both.

---

## 1.1.8 — 2026-08-10

### Changed

- The update page now says to re-run the command that installed the server,
  and what an update leaves alone, instead of explaining a setting that is off.

---

## 1.1.7 — 2026-08-10

### Changed

- Removed the heading above the changelog on the patch log page. The file
  brings its own, so there were two.

---

## 1.1.6 — 2026-08-10

### Added

- A "Check for the latest version" button on the patch log page. It asks
  straight away instead of waiting for the daily check.

---

## 1.1.5 — 2026-08-10

### Changed

- The installer now ends with the panel address and the game, instead of
  opening with them and scrolling them off the screen.
- A local Windows install no longer prints an admin passphrase. The panel does
  not ask for one there.
- Removed the note about the shipped `admin` and `test` accounts. They are
  deleted during setup.

---

## 1.1.4 — 2026-08-10

### Fixed

- The Windows installer now updates an existing server as well, and shows the
  installed and published versions before asking. Re-running it previously
  re-applied the settings and restarted without fetching anything.

---

## 1.1.3 — 2026-08-10

### Changed

- When a server is already installed, the installer shows which version it is
  on and which one is published, then asks whether to update or to only
  re-apply the settings and restart.
- A server installed before versions existed is recognised as such and offered
  the update.

---

## 1.1.2 — 2026-08-10

### Fixed

- Re-running the installer on a server that was already installed now updates
  it. It used to rewrite the settings and restart the containers without
  fetching anything, so the server stayed on the version it was installed with.

---

## 1.1.1 — 2026-08-10

### Changed

- The patch log has its own card in the admin area, with a button. It used to
  be a grey line at the bottom of the page.
- The card highlights itself when a newer version is available.
- The front page shows the version number only. The patch log and the update
  notice are in the admin area.
- Shorter wording when the update check cannot reach the server.

---

## 1.1.0 — 2026-08-09

### Added

- A `VERSION` file and this changelog.
- An update check in the admin panel. It compares your version against the
  published one roughly once a day and tells you when a newer one exists, with
  the release notes for it. Can be switched off with `M2_UPDATE_CHECK=0`.
- A patch-log page in the panel, showing this file.
- The command that updates your server, shown on that page. The installer
  records it, so the panel shows the exact line for your install. Re-running
  the installer pulls the published version, rebuilds and restarts, and keeps
  your database, passwords and settings.
- A one-click update button on Linux. Off by default; see
  [UPDATING.md](UPDATING.md) to turn it on. On Windows the panel shows the
  command to paste instead.

---

## 1.0.0 — 2026-08-09

First public release. A Metin2 r40250 server that runs on ordinary Linux — or
on a Windows PC, for one person — installed with a single command.

### Added

- The Linux port, as a 109 KB patch over 28 files. A fresh copy of the upstream
  package plus this patch reproduces the running server byte for byte.
- Docker packaging: game cores, MariaDB, the admin panel and a client builder,
  in one compose stack.
- One-command installers for Linux and Windows. The Linux one publishes the
  game ports and opens the firewall; the Windows one binds everything to
  `127.0.0.1` and creates no firewall rule.
- The admin panel — English, German and Turkish. Server rates, giving items and
  yang, levels, password-reset links, registration and a client download.
- A client builder that patches the game to point at your server and offers it
  for download. On a Windows install it unpacks the game and puts a
  `Metin2 Singleplayer` shortcut on the Desktop.

### Fixed

- The client download returned 500 on every request. The panel could not create
  the file it counts downloads in.
- The panel showed a running server as offline, and the player count stayed at
  zero.
- "Give 1000 potions" silently gave 255.
- Items were refused to characters that had room for them: the panel searched
  one inventory page of 45 where r40250 gives four.
- The dashboard reported "the database cannot be reached" for a character who
  had never played.
- The game archive was downloaded twice, once for the server and once for the
  client.
- A path containing a space broke the client build.

### Security

- The shipped `admin` and `test` accounts are deleted during setup, together
  with their game-master entry.
- Download limits: three per address per day, plus a server-wide daily ceiling.
- Rate limits on registration, account login and the admin passphrase.
- Passwords are generated on the machine at install time.
