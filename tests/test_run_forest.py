"""RUN_FOREST.md — epistemological core. No product recipe first."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "figureitout" / "public" / "RUN_FOREST.md"


def test_run_forest_exists_and_does_not_start_with_a_skill_recipe():
    text = DOC.read_text(encoding="utf-8")
    assert text.startswith("# Run Forest")
    head = "\n".join(text.splitlines()[:40]).lower()
    assert "alwaysapply" not in head
    assert ".cursor/skills" not in head
    assert "pip install" not in head


def test_run_forest_never_says_figureitout():
    text = DOC.read_text(encoding="utf-8")
    assert not re.search(r"figureitout", text, re.I)
    assert "/letscook" not in text.lower()


def test_run_forest_closes_three_tenets():
    text = DOC.read_text(encoding="utf-8")
    assert "### 3.1 Atoms" in text
    assert "### 3.2 Probe" in text
    assert "### 3.3 Conservation" in text
    assert "### 3.1 Correspondence" not in text
    assert "### 3.2 Falsification" not in text
    assert "cannot be added" in text.lower() or "cannot be added to" in text.lower()
    assert "cannot be subtracted" in text.lower() or "subtract" in text.lower()
    assert "What is not a tenet" in text
    assert "True That" in text
    assert "citation" in text.lower()
    assert "cheap ping" in text.lower()


def test_run_forest_teaches_deeming_and_prove_wrong():
    text = DOC.read_text(encoding="utf-8").lower()
    for needle in (
        "prove",
        "disconfirmation",
        "unverified",
        "survived",
        "preference",
        "pink",
        "purple",
        "working memory",
        "episodic",
        "semantic",
        "procedural",
        "research paper",
        "change how you look",
    ):
        assert needle in text, needle


def test_run_forest_build_comes_last():
    text = DOC.read_text(encoding="utf-8")
    impl = text.find("how one might implement")
    tenets = text.find("Three tenets")
    assert tenets != -1 and impl != -1
    assert tenets < impl


def test_readme_points_at_run_forest():
    readme = (REPO / "figureitout" / "public" / "README.md").read_text(encoding="utf-8")
    assert "RUN_FOREST.md" in readme


def test_runforest_skill_is_thin_and_points_at_core():
    skill = (REPO / ".cursor" / "skills" / "runforest" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: runforest" in skill
    assert "RUN_FOREST.md" in skill
    assert "atoms" in skill.lower()
    assert "probe" in skill.lower()
    assert "conservation" in skill.lower()
    assert "True That" in skill or "true that" in skill.lower()
    assert "alwaysApply" not in skill
    assert len(skill.splitlines()) < 40
