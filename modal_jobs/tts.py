"""W2 — synthetic VHF voice corpus: Piper TTS (PL/EN, several voices) + channel augmentation.

Input: VOICE items from a W1 run (or data/gold/train.jsonl) → wav at 8 kHz in
``/vol/vhf_synth/<run_id>/`` plus ``transcripts.jsonl`` {id, wav, text, lang, voice, preset}.
CPU only — Piper is fast. Alternatives if Piper's Polish voices disappoint: Coqui XTTS-v2
(GPU, cloned voices), or recording yourself (PRD Annex A.2 allows own voice).

    uv run modal run -m modal_jobs.tts --source datagen/<run_id>/generated.jsonl
    modal volume get falochron-artifacts vhf_synth/<run_id> data/audio/vhf_synth/
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import wave
from datetime import UTC, datetime
from pathlib import Path

from modal_jobs.common import app, base_image, hf_secret, mirror_hint, vol_path, volume, with_repo

VOICES = {
    "pl": ["pl_PL-gosia-medium", "pl_PL-darkman-medium"],
    "en": ["en_GB-alan-medium", "en_US-lessac-medium", "en_GB-northern_english_male-medium"],
}
VOICE_REPO = "rhasspy/piper-voices"
VOICE_DIR = vol_path("piper_voices")

tts_image = with_repo(base_image.pip_install("piper-tts>=1.3", "scipy>=1.13", "soundfile"))


def _voice_paths(voice: str) -> tuple[str, str]:
    """Piper voices live at <lang>/<locale>/<name>/<quality>/<voice>.onnx(.json) on HF."""
    locale, name, quality = voice.split("-", 2)
    base = f"{locale.split('_')[0]}/{locale}/{name}/{quality}/{voice}"
    return f"{base}.onnx", f"{base}.onnx.json"


@app.function(image=tts_image, volumes={"/vol": volume}, secrets=[hf_secret], timeout=1800)
def prefetch_voices() -> list[str]:
    """Download every voice once into the volume (containers then read it, no HF hammering)."""
    from huggingface_hub import hf_hub_download

    got = []
    for voices in VOICES.values():
        for v in voices:
            for rel in _voice_paths(v):
                hf_hub_download(VOICE_REPO, rel, local_dir=VOICE_DIR)
            got.append(v)
    volume.commit()
    return got


def _synth(text: str, onnx: Path) -> tuple[bytes, int]:
    proc = subprocess.run(
        [sys.executable, "-m", "piper", "--model", str(onnx), "--output-raw"],
        input=text.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    cfg = json.loads(Path(str(onnx) + ".json").read_text(encoding="utf-8"))
    return proc.stdout, int(cfg["audio"]["sample_rate"])


@app.function(image=tts_image, volumes={"/vol": volume}, timeout=3600, cpu=2)
def synth_item(run_id: str, item: dict, voice: str, preset: str) -> dict:
    import numpy as np

    from modal_jobs import augment

    volume.reload()
    onnx = Path(VOICE_DIR) / _voice_paths(voice)[0]
    raw, rate = _synth(item["source_text"], onnx)
    x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    y, out_rate = augment.augment(x, rate, augment.PRESETS[preset])
    pcm = np.clip(y * 32767, -32768, 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(out_rate)
        w.writeframes(pcm.tobytes())
    out_dir = Path(vol_path("vhf_synth", run_id))
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{item['id']}_{voice}_{preset}.wav"
    (out_dir / name).write_bytes(buf.getvalue())
    volume.commit()
    return {
        "id": item["id"],
        "wav": name,
        "text": item["source_text"],
        "lang": item["lang"],
        "voice": voice,
        "preset": preset,
        "expected": item.get("expected"),
        "duration_s": round(len(pcm) / out_rate, 2),
    }


@app.local_entrypoint()
def main(source: str = "", limit: int = 0, presets: str = "clean,typical,harsh"):
    """``source``: path inside the volume (datagen/<run>/generated.jsonl) or a local jsonl."""
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    if source and Path(source).exists():
        rows = [
            json.loads(ln)
            for ln in Path(source).read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    elif source:
        data = b"".join(volume.read_file(source))
        rows = [json.loads(ln) for ln in data.decode("utf-8").splitlines() if ln.strip()]
    else:
        raise SystemExit("--source required (volume path or local jsonl)")
    voice_items = [r for r in rows if r.get("channel") == "VOICE"]
    if limit:
        voice_items = voice_items[:limit]
    print("voices:", prefetch_voices.remote())
    jobs = [
        (run_id, it, voice, preset)
        for it in voice_items
        for voice in VOICES[it["lang"]]
        for preset in presets.split(",")
    ]
    print(f"{len(voice_items)} voice items × voices × presets = {len(jobs)} files")
    results = list(synth_item.starmap(jobs, return_exceptions=True))
    ok = [r for r in results if not isinstance(r, Exception)]
    failed = [repr(r) for r in results if isinstance(r, Exception)]
    manifest = "\n".join(json.dumps(r, ensure_ascii=False) for r in ok) + "\n"
    with volume.batch_upload() as batch:
        batch.put_file(
            io.BytesIO(manifest.encode("utf-8")), f"vhf_synth/{run_id}/transcripts.jsonl"
        )
    print(f"{len(ok)} files → vhf_synth/{run_id}; failed: {len(failed)}")
    for f in failed[:5]:
        print("  ", f)
    print("mirror: " + mirror_hint(f"vhf_synth/{run_id}", "data/audio/vhf_synth/"))
