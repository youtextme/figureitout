"""Shared connection registry for Cursor, Devin, and OpenClaw."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from figureitout.computer import desktop_status
from figureitout.kilocode import KILOCODE_BASE_URL, KILOCODE_FREE_MODEL, kilocode_api_key


CONNECTION_IDS = (
    "cursor",
    "devin",
    "openclaw",
    "kilocode",
    "telegram",
    "gmail",
    "computer_use",
    "wallpaper",
)


def list_connections() -> tuple[str, ...]:
    return CONNECTION_IDS


def dump_connections() -> dict[str, Any]:
    """Canonical connection map written to .figureitout/connections.json (no secrets)."""
    return {
        "fleet": ["cursor", "devin", "openclaw"],
        "llm": {
            "default": "kilocode",
            "model": KILOCODE_FREE_MODEL,
            "baseUrl": KILOCODE_BASE_URL,
            "fallbacks": ["local", "openai", "anthropic"],
            "apiKeyEnv": ["KILOCODE_API_KEY", "KILO_API_KEY", "KILOCODE_KEY"],
        },
        "computer_use": {
            "when": "native apps or logged-in browser UI; never for files/git/tests",
            "telegram": {"app": "Telegram Desktop", "channel": "Omimoh"},
            "gmail": {"browser": "chrome", "profile": "user"},
            "wallpaper": {"target": "desktop background", "subject": "BotFather", "resolution": "3840x2160"},
        },
    }


def connection_status(workspace: Path | None = None, home: Path | None = None) -> dict[str, Any]:
    root = (workspace or Path.cwd()).resolve()
    home_dir = (home or Path.home()).resolve()
    desk = desktop_status()
    key = kilocode_api_key()
    return {
        "cursor": {
            "ready": (root / ".cursor" / "skills" / "figureitout" / "SKILL.md").exists(),
            "path": str(root / ".cursor" / "skills" / "figureitout" / "SKILL.md"),
        },
        "devin": {
            "ready": (root / ".devin" / "skills" / "figureitout" / "SKILL.md").exists(),
            "path": str(root / ".devin" / "skills" / "figureitout" / "SKILL.md"),
        },
        "openclaw": {
            "ready": (root / ".openclaw" / "skills" / "figureitout" / "SKILL.md").exists(),
            "path": str(root / ".openclaw" / "skills" / "figureitout" / "SKILL.md"),
        },
        "kilocode": {
            "ready": True,  # anonymous free models work without a key
            "key_present": bool(key),
            "default_model": KILOCODE_FREE_MODEL,
            "base_url": KILOCODE_BASE_URL,
        },
        "telegram": {
            "ready": bool(desk.get("telegram")),
            "binary": desk.get("telegram"),
            "needed": "logged-in Telegram Desktop session",
        },
        "gmail": {
            "ready": bool(desk.get("chrome")),
            "binary": desk.get("chrome"),
            "needed": "logged-in Chrome Gmail session",
        },
        "computer_use": {
            "ready": bool(desk.get("available")),
            "display": desk.get("display"),
            "when": "effective and necessary — GUI jobs only",
        },
        "wallpaper": {
            "ready": bool(desk.get("wallpaper_tool") or desk.get("available")),
            "tool": desk.get("wallpaper_tool"),
        },
        "home": str(home_dir),
        "which": {
            "chrome": shutil.which("google-chrome") or shutil.which("google-chrome-stable"),
            "telegram": shutil.which("telegram-desktop") or shutil.which("telegram"),
        },
    }
