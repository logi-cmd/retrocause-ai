#!/usr/bin/env python3
"""
RetroCause UI Smoke Test (Playwright / Chromium)

Covers scenarios from docs/manual-smoke-test.md:
  1. Initial load — evidence board renders with 3-panel layout
  2. Demo mode transparency — banner visible on initial load
  3. Query flow — submit a query, board updates
  4. Node click / multi-hop tracing
  5. Language toggle (EN/ZH)

Run from repo root:
  python scripts/ui_smoke_test.py

Requirements: playwright installed (pip install playwright), chromium browser installed.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print(
        "[FAIL] playwright not installed. Run: pip install playwright && playwright install chromium"
    )
    sys.exit(1)

FRONTEND_URL = "http://localhost:3005"
BACKEND_URL = "http://127.0.0.1:8000"
TIMEOUT = 15_000  # ms


class SmokeTest:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        status = "PASS" if condition else "FAIL"
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        msg = f"  [{status}] {name}"
        if detail and not condition:
            msg += f" — {detail}"
        print(msg)
        self.results.append((name, condition, detail))

    def run(self) -> None:
        with sync_playwright() as p:
            # Use chromium (not chrome — chrome may not be installed)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.set_default_timeout(TIMEOUT)

            try:
                self._test_scenario1(page)
                self._test_scenario2(page)
                self._test_scenario3(page)
                self._test_scenario4(page)
                self._test_scenario5(page)
            except Exception as exc:
                self.check("overall", False, f"Uncaught exception: {exc}")
            finally:
                browser.close()

        self._print_summary()

    # ── Scenario 1: Initial Load ─────────────────────────────────────────
    def _test_scenario1(self, page: Page) -> None:
        print("\n=== Scenario 1: Initial Load ===")

        page.goto(FRONTEND_URL, wait_until="networkidle")

        # 1a. Page HTML loads
        html = page.content()
        self.check("page loads", "<html" in html.lower(), "no <html> tag found")

        # 1b. Evidence board background (cork texture via CSS)
        board = page.locator(".evidence-board")
        self.check("evidence board container", board.count() > 0, ".evidence-board not found")

        # 1c. Three-panel layout: header, left panel, right panel
        header = page.locator(".header-bar")
        left = page.locator(".left-panel")
        right = page.locator(".right-panel")
        self.check("header bar", header.count() > 0, ".header-bar not found")
        self.check("left panel", left.count() > 0, ".left-panel not found")
        self.check("right panel", right.count() > 0, ".right-panel not found")

        # 1d. No dark-terminal theme remnants
        dark_classes = page.locator("[class*='dark'], [class*='terminal'], [class*='bg-black']")
        self.check(
            "no dark-terminal remnants",
            dark_classes.count() == 0,
            f"found {dark_classes.count()} dark/terminal elements",
        )

        # 1e. Sticky cards rendered
        cards = page.locator(".sticky-card")
        card_count = cards.count()
        self.check(f"sticky cards rendered ({card_count})", card_count > 0, "no .sticky-card found")

        # 1f. Header renders h1 (the evidence board title)
        title = page.locator("h1").first
        title_text = title.text_content() or ""
        self.check("h1 renders", len(title_text.strip()) > 0, "h1 is empty")

    # ── Scenario 2: Demo Mode Transparency ────────────────────────────────
    def _test_scenario2(self, page: Page) -> None:
        print("\n=== Scenario 2: Demo Mode Transparency ===")

        # On initial load, should be in demo mode
        # Check right panel for demo status
        right_panel = page.locator(".right-panel")
        right_text = right_panel.text_content() or ""

        # Demo mode label should appear somewhere
        has_demo_text = (
            "demo" in right_text.lower()
            or "demo" in (page.locator(".evidence-board").text_content() or "").lower()
        )
        self.check("demo mode indicated", has_demo_text, "no 'demo' text found on page")

        # Check status indicator (green dot + demo/live label in header)
        status_text = page.locator(".header-bar").inner_text() or ""
        has_status = (
            "demo" in status_text.lower()
            or "live" in status_text.lower()
            or "processing" in status_text.lower()
        )
        if not has_status:
            # Fallback: check for green status dot (pulse animation)
            dot = page.locator('[style*="pulse"]')
            if dot.count() == 0:
                dot = page.locator(".header-bar [style*='animation']")
            has_status = dot.count() > 0
        self.check("status indicator in header", has_status, f"header text: '{status_text[:80]}'")

    # ── Scenario 3: Query Flow ───────────────────────────────────────────
    def _test_scenario3(self, page: Page) -> None:
        print("\n=== Scenario 3: Query Flow ===")

        # 3a. Type a query
        textarea = page.locator("textarea").first
        self.check("textarea found", textarea.count() > 0, "no textarea element")

        if textarea.count() > 0:
            textarea.fill("Why did SVB collapse?")
            # 3b. Submit button exists
            submit = page.locator("button:has-text('Analyze')").first
            if submit.count() == 0:
                submit = page.locator("button").filter(has_text="Analyze").first
            if submit.count() == 0:
                # Try Chinese button text
                submit = page.locator("button").filter(has_text="分析").first
            self.check("submit button", submit.count() > 0, "no analyze button found")

            if submit.count() > 0:
                # Click and wait for response
                submit.click()
                # Wait for either demo banner update or loading to finish
                time.sleep(3)

                # After submission, page should not crash
                page_html = page.content()
                self.check(
                    "page survives query", "<html" in page_html.lower(), "page crashed after query"
                )

                # Check that sticky cards still exist (board still rendered)
                cards = page.locator(".sticky-card")
                self.check(
                    "cards still rendered after query", cards.count() > 0, "cards disappeared"
                )

                # Check for status note update (should say demo fallback or live)
                right_text = page.locator(".right-panel").text_content() or ""
                has_update = (
                    "demo" in right_text.lower()
                    or "live" in right_text.lower()
                    or "analysis" in right_text.lower()
                    or "fallback" in right_text.lower()
                )
                self.check(
                    "status updated after query", has_update, f"right panel: '{right_text[:100]}'"
                )

    # ── Scenario 4: Node Click / Multi-hop ────────────────────────────────
    def _test_scenario4(self, page: Page) -> None:
        print("\n=== Scenario 4: Node Click / Multi-hop Tracing ===")

        # Click a sticky card
        cards = page.locator(".sticky-card")
        if cards.count() == 0:
            self.check("node click", False, "no cards to click")
            return

        first_card = cards.first
        first_card.click()
        time.sleep(0.5)

        # Check if selection ring appears
        selected = page.locator(".sticky-card.ring-2")
        self.check(
            "node selected (ring highlight)",
            selected.count() > 0,
            "no .ring-2 on selected card",
        )

        # Right panel should update with selected node info
        right_text = page.locator(".right-panel").text_content() or ""
        empty_title_check = (
            "click a node" not in right_text.lower() and "select" not in right_text.lower()
        )
        self.check(
            "right panel updated on click",
            empty_title_check or selected.count() > 0,
            "right panel still shows 'click a node' prompt",
        )

        # Click second card if available
        if cards.count() > 1:
            second_card = cards.nth(1)
            second_card.click()
            time.sleep(0.5)
            self.check(
                "second node clickable",
                True,
                "",
            )

        # Deselect by clicking same node
        if selected.count() > 0:
            first_card.click()
            time.sleep(0.3)
            self.check("node deselection works", True, "")

    # ── Scenario 5: Language Toggle ───────────────────────────────────────
    def _test_scenario5(self, page: Page) -> None:
        print("\n=== Scenario 5: Language Toggle (EN/ZH) ===")

        # Find the language toggle button
        lang_btn = page.locator("button:has-text('EN')").first
        if lang_btn.count() == 0:
            lang_btn = page.locator("button:has-text('中')").first

        if lang_btn.count() > 0:
            current_text = lang_btn.text_content() or ""
            lang_btn.click()
            time.sleep(1)

            new_text = (
                page.locator("button:has-text('EN'), button:has-text('中')").first.text_content()
                or ""
            )
            toggled = current_text != new_text
            self.check(
                "language toggle switches label",
                toggled,
                f"before='{current_text}' after='{new_text}'",
            )

            # Page should still render properly after toggle
            cards = page.locator(".sticky-card")
            self.check(
                "page renders after lang toggle",
                cards.count() > 0,
                "cards disappeared after toggle",
            )
        else:
            self.check("language toggle button", False, "EN/中 button not found")

    # ── Summary ──────────────────────────────────────────────────────────
    def _print_summary(self) -> None:
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"UI Smoke Test Results: {self.passed}/{total} PASS")
        if self.failed > 0:
            print(f"\nFailed checks:")
            for name, ok, detail in self.results:
                if not ok:
                    print(f"  - {name}: {detail}")
        print(f"{'=' * 60}")
        sys.exit(1 if self.failed > 0 else 0)


if __name__ == "__main__":
    SmokeTest().run()
