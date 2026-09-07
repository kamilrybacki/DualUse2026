#!/usr/bin/env python3
"""Curation helper for real NAVTEX / BHMW seed messages (data/gold/seeds/).

Not a scraper: you paste one message at a time (file, stdin or --text) with its provenance,
the tool normalizes it and writes one JSON file per message. The LLM data factory (W1)
uses these as few-shot examples; the ones you label by hand become gold.

    uv run python tools/curate_seed.py --source frisnit --station I \\
        --received 2026-09-07T13:20Z --url "https://www.frisnit.com/navtex/..." --file msg.txt
    cat msg.txt | uv run python tools/curate_seed.py --source own-kiwi --station J \\
        --received 2026-09-07T17:30Z
    uv run python tools/curate_seed.py --source bhmw --lang pl \\
        --url "https://bhmw.gov.pl/..." --file ow_214.txt
    uv run python tools/curate_seed.py --list
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEEDS = REPO_ROOT / "data" / "gold" / "seeds"
SOURCES = ("frisnit", "own-kiwi", "own-rtlsdr", "bhmw", "navarea", "other")
HEADER_RE = re.compile(r"ZCZC\s+([A-Z])([A-Z])(\d{2})")


def normalize_text(text: str) -> str:
    """CRLF → LF, strip trailing spaces, collapse 3+ blank lines, keep case and '*'."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    out = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", out) + "\n"


def parse_header(text: str) -> dict | None:
    m = HEADER_RE.search(text)
    if not m:
        return None
    return {"b1_station": m.group(1), "b2_subject": m.group(2), "b3b4_number": m.group(3)}


def next_id() -> int:
    nums = [int(p.name[:3]) for p in SEEDS.glob("[0-9][0-9][0-9]_*.json")]
    return (max(nums) + 1) if nums else 1


def build_seed(
    text: str,
    source: str,
    station: str | None,
    received: str | None,
    url: str | None,
    lang: str,
    channel: str,
    curator: str,
    note: str,
) -> dict:
    norm = normalize_text(text)
    header = parse_header(norm)
    if station is None and header:
        station = header["b1_station"]
    return {
        "id": None,  # filled on write
        "source": source,
        "url": url,
        "station": station,
        "received_at": received,
        "lang": lang,
        "channel": channel,
        "navtex_header": header,
        "text": norm,
        "sha256": hashlib.sha256(norm.encode("utf-8")).hexdigest(),
        "star_rate": round(norm.count("*") / max(1, len(norm.replace("\n", ""))), 4),
        "curated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "curator": curator,
        "note": note,
        "license_note": (
            "NAVTEX/MSI is public maritime safety information; kept with station and "
            "date attribution. Not for redistribution as a dataset outside this project."
        ),
        "label": None,  # filled by human review (extraction.schema.json object)
        "label_status": "unlabeled",  # unlabeled | draft | reviewed
    }


def write_seed(seed: dict) -> Path:
    SEEDS.mkdir(parents=True, exist_ok=True)
    for p in SEEDS.glob("*.json"):
        if json.loads(p.read_text(encoding="utf-8")).get("sha256") == seed["sha256"]:
            raise SystemExit(f"duplicate: identical text already curated as {p.name}")
    n = next_id()
    station = seed["station"] or "X"
    day = (seed["received_at"] or "undated")[:10].replace("-", "")
    seed["id"] = f"{n:03d}_{station}_{day}"
    path = SEEDS / f"{seed['id']}.json"
    path.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def list_seeds() -> int:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(SEEDS.glob("*.json"))]
    if not rows:
        print("no seeds yet")
        return 0
    print(f"{'id':<22}{'src':<10}{'st':<3}{'lang':<5}{'stars':<7}{'label':<10}first line")
    for s in rows:
        first = s["text"].strip().splitlines()[0][:50]
        print(
            f"{s['id']:<22}{s['source']:<10}{(s['station'] or '-'):<3}{s['lang']:<5}"
            f"{s['star_rate']:<7.3f}{s['label_status']:<10}{first}"
        )
    by_station: dict[str, int] = {}
    for s in rows:
        by_station[s["station"] or "-"] = by_station.get(s["station"] or "-", 0) + 1
    print(f"\n{len(rows)} seeds; by station: {by_station}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--station", help="NAVTEX B1 letter; inferred from ZCZC header if absent")
    ap.add_argument("--received", help="UTC time the message was broadcast/received, ISO 8601")
    ap.add_argument("--url", help="where the text came from (archive page, or 'own recording')")
    ap.add_argument("--lang", choices=("en", "pl"), default="en")
    ap.add_argument("--channel", choices=("TEXT", "SDR"), default="TEXT")
    ap.add_argument("--curator", default="kamil")
    ap.add_argument("--note", default="")
    ap.add_argument("--file", type=Path, help="text file with one message (default: stdin)")
    ap.add_argument("--text", help="message text inline")
    args = ap.parse_args(argv)

    if args.list:
        return list_seeds()
    if not args.source:
        ap.error("--source is required (or --list)")
    if args.text:
        text = args.text
    elif args.file:
        text = args.file.read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    if not text.strip():
        ap.error("empty message")
    seed = build_seed(
        text,
        args.source,
        args.station,
        args.received,
        args.url,
        args.lang,
        args.channel,
        args.curator,
        args.note,
    )
    path = write_seed(seed)
    print(
        f"wrote {path.relative_to(REPO_ROOT)} (station {seed['station']}, "
        f"star_rate {seed['star_rate']:.3f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
