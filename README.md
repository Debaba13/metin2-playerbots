# ⚔️ Metin2 Playerbots

**Polski** | [English (README_EN.md)](README_EN.md)

[![Discord](https://img.shields.io/badge/Discord-Dołącz_do_społeczności-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/6v4WkDY6a)
[![BuyCoffee](https://img.shields.io/badge/BuyCoffee-Postaw_kaw%C4%99-FF813F?style=for-the-badge&logo=coffeescript&logoColor=white)](https://buycoffee.to/metin2-playerbots)

Lokalny świat Metin2 singleplayer, w którym po mapie biegają i autentycznie grają autonomiczne postacie (Playerbots): zdobywają poziomy, walczą solo i w party, zbierają łup, ulepszają ekwipunek u Kowala, polują na Metiny i zapisują swój postęp w standardowej bazie danych.

## Wersja 2.0 — nowe pliki serwerowe (mt2009)

Od 2.0.0 projekt działa na plikach serwerowych mt2009. To **pełna paczka**
(klient + serwer w jednym zipie), do pobrania z Discorda:
[discord.gg/pt5tvnrN6](https://discord.gg/pt5tvnrN6). Stary launcher i stary
klient z linii 1.33 **nie pasują** do nowych plików — nie aktualizuj po staremu,
pobierz całość. Po rozpakowaniu aktualizacje serwera i klienta przychodzą przez
launcher, jak dotąd; linia 2.x ma własny kanał (`update-manifest-mt2009.json`),
więc instalacje 1.33.x niczego z niej nie dostaną.
Jak to jest zbudowane: [linux-port-mt2009/README.md](linux-port-mt2009/README.md).

## 💬 Społeczność i wsparcie projektu

- **[Dołącz do serwera Discord](https://discord.gg/6v4WkDY6a)** — porozmawiaj o projekcie, podziel się testami i pomysłami oraz śledź aktualności z rozwoju botów.
- **[Wesprzyj rozwój na Zrzutka.pl](https://zrzutka.pl/rw4g7p)** — dobrowolne wpłaty pomagają pokrywać koszty narzędzi i modeli AI wykorzystywanych podczas rozwijania projektu.

<a href="https://buycoffee.to/metin2-playerbots" target="_blank"><img src="https://buycoffee.to/btn/buycoffeeto-btn-primary.svg" style="height: 42px;" alt="Postaw kawę na buycoffee.to"></a>

Każda forma wsparcia — testy, zgłoszenia błędów, propozycje, kod lub wpłata — pomaga nam tworzyć coraz bardziej samodzielny i żywy świat Metin2.

> [!IMPORTANT]
> Projekt działa wyłącznie z **natywnym klientem Windows**. Nie zawiera ani nie pobiera automatycznie plików Metin2, pakietu r40250 lub wycofanego WebClienta. Do instalacji potrzebujesz własnej zgodnej kopii plików. Zobacz [pochodzenie projektu i atrybucję](docs/ATTRIBUTION.md).

W przeciwieństwie do tradycyjnych botów-klientów, boty w tym projekcie są **pełnoprawnymi bytami PC sterowanymi przez AI bezpośrednio wewnątrz silnika serwera (`game core`)**. Oznacza to, że zwykły gracz po wejściu do gry widzi ich naturalny ruch, animacje ataków, skille oraz ekwipunek przez standardowy protokół gry.

---

## 🌟 Możliwości botów

- ⚔️ **Inteligentna walka**: Obsługa wszystkich klas (Wojownik, Sura BM/WP, Ninja Dagger/Archer, Szaman), płynne animacje kombosów, ataki z łuku z uwzględnieniem strzał, utrzymywanie buffów i rotacje skilli.
- 🗺️ **Globalna nawigacja 2D NavGrid (A*)**: Własna siatka kolizji generowana z atrybutów mapy (`server_attr`) oraz algorytm A* z wygładzaniem tras (*String Pulling*). Boty sprawnie omijają góry, rzeki i mury miejskie.
- 🚪 **Podróże między mapami**: Autonomiczne przejścia przez portale M1 ↔ M2 ↔ M3 oraz połączenia wewnątrz Łatwego Lochu Małp. Boty dobierają strefę do poziomu i jakości ekwipunku.
- 💎 **Polowanie na Metiny**: Dedykowana rola łowców Metinów patrolujących całą mapę, niszczących kamienie i czyszczących fale potworów.
- 🎒 **Loot i ekonomia miejska**: Zbieranie Yang i przedmiotów po walce, automatyczne ubieranie lepszego ekwipunku wraz z tarczami, regularne powroty do odpowiednich handlarzy, uzupełnianie mikstur i ulepszanie u **Kowala**.
- 🐴 **Rozwój konia**: Wyprawy po prawdziwe Medale Konne do Lochu Małp, oddawanie ich najbliższemu Stajennemu i używanie konia do długich podróży.
- 👥 **Grupy i Party**: Dynamiczne tworzenie 2–3 osobowych drużyn, formacje bojowe i wspólne expienie w gęstych obozach potworów.
- 💾 **Trwały zapis w bazie**: Każdy bot posiada własne konto i postać w bazie MariaDB — zachowuje poziom, przedmioty, Yang i postępy po restarcie serwera.

---

## 📊 Status projektu

Projekt jest w fazie aktywnego rozwoju.

> [!NOTE]
> **Obsługiwane Królestwa:** Autonomiczny świat obejmuje **wszystkie trzy królestwa** (**Chunjo** – Żółci, **Shinsoo** – Czerwoni oraz **Jinno** – Niebiescy) wraz z mapami M1, M2, M3, Lochami Małp, **Doliną Orków**, **Pustynią Yongbi**, **Górą Sohan**, **Świątynią Hwang** oraz **Lochami Pająków**!

### Zużycie zasobów (Snapshot dla 350 botów)
- **Serwer gry (`game core`)**: ~1.05 GiB RAM
- **Baza danych (`MariaDB`)**: ~154 MiB RAM
- **Panel Webowy Live Map**: ~383 MiB RAM
- Całość bez problemu działa lokalnie w tle na maszynie deweloperskiej.

---

## 🚀 Szybki start (Quickstart)

### 1. Przygotowanie plików

Przygotuj lokalnie zgodne archiwum serwera r40250. Opcjonalnie przygotuj także archiwum natywnego klienta Windows, najlepiej z dokładnie tego samego wydania. Sama etykieta „r40250” nie gwarantuje zgodności protokołu i plików proto. Żaden z tych plików nie może być publikowany w tym repozytorium.

### 2. Klonowanie i instalacja (Windows)
```powershell
git clone https://github.com/TieruYT/metin2-playerbots.git
Set-Location .\metin2-playerbots
& .\installer\install.ps1 `
    -Archive 'C:\ścieżka\Reference_Server.zip' `
    -ClientArchive 'C:\ścieżka\Reference_Client.zip' `
    -NoWebClient
```

Jeśli masz już skonfigurowanego klienta, użyj zamiast `-ClientArchive` przełącznika `-NoClient`.

### 3. Uruchomienie serwera po instalacji
```powershell
Set-Location "$env:USERPROFILE\Metin2Server"
docker compose up -d
```

### 4. Wejście do gry
Skonfiguruj klienta z tego samego kompatybilnego zestawu r40250 na adres `127.0.0.1` (port Auth `11000`, porty gry `13000–13002`) i ciesz się tętniącym życiem światem w Chunjo!

👉 **Szczegółowy przewodnik instalacji, konfiguracji `.env` i klienta znajdziesz w: [docs/INSTALL.md](docs/INSTALL.md)**

---

## 🗄️ Dostęp do bazy danych (Navicat, HeidiSQL, DBeaver)

Baza serwera to MariaDB w kontenerze, wystawiona **tylko na tym komputerze**
(`127.0.0.1`, port `3306` — albo inny, jeśli w `.env` ustawiono `M2_DB_PUBLISH_PORT`).
Nowe połączenie w kliencie bazy: typ MySQL/MariaDB, host `127.0.0.1`, port `3306`.

| Konto | Do czego | Hasło |
|---|---|---|
| `root` | wszystko | `M2_DB_ROOT_PASSWORD` w `linux-port\docker\.env` |
| `metin2` | tylko bazy gry (`account`, `player`, `log`, `common`, `hotbackup`) | `M2_DB_PASSWORD` w tym samym pliku |

Najszybciej: w launcherze GUI przycisk **DANE DO BAZY (NAVICAT)** pokazuje
host, port i oba hasła w polach do skopiowania (w konsoli: akcja `DbAccess`,
pozycja 16 menu). Hasła są losowane przy pierwszym uruchomieniu i nie ma
żadnego „domyślnego” — nie wklejaj ich na Discordzie.

Jeśli klient odpowiada `1045 - Access denied for user 'root'@'172.18.0.1'`,
baza została zainicjalizowana pod innym hasłem niż to, które jest teraz w `.env`.
Kliknij **NAPRAW DOSTĘP DO BAZY** (akcja `RepairDb`): zatrzymuje serwer i
ustawia konta `metin2` i `root` na hasła z `.env`; postacie, przedmioty i boty
zostają nietknięte. Potem GRAJ i zaloguj się jeszcze raz.

## 🎮 Komendy w grze (GM Commands)

Zarządzanie botami bezpośrednio z poziomu czatu w grze (dla konta GM / Administratora):

| Komenda | Uprawnienia | Opis | Przykład |
|---|---|---|---|
| `/bot_spawn <id> <królestwo: 1-3>` | GM | Ręczny spawn konkretnego bota o danym ID (`1` = Shinsoo, `2` = Chunjo, `3` = Jinno). | `/bot_spawn 4 2` |
| `/bot_despawn <id>` | GM | Usunięcie / wylogowanie bota ze świata. | `/bot_despawn 4` |
| `/bot_spawn_many <start_id> <ilość> <królestwo>` | GM | Masowe zespawnowanie grupy botów. | `/bot_spawn_many 4 350 2` |
| `/bot_despawn_many <start_id> <ilość>` | GM | Masowe wylogowanie grupy botów. | `/bot_despawn_many 4 350` |
| `/bot_rank` | Wszyscy | Wyświetla na czacie aktualny ranking poziomów aktywnych botów. | `/bot_rank` |

---

## 🗺️ Roadmapa rozwoju

- [x] **Faza 1**: Pełne animacje wszystkich klas, łucznicy z pociskami, siatka 2D NavGrid (A*), ulepszanie u Kowala i 32 huby expienia w Chunjo.
- [x] **Faza 2A**: Przejścia M1/M2/M3, expienie strefowe, Łatwy Loch Małp i rzeczywiste wyprawy po Medale Konne.
- [ ] **Faza 2B**: Dolina Orków, Pustynia oraz wyprawy na **Wieżę Demonów (DT)**.
- [ ] **Faza 3**: Czytanie Ksiąg Umiejętności (KU) i Kamieni Duchowych (KD), zaawansowane buildy skilli.
- [x] **Faza 4A**: Podstawowe misje Biologa i pierwszy etap konia oparty na prawdziwym dropie Medali Konnych.
- [ ] **Faza 4B**: Zęby Orka i późniejsze misje Biologa oraz koń bojowy i militarny.
- [ ] **Faza 5**: Aktywności poboczne: łowienie ryb, kilof i wydobywanie rud z żył alchemii.
- [ ] **Faza 6**: Prywatne tobołki/sklepy botów w miastach, handel między botami i dynamiczna wycena przedmiotów.

---

## 📚 Dokumentacja projektu

Szczegółowe informacje podzielone na dedykowane poradniki:

- 📖 **[Instalacja i Konfiguracja (docs/INSTALL.md)](docs/INSTALL.md)** – Docker, WSL2, Linux, `.env`, podłączanie klienta.
- 💻 **[Przewodnik Deweloperski (docs/DEVELOPMENT.md)](docs/DEVELOPMENT.md)** – Szybka kompilacja C++ w 8s (`fast-game-build`), debugowanie i logi AI.
- 🧩 **[Architektura i refaktoryzacja (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md)** – granice modułów oraz bezpieczny plan dzielenia AI na testowalne części.
- 🧾 **[Pochodzenie i atrybucja (docs/ATTRIBUTION.md)](docs/ATTRIBUTION.md)** – historia forka, granice licencji i status WebClienta.

---

## 🤝 Podziękowania i Credits

- **AzzlackSyndicate** — autor pierwotnej bazy linuksowego portu, instalatorów i panelu. Repozytorium źródłowe jest obecnie prywatne; zachowujemy historię Git i pełną atrybucję.
- [DadsMmoLab/dads-mmo-lab](https://github.com/DadsMmoLab/dads-mmo-lab) — Inspiracja badawcza dla autonomicznych agentów w grach MMO.
- Społeczność badaczy i entuzjastów platformy Metin2.
