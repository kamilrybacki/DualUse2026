# CLAUDE.md — FALOCHRON pre-hackathon prep

You are working in the prep repository for **FALOCHRON** (Maritime Broadcast Fusion Node) — a solo project for the Baltic Dual Use Hackathon, 11–13 Sep 2026, Gdańsk. The single source of truth is **`PRD_FALOCHRON_BDUH2026.md`** in the repo root (written in Polish — read it fully before your first task; section references below point into it).

Your job in this repo is **preparation only**: data, tools, benchmarks, configs, cloud jobs, docs. The product itself gets built at the event.

---

## 1. HARD BOUNDARY — FROM SCRATCH compliance (non-negotiable)

The project competes in the FROM SCRATCH category. Regulations permit pre-event research, environment setup, repo creation, component purchase/testing — but the actual implementation must start at the hackathon.

**Therefore, in this repo you MUST NOT:**
- write any code under `src/` (it stays empty except `.gitkeep`),
- implement any part of the runtime pipeline: input adapters (PRD F1–F3), the extraction service (F4), validators wired into a pipeline (F5), geocoder service (F6), correlator (F7), map app (F8), exporters (F9), event store service (F10), cascade router (F12),
- pre-build "libraries" that are thinly disguised pipeline modules.

**You MAY (and should) build:** standalone test harnesses, benchmark tooling, data generators, recording/decoding *test* scripts, Modal jobs, schemas and fixtures, download/cache scripts, configs, docs. Rule of thumb: *anything whose purpose is to test a single technology or prepare a component is fine; anything that would run in the demo's critical path is not.*

If a task I give you seems to require crossing this line — **stop and say so** instead of complying.

---

## 2. Repo layout (create and maintain)

```
falochron/
├── README.md                 # category declaration (FROM SCRATCH) + explicit pre-work list
├── CLAUDE.md                 # this file
├── PRD_FALOCHRON_BDUH2026.md # source of truth (Polish)
├── STATUS.md                 # living checklist mirroring PRD §14.1 — update every session
├── Makefile                  # all entry points (see §6)
├── schemas/                  # event schema v0.1: JSON Schema + GBNF + fixtures
├── prompts/                  # extraction prompt versions, LLM-as-judge prompts
├── docs/                     # research notes, pitch skeleton (EN), mentor questions
├── data/
│   ├── gold/seeds/           # ~50 manually curated real NAVTEX/BHMW texts (attributed)
│   ├── gold/                 # generated+reviewed gold set (jsonl, PL/EN/noisy splits)
│   ├── recordings/518khz/    # KiwiSDR IQ/audio per PRD Annex A.1 (git-lfs)
│   └── audio/vhf_synth/      # synthetic VHF corpus (git-lfs)
├── bench/                    # benchmark harness + reports
├── modal_jobs/               # datagen.py, tts.py, bench.py, finetune.py (W1–W5)
├── tools/                    # kiwirecorder wrapper, fldigi config+test, CCIR476 generator, cache scripts
├── cache/                    # GGUF models, whisper models, map tiles — .gitignore'd, mirrored to USB
└── src/                      # EMPTY until event start (tag: event-start)
```

Git hygiene: git-lfs for `data/recordings/**` and `data/audio/**`; nothing >5 MB outside LFS paths; no secrets in the repo ever (env vars / Modal Secrets); commit prefixes `prep:|tools:|bench:|modal:|data:|schemas:|docs:`; small commits.

---

## 3. Conventions

- Python 3.12, `uv` for env/deps, `ruff` + `pytest` for anything under `tools/` and `bench/`.
- Type hints everywhere; each script has `--help` and sane defaults.
- Code and comments in English; jury-facing docs (README) in Polish with an English category note.
- **Offline discipline:** everything in `tools/` and `bench/` must run with zero network, reading models/data from `cache/` and `data/`. Network access is allowed only in `tools/download_*.py` and `modal_jobs/`.
- On any conflict between this file and the PRD, the PRD wins — flag the conflict.

---

## 4. Task backlog (priority order, with acceptance criteria)

### P0 — foundation (do first)

1. **Scaffold** the layout above; README with FROM SCRATCH declaration + pre-work list; `.gitignore` (cache/, *.gguf, venvs); git-lfs config; STATUS.md seeded from PRD §14.1.
   ✓ `git status` clean, `make setup` creates env.
2. **Schemas**: translate PRD §9 into `schemas/event.schema.json` (v0.1, every field nullable/UNKNOWN-able, enums per PRD), generate GBNF from it with llama.cpp's JSON-schema converter, write 6–8 fixture pairs (input text → expected JSON) covering NAVTEX EN, BHMW PL, corrupted `*` text, voice-report style.
   ✓ fixtures validate against schema; GBNF loads in llama.cpp.
3. **Benchmark harness** (`bench/`): runner that feeds (model GGUF × prompt version × gold jsonl) through llama.cpp with grammar enforcement, computes: schema validity, per-field exact/F1, **unsupported-fact rate**, omission rate, latency p50/p95, peak RSS, escalation triggers. Markdown + CSV report, Pareto table. PASS thresholds read from `bench/thresholds.yaml` (fixed *before* looking at results — PRD §13).
   ✓ end-to-end run on fixtures with one small model completes offline.
