# Metin2 Singleplayer Panel

Metin2 Singleplayer Panel to alternatywny panel administracyjny i obserwacyjny dla serwerów Metin2 z Playerbots. Działa w osobnym kontenerze na porcie `7789`, obok klasycznego Panelu Tieru, który zwykle pozostaje na porcie `7788`.

Projekt korzysta z tej samej bazy, plików statusu Playerbots i kolejki administracyjnej. Nie zastępuje klasycznego panelu ani nie wymaga migracji danych — rozszerza instalację o dodatkowy, nowoczesny widok świata i narzędzia administracyjne. W menu znajduje się opcjonalny odnośnik do Panelu Tieru.

## Wydanie 1.37.0

To wydanie jest przygotowane dla Playerbots Tieru `1.30.12`. Zawiera Łatwy, Normalny i Trudny Loch Małp (ID 25, 108 i 109) na mapie live, mapach historycznych, heatmapach i w ustawieniach respawnu. Dla tych lochów można zmieniać tylko respawn potworów: pakiety map nie zawierają osobnego pliku `stone.txt` dla Metinów.

## Co oferuje

- mapa świata botów odświeżana co 1,5 sekundy, z prawidłowymi proporcjami obsługiwanych map;
- filtry poziomów, wyszukiwarka, widok grup, ranking na mapie oraz oznaczenia botów możliwie zawieszonych i walczących z Metinem;
- globalne rankingi botów: poziom, Yang, broń, pancerz, koń oraz bronie 30 poziomu z sortowaniem po średnich obrażeniach, obrażeniach umiejętności i ulepszeniu;
- postacie z widokiem ekwipunku i magazynu, stackami, Yang, HP/MP/EXP, statystykami, pozycją, koniem, kolorową rangą oraz historią logów;
- tooltipy przedmiotów w stylu gry, z bonusami, wartościami ujemnymi, kamieniami duszy i ich właściwościami;
- ikony oraz stopnie umiejętności od zwykłego poziomu po M, G i P;
- ekonomię z historią stanu przedmiotów i wykresem Yang w obiegu;
- telemetrię CPU, RAM i dysku z historią oraz wyborem prezentacji hosta/VPS albo Dockera;
- dashboard z wersją Playerbots, poziomem jeździectwa i przypiętym paskiem istotnych wydarzeń świata;
- zarządzanie mnożnikami, zachowaniem Playerbots i restartem przez kolejkę natywnej instalacji;
- masowe nadawanie przedmiotów przez VNUM, ilość i warunki: poziom, klasa, koń, jeździectwo oraz czas gry;
- kreator pierwszego uruchomienia, motywy Ocean/Ember/Forest i opcjonalną ochronę hasłem.

Panel uzupełnia klasyczny Panel Tieru o historię gospodarki, telemetrię hosta, ticker wydarzeń, rozbudowane rankingi i masowe nadania z warunkami. Oba panele mogą działać równolegle.

## Wymagania

- Docker Engine i Docker Compose v2 na hoście Linux;
- uruchomiona instalacja Metin2 z MariaDB/MySQL oraz Playerbots;
- konto bazy używane przez panel z dostępem do baz `player`, `account` i `common`; konto musi móc utworzyć tabele `player.web_seban_*` oraz `player.web_admin_queue`;
- zewnętrzna sieć Dockera, na której panel rozwiąże nazwę bazy i kontenera gry;
- dwa istniejące wolumeny: wolumen z `/opt/metin2/var` oraz wolumen kolejki mnożników/restartu;
- dla masowych nadań: aktywny `web_admin.quest` i bezpiecznie zaimplementowane w rdzeniu `mysql_direct_query()` dla tabeli `player.web_admin_queue`.

Bez ostatniego punktu działa monitoring, profile, rankingi, gospodarka i konfiguracja, ale nadania dla aktywnych postaci nie zostaną wykonane w grze.

## Instalacja

1. Sklonuj repozytorium i przejdź do katalogu panelu.

   ```bash
   git clone <URL_REPOZYTORIUM>
   cd <KATALOG_REPOZYTORIUM>/seban-panel
   ```

