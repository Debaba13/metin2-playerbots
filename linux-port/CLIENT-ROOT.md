# Klient (`linux-port/client-root/`): pliki, ktore podmieniamy w `pack/root.epk`

> Ten opis lezy obok katalogu, a nie w nim. `tools/eterpack.py repack`
> bierze *kazdy* plik z katalogu podmian, wiec README lezacy w srodku
> wjezdzal do paczki klienta jako `readme.md`. Teraz repack odmawia
> dokladania plikow, ktorych archiwum nie ma, ale opis i tak nie ma tam
> czego szukac.


Klient r40250 trzyma skrypty w `pack/root.epk` (indeks w `root.eix`). Nic na
maszynie gracza nie dopisze pliku do tego archiwum, więc zmiana po stronie
klienta jedzie jako gotowe `root.eix`/`root.epk` w paczce klienta (składnik
`client` w `update-manifest.json`, nakładany przez launcher na folder klienta).

`linux-port/client-root/` to źródła tych plików, które różnią się od stockowego klienta — dziś
cztery pliki panelu GM na F9 i przycisków EQ/Sprawdź (autor: OskarPWA):
`game.py`, `interfacemodule.py`, `uitarget.py`, `constinfo.py`.

Przepakowanie (potrzebuje python-lzo; obraz `python:3.12-slim` + `liblzo2-dev`):

    python tools/eterpack.py repack <klient>/pack/root builds/clientpack/new/root linux-port/client-root

Potem `tools/New-M2UpdatePackage.ps1 -Type client` z listą
`launcher/client-update-files.txt` i wpis `client` w manifeście.
