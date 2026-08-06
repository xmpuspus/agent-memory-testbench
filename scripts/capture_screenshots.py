"""Capture the README screenshots from a running dashboard.

Point this at the wheel's `memory-arena demo` so the pictures show what a reader
gets, not what a checkout shows. `docs/recapture.sh` starts that server.

    python scripts/capture_screenshots.py --base http://127.0.0.1:8823
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

FAILING_QUESTION = "71017276"

OPEN_EVIDENCE = """(qid) => {
  const cards = [...document.querySelectorAll('div.rounded-lg.border')];
  const card = cards.find((c) => c.textContent.includes(qid));
  if (!card) throw new Error('no card for ' + qid);
  const details = card.querySelector('details');
  if (!details) throw new Error('no evidence panel for ' + qid);
  details.open = true;
}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", default="docs")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        problems: list[str] = []
        page.on("pageerror", lambda e: problems.append(str(e)))

        def shoot(route: str, name: str, full: bool = True) -> None:
            page.goto(f"{base}{route}", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1400)
            target = out / name
            page.screenshot(path=str(target), full_page=full)
            written.append((name, target.stat().st_size))

        shoot("/", "screenshot-home.png")
        shoot("/benchmark/", "screenshot-benchmark.png")
        shoot("/recall-lab/", "screenshot-recall-lab.png")

        # The Failure Lab shot needs the filter applied and one record open.
        page.goto(f"{base}/recall-lab/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1400)
        page.select_option("select >> nth=1", "correct_session_wrong_answer")
        page.wait_for_timeout(900)
        page.evaluate(OPEN_EVIDENCE, FAILING_QUESTION)
        page.wait_for_timeout(700)
        target = out / "screenshot-failure-lab.png"
        page.screenshot(path=str(target), full_page=True)
        written.append((target.name, target.stat().st_size))

        # The snapshot panel on its own, for the README's evidence section.
        # Find the bordered box that holds the heading, not an ancestor that
        # happens to wrap the whole page.
        page.goto(f"{base}/benchmark/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1200)
        box = page.evaluate(
            """() => {
              const panel = [...document.querySelectorAll('section.rounded-lg')].find(
                (s) => s.textContent.includes('Historical benchmark data')
              );
              if (!panel) throw new Error('no snapshot panel');
              const r = panel.getBoundingClientRect();
              return {x: r.x - 8, y: r.y - 8, width: r.width + 16, height: r.height + 16};
            }"""
        )
        target = out / "screenshot-snapshot.png"
        page.screenshot(path=str(target), clip=box)
        written.append((target.name, target.stat().st_size))

        context.close()
        browser.close()

    if problems:
        raise SystemExit(f"page errors during capture: {problems}")
    for name, size in written:
        print(f"  {name}  {size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
