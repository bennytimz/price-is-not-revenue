"""Screenshots of the built dashboard for the README (docs/img/*.png). Not part of run_all.py.

Opens dashboard.html from disk (no server) in a headless browser with a 1400 px wide viewport and the page's light
colour scheme, and captures four regions of the page exactly as built: nothing is added, hidden or edited. Each image
is clipped to the dashboard's content column, scaled so the PNG is 1400 px wide, reduced to a 256-colour palette and
saved optimised; the script stops if any image is 400 KB or more.

  1. dashboard_top.png          title, the four headline tiles and the top of the page
  2. dashboard_scorecard.png    the full verdict scorecard (all twelve tests, including the failed ones)
  3. dashboard_sensitivity.png  section 4, the dilution sensitivity at its default settings
  4. dashboard_predictions.png  section 8, where the predictions stand today (interim status, not a resolution)
  5. dashboard_top_narrow.png   the same top of the page at phone width: a 360 px viewport rendered at 2x (720 px wide
                                PNG), so the four tiles stack two by two and stay legible on a phone; under 150 KB

Setup (optional, not needed for run_all.py):  pip install playwright pillow
Browser: Playwright's Chromium if installed (`python -m playwright install chromium`), otherwise the installed
Microsoft Edge or Google Chrome. Rebuild the dashboard first (python run_all.py), then: python make_screenshots.py
"""
import io
import os
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "docs", "img")
WIDTH_PX, VIEWPORT_W, MAX_BYTES, PAD = 1400, 1400, 400 * 1024, 12

NARROW = ("dashboard_top_narrow.png", 360, 2, 150 * 1024)  # file, viewport width, scale, size limit

# (file, first element, element after the last one, or None for the end of the page)
REGIONS = [
    ("dashboard_top.png", "h1", "h2:text-is('Verdict scorecard')"),
    ("dashboard_scorecard.png", "h2:text-is('Verdict scorecard')", "h2:text-matches('^1\\\\. ')"),
    ("dashboard_sensitivity.png", "h2:text-matches('^4\\\\. ')", "h2:text-matches('^5\\\\. ')"),
    ("dashboard_predictions.png", "h2:text-matches('^8\\\\. ')", None),
]


def launch(p):
    for kw in ({}, {"channel": "msedge"}, {"channel": "chrome"}):
        try:
            return p.chromium.launch(**kw)
        except Exception:
            continue
    sys.exit("No browser: run `python -m playwright install chromium`, or install Edge or Chrome.")


def column(page):
    box = page.locator("main").bounding_box()
    return box["x"], box["width"]


def region(page, first, after):
    top = page.locator(first).first.bounding_box()["y"] - PAD
    if after:
        bottom = page.locator(after).first.bounding_box()["y"] - PAD  # stop above the next section's heading
    else:
        bottom = page.evaluate("document.querySelector('main').getBoundingClientRect().bottom + window.scrollY")
    return top, bottom


def save(png_bytes, path, max_bytes=MAX_BYTES):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    for colours in (256, 128, 64):
        q = im.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        buf = io.BytesIO()
        q.save(buf, format="PNG", optimize=True)
        if buf.tell() < max_bytes:
            open(path, "wb").write(buf.getvalue())
            return im.size, buf.tell(), colours
    sys.exit(f"{os.path.basename(path)}: still {buf.tell():,} bytes at 64 colours; not saved")


def main():
    page_file = os.path.join(D, "dashboard.html")
    if not os.path.exists(page_file):
        sys.exit("dashboard.html not found: run python run_all.py first")
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = launch(p)
        probe = browser.new_page(viewport={"width": VIEWPORT_W, "height": 900}, color_scheme="light")
        probe.goto("file:///" + page_file.replace(os.sep, "/"))
        _, col_w = column(probe)
        probe.close()
        scale = WIDTH_PX / col_w  # makes the clipped column exactly WIDTH_PX wide
        page = browser.new_page(viewport={"width": VIEWPORT_W, "height": 900}, device_scale_factor=scale, color_scheme="light")
        page.goto("file:///" + page_file.replace(os.sep, "/"))
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)  # let Chart.js finish its entry animation
        x, w = column(page)
        for name, first, after in REGIONS:
            top, bottom = region(page, first, after)
            shot = page.screenshot(full_page=True, clip={"x": x, "y": max(top, 0), "width": w, "height": bottom - max(top, 0)})
            size, nbytes, colours = save(shot, os.path.join(OUT, name))
            print(f"docs/img/{name}: {size[0]}x{size[1]} px, {nbytes:,} bytes ({nbytes / 1024:.0f} KB), {colours}-colour palette")
        # 5. the top of the page at phone width (same page, narrower viewport; nothing else changes)
        name, vw, scale, limit = NARROW
        page = browser.new_page(viewport={"width": vw, "height": 900}, device_scale_factor=scale, color_scheme="light")
        page.goto("file:///" + page_file.replace(os.sep, "/"))
        page.wait_for_load_state("networkidle")
        tops = page.evaluate("[...document.querySelectorAll('.tile')].map(e => Math.round(e.getBoundingClientRect().top))")
        if len(tops) != 4 or len(set(tops)) != 2:
            sys.exit(f"{name}: the four tiles are not two by two at {vw} px (rows at {sorted(set(tops))}); not saved")
        x, w = column(page)
        top, bottom = region(page, *REGIONS[0][1:])
        shot = page.screenshot(full_page=True, clip={"x": x, "y": max(top, 0), "width": w, "height": bottom - max(top, 0)})
        size, nbytes, colours = save(shot, os.path.join(OUT, name), limit)
        print(f"docs/img/{name}: {size[0]}x{size[1]} px, {nbytes:,} bytes ({nbytes / 1024:.0f} KB), {colours}-colour palette, "
              f"viewport {vw} px at {scale}x, tiles two by two")
        browser.close()


if __name__ == "__main__":
    main()
