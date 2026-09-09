# MMO LLM Adapter — Master Plan & Durum Raporu

> **Bu dosya, projeye dahil olacak her AI asistanı (Claude, GPT, Antigravity, Copilot, vb.) için tek ve
> güncel referans kaynağıdır.** Yeni bir oturuma başlamadan önce bu dosyayı baştan sona okuyun.
> Mimari kararlar, tamamlanan işler, bilinen sorunlar ve bir sonraki adımlar burada tutulur.
> Güncellemeler bu dosyaya eklenir, eski kararlar silinmez — üzerine "GÜNCELLEME" bölümleri eklenir.

**Son güncelleme:** 2026-09-09
**Durum:** Adapter, C++ köprüsü, Türkçe etkileşim, yaklaşma ve deterministik trade akışı canlı olarak
doğrulandı. Native PlayerBot davranışı temel otorite olmaya devam ediyor; LLM yalnızca sosyal etkileşim
katmanında devreye giriyor. Kalan işler Bölüm 11'deki sıralı roadmap'e göre yürütülecek.

---

## 1. Proje Amacı

Metin2 sunucusu (`Metin2_Singleplayer_Server_r40250_FIXED_1.25.2`), [Debaba13/metin2-playerbots](https://github.com/Debaba13/metin2-playerbots)
projesinin Türkçe lokalizasyonlu bir fork'unu kullanıyor (upstream: `TieruYT/metin2-playerbots`).
PlayerBots sistemi zaten çok güçlü bir C++ bot motoru: pathfinding, savaş, ekonomi, quest, market vb.
her şeyi deterministik olarak hallediyor.

Hedef: Bu botlara **yerel bir LLM (local LLM) ile "zihin" eklemek** — ama PlayerBots'un yerini almadan,
onu tamamlayan (complement eden), oyun-agnostik ve LLM-agnostik bir dış servis olarak.

Kullanıcının orijinal isteği (özet):
- Ayrı bir klasör, `playerbots`'un yanında (`mmo-llm-adapter/`).
- Herhangi bir "playerbots benzeri" projeye plug-and-play bağlanabilen genel bir "MMO Adapter".
- Yerel LLM değiştirilebilir olmalı (Ollama / LM Studio / vLLM arasında sorunsuz geçiş).
- Botlar varsayılan olarak PlayerBots kontrolünde kalmalı; sadece **oyuncuyla doğrudan etkileşimde**
  (fısıltı, parti, trade) LLM devreye girmeli, 2 dakika etkileşimsizlik sonrası PlayerBots'a geri dönmeli.
- LLM devredeyken bile mümkün olduğunca PlayerBots'un altyapısını (follow, attack, buff, trade fonksiyonları) kullanmalı.
- Model boyutu: 4B veya 7B arası, performans/kişilik dengesine göre karar verilecek.
- Başlangıçta İngilizce + Türkçe desteklenecek, config'te tek satırla değişebilir, yeni dil eklemek
  sadece yeni bir locale dosyası + bir satır config olmalı.
- Ölçek: 300–800 bot arasında sunucu olabilir. Oyuncuya en yakın 30–50 bot "aktif dikkat balonu" (attention
  bubble) içinde tutulacak, geri kalanlar dakikada bir toplu (macro pulse) güncelleme alacak — GPU'yu boğmadan.

---

## 2. Onaylanan Mimari

### 2.1. Çift Katman Felsefesi: "Refleks vs. Zihin"

```
STATE: AUTONOMOUS (PlayerBots C++)
  - Normal rutin: exp, fishing, market, quest
  - LLM hiç çağrılmıyor, sıfır GPU maliyeti
        │
        │  [Tetikleyici: Fısıltı / Yakın Konuşma / Parti Daveti / Trade]
        ▼
STATE: LLM_OVERRIDE (Zihin devrede)
  - 120 saniyelik "leash" (kayış) zamanlayıcısı başlar
  - Bot oyuncuyla doğal konuşur, PlayerBots primitiflerini
    (follow, attack, buff, trade, stance) LLM tool-call'ları ile tetikler
  - Her yeni etkileşim 120s sayacını sıfırlar
  - Parti liderliği aktifse süre dolmaz
        │
        │  [120s doldu VE partide değil]
        ▼
STATE: RESUME_ROUTINE (Nazik geri dönüş)
  - Bot vedalaşır (graceful farewell) veya sonraki işini söyler
  - Kontrol PlanPlayerBotLongTermGoal'a geri döner
```

### 2.2. 3 Katmanlı Modüler Yapı

```
[ Game Server (Metin2 r40250, C++) ]
                 ▲
                 │  JSON over HTTP (localhost, non-blocking worker thread)
                 ▼
┌────────────────────────────────────────────────────────┐
│               MMO LLM ADAPTER SERVICE (Python)          │
├────────────────────────────────────────────────────────┤
│ 1. Game Adapters (Pluggable)                            │
│    ├── Metin2Bridge (bridges/metin2/)                    │
│    └── (Gelecek: WoWBridge, L2Bridge, vb.)               │
├────────────────────────────────────────────────────────┤
│ 2. Core Agent Runtime (Oyun-agnostik)                    │
│    ├── State machine (AUTONOMOUS <-> LLM_OVERRIDE)       │
│    ├── Memory (kısa vadeli sohbet geçmişi)               │
│    ├── Attention Bubble (30-50 en yakın bot)             │
│    └── Tool schema (follow, attack, buff, trade, say...) │
├────────────────────────────────────────────────────────┤
│ 3. LLM Providers (Pluggable, OpenAI-uyumlu)              │
│    └── Ollama / LM Studio / vLLM / LocalAI               │
└────────────────────────────────────────────────────────┘
```

### 2.3. Lokalizasyon

- `config.yaml` içinde tek satır: `language: "tr"` (veya `"en"`).
- Her dil `locales/<kod>.yaml` dosyasında: prompt şablonları, kişilik/persona metinleri, jargon.
- Yeni dil eklemek = yeni `locales/xx.yaml` dosyası + config'te bir satır değişikliği.
- Türkçe karakterler ASCII güvenli tutulur (CP1250/ASCII chat paketlerini bozmamak için) — PlayerBots'un
  mevcut `playerbot_language.h` yaklaşımıyla tutarlı.

### 2.4. Attention Bubble / Macro Pulse

- Oyuncuya en yakın 30–50 bot: aktif algı, öncelik kuyruğu (whisper > parti komutu > trade > yakın konuşma > ambient).
- Diğer botlar: native C++ tick döngüsünde çalışmaya devam eder; adapter'dan dakikada bir (60s) toplu
  "macro pulse" güncellemesi alabilirler (opsiyonel, ileride).

### 2.5. C++ ↔ Python İletişimi

- Seçilen yöntem: hafif, **non-blocking arka plan thread + POSIX socket tabanlı basit HTTP client** (C++ tarafı).
- Oyun tick'i asla LLM cevabını beklemez; worker thread kuyruğa yazar, tick'te tamamlanan cevaplar drenajlanır (drain).
- Adapter offline ise bot anında native PlayerBots davranışına geri düşer (zero-regression fallback).

---

## 3. Klasör Yapısı (Uygulandı)

```
mmo-llm-adapter/
├── config.yaml               # LLM endpoint, model, dil, handover TTL, bubble ayarları
├── requirements.txt
├── main.py                   # FastAPI servis giriş noktası
├── run_adapter.bat           # Tek tık başlatıcı (.venv Python'unu kullanır)
├── core/
│   ├── agent.py              # PlayerBotAgent state machine (AUTONOMOUS <-> LLM_OVERRIDE, 120s TTL)
│   ├── memory.py             # Sohbet geçmişi (AgentMemory)
│   ├── bubble.py             # AttentionBubbleManager (30-50 en yakın bot, cooldown)
│   └── tools.py              # PlayerBots'a eşlenen tool şemaları
├── llm/
│   ├── base.py                # Soyut LLM provider arayüzü
│   ├── client.py               # OpenAI-uyumlu client (Ollama/LM Studio/vLLM)
│   └── prompts.py              # PromptManager (persona + dil + bağlam birleştirme)
├── locales/
│   ├── en.yaml
│   └── tr.yaml
├── bridges/
│   ├── base.py                 # Soyut oyun köprüsü arayüzü
│   └── metin2/
│       ├── connector.py        # Metin2Bridge: event alma, agent yönetimi, dispatch
│       └── schemas.py          # Pydantic modelleri (Metin2EventRequest, ActionResponse, vb.)
└── tests/                       # 32 test — hepsi geçiyor (bkz. Bölüm 5)
```

C++ tarafı (`linux-port/overlays/playerbot/src/game/src/`):
- `playerbot_llm_bridge.h` **(yeni, henüz commit edilmedi)** — arka plan worker thread, JSON encode/decode,
  basit socket HTTP client, `TPlayerBotLLMRequest` / `TPlayerBotLLMResponse` kuyrukları.
- `playerbot_chat_trade.h` **(değiştirildi)** — trade dışı fısıltılar artık önce
  `DispatchPlayerBotLLMWhisper()` çağırıyor; köprü uygun cevap veremezse eski native fallback mesajına düşüyor.
- `playerbot_manager.cpp` **(değiştirildi)** — `CPlayerBotManager::Update()` içine
  `UpdatePlayerBotLLMBridge(dwNow)` çağrısı eklendi (tamamlanan LLM cevaplarını her tick drenajlar).

---

## 4. Uygulanan Endpoint'ler (main.py)

| Endpoint | Açıklama |
|---|---|
| `GET /health` | Servis durumu, aktif dil, model adı, bubble/agent sayaçları |
| `POST /v1/config/language` | Dili çalışırken değiştirir (`tr`/`en`) |
| `POST /v1/metin2/event` | Ana giriş noktası: whisper/say event'i alır, agent'ı bulur/oluşturur, LLM'i çağırır, aksiyon döner |
| `POST /v1/metin2/bubble` | Oyuncu konumunu senkronlar, en yakın 30-50 botu aktif bubble'a alır |
| `GET /v1/agents/{pid}/state` | Bir botun bilişsel durumunu (state, lease, son sohbetler) inceleme |

Arka planda `lease_sweeper_task` her 5 saniyede bir tüm agent'ları tarayıp 120s TTL'i dolanları
`AUTONOMOUS`'a döndürüyor ve (varsa) vedalaşma mesajı üretiyor.

---

## 5. Doğrulama Durumu (Bugüne Kadar Yapılanlar)

1. **Birim testleri:** `pytest` ile `mmo-llm-adapter/tests/` içindeki 32 test **hepsi PASS**.
   (`test_api_endpoints.py`, `test_bubble_priority.py`, `test_handover_state.py`, `test_locales.py`, `test_mock_llm.py`)
2. **Servis canlı başlatma:** `run_adapter.bat` düzeltildi (artık `.venv\Scripts\python.exe` kullanıyor,
   önceden sistem Python'unu çağırıp `uvicorn bulunamadı` hatası veriyordu — düzeltildi ve doğrulandı).
3. **`/health` testi:** Gerçek çalışan serviste `curl`/`Invoke-RestMethod` ile test edildi, beklenen JSON döndü.
4. **Uçtan uca `/v1/metin2/event` testi:** Gerçek bir whisper event'i gönderildi, adapter Ollama'ya
   (`playerbot-4b` modeli) gerçek bir HTTP isteği attı (200 OK, ~11s), fakat **cevap boş döndü** (bkz. Bölüm 6).
5. **Git durumu:** `mmo-llm-adapter/` klasörü henüz **untracked** (commit edilmemiş). C++ tarafındaki
   3 dosya (`playerbot_llm_bridge.h` yeni, `playerbot_chat_trade.h` ve `playerbot_manager.cpp` değişti)
   da henüz commit edilmemiş durumda — working tree'de bekliyor.
6. **Lehçe temizliği ve deploy:** Native PlayerBot status, trade ve pazar çıktıları
   Türkçeleştirildi; görünen `KU` kullanımları `BK` oldu ve parser uyumluluğu korundu.
   LLM temizleyicisi `wyprzedaz`, `kupie`, `sprzedam`, `stragan` ve benzeri sızıntıları
   Türkçeye dönüştürüyor. Staged game context hash'leri eşitlendi, game image yeniden
   oluşturuldu ve container `healthy` durumunda doğrulandı.
7. **Görünen kısaltmalar:** Oyuncuya gösterilen `PT` ifadeleri `grup`, `[PT]`
   etiketi `[GRUP]`, `cel:` etiketi `hedef:` olarak güncellendi. Parser ve iç
   lookup anahtarları geriye dönük uyumluluk için değiştirilmedi; yeni game image
   yeniden oluşturulup `healthy` olarak deploy edildi.
8. **Hedef etiketleri:** Genel hedef fallback'i `poziom` yerine `seviye kasma`
   oldu; diğer hedef adları da doğrudan Türkçe ve anlaşılır hale getirildi.
9. **Item detayları:** Envanter sorguları artık item adı, refine seviyesi, stack
   adedi ve en fazla dört bonus tip/değerini kısa Türkçe özet olarak gösteriyor.
   `özellikleri`, `bonusları`, `kalkan`, `yay`, `hançer`, `kılıç`, `kitap` ve
   `kutsama` sorgu niyetleri eklendi; game image yeniden oluşturulup healthy deploy edildi.

---

## 6. BİLİNEN SORUNLAR (Çözülmeden oyun içi canlı teste geçilmemeli)

### 6.1. `playerbot-4b` modeli "thinking" modeli — boş cevap sorunu (ÇÖZÜLDÜ)

**Belirti:** `/v1/metin2/event` gerçek bir istek gönderildiğinde adapter 200 OK dönüyor ama
`primary_action`, `arguments` ve `speech_reply` hepsi boş/null geliyor.

**Kök neden:** `ollama show playerbot-4b` çıktısı modelin `thinking` (Qwen3.5 tabanlı, akıl yürütme/
reasoning) kapasitesine sahip olduğunu gösteriyor. Ollama'nın OpenAI-uyumlu
`/v1/chat/completions` endpoint'ine yapılan çağrılarda model, verilen `max_tokens` bütçesinin **tamamını**
`reasoning` alanına (iç düşünce süreci) harcıyor ve `content` alanı hep boş kalıyor:

```
"message": {
    "content": "",
    "reasoning": "Thinking Process:\n\n1. Analyze the Request...\n...",
},
"finish_reason": "length"
```

- `max_tokens: 200` (config.yaml varsayılanı) ile test edildi → boş content.
- `max_tokens: 700` ile tekrar test edildi → hâlâ boş content, reasoning yarım kesilmiş halde bitti.
- Ollama'nın native `/api/chat` endpoint'inde `think: false` parametresiyle test edildiğinde
  **çalıştı ve gerçek bir Türkçe cevap üretti**:
  ```
  "content": "Selam! Şu an Kazanköyü civarında (Süper Orman girişinden hemen sonra) dolaşıyorum. Nereye uğrayacağın?"
  ```
  Bu istek `eval_count: 42` token'da bitti (200'den çok daha az) ve `done_reason: "stop"` ile temiz sonlandı.

**Sonuç:** Sorun modelin kendisinde değil, **adapter'ın kullandığı OpenAI-uyumlu `/v1/chat/completions`
endpoint'inin bu model için `think`/reasoning modunu kapatmıyor olmasında.** Ollama'nın native `/api/chat`
endpoint'i + `think: false` parametresi ile aynı model doğru ve hızlı çalışıyor.

**Uygulanan çözüm (bkz. `llm/client.py`):** Seçenek (b) uygulandı — `OllamaNativeProvider` adında
ikinci bir provider eklendi, Ollama'nın native `/api/chat` endpoint'ini `think: false` ile çağırıyor
ve aynı `parse_message_to_llm_response` mantığını (`llm/base.py`) OpenAI-uyumlu provider ile paylaşıyor.
`config.yaml`'da `llm.provider: "ollama_native"` seçilirse aktif olur; `base_url` OpenAI-stili
(`.../v1`) veya çıplak host olabilir, ikisi de kabul edilir. Varsayılan `openai_compatible` provider'a
da opsiyonel `disable_thinking`/`think` alanı eklendi (bazı Ollama sürümleri OpenAI-uyumlu yolda da
`think` alanını kabul edebiliyor diye), ama varsayılan `false` olduğu için mevcut Ollama/LM Studio/vLLM
davranışı hiç değişmedi (payload'a `think` alanı hiç eklenmiyor — bkz.
`tests/test_llm_client.py::test_openai_compatible_omits_think_by_default`). Testler:
`tests/test_llm_client.py` (6 yeni test, httpx.MockTransport ile gerçek ağ çağrısı yapmadan).

### 6.2. Önceki oturumdaki Git index bozulmaları (ÇÖZÜLDÜ, bilgi amaçlı)

Antigravity Auto Accept eklentisi, repo'nun **dış** (üst) klasöründen (`C:\Metin2 Bot server`) çalıştırılırken
Antigravity aksiyonlarını otomatik onaylıyordu; bu durum tekrar tekrar `.git\index` dosyasının 0 byte'a
inmesine sebep oldu. Artık: Auto Accept devre dışı bırakıldı, çalışma doğrudan repo klasöründen yapılıyor,
`.git\index` sağlıklı (227,784 byte). İki bozuk yedek dosya (`.git\index.corrupt-*`) silindi.

---

## 7. Sıradaki Adımlar (Öncelik Sırasıyla)

1. **[TAMAMLANDI]** Thinking-model boş cevap sorunu `ollama_native` + `think: false` ile çözüldü.
2. **[TAMAMLANDI]** Adapter canlı event, Türkçe cevap, movement hold ve native trade akışı doğrulandı.
3. **[TAMAMLANDI]** Pazar shout teklifinden `tamam` ile pazarı kapatıp birebir trade'e geçiş doğrulandı.
4. Bir sonraki uygulanacak iş: **Bölüm 11.2 — Faz 1, Trade UX ve item/bonus anlatımı**.
5. Sonraki bağımlı fazlar: exchange state güvenliği, LLM tool-call, attention bubble/queue,
   provider-operasyon ve release/upstream senkronizasyonu.

> Ayrıntılı görev sırası, fonksiyon yüzeyleri ve test kapıları için Bölüm 11 tek güncel roadmap'tir.

---

## 8. Önceki Sohbetlerin Referans Özeti (Kronolojik)

1. Kullanıcının fork'u analiz edildi: PlayerBots + Türkçe lokalizasyon overlay pattern'i (`playerbot_language.h`,
   `PlayerBotText()`, ASCII-safe çeviri, overlay dosyaları tek anonymous namespace içinde sıralı include ediliyor).
2. "MMO LLM Adapter" konsepti tartışıldı: Reflex (C++) vs Mind (LLM) ikili katman felsefesi kabul edildi.
3. Kullanıcı karar verdi: Öncelik "A + biraz C" (sosyal etkileşim + yüksek seviye strateji), PlayerBots
   kontrolü korunmalı, 120s handover, 30-50 attention bubble, dakikada bir macro pulse (opsiyonel),
   TR+EN native destek + kolay dil ekleme.
4. Mimari onaylandı, `implementation_plan.md` (Part 1: Adapter) yazıldı ve onaylandı.
5. Adapter koda döküldü: `.venv` kuruldu, bağımlılıklar yüklendi, 16 test yazıldı ve geçti.
6. `implementation_plan.md` (Part 2: C++ Bridge) yazıldı ve onaylandı; `playerbot_llm_bridge.h` ve
   entegrasyon noktaları oluşturuldu.
7. Kullanıcı elindeki GGUF modellerden `Qwen3.5-4B-Uncensored-HauhauCS-Aggressive-Q6_K` önerildi (düşük
   gecikme, düşük VRAM, "aggressive" ton Metin2 kültürüne uygun) → `ollama create playerbot-4b -f Modelfile`
   ile Ollama'ya eklendi, `config.yaml`'da `model: "playerbot-4b"` olarak ayarlandı.
8. Bu oturumda (farklı bir AI asistanı ile) canlı test yapıldı: adapter başlatıldı, testler tekrar
   doğrulandı, gerçek bir whisper event'i gönderildi → **Bölüm 6.1'deki boş cevap sorunu keşfedildi.**

---

## 9. Önemli Notlar / Kısıtlar

- Bu ortamda bazı AI oturumları `C:\Metin2 Bot server` klasörüne yazma izni reddedebiliyor (araç/ortam
  kısıtlaması). Eğer bir asistan yazamıyorsa, kullanıcıdan repo klasörünü doğrudan paylaşmasını/açmasını
  istemeli, dış (üst) klasörden değil.
- Antigravity Auto Accept eklentisi, repo dışından çalıştırıldığında Git index'i bozabiliyor — bu eklenti
  repoklasörü dışında **kapalı tutulmalı**.
- Tüm karakterler ASCII güvenli tutulmalı (Türkçe özel karakterler chat paketlerini bozabilir) —
  PlayerBots'un mevcut kuralıyla tutarlı kalınmalı.

## 10. Son Canli Trade Duzeltmeleri (9 Eylul 2026)

- Oyuncu mesaji sonrasi bot yaklasma hold suresi milisaniye birimine uygun olarak 15 saniyeye
  (`15000`) duzeltildi; uzak fiyat sorusu ve erken `tamam` onayi bot mesafeye girince tamamlanabiliyor.
- Trade item eslestirmesine `kutsama`, `kagit`, `uzerinde` ve benzeri Turkce niyet kaliplari eklendi.
- Fiyat, `GetPlayerBotShopAskingPrice()` algoritmasi uzerinden birim pazar fiyatinin %10 ustune
  ve item stack miktariyla carpilarak hesaplanmaya baslandi.
- Botun exchange tarafini kabul etmesi ve oyuncunun son kabul tikini yapmasi saglandi.
- Pazar shout'ina cevap veren botun teklifi pending trade olarak tutuluyor; oyuncu
  `tamam` dediginde bot pazari kapatip oyuncuya gelerek dogrudan trade aciyor.

---

## 11. Güncel Durum ve Sıralı Roadmap

Bu bölüm sonraki tüm uygulama oturumlarında öncelik sırası olarak kullanılmalıdır.
Her faz, bir önceki fazın test kapısı geçmeden başlatılmamalıdır.

### 11.0. Plug-and-play / upstream conflict kuralı

LLM ve Turkce fork davranisi upstream'in aktif gelistirdigi buyuk
`playerbot_*.h` dosyalarinin govdesine gomulmemelidir. Upstream pull sonrasi
otomatik merge'i korumak icin:

- Ozel mantik yeni `playerbot_llm_*.h` adapter fragmentlerine tasinir.
- Upstream dosyasinda yalnizca include ve sabit imzali tek hook cagrisi kalir.
- Pazar tabelasi metinleri bu nedenle `playerbot_llm_shop.h` icindedir;
  `playerbot_town.h` yalnizca `BuildPlayerBotTurkishShopSign(...)` cagirir.
- `playerbot_status.h` ve `playerbot_chat_trade.h` seam wrapper olarak kalir.
- Yeni adapter dosyalari `playerbot_*.h` wildcard'i ile staged game context'e
  otomatik kopyalanir; ayri dosya listesi eklenmez.
- Upstream dosyasinda davranis degisikligi gerekiyorsa once adapter seam'i
  tasarla; dogrudan upstream fonksiyonuna uzun bir hunk ekleme.

Bu kural, upstream merge conflict'ini tamamen teorik olarak yok etmez; ancak
aktif upstream dosyasindaki degisiklik alanini include/hook satirlarina indirir.
Adapter mantigi ve dil sabitleri upstream'de bulunmayan yeni dosyalarda tutulur.

### 11.1. Tamamlanan ve korunacak temel sistemler

| Durum | Sistem | Uygulanan yüzeyler | Kabul kriteri |
|---|---|---|---|
| DONE | Türkçe PlayerBot görünür metinleri | `playerbot_status.h`, `playerbot_language.h` | Runtime status ve shout metinleri ASCII Türkçe |
| DONE | Pazar alias ve kısa adları | `playerbot_chat_trade.h` | `BK`, `KDP`, `GBY`, `SYH`, `DOLU`, `kutsama`, `kagit` eşleşir |
| DONE | Native trade parser | `ParsePlayerBotTradeText`, pending trade map | Shout/whisper niyeti deterministik ayrılır |
| DONE | Uzak bot yaklaşması | `HoldPlayerBotForPlayerMessage`, manager update | Bot yaklaşık 10 m'ye gelir, 15 s hold yenilenir |
| DONE | Fiyat sorusu ve erken onay | deferred price/confirmation helpers | Uzak botta `fiyat` ve `tamam` kaybolmaz |
| DONE | Pazar shout -> birebir trade | `AnswerPlayerBotBuyShout`, `OpenPlayerBotPendingTrade` | Bot pazarı kapatır, oyuncuya gelir, trade açar |
| DONE | Stack ve fiyat hesabı | `GetPlayerBotShopAskingPrice` + %10 satıcı marjı | Tüm stack tek toplam fiyatla koyulur |
| DONE | Exchange yönü | bot `Accept(true)`, oyuncu son onay | Bot item/yang koyar ve kendi tarafını kabul eder |
| DONE | LLM Türkçe cevap katmanı | `prompts.py`, `agent.py`, `text.py` | Kısa ASCII Türkçe, artifact temizliği, native Ollama |
| DONE | Lehçe çıktı temizliği | `playerbot_status.h`, `playerbot_chat_trade.h`, `playerbot_town.h`, `text.py` | Runtime ve LLM cevaplarında Lehçe kelime/kısaltma kalmaz; `BK` görünür |
| DONE | Item bonus ve özellik özeti | `AnswerPlayerBotInventoryQuestion`, `DescribePlayerBotItem` | İsim, refine, stack ve bonus tip/değeri Türkçe kısa cevapta görünür |
| DONE | 9B bellek araştırması | Ollama GPU ölçümü, Docker stats | Model GPU'da; vmmem artışı WSL cache olarak ayrıştırıldı |
| DONE | Docker staging/build prosedürü | `prepare-context.sh`, staged game context | Kaynak değişince staged dosya hash'leri kontrol edilir |

### 11.2. Faz 1 — Trade UX ve veri doğruluğu (P0)

**Amaç:** Oyuncunun trade sırasında gördüğü bilgiyi anlaşılır ve güvenilir yapmak.

1. Item sorgu sözlüğünü genişlet:
   - `silah`, `zirh`, `kalkan`, `yay`, `hançer`, `kılıç`, `kitap`, `kutsama`
   - `ne var`, `üzerinde ne var`, `özellikleri`, `bonusları`, `fiyatı`
2. `AnswerPlayerBotInventoryQuestion()` çıktısına ekle:
   - item adı, refine seviyesi, stack adedi
   - uygulanmış bonus tipi ve değeri
   - kısa Türkçe özet ve ASCII normalizasyonu
3. Trade teklifinde açık veri göster:
   - `item xN`, birim fiyat, toplam fiyat
   - botun pazarı kapattığı ve teklifin geçerlilik süresi
4. Pending state yaşam döngüsü:
   - oyuncu disconnect, bot logout, item taşınması ve timeout temizliği
   - aynı oyuncu için eski teklifin yeni teklifle atomik değiştirilmesi

**Test kapısı:** `kutsama fiyat`, `silah ne`, `özellikleri`, stack 1/20/200,
uzak `tamam`, pazar açıkken `tamam`, disconnect ve timeout senaryoları.

### 11.3. Faz 2 — Trade güvenliği ve native engine uyumu (P0)

**Amaç:** Native exchange state ile PlayerBot pending state'in her durumda tutarlı kalması.

1. `OpenPlayerBotPendingTrade()` için açık sonuç kodları:
   - `expired`, `too_far`, `shop_closed`, `exchange_busy`, `item_missing`,
     `gold_failed`, `bot_accept_failed`
2. Exchange event hook'ları:
   - trade cancel, item değişimi, gold değişimi, player accept ve completion
3. Bot kabul durumunu gerçek `CExchange` state'inden doğrula; yalnızca local bool'a güvenme.
4. Bot alıcı olduğu senaryoda oyuncu itemini exchange'e koyma ve miktar kontrolünü tamamla.
5. Fiyat taşması, negatif/0 fiyat ve maksimum yang sınırlarını ortak helper'a taşı.

**Test kapısı:** iki yönlü trade, cancel/retry, exchange busy, yetersiz slot/yang,
oyuncunun itemi değiştirmesi ve trade completion logları.

### 11.4. Faz 3 — LLM sosyal davranışının native araçlara bağlanması (P1)

**Amaç:** LLM konuşsun; hareket, savaş ve trade kararları güvenli native tool çağrılarıyla uygulansın.

1. Adapter tool şemaları:
   - `follow_player`, `stop_follow`, `come_to_player`
   - `say_status`, `inspect_inventory`, `ask_price`
   - `start_trade`, `cancel_trade`, `party_request`
2. C++ bridge action doğrulaması:
   - bot PID, player PID, map, mesafe, cooldown, state ve ownership kontrolü
3. LLM'nin doğrudan item/yang/exchange API'sine erişmesini engelle; yalnızca whitelist tool.
4. 120 s LLM leash, yeni mesajda yenileme ve native routine'e graceful dönüş.
5. Adapter offline/timeout olduğunda native fallback ve açık log.

**Test kapısı:** her tool için schema testleri, yetkisiz PID, uzak map, timeout,
adapter kapalıyken whisper/trade regresyon testleri.

### 11.5. Faz 4 — Attention bubble ve ölçekleme (P1)

**Amaç:** 750 botta LLM trafiğini sınırlamak ve bellek/queue büyümesini kontrol etmek.

1. `AttentionBubbleManager` gerçek oyun pozisyonlarıyla 30–50 bot seçsin.
2. Öncelik kuyruğu: whisper > trade > party > yakın konuşma > ambient.
3. C++ LLM request queue:
   - maksimum uzunluk
   - eski request discard
   - request timeout/cancellation
   - response queue limiti ve sayaç logları
4. Aynı bot/oyuncu için duplicate event coalescing.
5. 60 s macro pulse'u yalnızca opt-in ve düşük token bütçesiyle uygula.

**Test kapısı:** 750 bot soak testi, queue high-water mark, adapter restart,
LLM yokken CPU/RAM baseline ve 9B GPU belleği.

### 11.6. Faz 5 — Provider, dil ve operasyonel sağlamlık (P2)

1. Ollama native provider'ı ana yol olarak koru; OpenAI-compatible, LM Studio ve vLLM smoke testleri.
2. `locales/<kod>.yaml` ile yeni dil ekleme doğrulaması ve ASCII/CP1250 contract testleri.
3. `/health`, `/metrics`, request latency, model token kullanımı ve hata sayaçları.
4. Config validation: model, provider, timeout, max tokens, language ve queue limitleri.
5. Docker healthcheck, adapter restart policy ve log rotation.

**Test kapısı:** provider matrix, locale testleri, container restart, config invalidation
ve 24 saatlik düşük yoğunluk soak.

### 11.7. Faz 6 — Release ve upstream senkronizasyonu (P2)

1. Upstream değişikliklerini önce ayrı staging context'te uygulayıp overlay conflict kontrolü yap.
2. `prepare-context.sh` sonrası kaynak/staged hash doğrulaması zorunlu olsun.
3. Adapter testleri, game image build, Docker health ve canlı smoke test tek release checklist'inde toplansın.
4. Değişiklikleri anlamlı commit'lere ayır:
   - native trade/approach
   - Türkçe ve market aliasları
   - LLM adapter/prompt/provider
   - Docker/staging ve dokümantasyon
5. Testlerden sonra commit ve GitHub push; push öncesi `git diff --check`.

**Release kapısı:** tüm hedefli testler, game/panel/mariadb healthy, canlı trade smoke
ve rollback image tag'i mevcut.

### 11.8. Uygulama sırası özeti

```text
Faz 1: Trade UX ve item/bonus anlatımı
  -> Faz 2: Exchange state güvenliği
  -> Faz 3: LLM tool-call ve leash
  -> Faz 4: Attention bubble, queue limitleri, macro pulse
  -> Faz 5: Provider/locale/operasyon
  -> Faz 6: Upstream sync, release, commit/push
```

**Kural:** Deterministik native trade ve movement davranışı hiçbir fazda LLM'ye
devredilmez; LLM yalnızca niyet/sosyal katman ve whitelist edilmiş tool çağrıları sağlar.

---

## GÜNCELLEME — 2026-09-09: Shout ve pazar metni düzeltmesi

- Oyuncu bağırışlarında `alinir`, `alin`, `alirim`, `aranir` ve `satilir` kalıpları
  artık teklif metninden ayrıştırılıyor; örneğin `dolu alirim` doğrudan `dolu` item
  sorgusuna dönüşüyor.
- Pazar tabelası ve kitap listesinde kalan görünür Lehçe `inne`/`SK` çıktıları
  Türkçeleştirildi (`ve digerleri`, `BK`).
- Geliştirme metinlerinde kalan `poziom` görünümü `seviye` olarak düzeltildi.
- Demirci/pazar +7/+8/+9 shout örneklerindeki Lehçe cümleler Türkçe ASCII
  karşılıklarıyla değiştirildi.
- Doğrulama: game image yeniden build edildi, game container `healthy` oldu;
  `tests/test_locales.py`: **12 passed**.
- Docker doğrulaması: MariaDB, game ve panel container'ları `healthy`; panel canlı
  haritada 750 bot gösteriyor.
- Son 15 dakikalık game loglarında shout/shop event'i yok; bu nedenle oyuncu
  shout smoke testi henüz gerçek oyun istemcisi mesajıyla tamamlanmış sayılmıyor.
- Bir sonraki canlı testte şu mesajlar tek tek gönderilecek:
  `dolu alinir`, `dolu alin`, `dolu alirim`, `dolu aranir`, `KDP satilir`.
  Aynı anda `PLAYERBOT_INPUT`, `PLAYERBOT_TRADE` ve `PLAYERBOT_SHOP` logları
  izlenecek; pazar açılmıyorsa uygunluk ve 20 dakikalık bot shout throttling'i
  ayrıştırılacak.

## GÜNCELLEME — 2026-09-09: Item cevaplarının kapsamı

- `ustumde ne var`/`ustundeki` cevapları artık yalnızca item adı, refine seviyesi
  ve stack miktarını gösteriyor; bonuslar listeyi doldurmuyor.
- Fiyat sorularında item adı, refine, stack ve mevcut bonuslar birlikte gösteriliyor.
- Bilinmeyen bonus türlerinde görünen genel `bonus` etiketi yalnızca fiyat
  detayında kullanılacak; envanter özeti artık bu etiketi üretmiyor.

## GÜNCELLEME — 2026-09-09: Trade teklifinin kaybolmaması

- Oyuncu bağırışıyla item arayan bot artık yalnızca oyuncuya çok yakın olanı değil,
  aynı haritadaki uygun iteme sahip en yakın botu seçiyor; botun oyuncuya yaklaşması
  pending trade onayından sonra devam ediyor.
- Pending trade süresi 60 saniyeden 120 saniyeye çıkarıldı. Böylece `tamam` ile
  yaklaşma/trade açma arasında teklifin sessizce düşmesi engellendi.
- Bu akışta gerçek oyun istemcisiyle `dolu alinir` ve ardından `tamam` testi
  yapılmadan başarı kesin kabul edilmeyecek.

## GÜNCELLEME — 2026-09-09: Shout item detayları ve kısa yang gösterimi

- Oyuncunun bağırışına verilen item cevabı artık yalnızca item adı değil; refine,
  stack ve itemde bulunan tüm dolu bonusları gösteriyor (`ortalama`, `beceri`,
  `can` vb.).
- Bağırış cevabındaki pending trade, PM fiyat cevabındaki akışla aynı şekilde
  `tamam` sonrasında exchange açıyor.
- Oyuncuya gösterilen yang tutarları kısaltıldı:
  - `345000` -> `345k`
  - `1300000` -> `1M 300k`
  - `2000000` -> `2M`
- Native exchange'e gönderilen gerçek yang değeri değiştirilmedi; yalnızca chat
  metni kısaltılıyor.

## GÜNCELLEME — 2026-09-09: Item typo eşleştirme ve küçük fiyat yuvarlama

- Item aramalarında önce tam/alias eşleşmesi, sonra sınırlı Levenshtein benzerliği
  kullanılıyor. Örneğin `sus eysasi`, envanterdeki `sus esyasi` adına otomatik
  olarak eşleşiyor; birden fazla adayda en yakın isim seçiliyor.
- Aynı yakın isim mantığı shout, pazar ve PM fiyat sorgularında kullanılıyor.
- `1000 < fiyat < 10000` aralığındaki fiyatlar gerçek trade fiyatı dahil en yakın
  binliğe yuvarlanıyor: `9500 -> 10000`, `7350 -> 7000`.
- `1k` altı ve `10k` üzeri fiyatların mevcut değerleri korunuyor.

## GÜNCELLEME — 2026-09-09: Daha toleranslı typo ve tam envanter cevabı

- Fuzzy item eşleştirme toleransı artırıldı; `kilc -> kilici/kilic` ve
  `krmzi iskr -> kirmizi iksiri` gibi eksik harfli yazımlar envanterdeki en yakın
  ada göre eşleştiriliyor.
- Envanter özeti artık ilk birkaç itemle sınırlı değil; tüm taşınan itemler
  gösteriliyor.
- Uzun envanter cevapları chat sınırına göre virgül noktalarından bölünüp
  `Ustumde`, `Cantada` ve devam mesajları olarak eksiksiz gönderiliyor.
