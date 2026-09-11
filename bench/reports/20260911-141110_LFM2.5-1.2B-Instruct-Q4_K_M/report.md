# Benchmark run `20260911-141110_LFM2.5-1.2B-Instruct-Q4_K_M` — FAIL

- model: `cache/models/lfm2.5-1.2b-q4/LFM2.5-1.2B-Instruct-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T14:17:30+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 27.3% | 0.85 | ❌ |
| unsupported_fact_rate | 52.2% | 0.02 | ❌ |
| geo_resolution | 10.0% | 0.9 | ❌ |
| latency_p95_s | 42.504 s | 2.0 | ❌ |
| omission_rate | 2.2% | report | — |
| latency_p50_s | 37.296 s | report | — |
| peak_rss_mb | 1373.616 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.30 |
| warning_id | 0.70 |
| issued_at | 0.00 |
| valid_from | 0.50 |
| valid_to | 0.40 |
| geometry | 0.00 |
| location_name | 0.23 |
| agency | 0.30 |
| entities | 0.03 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 9 |
| time_inconsistent | 0 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.44 | issued_at, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 37535 |
| 02_navtex_en_exercise_polygon | ✅ | 0.17 | issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 40465 |
| 03_navtex_en_corrupted_stars | ✅ | 0.33 | issued_at, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 36313 |
| 04_bhmw_pl_cable_works | ✅ | 0.33 | issued_at, geometry, location_name, entities | valid_from, valid_to | geometry_outside_baltic, unsupported_fact | 36606 |
| 05_bhmw_pl_wreck | ✅ | 0.22 | issued_at, valid_from, valid_to, geometry, location_name | — | unsupported_fact | 39178 |
| 06_vhf_pl_voice_report | ✅ | 0.22 | warning_id, issued_at, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 32440 |
| 07_vhf_en_voice_report | ✅ | 0.25 | warning_id, issued_at, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 35863 |
| 08_navtex_en_gale_warning | ✅ | 0.22 | issued_at, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 41375 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.22 | issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 43428 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.31 | issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 37058 |
