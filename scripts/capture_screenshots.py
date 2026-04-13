#!/usr/bin/env python3
"""Capture screenshots for README using Playwright."""

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

FRONTEND_URL = "http://localhost:3005"
OUT = Path("docs/images")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # Screenshot 1: Initial evidence board (demo mode)
    page.goto(FRONTEND_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.screenshot(path=str(OUT / "evidence-board-demo.png"), full_page=False)
    print("1/3 evidence-board-demo.png")

    # Screenshot 2: Node selected
    card = page.locator(".sticky-card").first
    if card.count() > 0:
        card.click()
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "evidence-board-selected.png"), full_page=False)
        print("2/3 evidence-board-selected.png")

    # Screenshot 3: Chinese locale
    lang_btn = page.locator(".header-bar button").last
    if lang_btn.count() > 0:
        lang_btn.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "evidence-board-zh.png"), full_page=False)
        print("3/3 evidence-board-zh.png")
    else:
        print("3/3 SKIP (lang button not found)")

    browser.close()
    print("Done.")
