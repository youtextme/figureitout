"""Community loops — latest catalog, not a baseline frozen at install time."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runforrestrun.paths import canonical_dir, ensure_layout
from runforrestrun.upstream import sync_from_upstream


def bundled_path() -> Path:
    return Path(__file__).resolve().parent / "frontier.json"


def load_catalog() -> dict:
    ensure_layout()
    for candidate in (canonical_dir() / "runforrestrun" / "frontier.json", bundled_path()):
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return {"catalog": []}


def refresh_frontier(*, packaged_root: Path | None = None) -> Path:
    """Copy or sync frontier.json into canonical store."""
    dest = canonical_dir() / "runforrestrun"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "frontier.json"
    # upstream sync may have already written frontier.json
    if not target.exists():
        src = bundled_path()
        payload = json.loads(src.read_text(encoding="utf-8"))
        payload["refreshed_at"] = datetime.now(timezone.utc).isoformat()
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target
