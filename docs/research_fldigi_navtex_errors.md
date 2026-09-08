# Research note — how fldigi's NAVTEX modem reports lost characters (2026-09-07)

**Finding:** fldigi (4.2.03) never prints `*` for undecodable SITOR-B characters. PRD F3
("znaki utracone (FEC) oznaczone `*`") does not hold with fldigi as the decoder.

## Evidence

Headless rig in a bare container (`tools/fldigi/rig_up.sh`), synthetic signal from
`tools/gen_sitorb.py`, decoded through fldigi's XML-RPC (`tools/fldigi/decode_test.py`).

1. Clean signal (fixture 01, 178 chars): decoded verbatim, one stray `.` after `KATTEGAT.`
   (135/135 characters, frame `ZCZC IA47 … NNNN` intact).
2. 10 % burst errors (fixture 02, both DX and RX copy of 33 characters destroyed):

```
ZCWC JA05
120840 UTC SEP
SWEDISH NAV WARNING 0842
SOUTHERN BALTIC.
FRQNG  EXERS  127SEP QPP UTC TO 600 U: 8, -43- 973# 9! 75(800", ?97,$3' 6
55-55.0N 01 -40.0E
55-55.08, 01&-10.0E
55-35.0N 01610.0E
55-350 015-40.0U.
(3''3)' -43 4373')3$ 59 (330 :)3-4.
BNNNA
```

Not a single `*`. Two failure modes:

- **Substitution.** On a soft failure fldigi flips the lowest-confidence bit of the DX, the RX
  or their average until a valid 4-of-7 code appears and prints *that* character
  (`src/navtex/navtex.cxx`, `process_bytes`: "FEC calculation … flip_smallest_bit"). On a
  hard failure (`-2`) it prints nothing — the character is silently dropped.
- **Shift runaway.** When the lost character is a LTRS/FIGS shift code, every following
  character until the next shift decodes in the wrong register: letters become digits and
  punctuation (`(3''3)' -43 4373')3$`). One lost byte corrupts a whole line.

## Consequences for the project

1. The `*` convention in fixtures / gold (`03_navtex_en_corrupted_stars`) describes what
   YaND-style decoders and our own generator's reference decoder produce, not fldigi. Keep
   it (it is still the right *abstention* training signal), but the data factory must also
   produce **fldigi-style damage**: wrong characters and wrong-shift runs, no `*`.
   → `modal_jobs/datagen_lib.py` needs a `garble` mode next to `corrupt_stars`.
2. The deterministic validator (F5, event) and the unsupported-fact metric already treat
   "value not traceable to the source" as failure; a garbled coordinate like `01 -40.0E`
   must yield `geometry: null`, not a guess. Add such cases to gold.
3. Decision for the event (PRD F3): keep fldigi (robust, XML-RPC, proven headless) and
   accept substitution errors, **or** write our own SITOR-B decoder that emits `*` on hard
   failure (the encoder/framing already exists in `tools/sitorb.py`; a real decoder needs
   clock recovery and AFC — realistically 3–5 h at the event). Recommendation: fldigi for
   the demo, own decoder only if the SDR window (20–28 h) has slack. The F13 "restore `*`"
   experiment only makes sense with the own decoder.
4. The `ZCWC` in the sample above (header `ZCZC` with one substituted letter) shows that
   even the frame markers are not safe: the header parser (F1/tier 0) should accept
   1-character damage in `ZCZC`/`NNNN` (Hamming distance ≤ 1).

## Reproduce

```
tools/fldigi/rig_up.sh
uv run python tools/gen_sitorb.py --fixture 02_navtex_en_exercise_polygon --error-rate 0.1 --seed 2 --out /tmp/e.wav
uv run python tools/fldigi/decode_test.py /tmp/e.wav --player "paplay --device=cable" --echo
```

## Addendum 2026-09-08 — real air

Same rig, real 518 kHz audio (WebSDR recording 2018-05-31, Netherlands Coastguard station P,
from github.com/pd0wm/navtex): all 9 messages decoded with 0.0 % CER, frames intact
(`docs/evidence/fldigi_offair_2018-05-31_518khz.txt`). So on a good signal fldigi is
flawless; the substitution behaviour above only matters on weak signals — which is exactly
what the navtex.lv live decodes in `data/gold/seeds/016–033` look like (5–18 % lost
characters, garbage runs). Those seeds are the realistic "noisy" split.
