#!/usr/bin/env python3
"""Local, offline VHF-style audio from VOICE items: espeak-ng TTS (pl/en) → channel
augmentation (modal_jobs/augment.py presets) → 8 kHz wav + transcripts.jsonl.

A stand-in for the Piper/Modal corpus (W2) that runs anywhere with ``apt install espeak-ng``:
robotic voices, but the *channel* (band-pass, noise, clipping, dropouts, squelch tail) is
the same code path, so ASR robustness tests can start before the Modal run.

    uv run python tools/synth_vhf_local.py                      # VOICE fixtures, all presets
    uv run python tools/synth_vhf_local.py --gold data/gold/pl.jsonl --presets typical,harsh
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from modal_jobs import augment  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "data" / "audio" / "vhf_synth" / "local"
VOICES = {"pl": ["pl", "pl+f3"], "en": ["en-gb", "en-us+m3"]}


def load_items(path: Path) -> list[dict]:
    if path.is_dir():
        rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(path.glob("*.json"))]
    else:
        rows = [
            json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
    return [r for r in rows if r.get("channel") == "VOICE"]


def espeak(text: str, voice: str, wpm: int = 150) -> tuple[np.ndarray, int]:
    cmd = ["espeak-ng", "-v", voice, "-s", str(wpm), "--stdout", text]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    import io

    with wave.open(io.BytesIO(raw), "rb") as w:
        rate = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return pcm.astype(np.float32) / 32768.0, rate


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
    ap.add_argument("--gold", type=Path, default=REPO_ROOT / "schemas" / "fixtures")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--presets", default="clean,typical,harsh")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    if not shutil.which("espeak-ng"):
        sys.exit("espeak-ng not found: apt install espeak-ng")
    items = load_items(args.gold)
    if args.limit:
        items = items[: args.limit]
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = args.out / "transcripts.jsonl"
    n = 0
    with manifest.open("w", encoding="utf-8") as f:
        for it in items:
            for voice in VOICES[it.get("lang", "en")]:
                x, rate = espeak(it["source_text"], voice)
                for preset in args.presets.split(","):
                    y, out_rate = augment.augment(x, rate, augment.PRESETS[preset])
                    name = f"{it['id']}_{voice.replace('+', '')}_{preset}.wav"
                    write_wav(args.out / name, out_rate, y)
                    f.write(
                        json.dumps(
                            {
                                "id": it["id"],
                                "wav": name,
                                "text": it["source_text"],
                                "lang": it.get("lang"),
                                "voice": f"espeak-ng:{voice}",
                                "preset": preset,
                                "expected": it.get("expected"),
                                "duration_s": round(len(y) / out_rate, 2),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    n += 1
    print(f"{n} files → {args.out} (manifest {manifest.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
