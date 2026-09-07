# Demo reset + fault-injection checklist (PRD §14.1, N6, R9)

Prepared before the event as a *procedure*; the reset script itself (`scripts/reset_demo.sh`)
is part of the implementation and is written after `event-start`.

## T-60 min — cold start on the demo laptop

- [ ] Power, HDMI, second screen; laptop on battery-safe profile, sleep disabled
- [ ] `git status` clean at the freeze tag; `cache/MANIFEST.md` hashes verified (`tools/download_models.py --manifest`)
- [ ] Models load: llama-server up with the demo GGUF, one warm request through the GBNF
- [ ] whisper.cpp model loads; 5-second PL sample transcribes
- [ ] fldigi rig up (`tools/fldigi/rig_up.sh`), `make decode FILE=<clean recording>` gives a full frame
- [ ] Map tiles served locally; browser cache warm; **WAN disconnected during this check**
- [ ] Second node (RPi/M720q) reachable on the LAN switch; both clocks within 2 s (no NTP on stage)
- [ ] USB stick with `cache/` + `data/` plugged into the backup laptop; backup laptop booted

## T-10 min — reset to the canonical state

- [ ] Event store emptied (or re-seeded with the scripted starting set)
- [ ] Inbox directories emptied; inputs staged: `demo/01_navtex_cable.wav`, `demo/02_bhmw.txt`, `demo/03_vhf_report.wav`, `demo/04_vhf_after_cut.wav`
- [ ] Correlator thresholds as rehearsed (distance ≤ 3 NM, time overlap on)
- [ ] Browser tabs: map/event list left, input panel right; nothing else
- [ ] Terminal font size ≥ 18 pt; notifications off

## Fault injection (rehearse each; know the recovery in < 30 s)

| # | Fault | Expected behaviour | Recovery |
|---|---|---|---|
| 1 | Pull WAN cable mid-demo (the scripted one) | next report still becomes an event; sync queue grows | none needed — this is the show |
| 2 | fldigi loses phase on the recording | no frame → no event, panel shows "no decode" | replay from the synthetic generator file |
| 3 | llama-server dies | pipeline reports extraction unavailable, nothing invented | `systemctl restart` / `make serve`; events resume |
| 4 | ASR garbles the position | `needs_human_review` = true, geometry null, reason shown | show the card — that is the point |
| 5 | Second node offline at reconnect | sync retries with backoff, no duplicates on late join | boot node; show UUID dedup |
| 6 | Prompt-injection line in a text warning ("ignore previous …") | copied as text, no field changes, flagged by validator | show raw source on the card |
| 7 | Clock skew between nodes | events keep source timestamps; sync order by UUID | none |
| 8 | Projector loses HDMI | — | backup laptop already mirrored |

## After the run

- [ ] Export GeoJSON + CAP of the session to USB (jury hand-off)
- [ ] `git tag demo-freeze` if not yet done; push
