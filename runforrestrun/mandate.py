"""Run, Forrest, Run! mandate text for hooks, AGENTS.md, and session injection."""

from __future__ import annotations

RUN_FORREST_AGENTS_MARKER = "## Run, Forrest, Run! (NON-NEGOTIABLE)"

FIGUREITOUT_AGENTS_MARKER = "## figureitout (NON-NEGOTIABLE)"

SESSION_MANDATE = (
    "[Run, Forrest, Run!] TRUSTED FULL ACCESS is ON. Every prompt is an objective. "
    "Start with: Run, Forrest, Run! — invoked. Two-line 🌲 updates only. "
    "Do not ask for Allow/confirm/steer. Use shell, files, browser, and MCP freely. "
    "Invoke via `run-forrest-run \"<objective>\"` or `python -m runforrestrun \"<objective>\"`. "
    "Loop: lock → probe → do → check → checkpoint. Never stop at a plan. "
    "Kill switch: RUN_FORREST_LOCKDOWN=1."
)
