# MMO LLM Adapter — Normatif Calisma Sozlesmesi

> Bu dosya, projeye katilan her AI ajani icin guncel ve normatif referanstir.
> Oturuma baslamadan once tamamini okuyun. Tarihsel kararlar ve gunluk
> gelismeler [CHANGELOG](./MMO_LLM_ADAPTER_CHANGELOG.md) dosyasindadir; bu
> dosyaya gunluk not eklemeyin.

**Kapsam:** `mmo-llm-adapter/` ve onun Metin2 game adapter seam'leri
**Guncel durum:** Adapter, C++ koprusu, Turkce etkilesim, yaklasma ve
deterministik trade akisi canli olarak dogrulandi. Native PlayerBots temel
otoritedir; LLM yalnizca sosyal/niyet katmanidir.
**Son normatif gozden gecirme:** 2026-09-10

## 1. Okuma talimati ve net vizyon

Bu sozlesme su sirayla kullanilir:

1. Kapsami ve dosya sahipligini belirle.
2. Upstream seam'i ve ilgili engine/API varsayimlarini kontrol et.
3. Degisikligi uygula; hedefli test ve dogrulamayi calistir.
4. Teslim kaydini bu sozlesmenin formatinda ve tarihsel ayrintilari
   [CHANGELOG](./MMO_LLM_ADAPTER_CHANGELOG.md) icinde tut.

Vizyon: Metin2 PlayerBots'un deterministik reflekslerini bozmadan, herhangi
bir PlayerBots-benzeri oyuna takilabilen, oyun-agnostik ve LLM-agnostik yerel
bir sosyal zihin katmani kurmak.

- Normal exp, fishing, quest, combat, follow, buff, ekonomi ve market akisi
  PlayerBots C++ kontrolundedir.
- Fisilti, yakin konusma, parti daveti/komutu ve trade gibi oyuncu etkilesimi
  LLM katmanini tetikler.
- Her etkilesim 120 saniyelik lease'i yeniler; parti liderligi aktifse lease
  sona ermez. Sure dolunca bot nazikce native rutine doner.
- Ollama, LM Studio, vLLM ve LocalAI degistirilebilir provider'lardir.
- Baslangic dilleri `tr` ve `en`dir; yeni dil, locale dosyasi ve tek config
  satiriyla eklenir.
- 300-800 bot olceginde oyuncuya en yakin 30-50 bot attention bubble'da,
  digerleri native tick'te, istege bagli 60 saniyelik macro pulse ile
  calisir.

## 2. Degismez mimari ilkeler

### 2.1. Refleks ve zihin

```text
AUTONOMOUS (PlayerBots C++)
  normal rutin; LLM cagrisi yok
        |
        | whisper / yakin konusma / parti / trade
        v
LLM_OVERRIDE
  120s lease; sohbet ve whitelist tool-call
        |
        | lease doldu ve parti liderligi yok
        v
RESUME_ROUTINE
  farewell veya sonraki is; PlanPlayerBotLongTermGoal'a donus
```

LLM hareket, savas veya exchange'i dogrudan yurutmez. Yalnizca whitelist
edilmis niyeti/tool cagrisini uretir; deterministik native fonksiyonlar
uygular.

### 2.2. Katmanlar

```text
Game Server (Metin2 r40250, C++)
  <-> JSON over HTTP, localhost, non-blocking worker
MMO LLM Adapter (Python)
  1. Pluggable game adapters (Metin2Bridge, gelecek diger bridge'ler)
  2. Oyun-agnostik runtime (state, memory, bubble, queue, tools)
  3. Pluggable OpenAI-uyumlu/native LLM providers
```

Oyun tick'i LLM cevabini beklemez. Worker request'i kuyruklar; tamamlanan
cevaplar tick'te drain edilir. Adapter offline, timeout veya gecersiz cevap
verirse bot aninda native PlayerBots davranisina doner ve bu durum acikca
loglanir (zero-regression fallback).

### 2.3. Lokalizasyon ve performans

- `config.yaml`: `language: "tr"` veya `"en"`.
- `locales/<kod>.yaml`: prompt, persona ve jargon.
- Oyuncuya giden metinler ASCII/CP1250 guvenli olmalidir.
- Bubble onceligi: whisper > trade > party > yakin konusma > ambient.
- Queue uzunlugu, duplicate event coalescing, timeout/cancellation ve
  response high-water mark sinirli ve olculebilir olmalidir.

## 3. Dosya sahipligi ve upstream seam sozlesmesi

```text
upstream playerbot dosyalari
        |
        | minimal, sabit seam (include + tek hook)
        v
playerbot_llm_*.h / playerbot_llm_*.cpp
        ^
        |
mmo-llm-adapter/ (Python servis, locale, prompt, provider)
```

