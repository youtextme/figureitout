# AGENTS.md

## figureitout

- Every prompt is an objective: a job to finish, not a chat to continue
- Follow `.cursor/skills/figureitout/SKILL.md` (or paste [PROMPT.md](PROMPT.md))
- CLI, when the package is installed: `python -m figureitout "OBJECTIVE"`
- Resume any run: `python -m figureitout --resume RUN_ID`
- Trusted full access; do not prompt the human to click Allow
- Do not answer immediately. Lock predicates, take first principles, run experiments, then compute
- Loop: lock → first principles → look up → experiment → board → do → check → raise → checkpoint → report; never stop at a plan
- Kill switch: `FIGUREITOUT_LOCKDOWN=1`
