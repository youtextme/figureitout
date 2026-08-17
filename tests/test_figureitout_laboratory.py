"""Laboratory lifecycle — predicates, first principles, checkpoint, skill."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from figureitout.checkpoint import load_checkpoint, save_checkpoint
from figureitout.lifecycle import (
    PHASES,
    classify_quality_tier,
    evaluate_laboratory,
    run_laboratory,
)
from figureitout.objective_fn import (
    EvaluationContext,
    Predicate,
    PredicateBoard,
    PredicateKind,
)


def test_unevaluated_required_predicate_is_false():
    board = PredicateBoard(
        predicates=[
            Predicate(
                id="file",
                statement="result.md exists",
                kind=PredicateKind.FILE_EXISTS,
                target="result.md",
                required=True,
            )
        ]
    )
    assert board.all_required_true() is False
    assert board.unevaluated_required() == ["file"]


def test_predicate_cannot_pass_without_evidence(tmp_path: Path):
    target = tmp_path / "result.md"
    board = PredicateBoard(
        predicates=[
            Predicate(
                id="file",
                statement="result.md exists and is non-empty",
                kind=PredicateKind.FILE_EXISTS,
                target=str(target),
                required=True,
            )
        ]
    )
    ctx = EvaluationContext(final_output="", job_dir=tmp_path)
    board.evaluate(ctx)
    assert board.all_required_true() is False

    target.write_text("usable output\n", encoding="utf-8")
    board.evaluate(ctx)
    assert board.all_required_true() is True
    assert board.predicates[0].evidence


def test_text_contains_predicate_needs_the_needle():
    board = PredicateBoard(
        predicates=[
            Predicate(
                id="hello",
                statement="Output contains hello",
                kind=PredicateKind.TEXT_CONTAINS,
                target="hello",
                required=True,
            )
        ]
    )
    ctx = EvaluationContext(final_output="goodbye", job_dir=Path("."))
    board.evaluate(ctx)
    assert board.all_required_true() is False
    ctx = EvaluationContext(final_output="Hello, World!", job_dir=Path("."))
    board.evaluate(ctx)
    assert board.all_required_true() is True


def test_hello_world_is_trivial_and_standard_is_not():
    assert classify_quality_tier("write hello world") == "trivial"
    assert classify_quality_tier("build an executive research pack with live sources") == "standard"


def test_laboratory_writes_first_principles_experiments_board_use_steer(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_JOBS_DIR", str(tmp_path))
    monkeypatch.setenv("FIGUREITOUT_MOCK", "1")
    lab = run_laboratory("write hello world")
    job = Path(lab.job_dir)
    for name in (
        "objective_lock.md",
        "first_principles.md",
        "context_brief.md",
        "experiments.md",
        "board.md",
        "flaws.md",
        "use.md",
        "steer.md",
        "checkpoint.json",
        "predicates.json",
    ):
        assert (job / name).exists(), name
        assert (job / name).stat().st_size > 0, name

    principles = (job / "first_principles.md").read_text(encoding="utf-8").lower()
    for needle in ("irreducible", "assumption", "reuse", "frontier"):
        assert needle in principles, needle

    experiments = (job / "experiments.md").read_text(encoding="utf-8").lower()
    assert "hypothesis" in experiments
    assert "observation" in experiments
    assert "i read that" not in experiments

    use = (job / "use.md").read_text(encoding="utf-8").lower()
    assert "next action" in use
    assert "filler" in use or "slop" in use or "usable" in use

    steer = (job / "steer.md").read_text(encoding="utf-8").lower()
    assert "question" in steer
    assert "proceed" in steer

    board = (job / "board.md").read_text(encoding="utf-8").lower()
    for seat in ("operator", "skeptic", "verifier", "communicator"):
        assert seat in board, seat

    flaws = (job / "flaws.md").read_text(encoding="utf-8").lower()
    for flaw in ("hallucin", "plan", "invent"):
        assert flaw in flaws, flaw


def test_checkpoint_round_trip_lets_another_agent_resume(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_JOBS_DIR", str(tmp_path))
    lab = run_laboratory("write hello world")
    loaded = load_checkpoint(lab.run_id)
    assert loaded is not None
    assert loaded["run_id"] == lab.run_id
    assert loaded["objective"] == "write hello world"
    assert loaded["done_sentence"]
    assert loaded["phase"] in PHASES
    assert loaded["predicates"]
    assert loaded["next_action"]

    loaded["phase"] = "compute"
    loaded["next_action"] = "execute remaining tasks"
    save_checkpoint(lab.run_id, loaded)
    again = load_checkpoint(lab.run_id)
    assert again["phase"] == "compute"
    assert again["next_action"] == "execute remaining tasks"


def test_frontier_catalog_is_github_and_current():
    from figureitout.lifecycle import frontier_for

    items = frontier_for("research and reason about a dashboard")
    urls = {item["url"] for item in items}
    for url in (
        "https://github.com/langchain-ai/langgraph",
        "https://github.com/stanfordnlp/dspy",
        "https://github.com/UKGovernmentBEIS/inspect_ai",
        "https://github.com/openai/openai-agents-python",
        "https://github.com/modelcontextprotocol/python-sdk",
    ):
        assert url in urls, url
    assert all(u.startswith("https://github.com/") for u in urls)


def test_evolve_queues_proposal_and_does_not_rewrite_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_HOME", str(tmp_path / "home"))
    from figureitout.lifecycle import queue_lesson

    path = queue_lesson(
        "write hello world",
        "empty stdout is not a result",
        source="experiment",
    )
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["source"] == "experiment"
    assert payload["status"] == "preview"
    assert "empty stdout" in payload["lesson"]


def test_run_objective_hello_world_still_done_and_has_lab(tmp_path, monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_JOBS_DIR", str(tmp_path))
    monkeypatch.setenv("FIGUREITOUT_MOCK", "1")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from figureitout.runner import run_objective

    result = run_objective("write hello world")
    assert result["status"] == "done"
    assert "hello" in str(result.get("final_output", "")).lower()
    assert result.get("run_id")
    job = tmp_path / result["run_id"]
    assert (job / "checkpoint.json").exists()
    assert (job / "objective_lock.md").exists()


def test_evaluate_laboratory_blocks_done_when_predicates_fail(tmp_path):
    board = PredicateBoard(
        predicates=[
            Predicate(
                id="hello",
                statement="Output contains hello",
                kind=PredicateKind.TEXT_CONTAINS,
                target="hello",
                required=True,
            )
        ]
    )
    ctx = EvaluationContext(final_output="not the noun", job_dir=tmp_path)
    status, evaluated = evaluate_laboratory("done", board, ctx)
    assert status == "partial"
    assert evaluated.all_required_true() is False


def test_skill_teaches_laboratory_without_ceremony():
    skill = (Path(__file__).resolve().parents[1] / "figureitout" / "public" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    lower = skill.lower()
    for needle in (
        "first principles",
        "predicate",
        "experiment",
        "checkpoint",
        "do not answer immediately",
        "steer",
        "--resume",
    ):
        assert needle in lower, needle
    body = skill.split("---", 2)[-1]
    assert len(body.splitlines()) <= 120