### 3.1. Sahipler

- `mmo-llm-adapter/`: provider, prompt, locale, agent state machine,
  queue, bridge ve adapter testlerinin tek sahibi.
- `linux-port/overlays/playerbot/src/game/src/playerbot_llm_*.h/.cpp`:
  game tarafindaki LLM/fork fragmentleri; bridge, sosyal katman, dil ve
  adapter'a ozel state burada.
- `playerbot_manager.cpp`, `playerbot_town.h`, `playerbot_status.h`,
  `playerbot_chat_trade.h`: upstream'e yakin ana dosyalar. Yalnizca zorunlu
  include, forward declaration veya tek satirlik sabit hook kalabilir.
- `linux-port/overlays/playerbot/patches/`: engine patch mekanizmasi;
  LLM davranisi buraya konmaz.

### 3.2. MUST kurallari

Her ajan:

1. Davranisin sahibini (adapter, game fragmenti veya gercek upstream motoru)
   degisiklikten once siniflandirmalidir.
2. Ozel game mantigini `playerbot_llm_<alan>.h/.cpp` dosyasina koymali;
   include siralamasini dependency order olarak korumalidir.
3. Upstream dosyasinda en kucuk seam'i (tercihen include + tek sabit
   imzali hook) birakmalidir.
4. Yeni fragmentlerin `playerbot_*.h/.cpp` wildcard'i ile staged context'e
   girdigini kontrol etmelidir; ayri dosya listesi olusturmamalidir.
5. Upstream sync'i ayri branch/staging context'te yapmali, upstream diff'ini
   incelemeli ve uzun hunk'lari seam'e tasimalidir.
6. Adapter offline/timeout, gecersiz PID/map/mesafe/state, exchange ownership
   ve fiyat sinirlarini acik sonuc kodlariyla ele almalidir.
7. Degisiklik sonrasi hedefli test, staged/build kontrolu ve bu dosyanin
   teslim formatini tamamlamalidir.

### 3.3. DO NOT kurallari

- Upstream `playerbot_*.h` icine uzun Turkce/LLM/trade mantigi ekleme.
- Shop title, market cry, status veya chat metnini ana dosyada yeni sabit
  dizilere koyma.
- Ayni davranisi upstream ve adapter fragmentinde iki kez uygulama.
- Fragmenti `prepare-context.sh`, Makefile veya update listesine tek tek
  kaydetme; wildcard tek kaynaktir.
- Upstream dosyasini fork davranisiyla yeniden formatlama veya buyuk bolum
  tasima.
- LLM'ye dogrudan item, yang veya exchange API'si verme.
- Deterministik native trade, movement veya combat kararini LLM'ye devretme.
- Test edilmemis canlı basari, gecmis olay veya gecici workaround'u normatif
  durum gibi yazma; tarihsel bilgi changelog'a gider.

## 4. Sistem akis ve guvenlik sinirlari

### 4.1. Endpoint ve klasor kontrati

```text
mmo-llm-adapter/
  config.yaml, requirements.txt, main.py, run_adapter.bat
  core/agent.py, memory.py, bubble.py, tools.py
  llm/base.py, client.py, prompts.py
  locales/en.yaml, tr.yaml
  bridges/base.py
  bridges/metin2/connector.py, schemas.py
  tests/
```

Uygulanan endpoint'ler:

- `GET /health`: servis, dil, model, bubble/agent sayaçlari.
- `POST /v1/config/language`: calisirken `tr`/`en` degistirme.
- `POST /v1/metin2/event`: event -> agent -> LLM -> action response.
- `POST /v1/metin2/bubble`: oyuncu konumu ve 30-50 bot bubble secimi.
- `GET /v1/agents/{pid}/state`: state, lease ve sohbet inceleme.

`lease_sweeper_task` her 5 saniyede lease'leri tarar; 120 saniye sonunda
parti liderligi yoksa AUTONOMOUS'a doner ve varsa farewell uretir.

### 4.2. C++ bridge

- POSIX socket tabanli hafif HTTP client, non-blocking worker thread ve JSON
  request/response kuyruklari kullanilir.
- `CPlayerBotManager::Update()` tamamlanan cevaplari her tick drain eder.
- Bot PID, player PID, map, mesafe, cooldown, state ve ownership her action'da
  dogrulanir.
- Trade pending state; disconnect, logout, item tasima/equip ve timeout'ta
  temizlenir. Exchange gercek engine state'inden dogrulanir.
- Fallback ve reddetme nedenleri sessiz degil, yapisal log/sonuc kodudur.

