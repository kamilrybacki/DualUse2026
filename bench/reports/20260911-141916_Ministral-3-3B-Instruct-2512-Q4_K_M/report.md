# Benchmark run `20260911-141916_Ministral-3-3B-Instruct-2512-Q4_K_M` — FAIL

- model: `cache/models/ministral-3-3b-q4/Ministral-3-3B-Instruct-2512-Q4_K_M.gguf` (backend llama-cli)
- prompt: `prompts/extract_v0.2.md` v0.2
- gold: `schemas/fixtures` (10 items)
- host: lw-main — Linux-6.17.0-41-generic-x86_64-with-glibc2.42 — tag `lw-main-cpu`
- time: 2026-09-11T14:46:13+00:00

| metric | value | threshold | check |
|---|---|---|---|
| schema_validity | 100.0% | 1.0 | ✅ |
| field_f1 | 60.6% | 0.85 | ❌ |
| unsupported_fact_rate | 12.2% | 0.02 | ❌ |
| geo_resolution | 60.0% | 0.9 | ❌ |
| latency_p95_s | 179.348 s | 2.0 | ❌ |
| omission_rate | 8.9% | report | — |
| latency_p50_s | 165.288 s | report | — |
| peak_rss_mb | 4129.228 | report | — |
| escalation_rate | 70.0% | report | — |

## Per-field F1

| field | F1 |
|---|---|
| event_type | 0.50 |
| warning_id | 0.90 |
| issued_at | 0.30 |
| valid_from | 0.80 |
| valid_to | 0.80 |
| geometry | 0.70 |
| location_name | 0.30 |
| agency | 0.80 |
| entities | 0.35 |

## Escalation triggers (declarative rules from thresholds.yaml)

| rule | items |
|---|---|
| schema_invalid | 0 |
| type_unknown | 1 |
| no_location | 3 |
| geometry_outside_baltic | 0 |
| time_inconsistent | 0 |
| unsupported_fact | 6 |

## Items

| id | valid | F1 | unsupported | omitted | triggers | ms |
|---|---|---|---|---|---|---|
| 01_navtex_en_nav_warning | ✅ | 0.59 | agency | — | unsupported_fact | 154380 |
| 02_navtex_en_exercise_polygon | ✅ | 0.44 | — | location_name | — | 180619 |
| 03_navtex_en_corrupted_stars | ✅ | 0.37 | warning_id, issued_at, geometry, agency, entities | — | unsupported_fact | 142882 |
| 04_bhmw_pl_cable_works | ✅ | 0.65 | issued_at, entities | — | unsupported_fact | 177795 |
| 05_bhmw_pl_wreck | ✅ | 0.78 | issued_at | location_name | unsupported_fact | 172305 |
| 06_vhf_pl_voice_report | ✅ | 0.56 | entities | geometry, location_name | no_location, unsupported_fact | 144161 |
| 07_vhf_en_voice_report | ✅ | 0.67 | entities | geometry | no_location, unsupported_fact | 166372 |
| 08_navtex_en_gale_warning | ✅ | 0.67 | — | — | — | 165424 |
| 09_navtex_en_fldigi_garbled | ✅ | 0.67 | — | event_type, location_name | type_unknown, no_location | 147904 |
| 10_bhmw_pl_prompt_injection | ✅ | 0.67 | — | location_name | — | 165152 |
