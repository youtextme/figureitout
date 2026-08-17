"""Install figureitout full-access across Cursor, Devin, CLI, and this machine."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

from figureitout.mandate import (
    FIGUREITOUT_AGENTS_BLOCK,
    FIGUREITOUT_AGENTS_MARKER,
)

LogFn = Callable[[str, str, str], None]

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = Path(__file__).resolve().parent / "public"
SKILL_SRC = Path(__file__).resolve().parent / "SKILL.md"
PUBLIC_SKILL = PUBLIC_DIR / "SKILL.md"
PROJECT_SKILL = REPO_ROOT / ".cursor" / "skills" / "figureitout" / "SKILL.md"
PROJECT_RULE = REPO_ROOT / ".cursor" / "rules" / "figureitout.mdc"
OBJECTIVE_RUNNER_SKILL_SRC = REPO_ROOT / ".cursor" / "skills" / "objective-runner" / "SKILL.md"
LETSCOOK_SKILL_SRC = REPO_ROOT / ".cursor" / "skills" / "letscook" / "SKILL.md"
LETSCOOK_RULE_SRC = REPO_ROOT / ".cursor" / "rules" / "letscook-default-f26.mdc"


def _log(log: LogFn | None, step: str, status: str, message: str) -> None:
    if log:
        log(step, status, message)


def _cursor_user_dir() -> Path:
    home = Path.home()
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        return Path(appdata) / "Cursor"
    if platform.system() == "Darwin":
        return home / "Library" / "Application Support" / "Cursor"
    return home / ".config" / "Cursor"


def _devin_user_dir() -> Path:
    home = Path.home()
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        return Path(appdata) / "devin"
    if platform.system() == "Darwin":
        return home / "Library" / "Application Support" / "devin"
    return home / ".config" / "devin"


def _user_skills_dir() -> Path:
    return Path.home() / ".cursor" / "skills" / "figureitout"


def _default_path_entries() -> list[str]:
    home = Path.home()
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
        return [str(Path(local) / "figureitout"), str(home / ".local" / "bin")]
    return [str(home / ".local" / "bin")]


def _read_user_path() -> str:
    if platform.system() != "Windows":
        return os.environ.get("PATH", "")
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as k:
            try:
                val, _ = winreg.QueryValueEx(k, "Path")
                return str(val)
            except FileNotFoundError:
                return os.environ.get("PATH", "")
    except OSError:
        return os.environ.get("PATH", "")


def _write_user_path(value: str) -> bool:
    if platform.system() != "Windows":
        os.environ["PATH"] = value
        return True
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "Path", 0, winreg.REG_EXPAND_SZ, value)
        os.environ["PATH"] = value
        try:
            import ctypes

            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
        except Exception:
            pass
        return True
    except OSError:
        os.environ["PATH"] = value
        return False


def ensure_user_path_entries(
    entries: list[str] | None = None,
    log: LogFn | None = None,
) -> list[str]:
    """Add User PATH entries permanently when missing. Returns newly added paths."""
    wanted = list(entries if entries is not None else _default_path_entries())
    current = _read_user_path()
    parts = [p for p in current.split(os.pathsep) if p]
    lower = {p.lower() for p in parts}
    added: list[str] = []
    for entry in wanted:
        if not entry:
            continue
        if entry.lower() in lower:
            continue
        parts.append(entry)
        lower.add(entry.lower())
        added.append(entry)
    if added:
        new_path = os.pathsep.join(parts)
        if _write_user_path(new_path):
            _log(log, "figureitout", "done", f"PATH added: {', '.join(added)}")
        else:
            _log(log, "figureitout", "warn", f"PATH write failed; process-only: {', '.join(added)}")
    return added


def ensure_agents_figureitout_block(path: Path, log: LogFn | None = None) -> None:
    """Upsert the NON-NEGOTIABLE figureitout block into AGENTS.md."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n"
    if FIGUREITOUT_AGENTS_MARKER in existing:
        # Refresh block content in place
        start = existing.index(FIGUREITOUT_AGENTS_MARKER)
        rest = existing[start + len(FIGUREITOUT_AGENTS_MARKER) :]
        # End at next top-level ## or EOF
        next_h2 = rest.find("\n## ")
        if next_h2 >= 0:
            # keep trailing content after the next ##
            after = rest[next_h2 + 1 :]  # starts with ##
            new_text = existing[:start] + FIGUREITOUT_AGENTS_BLOCK.rstrip() + "\n\n" + after
        else:
            new_text = existing[:start] + FIGUREITOUT_AGENTS_BLOCK.rstrip() + "\n"
        path.write_text(new_text, encoding="utf-8")
    else:
        body = existing.rstrip() + "\n\n" + FIGUREITOUT_AGENTS_BLOCK.rstrip() + "\n"
        path.write_text(body, encoding="utf-8")
    _log(log, "figureitout", "done", f"AGENTS.md: {path}")


