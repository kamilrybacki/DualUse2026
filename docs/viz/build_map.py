#!/usr/bin/env python3
"""Build a self-contained interactive Baltic chart of the FALOCHRON concept."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
land = json.loads((HERE / "baltic_land.json").read_text())
ev = json.loads(Path("/tmp/events.json").read_text())

# NAVTEX transmitters (lon, lat)
stations = [
    {"id": "H", "name": "Bjuröklubb", "cc": "SE", "lon": 21.58, "lat": 64.46},
    {"id": "I", "name": "Grimeton", "cc": "SE", "lon": 12.72, "lat": 57.10},
    {"id": "J", "name": "Gislövshammar", "cc": "SE", "lon": 14.32, "lat": 55.48},
    {"id": "U", "name": "Tallinn", "cc": "EE", "lon": 24.80, "lat": 59.43},
]

# channel per event: SDR = NAVTEX 518 radio, TEXT = BHMW text, VOICE = VHF
CH = {"01": "SDR", "02": "SDR", "04": "TEXT", "05": "TEXT", "06": "VOICE", "07": "VOICE", "10": "TEXT"}


def pt(g):
    if not g:
        return None
    if g["type"] == "Point":
        return g["coordinates"]
    if g["type"] == "Polygon":
        ring = g["coordinates"][0]
        return [sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)]
    return None


events = []
for n, v in ev.items():
    p = pt(v["geom"])
    if not p:
        continue
    events.append({
        "n": n, "ch": CH.get(n, "TEXT"), "type": v["type"], "loc": v["loc"] or "—",
        "wid": v["wid"], "agency": v["agency"], "issued": v["issued"], "valid_to": v["valid_to"],
        "lon": p[0], "lat": p[1], "src": v["src"], "entities": v["entities"] or [],
        "poly": v["geom"]["coordinates"][0] if v["geom"]["type"] == "Polygon" else None,
    })

# the demo correlation: BHMW cable-works (04) <-> VHF drifting vessel (06)
corr = ["04", "06"]

DATA = {"land": land, "stations": stations, "events": events, "corr": corr}
payload = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

TEMPLATE = (HERE / "template.html").read_text(encoding="utf-8")
html = TEMPLATE.replace("/*__DATA__*/", "const DATA = " + payload + ";")
(HERE / "falochron_baltic.html").write_text(html, encoding="utf-8")
print("wrote falochron_baltic.html", len(html) // 1024, "KB;", len(events), "events")
