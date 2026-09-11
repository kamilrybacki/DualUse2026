# Benchmark run `20260911-125120_Ministral-3-3B-Instruct-2512-Q4_K_M` — FAIL

- model: `cache/models/ministral-3-3b-q4/Ministral-3-3B-Instruct-2512-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T13:12:16+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 90.0% | 1.0 | ❌ |
| field_f1 | 38.8% | 0.85 | ❌ |
| unsupported_fact_rate | 19.8% | 0.02 | ❌ |
| geo_resolution | 40.0% | 0.9 | ❌ |
| latency_p95_s | 176.799 s | 2.0 | ❌ |
| omission_rate | 15.6% | report | — |
| latency_p50_s | 116.592 s | report | — |
| peak_rss_mb | 4134.94 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.50 |
| warning_id | 0.60 |
| issued_at | 0.20 |
| valid_from | 0.30 |
| valid_to | 0.60 |
| geometry | 0.30 |
| location_name | 0.39 |
| agency | 0.40 |
| entities | 0.20 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 1 |
| type_unknown | 2 |
| no_location | 1 |
| geometry_outside_baltic | 3 |
| time_inconsistent | 0 |
| unsupported_fact | 8 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.59 | agency | — | unsupported_fact | 106349 |
| 02_navtex_en_exercise_polygon | ✅ | 0.28 | geometry, agency | — | geometry_outside_baltic, unsupported_fact | 144017 |
| 03_navtex_en_corrupted_stars | ✅ | 0.26 | issued_at, valid_from, geometry, agency | — | unsupported_fact | 116431 |
| 04_bhmw_pl_cable_works | ❌ | 0.00 | — | event_type, warning_id, valid_from, valid_to, geometry, location_name, agency, entities | schema_invalid | 203620 |
| 05_bhmw_pl_wreck | ✅ | 0.82 | issued_at | — | unsupported_fact | 116753 |
| 06_vhf_pl_voice_report | ✅ | 0.44 | — | event_type, geometry, location_name, agency | type_unknown, no_location | 98162 |
| 07_vhf_en_voice_report | ✅ | 0.67 | geometry | — | geometry_outside_baltic, unsupported_fact | 119576 |
| 08_navtex_en_gale_warning | ✅ | 0.22 | geometry | location_name | geometry_outside_baltic, unsupported_fact | 113124 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.11 | valid_from, valid_to, geometry, agency | event_type | type_unknown, unsupported_fact | 127894 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.48 | issued_at, valid_from | — | unsupported_fact | 109675 |
