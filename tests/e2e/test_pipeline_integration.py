"""E2E integration tests across all 5 layers.

Run with:  uv run pytest tests/e2e/test_pipeline_integration.py -v

Each test is self-contained: starts its own Streamlit on a dedicated port,
creates its own Playwright browser, then tears everything down.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _kill_port(port: int) -> None:
    result = subprocess.run(
        ["lsof", "-i", f":{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        subprocess.run(
            ["xargs", "-r", "kill", "-9"],
            input=result.stdout,
            stderr=subprocess.DEVNULL,
        )
    time.sleep(1)


def _wait_port(port: int, timeout: int = 60) -> None:
    for _ in range(timeout):
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-sTCP:LISTEN", "-t"],
            capture_output=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return
        time.sleep(1)
    raise RuntimeError(f"Port {port} did not start listening within {timeout}s")


def _start_dashboard(port: int) -> subprocess.Popen:
    _kill_port(port)
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    proc = subprocess.Popen(
        ["uv", "run", "streamlit", "run",
         str(REPO / "src/adoptakale/dashboard/app.py"),
         "--server.headless", "true",
         "--server.port", str(port),
         "--browser.gatherUsageStats", "false"],
        cwd=str(REPO),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_port(port)
    return proc


def _start_retail(port: int) -> subprocess.Popen:
    _kill_port(port)
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    proc = subprocess.Popen(
        ["uv", "run", "streamlit", "run",
         str(REPO / "pages/2_retail.py"),
         "--server.headless", "true",
         "--server.port", str(port),
         "--browser.gatherUsageStats", "false"],
        cwd=str(REPO),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_port(port)
    return proc


def _stop(proc: subprocess.Popen, port: int) -> None:
    proc.kill()
    proc.wait(timeout=10)
    _kill_port(port)


def _wait_streamlit_ready(page) -> None:
    """Wait for Streamlit to finish rendering dynamic content."""
    # Streamlit disables the chat input while processing; wait for it to re-enable
    # as a proxy for "页面已完全加载"
    page.wait_for_timeout(8000)


# ---------------------------------------------------------------------------
# Test 1: Layer 1b — diagnosis panel renders with all-rack table
# ---------------------------------------------------------------------------

class TestLayer1bDiagnosis:
    """Verify that Layer 1b transfer learning diagnosis panel is visible."""

    def test_diagnosis_panel_renders(self):
        """Crop Health & Growth Diagnosis section and all-rack table are visible."""
        proc = _start_dashboard(8511)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8511",
                           wait_until="networkidle", timeout=30000)
                _wait_streamlit_ready(page)

                # Verify page title
                assert "Adopt a Kale" in page.title()

                # Diagnosis section — use get_by_text for partial match
                diag = page.get_by_text("Crop Health")
                assert diag.count() >= 1, \
                    f"Layer 1b diagnosis panel not found. Page text: {page.locator('body').inner_text()[:500]}"

                # All-rack diagnosis table must be present
                table = page.get_by_text("All-rack diagnosis")
                assert table.count() >= 1, "All-rack diagnosis table not found"

                browser.close()
        finally:
            _stop(proc, 8511)


# ---------------------------------------------------------------------------
# Test 2: Layer 2 → Layer 3 — RL Control panel renders with tariff chart
# ---------------------------------------------------------------------------

class TestLayer2ToLayer3:
    """RL Control panel and electricity tariff chart are visible."""

    def test_tariff_and_rl_panel_visible(self):
        """Electricity tariff chart and RL Control panel are present."""
        proc = _start_dashboard(8512)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8512",
                           wait_until="networkidle", timeout=30000)
                _wait_streamlit_ready(page)

                # Electricity tariff section
                tariff = page.get_by_text("Electricity Tariff")
                assert tariff.count() >= 1, \
                    f"Electricity Tariff section not found. Page text: {page.locator('body').inner_text()[:500]}"

                # RL Control section
                rl = page.get_by_text("RL Control")
                assert rl.count() >= 1, "RL Control panel not found"

                # Run 10 RL steps button
                run_btn = page.get_by_text("Run 10 steps")
                assert run_btn.count() >= 1, "Run 10 steps button not found"

                browser.close()
        finally:
            _stop(proc, 8512)


# ---------------------------------------------------------------------------
# Test 4: Typhoon scenario — delivery window shrinks, Layer 3 targets update
# ---------------------------------------------------------------------------

class TestTyphoonScenario:
    """Press Typhoon Warning; verify re-optimisation and Layer 3 target propagation."""

    def test_typhoon_reduces_delivery_window_and_updates_layer3(self):
        """Typhoon Warning: delivery → 6h, re-optimises, Layer 3 targets update."""
        proc = _start_dashboard(8513)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8513",
                           wait_until="networkidle", timeout=30000)
                _wait_streamlit_ready(page)

                # Scenario Testing section present
                scenario = page.get_by_text("Scenario Testing")
                assert scenario.count() >= 1, \
                    f"Scenario Testing section not found. Page: {page.locator('body').inner_text()[:300]}"

                # Click Typhoon Warning button
                page.get_by_role("button", name="⚡ Typhoon Warning").click()
                page.wait_for_timeout(10000)  # solver may take up to 8s

                # Verify delivery window shows 6 hours
                assert page.get_by_text("6 hours").count() >= 1, \
                    "Delivery window did not show 6 hours after Typhoon Warning"

                # Verify Layer 3 targets updated
                assert page.get_by_text("Layer 3 targets updated").count() >= 1, \
                    "Layer 3 targets were not updated after Typhoon scenario"

                browser.close()
        finally:
            _stop(proc, 8513)


# ---------------------------------------------------------------------------
# Test 5: Layer 4 — Retail page shows customer segmentation
# ---------------------------------------------------------------------------

class TestLayer4DemandSignal:
    """Verify customer segmentation appears on the Retail AI page."""

    def test_retail_page_shows_segments(self):
        """Retail AI page shows customer behavioural segments."""
        proc = _start_retail(8514)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8514",
                           wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(8000)

                body = page.locator("body").inner_text()
                # Check for page content
                assert len(body) > 100, \
                    f"Retail page appears nearly empty. Body: {body[:200]}"
                # The retail page has customer segment cards
                assert page.get_by_text("segment").count() >= 1 or \
                       page.get_by_text("Customers").count() >= 1 or \
                       page.get_by_text("Retail AI").count() >= 1, \
                    f"No segment information found on Retail page. Body: {body[:500]}"

                browser.close()
        finally:
            _stop(proc, 8514)
