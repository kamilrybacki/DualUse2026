#!/usr/bin/env python3
"""Generate a SITOR-B / NAVTEX test signal (FSK 100 Bd, 170 Hz shift, CCIR 476 with FEC).

Test harness and demo fallback for the RF chain (PRD §10.3, §12.3) — not an input adapter.
``--error-rate`` injects fades that the decoder must print as ``*`` (burst mode kills both
the DX and the RX copy of a character).

    make gen-sitorb TEXT="ZCZC IA47 ..." ERROR_RATE=0.05
    uv run python tools/gen_sitorb.py --file msg.txt --out data/audio/sitorb/msg.wav --snr 12
    uv run python tools/gen_sitorb.py --fixture 01_navtex_en_nav_warning   # from schemas/fixtures
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.sitorb import FskParams, generate  # noqa: E402

DEFAULT_OUT_DIR = REPO_ROOT / "data" / "audio" / "sitorb"


def write_wav(path: Path, rate: int, audio: np.ndarray) -> None:
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--text", help="message text (ASCII; newlines allowed)")
    src.add_argument("--file", type=Path, help="text file")
    src.add_argument("--fixture", help="fixture id from schemas/fixtures (uses its source_text)")
    ap.add_argument("--out", type=Path, default=None, help="wav path (default data/audio/sitorb/)")
    ap.add_argument("--rate", type=int, default=8000, help="sample rate")
    ap.add_argument("--center", type=float, default=1000.0, help="audio centre of the FSK pair, Hz")
    ap.add_argument("--error-rate", type=float, default=0.0)
    ap.add_argument("--error-mode", choices=("burst", "random"), default="burst")
    ap.add_argument("--snr", type=float, default=None, help="add white noise at this SNR (dB)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--phasing", type=int, default=14, help="phasing pairs before the text")
    args = ap.parse_args(argv)

    if args.fixture:
        fx = json.loads(
            (REPO_ROOT / "schemas" / "fixtures" / f"{args.fixture}.json").read_text(
                encoding="utf-8"
            )
        )
        text = fx["source_text"]
        name = args.fixture
    elif args.file:
        text = args.file.read_text(encoding="utf-8")
        name = args.file.stem
    elif args.text:
        text = args.text
        name = "sitorb"
    else:
        text = "ZCZC IA00\nSITOR-B TEST SIGNAL 100 BD 170 HZ\nNNNN"
        name = "sitorb_test"

    params = FskParams(sample_rate=args.rate, center_hz=args.center)
    audio, meta = generate(
        text, params, args.error_rate, args.error_mode, args.snr, args.seed, args.phasing
    )
    suffix = f"_err{args.error_rate:g}" if args.error_rate else ""
    out = args.out or DEFAULT_OUT_DIR / f"{name}{suffix}.wav"
    write_wav(out, args.rate, audio)
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(
        f"wrote {out} ({meta['duration_s']} s, {meta['chars']} chars, "
        f"expected '*' rate {meta['expected_star_rate']:.3f}, killed {len(meta['killed'])})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
