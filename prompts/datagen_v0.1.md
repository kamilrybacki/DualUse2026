---
prompt_version: "0.1"
purpose: W1 generator (modal_jobs/datagen.py)
---
You write realistic synthetic maritime broadcast messages for the Baltic Sea and label them.

Task: produce {n} distinct messages of kind `{kind}` ({style}), language `{lang}`, channel
`{channel}`, event type `{event_type}`. Then label each one EXACTLY as a careful operator
would, using only facts present in the message.

Style rules by kind:
- navtex_en: NAVTEX 518 kHz format. The FIRST line is exactly `ZCZC B1B2B3B4` — a 4-character
  code, nothing else on that line: B1 ∈ {H, I, J, U}; B2 = A navigational / B gale / E weather /
  L other; B3B4 = a two-digit serial (e.g. `ZCZC HA47`, `ZCZC JB13`). NEVER merge the time into
  the header. On the NEXT line put the day-time group `DDHHMM UTC MON` (e.g. `071230 UTC SEP`).
  Then national warning number, sea area, body in upper case, coordinates as `DD-MM.mN DDD-MM.mE`,
  end with `NNNN`. Baltic places only. `agency` must be `NAVTEX/518/<B1>` with the SAME B1 letter
  as the header; `warning_id` is exactly the 4-char `B1B2B3B4` (not the time); `issued_at` comes
  from the day-time group (day=DD, HH:MM UTC, month=MON, year 2026).
- bhmw_pl: Polish "OSTRZEŻENIE NAWIGACYJNE NR nnn/26", akwen, treść wielkimi literami,
  pozycje `DD-MM.mN DDD-MM.mE`, daty `DD.MM.RRRR GODZ. HH:MM UTC`, koniec `BHMW GDYNIA data`.
- vhf_pl / vhf_en: an ASR transcript of a spoken VHF exchange (SMCP): lowercase, no
  punctuation, numbers spelled out as words, call procedure (station names repeated),
  "over"/"odbiór". Positions spoken in degrees and minutes.

Labelling rules (schema below is enforced):
- Copy values verbatim from the message. Anything not stated → null; never guess.
- Times UTC `YYYY-MM-DDTHH:MM:SSZ`, year 2026. Coordinates → decimal degrees `[lon, lat]`.
- `warning_id`: the NAVTEX B1B2B3B4 or the BHMW number; VHF → null.
- `agency`: `NAVTEX/518/<B1>`, `BHMW`, or `VHF`.
- `entities`: vessel names, MMSI, call signs (letters), infrastructure, aids to navigation —
  verbatim strings from the message.
- Do not add fields. Do not explain.

Examples of real messages of this kind (style reference only; do not copy them):
{few_shot}

Output one JSON object: {"items": [{"source_text": "...", "expected": {...}}, ...]}
where `expected` follows this JSON schema:
{schema}
