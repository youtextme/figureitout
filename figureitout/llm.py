"""Layer 2 — unified LLM interface. Nodes import from here only."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from figureitout.config import (
    anthropic_model,
    llm_provider,
    local_base_url,
    local_model,
    openai_model,
    use_mock,
)


class _MockChatModel(BaseChatModel):
    """Deterministic chat model for offline / CI verification."""

    model_name: str = "figureitout-mock"

    @property
    def _llm_type(self) -> str:
        return "figureitout-mock"

    def _generate(self, messages: list[Any], stop: list[str] | None = None, **kwargs: Any):
        from langchain_core.outputs import ChatGeneration, ChatResult
        from langchain_core.messages import AIMessage

        text = " ".join(getattr(m, "content", str(m)) for m in messages).lower()
        if "say hi" in text or "hi" in text:
            content = "hi"
        else:
            content = "Mock LLM response for figureitout verification."
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])


def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """Return a swappable chat model based on LLM_PROVIDER.

    Providers:
      - kilocode (default): Kilo Gateway free daily credits, then other models
      - local: OpenAI-compatible tireless-router / Ollama
      - anthropic: ChatAnthropic
      - openai: ChatOpenAI
      - mock: deterministic stub
    """
    if use_mock() or llm_provider() == "mock":
        return _MockChatModel()

    provider = llm_provider()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=anthropic_model(), temperature=temperature)
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=openai_model(), temperature=temperature)
    if provider == "kilocode":
        from langchain_openai import ChatOpenAI

        from figureitout.kilocode import KILOCODE_BASE_URL, kilocode_api_key, kilocode_model

        return ChatOpenAI(
            model=kilocode_model(),
            temperature=temperature,
            base_url=KILOCODE_BASE_URL,
            api_key=kilocode_api_key() or "anonymous",
        )
    # local / tireless / ollama — unlimited local inference by design
    from langchain_openai import ChatOpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "local-no-key")
    return ChatOpenAI(
        model=local_model(),
        temperature=temperature,
        base_url=local_base_url(),
        api_key=api_key,
    )


def ping_llm() -> str:
    """Smoke-check the configured LLM. Used by Layer 2 verification."""
    result = get_llm().invoke([HumanMessage(content="say hi")])
    content = getattr(result, "content", "") or ""
    if isinstance(content, list):
        content = "".join(str(part) for part in content)
    return str(content)
