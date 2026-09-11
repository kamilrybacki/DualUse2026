# Prompt dla Claude Code na maszynie z otwartą siecią

Skopiuj blok poniżej jako pierwszą wiadomość do Claude Code uruchomionego w sklonowanym
repo (`git clone --recurse-submodules … && cd DualUse2026`). Przed startem ustaw w
powłoce zmienne (nie wklejaj tokenów do promptu ani do repo):

```
export MODAL_TOKEN_ID=… MODAL_TOKEN_SECRET=… HF_TOKEN=…
```

Wymagania maszyny: Linux, `uv`, `git`, `cmake`, `sox`, `fldigi pulseaudio pulseaudio-utils xvfb`,
`espeak-ng`, `poppler-utils`; ≥60 GB dysku na `cache/`; sieć do huggingface.co, modal.com,
kiwisdr.com (+ porty 8073 odbiorników), overpass-api.de. GPU niepotrzebne (bench liczymy na CPU).

---

Read `CLAUDE.md`, `PRD_FALOCHRON_BDUH2026.md` and `STATUS.md` end-to-end before doing anything.
You are finishing the pre-hackathon preparation of FALOCHRON on a machine with open network.
The previous prep session had no network; everything below was blocked only by that.

Hard rules (non-negotiable):
- FROM SCRATCH category. Never write anything under `src/` (only `.gitkeep`), never implement
  pipeline modules F1–F12. `tools/hooks/pre-commit` enforces this; do not bypass it.
