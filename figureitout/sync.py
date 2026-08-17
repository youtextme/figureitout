"""Cursor / Devin / OpenClaw fleet sync — same skill, same mandate, same connections."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from figureitout.mandate import FIGUREITOUT_AGENTS_BLOCK, FIGUREITOUT_AGENTS_MARKER

FLEET_SURFACES = ("cursor", "devin", "openclaw", "claude")

_REPO = Path(__file__).resolve().parents[1]
_PUBLIC_SKILL = Path(__file__).resolve().parent / "public" / "SKILL.md"
_PACKAGE_SKILL = Path(__file__).resolve().parent / "SKILL.md"
_COMPUTER_USE_SKILL = Path(__file__).resolve().parent / "public" / "computer-use.SKILL.md"


def _canonical_skill() -> str:
    for path in (_PUBLIC_SKILL, _PACKAGE_SKILL, _REPO / "SKILL.md"):
        if path.exists():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError("figureitout SKILL.md missing")


def _computer_use_skill() -> str:
    if _COMPUTER_USE_SKILL.exists():
        return _COMPUTER_USE_SKILL.read_text(encoding="utf-8")
    return """---
name: computer-use
description: >-
  Use desktop or browser GUI only when the job is the UI, or APIs cannot finish it.
---

# computer-use

Prefer command line and APIs. Reach for computer use only when it is effective
and necessary:

- Native apps with no usable API (Telegram Desktop, wallpaper, OS settings)
- A logged-in browser session that is the work (Gmail in Chrome)

Do not use computer use for git, files, tests, or provider config.
If the GUI session is missing, say **blocked** with evidence. Do not invent data.
"""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _upsert_agents(path: Path) -> None:
    from figureitout.install import ensure_agents_figureitout_block

    ensure_agents_figureitout_block(path)


def _openclaw_tools() -> str:
    return """# TOOLS

Prefer command line and APIs. Use computer use only when it is effective and necessary.

| Job | Surface |
|-----|---------|
| Files, tests, git, kilocode config | files / CLI |
| Gmail, Coupang mail, logged-in web | browser (user Chrome profile) |
| Telegram Desktop, wallpaper, OS settings | desktop |

