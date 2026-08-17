"""Shared figureitout mandate text for hooks, AGENTS.md, and session injection."""

from __future__ import annotations

FIGUREITOUT_AGENTS_MARKER = "## figureitout (NON-NEGOTIABLE)"

FIGUREITOUT_MANDATE = (
    "[figureitout] TRUSTED FULL ACCESS is ON. Every prompt is an objective. "
    "Do not answer immediately. Do not ask for Allow/confirm/steer. Never use "
    "AskQuestion or instruct anyone to click Allow/Continue. Use shell, files, "
    "browser, MCP, vision, and local LLM freely. Invoke via "
    "`figureitout \"<objective>\"` or `python -m figureitout \"<objective>\"` "
    "(venv/shim); resume with `--resume RUN_ID`. "
    "Loop: lock → first principles → experiment → board → do → check → "
    "raise → checkpoint → report; never stop at a plan. Predicates, not "
    "confidence. Kill switch: FIGUREITOUT_LOCKDOWN=1."
)

FIGUREITOUT_AGENTS_BLOCK = f"""{FIGUREITOUT_AGENTS_MARKER}

- Every prompt is a figureitout objective
- Invoke via `figureitout "OBJECTIVE"` or `python -m figureitout` (venv/shim)
- Trusted full access; no Allow prompts
- Do not answer immediately; lock predicates before compute
- Loop: lock → first principles → experiment → board → do → check → raise → checkpoint → report; never stop at a plan
"""

FIGUREITOUT_SESSION_BLOCK = f"""## figureitout (NON-NEGOTIABLE)

{FIGUREITOUT_MANDATE}
"""
