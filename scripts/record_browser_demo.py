"""Record the browser half of the README recording against a live server.

The beats follow the approved design: the bundled overview, the historical
results, the correct-session/wrong-answer filter, and one Failure Lab record.
Every frame comes from the running dashboard. Nothing is staged, and the script
uses explicit waits per beat rather than one long automated scroll.

    python scripts/record_browser_demo.py --base http://127.0.0.1:8801 --out tmp/rec
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTH, HEIGHT = 960, 540
FAILING_QUESTION = "71017276"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = args.base.rstrip("/")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            record_video_dir=str(out),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = context.new_page()

        # Beat 2: the bundled overview, with the snapshot identity in view.
        page.goto(f"{base}/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(2200)

        # Beat 3: the historical results.
        page.goto(f"{base}/benchmark/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(2300)

        # Beat 4: pick the correct-session, wrong-answer questions.
        page.goto(f"{base}/recall-lab/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1200)
        page.select_option("select >> nth=1", "correct_session_wrong_answer")
        page.wait_for_timeout(1500)

        # Beat 5: open one record and hold on the evidence.
        page.evaluate(
            """(qid) => {
              const cards = [...document.querySelectorAll('div.rounded-lg.border')];
              const card = cards.find((c) => c.textContent.includes(qid));
              if (!card) throw new Error('no card for ' + qid);
              const details = card.querySelector('details');
              if (!details) throw new Error('no evidence panel for ' + qid);
              details.open = true;
              card.scrollIntoView({ block: 'center' });
            }""",
            FAILING_QUESTION,
        )
        page.wait_for_timeout(3400)

        video = page.video
        context.close()
        browser.close()
        if video is None:
            raise SystemExit("playwright recorded no video")
        saved = out / "browser.webm"
        Path(video.path()).replace(saved)
        print(f"wrote {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
