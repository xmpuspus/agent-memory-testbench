"""Generate docs/social-preview.png: 1280x640 GitHub social card.

When the repo URL is shared on Twitter / LinkedIn / Slack, GitHub's
default unfurl picks the README's first image. We can override that
in repo Settings -> Social preview with a curated 1280x640 image.

This script renders one: the title, a one-liner finding, and the four
top strategies + the four bottom strategies side-by-side. Pure flat
typography, no decorative boxes (Tufte: maximize data-ink ratio).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
# The card names the bundled historical snapshot, so it must read that snapshot.
# The working `results/` directory holds every strategy ever run, including five
# the snapshot does not contain, and reading it put those names under a heading
# that says 16 strategies.
SNAPSHOT = REPO_ROOT / "memory_arena" / "data" / "results_snapshot"
MANIFEST = SNAPSHOT / "manifest.json"
OUT = REPO_ROOT / "docs" / "social-preview.png"

NAVY = "#1f3b73"
CORAL = "#e3614c"
INK = "#1c1c1c"
SUB = "#5a6878"
GRID = "#cdd5e0"


def _load_summaries() -> list[dict]:
    """The snapshot's own summaries, checked against its manifest inventory."""
    manifest = json.loads(MANIFEST.read_text())
    declared = sorted(manifest["included_strategies"])
    out = []
    for p in SNAPSHOT.glob("longmemeval-s_*_summary.json"):
        out.append(json.loads(p.read_text()))
    found = sorted(r["strategy"] for r in out)
    if found != declared:
        raise SystemExit(f"snapshot summaries {found} do not match the manifest {declared}")
    out.sort(key=lambda r: -r.get("accuracy", 0.0))
    return out


def _snapshot_caption() -> str:
    manifest = json.loads(MANIFEST.read_text())
    return (
        f"Historical snapshot {manifest['snapshot_id']}: "
        f"{len(manifest['included_strategies'])} strategies, "
        f"{manifest['question_count']} questions, {manifest['category_count']} categories"
    )


def build() -> Path:
    summaries = _load_summaries()
    fig, ax = plt.subplots(figsize=(12.8, 6.4), dpi=100)  # 1280x640
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Title block, top-left.
    ax.text(
        4,
        90,
        "Agent Memory Testbench",
        fontsize=42,
        weight="bold",
        color=INK,
    )
    ax.text(
        4,
        81,
        "Benchmark agent memory from retrieval to answer.",
        fontsize=18,
        color=SUB,
    )
    ax.text(
        4,
        76,
        _snapshot_caption(),
        fontsize=12,
        color=SUB,
        style="italic",
    )

    # Hero finding line (no decorative box; Tufte: erase chartjunk).
    ax.text(
        50,
        66,
        "Past evidence you can open, not a present ranking. Mixed source commits and seed counts.",
        fontsize=15,
        color=INK,
        style="italic",
        ha="center",
        va="center",
    )

    # Top 4 + bottom 4 leaderboard (split across the bottom half)
    tops = summaries[:4]
    bots = summaries[-4:]

    def _row(label: str, x_left: float, items: list[dict], color: str) -> None:
        ax.text(x_left, 50, label, fontsize=14, weight="bold", color=color)
        for i, item in enumerate(items):
            y = 42 - i * 9
            ax.text(
                x_left,
                y,
                item["strategy"],
                fontsize=13,
                color=INK,
            )
            acc = item.get("accuracy", 0.0) * 100
            ci = item.get("accuracy_ci", 0.0) * 100
            ci_s = f" ±{ci:.1f}" if ci else ""
            ax.text(
                x_left + 30,
                y,
                f"{acc:.1f}%{ci_s}",
                fontsize=13,
                color=color,
                weight="bold",
            )

    _row("Highest in the snapshot", 4, tops, NAVY)
    _row("Lowest in the snapshot", 56, bots, CORAL)

    # Footer link + reproducibility hook
    footer = (
        "github.com/xmpuspus/agent-memory-testbench  |  MIT  |  "
        "pip install memory-arena  |  memory-arena demo: no API key, no Docker"
    )
    ax.text(
        50,
        4,
        footer,
        fontsize=10,
        color=SUB,
        ha="center",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=100, facecolor="white")
    plt.close(fig)
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
    return OUT


if __name__ == "__main__":
    build()
