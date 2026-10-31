#!/usr/bin/env python3
"""Capture each website's card picture for the home page's project index.

A card shows the site's most telling view, usually its map, framed to fill a
16:9 card: no side panels, cut-off buttons or text-only heroes. For each site
this opens the live page in Chrome (light and dark, as a new reader would see
it), prepares the view (selects, hides a panel, fits the map), measures the
figure, widens that box to 16:9 around its centre, screenshots it and writes
assets/sites/<id>-<scheme>-{1440,720}.webp, the files the cards already use.

Needs Playwright and Pillow (ai_workflow's .venv has both) and the installed
Google Chrome; Playwright's bundled browsers hang on Will's machine.

    ~/src/ai_workflow/.venv/bin/python scripts/capture_cards.py [site ...]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "sites"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "https://wcook04.github.io/"


HIDE_OVERLAYS = """(() => {
  // The map's own key and zoom buttons sit over the canvas's edges; at card
  // size they are noise, so the canvas's siblings step out of sight.
  const c = document.querySelector(%r);
  [...c.parentElement.children].forEach(e => { if (e !== c) e.style.visibility = 'hidden'; });
})()"""


def click_text(page, text: str) -> None:
    page.get_by_role("button", name=text, exact=True).first.click()
    page.wait_for_timeout(900)


def lean_prepare(page) -> None:
    page.mouse.move(800, 400)
    page.mouse.wheel(0, 400)
    page.wait_for_timeout(1500)
    page.mouse.wheel(0, -2000)
    page.wait_for_timeout(1500)
    page.mouse.move(1550, 500)
    page.keyboard.down("Control")
    for _ in range(2):
        page.mouse.wheel(0, 100)
        page.wait_for_timeout(250)
    page.keyboard.up("Control")
    page.mouse.move(5, 5)


# Each site: the page, the viewport, how to prepare it, and a script that
# returns the figure's box {x, y, w, h} in viewport pixels. `fill` scales the
# box before it is widened to 16:9: below 1 leaves a margin round the figure.
SITES = {
    "maths": {
        "url": BASE + "practical-formal-verification/maths/universe.html",
        "viewport": (2400, 1000), "dpr": 1, "fill": 1.0,
        "prepare": lambda page: page.evaluate(HIDE_OVERLAYS % ".universe-canvas"),
        "box": "(() => { const r = document.querySelector('.universe-canvas').getBoundingClientRect();"
               " return {x: r.left, y: r.top, w: r.width, h: r.height}; })()",
        "ring": True,
    },
    "atlas": {
        "url": BASE + "plectis-atlas/",
        "viewport": (2400, 1100), "dpr": 1, "fill": 1.0, "pad": True,
        # The circles, without the key strip across the canvas's top.
        "box": "(() => { const r = document.querySelector('.u-canvas').getBoundingClientRect();"
               " return {x: r.left, y: r.top + 90, w: r.width, h: r.height - 130}; })()",
    },
    "formal-verification": {
        "url": BASE + "practical-formal-verification/explorer/",
        "viewport": (1600, 900), "dpr": 2, "fill": 1.1,
        "prepare": lambda page: (click_text(page, "Hide panel"), click_text(page, "Fit"),
                                 page.evaluate(HIDE_OVERLAYS % "canvas")),
        "box": "(() => { const r = document.querySelector('canvas').getBoundingClientRect();"
               " return {x: r.left, y: r.top, w: r.width, h: r.height}; })()",
        "ring": True,
    },
    "lean-exposition": {
        # The paper and its argument map side by side, the view Will chose: the
        # exposition's opening beside the map at its main result. The map pane
        # draws once the passage has scrolled, and zooms out on ctrl and wheel.
        "url": BASE + "lean-exposition-site/read/expository/",
        "viewport": (2000, 1125), "dpr": 1, "fill": 1.0,
        "prepare": lambda page: lean_prepare(page),
        # From the passage's left edge to the window's right, under the header.
        "box": "(() => { const h = document.querySelector('header').getBoundingClientRect().bottom;"
               " return {x: 230, y: h, w: 1770, h: 1125 - h}; })()",
    },
    "proof-reader": {
        # A sentence in the paper beside the graph and the exact Lean lines it
        # describes, the same view as the picture in that repository's README.
        "url": BASE + "proof-reader/#/contextual-embeddings/@closed-world",
        "viewport": (1600, 900), "dpr": 2, "fill": 1.0,
        "box": "({x: 0, y: 0, w: 1600, h: 900})",
    },
    "zenith": {
        "url": BASE + "plectis-zenith/",
        "viewport": (1600, 1000), "dpr": 3, "fill": 1.0, "pad": True,
        "prepare": lambda page: page.evaluate(
            "document.querySelector('.chapter__figure img').scrollIntoView({block: 'center'})"),
        # The whole repair loop, set on its own paper.
        "box": "(() => { const r = document.querySelector('.chapter__figure img').getBoundingClientRect();"
               " return {x: r.left, y: r.top, w: r.width, h: r.height}; })()",
    },
}


def frame(box: dict, viewport: tuple[int, int], fill: float, ring: bool) -> dict:
    """Widen the figure's box to 16:9 around its centre, inside the viewport.
    A ring (a round map centred in its canvas) is framed by its height: the
    circle fills the card's height, so it shows whole, centred."""
    cx, cy = box["x"] + box["w"] / 2, box["y"] + box["h"] / 2
    if ring:
        h = min(box["w"], box["h"]) * 0.98 / fill
        w = h * 16 / 9
    else:
        w, h = box["w"] / fill, box["h"] / fill
        if w / h < 16 / 9:
            w = h * 16 / 9
        else:
            h = w * 9 / 16
    vw, vh = viewport
    w, h = min(w, vw), min(h, vh)
    if w / h > 16 / 9:
        w = h * 16 / 9
    else:
        h = w * 9 / 16
    x = min(max(cx - w / 2, 0), vw - w)
    y = min(max(cy - h / 2, 0), vh - h)
    return {"x": x, "y": y, "width": w, "height": h}


