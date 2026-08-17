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


# --- Computer-use gate: GUI only when the job is the UI ---

_FILES_HINTS = (
    "kilocode",
    "api key",
    "configure cursor",
    "configure devin",
    "unit test",
    "pytest",
    "git commit",
)
_DESKTOP_HINTS = (
    "telegram desktop",
    "wallpaper",
    "background wallpaper",
    "desktop wallpaper",
    "botfather",
    "change the background",
)
_BROWSER_HINTS = (
    "gmail",
    "in chrome",
    "google chrome",
    "coupang",
)


def decide_surface(objective: str) -> str:
    """files | browser | desktop. Computer use only for browser/desktop."""
    text = (objective or "").lower()
    if any(h in text for h in _FILES_HINTS):
        return "files"
    if any(h in text for h in _DESKTOP_HINTS):
        return "desktop"
    if "telegram" in text and "api" not in text:
        return "desktop"
    if any(h in text for h in _BROWSER_HINTS):
        return "browser"
    return "files"


def computer_use_needed(objective: str) -> bool:
    return decide_surface(objective) in {"desktop", "browser"}


def desktop_status() -> dict[str, Any]:
    """Live probe of display, Chrome, Telegram, wallpaper tools. No invented state."""
    import shutil

    display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    chrome = (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
    )
    telegram = shutil.which("telegram-desktop") or shutil.which("telegram")
    wallpaper_tool = (
        shutil.which("xfconf-query")
        or shutil.which("gsettings")
        or shutil.which("feh")
        or shutil.which("nitrogen")
    )
    return {
        "display": display or "",
        "available": bool(display),
        "chrome": chrome,
        "telegram": telegram,
        "wallpaper_tool": wallpaper_tool,
    }


