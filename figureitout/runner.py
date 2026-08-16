"""Layer 1 — LangGraph core loop for the figureitout objective runner."""

from __future__ import annotations

import re
import uuid
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from figureitout.bar_raiser import bar_raise
from figureitout.dora import DoraTracker
from figureitout.fail_closed import any_output_is_error_fallback, is_error_fallback_output
from figureitout.judge import judge_task
from figureitout.memory import save_task_result
from figureitout.planner import Plan, Task, plan_objective
from figureitout.worker import execute_task


class RunState(TypedDict, total=False):
    objective: str
    plan: list
    current_task: dict
    task_outputs: dict
    retries: int
    judge_score: float
    bar_raiser_score: float
    status: str
    replan: bool
    final_output: str
    failure_reason: str
    task_index: int
    more_tasks: bool
    dora: dict
    run_id: str
    degraded: bool
    done_criteria: str


_TRACKER: DoraTracker | None = None


def _tracker() -> DoraTracker:
    global _TRACKER
    if _TRACKER is None:
        _TRACKER = DoraTracker()
    return _TRACKER


def _as_task(raw: dict | Task) -> Task:
    return raw if isinstance(raw, Task) else Task.model_validate(raw)


def order_tasks_by_depends(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Topologically order tasks by depends_on; break cycles by original order."""
    by_name = {t.get("name", f"t{i}"): t for i, t in enumerate(tasks)}
    remaining = set(by_name)
    ordered: list[dict[str, Any]] = []
    # Preserve stable original index for ties
    original_index = {t.get("name", f"t{i}"): i for i, t in enumerate(tasks)}

    while remaining:
        ready = []
        for name in remaining:
            deps = list(by_name[name].get("depends_on") or [])
            if all(d not in remaining for d in deps):
                ready.append(name)
        if not ready:
            # Cycle — emit remaining in original order
            leftover = sorted(remaining, key=lambda n: original_index.get(n, 0))
            ordered.extend(by_name[n] for n in leftover)
            break
        ready.sort(key=lambda n: original_index.get(n, 0))
        for name in ready:
            ordered.append(by_name[name])
            remaining.remove(name)
    return ordered


def _objective_done_criteria_met(objective: str, done_criteria: str, final_output: str) -> bool:
    text = (final_output or "").strip()
    lower = text.lower()
    if not text:
        return False
    if is_error_fallback_output(final_output):
        return False
    if "failed/degraded" in lower and "do not treat as completed" in lower:
        return False
    if "completed task" in lower and len(text) < 200 and "```" not in text:
        # Shallow canned success
        complex_obj = len((objective or "").split()) >= 5
        if complex_obj:
            return False

    criteria = (done_criteria or objective or "").lower()
    tokens = [tok for tok in re.split(r"\W+", criteria) if len(tok) > 4][:8]
    token_hits = sum(1 for tok in tokens if tok in lower) if tokens else 0
    evidence = any(
        m in lower
        for m in (
            "pytest",
            "verified",
            "implemented",
            "artifact",
            "test_",
            ".py",
            "readme",
            "```",
            "file",
        )
    )
    if "hello world" in (objective or "").lower() and "hello" in lower:
        return True
    if evidence and (token_hits >= max(1, len(tokens) // 3) or len(text) > 160):
        return True
    if token_hits >= max(2, len(tokens) // 2):
        return True
    return False


def planner_node(state: RunState) -> dict[str, Any]:
    objective = state.get("objective", "")
    if state.get("replan") and state.get("failure_reason"):
        objective = f"{objective} [constraint: improve {state['failure_reason']}]"
    plan: Plan = plan_objective(objective)
    tasks = order_tasks_by_depends([t.model_dump() for t in plan.tasks])
    _tracker().total_tasks = max(_tracker().total_tasks, len(tasks))
    current = tasks[0] if tasks else Task(
        name="noop",
        description=objective,
        success_criteria="Produce a useful response",
        task_type="write",
    ).model_dump()
    degraded = bool(plan.degraded or state.get("degraded"))
    return {
        "plan": tasks,
        "current_task": current,
        "task_index": 0,
        "task_outputs": state.get("task_outputs") or {},
        "retries": state.get("retries", 0) if not state.get("replan") else 0,
        "replan": False,
        "status": "planned_degraded" if degraded else "planned",
        "objective": state.get("objective", objective),
        "degraded": degraded,
        "done_criteria": plan.done_criteria
        or state.get("done_criteria")
        or f"Objective fully met with concrete evidence: {state.get('objective', objective)}",
    }


def worker_node(state: RunState) -> dict[str, Any]:
    task = _as_task(state.get("current_task") or {})
    outputs = dict(state.get("task_outputs") or {})
    result = execute_task(task, outputs, run_id=state.get("run_id"))
    outputs[task.name] = result
    degraded = bool(state.get("degraded"))
    lower = str(result).lower()
    if (
        "failed/degraded" in lower
        or "degraded:" in lower
        or is_error_fallback_output(result)
    ):
        degraded = True
    return {
        "task_outputs": outputs,
        "final_output": result,
        "status": "worked",
        "degraded": degraded,
    }


def evaluator_node(state: RunState) -> dict[str, Any]:
    task = _as_task(state.get("current_task") or {})
    output = (state.get("task_outputs") or {}).get(task.name) or state.get("final_output") or ""
    result = judge_task(task, str(output))
    _tracker().mark_judge(result.passed)
    save_task_result(task, str(output), float(result.score), result.failure_reason)
    updates: dict[str, Any] = {
        "judge_score": float(result.score),
        "failure_reason": result.failure_reason,
        "degraded": bool(state.get("degraded")),
    }
    if not result.passed:
        updated = task.model_dump()
        updated["description"] = (
            f"{task.description}\nPrevious attempt failed: {result.failure_reason}"
        )
        updates["current_task"] = updated
        updates["retries"] = int(state.get("retries", 0)) + 1
        updates["more_tasks"] = False
        updates["status"] = "retry"
        _tracker().total_retries += 1
    else:
        plan = list(state.get("plan") or [])
        # Plan is already topologically ordered by depends_on in planner_node.
        idx = int(state.get("task_index", 0)) + 1
        if idx < len(plan):
            updates["task_index"] = idx
            updates["current_task"] = plan[idx]
            updates["retries"] = 0
            updates["more_tasks"] = True
            updates["status"] = "next_task"
        else:
            updates["more_tasks"] = False
            updates["status"] = "judged"
    return updates


def _after_evaluator(state: RunState) -> Literal["worker", "bar_raiser", "synthesiser"]:
    score = float(state.get("judge_score", 0))
    retries = int(state.get("retries", 0))
    # Above/at 80: continue remaining plan tasks, else raise the bar.
    if score >= 80:
        if state.get("more_tasks"):
            return "worker"
        return "bar_raiser"
    if retries < 3:
        return "worker"
    return "synthesiser"


def bar_raiser_node(state: RunState) -> dict[str, Any]:
    objective = state.get("objective", "")
    outputs = state.get("task_outputs") or {}
    final_output = state.get("final_output") or "\n\n".join(str(v) for v in outputs.values())
    result = bar_raise(objective, str(final_output))
    updates: dict[str, Any] = {
        "bar_raiser_score": float(result.total),
        "final_output": final_output,
        "failure_reason": result.weakest_dimension,
        "degraded": bool(state.get("degraded")),
    }
    if result.passed:
        updates["status"] = "done"
    else:
        updates["status"] = "replan"
        updates["replan"] = True
        updates["objective"] = (
            f"{objective} [improve weakest dimension: {result.weakest_dimension}]"
        )
    return updates


def _after_bar_raiser(state: RunState) -> Literal["synthesiser", "planner"]:
    score = float(state.get("bar_raiser_score", 0))
    if score >= 85:
        return "synthesiser"
    # Avoid infinite replan loops when planner already degraded or bar keeps failing.
    if state.get("degraded"):
        return "synthesiser"
    return "planner"


def synthesiser_node(state: RunState) -> dict[str, Any]:
    status = state.get("status") or "partial"
    degraded = bool(state.get("degraded"))
    outputs = state.get("task_outputs") or {}
    final_output = state.get("final_output") or "\n\n".join(str(v) for v in outputs.values())
    objective = state.get("objective", "")
    done_criteria = state.get("done_criteria") or ""

    bar_ok = float(state.get("bar_raiser_score", 0)) >= 85
    judge_exhausted = float(state.get("judge_score", 0)) < 80 and int(state.get("retries", 0)) >= 3
    criteria_ok = _objective_done_criteria_met(objective, done_criteria, str(final_output))
    error_fallback = any_output_is_error_fallback(outputs, str(final_output))

    # Fail-closed: error fallbacks / degraded runs never report done with a high score.
    if error_fallback:
        status = "blocked"
        degraded = True
        final_output = (
            f"{final_output}\n\n[synthesiser] Fail-closed: worker/API error fallback detected; "
            "status=blocked (not done)."
        )
    elif degraded:
        status = "partial"
    elif judge_exhausted:
        status = "partial"
    elif bar_ok and criteria_ok:
        status = "done"
    elif bar_ok and not criteria_ok:
        status = "partial"
        degraded = True
        final_output = (
            f"{final_output}\n\n[synthesiser] Objective-level done criteria not validated. "
            f"Criteria: {done_criteria or objective}"
        )
    elif status == "done" and not criteria_ok:
        status = "partial"
        degraded = True

    # Hard guard — never emit done when degraded or error fallback.
    if status == "done" and (degraded or error_fallback):
        status = "blocked" if error_fallback else "partial"

    metrics = _tracker().emit(
        "partial" if status in {"degraded", "blocked"} else status
    )
    return {
        "status": status,
        "final_output": final_output,
        "dora": metrics,
        "degraded": degraded,
        "done_criteria": done_criteria,
    }


def build_graph():
    builder = StateGraph(RunState)
    builder.add_node("planner", planner_node)
    builder.add_node("worker", worker_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("bar_raiser", bar_raiser_node)
    builder.add_node("synthesiser", synthesiser_node)

    builder.set_entry_point("planner")
    builder.add_edge("planner", "worker")
    builder.add_edge("worker", "evaluator")
    builder.add_conditional_edges(
        "evaluator",
        _after_evaluator,
        {
            "worker": "worker",
            "bar_raiser": "bar_raiser",
            "synthesiser": "synthesiser",
        },
    )
    builder.add_conditional_edges(
        "bar_raiser",
        _after_bar_raiser,
        {
            "synthesiser": "synthesiser",
            "planner": "planner",
        },
    )
    builder.add_edge("synthesiser", END)
    return builder.compile()


# Module-level compiled graph for Layer 1 verification.
graph = build_graph()


def run_objective(objective: str, retries: int = 0) -> dict[str, Any]:
    """Public entry: run an objective through the figureitout graph."""
    global _TRACKER
    _TRACKER = DoraTracker()
    result = graph.invoke(
        {
            "objective": objective,
            "retries": retries,
            "task_outputs": {},
            "plan": [],
            "status": "started",
            "replan": False,
            "run_id": str(uuid.uuid4()),
            "degraded": False,
            "done_criteria": "",
        }
    )
    return dict(result)
