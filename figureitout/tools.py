"""Unified tool surface — research, shell, files, browse, vision, think."""

from __future__ import annotations

import uuid
from typing import Any, Callable

from figureitout.computer import SandboxedComputer
from figureitout.config import is_trusted, thinking_model, use_mock
from figureitout.llm import get_llm
from figureitout.research_tool import run_research
from figureitout.vision import analyze_image


def _computer(run_id: str | None = None) -> SandboxedComputer:
    return SandboxedComputer(
        run_id=run_id or uuid.uuid4().hex[:10],
        objective_type="trusted" if is_trusted() else "build",
    )


def think(prompt: str) -> str:
    """Deep thinking pass — uses thinking model when available."""
    if use_mock():
        return f"[think] {prompt[:200]}"
    from langchain_core.messages import HumanMessage
    from figureitout.config import llm_provider
    import os

    # Prefer thinking model via env override on local provider.
    prev = os.environ.get("FIGUREITOUT_LOCAL_MODEL")
    try:
        if llm_provider() in {"local", "tireless", "ollama"}:
            os.environ["FIGUREITOUT_LOCAL_MODEL"] = thinking_model()
        llm = get_llm(temperature=0.2)
        result = llm.invoke([
            HumanMessage(
                content=(
                    "Think carefully step by step. Return a concise actionable conclusion.\n\n"
                    f"{prompt}"
                )
            )
        ])
        content = getattr(result, "content", "") or str(result)
        if isinstance(content, list):
            content = "".join(str(p) for p in content)
        return str(content)
    except Exception as exc:
        return f"[think-fallback] {prompt[:300]} ({exc})"
    finally:
        if prev is None:
            os.environ.pop("FIGUREITOUT_LOCAL_MODEL", None)
        else:
            os.environ["FIGUREITOUT_LOCAL_MODEL"] = prev


def get_all_tools(run_id: str | None = None) -> list[Any]:
    """Return LangChain StructuredTools for the worker (trusted = full set)."""
    try:
        from langchain_core.tools import tool
    except Exception:
        return _callable_tool_wrappers(run_id)

    comp = _computer(run_id)

    @tool
    def web_search(query: str) -> str:
        """Search the web for grounded information."""
        return run_research(query)

    @tool
    def shell(command: str) -> str:
        """Run a shell command on this machine (trusted) or in the run sandbox."""
        return comp.run_shell(command)

    @tool
    def read_file(path: str) -> str:
        """Read a file from disk."""
        return comp.read_file(path)

    @tool
    def write_file(path: str, content: str) -> str:
        """Write a file to disk."""
        return str(comp.write_file(path, content))

    @tool
    def browse(url: str) -> str:
        """Open a URL in a headless browser and return page HTML."""
        html = comp.browse(url)
        return html[:50000]

    @tool
    def vision(path: str, question: str = "Describe this image.") -> str:
        """Analyze an image with a vision model."""
        return analyze_image(path, question)

    @tool
    def deep_think(prompt: str) -> str:
        """Reason carefully about a hard sub-problem."""
        return think(prompt)

    @tool
    def computer_use(action: str, target: str = "") -> str:
        """Desktop/GUI last resort. Use only when the job is a native app or logged-in browser."""
        from figureitout.computer import computer_use as _cu

        return str(_cu(action, target))

    tools = [web_search, shell, read_file, write_file, browse, vision, deep_think, computer_use]
    if not is_trusted():
        # Sandbox: drop unrestricted browse/shell still available but policy-gated.
        pass
    return tools


def _callable_tool_wrappers(run_id: str | None) -> list[Any]:
    from figureitout.computer import computer_use as cu

    comp = _computer(run_id)
    return [
        _Fn("web_search", run_research),
        _Fn("shell", comp.run_shell),
        _Fn("read_file", comp.read_file),
        _Fn("write_file", lambda path, content="": str(comp.write_file(path, content))),
        _Fn("browse", comp.browse),
        _Fn("vision", analyze_image),
        _Fn("deep_think", think),
        _Fn("computer_use", lambda action, target="": str(cu(action, target))),
    ]


class _Fn:
    def __init__(self, name: str, fn: Callable[..., str]):
        self.name = name
        self._fn = fn

    def invoke(self, *args: Any, **kwargs: Any) -> str:
        return str(self._fn(*args, **kwargs))

    def run(self, *args: Any, **kwargs: Any) -> str:
        return self.invoke(*args, **kwargs)


def run_tool(name: str, **kwargs: Any) -> str:
    """Dispatch a named tool for non-LangChain callers."""
    rid = kwargs.pop("run_id", None)
    tools = {getattr(t, "name", str(t)): t for t in get_all_tools(rid)}
    tool = tools.get(name)
    if tool is None:
        raise KeyError(f"unknown tool: {name}")
    if hasattr(tool, "invoke"):
        # StructuredTool wants a single input dict sometimes
        try:
            return str(tool.invoke(kwargs if len(kwargs) != 1 else next(iter(kwargs.values()))))
        except Exception:
            return str(tool.invoke(kwargs))
    return str(tool.run(**kwargs))
