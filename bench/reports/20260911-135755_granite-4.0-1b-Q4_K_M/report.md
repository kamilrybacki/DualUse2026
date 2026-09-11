# Benchmark run `20260911-135755_granite-4.0-1b-Q4_K_M` — FAIL

- model: `cache/models/granite-4.0-1b-q4/granite-4.0-1b-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T14:08:37+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 90.0% | 1.0 | ❌ |
| field_f1 | 41.9% | 0.85 | ❌ |
| unsupported_fact_rate | 23.5% | 0.02 | ❌ |
| geo_resolution | 30.0% | 0.9 | ❌ |
| latency_p95_s | 91.110 s | 2.0 | ❌ |
| omission_rate | 14.4% | report | — |
| latency_p50_s | 58.598 s | report | — |
| peak_rss_mb | 2162.136 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.30 |
| warning_id | 0.80 |
| issued_at | 0.20 |
| valid_from | 0.60 |
| valid_to | 0.60 |
| geometry | 0.20 |
| location_name | 0.47 |
| agency | 0.60 |
| entities | 0.00 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 1 |
| type_unknown | 4 |
| no_location | 1 |
| geometry_outside_baltic | 1 |
| time_inconsistent | 0 |
| unsupported_fact | 7 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.59 | issued_at, geometry | — | unsupported_fact | 54642 |
| 02_navtex_en_exercise_polygon | ✅ | 0.32 | issued_at, valid_from, geometry | — | unsupported_fact | 70790 |
| 03_navtex_en_corrupted_stars | ✅ | 0.26 | issued_at, geometry, agency | event_type | type_unknown, unsupported_fact | 55806 |
| 04_bhmw_pl_cable_works | ✅ | 0.66 | — | event_type | type_unknown | 67925 |
| 05_bhmw_pl_wreck | ✅ | 0.59 | issued_at, entities | event_type | type_unknown, unsupported_fact | 54910 |
| 06_vhf_pl_voice_report | ✅ | 0.44 | — | event_type, geometry, location_name, agency, entities | type_unknown, no_location | 44856 |
| 07_vhf_en_voice_report | ✅ | 0.56 | geometry, location_name | — | geometry_outside_baltic, unsupported_fact | 55502 |
| 08_navtex_en_gale_warning | ✅ | 0.44 | issued_at, valid_from, geometry | — | unsupported_fact | 61389 |
| 09_navtex_en_fldigi_garbled | ❌ | 0.00 | — | event_type, warning_id, issued_at, location_name, agency | schema_invalid | 107736 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.32 | issued_at, valid_from, valid_to, geometry | — | unsupported_fact | 68963 |
