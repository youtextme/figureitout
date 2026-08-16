"""Layer 4 — web research."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"

from figureitout.planner import Task
from figureitout.research_tool import get_research_tools, run_research
from figureitout.worker import execute_task


def test_research_tools_available():
    tools = get_research_tools()
    assert len(tools) >= 1


def test_stub_research_says_no_live_search_without_example_com(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setenv("FIGUREITOUT_MOCK", "1")
    out = run_research("langgraph objective runner")
    assert "no live search" in out.lower()
    assert "example.com" not in out.lower()


def test_research_prefers_local_fallback_over_fake_example(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setattr(
        "figureitout.research_tool._duckduckgo_search",
        lambda q: '[{"url": "https://duckduckgo.com/?q=x", "content": "ddg hit", "title": "ddg"}]',
    )
    out = run_research("autonomous agents")
    assert "example.com" not in out.lower()
    assert "duckduckgo.com" in out or "ddg" in out.lower()


def test_worker_research_task_continues_beyond_stub(monkeypatch):
    """Research tasks must not short-circuit solely to run_research stub."""
    monkeypatch.setenv("FIGUREITOUT_MOCK", "0")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    class _FakeMsg:
        content = "Used shell and read_file to gather codebase evidence."
        tool_calls = [
            {"name": "shell", "args": {"command": "echo researched"}},
            {"name": "read_file", "args": {"path": "README.md"}},
        ]

    class _FakeLLM:
        def bind_tools(self, _tools):
            return self

        def invoke(self, _prompt):
            return _FakeMsg()

    monkeypatch.setattr("figureitout.worker.get_llm", lambda **_k: _FakeLLM())
    monkeypatch.setattr(
        "figureitout.worker.run_research",
        lambda q: "NO LIVE SEARCH available. Worker must use shell/read_file/browse.",
    )
    invoked = []

    class _Tool:
        def __init__(self, name):
            self.name = name

        def invoke(self, args):
            invoked.append(self.name)
            return f"ok:{self.name}:{args}"

    monkeypatch.setattr(
        "figureitout.worker.get_all_tools",
        lambda _rid=None: [_Tool("shell"), _Tool("read_file"), _Tool("browse"), _Tool("web_search")],
    )

    task = Task(
        name="research_demo",
        description="Find sources on autonomous agents",
        success_criteria="Include concrete findings from tools or files",
        task_type="research",
    )
    out = execute_task(task)
    assert "no live search" in out.lower() or "shell" in out.lower()
    assert "example.com" not in out.lower()
    assert "shell" in invoked or "read_file" in invoked
