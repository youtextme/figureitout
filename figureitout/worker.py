"""Worker node — executes the current task with memory + multi-turn tools."""

from __future__ import annotations

import uuid
from typing import Any

from figureitout.config import is_trusted, llm_provider, use_mock
from figureitout.fail_closed import is_error_fallback_output
from figureitout.llm import get_llm
from figureitout.memory import get_similar_past_tasks
from figureitout.planner import Task
from figureitout.research_tool import run_research
from figureitout.tools import get_all_tools, think

MAX_WORKER_TURNS = 8


def _task_from_state(current_task: dict[str, Any] | Task) -> Task:
    if isinstance(current_task, Task):
        return current_task
    return Task.model_validate(current_task)


def _research_insufficient(findings: str) -> bool:
    text = (findings or "").lower()
    if "no live search" in text:
        return True
    if "example.com" in text:
        return True
    if len(text.strip()) < 40:
        return True
    return False


def _looks_done(content: str, criteria: str) -> bool:
    text = (content or "").strip().lower()
    if not text:
        return False
    # Fail-closed: never treat API/worker error text as done.
    if is_error_fallback_output(content):
        return False
    if any(m in text for m in ("failed", "degraded", "error:", "tool error")):
        return False
    crit = (criteria or "").lower()
    tokens = [tok for tok in crit.split() if len(tok) > 4][:6]
    if tokens and sum(1 for tok in tokens if tok in text) >= max(1, len(tokens) // 2):
        return True
    evidence_markers = (
        "file",
        "test",
        "pytest",
        "wrote",
        "created",
        "verified",
        "artifact",
        "readme",
        ".py",
        "passed",
    )
    if sum(1 for m in evidence_markers if m in text) >= 2 and len(text) > 80:
        return True
    return False


def _run_tool_calls(tool_calls: list[Any], name_map: dict[str, Any]) -> list[str]:
    chunks: list[str] = []
    for call in tool_calls[:8]:
        name = call.get("name") if isinstance(call, dict) else getattr(call, "name", "")
        args = call.get("args") if isinstance(call, dict) else getattr(call, "args", {})
        tool = name_map.get(name)
        if not tool:
            chunks.append(f"[{name}] unknown tool")
            continue
        try:
            out = tool.invoke(args)
        except Exception as exc:  # noqa: BLE001
            out = f"tool error: {exc}"
        chunks.append(f"[{name}] {out}")
    return chunks


def _multi_turn_loop(
    *,
    llm: Any,
    tools: list[Any],
    base_prompt: str,
    success_criteria: str,
    max_turns: int = MAX_WORKER_TURNS,
) -> str:
    name_map = {getattr(t, "name", ""): t for t in tools}
    transcript: list[str] = []
    prompt = base_prompt
    bound = llm.bind_tools(tools) if hasattr(llm, "bind_tools") else llm

    for turn in range(max_turns):
        result = bound.invoke(prompt)
        content = getattr(result, "content", "") or str(result)
        if isinstance(content, list):
            content = "".join(str(part) for part in content)
        content_s = str(content).strip()
        tool_calls = getattr(result, "tool_calls", None) or []
        if tool_calls:
            chunks = _run_tool_calls(list(tool_calls), name_map)
            block = "\n".join([content_s] + chunks if content_s else chunks)
            transcript.append(block)
            if _looks_done(block, success_criteria) and turn + 1 >= 2:
                break
            prompt = (
                f"{base_prompt}\n\n--- Tool transcript so far ---\n"
                + "\n".join(transcript)
                + "\n\nContinue until success criteria are met. "
                "Call more tools if needed, else return the final deliverable with evidence."
            )
            continue
        if content_s:
            transcript.append(content_s)
        if _looks_done(content_s, success_criteria) or not tool_calls:
            break
    return "\n".join(transcript) if transcript else "FAILED: empty worker output"


def execute_task(
    task: Task | dict[str, Any],
    prior_outputs: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> str:
    """Run one task. Trusted mode binds research/shell/files/browse/vision/think."""
    t = _task_from_state(task)
    past = get_similar_past_tasks(t)
    context_block = f"Past experience:\n{past[:1500]}" if past else "Past experience:\n(none)"
    prior = prior_outputs or {}
    rid = run_id or uuid.uuid4().hex[:10]

    # Explicit mock path for deterministic CI — not used for local/real providers.
    if use_mock() or llm_provider() == "mock":
        if t.task_type == "research":
            research = run_research(t.description)
            return (
                f"Research results for '{t.name}':\n{research}\n"
                f"Prior outputs keys: {list(prior.keys())}"
            )
        if t.task_type == "analyse" and is_trusted():
            return think(f"Task: {t.description}\nCriteria: {t.success_criteria}\nPrior: {prior}")
        if "hello" in (t.description + t.name + t.success_criteria).lower():
            return (
                "```python\nprint('Hello, World!')\n```\n"
                "Deliverable: hello world program written and verified."
            )
        return (
            f"Completed task '{t.name}' ({t.task_type}): {t.description}. "
            f"Success criteria addressed: {t.success_criteria}."
        )

    # Real / local path — research may seed, but never short-circuit solely on stub.
    research_seed = ""
    if t.task_type == "research":
        research_seed = run_research(t.description)

    if t.task_type == "analyse" and is_trusted():
        # Still allow tool loop after think when criteria demand evidence.
        thought = think(f"Task: {t.description}\nCriteria: {t.success_criteria}\nPrior: {prior}")
        research_seed = (research_seed + "\n" + thought).strip()

    llm = get_llm(temperature=0.3)
    tools = get_all_tools(rid)
    prompt = (
        f"{context_block}\n\n"
        f"Task: {t.name}\nType: {t.task_type}\nDescription: {t.description}\n"
        f"Success criteria: {t.success_criteria}\n"
        f"Prior outputs: {prior}\n"
        f"Trusted full-access: {is_trusted()}\n"
    )
    if research_seed:
        prompt += (
            f"\nInitial research findings:\n{research_seed}\n"
            "If findings say NO LIVE SEARCH or are insufficient, you MUST use "
            "shell, read_file, and/or browse next — do not stop.\n"
        )
    prompt += (
        "You have tools: web_search, shell, read_file, write_file, browse, vision, deep_think. "
        "Use a ReAct-style loop: reason → tool → observe → repeat until done criteria. "
        "Produce concrete evidence (paths, test names, command output). "
        "Never invent example.com or claim success without artifacts. "
        "Do not repeat the Past experience block in your answer."
    )

    # If research stub is insufficient, force at least one tool-using turn.
    force_tools = t.task_type == "research" and _research_insufficient(research_seed)

    try:
        out = _multi_turn_loop(
            llm=llm,
            tools=tools,
            base_prompt=prompt,
            success_criteria=t.success_criteria,
            max_turns=MAX_WORKER_TURNS,
        )
        # Fail-closed: API-error text in model content must never look like success.
        if is_error_fallback_output(out):
            return (
                f"FAILED/DEGRADED worker for '{t.name}' ({t.task_type}): "
                f"error fallback in worker output. Do not treat as completed.\n{out}"
            )
        if force_tools and research_seed and "no live search" in research_seed.lower():
            # Ensure stub text is visible and tools were attempted.
            if "[" not in out and "tool" not in out.lower():
                return (
                    f"DEGRADED: research findings insufficient and no tools executed.\n"
                    f"{research_seed}\n{out}"
                )
            combined = f"Research results for '{t.name}':\n{research_seed}\n\nFollow-up tools:\n{out}"
            if is_error_fallback_output(combined) and not use_mock():
                return (
                    f"FAILED/DEGRADED worker for '{t.name}' ({t.task_type}): "
                    f"research/tool output is error fallback. Do not treat as completed.\n"
                    f"{combined}"
                )
            return combined
        if research_seed and t.task_type == "research":
            combined = f"Research results for '{t.name}':\n{research_seed}\n\nFollow-up:\n{out}"
            if is_error_fallback_output(combined) and not use_mock():
                return (
                    f"FAILED/DEGRADED worker for '{t.name}' ({t.task_type}): "
                    f"research output is error fallback. Do not treat as completed.\n"
                    f"{combined}"
                )
            return combined
        return out
    except Exception as exc:  # noqa: BLE001 — fail closed, never canned success
        return (
            f"FAILED/DEGRADED worker for '{t.name}' ({t.task_type}): "
            f"LLM or tool loop error: {exc}. "
            "Do not treat as completed."
        )
