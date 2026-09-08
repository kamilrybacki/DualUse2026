# data/demo — scripted inputs for the 3-minute final (PRD §15, docs/demo_checklist.md)

Five inputs in the order they hit the node. Texts are committed; audio is generated into
`data/audio/sitorb/demo_*.wav` (git-ignored) with `make demo-assets`, voice clips are your
own recordings (`data/audio/vhf_own/`, git-ignored) — never third-party traffic.

| # | t | Channel | File | What the audience sees |
|---|---|---|---|---|
| 1 | 0:25 | SDR (synthetic SITOR-B, the RF-in-a-box fallback; swap for a real Kiwi recording if we have one) | `01_navtex_cable_works.txt` → `demo_01_navtex_cable_works.wav` | fldigi decodes live, event card "cable repair, Pomeranian Bay" appears on the map |
| 2 | 0:50 | TEXT (real BHMW warning, PL) | `02_bhmw_216_ais_buoys.txt` | second card, Polish source, `agency: BHMW`, two AIS buoys |
| 3 | 1:10 | VOICE (own recording, PL) | `03_vhf_report_drifting_vessel.txt` (script to read) | ASR → card with `needs_human_review`, position within 2 NM of #1 → **correlation candidate** shown with distance/time basis |
| 4 | 1:30 | — | pull the WAN cable | nothing changes |
| 5 | 1:35 | VOICE (own recording, PL) | `04_vhf_report_after_cut.txt` | processed offline; queue counter +1 |
| 6 | 1:45 | — | plug WAN back | sync to node 2; same UUIDs, no duplicates |

Fallbacks: `demo_01_..._err0.05.wav` (5 % burst FEC errors — shows abstention on a damaged
frame if the clean one feels too smooth); `01b_navtex_gale.txt` as a second SDR message.

Correlation basis for #1 × #3: cable-works polygon centre ≈ 54-38.6N 018-56.9E, vessel
report at 54-39.2N 018-58.0E → ~0.9 NM, time overlap yes, shared entity "KABEL". Threshold
in the demo: 3 NM.
