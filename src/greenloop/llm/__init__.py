"""LLM integration — thin product layer over `greenloop.utils.llm.chat`.

The transport (provider switching, SDK selection, auth, logging) lives
in `greenloop.utils.llm`. This package owns the *product-facing* pieces:
the plan-explainer feature and the dashboard-friendly error type.
"""

from greenloop.llm.client import LLMUnavailable, llm_is_configured
from greenloop.llm.plan_explainer import explain_plan

__all__ = ["LLMUnavailable", "explain_plan", "llm_is_configured"]
