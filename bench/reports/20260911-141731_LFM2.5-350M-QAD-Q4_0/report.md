# Benchmark run `20260911-141731_LFM2.5-350M-QAD-Q4_0` — FAIL

- model: `cache/models/lfm2.5-350m-q4/LFM2.5-350M-QAD-Q4_0.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T14:19:16+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 5.1% | 0.85 | ❌ |
| unsupported_fact_rate | 54.4% | 0.02 | ❌ |
| geo_resolution | 0.0% | 0.9 | ❌ |
| latency_p95_s | 11.092 s | 2.0 | ❌ |
| omission_rate | 0.0% | report | — |
| latency_p50_s | 10.421 s | report | — |
| peak_rss_mb | 509.128 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.20 |
| warning_id | 0.00 |
| issued_at | 0.00 |
| valid_from | 0.00 |
| valid_to | 0.00 |
| geometry | 0.00 |
| location_name | 0.06 |
| agency | 0.20 |
| entities | 0.00 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 5 |
| time_inconsistent | 0 |
| unsupported_fact | 10 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.00 | issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 10458 |
| 02_navtex_en_exercise_polygon | ✅ | 0.14 | issued_at, valid_from, valid_to, geometry, location_name | — | geometry_outside_baltic, unsupported_fact | 10973 |
| 03_navtex_en_corrupted_stars | ✅ | 0.00 | issued_at, valid_from, valid_to, geometry | — | unsupported_fact | 10164 |
| 04_bhmw_pl_cable_works | ✅ | 0.02 | warning_id, issued_at, valid_to, geometry, entities | — | unsupported_fact | 11189 |
| 05_bhmw_pl_wreck | ✅ | 0.13 | issued_at, valid_from, valid_to, geometry | — | unsupported_fact | 10384 |
| 06_vhf_pl_voice_report | ✅ | 0.11 | issued_at, valid_from, valid_to, geometry, location_name, entities | — | geometry_outside_baltic, unsupported_fact | 10103 |
| 07_vhf_en_voice_report | ✅ | 0.00 | issued_at, valid_from, valid_to, geometry, location_name | — | unsupported_fact | 10298 |
| 08_navtex_en_gale_warning | ✅ | 0.00 | issued_at, valid_from, valid_to, agency | — | geometry_outside_baltic, unsupported_fact | 9600 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.00 | issued_at, valid_from, valid_to, geometry, location_name, entities | — | geometry_outside_baltic, unsupported_fact | 10909 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.11 | warning_id, issued_at, valid_from, valid_to, geometry, location_name | — | unsupported_fact | 10892 |
