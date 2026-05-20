"""Smoke tests for the adoptakale CLI."""

from __future__ import annotations

import subprocess


def test_cli_shows_help():
    result = subprocess.run(
        ["adoptakale", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "dashboard" in result.stdout
    assert "solve" in result.stdout
    assert "forecast" in result.stdout


def test_cli_solve_prints_profit():
    result = subprocess.run(
        ["adoptakale", "solve"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Profit:" in result.stdout
    assert "SGD" in result.stdout
