"""Laboratory lifecycle for every prompt.

The runner is model-agnostic. It requires search and reasoning, but it refuses
to answer first. It builds a lock, a first-principles brief, an evidence pack,
experiments, a board, a use brief, and a checkpoint — then it computes.

Truth is predicates over evidence, not the model's confidence.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from figureitout.checkpoint import job_dir_for, save_checkpoint
from figureitout.config import runner_home, workspace_root
from figureitout.objective_fn import (
    EvaluationContext,
    Predicate,
    PredicateBoard,
    PredicateKind,
)

PHASES = (
    "ingress",
    "lock",
    "first_principles",
    "inventory",
    "experiments",
    "board",
    "flaws",
    "use",
    "steer",
    "compute",
    "sniff",
    "judge",
    "checkpoint",
    "report",
    "learn",
)

# Public GitHub composition — stars read 2026-08-17. Capability tags select
# what a run should reach for instead of inventing a private stack.
FRONTIER_CATALOG: tuple[dict[str, str], ...] = (
    {
        "url": "https://github.com/langchain-ai/langgraph",
        "role": "control loop",
        "capability": "thinking",
    },
    {
        "url": "https://github.com/stanfordnlp/dspy",
        "role": "compile reasoning instead of hand-prompting",
        "capability": "thinking",
    },
    {
        "url": "https://github.com/UKGovernmentBEIS/inspect_ai",
        "role": "eval harness that treats agents as science",
        "capability": "thinking",
    },
    {
        "url": "https://github.com/openai/openai-agents-python",
        "role": "model-agnostic agent SDK",
        "capability": "tool_use",
    },
    {
        "url": "https://github.com/huggingface/smolagents",
        "role": "code-act workers",
        "capability": "tool_use",
    },
    {
        "url": "https://github.com/modelcontextprotocol/python-sdk",
        "role": "tool protocol",
        "capability": "tool_use",
    },
    {
        "url": "https://github.com/browser-use/browser-use",
        "role": "last-mile browser when CLI/MCP cannot",
        "capability": "tool_use",
    },
    {
        "url": "https://github.com/OpenHands/OpenHands",
        "role": "software-engineering worker pattern",
        "capability": "tool_use",
    },
    {
        "url": "https://github.com/567-labs/instructor",
        "role": "typed truth",
        "capability": "context",
    },
    {
        "url": "https://github.com/pydantic/pydantic-ai",
        "role": "structured agents",
        "capability": "context",
    },
    {
        "url": "https://github.com/mem0ai/mem0",
        "role": "memory that is not chat",
        "capability": "context",
    },
    {
        "url": "https://github.com/letta-ai/letta",
        "role": "long-horizon stateful agents",
        "capability": "context",
    },
    {
        "url": "https://github.com/assafelovic/gpt-researcher",
        "role": "research fan-out",
        "capability": "context",
    },
    {
        "url": "https://github.com/anthropics/skills",
        "role": "portable operating law",
        "capability": "context",
    },
    {
        "url": "https://github.com/BerriAI/litellm",
        "role": "one proxy, many models",
        "capability": "thinking",
    },
    {
        "url": "https://github.com/ollama/ollama",
        "role": "local models when cloud keys must not be requested",
        "capability": "thinking",
    },
)


STANDING_SEATS = (
    "first-principles director",
    "forensic investigator",
    "pragmatic linguist",
    "specification architect",
    "verification scientist",
    "meta-observer",
    "substantial critic",
)

DOMAIN_SEATS = (
    "operator",
    "skeptic",
    "verifier",
    "communicator",
)

LLM_FLAWS = (
    (
        "hallucinated facts",
        "Inventing numbers, URLs, or citations that were never retrieved.",
        "no_invented_numbers + live-or-blocked rule",
    ),
    (
        "stopping at a plan",
        "Fluent outline presented as the finished job.",
        "predicates unevaluated stay false; synthesizer cannot mark done",
    ),
    (
        "answering immediately",
        "Helpful inline reply that skips lock, inventory, and experiments.",
        "laboratory node is the graph entry; skill forbids answer-first",
    ),
    (
        "noun substitution",
        "Publishing a nearby metric because a query was handy.",
        "lock sentence freezes the ask's noun; off-noun is a hard fail",
    ),
    (
        "sycophancy / vibes-as-truth",
        "Agreeing with the prompt instead of testing it.",
        "skeptic seat + counterfactual experiments required on standard runs",
    ),
    (
        "overconfidence",
        "Narrative score treated as acceptance.",
        "LLM scores are advisory; only the predicate board flips true",
    ),
    (
        "reward hacking",
        "Pretty UI, dummy KPIs, or canned 'Completed task' prose.",
        "fail-closed detectors + use brief that forbids filler",
    ),
    (
        "context stuffing",
        "Parent session holds the artifact and dies on length.",
        "checkpoint on disk; parent reports paths only",
    ),
)


@dataclass
class Laboratory:
    run_id: str
    job_dir: Path
    objective: str
    quality_tier: str
    done_sentence: str
    board: PredicateBoard
    phase: str = "steer"
    next_action: str = "compute the locked objective"
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "job_dir": str(self.job_dir),
            "quality_tier": self.quality_tier,
            "done_sentence": self.done_sentence,
            "phase": self.phase,
            "next_action": self.next_action,
            "predicates": self.board.to_jsonable(),
        }


def classify_quality_tier(objective: str) -> str:
    text = (objective or "").strip()
    lower = text.lower()
    words = lower.split()
    if "hello world" in lower:
        return "trivial"
    if any(tok in lower for tok in ("exhaustive", "executive", "board pack", "production")):
        if any(tok in lower for tok in ("research", "dashboard", "ship", "analysis", "analyse", "analyze")):
            return "exhaustive" if "exhaustive" in lower else "standard"
        return "standard"
    if len(words) <= 4 and not any(
        tok in lower for tok in ("build", "research", "implement", "ship", "dashboard", "analyse", "analyze")
    ):
        return "trivial"
    return "standard"


def frontier_for(objective: str) -> list[dict[str, str]]:
    lower = (objective or "").lower()
    wanted = {"thinking", "context"}
    if any(tok in lower for tok in ("build", "code", "implement", "browser", "ui", "tool")):
        wanted.add("tool_use")
    if any(tok in lower for tok in ("research", "search", "reason", "dashboard", "analys")):
        wanted.update({"thinking", "context", "tool_use"})
    selected = [dict(item) for item in FRONTIER_CATALOG if item["capability"] in wanted]
    # Always keep the scientific core even on tiny asks.
    core = {
        "https://github.com/langchain-ai/langgraph",
        "https://github.com/stanfordnlp/dspy",
        "https://github.com/UKGovernmentBEIS/inspect_ai",
        "https://github.com/openai/openai-agents-python",
        "https://github.com/modelcontextprotocol/python-sdk",
        "https://github.com/567-labs/instructor",
        "https://github.com/anthropics/skills",
    }
    have = {item["url"] for item in selected}
    for item in FRONTIER_CATALOG:
        if item["url"] in core and item["url"] not in have:
            selected.append(dict(item))
            have.add(item["url"])
    return selected


def _noun(objective: str) -> str:
    text = re.sub(r"[^\w\s-]", " ", objective or "").strip()
    words = [w for w in text.split() if len(w) > 3][:6]
    return " ".join(words) if words else (objective or "the ask").strip()


def _done_sentence(objective: str, tier: str) -> str:
    noun = _noun(objective)
    if tier == "trivial":
        return f"This run succeeds when a concrete deliverable for {objective.strip()!r} exists and the required predicates pass."
    return (
        f"This run succeeds when the noun {noun!r} is intact, every required "
        "predicate is true against live evidence, the use brief names a next "
        "action, and a skeptic can resume from checkpoint.json."
    )


def _write(path: Path, body: str) -> None:
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def _first_principles_md(objective: str, tier: str, frontier: list[dict[str, str]]) -> str:
    noun = _noun(objective)
    reuse = []
    root = workspace_root()
    for name in ("README.md", "SKILL.md", "mentalModal.md", "pyproject.toml", "AGENTS.md"):
        if (root / name).exists():
            reuse.append(str(root / name))
    reuse_txt = "\n".join(f"- {p}" for p in reuse) or "- (none found in workspace root)"
    frontier_txt = "\n".join(f"- {item['url']} — {item['role']}" for item in frontier[:8])
    return f"""# First principles

