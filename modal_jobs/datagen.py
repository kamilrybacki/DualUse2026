"""W1 — synthetic text generation + LLM-as-judge on Modal (PRD §12.5).

Generates NAVTEX (EN, plus '*'-corrupted and fldigi-style garbled SDR variants), BHMW (PL)
and VHF-style (PL/EN) messages with extraction labels, few-shot from data/gold/seeds/.
A second pass judges every label; deterministic grounding (bench/metrics.py) runs first.

    uv run modal run -m modal_jobs.datagen                    # dry run: 7B model, L4, ~40 items
    uv run modal run -m modal_jobs.datagen --full             # H100, 72B AWQ, per-type=25
    modal volume get falochron-artifacts datagen/<run_id> data/gold/generated/

Labels produced here are *candidates*; only human-accepted ones become gold
(tools/gold_merge.py).
"""

from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

from modal_jobs.common import (
    app,
    base_image,
    hf_secret,
    mirror_hint,
    strip_front_matter,
    vol_path,
    volume,
    with_repo,
)

DRY_MODEL = "Qwen/Qwen2.5-7B-Instruct"
# The bf16 72B checkpoint (~145 GB) does not fit one H100; use the AWQ export.
FULL_MODEL = "Qwen/Qwen2.5-72B-Instruct-AWQ"
ITEMS_PER_PROMPT = 5  # keep each generation well under max_tokens (see review 2026-09-08)

# pin after the first successful dry run (vllm brings its own torch — do not add torch here)
gpu_image = with_repo(base_image.pip_install("vllm>=0.6.3"))


@app.function(
    image=gpu_image,
    gpu="L4",
    volumes={"/vol": volume},
    secrets=[hf_secret],
    timeout=3 * 3600,
)
def generate(
    run_id: str, model_id: str, per_type: int, kinds: list[str] | None, star_rate: float
) -> str:
    from jsonschema import Draft7Validator
    from vllm import LLM, SamplingParams

    from bench import metrics
    from modal_jobs import datagen_lib as lib

    schema = json.loads(Path("/repo/schemas/extraction.schema.json").read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    gen_tpl = strip_front_matter(Path("/repo/prompts/datagen_v0.1.md").read_text(encoding="utf-8"))
    judge_tpl = strip_front_matter(Path("/repo/prompts/judge_v0.1.md").read_text(encoding="utf-8"))
    seeds = lib.load_seeds(Path("/repo/data/gold/seeds"))
    n_prompts = max(1, math.ceil(per_type / ITEMS_PER_PROMPT))
    specs = []
    for k in range(n_prompts):
        for s in lib.build_specs(seeds, min(ITEMS_PER_PROMPT, per_type), kinds, rng_seed=k):
            specs.append(s)
    print(f"{len(seeds)} seeds, {len(specs)} prompts × ≤{ITEMS_PER_PROMPT} items, model {model_id}")

    llm_kwargs: dict = {"model": model_id, "trust_remote_code": True}
    if "AWQ" in model_id.upper():
        llm_kwargs["quantization"] = "awq"
        llm_kwargs["max_model_len"] = 16384
    else:
        llm_kwargs["max_model_len"] = 8192
    llm = LLM(**llm_kwargs)
    gen_params = SamplingParams(temperature=0.9, top_p=0.95, max_tokens=3000)
    judge_params = SamplingParams(temperature=0.0, max_tokens=800)

    prompts = [lib.render_prompt(gen_tpl, s, schema) for s in specs]
    t0 = time.time()
    outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], gen_params)
    items: list[dict] = []
    truncated = 0
    for spec, out in zip(specs, outs, strict=True):
        o = out.outputs[0]
        got = lib.parse_items(o.text, spec, validator, run_id)
        if getattr(o, "finish_reason", None) == "length":
            truncated += 1
        if not got:
            reason = getattr(o, "finish_reason", "?")
            print(f"warning: 0 valid items from {spec.id} (finish_reason={reason})")
        for it in got:
            it["generator"] = model_id
        items += got
        # SDR variants of NAVTEX items: '*' style (YaND / own decoder) and fldigi style
        if spec.kind == "navtex_en":
            items += [lib.corrupt_stars(it, star_rate, seed=i) for i, it in enumerate(got)]
            items += [lib.garble(it, star_rate, seed=i) for i, it in enumerate(got)]
    print(
        f"generated {len(items)} items in {time.time() - t0:.0f}s; truncated prompts: {truncated}"
    )

    # deterministic grounding first (cheap, no model), then the LLM judge
    tol = 0.5
    for it in items:
        it["grounding_unsupported"] = [
            f
            for f in schema["required"]
            if not metrics.value_supported(f, it["expected"].get(f), it["source_text"], tol)
        ]
    judge_prompts = [lib.judge_prompt(judge_tpl, it) for it in items]
    jouts = llm.chat([[{"role": "user", "content": p}] for p in judge_prompts], judge_params)
    for it, out in zip(items, jouts, strict=True):
        it["judge"] = {"model": model_id, **lib.parse_judge(out.outputs[0].text)}
        if it["grounding_unsupported"]:
            it["judge"]["verdict"] = "reject"
            it["judge"]["issues"].append(f"ungrounded: {', '.join(it['grounding_unsupported'])}")

    out_dir = Path(vol_path("datagen", run_id))
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "generated.jsonl").open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    stats = {
        "run_id": run_id,
        "model": model_id,
        "items": len(items),
        "accepted": sum(1 for it in items if it["judge"]["verdict"] == "accept"),
        "by_kind": {k: sum(1 for it in items if it["kind"] == k) for k in lib.KINDS},
        "truncated_prompts": truncated,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out_dir / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    volume.commit()
    return json.dumps(stats)


@app.local_entrypoint()
def main(full: bool = False, per_type: int = 0, kinds: str = "", star_rate: float = 0.03):
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S") + ("-full" if full else "-dry")
    model_id = FULL_MODEL if full else DRY_MODEL
    n = per_type or (25 if full else 2)
    kind_list = [k for k in kinds.split(",") if k] or None
    fn = generate.with_options(gpu="H100") if full else generate
    stats = fn.remote(run_id, model_id, n, kind_list, star_rate)
    print(stats)
    print("mirror: " + mirror_hint(f"datagen/{run_id}", "data/gold/generated/"))
