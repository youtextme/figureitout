#!/usr/bin/env bash
# One command. Detects IDEs/CLIs on this machine. Installs Run, Forrest, Run as the default.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "🌲 Run, Forrest, Run! — invoked."
  echo "🌲 I cannot install autonomously. I need python3 on PATH."
  exit 1
fi
if "$PY" -m pip install -e "$ROOT" -q >/dev/null 2>&1; then
  :
else
  export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
fi
"$PY" -m runforrestrun --install
"$PY" -m runforrestrun --watch
echo "🌲 Reload your IDE (or start a new OpenClaw session). Then any prompt is a trail."
