# Benchmark run `20260911-135232_Qwen_Qwen3.5-0.8B-Q4_K_M` — FAIL

- model: `cache/models/qwen3.5-0.8b-q4/Qwen_Qwen3.5-0.8B-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T13:57:54+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 50.0% | 1.0 | ❌ |
| field_f1 | 11.7% | 0.85 | ❌ |
| unsupported_fact_rate | 40.0% | 0.02 | ❌ |
| geo_resolution | 10.0% | 0.9 | ❌ |
| latency_p95_s | 38.694 s | 2.0 | ❌ |
| omission_rate | 28.9% | report | — |
| latency_p50_s | 30.123 s | report | — |
| peak_rss_mb | 1122.516 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.20 |
| warning_id | 0.10 |
| issued_at | 0.00 |
| valid_from | 0.10 |
| valid_to | 0.10 |
| geometry | 0.00 |
| location_name | 0.35 |
| agency | 0.20 |
| entities | 0.00 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 5 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 5 |
| time_inconsistent | 0 |
| unsupported_fact | 5 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.26 | geometry, agency | — | geometry_outside_baltic, unsupported_fact | 25884 |
| 02_navtex_en_exercise_polygon | ❌ | 0.00 | — | event_type, warning_id, issued_at, valid_from, valid_to, geometry, location_name, agency | schema_invalid | 36973 |
| 03_navtex_en_corrupted_stars | ❌ | 0.00 | — | event_type, location_name, agency, entities | schema_invalid | 36030 |
| 04_bhmw_pl_cable_works | ✅ | 0.41 | warning_id, geometry, location_name, agency, entities | — | geometry_outside_baltic, unsupported_fact | 27797 |
| 05_bhmw_pl_wreck | ✅ | 0.19 | warning_id, issued_at, geometry | — | geometry_outside_baltic, unsupported_fact | 29553 |
| 06_vhf_pl_voice_report | ❌ | 0.00 | — | event_type, geometry, location_name, agency, entities | schema_invalid | 37561 |
| 07_vhf_en_voice_report | ❌ | 0.00 | — | event_type, geometry, agency, entities | schema_invalid | 29188 |
| 08_navtex_en_gale_warning | ✅ | 0.11 | warning_id, agency, entities | — | geometry_outside_baltic, unsupported_fact | 29930 |
| 09_navtex_en_fldigi_garbled | ❌ | 0.00 | — | event_type, warning_id, issued_at, location_name, agency | schema_invalid | 39620 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.19 | warning_id, issued_at, valid_from, valid_to, geometry | — | geometry_outside_baltic, unsupported_fact | 30315 |
