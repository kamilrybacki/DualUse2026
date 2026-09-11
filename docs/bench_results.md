# Benchmark results — SLM extraction cascade (v0.1)

**Run:** 2026-09-11, host `lw-main` (Linux x86-64, 4 cores, 15 GiB), backend `llama-cli`,
tag `lw-main-cpu`. Gold = `schemas/fixtures` (10 hand-labelled pairs: NAVTEX EN incl. `*`-corrupted,
BHMW PL incl. prompt-injection, VHF PL/EN voice, gale warning). Grammar-constrained decoding
(`schemas/extraction.gbnf`), temperature 0. Thresholds are the ones **frozen 2026-09-07 before any
model ran** (`bench/thresholds.yaml`).

> ⚠️ **Two caveats the pitch must respect.**
> 1. **PRD §12.5/§11 conflict:** latency and RAM are only quotable from the *target* node
>    (M720q / field hub). These numbers are lw-main CPU — **target-hardware measurement is pending**.
>    Quality metrics (schema validity, F1, unsupported-fact, geo) are hardware-independent and *are*
>    comparable.
> 2. The `llama-cli` backend **reloads the model on every item**, so the latency here is
>    *per-call load + inference*, not pipeline latency. Real serving latency needs `llama-server`
>    (model resident) and is deferred. Treat the latency column as an upper bound / relative signal only.

## Frozen thresholds (PRD §13)

| metric | PASS | note |
|---|---|---|
| schema_validity | = 100 % | guaranteed by the grammar; <100 % ⇒ truncation/runtime, not the model |
| field_f1 | ≥ 0.85 | mean over 9 scored fields |
| unsupported_fact_rate | ≤ 2 % | **main safety metric** |
| geo_resolution | ≥ 0.90 | geometry within 0.5 nm OR location_name match |
| latency_p95 | ≤ 2 s | tier-2 on the field hub (informational off-target) |

## Headline

**No model passes the frozen thresholds on the zero-shot v0.1 prompt.** This is the expected,
useful baseline: it quantifies exactly how far raw sub-4B models are from the safety bar and motivates
the two levers that FALOCHRON actually ships — the tightened **v0.2 prompt** (sweep in progress) and
the **W4 QLoRA fine-tune** (text→JSON). The grammar already delivers its half of the contract:
schema validity is 90–100 % on every model that doesn't truncate.

## v0.1 — all models (fixtures)

| model | tier | schema % | field F1 % | unsupported % | geo % | p50 s | p95 s | RSS MB | pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| Qwen3-4B | 3 | 90 | **39.7** | 19.8 | 20 | 103.4 | 174.1 | 4976 | ✗ |
| Ministral-3-3B | 3 | 90 | 38.8 | 19.8 | **40** | 116.6 | 176.8 | 4135 | ✗ |
| Phi-4-mini (3.8B) | 3 | 90 | 35.2 | 28.4 | 20 | 77.9 | 121.9 | 4397 | ✗ |
| Qwen3-1.7B | 3 | 100 | 23.2 | 47.8 | 20 | 39.1 | 52.1 | 2524 | ✗ |
| granite-4.0-1b | 2 | 80 | 22.4 | 43.1 | 10 | 44.2 | 105.9 | 2172 | ✗ |
| Qwen3.5-0.8B | 2 | 50 | 11.7 | 40.0 | 10 | 30.1 | 38.7 | 1123 | ✗ |
| LFM2.5-1.2B | 2 | 100 | 10.6 | 63.3 | 0 | 29.4 | 35.7 | 1374 | ✗ |
| granite-4.0-350m | 1 | 100 | 9.2 | 66.7 | 10 | 11.3 | 12.7 | 558 | ✗ |
| LFM2.5-350M | 1 | 90 | 5.0 | 77.8 | 0 | 9.4 | 11.2 | 538 | ✗ |

(`bench/reports/pareto.md` is regenerated on every run; per-run detail in
`bench/reports/<run>/{report.md,summary.json,results.csv,items.jsonl}`.)

## Reading the front

- **Quality scales with size, as expected.** The 3–4B tier (Qwen3-4B, Ministral-3-3B, Phi-4-mini)
  leads on F1 (≈35–40 %) and on the safety metric (unsupported-fact ≈20–28 %). Sub-billion models
  (granite-350m, LFM-350M) sit at F1 5–9 % with unsupported-fact 67–78 % — **not usable zero-shot**.
- **The main candidate, Qwen3.5-0.8B, underperforms zero-shot** (F1 11.7 %, schema **50 %** — it
  over-generates and truncates against the 512-token budget). This is the strongest argument for the
  v0.2 prompt + fine-tune: the 0.8B target needs help the 4B models need less of.
- **Safety metric is the real gap.** Even the best model leaves ~20 % of values ungrounded.
  Constrained decoding fixes *form*, not *truth* — exactly the PRD's `schema-valid ≠ factually correct`
  thesis, and why the deterministic validator + human-review flag sit behind the model.
- **Geo is weak everywhere** (≤40 %): spoken/DMS positions and polygons are the hardest fields.
- **Footprint** matches the PRD node classes: tier-1/2 fit the pocket node (0.5–2.5 GB RSS),
  tier-3 needs the field hub (4–5 GB).

