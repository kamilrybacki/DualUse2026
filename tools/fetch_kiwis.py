#!/usr/bin/env python3
"""Pick KiwiSDR receivers around the Baltic for 518 kHz recording.

Network allowed (tools/fetch_*.py). Parses the public receiver list (kiwisdr.com/public),
keeps receivers inside a Baltic bounding box with free channels, ranks them by distance to
the target station, and optionally measures SNR on 518 kHz with kiwirecorder ``--snr``.

    uv run python tools/fetch_kiwis.py --station J --top 5
    uv run python tools/fetch_kiwis.py --station U --top 3 --snr     # ~20 s per candidate
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_URL = "http://kiwisdr.com/public/"
KIWIRECORDER = REPO_ROOT / "tools" / "vendor" / "kiwiclient" / "kiwirecorder.py"

# lon_min, lat_min, lon_max, lat_max — Baltic rim incl. Skagerrak/Kattegat and S Finland
BALTIC_BBOX = (7.0, 53.0, 31.0, 66.5)

# Approximate transmitter positions (deg) for ranking receivers by distance.
STATION_POS = {
    "H": (21.58, 64.46),  # Bjuröklubb
    "I": (12.72, 57.10),  # Grimeton
    "J": (14.32, 55.48),  # Gislövshammar
    "U": (24.75, 59.44),  # Tallinn
}


@dataclass
class Kiwi:
    host: str
    port: int
    name: str
    lat: float
    lon: float
    users: int
    users_max: int
    antenna: str
    tlimit: str
    distance_km: float = 0.0
    snr_db: float | None = None

    @property
    def free(self) -> bool:
        return self.users < self.users_max


ENTRY_RE = re.compile(r"<div class=['\"]cl-entry['\"].*?</div>\s*</div>", re.S)
KV_RE = re.compile(r"<!--\s*([a-z_]+)\s*=\s*(.*?)\s*-->", re.S)
URL_RE = re.compile(r"href=['\"]http://([^:'\"/]+):(\d+)")


def parse_public_list(page: str) -> list[Kiwi]:
    """Tolerant parser: each entry carries HTML comments like <!-- gps=(59.4, 24.7) -->."""
    out: list[Kiwi] = []
    for block in ENTRY_RE.findall(page) or page.split("cl-entry")[1:]:
        kv = {k: html.unescape(v) for k, v in KV_RE.findall(block)}
        m = URL_RE.search(block)
        if not m or "gps" not in kv:
            continue
        g = re.findall(r"-?\d+(?:\.\d+)?", kv["gps"])
        if len(g) < 2:
            continue
        try:
            out.append(
                Kiwi(
                    host=m.group(1),
                    port=int(m.group(2)),
                    name=kv.get("name", m.group(1))[:60],
                    lat=float(g[0]),
                    lon=float(g[1]),
                    users=int(kv.get("users", "0") or 0),
                    users_max=int(kv.get("users_max", "0") or 0),
                    antenna=kv.get("antenna", "")[:80],
                    tlimit=kv.get("tlimit", ""),
                )
            )
        except ValueError:
            continue
    return out


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def rank(
    kiwis: list[Kiwi], station: str, bbox=BALTIC_BBOX, require_free: bool = True
) -> list[Kiwi]:
    tx = STATION_POS[station]
    lon0, lat0, lon1, lat1 = bbox
    picked = []
    for k in kiwis:
        if not (lon0 <= k.lon <= lon1 and lat0 <= k.lat <= lat1):
            continue
        if require_free and not k.free:
            continue
        k.distance_km = round(haversine_km((k.lon, k.lat), tx), 1)
        picked.append(k)

    # prefer receivers that advertise LF/loop/whip antennas, then distance
    def key(k: Kiwi):
        ant = k.antenna.lower()
        bonus = 0 if any(w in ant for w in ("loop", "whip", "lf", "mw", "long")) else 200
        return k.distance_km + bonus

    return sorted(picked, key=key)


def fetch_public() -> str:
    import urllib.request

    with urllib.request.urlopen(PUBLIC_URL, timeout=30) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def measure_snr(k: Kiwi, seconds: int = 20) -> float | None:
    """Run kiwirecorder --snr and parse the last SNR it prints. None on failure."""
    cmd = [
        sys.executable,
        str(KIWIRECORDER),
        "-s",
        k.host,
        "-p",
        str(k.port),
        "-f",
        "518",
        "-m",
        "iq",
        "--snr",
        "5",
        "--tlimit",
        str(seconds),
        "--log",
        "info",
        "-u",
        "falochron-snr",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=seconds + 40)
    except (OSError, subprocess.TimeoutExpired):
        return None
    vals = re.findall(r"SNR[^0-9-]*(-?\d+(?:\.\d+)?)", proc.stdout + proc.stderr)
    return float(vals[-1]) if vals else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--station", choices=sorted(STATION_POS), default="J")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--snr", action="store_true", help="measure SNR on the top candidates")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a table")
    ap.add_argument("--page", type=Path, help="parse a saved copy of kiwisdr.com/public (offline)")
    args = ap.parse_args(argv)

    page = args.page.read_text(encoding="utf-8") if args.page else fetch_public()
    kiwis = rank(parse_public_list(page), args.station)[: args.top]
    if args.snr:
        for k in kiwis:
            k.snr_db = measure_snr(k)
        kiwis.sort(key=lambda k: -(k.snr_db if k.snr_db is not None else -999))
    if args.json:
        print(json.dumps([asdict(k) for k in kiwis], indent=2))
        return 0
    print(f"{'host:port':<34}{'km→' + args.station:<8}{'users':<8}{'snr':<7}antenna")
    for k in kiwis:
        snr = f"{k.snr_db:.0f}" if k.snr_db is not None else "-"
        hostport = f"{k.host}:{k.port}"
        users = f"{k.users}/{k.users_max}"
        print(f"{hostport:<34}{k.distance_km:<8.0f}{users:<8}{snr:<7}{k.antenna[:50]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
