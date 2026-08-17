"""Epistemology for the objective runner — warrants, not paragraphs.

A claim is not true because it was said. It is true enough to proceed only
when it is an atom, its kind is known, and (if it is a fact) a designed
disconfirmation contacted the world and the claim survived.

Semantic memory stores survivals. Chat is not that store.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from figureitout.config import runner_home


class ClaimKind(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    METHOD = "method"


class WarrantStatus(str, Enum):
    UNVERIFIED = "unverified"
    SURVIVED = "survived"
    KILLED = "killed"
    BLOCKED = "blocked"
    PREFERENCE = "preference"


LEGAL_SOURCES = frozenset({"experiment", "failed_check", "user_feedback"})


class ProofGrade(str, Enum):
    """How close a putative proof is to a reading of the meter.

    Citation is not a reading. Replication and cheap ping are.
    """

    NONE = "none"
    CITATION = "citation"
    CHEAP_PING = "cheap_ping"
    REPLICATION = "replication"


PREFERENCE_MARKERS = (
    "i want",
    "i need",
    "prefer",
    "please use",
    "make it pink",
    "make it blue",
    "my favorite",
    "taste",
    "aesthetic",
)


class Claim(BaseModel):
    atom: str
    kind: ClaimKind
    status: WarrantStatus = WarrantStatus.UNVERIFIED
    disconfirmation: str = ""
    pointers: list[str] = Field(default_factory=list)
    observation: str = ""
    source: str = ""  # experiment | failed_check | user_feedback — never "text"

    def is_warranted(self) -> bool:
        if self.kind == ClaimKind.PREFERENCE:
            return self.status == WarrantStatus.PREFERENCE and bool(self.pointers)
        if self.kind == ClaimKind.FACT:
            return (
                self.status == WarrantStatus.SURVIVED
                and bool(self.pointers)
                and bool(self.observation)
                and self.source in LEGAL_SOURCES
            )
        return self.status == WarrantStatus.SURVIVED and bool(self.observation)


def already_proven(claim: Claim) -> bool:
    """Operational 'already proven': warranted atom, not a citation."""
    return claim.is_warranted()


def grade_proof(
    *,
    observation: str,
    pointers: list[str],
    source: str,
    existing_warranted: bool = False,
) -> ProofGrade:
    """Citation names a document. Replication and ping read the meter."""
    prose = text_is_not_warrant(observation)
    has_ptr = bool(pointers)
    legal = source in LEGAL_SOURCES
    if existing_warranted and legal and has_ptr and not prose:
        return ProofGrade.CHEAP_PING
    if legal and has_ptr and not prose:
        return ProofGrade.REPLICATION
    if has_ptr and (not legal or prose):
        return ProofGrade.CITATION
    return ProofGrade.NONE


def normalize_atom(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def classify_kind(text: str) -> ClaimKind:
    lower = (text or "").lower()
    if any(m in lower for m in PREFERENCE_MARKERS):
        return ClaimKind.PREFERENCE
    if any(tok in lower for tok in ("should feel", "looks better", "nice color", "i like")):
        return ClaimKind.PREFERENCE
    if any(tok in lower for tok in ("search first", "use this tool", "run pytest", "method")):
        return ClaimKind.METHOD
    return ClaimKind.FACT


def text_is_not_warrant(text: str) -> bool:
    """True when the alleged proof is prose rather than a pointer/observation."""
    lower = (text or "").lower()
    if not lower.strip():
        return True
    if any(
        p in lower
        for p in (
            "i read that",
            "according to various",
            "as we all know",
            "clearly",
            "obviously",
            "completed task",
        )
    ):
        return True
    return False


def designed_disconfirmation(atom: str, kind: ClaimKind) -> str:
    if kind == ClaimKind.PREFERENCE:
        return "Do not experiment. Ask or record the preference."
    if kind == ClaimKind.METHOD:
        return f"Run the method once on this workspace; if it fails, the method-atom dies: {atom}"
    lower = atom.lower()
    if "exist" in lower or "file" in lower:
        return f"If this file/path is missing, the claim is false: {atom}"
    if any(tok in lower for tok in ("test", "pytest", "pass")):
        return f"If the named check is not green, the claim is false: {atom}"
    return f"Name a probe that would fail if this were false, then run it: {atom}"


class TruthStore:
    """Semantic memory — warranted atoms with pointers. Not chat."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (runner_home() / "semantic_truth.jsonl")

    def _rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def lookup(self, atom: str) -> Claim | None:
        key = normalize_atom(atom)
        for row in reversed(self._rows()):
            if normalize_atom(str(row.get("atom", ""))) == key:
                return Claim.model_validate(row)
        return None

    def record(self, claim: Claim) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = claim.model_dump()
        payload["ts"] = datetime.now(timezone.utc).isoformat()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
        return self.path


