#!/usr/bin/env bash
# Copy SKILL.md into Cursor (all projects). Run from this folder.
set -euo pipefail
DEST="${HOME}/.cursor/skills/figureitout"
mkdir -p "$DEST"
cp SKILL.md "$DEST/SKILL.md"
cp PROMPT.md "$DEST/PROMPT.md"
echo "Installed figureitout to $DEST"
echo "Reload the Cursor window."
