# Event schema v0.1

Source: PRD §9. Two files, kept in sync (a test compares their `definitions`):

| File | Who produces it | Purpose |
|---|---|---|
| `event.schema.json` | pipeline (at the event) | full stored record: S-124 core + `source`, `provenance`, `correlation`, `needs_human_review` |
| `extraction.schema.json` | the SLM, under grammar | the subset a model may fill from the source text; every key required, unknown → `null` / `UNKNOWN` |
| `extraction.gbnf` | `make gbnf` | llama.cpp grammar generated from `extraction.schema.json` with the vendored converter |
| `fixtures/*.json` | hand-written | (source text → expected extraction) pairs used by tests and the benchmark smoke run |

## Conventions (decided 2026-09-07)

- Enums carry an explicit `UNKNOWN` member; every non-enum field is nullable. No empty
  strings as "unknown".
- Timestamps are UTC ISO-8601 with `Z`, enforced by a regex pattern (llama.cpp's converter
  does not support `format: date-time`).
- `geometry` is GeoJSON (`Point` / `LineString` / `Polygon`), `[lon, lat]` order, or `null`
  when the source only names an area.
- `entities` is a project extension (not in the PRD table) needed by the correlator's
  "common entities" rule (F7): verbatim strings tagged `VESSEL | MMSI | CALLSIGN | INFRA |
  AID_TO_NAV | OTHER`.
- `warning_id` is the NAVTEX header `B1B2B3B4` when present (e.g. `IA47`); national
  numbering stays inside `location_name`/text.
- `agency` convention: `NAVTEX/518/<station letter>`, `BHMW`, `VHF`, or `null`.

## Fixture format

```json
{
  "id": "01_navtex_en_nav_warning",
  "channel": "TEXT | SDR | VOICE",
  "lang": "en | pl",
  "source_text": "...verbatim input the model sees...",
  "expected": { ...extraction.schema.json object... },
  "notes": "why the expected values are what they are",
  "attribution": "synthetic, written for this repo" 
}
```

Fixtures are synthetic (written for this repository in the style of real broadcasts) so
they can be committed without attribution issues; real recorded messages go to
`data/gold/seeds/` with station/date attribution.

## Using the grammar with llama.cpp (on your machine)

```
llama-cli -m cache/models/<model>.gguf --grammar-file schemas/extraction.gbnf \
  -p "$(cat prompts/extract_v0.1.md) $(cat schemas/fixtures/01_navtex_en_nav_warning.json | jq -r .source_text)" \
  -n 400 --temp 0
```

llama-server accepts the same file via `"grammar"` in the request body, or the schema
directly via `"json_schema"` (it runs the same converter internally).
