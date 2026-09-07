"""Offline tests for tools/fetch_kiwis.py (parser + ranking; no network)."""

from __future__ import annotations

from tools import fetch_kiwis as fk

SAMPLE = """
<div class='cl-entry'><div class='cl-info'>
<!-- name=Baltic loop, Gdańsk --> <!-- sdr_hw=KiwiSDR 2 -->
<!-- antenna=YouLoop magnetic loop, LF/MW ok -->
<!-- users=1 --> <!-- users_max=4 --> <!-- gps=(54.35, 18.65) --> <!-- tlimit=30 min -->
<a href='http://gdansk.example.org:8073' target='_blank'>gdansk.example.org:8073</a>
</div></div>
<div class='cl-entry'><div class='cl-info'>
<!-- name=Full house --> <!-- antenna=dipole --> <!-- users=4 --> <!-- users_max=4 -->
<!-- gps=(59.9, 10.7) --> <a href='http://oslo.example.org:8073'>x</a>
</div></div>
<div class='cl-entry'><div class='cl-info'>
<!-- name=Far away --> <!-- antenna=loop --> <!-- users=0 --> <!-- users_max=8 -->
<!-- gps=(40.0, -3.7) --> <a href='http://madrid.example.org:8074'>x</a>
</div></div>
<div class='cl-entry'><div class='cl-info'>
<!-- name=Tallinn whip --> <!-- antenna=Mini-Whip --> <!-- users=0 --> <!-- users_max=8 -->
<!-- gps=(59.4, 24.8) --> <a href='http://tallinn.example.org:8073'>x</a>
</div></div>
"""


def test_parse_public_list() -> None:
    kiwis = fk.parse_public_list(SAMPLE)
    assert [k.host for k in kiwis] == [
        "gdansk.example.org",
        "oslo.example.org",
        "madrid.example.org",
        "tallinn.example.org",
    ]
    g = kiwis[0]
    assert (g.port, g.users, g.users_max, g.lat, g.lon) == (8073, 1, 4, 54.35, 18.65)
    assert "loop" in g.antenna and g.tlimit == "30 min" and g.name.startswith("Baltic loop")
    assert kiwis[2].port == 8074


def test_rank_filters_bbox_and_busy_and_sorts_by_distance() -> None:
    kiwis = fk.parse_public_list(SAMPLE)
    for_j = fk.rank(kiwis, "J")
    assert [k.host for k in for_j] == [
        "gdansk.example.org",
        "tallinn.example.org",
    ]  # Oslo full, Madrid out
    assert for_j[0].distance_km < for_j[1].distance_km
    for_u = fk.rank(kiwis, "U")
    assert for_u[0].host == "tallinn.example.org"


def test_cli_offline_page(tmp_path, capsys) -> None:
    page = tmp_path / "public.html"
    page.write_text(SAMPLE, encoding="utf-8")
    assert fk.main(["--station", "J", "--page", str(page), "--json"]) == 0
    out = capsys.readouterr().out
    assert "gdansk.example.org" in out and "madrid" not in out
