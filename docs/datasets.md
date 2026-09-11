# Datasets — what exists, where, provenance, status (2026-09-11, pre-event)

Everything below is pre-work data for FALOCHRON (FROM SCRATCH: data + component tests, no
pipeline code). Sizes are as of 2026-09-11 ~15:00 UTC. Large binaries (audio, models,
recordings) are **git-ignored** and live in `cache/` / `data/` on the laptop + USB mirror;
manifests, transcripts, labels and notes are committed.

| # | Dataset | Path | Size | Origin | License / rights | Status |
|---|---|---|---|---|---|---|
| 1 | Gold fixtures (frozen) | `schemas/fixtures/` | 10 pairs | hand-written + hand-labelled | own | **FROZEN gold** — the only gold with data today |
| 2 | Real NAVTEX/BHMW seeds | `data/gold/seeds/` | 46 JSON | BHMW PDFs, own 2018 off-air decodes, navtex.lv live decodes | public MSI, attributed | **pending human review** (`review/pending.csv`) |
| 3 | W1 synthetic candidates | `data/gold/generated/20260911-140837-dry/` | 38 items (5 judge-accepted) | Qwen2.5-7B on Modal L4 + LLM-judge + grounding | synthetic (own) | candidates → `pending.csv`, never self-accepted |
| 4 | Gold splits | `data/gold/{pl,en,noisy}.jsonl` | 0 / 0 / 0 | `gold_merge.py` from human-accepted items | — | **empty until review**; `train.jsonl` = 12 drafts |
| 5 | MARTTS (EN VHF eval) | `data/martts/` | 480 wav, 1.3 GB (audio ignored) + 1.3 MB jsonl | HF `bonalor/synthetic_maritime_radio_communication` rev `3aa9455` | **cc-by-4.0** | ready for EN ASR eval |
| 6 | Local VHF synth (espeak) | `data/audio/vhf_synth/local/` | 12 wav (regenerate) + `transcripts.jsonl` | `tools/synth_vhf_local.py`, espeak-ng PL/EN × 3 channel presets | synthetic (own) | used by `bench/asr_bench.py`; wavs: `make synth-vhf-local` |
| 7 | SITOR-B audio | `data/audio/sitorb/` | 4 demo wav + 4 sample files | `gen_sitorb.py` from `data/demo/` texts; sigidwiki real sample | own / sigidwiki (CC) | demo + decoder validation; `make demo-assets` |
| 8 | 518 kHz off-air recordings | `data/recordings/518khz/` | U slot 15:20Z (sk5sm SE + oh3aa FI) — **recording pending** | KiwiSDR IQ via `record_navtex.py` | public MSI, attributed (host/slot) | log in `data/recordings/518khz/README.md` |
| 9 | Baltic gazetteer | `data/gazetteer.sqlite` (627 KB, **4 333 rows**) + `cache/gazetteer_overpass.json` (4.7 MB raw) | 4 307 OSM elements + 20 curated sea areas + 4 NAVTEX stations | Overpass (per-kind queries) + `data/gazetteer_seed.csv` | **ODbL 1.0** (attribution in `meta`) | verified: `--lookup Hel` → 54.60 N 18.81 E; rebuild offline `--from-cache` |
| 10 | Demo inputs | `data/demo/` | 5 texts | real BHMW 216 + scripted NAVTEX/VHF | own / public MSI | scripted 3-min demo |
| 11 | Model cache | `cache/models/` | 12 artifacts, **14 GB** | HF (9 SLM Q4 + whisper small/medium/large-v3-turbo) | per model (Apache-2.0 / MIT / LFM) | sha256 + revision in `cache/MANIFEST.md` |
| 12 | Benchmark reports | `bench/reports/` | v0.1: 9 models ✓ · v0.2: in progress · ASR report | `bench/run_bench.py`, `asr_bench.py` | own | `pareto.md` auto-refreshed; summary in `docs/bench_results.md` |
| 13 | Decoder evidence | `docs/evidence/` | 4 decoded texts | fldigi rig on demo / 2018 off-air / Wikipedia / sigidwiki | own | 0 % CER on 2018 off-air; sigidwiki body verbatim |

## Per-dataset notes

### 1. Gold fixtures — `schemas/fixtures/` (frozen)
Ten `{source_text, expected}` pairs covering the whole input space: NAVTEX EN ×3 (nav warning,
exercise **polygon**, `*`-corrupted), a **real fldigi-garbled** NAVTEX, BHMW PL ×3 (cable works,
wreck, **prompt injection**), VHF PL/EN voice reports, gale warning. Every label validated against
`schemas/extraction.schema.json`; every expected object accepted by the GBNF grammar
(`make gbnf-check`). This is the gold the benchmark thresholds were frozen against — it is also
the hardest set (polygon + spoken PL positions are where every model fails today).

