"""W4 — QLoRA fine-tune of the tier-2 model on text→JSON, then merge + GGUF Q4 (PRD §12.5).

DRY-RUN ONLY before the event: ≤200 samples, a few steps, proves the script end-to-end.
The full run is started during the hackathon (window 6–16 h) and is gated:

    uv run modal run -m modal_jobs.finetune                          # dry run (A100-40GB, minutes)
    FALOCHRON_EVENT=1 uv run modal run -m modal_jobs.finetune --full # refuses without the env var
    modal volume get falochron-artifacts models/<run_id> cache/models/

Training data: data/gold/train.jsonl (mirrored W1 output after judge) — never the gold
splits, which stay held out for the benchmark.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from modal_jobs.common import (
    REPO_ROOT,
    app,
    base_image,
    hf_secret,
    mirror_hint,
    strip_front_matter,
    vol_path,
    volume,
    with_repo,
)

# cache/models.yaml: repo id confirmed by web search only. If Qwen3.5-0.8B turns out to be a
# hybrid architecture (Gated-DeltaNet), keep the fallback and pin transformers to the version
# that supports it. Override with --base-model.
BASE_MODEL = "Qwen/Qwen3.5-0.8B"
FALLBACK_MODEL = "Qwen/Qwen3-0.6B"
DRY_LIMIT = 200
LORA_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# Order matters: llama.cpp (+ its CPU-torch convert requirements) FIRST, then the GPU stack so
# the CUDA torch wins the resolver. Pin exact versions after the first successful dry run.
ft_image = with_repo(
    base_image.apt_install("build-essential", "cmake")
    .run_commands(
        "git clone --depth 1 https://github.com/ggml-org/llama.cpp /opt/llama.cpp",
        "cmake -S /opt/llama.cpp -B /opt/llama.cpp/build -DGGML_CUDA=OFF -DLLAMA_CURL=OFF && "
        "cmake --build /opt/llama.cpp/build --target llama-quantize -j",
    )
    .pip_install("gguf", "mistral-common", "protobuf<5", "sentencepiece")
    .pip_install(
        "torch",
        "transformers>=4.51",
        "peft>=0.15",
        "trl>=0.20",
        "bitsandbytes>=0.45",
        "accelerate>=1.0",
        "datasets>=3.0",
    )
)
_train_file = REPO_ROOT / "data" / "gold" / "train.jsonl"
if _train_file.exists():
    ft_image = ft_image.add_local_file(str(_train_file), remote_path="/repo/data/gold/train.jsonl")


def build_examples(rows: list[dict], prompt_tpl: str) -> list[dict]:
    out = []
    for r in rows:
        if not r.get("expected"):
            continue
        prompt = prompt_tpl.replace("{source_text}", r["source_text"])
        out.append({"prompt": prompt, "completion": json.dumps(r["expected"], ensure_ascii=False)})
    return out


@app.function(
    image=ft_image, gpu="A100-40GB", volumes={"/vol": volume}, secrets=[hf_secret], timeout=4 * 3600
)
def train(run_id: str, full: bool, max_steps: int, base_model: str) -> str:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    tpl = strip_front_matter(Path("/repo/prompts/extract_v0.1.md").read_text(encoding="utf-8"))
    src = Path("/repo/data/gold/train.jsonl")
    rows = (
        [json.loads(ln) for ln in src.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if src.exists()
        else []
    )
    if not rows:  # dry run without W1 output yet: use the fixtures so the pipeline still runs
        rows = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(Path("/repo/schemas/fixtures").glob("*.json"))
        ]
    examples = build_examples(rows, tpl)
    if not full:
        examples = examples[:DRY_LIMIT]
    print(f"{len(examples)} training examples ({'FULL' if full else 'dry run'}); base {base_model}")

    tok = AutoTokenizer.from_pretrained(base_model)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4"
        ),
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(model)
    present = {n.split(".")[-1] for n, _ in model.named_modules()}
    targets = [t for t in LORA_TARGETS if t in present]
    print(f"LoRA targets present: {targets} (missing: {sorted(set(LORA_TARGETS) - present)})")
    lora = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM", target_modules=targets
    )
    out_dir = Path(vol_path("models", run_id))
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = SFTConfig(
        output_dir=str(out_dir / "adapter"),
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=2 if full else 1,
        max_steps=(-1 if full else max_steps),
        logging_steps=5,
        save_strategy="no",
        bf16=True,
        max_length=2048,
        completion_only_loss=True,
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tok,
        train_dataset=Dataset.from_list(examples),
        peft_config=lora,
        args=cfg,
    )
    trainer.train()
    trainer.model.save_pretrained(str(out_dir / "adapter"))
    del trainer, model
    torch.cuda.empty_cache()

    # merge into a bf16 copy of the base (merging into the bnb-4bit weights would leave packed
    # uint8 tensors that convert_hf_to_gguf.py cannot read)
    base = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.bfloat16, device_map="cpu"
    )
    merged = PeftModel.from_pretrained(base, str(out_dir / "adapter")).merge_and_unload()
    merged.save_pretrained(str(out_dir / "merged"), safe_serialization=True)
    tok.save_pretrained(str(out_dir / "merged"))

    tag = base_model.split("/")[-1].lower()
    subprocess.run(
        [
            sys.executable,
            "/opt/llama.cpp/convert_hf_to_gguf.py",
            str(out_dir / "merged"),
            "--outtype",
            "f16",
            "--outfile",
            str(out_dir / "model-f16.gguf"),
        ],
        check=True,
    )
    subprocess.run(
        [
            "/opt/llama.cpp/build/bin/llama-quantize",
            str(out_dir / "model-f16.gguf"),
            str(out_dir / f"{tag}-falochron-{run_id}-q4.gguf"),
            "Q4_K_M",
        ],
        check=True,
    )
    (out_dir / "model-f16.gguf").unlink()
    volume.commit()
    return str(out_dir)


@app.local_entrypoint()
def main(full: bool = False, max_steps: int = 30, base_model: str = BASE_MODEL):
    if full and os.environ.get("FALOCHRON_EVENT") != "1":
        raise SystemExit(
            "--full is reserved for the event window: set FALOCHRON_EVENT=1 (PRD §12.5)"
        )
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S") + ("-full" if full else "-dry")
    out = train.remote(run_id, full, max_steps, base_model)
    print(f"artifacts in {out}")
    print(f"(fallback base if the tier-2 id fails: --base-model {FALLBACK_MODEL})")
    print("mirror: " + mirror_hint(f"models/{run_id}", "cache/models/"))
