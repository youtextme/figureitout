"""Layer 10 — DORA delivery metrics via OpenTelemetry + JSONL."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from figureitout.config import METRICS_PATH, RUNNER_HOME

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource

    _resource = Resource.create({"service.name": "figureitout"})
    _provider = MeterProvider(resource=_resource)
    metrics.set_meter_provider(_provider)
    _meter = metrics.get_meter("figureitout.dora")
    _g_deploy = _meter.create_gauge("deployment_frequency")
    _g_lead = _meter.create_gauge("lead_time_seconds")
    _g_cfr = _meter.create_gauge("change_failure_rate")
    _g_mttr = _meter.create_gauge("mttr_seconds")
except Exception:  # pragma: no cover
    _g_deploy = _g_lead = _g_cfr = _g_mttr = None


@dataclass
class DoraTracker:
    started_at: float = field(default_factory=time.time)
    first_failure_at: float | None = None
    first_pass_after_failure_at: float | None = None
    total_retries: int = 0
    total_tasks: int = 0

    def mark_judge(self, passed: bool) -> None:
        now = time.time()
        if not passed and self.first_failure_at is None:
            self.first_failure_at = now
        if passed and self.first_failure_at is not None and self.first_pass_after_failure_at is None:
            self.first_pass_after_failure_at = now

    def emit(self, status: str, path: Path | None = None) -> dict[str, Any]:
        ended = time.time()
        deployment_frequency = 1 if status == "done" else 0
        lead_time_seconds = ended - self.started_at
        change_failure_rate = (
            float(self.total_retries) / float(self.total_tasks) if self.total_tasks else 0.0
        )
        if self.first_failure_at and self.first_pass_after_failure_at:
            mttr_seconds = self.first_pass_after_failure_at - self.first_failure_at
        else:
            mttr_seconds = 0.0

        payload = {
            "timestamp": ended,
            "deployment_frequency": deployment_frequency,
            "lead_time_seconds": lead_time_seconds,
            "change_failure_rate": change_failure_rate,
            "mttr_seconds": mttr_seconds,
            "status": status,
        }

        if _g_deploy is not None:
            _g_deploy.set(deployment_frequency)
            _g_lead.set(lead_time_seconds)
            _g_cfr.set(change_failure_rate)
            _g_mttr.set(mttr_seconds)

        out = path or METRICS_PATH
        RUNNER_HOME.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")
        return payload
