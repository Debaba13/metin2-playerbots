# Çeviri Rehberi

Bu dosya, bu fork'ta Türkçe çevirinin **nerede**, **nasıl** çalıştığını ve
**hangi terimlerin** hangi Türkçe karşılığa denk geldiğini açıklıyor. Amaç:
biri (siz ya da ben) yeni bir upstream güncellemesi çektiğinde ya da yeni bir
metin eklediğinde, doğru yere doğru şekilde eklemek — ve `PLAYER_SKILLS`
gibi birbirine bağlı dosyalardan birini unutup diğerini güncelleyerek panel
ile oyunu birbirinden koparmamak.

Bu depoda çeviri **tek bir sistem değil, dört ayrı katman**. Biri diğerini
etkilemez; biri bozulursa diğerleri çalışmaya devam eder. Bir hata ararken
önce hangi katmanda olduğunuzu bulun.

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Oyun sunucusunun kendi dili   (m2-lang, GAME_LANGS)           │
│    — NPC adları, eşya adları, quest metinleri, istemci arayüzü   │
├─────────────────────────────────────────────────────────────────┤
│ 2. Bot yapay zekâsının konuşması (C++ çekirdek, playerbot_*.h)   │
│    — "Ne yapıyorum" durum metni, stragan tabelaları              │
├─────────────────────────────────────────────────────────────────┤
│ 3. Klasik yönetici paneli        (files/admin_panel.py)          │
│    — Çok dilli: pl/en/de/tr arasında seçim yapılabilir           │
├─────────────────────────────────────────────────────────────────┤
│ 4. Seban paneli                  (linux-port/docker/seban-panel) │
│    — Tek dilli: doğrudan Türkçe, dil seçici yok                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Katman 1 — Oyunun kendi dili (bu fork'un işi değil)

`m2-lang` (bkz. CLAUDE.md, "The game's language lives in the image") oyun
sunucusunun **kendi** çok dilli sistemi: `share/conf/item_names.txt`,
`share/conf/mob_names.txt`, `share/locale/*/translate.lua`,
`share/locale/*/locale_string.txt`. GM paneli veya klasik panelin dil
sayfası bunu tetikleyip `RATES`/`cmd_apply` üzerinden konteynerde değiştirir.
`GAME_LANGS` listesinde ("tr" dahil, `en`, `de`, `pl`, ... — bkz.
`files/admin_panel.py:1228`) zaten Türkçe seçeneği vardı, bu fork'un bir
katkısı değil. Bu katman **istemcinin gösterdiği metni** (eşya adı, NPC
konuşması, görev metni) değiştirir — botların ne yaptığını anlatan metni
değil. Karıştırmayın: bir oyuncu "oyun İngilizce görünüyor" derse burası,
"botun üstündeki yazı Lehçe" derse Katman 2.

## Katman 2 — Bot yapay zekâsının konuşması (C++ çekirdek)

Botların üstünde görünen "ne yapıyorum" metni ve stragan tabelaları
`linux-port/overlays/playerbot/src/game/src/` altındaki C++ kaynağından
gelir. İki alt parça var:

### 2a. `playerbot_language.h` — anahtar → Türkçe çeviri tablosu

Bu, bütün sistemin **kalbi**. Mantığı şöyle: geri kalan bütün
`playerbot_*.h`/`.cpp` dosyalarında bir durum metni gerektiğinde kod hâlâ
**orijinal Lehçe anahtarı** çağırır:

```cpp
PlayerBotText("regeneracja")                 // -> "can basiyorum"
FormatPlayerBotText(out, size, "", "Walcze z %s", potvor_adi)  // -> "%s ile savasiyorum"
```

`PlayerBotText(anahtar)` fonksiyonu (`playerbot_language.h:12`), bu Lehçe
anahtarı `strcmp` ile tarayıp Türkçe karşılığını döndürüyor. Eşleşme yoksa
**anahtarın kendisini (yani Lehçe metni) olduğu gibi döndürür** — bu, yeni
bir çağrı eklenip buraya karşılığı eklenmezse ne olacağının cevabı: metin
sessizce Lehçe kalır, hata vermez, log de patlamaz.

**Neden anahtarlar hâlâ Lehçe?** Çünkü upstream (orijinal proje) hâlâ Lehçe
yazıyor ve `prepare-context.sh` bu overlay dosyasını her upstream
senkronundan sonra yeniden uyguluyor (bkz. dosyanın en üstündeki yorum). Call
site'ları (yani `PlayerBotText("...")` çağrılarının kendisini) Türkçeye
çevirmek, her upstream merge'ünde conflict demek olurdu. Bunun yerine sadece
bu tek dosyadaki çeviri tablosunu güncel tutuyoruz — upstream'in kendi
Lehçe metnini değiştirmesine bile dayanıklı, çünkü `strcmp` eşleşmezse
sadece o satır çevrilmemiş kalır (kırılmaz, sadece geçici olarak Lehçe
görünür).

**Yeni bir upstream senkronundan sonra ne yapmalı:** `playerbot_manager.cpp`
ve diğer fragment'larda yeni bir `PlayerBotText("...")` ya da
`FormatPlayerBotText(..., "...", ...)` çağrısı arayın
(`grep -rn 'PlayerBotText\|FormatPlayerBotText' linux-port/overlays/playerbot/src/game/src/`),
anahtarı `playerbot_language.h`'daki listede arayın; yoksa yeni bir
`if (strcmp(key, "<orijinal Lehçe metin>") == 0) return "<Türkçe karşılık>";`
satırı ekleyin. `%s`/`%d`/`%u` gibi biçim belirteçlerinin sayısı ve
sırası **birebir aynı kalmalı** (aksi halde `vsnprintf` çöker ya da anlamsız
sayı basar).

Ayrıca `GetPlayerBotTownNameTurkish()` fonksiyonu var — harita indeksinden
şehir adına ("Joan"/"Bokjung"/"kent") çeviren küçük bir yardımcı, aynı
dosyada.

### 2b. Doğrudan Türkçe yazılmış sabitler

Bazı dosyalarda anahtar-tablo dolayı yok — metin doğrudan Türkçe olarak
kod içinde yazılı:

- **`playerbot_shop_signs.h`** (277 satır) — bir bot stragan açtığında
  rastgele seçtiği ~100 tabela metni. Kategoriye göre diziler:
  `s_apszSignUniversal`, `s_apszSignBooks`, `s_apszSignFish`,
  `s_apszSignGear`, `s_apszSignMaterials`, `s_apszSignMedals`,
  `s_apszSignScrolls`, `s_apszSignStones`. Yeni bir kategori/tabela eklemek
  isterseniz doğrudan buraya Türkçe string ekleyin — bir anahtar tablosu
  yok, çünkü bunlar zaten rastgele seçilen dekoratif metin, upstream'de
  karşılığı yok.
- **`playerbot_types.h`** içindeki `GetPlayerBotShopReasonName()`
  (satır ~2099) gibi `switch`/`case` biçimindeki sabit çeviriler — stragan
  açma **sebebini** (loglama ve panel için) döndürür:

  | Sebep (enum) | Türkçe |
  |---|---|
  | `PLAYERBOT_SHOP_REASON_MERCHANT` | satıcı |
  | `PLAYERBOT_SHOP_REASON_POOR` | iksir için yang yok |
  | `PLAYERBOT_SHOP_REASON_BAG_FULL` | dolu çanta |
  | `PLAYERBOT_SHOP_REASON_DROPPER_PRESSURE` | dropper, dolu çanta |
  | `PLAYERBOT_SHOP_REASON_BOOKS` | fazla kitap |
  | `PLAYERBOT_SHOP_REASON_DROPPER_ROLL` | dropper |
  | `PLAYERBOT_SHOP_REASON_ROLL` | rastgele |
  | `PLAYERBOT_SHOP_REASON_SPARE` | gereksiz kopya |

**Önemli kısıtlama — ASCII zorunlu:** CLAUDE.md'nin kuralı hâlâ geçerli:
*"Player-visible bot strings are ... ASCII-only (no diacritics)."* Motorun
eski sohbet yolu ve stok verisi CP1250 olduğu için ğ/ş/ı/ç/ö/ü gibi Türkçe
özel harfler **kullanılmaz** — `playerbot_language.h`'a bakarsanız hepsi
`g/s/i/c/o/u` ile yazılmış (`"Balik tutuyorum"`, `"esya basiyorum"` gibi).
Bu, panellerdeki Türkçe metinden (orada özel harfler serbest) farklı bir
kural — karıştırmayın.

### 2c. `playerbot_config.h` — operatörün `playerbot_item_policy.tsv` dosyası

Bir operatörün `playerbot_item_policy.tsv` dosyasına yazabileceği
anahtar kelimeler `ParsePlayerBotItemPolicyWord()` fonksiyonunda
tanımlı — hem Lehçe hem Türkçe eş anlamlılar kabul ediliyor (İngilizce
zaten hep vardı):

| Politika | İngilizce | Lehçe | Türkçe |
|---|---|---|---|
| tut | `keep` | `zostaw` | `sakla` |
| stragana koy | `stall` | `stragan` | `tezgah` |
| satıcıya sat | `merchant` | `handlarz` | `satici` |
| at | `drop` | `wyrzuc` | `birak` |

Bu tablo **iki yerde** aynı anda tutuluyor ve ikisi de güncel kalmalı:
`linux-port/overlays/playerbot/src/game/src/playerbot_config.h`
(`ParsePlayerBotItemPolicyWord`, C++ tarafı — botun gerçekte okuduğu) ve
`files/admin_panel.py:1069` (`AI_ITEM_POLICY_WORDS`, sadece panelin
`/ai/items` sayfasındaki **doğrulama** — kullanıcı geçersiz bir kelime
yazarsa panel reddediyor). Birini güncelleyip diğerini unutursanız panel
botun kabul ettiği bir kelimeyi "geçersiz" diye reddedebilir, ya da tam
tersi.

---

## Katman 3 — Klasik yönetici paneli (`files/admin_panel.py`)

Bu panelin **gerçek** çok dilli (i18n) sistemi var: pl/en/de/tr arasında
üstteki dil değiştiriciden seçim yapılabiliyor. **~12800 satırlık dosyada
~446 anahtar** bu sistemden geçiyor; geri kalan kısa etiketler ayrı küçük
sözlüklerde.

### Nasıl çalışıyor

```python
def lang():
    # Varsayılan Lehçe ("pl"). Tarayıcının Accept-Language'ı SORULMUYOR —
    # bilinçli bir tercih (bkz. docstring, files/admin_panel.py:3346):
    # tarayıcı dili Lehçe olmayan biri otomatik İngilizce görürdü, ki panel
    # yarı çevrili olduğu için bu iki dilin de kötüsünü verirdi.
    # Kullanıcının üstteki menüden seçtiği dil bir çerezde (m2lang) kalıcı olarak hatırlanır.
    ...

def t(key):
    return T.get(key, {}).get(lang(), T.get(key, {}).get("en", key))
```

`T` sözlüğü `files/admin_panel.py:2462`'de başlıyor: her anahtar
`{"pl":..., "en":..., "de":..., "tr":...}` biçiminde dört dil taşıyor.
Şablonlarda ve Python kodunda `t("acc_title")` gibi çağrılıyor. **Yeni bir
kullanıcı-görünür metin eklerseniz** buraya yeni bir anahtar eklemek en
doğru yol — dört dili de doldurun (en azından `en` ve `tr`'yi; `de` genelde
eksik bırakılabiliyor, `t()` böyle durumda `en`'e düşüyor, ama `tr` asla
`en`'e düşmüyor — eksik `tr` demek Türkçe seçen kullanıcı İngilizce görür).

**Varsayılan dil hâlâ Lehçe'dir — Türkçe otomatik değil.** Bir aile üyesi
paneli açtığında üstteki dil menüsünden "Türkçe" seçmesi lazım; seçim bir
çerezle kalıcı olarak hatırlanır.

### `T` dışındaki sözlük aileleri

`T`'nin kapsamadığı, daha büyük/yapılı veri kalıpları için ayrı üçlü/dörtlü
sözlük aileleri var — hepsi aynı desende: temel isim (genelde Lehçe/varsayılan),
`_EN` veya `_PL` soneki, `_TR` soneki:

| Ne | Dosya:satır | Yapı |
|---|---|---|
| Meslek beceri ağaçları | `PLAYER_SKILLS` / `_EN` / `_TR` (satır 537, 560, 583) | job/group çiftine göre 8 giriş, her biri beceri listesi |
| Beceri kitabı adları (düz tablo) | `SKILL_ID_NAMES` / `_PL` / `_TR` (satır 223-225) | `PLAYER_SKILLS_*`'ten otomatik "düzleştirilerek" dolduruluyor (satır ~608-616) — **elle doldurmayın**, `PLAYER_SKILLS_TR`'yi güncelleyin, düzleştirme kodu gerisini halleder |
| Bot kişiliği / hedefi / eylemi | `BOT_PERSONALITY_LABELS`, `BOT_AMBITION_LABELS`, `BOT_GOAL_LABELS`, `BOT_ACTION_LABELS` (satır 302-395) | her biri `{"pl":{...}, "en":{...}, "tr":{...}}`, id→etiket |
| Canlı harita sayfası metni | `MAP_I18N` (satır 5037) | `{"pl":{...400+ anahtar...}, "en":{...}, "tr":{...}}` — sayfanın tamamı tek blokta |
| Bonus/istatistik açıklamaları | JS içindeki `APPLY_META` (satır ~6130) | `{id: {pl:.., en:.., tr:.., f:"percent"/"flat"/"boolean"}}`, ~120 giriş |
| Ekipman geçmişi olay etiketleri | `GEAR_HISTORY_HOWS` (satır 7229) | log.log'daki `how` sütunundan panel etiketine |
| Sınıf/cinsiyet adları | satır 5107-5109 civarı | `{"en":{0:"Warrior (M)",...}, "tr":{0:"Savaşçı (E)",...}}` |

### `localize_playerbot_status()` — neden asimetrik (satır 470)

Bu fonksiyon botun üstündeki durum metnini panelin seçili diline çevirir.
Ama **Katman 2'de bot artık zaten Türkçe konuşuyor** (bkz. yukarısı), bu da
şu tuhaf ama doğru davranışı doğuruyor:

- Panel dili **"tr"** ise: botun C++'tan gelen ham metnini **olduğu gibi**
  gösterir (zaten Türkçe, çevirmeye gerek yok).
- Panel dili **"pl"** ise: botun metni artık Lehçe olmadığı için gösterecek
  bir şey yok — bunun yerine sabit `BOT_ACTION_LABELS["pl"]` etiketine
  düşer (yani "Walcze z Kaplumbağa" gibi ayrıntılı bir cümle değil, sadece
  "Walczy" gibi genel bir eylem adı görünür).
- Panel dili **"en"/"de"** ise: `_PLAYERBOT_STATUS_PATTERNS_EN` adlı bir
  regex listesiyle botun Türkçe metnini İngilizceye çevirmeye **çalışır**
  (satır ~487) — tam kapsamlı değildir, eşleşmeyen desenler yine sabit
  eyleme düşer.

Bunu **task #25**'te bulduk: fonksiyon eskiden "bot metni Lehçedir"
varsayıyordu ve "pl" dilinde botun ham metnini gösteriyordu — ama metin
artık Türkçe olduğu için Lehçe okuyucuya anlamsız geliyordu. Eğer
`playerbot_language.h`'a yeni bir cümle kalıbı eklerseniz ve bu cümlenin
İngilizce panelde de düzgün görünmesini istiyorsanız, `_PLAYERBOT_STATUS_PATTERNS_EN`'e
karşılık gelen bir regex eklemeyi unutmayın — yoksa İngilizce/Almanca panel
kullanıcıları o cümle için de sadece genel eylem adını görür.

---

## Katman 4 — Seban paneli (`linux-port/docker/seban-panel/`)

Bu panelin **hiç i18n sistemi yok**. `T` sözlüğü, `lang()`, `t()` fonksiyonu
falan yok — 13 Eylül 2026'da bilinçli bir kararla (kullanıcı seçimi: "Doğrudan
Türkçeye çevir") bütün metin **doğrudan Türkçe olarak** koda, şablonlara ve
JS dosyalarına yazıldı. Dil seçici **yok** — bu panel artık sadece Türkçe.

Bunun admin_panel.py'den farkı: yeni bir dil eklemek isterseniz (örn. tekrar
İngilizce desteği), önce bir `T`+`lang()` sistemi **kurmanız** gerekir —
şu an string'ler doğrudan Türkçe yazılı, ayrı bir sözlükten gelmiyor.

### Sabitler (`app.py`)

| Ne | Satır | İçerik |
|---|---|---|
| `MAP_NAMES` | 33 | harita indeksi → Türkçe ad (tam liste aşağıda) |
| `CLASS_PROFILES` | 115 | job id → {isim, cinsiyet, portre dosyası} |
| `BOT_PERSONALITIES` | 147 | kişilik id → Türkçe etiket |
| `BOT_AMBITIONS` | 148 | hedef id → Türkçe etiket |
| `BOT_GOALS` | 149 | uzun vadeli hedef id → Türkçe etiket |
| `BOT_ACTIONS` | 150 | eylem id → Türkçe etiket (18 giriş, 0-17) |
| `APPLY_LABELS` | 161 | bonus/apply id → (isim, birim) — 117 giriş |
| `JOB_NAMES` | 195 | `("Savaşçı","Ninja","Sura","Şaman")` |
| `SKILLS` | 196 | job/group çiftine göre beceri listesi — `admin_panel.py`'nin `PLAYER_SKILLS_TR`'siyle **aynı çeviriler**, birebir kopyalandı, tutarlılık için |
| `honor_rank()` | 404 | onur puanı → (başlık, css sınıfı) — tam liste aşağıda |
| `is_stationary_activity()` | — | durum metnini `("balik","olta","fishing")` ile eşleştirir — Katman 2'nin ürettiği Türkçe metni okur |

### Şablonlar ve JS

19 Jinja şablonu (`templates/*.html`) ve 3 JS dosyası
(`static/heatmap.js`, `static/news-feed.js`, `static/live-widget.js`) —
hepsinde metin doğrudan HTML/JS içine Türkçe yazılı, ayrı bir sözlük yok.
Yeni bir şablon eklerseniz doğrudan Türkçe yazın; başka bir dile
tercüme etme ihtiyacı yoksa ekstra bir mekanizma kurmaya gerek yok.

`item_grants.py` (toplu eşya verme alt sistemi) da aynı şekilde: `TERMINAL`/
`LABELS` sözlükleri artık doğrudan Türkçe.

`gm_commands.txt` — GM komutlarının düz metin açıklaması, olduğu gibi
Türkçeye çevrildi (komut sözdizimi değişmedi, sadece açıklamalar).

---

## Ortak sözlük (glossary) — iki panel arasında tutarlılık

Aşağıdaki terimler **hem** `admin_panel.py` **hem** `seban-panel`'de aynı
Türkçe karşılığı kullanır. Yeni bir çeviri eklerken bu listeye bakıp aynı
kelimeyi kullanın — iki panel farklı kelime kullanırsa bir oyuncu/operatör
aynı şeyi iki farklı isimle görür ve kafası karışır.

### Harita adları

| İndeks | Türkçe |
|---|---|
| 1 | Shinsoo M1 — Yongan |
| 3 | Shinsoo M2 — Jayang |
| 4 | Shinsoo Klan Toprakları |
| 5 | Shinsoo Maymun Zindanı |
| 21 | Chunjo M1 — Joan |
| 23 | Chunjo M2 — Bokjung |
| 24 | Chunjo Klan Toprakları |
| 25 | Kolay Maymun Zindanı |
| 41 | Jinno M1 — Pyongmoo |
| 43 | Jinno M2 — Bakra |
| 44 | Jinno Klan Toprakları |
| 45 | Jinno Maymun Zindanı |
| 61 | Sohan Dağı |
| 63 | Yongbi Çölü |
| 64 | Ork Vadisi |
| 65 | Hwang Tapınağı |
| 71 | Örümcek Zindanı V2 |
| 104 | Örümcek Zindanı V1 |
| 108 | Orta Maymun Zindanı |
| 109 | Zor Maymun Zindanı |

(Not: `21/23/24/25` Chunjo'nun kendi haritaları — CLAUDE.md'nin uyardığı
gibi, **Chunjo'nun koordinatı başka bir krallık için asla doğru değildir**;
harita *adları* ortak ama koordinatlar krallığa özel, bkz. CLAUDE.md "Three
kingdoms" bölümü.)

### Sınıf adları

| Job id | İsim | Cinsiyet |
|---|---|---|
| 0 | Savaşçı | Erkek |
| 4 | Savaşçı | Kadın |
| 1 | Ninja | Kadın |
| 5 | Ninja | Erkek |
| 2 | Sura | Erkek |
| 6 | Sura | Kadın |
| 3 | Şaman | Kadın |
| 7 | Şaman | Erkek |

### Bot kişiliği (`BOT_PERSONALITIES` / `BOT_PERSONALITY_LABELS["tr"]`)

| id | Türkçe |
|---|---|
| 0 | Kararlı Maceracı |
| 1 | Metin Kırıcı |
| 2 | Takım Arkadaşı |
| 3 | Ekipman Ustası / Uzmanı |
| 4 | Dikkatli Toplayıcı |
| 5 | Tüccar |
| 6 | Gezgin |
| 7 | Metin Dropper'ı |
| 8 | M3 Dropper'ı / Silah Dropper'ı |
| 9 | M2 Dropper'ı / Bestial Dropper'ı |
| 10 | Madalya Dropper'ı |

### Bot eylemi (`BOT_ACTIONS` / `BOT_ACTION_LABELS["tr"]`, id 0-13 ortak, 14-17 sadece seban-panel'de — seban-panel'in eylem listesi daha geniş çünkü admin_panel.py bu dört durumu ayrı bir yoldan gösteriyor)

| id | Türkçe |
|---|---|
| 0 | Sonraki Hamleyi Planlıyor |
| 1 | Yolculukta |
| 2 | Savaşıyor |
| 3 | Ganimet Topluyor |
| 4 | İyileşiyor |
| 5 | Meslek Seçiyor |
| 6 | Ticaret Yapıyor |
| 7 | Ekipman Geliştiriyor |
| 8 | Beceri/Yetenek Kitabı Okuyor |
| 9 | Ruh Taşı Takıyor |
| 10 | Grup Topluyor |
| 11 | Biyolog Görevi Yapıyor |
| 12 | Seyis'i Ziyaret Ediyor |
| 13 | Tezgah İşletiyor |
| 14 | Balık Tutuyor *(sadece seban-panel)* |
| 15 | Tezgahlara Bakıyor *(sadece seban-panel)* |
| 16 | Canavar Çekiyor *(sadece seban-panel)* |
| 17 | Şehirde Dinleniyor *(sadece seban-panel)* |

### Onur seviyeleri (`honor_rank()`, seban-panel `app.py:404`)

| Eşik | Türkçe | CSS sınıfı |
|---|---|---|
| 12000+ | Şövalye Ruhlu | knightly |
| 8000+ | Asil | noble |
| 4000+ | İyi | good |
| 1000+ | Dostane | friendly |
| 0+ | Nötr | neutral |
| -3999+ | Saldırgan | aggressive |
| -7999+ | Sahtekar | dishonest |
| -11999+ | Kötü Niyetli | malicious |
| -20000+ | Acımasız | cruel |

**Dikkat:** bu başlıklar aynı zamanda `/player/<pid>` rotasında CSS sınıfına
çevrilmek için elle tutulan bir sözlükte anahtar olarak kullanılıyor
(`character["honor"]["css"] = {"Şövalye Ruhlu": "knightly", ...}`). Bu
tabloyu değiştirirseniz o sözlüğü de **aynı satırda** güncelleyin — bu,
task #38'de bulduğumuz gerçek bir `KeyError` hatasıydı (bkz. aşağıdaki
"Bilinen tuzaklar").

### Eşya politikası kelimeleri

Katman 2c'deki tabloyla aynı: `sakla` / `tezgah` / `satici` / `birak`.

---

## Bilinen tuzaklar (yeni çeviri eklerken tekrar düşmeyin)

Bunların hepsi bu oturumlarda gerçekten yaşandı, tahmini değil:

1. **"Tanımı çevirdim ama okuyanı unuttum" hatası.** Bir sözlüğün
   *tanımını* Türkçeye çevirmek yetmez — o sözlüğün değerini **anahtar**
   olarak kullanan başka bir yer varsa (örn. `honor_rank()`'ın ürettiği
   başlığı CSS sınıfına çeviren sözlük, ya da bir durum metnini regex'le
   arayan kod), o da güncellenmeli. Kontrol yöntemi: çevirdiğiniz her
   sözlük/fonksiyon için `grep -rn` ile **her çağrıldığı yeri** bulun,
   sadece tanımını değil.

2. **"Balık avlama tespiti" hatası (3 kere bulundu).** Bir durum metnini
   substring ile ("łowi", "ryb" gibi Lehçe parçalarla) arayan kod, metin
   kaynağı (Katman 2, `playerbot_language.h`) Türkçeye geçtikten sonra artık
   hiçbir zaman eşleşmiyordu — sessizce ölü kod haline geliyordu. Böyle bir
   substring-eşleştirme kodu görürseniz, aradığı metnin **hâlâ güncel**
   olduğunu (yani Katman 2'nin gerçekte ürettiği Türkçe kelimeyle eşleştiğini)
   doğrulayın: `grep -rn "<aranan_kelime>" linux-port/overlays/playerbot/src/game/src/playerbot_language.h`.

3. **Regex ile toplu dosya düzenleme riski.** `APPLY_LABELS` sözlüğünü
   Türkçeye çevirirken kullanılan bir Python regex'i (`\{(.*?)\n\}`), sözlüğün
   kapanış parantezinin aynı satırda olması yüzünden **45 satırlık alakasız
   kodu sildi** (`POINT_TO_APPLY`, `SKILLS`, `JOB_NAMES` dahil) — ve
   `py_compile` bunu **yakalamadı**, çünkü kalan kod hâlâ sözdizimsel olarak
   geçerliydi. Bunu yakalayan tek şey, script çalışmadan önce ve sonra
   `wc -l dosya.py` ile satır sayısını karşılaştırmaktı. **Kural: büyük bir
   toplu değişiklikten sonra her zaman satır sayısını karşılaştırın**,
   sadece syntax check'e güvenmeyin. Mümkünse regex yerine `Edit` aracının
   tam-metin eşleştirmesini kullanın.

4. **ASCII kuralı sadece Katman 2 için geçerli.** Panellerde (`admin_panel.py`,
   `seban-panel`) Türkçe özel harfler (ğ, ş, ı, İ, ç, ö, ü) serbestçe
   kullanılıyor — UTF-8 şablonlar ve Python kaynağı bunu destekliyor. Ama
   C++ çekirdek tarafında (`playerbot_language.h`, `playerbot_shop_signs.h`,
   `playerbot_types.h`'daki switch/case metinleri) **kesinlikle ASCII-only**
   kalın (g/s/i/c/o/u), yoksa CP1250 sohbet yolu ve eski stok verisiyle
   çakışma riski var (bkz. CLAUDE.md "A staged engine file must stay in the
   engine's own encoding").

5. **İki panelin aynı terimi farklı çevirmesi.** `PLAYER_SKILLS_TR`
   (admin_panel.py) ve `SKILLS` (seban-panel) **birebir aynı Türkçe beceri
   adlarını** taşımalı — biri "Kılıç Aurası" derken diğeri "Aura Kılıcı"
   dememeli. Yeni bir beceri çevirisi eklerken **iki dosyayı da** aynı anda
   güncelleyin ve aynı kelimeyi kullanın.

6. **`SKILL_ID_NAMES*`'i elle doldurmayın.** `admin_panel.py:608-616`'da üç
   döngü `PLAYER_SKILLS_*`'i "düzleştirip" bu tabloları dolduruyor — isim
   eşlemesi birebir değil, dikkat: `PLAYER_SKILLS` (Lehçe/varsayılan) →
   `SKILL_ID_NAMES_PL`, `PLAYER_SKILLS_EN` → `SKILL_ID_NAMES` (soneksiz!),
   `PLAYER_SKILLS_TR` → `SKILL_ID_NAMES_TR`. Yeni bir beceri eklemek
   isterseniz kaynak `PLAYER_SKILLS_*` tablolarını güncelleyin, bu üç döngü
   gerisini kendiliğinden halleder — hedef `SKILL_ID_NAMES*` tablolarına
   elle satır eklerseniz bir sonraki düzleştirme çalıştığında üzerine
   yazılır.

---

## Yeni bir upstream senkronundan sonra kontrol listesi

1. `git diff` ile hangi `playerbot_*.h`/`.cpp` dosyaları değişti, bak.
2. Yeni `PlayerBotText("...")` / `FormatPlayerBotText(...)` çağrısı var mı?
   → `playerbot_language.h`'a karşılığını ekle (Katman 2a).
3. `playerbot_shop_signs.h`'a yeni bir kategori/dizi eklendi mi? → doğrudan
   Türkçe yaz (Katman 2b).
4. `files/admin_panel.py`'de yeni bir `T[...]` anahtarı, yeni bir
   `PLAYER_SKILLS`/`BOT_*_LABELS`/`MAP_I18N`/`GEAR_HISTORY_HOWS` girdisi
   eklendi mi (upstream'in kendi Lehçe/İngilizce eklemesiyle)? → `tr`
   karşılığını ekle, `SKILL_ID_NAMES_TR` gibi otomatik türetilenleri elle
   dokunma.
5. `seban-panel/app.py`'de yeni bir sabit tablo (yeni harita, yeni eylem,
   yeni bonus id) eklendi mi? → doğrudan Türkçe ekle, **yukarıdaki ortak
   sözlükle aynı kelimeyi kullan**.
6. Yeni bir Python/JS dosyası eski Lehçe metin içeren bir substring arıyor
   mu (fishing-detection tuzağı gibi)? → aradığı metnin hâlâ Katman 2'nin
   ürettiğiyle eşleştiğini doğrula.
7. `python3 -m py_compile` + `node --check` + değişen dosyaların `wc -l`
   karşılaştırması + (mümkünse) gerçek şablon render testi.

---

*Bu dosya elle güncellenir; bir kod üretmiyor, sadece nerede ne olduğunu
anlatıyor. Ayrıntılı upstream senkron notları için `UPSTREAM_SYNC_2026-09-12.md`'ye
bakın.*
