"""Layer 3 — structured planning with instructor + pydantic."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

from figureitout.config import (
    anthropic_model,
    llm_provider,
    local_base_url,
    local_model,
    openai_model,
    use_mock,
)


PLAN_SYSTEM_PROMPT = """You are a foundation-up objective planner.

Rules:
1. Extract explicit done criteria for the whole objective.
2. Order tasks foundation-up: research → analyse/design → implement/code → verify → document.
3. Research-first: the first actionable task MUST gather real context (codebase, files, or live sources).
4. Anti-mock / anti-stub: never invent fake URLs, placeholder code, or "Completed task…" prose as success.
5. Each task needs concrete, falsifiable success_criteria and meaningful depends_on edges.
6. Prefer 3–5 tasks. Include a verify task that checks artifacts/tests against done criteria.
7. Do not treat shallow length heuristics as quality.
"""


class Task(BaseModel):
    name: str
    description: str
    success_criteria: str
    depends_on: list[str] = Field(default_factory=list)
    task_type: Literal["research", "code", "write", "analyse"] = "write"


class Plan(BaseModel):
    tasks: list[Task]
    rationale: str
    degraded: bool = False
    done_criteria: str = ""


def _mock_plan(objective: str, *, degraded: bool = False) -> Plan:
    obj = objective.strip() or "objective"
    lower = obj.lower()
    done = f"Objective fully met with concrete evidence: {obj}"
    if "hello world" in lower:
        return Plan(
            tasks=[
                Task(
                    name="write_hello_world",
                    description=f"Produce a hello world deliverable for: {obj}",
                    success_criteria="Output contains a clear hello world program or message",
                    depends_on=[],
                    task_type="write",
                )
            ],
            rationale="Single write task sufficient for hello world.",
            degraded=degraded,
            done_criteria=done,
        )
    tasks = [
        Task(
            name="research_context",
            description=(
                f"Research requirements and existing codebase context for: {obj}. "
                "Use shell/read_file/browse when live search is unavailable."
            ),
            success_criteria="Findings include at least one concrete source-backed or file-backed insight",
            depends_on=[],
            task_type="research",
        ),
        Task(
            name="design_approach",
            description=f"Analyse and design a foundation-up approach for: {obj}",
            success_criteria="Approach lists ordered steps, dependencies, and risks",
            depends_on=["research_context"],
            task_type="analyse",
        ),
        Task(
            name="implement",
            description=f"Implement the solution for: {obj}",
            success_criteria="Working artifact (files/tests) that meets the objective",
            depends_on=["design_approach"],
            task_type="code",
        ),
        Task(
            name="verify_output",
            description=(
                f"Verify the deliverable against done criteria for: {obj}. "
                "Confirm files exist, tests mention coverage, or other concrete evidence."
            ),
            success_criteria="Concrete verification evidence present (paths, tests, or command output)",
            depends_on=["implement"],
            task_type="analyse",
        ),
        Task(
            name="document",
            description=f"Write a short summary of the deliverable for: {obj}",
            success_criteria="Summary explains what was built and how to use it",
            depends_on=["verify_output"],
            task_type="write",
        ),
    ]
    if degraded:
        # Keep plan compact but force research + verify.
        tasks = [tasks[0], tasks[2], tasks[3]]
        tasks[1].depends_on = ["research_context"]
        tasks[2].depends_on = ["implement"]
        rationale = (
            "DEGRADED plan after planner LLM failure — forced research + implement + verify. "
            "Not full planning success."
        )
    else:
        rationale = "Default foundation-up decomposition covering research through documentation."
    return Plan(tasks=tasks, rationale=rationale, degraded=degraded, done_criteria=done)


def _instructor_client():
    import instructor

    provider = llm_provider()
    if provider == "anthropic":
        import anthropic

        return instructor.from_anthropic(anthropic.Anthropic()), anthropic_model(), "anthropic"
    # openai-compatible (openai + local)
    from openai import OpenAI

    if provider in {"local", "tireless", "ollama"}:
        client = OpenAI(base_url=local_base_url(), api_key=os.environ.get("OPENAI_API_KEY", "local-no-key"))
        return instructor.from_openai(client), local_model(), "openai"
    client = OpenAI()
    return instructor.from_openai(client), openai_model(), "openai"


def _call_planner_llm(objective: str) -> Plan:
    client, model, style = _instructor_client()
    prompt = (
        f"{PLAN_SYSTEM_PROMPT}\n\n"
        f"Objective: {objective}\n\n"
        "Return a Plan with 3-5 tasks, done_criteria, meaningful depends_on, "
        "and degraded=false."
    )
    if style == "anthropic":
        return client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
            response_model=Plan,
        )
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_model=Plan,
    )


def _is_empty_or_useless(plan: Plan) -> bool:
    if not plan.tasks:
        return True
    if all(not (t.success_criteria or "").strip() for t in plan.tasks):
        return True
    return False


def plan_objective(objective: str) -> Plan:
    """Break an objective into a typed, validated Plan (3–5 tasks)."""
    if use_mock() or llm_provider() == "mock":
        return _mock_plan(objective, degraded=False)

    last_exc: Exception | None = None
    for attempt in range(2):  # initial + one retry
        try:
            plan = _call_planner_llm(objective)
            if _is_empty_or_useless(plan):
                raise RuntimeError("empty or useless plan from LLM")
            plan.degraded = False
            if not (plan.done_criteria or "").strip():
                plan.done_criteria = f"Objective fully met with concrete evidence: {objective}"
            return plan
        except Exception as exc:  # noqa: BLE001 — retry then degrade
            last_exc = exc
            continue

    # Local/real provider: do NOT silently succeed with a mock plan.
    # Mark degraded and force research + verify tasks so the runner cannot claim full success.
    plan = _mock_plan(objective, degraded=True)
    plan.rationale = (
        f"{plan.rationale} Last error: {last_exc!r}" if last_exc else plan.rationale
    )
    return plan
