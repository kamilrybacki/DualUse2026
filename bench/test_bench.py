"""Offline tests for the benchmark harness: metrics + end-to-end run with the fake backend."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench import metrics as m  # noqa: E402
from bench import run_bench  # noqa: E402

THRESHOLDS = yaml.safe_load((ROOT / "bench" / "thresholds.yaml").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "schemas" / "extraction.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft7Validator(SCHEMA)
FIXTURES = run_bench.load_gold(ROOT / "schemas" / "fixtures")


def test_thresholds_frozen_values() -> None:
    p = THRESHOLDS["pass"]
    assert p["schema_validity"] == 1.0
    assert p["field_f1"] == 0.85
    assert p["unsupported_fact_rate"] == 0.02
    assert p["geo_resolution"] == 0.90
    assert p["latency_p95_s"] == 2.0
    assert {r["id"] for r in THRESHOLDS["escalation_rules"]} >= {
        "schema_invalid",
        "type_unknown",
        "no_location",
        "geometry_outside_baltic",
        "time_inconsistent",
        "unsupported_fact",
    }


def test_coords_in_text_and_distance() -> None:
    pts = m.coords_in_text("BUOY 57-18.2N 011-56.5E UNLIT")
    assert len(pts) == 1
    lon, lat = pts[0]
    assert abs(lat - 57.3033) < 1e-3 and abs(lon - 11.9417) < 1e-3
    assert m.haversine_nm((11.9417, 57.3033), (11.9417, 57.3033 + 1 / 60)) - 1.0 < 0.01


def test_field_scores() -> None:
    tol = 0.5
    assert m.field_score("event_type", "WRECK", "WRECK", tol) == 1.0
    assert m.field_score("event_type", "OTHER", "WRECK", tol) == 0.0
    assert m.field_score("issued_at", None, None, tol) == 1.0
    assert m.field_score("issued_at", "2026-09-07T12:30:00Z", None, tol) == 0.0
    g = {"type": "Point", "coordinates": [11.9417, 57.3033]}
    near = {"type": "Point", "coordinates": [11.9417, 57.3083]}  # 0.3 NM north
    far = {"type": "Point", "coordinates": [12.5, 57.3033]}
    assert m.field_score("geometry", near, g, tol) == 1.0
    assert m.field_score("geometry", far, g, tol) == 0.0
    assert m.field_score("location_name", "KATTEGAT", "KATTEGAT, LIGHT BUOY NIDINGEN E", tol) > 0.3
    ents_g = [{"type": "VESSEL", "text": "Neptun"}, {"type": "INFRA", "text": "kablu podmorskim"}]
    ents_p = [{"type": "VESSEL", "text": "NEPTUN"}]
    assert 0.6 < m.entity_f1(ents_p, ents_g) < 0.7


def test_grounding_rules() -> None:
    src = FIXTURES[0]["source_text"]
    tol = 0.5
    assert m.value_supported("warning_id", "IA47", src, tol)
    assert not m.value_supported("warning_id", "XX99", src, tol)
    assert m.value_supported("issued_at", "2026-09-07T12:30:00Z", src, tol)
    assert not m.value_supported("issued_at", "2026-09-07T23:45:00Z", src, tol)
    assert m.value_supported("agency", "NAVTEX/518/I", src, tol)
    assert not m.value_supported("agency", "NAVTEX/518/J", src, tol)
    ok = {"type": "Point", "coordinates": [11.9417, 57.3033]}
    bad = {"type": "Point", "coordinates": [18.0, 55.0]}
    assert m.value_supported("geometry", ok, src, tol)
    assert not m.value_supported("geometry", bad, src, tol)
    # spoken position (fixture 06): 54°32'N 018°48'E
    voice = next(f for f in FIXTURES if f["id"] == "06_vhf_pl_voice_report")
    assert m.value_supported("geometry", voice["expected"]["geometry"], voice["source_text"], tol)
    assert not m.value_supported("geometry", bad, voice["source_text"], tol)


def test_all_fixture_labels_are_grounded() -> None:
    """The gold labels themselves must pass the unsupported-fact check (sanity of the metric)."""
    for fx in FIXTURES:
        res = m.evaluate_item(
            fx["id"], fx["expected"], fx["expected"], fx["source_text"], VALIDATOR, THRESHOLDS
        )
        assert res.valid, fx["id"]
        assert res.unsupported == [], (fx["id"], res.unsupported)
        assert res.field_f1 == 1.0


def test_null_model_is_penalized_for_omissions_not_facts() -> None:
    fx = FIXTURES[0]
    null = {k: None for k in fx["expected"]} | {"event_type": "UNKNOWN", "entities": []}
    res = m.evaluate_item(fx["id"], null, fx["expected"], fx["source_text"], VALIDATOR, THRESHOLDS)
    assert res.valid
    assert res.unsupported == []
    assert "warning_id" in res.omitted and "geometry" in res.omitted
    assert "type_unknown" in res.triggers and "no_location" in res.triggers


def test_invalid_output_counts_as_schema_invalid() -> None:
    fx = FIXTURES[0]
    res = m.evaluate_item(
        fx["id"], {"event_type": "STORM"}, fx["expected"], fx["source_text"], VALIDATOR, THRESHOLDS
    )
    assert not res.valid and res.triggers == ["schema_invalid"]


def test_end_to_end_fake_gold_passes(tmp_path: Path) -> None:
    rc = run_bench.main(
        ["--backend", "fake", "--out", str(tmp_path / "run"), "--run-id", "t-gold", "--quiet"]
    )
    assert rc == 0
    s = json.loads((tmp_path / "run" / "summary.json").read_text(encoding="utf-8"))
    assert s["pass"] and s["schema_validity"] == 1.0 and s["unsupported_fact_rate"] == 0.0
    assert (tmp_path / "run" / "report.md").exists()
    assert (tmp_path / "run" / "results.csv").read_text(encoding="utf-8").count("\n") == len(
        FIXTURES
    ) + 1


def test_end_to_end_fake_noisy_fails_on_unsupported(tmp_path: Path) -> None:
    rc = run_bench.main(
        [
            "--backend",
            "fake",
            "--fake-mode",
            "noisy",
            "--out",
            str(tmp_path / "run"),
            "--run-id",
            "t-noisy",
            "--quiet",
        ]
    )
    assert rc == 1
    s = json.loads((tmp_path / "run" / "summary.json").read_text(encoding="utf-8"))
    assert s["unsupported_fact_rate"] > 0.02
    assert s["trigger_counts"]["unsupported_fact"] == len(FIXTURES)
    assert not s["checks"]["unsupported_fact_rate"]


def test_end_to_end_fake_null_fails_on_f1(tmp_path: Path) -> None:
    rc = run_bench.main(
        [
            "--backend",
            "fake",
            "--fake-mode",
            "null",
            "--out",
            str(tmp_path / "run"),
            "--run-id",
            "t-null",
            "--quiet",
        ]
    )
    assert rc == 1
    s = json.loads((tmp_path / "run" / "summary.json").read_text(encoding="utf-8"))
    assert s["unsupported_fact_rate"] == 0.0
    assert s["field_f1"] < 0.85 and s["omission_rate"] > 0.5
    assert s["escalation_rate"] == 1.0


def test_parse_json_tolerates_chatter() -> None:
    assert run_bench.parse_json('Sure! {"a": 1}') == {"a": 1}
    assert run_bench.parse_json("nope") is None
