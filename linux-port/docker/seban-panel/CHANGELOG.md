# Zmiany
## 2026-09-09 18:10 CEST · 1.40.0

- Dodano zwijany poradnik uruchomienia aktualizatora Tieru na VPS bezpośrednio w Zarządzaniu.
- Tabele, przyciski, linki, przedziałki i kafelki wskazanych widoków dziedziczą teraz aktywny motyw.
- Baza przedmiotów pokazuje ikonę rzeczywistego przedmiotu przy każdej kategorii.
- Konta i profil postaci pokazują flagę oraz nazwę królestwa.

## 2026-09-09 17:45 CEST · 1.39.1

- Karta Playerbots · świat na Dashboardzie dziedziczy pełną kolorystykę aktywnego motywu, także dla etykiet, rat i listy map.

## 2026-09-09 17:30 CEST · 1.39.0

- Kreator GM pozwala wybrać kobietę albo mężczyznę; zapisuje właściwy wariant modelu klienta, zachowując klasyczny wariant jako domyślny.
- Oryginalne portrety klas są widoczne w profilu postaci, liście graczy, rankingach, karuzeli Dashboardu i rankingu aktualnej mapy.
- Ranking botów otrzymał kolumnę klasy z portretem i nazwą.
- Mapa na żywo, filtry, paski aktywności oraz karuzela rankingów dziedziczą teraz pełną paletę motywu Ocean, Ember lub Forest.

## 2026-09-09 16:47 CEST · 1.38.6

- Kreator kont GM zapisuje teraz indeks wyboru postaci (`player.player_index`), więc utworzona postać jest widoczna od razu po zalogowaniu.
- Nieudana konfiguracja GM sprząta utworzone przez siebie rekordy, także na tabelach MyISAM bez transakcji.
- Nick GM przyjmuje pojedynczy prefiks w nawiasach, np. `[GM]Seban` lub `[GA]Seban`.
- Dodano osiem oryginalnych portretów klas z ekranu postaci klienta do `static/class-portraits/`.

## 2026-09-08 21:45 CEST · 1.38.5

- Wiadomości świata odzyskują polskie nazwy ulepszanych przedmiotów z VNUM; ulepszenia +8 i +9 są złote.
- Sezon liczy wyłącznie trzy indeksowane typy zdarzeń z ostatnich 7 dni, bez pełnych skanów całej historii logów.

## 2026-09-08 17:35 CEST · 1.38.4

- Sesja panelu ma własną nazwę ciasteczka i trwa 30 dni. Nie koliduje już z klasycznym panelem Tieru działającym na tym samym hoście pod innym portem.
- Dodano poprawkę rdzenia: po załadowaniu danych questa bot uruchamia własne timery. Dzięki temu odbiera także masowe nadania z kolejki panelu.
- Masowe nadania wybierają wyłącznie Playerboty; postacie zwykłych graczy i administracji nie trafią do listy odbiorców nawet wtedy, gdy spełniają warunki poziomu lub konia.

## 2026-09-08 17:15 CEST · 1.38.3

- Uporządkowano wykresy map: trwała paleta kolorów, wybór map przez tabelę i checkboxy oraz tooltip z godziną i liczbą postaci.
- Dashboard i `/manage` sprawdzają najnowsze wydanie Playerbots na GitHubie co 15 minut; lokalna wersja jest zielona, gdy aktualna, i pomarańczowa, gdy zaległa.
- Pasek wiadomości świata można ukryć; na telefonie zachowuje formę pojedynczego paska.
- Konto GM tworzy teraz od razu prawidłową postać wybranej klasy w wybranym królestwie; sama ranga GM nadal wymaga restartu usług gry.

## 2026-09-08 15:00 CEST · 1.38.2

- Dodano brakujące, śledzone tło ekwipunku `inventory-background.svg`; jest kopiowane do każdego obrazu i ZIP-a panelu.
- Helper ustawień serwera publikuje sygnał gotowości. `/manage` nie pozwala już utworzyć zlecenia restartu/respawnu, gdy integracja gry nie działa.
- Dodano bezpieczne usunięcie wyłącznie zaległego zlecenia po 10 minutach bez aktywnego helpera oraz wyjaśnienie instalacji integracji w README.

## 2026-09-08 14:35 CEST · 1.38.1

