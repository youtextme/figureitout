"""HOW_TO_BUILD.md — from scratch + default install on every host."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUBLIC = REPO / "figureitout" / "public"
DOC = PUBLIC / "HOW_TO_BUILD.md"


def test_how_to_build_section_exists():
    text = DOC.read_text(encoding="utf-8")
    assert text.startswith("# How to build")
    assert "## 4. Build from scratch" in text
    assert "## 5. Install as the default objective runner" in text


def test_how_to_build_names_hosts_and_community_loops():
    text = DOC.read_text(encoding="utf-8")
    lower = text.lower()
    for needle in (
        "cursor",
        "devin",
        "claude",
        "openclaw",
        "cli",
        "agents.md",
        "alwaysapply",
        "langgraph",
        "crewai",
        "autogen",
        "laboratory",
        "planner",
        "worker",
        "evaluator",
        "bar_raiser",
        "python -m figureitout --install",
        "~/.agents/skills",
        "~/.openclaw/workspace",
        "from scratch",
        "default",
    ):
        assert needle in lower, needle


def test_how_to_build_does_not_start_as_tenets():
    head = "\n".join(DOC.read_text(encoding="utf-8").splitlines()[:8]).lower()
    assert "how to build" in head
    assert "methods" in head


def test_readme_has_how_to_build_section():
    readme = (PUBLIC / "README.md").read_text(encoding="utf-8")
    assert "## How to build" in readme
    assert "HOW_TO_BUILD.md" in readme


def test_run_forest_how_to_build_comes_after_tenets():
    forest = (PUBLIC / "RUN_FOREST.md").read_text(encoding="utf-8")
    assert forest.find("Three tenets") < forest.find("## 10. How to build")
    assert "HOW_TO_BUILD.md" in forest
    assert "OpenClaw" in forest
    assert "langchain-ai/langgraph" in forest


def test_install_writes_openclaw_and_agent_skills(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    openclaw = tmp_path / "openclaw"
    openclaw.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("OPENCLAW_HOME", str(openclaw))
    from figureitout.install import install_openclaw_and_agent_skills

    result = install_openclaw_and_agent_skills(project_root=tmp_path)
    assert result["ok"] is True
    skill = tmp_path / ".agents" / "skills" / "figureitout" / "SKILL.md"
    assert skill.exists()
    assert "alwaysApply: true" in skill.read_text(encoding="utf-8")
    assert (tmp_path / ".agents" / "skills" / "figureitout" / "HOW_TO_BUILD.md").exists()
    assert (openclaw / "workspace" / "skills" / "figureitout" / "SKILL.md").exists()
    agents = (openclaw / "workspace" / "AGENTS.md").read_text(encoding="utf-8")
    assert "figureitout" in agents.lower()
    assert (home / ".agents" / "skills" / "figureitout" / "SKILL.md").exists()
