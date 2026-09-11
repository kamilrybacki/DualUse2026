# Benchmark run `20260911-133314_Qwen3-4B-Q4_K_M` — FAIL

- model: `cache/models/qwen3-4b-q4/Qwen3-4B-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T13:52:31+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 90.0% | 1.0 | ❌ |
| field_f1 | 39.7% | 0.85 | ❌ |
| unsupported_fact_rate | 19.8% | 0.02 | ❌ |
| geo_resolution | 20.0% | 0.9 | ❌ |
| latency_p95_s | 174.072 s | 2.0 | ❌ |
| omission_rate | 15.6% | report | — |
| latency_p50_s | 103.369 s | report | — |
| peak_rss_mb | 4976.292 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.40 |
| warning_id | 0.80 |
| issued_at | 0.20 |
| valid_from | 0.30 |
| valid_to | 0.50 |
| geometry | 0.00 |
| location_name | 0.47 |
| agency | 0.70 |
| entities | 0.20 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 1 |
| type_unknown | 3 |
| no_location | 1 |
| geometry_outside_baltic | 6 |
| time_inconsistent | 0 |
| unsupported_fact | 7 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.37 | geometry | — | geometry_outside_baltic, unsupported_fact | 101143 |
| 02_navtex_en_exercise_polygon | ❌ | 0.00 | — | event_type, warning_id, issued_at, valid_from, valid_to, geometry, location_name, agency | schema_invalid | 194610 |
| 03_navtex_en_corrupted_stars | ✅ | 0.15 | issued_at, valid_from, valid_to, geometry | event_type | type_unknown, geometry_outside_baltic, unsupported_fact | 102730 |
| 04_bhmw_pl_cable_works | ✅ | 0.65 | issued_at, geometry, entities | — | unsupported_fact | 98047 |
| 05_bhmw_pl_wreck | ✅ | 0.37 | issued_at, valid_from, geometry | — | geometry_outside_baltic, unsupported_fact | 104007 |
| 06_vhf_pl_voice_report | ✅ | 0.47 | — | event_type, geometry, location_name, agency | type_unknown, no_location | 111727 |
| 07_vhf_en_voice_report | ✅ | 0.59 | agency | event_type | type_unknown, geometry_outside_baltic, unsupported_fact | 89310 |
| 08_navtex_en_gale_warning | ✅ | 0.44 | geometry | — | geometry_outside_baltic, unsupported_fact | 123899 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.44 | — | — | geometry_outside_baltic | 148970 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.48 | issued_at, valid_from, geometry | — | unsupported_fact | 82425 |
