# Aktualizator Tieru na VPS

Ten poradnik włącza przycisk aktualizacji w Seban Panelu. Działa on przez oficjalny, odizolowany kontener `updater` Tieru. Seban Panel zapisuje tylko zlecenie do wspólnego wolumenu; nie ma dostępu do socketu Dockera.

Przed rozpoczęciem włącz hasło w Seban Panelu. Przycisk aktualizacji jest dostępny wyłącznie po zalogowaniu, aby osoba odwiedzająca publiczny adres panelu nie mogła zrestartować serwera.

## Wariant standardowy Tieru

Poniższe polecenia wykonaj na VPS przez SSH jako użytkownik z `sudo`. Zastąp `/opt/seban-panel` ścieżką, pod którą rozpakowano Seban Panel.

```bash
STACK=/opt/metin2/stack
PANEL=/opt/seban-panel

# Sprawdź, czy wskazany katalog należy do instalacji Tieru.
test -f "$STACK/docker-compose.yml"

# Znajdź nazwę współdzielonego wolumenu aktualizatora.
docker volume ls --format '{{.Name}}' | grep 'update-spool$'
```

Wpisz znalezioną nazwę do prywatnego pliku konfiguracji Seban Panelu, przykładowo dla `metin2_update-spool`:

```bash
printf '\nPLAYERBOTS_UPDATE_SPOOL_VOLUME=metin2_update-spool\n' >> "$PANEL/seban-panel.env"
cd "$PANEL"
docker compose --env-file seban-panel.env up -d --build seban-panel
```

Uruchom oficjalny kontener aktualizatora i sprawdź jego gotowość. Nie pobiera on wtedy wydania ani nie restartuje gry.

```bash
cd "$STACK"
docker compose --profile update up -d updater
docker compose exec updater m2-updater selftest
```

Poprawny wynik kończy się linią `everything it needs is here`. Odśwież `/manage` w Seban Panelu, zaloguj się i użyj przycisku **Pobierz i zainstaluj aktualizację Tieru**.

## Gdy test mówi o brakującym pakiecie serwera

Oficjalny projekt celowo nie pobiera plików serwera Metin2 z przypadkowych adresów. Aktualizator potrzebuje jednorazowo legalnie posiadanego pakietu bazowego r40250, np. `Reference_Server.zip`. Jeżeli serwer został postawiony oficjalnym instalatorem Tieru, pakiet zwykle jest już w cache i ten krok nie jest potrzebny.

Jeśli `selftest` przechodzi, ale pierwsze zlecenie zatrzymuje się przy `No Metin2 server-file package`, przygotuj cache z własnego pakietu. Wskaż prawidłową ścieżkę do archiwum — nie publikuj go ani nie dodawaj do repozytorium:

```bash
STACK=/opt/metin2/stack
CACHE=/var/cache/m2src
ARCHIVE=/bezpieczna/sciezka/Reference_Server.zip

sudo cp "$ARCHIVE" "$CACHE/Reference_Server.zip"
docker compose --project-directory "$STACK" exec updater sh -lc \
  'sh /var/cache/m2src/repo/linux-port/fetch-sources.sh fetch --cache /var/cache/m2src --archive /var/cache/m2src/Reference_Server.zip'
docker compose --project-directory "$STACK" exec updater m2-updater selftest
```

To przygotowuje cache i kontekst przyszłych wydań. Nie wdraża aktualizacji do działającej gry.

## Instalacja o niestandardowej ścieżce

Jeżeli `docker compose ls` pokazuje inny katalog niż `/opt/metin2/stack`, ustaw go jawnie w pliku `.env` instalacji Tieru. Przykład poniżej zachowuje istniejące wartości i aktualizuje tylko klucze aktualizatora:

```bash
STACK=/wlasna/sciezka/do/linux-port/docker
CACHE=/var/cache/m2src
REPO="$CACHE/repo"

set_kv() {
  key="$1" value="$2"
  if grep -q "^${key}=" "$STACK/.env"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$STACK/.env"
  else
    printf '%s=%s\n' "$key" "$value" >> "$STACK/.env"
  fi
}

set_kv M2_UPDATE_STACK_DIR "$STACK"
set_kv M2_UPDATE_CACHE_DIR "$CACHE"
set_kv M2_UPDATE_REPO_DIR "$REPO"
set_kv M2_UPDATE_BRANCH main

docker compose --project-directory "$STACK" --profile update up -d updater
docker compose --project-directory "$STACK" exec updater m2-updater selftest
```

Jeśli test wskaże brak repozytorium, utwórz je raz:

```bash
sudo git clone --depth=1 https://github.com/TieruYT/metin2-playerbots.git /var/cache/m2src/repo
```

Następnie wykonaj opisane wyżej przygotowanie cache z własnym pakietem r40250.

## Co robi przycisk

1. Pobiera bieżący kod z gałęzi `main` Tieru.
2. Przygotowuje kontekst Docker, korzystając z lokalnego cache plików serwera.
3. Kopiuje nowy kontekst nad instalację bez kasowania `.env` ani `docker-compose.override.yml`.
4. Wykonuje `docker compose up -d --build`.
5. Pokazuje postęp i log w `/manage`.

Podczas kroku 4 gracze zostaną rozłączeni. Aktualizator nie wykonuje `docker compose down -v` i nie usuwa wolumenów bazy, postaci ani ekwipunku.

## Diagnostyka

```bash
cd "$STACK"
docker compose ps
docker compose logs --tail=100 updater
docker compose exec updater m2-updater selftest
df -h /
```

Gdy aktualizacja zgłosi błąd, przeczytaj log w `/manage`. Błąd przygotowania cache następuje przed podmianą działającej gry; popraw cache i zleć aktualizację ponownie.
