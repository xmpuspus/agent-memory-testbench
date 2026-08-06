"""Load and verify the historical result snapshot bundled with the package."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _HistoricalManifest(BaseModel):
    """Schema for the only valid manifest type in the bundled v0.1.8 snapshot."""

    model_config = ConfigDict(extra="forbid", strict=True)

    snapshot_id: str
    status: Literal["historical"]
    protocol_id: str
    corpus: str
    question_set: str
    question_count: int = Field(ge=1)
    category_count: int = Field(ge=1)
    included_strategies: list[str] = Field(min_length=1)
    missing_from_v0_1_8_claim: list[str] = Field(alias="missing_from_v0.1.8_claim")
    source_commits: list[str] = Field(min_length=1)
    source_versions: dict[str, list[str]] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)


def _unavailable_manifest(reason: str) -> dict:
    return {"snapshot_id": None, "status": "unavailable", "reason": reason}


def load_bundled_manifest(results_dir: Path) -> dict:
    """Load a bundled snapshot manifest or explicitly report why it is unavailable."""
    manifest_path = results_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except FileNotFoundError:
        return _unavailable_manifest("manifest not found")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _unavailable_manifest("manifest is invalid")

    try:
        return _HistoricalManifest.model_validate(manifest).model_dump(by_alias=True)
    except ValidationError:
        return _unavailable_manifest("manifest is invalid")


def packaged_snapshot_dir() -> Path:
    """The snapshot directory that ships inside the package."""
    return Path(__file__).resolve().parents[1] / "data" / "results_snapshot"


def load_snapshot_manifest(results_dir: Path) -> dict:
    """The manifest for `results_dir`, or the packaged one when it has none.

    A checkout keeps a working `results/` directory that holds every run ever
    made and no manifest, so a local reader would see `unavailable` while the
    installed wheel shows the snapshot. Fall back to the packaged copy, which
    is the same snapshot the wheel serves.
    """
    manifest = load_bundled_manifest(results_dir)
    if manifest.get("status") != "unavailable":
        return manifest
    packaged = packaged_snapshot_dir()
    if packaged.resolve() == results_dir.resolve():
        return manifest
    return load_bundled_manifest(packaged)


def validate_manifest_inventory(manifest: dict, results_dir: Path) -> list[str]:
    """Return sorted strategy names that differ between a manifest and summaries."""
    corpus = manifest.get("corpus")
    included = manifest.get("included_strategies")
    if (
        not isinstance(corpus, str)
        or not isinstance(included, list)
        or not all(isinstance(strategy, str) for strategy in included)
    ):
        return ["invalid manifest inventory"]

    prefix = f"{corpus}_"
    suffix = "_summary.json"
    summaries = [
        path.name[len(prefix) : -len(suffix)]
        for path in results_dir.glob(f"{corpus}_*_summary.json")
        if path.name.startswith(prefix) and path.name.endswith(suffix)
    ]
    included_counts = Counter(included)
    summary_counts = Counter(summaries)
    if included_counts == summary_counts:
        return []
    return sorted(
        ((included_counts - summary_counts) + (summary_counts - included_counts)).elements()
    )
