# PRD — FALOCHRON (Maritime Broadcast Fusion Node)

| | |
|---|---|
| **Wersja** | 0.1 (draft do iteracji) |
| **Data** | 07.09.2026 |
| **Wydarzenie** | Baltic Dual Use Hackathon, 11–13.09.2026, Biblioteka UG, Gdańsk |
| **Ścieżka** | AI (narracyjnie: critical infrastructure / resilience; opcjonalnie Space przez kontekst GNSS) |
| **Kategoria** | FROM SCRATCH — przed wydarzeniem wyłącznie research, środowisko, gold set, cache i testy pojedynczych komponentów (dozwolone regulaminem, §D5.80); implementacja pipeline'u startuje 11.09 |
| **Zespół** | solo |
| **Nazwa** | robocza; alternatywy: SeaScribe, MSI-Edge, Bosman |

---

## 1. One-liner

**Przenośny, w pełni offline'owy węzeł, który zamienia morskie kanały rozgłoszeniowe — NAVTEX (tekst i radio 518 kHz) oraz komunikację głosową VHF — w zweryfikowane, ustrukturyzowane zdarzenia zgodne z modelem S-124, koreluje je czasoprzestrzennie i publikuje na lokalną mapę oraz do otwartych interfejsów (GeoJSON/CAP), bez żadnej zależności od chmury.**

SLM pełni rolę warstwy ekstrakcji i normalizacji — nie detektora zagrożeń i nie decydenta.

---

## 2. Problem i kontekst

Świadomość sytuacyjna na Bałtyku opiera się dziś w dużej mierze na AIS i GNSS. Oba są aktywnie degradowane: zasięg spoofingu/jammingu GPS z obszaru Kaliningradu obejmuje ok. 450 km i wody siedmiu państw regionu. Tymczasem równolegle działają kanały **niezależne od GNSS**, nadawane „w eter" dla wszystkich:

- **NAVTEX** (518 kHz międzynarodowo po angielsku, 490 kHz w językach narodowych): ostrzeżenia nawigacyjne, sztormowe, informacje o ćwiczeniach, uszkodzeniach infrastruktury, wrakach — SITOR-B/CCIR 476, 100 Bd, sloty 10-minutowe co 4 h na stację.
- **Tekstowe publikacje MSI**: ostrzeżenia nawigacyjne BHMW (polskie wody), komunikaty NAVAREA — dostępne jako tekst, ale nieustrukturyzowane.
- **VHF** (156–162 MHz): komunikacja głosowa statek–statek i statek–brzeg (SMCP), meldunki o zdarzeniach.

Te strumienie czyta dziś człowiek. Nikt nie oferuje małego, lokalnego urządzenia, które sprowadza je do wspólnego, audytowalnego schematu zdarzeń i utrzymuje obraz, gdy padnie łączność z Internetem lub gdy AIS przestaje być wiarygodny.

**Teza projektu:** critical operations should degrade gracefully when the cloud — and GNSS — disappear.

---

## 3. Pozycjonowanie i novelty claim

**Nie budujemy** systemu wykrywania podejrzanych jednostek (to robią Saab Situation Detector, Windward), platformy C2 ani kolejnego trackera AIS.

**Budujemy** warstwę o jeden krok wcześniej: *ingestion & normalization layer* dla morskich kanałów rozgłoszeniowych, która może zasilać istniejące systemy (GIS, TAK/COP, CEM, tracker AIS-owy) zamiast z nimi konkurować.

Novelty do pitchu (EN):
> "Existing maritime platforms track ships. We listen to what the sea *broadcasts* — NAVTEX over the air, navigational warnings as text, VHF voice — and turn it into trustworthy, interoperable, geo-referenced events on a box that keeps working with no cloud and no GNSS. Sub-billion models, fully on-premise."

Trzy filary przewagi:
1. **Luka rynkowa** — fuzja NAVTEX-RF + NAVTEX-tekst + VHF-głos w jeden schemat nie istnieje ani komercyjnie, ani w OSS (rozdz. 11).
2. **Odporność** — kanały wejściowe niezależne od GNSS/Internetu; krytyczna ścieżka działa air-gapped.
3. **Interoperacyjność** — schemat oparty o pola IMO S-124 (natywny standard MSI — sygnał wiedzy domenowej dla jury) z eksportem GeoJSON/CAP.

---

## 4. Użytkownicy i scenariusze (dual-use)

| Persona | Zastosowanie cywilne (dzień powszedni) | Zastosowanie kryzysowe (dual-use) |
|---|---|---|
| Operator małego portu / mariny | Automatyczna tablica aktualnych ostrzeżeń i zamknięć akwenów na mapie, bez ręcznego czytania NAVTEX-u | Lokalny obraz zdarzeń przy odciętej łączności |
| Zarządzanie kryzysowe wybrzeża / służby | Monitoring MSI dla operacji brzegowych | Węzeł świadomości sytuacyjnej odporny na jamming GNSS i utratę WAN |
| Analityk / badacz bezpieczeństwa morskiego | Ustrukturyzowane archiwum ostrzeżeń z proweniencją do analiz trendów | Korelacja meldunków głosowych z ostrzeżeniami przy incydentach infrastrukturalnych |

Scenariusz demo (finał): ostrzeżenie NAVTEX o pracach przy kablu + meldunek głosowy VHF o jednostce w tym rejonie → jedna skorelowana karta zdarzenia na mapie → **fizyczne odłączenie WAN** → kolejny meldunek nadal przetworzony → powrót łączności → synchronizacja do drugiego węzła.

---

## 5. Cele i non-goals

