"""Layer 11 — observability (langsmith traceable wrappers)."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

from figureitout.bar_raiser import bar_raise
from figureitout.judge import judge_task
from figureitout.planner import Task


def test_judge_and_bar_raiser_are_callable_trace_targets():
    task = Task(
        name="t",
        description="write hello world",
        success_criteria="hello world present",
        task_type="write",
    )
    j = judge_task(task, "hello world program")
    b = bar_raise("write hello world", "hello world program complete with example")
    assert j.score >= 0
    assert b.total >= 0


def test_langsmith_env_documented():
    # Layer 11 is env-driven; ensure the runner does not crash without keys.
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
    assert judge_task is not None
