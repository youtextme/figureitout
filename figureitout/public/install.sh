#!/usr/bin/env bash
# Install figureitout as the default objective runner on this machine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
copy_skill() {
  local dest="$1"
  mkdir -p "$dest"
  cp "$ROOT/SKILL.md" "$dest/SKILL.md"
  [ -f "$ROOT/PROMPT.md" ] && cp "$ROOT/PROMPT.md" "$dest/PROMPT.md"
  [ -f "$ROOT/HOW_TO_BUILD.md" ] && cp "$ROOT/HOW_TO_BUILD.md" "$dest/HOW_TO_BUILD.md"
  [ -f "$ROOT/RUN_FOREST.md" ] && cp "$ROOT/RUN_FOREST.md" "$dest/RUN_FOREST.md"
  echo "Installed figureitout to $dest"
}
copy_skill "${HOME}/.cursor/skills/figureitout"
copy_skill "${HOME}/.agents/skills/figureitout"
if [ -d "${HOME}/.openclaw" ]; then
  copy_skill "${HOME}/.openclaw/workspace/skills/figureitout"
  copy_skill "${HOME}/.openclaw/skills/figureitout"
fi
echo "Reload the IDE / start a new OpenClaw session. Or: python -m figureitout --install"
