"""Layer 10 — DORA metrics."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["FIGUREITOUT_MOCK"] = "1"
os.environ["LLM_PROVIDER"] = "mock"

from figureitout.config import METRICS_PATH
from figureitout.dora import DoraTracker
from figureitout.runner import run_objective


def test_dora_fields_numeric_after_run(tmp_path: Path):
    metrics_file = tmp_path / "metrics.jsonl"
    tracker = DoraTracker()
    tracker.total_tasks = 2
    tracker.total_retries = 0
    payload = tracker.emit("done", path=metrics_file)
    for key in (
        "deployment_frequency",
        "lead_time_seconds",
        "change_failure_rate",
        "mttr_seconds",
    ):
        assert key in payload
        assert isinstance(payload[key], (int, float))


def test_complete_objective_writes_metrics():
    before = METRICS_PATH.read_text(encoding="utf-8") if METRICS_PATH.exists() else ""
    run_objective("write hello world")
    assert METRICS_PATH.exists()
    after = METRICS_PATH.read_text(encoding="utf-8")
    assert len(after) > len(before)
    last = json.loads(after.strip().splitlines()[-1])
    for key in (
        "deployment_frequency",
        "lead_time_seconds",
        "change_failure_rate",
        "mttr_seconds",
    ):
        assert key in last
        assert isinstance(last[key], (int, float))


def test_change_failure_rate_target(tmp_path: Path):
    tracker = DoraTracker()
    tracker.total_tasks = 10
    tracker.total_retries = 1
    payload = tracker.emit("done", path=tmp_path / "metrics.jsonl")
    # Golden-suite gate: CFR must stay below 0.2 on healthy runs.
    assert payload["change_failure_rate"] < 0.2
