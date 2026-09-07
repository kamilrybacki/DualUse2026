#!/usr/bin/env python3
"""Build the Baltic gazetteer (names → coordinates) from OpenStreetMap via Overpass, plus a
small curated list of sea areas (PRD F6, CLAUDE.md P2.11). Output: data/gazetteer.sqlite.

Network allowed here (tools/download_*.py). The raw Overpass answer is cached in
cache/gazetteer_overpass.json so the database can be rebuilt offline (``--from-cache``).

    uv run python tools/download_gazetteer.py                 # query Overpass, build sqlite
    uv run python tools/download_gazetteer.py --from-cache    # rebuild without network
    uv run python tools/download_gazetteer.py --lookup "NIDINGEN"

Data: © OpenStreetMap contributors, ODbL 1.0 — attribution kept in the database.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import unicodedata
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_JSON = REPO_ROOT / "cache" / "gazetteer_overpass.json"
SEED_CSV = REPO_ROOT / "data" / "gazetteer_seed.csv"
DB_PATH = REPO_ROOT / "data" / "gazetteer.sqlite"

# lat_min, lon_min, lat_max, lon_max (Overpass order) — Baltic incl. Kattegat/Skagerrak
BBOX = (53.0, 9.0, 66.5, 31.0)

SEAMARK_KINDS = (
    "light_major",
    "light_minor",
    "landmark",
    "buoy_lateral",
    "buoy_cardinal",
    "buoy_safe_water",
    "buoy_isolated_danger",
    "buoy_special_purpose",
    "beacon_lateral",
    "beacon_cardinal",
    "beacon_special_purpose",
    "harbour",
    "wreck",
    "platform",
    "cable_submarine",
)

QUERY = """
[out:json][timeout:300];
(
  nwr["seamark:type"~"^({kinds})$"]["seamark:name"]({bbox});
  nwr["seamark:type"~"^({kinds})$"]["name"]({bbox});
  node["place"~"^(city|town|village)$"]["name"]({bbox})(if: t["population"] > 2000);
  nwr["natural"~"^(bay|strait|cape|shoal|reef)$"]["name"]({bbox});
  nwr["harbour"="yes"]["name"]({bbox});
);
out center tags;
"""


def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def match_key(name: str) -> str:
    """Uppercase, ASCII-folded, punctuation-free key used for lookups."""
    s = strip_diacritics(name).upper()
    s = "".join(ch if ch.isalnum() or ch == " " else " " for ch in s)
    return " ".join(s.split())


def alt_keys(names) -> str:
    """'|'-delimited match keys of alternative names, padded so LIKE '%|X|%' is exact."""
    keys = sorted({match_key(n) for n in names if n and match_key(n)})
    return "|" + "|".join(keys) + "|" if keys else ""


def kind_of(tags: dict) -> str:
    if "seamark:type" in tags:
        return tags["seamark:type"]
    if "place" in tags:
        return "place_" + tags["place"]
    if "natural" in tags:
        return "natural_" + tags["natural"]
    if tags.get("harbour") == "yes":
        return "harbour"
    return "other"


def rows_from_overpass(data: dict) -> list[dict]:
    rows = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("seamark:name") or tags.get("name")
        if not name:
            continue
        if "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        alts = {
            v
            for k, v in tags.items()
            if k
            in (
                "name:en",
                "name:pl",
                "name:sv",
                "name:de",
                "name:fi",
                "name:et",
                "alt_name",
                "int_name",
            )
        }
        rows.append(
            {
                "name": name,
                "key": match_key(name),
                "alt_names": "|".join(sorted(alts)),
                "alt_keys": alt_keys(alts),
                "kind": kind_of(tags),
                "lat": float(lat),
                "lon": float(lon),
                "source": f"osm:{el['type']}/{el['id']}",
                "light_character": tags.get("seamark:light:character", ""),
            }
        )
    return rows


def rows_from_seed(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [
            {
                "name": r["name"],
                "key": match_key(r["name"]),
                "alt_names": r.get("alt_names", ""),
                "alt_keys": alt_keys(r.get("alt_names", "").split("|")),
                "kind": r["kind"],
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "source": r.get("source", "curated"),
                "light_character": "",
            }
            for r in csv.DictReader(f)
        ]


def build_db(rows: list[dict], db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE gazetteer (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, key TEXT NOT NULL, alt_names TEXT,
          alt_keys TEXT, kind TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
          source TEXT NOT NULL,
          light_character TEXT
        );
        CREATE INDEX idx_key ON gazetteer(key);
        CREATE INDEX idx_kind ON gazetteer(kind);
        CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
        """
    )
    con.executemany(
        "INSERT INTO gazetteer(name,key,alt_names,alt_keys,kind,lat,lon,source,light_character) "
        "VALUES (:name,:key,:alt_names,:alt_keys,:kind,:lat,:lon,:source,:light_character)",
        rows,
    )
    con.execute(
        "INSERT INTO meta VALUES ('attribution', "
        "'© OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright); "
        "sea areas curated for FALOCHRON')"
    )
    con.execute("INSERT INTO meta VALUES ('bbox', ?)", (json.dumps(BBOX),))
    con.commit()
    n = con.execute("SELECT count(*) FROM gazetteer").fetchone()[0]
    con.close()
    return n


def lookup(db_path: Path, name: str, limit: int = 5) -> list[tuple]:
    """Test helper for eyeballing the data — not the F6 geocoder."""
    con = sqlite3.connect(db_path)
    key = match_key(name)
    rows = con.execute(
        "SELECT name, kind, lat, lon, source FROM gazetteer "
        "WHERE key = ? OR alt_keys LIKE ? OR key LIKE ? "
        "ORDER BY (key = ? OR alt_keys LIKE ?) DESC, length(key) LIMIT ?",
        (key, f"%|{key}|%", f"%{key}%", key, f"%|{key}|%", limit),
    ).fetchall()
    con.close()
    return rows


def fetch_overpass() -> dict:
    q = QUERY.format(kinds="|".join(SEAMARK_KINDS), bbox=",".join(str(x) for x in BBOX))
    req = urllib.request.Request(OVERPASS_URL, data=q.encode("utf-8"), method="POST")
    with urllib.request.urlopen(req, timeout=600) as resp:  # noqa: S310
        return json.load(resp)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--from-cache", action="store_true", help="rebuild from cache JSON, no network")
    ap.add_argument("--db", type=Path, default=DB_PATH)
    ap.add_argument("--lookup", help="query the built database and exit")
    args = ap.parse_args(argv)

    if args.lookup:
        for r in lookup(args.db, args.lookup):
            print(r)
        return 0
    if args.from_cache:
        if not CACHE_JSON.exists():
            sys.exit(f"{CACHE_JSON} missing — run without --from-cache first")
        data = json.loads(CACHE_JSON.read_text(encoding="utf-8"))
    else:
        data = fetch_overpass()
        CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)
        CACHE_JSON.write_text(json.dumps(data), encoding="utf-8")
    rows = rows_from_overpass(data) + rows_from_seed(SEED_CSV)
    n = build_db(rows, args.db)
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"{n} entries → {args.db}")
    for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<24}{v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
