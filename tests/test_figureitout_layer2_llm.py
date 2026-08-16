"""Layer 2 — unified LLM interface."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

from langchain_core.messages import HumanMessage

from figureitout.llm import get_llm, ping_llm


def test_get_llm_returns_nonempty_content():
    content = get_llm().invoke([HumanMessage(content="say hi")]).content
    assert content is not None
    assert str(content).strip() != ""


def test_ping_llm():
    assert ping_llm().strip() != ""


def test_provider_switch_mock():
    llm = get_llm()
    assert llm._llm_type == "figureitout-mock"