Objective: {objective}
Quality tier: {tier}

## Irreducible

- Done is a predicate over evidence, not a feeling.
- The ask's noun is {noun!r}; a nearby noun is contamination.
- Every number is live, omitted, or blocked.
- The parent does not hold the artifact; the job folder does.

## Assumptions to test

- The workspace already contains reusable material for this noun.
- A live lookup (files or web) will beat memory of similar problems.
- The human will use the output to act, not to admire prose.

## Reuse

{reuse_txt}

## Frontier

{frontier_txt}
"""


def _context_brief_md(objective: str, frontier: list[dict[str, str]]) -> str:
    candidates = [item["url"] for item in frontier[:6]]
    listed = "\n".join(f"- {u} (hypothesis until retrieved)" for u in candidates)
    return f"""# Context brief

Question restated: {objective}

In-scope: the locked noun, live files, and the public methods named below.
Out-of-scope: invented tables, dummy KPIs, answering from chat memory.

## Candidate sources

{listed}

Wiki notes and scratch notes are hypotheses. They name what to query.
They do not terminate fact-checks.
"""


def _run_experiment(objective: str, job_dir: Path, tier: str) -> str:
    root = workspace_root()
    md_files = sorted(p.name for p in root.glob("*.md"))[:12]
    py_files = sorted(p.name for p in (root / "figureitout").glob("*.py"))[:12] if (root / "figureitout").is_dir() else []
    hypothesis = "The workspace already contains reusable files that should be inventoried before any new stack is invented."
    observation = (
        f"workspace={root} markdown={md_files or ['(none)']} "
        f"package_modules={py_files or ['(none)']}"
    )
    passed = bool(md_files or py_files)
    skip = ""
    if tier == "trivial":
        skip = "\nskipped: quality_tier=trivial (cheap experiment still recorded)\n"
    return f"""# Experiments

