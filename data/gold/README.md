# data/gold — gold set (PRD §13)

Target 200–300 items: PL ~100, EN ~100, noisy (`*`-corrupted / ASR-style) ~50, every item
with provenance and a **human-reviewed** label.

```
seeds/            real messages, one JSON each (tools/curate_seed.py) — few-shot for W1 + gold
generated/        W1 output mirrored from the Modal volume (*.jsonl), LLM labels + judge verdicts
review/           pending.csv (export), verdicts.jsonl (import) — the human pass
pl.jsonl en.jsonl noisy.jsonl   gold splits: accepted + human-labelled only
train.jsonl       everything else with a valid label (fine-tuning, never for pitch numbers)
```

Item format is the fixture format (`schemas/README.md`) plus `provenance`, `noisy`,
`label_origin` (`human | llm+judge | llm | none`) and `review_status`.

Workflow:

1. Curate ~50 real messages: `tools/curate_seed.py` (frisnit.com/navtex archive, BHMW warnings,
   own KiwiSDR decodes). Keep station + date + URL. Do not bulk-scrape (CLAUDE.md §5).
2. Run W1 on Modal (`make modal-datagen`), mirror to `generated/`.
3. `tools/gold_merge.py --export-review` → fill `verdict` (`accepted | rejected | fix`) and fix
   `expected_json` where needed → `--import-review`.
4. `make gold-merge` writes the splits. Only then run `make bench GOLD=data/gold/pl.jsonl`.

Rule: gold labels never come from a model alone. The LLM proposes, the judge filters, a human
accepts.
