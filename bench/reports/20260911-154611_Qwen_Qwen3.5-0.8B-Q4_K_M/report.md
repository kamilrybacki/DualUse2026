# Benchmark run `20260911-154611_Qwen_Qwen3.5-0.8B-Q4_K_M` — FAIL

- model: `cache/models/qwen3.5-0.8b-q4/Qwen_Qwen3.5-0.8B-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T15:52:04+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 34.7% | 0.85 | ❌ |
| unsupported_fact_rate | 33.3% | 0.02 | ❌ |
| geo_resolution | 20.0% | 0.9 | ❌ |
| latency_p95_s | 42.218 s | 2.0 | ❌ |
| omission_rate | 0.0% | report | — |
| latency_p50_s | 34.171 s | report | — |
| peak_rss_mb | 1030.872 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.60 |
| warning_id | 0.60 |
| issued_at | 0.10 |
| valid_from | 0.40 |
| valid_to | 0.50 |
| geometry | 0.00 |
| location_name | 0.40 |
| agency | 0.50 |
| entities | 0.03 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 7 |
| time_inconsistent | 0 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.48 | geometry, agency | — | unsupported_fact | 31297 |
| 02_navtex_en_exercise_polygon | ✅ | 0.25 | valid_to, geometry, location_name, entities | — | unsupported_fact | 40454 |
| 03_navtex_en_corrupted_stars | ✅ | 0.37 | geometry, agency | — | geometry_outside_baltic, unsupported_fact | 29880 |
| 04_bhmw_pl_cable_works | ✅ | 0.37 | geometry, entities | — | geometry_outside_baltic, unsupported_fact | 33558 |
| 05_bhmw_pl_wreck | ✅ | 0.15 | issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 43661 |
| 06_vhf_pl_voice_report | ✅ | 0.44 | issued_at, geometry | — | geometry_outside_baltic, unsupported_fact | 36147 |
| 07_vhf_en_voice_report | ✅ | 0.47 | issued_at, geometry | — | geometry_outside_baltic, unsupported_fact | 32078 |
| 08_navtex_en_gale_warning | ✅ | 0.33 | issued_at, valid_from, valid_to | — | geometry_outside_baltic, unsupported_fact | 34783 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.22 | issued_at, valid_from, valid_to, geometry, agency, entities | — | unsupported_fact | 31787 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.37 | valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 39190 |
