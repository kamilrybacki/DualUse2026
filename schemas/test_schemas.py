"""Schema v0.1 consistency tests: fixtures validate, both schemas share definitions,
and the committed GBNF matches the schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.gen_gbnf import schema_to_gbnf  # noqa: E402

SCHEMAS = ROOT / "schemas"
EVENT = json.loads((SCHEMAS / "event.schema.json").read_text(encoding="utf-8"))
EXTRACTION = json.loads((SCHEMAS / "extraction.schema.json").read_text(encoding="utf-8"))
FIXTURES = sorted((SCHEMAS / "fixtures").glob("*.json"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_schemas_are_valid_draft7() -> None:
    Draft7Validator.check_schema(EVENT)
    Draft7Validator.check_schema(EXTRACTION)


def test_definitions_in_sync() -> None:
    assert EVENT["definitions"] == EXTRACTION["definitions"]


def test_extraction_is_subset_of_event() -> None:
    for key, prop in EXTRACTION["properties"].items():
        assert EVENT["properties"][key] == prop, key
    assert set(EXTRACTION["required"]) == set(EXTRACTION["properties"])


def test_event_type_enum_matches_prd() -> None:
    prd = [
        "NAV_WARNING",
        "MET_WARNING",
        "EXERCISE",
        "INFRA_DAMAGE",
        "WRECK",
        "OBSTRUCTION",
        "VOICE_REPORT",
        "OTHER",
    ]
    assert EVENT["definitions"]["event_type"]["enum"] == prd + ["UNKNOWN"]


def test_prd_example_event_validates() -> None:
    """PRD §9 example, completed with the fields the schema requires."""
    example = {
        "schema_version": "0.1",
        "event_type": "EXERCISE",
        "warning_id": "SE-A-0842",
        "issued_at": "2026-09-12T08:40:00Z",
        "valid_from": "2026-09-12T10:00:00Z",
        "valid_to": "2026-09-12T16:00:00Z",
        "geometry": {"type": "Point", "coordinates": [18.95, 55.21]},
        "location_name": "AREA SOUTH OF UTKLIPPAN",
        "agency": "NAVTEX/518",
        "entities": [],
        "source": {"channel": "SDR", "id": "rtlsdr-01", "raw_hash": "sha256:" + "0" * 64},
        "provenance": {
            "model_id": "qwen3.5-0.8b-q4",
            "prompt_version": "0.3",
            "schema_version": "0.1",
            "restored_chars": [],
        },
        "correlation": {"candidate_of": [], "basis": None},
        "needs_human_review": False,
    }
    Draft7Validator(EVENT).validate(example)


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_fixture_expected_validates(path: Path) -> None:
    fx = load(path)
    for key in ("id", "channel", "lang", "source_text", "expected", "notes", "attribution"):
        assert key in fx, f"{path.name} missing {key}"
    assert fx["id"] == path.stem
    assert fx["channel"] in ("TEXT", "SDR", "VOICE")
    Draft7Validator(EXTRACTION).validate(fx["expected"])


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_fixture_expected_is_grounded(path: Path) -> None:
    """Every entity text must appear in the source (case-insensitive) unless the note
    explains a spelled-out form (NATO alphabet call signs)."""
    fx = load(path)
    src = fx["source_text"].upper()
    for ent in fx["expected"]["entities"]:
        if ent["type"] == "CALLSIGN":
            continue
        # allow inflected forms: check the first word of the entity at least
        assert ent["text"].split()[0].upper() in src, f"{path.name}: {ent['text']} not in source"


def test_fixture_coverage() -> None:
    fxs = [load(p) for p in FIXTURES]
    assert 6 <= len(fxs) <= 12
    assert {f["lang"] for f in fxs} == {"en", "pl"}
    assert {f["channel"] for f in fxs} == {"TEXT", "SDR", "VOICE"}
    assert any("*" in f["source_text"] for f in fxs), "need a '*'-corrupted fixture"
    types = {f["expected"]["event_type"] for f in fxs}
    assert {"NAV_WARNING", "EXERCISE", "WRECK", "VOICE_REPORT", "MET_WARNING"} <= types


def test_invalid_examples_rejected() -> None:
    v = Draft7Validator(EXTRACTION)
    base = load(FIXTURES[0])["expected"]
    bad_time = dict(base, issued_at="2026-09-07 12:30")  # no T / Z
    bad_enum = dict(base, event_type="STORM")
    bad_geom = dict(base, geometry={"type": "Point", "coordinates": [57.3, 11.9, 0]})
    extra = dict(base, confidence=0.9)  # model "confidence" is banned by design (PRD F12)
    for obj in (bad_time, bad_enum, bad_geom, extra):
        assert not v.is_valid(obj)


def test_committed_gbnf_is_current() -> None:
    generated = schema_to_gbnf(EXTRACTION, url="file://schemas/extraction.schema.json")
    on_disk = (SCHEMAS / "extraction.gbnf").read_text(encoding="utf-8")
    assert on_disk.split("\n", 1)[1].rstrip("\n") == generated.rstrip("\n"), "run `make gbnf`"


def test_gbnf_key_order_and_enums() -> None:
    gbnf = (SCHEMAS / "extraction.gbnf").read_text(encoding="utf-8")
    root = next(line for line in gbnf.splitlines() if line.startswith("root ::="))
    keys = [
        "event-type-kv",
        "warning-id-kv",
        "agency-kv",
        "issued-at-kv",
        "valid-from-kv",
        "valid-to-kv",
        "location-name-kv",
        "geometry-kv",
        "entities-kv",
    ]
    positions = [root.index(k) for k in keys]
    assert positions == sorted(positions)
    for value in EXTRACTION["definitions"]["event_type"]["enum"]:
        assert f'"\\"{value}\\""' in gbnf
