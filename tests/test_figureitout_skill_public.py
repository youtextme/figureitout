"""Public figureitout skill: plain language, one-prompt install, no ceremony."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PUBLIC = REPO / "figureitout" / "public"
SKILL_PATHS = (
    PUBLIC / "SKILL.md",
    REPO / "figureitout" / "SKILL.md",
    REPO / ".cursor" / "skills" / "figureitout" / "SKILL.md",
)

# Ceremony that does not help a person install or finish work.
BANNED = (
    r"\bS(?:0\d|1\d|2\d|3[0-4])\b",
    r"\bA(?:0\d|1\d|2\d|3\d|4\d|5[01])\b",
    r"\bP(?:0|1[0-6])\b",
    r"\bShodh\b",
    r"Use-Backwards",
    r"Domain-Fit",
    r"eight-method",
    r"recovery matrix",
    r"\bMECE\b",
    r"\bf26\b",
    r"LangGraph",
    r"AutoGen",
    r"CrewAI",
    r"GPT-Researcher",
    r"Promptfoo",
    r"Langfuse",
    r"LiteLLM",
    r"SQLGlot",
    r"MarkItDown",
    r"smolagents",
    r"HELM",
    r"\bCEL\b",
    r"\bDORA\b",
    r"\bBOM\b",
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing {path}"
    return path.read_text(encoding="utf-8")


def test_public_bundle_exists():
    for name in (
        "README.md",
        "SKILL.md",
        "PROMPT.md",
        "AGENTS.md",
        "LICENSE",
        "mentalModal.md",
        "figureItOutObjective.md",
    ):
        assert (PUBLIC / name).exists(), name


def test_skill_frontmatter_and_size():
    text = _read(PUBLIC / "SKILL.md")
    assert text.startswith("---")
    assert "name: figureitout" in text
    assert "alwaysApply: true" in text
    body = text.split("---", 2)[-1]
    assert len(body.splitlines()) <= 120
    assert len(text) < 8000


def test_public_files_have_no_useless_terminology():
    files = [
        PUBLIC / "README.md",
        PUBLIC / "SKILL.md",
        PUBLIC / "PROMPT.md",
        PUBLIC / "AGENTS.md",
        REPO / "figureitout" / "SKILL.md",
        REPO / ".cursor" / "skills" / "figureitout" / "SKILL.md",
        REPO / ".cursor" / "skills" / "letscook" / "SKILL.md",
        REPO / ".cursor" / "skills" / "objective-runner" / "SKILL.md",
    ]
    for path in files:
        text = _read(path)
        for pat in BANNED:
            hits = re.findall(pat, text)
            assert not hits, f"{path.name} still contains {pat}: {hits}"


def test_canonical_skill_copies_match():
    canonical = _read(PUBLIC / "SKILL.md")
    for path in SKILL_PATHS:
        assert _read(path) == canonical, f"drift: {path}"


def test_readme_explains_install_for_every_surface():
    text = _read(PUBLIC / "README.md").lower()
    for word in ("cursor", "devin", "claude", "cli", "install", "prompt"):
        assert word in text, word
    assert "github.com/youtextme/figureitout" in text.lower() or "youtextme/figureitout" in text


def test_prompt_is_self_contained_one_paste():
    text = _read(PUBLIC / "PROMPT.md")
    assert "figureitout" in text.lower()
    assert ".cursor/skills/figureitout/SKILL.md" in text
    words = text.split()
    assert 80 <= len(words) <= 900
    # Must contain the operating loop so a paste works with no network.
    assert "never stop at a plan" in text.lower()
    assert "evidence" in text.lower()


def test_skill_states_epistemic_core():
    text = _read(PUBLIC / "SKILL.md").lower()
    assert "objective" in text
    assert "evidence" in text
    assert "never stop at a plan" in text
    assert "allow" in text  # tells the agent not to ask for Allow
    assert "lockdown" in text


def test_letscook_is_thin_alias():
    text = _read(REPO / ".cursor" / "skills" / "letscook" / "SKILL.md")
    assert "name: letscook" in text
    assert "figureitout" in text.lower()
    assert "/letscook" in text
    assert "S00" not in text
    assert "S34" not in text


def test_objective_runner_is_thin_alias():
    text = _read(REPO / ".cursor" / "skills" / "objective-runner" / "SKILL.md")
    assert "name: objective-runner" in text
    assert "figureitout" in text.lower()
    assert "P0" not in text
    assert "P16" not in text


def test_license_is_permissive():
    text = _read(PUBLIC / "LICENSE")
    assert "MIT" in text
    assert "Permission is hereby granted" in text
