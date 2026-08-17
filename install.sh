#!/usr/bin/env bash
# Copy SKILL.md into Cursor, Devin, and OpenClaw. Run from this folder.
set -euo pipefail
for dest in \
  "${HOME}/.cursor/skills/figureitout" \
  "${HOME}/.openclaw/skills/figureitout" \
  "${HOME}/.agents/skills/figureitout"
do
  mkdir -p "$dest"
  cp SKILL.md "$dest/SKILL.md"
  cp PROMPT.md "$dest/PROMPT.md"
  echo "Installed figureitout to $dest"
done
echo "Reload the Cursor window. OpenClaw picks up ~/.openclaw/skills on the next session."
