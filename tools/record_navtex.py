#!/usr/bin/env python3
"""Record Baltic 518 kHz NAVTEX slots from public KiwiSDR receivers (PRD Annex A.1).

This is a scheduling wrapper around the vendored ``kiwirecorder.py``
(``tools/vendor/kiwiclient``). It is a *recording tool*, not a runtime input adapter:
it produces wav files under ``data/recordings/518khz/`` and nothing else.

Examples::

    # show the slot table (UTC + local) and the next slot for every station
    python tools/record_navtex.py --list

    # record the whole H/I/J block (19:10–19:40 CEST) from two Kiwis, wait for the slot
    python tools/record_navtex.py --station HIJ --kiwi kiwi1.example.org,kiwi2.example.org:8073

    # single station, 13 min IQ recording starting 2 min early (Annex A defaults)
    python tools/record_navtex.py --station U --kiwi kiwi1.example.org

    # only print what would run
    python tools/record_navtex.py --station J --kiwi kiwi1.example.org --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
KIWIRECORDER = REPO_ROOT / "tools" / "vendor" / "kiwiclient" / "kiwirecorder.py"
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "recordings" / "518khz"
LOCAL_TZ = ZoneInfo("Europe/Warsaw")

SLOT_MINUTES = 10  # NAVTEX slot length
SLOT_PERIOD_H = 4  # each station repeats every 4 h
LEAD_SECONDS = 120  # start 2 min before the slot (Annex A)
SINGLE_TLIMIT = 780  # 13 min: slot + margin (Annex A)
TAIL_SECONDS = 60  # extra tail when recording a block of consecutive slots

FREQ_IQ_KHZ = 518.0
FREQ_USB_KHZ = 516.8  # carrier so mark/space tones land in the audio passband (Annex A)


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    country: str
    first_hour: int  # UTC hour of the first daily slot
    minute: int  # minute within the hour

    @property
    def slot_hours(self) -> list[int]:
        return [(self.first_hour + SLOT_PERIOD_H * k) % 24 for k in range(24 // SLOT_PERIOD_H)]

    def slots_utc(self) -> list[str]:
        return [f"{h:02d}{self.minute:02d}" for h in self.slot_hours]


# PRD Annex A.1 — verbatim slot table.
STATIONS: dict[str, Station] = {
    "H": Station("H", "Bjuröklubb", "SE", first_hour=1, minute=10),
    "I": Station("I", "Grimeton", "SE", first_hour=1, minute=20),
    "J": Station("J", "Gislövshammar", "SE", first_hour=1, minute=30),
    "U": Station("U", "Tallinn", "EE", first_hour=3, minute=20),
}


def parse_station_arg(arg: str) -> list[Station]:
    """``"H"`` → [H]; ``"HIJ"`` or ``"H,I,J"`` → [H, I, J]. Order is kept, duplicates dropped."""
    ids: list[str] = []
    for ch in arg.upper().replace(",", "").replace(" ", ""):
        if ch not in STATIONS:
            raise argparse.ArgumentTypeError(
                f"unknown station {ch!r}; known: {', '.join(STATIONS)}"
            )
        if ch not in ids:
            ids.append(ch)
    if not ids:
        raise argparse.ArgumentTypeError("at least one station id required")
    return [STATIONS[i] for i in ids]


def next_slot(station: Station, now: datetime) -> datetime:
    """Next slot start (UTC) at or after ``now``."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(UTC)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    candidates = [
        day + timedelta(days=d, hours=h, minutes=station.minute)
        for d in (0, 1)
        for h in station.slot_hours
    ]
    return min(c for c in candidates if c >= now)


@dataclass(frozen=True)
class Window:
    """Recording window covering one or more consecutive slots."""

    stations: tuple[Station, ...]
    first_slot: datetime  # UTC start of the earliest slot
    last_slot: datetime  # UTC start of the latest slot

    @property
    def record_start(self) -> datetime:
        return self.first_slot - timedelta(seconds=LEAD_SECONDS)

    @property
    def tlimit(self) -> int:
        if len(self.stations) == 1:
            return SINGLE_TLIMIT
        span = (self.last_slot - self.first_slot).total_seconds()
        return int(LEAD_SECONDS + span + SLOT_MINUTES * 60 + TAIL_SECONDS)

    @property
    def record_end(self) -> datetime:
        return self.record_start + timedelta(seconds=self.tlimit)

    @property
    def label(self) -> str:
        return "".join(s.id for s in self.stations)


def cycle_slots(stations: list[Station], cycle_base: datetime) -> dict[str, datetime]:
    """Slot start of every station within the 4 h cycle starting at ``cycle_base`` (UTC)."""
    return {
        s.id: cycle_base + timedelta(hours=s.first_hour % SLOT_PERIOD_H, minutes=s.minute)
        for s in stations
    }


