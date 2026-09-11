# Benchmark run `20260911-144614_microsoft_Phi-4-mini-instruct-Q4_K_M` — FAIL

- model: `cache/models/phi-4-mini-q4/microsoft_Phi-4-mini-instruct-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T15:11:12+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 80.0% | 1.0 | ❌ |
| field_f1 | 47.9% | 0.85 | ❌ |
| unsupported_fact_rate | 12.5% | 0.02 | ❌ |
| geo_resolution | 10.0% | 0.9 | ❌ |
| latency_p95_s | 232.576 s | 2.0 | ❌ |
| omission_rate | 24.4% | report | — |
| latency_p50_s | 132.624 s | report | — |
| peak_rss_mb | 4387.748 | report | — |
| escalation_rate | 90.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.40 |
| warning_id | 0.70 |
| issued_at | 0.40 |
| valid_from | 0.70 |
| valid_to | 0.60 |
| geometry | 0.10 |
| location_name | 0.47 |
| agency | 0.60 |
| entities | 0.33 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 2 |
| type_unknown | 1 |
| no_location | 2 |
| geometry_outside_baltic | 1 |
| time_inconsistent | 0 |
| unsupported_fact | 6 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.73 | issued_at, geometry | — | unsupported_fact | 118642 |
| 02_navtex_en_exercise_polygon | ✅ | 0.50 | issued_at, geometry | valid_from, valid_to | geometry_outside_baltic, unsupported_fact | 123977 |
| 03_navtex_en_corrupted_stars | ✅ | 0.49 | geometry, entities | — | unsupported_fact | 120657 |
| 04_bhmw_pl_cable_works | ❌ | 0.00 | — | event_type, warning_id, valid_from, valid_to, geometry, location_name, agency, entities | schema_invalid | 232680 |
| 05_bhmw_pl_wreck | ✅ | 0.64 | geometry | — | unsupported_fact | 135155 |
| 06_vhf_pl_voice_report | ✅ | 0.44 | entities | event_type, geometry, location_name, agency | type_unknown, no_location, unsupported_fact | 133166 |
| 07_vhf_en_voice_report | ✅ | 0.70 | — | geometry | no_location | 132082 |
| 08_navtex_en_gale_warning | ✅ | 0.67 | issued_at | valid_to | unsupported_fact | 130298 |
| 09_navtex_en_fldigi_garbled | ❌ | 0.00 | — | event_type, warning_id, issued_at, location_name, agency | schema_invalid | 232449 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.61 | — | geometry | — | 138977 |
