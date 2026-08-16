"""Layer 4 — web research via Tavily with honest local fallbacks."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any

from figureitout.config import use_mock


def _duckduckgo_search(query: str) -> str:
    """Best-effort HTML scrape of DuckDuckGo lite results. Returns JSON string or ''."""
    q = (query or "").strip()
    if not q:
        return ""
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "figureitout-research/1.0 (+local-fallback)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

    # result__a / result__snippet patterns in DDG HTML
    links = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html,
        flags=re.I | re.S,
    )
    snippets = re.findall(
        r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)>',
        html,
        flags=re.I | re.S,
    )
    results: list[dict[str, str]] = []
    for i, (href, title) in enumerate(links[:5]):
        # unwrap ddg redirect
        if "uddg=" in href:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            href = urllib.parse.unquote(parsed.get("uddg", [href])[0])
        clean_title = re.sub(r"<[^>]+>", "", title).strip()
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()
        if href.startswith("http"):
            results.append({"url": href, "title": clean_title, "content": snippet or clean_title})
    if not results:
        return ""
    return json.dumps(results)


class _NoLiveSearchStub:
    """Honest offline stub — never invents example.com evidence."""

    name = "tavily_search_results_json"
    description = (
        "Search unavailable. NO LIVE SEARCH — worker must use shell/read_file/browse."
    )

    def invoke(self, query: str | dict[str, Any]) -> str:
        q = query if isinstance(query, str) else str(query.get("query", query))
        return (
            "NO LIVE SEARCH available (Tavily missing and local web fallback empty). "
            f"Query was: {q}. "
            "Do not treat this as evidence. Worker MUST continue with shell, read_file, "
            "and/or browse against the local codebase or known URLs."
        )

    def run(self, query: str) -> str:
        return self.invoke(query)


class _LocalWebSearch:
    """DuckDuckGo HTML fallback tool."""

    name = "local_web_search"
    description = "Local DuckDuckGo HTML web search fallback."

    def invoke(self, query: str | dict[str, Any]) -> str:
        q = query if isinstance(query, str) else str(query.get("query", query))
        hit = _duckduckgo_search(q)
        if hit:
            return hit
        return _NoLiveSearchStub().invoke(q)

    def run(self, query: str) -> str:
        return self.invoke(query)


def get_research_tools() -> list[Any]:
    """Return LangChain research tools. Falls back without inventing fake URLs."""
    if use_mock() or os.environ.get("LLM_PROVIDER", "").strip().lower() == "mock":
        # Offline/CI: never hit the network; honest no-live-search stub only.
        return [_NoLiveSearchStub()]
    if os.environ.get("TAVILY_API_KEY"):
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            return [TavilySearchResults(max_results=5)]
        except Exception:
            pass
    # Prefer local DDG fallback; honest stub if that also fails at invoke time.
    return [_LocalWebSearch()]


def run_research(query: str) -> str:
    tools = get_research_tools()
    tool = tools[0]
    try:
        if hasattr(tool, "invoke"):
            out = str(tool.invoke(query))
        else:
            out = str(tool.run(query))
    except Exception as exc:
        out = (
            "NO LIVE SEARCH available (research tool error). "
            f"Query was: {query}. Error: {exc}. "
            "Worker MUST continue with shell/read_file/browse."
        )
    # Hard ban: never return invented example.com evidence.
    if "example.com" in out.lower() and "no live search" not in out.lower():
        return (
            "NO LIVE SEARCH available. Rejected fabricated example.com evidence. "
            f"Query was: {query}. Worker MUST use shell/read_file/browse."
        )
    return out
