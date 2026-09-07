# Picking KiwiSDR receivers for 518 kHz

Goal (PRD Annex A.1): ≥6 clean, complete transmissions from ≥2 stations, recorded from
two Kiwis in parallel, plus 2–3 weak/noisy ones for robustness tests.

## Where to look

1. Map: https://map.kiwisdr.com / http://kiwisdr.com/public — filter to the Baltic rim
   (S/SE Sweden, Denmark, N Poland, N Germany, Estonia, Finland). Distance matters less than
   local noise: 518 kHz ground-wave covers a few hundred km, so a quiet rural Kiwi 400 km
   away beats an urban one 100 km away.
2. Prefer receivers that list an **active loop or Mini-Whip** and mention LF/MF; discard
   ones with "HF only" filters or a high-pass around 1 MHz.
3. Check the receiver is free (public Kiwis have 4–8 channels; a busy one refuses you at
   slot time). Note any time limit ("tlimit") — some Kiwis cap sessions at 15–30 min, which
   is fine for a single slot (13 min) but kills an H/I/J block (33 min). Pick block-capable
   Kiwis for blocks, or record each station separately.

## Checking SNR before the slot

Do this ~10 min before the slot. In the browser UI:

- tune **518.00 kHz**, mode **CW** or **USB**, passband ~300 Hz wide around the carrier,
- look for the two FSK tones 170 Hz apart in the waterfall during a neighbouring station's
  slot (any 518 kHz station in range — the slot plan means someone is on air most of the
  hour),
- noise floor on the S-meter with no signal: S3–S5 is good, S7+ means urban QRM,
- confirm no strong broadcaster splatter from the LW/MW band.

From the command line (uses kiwirecorder's SNR estimate, no wav written):

```
python tools/vendor/kiwiclient/kiwirecorder.py -s <host> -p 8073 -f 518 -m iq \
  --snr 5 --tlimit 20 --log info
```

Higher reported SNR is better; compare 2–3 candidates and keep the best two.

## Recording

```
python tools/record_navtex.py --list                      # slot table + next slots
python tools/record_navtex.py --station HIJ --kiwi k1,k2  # waits for 19:08 CEST, records block
python tools/record_navtex.py --station U --kiwi k1       # 13 min single-station IQ
```

Files land in `data/recordings/518khz/navtex_<ID>_<YYYYmmdd_HHMM>[_<kiwi>].wav` (UTC slot
time in the name). Record the Kiwi host, antenna and subjective quality in
`data/recordings/518khz/README.md` right after each slot — it is the attribution.

## Verifying a recording

- File size sanity: IQ at 12 kHz, 16-bit stereo ≈ 48 kB/s → ~37 MB for 780 s.
- Decode it with the fldigi rig: `make decode FILE=data/recordings/518khz/<file>.wav`
  (IQ files need the USB conversion step described in `tools/fldigi/README.md`).
- A "clean" transmission = header `ZCZC <B1B2B3B4>` through `NNNN` with <2 % `*`.