def pad_to_card(image: Image.Image, margin: float = 0.06) -> Image.Image:
    """Set a figure captured on its own in the middle of a 16:9 card of its
    own background (a pixel just inside its left edge), with a margin round it."""
    w, h = image.size
    cw = max(w * (1 + 2 * margin), h * (1 + 2 * margin) * 16 / 9)
    ch = cw * 9 / 16
    card = Image.new("RGB", (round(cw), round(ch)), image.getpixel((6, h // 2)))
    card.paste(image, (round((cw - w) / 2), round((ch - h) / 2)))
    return card


def capture(pw, site_id: str, spec: dict, scheme: str) -> None:
    browser = pw.chromium.launch(executable_path=CHROME, headless=True)
    try:
        context = browser.new_context(viewport={"width": spec["viewport"][0], "height": spec["viewport"][1]},
                                      device_scale_factor=spec["dpr"], color_scheme=scheme,
                                      reduced_motion="reduce")
        page = context.new_page()
        page.goto(spec["url"], wait_until="networkidle")
        page.wait_for_timeout(1500)
        if spec.get("prepare"):
            spec["prepare"](page)
        page.wait_for_timeout(2000)
        box = page.evaluate(spec["box"])
        if spec.get("pad"):
            clip = {"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]}
        else:
            clip = frame(box, spec["viewport"], spec["fill"], spec.get("ring", False))
        png = page.screenshot(clip=clip)
    finally:
        browser.close()
    image = Image.open(io.BytesIO(png)).convert("RGB")
    if spec.get("pad"):
        image = pad_to_card(image)
    for width in (1440, 720):
        resized = image.resize((width, round(width * 9 / 16)), Image.LANCZOS)
        resized.save(OUT / f"{site_id}-{scheme}-{width}.webp", "WEBP", quality=86, method=6)
    print(f"{site_id} {scheme}: box {[round(v) for v in box.values()]} -> clip "
          f"{[round(v) for v in clip.values()]}")


def main(argv: list[str]) -> int:
    wanted = argv or list(SITES)
    with sync_playwright() as pw:
        for site_id in wanted:
            for scheme in ("light", "dark"):
                capture(pw, site_id, SITES[site_id], scheme)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
