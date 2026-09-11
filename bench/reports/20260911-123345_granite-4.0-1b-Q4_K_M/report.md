# Benchmark run `20260911-123345_granite-4.0-1b-Q4_K_M` — FAIL

- model: `cache/models/granite-4.0-1b-q4/granite-4.0-1b-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T12:42:42+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 80.0% | 1.0 | ❌ |
| field_f1 | 22.4% | 0.85 | ❌ |
| unsupported_fact_rate | 43.1% | 0.02 | ❌ |
| geo_resolution | 10.0% | 0.9 | ❌ |
| latency_p95_s | 105.877 s | 2.0 | ❌ |
| omission_rate | 13.3% | report | — |
| latency_p50_s | 44.227 s | report | — |
| peak_rss_mb | 2171.696 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.40 |
| warning_id | 0.50 |
| issued_at | 0.00 |
| valid_from | 0.10 |
| valid_to | 0.40 |
| geometry | 0.10 |
| location_name | 0.27 |
| agency | 0.10 |
| entities | 0.14 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 2 |
| type_unknown | 2 |
| no_location | 0 |
| geometry_outside_baltic | 3 |
| time_inconsistent | 0 |
| unsupported_fact | 8 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.26 | issued_at, valid_from, valid_to, geometry, agency | — | unsupported_fact | 53683 |
| 02_navtex_en_exercise_polygon | ✅ | 0.28 | issued_at, valid_from, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 48215 |
| 03_navtex_en_corrupted_stars | ✅ | 0.15 | issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 39546 |
| 04_bhmw_pl_cable_works | ✅ | 0.27 | geometry, entities | event_type | type_unknown, unsupported_fact | 41834 |
| 05_bhmw_pl_wreck | ✅ | 0.48 | issued_at, geometry, entities | event_type | type_unknown, unsupported_fact | 46620 |
| 06_vhf_pl_voice_report | ❌ | 0.00 | — | event_type, geometry, location_name, agency, entities | schema_invalid | 74680 |
| 07_vhf_en_voice_report | ✅ | 0.11 | warning_id, issued_at, valid_from, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 34937 |
| 08_navtex_en_gale_warning | ✅ | 0.44 | issued_at, valid_from, valid_to | — | unsupported_fact | 28421 |
| 09_navtex_en_fldigi_garbled | ❌ | 0.00 | — | event_type, warning_id, issued_at, location_name, agency | schema_invalid | 131401 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.24 | issued_at, valid_from, geometry, entities | — | unsupported_fact | 38017 |
