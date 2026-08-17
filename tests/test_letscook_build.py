"""LETSCOOK_BUILD.md — from-scratch rebuild contract any model can follow."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "figureitout" / "public" / "LETSCOOK_BUILD.md"


def test_letscook_build_playbook_exists_and_is_followable():
    text = DOC.read_text(encoding="utf-8")
    assert text.startswith("# /letscook")
    assert "figureitout" in text.lower()
    assert "/letscook" in text
    # Step-by-step rebuild exists
    assert "Step-by-step rebuild" in text
    assert "Write **failing** tests" in text or "failing tests" in text.lower()


def test_letscook_build_encodes_complexity_router():
    text = DOC.read_text(encoding="utf-8")
    assert "classify_complexity" in text
    assert "papercut" in text
    assert "where is run_objective defined" in text
    assert "just research" in text.lower()


def test_letscook_build_encodes_every_tenet_as_a_predicate():
    text = DOC.read_text(encoding="utf-8").lower()
    for needle in (
        "all_required_true",
        "first principles",
        "preview",
        "experiment",
        "frontier",
        "flaws.md",
        "next action",
        "steer",
        "operator",
        "checkpoint.json",
    ):
        assert needle in text, needle


def test_letscook_build_points_at_public_github():
    text = DOC.read_text(encoding="utf-8")
    for url in (
        "https://github.com/youtextme/figureitout",
        "https://github.com/anthropics/skills",
        "https://github.com/langchain-ai/langgraph",
        "https://github.com/stanfordnlp/dspy",
        "https://github.com/UKGovernmentBEIS/inspect_ai",
    ):
        assert url in text, url


def test_readme_points_at_letscook_build():
    readme = (REPO / "figureitout" / "public" / "README.md").read_text(encoding="utf-8")
    assert "LETSCOOK_BUILD.md" in readme
