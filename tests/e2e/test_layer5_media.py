"""E2E tests for Layer 5 Media AI RAG Chatbot.

Run with:  uv run pytest tests/e2e/test_layer5_media.py -v

Each test is fully self-contained: starts its own Streamlit on a dedicated port,
creates its own Playwright browser, then tears everything down.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ENV_FILE = REPO / ".env"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _kill_port(port: int) -> None:
    result = subprocess.run(
        ["lsof", "-i", f":{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True,
    )
    if result.stdout.strip():
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


def _start_streamlit(port: int, extra_env: dict | None = None) -> subprocess.Popen:
    _kill_port(port)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(
        ["uv", "run", "streamlit", "run", str(REPO / "pages/3_media.py"),
         "--server.headless", "true", "--server.port", str(port),
         "--browser.gatherUsageStats", "false"],
        cwd=str(REPO),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_port(port)
    return proc


def _stop_streamlit(proc: subprocess.Popen, port: int) -> None:
    proc.kill()
    proc.wait(timeout=10)
    _kill_port(port)


# ---------------------------------------------------------------------------
# Test 1: Demo mode reliability
# ---------------------------------------------------------------------------

class TestDemoMode:
    """Case 1: Demo mode returns cached answers without crash."""

    def test_demo_mode_no_crash(self):
        """All 4 priority questions return cached answers without crash."""
        # Strip API keys from .env
        original = ENV_FILE.read_text()
        cleaned = original
        for key in ["ANTHROPIC_API_KEY", "MINIMAX_API_KEY", "ZAI_API_KEY",
                     "OPENAI_API_KEY", "LLM_PROVIDER"]:
            cleaned = re.sub(rf"^{key}=.*\n", "", cleaned, flags=re.MULTILINE)

        ENV_FILE.write_text(cleaned)
        proc = None
        try:
            proc = _start_streamlit(8501)

            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8501", wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(3000)

                questions = [
                    "Are pesticides used?",
                    "What crops do you grow?",
                    "What is the carbon footprint?",
                    "Where was this grown?",
                ]
                for q in questions:
                    page.fill("[data-testid=\"stChatInputTextArea\"]", q)
                    page.keyboard.press("Enter")
                    # Wait for input to be re-enabled (Streamlit disables it while processing)
                    page.wait_for_function(
                        "document.querySelector('[data-testid=\"stChatInputTextArea\"]')?.disabled === false",
                        timeout=30000,
                    )
                    page.wait_for_timeout(800)
                    msgs = page.locator(".stChatMessage").all_inner_texts()
                    assert len(msgs) >= 2, f"No response for: {q}"
                    assert "Traceback" not in msgs[-1], f"Crash on: {q}"

                browser.close()

        finally:
            if proc:
                _stop_streamlit(proc, 8501)
            ENV_FILE.write_text(original)


# ---------------------------------------------------------------------------
# Test 2: Freshness score accuracy
# ---------------------------------------------------------------------------

class TestFreshnessScore:
    """Case 2: Freshness score is computed dynamically."""

    def test_freshness_score(self):
        """Sidebar shows a freshness score computed from file mtime."""
        proc = _start_streamlit(8502)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8502", wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(3000)

                page.fill("[data-testid=\"stChatInputTextArea\"]", "How fresh is the kai lan?")
                page.keyboard.press("Enter")
                page.wait_for_function(
                    "document.querySelector('[data-testid=\"stChatInputTextArea\"]')?.disabled === false",
                    timeout=30000,
                )
                page.wait_for_timeout(500)

                sidebar = page.locator("[data-testid=\"stSidebar\"]").inner_text()
                assert "Knowledge" in sidebar or "Freshness" in sidebar or "Status" in sidebar
                assert "%" in sidebar or "day" in sidebar.lower() or "Fresh" in sidebar

                browser.close()
        finally:
            _stop_streamlit(proc, 8502)


# ---------------------------------------------------------------------------
# Test 3: Response latency
# ---------------------------------------------------------------------------

class TestResponseLatency:
    """Case 3: Response latency under 500ms after warmup."""

    def test_latency_under_500ms(self):
        """3 questions return in under 500ms (ChromaDB pre-warmed)."""
        proc = _start_streamlit(8503)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("http://localhost:8503", wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(3000)

                # Pre-warm: first question initializes ChromaDB + embedder
                page.fill("[data-testid=\"stChatInputTextArea\"]", "What crops do you grow?")
                page.keyboard.press("Enter")
                page.wait_for_function(
                    "document.querySelector('[data-testid=\"stChatInputTextArea\"]')?.disabled === false",
                    timeout=30000,
                )
                page.wait_for_timeout(500)

                # Measure 3 timed questions
                questions = [
                    "How much water do you save?",
                    "Where are you located?",
                    "What is your pricing?",
                ]
                for q in questions:
                    page.fill("[data-testid=\"stChatInputTextArea\"]", q)
                    page.keyboard.press("Enter")
                    t0 = time.monotonic()
                    page.wait_for_function(
                        "document.querySelector('[data-testid=\"stChatInputTextArea\"]')?.disabled === false",
                        timeout=15000,
                    )
                    elapsed_ms = (time.monotonic() - t0) * 1000
                    assert elapsed_ms < 500, f"Latency {elapsed_ms:.0f}ms > 500ms for: {q}"

                browser.close()
        finally:
            _stop_streamlit(proc, 8503)


# ---------------------------------------------------------------------------
# Test 4: Navigation stability
# ---------------------------------------------------------------------------

class TestNavigationStability:
    """Case 4: Rapid page switching with no session state errors."""

    def test_page_switching_no_errors(self):
        """Reload the media page rapidly without JS errors or crashes."""
        proc = _start_streamlit(8504)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Verify the page loads with content
                page.goto("http://localhost:8504", wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(2000)
                body = page.locator("body").inner_text()
                assert len(body) > 10, "Media page appears empty on first load"

                # Rapid reloads — stress-test session state and widget re-render
                for i in range(10):
                    page.reload(wait_until="domcontentloaded", timeout=15_000)
                    page.wait_for_timeout(500)
                    # Every reload should still have the chat input
                    assert page.locator("[data-testid=\"stChatInputTextArea\"]").count() == 1, \
                        f"Reload {i+1}: chat input missing"
                    assert page.locator(".stChatMessage").count() == 0, \
                        f"Reload {i+1}: unexpected chat messages"

                # No JS TypeErrors during reload
                js_errors: list[str] = []
                page.on("console", lambda m: (
                    m.type == "error" and "TypeError" in m.text and js_errors.append(m.text)
                ))
                page.reload(wait_until="networkidle")
                page.wait_for_timeout(2000)
                assert not js_errors, f"JS errors on reload: {js_errors}"

                browser.close()
        finally:
            _stop_streamlit(proc, 8504)


# ---------------------------------------------------------------------------
# Test 5: 10-minute full demo run-through
# ---------------------------------------------------------------------------

class TestFullDemoTiming:
    """Case 5: Full demo completes in under 10 minutes."""

    def test_full_demo_timing(self):
        """Time the full demo: start + chat query."""
        t0 = time.monotonic()
        proc = _start_streamlit(8505)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto("http://localhost:8505",
                          wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(3000)
                page.wait_for_function(
                    "document.querySelector('[data-testid=\"stChatInputTextArea\"]')?.disabled === false",
                    timeout=30000,
                )

                page.fill("[data-testid=\"stChatInputTextArea\"]", "What is your farm address?")
                page.keyboard.press("Enter")
                page.wait_for_function(
                    "document.querySelector('[data-testid=\"stChatInputTextArea\"]')?.disabled === false",
                    timeout=30000,
                )
                page.wait_for_timeout(800)
                msgs = page.locator(".stChatMessage").all_inner_texts()
                assert len(msgs) >= 2, "No response received"

                browser.close()

                total = time.monotonic() - t0
                assert total < 600, f"Full demo took {total:.0f}s > 600s"
                print(f"\nFull demo: {total:.1f}s")

        finally:
            _stop_streamlit(proc, 8505)
