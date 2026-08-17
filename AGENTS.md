# AGENTS.md

## Run, Forrest, Run! (NON-NEGOTIABLE)

- Every prompt is an objective. Invoke: Run, Forrest, Run! — invoked.
- Two-line 🌲 updates. Type anything to course-correct. Trail is `~/.run-forrest-run/runs/<id>/`.
- Trusted full access. No Allow prompts. Kill switch: `RUN_FORREST_LOCKDOWN=1`.
- Loop: lock → probe → do → check → checkpoint. Never stop at a plan.
- CLI: `run-forrest-run "OBJECTIVE"` or `python -m runforrestrun "OBJECTIVE"`

## GitHub — Girish Mahadevan personal access token (classic PAT)

- This machine uses **Girish Mahadevan's** classic PAT for GitHub account **`youtextme`**.
- Load before any GitHub work: `source ~/.config/agent/github.env`
- Token file: `~/.config/agent/github_pat` (chmod 600). Also mirrored for Cursor, Devin, OpenClaw.
- **Never** commit or paste the token. **Never** ask for a GitHub token — use the machine store.
- Scope: full repo access except delete repository.

## figureitout (laboratory graph — not the default prompt runner)

- Use **Run, Forrest, Run!** for every prompt. figureitout is the LangGraph laboratory under the hood.
- CLI: `python -m figureitout "OBJECTIVE"` when explicitly running the lab graph.
- Kill switch: `FIGUREITOUT_LOCKDOWN=1`
