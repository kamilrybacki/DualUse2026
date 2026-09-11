# FALOCHRON — Overview, scenarios, reliability scoring

*Spec section, draft for spec-driven development. Facts marked **[measured]** come from the
pre-event benchmark/data work in this repo; everything else is design intent to be validated
during the 48 h.*

## 1. What we are building

A **portable, fully offline node** that runs small language models (SLMs, 0.35B–4B parameters,
Q4 GGUF on llama.cpp) on a local machine to turn what the sea *broadcasts* — NAVTEX radio,
navigational-warning text and VHF voice — into **verified, structured, geo-referenced events**,
correlates them across channels, assigns each event an explainable **reliability score**, and
publishes the picture to a local map and open interfaces (GeoJSON / CAP), with **no cloud and no
GNSS dependency**.

**For whom.** The Polish Navy and maritime services (VTS, harbour masters, coastal crisis
management) as the primary, *authorized* users, with the same node serving civilian ports and
marinas day to day (dual-use). The product addresses authorized institutions on purpose: in
Poland, disclosing the content of third-party radio correspondence is legally restricted, so the
demo and all benchmarks use only our own or synthetic VHF audio (NAVTEX and BHMW warnings are
public maritime-safety information and are unrestricted).

**Why it matters.** Baltic situational awareness leans on AIS and GNSS, and both are actively
degraded — GPS jamming/spoofing from the Kaliningrad area reaches ~450 km and the waters of seven
states. The broadcast channels keep transmitting in the clear and are independent of GNSS and of
the Internet, but today a human reads them. No commercial or open-source system fuses
NAVTEX-RF + NAVTEX-text + VHF-voice into one auditable event picture; existing players are either
state platforms (Baltic Sentry, Nordic Warden), pure AIS trackers (Shadow Fleet Tracker Light,
Saab Situation Detector, Windward) or single-channel academic prototypes.

**Positioning.** We are the layer *one step before* every existing system — an ingestion &
normalization layer that can feed GIS / TAK / COP / AIS trackers, not compete with them. The SLM
is one stage of the pipeline: it **proposes structure and never decides, publishes or classifies
intent**. Form is guaranteed by a grammar; truth comes from deterministic validators, evidence and
a human-review flag.

**Non-goals.** No hostile/suspicious-vessel classification, no autonomous actions or operational
recommendations, no full S-100/S-124 GML compliance (core field mapping only), no replacement of
VTS / TAK / CEM.

## 2. Sources (scenarios) — what the data is and how we read it

Every source ends as **plain text**; from there the same SLM extraction path applies.