## 5. Guncel durum

### DONE

- Turkce ASCII PlayerBot status, trade, market ve alias katmani.
- Deterministik native trade parser, uzak yaklasma, 15s hold ve erken
  confirmation.
- Pazar shout -> pending teklif -> `tamam` ile birebir trade gecisi.
- Stack/toplam fiyat ve native exchange yonu.
- LLM Turkce cevap katmani, native Ollama provider ve artifact temizligi.
- Item adi/refine/stack/bonus ozeti ve typo-tolerant sorgular.
- Attention/bubble ve temel adapter endpointleri.
- Docker staging/build proseduru ve saglikli game/panel deploy dogrulamasi.
- Pending trade temizligi ve `playerbot_llm_shop.h` seam ayrimi.

### ACTIVE

- **Faz 1 — Trade UX ve veri dogrulugu (P0):** item sorgu kapsami,
  teklif gorunurlugu ve pending state yasam dongusunun tamamlanmasi.
- Sonraki implementasyon, Faz 1 test kapisi gecmeden Faz 2'ye gecemez.

### BLOCKED / LIVE TEST BEKLIYOR

- Gercek oyun istemcisiyle shout smoke testi henüz tamamlanmis sayilmaz:
  `dolu alinir`, `dolu alin`, `dolu alirim`, `dolu aranir`, `KDP satilir`.
- Bu testte `PLAYERBOT_INPUT`, `PLAYERBOT_TRADE` ve `PLAYERBOT_SHOP`
  loglari birlikte izlenmelidir.
- Faz 4'te 750 bot soak'i ve Faz 5 provider/operasyon matrisi yapilmadan
  olceklenmis release kabul edilmez.

## 6. Sirali roadmap ve kapilar

Fazlar sirasiyla ilerler. Her fazin test kapisi gecmeden sonraki faz
baslatilamaz.

### Faz 1 — Trade UX ve veri dogrulugu (P0)

Item sorgu sozlugunu (`silah`, `zirh`, `kalkan`, `yay`, `hançer`, `kılıç`,
`kitap`, `kutsama`, `ne var`, `uzerinde ne var`, `ozellikleri`, `bonuslari`,
`fiyati`) genislet. Cikti item adi, refine, stack, bonus ve kisa ASCII
Turkce ozeti gostersin. Teklifte `item xN`, birim/toplam fiyat, pazar kapanisi
ve gecerlilik suresi acik olsun. Pending kaydi disconnect, logout, item
tasima/equip ve timeout'ta temizlensin; ayni oyuncunun eski teklifi atomik
olarak degissin.

**Kapi:** `kutsama fiyat`, `silah ne`, `ozellikleri`; stack 1/20/200; uzak
`tamam`; pazar acikken `tamam`; disconnect ve timeout.

### Faz 2 — Trade guvenligi ve native engine uyumu (P0)

`expired`, `too_far`, `shop_closed`, `exchange_busy`, `item_missing`,
`gold_failed`, `bot_accept_failed` sonuc kodlari; cancel/item/gold/accept/
completion hook'lari; gercek `CExchange` state dogrulamasi; bot alici
senaryosu; miktar, fiyat tasmasi, negatif/0 fiyat ve maksimum yang siniri.

**Kapi:** iki yonlu trade, cancel/retry, busy, slot/yang yetersizligi,
item degistirme ve completion loglari.

### Faz 3 — LLM sosyal davranisinin native araclara baglanmasi (P1)

Whitelist tool'lar: `follow_player`, `stop_follow`, `come_to_player`,
`say_status`, `inspect_inventory`, `ask_price`, `start_trade`,
`cancel_trade`, `party_request`. Her cagri PID/player/map/mesafe/cooldown/
state/ownership kontrolunden gecsin. 120s leash, yenileme, graceful native
donus ve offline/timeout fallback'i korunur.

**Kapi:** her tool schema'si, yetkisiz PID, uzak map, timeout ve adapter
kapaliyken whisper/trade regresyonu.

### Faz 4 — Attention bubble ve olcekleme (P1)

Gercek pozisyonlardan 30-50 bot secimi; whisper > trade > party > yakin
konusma > ambient kuyrugu; request/response limitleri, eski request discard,
timeout/cancellation, duplicate coalescing ve sayaçlar. 60s macro pulse
yalnizca opt-in ve dusuk token butcesiyle.

**Kapi:** 750 bot soak, queue high-water mark, adapter restart, LLM yokken
CPU/RAM baseline ve 9B GPU bellegi.

### Faz 5 — Provider, dil ve operasyonel saglamlik (P2)

