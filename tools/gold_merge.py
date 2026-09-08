#!/usr/bin/env python3
"""Assemble the gold set: seeds + W1 generated items + human review verdicts →
data/gold/{pl,en,noisy}.jsonl (PRD §13 splits). Also exports/imports the review CSV.

Only items with a *human* verdict (review_status == "accepted") reach the gold files;
everything else stays in data/gold/train.jsonl for fine-tuning (decision 2026-09-07).

    uv run python tools/gold_merge.py --export-review        # → data/gold/review/pending.csv
    # ... edit verdict column: accepted | rejected | fix (and fix the label JSON if needed)
    uv run python tools/gold_merge.py --import-review data/gold/review/pending.csv
    uv run python tools/gold_merge.py                        # write splits + train
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD = REPO_ROOT / "data" / "gold"
SEEDS = GOLD / "seeds"
GENERATED = GOLD / "generated"  # W1 output mirrored from the Modal volume (*.jsonl)
REVIEW = GOLD / "review"
VERDICTS = REVIEW / "verdicts.jsonl"
SCHEMA = REPO_ROOT / "schemas" / "extraction.schema.json"

SPLITS = ("pl", "en", "noisy")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def item_from_seed(seed: dict) -> dict:
    return {
        "id": f"seed:{seed['id']}",
        "channel": seed.get("channel", "TEXT"),
        "lang": seed.get("lang", "en"),
        "source_text": seed["text"],
        "expected": seed.get("label"),
        "provenance": {
            "kind": "real",
            "source": seed.get("source"),
            "url": seed.get("url"),
            "station": seed.get("station"),
            "received_at": seed.get("received_at"),
            "sha256": seed.get("sha256"),
        },
        "noisy": (seed.get("star_rate") or 0) > 0.0,
        "label_origin": {"reviewed": "human", "draft": "draft"}.get(
            seed.get("label_status"), "none"
        ),
    }


def item_from_generated(row: dict, file: Path) -> dict:
    """W1 rows: {id, channel, lang, source_text, expected, judge: {...}, noisy?}."""
    return {
        "id": f"gen:{row['id']}",
        "channel": row.get("channel", "TEXT"),
        "lang": row.get("lang", "en"),
        "source_text": row["source_text"],
        "expected": row.get("expected"),
        "provenance": {
            "kind": "synthetic",
            "file": str(file.relative_to(REPO_ROOT))
            if file.is_relative_to(REPO_ROOT)
            else str(file),
            "generator": row.get("generator"),
            "judge": row.get("judge"),
            "seed_ids": row.get("seed_ids", []),
        },
        "noisy": bool(row.get("noisy") or "*" in row["source_text"] or row.get("asr_noise")),
        "label_origin": "llm+judge" if row.get("judge") else "llm",
    }


def collect() -> list[dict]:
    items = [
        item_from_seed(json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(SEEDS.glob("*.json"))
    ]
    for f in sorted(GENERATED.glob("*.jsonl")):
        items += [item_from_generated(r, f) for r in read_jsonl(f)]
    verdicts = {v["id"]: v for v in read_jsonl(VERDICTS)}
    for it in items:
        v = verdicts.get(it["id"])
        # a seed whose label_status is "reviewed" was labelled by hand: that is the human
        # sign-off; a verdict in verdicts.jsonl can still override it
        default = "accepted" if it["label_origin"] == "human" else "pending"
        it["review_status"] = v["verdict"] if v else default
        if v and v.get("expected"):
            it["expected"] = v["expected"]
            it["label_origin"] = "human"
        it["reviewer"] = v.get("reviewer") if v else None
    return items


def split_of(it: dict) -> str:
    if it["noisy"]:
        return "noisy"
    return "pl" if it["lang"] == "pl" else "en"


def export_review(items: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "id",
                "lang",
                "channel",
                "split",
                "label_origin",
                "source_text",
                "expected_json",
                "verdict",
                "reviewer",
                "comment",
            ]
        )
        for it in items:
            if it["review_status"] == "pending":
                w.writerow(
                    [
                        it["id"],
                        it["lang"],
                        it["channel"],
                        split_of(it),
                        it["label_origin"],
                        it["source_text"],
                        json.dumps(it["expected"], ensure_ascii=False) if it["expected"] else "",
                        "",
                        "",
                        "",
                    ]
                )


def import_review(path: Path) -> int:
    validator = Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    existing = {v["id"]: v for v in read_jsonl(VERDICTS)}
    n = 0
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verdict = (row.get("verdict") or "").strip().lower()
            if verdict not in ("accepted", "rejected", "fix"):
                continue
            expected = None
            if row.get("expected_json"):
                expected = json.loads(row["expected_json"])
                if verdict == "accepted" and not validator.is_valid(expected):
                    raise SystemExit(f"{row['id']}: accepted label does not validate")
            existing[row["id"]] = {
                "id": row["id"],
                "verdict": "accepted" if verdict == "fix" else verdict,
                "expected": expected if verdict in ("accepted", "fix") else None,
                "reviewer": row.get("reviewer") or "kamil",
                "comment": row.get("comment") or "",
            }
            n += 1
    write_jsonl(VERDICTS, list(existing.values()))
    print(f"imported {n} verdicts → {VERDICTS.relative_to(REPO_ROOT)}")
    return 0


def merge(items: list[dict]) -> dict:
    validator = Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    gold = {s: [] for s in SPLITS}
    train = []
    for it in items:
        if it["expected"] is None:
            continue
        if not validator.is_valid(it["expected"]):
            print(f"skip {it['id']}: label invalid")
            continue
        if it["review_status"] == "accepted" and it["label_origin"] == "human":
            gold[split_of(it)].append(it)
        elif it["review_status"] != "rejected":
            train.append(it)
    for s in SPLITS:
        write_jsonl(GOLD / f"{s}.jsonl", gold[s])
    write_jsonl(GOLD / "train.jsonl", train)
    return {s: len(v) for s, v in gold.items()} | {"train": len(train)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--export-review", action="store_true")
    ap.add_argument("--import-review", type=Path)
    ap.add_argument("--out", type=Path, default=REVIEW / "pending.csv")
    args = ap.parse_args(argv)

    if args.import_review:
        return import_review(args.import_review)
    items = collect()
    if args.export_review:
        export_review(items, args.out)
        pending = sum(1 for it in items if it["review_status"] == "pending")
        print(f"{pending} pending items → {args.out.relative_to(REPO_ROOT)}")
        return 0
    counts = merge(items)
    total = sum(counts[s] for s in SPLITS)
    print(f"gold: {counts} (gold total {total}, target 200–300: pl~100 en~100 noisy~50)")
    print(Counter(it["review_status"] for it in items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
