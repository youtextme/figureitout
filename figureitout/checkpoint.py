"""Durable run state — any agent can stop, start, and continue.

Chat history is not memory. A checkpoint is a short, typed snapshot: the lock,
the phase, the predicates, and the next action. Parents read this file, not blobs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from figureitout.config import jobs_root


CHECKPOINT_NAME = "checkpoint.json"


def job_dir_for(run_id: str) -> Path:
    path = jobs_root() / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def checkpoint_path(run_id: str) -> Path:
    return job_dir_for(run_id) / CHECKPOINT_NAME


def save_checkpoint(run_id: str, state: dict[str, Any]) -> Path:
    payload = dict(state)
    payload["run_id"] = run_id
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = checkpoint_path(run_id)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def load_checkpoint(run_id: str) -> dict[str, Any] | None:
    path = jobs_root() / run_id / CHECKPOINT_NAME
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("run_id") != run_id:
        return None
    return data


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    root = jobs_root()
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not child.is_dir():
            continue
        data = load_checkpoint(child.name)
        if data:
            rows.append(data)
        if len(rows) >= limit:
            break
    return rows
