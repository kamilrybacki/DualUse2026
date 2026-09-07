# Questions for mentors (PRD §14.1, §17)

## Public safety / crisis management

1. Who in a coastal crisis centre would actually consume a stream of S-124-shaped events —
   a GIS analyst, a duty officer, or an existing CEM tool? Which integration would they
   test first: GeoJSON file drop, REST, or CAP?
2. Is "candidate correlation with a reason" the right level of automation, or do operators
   expect the system to merge and let them undo?
3. Which NAVTEX message classes matter most operationally on the Polish coast (A nav
   warnings, B gale, L other, D SAR)? Should the demo show a SAR (D) message?

## Cyber

4. Prompt injection via broadcast content: we treat input as data, no tool calls, grammar-
   constrained output, validator behind the model. What attack would you try first?
5. Provenance: sha256 of raw input + model id + prompt version + schema version per event.
   Is that enough for an audit trail, or do you want signed events between nodes?
6. Store-and-forward sync between two nodes over an untrusted link — what minimum would you
   expect (mTLS? pre-shared keys? none for the demo)?

## Embedded / RF

7. 518 kHz reception indoors is hopeless; the demo replays KiwiSDR recordings through the
   same decoder path. Does the jury accept that framing, or should a live 490/518 kHz
   attempt with a loop antenna be shown anyway?
8. Pocket node choice: used ThinkCentre M720q vs RPi 5 16 GB vs Jetson Orin Nano Super for
   Whisper — which would you bring to a field trial?
9. Any experience with fldigi's NAVTEX modem on weak signals vs YaND/MultiPSK? Is the
   `*`-restoration experiment (F13) worth a slide?

## GovTech / product

10. FROM SCRATCH: pre-event data, benchmarks and configs are documented in the README. Is
    the line we drew (no pipeline code before 11.09) where you'd draw it?
11. Who pays for a device like this — harbour masters, maritime offices, the Coast Guard?
    Procurement path for a "resilience node" that is deliberately low-cost?
12. Name: FALOCHRON (Polish "breakwater") vs an EN-friendly variant for the pitch?

## Legal

13. VHF: we use only synthetic/own-voice audio. For a real deployment, which entities in
    Poland may lawfully process third-party maritime voice traffic (VTS, SAR, harbour
    captains)?
14. Redistributing decoded NAVTEX text as a dataset — any attribution/licensing constraints
    beyond station/date?
