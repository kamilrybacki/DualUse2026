# Benchmark run `20260911-140838_granite-4.0-350m-Q4_K_M` — FAIL

- model: `cache/models/granite-4.0-350m-q4/granite-4.0-350m-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T14:11:10+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 26.4% | 0.85 | ❌ |
| unsupported_fact_rate | 46.7% | 0.02 | ❌ |
| geo_resolution | 0.0% | 0.9 | ❌ |
| latency_p95_s | 18.826 s | 2.0 | ❌ |
| omission_rate | 5.6% | report | — |
| latency_p50_s | 14.924 s | report | — |
| peak_rss_mb | 604.02 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.30 |
| warning_id | 0.50 |
| issued_at | 0.40 |
| valid_from | 0.50 |
| valid_to | 0.60 |
| geometry | 0.00 |
| location_name | 0.07 |
| agency | 0.00 |
| entities | 0.00 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 2 |
| time_inconsistent | 0 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.33 | valid_from, geometry, agency | issued_at | unsupported_fact | 14986 |
| 02_navtex_en_exercise_polygon | ✅ | 0.15 | issued_at, geometry, agency, entities | valid_from, valid_to | unsupported_fact | 13650 |
| 03_navtex_en_corrupted_stars | ✅ | 0.22 | valid_from, valid_to, geometry, agency | — | unsupported_fact | 17104 |
| 04_bhmw_pl_cable_works | ✅ | 0.22 | geometry, location_name, agency, entities | valid_from, valid_to | unsupported_fact | 14863 |
| 05_bhmw_pl_wreck | ✅ | 0.33 | warning_id, geometry, location_name, agency, entities | — | unsupported_fact | 16477 |
| 06_vhf_pl_voice_report | ✅ | 0.33 | location_name, agency | — | geometry_outside_baltic, unsupported_fact | 11253 |
| 07_vhf_en_voice_report | ✅ | 0.33 | warning_id, geometry, location_name, agency, entities | — | unsupported_fact | 15863 |
| 08_navtex_en_gale_warning | ✅ | 0.16 | issued_at, valid_from, valid_to, geometry, location_name, agency, entities | — | unsupported_fact | 20235 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.22 | issued_at, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 14250 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.33 | issued_at, geometry, location_name, agency, entities | — | unsupported_fact | 13050 |