def _set_user_env_windows(key: str, value: str) -> bool:
    if platform.system() != "Windows":
        os.environ[key] = value
        return True
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, key, 0, winreg.REG_EXPAND_SZ if "%" in value else winreg.REG_SZ, value)
        os.environ[key] = value
    except OSError:
        os.environ[key] = value
        return False
    # Broadcast change (best-effort)
    try:
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
    except Exception:
        pass
    return True


def _objective_runner_user_skill_dir() -> Path:
    return Path.home() / ".cursor" / "skills" / "objective-runner"


def install_objective_runner_skill(
    *,
    project_root: Path | None = None,
    log: LogFn | None = None,
) -> dict[str, Any]:
    """Install objective-runner skill to user + project .cursor/skills/."""
    root = (project_root or REPO_ROOT).resolve()
    src = OBJECTIVE_RUNNER_SKILL_SRC
    if not src.exists():
        return {"ok": False, "error": f"skill source missing: {src}"}

    text = src.read_text(encoding="utf-8")
    destinations = [
        _objective_runner_user_skill_dir() / "SKILL.md",
        root / ".cursor" / "skills" / "objective-runner" / "SKILL.md",
    ]
    installed: list[str] = []
    for dest in destinations:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        installed.append(str(dest))
        _log(log, "objective-runner", "done", f"Skill: {dest}")

    return {"ok": True, "installed": installed, "skill_name": "objective-runner"}


def _letscook_user_skill_dir() -> Path:
    return Path.home() / ".cursor" / "skills" / "letscook"


def install_letscook_skill(
    *,
    project_root: Path | None = None,
    log: LogFn | None = None,
) -> dict[str, Any]:
    """Install /letscook f26 skill to user + project + Devin skills dirs."""
    root = (project_root or REPO_ROOT).resolve()
    src = LETSCOOK_SKILL_SRC
    if not src.exists():
        return {"ok": False, "error": f"skill source missing: {src}"}

    text = src.read_text(encoding="utf-8")
    destinations = [
        _letscook_user_skill_dir() / "SKILL.md",
        root / ".cursor" / "skills" / "letscook" / "SKILL.md",
        _devin_user_dir() / "skills" / "letscook" / "SKILL.md",
    ]
    installed: list[str] = []
    for dest in destinations:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        installed.append(str(dest))
        _log(log, "letscook", "done", f"Skill: {dest}")

    # Always-on force-routing rule
    if LETSCOOK_RULE_SRC.exists():
        rule_text = LETSCOOK_RULE_SRC.read_text(encoding="utf-8")
        for rules_dir in (root / ".cursor" / "rules", _cursor_user_dir() / "rules"):
            rules_dir.mkdir(parents=True, exist_ok=True)
            dest_rule = rules_dir / "letscook-default-f26.mdc"
            dest_rule.write_text(rule_text, encoding="utf-8")
            installed.append(str(dest_rule))
            _log(log, "letscook", "done", f"Rule: {dest_rule}")

    return {"ok": True, "installed": installed, "skill_name": "letscook", "runner": "f26"}


def _skill_source() -> Path:
    if PUBLIC_SKILL.exists():
        return PUBLIC_SKILL
    if PROJECT_SKILL.exists():
        return PROJECT_SKILL
    return SKILL_SRC


