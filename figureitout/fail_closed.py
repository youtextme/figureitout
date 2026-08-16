"""Fail-closed detectors — LLM/API error outputs must never look like success."""

from __future__ import annotations

import re

from figureitout.config import use_mock

# Always reject these — silent/API fallbacks that previously scored as "done".
ALWAYS_FAIL_MARKERS = (
    "worker fallback",
    "error code: 500",
    "max retries exceeded",
    "failed/degraded",
    "do not treat as completed",
    "llm or tool loop error",
)

# Stub / fabricated evidence — reject unless FIGUREITOUT_MOCK=1.
NON_MOCK_FAIL_MARKERS = (
    "http://example.com",
    "https://example.com",
)


def is_error_fallback_output(text: str | None) -> bool:
    """True when output is an LLM/API/worker failure that must not pass as done."""
    lower = (text or "").strip().lower()
    if not lower:
        return False
    if any(m in lower for m in ALWAYS_FAIL_MARKERS):
        return True
    # HTTP 500 variants from OpenAI/httpx style errors
    if re.search(r"\b(error|status|http)\s*code[:\s]*500\b", lower):
        return True
    if re.search(r"\bhttp\s*500\b", lower):
        return True
    if not use_mock():
        if any(m in lower for m in NON_MOCK_FAIL_MARKERS):
            return True
        # Research stub that only points at example.com without honest NO LIVE SEARCH.
        if "example.com" in lower and "no live search" not in lower:
            return True
    return False


def any_output_is_error_fallback(outputs: dict | None, *extra: str | None) -> bool:
    """Scan task outputs / final text for fail-closed markers."""
    for value in (outputs or {}).values():
        if is_error_fallback_output(str(value)):
            return True
    for item in extra:
        if is_error_fallback_output(item):
            return True
    return False