def promote_if_survived(
    *,
    atom: str,
    kind: ClaimKind,
    observation: str,
    pointers: list[str],
    source: str,
    store: TruthStore | None = None,
) -> Claim:
    """Refuse to mark SURVIVED when the proof is prose or the source is illegal."""
    if source not in LEGAL_SOURCES:
        raise ValueError("warrant source must be experiment, failed_check, or user_feedback")
    if kind == ClaimKind.FACT and (text_is_not_warrant(observation) or not pointers):
        claim = Claim(
            atom=atom,
            kind=kind,
            status=WarrantStatus.UNVERIFIED,
            disconfirmation=designed_disconfirmation(atom, kind),
            pointers=list(pointers),
            observation=observation,
            source=source,
        )
        return claim
    if kind == ClaimKind.PREFERENCE:
        claim = Claim(
            atom=atom,
            kind=kind,
            status=WarrantStatus.PREFERENCE,
            disconfirmation=designed_disconfirmation(atom, kind),
            pointers=list(pointers) or ["user"],
            observation=observation,
            source="user_feedback",
        )
    else:
        claim = Claim(
            atom=atom,
            kind=kind,
            status=WarrantStatus.SURVIVED,
            disconfirmation=designed_disconfirmation(atom, kind),
            pointers=list(pointers),
            observation=observation,
            source=source,
        )
    (store or TruthStore()).record(claim)
    return claim


def cheap_confirm(existing: Claim, ping_observation: str, ping_pointer: str) -> Claim:
    """Already-warranted atom: one ping that could still kill it. No literature review."""
    if not existing.is_warranted():
        existing.status = WarrantStatus.UNVERIFIED
        return existing
    if text_is_not_warrant(ping_observation) or not ping_pointer:
        existing.status = WarrantStatus.UNVERIFIED
        return existing
    existing.observation = ping_observation
    if ping_pointer not in existing.pointers:
        existing.pointers.append(ping_pointer)
    existing.status = WarrantStatus.SURVIVED if existing.kind == ClaimKind.FACT else existing.status
    TruthStore().record(existing)
    return existing


def split_atoms(objective: str) -> list[Claim]:
    """First-principles split: one claim per sentence-ish clause; kind tagged."""
    text = (objective or "").strip()
    parts = [p.strip() for p in re.split(r"[.;]+|\band then\b|\band\b", text) if p.strip()]
    if not parts:
        parts = [text]
    atoms: list[Claim] = []
    seen: set[str] = set()
    for part in parts[:8]:
        key = normalize_atom(part)
        if len(key) < 4 or key in seen:
            continue
        seen.add(key)
        kind = classify_kind(part)
        atoms.append(
            Claim(
                atom=part,
                kind=kind,
                status=(
                    WarrantStatus.PREFERENCE
                    if kind == ClaimKind.PREFERENCE
                    else WarrantStatus.UNVERIFIED
                ),
                disconfirmation=designed_disconfirmation(part, kind),
            )
        )
    if not atoms:
        atoms.append(
            Claim(
                atom=text or "the ask",
                kind=ClaimKind.FACT,
                disconfirmation=designed_disconfirmation(text or "the ask", ClaimKind.FACT),
            )
        )
    return atoms
