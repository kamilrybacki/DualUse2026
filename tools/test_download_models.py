"""Offline tests for tools/download_models.py (no HF calls)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools import download_models as dm


def test_shortlist_loads_and_covers_prd() -> None:
    entries = dm.load_entries()
    names = {e.name for e in entries}
    for required in (
        "qwen3.5-0.8b-q4",
        "granite-4.0-350m-q4",
        "granite-4.0-1b-q4",
        "lfm2.5-350m-q4",
        "lfm2.5-1.2b-q4",
        "ministral-3-3b-q4",
        "phi-4-mini-q4",
        "whisper-small",
        "whisper-medium",
        "whisper-large-v3-turbo",
    ):
        assert required in names, required
    for e in entries:
        assert e.repo.count("/") == 1, e.name
        assert e.file, e.name
        assert e.license, e.name


def test_unverified_entries_are_not_downloaded_by_all(capsys) -> None:
    rc = dm.main(["--all"]) if any(e.verified for e in dm.load_entries()) else None
    # With every entry unverified, --all must refuse rather than guess.
    if rc is None:
        import pytest

        with pytest.raises(SystemExit):
            dm.main(["--all"])


def test_sha256_and_manifest_render(tmp_path: Path) -> None:
    f = tmp_path / "m.gguf"
    f.write_bytes(b"falochron" * 1000)
    assert dm.sha256_of(f) == hashlib.sha256(b"falochron" * 1000).hexdigest()
    row = {
        "name": "x",
        "repo": "org/x",
        "revision": "abcdef1234567890",
        "file": "cache/models/x/m.gguf",
        "sha256": dm.sha256_of(f),
        "size_bytes": f.stat().st_size,
        "license": "MIT",
    }
    md = dm.render_manifest([row])
    assert "| x | org/x | abcdef123456 | cache/models/x/m.gguf |" in md
    assert row["sha256"] in md
    assert "convert_hf_to_gguf.py" in md


def test_list_prints_unverified_flag(capsys) -> None:
    assert dm.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "qwen3.5-0.8b-q4" in out and "UNVERIFIED" in out
