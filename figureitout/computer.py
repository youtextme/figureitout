"""Layer 8 — computer use. Trusted mode = full host access; else sandbox."""

from __future__ import annotations

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from figureitout.config import is_trusted, workspace_root
from figureitout.policy import check_policy, resolve_objective_type


class SandboxedComputer:
    """Computer surface used by the runner.

    Trusted (default): read/write/shell/network anywhere on the host.
    Sandboxed: writes confined to ~/.myrunner/runs/<run_id>.
    """

    def __init__(
        self,
        run_id: str,
        objective_type: str = "build",
        allowed_hosts: list[str] | None = None,
    ):
        self.run_id = run_id
        self.trusted = is_trusted() or objective_type == "trusted"
        self.objective_type = resolve_objective_type(objective_type)
        self.allowed_hosts = allowed_hosts or ["*"] if self.trusted else ["localhost", "127.0.0.1"]
        self.allowed_write_path = Path.home() / ".myrunner" / "runs" / run_id
        self.allowed_write_path.mkdir(parents=True, exist_ok=True)
        (self.allowed_write_path / "evidence").mkdir(parents=True, exist_ok=True)
        self.workspace = workspace_root()

    def _policy_context(self, action: str, **extra: Any) -> dict[str, Any]:
        ctx: dict[str, Any] = {
            "action": action,
            "path": str(self.allowed_write_path if not self.trusted else self.workspace),
            "run_dir": str(self.allowed_write_path),
            "host": "localhost",
            "allowed_hosts": list(self.allowed_hosts),
            "trusted": self.trusted,
        }
        ctx.update(extra)
        return ctx

    def _evidence(self, action: str, note: str = "") -> Path:
        ts = int(time.time() * 1000)
        evidence_dir = self.allowed_write_path / "evidence"
        marker = evidence_dir / f"{action}_{ts}.txt"
        marker.write_text(note or f"action={action}", encoding="utf-8")
        png = evidence_dir / f"{action}_{ts}.png"
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (320, 80), color=(24, 24, 28))
            draw = ImageDraw.Draw(img)
            draw.text((10, 30), f"{action} @ {ts}", fill=(220, 220, 220))
            img.save(png)
            return png
        except Exception:
            return marker

    def browse(self, url: str) -> str:
        host = _host_of(url)
        check_policy(
            self.objective_type,
            "network",
            self._policy_context("network", host=host or "unknown"),
        )
        self._evidence("browse_before", url)
        content = asyncio.run(self._browse_async(url))
        self._evidence("browse_after", f"bytes={len(content)}")
        return content

    async def _browse_async(self, url: str) -> str:
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            raise RuntimeError("playwright is required for browse()") from exc
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            content = await page.content()
            shot = self.allowed_write_path / "evidence" / f"browse_{int(time.time()*1000)}.png"
            try:
                await page.screenshot(path=str(shot), full_page=False)
            except Exception:
                pass
            await browser.close()
            return content

    def read_file(self, path: str, max_bytes: int = 2_000_000) -> str:
        target = Path(path).expanduser().resolve()
        check_policy(
            self.objective_type,
            "read",
            self._policy_context("read", path=str(target)),
        )
        self._evidence("read", str(target))
        data = target.read_bytes()[:max_bytes]
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> Path:
        target = Path(path).expanduser().resolve()
        allowed = self.allowed_write_path.resolve()
        check_policy(
            self.objective_type,
            "write",
            self._policy_context("write", path=str(target), run_dir=str(allowed)),
        )
        if not self.trusted:
            try:
                target.relative_to(allowed)
            except ValueError as exc:
                raise PermissionError(f"write path outside sandbox: {target}") from exc
        self._evidence("write_before", str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._evidence("write_after", str(target))
        return target

    def run_shell(self, cmd: str | list[str], cwd: str | None = None) -> str:
        work = Path(cwd).expanduser().resolve() if cwd else (
            self.workspace if self.trusted else self.allowed_write_path
        )
        check_policy(
            self.objective_type,
            "shell",
            self._policy_context("shell", path=str(work)),
        )
        self._evidence("shell_before", str(cmd))
        if self.trusted and isinstance(cmd, str):
            completed = subprocess.run(
                cmd,
                shell=True,
                cwd=str(work),
                capture_output=True,
                text=True,
                check=False,
                env=os.environ.copy(),
            )
        else:
            args = cmd if isinstance(cmd, list) else cmd.split()
            completed = subprocess.run(
                args,
                shell=False,
                cwd=str(work),
                capture_output=True,
                text=True,
                check=False,
                env=os.environ.copy(),
            )
        self._evidence("shell_after", f"exit={completed.returncode}")
        if completed.returncode != 0:
            raise RuntimeError(
                f"shell failed ({completed.returncode}): {completed.stderr or completed.stdout}"
            )
        return completed.stdout

    def screenshot(self, url: str | None = None) -> Path:
        """Capture a page or blank evidence screenshot; returns PNG path."""
        check_policy(self.objective_type, "network" if url else "read", self._policy_context("read"))
        out = self.allowed_write_path / "evidence" / f"shot_{int(time.time()*1000)}.png"
        if url:
            async def _shot() -> None:
                from playwright.async_api import async_playwright

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await page.screenshot(path=str(out))
                    await browser.close()

            asyncio.run(_shot())
        else:
            self._evidence("screenshot", "local")
            # evidence png already written by _evidence when pillow present
            candidates = sorted((self.allowed_write_path / "evidence").glob("screenshot_*.png"))
            if candidates:
                return candidates[-1]
            out.write_bytes(b"")
        return out


# Back-compat alias
TrustedComputer = SandboxedComputer


def _host_of(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""
