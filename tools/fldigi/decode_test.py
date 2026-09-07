#!/usr/bin/env python3
"""One-shot SITOR-B/NAVTEX decode test: wav → virtual cable → fldigi → XML-RPC → text file.

This is a technology test for the decoder, not the F3 input adapter (CLAUDE.md §1).

Requires a running fldigi with its XML-RPC server enabled (see tools/fldigi/README.md)
and a virtual audio cable whose playback side is ``--player``'s output and whose capture
side is fldigi's input.

Example::

    uv run python tools/fldigi/decode_test.py data/recordings/518khz/navtex_J_20260907_1730.wav \\
        --carrier 1200 --player "aplay -D hw:Loopback,0,0"
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
import wave
import xmlrpc.client
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PLAYER = "aplay -D hw:Loopback,0,0"
FRAME_RE = re.compile(r"ZCZC\s+([A-Z]{2}\d{2})(.*?)NNNN", re.S)


@dataclass
class DecodeStats:
    chars: int
    star_rate: float
    frames: list[str]

    def summary(self) -> str:
        frames = ", ".join(self.frames) if self.frames else "none"
        return f"chars={self.chars} star_rate={self.star_rate:.3%} frames={frames}"


def stats_for(text: str) -> DecodeStats:
    body = "".join(ch for ch in text if not ch.isspace())
    stars = body.count("*")
    frames = [m.group(1) for m in FRAME_RE.finditer(text)]
    return DecodeStats(len(body), stars / len(body) if body else 0.0, frames)


def wav_duration(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / w.getframerate()
    except (wave.Error, EOFError):
        return None


class Fldigi:
    """Thin wrapper over the fldigi XML-RPC surface used here."""

    def __init__(self, host: str, port: int):
        self.rpc = xmlrpc.client.ServerProxy(f"http://{host}:{port}", allow_none=True)

    def version(self) -> str:
        return str(self.rpc.fldigi.version())

    def setup(self, modem: str, carrier: int) -> None:
        self.rpc.modem.set_by_name(modem)
        self.rpc.modem.set_carrier(carrier)
        self.rpc.main.set_afc(True)
        self.rpc.main.set_squelch(False)
        self.rpc.main.set_rsid(False)
        self.rpc.text.clear_rx()

    def rx_length(self) -> int:
        return int(self.rpc.text.get_rx_length())

    def rx_text(self, start: int, end: int) -> str:
        data = self.rpc.text.get_rx(start, end)
        raw = data.data if isinstance(data, xmlrpc.client.Binary) else data
        return raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)


def run(args: argparse.Namespace) -> int:
    wav = args.wav
    if not wav.exists():
        print(f"error: {wav} not found", file=sys.stderr)
        return 2
    duration = wav_duration(wav)

    fl = Fldigi(args.host, args.port)
    try:
        ver = fl.version()
    except OSError as exc:
        print(
            f"error: cannot reach fldigi XML-RPC at {args.host}:{args.port}: {exc}", file=sys.stderr
        )
        return 2
    print(f"fldigi {ver}; modem={args.modem} carrier={args.carrier} Hz")
    fl.setup(args.modem, args.carrier)

    cmd = shlex.split(args.player) + [str(wav)]
    print("player: " + " ".join(cmd))
    proc = subprocess.Popen(cmd)

    deadline = time.monotonic() + (duration or args.timeout) + args.tail
    player_done_at: float | None = None
    pos = 0
    chunks: list[str] = []
    try:
        while time.monotonic() < deadline:
            n = fl.rx_length()
            if n > pos:
                chunk = fl.rx_text(pos, n)
                chunks.append(chunk)
                pos = n
                if args.echo:
                    print(chunk, end="", flush=True)
            if player_done_at is None and proc.poll() is not None:
                player_done_at = time.monotonic()  # keep polling through the tail only
            if player_done_at is not None and time.monotonic() > player_done_at + args.tail:
                break
            time.sleep(args.poll)
    finally:
        if proc.poll() is None:
            proc.terminate()

    text = "".join(chunks)
    out = args.out or wav.with_suffix(".decoded.txt")
    out.write_text(text, encoding="utf-8")
    st = stats_for(text)
    print(f"wrote {out}: {st.summary()}")
    return 0 if st.chars else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("wav", type=Path, help="audio file to play (8–48 kHz mono/stereo wav)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7362)
    ap.add_argument("--modem", default="NAVTEX", choices=("NAVTEX", "SITORB"))
    ap.add_argument("--carrier", type=int, default=1000, help="audio centre of the FSK pair, Hz")
    ap.add_argument(
        "--player", default=DEFAULT_PLAYER, help="command that plays a wav to the cable"
    )
    ap.add_argument("--out", type=Path, default=None, help="output text file")
    ap.add_argument(
        "--tail", type=float, default=4.0, help="seconds to keep polling after playback"
    )
    ap.add_argument("--poll", type=float, default=0.5)
    ap.add_argument("--timeout", type=float, default=900.0, help="max seconds if duration unknown")
    ap.add_argument("--echo", action="store_true", help="print decoded text as it arrives")
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
