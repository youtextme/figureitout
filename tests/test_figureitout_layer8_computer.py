"""Layer 8 — sandboxed computer use."""

from __future__ import annotations

import os
import uuid

import pytest

from figureitout.computer import SandboxedComputer


@pytest.fixture(autouse=True)
def _force_sandbox(monkeypatch):
    monkeypatch.setenv("FIGUREITOUT_TRUSTED", "0")
    monkeypatch.delenv("FIGUREITOUT_LOCKDOWN", raising=False)


def test_write_outside_sandbox_raises_permission_error():
    assert os.environ.get("FIGUREITOUT_TRUSTED") == "0"
    comp = SandboxedComputer(run_id=f"test-{uuid.uuid4().hex[:8]}", objective_type="build")
    assert comp.trusted is False
    outside = str(comp.allowed_write_path.parent / "not-allowed.txt")
    with pytest.raises(PermissionError):
        comp.write_file(outside, "nope")


def test_write_inside_sandbox_ok():
    comp = SandboxedComputer(run_id=f"test-{uuid.uuid4().hex[:8]}", objective_type="build")
    target = comp.allowed_write_path / "hello.txt"
    path = comp.write_file(str(target), "hello")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "hello"


def test_shell_echo():
    import sys

    comp = SandboxedComputer(run_id=f"test-{uuid.uuid4().hex[:8]}", objective_type="build")
    out = comp.run_shell([sys.executable, "-c", "print('ok')"])
    assert "ok" in out
