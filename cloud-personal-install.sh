#!/usr/bin/env bash
# Personal Cloud Agent environment install — paste into dashboard → Environments → Install
# Applies to ANY repo without its own .cursor/environment.json (e.g. mohPlay).
set -euo pipefail
pip install "git+https://github.com/youtextme/figureitout.git" -q 2>/dev/null || true
export RUN_FORREST_SKIP_SYNC=1
python3 -m runforrestrun --bootstrap .
python3 -m runforrestrun --install
