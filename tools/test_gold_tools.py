"""Tests for curate_seed.py and gold_merge.py (offline, tmp dirs)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import curate_seed as cs
from tools import gold_merge as gm

FIXTURES = Path(__file__).resolve().parents[1] / "schemas" / "fixtures"


def test_normalize_and_header() -> None:
    raw = "ZCZC IA47\r\n071230 UTC SEP   \r\n\r\n\r\n\r\nTEXT\r\nNNNN\r\n"
    norm = cs.normalize_text(raw)
    assert norm == "ZCZC IA47\n071230 UTC SEP\n\nTEXT\nNNNN\n"
    assert cs.parse_header(norm) == {"b1_station": "I", "b2_subject": "A", "b3b4_number": "47"}
    assert cs.parse_header("OSTRZEŻENIE NR 1") is None


def test_write_seed_and_duplicate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cs, "SEEDS", tmp_path)
    seed = cs.build_seed(
        "ZCZC JA05\nTEST *\nNNNN",
        "frisnit",
        None,
        "2026-09-07T17:30Z",
        "https://example.org",
        "en",
        "TEXT",
        "k",
        "",
    )
    assert seed["station"] == "J" and seed["star_rate"] > 0
    path = cs.write_seed(seed)
    assert path.name == "001_J_20260907.json"
    with pytest.raises(SystemExit):
        cs.write_seed(
            cs.build_seed(
                "ZCZC JA05\nTEST *\nNNNN", "frisnit", None, None, None, "en", "TEXT", "k", ""
            )
        )
    seed2 = cs.build_seed(
        "OSTRZEŻENIE NAWIGACYJNE NR 1/26\nTEST", "bhmw", None, None, None, "pl", "TEXT", "k", ""
    )
    assert cs.write_seed(seed2).name == "002_X_undated.json"


def test_merge_only_human_accepted_reaches_gold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gold = tmp_path / "gold"
    (gold / "seeds").mkdir(parents=True)
    (gold / "generated").mkdir()
    (gold / "review").mkdir()
    monkeypatch.setattr(gm, "GOLD", gold)
    monkeypatch.setattr(gm, "SEEDS", gold / "seeds")
    monkeypatch.setattr(gm, "GENERATED", gold / "generated")
    monkeypatch.setattr(gm, "REVIEW", gold / "review")
    monkeypatch.setattr(gm, "VERDICTS", gold / "review" / "verdicts.jsonl")

    fx = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in FIXTURES.glob("*.json")}
    en = fx["01_navtex_en_nav_warning"]
    pl = fx["04_bhmw_pl_cable_works"]
    noisy = fx["03_navtex_en_corrupted_stars"]

    # a reviewed real seed (EN), an unlabeled seed, two generated items (PL, noisy)
    (gold / "seeds" / "001_I_20260907.json").write_text(
        json.dumps(
            {
                "id": "001_I_20260907",
                "text": en["source_text"],
                "lang": "en",
                "channel": "TEXT",
                "source": "frisnit",
                "station": "I",
                "star_rate": 0.0,
                "label": en["expected"],
                "label_status": "reviewed",
            }
        ),
        encoding="utf-8",
    )
    (gold / "seeds" / "002_X_undated.json").write_text(
        json.dumps(
            {
                "id": "002_X_undated",
                "text": "ZCZC HB01\nNOTHING\nNNNN",
                "lang": "en",
                "star_rate": 0.0,
                "label": None,
                "label_status": "unlabeled",
            }
        ),
        encoding="utf-8",
    )
    gm.write_jsonl(
        gold / "generated" / "w1.jsonl",
        [
            {
                "id": "g1",
                "lang": "pl",
                "channel": "TEXT",
                "source_text": pl["source_text"],
                "expected": pl["expected"],
                "judge": {"ok": True},
            },
            {
                "id": "g2",
                "lang": "en",
                "channel": "SDR",
                "source_text": noisy["source_text"],
                "expected": noisy["expected"],
                "judge": {"ok": True},
            },
        ],
    )

    items = gm.collect()
    assert {it["id"] for it in items} == {
        "seed:001_I_20260907",
        "seed:002_X_undated",
        "gen:g1",
        "gen:g2",
    }
    counts = gm.merge(items)
    # the hand-labelled seed is gold already; LLM-labelled items wait in train
    assert counts == {"pl": 0, "en": 1, "noisy": 0, "train": 2}

    # review round: accept the seed and g1, reject g2
    gm.export_review(items, gold / "review" / "pending.csv")
    csv_text = (gold / "review" / "pending.csv").read_text(encoding="utf-8")
    assert "gen:g1" in csv_text and "seed:001_I_20260907" not in csv_text
    gm.write_jsonl(
        gold / "review" / "verdicts.jsonl",
        [
            {
                "id": "seed:001_I_20260907",
                "verdict": "accepted",
                "expected": en["expected"],
                "reviewer": "k",
            },
            {"id": "gen:g1", "verdict": "accepted", "expected": pl["expected"], "reviewer": "k"},
            {"id": "gen:g2", "verdict": "rejected", "expected": None, "reviewer": "k"},
        ],
    )
    counts = gm.merge(gm.collect())
    assert counts == {"pl": 1, "en": 1, "noisy": 0, "train": 0}
    en_rows = gm.read_jsonl(gold / "en.jsonl")
    assert en_rows[0]["provenance"]["kind"] == "real" and en_rows[0]["label_origin"] == "human"


def test_import_review_rejects_invalid_accepted_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gm, "VERDICTS", tmp_path / "verdicts.jsonl")
    csv_path = tmp_path / "r.csv"
    csv_path.write_text(
        "id,lang,channel,split,label_origin,source_text,expected_json,verdict,reviewer,comment\n"
        'gen:x,en,TEXT,en,llm,"t","{""event_type"": ""STORM""}",accepted,k,\n',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        gm.import_review(csv_path)
