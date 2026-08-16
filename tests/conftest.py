"""Public figureitout test defaults — no host-stack imports."""

from __future__ import annotations

import os

os.environ.setdefault("FIGUREITOUT_MOCK", "1")
os.environ.setdefault("LLM_PROVIDER", "mock")
