# Benchmark run `20260911-132629_Qwen_Qwen3-1.7B-Q4_K_M` — FAIL

- model: `cache/models/qwen3-1.7b-q4/Qwen_Qwen3-1.7B-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.1.md` v0.1
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T13:33:13+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 23.2% | 0.85 | ❌ |
| unsupported_fact_rate | 47.8% | 0.02 | ❌ |
| geo_resolution | 20.0% | 0.9 | ❌ |
| latency_p95_s | 52.138 s | 2.0 | ❌ |
| omission_rate | 6.7% | report | — |
| latency_p50_s | 39.129 s | report | — |
| peak_rss_mb | 2524.224 | report | — |
| escalation_rate | 100.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.40 |
| warning_id | 0.50 |
| issued_at | 0.00 |
| valid_from | 0.10 |
| valid_to | 0.10 |
| geometry | 0.10 |
| location_name | 0.46 |
| agency | 0.40 |
| entities | 0.03 |

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
| 01_navtex_en_nav_warning | ✅ | 0.26 | issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 49158 |
| 02_navtex_en_exercise_polygon | ✅ | 0.17 | issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 41487 |
| 03_navtex_en_corrupted_stars | ✅ | 0.15 | issued_at, valid_from, valid_to, geometry, agency | — | unsupported_fact | 38766 |
| 04_bhmw_pl_cable_works | ✅ | 0.59 | issued_at | geometry, entities | unsupported_fact | 31577 |
| 05_bhmw_pl_wreck | ✅ | 0.26 | issued_at, valid_from, valid_to | geometry, entities | unsupported_fact | 35327 |
| 06_vhf_pl_voice_report | ✅ | 0.04 | warning_id, issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 45500 |
| 07_vhf_en_voice_report | ✅ | 0.03 | warning_id, issued_at, valid_from, valid_to, geometry, agency | — | geometry_outside_baltic, unsupported_fact | 54576 |
| 08_navtex_en_gale_warning | ✅ | 0.56 | issued_at, valid_from, valid_to | — | unsupported_fact | 32198 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.11 | warning_id, issued_at, valid_from, valid_to, agency | — | geometry_outside_baltic, unsupported_fact | 39493 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.15 | warning_id, issued_at, valid_from, valid_to | geometry, entities | unsupported_fact | 36063 |
