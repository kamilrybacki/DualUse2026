# Benchmark run `20260911-124243_granite-4.0-350m-Q4_K_M` — FAIL

- model: `cache/models/granite-4.0-350m-q4/granite-4.0-350m-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T12:44:34+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 9.2% | 0.85 | ❌ |
| unsupported_fact_rate | 66.7% | 0.02 | ❌ |
| geo_resolution | 10.0% | 0.9 | ❌ |
| latency_p95_s | 12.667 s | 2.0 | ❌ |
| omission_rate | 0.0% | report | — |
| latency_p50_s | 11.330 s | report | — |
| peak_rss_mb | 558.376 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.30 |
| warning_id | 0.30 |
| issued_at | 0.00 |
| valid_from | 0.00 |
| valid_to | 0.00 |
| geometry | 0.00 |
| location_name | 0.23 |
| agency | 0.00 |
| entities | 0.00 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 10 |
| time_inconsistent | 0 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.22 | issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 9624 |
| 02_navtex_en_exercise_polygon | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, agency, entities | — | geometry_outside_baltic, unsupported_fact | 9616 |
| 03_navtex_en_corrupted_stars | ✅ | 0.11 | issued_at, valid_from, valid_to, geometry, location_name, agency | — | geometry_outside_baltic, unsupported_fact | 9330 |
| 04_bhmw_pl_cable_works | ✅ | 0.31 | issued_at, valid_from, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 12875 |
| 05_bhmw_pl_wreck | ✅ | 0.16 | issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 12414 |
| 06_vhf_pl_voice_report | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 10848 |
| 07_vhf_en_voice_report | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 10245 |
| 08_navtex_en_gale_warning | ✅ | 0.11 | issued_at, valid_from, valid_to, geometry, agency, entities | — | geometry_outside_baltic, unsupported_fact | 11812 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, agency | — | geometry_outside_baltic, unsupported_fact | 12027 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.00 | warning_id, issued_at, valid_from, valid_to, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 11953 |
