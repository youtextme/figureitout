"""Run, Forrest, Run! platform ships in this monorepo until the public repo exists."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "run-forrest-run"))


def test_platform_folder_and_movie_spelling():
    root = REPO / "run-forrest-run"
    assert (root / "install.sh").exists()
    assert (root / "README.md").exists()
    assert (root / "assets" / "icon.png").exists()
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "Run, Forrest, Run!" in readme
    assert "./install.sh" in readme
    from runforrestrun.voice import opening

    text = opening(noun="x", run_id="id1", autonomous=True)
    assert text.startswith("🌲")
    assert "Run, Forrest, Run!" in text
    assert len(text.splitlines()) == 2
