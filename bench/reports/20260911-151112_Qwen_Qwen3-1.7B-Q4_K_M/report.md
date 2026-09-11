# Benchmark run `20260911-151112_Qwen_Qwen3-1.7B-Q4_K_M` — FAIL

- model: `cache/models/qwen3-1.7b-q4/Qwen_Qwen3-1.7B-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T15:21:08+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 56.0% | 0.85 | ❌ |
| unsupported_fact_rate | 23.3% | 0.02 | ❌ |
| geo_resolution | 30.0% | 0.9 | ❌ |
| latency_p95_s | 81.692 s | 2.0 | ❌ |
| omission_rate | 0.0% | report | — |
| latency_p50_s | 54.959 s | report | — |
| peak_rss_mb | 2519.54 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.60 |
| warning_id | 0.80 |
| issued_at | 0.20 |
| valid_from | 0.80 |
| valid_to | 0.90 |
| geometry | 0.10 |
| location_name | 0.54 |
| agency | 1.00 |
| entities | 0.10 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 4 |
| time_inconsistent | 0 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.70 | issued_at | — | unsupported_fact | 55160 |
| 02_navtex_en_exercise_polygon | ✅ | 0.44 | issued_at, valid_from, geometry | — | geometry_outside_baltic, unsupported_fact | 65478 |
| 03_navtex_en_corrupted_stars | ✅ | 0.48 | issued_at, geometry | — | unsupported_fact | 53879 |
| 04_bhmw_pl_cable_works | ✅ | 0.56 | geometry, entities | — | unsupported_fact | 93097 |
| 05_bhmw_pl_wreck | ✅ | 0.71 | issued_at, geometry | — | unsupported_fact | 52619 |
| 06_vhf_pl_voice_report | ✅ | 0.44 | geometry | — | geometry_outside_baltic, unsupported_fact | 50253 |
| 07_vhf_en_voice_report | ✅ | 0.67 | geometry, entities | — | geometry_outside_baltic, unsupported_fact | 47921 |
| 08_navtex_en_gale_warning | ✅ | 0.56 | issued_at, valid_from, geometry, entities | — | unsupported_fact | 54936 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.56 | issued_at, entities | — | geometry_outside_baltic, unsupported_fact | 54982 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.48 | issued_at, geometry | — | unsupported_fact | 67753 |