2. Sprawdź nazwy zasobów istniejącej instalacji.

   ```bash
   docker network ls
   docker volume ls
   ```

   Potrzebujesz sieci, na której działają MariaDB i gra, wolumenu zawierającego `/opt/metin2/var` oraz wolumenu kolejki używanej przez klasyczny panel.

3. Utwórz prywatny plik konfiguracji i uzupełnij go własnymi wartościami.

   ```bash
   cp seban-panel.env.example seban-panel.env
   openssl rand -hex 32
   ```

   Wklej wygenerowaną wartość do `SEBAN_SESSION_SECRET`. Ustaw też `DB_HOST`, dane bazy, nazwy sieci i wolumenów. `TIERU_PANEL_URL` musi być adresem dostępnym **z przeglądarki użytkownika**, np. `http://adres-serwera:7788`.

4. Sprawdź konfigurację, a następnie uruchom kontenery.

   ```bash
   docker compose --env-file seban-panel.env config
   docker compose --env-file seban-panel.env up -d --build
   ```

5. Otwórz `http://adres-serwera:7789/setup`. Kreator poprosi o nazwę panelu, motyw, alarm bez ruchu, źródło monitoringu i opcjonalne hasło.

6. Zweryfikuj uruchomienie.

   ```bash
   docker compose --env-file seban-panel.env ps
   docker compose --env-file seban-panel.env logs --tail=100 seban-panel seban-collector seban-item-grants
   ```

## Konfiguracja środowiska

| Zmienna | Znaczenie |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` | Połączenie z bazą Metin2. |
| `PLAYERBOTS_NETWORK` | Nazwa zewnętrznej sieci Dockera wspólnej z grą i bazą. |
| `PLAYERBOTS_GAME_VAR_VOLUME` | Wolumen zamontowany przez grę jako `/opt/metin2/var`. |
| `PLAYERBOTS_RATES_SPOOL_VOLUME` | Wolumen kolejki mnożników, zachowań i restartu. |
| `PLAYERBOTS_GAME_HOST` | Nazwa DNS kontenera gry w tej sieci. |
| `PLAYERBOTS_LOGIN_PORT`, `PLAYERBOTS_WORLD_PORT` | Porty używane do kontroli etapu restartu. |
| `PLAYERBOTS_VERSION` | Wersja aktualnie zainstalowanego wydania Tieru, wyświetlana na Dashboardzie. Aktualizuj ją razem z rdzeniem. |
| `PLAYERBOTS_STATUS_GLOB` | Położenie plików `playerbot_status.tsv` wewnątrz panelu. |
| `TIERU_PANEL_URL` | Publiczny adres klasycznego Panelu Tieru; używany przez link i ikony umiejętności. |
| `SEBAN_SESSION_SECRET` | Długi, losowy sekret sesji. Nigdy go nie publikuj. |
| `SEBAN_COLLECTOR_INTERVAL` | Interwał kolektora w sekundach, domyślnie `300`. |

`seban-panel.env` jest ignorowany przez Git. Nie umieszczaj w repozytorium haseł, adresów prywatnych ani sekretów.

## Aktualizacja

Od wersji 1.34.0 wspólne ustawianie mnożników i osobnych czasów respawnu potworów/Metinów wymaga również [integracji z kontenerem gry](integration/README.md). Samo zaktualizowanie kontenera panelu nie wystarczy do obsługi tej kolejki. Postęp, data oraz źródło restartu są widoczne w tej samej sekcji co przyciski zarządzania.

```bash
git pull
docker compose --env-file seban-panel.env up -d --build
```

Tabele historii i ustawienia pozostają w bazie. Przed aktualizacją produkcji wykonaj kopię bazy danych.

## Bezpieczeństwo

- Włącz hasło podczas pierwszej konfiguracji, jeśli panel jest dostępny spoza zaufanej sieci.
- Wystawiaj port `7789` przez reverse proxy z HTTPS, gdy panel ma być dostępny z Internetu.
- Nie wystawiaj MariaDB publicznie i ogranicz uprawnienia konta bazy do niezbędnych baz.
- Przed uruchomieniem masowych nadań przetestuj `web_admin.quest` na postaci testowej.

## Rozwój

Projekt będzie rozwijany dalej. Kolejne wersje będą poszerzać diagnostykę Playerbots i widoki danych, zachowując współpracę z klasycznym Panelem Tieru.
