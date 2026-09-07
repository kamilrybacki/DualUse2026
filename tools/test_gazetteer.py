"""Offline tests for tools/download_gazetteer.py (parser, seed CSV, sqlite build, lookup)."""

from __future__ import annotations

from pathlib import Path

from tools import download_gazetteer as gz

SAMPLE = {
    "elements": [
        {
            "type": "node",
            "id": 1,
            "lat": 57.3033,
            "lon": 11.9417,
            "tags": {
                "seamark:type": "light_major",
                "seamark:name": "Nidingen",
                "seamark:light:character": "Fl(2) W 15s",
            },
        },
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 54.52, "lon": 18.55},
            "tags": {"seamark:type": "harbour", "name": "Port Gdynia", "name:en": "Gdynia Harbour"},
        },
        {
            "type": "node",
            "id": 3,
            "lat": 54.35,
            "lon": 18.65,
            "tags": {
                "place": "city",
                "name": "Gdańsk",
                "name:en": "Gdansk",
                "population": "470000",
            },
        },
        {
            "type": "node",
            "id": 4,
            "lat": 55.0,
            "lon": 15.0,
            "tags": {"seamark:type": "buoy_lateral"},
        },
        {"type": "relation", "id": 5, "tags": {"natural": "bay", "name": "Zatoka Pucka"}},
    ]
}


def test_match_key_folds_diacritics_and_punctuation() -> None:
    assert gz.match_key("Zatoka Gdańska") == "ZATOKA GDANSKA"
    assert gz.match_key("Bjuröklubb (H)") == "BJUROKLUBB H"
    assert gz.match_key("St. Petersburg-Kronstadt") == "ST PETERSBURG KRONSTADT"


def test_rows_from_overpass_skips_unnamed_and_uncentred() -> None:
    rows = gz.rows_from_overpass(SAMPLE)
    assert [r["name"] for r in rows] == ["Nidingen", "Port Gdynia", "Gdańsk"]
    assert rows[0]["kind"] == "light_major" and rows[0]["light_character"] == "Fl(2) W 15s"
    assert rows[1]["kind"] == "harbour" and rows[1]["lat"] == 54.52
    assert rows[2]["kind"] == "place_city" and rows[2]["alt_names"] == "Gdansk"


def test_seed_csv_loads_and_has_prd_areas() -> None:
    rows = gz.rows_from_seed(gz.SEED_CSV)
    keys = {r["key"] for r in rows}
    for needed in ("KATTEGAT", "SOUTHERN BALTIC", "GULF OF GDANSK", "BOTHNIAN SEA", "UTKLIPPAN"):
        assert needed in keys, needed
    for r in rows:
        assert 53.0 <= r["lat"] <= 66.5 and 7.0 <= r["lon"] <= 31.0, r["name"]


def test_build_and_lookup(tmp_path: Path) -> None:
    db = tmp_path / "g.sqlite"
    rows = gz.rows_from_overpass(SAMPLE) + gz.rows_from_seed(gz.SEED_CSV)
    n = gz.build_db(rows, db)
    assert n == len(rows)
    hit = gz.lookup(db, "NIDINGEN")
    assert hit and hit[0][0] == "Nidingen" and abs(hit[0][2] - 57.3033) < 1e-6
    assert gz.lookup(db, "zatoka gdańska")[0][1] == "sea_area"
    assert gz.lookup(db, "NOWHERE-XYZ") == []
