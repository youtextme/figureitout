#!/usr/bin/env bash
# Publish run-forrest-run as https://github.com/youtextme/run-forrest-run
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  git init -b main
  git add -A
  git commit -m "Run, Forrest, Run! — objective-runner platform."
fi

if gh auth status >/dev/null 2>&1; then
  gh repo create youtextme/run-forrest-run --public --source=. --remote=origin --push
  echo "🌲 Published: https://github.com/youtextme/run-forrest-run"
  exit 0
fi

echo "🌲 Run, Forrest, Run! — invoked."
echo "🌲 Create an empty repo at https://github.com/new named run-forrest-run, then:"
echo "   git remote add origin https://github.com/youtextme/run-forrest-run.git"
echo "   git push -u origin main"