def plan_window(stations: list[Station], now: datetime) -> Window:
    """Earliest upcoming 4 h cycle in which *all* requested stations still lie ahead.

    Every station repeats every 4 h, so a block like H/I/J (10 min apart) is one
    continuous recording. If ``now`` falls inside a block that already started, the
    whole block moves to the next cycle — a partial block is not worth a file.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(UTC)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for k in range(2 * 24 // SLOT_PERIOD_H):
        slots = cycle_slots(stations, day + timedelta(hours=SLOT_PERIOD_H * k))
        if min(slots.values()) >= now:
            ordered = sorted(stations, key=lambda s: slots[s.id])
            return Window(tuple(ordered), slots[ordered[0].id], slots[ordered[-1].id])
    raise RuntimeError("no upcoming cycle found")  # unreachable: 48 h of cycles scanned


def filename(window: Window, kiwi_label: str | None = None) -> str:
    """``navtex_<stations>_<YYYYmmdd_HHMM>`` (UTC slot time), optional Kiwi suffix."""
    base = f"navtex_{window.label}_{window.first_slot.strftime('%Y%m%d_%H%M')}"
    return f"{base}_{kiwi_label}" if kiwi_label else base


@dataclass(frozen=True)
class Kiwi:
    host: str
    port: int = 8073

    @property
    def label(self) -> str:
        return self.host.split(".")[0].replace("-", "")


def parse_kiwi_arg(arg: str) -> list[Kiwi]:
    kiwis: list[Kiwi] = []
    for item in arg.split(","):
        item = item.strip()
        if not item:
            continue
        host, _, port = item.partition(":")
        kiwis.append(Kiwi(host, int(port) if port else 8073))
    if not kiwis:
        raise argparse.ArgumentTypeError("at least one Kiwi host required")
    return kiwis


def build_command(
    window: Window,
    kiwis: list[Kiwi],
    mode: str,
    out_dir: Path,
    python: str = sys.executable,
    kiwirecorder: Path = KIWIRECORDER,
    user: str = "falochron",
) -> list[str]:
    """kiwirecorder command line; multi-Kiwi uses its native comma-separated lists."""
    multi = len(kiwis) > 1
    names = [filename(window, k.label if multi else None) for k in kiwis]
    cmd = [
        python,
        str(kiwirecorder),
        "-s",
        ",".join(k.host for k in kiwis),
        "-p",
        ",".join(str(k.port) for k in kiwis),
        "-u",
        ",".join([user] * len(kiwis)),
        "--fn",
        ",".join(names),
        "-d",
        str(out_dir),
        "--tlimit",
        str(window.tlimit),
        "--log",
        "info",
    ]
    if mode == "iq":
        cmd += ["-f", f"{FREQ_IQ_KHZ:g}", "-m", "iq", "--kiwi-wav"]
    elif mode == "usb":
        cmd += ["-f", f"{FREQ_USB_KHZ:g}", "-m", "usb"]
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return cmd


def fmt(dt: datetime) -> str:
    local = dt.astimezone(LOCAL_TZ)
    return f"{dt.astimezone(UTC):%Y-%m-%d %H:%M}Z ({local:%H:%M} {local.tzname()})"


def print_table(now: datetime) -> None:
    print("Baltic 518 kHz NAVTEX slots (PRD Annex A.1)\n")
    print(f"{'ID':<3}{'Station':<16}{'Slots UTC':<38}{'Next slot'}")
    for s in STATIONS.values():
        nxt = next_slot(s, now)
        label = f"{s.name} ({s.country})"
        print(f"{s.id:<3}{label:<16}{' '.join(s.slots_utc()):<38}{fmt(nxt)}")
    print(f"\nnow: {fmt(now)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--station",
        type=parse_station_arg,
        default=None,
        help="station id(s): H, I, J, U or a block like HIJ (default: --list)",
    )
    ap.add_argument(
        "--kiwi",
        type=parse_kiwi_arg,
        default=None,
        help="comma-separated KiwiSDR host[:port] list (records from all in parallel)",
    )
    ap.add_argument(
        "--mode",
        choices=("iq", "usb"),
        default="iq",
        help="iq: 518 kHz IQ wav with KIWI header (default); usb: 516.8 kHz audio",
    )
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument(
        "--now",
        action="store_true",
        help="start immediately instead of waiting for the slot (still uses slot naming)",
    )
    ap.add_argument(
        "--at",
        default=None,
        help="pretend the current time is this ISO timestamp (testing / planning)",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="print schedule and command, do not record"
    )
    ap.add_argument("--list", action="store_true", help="print the slot table and exit")
    args = ap.parse_args(argv)

    now = datetime.fromisoformat(args.at) if args.at else datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    if args.list or args.station is None:
        print_table(now)
        return 0
    if args.kiwi is None:
        ap.error("--kiwi is required to record (use --list to only show slots)")

    window = plan_window(args.station, now)
    cmd = build_command(window, args.kiwi, args.mode, args.out_dir)

    print(f"stations : {', '.join(f'{s.id} {s.name}' for s in window.stations)}")
    print(f"slot(s)  : {fmt(window.first_slot)} .. {fmt(window.last_slot)} (+{SLOT_MINUTES} min)")
    print(
        f"recording: {fmt(window.record_start)} for {window.tlimit} s -> {fmt(window.record_end)}"
    )
    print(f"kiwis    : {', '.join(f'{k.host}:{k.port}' for k in args.kiwi)}")
    print(f"files    : {args.out_dir}/{filename(window)}*.wav")
    print("command  : " + " ".join(cmd))

    if args.dry_run:
        return 0
    if not KIWIRECORDER.exists():
        print(f"error: {KIWIRECORDER} missing — run `git submodule update --init`", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.now:
        wait = (window.record_start - datetime.now(UTC)).total_seconds()
        if wait > 0:
            print(f"waiting {int(wait)} s until {fmt(window.record_start)} ...")
            time.sleep(wait)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
