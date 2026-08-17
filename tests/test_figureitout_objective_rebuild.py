"""figureItOutObjective.md — Cursor rebuild playbook for the objective runner."""

from __future__ import annotations

import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "figureitout" / "public"
DOC = PUBLIC / "figureItOutObjective.md"


def test_rebuild_doc_exists():
    text = DOC.read_text(encoding="utf-8")
    assert text.startswith("# ")
    assert "figureitout" in text.lower()
    assert "Cursor" in text


def test_rebuild_doc_never_says_f26():
    text = DOC.read_text(encoding="utf-8")
    assert not re.search(r"\bf26\b", text, re.I)
    assert "App.agents" not in text
    assert "Shodh" not in text


def test_rebuild_doc_has_cursor_file_tree():
    text = DOC.read_text(encoding="utf-8")
    for needle in (
        ".cursor/skills/figureitout/SKILL.md",
        "AGENTS.md",
        "python -m figureitout",
        "FIGUREITOUT_LOCKDOWN",
        "planner",
        "worker",
        "evaluator",
        "bar_raiser",
        "synthesizer",
        "tests first",
    ):
        assert needle.lower() in text.lower(), needle


def test_rebuild_doc_links_skill_and_mental_model():
    text = DOC.read_text(encoding="utf-8")
    assert "SKILL.md" in text
    assert "mentalModal.md" in text
    assert "HOW_TO_BUILD.md" in text
    assert "https://github.com/youtextme/figureitout" in text
    assert "https://github.com/anthropics/skills" in text
    assert "https://github.com/langchain-ai/langgraph" in text


def test_rebuild_doc_learning_links_are_github_only():
    hrefs = re.findall(r"https?://[^\s)>\"]+", DOC.read_text(encoding="utf-8"))
    bad = [h for h in hrefs if "github.com" not in h and "githubusercontent.com" not in h]
    assert bad == [], bad


def test_readme_points_at_rebuild_doc():
    readme = (PUBLIC / "README.md").read_text(encoding="utf-8")
    assert "figureItOutObjective.md" in readme
