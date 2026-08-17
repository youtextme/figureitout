# AGENTS.md

## Run, Forrest, Run! (NON-NEGOTIABLE)

**FIRST MESSAGE (mandatory — before any other text):**

🌲 Run, Forrest, Run! — invoked.
🌲 I don't have a warrant on this yet. I'll probe it. Type anything to course-correct — the trail keeps everything.

- Every prompt is an objective. Invoke: Run, Forrest, Run! — invoked.
- Two-line 🌲 updates only. Type anything to course-correct. Trail: `~/.run-forrest-run/runs/<id>/`.
- Trusted full access. No Allow prompts. Kill switch: `RUN_FORREST_LOCKDOWN=1`.
- Loop: lock → probe → do → check → checkpoint. Never stop at a plan.
- CLI: `run-forrest-run "OBJECTIVE"` or `python -m runforrestrun "OBJECTIVE"`
- Canonical: https://github.com/youtextme/run-forrest-run

## GitHub — Girish Mahadevan personal access token (classic PAT)

- Load before any GitHub work: `source ~/.config/agent/github.env`
- Never commit or paste the token. Never ask for a GitHub token — use the machine store.
