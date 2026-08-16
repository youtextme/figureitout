"""Layer 6 — LLM-as-judge (openai/evals pattern) with instructor."""

from __future__ import annotations

import os
import re
from typing import Any

from pydantic import BaseModel, Field

from figureitout.config import (
    anthropic_model,
    llm_provider,
    local_base_url,
    local_model,
    openai_model,
    use_mock,
)
from figureitout.fail_closed import is_error_fallback_output
from figureitout.planner import Task


class JudgeResult(BaseModel):
    score: int = Field(ge=0, le=100)
    passed: bool
    failure_reason: str = ""


def _traceable(fn):
    try:
        from langsmith import traceable

        return traceable(name=fn.__name__)(fn)
    except Exception:
        return fn


def _has_code_evidence(output: str) -> bool:
    text = output or ""
    lower = text.lower()
    path_hit = bool(re.search(r"[\w./\\-]+\.(py|ts|tsx|js|md|json|yml|yaml|toml)\b", text))
    test_hit = any(tok in lower for tok in ("pytest", "unittest", "test_", "tests/", "assert"))
    artifact_hit = any(
        tok in lower
        for tok in ("wrote ", "created ", "updated ", "file exists", "artifact", "implemented")
    )
    code_fence = "```" in text
    return path_hit or (test_hit and artifact_hit) or (code_fence and path_hit) or (path_hit and artifact_hit)


def _is_localish() -> bool:
    return llm_provider() in {"local", "tireless", "ollama"} and not use_mock()


def _mock_judge(task: Task, output: str) -> JudgeResult:
    text = (output or "").strip().lower()
    criteria = (task.success_criteria or "").lower()
    bad_markers = (
        "bad fail",
        "not implemented",
        "lorem ipsum",
        "clearly wrong",
        "this is bad",
        "failed/degraded",
        "do not treat as completed",
        "worker fallback",
        "error code: 500",
        "max retries exceeded",
    )
    if not text:
        return JudgeResult(score=20, passed=False, failure_reason="Empty output")
    if is_error_fallback_output(output):
        return JudgeResult(
            score=10,
            passed=False,
            failure_reason="Error fallback / API failure output rejected (fail-closed)",
        )
    if any(m in text for m in bad_markers):
        return JudgeResult(score=20, passed=False, failure_reason="Output clearly fails success criteria")

    # Local / real provider: code tasks require concrete evidence — no lenient hello/len pass.
    if _is_localish() and task.task_type == "code":
        if not _has_code_evidence(output):
            return JudgeResult(
                score=40,
                passed=False,
                failure_reason="Code task lacks file/test/artifact evidence",
            )
        return JudgeResult(score=90, passed=True, failure_reason="")

    if _is_localish():
        # Still reject canned shallow stubs under local.
        if "completed task" in text and not _has_code_evidence(output) and "http" not in text:
            if len(text) < 200 or "hello" in text:
                return JudgeResult(
                    score=45,
                    passed=False,
                    failure_reason="Shallow stub output rejected under local provider",
                )

    # Hello-world / substantive outputs pass the bar for offline mock verification.
    if not _is_localish():
        if "hello" in text or len(text) > 40 or "http" in text or '"tasks"' in text:
            return JudgeResult(score=90, passed=True, failure_reason="")
    else:
        if "hello" in text and task.task_type == "write":
            return JudgeResult(score=90, passed=True, failure_reason="")
        if _has_code_evidence(output) or ("http" in text and "example.com" not in text):
            return JudgeResult(score=90, passed=True, failure_reason="")
        if '"tasks"' in text and "success_criteria" in text:
            return JudgeResult(score=90, passed=True, failure_reason="")

    if criteria and any(tok in text for tok in criteria.split() if len(tok) > 4):
        return JudgeResult(score=85, passed=True, failure_reason="")
    return JudgeResult(score=55, passed=False, failure_reason="Output does not meet success criteria")


def _instructor_client():
    import instructor

    provider = llm_provider()
    if provider == "anthropic":
        import anthropic

        return instructor.from_anthropic(anthropic.Anthropic()), anthropic_model(), "anthropic"
    from openai import OpenAI

    if provider in {"local", "tireless", "ollama"}:
        client = OpenAI(base_url=local_base_url(), api_key=os.environ.get("OPENAI_API_KEY", "local-no-key"))
        return instructor.from_openai(client), local_model(), "openai"
    return instructor.from_openai(OpenAI()), openai_model(), "openai"


@_traceable
def judge_task(task: Task, output: str) -> JudgeResult:
    """Score worker output 0–100 against task.success_criteria."""
    # Fail-closed before any lenient path — API/worker fallbacks never pass.
    if is_error_fallback_output(output):
        return JudgeResult(
            score=10,
            passed=False,
            failure_reason="Error fallback / API failure output rejected (fail-closed)",
        )

    if use_mock() or llm_provider() == "mock":
        return _mock_judge(task, output)

    # Local provider: evidence-gated heuristic judge (no lenient hello/len pass).
    if _is_localish():
        return _mock_judge(task, output)

    prompt = (
        "Score this output 0-100 against the success criteria. "
        "Reject shallow stubs, canned 'Completed task…' text, and invented URLs. "
        "For code/implement tasks require file paths, tests, or concrete artifacts. "
        f"Criteria: {task.success_criteria}. Output: {output}. "
        "Return score, passed (True if score >= 80), and failure_reason."
    )
    try:
        client, model, style = _instructor_client()
        if style == "anthropic":
            return client.messages.create(
                model=model,
                max_tokens=512,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                response_model=JudgeResult,
            )
        return client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            response_model=JudgeResult,
        )
    except Exception as exc:
        result = _mock_judge(task, output)
        if not result.failure_reason:
            result.failure_reason = f"judge_fallback:{exc}"
        return result
