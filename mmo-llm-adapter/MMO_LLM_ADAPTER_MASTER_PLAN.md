# MMO LLM Adapter — Master Plan & Durum Raporu

> **Bu dosya, projeye dahil olacak her AI asistanı (Claude, GPT, Antigravity, Copilot, vb.) için tek ve
> güncel referans kaynağıdır.** Yeni bir oturuma başlamadan önce bu dosyayı baştan sona okuyun.
> Mimari kararlar, tamamlanan işler, bilinen sorunlar ve bir sonraki adımlar burada tutulur.
> Güncellemeler bu dosyaya eklenir, eski kararlar silinmez — üzerine "GÜNCELLEME" bölümleri eklenir.

**Son güncelleme:** 2026-09-09
**Durum:** Adapter servisi ve C++ köprüsü kodlanmış ve birim testleri geçmiş durumda. Canlı LLM testinde
kritik bir model sorunu bulundu (aşağıda "BİLİNEN SORUNLAR" bölümüne bakın) — oyun içi test öncesi çözülmeli.

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
└── tests/                       # 16 test — hepsi geçiyor (bkz. Bölüm 5)
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

1. **Birim testleri:** `pytest` ile `mmo-llm-adapter/tests/` içindeki 16 test **hepsi PASS**.
   (`test_api_endpoints.py`, `test_bubble_priority.py`, `test_handover_state.py`, `test_locales.py`, `test_mock_llm.py`)
2. **Servis canlı başlatma:** `run_adapter.bat` düzeltildi (artık `.venv\Scripts\python.exe` kullanıyor,
   önceden sistem Python'unu çağırıp `uvicorn bulunamadı` hatası veriyordu — düzeltildi ve doğrulandı).
3. **`/health` testi:** Gerçek çalışan serviste `curl`/`Invoke-RestMethod` ile test edildi, beklenen JSON döndü.
4. **Uçtan uca `/v1/metin2/event` testi:** Gerçek bir whisper event'i gönderildi, adapter Ollama'ya
   (`playerbot-4b` modeli) gerçek bir HTTP isteği attı (200 OK, ~11s), fakat **cevap boş döndü** (bkz. Bölüm 6).
5. **Git durumu:** `mmo-llm-adapter/` klasörü henüz **untracked** (commit edilmemiş). C++ tarafındaki
   3 dosya (`playerbot_llm_bridge.h` yeni, `playerbot_chat_trade.h` ve `playerbot_manager.cpp` değişti)
   da henüz commit edilmemiş durumda — working tree'de bekliyor.

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

1. **[TAMAMLANDI]** Bölüm 6.1'deki thinking-model / boş cevap sorunu `ollama_native` provider ile
   çözüldü; `config.yaml`'da `llm.provider: "ollama_native"` ve `llm.think: false` set edilmeli.
2. Düzeltmeden sonra `/v1/metin2/event` ile uçtan uca gerçek cevap testini tekrar doğrula.
3. `mmo-llm-adapter/` klasörünü ve C++ köprü değişikliklerini (`playerbot_llm_bridge.h`,
   `playerbot_chat_trade.h`, `playerbot_manager.cpp`) commit'le.
4. Docker/staged build ağacına C++ değişikliklerinin senkronize olduğunu doğrula (linux-port build).
5. Oyun içi canlı test: sunucuyu başlat, bir bota `/w [BotAdı] mesaj` ile fısılda, 1-2 saniyede
   Türkçe cevap gelip gelmediğini doğrula, 120s sonra botun rutine dönüp dönmediğini gözlemle.
6. (İleri aşama) Macro Pulse / arka plan botlar için toplu güncelleme mekanizmasını uygula (henüz yapılmadı).

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
