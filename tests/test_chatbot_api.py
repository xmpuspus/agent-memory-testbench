"""Tests for memory_arena.chatbot.api FastAPI endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from memory_arena.chatbot.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_openapi_uses_agent_memory_testbench_title(self, client):
        body = client.get("/openapi.json").json()

        assert body["info"]["title"] == "Agent Memory Testbench"

    def test_health_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert isinstance(body["strategies"], list)
        assert "full_context" in body["strategies"]

    def test_health_includes_results_flag(self, client):
        r = client.get("/api/health")
        assert "has_results" in r.json()

    def test_health_exposes_snapshot_status(self, client):
        body = client.get("/api/health").json()

        assert body["snapshot_status"] in {"historical", "unavailable"}
        assert "snapshot_id" in body


class TestCorpora:
    def test_corpora_returns_list(self, client):
        r = client.get("/api/corpora")
        assert r.status_code == 200
        body = r.json()
        assert "corpora" in body
        assert isinstance(body["corpora"], list)

    def test_corpora_has_label_and_count(self, client):
        r = client.get("/api/corpora")
        body = r.json()
        if body["corpora"]:
            entry = body["corpora"][0]
            assert "name" in entry
            assert "label" in entry
            assert "count" in entry


class TestStrategies:
    def test_strategies_endpoint(self, client):
        r = client.get("/api/strategies")
        assert r.status_code == 200
        body = r.json()
        names = [s["name"] for s in body["strategies"]]
        assert "full_context" in names
        assert "naive_vector" in names


class TestResultsLookup:
    def test_bundled_results_include_historical_snapshot(self, client, monkeypatch):
        bundled_results = Path(__file__).parents[1] / "memory_arena" / "data" / "results_snapshot"
        monkeypatch.setenv("MEM_ARENA_RESULTS_PATH", str(bundled_results))

        body = client.get("/api/results/longmemeval-s").json()

        assert body["snapshot"]["status"] == "historical"

    def test_benchmark_alias_includes_historical_snapshot(self, client, monkeypatch):
        bundled_results = Path(__file__).parents[1] / "memory_arena" / "data" / "results_snapshot"
        monkeypatch.setenv("MEM_ARENA_RESULTS_PATH", str(bundled_results))

        body = client.get("/api/benchmark/longmemeval-s").json()

        assert body["snapshot"]["status"] == "historical"

    def test_results_routes_publish_the_same_typed_snapshot_contract(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        results_schema = paths["/api/results/{corpus}"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        benchmark_schema = paths["/api/benchmark/{corpus}"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]

        assert results_schema == benchmark_schema
        response_ref = results_schema["$ref"]
        response_name = response_ref.rsplit("/", 1)[-1]
        response_model = schema["components"]["schemas"][response_name]
        snapshot_ref = response_model["properties"]["snapshot"]["$ref"]
        assert snapshot_ref == "#/components/schemas/SnapshotResponse"

    def test_results_404_when_missing(self, client):
        r = client.get("/api/results/nonexistent-corpus")
        assert r.status_code == 404

    def test_benchmark_alias_404(self, client):
        r = client.get("/api/benchmark/nonexistent-corpus")
        assert r.status_code == 404


class TestCORS:
    def test_cors_preflight_allowed(self, client):
        r = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORSMiddleware responds 200 to preflight requests
        assert r.status_code in (200, 204)


class TestRecallRecords:
    def test_recall_records_falls_back_to_seed0(self, client):
        # bm25 ships only `_seed{N}.json` / `_summary.json` with no bare
        # `{corpus}_{strategy}.json`, the same shape as the bundled wheel
        # snapshot. The endpoint must fall back to seed 0 (which carries
        # recall_records) instead of 404ing, otherwise the Recall Lab page is
        # dead for every pip-installed user.
        r = client.get("/api/recall-records/longmemeval-s/bm25")
        assert r.status_code == 200
        body = r.json()
        assert body["strategy"] == "bm25"
        assert len(body["records"]) > 0

    def test_recall_records_unknown_strategy_404(self, client):
        r = client.get("/api/recall-records/longmemeval-s/not_a_strategy")
        assert r.status_code == 404
