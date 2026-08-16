"""Layer 7 — HELM-inspired bar raiser for final output quality."""

from __future__ import annotations

import os
import re

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


class BarRaiserResult(BaseModel):
    accuracy: int = Field(ge=0, le=20)
    calibration: int = Field(ge=0, le=20)
    robustness: int = Field(ge=0, le=20)
    fairness: int = Field(ge=0, le=20)
    efficiency: int = Field(ge=0, le=20)
    total: int = Field(ge=0, le=100)
    passed: bool
    weakest_dimension: str


def _traceable(fn):
    try:
        from langsmith import traceable

        return traceable(name=fn.__name__)(fn)
    except Exception:
        return fn


def _finalize(scores: dict[str, int]) -> BarRaiserResult:
    total = sum(scores.values())
    weakest = min(scores, key=scores.get)
    return BarRaiserResult(
        accuracy=scores["accuracy"],
        calibration=scores["calibration"],
        robustness=scores["robustness"],
        fairness=scores["fairness"],
        efficiency=scores["efficiency"],
        total=total,
        passed=total >= 85,
        weakest_dimension=weakest,
    )


def _is_localish() -> bool:
    return llm_provider() in {"local", "tireless", "ollama"} and not use_mock()


def _is_shallow_stub(final_output: str) -> bool:
    text = (final_output or "").strip()
    lower = text.lower()
    if is_error_fallback_output(final_output):
        return True
    if "completed task" in lower and len(text) < 280:
        return True
    if "hello" in lower and "print(" not in lower and "```" not in text:
        # padded hello stubs without real deliverable
        if "stub" in lower or "completed task" in lower:
            return True
    # Reject fabricated example.com evidence URLs, not prose that forbids them.
    if re.search(r"https?://example\.com", lower) and "no live search" not in lower:
        return True
    if "lorem ipsum" in lower:
        return True
    # Long but contentless padding
    words = lower.split()
    unique = set(words)
    if len(words) > 20 and len(unique) <= 8:
        return True
    return False


def _has_substance(final_output: str) -> bool:
    if is_error_fallback_output(final_output):
        return False
    text = final_output or ""
    lower = text.lower()
    path_hit = bool(re.search(r"[\w./\\-]+\.(py|ts|tsx|js|md|json)\b", text))
    markers = (
        "implemented",
        "verified",
        "pytest",
        "foundation",
        "research",
        "multi-turn",
        "evidence",
        "```",
    )
    return path_hit or sum(1 for m in markers if m in lower) >= 3 or len(text) > 180


def _fail_closed_bar() -> BarRaiserResult:
    return _finalize(
        {
            "accuracy": 2,
            "calibration": 4,
            "robustness": 2,
            "fairness": 8,
            "efficiency": 4,
        }
    )


def _mock_bar_raise(objective: str, final_output: str) -> BarRaiserResult:
    text = (final_output or "").strip()
    words = text.split()
    if is_error_fallback_output(final_output):
        return _fail_closed_bar()
    # One-word / trivial outputs fail the bar for complex objectives.
    if len(words) <= 1 and len((objective or "").split()) >= 3:
        return _finalize(
            {
                "accuracy": 4,
                "calibration": 6,
                "robustness": 3,
                "fairness": 10,
                "efficiency": 8,
            }
        )

    if _is_localish() and _is_shallow_stub(text):
        return _finalize(
            {
                "accuracy": 5,
                "calibration": 8,
                "robustness": 5,
                "fairness": 12,
                "efficiency": 10,
            }
        )

    if _is_localish():
        if _has_substance(text):
            return _finalize(
                {
                    "accuracy": 18,
                    "calibration": 17,
                    "robustness": 17,
                    "fairness": 18,
                    "efficiency": 17,
                }
            )
        return _finalize(
            {
                "accuracy": 8,
                "calibration": 10,
                "robustness": 8,
                "fairness": 12,
                "efficiency": 10,
            }
        )

    if "hello" in text.lower() or len(text) > 60:
        return _finalize(
            {
                "accuracy": 18,
                "calibration": 17,
                "robustness": 17,
                "fairness": 18,
                "efficiency": 18,
            }
        )
    if len(text) < 20:
        return _finalize(
            {
                "accuracy": 8,
                "calibration": 8,
                "robustness": 7,
                "fairness": 12,
                "efficiency": 10,
            }
        )
    return _finalize(
        {
            "accuracy": 16,
            "calibration": 15,
            "robustness": 15,
            "fairness": 16,
            "efficiency": 15,
        }
    )


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
def bar_raise(objective: str, final_output: str) -> BarRaiserResult:
    """Score final output across five HELM dimensions (0–20 each)."""
    # Fail-closed before any lenient / LLM path.
    if is_error_fallback_output(final_output):
        return _fail_closed_bar()

    if use_mock() or llm_provider() == "mock":
        return _mock_bar_raise(objective, final_output)

    # Local provider: enforce shallow-stub rejection and substance heuristics
    # before any LLM call (fail closed; do not treat length/hello as success).
    if _is_localish():
        return _mock_bar_raise(objective, final_output)

    prompt = (
        "Score this output across five dimensions, 0-20 each. "
        "Fail shallow stubs, canned Completed-task prose, and invented evidence. "
        "Accuracy: does it correctly achieve the objective. "
        "Calibration: are confidence levels appropriate. "
        "Robustness: would it hold under edge cases. "
        "Fairness: is it unbiased. "
        "Efficiency: is it concise without loss. "
        f"Objective: {objective}. Output: {final_output}."
    )
    try:
        client, model, style = _instructor_client()

        class _Scores(BaseModel):
            accuracy: int
            calibration: int
            robustness: int
            fairness: int
            efficiency: int

        if style == "anthropic":
            raw = client.messages.create(
                model=model,
                max_tokens=512,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                response_model=_Scores,
            )
        else:
            raw = client.chat.completions.create(
                model=model,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                response_model=_Scores,
            )
        return _finalize(
            {
                "accuracy": max(0, min(20, raw.accuracy)),
                "calibration": max(0, min(20, raw.calibration)),
                "robustness": max(0, min(20, raw.robustness)),
                "fairness": max(0, min(20, raw.fairness)),
                "efficiency": max(0, min(20, raw.efficiency)),
            }
        )
    except Exception:
        return _mock_bar_raise(objective, final_output)
