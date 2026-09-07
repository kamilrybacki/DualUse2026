"""W1 — synthetic text generation + LLM-as-judge on Modal (PRD §12.5).

Generates NAVTEX (EN, plus '*'-corrupted SDR variants), BHMW (PL) and VHF-style (PL/EN)
messages with extraction labels, few-shot from data/gold/seeds/. A second pass judges
every label; deterministic grounding (bench/metrics.py) runs before the judge.

    modal run modal_jobs/datagen.py                     # dry run: small model, ~40 items, L4
    modal run modal_jobs/datagen.py --full              # H100, big open model, per-type=25
    modal volume get falochron-artifacts datagen/<run_id> data/gold/generated/

Labels produced here are *candidates*; only human-accepted ones become gold
(tools/gold_merge.py).
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from modal_jobs.common import app, base_image, hf_secret, mirror_hint, vol_path, volume

DRY_MODEL = "Qwen/Qwen2.5-7B-Instruct"
FULL_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # or openai/gpt-oss-120b; both fit 1×H100 in fp8/awq
JUDGE_MODEL = None  # None → same model as generator (cheaper); set to a different id to cross-judge

gpu_image = base_image.pip_install("vllm>=0.6.0", "torch").add_local_dir(
    str(Path(__file__).resolve().parent), remote_path="/repo/modal_jobs"
)


def _load_repo():
    sys.path.insert(0, "/repo")
    from bench import metrics  # noqa: WPS433
    from modal_jobs import datagen_lib as lib

    return metrics, lib


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
    metrics, lib = _load_repo()
    from jsonschema import Draft7Validator
    from vllm import LLM, SamplingParams

    schema = json.loads(Path("/repo/schemas/extraction.schema.json").read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    gen_tpl = Path("/repo/prompts/datagen_v0.1.md").read_text(encoding="utf-8")
    judge_tpl = Path("/repo/prompts/judge_v0.1.md").read_text(encoding="utf-8")
    seeds = lib.load_seeds(Path("/repo/data/gold/seeds"))
    specs = lib.build_specs(seeds, per_type, kinds)
    print(f"{len(seeds)} seeds, {len(specs)} specs, model {model_id}")

    llm = LLM(model=model_id, max_model_len=8192, trust_remote_code=True)
    gen_params = SamplingParams(temperature=0.9, top_p=0.95, max_tokens=3000)
    judge_params = SamplingParams(temperature=0.0, max_tokens=800)

    prompts = [lib.render_prompt(gen_tpl, s, schema) for s in specs]
    t0 = time.time()
    outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], gen_params)
    items: list[dict] = []
    for spec, out in zip(specs, outs, strict=True):
        got = lib.parse_items(out.outputs[0].text, spec, validator, run_id)
        for it in got:
            it["generator"] = model_id
        items += got
        # SDR variants of NAVTEX items: '*' style (YaND / own decoder) and fldigi style
        if spec.kind == "navtex_en":
            items += [lib.corrupt_stars(it, star_rate, seed=i) for i, it in enumerate(got)]
            items += [lib.garble(it, star_rate, seed=i) for i, it in enumerate(got)]
    print(f"generated {len(items)} items in {time.time() - t0:.0f}s")

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
        it["judge"] = {"model": JUDGE_MODEL or model_id, **lib.parse_judge(out.outputs[0].text)}
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
    if full:
        # H100 for the 72B model; the decorator's L4 is the dry-run default
        stats = generate.with_options(gpu="H100")(run_id, model_id, n, kind_list, star_rate)
    else:
        stats = generate.remote(run_id, model_id, n, kind_list, star_rate)
    print(stats)
    print("mirror: " + mirror_hint(f"datagen/{run_id}", "data/gold/generated/"))