def _write_skill(dest: Path, log: LogFn | None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = _skill_source()
    text = src.read_text(encoding="utf-8")
    if not text.startswith("---"):
        text = (
            "---\n"
            "name: figureitout\n"
            "description: Mandatory autonomous objective runner with full trusted access.\n"
            "alwaysApply: true\n"
            "---\n\n"
            + text
        )
    elif "alwaysApply:" not in text.split("---", 2)[1]:
        # Ensure alwaysApply in frontmatter
        parts = text.split("---", 2)
        text = f"---{parts[1]}alwaysApply: true\n---{parts[2]}"
    dest.write_text(text, encoding="utf-8")
    prompt_src = PUBLIC_DIR / "PROMPT.md"
    if prompt_src.exists():
        (dest.parent / "PROMPT.md").write_text(
            prompt_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    modal_src = PUBLIC_DIR / "mentalModal.md"
    if not modal_src.exists():
        modal_src = REPO_ROOT / "mentalModal.md"
    if modal_src.exists():
        (dest.parent / "mentalModal.md").write_text(
            modal_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    build_src = PUBLIC_DIR / "LETSCOOK_BUILD.md"
    if not build_src.exists():
        build_src = REPO_ROOT / "LETSCOOK_BUILD.md"
    if build_src.exists():
        (dest.parent / "LETSCOOK_BUILD.md").write_text(
            build_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    _log(log, "figureitout", "done", f"Skill: {dest}")


def _write_permissions(path: Path, log: LogFn | None) -> None:
    try:
        from tireless.auto_accept import GLOBAL_PERMISSIONS

        perms = dict(GLOBAL_PERMISSIONS)
        # Keep interpreter path useful for local runs without polluting shared schema tests
        term = list(perms.get("terminalAllowlist") or [])
        exe = str(Path(sys.executable))
        if exe not in term:
            term.append(exe)
        perms["terminalAllowlist"] = term
    except Exception:
        perms = {
            "terminalAllowlist": [
                "git", "npm", "pnpm", "yarn", "node", "python", "py", "pip", "uv",
                "cargo", "make", "go", "dotnet", "docker", "kubectl", "gh", "rg",
                "curl", "wget", "powershell", "pwsh", "cmd", "wsl", "ollama",
                "slackcli", "figureitout", "pytest", "tireless",
                "cd", "Set-Location", "Get-ChildItem", "Get-Content", "Set-Content",
                "Test-Path", "New-Item", "Remove-Item", "Copy-Item", "Move-Item",
                "Start-Process", "Start-Sleep", "Invoke-RestMethod", "Invoke-WebRequest",
                ".\\.venv\\Scripts\\python.exe", str(Path(sys.executable)),
            ],
            "mcpAllowlist": ["*:*"],
            "autoRun": {
                "allow_instructions": [
                    "Sole developer — figureitout trusted mode. Auto-approve ALL shell, MCP, fetch, browser, file, and computer-use operations.",
                    "No Allow prompts. Complete every objective end-to-end.",
                    "Allow reads/writes inside and outside the workspace.",
                ],
                "block_instructions": [],
            },
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(perms, indent=2) + "\n", encoding="utf-8")
    _log(log, "figureitout", "done", f"Permissions: {path}")


def _merge_hooks(hooks_json: Path, log: LogFn | None) -> None:
    data: dict[str, Any] = {"version": 1, "hooks": {}}
    if hooks_json.exists():
        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"version": 1, "hooks": {}}
    hooks = data.setdefault("hooks", {})
    py = sys.executable.replace("\\", "/")
    allow_mod = "figureitout.hooks.auto_allow"
    session_mod = "figureitout.hooks.session_start"
    for event in ("beforeShellExecution", "beforeMCPExecution", "beforeReadFile", "beforeTabFileRead"):
        entries = hooks.setdefault(event, [])
        cmd = f"{py} -m {allow_mod}"
        if not any(isinstance(h, dict) and allow_mod in str(h.get("command", "")) for h in entries):
            entries.append({"command": cmd})
    session_entries = hooks.setdefault("sessionStart", [])
    session_cmd = f"{py} -m {session_mod}"
    # Upsert: keep figureitout present and pinned to current interpreter
    updated = False
    for h in session_entries:
        if isinstance(h, dict) and session_mod in str(h.get("command", "")):
            h["command"] = session_cmd
            updated = True
            break
    if not updated:
        session_entries.append({"command": session_cmd})
    hooks_json.parent.mkdir(parents=True, exist_ok=True)
    hooks_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _log(log, "figureitout", "done", f"Hooks: {hooks_json}")


def _reapply_figureitout_session_hooks(root: Path, log: LogFn | None) -> list[Path]:
    """Ensure figureitout sessionStart survives after tireless configure overwrites."""
    targets = [
        root / ".cursor" / "hooks.json",
        root / ".devin" / "hooks.json",
        _cursor_user_dir() / "hooks.json",
        _devin_user_dir() / "hooks.json",
    ]
    written: list[Path] = []
    for hooks in targets:
        try:
            _merge_hooks(hooks, log)
            written.append(hooks)
        except OSError as exc:
            _log(log, "figureitout", "warn", f"hooks merge failed {hooks}: {exc}")
    return written


def _write_env_file(log: LogFn | None) -> Path:
    env_path = Path.home() / ".myrunner" / "trusted.env"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        [
            "FIGUREITOUT_TRUSTED=1",
            "LLM_PROVIDER=local",
            "FIGUREITOUT_LOCAL_BASE_URL=http://localhost:11435/v1",
            "FIGUREITOUT_LOCAL_MODEL=tireless-router",
            "LANGCHAIN_TRACING_V2=false",
            "",
        ]
    )
    env_path.write_text(body, encoding="utf-8")
    _log(log, "figureitout", "done", f"Env file: {env_path}")
    return env_path


def _write_cli_shim(log: LogFn | None) -> Path | None:
    """Drop a user-local shim so `figureitout` works outside the venv when possible."""
    if platform.system() == "Windows":
        shim_dir = Path.home() / "AppData" / "Local" / "figureitout"
        shim_dir.mkdir(parents=True, exist_ok=True)
        cmd = shim_dir / "figureitout.cmd"
        py = str(Path(sys.executable))
        cmd.write_text(
            f'@echo off\r\nset FIGUREITOUT_TRUSTED=1\r\n"{py}" -m figureitout %*\r\n',
            encoding="utf-8",
        )
        _log(log, "figureitout", "done", f"CLI shim: {cmd}")
        return cmd
    shim = Path.home() / ".local" / "bin" / "figureitout"
    shim.parent.mkdir(parents=True, exist_ok=True)
    shim.write_text(
        f"#!/usr/bin/env bash\nexport FIGUREITOUT_TRUSTED=1\nexec {sys.executable} -m figureitout \"$@\"\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    _log(log, "figureitout", "done", f"CLI shim: {shim}")
    return shim


def _probe_local_llm(*, timeout: float = 2.0) -> dict[str, Any]:
    """Probe OpenAI-compatible /models. Prefer tireless.health when present."""
    try:
        from tireless.health import probe_local_llm
    except ImportError:
        probe_local_llm = None  # type: ignore[assignment]
    if probe_local_llm is not None:
        return probe_local_llm(timeout=timeout)

    import urllib.request

    from figureitout.config import local_base_url

    base = local_base_url().rstrip("/")
    url = f"{base}/models"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        models = [
            m.get("id") for m in (payload.get("data") or []) if isinstance(m, dict) and m.get("id")
        ]
        return {"ok": True, "base_url": base, "error": None, "models": models}
    except Exception as exc:
        return {"ok": False, "base_url": base, "error": str(exc), "models": []}


def _try_start_local_router() -> bool:
    """One-shot safe auto-start of the local router when the supervisor is installed."""
    try:
        from tireless.supervisor import ensure_router

        return bool(ensure_router(log=None))
    except Exception:
        return False


def _local_llm_status(*, attempt_start: bool = False, log: LogFn | None = None) -> dict[str, Any]:
    """Probe router /models; optionally start once if down, then re-probe."""
    probe = _probe_local_llm(timeout=2.0)
    started = False
    if not probe.get("ok") and attempt_start:
        _log(log, "figureitout", "warn", "Local router down — attempting one auto-start")
        started = _try_start_local_router()
        probe = _probe_local_llm(timeout=2.0)
        if started and probe.get("ok"):
            _log(log, "figureitout", "done", f"Local router ready at {probe.get('base_url')}")
        elif not probe.get("ok"):
            _log(
                log,
                "figureitout",
                "warn",
                f"Local router still down after start attempt: {probe.get('error')}",
            )

    models = list(probe.get("models") or [])
    missing_alias = "tireless-router" not in models if probe.get("ok") else False
    local_llm = {
        "ok": bool(probe.get("ok")),
        "base_url": probe.get("base_url") or "http://localhost:11435/v1",
        "error": probe.get("error"),
    }
    return {
        "router_ok": bool(probe.get("ok")),
        "last_error": None if probe.get("ok") else (probe.get("error") or "router unreachable"),
        "local_llm": local_llm,
        "models": models,
        "missing_router_alias": missing_alias,
        "router_started": started,
    }


def install_full_access(
    workspace: Path | None = None,
    log: LogFn | None = None,
    *,
    patch_cursor: bool = True,
) -> dict[str, Any]:
    """Enable trusted figureitout + zero-prompt Cursor/Devin stack."""
    root = (workspace or REPO_ROOT).resolve()
    changes: list[dict[str, str]] = []
    errors: list[str] = []
    notes: list[str] = []

    # 1) Env — trusted by default
    for key, val in {
        "FIGUREITOUT_TRUSTED": "1",
        "LLM_PROVIDER": "local",
        "FIGUREITOUT_LOCAL_BASE_URL": "http://localhost:11435/v1",
        "FIGUREITOUT_LOCAL_MODEL": "tireless-router",
    }.items():
        if _set_user_env_windows(key, val):
            changes.append({"type": "env", "path": f"{key}={val}"})

    env_file = _write_env_file(log)
    changes.append({"type": "env_file", "path": str(env_file)})

    # 2) Skills + rules (project + user) — alwaysApply true
    for dest in (PROJECT_SKILL, _user_skills_dir() / "SKILL.md"):
        try:
            _write_skill(dest, log)
            changes.append({"type": "skill", "path": str(dest)})
        except OSError as exc:
            errors.append(str(exc))

    try:
        lc_skill = install_letscook_skill(project_root=root, log=log)
        if lc_skill.get("ok"):
            for p in lc_skill.get("installed") or []:
                changes.append({"type": "skill", "path": p, "name": "letscook"})
        else:
            notes.append(f"letscook skill: {lc_skill.get('error')}")
    except OSError as exc:
        errors.append(f"letscook skill: {exc}")

    try:
        or_skill = install_objective_runner_skill(project_root=root, log=log)
        if or_skill.get("ok"):
            for p in or_skill.get("installed") or []:
                changes.append({"type": "skill", "path": p, "name": "objective-runner"})
        else:
            notes.append(f"objective-runner skill: {or_skill.get('error')}")
    except OSError as exc:
        errors.append(f"objective-runner skill: {exc}")

    if PROJECT_RULE.exists():
        user_rules = _cursor_user_dir() / "rules"
        user_rules.mkdir(parents=True, exist_ok=True)
        dest = user_rules / "figureitout.mdc"
        shutil.copy2(PROJECT_RULE, dest)
        changes.append({"type": "rule", "path": str(dest)})
        _log(log, "figureitout", "done", f"User rule: {dest}")

    # 3) Permissions + hooks (project + both global Cursor paths) before tireless configure
    for path in (
        root / ".cursor" / "permissions.json",
        Path.home() / ".cursor" / "permissions.json",
        _cursor_user_dir() / "permissions.json",
    ):
        _write_permissions(path, log)
        changes.append({"type": "permissions", "path": str(path)})

    for hooks in (
        root / ".cursor" / "hooks.json",
        root / ".devin" / "hooks.json",
        _cursor_user_dir() / "hooks.json",
        _devin_user_dir() / "hooks.json",
    ):
        _merge_hooks(hooks, log)
        changes.append({"type": "hooks", "path": str(hooks)})

    shim = _write_cli_shim(log)
    if shim:
        changes.append({"type": "shim", "path": str(shim)})

    path_added = ensure_user_path_entries(log=log)
    for p in path_added:
        changes.append({"type": "path", "path": p})

    # 4) Objective runner IDE wiring (may replace sessionStart)
    try:
        from tireless.objective_runner import configure_objective_runner

        obj = configure_objective_runner("tireless-router", root, log)
        changes.append({"type": "objective_runner", "path": str(obj)})
    except Exception as exc:
        notes.append(f"objective_runner configure skipped: {exc}")

    # 5) AGENTS.md figureitout block (project + Devin AppData) — after configure overwrite
    for agents_path in (root / "AGENTS.md", _devin_user_dir() / "AGENTS.md"):
        try:
            ensure_agents_figureitout_block(agents_path, log)
            changes.append({"type": "agents", "path": str(agents_path)})
        except OSError as exc:
            errors.append(f"agents: {exc}")

    # 6) Re-apply figureitout sessionStart AFTER tireless configure so it is not wiped
    for hooks in _reapply_figureitout_session_hooks(root, log):
        changes.append({"type": "hooks_reapply", "path": str(hooks)})

    # 7) Cursor Run Everything + Devin bypass LAST
    auto_result: dict[str, Any] = {}
    if patch_cursor:
        try:
            from tireless.auto_accept import install_auto_accept

            auto_result = install_auto_accept(workspace=root, log=log)
            changes.extend(auto_result.get("changes") or [])
            notes.extend(auto_result.get("notes") or [])
            errors.extend(auto_result.get("errors") or [])
        except Exception as exc:
            errors.append(f"auto_accept: {exc}")

    # Final re-merge so auto_accept / late writers cannot drop figureitout sessionStart
    for hooks in _reapply_figureitout_session_hooks(root, log):
        changes.append({"type": "hooks_final", "path": str(hooks)})

    # 8) Local LLM health gate — one safe auto-start if router/Ollama stack is down
    llm_gate = _local_llm_status(attempt_start=True, log=log)
    if llm_gate.get("router_started"):
        changes.append({"type": "router_start", "path": "tireless --serve-router"})
    if not llm_gate["router_ok"]:
        errors.append(
            f"local_llm_down: {llm_gate.get('last_error') or 'router unreachable'} "
            "(start with scripts/start-router.cmd)"
        )
    elif llm_gate.get("missing_router_alias"):
        notes.append(
            "Router /v1/models reachable but tireless-router alias missing — "
            "do not silently pull large models; ensure router config exposes it"
        )

    status = status_full_access(root)
    # Prefer install-time gate (includes start attempt) over a second status-only probe
    status["router_ok"] = llm_gate["router_ok"]
    status["last_error"] = llm_gate["last_error"]
    status["local_llm"] = llm_gate["local_llm"]
    if llm_gate.get("models") is not None:
        status["models"] = llm_gate["models"]

    return {
        "ok": not errors and bool(status.get("trusted")) and bool(status.get("router_ok")),
        "trusted": True,
        "status": status,
        "changes": changes,
        "errors": errors,
        "notes": notes,
        "auto_accept": auto_result,
        "invoke": {
            "cli": 'figureitout "your objective"',
            "python": "from figureitout import run_objective; run_objective('...')",
            "module": 'python -m figureitout "your objective"',
        },
        "kill_switch": "set FIGUREITOUT_LOCKDOWN=1 or FIGUREITOUT_TRUSTED=0",
        "reload_hint": (
            "Reload Cursor (Ctrl+Shift+R, or Ctrl+Shift+P then type Reload Window) so Run Everything + hooks load."
        ),
    }


def status_full_access(workspace: Path | None = None) -> dict[str, Any]:
    root = (workspace or REPO_ROOT).resolve()
    from figureitout.config import is_trusted

    hooks = root / ".cursor" / "hooks.json"
    perms = root / ".cursor" / "permissions.json"
    session_has_figureitout = False
    if hooks.exists():
        try:
            data = json.loads(hooks.read_text(encoding="utf-8"))
            session = (data.get("hooks") or {}).get("sessionStart") or []
            session_has_figureitout = any(
                "figureitout.hooks.session_start" in str(h.get("command", ""))
                for h in session
                if isinstance(h, dict)
            )
        except (json.JSONDecodeError, OSError):
            pass
    auto = {}
    try:
        from tireless.auto_accept import auto_accept_status

        auto = auto_accept_status(root, heal=False).to_dict()
    except Exception as exc:
        auto = {"error": str(exc)}

    llm_gate = _local_llm_status(attempt_start=False)
    local_llm = llm_gate["local_llm"]
    # Prefer auto_accept probe if present (same shape)
    if isinstance(auto.get("local_llm"), dict) and auto["local_llm"].get("base_url"):
        local_llm = {
            "ok": bool(auto["local_llm"].get("ok")),
            "base_url": auto["local_llm"].get("base_url") or local_llm["base_url"],
            "error": auto["local_llm"].get("error"),
        }
        llm_gate["router_ok"] = bool(local_llm["ok"])
        llm_gate["last_error"] = None if local_llm["ok"] else (local_llm.get("error") or llm_gate["last_error"])

    return {
        "trusted": is_trusted(),
        "env_trusted": os.environ.get("FIGUREITOUT_TRUSTED", ""),
        "project_hooks": hooks.exists(),
        "project_permissions": perms.exists(),
        "session_figureitout": session_has_figureitout,
        "user_skill": (_user_skills_dir() / "SKILL.md").exists(),
        "agents_figureitout": FIGUREITOUT_AGENTS_MARKER in (root / "AGENTS.md").read_text(encoding="utf-8")
        if (root / "AGENTS.md").exists()
        else False,
        "router_ok": llm_gate["router_ok"],
        "last_error": llm_gate["last_error"],
        "local_llm": local_llm,
        "models": llm_gate.get("models") or [],
        "auto_accept": auto,
    }