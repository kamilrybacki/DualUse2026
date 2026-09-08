"""W3 — parallel benchmark sweep on Modal: (model × prompt × item) with ``.starmap()``.

Uses the same GGUF files and the same GBNF grammar as the edge node (llama-cpp-python on
CPU containers) and the same metrics (bench/metrics.py). Quality numbers are portable;
latency/RSS from Modal are NOT the pitch numbers (PRD §12.5) — they are recorded with
host="modal" so the Pareto table keeps them apart.

    uv run modal run -m modal_jobs.bench --models qwen3-1.7b-q4,qwen3.5-0.8b-q4 \
        --gold schemas/fixtures
"""

# no `from __future__ import annotations`: modal.parameter() needs a real type object
import fnmatch
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import modal
import yaml

from modal_jobs.common import app, base_image, hf_secret, vol_path, volume, with_repo

# prebuilt CPU wheels: no compiler needed in the image
bench_image = with_repo(
    base_image.pip_install(
        "llama-cpp-python>=0.3",
        extra_index_url="https://abetlen.github.io/llama-cpp-python/whl/cpu",
    )
)


def _entry(model_name: str) -> dict:
    models = yaml.safe_load(Path("/repo/cache/models.yaml").read_text(encoding="utf-8"))["models"]
    try:
        return next(m for m in models if m["name"] == model_name)
    except StopIteration as exc:
        raise SystemExit(f"unknown model {model_name!r} (see cache/models.yaml)") from exc


@app.function(image=bench_image, volumes={"/vol": volume}, secrets=[hf_secret], timeout=3600)
def prefetch(model_name: str) -> str:
    """Download the GGUF once into the volume (avoids N containers racing on the same file)."""
    from huggingface_hub import HfApi, hf_hub_download

    entry = _entry(model_name)
    cache_dir = Path(vol_path("models", model_name))
    cache_dir.mkdir(parents=True, exist_ok=True)
    ggufs = list(cache_dir.glob("*.gguf"))
    if ggufs:
        return str(ggufs[0])
    files = [s.rfilename for s in HfApi().model_info(entry["repo"]).siblings or []]
    matches = fnmatch.filter(files, entry["file"])
    if not matches:
        raise SystemExit(f"{entry['repo']}: no file matches {entry['file']!r}; have {files[:10]}")
    local = hf_hub_download(entry["repo"], matches[0], local_dir=cache_dir)
    volume.commit()
    return local


@app.cls(image=bench_image, volumes={"/vol": volume}, timeout=3600, cpu=4, memory=8192)
class Runner:
    """One llama.cpp model per container, loaded once; items are streamed through it."""

    model_name: str = modal.parameter()

    @modal.enter()
    def load(self) -> None:
        from llama_cpp import Llama, LlamaGrammar

        volume.reload()
        gguf = next(Path(vol_path("models", self.model_name)).glob("*.gguf"))
        self.llm = Llama(model_path=str(gguf), n_ctx=4096, verbose=False)
        self.grammar = LlamaGrammar.from_string(
            Path("/repo/schemas/extraction.gbnf").read_text(encoding="utf-8")
        )

    @modal.method()
    def run_item(self, prompt: str, item_id: str) -> dict:
        t0 = time.perf_counter()
        out = self.llm.create_completion(
            prompt, max_tokens=512, temperature=0, grammar=self.grammar
        )
        return {
            "model": self.model_name,
            "id": item_id,
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
    from bench.run_bench import load_gold, load_prompt, parse_json, write_pareto

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    items = load_gold(Path(gold))
    if limit:
        items = items[:limit]
    tpl, meta = load_prompt(Path(prompt))
    model_list = [m for m in models.split(",") if m]
    for m in model_list:
        print(f"prefetch {m}: {prefetch.remote(m)}")

    schema = json.loads(Path("schemas/extraction.schema.json").read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    thresholds = yaml.safe_load(Path("bench/thresholds.yaml").read_text(encoding="utf-8"))
    reports = Path("bench/reports")
    for m in model_list:
        runner = Runner(model_name=m)
        jobs = [(tpl.replace("{source_text}", it["source_text"]), it["id"]) for it in items]
        results = list(runner.run_item.starmap(jobs, return_exceptions=True))
        rs = []
        for it, r in zip(items, results, strict=True):
            if isinstance(r, Exception):
                rs.append(
                    evaluate_item(
                        it["id"],
                        None,
                        it["expected"],
                        it["source_text"],
                        validator,
                        thresholds,
                        0.0,
                        repr(r),
                    )
                )
                continue
            rs.append(
                evaluate_item(
                    it["id"],
                    parse_json(r["raw"]),
                    it["expected"],
                    it["source_text"],
                    validator,
                    thresholds,
                    r["latency_s"],
                )
            )
        s = summarize(rs, thresholds, None)
        rid = f"{run_id}_modal_{m}"
        s.update(
            {
                "run_id": rid,
                "model": m,
                "backend": "llama-cpp-python@modal",
                "prompt": prompt,
                "prompt_version": str(meta.get("prompt_version", "?")),
                "gold": gold,
                "host": "modal",
                "platform": "modal-cpu",
                "tag": "modal",
                "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                "thresholds": thresholds["pass"],
            }
        )
        out_dir = reports / rid
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
        with (out_dir / "raw.jsonl").open("w", encoding="utf-8") as f:
            for r in results:
                f.write(
                    json.dumps(
                        r if not isinstance(r, Exception) else {"error": repr(r)},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        print(
            f"{m:<24} pass={s['pass']} f1={s['field_f1']:.2f} "
            f"unsupported={s['unsupported_fact_rate']:.1%} → {out_dir}"
        )
    write_pareto(reports)
    print(f"pareto → {reports / 'pareto.md'}")
