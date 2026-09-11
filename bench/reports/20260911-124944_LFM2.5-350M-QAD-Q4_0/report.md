# Benchmark run `20260911-124944_LFM2.5-350M-QAD-Q4_0` — FAIL

- model: `cache/models/lfm2.5-350m-q4/LFM2.5-350M-QAD-Q4_0.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T12:51:20+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 90.0% | 1.0 | ❌ |
| field_f1 | 5.0% | 0.85 | ❌ |
| unsupported_fact_rate | 77.8% | 0.02 | ❌ |
| geo_resolution | 0.0% | 0.9 | ❌ |
| latency_p95_s | 11.207 s | 2.0 | ❌ |
| omission_rate | 6.7% | report | — |
| latency_p50_s | 9.449 s | report | — |
| peak_rss_mb | 537.816 | report | — |
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
| location_name | 0.03 |
| agency | 0.00 |
| entities | 0.02 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 1 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 8 |
| time_inconsistent | 3 |
| unsupported_fact | 9 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.22 | issued_at, valid_from, valid_to, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 9514 |
| 02_navtex_en_exercise_polygon | ✅ | 0.03 | warning_id, issued_at, valid_from, geometry, agency, entities | — | geometry_outside_baltic, time_inconsistent, unsupported_fact | 11144 |
| 03_navtex_en_corrupted_stars | ✅ | 0.11 | warning_id, issued_at, valid_from, valid_to, agency, entities | — | geometry_outside_baltic, unsupported_fact | 9383 |
| 04_bhmw_pl_cable_works | ✅ | 0.11 | warning_id, issued_at, valid_from, valid_to, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 8600 |
| 05_bhmw_pl_wreck | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, agency, entities | — | geometry_outside_baltic, time_inconsistent, unsupported_fact | 11257 |
| 06_vhf_pl_voice_report | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, location_name, agency, entities | geometry | unsupported_fact | 7814 |
| 07_vhf_en_voice_report | ✅ | 0.02 | warning_id, issued_at, valid_from, valid_to, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 10198 |
| 08_navtex_en_gale_warning | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, agency, entities | — | geometry_outside_baltic, time_inconsistent, unsupported_fact | 9083 |
| 09_navtex_en_fldigi_garbled | ❌ | 0.00 | — | event_type, warning_id, issued_at, location_name, agency | schema_invalid | 9888 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 9254 |
