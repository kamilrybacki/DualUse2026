#!/usr/bin/env python3
"""Pull the MARTTS evaluation set (HF dataset bonalor/synthetic_maritime_radio_communication)
into data/martts/ and write an attribution note with the license stated on the dataset card.

Network allowed (CLAUDE.md §3, tools/fetch_*.py). Audio is git-ignored; only README lands in git.

    uv run python tools/fetch_martts.py            # snapshot into data/martts/
    uv run python tools/fetch_martts.py --dry-run  # only print card metadata + file list
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET = "bonalor/synthetic_maritime_radio_communication"
OUT = REPO_ROOT / "data" / "martts"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--dataset", default=DATASET)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError:
        sys.exit("huggingface_hub missing — run `uv sync --extra hf`")

    api = HfApi()
    info = api.dataset_info(args.dataset)
    card = info.card_data or {}
    license_ = card.get("license") if isinstance(card, dict) else getattr(card, "license", None)
    files = [s.rfilename for s in info.siblings or []]
    print(f"{args.dataset} @ {info.sha[:12]}  license={license_!r}  files={len(files)}")
    for f in files[:15]:
        print("  " + f)
    if args.dry_run:
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    local = snapshot_download(
        args.dataset, repo_type="dataset", revision=info.sha, local_dir=args.out
    )
    readme = args.out / "README.md"
    license_line = license_ or "not stated — check the card before any use beyond local evaluation"
    readme.write_text(
        "\n".join(
            [
                "# MARTTS — synthetic maritime radio communication (evaluation only)",
                "",
                f"- source: https://huggingface.co/datasets/{args.dataset}",
                f"- revision: `{info.sha}`",
                f"- license (from dataset card): **{license_line}**",
                "- use in this project: English VHF ASR evaluation (PRD Annex A.2).",
                "  Not redistributed; audio files are git-ignored, only this note is committed.",
                "- fetched with tools/fetch_martts.py",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"snapshot in {local}; attribution → {readme.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
