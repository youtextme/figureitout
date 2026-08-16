"""Layer 3 — structured planning."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

import pytest
from pydantic import ValidationError

from figureitout.planner import Plan, Task, plan_objective


def test_plan_objective_typed():
    plan = plan_objective("build a todo app")
    assert isinstance(plan, Plan)
    assert 1 <= len(plan.tasks) <= 5
    for task in plan.tasks:
        assert task.success_criteria.strip() != ""


def test_task_validation_rejects_bad_type():
    with pytest.raises(ValidationError):
        Task(
            name="x",
            description="y",
            success_criteria="z",
            task_type="not-a-type",  # type: ignore[arg-type]
        )


def test_plan_passes_judge_bar():
    from figureitout.judge import judge_task

    plan = plan_objective("build a todo app")
    # Rationale itself is a useful artefact for the judge smoke check.
    task = Task(
        name="plan_quality",
        description="Validate plan quality",
        success_criteria="Plan has tasks with success criteria",
        task_type="analyse",
    )
    output = plan.model_dump_json()
    result = judge_task(task, output)
    assert result.score >= 80


def test_mock_plan_has_depends_on_chain():
    plan = plan_objective("build a todo app")
    assert any(t.depends_on for t in plan.tasks)
    names = {t.name for t in plan.tasks}
    for t in plan.tasks:
        for dep in t.depends_on:
            assert dep in names


def test_plan_prompt_helpers_include_foundation_up():
    from figureitout.planner import PLAN_SYSTEM_PROMPT

    lower = PLAN_SYSTEM_PROMPT.lower()
    assert "done criteria" in lower or "success criteria" in lower
    assert "foundation" in lower or "research-first" in lower or "research first" in lower
    assert "mock" in lower or "stub" in lower


def test_local_llm_failure_marks_plan_degraded(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    calls = {"n": 0}

    def boom(*_a, **_k):
        calls["n"] += 1
        raise RuntimeError("planner unavailable")

    monkeypatch.setattr("figureitout.planner._instructor_client", boom)

    plan = plan_objective("harden the runner against shallow stubs")
    assert plan.degraded is True
    assert calls["n"] >= 2  # retry once
    types = [t.task_type for t in plan.tasks]
    assert "research" in types
    assert any(t.task_type in {"code", "write", "analyse"} for t in plan.tasks)
    # Forced verify-style task present
    assert any("verif" in t.name.lower() or "verif" in t.description.lower() for t in plan.tasks)