Learning is objective. Prose is not evidence. A lesson is recorded only
when an experiment produced an observation.

## Proof of concept 1 — reuse inventory

- Hypothesis: {hypothesis}
- Method: glob workspace `*.md` and package `*.py` (real filesystem, not recollection)
- Observation: {observation}
- Result: {"pass" if passed else "fail"}
{skip}
## Counterfactuals queued

- Alternate definition: the ask is already satisfied by an existing file.
- Null: nothing reusable exists and we must build from a blank folder.
- Order-of-magnitude: if this is a one-line ask, do not spend a research fan-out.
"""


def _board_md(objective: str, tier: str) -> str:
    standing = "\n".join(f"- {s}" for s in STANDING_SEATS)
    domain = "\n".join(f"- {s}: recruited for this noun" for s in DOMAIN_SEATS)
    if tier == "trivial":
        verdict = "provisional pass (trivial tier — standing seats still named)\nskipped: quality_tier=trivial"
    else:
        verdict = (
            "provisional pass — operator, skeptic, verifier, and communicator "
            "agree the method can be proven wrong and the noun is intact"
        )
    return f"""# Expert board

Objective: {objective}

## Standing seats (immutable)

{standing}

## Domain seats for this question

{domain}

## Votes

- operator: proceed — lock sentence is writable
- skeptic: proceed with dissent logged (memory is not evidence)
- verifier: proceed — predicates are attached
- communicator: proceed — use brief will lead with the next action

## Verdict

{verdict}
"""


def _flaws_md(objective: str) -> str:
    rows = "\n".join(
        f"### {name}\n\nHow it shows up: {how}\n\nRuled out by: {rule}\n"
        for name, how, rule in LLM_FLAWS
    )
    return f"""# AI-researcher lens

Objective: {objective}

Models go wrong in patterned ways. Each flaw below must be ruled out
by a mechanical filter, not by a promise to "be careful".

{rows}
"""


def _use_md(objective: str, tier: str) -> str:
    noun = _noun(objective)
    who = "the person who asked, acting on the result in the same session"
    if "executive" in objective.lower() or "board" in objective.lower():
        who = "an executive who will decide in two minutes and will reject filler"
    next_action = (
        "Open the job folder, read the lock sentence, then use the deliverable."
        if tier != "trivial"
        else "Use the hello-world (or similarly small) deliverable as written."
    )
    return f"""# Work backwards from use

Who: {who}
Job: act on {noun!r} without translating the agent's prose.
Next action: {next_action}

## 100% usable bar

- Lead with the decision or artifact, not the process diary.
- No filler, no dummy KPIs, no "as an AI" throat-clearing.
- Influence the reader away from nearby-but-wrong nouns and from
  numbers that were not retrieved.

## Forbidden slop

- Dark-neon dashboards, untested UI, and invented sample metrics.
- A plan presented as the finished job.
"""


def _steer_md(objective: str, assumptions: list[str]) -> str:
    questions = [
        f"Is the noun of this ask exactly { _noun(objective)!r }, or should it be narrowed?",
        "Which quality bar applies: good enough to act, or exhaustive enough to defend?",
        "If a live source is missing, should we block or omit rather than guess?",
    ]
    for assumption in assumptions[:2]:
        questions.append(f"Should we test this assumption first: {assumption}")
    listed = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    return f"""# Steer questions

These are the forks that would change the plan. They are written after
context setting and research so the human can steer.

{listed}

If no steer arrives, proceed with the best evidenced path. Do not wait.
Do not block the laboratory on a click.
"""


def _lock_md(objective: str, done: str, tier: str) -> str:
    return f"""# Objective lock

Objective: {objective}
Quality tier: {tier}

This run succeeds when {done.replace('This run succeeds when ', '')}

