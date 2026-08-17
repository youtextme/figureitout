"""User observations — how they work, never who they are."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runforrestrun.paths import ensure_layout, observations_dir
from runforrestrun.trail import abstract_text


def record_observation(
    *,
    kind: str,
    note: str,
    example: str = "",
    foundational_need: str = "",
    run_id: str = "",
) -> Path:
    """Write a depersonalized observation. Humans may read it. Agents will."""
    ensure_layout()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = observations_dir() / f"{day}.jsonl"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "note": abstract_text(note),
        "example": abstract_text(example)[:800],
        "foundational_need": foundational_need,
        "run_id": run_id,
        "user": None,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
    md = observations_dir() / f"{day}.md"
    with md.open("a", encoding="utf-8") as fh:
        fh.write(
            f"## {payload['ts']}\n\n"
            f"- Kind: {kind}\n"
            f"- Need: {foundational_need or 'n/a'}\n"
            f"- Note: {payload['note']}\n"
            f"- Example (abstracted): {payload['example'] or 'n/a'}\n\n"
        )
    return path


def recent(limit: int = 20) -> list[dict]:
    ensure_layout()
    rows: list[dict] = []
    files = sorted(observations_dir().glob("*.jsonl"))[-14:]
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:]
