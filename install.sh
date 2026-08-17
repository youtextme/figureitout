#!/usr/bin/env bash
# One command. Prompt-level law. No repo files. Evolves all IDEs/CLIs via --sync.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
PY=python3
if ! command -v python3 >/dev/null 2>&1; then PY=python; fi
"$PY" -m pip install -e "$ROOT" -q 2>/dev/null || export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
RUN_FORREST_SKIP_SYNC=1 "$PY" -m runforrestrun --install-global
RUN_FORREST_SKIP_SYNC=1 "$PY" -m runforrestrun --watch
echo "🌲 Reload Cursor (Developer: Reload Window). Restart OpenClaw/Devin. Any repo, any prompt."