### 2. Real seeds — `data/gold/seeds/` (46, pending review)
Provenance in each file (`source`, `station`, `date`, `receiver`): BHMW warnings 208/211/212/213/
215/216 (PL + EN from the official PDFs), 9 NL Coastguard 2018 messages decoded from an off-air
recording by our own rig, 25 live decodes from navtex.lv (Baltic J/I; Mondolfo U and Irakleio H via
sky-wave). `label_status`: 12 `draft` (assistant-proposed labels), 34 `unlabeled`.
**Human task:** open `data/gold/review/pending.csv`, set `verdict` (accepted / rejected / fix),
run `uv run python tools/gold_merge.py --import-review data/gold/review/pending.csv && make gold-merge`.
Only then do `pl/en/noisy.jsonl` fill.

### 3. W1 synthetic candidates — `data/gold/generated/…-dry/` (38, 5 accepted by the judge)
First real Modal run (L4, Qwen2.5-7B-Instruct, prompt `datagen_v0.1`): 30 navtex_en, 4 bhmw_pl,
2 vhf_pl, 2 vhf_en; `truncated_prompts = 0`. Each item carries deterministic grounding
(`grounding_unsupported`) and an LLM-judge verdict with issues + a corrected label. The judge is
strict on purpose (first run: 0/35 — the 7B merged the day-time group into the NAVTEX header; the
prompt was tightened and the re-run yields 5/38). These are **candidates**: `--export-review` puts
them in `pending.csv`; a human accepts them into gold. Full-size run (H100, 72B-AWQ) is an
event-window job.

### 5. MARTTS — `data/martts/` (EN VHF, 480 dialogs)
Synthetic maritime VHF dialogs (SMCP scenarios → LLM → TTS → channel degradation), clean +
noisy variants. Metadata/transcripts (`scenarios*.jsonl`, `noise_metadata.jsonl`,
`speaker_metadata.jsonl`) committed; wavs on disk only. Use for the **EN ASR entity-recall
evaluation** (`bench/asr_bench.py`) and as the methodological template for our W2 TTS job.

### 6–7. Synthetic audio
`vhf_synth/local`: espeak-ng renders of the VOICE fixtures × {clean, typical, harsh} channel
presets — a pessimistic proxy (espeak ≠ human); result so far: only whisper `large-v3-turbo` is a
candidate (WER 0.37 clean / 0.49 typical). `sitorb/`: bit-exact CCIR 476 / SITOR-B audio with
FEC + phasing from `gen_sitorb.py` (`--error-rate` injects `*`), incl. an IQ variant in KiwiSDR
layout; round-trips through the real fldigi rig. `sitorb/samples/`: the sigidwiki real SITOR-B
recording (decoded, see `docs/evidence/`).

### 8. Off-air 518 kHz — `data/recordings/518khz/`
Live capture path proven (decoder + IQ→audio); today's Baltic slots were mostly lost to the
kiwisdr.com directory outage. One recording is armed: **station U (Tallinn) 15:20 UTC** from
`sk5sm.proxy.kiwisdr.com` (SE) and `oh3aa.dy.fi:18073` (FI) in parallel. After it lands:
`iq_to_audio.py` → `make decode` → log host/SNR/`*`-rate in the README, curate readable frames as
seeds. More slots every 4 h (H 1310/1710/2110, I +10, J +20, U 1520/1920/2320 UTC).

### 9. Gazetteer — `data/gazetteer.sqlite`
4 333 names → coordinates for the Baltic bbox (53–66.5 N, 9–31 E): lights, buoys, beacons,
harbours, wrecks, platforms, cables, towns > 2 000, bays/straits/capes/shoals + curated sea areas
and NAVTEX stations. Match keys are ASCII-folded, alt names (`name:pl/sv/de/fi/et`) indexed.
Rebuilt offline from the committed raw JSON. This is **data** for the F6 geocoder — the geocoder
itself is event-time code.

### 11. Model cache — `cache/models/` (14 GB, USB-mirrored)
Q4_K_M unless noted: granite-4.0-350m / 1b, LFM2.5-350M (QAD-Q4_0) / 1.2B, Qwen3.5-0.8B,
Ministral-3-3B, Phi-4-mini, Qwen3-1.7B, Qwen3-4B; whisper ggml small / medium / large-v3-turbo.
Every file hashed (`cache/MANIFEST.md`: repo, HF revision, sha256, size, license).

## What the human still has to do
1. Review `data/gold/review/pending.csv` (46 seeds + 38 W1 candidates) → `make gold-merge`.
2. Record own-voice PL/EN VHF reports (never third-party traffic) → `data/audio/vhf_own/`.
3. Decode + log the 15:20 UTC U recording; grab more slots (2 per 4 h cycle) before the SDR demo.
4. USB mirror: `rsync -a cache/ data/recordings/ data/audio/ <mount>/falochron/`.
