"""Load and verify the historical result snapshot bundled with the package."""

from __future__ import annotations

import json
from pathlib import Path


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

    if not isinstance(manifest, dict) or not all(
        isinstance(manifest.get(key), str) for key in ("snapshot_id", "status")
    ):
        return _unavailable_manifest("manifest is invalid")
    return manifest


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
    if sorted(included) == sorted(summaries):
        return []
    return sorted(set(included).symmetric_difference(summaries))