## Three failure examples (raw parsed output vs gold)

**1. Hallucinated geometry — Qwen3-4B (the best model), `01_navtex_en_nav_warning`.**
Source states the buoy position and the year 2026.
```
pred     : geometry {Point [-11.565, 57.182]}   location "KATTEGAT"                 issued 2023-09-07
expected : geometry {Point [ 11.9417, 57.3033]} location "KATTEGAT, LIGHT BUOY NIDINGEN E" issued 2026-09-07
```
Longitude sign flipped into the Atlantic, coordinates invented, year wrong → flagged
`unsupported_fact: [geometry]`. The safety metric catches exactly the failure the jury will fear.

**2. Invalid / truncated polygon — Qwen3-4B, `02_navtex_en_exercise_polygon`.**
```
pred     : null  (valid=false)          expected: EXERCISE, geometry Polygon
```
The one EXERCISE-with-polygon fixture: the model runs past the 512-token budget writing the
coordinate ring and never closes the JSON → grammar-valid prefix, unparseable whole. (Raises
`schema_invalid`; argues for a larger n_predict and/or a polygon-aware prompt.)

**3. Missed PL spoken position + wrong type — Ministral-3-3B, `06_vhf_pl_voice_report`.**
Source (PL voice): "…moja pozycja pięćdziesiąt cztery stopnie trzydzieści dwie minuty północ zero
osiemnaście stopni czterdzieści osiem minut wschód…".
```
pred     : event_type UNKNOWN, geometry null, entities [VESSEL "jednostka", OTHER "bałtyk"]
expected : event_type VOICE_REPORT, geometry Point ≈ [18.80, 54.53]
```
It neither classified the voice report nor converted the spoken PL numbers into a position — the
ASR→extraction path (PRD R1) needs the fine-tune and the number-word normaliser.

## v0.2 — the tightened prompt roughly doubles F1

Same 9 models, `prompts/extract_v0.2.md`, same fixtures/grammar/thresholds.

| model | F1 % (v0.1 → **v0.2**) | unsupported % (v0.1 → v0.2) | schema % | geo % | p50 s | RSS MB |
|---|---|---|---:|---:|---:|---:|
| Ministral-3-3B | 38.8 → **60.6** | 19.8 → 12.2 | 100 | 60 | 165 | 4129 |
| Qwen3-4B | 39.7 → **59.5** | 19.8 → 14.8 | 90 | 50 | 136 | 4923 |
| Qwen3-1.7B | 23.2 → **56.0** | 47.8 → 23.3 | 100 | 30 | 55 | 2520 |
| Phi-4-mini | 35.2 → **47.9** | 28.4 → 12.5 | 80 | 10 | 133 | 4388 |
| granite-4.0-1b | 22.4 → **41.9** | 43.1 → 23.5 | 90 | 30 | 59 | 2162 |
| **Qwen3.5-0.8B** (candidate) | 11.7 → **34.7** | 40.0 → 33.3 | 100 | 20 | 34 | 1031 |
| LFM2.5-1.2B | 10.6 → **27.3** | 63.3 → 52.2 | 100 | 10 | 37 | 1374 |
| granite-4.0-350m | 9.2 → **26.4** | 66.7 → 46.7 | 100 | 0 | 15 | 604 |
| LFM2.5-350M | 5.0 → **5.1** | 77.8 → 54.4 | 100 | 0 | 10 | 509 |

**The headline the pitch quotes:** a single prompt revision (`v0.1`→`v0.2`) roughly **doubles field-F1
across the whole cascade** — Ministral-3-3B and Qwen3-4B jump to ~60 %, and the 0.8B main candidate
**triples (11.7 → 34.7)** — while unsupported-fact drops (e.g. Phi-4-mini 28 → 13 %, Ministral 20 → 12 %)
and schema validity is 100 % on almost every model. Geo also climbs (Ministral 40 → 60 %).

**Still nobody passes the frozen bar** (best F1 60.6 < 0.85; best unsupported 12.2 % > 2 %). That is the
whole argument for the two remaining levers: prompt engineering alone gets the 3-4B tier two-thirds of
the way; the **W4 QLoRA fine-tune** (text→JSON on Qwen3.5-0.8B, gold from W1 + human review) is what
closes the last third — especially for the sub-billion target, which needs the most help. Note LFM-350M
barely moves (5.0 → 5.1): the ultra-light EN model is a dead end for this task, prompt or not.

(v0.1 and v0.2 measured on lw-main CPU; the latency/RSS caveat above applies to both.)

## Not yet measured (deferred / event-time)

- **Target-hardware latency & RSS** (M720q / field hub) via `llama-server` — the only latency the PRD
  permits quoting.
- **Gold splits** `data/gold/{pl,en,noisy}` — empty pending human review of the 46 seeds, so these
  numbers are on the 10 fixtures only. The frozen thresholds are unchanged when real gold lands.
- **Modal W3** parallel sweep (`host=modal`) — quality cross-check, never quoted as edge numbers.
