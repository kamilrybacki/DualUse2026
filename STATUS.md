# STATUS — gotowość na 11.09.2026

Lustro PRD §14.1. Legenda: `[ ]` do zrobienia · `[~]` w toku · `[x]` zrobione · `[!]` zablokowane.
Aktualizowane na koniec każdej sesji. Ostatnia aktualizacja: **2026-09-07 późny wieczór (sesja 1, zdalna, kontynuacja)**.

## PRD §14.1 — przed 11.09

- [~] Zamrozić schema v0.1 + słowniki typów; JSON Schema i gramatyka GBNF.
  - [x] `schemas/event.schema.json` (pełny) i `schemas/extraction.schema.json` (wyjście modelu)
  - [x] `schemas/extraction.gbnf` wygenerowany zwendorowanym konwerterem llama.cpp (`make gbnf`)
  - [x] 10 fixture'ów (NAVTEX EN ×3 w tym `*`, prawdziwe zniekształcenie fldigi, BHMW PL ×3 w tym prompt injection, VHF PL/EN, gale warning) walidują się
  - [x] gramatyka zweryfikowana w prawdziwym llama.cpp (zbudowany ze źródeł w sesji): 9 fixture'ów przyjętych, 3 negatywy odrzucone, kolejność kluczy wymuszona (`make gbnf-check`)
- [~] Gold set 200+ przykładów z etykietami.
  - [x] format seedów + helper kuracji (`tools/curate_seed.py`), scalanie i przegląd CSV (`tools/gold_merge.py`)
  - [~] realne seedy: **33** (BHMW 213/215/216 PL+EN z PDF, 9 własnych dekodów NL Coastguard 2018, 18 dekodów live navtex.lv I/J z 2026-09-08) — cel ~50, brakuje H/U i typu B; `data/gold/review/pending.csv` czeka na Twój przegląd
  - [ ] W1 (`make modal-datagen`) uruchomiony, wynik zmirrorowany do `data/gold/generated/`
  - [ ] przegląd ludzki (`--export-review` / `--import-review`) i `make gold-merge`
- [~] Harness benchmarku (model × prompt × gold → metryki).
  - [x] `bench/run_bench.py`: backendy llama-cli / llama-server / fake; raport MD+CSV; tabela Pareto
  - [x] `bench/thresholds.yaml` **zamrożony 2026-09-07 przed jakimkolwiek biegiem modelu**
  - [x] metryki: schema validity, per-field F1, unsupported-fact (grounding w tekście, także pozycje mówione), omission, geo-resolution, latencja, RSS, trafienia reguł eskalacji
  - [x] end-to-end na atrapie (`make bench-fake`, w testach)
  - [ ] bieg na prawdziwym modelu (`make bench MODEL=cache/models/...`) — wymaga llama.cpp lokalnie
- [~] Modal: workspace + Volume + Secrets; joby W1–W3 wykonane.
  - [x] `modal_jobs/common.py`, `datagen.py` (W1 + judge + grounding), `tts.py` (W2, Piper + augmentacja), `bench.py` (W3), README z kosztami i sekretami
  - [ ] `modal setup`, sekret `huggingface`, pierwszy dry-run każdego joba (API vLLM/TRL do potwierdzenia na żywo)
- [~] Modal: dry-run W4 (QLoRA ≤200 próbek).
  - [x] `modal_jobs/finetune.py` z `--full` zablokowanym bez `FALOCHRON_EVENT=1`
  - [ ] dry-run wykonany, GGUF w `cache/models/`
- [~] whisper.cpp vs sherpa-onnx na ~20 nagraniach z szumem; wybór rozmiaru.
  - [x] lokalny korpus testowy: `tools/synth_vhf_local.py` (espeak-ng pl/en × 3 presety kanału) → `data/audio/vhf_synth/local/` (12 plików)
  - [x] Whisper tiny/small/large-v3-turbo (ONNX int8 z GitHub Releases sherpa-onnx) w `cache/asr/`; `bench/asr_bench.py` (WER, recall encji, RTF)
  - [x] **wynik** (`bench/reports/20260907-205336_asr`, `docs/research_asr_espeak.md`): tylko turbo jest kandydatem (WER 0.37 clean / 0.49 typical, recall encji 0.47 / 0.29); tiny i small nieużyteczne; preset harsh łamie wszystko; espeak to pesymistyczny proxy, powtórzyć na korpusie Piper/własnym głosie
  - [ ] whisper.cpp z wagami ggml (HF zablokowane) — latencja/RSS na docelowym węźle
- [~] fldigi (SITOR-B/NAVTEX, XML-RPC) + nagrania 518 kHz wg Aneksu A.
  - [x] `tools/record_navtex.py` — tabela slotów H/I/J/U z testami, tryb blokowy (HIJ = jedno nagranie 33 min), wiele Kiwi, IQ/USB
  - [x] `tools/check_kiwi_snr.md` — dobór odbiorników i weryfikacja nagrań
  - [x] `tools/fldigi/` — rig headless **uruchomiony i sprawdzony w sesji** (`rig_up.sh`: PulseAudio null sink + Xvfb + fldigi 4.2.03): syntetyczny sygnał zdekodowany dosłownie, ramka `ZCZC IA47…NNNN`
  - [x] odkrycie: fldigi nie drukuje `*`, podstawia lub gubi znaki i traci rejestr LTRS/FIGS → `docs/research_fldigi_navtex_errors.md`, fixture 09, tryb `garble` w W1, tolerancja 1 znaku w nagłówku w metryce
  - [x] `tools/gen_sitorb.py` — generator CCIR 476 z FEC, tryby błędów burst/random; **round-trip przez prawdziwy fldigi potwierdzony** (odbiór P1.7)
  - [x] `gen_sitorb.py --iq` → plik w układzie Kiwi (bloki `kiwi`+`data`) → `iq_to_audio.py` → fldigi: pełna ramka `HB13`; ścieżka odtwarzania nagrań IQ sprawdzona bez prawdziwego nagrania
  - [ ] **pierwsze nagranie** — z tej sesji niemożliwe (KiwiSDR nieosiągalny). Opcje: `make record` na dowolnej maszynie z siecią, albo `make modal-record STATION=HIJ` z chmury (`modal_jobs/record.py`, auto-dobór Kiwi przez `tools/fetch_kiwis.py`)
  - [ ] ≥6 czystych transmisji z ≥2 stacji + wpisy w `data/recordings/518khz/README.md`
  - [x] odbiór P0.6 domknięty: próbka z Wikipedii zdekodowana (`--carrier 1700 --reverse`), nagranie z eteru 2018 (9 komunikatów NL Coastguard) zdekodowane z **0,0 % CER** względem referencji — `docs/evidence/`
