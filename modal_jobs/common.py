"""Shared Modal app, image, volume and secrets for the FALOCHRON data factory (PRD §12.5).

Modal never touches the demo's critical path: every artifact produced here is mirrored to
the local cache with ``modal volume get`` and lives on the USB stick.

Secrets (create once in the Modal dashboard or CLI, see README.md):
    huggingface   HF_TOKEN=hf_...   (gated models, dataset access)
"""

from __future__ import annotations

from pathlib import Path

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "falochron"
VOLUME_NAME = "falochron-artifacts"
VOL = "/vol"  # mount point inside containers

app = modal.App(APP_NAME)
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
hf_secret = modal.Secret.from_name("huggingface")

# Base image: CPU tooling shared by every job. GPU-specific packages are layered per job.
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "jsonschema>=4.23",
        "pyyaml>=6.0",
        "numpy>=1.26",
        "huggingface_hub>=0.25",
    )
    # repo pieces the jobs need at runtime; kept small and read-only
    .add_local_dir(str(REPO_ROOT / "schemas"), remote_path="/repo/schemas")
    .add_local_dir(str(REPO_ROOT / "prompts"), remote_path="/repo/prompts")
    .add_local_dir(str(REPO_ROOT / "bench"), remote_path="/repo/bench")
    .add_local_dir(str(REPO_ROOT / "data" / "gold" / "seeds"), remote_path="/repo/data/gold/seeds")
    .add_local_file(str(REPO_ROOT / "cache" / "models.yaml"), remote_path="/repo/cache/models.yaml")
)


def vol_path(*parts: str) -> str:
    return "/".join([VOL, *parts])


def mirror_hint(remote_dir: str, local_dir: str) -> str:
    """Command the user runs to pull artifacts to the local cache (printed by every job)."""
    return f"modal volume get {VOLUME_NAME} {remote_dir} {local_dir}"
