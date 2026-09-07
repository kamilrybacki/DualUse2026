"""Pure helpers for the W1 data generation job — no Modal, no GPU, unit-testable offline.

Builds generation specs from the seed set, renders prompts, parses/validates model output,
and derives '*'-corrupted variants with deterministically adjusted labels.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft7Validator

COORD_RE = re.compile(r"\d{2}-\d{2}(?:\.\d+)?[NS]\s+\d{3}-\d{2}(?:\.\d+)?[EW]")
TIME_GROUP_RE = re.compile(r"\b\d{6}\s+UTC\b")
HEADER_RE = re.compile(r"ZCZC\s+[A-Z]{2}\d{2}")

KINDS = {
    # kind: (lang, channel, event types to cover, style hint)
    "navtex_en": (
        "en",
        "TEXT",
        ["NAV_WARNING", "MET_WARNING", "EXERCISE", "WRECK", "OBSTRUCTION", "INFRA_DAMAGE"],
        "NAVTEX 518 kHz, NAVAREA I Baltic style",
    ),
    "bhmw_pl": (
        "pl",
        "TEXT",
        ["NAV_WARNING", "WRECK", "OBSTRUCTION", "INFRA_DAMAGE", "EXERCISE"],
        "BHMW ostrzeżenie nawigacyjne, polskie wody",
    ),
    "vhf_pl": ("pl", "VOICE", ["VOICE_REPORT"], "transkrypt ASR meldunku VHF po polsku, SMCP"),
    "vhf_en": ("en", "VOICE", ["VOICE_REPORT"], "ASR transcript of an English VHF report, SMCP"),
}


@dataclass
class Spec:
    kind: str
    lang: str
    channel: str
    event_type: str
    style: str
    seed_ids: list[str] = field(default_factory=list)
    few_shot: list[dict] = field(default_factory=list)
    n: int = 5

    @property
    def id(self) -> str:
        return f"{self.kind}_{self.event_type.lower()}"


def load_seeds(seeds_dir: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(seeds_dir.glob("*.json"))]


def build_specs(
    seeds: list[dict],
    per_type: int,
    kinds: list[str] | None = None,
    max_few_shot: int = 3,
    rng_seed: int = 0,
) -> list[Spec]:
    rng = random.Random(rng_seed)
    specs: list[Spec] = []
    for kind, (lang, channel, types, style) in KINDS.items():
        if kinds and kind not in kinds:
            continue
        pool = [
            s for s in seeds if s.get("lang", "en") == lang and s.get("channel", "TEXT") == channel
        ]
        for et in types:
            shots = rng.sample(pool, min(max_few_shot, len(pool))) if pool else []
            specs.append(
                Spec(kind, lang, channel, et, style, [s["id"] for s in shots], shots, per_type)
            )
    return specs


def render_prompt(template: str, spec: Spec, schema: dict) -> str:
    shots = "\n\n".join(f"<<<\n{s['text'].strip()}\n>>>" for s in spec.few_shot) or "(none)"
    return (
        template.replace("{kind}", spec.kind)
        .replace("{lang}", spec.lang)
        .replace("{channel}", spec.channel)
        .replace("{event_type}", spec.event_type)
        .replace("{style}", spec.style)
        .replace("{n}", str(spec.n))
        .replace("{few_shot}", shots)
        .replace("{schema}", json.dumps(schema, ensure_ascii=False))
    )


def output_schema(extraction_schema: dict) -> dict:
    """Wrapper the generator must emit: a list of {source_text, expected}."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["source_text", "expected"],
                    "properties": {
                        "source_text": {"type": "string", "minLength": 20},
                        "expected": {k: v for k, v in extraction_schema.items() if k != "$schema"},
                    },
                },
            }
        },
    }


def parse_items(raw: str, spec: Spec, validator: Draft7Validator, run_id: str) -> list[dict]:
    """Model text → validated items with ids and provenance. Invalid ones are dropped."""
    raw = raw.strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return []
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for it in obj.get("items", []):
        text, exp = it.get("source_text"), it.get("expected")
        if not isinstance(text, str) or not validator.is_valid(exp):
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
        out.append(
            {
                "id": f"{run_id}_{spec.id}_{digest}",
                "kind": spec.kind,
                "lang": spec.lang,
                "channel": spec.channel,
                "source_text": text.strip(),
                "expected": exp,
                "seed_ids": spec.seed_ids,
                "generator": None,  # filled by the job with the model id
            }
        )
    return out


def corrupt_stars(item: dict, rate: float, seed: int) -> dict:
    """'*'-corrupted SDR variant with labels adjusted deterministically:
    a '*' inside the header kills warning_id, inside a time group kills the timestamps,
    inside any coordinate kills geometry. Everything else keeps its label."""
    rng = random.Random(seed)
    text = item["source_text"]
    chars = list(text)
    protected = set()  # never corrupt newlines
    for i, ch in enumerate(chars):
        if ch == "\n":
            protected.add(i)
    hit = set()
    for i in range(len(chars)):
        if i not in protected and chars[i] not in " \n" and rng.random() < rate:
            chars[i] = "*"
            hit.add(i)
    corrupted = "".join(chars)
    exp = dict(item["expected"])

    def span_hit(regex: re.Pattern) -> bool:
        return any(any(m.start() <= i < m.end() for i in hit) for m in regex.finditer(text))

    if span_hit(HEADER_RE):
        exp["warning_id"] = None
    if span_hit(TIME_GROUP_RE):
        exp["issued_at"] = None
        exp["valid_from"] = None
        exp["valid_to"] = None
    if span_hit(COORD_RE):
        exp["geometry"] = None
    # location_name / entities: keep the text but with the stars, as the fixtures do
    for key in ("location_name",):
        if exp.get(key):
            exp[key] = _apply_stars(exp[key], text, corrupted)
    exp["entities"] = [
        dict(e, text=_apply_stars(e["text"], text, corrupted)) for e in exp.get("entities", [])
    ]
    return {
        **item,
        "id": item["id"] + "_stars",
        "channel": "SDR",
        "source_text": corrupted,
        "expected": exp,
        "noisy": True,
        "star_rate": round(len(hit) / max(1, len(text)), 4),
        "derived_from": item["id"],
    }


def _apply_stars(value: str, clean: str, corrupted: str) -> str:
    """If ``value`` occurs verbatim in the clean text, return the same span from the
    corrupted text (so labels stay verbatim copies of what the model sees)."""
    i = clean.upper().find(value.upper())
    if i < 0:
        return value
    return corrupted[i : i + len(value)]


def judge_prompt(template: str, item: dict) -> str:
    return template.replace("{source_text}", item["source_text"]).replace(
        "{expected}", json.dumps(item["expected"], ensure_ascii=False)
    )


def parse_judge(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw.strip(), re.S)
    if not m:
        return {"verdict": "reject", "issues": ["judge output unparsable"], "corrected": None}
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"verdict": "reject", "issues": ["judge output invalid json"], "corrected": None}
    verdict = str(obj.get("verdict", "reject")).lower()
    return {
        "verdict": "accept" if verdict == "accept" else "reject",
        "issues": [str(x) for x in obj.get("issues", [])],
        "corrected": obj.get("corrected"),
    }