- Dodano `UPDATER_VPS.md`: komendy dla standardowych i niestandardowych instalacji Tieru na VPS, przygotowanie cache oraz diagnostykę aktualizatora.
- Rozszerzono README o wymagany wolumen `update-spool` i instrukcję włączenia aktualizacji z panelu.

## 2026-09-08 00:00 CEST · 1.38.0

- Dodano most do izolowanego aktualizatora Tieru w `/manage`: stan, postęp, log i przycisk zlecenia aktualizacji.
- Panel zapisuje wyłącznie identyfikator zlecenia do wspólnej kolejki; Docker socket pozostaje wyłącznie w kontenerze aktualizatora.
- Przycisk wymaga aktywnej ochrony hasłem oraz tokenu sesji; wdrożona aktualizacja automatycznie odświeża widoczną wersję Playerbots.

## 2026-09-07 22:55 CEST · 1.37.1

- Poprawiono źródło wersji Playerbots w Dashboardzie: jest ustawiane jawnie w `PLAYERBOTS_VERSION`, a przykładowa konfiguracja wskazuje 1.30.12.

## 2026-09-07 22:35 CEST · 1.37.0

- Zaktualizowano rdzeń Playerbots do wydania Tieru 1.30.12: obsługę szkatułek, wycenę bonusów w sklepach oraz diagnostykę Dockera.
- Dodano Loch Małp Normalny (108) i Loch Małp Trudny (109) do mapy na żywo, historii natężenia, heatmap, wykresów, list map i zarządzania respawnem.
- Z panelu można teraz sterować respawnem potworów we wszystkich trzech Lochach Małp; Metiny są ukryte, ponieważ te mapy nie mają pliku `stone.txt`.

## 2026-09-07 22:00 CEST · 1.36.2

- Dodano ranking zabitych bossów (`BOSS_KILL`) za ostatnie 7 dni do `/rankings` i karuzeli Dashboardu.
- Zweryfikowano produkcyjnie ustawienia respawnu: aktywne wartości są zapisywane do właściwych plików `regen.txt` przed restartem rdzeni.

## 2026-09-07 21:27 CEST · 1.36.1

- `/maps` pokazuje pełną listę obsługiwanych map, także gdy bieżące natężenie wynosi 0.
- Dodano warstwę cieplną zabitych bossów (`BOSS_KILL`) na dashboardzie i w aktywności map.
- Dodano publiczną w panelu sekcję Changelog; kolejne hotfixy będą dopisywane z czasem wdrożenia.
- Połączono kafelki postaci i kont, a wersję panelu przeniesiono do stopki dashboardu.

## 1.36.0

- Dodano Górę Sohan (ID 61) i Loch Pająków V1 (ID 104) do mapy live, historii natężenia, heatmap, wykresów, list botów oraz ustawień respawnu.
- Wsparto osobny respawn potworów dla obu map i Metinów dla Góry Sohan; Loch Pająków V1 nie zawiera pliku `stone.txt`, co panel oznacza wprost.
- Podkłady obu map są renderowane z tych samych danych terenu, z których korzysta nawigacja Playerbots.

## 1.35.0

- Synchronizacja nazw i numerów umiejętności z aktualnym Panelem Tieru: ikona i podpis używają tego samego VNUM; nieużywane pozycje nie są już wyświetlane.
- Zarządzanie zachowaniem obsługuje przełącznik szybkich ksiąg (`BOOKS`) oraz szanse szkatułek (`CHEST`, `CHEST_STONE`).
- Zapis wag zachowuje przyszłe klucze silnika, których panel jeszcze nie zna.

## 1.34.0

- Osobne czasy respawnu potworów i Metinów dla obsługiwanych map.
- Jawne ID map, Joan przypisane do Chunjo M1 (21); poprawiona ścieżka Doliny Orków (64).
- Wspólna kolejka mnożników i respawnu: jeden restart dla całego zestawu, walidacja i cofnięcie ustawień przy błędzie zapisu.
- Równe przyciski, postęp i historia restartu w jednej sekcji zarządzania.
- Data ukończonego restartu, źródło zlecenia oraz osobna informacja o automatycznym podniesieniu rdzenia.
- Przycisk samego restartu pomija niezapisane pola, również gdy zawierają nieprawidłowe wartości.
- Testy regresji formularza i integracji z kontenerem gry.
