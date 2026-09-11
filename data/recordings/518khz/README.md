# 518 kHz NAVTEX recordings (not in git)

Wav files here are ignored by git (see `.gitignore`) and mirrored to the USB stick.
Keep this log up to date — it is the attribution required for the gold set (station, UTC
time, receiver).

Naming: `navtex_<STATION>_<YYYYmmdd_HHMM>[_<kiwi>].wav` — UTC slot start, per PRD Annex A.
IQ files are 518.00 kHz centre, KiwiSDR wav with GPS timestamps (`--kiwi-wav`);
USB files are 516.8 kHz carrier so the FSK tones fall in the audio band.

| File | Station | Slot UTC | Kiwi (host, antenna) | Mode | Quality (clean / weak / noisy) | Decoded `*` rate | Notes |
|---|---|---|---|---|---|---|---|
| `navtex_U_20260911_1520_oh3aa_1.wav` | U (Tallinn) | 2026-09-11 15:20Z | oh3aa.dy.fi:18073 (Hämeenlinna FI, 60.95 N 24.48 E) | IQ (KiwiSDR wav) | unusable | frames=none | RSSI ~-80 dBm; full slot captured but **no decodable NAVTEX** — signal too weak/absent at this receiver (Tallinn→central Finland). IQ+audio kept for re-decode with carrier/reverse tuning. sk5sm.proxy.kiwisdr.com leg dropped mid-capture (server closed connection), so only the oh3aa capture exists. |

> Note (2026-09-11): this was the only reachable 518 kHz slot before the event — kiwisdr.com/public
> was down/anti-bot-gated most of the afternoon. The capture path (arm → IQ → `iq_to_audio.py` →
> fldigi) is proven end-to-end; this slot simply carried no decodable transmission at the available
> receiver. Real decodable evidence stays in `docs/evidence/` (2018 off-air @0 % CER, sigidwiki sample).

Quality rubric: *clean* = full `ZCZC … NNNN` with <2 % `*`; *weak* = readable with 2–10 % `*`;
*noisy* = >10 % `*` or partial (kept for robustness tests and the F13 experiment).
