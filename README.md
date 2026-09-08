# FALOCHRON — Maritime Broadcast Fusion Node

> **Category note (EN):** This project competes in the **FROM SCRATCH** category of the
> Baltic Dual Use Hackathon (11–13 Sep 2026, Gdańsk). Nothing under `src/` exists before
> the event opens. Everything else in this repository is pre-event preparation explicitly
> permitted by the regulations (§D5.80): research, environment setup, repository creation,
> component testing, data collection and benchmarking of single technologies. The runtime
> pipeline is implemented during the 48-hour event and tagged `event-start` on its first
> commit.

Repozytorium przygotowawcze projektu **FALOCHRON** — przenośnego, offline'owego węzła,
który zamienia morskie kanały rozgłoszeniowe (NAVTEX tekst i radio 518 kHz, głos VHF)
w ustrukturyzowane, zweryfikowane zdarzenia zgodne z modelem S-124. Pełny opis:
[`PRD_FALOCHRON_BDUH2026.md`](PRD_FALOCHRON_BDUH2026.md).

## Kategoria: FROM SCRATCH

Projekt startuje w kategorii FROM SCRATCH. Regulamin (Terms and Conditions, D5.2) dopuszcza
przed hackathonem research, przygotowanie środowiska, założenie repozytorium, konfigurację
narzędzi, zakup i testowanie pojedynczych technologii, bibliotek, urządzeń i komponentów.
**Implementacja pipeline'u zaczyna się w piątek 11.09.2026 o 18:00** (start hackathonu wg
regulaminu) — katalog `src/` pozostaje pusty do tego momentu (pilnuje tego hook
`tools/hooks/pre-commit`), a pierwszy commit implementacji następuje po tagu `event-start`.
Mapowanie każdego elementu pre-worku na zapisy regulaminu: [`docs/regulations_check.md`](docs/regulations_check.md).

**Jawność wkładu (D4.3):** pre-work w tym repozytorium powstał z użyciem asystenta AI do
programowania (Claude Code), pod kierunkiem i z decyzjami autora; etykiety gold oznaczone
jako `draft` zostały zaproponowane przez asystenta i są akceptowane ręcznie. Regulamin
(D4.1–2) dopuszcza narzędzia AI i treści przez nie generowane.

## Co powstało przed wydarzeniem (jawna lista pre-worku)

Wszystko poniżej to narzędzia do testów pojedynczych technologii, dane i konfiguracje —
nic z tego nie jest częścią ścieżki krytycznej demo.

| Obszar | Co | Gdzie |
|---|---|---|
| Dokumentacja | PRD, brief dla asystenta AI, checklista gotowości | `PRD_FALOCHRON_BDUH2026.md`, `CLAUDE.md`, `STATUS.md` |
| Schemat zdarzenia | JSON Schema v0.1 (pełny + podzbiór dla ekstrakcji), gramatyka GBNF, fixture'y | `schemas/` |
| Benchmark | harness porównujący modele SLM na gold secie (schema validity, F1, unsupported-fact rate, latencja, RSS) | `bench/` |
| Nagrania NAVTEX | wrapper `kiwirecorder.py` z harmonogramem stacji bałtyckich 518 kHz, ranking publicznych KiwiSDR, wariant chmurowy | `tools/record_navtex.py`, `tools/fetch_kiwis.py`, `modal_jobs/record.py` |
| Dekoder SITOR-B | headless fldigi (PulseAudio + Xvfb) + skrypt testowy wav → tekst przez XML-RPC; notatka o zachowaniu fldigi przy błędach FEC | `tools/fldigi/`, `docs/research_fldigi_navtex_errors.md` |
| Generator SITOR-B | syntetyczny sygnał CCIR 476 z FEC i fazowaniem do testów dekodera | `tools/gen_sitorb.py` |
| Cache modeli | skrypt pobierania GGUF/ggml z manifestem sha256 | `tools/download_models.py`, `cache/` |
| Gold set | kuracja realnych tekstów NAVTEX/BHMW z atrybucją, scalanie z danymi syntetycznymi | `tools/curate_seed.py`, `tools/gold_merge.py`, `data/gold/` |
| Dane syntetyczne | joby Modal: generacja tekstów, TTS+augmentacja, sweep benchmarku, dry-run QLoRA; lokalny korpus VHF z espeak-ng | `modal_jobs/`, `tools/synth_vhf_local.py` |
| Gazeter | skrypt budujący `data/gazetteer.sqlite` z OSM (Overpass) + kuratorowane akweny | `tools/download_gazetteer.py`, `data/gazetteer_seed.csv` |
| Demo | checklista resetu i fault-injection (procedura, bez skryptu) | `docs/demo_checklist.md` |
| Prompty | wersjonowane prompty ekstrakcji i LLM-as-judge | `prompts/` |

Szczegółowy stan każdego elementu: [`STATUS.md`](STATUS.md).

## Czego tu nie ma (i nie będzie przed 11.09)

- adapterów wejściowych (F1–F3), serwisu ekstrakcji (F4), walidatora w pipeline (F5),
  geokodera (F6), korelatora (F7), mapy (F8), eksporterów (F9), event store (F10),
  routera kaskady (F12) — patrz PRD §6,
- żadnego kodu w `src/`.

## Środowisko

```
make setup        # uv venv + zależności narzędzi
make status       # pokaż STATUS.md
make -n <cel>     # podgląd komendy bez uruchamiania
```

Pełna lista celów: `make help`. Narzędzia w `tools/` i `bench/` działają offline,
czytając modele z `cache/` i dane z `data/`. Sieci używają wyłącznie skrypty
`tools/download_*.py`, `tools/fetch_*.py`, `tools/record_*.py` oraz `modal_jobs/`.

## Dane i prawo

- NAVTEX to publiczna informacja bezpieczeństwa morskiego (MSI); nagrania i teksty
  są przechowywane z atrybucją stacji i daty.
- Audio VHF w repo jest wyłącznie syntetyczne lub nagrane własnym głosem. Żadnych
  nagrań cudzej korespondencji radiowej.
- Nagrania IQ/audio i modele nie trafiają do gita (patrz `.gitignore`); są w `cache/`
  i `data/recordings/`, mirrorowane na pendrive.

## Licencje komponentów zewnętrznych

- `tools/vendor/kiwiclient` — submoduł git, github.com/jks-prv/kiwiclient (przypięty commit).
- `tools/vendor/llama_cpp/json_schema_to_grammar.py` — z github.com/ggml-org/llama.cpp, MIT.
