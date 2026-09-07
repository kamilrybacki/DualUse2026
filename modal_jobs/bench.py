"""W3 — parallel benchmark sweep on Modal: (model × prompt × item) with ``.map()``.

Uses the same GGUF files and the same GBNF grammar as the edge node (llama-cpp-python on
CPU containers), and the same metrics (bench/metrics.py). Quality numbers are portable;
latency/RSS from Modal are NOT the pitch numbers (PRD §12.5) — they are recorded with
host="modal" so the Pareto table keeps them apart.

    modal run modal_jobs/bench.py --models qwen3-1.7b-q4,qwen3.5-0.8b-q4 --gold schemas/fixtures
    modal volume get falochron-artifacts bench/<run_id> bench/reports/
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

from modal_jobs.common import app, base_image, hf_secret, mirror_hint, vol_path, volume

bench_image = base_image.pip_install("llama-cpp-python>=0.3")


@app.function(
    image=bench_image,
    volumes={"/vol": volume},
    secrets=[hf_secret],
    timeout=3600,
    cpu=4,
    memory=8192,
)
def run_item(model_name: str, prompt_path: str, item: dict) -> dict:
    """One (model, item) completion under grammar; returns raw text + latency."""
    import fnmatch

    from huggingface_hub import HfApi, hf_hub_download
    from llama_cpp import Llama, LlamaGrammar

    sys.path.insert(0, "/repo")
    models = yaml.safe_load(Path("/repo/cache/models.yaml").read_text(encoding="utf-8"))["models"]
    entry = next(m for m in models if m["name"] == model_name)
    cache_dir = Path(vol_path("models", model_name))
    cache_dir.mkdir(parents=True, exist_ok=True)
    ggufs = list(cache_dir.glob("*.gguf"))
    if not ggufs:
        files = [s.rfilename for s in HfApi().model_info(entry["repo"]).siblings or []]
        fname = fnmatch.filter(files, entry["file"])[0]
        hf_hub_download(entry["repo"], fname, local_dir=cache_dir)
        volume.commit()
        ggufs = list(cache_dir.glob("*.gguf"))
    grammar = LlamaGrammar.from_string(
        Path("/repo/schemas/extraction.gbnf").read_text(encoding="utf-8")
    )
    tpl = Path(prompt_path).read_text(encoding="utf-8")
    tpl = tpl.split("---\n", 2)[-1] if tpl.startswith("---") else tpl
    prompt = tpl.replace("{source_text}", item["source_text"])
    llm = Llama(model_path=str(ggufs[0]), n_ctx=4096, verbose=False)
    t0 = time.perf_counter()
    out = llm.create_completion(prompt, max_tokens=512, temperature=0, grammar=grammar)
    return {
        "model": model_name,
        "id": item["id"],
        "raw": out["choices"][0]["text"],
        "latency_s": time.perf_counter() - t0,
    }


@app.local_entrypoint()
def main(
    models: str = "qwen3-1.7b-q4",
    gold: str = "schemas/fixtures",
    prompt: str = "prompts/extract_v0.1.md",
    limit: int = 0,
):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from jsonschema import Draft7Validator

    from bench.metrics import evaluate_item, summarize
    from bench.run_bench import load_gold, parse_json

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    items = load_gold(Path(gold))
    if limit:
        items = items[:limit]
    model_list = [m for m in models.split(",") if m]
    jobs = [(m, f"/repo/{prompt}", it) for m in model_list for it in items]
    print(f"{len(model_list)} models × {len(items)} items = {len(jobs)} completions")
    results = list(run_item.starmap(jobs))

    schema = json.loads(Path("schemas/extraction.schema.json").read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    thresholds = yaml.safe_load(Path("bench/thresholds.yaml").read_text(encoding="utf-8"))
    by_id = {it["id"]: it for it in items}
    out_dir = Path("bench/reports") / f"{run_id}_modal"
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for m in model_list:
        rs = []
        for r in (x for x in results if x["model"] == m):
            it = by_id[r["id"]]
            pred = parse_json(r["raw"])
            rs.append(
                evaluate_item(
                    it["id"],
                    pred,
                    it["expected"],
                    it["source_text"],
                    validator,
                    thresholds,
                    r["latency_s"],
                )
            )
        s = summarize(rs, thresholds, None)
        s.update(
            {
                "run_id": f"{run_id}_modal",
                "model": m,
                "backend": "llama-cpp-python@modal",
                "prompt": prompt,
                "prompt_version": "0.1",
                "gold": gold,
                "host": "modal",
                "platform": "modal-cpu",
                "tag": "modal",
                "timestamp": datetime.now(UTC).isoformat(),
                "thresholds": thresholds["pass"],
            }
        )
        summaries.append(s)
        (out_dir / f"summary_{m}.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
        unsupported = s["unsupported_fact_rate"]
        print(f"{m:<24} pass={s['pass']} f1={s['field_f1']:.2f} unsupported={unsupported:.1%}")
    (out_dir / "raw.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n", encoding="utf-8"
    )
    print(
        f"reports → {out_dir}  (also: {mirror_hint('bench', 'bench/reports/')} for volume copies)"
    )
