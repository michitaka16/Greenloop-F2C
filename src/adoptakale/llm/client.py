"""Dashboard-facing helpers around `adoptakale.utils.llm.chat`.

The low-level client (provider switching, SDK selection, logging) lives
in `adoptakale.utils.llm`. This module only exposes what the Streamlit
code needs:

- `LLMUnavailable` — typed error carrying a user-actionable `.reason`
- `llm_is_configured()` — predicate for gating UI without raising
"""

from __future__ import annotations

import os


class LLMUnavailable(RuntimeError):
    """Raised when LLM env is incomplete. `.reason` is safe to show to the user."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def llm_is_configured() -> bool:
    """True iff `LLM_PROVIDER` and the matching API key + model are set.

    Delegates to `adoptakale.utils.llm._provider_config` so there's one
    source of truth for what "configured" means.
    """
    from dotenv import load_dotenv

    from adoptakale.utils.llm import _provider_config

    load_dotenv(override=False)
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    if not provider:
        return False
    try:
        _provider_config(provider)
    except (ValueError, RuntimeError):
        return False
    return True
