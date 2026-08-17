"""Can we run without a human at the desk?"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from runforrestrun.paths import lockdown


@dataclass
class Autonomy:
    ok: bool
    need: str = ""


def check_autonomy(objective: str = "") -> Autonomy:
    """Fail closed when a paid secret is missing or lockdown is on for a job that needs the world."""
    if lockdown():
        return Autonomy(ok=False, need="lockdown is on (RUN_FORREST_LOCKDOWN=1) — sandbox only")
    lower = (objective or "").lower()
    needs_net = any(
        tok in lower
        for tok in ("search the web", "github stars", "http://", "https://", "look up online")
    )
    if needs_net and os.environ.get("RUN_FORREST_OFFLINE", "").strip() in {"1", "true"}:
        return Autonomy(ok=False, need="network (RUN_FORREST_OFFLINE=1)")
    # Never ask for keys in chat. If a named cloud provider is forced and empty, block.
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        return Autonomy(ok=False, need="ANTHROPIC_API_KEY in the environment (not in chat)")
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        return Autonomy(ok=False, need="OPENAI_API_KEY in the environment (not in chat)")
    if not shutil.which("python3") and not shutil.which("python"):
        return Autonomy(ok=False, need="python3 on PATH")
    return Autonomy(ok=True)
