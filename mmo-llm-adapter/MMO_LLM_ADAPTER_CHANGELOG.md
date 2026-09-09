# MMO LLM Adapter — Changelog ve Tarihsel Kararlar

Bu dosya, [normatif calisma sozlesmesinden](./MMO_LLM_ADAPTER_MASTER_PLAN.md)
ayrilmis tarihsel kayittir. Yeni kayitlar en yeni tarihte sona eklenir.
Tekrarlanan gunluk notlar birlestirilir; kalici mimari kurallar ana dosyada
tekrar edilmez.

## 2026-09-10 — Plug-and-play seam ve pending trade temizligi

- Private shop tabelalarinin Lehce sabitleri ortak `playerbot_town.h`
  govdesinden cikarildi.
- Yeni `playerbot_llm_shop.h`, Turkce shop prefix/template/market cry
  uretimini tasiyor; `playerbot_town.h` tek
  `BuildPlayerBotTurkishShopSign(...)` hook'u cagiriyor.
- Pending trade kayitlari bot PID'sini tutuyor ve her tick'te timeout, oyuncu
  logout, bot logout veya teklif edilen item tasinmasi/equip edilmesinde
  temizleniyor.
- Cache'siz game build ve force-recreate sonrasi game container `healthy`;
  canli status dosyasi Turkce cikti uretmeye devam etti.
- Bu degisiklik Faz 1 pending-state maddesini ilerletti ve upstream sync'te
  uzun adapter mantiginin ortak dosyaya gomulmesini engelledi.

## 2026-09-09 — Shout, item cevaplari ve trade akisinin canli gelismeleri

- `alinir`, `alin`, `alirim`, `aranir`, `satilir` kaliplari shout teklifinden
  ayriliyor; `dolu alirim` gibi ifadeler item sorgusuna donusuyor.
- Shop/kitap listesinde kalan `inne`/`SK` gorunumleri `ve digerleri`/`BK`
  oldu; gelistirme metinlerindeki `poziom` `seviye` olarak duzeltildi.
- Item cevaplari refine, stack ve dolu bonuslari gosterecek sekilde
  genisletildi; `ustumde ne var` ozeti bonuslari dahil etmezken fiyat sorusu
  bonuslari dahil ediyor.
- Fuzzy item eslestirme sinirli Levenshtein ile typo ve eksik harfleri
  destekliyor; uzun envanter cevaplari chat sinirinda parcalaniyor.
- Oyuncu shout'i artik ayni haritadaki uygun iteme sahip en yakin botu
  seciyor. Pending trade 60 saniyeden 120 saniyeye cikti; `tamam` sonrasi
  exchange yaklasma devam ediyor.
- Yang gosterimi `345k`, `1M 300k`, `2M` gibi kisaltiliyor; native exchange
  degeri degismiyor. 1k-10k arasi fiyatlar en yakin bine yuvarlaniyor.
- Item cevaplarinda gercek oyun istemcisiyle `dolu alinir` -> `tamam` smoke
  testi tamamlanmadan basari kesin kabul edilmedi.
- Game image yeniden build edildi; game/panel/MariaDB container'lari
  `healthy` oldu, panel canli haritada 750 bot gosterdi. Son 15 dakikalik
  loglarda shout/shop event'i olmadigi icin istemci smoke testi acik kaldi.

## 2026-09-09 — Thinking modeli bos cevap sorunu

- `playerbot-4b`, OpenAI-uyumlu endpoint'te `max_tokens` butcesini reasoning'e
  harciyor; `content` bos ve `finish_reason=length` donuyordu.
- Ollama native `/api/chat` ve `think: false` ile ayni model temiz Turkce
  cevap verdi.
- `OllamaNativeProvider` eklendi; `config.yaml` icinde
  `llm.provider: "ollama_native"` ile seciliyor. OpenAI-compatible provider'a
  opsiyonel `disable_thinking`/`think` eklendi, varsayilan davranis
  degistirilmedi.
- `tests/test_llm_client.py` icin httpx MockTransport kullanan 6 test eklendi.

## 2026-09-09 — Onceden tamamlanan uygulama ve dogrulama

- Adapter klasoru, FastAPI girisi, core state/memory/bubble/tools, LLM
  provider/client/prompt, `tr`/`en` locale ve Metin2 bridge kuruldu.
- `pytest` ile adapter testleri (endpoint, bubble priority, handover,
  locale, mock LLM ve son client testleri) gecirildi. Ilk kayitta 32 test
  PASS idi; son client testleri bu tabana eklendi.
- `run_adapter.bat` sistem Python'u yerine `.venv\\Scripts\\python.exe`
  kullanacak sekilde duzeltildi; `/health` gercek calisan serviste
  `curl`/`Invoke-RestMethod` ile dogrulandi.
