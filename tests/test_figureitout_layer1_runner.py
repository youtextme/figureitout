"""Layer 1 — core LangGraph loop."""

from __future__ import annotations

import os

import pytest

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["FIGUREITOUT_TRUSTED"] = "0"  # sandbox assertions
os.environ.setdefault("LLM_PROVIDER", "mock")


from figureitout.runner import (
    evaluator_node,
    graph,
    order_tasks_by_depends,
    run_objective,
    synthesiser_node,
)


def test_hello_world_traverses_to_done():
    result = graph.invoke({"objective": "write hello world", "retries": 0})
    assert isinstance(result, dict)
    assert result.get("status") == "done"
    assert float(result.get("judge_score", 0)) >= 80
    assert float(result.get("bar_raiser_score", 0)) >= 85


def test_run_objective_public_api():
    result = run_objective("write hello world")
    assert result["status"] == "done"
    assert "hello" in str(result.get("final_output", "")).lower()


def test_bad_objective_can_partial_or_replan():
    # Extremely empty worker path still returns a typed status.
    result = run_objective("x")
    assert result.get("status") in {"done", "partial", "replan"}


def test_order_tasks_by_depends_honors_edges():
    tasks = [
        {"name": "implement", "depends_on": ["design"], "description": "i", "success_criteria": "c", "task_type": "code"},
        {"name": "research", "depends_on": [], "description": "r", "success_criteria": "c", "task_type": "research"},
        {"name": "design", "depends_on": ["research"], "description": "d", "success_criteria": "c", "task_type": "analyse"},
    ]
    ordered = order_tasks_by_depends(tasks)
    names = [t["name"] for t in ordered]
    assert names.index("research") < names.index("design") < names.index("implement")


def test_synthesiser_rejects_shallow_when_done_criteria_unmet():
    state = {
        "objective": "build a production todo app with tests and auth",
        "status": "done",
        "bar_raiser_score": 90.0,
        "judge_score": 90.0,
        "retries": 0,
        "task_outputs": {"implement": "Completed task implement. Hello stub."},
        "final_output": "Completed task implement. Hello stub.",
        "degraded": False,
        "done_criteria": "Working app with tests and auth",
    }
    out = synthesiser_node(state)
    assert out["status"] in {"partial", "degraded"}
    assert "done" != out.get("status") or out.get("degraded") is True


def test_degraded_plan_surfaces_in_final_result(monkeypatch):
    from figureitout.planner import Plan, Task

    degraded = Plan(
        tasks=[
            Task(
                name="research_context",
                description="Research requirements",
                success_criteria="Findings include concrete insight",
                task_type="research",
            ),
            Task(
                name="verify_output",
                description="Verify deliverable against done criteria",
                success_criteria="Concrete verification evidence present",
                depends_on=["research_context"],
                task_type="analyse",
            ),
        ],
        rationale="Degraded fallback plan",
        degraded=True,
        done_criteria="Objective met with evidence",
    )
    monkeypatch.setattr("figureitout.runner.plan_objective", lambda _o: degraded)
    def _fake_exec(task, *_a, **_k):
        ttype = getattr(task, "task_type", None)
        if ttype is None and isinstance(task, dict):
            ttype = task.get("task_type")
        if ttype == "research":
            return "NO LIVE SEARCH — used shell/read_file. Found README.md evidence.\n"
        return "Verified artifacts: README.md mentioned; tests referenced."

    monkeypatch.setattr("figureitout.runner.execute_task", _fake_exec)
    # Force judge/bar to pass so synthesiser is reached with degraded flag.
    from figureitout.judge import JudgeResult
    from figureitout.bar_raiser import BarRaiserResult

    monkeypatch.setattr(
        "figureitout.runner.judge_task",
        lambda *_a, **_k: JudgeResult(score=90, passed=True, failure_reason=""),
    )
    monkeypatch.setattr(
        "figureitout.runner.bar_raise",
        lambda *_a, **_k: BarRaiserResult(
            accuracy=18,
            calibration=17,
            robustness=17,
            fairness=18,
            efficiency=18,
            total=88,
            passed=True,
            weakest_dimension="calibration",
        ),
    )
    result = run_objective("complex objective needing real work")
    assert result.get("degraded") is True
    # Fail-closed: degraded runs never report done.
    assert result.get("status") in {"partial", "blocked", "degraded"}
    assert result.get("status") != "done"


def test_synthesiser_blocks_worker_fallback_false_success():
    state = {
        "objective": "research bag deals and produce a report",
        "status": "done",
        "bar_raiser_score": 88.0,
        "judge_score": 90.0,
        "retries": 0,
        "task_outputs": {
            "research": (
                "Worker fallback for document task. "
                "Error code: 500 — Max retries exceeded with url."
            )
        },
        "final_output": (
            "Worker fallback for document task. "
            "Error code: 500 — Max retries exceeded with url."
        ),
        "degraded": False,
        "done_criteria": "Concrete research findings with sources",
    }
    out = synthesiser_node(state)
    assert out["status"] == "blocked"
    assert out["status"] != "done"
    assert out.get("degraded") is True


def test_synthesiser_partial_when_degraded_even_if_bar_high():
    state = {
        "objective": "build production app with auth and tests",
        "status": "done",
        "bar_raiser_score": 90.0,
        "judge_score": 90.0,
        "retries": 0,
        "task_outputs": {
            "implement": (
                "Wrote app/main.py and tests/test_app.py. "
                "pytest passed. Verified auth flow and artifact evidence."
            )
        },
        "final_output": (
            "Wrote app/main.py and tests/test_app.py. "
            "pytest passed. Verified auth flow and artifact evidence."
        ),
        "degraded": True,
        "done_criteria": "Working app with tests and auth",
    }
    out = synthesiser_node(state)
    assert out["status"] in {"partial", "blocked"}
    assert out["status"] != "done"
