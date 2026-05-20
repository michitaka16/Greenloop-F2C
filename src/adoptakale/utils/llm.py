"""LLM client — provider-switchable via LLM_PROVIDER env var.

Supported providers:
  - openai    → api.openai.com            (OpenAI SDK, chat/completions)
  - zai       → api.z.ai/api/anthropic    (Anthropic SDK, /v1/messages — GLM)
  - minimax   → api.minimax.io/anthropic  (Anthropic SDK, /v1/messages — MiniMax M2.x)
  - anthropic → api.anthropic.com         (Anthropic SDK, /v1/messages — Claude)
  - claude    → api.anthropic.com         (alias for `anthropic`)

Why Anthropic-compatible endpoints for ZAI and MiniMax:
  ZAI's "Coding Plan" keys and MiniMax's newer M2.x models are only exposed
  on the Anthropic-compatible surface. The OpenAI-compatible endpoints are
  restricted to separate paid tiers that most users don't provision.

Usage:
    from adoptakale.utils.llm import chat
    reply = chat([{"role": "user", "content": "Hello"}])
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

_SUPPORTED = {"openai", "zai", "minimax", "anthropic", "claude"}

_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "zai": "https://api.z.ai/api/anthropic",
    "minimax": "https://api.minimax.io/anthropic",
    "anthropic": "https://api.anthropic.com",
    "claude": "https://api.anthropic.com",
}

# Which SDK each provider uses on the wire.
_SDK = {"openai": "openai", "zai": "anthropic", "minimax": "anthropic", "anthropic": "anthropic", "claude": "anthropic"}


def _provider_config(provider: str) -> tuple[str, str, str]:
    """Return (api_key, base_url, model) for the provider, from .env."""
    if provider not in _SUPPORTED:
        raise ValueError(
            f"Unsupported LLM_PROVIDER={provider!r}; choose one of {sorted(_SUPPORTED)}"
        )

    key_env = {
        "openai": "OPENAI_API_KEY",
        "zai": "ZAI_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
    }[provider]
    base_env = {
        "openai": "OPENAI_BASE_URL",
        "zai": "ZAI_BASE_URL",
        "minimax": "MINIMAX_BASE_URL",
        "anthropic": "ANTHROPIC_BASE_URL",
        "claude": "ANTHROPIC_BASE_URL",
    }[provider]
    model_env = {
        "openai": "OPENAI_MODEL",
        "zai": "ZAI_MODEL",
        "minimax": "MINIMAX_MODEL",
        "anthropic": "ANTHROPIC_MODEL",
        "claude": "ANTHROPIC_MODEL",
    }[provider]

    api_key = os.environ.get(key_env)
    if not api_key:
        raise RuntimeError(f"{key_env} is not set — add it to .env (see .env.example)")

    base_url = os.environ.get(base_env, _DEFAULT_BASE_URLS[provider])
    model = os.environ.get(model_env) or os.environ.get("DEFAULT_LLM_MODEL")
    if not model:
        raise RuntimeError(f"{model_env} (or DEFAULT_LLM_MODEL) is not set — add it to .env")
    return api_key, base_url, model


def get_client(provider: str | None = None) -> tuple[Any, str, str]:
    """Build a client for the selected provider.

    Returns (client, model, provider_name). The client is either an
    ``openai.OpenAI`` or ``anthropic.Anthropic`` instance depending on
    the provider's wire protocol.
    """
    provider = (provider or os.environ.get("LLM_PROVIDER") or "openai").lower()
    api_key, base_url, model = _provider_config(provider)
    sdk = _SDK[provider]
    logger.info(
        "llm.client.init",
        extra={"provider": provider, "sdk": sdk, "base_url": base_url, "model": model},
    )
    if sdk == "openai":
        return OpenAI(api_key=api_key, base_url=base_url), model, provider
    return Anthropic(api_key=api_key, base_url=base_url), model, provider


def _split_system(
    messages: list[dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Anthropic API takes `system` as a top-level arg, not a message role."""
    system: str | None = None
    rest: list[dict[str, Any]] = []
    for m in messages:
        if m.get("role") == "system":
            system = (system + "\n\n" + m["content"]) if system else m["content"]
        else:
            rest.append(m)
    return system, rest


def chat(
    messages: list[dict[str, Any]],
    *,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int = 1024,
    **kwargs: Any,
) -> str:
    """Send a chat request and return the assistant text.

    Works uniformly across OpenAI-style and Anthropic-style providers.
    Extra ``kwargs`` (temperature, top_p, ...) are forwarded to the client.
    """
    client, default_model, prov = get_client(provider)
    model_used = model or default_model
    sdk = _SDK[prov]

    logger.info(
        "llm.chat.start",
        extra={"provider": prov, "sdk": sdk, "model": model_used, "n_messages": len(messages)},
    )
    t0 = time.monotonic()
    try:
        if sdk == "openai":
            resp = client.chat.completions.create(
                model=model_used,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs,
            )
            text = resp.choices[0].message.content or ""
            finish = resp.choices[0].finish_reason
        else:  # anthropic
            system, rest = _split_system(messages)
            anth_kwargs: dict[str, Any] = {
                "model": model_used,
                "max_tokens": max_tokens,
                "messages": rest,
            }
            if system:
                anth_kwargs["system"] = system
            anth_kwargs.update(kwargs)
            resp = client.messages.create(**anth_kwargs)
            # resp.content is a list of content blocks; stitch text blocks together.
            text = "".join(
                block.text for block in resp.content if getattr(block, "type", None) == "text"
            )
            finish = resp.stop_reason

        latency_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "llm.chat.ok",
            extra={
                "provider": prov,
                "sdk": sdk,
                "model": model_used,
                "latency_ms": round(latency_ms, 1),
                "finish_reason": finish,
            },
        )
        return text
    except Exception as e:
        latency_ms = (time.monotonic() - t0) * 1000
        logger.exception(
            "llm.chat.error",
            extra={
                "provider": prov,
                "sdk": sdk,
                "model": model_used,
                "latency_ms": round(latency_ms, 1),
                "error": str(e),
            },
        )
        raise
