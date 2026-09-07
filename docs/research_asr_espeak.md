# Research note — Whisper sizes on the synthetic VHF channel (2026-09-07)

Run: `bench/reports/20260907-205336_asr/` (`make asr-bench`). Engine: sherpa-onnx, Whisper
int8 ONNX from the k2-fsa release assets; CPU container, 4 threads. Corpus: the two VOICE
fixtures (PL 06, EN 07) rendered by **espeak-ng** (two voices each) through the three channel
presets of `modal_jobs/augment.py` — 12 clips. RTF numbers are for this host only.

| model | clean | typical (15 dB, clip, dropouts) | harsh (6 dB, heavy clip, dropouts) |
|---|---|---|---|
| tiny | WER 1.22 · entity recall 0.00 | WER 0.99 · 0.00 | WER 0.99 · 0.00 |
| small | WER 0.79 · 0.11 | WER 0.95 · 0.01 | WER 1.06 · 0.01 |
| large-v3-turbo | **WER 0.37 · 0.47** | **WER 0.49 · 0.29** | WER 0.91 · 0.09 |

Per language (all presets): turbo EN WER 0.60 / recall 0.38, turbo PL WER 0.58 / recall 0.18.

## What this says (and what it does not)

1. **Only large-v3-turbo is a candidate.** tiny hallucinates ("[MUZYKA]", "I'm not really
   doing anything…"), small garbles names ("Talin Rabid-O", "Dynia raniotu"). This matches
   PRD §10.2's expectation that the field hub needs the big model; the pocket node's
   `small` is not enough for entity recall on this channel. RTF 0.35–0.45 on a plain CPU
   container means turbo is real-time with margin on the M720q class hardware.
2. **The "harsh" preset breaks everything.** 6 dB SNR with 0.6 clipping and 200 ms dropouts
   is beyond any Whisper size; the demo channel should be "typical". Keep harsh clips for the
   robustness slide, not the pitch numbers.
3. **Entity recall is the metric that hurts.** Even turbo on clean PL audio returns
   "Małtyk" for "Bałtyk" and drops the spoken position; on EN it keeps "Nordlin" (Nordlys)
   and the NATO letters but loses digits in typical. This is exactly why the extraction
   layer must abstain (`needs_human_review`) rather than geocode a half-heard position.
4. **espeak-ng is a pessimistic proxy.** Formant synthesis is far from human speech; Whisper
   was never trained on it. Expect materially better numbers with Piper voices (W2 on
   Modal) or own-voice recordings (PRD Annex A.2). Do not quote these WERs in the pitch;
   quote the ordering (turbo ≫ small ≫ tiny) and re-measure on the real corpus.
5. **Time-domain repetition**: turbo repeats the call-up ("dynia radio, dynia radio…")
   correctly — SMCP redundancy survives; a light SMCP normalizer (F2) can exploit that.

## Next

- Re-run with the Piper corpus (`modal_jobs/tts.py`) and, if available, own-voice clips.
- Add whisper.cpp with the same ggml weights (`cache/models.yaml`) for the latency/RSS
  numbers on the target node; quality should match sherpa-onnx within noise.
- Consider sherpa-onnx's other multilingual models (e.g. SenseVoice, Paraformer) for PL —
  the release assets are reachable where HF is not.
