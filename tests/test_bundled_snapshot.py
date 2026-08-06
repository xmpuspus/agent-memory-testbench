"""Tests for the bundled historical benchmark snapshot manifest."""

from __future__ import annotations

import json
from pathlib import Path

from memory_arena.evidence.bundled import (
    load_bundled_manifest,
    validate_manifest_inventory,
)
from memory_arena.paths import results_root


def test_bundled_manifest_matches_summary_inventory(monkeypatch):
    """A changed summary set must not remain labeled as the bundled snapshot."""
    bundled_results = Path(__file__).parents[1] / "memory_arena" / "data" / "results_snapshot"
    monkeypatch.setenv("MEM_ARENA_RESULTS_PATH", str(bundled_results))
    results_dir = results_root()
    manifest = load_bundled_manifest(results_dir)

    assert manifest["status"] == "historical"
    assert manifest["question_count"] == 16
    summary_metadata = [
        json.loads(path.read_text())["metadata"]
        for path in results_dir.glob("longmemeval-s_*_summary.json")
    ]
    expected_commits = sorted(
        {metadata["commit_sha"] for metadata in summary_metadata if metadata.get("commit_sha")}
    )
    expected_memory_arena_versions = sorted(
        {
            metadata["package_versions"]["memory-arena"]
            for metadata in summary_metadata
            if metadata.get("package_versions", {}).get("memory-arena")
        }
    )

    assert manifest["source_commits"] == expected_commits
    assert len(manifest["source_commits"]) == len(set(manifest["source_commits"]))
    assert manifest["source_versions"]["memory-arena"] == expected_memory_arena_versions
    assert validate_manifest_inventory(manifest, results_dir) == []


def test_missing_manifest_is_explicitly_unavailable(tmp_path):
    """A snapshot without a manifest must not be presented as benchmark data."""
    manifest = load_bundled_manifest(tmp_path)

    assert manifest == {
        "snapshot_id": None,
        "status": "unavailable",
        "reason": "manifest not found",
    }


def test_malformed_manifest_is_explicitly_unavailable(tmp_path):
    """Invalid JSON must not quietly produce an invented snapshot description."""
    (tmp_path / "manifest.json").write_text("{")

    manifest = load_bundled_manifest(tmp_path)

    assert manifest == {
        "snapshot_id": None,
        "status": "unavailable",
        "reason": "manifest is invalid",
    }


def test_inventory_validation_reports_summary_name_mismatches(tmp_path):
    """A renamed or omitted summary must be reported by inventory validation."""
    (tmp_path / "longmemeval-s_bm25_summary.json").write_text("{}")
    manifest = {"corpus": "longmemeval-s", "included_strategies": ["not_bm25"]}

    assert validate_manifest_inventory(manifest, tmp_path) == ["bm25", "not_bm25"]
