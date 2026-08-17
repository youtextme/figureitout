"""Shared configuration for the figureitout objective runner."""

from __future__ import annotations

import os
from pathlib import Path


RUNNER_HOME = Path.home() / ".myrunner"
METRICS_PATH = RUNNER_HOME / "metrics.jsonl"
MEMORY_USER_ID = "runner"
TRUSTED_ENV = "FIGUREITOUT_TRUSTED"
KILL_SWITCH_ENV = "FIGUREITOUT_LOCKDOWN"


def runner_home() -> Path:
    """~/.myrunner unless FIGUREITOUT_HOME is set (tests / alternate machines)."""
    override = os.environ.get("FIGUREITOUT_HOME", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".myrunner"


def jobs_root() -> Path:
    """On-disk job folders. Lockdown sandboxes under runner_home()/runs."""
    override = os.environ.get("FIGUREITOUT_JOBS_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if not is_trusted():
        return runner_home() / "runs"
    return Path.home() / ".letscook" / "cursor-jobs"


def is_trusted() -> bool:
    """Full-access mode — default ON. Set FIGUREITOUT_LOCKDOWN=1 or FIGUREITOUT_TRUSTED=0 to sandbox."""
    if os.environ.get(KILL_SWITCH_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return False
    flag = os.environ.get(TRUSTED_ENV, "1").strip().lower()
    return flag in {"1", "true", "yes", "on", ""}


def use_mock() -> bool:
    """Deterministic stubs when FIGUREITOUT_MOCK=1 or no cloud keys (tests / offline)."""
    flag = os.environ.get("FIGUREITOUT_MOCK", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return True
    if flag in {"0", "false", "no", "off"}:
        return False
    provider = os.environ.get("LLM_PROVIDER", "local").strip().lower()
    if provider in {"local", "tireless", "ollama"}:
        return False
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        return True
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        return True
    return False


def llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "local").strip().lower()


def local_base_url() -> str:
    return os.environ.get(
        "FIGUREITOUT_LOCAL_BASE_URL",
        os.environ.get("OPENAI_BASE_URL", "http://localhost:11435/v1"),
    )


def local_model() -> str:
    return os.environ.get("FIGUREITOUT_LOCAL_MODEL", "tireless-router")


def vision_model() -> str:
    return os.environ.get("FIGUREITOUT_VISION_MODEL", os.environ.get("VISION_MODEL", "llava:7b"))


def thinking_model() -> str:
    return os.environ.get(
        "FIGUREITOUT_THINKING_MODEL",
        os.environ.get("THINKING_MODEL", local_model()),
    )


def anthropic_model() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


def openai_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o")


def workspace_root() -> Path:
    return Path(os.environ.get("FIGUREITOUT_WORKSPACE", os.getcwd())).expanduser().resolve()
