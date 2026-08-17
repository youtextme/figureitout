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
  if gh repo view youtextme/run-forrest-run >/dev/null 2>&1; then
    git remote remove origin 2>/dev/null || true
    git remote add origin https://github.com/youtextme/run-forrest-run.git
    git push -u origin main
    echo "🌲 Published: https://github.com/youtextme/run-forrest-run"
    exit 0
  fi
  gh repo create youtextme/run-forrest-run --public --source=. --remote=origin --push && exit 0
fi

echo "🌲 Mirror branch (works today):"
echo "   git clone -b run-forrest-run-standalone https://github.com/youtextme/figureitout.git run-forrest-run"
echo ""
echo "🌲 To publish as youtextme/run-forrest-run:"
echo "   1. Create an empty public repo named run-forrest-run on GitHub"
echo "   2. git remote add origin https://github.com/youtextme/run-forrest-run.git"
echo "   3. git push -u origin main"
