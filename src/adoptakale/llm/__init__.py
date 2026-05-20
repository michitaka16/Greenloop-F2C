"""LLM integration — thin product layer over `adoptakale.utils.llm.chat`.

The transport (provider switching, SDK selection, auth, logging) lives
in `adoptakale.utils.llm`. This package owns the *product-facing* pieces:
the plan-explainer feature and the dashboard-friendly error type.
"""

from adoptakale.llm.client import LLMUnavailable, llm_is_configured
from adoptakale.llm.plan_explainer import explain_plan

__all__ = ["LLMUnavailable", "explain_plan", "llm_is_configured"]
