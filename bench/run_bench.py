#!/usr/bin/env python3
"""Benchmark runner: (model GGUF × prompt version × gold set) → metrics report.

Offline; reads models from cache/, gold from schemas/fixtures or data/gold/*.jsonl, PASS
thresholds from bench/thresholds.yaml. Writes bench/reports/<run-id>/{report.md,
results.csv, items.jsonl, summary.json} and refreshes bench/reports/pareto.md.

    uv run python bench/run_bench.py --backend fake                     # smoke, no model
    uv run python bench/run_bench.py --model cache/models/qwen3.5-0.8b-q4/x.gguf
    uv run python bench/run_bench.py --backend llama-server --server http://127.0.0.1:8080 \\
        --gold data/gold/pl.jsonl --tag field-hub
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import re
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bench.backends import make_backend, peak_rss_children_mb  # noqa: E402
from bench.metrics import ItemResult, evaluate_item, summarize  # noqa: E402

DEFAULT_PROMPT = REPO_ROOT / "prompts" / "extract_v0.1.md"
DEFAULT_GOLD = REPO_ROOT / "schemas" / "fixtures"
DEFAULT_SCHEMA = REPO_ROOT / "schemas" / "extraction.schema.json"
DEFAULT_GRAMMAR = REPO_ROOT / "schemas" / "extraction.gbnf"
DEFAULT_THRESHOLDS = REPO_ROOT / "bench" / "thresholds.yaml"
REPORTS = REPO_ROOT / "bench" / "reports"


def load_prompt(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        text = text[m.end() :]
    if "{source_text}" not in text:
        raise SystemExit(f"{path}: prompt must contain {{source_text}}")
    return text, meta


def load_gold(path: Path) -> list[dict]:
    if path.is_dir():
        items = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(path.glob("*.json"))]
    else:
        items = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    for it in items:
        for k in ("id", "source_text", "expected"):
            if k not in it:
                raise SystemExit(f"gold item missing {k!r}: {it}")
    return items


def parse_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(
        r"\{.*\}", text, re.S
    )  # tolerate chatter around the object (not counted valid otherwise)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def run(args: argparse.Namespace) -> dict:
    prompt_tpl, prompt_meta = load_prompt(args.prompt)
    gold = load_gold(args.gold)
    if args.limit:
        gold = gold[: args.limit]
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    grammar = args.grammar.read_text(encoding="utf-8")
    thresholds = yaml.safe_load(args.thresholds.read_text(encoding="utf-8"))
    backend = make_backend(args.backend, args.model, args.server, args.fake_mode)

    results: list[ItemResult] = []
    items_out: list[dict] = []
    for it in gold:
        prompt = prompt_tpl.replace("{source_text}", it["source_text"])
        comp = backend.complete(prompt, grammar, gold=it["expected"])
        pred = parse_json(comp.text) if not comp.error else None
        res = evaluate_item(
            it["id"],
            pred,
            it["expected"],
            it["source_text"],
            validator,
            thresholds,
            comp.latency_s,
            comp.error,
        )
        results.append(res)
        items_out.append(
            {
                "id": it["id"],
                "pred": pred,
                "raw": comp.text[:4000],
                **res.__dict__,
                "field_f1": res.field_f1,
            }
        )
        if not args.quiet:
            flag = "ok " if res.valid else "INV"
            print(
                f"[{flag}] {it['id']:<36} f1={res.field_f1:.2f} unsupported={res.unsupported} "
                f"omitted={res.omitted} {res.latency_s * 1000:.0f} ms"
            )

    peak = peak_rss_children_mb() if args.backend == "llama-cli" else None
    summary = summarize(results, thresholds, peak)
    summary.update(
        {
            "run_id": args.run_id,
            "model": str(args.model) if args.model else backend.name,
            "backend": backend.name,
            "prompt": str(args.prompt.relative_to(REPO_ROOT))
            if args.prompt.is_relative_to(REPO_ROOT)
            else str(args.prompt),
            "prompt_version": str(prompt_meta.get("prompt_version", "?")),
            "gold": str(args.gold),
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "tag": args.tag,
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "thresholds": thresholds["pass"],
        }
    )

    out = args.out or REPORTS / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (out / "items.jsonl").open("w", encoding="utf-8") as f:
        for row in items_out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_csv(out / "results.csv", results, thresholds)
    (out / "report.md").write_text(render_report(summary, results), encoding="utf-8")
    write_pareto(REPORTS)
    if not args.quiet:
        print(f"\n{'PASS' if summary['pass'] else 'FAIL'}  → {out / 'report.md'}")
    return summary


def write_csv(path: Path, results: list[ItemResult], thresholds: dict) -> None:
    fields = thresholds["scored_fields"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "id",
                "valid",
                "field_f1",
                *fields,
                "unsupported",
                "omitted",
                "geo_resolved",
                "triggers",
                "latency_s",
                "error",
            ]
        )
        for r in results:
            w.writerow(
                [
                    r.id,
                    int(r.valid),
                    f"{r.field_f1:.3f}",
                    *[f"{r.field_scores.get(x, 0.0):.2f}" for x in fields],
                    ";".join(r.unsupported),
                    ";".join(r.omitted),
                    int(r.geo_resolved),
                    ";".join(r.triggers),
                    f"{r.latency_s:.3f}",
                    r.error or "",
                ]
            )


def fmt_pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.1%}"


def render_report(s: dict, results: list[ItemResult]) -> str:
    lines = [
        f"# Benchmark run `{s['run_id']}` — {'PASS' if s['pass'] else 'FAIL'}",
        "",
        f"- model: `{s['model']}` (backend {s['backend']})",
        f"- prompt: `{s['prompt']}` v{s['prompt_version']}",
        f"- gold: `{s['gold']}` ({s['items']} items)",
        f"- host: {s['host']} — {s['platform']}" + (f" — tag `{s['tag']}`" if s["tag"] else ""),
        f"- time: {s['timestamp']}",
        "",
        "| metric | value | threshold | check |",
        "|---|---|---|---|",
    ]
    for metric, limit in s["thresholds"].items():
        value = s[metric]
        check = s["checks"][metric]
        mark = "—" if check is None else ("✅" if check else "❌")
        shown = (
            fmt_pct(value)
            if "latency" not in metric
            else (f"{value:.3f} s" if value is not None else "n/a")
        )
        lines.append(f"| {metric} | {shown} | {limit} | {mark} |")
    lines += [
        f"| omission_rate | {fmt_pct(s['omission_rate'])} | report | — |",
        f"| latency_p50_s | {s['latency_p50_s']:.3f} s | report | — |",
        f"| peak_rss_mb | {s['peak_rss_mb'] if s['peak_rss_mb'] is not None else 'n/a'} "
        "| report | — |",
        f"| escalation_rate | {fmt_pct(s['escalation_rate'])} | report | — |",
        "",
        "## Per-field F1",
        "",
        "| field | F1 |",
        "|---|---|",
        *[f"| {k} | {v:.2f} |" for k, v in s["per_field_f1"].items()],
        "",
        "## Escalation triggers (declarative rules from thresholds.yaml)",
        "",
        "| rule | items |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in s["trigger_counts"].items()],
        "",
        "## Items",
        "",
        "| id | valid | F1 | unsupported | omitted | triggers | ms |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        cells = [
            r.id,
            "✅" if r.valid else "❌",
            f"{r.field_f1:.2f}",
            ", ".join(r.unsupported) or "—",
            ", ".join(r.omitted) or "—",
            ", ".join(r.triggers) or "—",
            f"{r.latency_s * 1000:.0f}",
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def write_pareto(reports_dir: Path) -> None:
    """Table over every run's summary.json: quality × latency × RAM (PRD §13 'Pareto front')."""
    rows = []
    for p in sorted(reports_dir.glob("*/summary.json")):
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    if not rows:
        return
    lines = [
        "# Pareto table — all runs in bench/reports/",
        "",
        "Latency/RSS only comparable within the same host. "
        "Smallest model that passes wins (PRD §10.1).",
        "",
        "| run | model | prompt | gold | items | pass | field_f1 | unsupported | geo "
        "| p95 s | RSS MB | host |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sorted(rows, key=lambda r: (not r["pass"], -r["field_f1"])):
        cells = [
            s["run_id"],
            Path(s["model"]).name,
            f"v{s['prompt_version']}",
            Path(s["gold"]).name,
            str(s["items"]),
            "✅" if s["pass"] else "❌",
            f"{s['field_f1']:.2f}",
            f"{s['unsupported_fact_rate']:.1%}",
            f"{s['geo_resolution']:.0%}",
            f"{s['latency_p95_s']:.2f}",
            str(s["peak_rss_mb"]) if s["peak_rss_mb"] is not None else "—",
            s["host"],
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    (reports_dir / "pareto.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--model", type=Path, default=None, help="GGUF path (llama-cli backend)")
    ap.add_argument(
        "--backend",
        choices=("llama-cli", "llama-server", "fake"),
        default=None,
        help="default: llama-cli when --model given, else fake",
    )
    ap.add_argument("--server", default="http://127.0.0.1:8080")
    ap.add_argument("--fake-mode", choices=("gold", "null", "noisy"), default="gold")
    ap.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD, help="fixtures dir or jsonl")
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    ap.add_argument("--thresholds", type=Path, default=DEFAULT_THRESHOLDS)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.backend is None:
        args.backend = "llama-cli" if args.model else "fake"
    if args.run_id is None:
        stem = args.model.stem if args.model else f"{args.backend}-{args.fake_mode}"
        args.run_id = f"{datetime.now(UTC):%Y%m%d-%H%M%S}_{stem}"
    summary = run(args)
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
