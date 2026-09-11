# Benchmark run `20260911-152109_Qwen3-4B-Q4_K_M` — FAIL

- model: `cache/models/qwen3-4b-q4/Qwen3-4B-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T15:46:10+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 90.0% | 1.0 | ❌ |
| field_f1 | 59.5% | 0.85 | ❌ |
| unsupported_fact_rate | 14.8% | 0.02 | ❌ |
| geo_resolution | 50.0% | 0.9 | ❌ |
| latency_p95_s | 218.260 s | 2.0 | ❌ |
| omission_rate | 11.1% | report | — |
| latency_p50_s | 136.375 s | report | — |
| peak_rss_mb | 4922.58 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.50 |
| warning_id | 0.80 |
| issued_at | 0.40 |
| valid_from | 0.80 |
| valid_to | 0.80 |
| geometry | 0.40 |
| location_name | 0.51 |
| agency | 0.90 |
| entities | 0.25 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 1 |
| type_unknown | 1 |
| no_location | 1 |
| geometry_outside_baltic | 1 |
| time_inconsistent | 0 |
| unsupported_fact | 9 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.70 | geometry | — | unsupported_fact | 155533 |
| 02_navtex_en_exercise_polygon | ✅ | 0.51 | issued_at | valid_from, valid_to | unsupported_fact | 197401 |
| 03_navtex_en_corrupted_stars | ✅ | 0.48 | issued_at, geometry | — | unsupported_fact | 130034 |
| 04_bhmw_pl_cable_works | ✅ | 0.72 | issued_at, entities | — | unsupported_fact | 156084 |
| 05_bhmw_pl_wreck | ✅ | 0.88 | issued_at | — | unsupported_fact | 137235 |
| 06_vhf_pl_voice_report | ✅ | 0.56 | entities | event_type, geometry, location_name | type_unknown, no_location, unsupported_fact | 111335 |
| 07_vhf_en_voice_report | ✅ | 0.56 | geometry | — | unsupported_fact | 119310 |
| 08_navtex_en_gale_warning | ✅ | 0.89 | geometry | — | geometry_outside_baltic, unsupported_fact | 123222 |
| 09_navtex_en_fldigi_garbled | ❌ | 0.00 | — | event_type, warning_id, issued_at, location_name, agency | schema_invalid | 235326 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.66 | issued_at, entities | — | unsupported_fact | 135515 |
