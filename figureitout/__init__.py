"""figureitout — autonomous objective runner for every IDE and CLI.

Every prompt is an objective. The runner plans, works, judges, raises the bar,
learns, and synthesises without waiting for a human to steer.

Trusted full-access is ON by default (FIGUREITOUT_TRUSTED=1).
Kill switch: FIGUREITOUT_LOCKDOWN=1 or FIGUREITOUT_TRUSTED=0.

Importing this package does NOT load LangGraph/runner; use lazy access or
`python -m figureitout` so `--status` / `--install` work without heavy deps.
"""

from __future__ import annotations

from typing import Any

__version__ = "0.3.0"

__all__ = ["run_objective", "__version__"]


def __getattr__(name: str) -> Any:
    if name == "run_objective":
        from figureitout.runner import run_objective

        return run_objective
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals()) + ["run_objective"])
