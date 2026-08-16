"""Layer 6 — task judge."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

from figureitout.judge import JudgeResult, judge_task
from figureitout.planner import Task


def _task() -> Task:
    return Task(
        name="hello",
        description="write hello world",
        success_criteria="Output contains a clear hello world program or message",
        task_type="write",
    )


def test_judge_rejects_bad_output():
    result = judge_task(_task(), "bad fail error not implemented")
    assert isinstance(result, JudgeResult)
    assert result.passed is False
    assert result.score < 80


def test_judge_accepts_good_output():
    result = judge_task(_task(), "print('Hello, World!') — hello world program complete")
    assert result.passed is True
    assert result.score > 80


def test_judge_typed_bounds():
    result = judge_task(_task(), "hello world")
    assert 0 <= result.score <= 100


def test_local_code_task_requires_evidence(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    task = Task(
        name="implement",
        description="Implement feature X",
        success_criteria="Working artifact that meets the objective",
        task_type="code",
    )
    # Lenient mock markers alone must not pass under local provider.
    shallow = "Completed task implement. Hello there, this is longer than forty characters."
    result = judge_task(task, shallow)
    assert result.passed is False
    assert result.score < 80


def test_local_code_task_passes_with_artifact_evidence(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    task = Task(
        name="implement",
        description="Implement feature X",
        success_criteria="Working artifact that meets the objective",
        task_type="code",
    )
    evidence = (
        "Wrote figureitout/runner.py and added tests/test_figureitout_layer1_runner.py. "
        "pytest passed for the new module."
    )
    result = judge_task(task, evidence)
    assert result.passed is True


def test_judge_rejects_worker_fallback_and_http_500():
    task = _task()
    bad = (
        "Worker fallback for document task after Error code: 500. "
        "Max retries exceeded with url: http://localhost:11435/v1/chat/completions"
    )
    result = judge_task(task, bad)
    assert result.passed is False
    assert result.score < 80


def test_judge_rejects_example_com_stub_when_not_mock(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    task = Task(
        name="research",
        description="Find pricing data",
        success_criteria="Live sources with concrete prices",
        task_type="research",
    )
    stub = "Found deals at https://example.com/bag-deal — research complete."
    result = judge_task(task, stub)
    assert result.passed is False
    assert result.score < 80
