# bench/ — SLM cascade benchmark (technology test, PRD §13)

Runs (model GGUF × prompt version × gold set) through llama.cpp **with the same GBNF grammar
the product will use**, and scores the output against gold labels and against the source
text. Thresholds in `thresholds.yaml` were frozen before the first model run.

```
make bench-fake                                    # smoke run, no model (fake backend)
make bench MODEL=cache/models/qwen3.5-0.8b-q4/x.gguf
uv run python bench/run_bench.py --backend llama-server --server http://127.0.0.1:8080 \
    --gold data/gold/en.jsonl --tag m720q
```

Outputs per run in `bench/reports/<run-id>/`: `report.md`, `results.csv`, `items.jsonl`
(raw model text + parsed object per item), `summary.json`. `bench/reports/pareto.md` is
rebuilt from every `summary.json` (quality × latency × RSS, "smallest model that passes").

## Metrics (`metrics.py`)

| metric | definition |
|---|---|
| schema_validity | output parses and validates against `extraction.schema.json` (grammar should make this 100 %; anything less is a runtime bug) |
| field_f1 | mean over scored fields: exact match for enums/ids/times, centroid within 0.5 NM for geometry, token-F1 for `location_name`, set-F1 for `entities` |
| **unsupported_fact_rate** | fraction of predicted non-null values not traceable to the source text: ids/strings must occur verbatim, times must have their day/hour/minute digits in the text, coordinates must be within 0.5 NM of a position stated (DMS or spoken numbers) in the text, `agency` must match the header letter |
| omission_rate | gold facts the model returned as null |
| geo_resolution | geometry matched, or `location_name` matched when gold has no geometry |
| latency p50/p95, peak RSS | only meaningful on the target node; hostname recorded per run |
| escalation_rate + trigger counts | how often each declarative rule in `thresholds.yaml` fires |

Backends: `llama-cli` (loads the model per item, RSS measurable, latency pessimistic),
`llama-server` (realistic latency; start it with `--grammar-file` not needed, the request
carries the grammar), `fake` (gold / null / noisy — for testing the harness itself).

The harness is not the product's validator or router: it *counts* rule hits, it does not
route anything.
