"""Screenshot every dashboard route at desktop and mobile width.

The visual gate needs pictures of the running product, not of the source. Point
this at a live server (the wheel's `memory-arena demo`, or the Pages URL) and it
writes one PNG per route per viewport, then reports the page height so a
reviewer can see overflow without opening each file.

    python scripts/shoot_pages.py --base http://127.0.0.1:8792 --out tmp/shots
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROUTES = ["/", "/benchmark/", "/recall-lab/", "/arena/"]
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for label, (width, height) in VIEWPORTS.items():
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2 if label == "mobile" else 1,
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            for route in ROUTES:
                url = f"{args.base.rstrip('/')}{args.prefix}{route}"
                page.goto(url, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(1200)
                name = route.strip("/").replace("/", "-") or "home"
                target = out / f"{label}-{name}.png"
                page.screenshot(path=str(target), full_page=True)
                body_height = page.evaluate("document.body.scrollHeight")
                overflow = page.evaluate(
                    "document.documentElement.scrollWidth > window.innerWidth + 1"
                )
                report.append(
                    {
                        "viewport": label,
                        "route": route,
                        "url": url,
                        "file": target.name,
                        "page_height_px": body_height,
                        "horizontal_overflow": overflow,
                        "console_errors": list(errors),
                    }
                )
                errors.clear()
            context.close()
        browser.close()

    (out / "report.json").write_text(json.dumps(report, indent=2))
    for row in report:
        flag = "OVERFLOW" if row["horizontal_overflow"] else "ok"
        errs = len(row["console_errors"])
        print(
            f"{row['viewport']:<8} {row['route']:<14} h={row['page_height_px']:>6}px "
            f"{flag:<9} console_errors={errs}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
