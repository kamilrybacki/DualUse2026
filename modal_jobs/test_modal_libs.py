"""Offline tests for the pure parts of the Modal jobs (no modal import)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest
from jsonschema import Draft7Validator

from modal_jobs import augment
from modal_jobs import datagen_lib as lib

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "extraction.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft7Validator(SCHEMA)
FIXTURES = [
    json.loads(p.read_text(encoding="utf-8"))
    for p in sorted((ROOT / "schemas" / "fixtures").glob("*.json"))
]


def fake_seeds() -> list[dict]:
    return [
        {"id": f"s{i}", "lang": f["lang"], "channel": f["channel"], "text": f["source_text"]}
        for i, f in enumerate(FIXTURES)
    ]


def test_specs_cover_every_kind_and_type() -> None:
    specs = lib.build_specs(fake_seeds(), per_type=3)
    assert {s.kind for s in specs} == set(lib.KINDS)
    for s in specs:
        assert s.n == 3
        assert all(fs["lang"] == s.lang and fs["channel"] == s.channel for fs in s.few_shot)
    only = lib.build_specs(fake_seeds(), 1, kinds=["vhf_pl"])
    assert {s.kind for s in only} == {"vhf_pl"} and only[0].event_type == "VOICE_REPORT"


def test_prompt_renders_all_placeholders() -> None:
    tpl = (ROOT / "prompts" / "datagen_v0.1.md").read_text(encoding="utf-8")
    spec = lib.build_specs(fake_seeds(), 2, kinds=["navtex_en"])[0]
    p = lib.render_prompt(tpl, spec, SCHEMA)
    assert not re.search(r"\{(kind|lang|channel|event_type|style|n|few_shot|schema)\}", p)
    assert "ZCZC" in p and "NAV_WARNING" in p


def test_output_schema_wraps_extraction_schema() -> None:
    wrapper = lib.output_schema(SCHEMA)
    Draft7Validator.check_schema(wrapper)
    ok = {
        "items": [
            {
                "source_text": "ZCZC IA00 TEST MESSAGE LONG ENOUGH NNNN",
                "expected": FIXTURES[0]["expected"],
            }
        ]
    }
    assert Draft7Validator(wrapper).is_valid(ok)


def test_parse_items_drops_invalid_labels() -> None:
    spec = lib.build_specs(fake_seeds(), 1, kinds=["navtex_en"])[0]
    good = FIXTURES[0]["expected"]
    bad = dict(good, event_type="STORM")
    raw = "Here you go:\n" + json.dumps(
        {
            "items": [
                {"source_text": "ZCZC IA47 SOME LONG ENOUGH TEXT NNNN", "expected": good},
                {"source_text": "ZCZC IA48 ANOTHER LONG ENOUGH TEXT NNNN", "expected": bad},
            ]
        }
    )
    items = lib.parse_items(raw, spec, VALIDATOR, "run1")
    assert len(items) == 1 and items[0]["id"].startswith("run1_navtex_en_nav_warning_")
    assert lib.parse_items("garbage", spec, VALIDATOR, "run1") == []


def test_corrupt_stars_adjusts_labels_deterministically() -> None:
    item = {
        "id": "x",
        "kind": "navtex_en",
        "lang": "en",
        "channel": "TEXT",
        "source_text": FIXTURES[0]["source_text"],
        "expected": FIXTURES[0]["expected"],
    }
    a = lib.corrupt_stars(item, rate=0.15, seed=1)
    b = lib.corrupt_stars(item, rate=0.15, seed=1)
    assert a == b and a["channel"] == "SDR" and a["noisy"] and "*" in a["source_text"]
    assert VALIDATOR.is_valid(a["expected"])
    text = a["source_text"]
    # header hit → warning_id null; coordinate hit → geometry null; time hit → times null
    if "*" in text.split("\n")[0]:
        assert a["expected"]["warning_id"] is None
    coord_span = re.search(lib.COORD_RE, item["source_text"]).span()
    if "*" in text[coord_span[0] : coord_span[1]]:
        assert a["expected"]["geometry"] is None
    else:
        assert a["expected"]["geometry"] == item["expected"]["geometry"]
    # entities stay verbatim copies of the (corrupted) source
    for e in a["expected"]["entities"]:
        assert e["text"].upper() in text.upper()


def test_corrupt_stars_zero_rate_is_identity_except_channel() -> None:
    item = {
        "id": "x",
        "kind": "navtex_en",
        "lang": "en",
        "channel": "TEXT",
        "source_text": FIXTURES[0]["source_text"],
        "expected": FIXTURES[0]["expected"],
    }
    c = lib.corrupt_stars(item, 0.0, 0)
    assert c["source_text"] == item["source_text"] and c["expected"] == item["expected"]


def test_garble_is_fldigi_style_and_labels_abstain() -> None:
    item = {
        "id": "x",
        "kind": "navtex_en",
        "lang": "en",
        "channel": "TEXT",
        "source_text": FIXTURES[1]["source_text"],  # exercise polygon, 4 corners
        "expected": FIXTURES[1]["expected"],
    }
    g = lib.garble(item, rate=0.08, seed=5)
    assert g == lib.garble(item, rate=0.08, seed=5)
    assert "*" not in g["source_text"] and g["source_text"] != item["source_text"]
    assert g["channel"] == "SDR" and g["noisy"] and g["id"].endswith("_garbled")
    assert VALIDATOR.is_valid(g["expected"])
    assert len(g["source_text"]) == len(item["source_text"])  # substitutions only, no drops
    # any damaged coordinate → no geometry; untouched fields keep their values
    coord_hit = any(
        a != b
        for m in lib.COORD_RE.finditer(item["source_text"])
        for a, b in zip(
            item["source_text"][m.start() : m.end()],
            g["source_text"][m.start() : m.end()],
            strict=True,
        )
    )
    assert (g["expected"]["geometry"] is None) == coord_hit
    assert g["expected"]["event_type"] == "EXERCISE"


def test_garble_zero_rate_is_identity() -> None:
    item = {
        "id": "x",
        "kind": "navtex_en",
        "lang": "en",
        "channel": "TEXT",
        "source_text": FIXTURES[0]["source_text"],
        "expected": FIXTURES[0]["expected"],
    }
    g = lib.garble(item, 0.0, 0)
    assert g["source_text"] == item["source_text"] and g["expected"] == item["expected"]


def test_judge_parse() -> None:
    assert lib.parse_judge('{"verdict":"ACCEPT","issues":[]}')["verdict"] == "accept"
    assert lib.parse_judge("no json")["verdict"] == "reject"
    r = lib.parse_judge('x {"verdict":"reject","issues":["geometry"],"corrected":null} y')
    assert r["issues"] == ["geometry"] and r["corrected"] is None


@pytest.mark.parametrize("preset", list(augment.PRESETS))
def test_augment_presets_produce_8k_audio(preset: str) -> None:
    pytest.importorskip("scipy")
    rate = 22050
    t = np.arange(rate * 2) / rate
    x = (0.5 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 5000 * t)).astype(np.float32)
    y, out_rate = augment.augment(x, rate, augment.PRESETS[preset])
    assert out_rate == 8000
    assert abs(len(y) / out_rate - 2.0) < 0.2  # duration kept (+ squelch tail)
    assert float(np.max(np.abs(y))) <= 0.9 + 1e-6
    # band-pass removed the 5 kHz component: compare spectra
    spec = np.abs(np.fft.rfft(y[:out_rate]))
    freqs = np.fft.rfftfreq(out_rate, 1 / out_rate)
    assert spec[(freqs > 400) & (freqs < 480)].max() > 5 * spec[(freqs > 3600)].max()


def test_parse_items_accepts_bare_list_and_fences() -> None:
    spec = lib.build_specs(fake_seeds(), 1, kinds=["navtex_en"])[0]
    good = FIXTURES[0]["expected"]
    bare = json.dumps([{"source_text": "ZCZC IA49 BARE LIST LONG ENOUGH NNNN", "expected": good}])
    assert len(lib.parse_items(bare, spec, VALIDATOR, "run1")) == 1
    fenced = "```json\n" + json.dumps({"items": json.loads(bare)}) + "\n```"
    assert len(lib.parse_items(fenced, spec, VALIDATOR, "run1")) == 1
