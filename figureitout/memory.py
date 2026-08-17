"""Memory that is not chat — four stores.

Working: checkpoint (see checkpoint.py).
Episodic: what happened in a run.
Semantic: warranted atoms (see truth.py TruthStore).
Procedural: the runner itself — never mutated mid-flight.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from figureitout.config import MEMORY_USER_ID, runner_home, use_mock
from figureitout.planner import Task

_memory: Any | None = None
_memory_failed = False


def _get_memory() -> Any | None:
    global _memory, _memory_failed
    if use_mock() or _memory_failed:
        return None
    if _memory is not None:
        return _memory
    try:
        from mem0 import Memory

        _memory = Memory()
        return _memory
    except Exception:
        _memory_failed = True
        return None


def _fallback_add(content: str) -> None:
    home = runner_home()
    home.mkdir(parents=True, exist_ok=True)
    path = home / "memory_fallback.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"content": content[:2000]}) + "\n")


def _fallback_search(query: str, limit: int = 3) -> str:
    path = runner_home() / "memory_fallback.jsonl"
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()[-200:]
    hits: list[str] = []
    tokens = [tok for tok in query.lower().split() if len(tok) > 3]
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = str(payload.get("content", ""))[:800]
        if tokens and any(tok in content.lower() for tok in tokens):
            hits.append(content)
        if len(hits) >= limit:
            break
    return "\n".join(hits)


def save_task_result(task: Task, output: str, score: float, failure_reason: str) -> None:
    clipped = (output or "")[:1200]
    content = (
        f"Task: {task.description} | Output: {clipped} | Score: {score} | Failure: {failure_reason}"
    )
    mem = _get_memory()
    if mem is None:
        _fallback_add(content)
        return
    try:
        mem.add(
            [{"role": "assistant", "content": content}],
            user_id=MEMORY_USER_ID,
        )
    except Exception:
        _fallback_add(content)


def get_similar_past_tasks(task: Task) -> str:
    mem = _get_memory()
    if mem is None:
        return _fallback_search(task.description, limit=3)
    try:
        results = mem.search(task.description, user_id=MEMORY_USER_ID, limit=3)
        if isinstance(results, dict):
            items = results.get("results") or results.get("memories") or []
        else:
            items = results or []
        parts: list[str] = []
        for item in items:
            if isinstance(item, dict):
                parts.append(str(item.get("memory") or item.get("content") or item)[:800])
            else:
                parts.append(str(item)[:800])
        return "\n".join(parts)
    except Exception:
        return _fallback_search(task.description, limit=3)


def episodic_path() -> Path:
    return runner_home() / "episodic.jsonl"


def append_episode(run_id: str, event: str, pointers: list[str] | None = None) -> Path:
    """Episodic memory: what happened, with pointers. Not a generalization."""
    path = episodic_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "event": event[:2000],
        "pointers": list(pointers or []),
        "store": "episodic",
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path


def memory_layout() -> dict[str, str]:
    """The four stores. Procedural is the installed runner — never a jsonl mid-run."""
    home = runner_home()
    return {
        "working": "checkpoint.json in the job folder",
        "episodic": str(home / "episodic.jsonl"),
        "semantic": str(home / "semantic_truth.jsonl"),
        "procedural": "runner source; preview-only proposals.jsonl",
    }
