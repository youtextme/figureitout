"""KiloCode Gateway — free daily credits first, then other models."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

KILOCODE_BASE_URL = os.environ.get(
    "FIGUREITOUT_KILOCODE_BASE_URL",
    "https://api.kilo.ai/api/gateway",
)
KILOCODE_FREE_MODEL = os.environ.get("FIGUREITOUT_KILOCODE_MODEL", "kilo-auto/free")
KILOCODE_KEY_ENVS = ("KILOCODE_API_KEY", "KILO_API_KEY", "KILOCODE_KEY")
DEFAULT_CHAIN = ("kilocode", "local", "openai", "anthropic")


def kilocode_api_key() -> str | None:
    for name in KILOCODE_KEY_ENVS:
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return None


def kilocode_model() -> str:
    return os.environ.get("FIGUREITOUT_KILOCODE_MODEL", KILOCODE_FREE_MODEL)


def provider_chain() -> list[str]:
    """Default: kilocode free credits, then local / openai / anthropic.

    An explicit LLM_PROVIDER is tried first (except mock, which is exclusive).
    FIGUREITOUT_FALLBACK_PROVIDERS may override the tail of the chain.
    """
    explicit = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if explicit == "mock":
        return ["mock"]
    tail_raw = os.environ.get("FIGUREITOUT_FALLBACK_PROVIDERS", "")
    tail = [p.strip().lower() for p in tail_raw.split(",") if p.strip()] or list(DEFAULT_CHAIN)
    chain: list[str] = []
    if explicit and explicit not in {"", "kilocode"}:
        chain.append(explicit)
    for item in tail:
        if item not in chain:
            chain.append(item)
    if "kilocode" not in chain:
        chain.insert(0, "kilocode")
    elif chain[0] != "kilocode" and not explicit:
        chain = ["kilocode"] + [p for p in chain if p != "kilocode"]
    # Default install: kilocode first.
    if not explicit:
        rest = [p for p in chain if p != "kilocode"]
        chain = ["kilocode"] + rest
    return chain


def _config_payload(*, key_present: bool) -> dict[str, Any]:
    return {
        "provider": "kilocode",
        "baseUrl": KILOCODE_BASE_URL,
        "defaultModel": kilocode_model(),
        "fallbacks": [p for p in provider_chain() if p != "kilocode"],
        "fallbackModels": ["kilo-auto/small", "openrouter/free"],
        "apiKeyEnv": list(KILOCODE_KEY_ENVS),
        "keyPresent": key_present,
        "anonymousFreeOk": True,
        "notes": (
            "Use kilo-auto/free daily credits first. On 402/429 or missing capability, "
            "fall through fallbacks. Never print the API key."
        ),
    }


def _merge_json(path: Path, update: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            data = {}
    data.update(update)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _openclaw_models_patch() -> dict[str, Any]:
    key_env = "KILOCODE_API_KEY"
    return {
        "models": {
            "providers": {
                "kilocode": {
                    "baseUrl": KILOCODE_BASE_URL,
                    "api": "openai-completions",
                    "apiKey": {"source": "env", "id": key_env},
                }
            }
        },
        "agents": {
            "defaults": {
                "model": {
                    "primary": f"kilocode/{kilocode_model()}",
                    "fallbacks": [
                        "kilocode/kilo-auto/small",
                        "kilocode/openrouter/free",
                    ],
                }
            }
        },
        "browser": {"defaultProfile": "openclaw"},
    }


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, val in patch.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def configure_kilocode(
    workspace: Path | None = None,
    home: Path | None = None,
) -> dict[str, Any]:
    """Point Cursor, Devin, and OpenClaw at KiloCode free credits, then fallbacks."""
    root = (workspace or Path.cwd()).resolve()
    home_dir = (home or Path.home()).resolve()
    key_present = bool(kilocode_api_key())
    payload = _config_payload(key_present=key_present)
    written: list[str] = []

    for dest in (
        root / ".cursor" / "kilocode.json",
        root / ".devin" / "kilocode.json",
        root / ".openclaw" / "kilocode.json",
        home_dir / ".cursor" / "kilocode.json",
        home_dir / ".config" / "devin" / "kilocode.json",
        home_dir / ".openclaw" / "kilocode.json",
    ):
        _write_json(dest, payload)
        written.append(str(dest))

    openclaw_cfg = home_dir / ".openclaw" / "openclaw.json"
    existing: dict[str, Any] = {}
    if openclaw_cfg.exists():
        try:
            loaded = json.loads(openclaw_cfg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except (json.JSONDecodeError, OSError):
            existing = {}
    merged = _deep_merge(existing, _openclaw_models_patch())
    _write_json(openclaw_cfg, merged)
    written.append(str(openclaw_cfg))
    project_openclaw = root / ".openclaw" / "openclaw.json"
    _write_json(project_openclaw, _openclaw_models_patch())
    written.append(str(project_openclaw))

    # Cursor user settings: OpenAI-compatible override. Do not store the raw key.
    cursor_settings = home_dir / ".config" / "Cursor" / "User" / "settings.json"
    _merge_json(
        cursor_settings,
        {
            "openai.baseURL": KILOCODE_BASE_URL,
            "cursor.model": kilocode_model(),
        },
    )
    written.append(str(cursor_settings))

    env_path = home_dir / ".myrunner" / "trusted.env"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    wanted = {
        "LLM_PROVIDER": "kilocode",
        "FIGUREITOUT_KILOCODE_BASE_URL": KILOCODE_BASE_URL,
        "FIGUREITOUT_KILOCODE_MODEL": kilocode_model(),
        "FIGUREITOUT_FALLBACK_PROVIDERS": "kilocode,local,openai,anthropic",
    }
    by_key = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            by_key[k.strip()] = v
    by_key.update(wanted)
    body = "\n".join(f"{k}={v}" for k, v in by_key.items()) + "\n"
    env_path.write_text(body, encoding="utf-8")
    written.append(str(env_path))

    return {
        "ok": True,
        "key_present": key_present,
        "default_model": kilocode_model(),
        "base_url": KILOCODE_BASE_URL,
        "written": written,
        "chain": provider_chain(),
    }
