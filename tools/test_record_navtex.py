"""Tests for tools/record_navtex.py — slot table must match PRD Annex A.1 exactly."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools import record_navtex as rn

ANNEX_A = {
    "H": ["0110", "0510", "0910", "1310", "1710", "2110"],
    "I": ["0120", "0520", "0920", "1320", "1720", "2120"],
    "J": ["0130", "0530", "0930", "1330", "1730", "2130"],
    "U": ["0320", "0720", "1120", "1520", "1920", "2320"],
}


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_slot_table_matches_annex_a() -> None:
    assert {k: v.slots_utc() for k, v in rn.STATIONS.items()} == ANNEX_A


def test_next_slot_same_day_and_rollover() -> None:
    h = rn.STATIONS["H"]
    assert rn.next_slot(h, utc("2026-09-07T17:00")) == utc("2026-09-07T17:10")
    assert rn.next_slot(h, utc("2026-09-07T17:10")) == utc("2026-09-07T17:10")  # inclusive
    assert rn.next_slot(h, utc("2026-09-07T17:11")) == utc("2026-09-07T21:10")
    assert rn.next_slot(h, utc("2026-09-07T21:30")) == utc("2026-09-08T01:10")


def test_next_slot_local_time_input() -> None:
    u = rn.STATIONS["U"]
    local = datetime.fromisoformat("2026-09-07T17:00").replace(tzinfo=rn.LOCAL_TZ)  # 15:00Z
    assert rn.next_slot(u, local) == utc("2026-09-07T15:20")


def test_single_station_window_uses_annex_defaults() -> None:
    w = rn.plan_window(rn.parse_station_arg("U"), utc("2026-09-07T15:00"))
    assert w.first_slot == w.last_slot == utc("2026-09-07T15:20")
    assert w.record_start == utc("2026-09-07T15:18")  # 2 min early
    assert w.tlimit == 780


def test_hij_block_is_one_contiguous_recording() -> None:
    w = rn.plan_window(rn.parse_station_arg("HIJ"), utc("2026-09-07T17:00"))
    assert [s.id for s in w.stations] == ["H", "I", "J"]
    assert w.first_slot == utc("2026-09-07T17:10")
    assert w.last_slot == utc("2026-09-07T17:30")
    assert w.record_start == utc("2026-09-07T17:08")
    # 2 min lead + 20 min span + 10 min slot + 1 min tail
    assert w.tlimit == 120 + 20 * 60 + 600 + 60
    assert w.record_end == utc("2026-09-07T17:41")


def test_block_reanchors_when_now_is_mid_block() -> None:
    # 17:15Z: H already started; the block should move to the 21:10 cycle as a whole.
    w = rn.plan_window(rn.parse_station_arg("H,I,J"), utc("2026-09-07T17:15"))
    assert w.first_slot == utc("2026-09-07T21:10")
    assert w.last_slot == utc("2026-09-07T21:30")


def test_filename_per_annex_a() -> None:
    w = rn.plan_window(rn.parse_station_arg("H"), utc("2026-09-07T17:00"))
    assert rn.filename(w) == "navtex_H_20260907_1710"
    assert rn.filename(w, "kiwi1") == "navtex_H_20260907_1710_kiwi1"


def test_command_single_kiwi_iq() -> None:
    w = rn.plan_window(rn.parse_station_arg("U"), utc("2026-09-07T15:00"))
    cmd = rn.build_command(
        w,
        rn.parse_kiwi_arg("sdr.example.org"),
        "iq",
        Path("/out"),
        python="python3",
        kiwirecorder=Path("kiwirecorder.py"),
    )
    assert cmd[:2] == ["python3", "kiwirecorder.py"]
    assert cmd[cmd.index("-s") + 1] == "sdr.example.org"
    assert cmd[cmd.index("-p") + 1] == "8073"
    assert cmd[cmd.index("--fn") + 1] == "navtex_U_20260907_1520"
    assert cmd[cmd.index("--tlimit") + 1] == "780"
    assert cmd[cmd.index("-f") + 1] == "518"
    assert cmd[cmd.index("-m") + 1] == "iq"
    assert "--kiwi-wav" in cmd


def test_command_two_kiwis_usb() -> None:
    w = rn.plan_window(rn.parse_station_arg("J"), utc("2026-09-07T17:00"))
    kiwis = rn.parse_kiwi_arg("a-1.example.org, b.example.net:8074")
    cmd = rn.build_command(w, kiwis, "usb", Path("/out"))
    assert cmd[cmd.index("-s") + 1] == "a-1.example.org,b.example.net"
    assert cmd[cmd.index("-p") + 1] == "8073,8074"
    assert cmd[cmd.index("--fn") + 1] == "navtex_J_20260907_1730_a1,navtex_J_20260907_1730_b"
    assert cmd[cmd.index("-f") + 1] == "516.8"
    assert cmd[cmd.index("-m") + 1] == "usb"
    assert "--kiwi-wav" not in cmd


def test_bad_station_rejected() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        rn.parse_station_arg("X")


def test_block_with_u_spans_the_cycle() -> None:
    # H/I/J at xx:10-xx:30 and U two hours later share the same 4 h cycle.
    w = rn.plan_window(rn.parse_station_arg("HIJU"), utc("2026-09-07T17:00"))
    assert w.first_slot == utc("2026-09-07T17:10")
    assert w.last_slot == utc("2026-09-07T19:20")
    assert w.record_end == utc("2026-09-07T19:31")


def test_cli_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    rc = rn.main(
        [
            "--station",
            "HIJ",
            "--kiwi",
            "k.example.org",
            "--at",
            "2026-09-07T17:00+00:00",
            "--dry-run",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "navtex_HIJ_20260907_1710" in out
    assert "--tlimit 1980" in out


def test_cli_list(capsys: pytest.CaptureFixture[str]) -> None:
    assert rn.main(["--list", "--at", "2026-09-07T12:00+00:00"]) == 0
    out = capsys.readouterr().out
    for sid, slots in ANNEX_A.items():
        assert sid in out and " ".join(slots) in out
