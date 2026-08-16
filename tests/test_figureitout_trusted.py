"""Trusted full-access mode — computer, tools, vision, policy bypass."""

from __future__ import annotations

from pathlib import Path

import pytest
import uuid

from figureitout.computer import SandboxedComputer
from figureitout.config import is_trusted
from figureitout.planner import Task
from figureitout.policy import check_policy
from figureitout.tools import get_all_tools, think
from figureitout.vision import analyze_image
from figureitout.worker import execute_task


@pytest.fixture(autouse=True)
def _force_trusted(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_TRUSTED", "1")
    monkeypatch.setenv("FIGUREITOUT_MOCK", "1")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("FIGUREITOUT_LOCKDOWN", raising=False)


def test_trusted_default_on():
    assert is_trusted() is True


def test_trusted_policy_allows_shell():
    assert check_policy("research", "shell", {}) is True
    assert check_policy("trusted", "network", {"host": "example.com"}) is True


def test_trusted_write_outside_run_dir(tmp_path: Path):
    comp = SandboxedComputer(run_id=f"t-{uuid.uuid4().hex[:8]}", objective_type="trusted")
    assert comp.trusted is True
    target = tmp_path / "outside.txt"
    path = comp.write_file(str(target), "trusted-ok")
    assert path.read_text(encoding="utf-8") == "trusted-ok"


def test_tools_include_vision_and_think():
    tools = get_all_tools()
    names = {getattr(t, "name", "") for t in tools}
    assert "web_search" in names
    assert "shell" in names
    assert "vision" in names
    assert "deep_think" in names


def test_vision_mock(tmp_path: Path):
    img = tmp_path / "x.png"
    img.write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
            "de0000000c4944415408d763f8ffff3f0005fe02fea57550a00000000049454e44ae426082"
        )
    )
    out = analyze_image(str(img), "what is this?")
    assert len(out) > 0


def test_think_mock():
    assert "think" in think("how to ship figureitout").lower()


def test_worker_llm_failure_is_not_canned_success(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    class _BoomLLM:
        def bind_tools(self, _tools):
            return self

        def invoke(self, _prompt):
            raise RuntimeError("Error code: 500 — Max retries exceeded")

    monkeypatch.setattr("figureitout.worker.get_llm", lambda **_k: _BoomLLM())
    monkeypatch.setattr("figureitout.worker.get_all_tools", lambda _rid=None: [])

    task = Task(
        name="implement",
        description="Implement feature",
        success_criteria="Working artifact exists",
        task_type="code",
    )
    out = execute_task(task)
    lower = out.lower()
    assert "failed" in lower or "degraded" in lower
    assert "completed task" not in lower
    assert "do not treat as completed" in lower
    assert "worker fallback" not in lower


def test_worker_error_content_is_fail_closed(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    class _Msg:
        def __init__(self, content):
            self.content = content
            self.tool_calls = []

    class _BadLLM:
        def bind_tools(self, _tools):
            return self

        def invoke(self, _prompt):
            return _Msg(
                "Worker fallback for document after Error code: 500. "
                "Max retries exceeded with url."
            )

    monkeypatch.setattr("figureitout.worker.get_llm", lambda **_k: _BadLLM())
    monkeypatch.setattr("figureitout.worker.get_all_tools", lambda _rid=None: [])

    task = Task(
        name="document",
        description="Write research document",
        success_criteria="Document with sources",
        task_type="write",
    )
    out = execute_task(task)
    lower = out.lower()
    assert "failed/degraded" in lower
    assert "do not treat as completed" in lower
    assert "completed task" not in lower


def test_worker_multi_turn_tool_loop(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    turns = {"n": 0}

    class _Msg:
        def __init__(self, content, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls or []

    class _LoopLLM:
        def bind_tools(self, _tools):
            return self

        def invoke(self, _prompt):
            turns["n"] += 1
            if turns["n"] == 1:
                return _Msg(
                    "Need to inspect files",
                    tool_calls=[{"name": "read_file", "args": {"path": "README.md"}}],
                )
            if turns["n"] == 2:
                return _Msg(
                    "Need shell check",
                    tool_calls=[{"name": "shell", "args": {"command": "echo ok"}}],
                )
            return _Msg(
                "Done criteria met: README.md inspected and shell verified. "
                "Artifact evidence recorded."
            )

    class _Tool:
        def __init__(self, name):
            self.name = name

        def invoke(self, args):
            return f"{self.name}-ok:{args}"

    monkeypatch.setattr("figureitout.worker.get_llm", lambda **_k: _LoopLLM())
    monkeypatch.setattr(
        "figureitout.worker.get_all_tools",
        lambda _rid=None: [_Tool("read_file"), _Tool("shell"), _Tool("web_search")],
    )
    monkeypatch.setattr("figureitout.worker.MAX_WORKER_TURNS", 8)

    task = Task(
        name="implement",
        description="Implement with tools",
        success_criteria="Artifact evidence recorded",
        task_type="code",
    )
    out = execute_task(task)
    assert turns["n"] >= 3
    assert "read_file" in out
    assert "shell" in out
    assert "artifact evidence" in out.lower()
