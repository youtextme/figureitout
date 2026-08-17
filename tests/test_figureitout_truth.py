"""Truth store — warrants, kinds, conservation, refuse prose-as-proof."""

from __future__ import annotations

import pytest

from figureitout.memory import append_episode, memory_layout
from figureitout.truth import (
    Claim,
    ClaimKind,
    ProofGrade,
    TruthStore,
    WarrantStatus,
    already_proven,
    cheap_confirm,
    classify_kind,
    grade_proof,
    promote_if_survived,
    split_atoms,
    text_is_not_warrant,
)


def test_unevaluated_fact_is_not_warranted():
    claim = Claim(atom="the file exists", kind=ClaimKind.FACT)
    assert claim.is_warranted() is False
    assert claim.status == WarrantStatus.UNVERIFIED


def test_prose_is_not_a_warrant():
    assert text_is_not_warrant("I read that pytest is always green") is True
    claim = promote_if_survived(
        atom="pytest is green",
        kind=ClaimKind.FACT,
        observation="I read that pytest is always green",
        pointers=[],
        source="experiment",
    )
    assert claim.is_warranted() is False
    assert claim.status == WarrantStatus.UNVERIFIED


def test_illegal_source_cannot_promote():
    with pytest.raises(ValueError):
        promote_if_survived(
            atom="x",
            kind=ClaimKind.FACT,
            observation="file exists",
            pointers=["/tmp/x"],
            source="I read a blog",
        )


def test_experiment_with_pointer_survives(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_HOME", str(tmp_path))
    store = TruthStore(path=tmp_path / "semantic_truth.jsonl")
    claim = promote_if_survived(
        atom="README.md exists in the workspace",
        kind=ClaimKind.FACT,
        observation="glob found README.md size>0",
        pointers=["README.md"],
        source="experiment",
        store=store,
    )
    assert claim.is_warranted() is True
    found = store.lookup("README.md exists in the workspace")
    assert found is not None
    assert found.is_warranted() is True


def test_already_warranted_gets_cheap_ping_not_literature(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_HOME", str(tmp_path))
    store = TruthStore(path=tmp_path / "semantic_truth.jsonl")
    first = promote_if_survived(
        atom="SKILL.md names the loop",
        kind=ClaimKind.FACT,
        observation="file read; loop heading present",
        pointers=["SKILL.md"],
        source="experiment",
        store=store,
    )
    assert first.is_warranted()
    # cheap_confirm uses default store at runner_home()
    ping = cheap_confirm(first, "re-read SKILL.md; loop still present", "SKILL.md")
    assert ping.status == WarrantStatus.SURVIVED
    assert "literature" not in ping.observation.lower()


def test_pink_over_blue_is_preference_not_a_fact():
    assert classify_kind("I need pink over blue") == ClaimKind.PREFERENCE
    assert classify_kind("pytest is green") == ClaimKind.FACT
    atoms = split_atoms("I want pink. Users stay longer on purple.")
    kinds = {a.kind for a in atoms}
    assert ClaimKind.PREFERENCE in kinds
    assert ClaimKind.FACT in kinds


def test_citation_is_not_already_proven():
    cited = Claim(
        atom="paper shows conversion lift for purple",
        kind=ClaimKind.FACT,
        status=WarrantStatus.UNVERIFIED,
        pointers=["https://arxiv.org/abs/0000.0000"],
        observation="I read that the abstract confirms it",
        source="blog",
    )
    assert already_proven(cited) is False
    assert (
        grade_proof(
            observation="I read that the abstract confirms it",
            pointers=["https://arxiv.org/abs/0000.0000"],
            source="blog",
        )
        == ProofGrade.CITATION
    )


def test_replication_and_cheap_ping_are_proof_grades():
    assert (
        grade_proof(
            observation="pytest exit 0 on test_foo",
            pointers=["tests/test_foo.py"],
            source="failed_check",
        )
        == ProofGrade.REPLICATION
    )
    assert (
        grade_proof(
            observation="re-read tests/test_foo.py; still passing",
            pointers=["tests/test_foo.py"],
            source="experiment",
            existing_warranted=True,
        )
        == ProofGrade.CHEAP_PING
    )
    assert (
        grade_proof(observation="", pointers=[], source="")
        == ProofGrade.NONE
    )


def test_memory_layout_has_four_stores(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_HOME", str(tmp_path))
    layout = memory_layout()
    assert set(layout) == {"working", "episodic", "semantic", "procedural"}
    path = append_episode("run1", "laboratory locked an objective", pointers=["lock.md"])
    assert path.exists()
    assert "laboratory locked" in path.read_text(encoding="utf-8")
