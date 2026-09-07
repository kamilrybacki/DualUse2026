# modal_jobs — the cloud data factory (PRD §12.5)

**Rule:** Modal never touches the demo. Every artifact comes back to `cache/` / `data/` with
`modal volume get` and goes on the USB stick. On demo day the Modal account may not exist.

## One-time setup

```
uv sync --extra modal
uv run modal setup                                   # browser login, stores the token locally
uv run modal secret create huggingface HF_TOKEN=hf_xxx
uv run modal volume create falochron-artifacts       # or let common.py create it on first run
```

Secrets: only `huggingface` (HF_TOKEN). Nothing else. Never put tokens in the repo.

## Jobs

| job | PRD | run | GPU / cost (Starter credit: 30 USD/mo) | artifact (volume path → local) |
|---|---|---|---|---|
| `datagen.py` | W1 | `make modal-datagen` (dry) / `modal run modal_jobs/datagen.py --full` | dry: L4 minutes (<1 USD); full: H100 2–3 h (~8–12 USD) | `datagen/<run>/generated.jsonl` → `data/gold/generated/` |
| `tts.py` | W2 | `modal run modal_jobs/tts.py --source datagen/<run>/generated.jsonl` | CPU, minutes (<1 USD) | `vhf_synth/<run>/*.wav + transcripts.jsonl` → `data/audio/vhf_synth/` |
| `bench.py` | W3 | `modal run modal_jobs/bench.py --models qwen3-1.7b-q4 --gold data/gold/en.jsonl` | CPU containers, minutes–1 h (~1–3 USD) | summaries written locally to `bench/reports/<run>_modal/` |
| `finetune.py` | W4 | `make modal-finetune-dry`; full run only with `FALOCHRON_EVENT=1 ... --full` | A100-40GB 20–60 min (~1–2 USD) | `models/<run>/*.gguf` → `cache/models/` |

Dry-run checklist before 11.09 (STATUS.md): each job completes end-to-end once; the
`modal run` output ends with the `modal volume get ...` line to mirror.

## Design notes

- `common.py` holds the app, base image (`schemas/`, `prompts/`, `bench/`, seeds and
  `cache/models.yaml` are added to the image so jobs use the *same* schema, grammar,
  prompts and metrics as the edge node), the volume and the HF secret.
- `datagen_lib.py` and `augment.py` are pure Python (no Modal import) and covered by the
  offline test suite; the Modal files only orchestrate.
- W1 labels are candidates. Deterministic grounding (`bench/metrics.py`) rejects ungrounded
  values before the LLM judge; humans accept into gold via `tools/gold_merge.py`.
- W3 latency/RSS are tagged `host=modal` and never quoted as edge numbers.
- W4 `--full` refuses to run unless `FALOCHRON_EVENT=1` — FROM SCRATCH compliance.
- Model ids for vLLM/TTS/finetune are stated in each file's header; `--dry-run` runs are
  the place to discover API drift (vLLM `SamplingParams`, TRL `SFTConfig`) — the remote prep
  session cannot execute Modal, so the first real run is yours.