### Cele (MVP, 48 h)
- G1: Trzy kanały wejściowe sprowadzone do jednego schematu zdarzeń (priorytet realizacji: tekst → VHF → SDR-live; SDR z nagrań IQ jest częścią MVP, odbiór na żywo jest stretch).
- G2: 100% poprawności składniowej wyjścia przez constrained decoding; fakty bez pokrycia w źródle → `UNKNOWN`/`null`.
- G3: Korelacja czasoprzestrzenna zdarzeń między kanałami z jawnym progiem i statusem „kandydat", nie auto-merge.
- G4: Mapa offline + eksport GeoJSON; CAP jako drugi format; store-and-forward do drugiego węzła.
- G5: Benchmark kaskady modeli („smallest model that passes") jako artefakt badawczy do pitchu.

### Non-goals
- Żadnej klasyfikacji intencji jednostek („hostile/suspicious") — system relacjonuje, co zostało nadane, z proweniencją.
- Żadnych autonomicznych akcji ani rekomendacji operacyjnych.
- Pełna zgodność z S-124 GML/S-100 (tylko mapowanie pól rdzenia).
- Zastępowanie TAK/CEM/systemów VTS.
- Live nasłuch VHF cudzej korespondencji na demo — używamy nagrań własnych i syntetycznych (patrz 12.4).

---

## 6. Wymagania funkcjonalne

| ID | Wymaganie | Priorytet |
|---|---|---|
| F1 | Ingest tekstu NAVTEX/ostrzeżeń nawigacyjnych (plik/dir watch/wklejka); parser deterministyczny nagłówka (ID stacji + typ + numer, `B1B2B3B4`) przed SLM | MUST |
| F2 | Ingest audio VHF (WAV/strumień) → VAD → ASR offline → normalizacja SMCP → ekstrakcja | MUST |
| F3 | Ingest audio/IQ 518 kHz → demodulacja FSK 170 Hz → dekoder SITOR-B → tekst → ta sama ścieżka co F1; znaki utracone (FEC) oznaczone `*` | MUST (z nagrań), SHOULD (live) |
| F4 | Ekstrakcja do schematu zdarzeń (rozdz. 9) z constrained decoding (JSON Schema/GBNF) | MUST |
| F5 | Walidator deterministyczny: pola obowiązkowe, zakresy współrzędnych (Bałtyk bbox), spójność czasów, słowniki typów; niespełnione → `needs_human_review` | MUST |
| F6 | Geokodowanie offline: lokalny gazeter nazw bałtyckich (latarnie, pławy, akweny, porty) + parsing współrzędnych z tekstu | MUST |
| F7 | Korelator: łączenie zdarzeń z różnych kanałów po (odległość ≤ próg Nm, przecięcie okien czasowych, wspólne encje); wynik jako propozycja z uzasadnieniem | MUST |
| F8 | Mapa offline (kafle lokalne) z warstwami per kanał + lista/karta zdarzenia z surowym źródłem | MUST |
| F9 | Eksport GeoJSON (plik + REST) i CAP 1.2; CoT/TAK jako stretch | MUST / SHOULD |
| F10 | Event store append-only (SQLite) z proweniencją: hash surowego wejścia, `model_id`, `prompt_version`, `schema_version`; korekty jako nowe wersje | MUST |
| F11 | Store-and-forward: trwała kolejka, idempotentna synchronizacja po UUID do drugiego węzła po powrocie łączności | SHOULD |
| F12 | Router kaskady: reguły → tier-1 → tier-2 → tier-3; eskalacja wyłącznie po testowalnych regułach (brak pól, konflikt, walidator), nigdy po „confidence" modelu | MUST |
| F13 | Eksperyment: naprawa zniekształconych znaków SITOR-B (`*`) przez SLM jako masked restoration, z oznaczeniem pól naprawionych | COULD |

## 7. Wymagania niefunkcjonalne

| ID | Wymaganie |
|---|---|
| N1 | **Offline-first:** zerwanie WAN nie przerywa ASR, dekodowania, ekstrakcji, walidacji, mapy ani audytu — to warunek architektoniczny, nie feature |
| N2 | Języki: PL + EN na wejściu (NAVTEX 518 = EN; 490/BHMW/VHF = PL); UI i pitch EN |
| N3 | Footprint celu: pełny pipeline tekstowy działa na 8–16 GB RAM (pocket node); ASR + tier-3 na 32 GB (field hub) |
| N4 | Latencja (cel do kalibracji na benchmarku, nie obietnica): p95 tekst→zwalidowany event ≤ 2 s na field hubie dla tier-2 |
| N5 | Model bez dostępu do sieci i bez tool-calls w etapie ekstrakcji; wejście traktowane jako dane, nie instrukcje (odporność na injection w treści meldunków) |
| N6 | Powtarzalne demo: skrypt resetu, pełny lokalny cache modeli/kontenerów/kafli, drugi laptop jako backup |
| N7 | Stack świadomie niezależny od istniejącej infrastruktury domowej autora — czysty, przenośny build (repo + kontenery + modele na dysku/pendrive) |
| N8 | Licencje wszystkich komponentów zgodne z regulaminem (open source / posiadane prawa) |

---

## 8. Architektura

```
  KANAŁY WEJŚCIOWE                    RDZEŃ (wszystko lokalnie)                       WYJŚCIA
┌────────────────────┐   ┌──────────────────────────────────────────────┐   ┌──────────────────┐
│ NAVTEX tekst       │──▶│ Adaptery ──▶ Router kaskady                  │   │ Mapa offline     │
│ (BHMW/NAVAREA/plik)│   │              reguły → 0.35B → 0.8B → 3B      │──▶│ (MapLibre+kafle) │
├────────────────────┤   │                   │                          │   ├──────────────────┤
│ SDR 518 kHz        │   │                   ▼                          │   │ GeoJSON (REST)   │
│ IQ→FSK→SITOR-B     │──▶│ Constrained extraction (JSON Schema/GBNF)    │──▶│ CAP 1.2          │
│ (fldigi/YaND)      │   │                   │                          │   │ CoT/TAK (stretch)│
├────────────────────┤   │                   ▼                          │   ├──────────────────┤
│ VHF audio          │   │ Walidator determin. ──▶ Korelator geo/czas   │   │ Sync do 2. node  │
│ VAD→whisper.cpp    │──▶│                   │                          │   │ (store&forward)  │
└────────────────────┘   │                   ▼                          │   └──────────────────┘
                         │ Event store (SQLite, append-only,            │
                         │ proweniencja + hash + wersje)                │
                         └──────────────────────────────────────────────┘
```

Zasady:
- **SLM jest jednym etapem potoku; za nim zawsze stoi warstwa deterministyczna.** Model proponuje strukturę — nie zapisuje, nie publikuje, nie decyduje.
- Runtime: **llama.cpp** (serwer z API OpenAI-compat, GBNF/`json_schema` — składniowa poprawność wymuszona, nie „poproszona"), **whisper.cpp** lub **sherpa-onnx** dla ASR, **fldigi/YaND** dla SITOR-B.
- Deployment MVP: pojedynczy host, Docker Compose (albo gołe binarki + systemd). K3s tylko jeśli demo dwuwęzłowe okaże się stabilne; KubeEdge poza zakresem hackathonu.
- `schema-valid ≠ factually correct`: forma z gramatyki, prawda z walidatorów, dowodów i człowieka.

---

## 9. Schemat zdarzenia (rdzeń, wersja 0.1)

Mapowanie na S-124 (pola natywne standardu MSI) + rozszerzenia projektu:

| Pole | Odpowiednik S-124 | Uwagi |
|---|---|---|
| `event_type` | warningType | Enum: NAV_WARNING, MET_WARNING, EXERCISE, INFRA_DAMAGE, WRECK, OBSTRUCTION, VOICE_REPORT, OTHER |
| `warning_id` | warningIdentifier / warningNumber | Z nagłówka NAVTEX gdy dostępny |
| `issued_at` / `valid_from` / `valid_to` | publicationTime / dateTimeStart / dateTimeEnd | UTC; `null` gdy nie podano |
| `geometry` | geometry (Point/Curve/Surface) | GeoJSON; `null` gdy tylko nazwa akwenu |
| `location_name` | locationName | Surowe odniesienie tekstowe zawsze zachowane |
| `agency` | agencyResponsibleForProduction | Stacja NAVTEX / BHMW / "VHF" |
| `source` | — | `{channel: TEXT|SDR|VOICE, id, raw_hash}` |
| `provenance` | — | `{model_id, prompt_version, schema_version, restored_chars: []}` |
| `correlation` | — | `{candidate_of: [], basis: {distance_nm, time_overlap, entities}}` |
| `needs_human_review` | — | Wynik reguł walidatora, nie „nastroju" modelu |

Przykład (wejście SDR, ostrzeżenie o ćwiczeniach):

```json
{
  "event_type": "EXERCISE",
  "warning_id": "SE-A-0842",
  "issued_at": "2026-09-12T08:40:00Z",
  "valid_from": "2026-09-12T10:00:00Z",
  "valid_to": "2026-09-12T16:00:00Z",
  "geometry": {"type": "Point", "coordinates": [18.95, 55.21]},
  "location_name": "AREA SOUTH OF UTKLIPPAN",
  "agency": "NAVTEX/518",
  "source": {"channel": "SDR", "id": "rtlsdr-01", "raw_hash": "sha256:…"},
  "provenance": {"model_id": "qwen3.5-0.8b-q4", "prompt_version": "0.3", "schema_version": "0.1", "restored_chars": []},
  "correlation": {"candidate_of": [], "basis": null},
  "needs_human_review": false
}
```

Reguły: enumy tylko dla stabilnych pojęć; każde pole dopuszcza `UNKNOWN`/`null`; adaptery wyjściowe (CAP/GeoJSON) mapują albo odrzucają — nigdy nie dopowiadają.

---

## 10. Wykaz modeli

### 10.1. Kaskada SLM (ekstrakcja/normalizacja)

Zasada: **smallest model that passes** — próg PASS zdefiniowany przed benchmarkiem (rozdz. 13), router eskaluje wyłącznie po regułach.

| Tier | Model | Parametry | Licencja | Kontekst | Rola | Status weryfikacji (09.2026) | Uwagi |
|---|---|---|---|---|---|---|---|
| 0 | reguły/regex/parsery | — | — | — | nagłówki NAVTEX, współrzędne, daty, MMSI, słowniki | n/d | pokaże, które pola w ogóle nie potrzebują NLP |
| 1 | **Granite 4.0 350M** | 0.35B | Apache 2.0 | — | klasyfikacja typu, proste pola | wg dok. IBM (za raportem GPT) | bezpieczna licencja |
| 1 | LFM2.5-230M / 350M | 0.23/0.35B | LFM Open License v1.0 | — | eksperyment ultra-light | ✅ potwierdzone (premiery VI i III 2026) | karta nie deklaruje PL → tor EN |
| 2 | **Qwen3.5-0.8B** — kandydat główny | 0.8B | Apache 2.0 | 262K | główna ekstrakcja PL/EN | ✅ potwierdzone (premiera II/III 2026; eksporty q4_0 pod llama.cpp) | ~200 języków, thinking opt-in, multimodal |
| 2 | Granite 4.0 1B | 1B | Apache 2.0 | — | alternatywa tier-2 | wg dok. IBM | dobra kompatybilność llama.cpp |
| 2 | LFM2.5-1.2B | 1.2B | LFM Open License v1.0 | 33K | tor EN / porównanie | ✅ potwierdzone (premiera I 2026; <1 GB RAM, 239 tok/s na CPU AMD wg vendora) | **brak PL na karcie modelu** — nie do polskich meldunków |
| 3 | **Ministral 3 3B** | 3B | Apache 2.0 | 256K | fallback trudne przypadki, structured outputs | wg dok. Mistral (za raportem GPT) | vision opcjonalnie |
| 3 | Phi-4-mini | 3.8B | MIT | 128K | alternatywa fallbacku | ✅ (karta wymienia PL i UA) | mocny multilingual |
| 3 | Qwen3-1.7B / Qwen3-4B | 1.7/4B | Apache 2.0 | 32K+ | znane, sprawdzone alternatywy | ✅ | plan B gdyby 3.5 zawiodło na PL |
| opc. | Gemma 3n E2B | ~2B eff. | Gemma Terms | — | tylko jeśli eksperyment audio-direct | ✅ (~2 GB footprint wg Google) | poza MVP |

Wszystkie w kwantyzacji Q4 przez llama.cpp; temperatura ~0; identyczny prompt i schema dla całej kaskady.

### 10.2. ASR (kanał VHF)

| Komponent | Rola | Licencja | Uwagi |
|---|---|---|---|
| **whisper.cpp** + Whisper `small`/`medium`/`large-v3-turbo` | ASR PL/EN offline | MIT (silnik i wagi) | benchmark na własnych nagraniach zdecyduje o rozmiarze; kwantyzacja ggml |
| sherpa-onnx | alternatywny, w pełni lokalny toolkit ASR/TTS | Apache 2.0 | opcja na ARM/embedded |
| Silero VAD | detekcja mowy przed ASR | MIT | tnie transmisje na wypowiedzi |
| faster-whisper (CTranslate2) | batchowe przetwarzanie nagrań w benchmarku | MIT | poza ścieżką krytyczną demo |
| Fine-tuning (opcjonalny, po hackathonie) | adaptacja do domeny morskiej | — | przepis z literatury: syntetyczny korpus SMCP z nazwami bałtyckimi + augmentacja szumem kanału (podejście Fraunhofer CML) |

Metryka ASR: nie sam WER, lecz **recall encji morskich** (nazwy jednostek, lokalizacje, liczby) — za literaturą maritime-ASR.

### 10.3. Dekodowanie SITOR-B (kanał SDR)

| Komponent | Rola | Uwagi |
|---|---|---|
| fldigi | demodulacja/dekod NAVTEX i SITOR-B, sterowanie przez XML-RPC | Linux, skryptowalne — kandydat główny |
| YaND (Yet another Navtex Decoder) | dedykowany dekoder NAVTEX | Windows; referencja porównawcza |
| MultiPSK | dekoder wielomodowy z SITOR-B | referencja |
| Generator testowy SITOR-B | syntetyczny bitstream CCIR 476 z poprawnym FEC i fazowaniem (wzorzec: baltic-lab.com) | **kluczowy dla demo** — pełny tor RF bez zależności od propagacji |
| Eksperyment F13 | SLM jako masked-restoration znaków `*` po błędach FEC | analogiczny problem rozwiązywano Transformerem w literaturze (JMSE 2025) |

---

## 11. Istniejące rozwiązania i luka

| Rozwiązanie | Kategoria | Co robi dobrze | Czego nie robi (nasza luka) |
|---|---|---|---|
| NATO Baltic Sentry / CTF Baltic (od I 2025) | operacja państwowa | fregaty, lotnictwo patrolowe, drony morskie; AI buduje „patterns of life" ruchu | niedostępne, nieprzenośne, zamknięte |
| Nordic Warden (JEF) | system państwowy | AI ocenia ryzyko jednostek wchodzących w obszary zainteresowania (m.in. AIS) | j.w.; wejście sensorowe, nie NLP kanałów rozgłoszeniowych |
| Shadow Fleet Tracker Light (OSS) | tracker AIS | lokalny, bez chmury; watchlista GUR, bliskość kabli, loitering | czysto AIS — zero NAVTEX/VHF/NLP; **najbliższy sąsiad i potencjalny downstream** |
| Saab Situation Detector | detekcja komercyjna | anomalie zachowań: rendezvous, AIS dropout, fake ID | detekcja z AIS/radaru, nie ekstrakcja z kanałów tekstowo-głosowych |
| Windward | maritime AI intelligence | wielosensorowa analityka, ochrona infrastruktury podmorskiej | chmurowa platforma enterprise; nie edge, nie broadcast-NLP |
| Fraunhofer CML marFM; Fintraffic (fiński VTS); projekt ARTUS | badania/pilotaże ASR | transkrypcja VHF, fine-tuning Whispera na danych syntetycznych, radionamierzanie | pojedynczy kanał; bez fuzji, bez schematu zdarzeń, bez edge-produktu |
| Badania NLP NAVTEX (TF-IDF adaptacyjny; Bi-LSTM CRF; Transformer-restoration; mapowanie S-124/IMO Compendium) | akademia | klasyfikacja i tagowanie semantyczne NAVTEX; gotowy szkielet mapowania pól | metody klasyczne, bez SLM, bez pipeline'u end-to-end, bez RF |
| EdgeRunner AI (Tactical-24B, 20B, Camo z US Army, WarClaw) | defense edge SLM | dowód, że wzorzec „air-gapped SLM na urządzeniu" działa produkcyjnie | asystent proceduralny, nie pasywny nasłuch morski; waliduje wzorzec, nie wypełnia luki |
| MarineTraffic / AISStream | dane AIS | tani strumień pozycji | opcjonalny 4. kanał **kontekstowy** dla korelatora (nie budujemy na nim wartości) |

**Synteza:** rynek dzieli się na (a) wielkie platformy państwowe/enterprise, (b) trackery czysto AIS-owe, (c) akademickie prototypy pojedynczego kanału. Przecięcie „kanały rozgłoszeniowe × SLM × przenośny on-prem × otwarte standardy" jest puste.

---

## 12. Sprzęt on-premise

### 12.1. Profile maszyn (mini PC)

Ceny orientacyjne na IX 2026 i **bardzo zmienne** — braki DRAM podniosły ceny maszyn 128 GB o 60–120% między VI a VIII 2026; weryfikować w dniu zakupu.

| Profil | Maszyna | CPU / akcelerator | RAM | Cena orient. | Co uciągnie | Rola w projekcie |
|---|---|---|---|---|---|---|
| **Pocket** | Raspberry Pi 5 (16 GB) + NVMe HAT | 4× A76 | 16 GB | ~120–150 USD + dysk | tier-1/2 Q4 na CPU (wolno), Whisper `base/small` | drugi węzeł do demo sync; dowód „działa na SBC" |
| **Pocket** | Lenovo ThinkCentre Tiny M720q/M920q (używany) | i5-8500T; slot PCIe x8 (riser) na przyszłość | 16–64 GB DDR4 | kilkaset zł (rynek wtórny) | tier-1/2 komfortowo, tier-3 Q4 na CPU akceptowalnie, Whisper `small` | **kandydat główny na węzeł demo** — tani, x86, znany, 1L |
| **Pocket/GPU** | NVIDIA Jetson Orin Nano Super | 6× A78AE + 1024 CUDA, 67 TOPS, 8 GB LPDDR5 (102 GB/s), 7–25 W | 8 GB | 249 USD | Whisper na GPU + tier-1/2; CUDA end-to-end | opcja, jeśli ASR na CPU okaże się za wolne; zasilanie z powerbanku PD |
| **Field hub** | mini PC Ryzen AI 9 HX 370 (Beelink SER9, Minisforum AI X1 Pro) | 12 rdzeni, NPU XDNA2 50 TOPS, iGPU 890M | 32 GB+ | ~860–1360 USD (skoki cen) | cała kaskada do 3B + Whisper `large-v3-turbo` równolegle | docelowy „field hub", jeśli budżet pozwoli |
| **Field hub** | Mac mini M4 (16 GB) | Apple M4, 120 GB/s unified | 16 GB | 599 USD | bardzo dobre tok/s w llama.cpp/Metal | opcja; macOS odstaje od reszty stacku Linux |
| **Site hub** (poza zakresem hackathonu) | Strix Halo / Ryzen AI Max+ 395 (GMKtec EVO-X2, Framework Desktop) | 40 CU RDNA3.5, do 128 GB unified, ~256 GB/s | 64–128 GB | 64 GB ~2000 USD; 128 GB 3300–4300 USD (VIII 2026) | modele 30–70B+, batch | pokazuje ścieżkę skalowania w pitchu — **nie kupować pod hackathon** |

Wnioski zakupowe: projekt **celowo nie wymaga** drogiego sprzętu — to teza produktu. Minimalny zestaw demo: posiadany laptop (dev + field hub) + jeden tani węzeł (M720q albo RPi5) do sceny „sync po odzyskaniu łączności". Jetson tylko, jeśli benchmark ASR na CPU nie zmieści się w celu latencji.

Nie podajemy tok/s bez pomiaru na własnym sprzęcie — benchmark (rozdz. 13) mierzy latencję i RAM na faktycznie użytym węźle; jedyna liczba vendorowa w tym PRD (239 tok/s LFM2.5-1.2B) jest oznaczona jako deklaracja producenta.

### 12.2. Tor radiowy (SDR)

| Element | Wybór | Uwagi |
|---|---|---|
| Odbiornik | RTL-SDR Blog V4 (~35–45 USD) lub Airspy HF+ Discovery (~170 USD) | V4 ma wbudowany upconverter HF/MF — wystarczy na start; HF+ znacząco lepszy na 518 kHz |
| Antena | aktywna mini-whip lub pętla magnetyczna | 518 kHz w mieście = silny QRM; pętla ogranicza zakłócenia lokalne |
| Parametry sygnału | FSK 100 Bd, shift 170 Hz, CCIR 476 (4 z 7 bitów „1"), sloty 10 min / 4 h | 518 kHz = EN międzynarodowo; 490 kHz = języki narodowe |
| Pipeline | SDR → demod (fldigi bezpośrednio z audio/IQ) → tekst przez XML-RPC → adapter F3 | |

### 12.3. Krytyczne dla demo: „RF-in-a-box"

Odbiór 518 kHz **wewnątrz biblioteki UG jest praktycznie niemożliwy** (beton, QRM, sloty czasowe co 4 h). Decyzja (07.09): **warstwą podstawową demo jest prawdziwy eter nagrany wcześniej** — IQ/audio stacji bałtyckich zebrane przez odbiorniki KiwiSDR (kiwirecorder; harmonogram i komendy w Aneksie A), odtwarzane na demo przez wirtualny kabel audio do dekodera — identyczna ścieżka jak przy odbiorze na żywo. Syntetyczny generator SITOR-B (poprawny CCIR 476 + FEC + fazowanie) zostaje jako test harness i fallback na wypadek zbyt niskiego SNR nagrań.

To nie jest obejście — dekoder dostaje dokładnie ten sygnał, który wisiał w eterze; różni się wyłącznie moment odbioru, co mówimy jury wprost.

### 12.4. Uwagi prawne (do potwierdzenia z mentorem)

Odbiór NAVTEX to publiczna informacja bezpieczeństwa (MSI) — bez kontrowersji. Nasłuch VHF: samo posiadanie odbiornika nie wymaga pozwolenia, ale ujawnianie treści cudzej korespondencji radiowej jest w Polsce ograniczone prawem — dlatego demo i benchmark używają wyłącznie nagrań własnych/syntetycznych, a produkt docelowy adresujemy do podmiotów uprawnionych (VTS, służby, kapitanaty).

### 12.5. Compute pomocnicze: Modal (poza ścieżką krytyczną)

Zasada brzegowa: **Modal nie dotyka ścieżki krytycznej ani demo** — kill-WAN pozostaje nienaruszony. Wzorzec: *fabryka w chmurze, produkt na brzegu*. Jednorazowe, ciężkie joby (synteza danych, masowa ewaluacja, fine-tuning) idą na sekundowo rozliczane GPU; każdy artefakt (korpusy, adaptery, GGUF, raporty) wraca natychmiast do lokalnego cache i na pendrive. W pitchu to argument, nie kompromis: „train anywhere, run everywhere".

Ekonomia (stan IX 2026): rozliczenie per sekunda, bez opłat za idle; plan Starter = 0 USD/mies. + **30 USD kredytów miesięcznie** (≈ 7,6 h H100 albo ~50 h T4). Stawki bazowe: H100 ~3,95 USD/h, A100-80GB ~2,50 USD/h, A100-40GB ~2,10 USD/h, L40S ~1,95 USD/h, L4 ~0,80 USD/h, T4 ~0,59 USD/h. Uwaga: egzekucja non-preemptible i wymuszenie regionu podnoszą stawkę (do ~3×) — krótkie joby zostają na ustawieniach domyślnych; dłuższe (W5) z checkpointami zamiast trybu non-preemptible.

| WS | Zadanie | GPU / czas orient. | Koszt orient. | Artefakt (mirrorowany lokalnie) |
|---|---|---|---|---|
| W1 | Synteza gold/train setu: duży otwarty LLM (np. gpt-oss-120B / Qwen-72B na vLLM) generuje warianty NAVTEX (EN + zniekształcenia `*`), meldunki VHF PL/EN wg SMCP, etykiety JSON; drugi przebieg LLM-as-judge weryfikuje etykiety | 1× H100 lub A100-80, 2–3 h | ~8–12 USD | `data/gold_v1.jsonl`, `data/train_v1.jsonl` |
| W2 | Korpus audio VHF: TTS wieloma głosami → augmentacja kanału (pasmo 300–3400 Hz, szum, przester, zaniki) | L4/T4, ~1 h | <1 USD | `audio/vhf_synth/*.wav` + transkrypty |
| W3 | Sweep benchmarku kaskady: te same GGUF Q4 + gramatyki co na edge, `.map()` równolegle po (model × prompt × przykład) | kontenery CPU (+ ew. L4), minuty–1 h | ~1–3 USD | `bench/report.md`, front Pareto, wybór tierów |
| W4 | QLoRA Qwen3.5-0.8B (i ew. Granite 350M) na zadaniu tekst→JSON; merge → konwersja do GGUF Q4 | 1× A100-40, 20–60 min | ~1–2 USD | `models/qwen35-0.8b-falochron-q4.gguf` |
| W5 | (opcjonalnie) Fine-tuning Whisper `small` na syntetycznym PL-maritime (podejście Fraunhofer CML) | 1× A100, 1–3 h, checkpointy | ~5–8 USD | `models/whisper-small-mar-pl` (+ ggml) |

Suma: **~15–25 USD — mieści się w darmowym kredycie Starter.**

Zasady:
- Jakość (F1, unsupported-fact, entity recall) mierzona na Modalu jest przenośna, bo używamy identycznych GGUF i gramatyk co na węźle; **latencja i RAM raportowane wyłącznie z pomiaru na docelowym sprzęcie** (Modal ich nie zastępuje).
- Zgodność z FROM SCRATCH: W1–W3 i dry-runy W4/W5 przed 11.09 mieszczą się w „testowaniu pojedynczych technologii i przygotowaniu komponentów" (§D5.80). Pełny bieg W4 odpalamy w oknie 6–16 h hackathonu jako job w tle (pipeline i tak powstaje lokalnie w tym czasie); alternatywa — gotowy adapter zadeklarowany jawnie jako przygotowany komponent. W razie wątpliwości: pytanie do organizatora, regulamin wprost to przewiduje.
- Higiena: tokeny (HF) w Modal Secrets; artefakty w `modal.Volume` `falochron-artifacts`, po każdym jobie `modal volume get` do lokalnego cache; repo `modal_jobs/{datagen,tts,bench,finetune}.py` na wspólnym `modal.Image`.
- Dzień demo: zero wywołań Modala w ścieżce pokazowej; konto może nie istnieć i demo się nie zmienia.

---

## 13. Metryki i benchmark

Gold set: 200–300 przykładów (PL ~100, EN ~100, noisy-ASR/`*`-corrupted ~50), etykiety ręczne, **progi PASS zdefiniowane przed uruchomieniem porównania**.

| Metryka | Definicja | Cel |
|---|---|---|
| Schema validity | % wyjść przechodzących JSON Schema | 100% (gwarantowane gramatyką; błąd = bug runtime) |
| Field F1 | exact match/F1 per pole (typ, czasy, liczby, geometria) | ≥ 0.85 tier-2 na gold |
| **Unsupported-fact rate** | % wartości bez pokrycia w źródle | ≤ 2% — **główna metryka bezpieczeństwa** |
| Omission rate | % faktów źródłowych pominiętych | raportowane |
| Geo-resolution | % zdarzeń z poprawną geometrią lub poprawnym `location_name` | ≥ 0.9 |
| Latencja p50/p95 | tekst → zwalidowany event | p95 ≤ 2 s (field hub, tier-2) — do kalibracji |
| Peak RSS / rozmiar modelu | footprint per tier | raportowane |
| Escalation rate | % wejść eskalowanych do wyższego tieru / człowieka | raportowane |
| ASR: entity recall | recall nazw jednostek/lokalizacji/liczb | raportowane vs rozmiar Whispera |

Wynik do pitchu: front Pareto jakość × latencja × RAM + jedno zdanie typu „0.8B przechodzi próg przy X ms i Y MB; 3B potrzebny tylko dla N% przypadków".

---

## 14. Plan

### 14.1. Przed 11.09 (dozwolone w FROM SCRATCH — bez implementacji pipeline'u)

- [ ] Zamrozić schema v0.1 + słowniki typów; przygotować JSON Schema i gramatykę GBNF.
- [ ] Gold set 200+ przykładów z etykietami (NAVTEX z publicznych archiwów, syntetyczne meldunki VHF PL/EN nagrane własnym głosem/TTS + szum).
- [ ] Harness benchmarku (skrypt: model × prompt × gold → metryki) i **przebenchmarkować kaskadę 350M/0.8B/1B/1.2B/3B jako test pojedynczych technologii**.
- [ ] Modal: workspace + `modal.Volume` + Secrets skonfigurowane; joby W1–W3 (rozdz. 12.5) wykonane, korpusy i raport benchmarku zmirrorowane lokalnie i na pendrive.
- [ ] Modal: dry-run W4 (QLoRA na próbce ~200 przykładów) potwierdza, że skrypt działa end-to-end — pełny bieg zostaje na okno 6–16 h eventu.
- [ ] Przetestować whisper.cpp vs sherpa-onnx na ~20 nagraniach z szumem; wybrać rozmiar.
- [ ] Skonfigurować fldigi (SITOR-B/NAVTEX, XML-RPC); wykonać nagrania 518 kHz wg harmonogramu z Aneksu A (≥6 czystych transmisji z ≥2 stacji, z dwóch KiwiSDR-ów równolegle); generator syntetyczny jako fallback.
- [ ] Cache offline: modele GGUF, obrazy kontenerów, kafle mapy Bałtyku, dokumentacja; wszystko też na pendrive.
- [ ] Gazeter bałtycki (nazwy → współrzędne) z otwartych danych.
- [ ] Szkielet pitchu 3 min (EN) + lista pytań do mentorów (public safety, cyber, embedded, GovTech).
- [ ] Skrypt resetu demo + checklista fault-injection.

### 14.2. 48 h (11–13.09)

| Okno | Cel | Definition of done |
|---|---|---|
| 0–6 h | Kontrakt i szkielet | schema v1.0 w repo, event store, serwer llama.cpp, 10 testów kontraktu |
| 6–14 h | Kanał tekstowy | parser nagłówka + constrained extraction + walidator; 30–50 testów zielonych; równolegle start joba W4 (QLoRA na Modalu, w tle) |
| 14–20 h | Mapa + eksport | zdarzenia na mapie offline; GeoJSON REST; karta zdarzenia z surowym źródłem |
| 20–28 h | Kanał SDR (nagrania) | IQ/audio → fldigi → tekst → event; obsługa `*`; generator syntetyczny w demo |
| 28–36 h | Kanał VHF + korelacja | VAD → ASR → event; korelator z progami; karta skorelowana |
| 36–42 h | Benchmark + hardening | tabela kaskady na gold; kill-WAN test; sync do 2. węzła (jeśli stabilny) |
| 42–48 h | Freeze | zero nowych funkcji; reset script; backup; próba pitchu ×3 |

Zasada cięcia zakresu przy poślizgu: **tekst > mapa > VHF > SDR-live**; sync dwuwęzłowy i F13 odpadają pierwsze.

---

## 15. Demo finałowe (3 min)

1. (0:00–0:25) Problem: chmura i GNSS to pierwsze ofiary kryzysu; kanały rozgłoszeniowe nadal nadają — ale czyta je człowiek.
2. (0:25–1:45) Live: syntetyczny sygnał SITOR-B → dekod → event na mapie; ostrzeżenie tekstowe BHMW → event; meldunek głosowy PL → event; korelator łączy dwa z nich w kartę incydentu przy kablu. **Fizyczne wyciągnięcie WAN.** Kolejny meldunek — nadal działa.
3. (1:45–2:20) Powrót łączności → synchronizacja do drugiego węzła (RPi/M720q).
4. (2:20–2:45) Jedna tabela benchmarku: smallest model that passes + unsupported-fact rate.
5. (2:45–3:00) Dual-use close: dziś tablica MSI dla mariny i kapitanatu — w kryzysie węzeł świadomości odporny na jamming. Nie zastępujemy systemów — czynimy ich wejścia odpornymi i interoperacyjnymi.

Zero chat UI. Dwa ekrany: mapa/lista zdarzeń + panel wejść.

---

## 16. Ryzyka

| ID | Ryzyko | P | Wpływ | Mitigacja |
|---|---|---|---|---|
| R1 | Polski ASR w szumie poniżej progu | wys. | śr. | większy Whisper na field hubie; krótkie meldunki; pola z ASR domyślnie `needs_review`; benchmark przed eventem |
| R2 | Brak odbioru 518 kHz na miejscu | pewne | wys. | RF-in-a-box (12.3) zaplanowany od początku, nie jako plan B |
| R3 | Solo + 3 kanały = za szeroko | wys. | wys. | twarda kolejność cięcia (14.2); kanał SDR-live i sync to stretch |
| R4 | Halucynacje podważają wiarygodność przy jury | śr. | wys. | `UNKNOWN`, constrained output, unsupported-fact w pitchu, human-review flag |
| R5 | Fałszywe korelacje (false-merge) | śr. | śr. | korelator proponuje, nie łączy; jawne progi i uzasadnienie na karcie |
| R6 | „Wygląda jak chatbot z mapką" | śr. | wys. | zero chat UI; kill-WAN; standardy S-124/CAP; benchmark jako artefakt |
| R7 | Ceny/dostępność sprzętu (zmienność DRAM) | śr. | nis. | projekt działa na posiadanym sprzęcie; zakupy tylko RTL-SDR (+ ew. Jetson) |
| R8 | Prompt injection w treści meldunku | nis. | śr. | wejście jako dane; brak tool-calls; strict system prompt; walidator za modelem |
| R9 | Demo zależne od sieci/pobrań | śr. | wys. | pełny cache offline + pendrive + drugi laptop |
| R10 | Awaria/limit/preempcja Modala w trakcie eventu | nis. | nis. | Modal wyłącznie poza ścieżką krytyczną; fallback: adapter z dry-runu albo czysty prompting tier-2; artefakty mirrorowane po każdym jobie |

---

## 17. Otwarte pytania

1. Hardware demo: laptop + M720q, czy dokupić Jetsona pod ASR? → decyzja po benchmarku whisper.cpp na CPU (pkt 14.1).
2. AIS jako 4. kanał kontekstowy korelatora (AISStream, tylko gdy WAN jest) — czy dodaje wartości w 48 h, czy rozmywa story „broadcast channels"?
3. CoT/TAK: czy pokazać choć jeden marker w ATAK jako downstream (mocne dla jury), czy zostać przy GeoJSON/CAP?
4. Kategoria potwierdzona jako FROM SCRATCH — pilnować, by przed 11.09 nie powstał kod właściwego pipeline'u (benchmark i konfiguracje komponentów są OK per regulamin).
5. Nazwa: FALOCHRON vs wariant EN-friendly do pitchu.
6. PMR446 jako żywy tor głosowy na demo (para radiotelefonów bez pozwolenia, RTL-SDR odbiera meldunek na 446 MHz): dodać jako trzeci akt demo czy zostać przy nagraniach własnych? Decyzja po testach ASR.

---

## Aneks A. Plan nagrań 518 kHz i źródła danych

### A.1. Harmonogram nagrań (wykonać 7–10.09)

Bałtyckie stacje 518 kHz nadają w 10-minutowych slotach co 4 h (czasy UTC; lokalnie CEST = UTC+2):

| Stacja | ID | Sloty UTC | Wygodne sloty lokalne (CEST) |
|---|---|---|---|
| Bjuröklubb (SE) | H | 0110, 0510, 0910, 1310, 1710, 2110 | 15:10, 19:10, 23:10 |
| Grimeton (SE) | I | 0120, 0520, 0920, 1320, 1720, 2120 | 15:20, 19:20, 23:20 |
| Gislövshammar (SE) | J | 0130, 0530, 0930, 1330, 1730, 2130 | 15:30, 19:30, 23:30 |
| Tallinn (EE) | U | 0320, 0720, 1120, 1520, 1920, 2320 | 13:20, 17:20, 21:20 |

Wykonanie: wybrać 2–3 odbiorniki KiwiSDR znad Bałtyku (mapa kiwisdr.com; przed slotem ręcznie sprawdzić SNR na 518 kHz), start nagrania ~2 min przed slotem:

```
python3 kiwirecorder.py --server-host=<kiwi> --server-port=8073 \
  -f 518 -m iq --kiwi-wav --tlimit=780 \
  --fn=navtex_<stacjaID>_$(date -u +%Y%m%d_%H%M)
```

`--tlimit=780` ≈ 13 min (slot + zapas). Wariant czysto audio: `-m usb -f 516.8`, tak by tony mark/space wypadły w paśmie akustycznym dekodera. kiwirecorder potrafi nagrywać z kilku Kiwi jednocześnie — redundancja na QRM/zanik. Cel: **≥6 czystych, pełnych transmisji z ≥2 stacji** + 2–3 słabe/zaszumione do testów odporności (i do eksperymentu F13).

Odtwarzanie na demo: plik → wirtualne urządzenie audio (snd-aloop / pw-loopback) → fldigi (XML-RPC) → adapter F3 — ta sama ścieżka co przy żywym odbiorze.

### A.2. Źródła danych do gold setu

| Źródło | Typ | Zastosowanie |
|---|---|---|
| frisnit.com/navtex | baza zdekodowanych wiadomości NAVTEX (crowd-fed, wyszukiwarka po stacjach/typach) | prawdziwe teksty bałtyckie: few-shot dla W1 + gold |
| BHMW — ostrzeżenia nawigacyjne | oficjalny tekst PL | gold PL |
| HF: `bonalor/synthetic_maritime_radio_communication` (MARTTS) | 480 syntetycznych nagrań dialogów VHF EN (clean + degraded); SMCP + scenariusze LLM + TTS + post-processing kanału | gotowa ewaluacja toru EN od zaraz; wzorzec metodyczny dla W2 |
| RescueSpeech | publiczny niemiecki korpus mowy SAR | test odporności ASR na szum/kanał |
| korpusy ATC (np. radiotalk) | lotnicze VHF | realizm kanału, nie słownictwo |
| Wikipedia: `Navtex transmission example.ogg` + royalty-free sample NAVTEX | pojedyncze próbki | smoke-test dekodera przed własnymi nagraniami |
| github.com/jks-prv/kiwiclient | narzędzie (kiwirecorder, kiwiclientd) | produkcja własnych nagrań; kiwiclientd podaje audio Kiwi na wirtualną kartę pod fldigi |

### A.3. Status decyzji toru radiowego

Nagrany prawdziwy eter = **warstwa podstawowa** (zatwierdzone 07.09). Generator syntetyczny CCIR 476 = fallback + test harness. PMR446 na żywo = opcja otwarta (rozdz. 17, pyt. 6).

---

## Aneks B. Repozytorium i higiena FROM SCRATCH

Regulamin (§D5.80) wprost dopuszcza przed hackathonem: research, przygotowanie środowiska, **założenie repozytorium**, konfigurację narzędzi, listę i zakup komponentów, przygotowanie sprzętu oraz testowanie pojedynczych technologii/bibliotek/urządzeń — i stanowi, że wykonanie tych czynności nie czyni projektu „rozpoczętym przed hackathonem". Nagrania publicznych transmisji NAVTEX, gold set i benchmarki mieszczą się w tym zakresie (research + komponenty + test technologii). Granica: **kod właściwego pipeline'u nie powstaje przed 11.09**.

Struktura repo:

```
falochron/
├── README.md                 # deklaracja kategorii + jawna lista pre-worku
├── CLAUDE.md                 # brief dla Claude Code (granice FROM SCRATCH + backlog)
├── STATUS.md                 # żywa checklista gotowości (lustro rozdz. 14.1)
├── PRD_FALOCHRON_BDUH2026.md
├── docs/                     # research, notatki, szkielet pitchu
├── data/
│   ├── recordings/518khz/    # nagrania IQ/audio wg Aneksu A.1 (git-lfs)
│   ├── gold/                 # gold set + etykiety (W1)
│   └── audio/vhf_synth/      # korpus VHF (W2) (git-lfs)
├── bench/                    # harness benchmarku + raporty (test technologii)
├── modal_jobs/               # datagen.py, tts.py, bench.py, finetune.py (W1–W5)
├── tools/                    # konfig fldigi, skrypty kiwirecorder, generator CCIR 476
├── cache/                    # GGUF, kafle map, obrazy — w .gitignore, mirror na pendrive
└── src/                      # PUSTE do otwarcia 11.09 — tu startuje implementacja
```

Zasady:
- Zero commitów w `src/` przed otwarciem hackathonu; **historia gita ze znacznikami czasu jest naturalnym dowodem zgodności** — tag `event-start` na pierwszym commicie implementacji, tag `demo-freeze` na ~44 h.
- README jawnie deklaruje kategorię FROM SCRATCH i wylicza pre-work (regulamin opiera się na zasadzie zaufania — transparentność działa na naszą korzyść przy jury).
- Duże binaria (nagrania, modele) przez git-lfs albo poza repo w `cache/`; wszystko dodatkowo na pendrive (N6/R9).
- Wątpliwości co do zakresu pre-worku → konsultacja z organizatorem/mentorem (przewidziana regulaminem).
- Plan B: kategorię można zmienić do zamknięcia zgłoszeń w niedzielę — przy niekontrolowanym scope-creepie legalnym wyjściem jest NEXT STAGE (jury ocenia wtedy przede wszystkim deltę wykonaną w 48 h).

---

## 18. Źródła

Regulamin i wydarzenie: balticdualuse.eu/en/index, balticdualuse.eu/en/regulations.
Modele: huggingface.co/Qwen/Qwen3.5-0.8B (+ eksporty qualcomm/Qwen3.5-0.8B), liquid.ai/news/models (LFM2.5-1.2B/350M/230M), huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct, ibm.com/granite/docs, docs.mistral.ai (Ministral 3 3B), huggingface.co/microsoft/Phi-4-mini-instruct, developers.googleblog.com (Gemma 3n).
Runtime: github.com/ggml-org/llama.cpp (+ grammars/README — GBNF/JSON Schema), github.com/ggml-org/whisper.cpp, k2-fsa.github.io/sherpa (sherpa-onnx).
NAVTEX/SITOR-B: winradio.co.uk/home/ads-navtex.htm (parametry CCIR 476), goughlui.com/?p=30368 (sloty, FEC), baltic-lab.com/?p=9236 (generator testowy), swling.com (fldigi/YaND/MultiPSK), en.wikipedia.org/wiki/NAVTEX.
Badania NLP/ASR morskie: dl.acm.org/doi/10.1145/3624875.3624898 (TF-IDF), mdpi.com/2077-1312/12/9/1518 (Bi-LSTM CRF), doi.org/10.3390/jmse13091657 (Transformer restoration), mdpi.com/2077-1312/12/12/2328 (S-124/IMO Compendium), arxiv.org/pdf/2306.00614 (marFM), sciencedirect S2666822X24000121 (fine-tuning Whisper syntetycznie), hellenicshippingnews (Fintraffic).
Krajobraz bałtycki: atlanticcouncil.org (Baltic Sentry/CTF Baltic), jsis.washington.edu (Nordic Warden), github.com/FormerLab/shadow-fleet-tracker-light, grosswald.org/baltic-sea-security-tracker (jamming ~450 km / 7 państw), saab.com/products/situation-detector, windward.ai.
Edge defense SLM: thedefensepost.com (EdgeRunner Camo, WarClaw), businesswire (EdgeRunner Tactical-24B), aijourn.com (EdgeRunner 20B).
Compute pomocnicze: modal.com/pricing (stawki per sekunda, kredyty Starter).
Sprzęt: thinkrobotics.com (Jetson Orin Nano Super — specyfikacja), computingforgeeks.com i terminalbytes.com (ceny mini PC AI, VIII 2026), localaimaster.com (Strix Halo).
Dane i nagrania: frisnit.com/navtex, huggingface.co/datasets/bonalor/synthetic_maritime_radio_communication (MARTTS), github.com/jks-prv/kiwiclient, 112.is/en/navtex-utsendingar (harmonogram stacji NAVAREA I/Bałtyk).
Raport wejściowy: „Baltic Dual Use 2026 — Deep Research SLM Edge" (GPT, 07.09.2026) — architektura EdgeSITREP, kaskada, plan 48 h; zweryfikowany wyrywkowo j.w.
