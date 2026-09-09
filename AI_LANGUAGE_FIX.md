# Playerbot dil duzeltmesi: upstream pull sonrasi kontrol

Bu not, upstream'den merge/pull sonrasi playerbot mesajlarinin tekrar Lehceye
donmesini engellemek icindir. Bir AI, dil sorunu bildirildiginde once bu dosyayi
okumali; sorunu sifirdan aramamalidir.

## Sorunun kok nedeni

Playerbot metinleri tek bir kaynaktan gelmiyor:

1. Bot overhead/status metinleri `playerbot_llm_status.h` icinde uretilir.
2. `FormatPlayerBotText()` ceviri anahtarlarini
   `playerbot_language.h` icindeki Turkce karsiliklara cevirir.
3. Private shop/pazar basliklari status kodundan bagimsiz olarak
   `playerbot_town.h` icindeki sabit dizi ve prefix'lerden uretilir.
4. Chat/trade cevaplari `playerbot_llm_chat_trade.h` icinden gelir.

Bu nedenle sadece `playerbot_language.h` veya status dosyasini duzeltmek yeterli
degildir. Son gorulen hata, bot statuslerinin Turkce olmasina ragmen pazar
basliklarinin `playerbot_town.h` icindeki Lehce sabitlerden gelmesiydi.

## Kontrol edilecek dosyalar

Asagidaki dosyalar fork overlay'idir ve upstream merge sonrasi mutlaka kontrol
edilmelidir:

- `linux-port/overlays/playerbot/src/game/src/playerbot_language.h`
- `linux-port/overlays/playerbot/src/game/src/playerbot_llm_status.h`
- `linux-port/overlays/playerbot/src/game/src/playerbot_llm_chat_trade.h`
- `linux-port/overlays/playerbot/src/game/src/playerbot_town.h`
- `linux-port/overlays/playerbot/src/game/src/playerbot_status.h`
- `linux-port/overlays/playerbot/src/game/src/playerbot_chat_trade.h`
- `linux-port/overlays/playerbot/src/game/src/playerbot_manager.cpp`

`playerbot_status.h` ve `playerbot_chat_trade.h` upstream seam dosyalari olarak
ince tutulmalidir. Ozel mantik wrapper'lara degil, `playerbot_llm_*.h`
dosyalarina ait olmalidir.

## Upstream pull sonrasi uygulanacak adimlar

1. `git pull` veya upstream merge sonrasinda yukaridaki dosyalarda conflict,
   overwrite veya Lehce sabit metin olup olmadigini kontrol et.
2. Status ve chat/trade tarafinda kullaniciya giden her metnin
   `FormatPlayerBotText()` veya Turkce bir sabit uzerinden geldigini dogrula.
3. `playerbot_town.h` icinde ozellikle su gruplari kontrol et:
   - `s_apszPrefixes`
   - `s_apszBookShops`
   - `s_apszMaterialShops`
   - `s_apszMarketCries`
   - `pszPrefix`
   - shop sign icindeki `snprintf()` sabitleri
4. Bu dizilerde `Sprzedam`, `Kupie`, `Ksiegi`, `Zobacz`, `Tanio`,
   `Wyprzedaz`, `Okazja`, `Czego szukasz` gibi Lehce metinler kalmamali.
   Bunlar ceviri anahtari olarak degil, dogrudan oyuncuya giden pazar
   basliklaridir; Turkce karsiliklari dogrudan burada tutulabilir.
5. `playerbot_language.h` icindeki Lehce kelimeler genellikle **anahtar** olarak
   bulunur. Anahtari silme; `FormatPlayerBotText()` bu eski upstream metnini
   anahtar olarak alir. Degistirilmesi gereken kisim sagdaki Turkce return
   degeridir.
6. Yeni veya upstream'den gelen player-visible bir metni Lehce ekleme. Yeni
   metin icin ASCII Turkce kullan: `savasiyorum`, `pazar kuruyorum`,
   `alisveris`, `gelistirme`, `olum`, `kalan`.
7. Degisen overlay dosyalarini staged build context'e kopyala veya resmi
   `prepare-context.sh` akisini kullan. Sadece kaynak dosyasini degistirip eski
   staged dosyayi derleme; bu durumda Docker basarili olsa bile eski dil binary'e
   girebilir.

## Hizli arama

Repo kokunden:

```text
rg "Sprzedam|Kupie|Ksiegi|Zobacz|Tanio|Wyprzedaz|Okazja|Czego szukasz" linux-port/overlays/playerbot/src/game/src
```

Sonuclarin yorum satirlarinda veya ceviri anahtari olarak bulunmasi normaldir.
Ancak `return`, `snprintf`, shop prefix/template/cry dizileri veya oyuncuya
gonderilen chat metni icinde dogrudan cikiyorsa Turkceye cevrilmelidir.

## Dogrulama

1. Degisen tum `playerbot_*` dosyalarini staged game source'a kopyala.
2. `docker compose build --no-cache game` calistir.
3. `docker compose up -d --force-recreate game` ile game servisini yeniden
   olustur.
4. Game servisinin `healthy` oldugunu kontrol et.
5. Canli status dosyasinda Turkce cikti ara:

```text
docker exec <game-container> tail -n 20 /opt/metin2/var/channel1/game1/playerbot_status.tsv
```

Beklenen ornekler:

- `Pazar kuruyorum`
- `Balik tutuyorum - oltayi bekliyorum`
- `... pesindeyim`

6. Pazar tabelasi icin binary veya oyundaki yeni acilmis bir shop kontrol
   edilmeli. Eski acik shop tabelalari client tarafinda cache'lenebilir; test
   icin client'i yeniden baglat ve yeni shop acilmasini bekle.

## Onemli ayrimlar

- Panel dili ile oyun dili ayni ayar degildir. Paneldeki PL/TR secimi, game
  server'in playerbot metinlerini degistirmez.
- Binary icinde `Sprzedam`, `Kupie` gibi Lehce kelimelerin bulunmasi tek basina
  hata kaniti degildir; bunlar `playerbot_language.h` icinde eski ceviri
  **anahtarlari** olarak bulunabilir. Gercek kontrol, canli status/shop
  cikisinin ne yazdigidir.
- Bu duzeltme `mmo-llm-adapter/` Python kodunu degistirmez. Sorun game
  overlay'inin sabit player-visible metinlerindedir.
