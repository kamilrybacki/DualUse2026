"""Benchmark metrics for extraction outputs (PRD §13). Pure functions, offline.

Nothing here is pipeline code: these compare a model output with a gold label and with the
source text. The validator that will ship in the product (F5) is written at the event.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft7Validator

WORD_NUMBERS_PL = {
    "zero": 0,
    "jeden": 1,
    "jedna": 1,
    "dwa": 2,
    "dwie": 2,
    "trzy": 3,
    "cztery": 4,
    "pięć": 5,
    "sześć": 6,
    "siedem": 7,
    "osiem": 8,
    "dziewięć": 9,
    "dziesięć": 10,
    "jedenaście": 11,
    "dwanaście": 12,
    "trzynaście": 13,
    "czternaście": 14,
    "piętnaście": 15,
    "szesnaście": 16,
    "siedemnaście": 17,
    "osiemnaście": 18,
    "dziewiętnaście": 19,
    "dwadzieścia": 20,
    "trzydzieści": 30,
    "czterdzieści": 40,
    "pięćdziesiąt": 50,
    "sześćdziesiąt": 60,
}
WORD_NUMBERS_EN = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "niner": 9,
}
COORD_RE = re.compile(r"(\d{2})-(\d{2}(?:\.\d+)?)\s*([NS])\s+(\d{3})-(\d{2}(?:\.\d+)?)\s*([EW])")
NUM_RE = re.compile(r"\d+")


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w*]+", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def dms_to_decimal(deg: str, minutes: str, hemi: str) -> float:
    v = int(deg) + float(minutes) / 60.0
    return -v if hemi in "SW" else v


def coords_in_text(text: str) -> list[tuple[float, float]]:
    """All positions stated in DMS in the text, as (lon, lat)."""
    out = []
    for m in COORD_RE.finditer(text):
        lat = dms_to_decimal(m.group(1), m.group(2), m.group(3))
        lon = dms_to_decimal(m.group(4), m.group(5), m.group(6))
        out.append((lon, lat))
    return out


def spoken_numbers(text: str) -> set[int]:
    """Integers a listener could form from the numbers spoken in the text.

    Covers digit-by-digit reading ("five nine" → 59, "zero two four" → 24), Polish/English
    compound tens ("pięćdziesiąt cztery" → 54) and bare tokens. Used only to check that a
    spoken position is *supported* by the transcript, not to extract it.
    """
    seq: list[int] = []
    for tok in normalize(text).split():
        if tok.isdigit():
            seq.extend(int(ch) for ch in tok) if len(tok) > 2 else seq.append(int(tok))
        elif tok in WORD_NUMBERS_PL:
            seq.append(WORD_NUMBERS_PL[tok])
        elif tok in WORD_NUMBERS_EN:
            seq.append(WORD_NUMBERS_EN[tok])
    out = set(seq)
    for i in range(len(seq)):
        a = seq[i]
        if i + 1 < len(seq):
            b = seq[i + 1]
            if a < 10 and b < 10:
                out.add(a * 10 + b)
                if i + 2 < len(seq) and seq[i + 2] < 10:
                    out.add(a * 100 + b * 10 + seq[i + 2])
            if a >= 20 and a % 10 == 0 and 0 < b < 10:
                out.add(a + b)
    return out


def haversine_nm(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 3440.065 * math.asin(math.sqrt(h))


def geometry_points(geom: dict | None) -> list[tuple[float, float]]:
    if not geom:
        return []
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "Point":
        return [tuple(c)]
    if t == "LineString":
        return [tuple(p) for p in c]
    if t == "Polygon":
        return [tuple(p) for ring in c for p in ring]
    return []


def centroid(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    if not points:
        return None
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def geometry_match(pred: dict | None, gold: dict | None, tol_nm: float) -> float:
    if pred is None and gold is None:
        return 1.0
    if pred is None or gold is None:
        return 0.0
    if pred.get("type") != gold.get("type"):
        return 0.0
    cp, cg = centroid(geometry_points(pred)), centroid(geometry_points(gold))
    if cp is None or cg is None:
        return 0.0
    return 1.0 if haversine_nm(cp, cg) <= tol_nm else 0.0


def entity_f1(pred: list[dict], gold: list[dict]) -> float:
    p = {(e["type"], normalize(e["text"])) for e in pred or []}
    g = {(e["type"], normalize(e["text"])) for e in gold or []}
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    tp = len(p & g)
    prec, rec = tp / len(p), tp / len(g)
    return 0.0 if tp == 0 else 2 * prec * rec / (prec + rec)


def field_score(name: str, pred: Any, gold: Any, tol_nm: float) -> float:
    if name == "geometry":
        return geometry_match(pred, gold, tol_nm)
    if name == "entities":
        return entity_f1(pred, gold)
    if pred is None and gold is None:
        return 1.0
    if pred is None or gold is None:
        return 0.0
    if isinstance(pred, str) and isinstance(gold, str):
        if name in ("location_name",):
            # partial credit: token F1 (names are often longer/shorter, never wrong direction)
            p, g = set(normalize(pred).split()), set(normalize(gold).split())
            if not p or not g:
                return 0.0
            tp = len(p & g)
            return 0.0 if tp == 0 else 2 * tp / (len(p) + len(g))
        return 1.0 if normalize(pred) == normalize(gold) else 0.0
    return 1.0 if pred == gold else 0.0


# --- grounding (unsupported-fact) ----------------------------------------------------------


def value_supported(name: str, value: Any, source: str, tol_nm: float) -> bool:
    """Is this predicted value traceable to the source text? Conservative by design."""
    if value is None or value == "UNKNOWN":
        return True
    src_norm = normalize(source)
    if name == "event_type":
        return True  # classification, not a fact copied from text
    if name == "agency":
        v = str(value).upper()
        if v.startswith("NAVTEX/518/"):
            letter = v.rsplit("/", 1)[-1]
            m = re.search(r"ZCZC\s+([A-Z])", source)
            return bool(m and m.group(1) == letter)
        return v in ("BHMW", "VHF") or normalize(v) in src_norm
    if name in ("issued_at", "valid_from", "valid_to"):
        # day, hour and minute digits must appear somewhere in the source
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", str(value))
        if not m:
            return False
        day, hh, mm = m.group(3), m.group(4), m.group(5)
        return (
            (day + hh + mm in re.sub(r"\D", "", source))
            or (f"{hh}:{mm}" in source and day in source)
            or (f"{hh}{mm}" in source and day in source)
        )
    if name == "geometry":
        pts = geometry_points(value)
        stated = coords_in_text(source)
        if stated:
            return all(any(haversine_nm(p, s) <= tol_nm for s in stated) for p in pts)
        # spoken position: degrees and whole minutes must be formable from the spoken numbers
        spoken = spoken_numbers(source)
        for lon, lat in pts:
            for v in (abs(lat), abs(lon)):
                deg = int(v)
                mins = int(round((v - deg) * 60, 1))
                if deg not in spoken or mins not in spoken:
                    return False
        return True
    if name == "entities":
        for ent in value:
            if ent.get("type") == "CALLSIGN":
                continue  # NATO-alphabet expansion; checked by humans in review
            if normalize(ent["text"]) not in src_norm:
                return False
        return True
    if name == "warning_id":
        return normalize(str(value)) in src_norm
    if isinstance(value, str):
        # free text (location_name): every token must occur in the source, allowing
        # inflection ("pozycja" ~ "pozycji") via a 5-char stem match
        src_toks = src_norm.split()
        toks = normalize(value).split()
        return bool(toks) and all(token_in(t, src_toks) for t in toks)
    return True


def token_in(tok: str, src_toks: list[str]) -> bool:
    if tok in src_toks:
        return True
    if len(tok) < 4:
        return False
    stem = tok[:5]
    return any(s.startswith(stem) or tok.startswith(s[:5]) and len(s) >= 4 for s in src_toks)


# --- per-item evaluation -------------------------------------------------------------------


@dataclass
class ItemResult:
    id: str
    valid: bool
    field_scores: dict[str, float] = field(default_factory=dict)
    unsupported: list[str] = field(default_factory=list)
    omitted: list[str] = field(default_factory=list)
    geo_resolved: bool = False
    triggers: list[str] = field(default_factory=list)
    latency_s: float = 0.0
    error: str | None = None

    @property
    def field_f1(self) -> float:
        return (
            sum(self.field_scores.values()) / len(self.field_scores) if self.field_scores else 0.0
        )


def in_bbox(geom: dict | None, bbox: list[float]) -> bool:
    pts = geometry_points(geom)
    if not pts:
        return True
    return all(bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3] for lon, lat in pts)


def evaluate_item(
    item_id: str,
    pred: dict | None,
    gold: dict,
    source: str,
    validator: Draft7Validator,
    thresholds: dict,
    latency_s: float = 0.0,
    error: str | None = None,
) -> ItemResult:
    fields = thresholds["scored_fields"]
    tol = float(thresholds["tolerances"]["geometry_nm"])
    rules = {r["id"]: r for r in thresholds["escalation_rules"]}
    res = ItemResult(id=item_id, valid=False, latency_s=latency_s, error=error)

    if pred is None or not validator.is_valid(pred):
        res.triggers.append("schema_invalid")
        res.field_scores = {f: 0.0 for f in fields}
        res.omitted = [f for f in fields if gold.get(f) not in (None, [], "UNKNOWN")]
        return res
    res.valid = True

    for f in fields:
        res.field_scores[f] = field_score(f, pred.get(f), gold.get(f), tol)
        if not value_supported(f, pred.get(f), source, tol):
            res.unsupported.append(f)
        gold_has = gold.get(f) not in (None, [], "UNKNOWN")
        pred_has = pred.get(f) not in (None, [], "UNKNOWN")
        if gold_has and not pred_has:
            res.omitted.append(f)

    res.geo_resolved = bool(
        (gold.get("geometry") is not None and res.field_scores.get("geometry", 0) == 1.0)
        or (
            gold.get("geometry") is None
            and gold.get("location_name")
            and res.field_scores.get("location_name", 0) >= 0.5
        )
        or (
            gold.get("geometry") is None
            and gold.get("location_name") is None
            and pred.get("geometry") is None
        )
    )

    if pred.get("event_type") == "UNKNOWN":
        res.triggers.append("type_unknown")
    if pred.get("geometry") is None and pred.get("location_name") is None:
        res.triggers.append("no_location")
    if not in_bbox(pred.get("geometry"), rules["geometry_outside_baltic"]["bbox"]):
        res.triggers.append("geometry_outside_baltic")
    if pred.get("valid_from") and pred.get("valid_to") and pred["valid_to"] < pred["valid_from"]:
        res.triggers.append("time_inconsistent")
    if res.unsupported:
        res.triggers.append("unsupported_fact")
    return res


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def summarize(results: list[ItemResult], thresholds: dict, peak_rss_mb: float | None) -> dict:
    n = len(results) or 1
    fields = thresholds["scored_fields"]
    valid = [r for r in results if r.valid]
    total_values = sum(len(r.field_scores) for r in valid) or 1
    unsupported_values = sum(len(r.unsupported) for r in valid)
    gold_facts = (
        sum(len(r.omitted) + sum(1 for f in fields if f not in r.omitted) for r in results) or 1
    )
    summary = {
        "items": len(results),
        "schema_validity": len(valid) / n,
        "field_f1": sum(r.field_f1 for r in results) / n,
        "per_field_f1": {f: sum(r.field_scores.get(f, 0.0) for r in results) / n for f in fields},
        "unsupported_fact_rate": unsupported_values / total_values,
        "omission_rate": sum(len(r.omitted) for r in results) / gold_facts,
        "geo_resolution": sum(1 for r in results if r.geo_resolved) / n,
        "latency_p50_s": percentile([r.latency_s for r in results], 0.5),
        "latency_p95_s": percentile([r.latency_s for r in results], 0.95),
        "peak_rss_mb": peak_rss_mb,
        "escalation_rate": sum(1 for r in results if r.triggers) / n,
        "trigger_counts": {
            rule["id"]: sum(1 for r in results if rule["id"] in r.triggers)
            for rule in thresholds["escalation_rules"]
        },
    }
    checks = {}
    for metric, limit in thresholds["pass"].items():
        value = summary[metric]
        higher_is_better = metric in ("schema_validity", "field_f1", "geo_resolution")
        if value is None:
            checks[metric] = None
        else:
            checks[metric] = value >= limit if higher_is_better else value <= limit
    summary["checks"] = checks
    summary["pass"] = all(v for v in checks.values() if v is not None)
    return summary
