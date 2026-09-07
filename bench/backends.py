"""Model backends for the benchmark runner. Only llama.cpp (CLI or server) and a fake.

All backends take a fully rendered prompt and a GBNF grammar and return the raw text the
model produced plus wall-clock latency. Nothing here parses or validates — that is metrics.py.
"""

from __future__ import annotations

import json
import resource
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Completion:
    text: str
    latency_s: float
    error: str | None = None


class FakeBackend:
    """Deterministic stand-in so the harness runs offline without a model.

    ``mode``: 'gold' echoes the expected label (perfect model), 'null' answers every field
    with null/UNKNOWN (abstaining model), 'noisy' copies gold but hallucinates a warning id
    and drops entities (exercises the unsupported/omission metrics).
    """

    name = "fake"

    def __init__(self, mode: str = "gold"):
        self.mode = mode

    def complete(self, prompt: str, grammar: str, gold: dict | None = None) -> Completion:
        t0 = time.perf_counter()
        if self.mode == "null" or gold is None:
            out = {
                "event_type": "UNKNOWN",
                "warning_id": None,
                "agency": None,
                "issued_at": None,
                "valid_from": None,
                "valid_to": None,
                "location_name": None,
                "geometry": None,
                "entities": [],
            }
        elif self.mode == "noisy":
            out = dict(gold, warning_id="XX99", entities=[])
        else:
            out = dict(gold)
        return Completion(json.dumps(out, ensure_ascii=False), time.perf_counter() - t0)


class LlamaCliBackend:
    """Runs ``llama-cli`` per item with --grammar-file. Simple; pays model load every call,
    so latency here is *not* the pipeline latency — use the server backend for that."""

    name = "llama-cli"

    def __init__(
        self,
        model: Path,
        binary: str = "llama-cli",
        n_predict: int = 512,
        threads: int | None = None,
        ctx: int = 4096,
    ):
        self.model = Path(model)
        self.binary = shutil.which(binary) or binary
        self.n_predict = n_predict
        self.threads = threads
        self.ctx = ctx
        self._grammar_file: Path | None = None

    def _grammar_path(self, grammar: str) -> Path:
        if self._grammar_file is None:
            p = Path.cwd() / ".bench_grammar.gbnf"
            p.write_text(grammar, encoding="utf-8")
            self._grammar_file = p
        return self._grammar_file

    def complete(self, prompt: str, grammar: str, gold: dict | None = None) -> Completion:
        cmd = [
            self.binary,
            "-m",
            str(self.model),
            "--grammar-file",
            str(self._grammar_path(grammar)),
            "-p",
            prompt,
            "-n",
            str(self.n_predict),
            "--temp",
            "0",
            "-c",
            str(self.ctx),
            "--no-display-prompt",
            "-no-cnv",
            "--simple-io",
        ]
        if self.threads:
            cmd += ["-t", str(self.threads)]
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return Completion("", time.perf_counter() - t0, error=f"{type(exc).__name__}: {exc}")
        dt = time.perf_counter() - t0
        if proc.returncode != 0:
            return Completion(proc.stdout, dt, error=proc.stderr.strip()[-500:])
        return Completion(proc.stdout.strip(), dt)


class LlamaServerBackend:
    """Talks to a running ``llama-server`` (/completion) — model stays loaded, latency is real."""

    name = "llama-server"

    def __init__(self, url: str = "http://127.0.0.1:8080", n_predict: int = 512):
        self.url = url.rstrip("/")
        self.n_predict = n_predict

    def complete(self, prompt: str, grammar: str, gold: dict | None = None) -> Completion:
        body = json.dumps(
            {
                "prompt": prompt,
                "grammar": grammar,
                "n_predict": self.n_predict,
                "temperature": 0,
                "cache_prompt": True,
                "stream": False,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.url}/completion", data=body, headers={"Content-Type": "application/json"}
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:  # noqa: S310 — localhost
                data = json.loads(resp.read())
        except Exception as exc:  # noqa: BLE001
            return Completion("", time.perf_counter() - t0, error=f"{type(exc).__name__}: {exc}")
        return Completion(str(data.get("content", "")).strip(), time.perf_counter() - t0)


def peak_rss_children_mb() -> float:
    """Peak RSS of child processes (llama-cli runs), MB. Linux reports KB, macOS bytes."""
    ru = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    import sys

    return ru / 1e6 if sys.platform == "darwin" else ru / 1e3


def make_backend(name: str, model: Path | None, server_url: str, fake_mode: str):
    if name == "fake":
        return FakeBackend(fake_mode)
    if name == "llama-cli":
        if model is None:
            raise SystemExit("--model is required for llama-cli")
        return LlamaCliBackend(model)
    if name == "llama-server":
        return LlamaServerBackend(server_url)
    raise SystemExit(f"unknown backend {name}")
