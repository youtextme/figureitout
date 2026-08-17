"""LETSCOOK_BUILD.md is a pointer; the contract is RUN_FOREST.md."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUBLIC = REPO / "figureitout" / "public"
STUB = PUBLIC / "LETSCOOK_BUILD.md"


def test_letscook_build_points_at_run_forest():
    text = STUB.read_text(encoding="utf-8")
    assert "RUN_FOREST.md" in text
    assert "truth" in text.lower()


def test_readme_points_at_letscook_or_run_forest():
    readme = (PUBLIC / "README.md").read_text(encoding="utf-8")
    assert "RUN_FOREST.md" in readme
