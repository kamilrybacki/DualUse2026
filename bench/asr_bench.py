#!/usr/bin/env python3
"""ASR technology test: Whisper (via sherpa-onnx) on the synthetic VHF corpus (PRD §10.2).

Metric is not just WER: **maritime entity recall** — vessel names, call signs, and the
number words of positions must survive the channel (PRD §10.2, "recall encji morskich").
Offline; reads models from cache/asr/ and audio from data/audio/vhf_synth/<set>/.

    uv run python bench/asr_bench.py --models tiny,small,turbo --corpus data/audio/vhf_synth/local
    uv run python bench/asr_bench.py --models turbo --presets typical,harsh --lang pl

Models come from the sherpa-onnx release assets (github.com/k2-fsa/sherpa-onnx, asr-models)
— the same Whisper weights whisper.cpp uses, exported to ONNX. whisper.cpp itself can be
benchmarked with the same corpus once its ggml weights are cached (cache/models.yaml).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import socket
import time
import wave
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
ASR_DIR = REPO_ROOT / "cache" / "asr"
REPORTS = REPO_ROOT / "bench" / "reports"

NUMBER_WORDS = {
    "pl": "zero jeden jedna dwa dwie trzy cztery pięć sześć siedem osiem dziewięć dziesięć "
    "jedenaście dwanaście trzynaście czternaście piętnaście szesnaście siedemnaście osiemnaście "
    "dziewiętnaście dwadzieścia trzydzieści czterdzieści pięćdziesiąt sześćdziesiąt".split(),
    "en": "zero one two three four five six seven eight nine niner ten decimal".split(),
}


def normalize(s: str) -> list[str]:
    s = s.lower().replace("-", " ")
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    return s.split()


def wer(ref: list[str], hyp: list[str]) -> float:
    d = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=np.int32)
    d[:, 0] = np.arange(len(ref) + 1)
    d[0, :] = np.arange(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + cost)
    return float(d[len(ref), len(hyp)]) / max(1, len(ref))


def entity_terms(item: dict) -> list[str]:
    """Tokens that must be recovered: entity words (vessel/callsign/station names) and the
    number words that carry the position."""
    lang = item.get("lang", "en")
    terms: list[str] = []
    for e in (item.get("expected") or {}).get("entities", []):
        if e.get("type") == "CALLSIGN":
            continue  # spelled letters; scored via number/letter words below is unfair
        terms += normalize(e["text"])
    ref = normalize(item["text"])
    terms += [w for w in ref if w in NUMBER_WORDS.get(lang, [])]
    return terms


def entity_recall(item: dict, hyp: list[str]) -> float:
    terms = entity_terms(item)
    if not terms:
        return 1.0
    from collections import Counter

    have, want = Counter(hyp), Counter(terms)
    found = sum(min(have[t], n) for t, n in want.items())
    return found / sum(want.values())


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        if w.getnchannels() > 1:
            pcm = pcm[:: w.getnchannels()]
    return pcm.astype(np.float32) / 32768.0, rate


def load_recognizer(model: str, lang: str):
    import sherpa_onnx

    d = ASR_DIR / f"sherpa-onnx-whisper-{model}"
    enc = d / f"{model}-encoder.int8.onnx"
    dec = d / f"{model}-decoder.int8.onnx"
    if not enc.exists():
        enc, dec = d / f"{model}-encoder.onnx", d / f"{model}-decoder.onnx"
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(enc),
        decoder=str(dec),
        tokens=str(d / f"{model}-tokens.txt"),
        language=lang,
        task="transcribe",
        num_threads=4,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--models", default="tiny,small,turbo")
    ap.add_argument(
        "--corpus", type=Path, default=REPO_ROOT / "data" / "audio" / "vhf_synth" / "local"
    )
    ap.add_argument("--presets", default="")
    ap.add_argument("--lang", default="", help="only this language (pl/en)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    manifest = args.corpus / "transcripts.jsonl"
    items = [
        json.loads(ln) for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    if args.presets:
        items = [it for it in items if it.get("preset") in args.presets.split(",")]
    if args.lang:
        items = [it for it in items if it.get("lang") == args.lang]
    if args.limit:
        items = items[: args.limit]

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S") + "_asr"
    out = args.out or REPORTS / run_id
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for model in args.models.split(","):
        recognizers: dict[str, object] = {}
        for it in items:
            lang = it.get("lang", "en")
            if lang not in recognizers:
                recognizers[lang] = load_recognizer(model, lang)
            rec = recognizers[lang]
            audio, rate = read_wav(args.corpus / it["wav"])
            t0 = time.perf_counter()
            stream = rec.create_stream()
            stream.accept_waveform(rate, audio)
            rec.decode_stream(stream)
            dt = time.perf_counter() - t0
            hyp_text = stream.result.text
            ref, hyp = normalize(it["text"]), normalize(hyp_text)
            row = {
                "model": model,
                "id": it["id"],
                "lang": lang,
                "preset": it.get("preset"),
                "voice": it.get("voice"),
                "duration_s": it.get("duration_s"),
                "latency_s": round(dt, 3),
                "rtf": round(dt / max(0.1, it.get("duration_s") or 0.1), 3),
                "wer": round(wer(ref, hyp), 3),
                "entity_recall": round(entity_recall(it, hyp), 3),
                "hyp": hyp_text.strip(),
            }
            rows.append(row)
            print(
                f"[{model:<5}] {it['id'][:28]:<28} {it.get('preset'):<8} wer={row['wer']:.2f} "
                f"ent={row['entity_recall']:.2f} rtf={row['rtf']:.2f} | {hyp_text.strip()[:70]}"
            )

    with (out / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    write_report(out / "report.md", rows, run_id, args)
    print(f"\n→ {out / 'report.md'}")
    return 0


def write_report(path: Path, rows: list[dict], run_id: str, args) -> None:
    import platform

    def agg(sel: list[dict]) -> str:
        if not sel:
            return "—"
        w = np.mean([r["wer"] for r in sel])
        e = np.mean([r["entity_recall"] for r in sel])
        t = np.mean([r["rtf"] for r in sel])
        return f"WER {w:.2f} · entity recall {e:.2f} · RTF {t:.2f}"

    models = sorted(
        {r["model"] for r in rows},
        key=lambda m: (
            ["tiny", "base", "small", "medium", "turbo"].index(m)
            if m in ["tiny", "base", "small", "medium", "turbo"]
            else 99
        ),
    )
    presets = sorted(
        {r["preset"] for r in rows},
        key=lambda p: (
            ["clean", "typical", "harsh"].index(p) if p in ["clean", "typical", "harsh"] else 99
        ),
    )
    langs = sorted({r["lang"] for r in rows})
    lines = [
        f"# ASR benchmark `{run_id}`",
        "",
        f"- corpus: `{args.corpus}` ({len(rows) // max(1, len(models))} clips) — "
        "synthetic espeak-ng voices, channel presets from modal_jobs/augment.py",
        f"- engine: sherpa-onnx Whisper (int8 ONNX), CPU, host {socket.gethostname()} "
        f"({platform.platform()})",
        "- latency/RTF are for this host only; quality (WER, entity recall) is portable",
        "",
        "## Model × preset (mean over clips, both languages)",
        "",
        "| model | " + " | ".join(presets) + " |",
        "|---|" + "---|" * len(presets),
    ]
    for m in models:
        cells = [agg([r for r in rows if r["model"] == m and r["preset"] == p]) for p in presets]
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Model × language",
        "",
        "| model | " + " | ".join(langs) + " |",
        "|---|" + "---|" * len(langs),
    ]
    for m in models:
        cells = [agg([r for r in rows if r["model"] == m and r["lang"] == lg]) for lg in langs]
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Clips",
        "",
        "| model | clip | voice | preset | WER | entity recall | RTF | hypothesis |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        cells = [
            r["model"],
            r["id"],
            str(r.get("voice", "")).replace("espeak-ng:", ""),
            r["preset"],
            f"{r['wer']:.2f}",
            f"{r['entity_recall']:.2f}",
            f"{r['rtf']:.2f}",
            r["hyp"][:90],
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
