# Benchmark run `20260911-124434_LFM2.5-1.2B-Instruct-Q4_K_M` — FAIL

- model: `cache/models/lfm2.5-1.2b-q4/LFM2.5-1.2B-Instruct-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T12:49:43+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 10.6% | 0.85 | ❌ |
| unsupported_fact_rate | 63.3% | 0.02 | ❌ |
| geo_resolution | 0.0% | 0.9 | ❌ |
| latency_p95_s | 35.682 s | 2.0 | ❌ |
| omission_rate | 0.0% | report | — |
| latency_p50_s | 29.382 s | report | — |
| peak_rss_mb | 1374.472 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.30 |
| warning_id | 0.10 |
| issued_at | 0.00 |
| valid_from | 0.00 |
| valid_to | 0.00 |
| geometry | 0.00 |
| location_name | 0.24 |
| agency | 0.30 |
| entities | 0.02 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 10 |
| time_inconsistent | 3 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.11 | warning_id, issued_at, valid_from, valid_to, geometry, agency, entities | — | geometry_outside_baltic, time_inconsistent, unsupported_fact | 27881 |
| 02_navtex_en_exercise_polygon | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, entities | — | geometry_outside_baltic, time_inconsistent, unsupported_fact | 33441 |
| 03_navtex_en_corrupted_stars | ✅ | 0.11 | warning_id, issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, time_inconsistent, unsupported_fact | 29463 |
| 04_bhmw_pl_cable_works | ✅ | 0.42 | geometry, entities | — | geometry_outside_baltic, unsupported_fact | 31545 |
| 05_bhmw_pl_wreck | ✅ | 0.20 | issued_at, valid_from, valid_to, geometry, entities | — | geometry_outside_baltic, unsupported_fact | 37268 |
| 06_vhf_pl_voice_report | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, location_name, entities | — | geometry_outside_baltic, unsupported_fact | 29302 |
| 07_vhf_en_voice_report | ✅ | 0.02 | warning_id, issued_at, valid_from, valid_to, geometry, location_name, entities | — | geometry_outside_baltic, unsupported_fact | 33743 |
| 08_navtex_en_gale_warning | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, entities | — | geometry_outside_baltic, unsupported_fact | 29257 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, location_name, entities | — | geometry_outside_baltic, unsupported_fact | 28678 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.20 | warning_id, issued_at, valid_from, valid_to, geometry, entities | — | geometry_outside_baltic, unsupported_fact | 28076 |
