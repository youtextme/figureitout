"""mentalModal.md — full operating-law rewrite, public links, no F26."""

from __future__ import annotations

import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "figureitout" / "public"
MODAL = PUBLIC / "mentalModal.md"

PUBLIC_REPOS = (
    "https://github.com/langchain-ai/langgraph",
    "https://github.com/anthropics/skills",
    "https://github.com/promptfoo/promptfoo",
    "https://github.com/BerriAI/litellm",
    "https://github.com/ollama/ollama",
    "https://github.com/assafelovic/gpt-researcher",
    "https://github.com/huggingface/smolagents",
    "https://github.com/langfuse/langfuse",
    "https://github.com/567-labs/instructor",
    "https://github.com/mem0ai/mem0",
    "https://github.com/microsoft/autogen",
    "https://github.com/crewAIInc/crewAI",
    "https://github.com/microsoft/markitdown",
    "https://github.com/tobymao/sqlglot",
    "https://github.com/evidence-dev/evidence",
    "https://github.com/microsoft/playwright",
    "https://github.com/chartjs/Chart.js",
    "https://github.com/cli/cli",
    "https://github.com/pydantic/pydantic-ai",
)

THEME_MARKERS = (
    "### Frame",
    "### Force the run",
    "### Host and backends",
    "### Thin parent",
    "### Status while waiting",
    "### Objective lock",
    "### First-principles defaults",
    "### Standing governance",
    "### Source inventory",
    "### Prove the method wrong",
    "### Expert board",
    "### Noun match",
    "### Route by intent",
    "### Known queries first",
    "### Plan, work, judge, replan",
    "### Memory that is not chat",
    "### Data cascade",
    "### No invented numbers",
    "### Warehouse proves",
    "### Sniff every number",
    "### Lineage under the chart",
    "### Light UI, proven done",
    "### Work backwards from use",
    "### Preview before default",
    "### Predicate truth",
    "### Multi-lens judge",
    "### Recover missing output",
    "### Continue if the runner is sick",
    "### Click the customer path",
    "### Claims need links",
    "### Private publish only",
    "### Engineering excellence",
    "### Learn after the run",
    "### Public composition",
    "### Internalize the cascade",
)


def test_mental_modal_exists_and_names_figureitout():
    text = MODAL.read_text(encoding="utf-8")
    assert "figureitout" in text.lower()
    assert "/letscook" in text


def test_mental_modal_never_says_f26():
    text = MODAL.read_text(encoding="utf-8")
    assert not re.search(r"\bf26\b", text, re.I)
    assert "App.agents" not in text
    assert "Shodh" not in text
    assert "Jot" not in text


def test_mental_modal_has_all_thirty_five_themes():
    text = MODAL.read_text(encoding="utf-8")
    missing = [m for m in THEME_MARKERS if m not in text]
    assert missing == []
    assert len(THEME_MARKERS) == 35


def test_mental_modal_covers_fifty_one_atoms():
    text = MODAL.read_text(encoding="utf-8")
    ids = re.findall(r"\bA(?:0[1-9]|[1-4]\d|5[01])\b", text)
    assert set(ids) == {f"A{i:02d}" for i in range(1, 52)}


def test_mental_modal_links_every_public_repo():
    text = MODAL.read_text(encoding="utf-8")
    missing = [u for u in PUBLIC_REPOS if u not in text]
    assert missing == []


def test_mental_modal_learning_links_are_github_only():
    text = MODAL.read_text(encoding="utf-8")
    hrefs = re.findall(r"https?://[^\s)>\"]+", text)
    non_gh = [
        h for h in hrefs
        if "github.com" not in h and "githubusercontent.com" not in h
    ]
    assert non_gh == [], non_gh


def test_readme_points_at_mental_modal():
    readme = (PUBLIC / "README.md").read_text(encoding="utf-8")
    assert "mentalModal.md" in readme
