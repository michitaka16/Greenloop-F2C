"""Smoke tests for the greenloop CLI."""

from __future__ import annotations

import subprocess
import sys


def test_cli_shows_help():
    result = subprocess.run(
        [sys.executable, "-m", "greenloop.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "dashboard" in result.stdout
    assert "solve" in result.stdout
    assert "forecast" in result.stdout


def test_cli_solve_prints_profit():
    result = subprocess.run(
        [sys.executable, "-m", "greenloop.cli", "solve"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Profit:" in result.stdout
    assert "SGD" in result.stdout
