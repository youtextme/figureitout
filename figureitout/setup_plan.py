"""Build plan + permissions for figureitout v0.1 (executable checklist)."""

from __future__ import annotations

# Permissions required
PERMISSIONS = {
    "filesystem": "~/.myrunner/runs/<run_id> write sandbox",
    "network_research": "TAVILY_API_KEY (optional; stub without it)",
    "network_llm_kilocode": "KILOCODE_API_KEY optional; kilo-auto/free works anonymously",
    "network_llm_local": "http://localhost:11435/v1 tireless-router (fallback)",
    "network_llm_cloud": "ANTHROPIC_API_KEY or OPENAI_API_KEY as later fallbacks",
    "browser": "playwright chromium for SandboxedComputer.browse",
    "tracing": "LANGCHAIN_API_KEY + LANGCHAIN_TRACING_V2=true for LangSmith",
    "policy": "CEL policies in figureitout/policies.yaml",
}

# Setup sequence
SETUP_STEPS = [
    "python -m pip install -e '.[figureitout,dev]'",
    "playwright install chromium",
    "Ensure Kilo Gateway (kilo-auto/free) or tireless-router on :11435",
    "Optional: export TAVILY_API_KEY, LANGCHAIN_API_KEY",
    "pytest -x --tb=short tests/test_figureitout_layer*.py tests/test_dora.py",
    "python -m figureitout 'write hello world'",
]