- [~] Cache offline: modele GGUF, obrazy, kafle, dokumentacja; pendrive.
  - [x] `tools/download_models.py` + `cache/models.yaml` — identyfikatory repo potwierdzone wyszukiwarką (oficjalne GGUF: Granite 350M/1B, LFM2.5 350M/1.2B, Ministral 3 3B, Qwen3 1.7B/4B; Qwen3.5-0.8B i Phi-4-mini tylko jako kwantyzacje bartowski)
  - [ ] `--all` z maszyny z dostępem do HF → `cache/MANIFEST.md` z hashami (HF zablokowane w sesji)
  - [ ] kafle mapy Bałtyku (P2.12)
- [~] Gazeter bałtycki (nazwy → współrzędne) (P2.11).
  - [x] `tools/download_gazetteer.py` (Overpass: latarnie, pławy, porty, miejscowości, zatoki) + `data/gazetteer_seed.csv` (20 akwenów, stacje NAVTEX) + testy offline
  - [ ] zapytanie Overpass wykonane (overpass-api.de zablokowany w sesji) → `data/gazetteer.sqlite`
- [x] Szkielet pitchu 3 min (EN) — `docs/pitch_skeleton.md`; pytania do mentorów — `docs/mentor_questions.md`.
- [~] Skrypt resetu demo + checklista fault-injection.
  - [x] `docs/demo_checklist.md` (T-60, T-10, 8 scenariuszy awarii z odzyskaniem)
  - [ ] skrypt resetu — po `event-start`
- [ ] `tools/fetch_martts.py` uruchomiony (`make fetch-martts`), notatka licencyjna w `data/martts/README.md`.

## Decyzje podjęte 2026-09-07

- Nagrania i audio poza gitem (bez LFS): `data/recordings/`, `data/audio/` w `.gitignore`, mirror na pendrive. PRD Aneks B dopuszcza.
- Wyjątek od reguły offline rozszerzony na `tools/{download,fetch,record}_*.py`.
- `gold` = wyłącznie pozycje z przeglądem ludzkim (seed `label_status: reviewed` albo werdykt `accepted`); reszta → `train.jsonl`.
- Enumy mają wartość `UNKNOWN`, pozostałe pola `null`. Dwa schematy: pełny i ekstrakcyjny. `entities` jako rozszerzenie projektu (potrzebne F7).
- Benchmark raportuje trafienia reguł eskalacji zapisanych deklaratywnie w `thresholds.yaml`; kod routera nie istnieje.
- Rig fldigi to jednorazowe CLI zapisujące txt; adapter F3 powstaje na evencie.
- kiwiclient jako submoduł (brak pliku licencji w upstream), konwerter GBNF z llama.cpp zwendorowany (MIT), tablica CCIR 476 przepisana jako dane z fldigi.
- Stara gałąź z gotowym pipeline'em usunięta; `main` zaczyna się od dokumentów (commit `fca9e71`).

## Blokery / co możesz zrobić z telefonu

Z tej sesji osiągalne są tylko: github.com (git + raw), PyPI i apt Ubuntu. Zablokowane (sprawdzone, kod 000/403):
huggingface.co, api.modal.com, kiwisdr.com i porty 8073, overpass-api.de, nominatim, upload.wikimedia.org,
frisnit.com, bhmw.gov.pl, build.protomaps.com, CDN wag Whispera. Dlatego:

- [!] modele (P0.4), nagrania Kiwi (P0.5), Modal (P1.8), gazeter (P2.11), kafle (P2.12), seedy z archiwów — wymagają sieci.
- [ ] **Odblokowanie z telefonu (claude.ai → Code → środowisko tej sesji → Network access):** ustaw „Full access” albo dodaj do allowlisty
  `huggingface.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co`, `api.modal.com`, `modal.com`, `overpass-api.de`, `kiwisdr.com`, `frisnit.com`, `bhmw.gov.pl`.
  Do Modala dodaj w tym samym miejscu zmienne środowiskowe `MODAL_TOKEN_ID` i `MODAL_TOKEN_SECRET` (z modal.com → Settings → API tokens).
  Potem napisz w sesji „odblokowane” — dalej pójdzie: `--verify` i pobranie modeli, bench na prawdziwym modelu (llama.cpp jest już zbudowany), `modal-record` na najbliższy slot, W1/W2/W3, gazeter.
- [ ] Nagrania Kiwi używają WebSocket na porcie 8073 — jeśli proxy sesji nie przepuszcza portów innych niż 443, zostaje wyłącznie wariant chmurowy `make modal-record`.
- [ ] Po sklonowaniu: `make setup` (uv sync + `git submodule update --init`).
- [ ] Python: docelowo 3.12, `pyproject` dopuszcza 3.11 (sesja zdalna). Testy: `make test` (87 testów), lint: `make lint`.
