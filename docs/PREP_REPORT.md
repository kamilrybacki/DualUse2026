# FALOCHRON — pre-event prep report (session 2, 2026-09-11, lw-main, networked)

Repo: `github.com/kamilrybacki/DualUse2026` (name diverges from `falochron/` in the docs).
`make lint` + `make test` **green (93 tests)**. All prep commits landed before the 16:00 UTC
event open. This session closed the network-bound blockers left by the offline session 1.

## What is cached (offline, USB-mirror targets)

| Artifact | Where | Size | State |
|---|---|---|---|
| SLM + ASR models (12) | `cache/models/` | **14 GB** | sha256 + HF revision in `cache/MANIFEST.md` |
| llama.cpp (Release build) | `cache/llama.cpp/build/bin/` | ~1 GB | llama-cli/server/test-gbnf-validator |
| Baltic gazetteer | `data/gazetteer.sqlite` (627 KB) + `cache/gazetteer_overpass.json` (4.7 MB) | 4 333 rows | `--lookup Hel` ✓; rebuild offline `--from-cache` |
| MARTTS EN ASR eval | `data/martts/` | 1.3 GB audio (ignored) + 1.3 MB jsonl | cc-by-4.0, attributed |
| W1 synthetic candidates | `data/gold/generated/20260911-140837-dry/` | 38 items | 5 judge-accepted, in `pending.csv` |
| Bench reports | `bench/reports/` | v0.1 ×9 done, v0.2 running | summaries + `pareto.md` + `docs/bench_results.md` |
| Off-air recordings | `data/recordings/518khz/` | U-slot 15:20Z **armed** | decode + log after capture |

Models: granite-4.0-350m/1b, LFM2.5-350M(QAD-Q4_0)/1.2B, Qwen3.5-0.8B, Ministral-3-3B,
Phi-4-mini, Qwen3-1.7B, Qwen3-4B (Q4_K_M) + whisper ggml small/medium/large-v3-turbo.

## Which model passes the frozen thresholds

**None — on the zero-shot v0.1 prompt** (thresholds: schema 100 %, field-F1 ≥ 0.85,
unsupported-fact ≤ 2 %, geo ≥ 0.90). This is the honest baseline and the pitch's motivation:
- The 3–4B tier leads (Qwen3-4B / Ministral-3-3B: F1 ≈ 39–40 %, unsupported ≈ 20 %); sub-billion
  models are unusable zero-shot (unsupported 67–78 %).
- The grammar already gives 90–100 % schema validity — form is solved; **truth is the gap** → the
  v0.2 prompt (sweep finishing) and the W4 QLoRA fine-tune are exactly the two levers that close it.
- ⚠️ Latency/RSS are **lw-main CPU numbers** (per-item model reload); PRD §12.5 forbids quoting
  them off the target node — flagged in `docs/bench_results.md`; target-HW measurement is pending.

## Clean NAVTEX recordings

**0 captured this session, 1 armed.** kiwisdr.com/public suffered a transient outage + a new
anti-bot gate (the receiver directory can't be scraped — needs a real browser). One recording is
armed for **station U (Tallinn), 15:20 UTC**, from `sk5sm.proxy.kiwisdr.com` (SE) and
`oh3aa.dy.fi:18073` (FI) in parallel (hosts you supplied). The PRD's ≥6-clean/≥2-station target is
physically impossible today (only two slots before the event). Existing real-signal evidence stands:
9 off-air 2018 decodes @0 % CER + 25 navtex.lv seeds + a fresh sigidwiki SITOR-B decode.

## Modal dry-runs

- **Auth + secret:** creds recovered from `~/.modal.toml`, saved to Vault `secret/homelab/modal/api`;
  `huggingface` secret created from Vault `homelab/huggingface#token`.
- **W1 datagen ✓** end-to-end (L4, Qwen2.5-7B): fixed a real drift (flashinfer sampler needs no
  nvcc → `VLLM_USE_FLASHINFER_SAMPLER=0`) and a prompt bug (7B merged the time into the NAVTEX
  header). Result: 38 items, **5 judge-accepted**, `truncated_prompts=0`.
- **W2 / W3 / W4 dry-runs: not run** (time window). W1 proved the image + secret + GPU path, so
  these are low-risk follow-ups; each `modal run -m modal_jobs.<job>` per `modal_jobs/README.md`.

## Open for the human

1. **Review the gold candidates** — `data/gold/review/pending.csv` (84: 46 real seeds + 38 W1),
   set `verdict`, then `--import-review` + `make gold-merge`. Gold splits are empty until this.
2. **Own-voice VHF** — record PL/EN reports in your own voice (never third-party traffic).
3. **Recordings** — decode + log the 15:20 U capture; grab more 518 kHz slots (2 per 4 h) once
   kiwisdr.com is stable.
4. **Modal W2/W3/W4** dry-runs + the full W4 QLoRA (event-window, `FALOCHRON_EVENT=1`).
5. **Map tiles (P2.12)** — Baltic pmtiles extract into `cache/tiles/` (not done).
6. **Vault** — Modal leaf `secret/homelab/modal/api` is written but not yet in the ansible
   `migrate/map.yaml` (add for reproducibility).

## USB mirror (run when the stick is mounted)

```
rsync -a cache/ data/recordings/ data/audio/ <mount>/falochron/
```