def set_wallpaper(image_path: str | Path) -> dict[str, Any]:
    """Point the desktop background at image_path. Returns evidence, or blocked."""
    target = Path(image_path).expanduser().resolve()
    if not target.exists():
        return {"ok": False, "status": "blocked", "reason": f"image missing: {target}"}
    desk = desktop_status()
    errors: list[str] = []
    tried: list[str] = []

    xfconf = _which("xfconf-query")
    if xfconf:
        tried.append("xfconf-query")
        # Enumerate backdrop properties and set last-image on each.
        list_proc = subprocess.run(
            [xfconf, "-c", "xfce4-desktop", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
        props = [
            line.strip()
            for line in (list_proc.stdout or "").splitlines()
            if line.strip().endswith("/last-image")
        ]
        if not props:
            props = ["/backdrop/screen0/monitor0/workspace0/last-image"]
        ok_any = False
        for prop in props:
            proc = subprocess.run(
                [xfconf, "-c", "xfce4-desktop", "-p", prop, "-s", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                ok_any = True
            else:
                errors.append(proc.stderr.strip() or proc.stdout.strip() or f"xfconf {prop} failed")
        if ok_any:
            return {"ok": True, "status": "done", "tool": "xfconf-query", "path": str(target), "props": props}

    gsettings = _which("gsettings")
    if gsettings:
        tried.append("gsettings")
        uri = target.as_uri()
        proc = subprocess.run(
            [gsettings, "set", "org.gnome.desktop.background", "picture-uri", uri],
            capture_output=True,
            text=True,
            check=False,
        )
        subprocess.run(
            [gsettings, "set", "org.gnome.desktop.background", "picture-uri-dark", uri],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return {"ok": True, "status": "done", "tool": "gsettings", "path": str(target)}
        errors.append(proc.stderr.strip() or "gsettings failed")

    feh = _which("feh")
    if feh and desk.get("available"):
        tried.append("feh")
        proc = subprocess.run([feh, "--bg-fill", str(target)], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return {"ok": True, "status": "done", "tool": "feh", "path": str(target)}
        errors.append(proc.stderr.strip() or "feh failed")

    reason = "no wallpaper tool succeeded"
    if not desk.get("available"):
        reason = "no desktop display"
    return {
        "ok": False,
        "status": "blocked",
        "reason": reason,
        "tried": tried,
        "errors": errors,
        "path": str(target),
        "desktop": desk,
    }


def _which(name: str) -> str | None:
    import shutil

    return shutil.which(name)


def upscale_to_4k(src: str | Path, dest: str | Path) -> Path:
    """Resize any image to 3840×2160 PNG. Requires Pillow."""
    from PIL import Image

    source = Path(src).expanduser().resolve()
    target = Path(dest).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as im:
        rgb = im.convert("RGB")
        out = rgb.resize((3840, 2160), Image.Resampling.LANCZOS)
        out.save(target, "PNG")
    return target


def render_botfather_wallpaper(dest: Path, size: tuple[int, int] = (3840, 2160)) -> Path:
    """Paint a 16:9 BotFather-style wallpaper. Real pixels, not a description."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as exc:
        dest.write_bytes(_minimal_png())
        raise RuntimeError("Pillow is required to render a wallpaper") from exc

    w, h = size
    img = Image.new("RGB", (w, h), (6, 12, 28))
    draw = ImageDraw.Draw(img)
    # Deep navy → telegram-blue glow
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(6 + 20 * t)
        g = int(12 + 80 * t)
        b = int(28 + 140 * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    cx, cy = w // 2, int(h * 0.46)
    halo = Image.new("RGB", (w, h), (6, 12, 28))
    hd = ImageDraw.Draw(halo)
    hd.ellipse((cx - w * 0.22, cy - h * 0.28, cx + w * 0.22, cy + h * 0.28), fill=(34, 158, 217))
    img = Image.blend(img, halo.filter(ImageFilter.GaussianBlur(radius=max(w // 80, 8))), 0.45)
    draw = ImageDraw.Draw(img)

    head_r = int(min(w, h) * 0.16)
    draw.ellipse((cx - head_r, cy - head_r, cx + head_r, cy + head_r), fill=(18, 28, 48), outline=(120, 210, 255), width=max(w // 400, 4))
    # visor / eyes
    eye_y = cy - head_r // 5
    er = head_r // 6
    for dx in (-head_r // 3, head_r // 3):
        draw.ellipse((cx + dx - er, eye_y - er, cx + dx + er, eye_y + er), fill=(80, 230, 255))
    # beard
    draw.pieslice(
        (cx - head_r * 0.85, cy, cx + head_r * 0.85, cy + int(head_r * 1.35)),
        20,
        160,
        fill=(200, 210, 220),
    )
    # crown
    crown_y = cy - int(head_r * 1.05)
    draw.polygon(
        [
            (cx - head_r // 2, crown_y + head_r // 5),
            (cx - head_r // 4, crown_y - head_r // 6),
            (cx, crown_y + head_r // 8),
            (cx + head_r // 4, crown_y - head_r // 6),
            (cx + head_r // 2, crown_y + head_r // 5),
        ],
        fill=(255, 214, 90),
    )
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=max(w // 28, 24))
        small = ImageFont.truetype("DejaVuSans.ttf", size=max(w // 48, 16))
    except OSError:
        font = ImageFont.load_default()
        small = font
    title = "BOTFATHER"
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, int(h * 0.82)), title, fill=(230, 245, 255), font=font)
    sub = "4K  ·  3840×2160" if size == (3840, 2160) else f"{w}×{h}"
    bbox = draw.textbbox((0, 0), sub, font=small)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, int(h * 0.90)), sub, fill=(160, 200, 230), font=small)
    img.save(dest, "PNG")
    return dest


def _minimal_png() -> bytes:
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
        "de0000000c4944415408d763f8ffff3f0005fe02fea57550a00000000049454e44ae426082"
    )


def computer_use(action: str, target: str = "") -> dict[str, Any]:
    """Small desktop dispatcher. Prefer APIs; this is the GUI last resort."""
    action = (action or "").strip().lower()
    desk = desktop_status()
    if action in {"status", "probe"}:
        return {"ok": True, "desktop": desk}
    if action in {"set_wallpaper", "wallpaper"}:
        return set_wallpaper(target)
    if action in {"open", "open_app"}:
        if not desk.get("available"):
            return {"ok": False, "status": "blocked", "reason": "no desktop display", "desktop": desk}
        if not target:
            return {"ok": False, "status": "blocked", "reason": "no app target"}
        subprocess.Popen(  # noqa: S603
            [target] if not target.startswith("/") and " " not in target else target,
            shell=(" " in target),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=os.environ.copy(),
        )
        return {"ok": True, "status": "launched", "target": target}
    return {"ok": False, "status": "blocked", "reason": f"unknown computer-use action: {action}"}

