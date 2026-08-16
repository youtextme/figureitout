"""Layer 7 — HELM bar raiser."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

from figureitout.bar_raiser import BarRaiserResult, bar_raise


def test_bar_raise_rejects_trivial_output():
    result = bar_raise(
        "build a production-ready multi-tenant todo platform with auth",
        "Nope",
    )
    assert isinstance(result, BarRaiserResult)
    assert result.total < 85
    assert result.passed is False


def test_bar_raise_accepts_solid_hello_world():
    result = bar_raise(
        "write hello world",
        "```python\nprint('Hello, World!')\n```\nDeliverable complete and verified.",
    )
    assert result.passed is True
    assert result.total >= 85


def test_weakest_dimension_present():
    result = bar_raise("complex objective needing depth", "ok")
    assert result.weakest_dimension in {
        "accuracy",
        "calibration",
        "robustness",
        "fairness",
        "efficiency",
    }


def test_bar_raise_rejects_shallow_stub_under_local(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    result = bar_raise(
        "harden figureitout research and planning",
        "Completed task implement. Hello world stub output padded to look long enough for len checks.",
    )
    assert result.passed is False
    assert result.total < 85


def test_bar_raise_accepts_substantive_local_output(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    result = bar_raise(
        "harden figureitout research and planning",
        (
            "Implemented foundation-up planner with planning flags, research fallback without "
            "invented URLs, multi-turn worker tool loop, evidence-based judge for code tasks, "
            "and synthesiser done-criteria validation. Verified via pytest layer tests."
        ),
    )
    assert result.passed is True


def test_bar_raise_rejects_worker_fallback_http_500():
    result = bar_raise(
        "research bag deals thoroughly",
        (
            "Worker fallback for document. Error code: 500. "
            "Max retries exceeded — pretending research is done with padding text here."
        ),
    )
    assert result.passed is False
    assert result.total < 85


def test_bar_raise_rejects_example_com_when_not_mock(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    result = bar_raise(
        "research live pricing sources",
        "Collected sources from https://example.com/pricing and summarized deals.",
    )
    assert result.passed is False
    assert result.total < 85