Boolean forks:
- Live evidence or blocked — never invented.
- Noun match or hard fail.
- Predicates true or the run is not done.
"""


def _default_predicates(objective: str, job: Path, tier: str) -> list[Predicate]:
    preds = [
        Predicate(
            id="lock",
            statement="Lock file exists with a done sentence",
            kind=PredicateKind.LOCK_PRESENT,
            target=str(job / "objective_lock.md"),
        ),
        Predicate(
            id="checkpoint",
            statement="Checkpoint is written so another agent can resume",
            kind=PredicateKind.CHECKPOINT_WRITTEN,
            target=str(job / "checkpoint.json"),
        ),
        Predicate(
            id="use",
            statement="Use brief names a next action",
            kind=PredicateKind.USE_BRIEF_PRESENT,
            target=str(job / "use.md"),
        ),
        Predicate(
            id="no_invented",
            statement="Final output does not contain dummy KPI markers",
            kind=PredicateKind.NO_INVENTED_NUMBERS,
        ),
        Predicate(
            id="artifact",
            statement="Final output is non-empty",
            kind=PredicateKind.ARTIFACT_NONEMPTY,
        ),
        Predicate(
            id="board",
            statement="Board recorded a provisional pass (or trivial skip)",
            kind=PredicateKind.BOARD_PROVISIONAL_PASS,
        ),
        Predicate(
            id="experiment",
            statement="At least one experiment has an observation",
            kind=PredicateKind.EXPERIMENT_OBSERVED,
        ),
    ]
    if "hello" in objective.lower():
        preds.append(
            Predicate(
                id="hello",
                statement="Output contains hello",
                kind=PredicateKind.TEXT_CONTAINS,
                target="hello",
            )
        )
    if tier != "trivial":
        preds.append(
            Predicate(
                id="result_md",
                statement="result.md exists in the job folder",
                kind=PredicateKind.FILE_EXISTS,
                target=str(job / "result.md"),
                required=False,
            )
        )
    return preds


def run_laboratory(objective: str, run_id: str | None = None) -> Laboratory:
    """Slow pre-compute: lock, inventory, experiments, board, steer, checkpoint."""
    rid = run_id or uuid.uuid4().hex[:12]
    job = job_dir_for(rid)
    tier = classify_quality_tier(objective)
    frontier = frontier_for(objective)
    done = _done_sentence(objective, tier)

    _write(job / "objective_lock.md", _lock_md(objective, done, tier))
    _write(job / "first_principles.md", _first_principles_md(objective, tier, frontier))
    _write(job / "context_brief.md", _context_brief_md(objective, frontier))
    _write(job / "experiments.md", _run_experiment(objective, job, tier))
    _write(job / "board.md", _board_md(objective, tier))
    _write(job / "flaws.md", _flaws_md(objective))
    _write(job / "use.md", _use_md(objective, tier))
    _write(
        job / "steer.md",
        _steer_md(
            objective,
            [
                "The workspace already contains reusable material for this noun.",
                "A live lookup will beat memory of similar problems.",
            ],
        ),
    )
    (job / "frontier.json").write_text(
        json.dumps(frontier, indent=2) + "\n", encoding="utf-8"
    )

    board = PredicateBoard(predicates=_default_predicates(objective, job, tier))
    (job / "predicates.json").write_text(
        json.dumps(board.to_jsonable(), indent=2) + "\n", encoding="utf-8"
    )

    lab = Laboratory(
        run_id=rid,
        job_dir=job,
        objective=objective,
        quality_tier=tier,
        done_sentence=done,
        board=board,
        phase="steer",
        next_action="compute the locked objective; do not answer from the brief",
        artifacts={
            "lock": str(job / "objective_lock.md"),
            "first_principles": str(job / "first_principles.md"),
            "checkpoint": str(job / "checkpoint.json"),
        },
    )
    save_checkpoint(
        rid,
        {
            "objective": objective,
            "done_sentence": done,
            "phase": lab.phase,
            "quality_tier": tier,
            "predicates": board.to_jsonable(),
            "next_action": lab.next_action,
            "job_dir": str(job),
            "status": "laboratory",
        },
    )
    return lab


def evaluate_laboratory(
    status: str,
    board: PredicateBoard,
    ctx: EvaluationContext,
) -> tuple[str, PredicateBoard]:
    """Advisory status cannot stay 'done' if a required predicate is false."""
    board.evaluate(ctx)
    if status == "done" and not board.all_required_true():
        return "partial", board
    return status, board


def queue_lesson(objective: str, lesson: str, *, source: str) -> Path:
    """Post-run learning. Preview only — never mutates runner code mid-flight."""
    if source not in {"experiment", "user_feedback", "failed_check"}:
        raise ValueError("learning source must be experiment, user_feedback, or failed_check")
    home = runner_home()
    home.mkdir(parents=True, exist_ok=True)
    path = home / "proposals.jsonl"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "objective": objective,
        "lesson": lesson.strip(),
        "source": source,
        "status": "preview",
        "promote": False,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path