- Gercek whisper event'i Ollama'ya 200 OK ile ulasti; yukaridaki thinking
  sorunu bu testte kesfedildi ve native provider ile giderildi.
- Turkce status/trade/pazar ciktilari, `BK`, `[GRUP]`, `hedef:` ve
  `seviye kasma` etiketleri; item ad/refine/stack/bonus ozetleri canli
  image'da dogrulandi.

## 2026-09-08 ve oncesi — Kalici mimari kararlar

- PlayerBots C++ refleksleri ile LLM sosyal zihninin cift katmanli modeli
  kabul edildi: native rutin varsayilan, oyuncu etkilesiminde LLM override,
  120s handover ve parti liderliginde kalici lease.
- Adapter'in PlayerBots'un yaninda ayri klasorde, oyun-agnostik ve
  provider-degistirilebilir olmasi; Ollama/LM Studio/vLLM gecisi ve TR+EN
  locale kontrati kararlastirildi.
- 30-50 bot attention bubble, oncelik sirasi ve istege bagli 60s macro pulse
  ile 300-800 bot olcegi hedeflendi.
- C++ koprusunde non-blocking worker thread, localhost JSON/HTTP, request ve
  response kuyrugu, tick'te drain ve adapter offline native fallback'i
  secildi.
- Yeni mantigin `playerbot_llm_*.h/.cpp` fragmentlerine konmasi, upstream
  dosyalarinda include + tek hook seam'i birakilmasi ve wildcard staging'in
  tek kaynak olmasi kalici hale getirildi.
- `implementation_plan.md` Part 1 (adapter) ve Part 2 (C++ bridge) bu
  kararlar uzerinden yazilip onaylandi.
- Native trade parser, uzak bot yaklasmasi/hold, fiyat sorusu, erken
  `tamam`, pazar shout'tan birebir trade ve exchange yonu adim adim
  dogrulandi.
- Eski sohbetlerdeki PlayerBots fork analizi; `playerbot_language.h`,
  `PlayerBotText()`, ASCII-safe ceviri ve tek anonymous namespace/include
  dependency order bilgileri bu kararlarin kaynagiydi.

## 2026-09-08 ve oncesi — Operasyon notlari ve kapanan sorunlar

- Adapter klasoru ve C++ bridge dosyalari bir donem untracked olarak bekledi;
  bu bir teslim eksigiydi, runtime basari iddiasi degildi.
- Antigravity Auto Accept'in repo disi calismada `.git\\index` dosyasini
  bozabildigi kesfedildi; eklenti kapatildi ve calisma dogrudan repo
  klasorune alindi. Bozuk index yedekleri temizlendi.
- Turkish chat paketlerinin CP1250/ASCII uyumu korundu; gorunen Lehce
  alias ve kisaltmalar temizlendi, parser anahtarlari geriye uyumluluk icin
  korunarak yalnizca gorunum degistirildi.
- Docker staging hash kontrolu ve game image rebuild sonrasi healthy
  container dogrulamasi kullanilan operasyon kalibi oldu.

## Tarihsel uygulama sirasi

```text
Konsept ve sahiplik karari
  -> Adapter Part 1
  -> C++ bridge Part 2
  -> Native trade/approach
  -> Turkce ve market aliaslari
  -> LLM provider ve thinking fix
  -> Item/bonus anlatimi
  -> Plug-and-play seam
  -> Pending trade temizligi
  -> Gercek istemci shout/trade smoke testi (acik)
```

### Kaynak ve kapsam notu

Bu dosyadaki kayitlar, eski master planin uygulanan endpoint'ler,
dogrulama durumu, bilinen sorunlar, onceki sohbet ozeti, 2026-09-09 ve
2026-09-10 guncellemeleri birlestirilerek tasindi. Normatif kurallar,
guncel DONE/ACTIVE/BLOCKED durumu, Faz 1-6 roadmap'i ve dort zorunlu kapi
icin tek kaynak master plan'dir.

## 2026-09-10 — AI oturum loglari ve calisma kayitlari

- Yeni normatif kural: kalici tarihsel/oturum ozetleri bu changelog'un sonuna
  tarihli baslikla yazilacak; mimari, sahiplik, seam, roadmap, kapi veya
  durum degisiklikleri ilgili master plan bolumunde tutulacak.
- Gecici debug ciktisi repo disindaki session-state `files/` altinda veya
  sistem temp dizininde tutulacak; repoya konmayacak.
- Yeni bir `mmo-llm-adapter/logs/` convention'i onerilmedi veya olusturulmadi.
  Mevcut Docker/game log yollari yalnizca dogrulama kaniti olarak
  referanslanabilir.
- Bu oturumdaki plan ozeti: kapsam -> dosya sahipligi/upstream seam ->
  hedefli test/dogrulama -> teslim kaydi kapilari korunur; native PlayerBots
  otoritesi, LLM sosyal katmani ve Faz 1-6 sirasi degismez.
