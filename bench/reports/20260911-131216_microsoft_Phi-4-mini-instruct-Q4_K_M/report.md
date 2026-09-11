# Benchmark run `20260911-131216_microsoft_Phi-4-mini-instruct-Q4_K_M` — FAIL

- model: `cache/models/phi-4-mini-q4/microsoft_Phi-4-mini-instruct-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T13:26:28+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 90.0% | 1.0 | ❌ |
| field_f1 | 35.2% | 0.85 | ❌ |
| unsupported_fact_rate | 28.4% | 0.02 | ❌ |
| geo_resolution | 20.0% | 0.9 | ❌ |
| latency_p95_s | 121.921 s | 2.0 | ❌ |
| omission_rate | 6.7% | report | — |
| latency_p50_s | 77.926 s | report | — |
| peak_rss_mb | 4396.7 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.60 |
| warning_id | 0.60 |
| issued_at | 0.10 |
| valid_from | 0.50 |
| valid_to | 0.60 |
| geometry | 0.10 |
| location_name | 0.33 |
| agency | 0.30 |
| entities | 0.04 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 1 |
| type_unknown | 0 |
| no_location | 0 |
| geometry_outside_baltic | 5 |
| time_inconsistent | 0 |
| unsupported_fact | 9 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.51 | geometry, agency | — | unsupported_fact | 74281 |
| 02_navtex_en_exercise_polygon | ✅ | 0.17 | geometry, agency | — | geometry_outside_baltic, unsupported_fact | 82840 |
| 03_navtex_en_corrupted_stars | ✅ | 0.33 | warning_id, issued_at, valid_from, agency | — | unsupported_fact | 73756 |
| 04_bhmw_pl_cable_works | ✅ | 0.56 | geometry | — | geometry_outside_baltic, unsupported_fact | 83429 |
| 05_bhmw_pl_wreck | ✅ | 0.36 | issued_at, geometry, agency | — | unsupported_fact | 75744 |
| 06_vhf_pl_voice_report | ❌ | 0.00 | — | event_type, geometry, location_name, agency, entities | schema_invalid | 138088 |
| 07_vhf_en_voice_report | ✅ | 0.49 | geometry, agency | — | geometry_outside_baltic, unsupported_fact | 69122 |
| 08_navtex_en_gale_warning | ✅ | 0.44 | issued_at, valid_from, valid_to | — | geometry_outside_baltic, unsupported_fact | 72155 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.22 | issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 102162 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.44 | issued_at | geometry | unsupported_fact | 80108 |
