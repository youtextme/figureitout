"""Live playbooks: one example each for Cursor, Devin, and OpenClaw — no invented data."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from figureitout.computer import (
    computer_use_needed,
    decide_surface,
    desktop_status,
    render_botfather_wallpaper,
    set_wallpaper,
)
from figureitout.kilocode import configure_kilocode, kilocode_api_key
from figureitout.sync import sync_agents

FLEET_AGENTS = ("cursor", "devin", "openclaw")
EXAMPLE_IDS = ("telegram_omimoh", "gmail_coupang", "kilocode_default", "wallpaper_botfather")

_REPO = Path(__file__).resolve().parents[1]


def _evidence_dir(workspace: Path, agent: str, example: str) -> Path:
    dest = workspace / ".figureitout" / "examples" / agent / example
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _write_report(dest: Path, report: dict[str, Any]) -> Path:
    path = dest / "report.json"
    path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def run_example(
    example: str,
    *,
    agent: str,
    workspace: Path | None = None,
    home: Path | None = None,
    live: bool = False,
) -> dict[str, Any]:
    if example not in EXAMPLE_IDS:
        raise KeyError(f"unknown example: {example}")
    if agent not in FLEET_AGENTS:
        raise KeyError(f"unknown agent: {agent}")
    root = (workspace or _REPO).resolve()
    home_dir = (home or Path.home()).resolve()
    dest = _evidence_dir(root, agent, example)
    runners = {
        "telegram_omimoh": _telegram_omimoh,
        "gmail_coupang": _gmail_coupang,
        "kilocode_default": _kilocode_default,
        "wallpaper_botfather": _wallpaper_botfather,
    }
    report = runners[example](agent=agent, workspace=root, home=home_dir, dest=dest, live=live)
    report.setdefault("agent", agent)
    report.setdefault("example", example)
    report.setdefault("surface", decide_surface(example))
    report.setdefault("computer_use_needed", computer_use_needed(example))
    report["evidence_dir"] = str(dest)
    _write_report(dest, report)
    return report


def run_all_examples(
    workspace: Path | None = None,
    home: Path | None = None,
    live: bool = False,
) -> list[dict[str, Any]]:
    root = (workspace or _REPO).resolve()
    home_dir = (home or Path.home()).resolve()
    sync_agents(workspace=root, home=home_dir)
    reports: list[dict[str, Any]] = []
    for example in EXAMPLE_IDS:
        for agent in FLEET_AGENTS:
            reports.append(
                run_example(example, agent=agent, workspace=root, home=home_dir, live=live)
            )
    summary = root / ".figureitout" / "examples" / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(reports, indent=2, default=str) + "\n", encoding="utf-8")
    return reports


def _telegram_omimoh(
    *,
    agent: str,
    workspace: Path,
    home: Path,
    dest: Path,
    live: bool,
) -> dict[str, Any]:
    objective = "Open Telegram Desktop and go to Omimoh channel and type What is cheese made of"
    desk = desktop_status()
    (dest / "desktop.json").write_text(json.dumps(desk, indent=2) + "\n", encoding="utf-8")
    if not live:
        return {
            "status": "blocked",
            "reason": "dry-run: will not send a Telegram message without a live user session",
            "objective": objective,
            "desktop": desk,
            "typed": None,
            "channel": "Omimoh",
        }
    if not desk.get("telegram"):
        return {
            "status": "blocked",
            "reason": "Telegram Desktop is not installed on this host",
            "objective": objective,
            "desktop": desk,
            "typed": None,
            "channel": "Omimoh",
        }
    if not desk.get("available"):
        return {
            "status": "blocked",
            "reason": "no desktop display for Telegram Desktop",
            "objective": objective,
            "desktop": desk,
            "typed": None,
            "channel": "Omimoh",
        }
    binary = str(desk["telegram"])
    import subprocess

    subprocess.Popen(
        [binary],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )
    # A launched app is not a sent message. Without the user's Omimoh session this stays blocked.
    return {
        "status": "blocked",
        "reason": (
            "Telegram Desktop binary is present but there is no evidence of a logged-in "
            "Omimoh channel session on this host; message not sent"
        ),
        "objective": objective,
        "desktop": desk,
        "launched": True,
        "typed": None,
        "channel": "Omimoh",
        "message": "What is cheese made of",
    }


def _gmail_coupang(
    *,
    agent: str,
    workspace: Path,
    home: Path,
    dest: Path,
    live: bool,
) -> dict[str, Any]:
    objective = (
        "Open my Gmail in chrome and tell me about my orders in Coupang in the last month "
        "= how much did I spend and one graph that gives that expenditure split and categorization"
    )
    desk = desktop_status()
    (dest / "desktop.json").write_text(json.dumps(desk, indent=2) + "\n", encoding="utf-8")
    base = {
        "objective": objective,
        "total_spent": None,
        "currency": None,
        "orders": None,
        "graph": None,
        "desktop": desk,
    }
    if not live:
        return {
            **base,
            "status": "blocked",
            "reason": "dry-run: no Gmail session probed; spend omitted (no live total)",
        }
    if not desk.get("chrome"):
        return {**base, "status": "blocked", "reason": "Chrome is not installed"}
    # Live: open Gmail. Do not parse spend unless the inbox is actually signed in.
    chrome = str(desk["chrome"])
    html_path = dest / "gmail.html"
    signed_in = False
    page_note = ""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        # Fall back to launching the real Chrome window when computer use is the job.
        if desk.get("available"):
            import subprocess

            subprocess.Popen(
                [chrome, "https://mail.google.com"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=os.environ.copy(),
            )
            page_note = f"launched Chrome to Gmail ({exc})"
        else:
            page_note = f"playwright missing and no display ({exc})"
        return {
            **base,
            "status": "blocked",
            "reason": "Gmail session not readable; Coupang spend omitted (no live total)",
            "page": page_note,
            "signed_in": False,
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not bool(desk.get("available")))
            page = browser.new_page()
            page.goto("https://mail.google.com", wait_until="domcontentloaded", timeout=45000)
            html = page.content()
            html_path.write_text(html[:200_000], encoding="utf-8")
            shot = dest / "gmail.png"
            try:
                page.screenshot(path=str(shot), full_page=False)
            except Exception:
                shot = None
            lower = html.lower()
            signed_in = "inbox" in lower and "sign in" not in lower and "accounts.google.com" not in page.url
            page_note = page.url
            browser.close()
    except Exception as exc:
        return {
            **base,
            "status": "blocked",
            "reason": f"Gmail navigation failed: {exc}",
            "signed_in": False,
        }

    if not signed_in:
        return {
            **base,
            "status": "blocked",
            "reason": "not signed into Gmail; Coupang last-month spend omitted (no live total)",
            "page": page_note,
            "signed_in": False,
            "screenshot": str(shot) if shot else None,
        }
    # Signed in but Coupang parsing is a further live search — still omit if no matches.
    return {
        **base,
        "status": "partial",
        "reason": "Gmail appears signed in; Coupang totals not extracted in this run — omitted (no live total)",
        "page": page_note,
        "signed_in": True,
        "screenshot": str(shot) if shot else None,
    }


def _kilocode_default(
    *,
    agent: str,
    workspace: Path,
    home: Path,
    dest: Path,
    live: bool,
) -> dict[str, Any]:
    objective = (
        "Configure Cursor and Devin with my kilocode key so that they can also use "
        "the free API credits every day as the default and then move to other models"
    )
    result = configure_kilocode(workspace=workspace, home=home)
    (dest / "kilocode-result.json").write_text(
        json.dumps({k: v for k, v in result.items() if k != "key"}, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    ping: dict[str, Any] | None = None
    if live:
        ping = _ping_kilocode_free()
        (dest / "kilocode-ping.json").write_text(json.dumps(ping, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "done" if result.get("ok") else "blocked",
        "objective": objective,
        "key_present": bool(kilocode_api_key()),
        "default_model": result.get("default_model"),
        "chain": result.get("chain"),
        "written": result.get("written"),
        "ping": ping,
        "note": "API key is read from the environment and is never written into report.json",
    }


def _ping_kilocode_free() -> dict[str, Any]:
    import json as _json
    import urllib.error
    import urllib.request

    from figureitout.kilocode import KILOCODE_BASE_URL, kilocode_api_key, kilocode_model

    url = KILOCODE_BASE_URL.rstrip("/") + "/chat/completions"
    body = _json.dumps(
        {
            "model": kilocode_model(),
            "messages": [{"role": "user", "content": "Reply with the single word pong."}],
            "max_tokens": 16,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = kilocode_api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = _json.loads(resp.read().decode("utf-8"))
        return {
            "ok": True,
            "status_code": 200,
            "ms": int((time.time() - started) * 1000),
            "model": kilocode_model(),
            "has_choices": bool(payload.get("choices")),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status_code": int(exc.code),
            "reason": str(exc.reason),
            "model": kilocode_model(),
        }
    except Exception as exc:
        return {"ok": False, "reason": str(exc), "model": kilocode_model()}


def _wallpaper_botfather(
    *,
    agent: str,
    workspace: Path,
    home: Path,
    dest: Path,
    live: bool,
) -> dict[str, Any]:
    objective = "change the background wallpaper to a photo of botfather - 4K resolution really cool looking"
    size = (3840, 2160) if live else (64, 36)
    image = dest / ("botfather-4k.png" if live else "botfather-preview.png")
    try:
        render_botfather_wallpaper(image, size=size)
    except Exception as exc:
        return {
            "status": "blocked",
            "reason": f"wallpaper render failed: {exc}",
            "objective": objective,
            "image": None,
        }
    applied: dict[str, Any] | None = None
    if live:
        applied = set_wallpaper(image)
    else:
        applied = {"ok": False, "status": "blocked", "reason": "dry-run: wallpaper not applied"}
    width = height = None
    try:
        from PIL import Image

        with Image.open(image) as im:
            width, height = im.size
    except Exception:
        pass
    status = "done" if live and applied and applied.get("ok") else ("partial" if image.exists() else "blocked")
    if not live:
        status = "partial"
    return {
        "status": status,
        "objective": objective,
        "image": str(image),
        "width": width,
        "height": height,
        "applied": applied,
        "live": live,
    }
