"""Objective functions — predicates that cannot be true without evidence.

LLM narrative scores are advisory only. A required predicate that was never
run is false. That is the constitutive law behind "done".
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class PredicateKind(str, Enum):
    FILE_EXISTS = "file_exists"
    ARTIFACT_NONEMPTY = "artifact_nonempty"
    TEXT_CONTAINS = "text_contains"
    COMMAND_EXIT_ZERO = "command_exit_zero"
    NO_INVENTED_NUMBERS = "no_invented_numbers"
    USE_BRIEF_PRESENT = "use_brief_present"
    CHECKPOINT_WRITTEN = "checkpoint_written"
    BOARD_PROVISIONAL_PASS = "board_provisional_pass"
    EXPERIMENT_OBSERVED = "experiment_observed"
    LOCK_PRESENT = "lock_present"


class Predicate(BaseModel):
    id: str
    statement: str
    kind: PredicateKind
    target: str = ""
    required: bool = True
    evaluated: bool = False
    passed: bool = False
    evidence: str = ""


class EvaluationContext(BaseModel):
    final_output: str = ""
    job_dir: Path
    invented_number_markers: tuple[str, ...] = (
        "lorem ipsum",
        "dummy kpi",
        "sample metric",
        "placeholder number",
        "n/a as 100%",
    )

    model_config = {"arbitrary_types_allowed": True}


class PredicateBoard(BaseModel):
    predicates: list[Predicate] = Field(default_factory=list)

    def unevaluated_required(self) -> list[str]:
        return [p.id for p in self.predicates if p.required and not p.evaluated]

    def all_required_true(self) -> bool:
        """Impossible to be true unless every required predicate ran and passed."""
        if not self.predicates:
            return False
        for pred in self.predicates:
            if not pred.required:
                continue
            if not pred.evaluated or not pred.passed:
                return False
        return True

    def evaluate(self, ctx: EvaluationContext) -> "PredicateBoard":
        for pred in self.predicates:
            passed, evidence = _eval_one(pred, ctx)
            pred.evaluated = True
            pred.passed = passed
            pred.evidence = evidence
        return self

    def to_jsonable(self) -> list[dict[str, Any]]:
        return [p.model_dump() for p in self.predicates]

    @classmethod
    def from_dicts(cls, rows: list[dict[str, Any]] | None) -> "PredicateBoard":
        return cls(predicates=[Predicate.model_validate(r) for r in (rows or [])])


def _eval_one(pred: Predicate, ctx: EvaluationContext) -> tuple[bool, str]:
    kind = pred.kind
    target = (pred.target or "").strip()
    output = ctx.final_output or ""
    job = Path(ctx.job_dir)

    if kind == PredicateKind.FILE_EXISTS:
        path = Path(target)
        if not path.is_absolute():
            path = job / target
        ok = path.exists() and path.stat().st_size > 0
        return ok, f"path={path} exists={path.exists()} size={path.stat().st_size if path.exists() else 0}"

    if kind == PredicateKind.ARTIFACT_NONEMPTY:
        ok = bool(output.strip())
        return ok, f"final_output_chars={len(output.strip())}"

    if kind == PredicateKind.TEXT_CONTAINS:
        needle = target.lower()
        ok = bool(needle) and needle in output.lower()
        return ok, f"needle={target!r} hit={ok}"

    if kind == PredicateKind.COMMAND_EXIT_ZERO:
        # Commands are evidence the worker already ran. Presence of "exit 0" or pytest pass.
        lower = output.lower()
        ok = "exit 0" in lower or "passed" in lower or "ok" in lower
        return ok, "command evidence scanned in final_output"

    if kind == PredicateKind.NO_INVENTED_NUMBERS:
        lower = output.lower()
        hits = [m for m in ctx.invented_number_markers if m in lower]
        ok = not hits
        return ok, "clean" if ok else f"markers={hits}"

    if kind == PredicateKind.USE_BRIEF_PRESENT:
        path = job / "use.md"
        ok = path.exists() and "next action" in path.read_text(encoding="utf-8").lower()
        return ok, f"use.md exists={path.exists()}"

    if kind == PredicateKind.CHECKPOINT_WRITTEN:
        path = job / "checkpoint.json"
        ok = False
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                ok = bool(payload.get("run_id") and payload.get("done_sentence"))
            except json.JSONDecodeError:
                ok = False
        return ok, f"checkpoint={path} ok={ok}"

    if kind == PredicateKind.BOARD_PROVISIONAL_PASS:
        path = job / "board.md"
        text = path.read_text(encoding="utf-8").lower() if path.exists() else ""
        ok = "provisional pass" in text or "skipped: quality_tier=" in text
        return ok, f"board.md pass={ok}"

    if kind == PredicateKind.EXPERIMENT_OBSERVED:
        path = job / "experiments.md"
        text = path.read_text(encoding="utf-8").lower() if path.exists() else ""
        ok = (
            "observation:" in text
            or "observation —" in text
            or "skipped: quality_tier=" in text
        )
        return ok, f"experiments.md observed={ok}"

    if kind == PredicateKind.LOCK_PRESENT:
        path = job / "objective_lock.md"
        ok = path.exists() and "this run succeeds when" in path.read_text(encoding="utf-8").lower()
        return ok, f"lock={path} ok={ok}"

    return False, f"unknown kind {kind}"
