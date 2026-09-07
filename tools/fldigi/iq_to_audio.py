#!/usr/bin/env python3
"""Convert a KiwiSDR IQ recording (518 kHz centre) to a mono audio wav for fldigi.

The IQ file is complex baseband: the NAVTEX FSK pair sits at 0 Hz ± 85 Hz. We shift it up
to ``--audio-center`` (default 1000 Hz, where fldigi's NAVTEX modem expects it), take the
real part, and write 16-bit PCM at the IQ sample rate (12 kHz for Kiwi IQ).

Handles the KiwiSDR wav layout (``kiwi`` GPS-timestamp chunks interleaved with ``data``
chunks) as well as plain 2-channel wav files. Offline, numpy only.

    uv run python tools/fldigi/iq_to_audio.py data/recordings/518khz/navtex_J_20260907_1730.wav
"""

from __future__ import annotations

import argparse
import struct
import wave
from pathlib import Path

import numpy as np


def read_iq_wav(path: Path) -> tuple[int, np.ndarray]:
    """Return (sample_rate, complex64 samples). Skips non-data chunks (e.g. 'kiwi')."""
    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError(f"{path} is not a RIFF/WAVE file")
    pos = 12
    rate: int | None = None
    channels = 0
    bits = 0
    data_parts: list[bytes] = []
    while pos + 8 <= len(raw):
        cid = raw[pos : pos + 4]
        size = struct.unpack("<I", raw[pos + 4 : pos + 8])[0]
        body = raw[pos + 8 : pos + 8 + size]
        if cid == b"fmt ":
            fmt_tag, channels, rate, _, _, bits = struct.unpack("<HHIIHH", body[:16])
            if fmt_tag != 1 or bits != 16:
                raise ValueError("expected 16-bit PCM wav")
        elif cid == b"data":
            data_parts.append(body)
        pos += 8 + size + (size & 1)
    if rate is None or channels != 2:
        raise ValueError("expected a 2-channel (I/Q) 16-bit PCM wav")
    pcm = np.frombuffer(b"".join(data_parts), dtype="<i2").astype(np.float32) / 32768.0
    iq = pcm[0::2] + 1j * pcm[1::2]
    return rate, iq.astype(np.complex64)


def iq_to_audio(iq: np.ndarray, rate: int, audio_center: float, gain: float = 0.8) -> np.ndarray:
    n = np.arange(len(iq), dtype=np.float64)
    shifted = iq * np.exp(2j * np.pi * audio_center * n / rate)
    audio = np.real(shifted)
    peak = float(np.max(np.abs(audio))) or 1.0
    return (audio / peak * gain).astype(np.float32)


def write_wav(path: Path, rate: int, audio: np.ndarray) -> None:
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("iq_wav", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="default: <name>.audio.wav")
    ap.add_argument("--audio-center", type=float, default=1000.0, help="Hz")
    args = ap.parse_args(argv)

    rate, iq = read_iq_wav(args.iq_wav)
    audio = iq_to_audio(iq, rate, args.audio_center)
    out = args.out or args.iq_wav.with_suffix(".audio.wav")
    write_wav(out, rate, audio)
    print(
        f"wrote {out}: {len(audio) / rate:.1f} s @ {rate} Hz, FSK centre {args.audio_center:g} Hz"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
