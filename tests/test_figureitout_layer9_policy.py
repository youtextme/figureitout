"""Layer 9 — CEL permission policy."""

from __future__ import annotations

import pytest

from figureitout.policy import PolicyViolationError, check_policy, load_policies


@pytest.fixture(autouse=True)
def _force_sandbox(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_TRUSTED", "0")
    monkeypatch.delenv("FIGUREITOUT_LOCKDOWN", raising=False)


def test_research_blocks_shell():
    with pytest.raises(PolicyViolationError):
        check_policy("research", "shell", {})


def test_research_allows_search():
    assert check_policy("research", "search", {"action": "search"}) is True


def test_policies_load():
    policies = load_policies()
    assert "research" in policies
    assert "build" in policies
    assert "deploy" in policies
    assert "trusted" in policies
