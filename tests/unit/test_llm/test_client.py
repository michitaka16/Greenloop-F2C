"""Tests for `llm_is_configured` and `LLMUnavailable`.

These gate the dashboard's AI-narrative UI. Unit tests only — no live
API calls.
"""

from __future__ import annotations

import pytest

from adoptakale.llm import LLMUnavailable, llm_is_configured


_LLM_ENVS = [
    "LLM_PROVIDER", "DEFAULT_LLM_MODEL",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL",
    "ZAI_API_KEY", "ZAI_BASE_URL", "ZAI_MODEL",
    "MINIMAX_API_KEY", "MINIMAX_BASE_URL", "MINIMAX_MODEL",
]


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Strip every LLM-related env var + neutralize dotenv so nothing
    leaks in from the developer's real .env file.

    `llm_is_configured` imports `dotenv.load_dotenv` at call time, so we
    patch the canonical symbol in the `dotenv` module — any consumer
    looking up `dotenv.load_dotenv` after monkeypatch gets the no-op."""
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: False)
    for k in _LLM_ENVS:
        monkeypatch.delenv(k, raising=False)


def test_unavailable_carries_reason():
    err = LLMUnavailable("MINIMAX_API_KEY is not set")
    assert err.reason == "MINIMAX_API_KEY is not set"
    assert str(err) == "MINIMAX_API_KEY is not set"


def test_not_configured_when_provider_missing():
    assert llm_is_configured() is False


def test_not_configured_when_provider_invalid(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")  # not in _SUPPORTED
    assert llm_is_configured() is False


def test_not_configured_when_api_key_missing(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M1")
    assert llm_is_configured() is False


def test_not_configured_when_model_missing(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
    assert llm_is_configured() is False


def test_configured_with_full_minimax_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "sk-mm-test")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M1")
    assert llm_is_configured() is True


def test_configured_with_zai_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "zai")
    monkeypatch.setenv("ZAI_API_KEY", "sk-zai-test")
    monkeypatch.setenv("ZAI_MODEL", "glm-4.6")
    assert llm_is_configured() is True


def test_default_model_is_fallback(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-o-test")
    monkeypatch.setenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
    assert llm_is_configured() is True


def test_provider_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "MiniMax")
    monkeypatch.setenv("MINIMAX_API_KEY", "sk")
    monkeypatch.setenv("MINIMAX_MODEL", "x")
    assert llm_is_configured() is True
