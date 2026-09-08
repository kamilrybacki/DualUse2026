# Regulations check — Terms and Conditions, Baltic Dual Use Hackathon 2026

Source: "Terms and Conditions – Baltic Dual Use Hackathon 2026" (PDF, 25 pages), read
2026-09-08. Clause numbers below are the section/paragraph labels used in the document
(D4, D5, D6, evaluation section). Quotes are verbatim from the English text.

## Hard facts that change our plan

| Fact | Where | Consequence |
|---|---|---|
| Hackathon runs **Friday 11 Sep 2026 18:00 → Sunday 13 Sep 2026 18:00** (48 h) | Hackathon rules, para. 1 | `event-start` tag = first implementation commit **after 2026-09-11 18:00 CEST (16:00 UTC)**; PRD §14.2 windows are relative to 18:00 Friday, so "0–6 h" is Friday evening/night |
| Solo participation allowed ("individually or in Teams of up to 5") | Participation, para. 2 | fine |
| Final presentation **max 3 minutes**; presenting is a condition of evaluation | Evaluation, para. 7 | PRD §15 already sized for 3:00; keep 15 s slack |
| Category may be changed until Project submissions close on **Sunday 13 Sep**; then final | D5.3 | Plan B (switch to NEXT STAGE) stays open until Sunday |
| "The Main Organizer relies on the principle of trust in Participants and on their fair assessment" | D5.4 | our README pre-work list is the fair assessment, keep it explicit |
| Projects used commercially before the Event are excluded | Evaluation, para. 3 | not applicable |
| Detailed scoring criteria published before work starts on the day | Evaluation, para. 6 | read them Friday 18:00, re-weight the pitch if needed |

## FROM SCRATCH — what D5.2 permits, mapped to this repo

> "Prior preparation of organizational and technical elements necessary to begin work is
> permitted, including in particular: developing an idea or concept, conducting research,
> preparing a development environment, creating a repository, configuring tools and the
> Team's working methods, preparing a list of required components and purchasing them in
> advance, preparing hardware, and testing individual technologies, libraries, devices or
> components."

| Pre-work item | Permitted activity it falls under | Risk |
|---|---|---|
| PRD, CLAUDE.md, STATUS, pitch skeleton, mentor questions | idea/concept, research, working methods | none |
| Repo, Makefile, uv env, CI-less test suite | creating a repository, development environment | none |
| `schemas/` (JSON Schema, GBNF, fixtures) | configuring tools (the grammar is a llama.cpp *configuration*), research | low — a schema is a contract, not an implementation; keep v0.1 frozen and re-cut v1.0 at the event as PRD §14.2 says |
| `bench/` harness + thresholds + reports | testing individual technologies (models) | low — it never runs in the product |
| `tools/record_navtex.py`, `fetch_kiwis.py`, `modal_jobs/record.py` | preparing hardware/components, research (data) | none — recordings of public MSI |
| `tools/fldigi/` rig, `gen_sitorb.py` | testing individual technologies/devices | low — rig is a one-shot test CLI; the F3 adapter is written at the event |
| `tools/sitorb.py` (CCIR 476 encoder) | testing a technology (generator for the test rig) | low — an *encoder*; the product needs a *decoder* (fldigi) |
| `data/gold/seeds`, `gold_merge.py`, review CSV | research, preparing components (data) | none |
| `modal_jobs/datagen.py`, `tts.py`, `bench.py` | preparing components (data), testing technologies | low |
| `modal_jobs/finetune.py` **dry-run** | testing a technology | low — the *full* run and the adapter it produces happen during the event (gated by `FALOCHRON_EVENT=1`); if we ever ship a pre-event adapter, declare it as a prepared component in the README |
| `tools/download_gazetteer.py`, `data/gazetteer_seed.csv` | preparing a list of required components and purchasing/obtaining them | none — data |
| `cache/` models, tiles | purchasing/obtaining components in advance | none |
| `src/` | **must stay empty** | enforced by `tools/hooks/pre-commit` |

Boundary we hold: nothing that would run in the demo's critical path exists before Friday
18:00. Test harnesses, generators, benchmarks, data and configs do.

## D4 — components, AI tools and honesty

- D4.1–2: publicly available libraries, AI models and tools, and **content generated using
  AI tools** may be used, "provided that they hold the appropriate rights, licenses or
  consents". → licenses recorded in `README.md` (kiwiclient, llama.cpp converter, fldigi
  tables as data, OSM ODbL for the gazetteer, MARTTS per its card).
- D4.3: "It is prohibited to present a solution created by third parties as the Project, or
  to mislead the Main Organizer or the jury as to the authorship of the Project or the
  Team's actual own contribution." → the README states openly that the pre-work was done
  with an AI coding assistant under the author's direction, and that gold labels marked
  `draft` were proposed by the assistant and accepted by the author. Say the same in the
  pitch if asked.
- D4.4: the Project must be demonstrable; provide launch instructions where possible. →
  `docs/demo_checklist.md`, `make` targets, offline cache.

## D6 — IP, safety, ethics

- IP stays with the creators; the organizer acquires nothing. → we may keep the repo
  private or public as we like; no license grant required.
- "prohibited to create solutions that violate security standards or deliberately exploit
  vulnerabilities" → receiving public NAVTEX is lawful MSI reception; VHF audio in the demo
  is synthetic or own-voice (PRD §12.4). No transmission, no decryption, no third-party
  traffic. Say so on one slide.

## Open items to confirm with the organizer/mentors on Friday

1. Pre-event data generation (W1/W2) and the dry-run adapter: confirm they read them as
   "preparing components", as we do.
2. Whether the jury wants the git history as evidence (we will tag `event-start` and
   `demo-freeze` regardless).
3. Scoring weights (published Friday) — adjust the 3-minute pitch to them.
