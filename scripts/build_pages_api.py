"""Freeze the read-only API into static files for the GitHub Pages site.

GitHub Pages serves files, not a FastAPI process, so the dashboard would show
its unavailable state on every page. This script asks the real application for
each response the browser asks for and writes the body to a file at the same
path. The Pages site then serves the same bytes the wheel serves, and no second
copy of the data has to be kept in step by hand.

Run it after `next build`, against the export directory:

    python scripts/build_pages_api.py --out web/out
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_RESULTS = REPO_ROOT / "memory_arena" / "data" / "results_snapshot"

# The public site must show what the wheel shows. A checkout also has a working
# `results/` directory that holds every strategy ever run, and `results_root()`
# prefers it. Point at the bundled snapshot instead, so the Pages rows and the
# wheel rows come from one source.
os.environ.setdefault("MEM_ARENA_RESULTS_PATH", str(BUNDLED_RESULTS))

# Python puts this script's own directory first on the import path, not the
# repository root. Without this line an editable install elsewhere on the
# machine wins, and the site freezes another checkout's results.
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from memory_arena.chatbot.api import app  # noqa: E402
from memory_arena.paths import results_root  # noqa: E402

MANIFEST = REPO_ROOT / "memory_arena" / "data" / "results_snapshot" / "manifest.json"


def _snapshot_strategies() -> list[str]:
    """Strategy names the bundled historical manifest declares."""
    manifest = json.loads(MANIFEST.read_text())
    return list(manifest.get("included_strategies") or [])


def _corpora(client: TestClient) -> list[str]:
    body = client.get("/api/corpora").json()
    return [c["name"] for c in body.get("corpora", [])] or ["longmemeval-s"]


def _write(out_dir: Path, route: str, payload: object) -> None:
    target = out_dir / route.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload))
    print(f"  wrote {route}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="web/out", help="Static export directory")
    args = ap.parse_args()

    out_dir = (REPO_ROOT / args.out).resolve()
    if not out_dir.is_dir():
        raise SystemExit(f"export directory not found: {out_dir}")

    import memory_arena

    package_root = Path(memory_arena.__file__).resolve().parents[1]
    if package_root != REPO_ROOT:
        raise SystemExit(f"imported memory_arena from {package_root}, expected {REPO_ROOT}")

    print(f"Freezing API responses into {out_dir}")
    print(f"Results root: {results_root()}")

    with TestClient(app) as client:
        health = client.get("/api/health")
        if health.status_code != 200:
            raise SystemExit(f"/api/health returned {health.status_code}")
        snapshot_status = health.json().get("snapshot_status")
        if snapshot_status == "unavailable":
            raise SystemExit("refusing to build a Pages site with no bundled snapshot")
        print(f"Snapshot status: {snapshot_status}")
        _write(out_dir, "/api/health", health.json())

        _write(out_dir, "/api/corpora", client.get("/api/corpora").json())
        _write(out_dir, "/api/strategies", client.get("/api/strategies").json())

        frozen = 0
        for corpus in _corpora(client):
            benchmark = client.get(f"/api/benchmark/{corpus}")
            if benchmark.status_code != 200:
                raise SystemExit(f"/api/benchmark/{corpus} returned {benchmark.status_code}")
            body = benchmark.json()
            snapshot = body.get("snapshot") or {}
            if snapshot.get("status") != "historical":
                raise SystemExit(f"/api/benchmark/{corpus} snapshot is {snapshot.get('status')}")
            declared = _snapshot_strategies()
            got = [row["strategy"] for row in body.get("results", [])]
            if got != declared:
                raise SystemExit(f"benchmark rows {got} do not match the manifest {declared}")
            _write(out_dir, f"/api/benchmark/{corpus}", body)
            _write(out_dir, f"/api/results/{corpus}", client.get(f"/api/results/{corpus}").json())

            for strategy in _snapshot_strategies():
                route = f"/api/recall-records/{corpus}/{strategy}"
                res = client.get(route)
                if res.status_code != 200:
                    print(f"  skip {route} ({res.status_code})")
                    continue
                _write(out_dir, route, res.json())
                frozen += 1

    # GitHub Pages runs Jekyll on a plain branch source, and Jekyll drops any
    # directory whose name starts with an underscore. That would remove every
    # Next.js asset under _next/.
    (out_dir / ".nojekyll").write_text("")
    print(f"  wrote /.nojekyll\nFroze {frozen} recall-record routes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
