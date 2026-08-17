"""Remove legacy figureitout / letscook runner artifacts from known host paths."""

from __future__ import annotations

import shutil
from pathlib import Path


LEGACY_SKILL_NAMES = ("figureitout", "letscook", "objective-runner")
LEGACY_RULE_NAMES = ("figureitout.mdc", "letscook-default-f26.mdc")
LEGACY_HOOK_MARKERS = ("figureitout.hooks.",)


def _rm_tree(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)
    return True


def _cursor_user_dir() -> Path:
    home = Path.home()
    for candidate in (home / ".config" / "Cursor", home / "Library" / "Application Support" / "Cursor"):
        if candidate.exists():
            return candidate
    return home / ".config" / "Cursor"


def _devin_user_dir() -> Path:
    home = Path.home()
    for candidate in (
        home / ".config" / "devin",
        home / "Library" / "Application Support" / "devin",
        home / ".devin",
    ):
        if candidate.exists():
            return candidate
    return home / ".config" / "devin"


def purge_legacy_runners(*, project_root: Path | None = None) -> list[str]:
    """Delete figureitout-era skills, rules, and stale hook commands."""
    root = (project_root or Path.cwd()).resolve()
    home = Path.home()
    removed: list[str] = []

    skill_roots = [
        root / ".cursor" / "skills",
        root / ".claude" / "skills",
        root / ".devin" / "skills",
        root / ".agents" / "skills",
        home / ".cursor" / "skills",
        home / ".claude" / "skills",
        home / ".devin" / "skills",
        home / ".agents" / "skills",
        _devin_user_dir() / "skills",
    ]
    for base in skill_roots:
        for name in LEGACY_SKILL_NAMES:
            path = base / name
            if _rm_tree(path):
                removed.append(str(path))

    rule_roots = [
        root / ".cursor" / "rules",
        home / ".cursor" / "rules",
        _cursor_user_dir() / "rules",
    ]
    for base in rule_roots:
        for name in LEGACY_RULE_NAMES:
            path = base / name
            if _rm_tree(path):
                removed.append(str(path))

    for hooks_path in (
        root / ".cursor" / "hooks.json",
        root / ".devin" / "hooks.json",
        _cursor_user_dir() / "hooks.json",
        _devin_user_dir() / "hooks.json",
    ):
        if not hooks_path.exists():
            continue
        try:
            import json

            data = json.loads(hooks_path.read_text(encoding="utf-8"))
            hooks = data.get("hooks") or {}
            changed = False
            for event, entries in list(hooks.items()):
                if not isinstance(entries, list):
                    continue
                kept = [
                    entry
                    for entry in entries
                    if not (
                        isinstance(entry, dict)
                        and any(marker in str(entry.get("command", "")) for marker in LEGACY_HOOK_MARKERS)
                    )
                ]
                if len(kept) != len(entries):
                    hooks[event] = kept
                    changed = True
            if changed:
                hooks_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                removed.append(str(hooks_path))
        except (OSError, json.JSONDecodeError):
            continue

    return removed
