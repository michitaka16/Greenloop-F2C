"""Plain-English narrative for a Layer 2 plan + Layer 1 forecast.

The LLM explains the plan in operator-friendly terms. It does NOT make
operational decisions — Layer 2's MILP output is authoritative. The
narrative is pure translation for the dashboard / VC-pitch audience.

Uses `adoptakale.utils.llm.chat` as the provider-agnostic transport so
OpenAI-, Anthropic-, Z.AI- and MiniMax-compatible endpoints all work
through the same call.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from adoptakale.llm.client import LLMUnavailable
from adoptakale.utils.llm import chat as _default_chat

_SYSTEM_PROMPT = (
    "You are the ops narrator for a Singapore vertical hydroponic farm. "
    "You receive the day's demand forecast and the MILP-optimised operating plan. "
    "Write a concise, operator-facing brief in markdown (2-4 short paragraphs, "
    "no headings). Explain WHY the plan is what it is — which crops dominate the "
    "rack layout and why, the shape of the cost breakdown (energy vs labour vs "
    "waste), how uncertainty buffers were sized, and if a scenario comparison is "
    "provided, what it changes. Use plain English; avoid jargon. Never invent "
    "numbers that aren't in the inputs. Round currency to whole SGD in prose."
)


def _build_user_prompt(
    forecast: dict[str, Any],
    plan: dict[str, Any],
    scenario_comparison: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {"forecast": forecast, "plan": plan}
    if scenario_comparison:
        payload["scenario"] = scenario_comparison
    return (
        "Write the operator brief for this day.\n\n"
        "```json\n" + json.dumps(payload, default=str, indent=2) + "\n```"
    )


def explain_plan(
    forecast: dict[str, Any],
    plan: dict[str, Any],
    scenario_comparison: dict[str, Any] | None = None,
    *,
    chat_fn: Callable[..., str] = _default_chat,
    max_tokens: int = 500,
    temperature: float = 0.4,
) -> str:
    """Return the LLM's markdown brief for this day.

    Raises `LLMUnavailable` on empty output so UI code shows an actionable
    setup hint instead of a blank panel. Provider-level errors (bad key,
    rate limit, network) propagate as-is — the UI surfaces them verbatim.

    `chat_fn` is injected for tests; production callers use the default.
    """
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(forecast, plan, scenario_comparison)},
    ]
    text = chat_fn(messages, max_tokens=max_tokens, temperature=temperature)
    if not text or not text.strip():
        raise LLMUnavailable(
            "LLM returned an empty response. Check the provider's quota and model name."
        )
    return text.strip()