- No secrets in the repo. `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `HF_TOKEN` are already in
  the environment; use `modal secret create huggingface HF_TOKEN=$HF_TOKEN` for Modal.
- Only synthetic or own-voice VHF audio. NAVTEX recordings are fine (public MSI), keep
  station/date attribution.
- Commit small, prefixes `prep:|tools:|bench:|modal:|data:|schemas:|docs:`. Push to `main`
  only (`git push -u origin main`). Large binaries (`cache/`, `data/recordings/`, `data/audio/*.wav`)
  stay out of git per `.gitignore`; commit manifests, reports, transcripts and READMEs.
- `make lint` and `make test` must stay green before every push.
- Never claim something is cached or verified without a hash in `cache/MANIFEST.md` or a
  passing test/report file. Update `STATUS.md` after every task (done / blocked, with the
  evidence path).
- The event starts Friday 2026-09-11 at 18:00 local (16:00 UTC). Prep commits must land before
  that. If you are running after that time, everything you do counts as hackathon work: do not
  add it to the README pre-work table.

Work through the tasks in this order. Run long jobs (recordings, Modal, downloads) in the
background with `nohup … &` and logs under `logs/`, and keep working on the next task while they run.

## 0. Environment
1. `make setup && uv sync --all-extras`. Confirm `git config core.hooksPath` is `tools/hooks`.
2. Build llama.cpp for the benchmark and the grammar validator:
   `git clone --depth 1 https://github.com/ggml-org/llama.cpp cache/llama.cpp && cmake -S cache/llama.cpp -B cache/llama.cpp/build -DLLAMA_BUILD_TESTS=ON -DLLAMA_CURL=OFF && cmake --build cache/llama.cpp/build -j --target llama-cli llama-server test-gbnf-validator`.
   Then `make gbnf-check` must pass (10 fixtures valid, negatives rejected).
3. `make rig-up` and `make decode FILE=data/audio/sitorb/demo_01_navtex_cable_works.wav`
   (run `make demo-assets` first if the wav is missing). Expect `frames=JA21`, 0.0% `*`.
   See `tools/fldigi/README.md` for the PulseAudio `XDG_RUNTIME_DIR` note.

## 1. Models (P0.4)
1. `uv run python tools/download_models.py --verify` — every entry in `cache/models.yaml` must
   resolve to a real repo and file. Fix wrong ids/file globs in `cache/models.yaml` (do not guess:
   list the repo files and pick the Q4_K_M or official Q4 file).
2. `uv run python tools/download_models.py --all` then `--manifest`. Commit `cache/MANIFEST.md`
   (`data:` prefix). Also download whisper ggml small / large-v3-turbo (they are in the same list).

## 2. Benchmark on real models (P0.3)
1. `make gold-merge` → `data/gold/{pl,en,noisy}.jsonl` from the reviewed seeds (drafts stay out).
2. For every GGUF in `cache/models/`, run on CPU (this must reflect the edge node, not a GPU):
   `make bench MODEL=cache/models/<file>.gguf GOLD=schemas/fixtures` and again with
   `GOLD=data/gold/en.jsonl`, `GOLD=data/gold/pl.jsonl`, `GOLD=data/gold/noisy.jsonl`, for both
   `PROMPT=prompts/extract_v0.1.md` and `PROMPT=prompts/extract_v0.2.md`, always with
   `BENCH_ARGS="--tag <hostname>-cpu"`.
3. Never edit `bench/thresholds.yaml` (frozen 2026-09-07). Commit `bench/reports/*/summary.json`,
   `report.md`, and the regenerated `bench/reports/pareto.md` (`bench:` prefix).
4. Write `docs/bench_results.md`: the Pareto table, which tier-1/tier-2 model passes the frozen
   thresholds, latency p50/p95 and RSS per model, and 3 concrete failure examples with the raw
   model output. This is what the pitch quotes.
5. If llama-cli errors on a model (unsupported architecture etc.), record it in the doc and move
   on; do not patch llama.cpp.

## 3. NAVTEX recordings (P0.5, PRD Annex A.1)
1. `make kiwis STATION=J` and `STATION=I`, `H`, `U` (with `--snr` via `tools/fetch_kiwis.py --snr`).
   Pick 2 receivers per station with the best 518 kHz SNR; note hosts in
   `data/recordings/518khz/README.md`.
2. `uv run python tools/record_navtex.py --list` for today's slot table. Start
   `make record STATION=HIJ KIWI=host1,host2` in the background for the next HIJ block and
   `make record STATION=U KIWI=…` for the next U slot; repeat for at least two 4-hour cycles
   (≥6 clean transmissions from ≥2 stations is the target).
3. After each recording: `uv run python tools/fldigi/iq_to_audio.py <iq.wav> --out <audio.wav>`
   then `make decode FILE=<audio.wav>`. Save decoded texts to `docs/evidence/` and list every
   recording (station, UTC slot, Kiwi host, SNR, decoded frames, `*` rate) in
   `data/recordings/518khz/README.md`. Rate each as clean/marginal/unusable.
4. Real off-air texts with readable frames become new seeds via
   `uv run python tools/curate_seed.py` (station, date, receiver in the provenance fields,
   `label_status: draft`) and `data/gold/review/pending.csv`.

## 4. Modal data factory (P1.8)
Prereq: `uv run modal token set --token-id $MODAL_TOKEN_ID --token-secret $MODAL_TOKEN_SECRET`,
`uv run modal secret create huggingface HF_TOKEN=$HF_TOKEN`. Read `modal_jobs/README.md`.
Every job is run as a module: `uv run modal run -m modal_jobs.<job>`. The code was reviewed
but never executed; expect API drift in vLLM / TRL / Piper and fix it in place with `modal:`
commits. Keep each dry run inside the free credit (see the cost table in the README).
1. W1: `make modal-datagen` (dry, L4, 7B). Mirror with the printed `modal volume get …` line
   into `data/gold/generated/<run>/`. Check `stats.json`: `accepted > 0`, all kinds present,
   `truncated_prompts == 0`. Fix prompt/parse issues until it holds.
2. W2: `uv run modal run -m modal_jobs.tts --source datagen/<run>/generated.jsonl --limit 10`.
   Mirror to `data/audio/vhf_synth/<run>/`; listen-check one PL and one EN wav (`sox --i`, RMS
   not silent); commit only `transcripts.jsonl`.
3. W3: `uv run modal run -m modal_jobs.bench --models <two names from cache/models.yaml> --gold schemas/fixtures`.
   Results must be tagged `host=modal` and never quoted as edge numbers.
4. W4: `make modal-finetune-dry`. Expect `models/<run>-dry/*-q4.gguf` in the volume; mirror to
   `cache/models/` and run `make bench` on it once (fixtures) to prove the GGUF loads.
   `--full` stays forbidden (requires `FALOCHRON_EVENT=1`, event window only).
5. `uv run python tools/gold_merge.py --export-review` so the W1 candidates appear in
   `data/gold/review/pending.csv` for the human pass. Do not accept candidates yourself.

## 5. Remaining P1/P2 network items
1. `make fetch-martts` → `data/martts/` with the license note (commit the note and the small jsonl
   only if under 5 MB; otherwise commit the download script output manifest).
2. `make gazetteer` → `data/gazetteer.sqlite` (commit the cached Overpass JSON, not the sqlite if
   it is large; document the size). Verify `tools/download_gazetteer.py --lookup "Hel"` returns
   coordinates.
3. `make asr-bench ASR_MODELS=turbo` on `data/audio/vhf_synth/<W2 run>` if the runner supports a
   directory argument; otherwise run it on `local` and note it. Add the report to
   `bench/reports/` and one paragraph to `docs/research_asr_espeak.md`.
4. Offline map tiles (P2.12): download a Baltic pmtiles extract per the note in `STATUS.md` /
   PRD into `cache/tiles/` and document source, license and size in `cache/MANIFEST.md`.

## 6. Wrap-up
1. `make lint && make test`, then `make status`.
2. Update `STATUS.md` (every checkbox you closed, with the evidence path) and `README.md`
   pre-work table if a new artifact type appeared. Push to `main`.
3. Finish with a short report: what is cached (with sizes), which model passes the frozen
   thresholds, how many clean NAVTEX recordings exist, which Modal dry runs completed, and
   what is still open for the human (review CSV, own-voice recordings, hardware).
4. Prepare the USB mirror: `rsync -a cache/ data/recordings/ data/audio/ <mount>/falochron/`
   once the human tells you the mount path; until then print the command.
