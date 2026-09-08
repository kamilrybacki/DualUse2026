"""Shared Modal app, image, volume and secrets for the FALOCHRON data factory (PRD §12.5).

Modal never touches the demo's critical path: every artifact produced here is mirrored to
the local cache with ``modal volume get`` and lives on the USB stick.

Run jobs as a package so ``modal_jobs`` is importable both locally and in the container:

    uv run modal run -m modal_jobs.datagen
    uv run modal run --detach -m modal_jobs.record --station HIJ

Secrets (create once in the Modal dashboard or CLI, see README.md):
    huggingface   HF_TOKEN=hf_...   (gated models, dataset access, higher rate limits)

Modal 1.x rule: ``add_local_*`` layers must be the LAST layers of an image — build steps
(pip_install, apt_install, run_commands) after them raise InvalidError. So ``base_image``
is dependencies only and every job finishes its image with ``with_repo(...)``.
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

# Dependencies only — no add_local_* here (see module docstring).
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "jsonschema>=4.23",
        "pyyaml>=6.0",
        "numpy>=1.26",
        "huggingface_hub>=0.25",
    )
)


def with_repo(image: modal.Image, extra_dirs: dict[str, str] | None = None) -> modal.Image:
    """Attach the repo pieces jobs need at runtime. MUST be the last call on an image.

    ``modal_jobs`` and ``bench`` are added as Python sources (importable from /root, on
    PYTHONPATH); schemas, prompts, seeds and the model list land under /repo.
    """
    img = (
        image.add_local_dir(str(REPO_ROOT / "schemas"), remote_path="/repo/schemas")
        .add_local_dir(str(REPO_ROOT / "prompts"), remote_path="/repo/prompts")
        .add_local_dir(
            str(REPO_ROOT / "data" / "gold" / "seeds"), remote_path="/repo/data/gold/seeds"
        )
        .add_local_file(
            str(REPO_ROOT / "cache" / "models.yaml"), remote_path="/repo/cache/models.yaml"
        )
    )
    for local, remote in (extra_dirs or {}).items():
        img = img.add_local_dir(str(REPO_ROOT / local), remote_path=remote)
    return img.add_local_python_source("modal_jobs", "bench")


def vol_path(*parts: str) -> str:
    return "/".join([VOL, *parts])


def mirror_hint(remote_dir: str, local_dir: str) -> str:
    """Command the user runs to pull artifacts to the local cache (printed by every job)."""
    return f"modal volume get {VOLUME_NAME} {remote_dir} {local_dir}"


def strip_front_matter(text: str) -> str:
    """Drop the YAML front matter of a prompts/*.md file (same rule as bench.run_bench)."""
    if text.startswith("---"):
        parts = text.split("---\n", 2)
        return parts[2] if len(parts) == 3 else text
    return text