Ollama native ana yol; OpenAI-compatible, LM Studio ve vLLM smoke testleri.
Locale ekleme ve ASCII/CP1250 contract testleri. `/health`, `/metrics`,
latency, token ve hata sayaçlari. Config validation, Docker healthcheck,
restart policy ve log rotation.

**Kapi:** provider matrisi, locale, container restart, gecersiz config ve
24 saat dusuk yogunluk soak.

### Faz 6 — Release ve upstream senkronizasyonu (P2)

Upstream degisikligini staging context'te uygula; seam conflict kontrolu,
`prepare-context.sh` sonrasi kaynak/staged hash eslesmesi, adapter testleri,
game image build, Docker health ve canlı smoke checklist'te birlikte olsun.
Commit alanlari: native trade/approach; Turkce/market alias; LLM adapter/
prompt/provider; Docker/staging/dokumantasyon.

**Release kapisi:** tum hedefli testler; game/panel/mariadb healthy; canli
trade smoke; rollback image tag'i. Commit/push bu kullanici isteginin
disindadir; bu dokuman duzenlemesinde commit olusturulmaz.

```text
Faz 1 -> Faz 2 -> Faz 3 -> Faz 4 -> Faz 5 -> Faz 6
```

## 7. Zorunlu calisma kapilari

Her kod degisikligi teslim edilmeden once su dort kapi kayitsiz gecilemez:

1. **Kapsam:** Istek, etkilenen davranis, owner dosyalari ve kapsam disi
   alanlar yazilir.
2. **Dosya sahipligi ve upstream seam:** Sahiplik, include dependency order,
   upstream API/engine seam'i ve conflict risk'i kontrol edilir.
3. **Hedefli test/dogrulama:** Degisen davranisa en yakin mevcut test,
   syntax/build, endpoint veya canli smoke secilir; neyin derlendiği ve
   neyin gozlemlendigi ayrilir.
4. **Teslim kaydi:** Degisen dosyalar, seam, test sonucu, kalan risk ve
   changelog tarihi kaydedilir.

## 8. AI oturum loglari ve calisma kayitlari

Log ve kayit turleri birbirinden ayrilmalidir:

- **Kalici tarihsel/oturum ozeti:** Oturumun tarihini baslik yapan bir kayit
  olarak [CHANGELOG](./MMO_LLM_ADAPTER_CHANGELOG.md) dosyasinin sonuna eklenir.
  Ozet; amaci, degisen alanlari, karar gerekcesini, dogrulamayi ve kalan
  riski kisa ve tekrar etmeyecek sekilde belirtir.
- **Normatif degisiklik:** Bu sozlesmenin ilgili bolumunde guncellenir.
  Mimari ilke, sahiplik, seam, roadmap, kapi veya durum degisiyorsa ana
  dosyada acikca guncellenmelidir; changelog tek basina normatif kaynak
  degildir.
- **Gecici debug ciktisi:** Repo disindaki session-state `files/` altina
  (bu oturumda `C:/Users/Boran/.copilot/session-state/.../files/`) veya
  sistem temp dizinine yazilir. Bu dosyalar repoya eklenmez ve teslim
  kaydinda yalnizca gerekiyorsa yolu/amaciyla anilir.
- **Runtime uygulama logu:** Bu sozlesme yeni bir `mmo-llm-adapter/logs/`
  dizini tanimlamaz veya olusturmaz. Mevcut Docker/game log yollari ancak
  hedefli dogrulamanin kaniti olarak referans verilebilir; yeni kalici log
  convention'i icin ayri bir karar gerekir.

Bir kayit hem tarihsel hem normatif bilgi iceriyorsa normatif kisim once
ilgili master plan bolumune, oturum anlatimi ve kanit ise changelog sonuna
konur. Hassas veri, credential, tam sohbet transkripti veya gereksiz ham
debug dump'i kaydedilmez.

## 9. Oturum teslim formati

Her ajan son mesajinda su sirayi kullanir:

```text
Kapsam:
- ...

Dosya sahipligi / upstream seam:
- adapter dosyasi:
- game fragmenti:
- upstream ana dosyada kalan minimal hook:

Uygulama:
- ...

Hedefli dogrulama:
- Komut/test:
- Derlenen:
- Canli gozlemlenen:
- Sonuc:

Teslim:
- Normatif dosyada guncellenen bolum:
- Tarihsel ayrinti icin changelog kaydi:
- Kalan risk / BLOCKED:
```

Bu sozlesme, native PlayerBots kontrolunu ve Faz 1-6 sirasini degistirmeden
uygulanir. Yeni tarihsel bilgi normatif metni sisirmek yerine changelog'a
eklenir.
