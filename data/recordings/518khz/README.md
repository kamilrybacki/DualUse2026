# 518 kHz NAVTEX recordings (not in git)

Wav files here are ignored by git (see `.gitignore`) and mirrored to the USB stick.
Keep this log up to date — it is the attribution required for the gold set (station, UTC
time, receiver).

Naming: `navtex_<STATION>_<YYYYmmdd_HHMM>[_<kiwi>].wav` — UTC slot start, per PRD Annex A.
IQ files are 518.00 kHz centre, KiwiSDR wav with GPS timestamps (`--kiwi-wav`);
USB files are 516.8 kHz carrier so the FSK tones fall in the audio band.

| File | Station | Slot UTC | Kiwi (host, antenna) | Mode | Quality (clean / weak / noisy) | Decoded `*` rate | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Quality rubric: *clean* = full `ZCZC … NNNN` with <2 % `*`; *weak* = readable with 2–10 % `*`;
*noisy* = >10 % `*` or partial (kept for robustness tests and the F13 experiment).
