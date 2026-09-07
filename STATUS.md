# STATUS — gotowość na 11.09.2026

Lustro PRD §14.1. Legenda: `[ ]` do zrobienia · `[~]` w toku · `[x]` zrobione · `[!]` zablokowane.
Aktualizowane na koniec każdej sesji. Ostatnia aktualizacja: **2026-09-07 (sesja 1, zdalna)**.

## PRD §14.1 — przed 11.09

- [~] Zamrozić schema v0.1 + słowniki typów; JSON Schema i gramatyka GBNF.
  - [x] `schemas/event.schema.json` (pełny) i `schemas/extraction.schema.json` (wyjście modelu)
  - [x] `schemas/extraction.gbnf` wygenerowany zwendorowanym konwerterem llama.cpp (`make gbnf`)
  - [x] 8 fixture'ów (NAVTEX EN ×3 w tym `*`, BHMW PL ×2, VHF PL/EN, gale warning) walidują się
  - [ ] gramatyka załadowana w prawdziwym llama.cpp **na Twojej maszynie** (`llama-cli --grammar-file schemas/extraction.gbnf`)
- [~] Gold set 200+ przykładów z etykietami.
  - [x] format seedów + helper kuracji (`tools/curate_seed.py`), scalanie i przegląd CSV (`tools/gold_merge.py`)
  - [ ] ~50 realnych seedów NAVTEX/BHMW wklejonych (frisnit.com/navtex, BHMW, własne dekody) — praca ręczna
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
- [ ] whisper.cpp vs sherpa-onnx na ~20 nagraniach z szumem; wybór rozmiaru.
- [~] fldigi (SITOR-B/NAVTEX, XML-RPC) + nagrania 518 kHz wg Aneksu A.
  - [x] `tools/record_navtex.py` — tabela slotów H/I/J/U z testami, tryb blokowy (HIJ = jedno nagranie 33 min), wiele Kiwi, IQ/USB
  - [x] `tools/check_kiwi_snr.md` — dobór odbiorników i weryfikacja nagrań
  - [x] `tools/fldigi/` — instrukcja headless, `decode_test.py` (XML-RPC → txt), `iq_to_audio.py` (Kiwi IQ → audio)
  - [x] `tools/gen_sitorb.py` — generator CCIR 476 z FEC, tryby błędów burst/random, round-trip w testach
  - [ ] **pierwsze nagranie**: najbliższe sloty U 21:20 CEST (19:20Z) i blok H/I/J 23:08–23:41 CEST (`make record STATION=HIJ KIWI=host1,host2`)
  - [ ] ≥6 czystych transmisji z ≥2 stacji + wpisy w `data/recordings/518khz/README.md`
  - [ ] próbka z Wikipedii i wygenerowany sygnał zdekodowane przez rig fldigi (odbiór P0.6 / P1.7)
- [~] Cache offline: modele GGUF, obrazy, kafle, dokumentacja; pendrive.
  - [x] `tools/download_models.py` + `cache/models.yaml` (12 wpisów, wszystkie `verified: false`)
  - [ ] `--verify` na Twojej maszynie, poprawienie identyfikatorów, `--all`, `cache/MANIFEST.md` z hashami
  - [ ] kafle mapy Bałtyku (P2.12)
- [ ] Gazeter bałtycki (nazwy → współrzędne) (P2.11).
- [x] Szkielet pitchu 3 min (EN) — `docs/pitch_skeleton.md`; pytania do mentorów — `docs/mentor_questions.md`.
- [ ] Skrypt resetu demo + checklista fault-injection (po evencie startuje implementacja; checklista może powstać wcześniej).
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

## Blokery / do zrobienia po Twojej stronie

- [!] Sesja zdalna nie ma dostępu do huggingface.co, KiwiSDR (port 8073), audio, llama.cpp ani Modala — odbiory P0.4/P0.5/P0.6, P1.7/P1.8 i bench na modelu uruchamiasz lokalnie.
- [ ] Po sklonowaniu: `make setup` (uv sync + `git submodule update --init`).
- [ ] Python: docelowo 3.12, `pyproject` dopuszcza 3.11 (sesja zdalna). Testy: `make test` (76 testów), lint: `make lint`.