If Telegram Desktop or a logged-in Gmail session is missing, stop and report **blocked**.
Never invent spend totals, messages sent, or screenshots you do not have.
"""


def _openclaw_agents() -> str:
    return "# AGENTS.md\n\n" + FIGUREITOUT_AGENTS_BLOCK.rstrip() + "\n"


def skill_destinations(workspace: Path, home: Path) -> dict[str, list[Path]]:
    """Where each fleet surface stores figureitout SKILL.md."""
    return {
        "cursor": [
            workspace / ".cursor" / "skills" / "figureitout" / "SKILL.md",
            home / ".cursor" / "skills" / "figureitout" / "SKILL.md",
        ],
        "devin": [
            workspace / ".devin" / "skills" / "figureitout" / "SKILL.md",
            home / ".config" / "devin" / "skills" / "figureitout" / "SKILL.md",
        ],
        "openclaw": [
            workspace / ".openclaw" / "skills" / "figureitout" / "SKILL.md",
            workspace / ".agents" / "skills" / "figureitout" / "SKILL.md",
            home / ".openclaw" / "skills" / "figureitout" / "SKILL.md",
            home / ".agents" / "skills" / "figureitout" / "SKILL.md",
        ],
        "claude": [
            workspace / ".claude" / "skills" / "figureitout" / "SKILL.md",
        ],
    }


def computer_use_destinations(workspace: Path, home: Path) -> dict[str, list[Path]]:
    return {
        "cursor": [
            workspace / ".cursor" / "skills" / "computer-use" / "SKILL.md",
            home / ".cursor" / "skills" / "computer-use" / "SKILL.md",
        ],
        "devin": [
            workspace / ".devin" / "skills" / "computer-use" / "SKILL.md",
            home / ".config" / "devin" / "skills" / "computer-use" / "SKILL.md",
        ],
        "openclaw": [
            workspace / ".openclaw" / "skills" / "computer-use" / "SKILL.md",
            home / ".openclaw" / "skills" / "computer-use" / "SKILL.md",
        ],
        "claude": [
            workspace / ".claude" / "skills" / "computer-use" / "SKILL.md",
        ],
    }


def skill_hashes(workspace: Path | None = None, home: Path | None = None) -> dict[str, str]:
    root = (workspace or _REPO).resolve()
    home_dir = (home or Path.home()).resolve()
    canonical = _sha(_canonical_skill())
    out: dict[str, str] = {"canonical": canonical}
    for surface, paths in skill_destinations(root, home_dir).items():
        found = [p for p in paths if p.exists()]
        if not found:
            out[surface] = ""
            continue
        # First existing path represents the surface.
        out[surface] = _sha(found[0].read_text(encoding="utf-8"))
    return out


def sync_status(workspace: Path | None = None, home: Path | None = None) -> dict[str, Any]:
    root = (workspace or _REPO).resolve()
    home_dir = (home or Path.home()).resolve()
    hashes = skill_hashes(workspace=root, home=home_dir)
    canonical = hashes.get("canonical", "")
    drift: list[str] = []
    missing: list[str] = []
    for surface in FLEET_SURFACES:
        digest = hashes.get(surface, "")
        if not digest:
            missing.append(surface)
        elif digest != canonical:
            drift.append(surface)
    in_sync = not drift and not missing
    return {
        "in_sync": in_sync,
        "hashes": hashes,
        "drift": drift,
        "missing": missing,
        "surfaces": list(FLEET_SURFACES),
        "marker": FIGUREITOUT_AGENTS_MARKER,
    }


def sync_agents(workspace: Path | None = None, home: Path | None = None) -> dict[str, Any]:
    """Copy the canonical skill + computer-use skill to Cursor, Devin, and OpenClaw."""
    root = (workspace or _REPO).resolve()
    home_dir = (home or Path.home()).resolve()
    skill = _canonical_skill()
    cu = _computer_use_skill()
    written: list[str] = []

    for paths in skill_destinations(root, home_dir).values():
        for dest in paths:
            _write(dest, skill)
            prompt_src = _REPO / "PROMPT.md"
            if not prompt_src.exists():
                prompt_src = Path(__file__).resolve().parent / "public" / "PROMPT.md"
            if prompt_src.exists():
                _write(dest.parent / "PROMPT.md", prompt_src.read_text(encoding="utf-8"))
            written.append(str(dest))

    for paths in computer_use_destinations(root, home_dir).values():
        for dest in paths:
            _write(dest, cu)
            written.append(str(dest))

    _upsert_agents(root / "AGENTS.md")
    _write(root / ".openclaw" / "AGENTS.md", _openclaw_agents())
    _write(root / ".openclaw" / "TOOLS.md", _openclaw_tools())
    _upsert_agents(root / ".devin" / "AGENTS.md")
    workspace_openclaw = home_dir / ".openclaw" / "workspace" / "AGENTS.md"
    _upsert_agents(workspace_openclaw)
    _write(home_dir / ".openclaw" / "workspace" / "TOOLS.md", _openclaw_tools())

    connections_path = root / ".figureitout" / "connections.json"
    from figureitout.connections import dump_connections

    _write(connections_path, json.dumps(dump_connections(), indent=2) + "\n")
    written.append(str(connections_path))

    kilo: dict[str, Any] = {}
    try:
        from figureitout.kilocode import configure_kilocode

        kilo = configure_kilocode(workspace=root, home=home_dir)
        written.extend(kilo.get("written") or [])
    except Exception as exc:
        kilo = {"ok": False, "error": str(exc)}

    status = sync_status(workspace=root, home=home_dir)
    return {
        "ok": bool(status["in_sync"]) and bool(kilo.get("ok", True)),
        "in_sync": status["in_sync"],
        "written": written,
        "status": status,
        "kilocode": {k: v for k, v in kilo.items() if k != "written"} if kilo else {},
    }
