"""Foundational capabilities — rare, credited, opt-in to the community."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from runforrestrun.observer import recent, record_observation
from runforrestrun.paths import ensure_layout, platform_dir
from runforrestrun.trail import abstract_text
from runforrestrun.voice import learned_capability


# Not every prompt. A capability is a pattern that would help millions
# without carrying anyone's private work.
_FOUNDATIONS = (
    (
        "query-bank-before-sql",
        "Look up known queries before inventing SQL",
        re.compile(r"\b(sql|warehouse|query bank|known query)\b", re.I),
        "Stops invented tables from becoming 'official' numbers.",
    ),
    (
        "click-path-proof",
        "Prove a UI path with a real click, not a screenshot claim",
        re.compile(r"\b(click path|playwright|customer ux|button)\b", re.I),
        "UI work is not done until a human-path is evidenced.",
    ),
    (
        "cheap-ping-not-literature",
        "Re-contact a stored pointer instead of re-reading blogs",
        re.compile(r"\b(cheap ping|already proven|citation launder)\b", re.I),
        "Stops agents from spending a laboratory on settled atoms.",
    ),
    (
        "papercut-router",
        "Mechanical papercut vs laboratory routing",
        re.compile(r"\b(papercut|just research|where is )\b", re.I),
        "Keeps small asks cheap without letting real jobs skip the probe.",
    ),
)


def maybe_propose(objective: str, run_id: str = "") -> dict | None:
    """At most one proposal. Never a billion PRs."""
    ensure_layout()
    text = objective or ""
    for slug, title, pattern, why in _FOUNDATIONS:
        if not pattern.search(text):
            continue
        dest = platform_dir() / "proposals" / f"{slug}.md"
        if dest.exists():
            continue
        body = (
            f"# {title}\n\n"
            f"Foundational. Not a user's private project.\n\n"
            f"Why the world: {why}\n\n"
            f"Abstracted example: {abstract_text(text)[:400]}\n\n"
            f"Credits: the operator who opts in.\n"
        )
        dest.write_text(body, encoding="utf-8")
        record_observation(
            kind="capability",
            note=title,
            example=text,
            foundational_need=slug,
            run_id=run_id,
        )
        return {
            "slug": slug,
            "title": title,
            "path": str(dest),
            "voice": learned_capability(title=title, why_world=why),
            "consent_needed": True,
        }
    # Cluster: if many observations share a need, surface it once.
    needs: dict[str, int] = {}
    for row in recent(50):
        need = str(row.get("foundational_need") or "")
        if need:
            needs[need] = needs.get(need, 0) + 1
    return None


def consent_receipt(slug: str, *, yes: bool, credit_name: str) -> Path:
    path = platform_dir() / "consent.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "slug": slug,
        "yes": yes,
        "credit": credit_name if yes else None,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    return path


def pr_draft(slug: str, credit_name: str) -> str:
    proposal = platform_dir() / "proposals" / f"{slug}.md"
    body = proposal.read_text(encoding="utf-8") if proposal.exists() else slug
    return (
        f"## Community skill: {slug}\n\n"
        f"Full credit: **{credit_name}**\n\n"
        f"This is a foundational capability extracted from how an operator "
        f"works — not from their private documents or product data.\n\n"
        f"{body}\n"
    )
