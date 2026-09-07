# STATUS — gotowość na 11.09.2026

Lustro PRD §14.1. Legenda: `[ ]` do zrobienia · `[~]` w toku · `[x]` zrobione · `[!]` zablokowane.
Aktualizowane na koniec każdej sesji. Ostatnia aktualizacja: **2026-09-07**.

## PRD §14.1 — przed 11.09

- [~] Zamrozić schema v0.1 + słowniki typów; JSON Schema i gramatyka GBNF.
  - [x] `schemas/event.schema.json` (pełny) i `schemas/extraction.schema.json` (wyjście modelu)
  - [x] fixture'y w `schemas/fixtures/` walidują się (`make test`)
  - [ ] GBNF wygenerowany i załadowany w llama.cpp **na Twojej maszynie** (`make gbnf`, potem `llama-cli --grammar-file`)
- [ ] Gold set 200+ przykładów z etykietami.
  - [x] format seedów + helper kuracji (`tools/curate_seed.py`)
  - [ ] ~50 realnych seedów NAVTEX/BHMW wklejonych i zatwierdzonych (praca ręczna)
  - [ ] W1 (Modal datagen) uruchomiony, wynik zmirrorowany
  - [ ] przegląd ludzki (CSV) i scalenie `make gold-merge`
- [~] Harness benchmarku (model × prompt × gold → metryki).
  - [x] `bench/run_bench.py` z backendem llama.cpp i backendem atrapą; `bench/thresholds.yaml` ustalony przed pierwszym biegiem
  - [x] test end-to-end na atrapie (`make test`)
  - [ ] bieg na prawdziwym modelu z `cache/` (`make bench MODEL=...`) — wymaga llama.cpp lokalnie
- [ ] Modal: workspace + Volume + Secrets; joby W1–W3 wykonane.
  - [ ] `modal_jobs/common.py` + `datagen.py` + `tts.py` + `bench.py`
- [ ] Modal: dry-run W4 (QLoRA ≤200 próbek).
- [ ] whisper.cpp vs sherpa-onnx na ~20 nagraniach z szumem; wybór rozmiaru.
- [~] fldigi (SITOR-B/NAVTEX, XML-RPC) + nagrania 518 kHz wg Aneksu A.
  - [x] `tools/record_navtex.py` z tabelą slotów H/I/J/U, trybem blokowym i wieloma Kiwi
  - [x] `tools/fldigi/` konfiguracja headless + `tools/fldigi/decode_test.py`
  - [ ] nagranie testowe z jednego Kiwi (**dziś wieczorem**: blok H/I/J 19:08–19:42 CEST)
  - [ ] ≥6 czystych transmisji z ≥2 stacji
  - [ ] próbka z Wikipedii zdekodowana przez rig fldigi
- [~] Cache offline: modele GGUF, obrazy, kafle, dokumentacja; pendrive.
  - [x] `tools/download_models.py` + `cache/models.yaml`
  - [ ] identyfikatory HF zweryfikowane (oznaczone UNVERIFIED do czasu sprawdzenia)
  - [ ] modele pobrane, `cache/MANIFEST.md` z hashami
  - [ ] kafle mapy Bałtyku
- [ ] Gazeter bałtycki (nazwy → współrzędne).
- [ ] Szkielet pitchu 3 min (EN) + pytania do mentorów.
- [ ] Skrypt resetu demo + checklista fault-injection.

## Decyzje podjęte 2026-09-07

- Nagrania i audio poza gitem (bez LFS): `data/recordings/`, `data/audio/` w `.gitignore`, mirror na pendrive. PRD Aneks B dopuszcza.
- Wyjątek od reguły offline rozszerzony na `tools/{download,fetch,record}_*.py`.
- `gold` = wyłącznie pozycje z przeglądem ludzkim; reszta W1 → `train`.
- Enumy mają wartość `UNKNOWN`, pozostałe pola `null`. Dwa schematy: pełny i ekstrakcyjny.
- Benchmark raportuje trafienia reguł eskalacji zapisanych deklaratywnie w `thresholds.yaml`; kod routera nie istnieje.
- Rig fldigi to jednorazowe CLI zapisujące txt; adapter F3 powstaje na evencie.
- kiwiclient jako submoduł (brak pliku licencji w upstream), konwerter GBNF z llama.cpp zwendorowany (MIT).

## Blokery / do zrobienia po Twojej stronie

- [!] Sesja zdalna nie ma dostępu do huggingface.co, KiwiSDR (port 8073), audio ani llama.cpp — odbiory P0.4/P0.5/P0.6 i bench na modelu uruchamiasz lokalnie.
- [ ] `git submodule update --init` po sklonowaniu.
