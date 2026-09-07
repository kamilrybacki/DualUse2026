# FALOCHRON prep — all entry points. Everything except download/fetch/record/modal
# targets runs offline against cache/ and data/.

SHELL := /bin/bash
UV ?= uv
PY := $(UV) run python
STATION ?= HIJ
KIWI ?=
FILE ?=
TEXT ?= NAVTEX TEST MESSAGE
MODEL ?=
PROMPT ?= prompts/extract_v0.1.md
GOLD ?= schemas/fixtures
ERROR_RATE ?= 0.0

.DEFAULT_GOAL := help

.PHONY: help setup test lint status cache gbnf record decode gen-sitorb bench \
        modal-datagen modal-tts modal-bench modal-finetune-dry fetch-martts gold-merge

help: ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-20s %s\n", $$1, $$2}'

setup: ## create venv and install tool deps (uv)
	$(UV) sync
	git submodule update --init --recursive

test: ## pytest for tools/ bench/ schemas/ (offline)
	$(UV) run pytest -q

lint: ## ruff check + format check
	$(UV) run ruff check tools bench
	$(UV) run ruff format --check tools bench

status: ## show readiness checklist
	@cat STATUS.md

cache: ## download shortlisted models into cache/ (network)
	$(PY) tools/download_models.py --all

gbnf: ## regenerate schemas/extraction.gbnf from extraction.schema.json
	$(PY) tools/gen_gbnf.py

record: ## record a NAVTEX slot: make record STATION=HIJ KIWI=host1,host2 (network)
	$(PY) tools/record_navtex.py --station $(STATION) $(if $(KIWI),--kiwi $(KIWI),)

decode: ## decode a wav through fldigi (XML-RPC): make decode FILE=path.wav
	$(PY) tools/fldigi/decode_test.py $(FILE)

gen-sitorb: ## synthesize SITOR-B audio: make gen-sitorb TEXT="..." ERROR_RATE=0.02
	$(PY) tools/gen_sitorb.py --text "$(TEXT)" --error-rate $(ERROR_RATE)

bench: ## run benchmark: make bench MODEL=cache/models/x.gguf [PROMPT= GOLD=]
	$(PY) bench/run_bench.py --model $(MODEL) --prompt $(PROMPT) --gold $(GOLD)

bench-fake: ## smoke-run the benchmark harness with the fake backend (no model)
	$(PY) bench/run_bench.py --backend fake --prompt $(PROMPT) --gold $(GOLD)

modal-datagen: ## W1 synthetic text generation (Modal, network)
	$(UV) run modal run modal_jobs/datagen.py

modal-tts: ## W2 TTS + channel augmentation (Modal, network)
	$(UV) run modal run modal_jobs/tts.py

modal-bench: ## W3 parallel benchmark sweep (Modal, network)
	$(UV) run modal run modal_jobs/bench.py

modal-finetune-dry: ## W4 QLoRA dry-run, <=200 samples (Modal, network)
	$(UV) run modal run modal_jobs/finetune.py

fetch-martts: ## pull MARTTS eval set from HF into data/martts (network)
	$(PY) tools/fetch_martts.py

gold-merge: ## merge seeds + W1 output + review verdicts into data/gold/{pl,en,noisy}.jsonl
	$(PY) tools/gold_merge.py
