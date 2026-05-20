"""Tests for `adoptakale.llm.plan_explainer.explain_plan`.

`explain_plan` takes a `chat_fn` injectable so we can stub the transport.
No live API calls.
"""

from __future__ import annotations

import pytest

from adoptakale.llm import LLMUnavailable, explain_plan


_FORECAST = {
    "kai_lan": {"predicted_kg": 48.2, "lower_ci": 34.5, "upper_ci": 68.3},
    "lettuce_mambo": {"predicted_kg": 56.8, "lower_ci": 51.2, "upper_ci": 62.4},
}
_PLAN = {
    "objective_value_sgd": 153.98,
    "solve_time_ms": 40,
    "cost_breakdown": {"revenue": 412.50, "electricity": 120.10, "labour": 138.42},
    "rack_layout": {"tier_0": "kai_lan", "tier_1": "kai_lan"},
}


def _capturing_chat(response_text: str):
    """Build a chat_fn that returns `response_text` and records its inputs."""
    captured: dict = {}

    def chat_fn(messages, *, max_tokens=1024, **kwargs):
        captured["messages"] = messages
        captured["max_tokens"] = max_tokens
        captured["kwargs"] = kwargs
        return response_text

    chat_fn.captured = captured
    return chat_fn


def test_returns_llm_output_stripped():
    chat = _capturing_chat("  Today's plan concentrates on kai lan because...  \n")
    result = explain_plan(_FORECAST, _PLAN, chat_fn=chat)
    assert result == "Today's plan concentrates on kai lan because..."


def test_sends_forecast_and_plan_in_user_prompt():
    chat = _capturing_chat("ok")
    explain_plan(_FORECAST, _PLAN, chat_fn=chat)
    user_msg = next(m for m in chat.captured["messages"] if m["role"] == "user")
    assert "kai_lan" in user_msg["content"]
    assert "objective_value_sgd" in user_msg["content"]
    assert "153.98" in user_msg["content"]


def test_system_prompt_comes_first():
    chat = _capturing_chat("ok")
    explain_plan(_FORECAST, _PLAN, chat_fn=chat)
    assert chat.captured["messages"][0]["role"] == "system"
    assert "hydroponic" in chat.captured["messages"][0]["content"].lower()


def test_includes_scenario_when_provided():
    chat = _capturing_chat("ok")
    scenario = {"name": "typhoon", "delta_profit_sgd": -42.10}
    explain_plan(_FORECAST, _PLAN, scenario_comparison=scenario, chat_fn=chat)
    user_msg = next(m for m in chat.captured["messages"] if m["role"] == "user")
    assert "typhoon" in user_msg["content"]


def test_passes_temperature_and_max_tokens_through():
    chat = _capturing_chat("ok")
    explain_plan(_FORECAST, _PLAN, chat_fn=chat, max_tokens=777, temperature=0.9)
    assert chat.captured["max_tokens"] == 777
    assert chat.captured["kwargs"]["temperature"] == 0.9


def test_empty_response_raises():
    chat = _capturing_chat("")
    with pytest.raises(LLMUnavailable) as excinfo:
        explain_plan(_FORECAST, _PLAN, chat_fn=chat)
    assert "empty" in excinfo.value.reason.lower()


def test_whitespace_only_response_raises():
    chat = _capturing_chat("   \n\t  ")
    with pytest.raises(LLMUnavailable):
        explain_plan(_FORECAST, _PLAN, chat_fn=chat)
