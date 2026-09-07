"""W2 — synthetic VHF voice corpus: Piper TTS (PL/EN, several voices) + channel augmentation.

Input: VOICE items from a W1 run (or data/gold/train.jsonl) → wav at 8 kHz in
``/vol/vhf_synth/<run_id>/`` plus ``transcripts.jsonl`` {id, wav, text, lang, voice, preset}.
CPU only — Piper is fast; T4 not needed. Alternatives if Piper's Polish voices disappoint:
Coqui XTTS-v2 (GPU, cloned voices), or recording yourself (PRD Annex A.2 allows own voice).

    modal run modal_jobs/tts.py --source datagen/<run_id>/generated.jsonl
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

from modal_jobs.common import app, base_image, mirror_hint, vol_path, volume

VOICES = {
    "pl": ["pl_PL-gosia-medium", "pl_PL-darkman-medium"],
    "en": ["en_GB-alan-medium", "en_US-lessac-medium", "en_GB-northern_english_male-medium"],
}
VOICE_REPO = "rhasspy/piper-voices"

tts_image = base_image.pip_install("piper-tts>=1.2", "scipy>=1.13", "soundfile").add_local_dir(
    str(Path(__file__).resolve().parent), remote_path="/repo/modal_jobs"
)


def _voice_files(voice: str) -> tuple[str, str]:
    """Piper voices live at <lang>/<locale>/<name>/<quality>/<voice>.onnx(.json) on HF."""
    from huggingface_hub import hf_hub_download

    locale, name, quality = voice.split("-", 2)[0], voice.split("-")[1], voice.split("-")[-1]
    lang = locale.split("_")[0]
    base = f"{lang}/{locale}/{name}/{quality}/{voice}"
    onnx = hf_hub_download(VOICE_REPO, f"{base}.onnx")
    cfg = hf_hub_download(VOICE_REPO, f"{base}.onnx.json")
    return onnx, cfg


def _synth(text: str, onnx: str) -> tuple[bytes, int]:
    proc = subprocess.run(
        ["piper", "--model", onnx, "--output-raw"],
        input=text.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    cfg = json.loads(Path(onnx + ".json").read_text(encoding="utf-8"))
    return proc.stdout, int(cfg["audio"]["sample_rate"])


@app.function(image=tts_image, volumes={"/vol": volume}, timeout=3600, cpu=2)
def synth_item(run_id: str, item: dict, voice: str, preset: str) -> dict:
    sys.path.insert(0, "/repo")
    import numpy as np

    from modal_jobs import augment

    onnx, _ = _voice_files(voice)
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
    jobs = [
        (run_id, it, voice, preset)
        for it in voice_items
        for voice in VOICES[it["lang"]]
        for preset in presets.split(",")
    ]
    print(f"{len(voice_items)} voice items × voices × presets = {len(jobs)} files")
    results = list(synth_item.starmap(jobs))
    manifest = "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n"
    with volume.batch_upload() as batch:
        batch.put_file(
            io.BytesIO(manifest.encode("utf-8")), f"vhf_synth/{run_id}/transcripts.jsonl"
        )
    print(f"{len(results)} files → vhf_synth/{run_id}")
    print("mirror: " + mirror_hint(f"vhf_synth/{run_id}", "data/audio/vhf_synth/"))