4. **Cache scripts** (`tools/download_models.py`): resolve exact HF repo ids for the PRD §10.1 shortlist (Qwen3.5-0.8B, Granite 4.0 350M/1B, LFM2.5-350M/1.2B, Ministral 3 3B, Phi-4-mini; Whisper ggml small/medium/large-v3-turbo) — **verify ids on HF, do not guess** — download GGUF/Q4 where official, otherwise document conversion steps; sha256 manifest in `cache/MANIFEST.md`.
   ✓ manifest lists id, revision, file, hash, size for every artifact.
5. **Recording tooling** (`tools/record_navtex.py`): wrapper around `kiwirecorder.py` (vendored from github.com/jks-prv/kiwiclient) implementing PRD Annex A.1 — station slot table (UTC), `--station H|I|J|U`, starts 2 min early, `--tlimit 780`, IQ + optional USB-audio mode, filenames per Annex A; plus `tools/check_kiwi_snr.md` note on picking receivers.
   ✓ dry-run against one public Kiwi produces a valid wav; slot table matches Annex A exactly.
6. **fldigi test rig** (`tools/`): headless fldigi config for SITOR-B/NAVTEX + a *test* script that plays a wav into fldigi (snd-aloop/pw-loopback) and captures decoded text via XML-RPC to a file. This is a technology test, **not** the F3 adapter.
   ✓ Wikipedia's sample NAVTEX ogg decodes to readable text.

### P1 — data factory

7. **CCIR 476 / SITOR-B generator** (`tools/gen_sitorb.py`): text → valid SITOR-B audio (FSK 100 Bd, 170 Hz shift, 4-of-7 code, phasing, FEC repetition), with `--error-rate` to inject failures that decode as `*`. Reference approach: baltic-lab.com test-signal article.
   ✓ generated audio round-trips through the fldigi rig; error injection produces `*` at the expected rate.
8. **Modal app** (`modal_jobs/common.py` + jobs): shared `modal.Image`, Volume `falochron-artifacts`, secrets documented in `modal_jobs/README.md`. Jobs per PRD §12.5:
   - `datagen.py` (W1): few-shot from `data/gold/seeds/`, generate NAVTEX variants (EN + `*`-corrupted) and PL/EN VHF-style reports with labels; second LLM-as-judge pass; output jsonl to Volume, mirror locally.
   - `tts.py` (W2): PL/EN TTS (Piper voices for PL; document alternatives) + channel augmentation (300–3400 Hz bandpass, noise, clipping, squelch tails, dropouts) → `data/audio/vhf_synth/`.
   - `bench.py` (W3): parallel `.map()` sweep reusing `bench/` metrics on the same GGUF+GBNF as edge.
   - `finetune.py` (W4): QLoRA on Qwen3.5-0.8B, text→JSON; **dry-run mode only (≤200 samples)** — full run happens during the event, keep a `--full` flag gated behind `FALOCHRON_EVENT=1`.
   ✓ each job runs end-to-end in dry-run within free-tier budget; artifacts mirrored via `modal volume get`.
9. **EN eval import** (`tools/fetch_martts.py`): pull HF dataset `bonalor/synthetic_maritime_radio_communication` into `data/` with a small license/attribution note.
10. **Gold set assembly**: curation helper (not a mass scraper) to paste/normalize ~50 real messages into `data/gold/seeds/` with source+date fields; merge script seeds + W1 output + judge verdicts → `data/gold/{pl,en,noisy}.jsonl` (target 200–300 total); human-review CSV export/import.
    ✓ splits match PRD §13; every item has provenance.

### P2 — nice to have before Friday

11. **Gazetteer** (`tools/build_gazetteer.py`): Baltic names→coords (lights, buoys, ports, areas) from open data into `data/gazetteer.sqlite`.
12. **Map tiles**: offline Baltic basemap into `cache/tiles/` — prefer a downloadable extract (e.g., pmtiles) over scraping tile servers; respect usage policies; document the choice.
13. **Docs**: `docs/pitch_skeleton.md` (EN, per PRD §15), `docs/mentor_questions.md`.

---

## 5. Data & legal notes

- NAVTEX is public maritime safety information — recording and using it is fine; keep station/date attribution.
- VHF: only synthetic or self-recorded audio in this repo. Never add recordings of third-party voice traffic.
- Don't bulk-scrape message archives; a small curated, attributed seed set is enough (the LLM generates volume).

## 6. Make targets (implement as you go)

`setup · cache · record STATION= · decode FILE= · gen-sitorb TEXT= · bench MODEL= · modal-datagen · modal-tts · modal-bench · modal-finetune-dry · fetch-martts · gold-merge · status`

## 7. Working style

- Before any multi-file change: state a short plan, then execute.
- Ambiguity vs PRD → ask; PRD wins.
- End every session by updating `STATUS.md` (done / in progress / blocked) — it doubles as the ready-for-Friday checklist.
- Never claim something is cached/verified without the manifest hash or a passing test to show for it.

---

## Kickoff message (paste this as your first instruction to Claude Code)

> Read CLAUDE.md and PRD_FALOCHRON_BDUH2026.md end-to-end. Then (1) list any conflicts or open questions you see, (2) propose a concrete execution plan for the P0 tasks, and after my approval (3) execute P0 in order. Absolute constraint: nothing gets implemented under src/ — this repo is pre-hackathon prep only.
