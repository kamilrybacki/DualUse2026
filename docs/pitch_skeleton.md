# FALOCHRON — 3-minute pitch skeleton (EN)

Timing per PRD §15; the Terms and Conditions cap the final presentation at **3 minutes** (a condition of being evaluated). Keep 15 s slack. Two screens: map/event list + input panel. No chat UI.

## 0:00–0:25 — Problem

- "When a crisis hits the Baltic, the cloud and GNSS are the first casualties. Spoofing from
  the Kaliningrad area reaches ~450 km and seven countries' waters."
- "Meanwhile the sea keeps *broadcasting*: NAVTEX on 518 kHz, navigational warnings as
  text, VHF voice. Today a human reads all of it."
- One line: **critical operations should degrade gracefully when the cloud — and GNSS — disappear.**

## 0:25–1:45 — Live

1. Synthetic SITOR-B signal (or the recorded 518 kHz air) → fldigi decode → event on the map.
   Say: "this is the exact signal that was on air, only the moment of reception differs."
2. BHMW text warning (PL) → event. Point at the raw source on the event card.
3. Polish VHF voice report → event. Show `needs_human_review` and the reason.
4. Correlator proposes a candidate: cable works + drifting vessel report → one incident card
   with distance/time basis. It *proposes*, it does not merge.
5. **Pull the WAN cable.** Next report still becomes an event. Nothing changed.

## 1:45–2:20 — Recovery

- Plug back in → store-and-forward sync to the second node (RPi / M720q). Same events, same
  UUIDs, no duplicates.

## 2:20–2:45 — One table

- Cascade benchmark: smallest model that passes. "0.8B passes at X ms and Y MB; 3B needed
  for N % of cases. Unsupported-fact rate Z %." (numbers from `bench/reports/pareto.md`,
  measured on the demo node, never from the cloud).
- S-124 fields, GeoJSON/CAP out — it feeds the systems you already have.

## 2:45–3:00 — Dual-use close

- Weekday: an MSI board for a marina or harbour master.
- Crisis: a situational-awareness node immune to jamming and WAN loss.
- "We don't replace TAK, VTS or CEM. We make their inputs resilient and interoperable.
  Sub-billion models, fully on-premise, trained anywhere, running everywhere."

## Backup slides / answers

- Why not just AIS? AIS is the thing being spoofed; broadcast channels are independent.
- Why SLMs? Extraction and normalization only — deterministic validators own the truth.
- Why FROM SCRATCH is honest: repo history, `event-start` tag, README pre-work list.
- Legal: NAVTEX is public MSI; VHF audio in the demo is synthetic / own voice.
