"""Prompt-level install — canonical brain → every IDE/CLI. Zero repo dependency."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from runforrestrun.install import (
    AGENTS_BLOCK,
    DEVIN_GLOBAL,
    DEVIN_RULE,
    RULE_MDC,
    _configure_openclaw,
    _cursor_user_dir,
    _devin_user_dir,
    _install_personal_agents,
    _merge_hooks,
    _upsert_agents,
    _write,
    write_canonical,
)
from runforrestrun.mandate import USER_RULES_TEXT
from runforrestrun.purge import purge_legacy_runners


def _cursor_user_rules_db() -> Path | None:
    home = Path.home()
    for candidate in (
        home / ".config" / "Cursor" / "User" / "globalStorage" / "state.vscdb",
        home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "state.vscdb",
    ):
        if candidate.exists():
            return candidate
    return None


def _sync_cursor_user_rules(text: str) -> str | None:
    """Best-effort local User Rules DB sync (cloud account may override)."""
    db_path = _cursor_user_rules_db()
    if not db_path:
        return None
    key = "aicontext.personalContext"
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute("SELECT value FROM ItemTable WHERE key = ?", (key,)).fetchone()
            existing = row[0] if row else ""
            if isinstance(existing, bytes):
                existing = existing.decode("utf-8", errors="replace")
            marker = "Run, Forrest, Run! — NON-NEGOTIABLE"
            if marker in existing:
                start = existing.index(marker)
                rest = existing[start:]
                nxt = rest.find("\n\n", len(marker))
                updated = existing[:start] + text.rstrip() + ("\n\n" + rest[nxt + 2 :] if nxt >= 0 else "\n")
            else:
                updated = existing.rstrip() + "\n\n" + text.rstrip() + "\n"
            conn.execute(
                "INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                (key, updated),
            )
            conn.commit()
        finally:
            conn.close()
        return str(db_path)
    except (sqlite3.Error, OSError):
        return None


def _install_cursor_plugin(skill: str) -> Path:
    """User-scoped Cursor Plugin — Always rules across every repo (prompt processing level)."""
    root = Path.home() / ".cursor" / "plugins" / "local" / "run-forrest-run"
    _write(
        root / ".cursor-plugin" / "plugin.json",
        json.dumps(
            {
                "name": "run-forrest-run",
                "description": "Run, Forrest, Run! — default objective runner for every prompt",
                "version": "0.1.0",
            },
            indent=2,
        )
        + "\n",
    )
    _write(root / "rules" / "run-forrest-run.mdc", RULE_MDC)
    _write(root / "skills" / "run-forrest-run" / "SKILL.md", skill)
    hooks = {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": f"{__import__('sys').executable} -m runforrestrun.hooks.session_start"}]
        },
    }
    _write(root / "hooks.json", json.dumps(hooks, indent=2) + "\n")
    return root


def _install_openclaw_workspace(skill: str) -> list[str]:
    """OpenClaw injects workspace AGENTS.md / SOUL.md every session — not repo-dependent."""
    home = Path.home()
    openclaw = Path(__import__("os").environ.get("OPENCLAW_HOME") or (home / ".openclaw"))
    openclaw.mkdir(parents=True, exist_ok=True)
    workspace = openclaw / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []

    soul = """# Run, Forrest, Run!

Every prompt is an objective. FIRST output lines (mandatory):

🌲 Run, Forrest, Run! — invoked.
🌲 I don't have a warrant on this yet. I'll probe it. Type anything to course-correct — the trail keeps everything.

Two-line 🌲 updates only. Never stop at a plan. Trail: ~/.run-forrest-run/runs/
"""
    for path, body in (
        (workspace / "AGENTS.md", f"# AGENTS.md\n\n{AGENTS_BLOCK}"),
        (workspace / "SOUL.md", soul),
        (openclaw / "AGENTS.md", f"# AGENTS.md\n\n{AGENTS_BLOCK}"),
        (openclaw / "skills" / "run-forrest-run" / "SKILL.md", skill),
        (workspace / "skills" / "run-forrest-run" / "SKILL.md", skill),
    ):
        _write(path, body)
        installed.append(str(path))

    _configure_openclaw(openclaw / "openclaw.json")
    installed.append(str(openclaw / "openclaw.json"))
    return installed


def _install_devin_user() -> list[str]:
    home = Path.home()
    installed: list[str] = []
    for path, body in (
        (home / ".devin" / "global_rules.md", DEVIN_GLOBAL),
        (home / ".config" / "devin" / "global_rules.md", DEVIN_GLOBAL),
        (home / ".devin" / "rules" / "run-forrest-run.md", DEVIN_RULE),
    ):
        _write(path, body)
        installed.append(str(path))
    return installed


def install_global_prompt_law(
    *,
    packaged: Path | None = None,
    sync: bool = True,
) -> dict:
    """
    Install at prompt-processing level only. No repo files. One canonical brain;
    refresh with `run-forrest-run --sync` to evolve every IDE/CLI at once.
    """
    removed = purge_legacy_runners(project_root=Path.cwd())
    canonical = write_canonical(packaged, sync=sync)
    skill = (canonical / "SKILL.md").read_text(encoding="utf-8")
    installed: list[str] = list(removed)

    # Cursor: local plugin (cross-repo Always rules) + user skill/rule/hooks fallbacks
    plugin = _install_cursor_plugin(skill)
    installed.append(str(plugin))
    home = Path.home()
    for path, body in (
        (home / ".cursor" / "skills" / "run-forrest-run" / "SKILL.md", skill),
        (home / ".cursor" / "rules" / "run-forrest-run.mdc", RULE_MDC),
        (home / ".agents" / "skills" / "run-forrest-run" / "SKILL.md", skill),
        (home / ".devin" / "skills" / "run-forrest-run" / "SKILL.md", skill),
        (home / ".claude" / "skills" / "run-forrest-run" / "SKILL.md", skill),
    ):
        _write(path, body)
        installed.append(str(path))

    _upsert_agents(home / ".agents" / "AGENTS.md")
    installed.append(str(home / ".agents" / "AGENTS.md"))

    installed.extend(_install_openclaw_workspace(skill))
    installed.extend(_install_devin_user())
    for hooks_path in (
        home / ".cursor" / "hooks.json",
        _cursor_user_dir() / "hooks.json",
        _devin_user_dir() / "hooks.json",
        home / ".devin" / "hooks.json",
    ):
        try:
            _merge_hooks(hooks_path)
            installed.append(str(hooks_path))
        except OSError:
            continue
    installed.extend(_install_personal_agents())

    user_rules_db = _sync_cursor_user_rules(USER_RULES_TEXT)
    if user_rules_db:
        installed.append(user_rules_db)

    return {
        "ok": True,
        "mode": "global-prompt-law",
        "canonical": str(canonical),
        "installed": installed,
        "cursor_plugin": str(plugin),
        "evolve": "run-forrest-run --sync",
    }
