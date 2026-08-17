"""Cursor, Devin, and OpenClaw stay in sync; computer use is gated; kilocode is default."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from figureitout.computer import computer_use_needed, decide_surface, desktop_status
from figureitout.connections import connection_status, list_connections
from figureitout.examples import EXAMPLE_IDS, FLEET_AGENTS, run_all_examples, run_example
from figureitout.kilocode import (
    KILOCODE_BASE_URL,
    KILOCODE_FREE_MODEL,
    configure_kilocode,
    kilocode_api_key,
    provider_chain,
)
from figureitout.sync import FLEET_SURFACES, skill_hashes, sync_agents, sync_status


def _home_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "home"
    workspace = tmp_path / "repo"
    home.mkdir()
    workspace.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return workspace, home


def test_computer_use_not_needed_for_files_and_keys():
    assert computer_use_needed("add a unit test for the planner") is False
    assert decide_surface("Configure Cursor and Devin with my kilocode key") == "files"


def test_computer_use_needed_for_telegram_and_wallpaper():
    assert computer_use_needed("Open Telegram Desktop and go to Omimoh channel") is True
    assert decide_surface("Open Telegram Desktop and type What is cheese made of") == "desktop"
    assert decide_surface("change the background wallpaper to a photo of botfather") == "desktop"


def test_gmail_in_chrome_uses_browser_not_files():
    assert computer_use_needed("Open my Gmail in chrome and tell me about Coupang orders") is True
    assert decide_surface("Open my Gmail in chrome") == "browser"


def test_upscale_to_4k(tmp_path):
    from PIL import Image

    from figureitout.computer import upscale_to_4k

    src = tmp_path / "tiny.png"
    Image.new("RGB", (16, 9), (10, 20, 40)).save(src)
    dest = tmp_path / "out.png"
    path = upscale_to_4k(src, dest)
    with Image.open(path) as im:
        assert im.size == (3840, 2160)


def test_desktop_status_is_a_live_probe():
    status = desktop_status()
    assert "display" in status
    assert "available" in status
    assert "chrome" in status
    assert "telegram" in status


def test_sync_writes_identical_skill_to_cursor_devin_openclaw(tmp_path, monkeypatch):
    workspace, _home = _home_workspace(tmp_path, monkeypatch)
    result = sync_agents(workspace=workspace, home=_home)
    assert result["ok"] is True
    assert result["in_sync"] is True
    hashes = skill_hashes(workspace=workspace, home=_home)
    assert set(FLEET_SURFACES) <= set(hashes)
    vals = {hashes[s] for s in ("cursor", "devin", "openclaw") if hashes.get(s)}
    assert len(vals) == 1
    for rel in (
        ".cursor/skills/figureitout/SKILL.md",
        ".devin/skills/figureitout/SKILL.md",
        ".openclaw/skills/figureitout/SKILL.md",
        ".openclaw/skills/computer-use/SKILL.md",
        ".cursor/skills/computer-use/SKILL.md",
        ".devin/skills/computer-use/SKILL.md",
        ".openclaw/AGENTS.md",
        ".openclaw/TOOLS.md",
    ):
        assert (workspace / rel).exists(), rel


def test_sync_detects_drift(tmp_path, monkeypatch):
    workspace, home = _home_workspace(tmp_path, monkeypatch)
    sync_agents(workspace=workspace, home=home)
    drifted = workspace / ".devin" / "skills" / "figureitout" / "SKILL.md"
    drifted.write_text("drifted-on-purpose\n", encoding="utf-8")
    status = sync_status(workspace=workspace, home=home)
    assert status["in_sync"] is False
    assert "devin" in status["drift"]


def test_kilocode_is_default_then_other_models(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("FIGUREITOUT_FALLBACK_PROVIDERS", raising=False)
    chain = provider_chain()
    assert chain[0] == "kilocode"
    assert "local" in chain
    assert "openai" in chain
    assert "anthropic" in chain
    assert KILOCODE_FREE_MODEL == "kilo-auto/free"
    assert "api.kilo.ai" in KILOCODE_BASE_URL


def test_configure_kilocode_writes_cursor_and_devin_without_leaking_key(
    tmp_path, monkeypatch, capsys
):
    workspace, home = _home_workspace(tmp_path, monkeypatch)
    monkeypatch.setenv("KILOCODE_API_KEY", "secret-test-key-do-not-print")
    result = configure_kilocode(workspace=workspace, home=home)
    printed = capsys.readouterr().out + capsys.readouterr().err
    assert "secret-test-key-do-not-print" not in printed
    assert kilocode_api_key() == "secret-test-key-do-not-print"
    cursor = json.loads((workspace / ".cursor" / "kilocode.json").read_text(encoding="utf-8"))
    devin = json.loads((workspace / ".devin" / "kilocode.json").read_text(encoding="utf-8"))
    openclaw = json.loads((workspace / ".openclaw" / "kilocode.json").read_text(encoding="utf-8"))
    for cfg in (cursor, devin, openclaw):
        assert cfg["defaultModel"] == "kilo-auto/free"
        assert cfg["baseUrl"] == KILOCODE_BASE_URL
        assert cfg["fallbacks"]
        assert cfg["apiKeyEnv"]
        assert "secret-test-key" not in json.dumps(cfg)
    assert result["ok"] is True
    assert result["key_present"] is True


def test_connections_cover_fleet_and_computer_use():
    names = list_connections()
    for needed in (
        "cursor",
        "devin",
        "openclaw",
        "kilocode",
        "telegram",
        "gmail",
        "computer_use",
        "wallpaper",
    ):
        assert needed in names, needed
    status = connection_status()
    assert "kilocode" in status
    assert "computer_use" in status


def test_examples_run_each_playbook_per_agent_and_do_not_invent_spend(tmp_path, monkeypatch):
    workspace, home = _home_workspace(tmp_path, monkeypatch)
    monkeypatch.delenv("KILOCODE_API_KEY", raising=False)
    monkeypatch.delenv("KILO_API_KEY", raising=False)
    reports = run_all_examples(workspace=workspace, home=home, live=False)
    agents = {r["agent"] for r in reports}
    examples = {r["example"] for r in reports}
    assert agents == set(FLEET_AGENTS)
    assert examples == set(EXAMPLE_IDS)
    assert len(reports) == len(FLEET_AGENTS) * len(EXAMPLE_IDS)
    for report in reports:
        if report["example"] == "gmail_coupang":
            assert report["status"] in {"blocked", "partial"}
            assert report.get("total_spent") is None
            assert report.get("orders") is None
            assert report.get("graph") is None
        if report["example"] == "telegram_omimoh" and report["status"] == "done":
            raise AssertionError("dry-run telegram must not claim a sent message")
        assert "paste your api key" not in json.dumps(report).lower()


def test_run_example_kilocode_configures_cursor_and_devin(tmp_path, monkeypatch):
    workspace, home = _home_workspace(tmp_path, monkeypatch)
    monkeypatch.setenv("KILOCODE_API_KEY", "kilo-from-env")
    report = run_example("kilocode_default", agent="cursor", workspace=workspace, home=home, live=False)
    assert report["status"] in {"done", "partial"}
    assert (workspace / ".cursor" / "kilocode.json").exists()
    assert (workspace / ".devin" / "kilocode.json").exists()
    assert "kilo-from-env" not in json.dumps(report)
