# Aktualizator Tieru — instrukcja krok po kroku

To wykonujesz **raz na VPS**. Potem aktualizacja odbywa się przyciskiem w panelu.

1. Zaloguj się przez SSH i przejdź do katalogu instalacji Tieru:

```bash
cd /opt/metin2-playerbots/upstream-1.29.10/linux-port/docker
```

2. Uruchom oficjalny aktualizator i sprawdź go:

```bash
docker compose --profile update up -d updater
docker compose exec updater m2-updater selftest
```

Jeżeli na końcu jest `everything it needs is here`, aktualizator jest gotowy.

3. W pliku `seban-panel.env` panelu wpisz nazwę wolumenu aktualizatora. Najpierw znajdź ją:

```bash
docker volume ls --format '{{.Name}}' | grep 'update-spool$'
```

Skopiuj wynik do `PLAYERBOTS_UPDATE_SPOOL_VOLUME=...`, a potem przebuduj panel:

```bash
cd /opt/seban-panel
docker compose --env-file seban-panel.env up -d --build seban-panel
```

4. Otwórz `/manage`, włącz ochronę hasłem panelu i zaloguj się. W sekcji **Aktualizator Tieru** kliknij **Pobierz i zainstaluj aktualizację Tieru**. Obserwuj postęp oraz log na tej samej stronie.

## Jeżeli selftest zgłasza brak `Reference_Server.zip`

To znaczy, że aktualizator nie ma legalnego pakietu bazowego plików serwera r40250. Nie pobieraj go z przypadkowego adresu. Skorzystaj z własnego, legalnie posiadanego pakietu i wykonaj pełną procedurę z `UPDATER_VPS.md`.

Aktualizacja rozłączy graczy podczas przebudowy, ale nie usuwa wolumenów bazy, postaci ani ekwipunku.