| # | Source | Form of the data | How it becomes text | What we already have |
|---|---|---|---|---|
| S1 | **NAVTEX over the air, 518 kHz** (international, English) | A digital FSK radio signal: 100 Bd, 170 Hz shift, SITOR-B / CCIR 476, every character sent twice (FEC). Baltic stations transmit 10-min slots every 4 h — H Bjuröklubb 0110/0510/…, I Grimeton +10 min, J Gislövshammar +20 min, U Tallinn 0320/0720/… (UTC). | SDR (RTL-SDR V4 / Airspy HF+, or a remote KiwiSDR IQ recording) → fldigi SITOR-B demodulator via XML-RPC → text `ZCZC B1B2B3B4 … NNNN`. Characters lost to FEC come out as `*`. | Headless fldigi rig proven on three real sources **[measured]**: a 2018 off-air capture decoded at **0 % CER**, the Wikipedia sample, a sigidwiki SITOR-B recording. Our own CCIR-476 generator produces bit-exact test signals with injectable `*` error rates (the demo's "RF-in-a-box" when live reception fails). Full capture path (arm → IQ → audio → decode) exercised on a live Tallinn slot. |
| S2 | **Navigational-warning text** — BHMW (bhmw.gov.pl, Polish waters, Polish language) and NAVAREA/NAVTEX text feeds | Plain text with a stable header: `OSTRZEŻENIE NAWIGACYJNE NR nnn/26`, sea area, positions as `DD-MM.mN DDD-MM.mE`, dates `DD.MM.RRRR GODZ. HH:MM UTC`, `BHMW GDYNIA <date>`. | No decoding: a deterministic header parser (station/number, `B1B2B3B4`), then the body goes to the SLM. | 46 real attributed seed messages (BHMW 208–216 PL+EN, NL Coastguard 2018, navtex.lv live decodes) + 10 hand-labelled gold fixtures. A real prompt-injection case ("UWAGA DLA SYSTEMU: zignoruj poprzednie instrukcje…") is fixture #10 — input is treated as data. |
| S3 | **VHF voice** (156–162 MHz, ship–shore, SMCP phrasing, PL/EN) | Human speech; positions spoken in degrees and minutes ("pięćdziesiąt cztery stopnie trzydzieści dwie minuty północ…"). | VAD (Silero) → offline ASR (whisper.cpp; large-v3-turbo is the only viable size) → SMCP normalization (spoken numbers → digits, NATO alphabet → letters) → SLM. | ASR benchmark **[measured]** on an espeak proxy corpus: large-v3-turbo WER 0.37 clean / 0.49 typical channel, maritime-entity recall 0.47 / 0.29; tiny/small unusable; a harsh channel breaks everything. MARTTS eval set (480 synthetic EN VHF dialogs, cc-by-4.0) ready; whisper ggml small/medium/large-v3-turbo cached. Fields coming from ASR default to `needs_human_review` (risk R1). |
| S4 (optional, context only) | **AIS** (AISStream / MarineTraffic) | Position stream, only when WAN is up | Not extracted — used by the correlator as a fourth, *untrusted* channel for corroboration and mismatch detection (see §4). | Deliberately not on the critical path: the kill-WAN demo must not change. |

**Shared facts.** All positions parse to decimal degrees `[lon, lat]`; a Baltic bounding box
(53–66.5 N, 9–31 E) is a hard validator rule; names resolve offline through a gazetteer of
**4 333** Baltic lights, buoys, harbours, sea areas and NAVTEX stations (OSM, ODbL + curated).

## 3. Pipeline (for reference — built at the event)

```
S1 SDR → fldigi ─┐
S2 text ─────────┼→ rules/regex (tier 0) → cascade router → constrained SLM extraction (GBNF)
S3 voice → ASR ──┘        ↓                                              ↓
                   deterministic validator → geocoder → correlator + reliability scoring
                                                              ↓
                  append-only event store (SQLite, provenance) → offline map · GeoJSON · CAP · sync
```

Event schema v0.1 (S-124-aligned, frozen JSON Schema + GBNF grammar): `event_type` ∈ {NAV_WARNING,
MET_WARNING, EXERCISE, INFRA_DAMAGE, WRECK, OBSTRUCTION, VOICE_REPORT, OTHER, UNKNOWN},
`warning_id`, `issued_at / valid_from / valid_to` (UTC), `geometry` (GeoJSON Point/LineString/
Polygon), `location_name`, `agency` (`NAVTEX/518/<station>` | `BHMW` | `VHF`), `entities`
(VESSEL/MMSI/CALLSIGN/INFRA/AID_TO_NAV), `source{channel, id, raw_hash}`,
`provenance{model_id, prompt_version, schema_version, restored_chars}`,
`correlation{candidate_of, basis}`, `needs_human_review`. Every field is nullable / `UNKNOWN`;
the grammar makes 100 % syntactic validity a property of the runtime, not a request to the model.

**Model cascade [measured, 10 fixtures, lw-main CPU, prompt v0.2].** Field-F1 / unsupported-fact
rate: Ministral-3-3B 60.6 % / 12.2 %, Qwen3-4B 59.5 % / 14.8 %, Qwen3-1.7B 56.0 % / 23.3 %,
Phi-4-mini 47.9 % / 12.5 %, granite-4.0-1b 41.9 % / 23.5 %, **Qwen3.5-0.8B (target) 34.7 % /
33.3 %**; a single prompt revision roughly doubled F1 across the board (0.8B: 11.7 → 34.7 %).
Nobody yet passes the frozen thresholds (schema 100 %, F1 ≥ 0.85, unsupported-fact ≤ 2 %, geo ≥ 0.9,
p95 ≤ 2 s on the target node) — the QLoRA fine-tune on the gold set is the lever that closes the
gap. Typical failures we have to design around: invented coordinates (a longitude sign flip put a
Kattegat buoy in the Atlantic), truncated polygons, and spoken Polish positions not converted.
Twelve models (14 GB) are cached with sha256 manifests; footprint targets are 8–16 GB RAM for the
text pipeline, 32 GB with ASR + tier-3.

## 4. Reliability scoring — design proposal

**Principle.** The score is **explainable and rule-based**: every point comes from a testable rule
whose inputs are visible on the event card. The model's own "confidence" is never an input (PRD
F12 / R4). Scores rank and flag; they do not merge events or trigger actions.

**4.1 What "the same information on several channels" means.** Two events are *correlation
candidates* when all of the following hold (thresholds live in a config file, like the frozen
`bench/thresholds.yaml`, so they are testable and tunable):

- **space** — geometry centroid distance ≤ *D* nautical miles (proposal: 2 Nm for points, polygon
  intersection or centroid ≤ 5 Nm for areas), or the same resolved `location_name`;
- **time** — validity windows overlap, or `issued_at` within *T* (proposal: 6 h) for voice reports;
- **content** — same `event_type` family, or ≥ 1 shared entity (vessel name, infrastructure,
  aid-to-navigation), or a key-phrase match after normalization.

The correlator emits a **candidate** with its `basis` (distance, overlap, shared entities) and never
auto-merges (PRD G3 / R5). The demo pair: BHMW warning 214/26 "cable works, 54-30.0N 018-50.0E"
and a VHF report of an unlit drifting vessel "in the cable-works area" — 2.3 Nm apart, windows
overlap, shared entity `NEPTUN` / cable.

**4.2 Independence.** Corroboration only counts across *independent* channels. A NAVTEX message
repeated in the next 4-h slot, or the same BHMW warning re-issued, is a **repeat**, not a second
source. Channel classes: `SDR` (NAVTEX over the air), `TEXT` (BHMW/NAVAREA feed), `VOICE` (VHF),
`AIS` (context). Two events from the same class and the same `agency` never corroborate each other.

**4.3 Score components (0–1, sum of weighted, rule-derived parts; weights are a starting point).**

| component | rule (deterministic) | weight |
|---|---|---|
| **source class** | official broadcast (`SDR`, `TEXT` from NAVTEX/BHMW) 1.0 · voice report 0.5 · AIS 0.3 | 0.30 |
| **validity** | passes schema, Baltic bbox, time consistency (`valid_to ≥ valid_from`) → 1; each failed validator rule → 0 and `needs_human_review` | 0.20 |
| **grounding** | share of extracted values traceable to the raw source (our unsupported-fact check, e.g. DMS in text ↔ decimal geometry within 0.5 Nm); 1 − unsupported-fact rate | 0.20 |
| **signal quality** | SDR: 1 − (`*` rate); TEXT: header parsed → 1; VOICE: spoken position parsed and SMCP call procedure detected → 1, else 0.5 | 0.10 |
| **corroboration** | 0 for one channel; +0.5 for a second *independent* channel candidate; +0.5 for a third (cap 1) | 0.20 |

A **conflict** (independent channels disagree on position beyond *D*, on `event_type`, or an AIS
position contradicts a broadcast) does **not** average out: it sets `conflict = true`, forces
`needs_human_review`, and is shown as such — this is the anti-spoofing hook (§5). Scores decay
with `valid_to`; expired NAVTEX warnings drop out of the "current" layer but stay in the archive.

**4.4 Output contract.** Each event carries `reliability {score, basis: [rule ids that fired],
corroborated_by: [event ids], conflict}`; the map colours by score band, the card shows the rules.
Escalation to a larger model or to a human happens only on rule outcomes (schema invalid,
`event_type == UNKNOWN`, no location, geometry outside the Baltic, time inconsistent, unsupported
fact) — the same declarative rules our benchmark already counts.

## 5. Anti-spoofing — how the scoring uses independence

1. **Resilience:** inputs are GNSS-independent, so a jammed/spoofed AIS/GPS picture does not
   degrade ours.
2. **Detection by corroboration:** broadcast channels act as an independent reference; a
   broadcast-vs-AIS mismatch is a flagged anomaly for a human, not an automated verdict.
3. **Spoofed NAVTEX exists** (Irakleio Radio warned on 8 Sep 2026 about an unauthorized station
   transmitting NAVTEX): every event keeps station id, slot time, raw text and its hash, and a
   message that does not match the station's known schedule/format loses source-class points and
   is flagged.

## 6. Demo storyline (3 min)

Synthetic SITOR-B → decode → event on the map; BHMW text warning → event; Polish voice report →
event; the correlator pairs the cable-works warning with the drifting-vessel report into one
incident card with its score basis; **the WAN cable is physically pulled**; another report is
still processed; connectivity returns → store-and-forward sync to a second node; one benchmark
slide: "smallest model that passes".

## 7. What already exists (assets we build on)

- Frozen event schema + GBNF grammar, 10 gold fixtures, benchmark harness with frozen thresholds.
- 12 cached models (SLM cascade Q4 + whisper), 14 GB, sha256-manifested; llama.cpp built.
- Decoder rig (fldigi) validated on real audio; SITOR-B test-signal generator; KiwiSDR recorder.
- Data: 46 real seeds + 38 synthetic candidates (84 items awaiting human review), MARTTS eval set,
  gazetteer (4 333 names), demo input texts, 18 benchmark reports (v0.1 + v0.2).
- Cloud data factory (Modal) for synthetic generation, LLM-as-judge, TTS and QLoRA — never on
  the demo path.

## 8. Open questions for the team

1. Primary customer framing: Polish Navy only, or Navy + maritime services (dual-use) as in the
   PRD — affects pitch, legal wording and which channels we emphasize.
2. Score weights and thresholds *D*, *T* (§4) — pick, freeze in config before measuring.
3. AIS as the 4th channel: worth the 48 h, or does it blur the "broadcast channels" story?
4. Which tier is the demo model: Qwen3.5-0.8B after fine-tune (the thesis) vs Ministral-3-3B
   (best measured today) as fallback.
5. Own-voice VHF recordings (PL/EN) still to be made — needed for a credible S3 demo.
